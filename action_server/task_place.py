"""
放置任务 - 将物体放下（左手/右手/单手/双手）

不需要 VLA 推理，直接使用预设的放置位姿 + 线性插值轨迹。

任务接口:
  {
    "task": "left arm place",    # 左手放置
    "target": "none",
    "waypoint": "none"
  }
  {
    "task": "right arm place",   # 右手放置
    "target": "none",
    "waypoint": "none"
  }
  {
    "task": "one arm place",     # 单手放置（自动判断哪只手有物体）
    "target": "none",
    "waypoint": "none"
  }
  {
    "task": "both arm place",    # 双手放置
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
    ERR_PLACE_TIMEOUT, ERR_PLACE_LEFT_EMPTY, ERR_PLACE_RIGHT_EMPTY,
    ERR_PLACE_ONE_HAND_BOTH_EMPTY, ERR_PLACE_BOTH_HAND_NOT_BOTH,
    ERR_PLACE_ONE_HAND_STILL_HOLDING,
)

# ==============================================
# 放置目标位姿（7 关节，弧度）—— 请根据实测调节
# LEFT_PLACE_POSE = np.array([-0.0, 0.1, 0.0, 0.72, 0.0, -0.9, 0.0])
# RIGHT_PLACE_POSE = np.array([-0.0, -0.1, 0.0, 0.72, 0.0, -0.9, 0.0])
# ==============================================
LEFT_PLACE_POSE  = np.array([-0.1726,  0.1, 0.0, 1.045, 0.0, -1.393, 0.0])
RIGHT_PLACE_POSE = np.array([-0.1726, -0.1, 0.0, 1.045, 0.0, -1.393, 0.0])

# ==============================================
# 放置完成后回缩位姿（手掌打开后手臂后退一段距离）
# ==============================================
LEFT_RETRACT_POSE  = np.array([0.5,  0.1, 0.0, 0.0, 0.0, -0.8, 0.0])
RIGHT_RETRACT_POSE = np.array([0.5, -0.1, 0.0, 0.0, 0.0, -0.8, 0.0])

# ==============================================
# 安全中间姿态（与 task_init_grasp.py 一致）
# ==============================================
_SAFE_LEFT_ARM = np.array([1.5,   0.5, 0.0, -0.8, 0.0, -0.8,  0.0])
_SAFE_RIGHT_ARM = np.array([1.5, -0.5, 0.0, -0.8, 0.0, -0.8,  0.0])

# ==============================================
# 垂直复位姿态（与 task_reset.py 一致）
# ==============================================
_LEFT_RESET_POSE = np.array([0, 0.3, 0, 1.3, 0, 0, 0])
_RIGHT_RESET_POSE = np.array([0, -0.3, 0, 1.3, 0, 0, 0])

# ==============================================
# 时间常量
# ==============================================
ARM_INTERPOLATION_TIME = 3.0   # 手臂线性插值时长（秒）
ARM_RETRACT_TIME = 3.0          # 放置后手臂回缩时长（秒）
ARM_SAFE_TIME = 4.0             # 手臂安全姿态过渡时长（秒）
ARM_RESET_TIME = 4.0            # 手臂垂直复位时长（秒）
HAND_OPEN_HOLD_TIME = 1.0       # 手掌打开后保持时长（秒）
CONTROL_INTERVAL = 0.02         # 控制周期 ~50Hz


class PlaceHandler(AbstractTaskHandler):
    """放置任务处理器

    由 dispatcher 路由到以下 4 个 task name 之一:
      - "left arm place"
      - "right arm place"
      - "one arm place"
      - "both arm place"
    """

    @property
    def task_name(self) -> str:
        return "place"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        task = params.get("task", "")

        if task == "left arm place":
            return self._left_arm_place(goal_handle, context)
        elif task == "right arm place":
            return self._right_arm_place(goal_handle, context)
        elif task == "one arm place":
            return self._one_arm_place(goal_handle, context)
        elif task == "both arm place":
            return self._both_arm_place(goal_handle, context)
        else:
            self.send_feedback(goal_handle, 0, f"未知放置子任务: {task}")
            return TaskResult(False, error_code=99,
                              error_message=f'Unknown place sub-task: "{task}"')

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
        zero_hand = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 700.0])

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
    # 放置逻辑
    # ================================================================

    def _left_arm_place(self, goal_handle, context) -> TaskResult:
        """左手放置 + 放置后复位

        完整序列:
          1. 3s 线性插值 → 左放置位姿
          2. 左手手掌全开，维持 1s
          3. 3s 线性插值 → 左回缩位姿
          4. 3s 线性插值 → 左安全中间姿态
          5. 3s 线性插值 → 左垂直复位姿态
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "左手放置开始")

        # 1. 3s 线性插值 → 放置位姿
        current_state = self._linear_interpolate_arms(
            robot_body,
            left_target=LEFT_PLACE_POSE,
            right_target=None,
            duration=ARM_INTERPOLATION_TIME,
            goal_handle=goal_handle,
            start_progress=10, end_progress=50,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_PLACE_TIMEOUT,
                              error_message="Failed to get current robot state for left arm place")

        # 2. 打开左手，保持
        self._open_hand_and_hold(robot_body, 'left', goal_handle, HAND_OPEN_HOLD_TIME, base_state=current_state)

        # 3. 手臂回缩到安全位置
        self._linear_interpolate_arms(
            robot_body,
            left_target=LEFT_RETRACT_POSE,
            right_target=None,
            duration=ARM_RETRACT_TIME,
            goal_handle=goal_handle,
            start_progress=55, end_progress=70,
        )

        # 4. 过渡到安全中间姿态
        self._linear_interpolate_arms(
            robot_body,
            left_target=_SAFE_LEFT_ARM,
            right_target=None,
            duration=ARM_SAFE_TIME,
            goal_handle=goal_handle,
            start_progress=75, end_progress=88,
        )

        # 5. 过渡到垂直复位姿态
        self._linear_interpolate_arms(
            robot_body,
            left_target=_LEFT_RESET_POSE,
            right_target=None,
            duration=ARM_RESET_TIME,
            goal_handle=goal_handle,
            start_progress=90, end_progress=99,
        )

        send_vla_feedback(goal_handle, 100, "左手放置完成")
        return TaskResult(True)

    def _right_arm_place(self, goal_handle, context) -> TaskResult:
        """右手放置 + 放置后复位

        完整序列:
          1. 3s 线性插值 → 右放置位姿
          2. 右手手掌全开，维持 1s
          3. 3s 线性插值 → 右回缩位姿
          4. 3s 线性插值 → 右安全中间姿态
          5. 3s 线性插值 → 右垂直复位姿态
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "右手放置开始")

        # 1. 3s 线性插值 → 放置位姿
        current_state = self._linear_interpolate_arms(
            robot_body,
            left_target=None,
            right_target=RIGHT_PLACE_POSE,
            duration=ARM_INTERPOLATION_TIME,
            goal_handle=goal_handle,
            start_progress=10, end_progress=50,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_PLACE_TIMEOUT,
                              error_message="Failed to get current robot state for right arm place")

        # 2. 打开右手，保持
        self._open_hand_and_hold(robot_body, 'right', goal_handle, HAND_OPEN_HOLD_TIME, base_state=current_state)

        # 3. 手臂回缩到安全位置
        self._linear_interpolate_arms(
            robot_body,
            left_target=None,
            right_target=RIGHT_RETRACT_POSE,
            duration=ARM_RETRACT_TIME,
            goal_handle=goal_handle,
            start_progress=55, end_progress=70,
        )

        # 4. 过渡到安全中间姿态
        self._linear_interpolate_arms(
            robot_body,
            left_target=None,
            right_target=_SAFE_RIGHT_ARM,
            duration=ARM_SAFE_TIME,
            goal_handle=goal_handle,
            start_progress=75, end_progress=88,
        )

        # 5. 过渡到垂直复位姿态
        self._linear_interpolate_arms(
            robot_body,
            left_target=None,
            right_target=_RIGHT_RESET_POSE,
            duration=ARM_RESET_TIME,
            goal_handle=goal_handle,
            start_progress=90, end_progress=99,
        )

        send_vla_feedback(goal_handle, 100, "右手放置完成")
        return TaskResult(True)

    def _one_arm_place(self, goal_handle, context) -> TaskResult:
        """单手放置：自动判断哪只手有物体"""
        grasp_state = context.grasp_detector.grasp_state  # [left_grasped, right_grasped]

        if grasp_state[1]:   # 右手有东西 → 右手放置
            return self._right_arm_place(goal_handle, context)
        elif grasp_state[0]:  # 左手有东西 → 左手放置
            return self._left_arm_place(goal_handle, context)
        else:
            # 双手都没东西
            send_vla_feedback(goal_handle, 0, "双手都没有物体，无法放置")
            return TaskResult(False, error_code=ERR_PLACE_ONE_HAND_BOTH_EMPTY,
                              error_message="Both hands are empty, cannot do one arm place")

    def _both_arm_place(self, goal_handle, context) -> TaskResult:
        """双手放置 + 放置后复位

        完整序列:
          1. 3s 线性插值 → 双臂放置位姿
          2. 同时打开双手，维持 1s
          3. 等待 0.5s 检测是否所有物体已放下
          4. 3s 线性插值 → 双臂回缩位姿
          5. 3s 线性插值 → 双臂安全中间姿态
          6. 3s 线性插值 → 双臂垂直复位姿态
        """
        grasp_state = context.grasp_detector.grasp_state  # [left_grasped, right_grasped]

        if not (grasp_state[0] and grasp_state[1]):
            send_vla_feedback(goal_handle, 0, "双手没有同时有物体，无法放置")
            return TaskResult(False, error_code=ERR_PLACE_BOTH_HAND_NOT_BOTH,
                              error_message="Not both hands have objects, cannot do both arm place")

        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "双手放置开始")

        # 1. 3s 线性插值，双臂同时到放置位姿
        current_state = self._linear_interpolate_arms(
            robot_body,
            left_target=LEFT_PLACE_POSE,
            right_target=RIGHT_PLACE_POSE,
            duration=ARM_INTERPOLATION_TIME,
            goal_handle=goal_handle,
            start_progress=10, end_progress=45,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_PLACE_TIMEOUT,
                              error_message="Failed to get current robot state for both arm place")

        # 2. 同时打开双手，保持 1s
        self._open_hand_and_hold(robot_body, 'both', goal_handle, HAND_OPEN_HOLD_TIME, base_state=current_state)

        # 3. 等待 0.5s 让 grasp_detector 更新
        time.sleep(0.5)
        final_grasp_state = context.grasp_detector.grasp_state
        if final_grasp_state[0] or final_grasp_state[1]:
            send_vla_feedback(goal_handle, 50, "有一只手未能放下物体")
            return TaskResult(False, error_code=ERR_PLACE_ONE_HAND_STILL_HOLDING,
                              error_message="One hand still holding object after both arm place")

        # 4. 双臂回缩
        self._linear_interpolate_arms(
            robot_body,
            left_target=LEFT_RETRACT_POSE,
            right_target=RIGHT_RETRACT_POSE,
            duration=ARM_RETRACT_TIME,
            goal_handle=goal_handle,
            start_progress=55, end_progress=70,
        )

        # 5. 双臂过渡到安全中间姿态
        self._linear_interpolate_arms(
            robot_body,
            left_target=_SAFE_LEFT_ARM,
            right_target=_SAFE_RIGHT_ARM,
            duration=ARM_SAFE_TIME,
            goal_handle=goal_handle,
            start_progress=75, end_progress=88,
        )

        # 6. 双臂过渡到垂直复位姿态
        self._linear_interpolate_arms(
            robot_body,
            left_target=_LEFT_RESET_POSE,
            right_target=_RIGHT_RESET_POSE,
            duration=ARM_RESET_TIME,
            goal_handle=goal_handle,
            start_progress=90, end_progress=99,
        )

        send_vla_feedback(goal_handle, 100, "双手放置完成")
        return TaskResult(True)
