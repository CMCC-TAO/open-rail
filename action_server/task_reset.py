"""
复位任务 - 将手臂复位到预设姿态（左手/右手/双手）

不需要 VLA 推理，直接使用预设的复位位姿 + 线性插值轨迹。

任务接口:
  {
    "task": "left arm reset",
    "target": "none",
    "waypoint": "none"
  }
  {
    "task": "right arm reset",
    "target": "none",
    "waypoint": "none"
  }
  {
    "task": "both arm reset",
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
    ERR_RESET_NO_STATE,
)

# ==============================================
# 复位目标位姿（7 关节，弧度）
# ==============================================
LEFT_RESET_POSE = np.array([0, 0.3, 0, 1.3, 0, 0, 0])
RIGHT_RESET_POSE = np.array([0, -0.3, 0, 1.3, 0, 0, 0])

# ==============================================
# 时间常量
# ==============================================
ARM_INTERPOLATION_TIME = 3.0   # 手臂线性插值时长（秒）
CONTROL_INTERVAL = 0.02         # 控制周期 ~50Hz


class ResetHandler(AbstractTaskHandler):
    """复位任务处理器

    由 dispatcher 路由到以下 3 个 task name 之一:
      - "left arm reset"
      - "right arm reset"
      - "both arm reset"
    """

    @property
    def task_name(self) -> str:
        return "reset"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        task = params.get("task", "")

        if task == "left arm reset":
            return self._left_arm_reset(goal_handle, context)
        elif task == "right arm reset":
            return self._right_arm_reset(goal_handle, context)
        elif task == "both arm reset":
            return self._both_arm_reset(goal_handle, context)
        else:
            self.send_feedback(goal_handle, 0, f"未知复位子任务: {task}")
            return TaskResult(False, error_code=99,
                              error_message=f'Unknown reset sub-task: "{task}"')

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

        注：不使用 _get_reset_current_action()，而是直接在 action 缓存读不到时降级到
            state 测量值作为兜底，确保即使 action 话题延迟也能正常工作。
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
                return obs["obs.state"]
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

        流程:
          1. 禁用相对限幅（允许大幅规划）
          2. 逐帧线性插值，每帧发送完整 26 维动作
          3. 恢复相对限幅

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
            t = (step + 1) / num_steps

            action = current_state.copy()
            if left_target is not None:
                action[0:7] = current_state[0:7] + t * (left_target - current_state[0:7])
            if right_target is not None:
                action[7:14] = current_state[7:14] + t * (right_target - current_state[7:14])

            robot.send_robot_action(action)

            pct = start_progress + int((end_progress - start_progress) * (step + 1) / num_steps)
            send_vla_feedback(goal_handle, pct,
                              f"手臂复位中... {t * 100:.0f}%")

            time.sleep(actual_interval)

        return current_state

    # ================================================================
    # 复位逻辑
    # ================================================================

    def _left_arm_reset(self, goal_handle, context) -> TaskResult:
        """左手复位：
          1. 3s 线性插值 → 左手复位位姿 [0,0.3,0,1.3,0,0,0]
          2. 左手掌不变
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "左手复位开始")

        current_state = self._linear_interpolate_arms(
            robot_body,
            left_target=LEFT_RESET_POSE,
            right_target=None,
            duration=ARM_INTERPOLATION_TIME,
            goal_handle=goal_handle,
            start_progress=10, end_progress=95,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_RESET_NO_STATE,
                              error_message="Failed to get current robot state for left arm reset")

        send_vla_feedback(goal_handle, 100, "左手复位完成")
        return TaskResult(True)

    def _right_arm_reset(self, goal_handle, context) -> TaskResult:
        """右手复位：
          1. 3s 线性插值 → 右手复位位姿 [0,-0.3,0,1.3,0,0,0]
          2. 右手掌不变
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "右手复位开始")

        current_state = self._linear_interpolate_arms(
            robot_body,
            left_target=None,
            right_target=RIGHT_RESET_POSE,
            duration=ARM_INTERPOLATION_TIME,
            goal_handle=goal_handle,
            start_progress=10, end_progress=95,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_RESET_NO_STATE,
                              error_message="Failed to get current robot state for right arm reset")

        send_vla_feedback(goal_handle, 100, "右手复位完成")
        return TaskResult(True)

    def _both_arm_reset(self, goal_handle, context) -> TaskResult:
        """双手复位：
          1. 3s 线性插值，双臂同时到复位位姿
          2. 手掌不变
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "双手复位开始")

        current_state = self._linear_interpolate_arms(
            robot_body,
            left_target=LEFT_RESET_POSE,
            right_target=RIGHT_RESET_POSE,
            duration=ARM_INTERPOLATION_TIME,
            goal_handle=goal_handle,
            start_progress=10, end_progress=95,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_RESET_NO_STATE,
                              error_message="Failed to get current robot state for both arm reset")

        send_vla_feedback(goal_handle, 100, "双手复位完成")
        return TaskResult(True)
