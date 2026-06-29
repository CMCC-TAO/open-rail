"""
递物任务 - 将物体递出（左手/右手/单手/双手）

不需要 VLA 推理，直接使用预设的递物位姿 + 线性插值轨迹。

任务接口:
  {
    "task": "left arm deliver",   # 左手递物
    "target": "none",
    "waypoint": "none"
  }
  {
    "task": "right arm deliver",  # 右手递物
    "target": "none",
    "waypoint": "none"
  }
  {
    "task": "one arm deliver",    # 单手递物（自动判断哪只手有物体）
    "target": "none",
    "waypoint": "none"
  }
  {
    "task": "both arm deliver",   # 双手递物
    "target": "none",
    "waypoint": "none"
  }
"""

import sys
import os
import time
import numpy as np

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.action_base import (
    AbstractTaskHandler, TaskResult, send_vla_feedback,
    ERR_DELIVER_TIMEOUT, ERR_DELIVER_LEFT_EMPTY, ERR_DELIVER_RIGHT_EMPTY,
    ERR_DELIVER_ONE_HAND_BOTH_EMPTY, ERR_DELIVER_BOTH_HAND_NOT_BOTH,
    ERR_DELIVER_ONE_HAND_STILL_HOLDING,
)

# ==============================================
# 递物目标位姿（7 关节，弧度）
# ==============================================
LEFT_DELIVER_POSE = np.array([-1.0, 0.1, 0.0, 0.5, 0.0, 0.0, 0.0])
RIGHT_DELIVER_POSE = np.array([-1.0, -0.1, 0.0, 0.5, 0.0, 0.0, 0.0])

# ==============================================
# 时间常量
# ==============================================
ARM_INTERPOLATION_TIME = 3.0   # 手臂线性插值时长（秒）
HAND_OPEN_HOLD_TIME = 1.0       # 手掌打开后保持时长（秒）
CONTROL_INTERVAL = 0.02         # 控制周期 ~50Hz


class DeliverHandler(AbstractTaskHandler):
    """递物任务处理器

    由 dispatcher 路由到以下 4 个 task name 之一:
      - "left arm deliver"
      - "right arm deliver"
      - "one arm deliver"
      - "both arm deliver"
    """

    @property
    def task_name(self) -> str:
        return "deliver"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        task = params.get("task", "")

        if task == "left arm deliver":
            return self._left_arm_deliver(goal_handle, context)
        elif task == "right arm deliver":
            return self._right_arm_deliver(goal_handle, context)
        elif task == "one arm deliver":
            return self._one_arm_deliver(goal_handle, context)
        elif task == "both arm deliver":
            return self._both_arm_deliver(goal_handle, context)
        else:
            self.send_feedback(goal_handle, 0, f"未知递物子任务: {task}")
            return TaskResult(False, error_code=99,
                              error_message=f'Unknown deliver sub-task: "{task}"')

    # ================================================================
    # 工具方法
    # ================================================================

    def _get_current_full_state(self, robot_body) -> np.ndarray | None:
        """获取当前 26 维完整状态（优先从 action 缓存读取，用于轨迹规划起点）

        优先级:
          1. Action 缓存 — /joint_action + /left_hand/set_angle + /right_hand/set_angle
             （最新下发量，轨迹规划起点更平滑）
          2. robot_body.current_state（VLA 观察线程缓存，可能过期）
          3. retrieve_observation() 回退（需要相机数据）
        """
        # 优先级 1: 从 action 订阅缓存读取（最新下发量，消除执行滞后）
        try:
            robot = robot_body.robot
            la = robot.latest_left_arm_action
            ra = robot.latest_right_arm_action
            lh = robot.latest_left_hand_action
            rh = robot.latest_right_hand_action
            if all(x is not None for x in (la, ra, lh, rh)):
                la_msg, _ = la
                ra_msg, _ = ra
                lh_msg, _ = lh
                rh_msg, _ = rh
                if (la_msg and ra_msg and lh_msg and rh_msg
                        and la_msg.position and ra_msg.position
                        and lh_msg.position and rh_msg.position):
                    state = np.array(
                        list(la_msg.position)
                        + list(ra_msg.position)
                        + list(lh_msg.position)
                        + list(rh_msg.position),
                        dtype=float,
                    )
                    robot_body.current_state = state.copy()
                    return state
        except Exception:
            pass

        # 优先级 2: 使用 VLA 缓存的状态
        try:
            cs = getattr(robot_body, 'current_state', None)
            if cs is not None:
                return cs.copy()
        except Exception:
            pass

        # 优先级 3: 回退 retrieve_observation（需要相机数据）
        for _ in range(20):
            obs = robot_body.retrieve_observation()
            if obs is not None and "obs.state" in obs:
                state = obs["obs.state"]
                return state
            time.sleep(0.05)
        return None

    def _linear_interpolate_arms(
        self, robot_body,
        left_target: np.ndarray | None,
        right_target: np.ndarray | None,
        duration: float,
        goal_handle,
        start_progress: int,
        end_progress: int,
    ) -> np.ndarray | None:
        """线性插值手臂到目标位姿，手掌保持当前值不变

        注：delta 相对限幅保持开启，插值每步变化很小
            （~0.01 rad，远小于 0.15~0.50 的限幅阈值），
            不会触发裁剪，但能防止意外跳变。

        Args:
            left_target:  左臂 7 维目标位姿，None 表示不动
            right_target: 右臂 7 维目标位姿，None 表示不动
            duration:     插值总时长（秒）

        Returns:
            初始 26 维状态（含手掌值），失败返回 None
        """
        current_state = self._get_current_full_state(robot_body)
        if current_state is None:
            return None

        num_steps = max(1, int(duration / CONTROL_INTERVAL))
        actual_interval = duration / num_steps

        robot = robot_body.robot

        for step in range(num_steps):
            t = (step + 1) / num_steps  # 0 → 1

            action = current_state.copy()
            if left_target is not None:
                action[0:7] = current_state[0:7] + t * (left_target - current_state[0:7])
            if right_target is not None:
                action[7:14] = current_state[7:14] + t * (right_target - current_state[7:14])
            # 手掌保持 current_state 中的值不变

            robot.send_robot_action(action)

            # 进度反馈
            pct = start_progress + int((end_progress - start_progress) * (step + 1) / num_steps)
            send_vla_feedback(goal_handle, pct,
                              f"手臂过渡中... {t * 100:.0f}%")

            time.sleep(actual_interval)

        return action  # 返回最后一帧动作（含目标手臂位姿 + 原始手掌值）

    def _open_hand_and_hold(
        self, robot_body, hand_side: str,
        goal_handle, hold_duration: float,
        base_state: np.ndarray | None = None,
    ) -> None:
        """打开手部（全部手指设为 0.0）并保持指定时间

        Args:
            hand_side: 'left' / 'right' / 'both'
            base_state: 基础状态（含期望的手臂位置），None 则从 robot 读取
        """
        if base_state is not None:
            action = base_state.copy()
        else:
            current_state = self._get_current_full_state(robot_body)
            if current_state is None:
                print('[WARN] _open_hand_and_hold: 无法获取当前机器人状态，跳过松手')
                return
            action = current_state.copy()
        zero_hand = np.zeros(6)

        if hand_side in ('left', 'both'):
            action[14:20] = zero_hand
        if hand_side in ('right', 'both'):
            action[20:26] = zero_hand

        # 注：只修改手掌[14:26]，手臂不变，delta 限幅不会触发
        side_label = {'left': '左手', 'right': '右手', 'both': '双手'}.get(hand_side, hand_side)
        robot_body.control_robot(action)
        send_vla_feedback(goal_handle, 95, f"{side_label}已打开，保持 {hold_duration:.0f}s...")
        time.sleep(hold_duration)

    # ================================================================
    # 递物逻辑
    # ================================================================

    def _left_arm_deliver(self, goal_handle, context) -> TaskResult:
        """左手递物：
          1. 3s 线性插值 → 左边递物位姿
          2. 左手手掌全开，维持 1s
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "左手递物开始")

        current_state = self._linear_interpolate_arms(
            robot_body,
            left_target=LEFT_DELIVER_POSE,
            right_target=None,
            duration=ARM_INTERPOLATION_TIME,
            goal_handle=goal_handle,
            start_progress=10, end_progress=90,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_DELIVER_TIMEOUT,
                              error_message="Failed to get current robot state for left arm deliver")

        self._open_hand_and_hold(robot_body, 'left', goal_handle, HAND_OPEN_HOLD_TIME, base_state=current_state)

        send_vla_feedback(goal_handle, 100, "左手递物完成")
        return TaskResult(True)

    def _right_arm_deliver(self, goal_handle, context) -> TaskResult:
        """右手递物：
          1. 3s 线性插值 → 右边递物位姿
          2. 右手手掌全开，维持 1s
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "右手递物开始")

        current_state = self._linear_interpolate_arms(
            robot_body,
            left_target=None,
            right_target=RIGHT_DELIVER_POSE,
            duration=ARM_INTERPOLATION_TIME,
            goal_handle=goal_handle,
            start_progress=10, end_progress=90,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_DELIVER_TIMEOUT,
                              error_message="Failed to get current robot state for right arm deliver")

        self._open_hand_and_hold(robot_body, 'right', goal_handle, HAND_OPEN_HOLD_TIME, base_state=current_state)

        send_vla_feedback(goal_handle, 100, "右手递物完成")
        return TaskResult(True)

    def _one_arm_deliver(self, goal_handle, context) -> TaskResult:
        """单手递物：自动判断哪只手有物体"""
        grasp_state = context.grasp_detector.grasp_state  # [left_grasped, right_grasped]

        if grasp_state[1]:   # 右手有东西 → 右手递物
            return self._right_arm_deliver(goal_handle, context)
        elif grasp_state[0]:  # 左手有东西 → 左手递物
            return self._left_arm_deliver(goal_handle, context)
        else:
            # 双手都没东西
            send_vla_feedback(goal_handle, 0, "双手都没有物体，无法递物")
            return TaskResult(False, error_code=ERR_DELIVER_ONE_HAND_BOTH_EMPTY,
                              error_message="Both hands are empty, cannot do one arm deliver")

    def _both_arm_deliver(self, goal_handle, context) -> TaskResult:
        """双手递物：两只手必须同时有物体"""
        grasp_state = context.grasp_detector.grasp_state  # [left_grasped, right_grasped]

        if not (grasp_state[0] and grasp_state[1]):
            send_vla_feedback(goal_handle, 0, "双手没有同时有物体，无法递物")
            return TaskResult(False, error_code=ERR_DELIVER_BOTH_HAND_NOT_BOTH,
                              error_message="Not both hands have objects, cannot do both arm deliver")

        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "双手递物开始")

        # 1. 3s 线性插值，双臂同时到递物位姿
        current_state = self._linear_interpolate_arms(
            robot_body,
            left_target=LEFT_DELIVER_POSE,
            right_target=RIGHT_DELIVER_POSE,
            duration=ARM_INTERPOLATION_TIME,
            goal_handle=goal_handle,
            start_progress=10, end_progress=85,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_DELIVER_TIMEOUT,
                              error_message="Failed to get current robot state for both arm deliver")

        # 2. 同时打开双手，保持 1s
        self._open_hand_and_hold(robot_body, 'both', goal_handle, HAND_OPEN_HOLD_TIME, base_state=current_state)

        # 3. 等待 0.5s 让 grasp_detector 更新
        time.sleep(0.5)
        final_grasp_state = context.grasp_detector.grasp_state
        if final_grasp_state[0] or final_grasp_state[1]:
            send_vla_feedback(goal_handle, 98, "有一只手未能放下物体")
            return TaskResult(False, error_code=ERR_DELIVER_ONE_HAND_STILL_HOLDING,
                              error_message="One hand still holding object after both arm deliver")

        send_vla_feedback(goal_handle, 100, "双手递物完成")
        return TaskResult(True)
