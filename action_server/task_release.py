"""
松手任务 - 释放手部抓取的物体（左手/右手/双手）

不需要 VLA 推理，直接将指定手部关节控制量设为 0 并保持 1 秒。

任务接口:
  {
    "task": "left hand release",    # 左手松手
    "target": "none",
    "waypoint": "none"
  }
  {
    "task": "right hand release",   # 右手松手
    "target": "none",
    "waypoint": "none"
  }
  {
    "task": "both hand release",    # 双手松手
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
)

# ==============================================
# 时间常量
# ==============================================
HAND_RELEASE_HOLD_TIME = 1.0  # 手部松开后保持时长（秒）
HAND_RELEASE_STEPS = 10       # 渐变释放步数（均匀插值，每步40ms，共~0.4s渐变）
HAND_RELEASE_STEP_INTERVAL = 0.04  # 每步间隔（秒）


class ReleaseHandler(AbstractTaskHandler):
    """松手任务处理器

    由 dispatcher 路由到以下 3 个 task name 之一:
      - "left hand release"
      - "right hand release"
      - "both hand release"
    """

    @property
    def task_name(self) -> str:
        return "release"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        task = params.get("task", "")

        if task == "left hand release":
            return self._left_hand_release(goal_handle, context)
        elif task == "right hand release":
            return self._right_hand_release(goal_handle, context)
        elif task == "both hand release":
            return self._both_hand_release(goal_handle, context)
        else:
            self.send_feedback(goal_handle, 0, f"未知松手子任务: {task}")
            return TaskResult(False, error_code=99,
                              error_message=f'Unknown release sub-task: "{task}"')

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

    def _release_hand_and_hold(
        self, robot_body, hand_side: str,
        goal_handle, hold_duration: float,
    ) -> None:
        """松手：将手部 6 个关节控制量渐变归零，手臂保持不变，保持指定时间

        使用均匀插值分步释放，避免一步归零导致手部快速坠落。

        Args:
            hand_side: 'left' / 'right' / 'both'
        """
        current_state = self._get_current_full_state(robot_body)
        if current_state is None:
            return

        action_start = current_state.copy()
        action_end = current_state.copy()
        zero_hand = np.zeros(6)

        if hand_side in ('left', 'both'):
            action_end[14:20] = zero_hand
        if hand_side in ('right', 'both'):
            action_end[20:26] = zero_hand

        side_label = {'left': '左手', 'right': '右手', 'both': '双手'}.get(hand_side, hand_side)

        # 渐变释放：均匀插值 HAND_RELEASE_STEPS 步
        for step in range(1, HAND_RELEASE_STEPS + 1):
            alpha = step / HAND_RELEASE_STEPS
            action = action_start * (1 - alpha) + action_end * alpha
            robot_body.control_robot(action)
            time.sleep(HAND_RELEASE_STEP_INTERVAL)

        send_vla_feedback(goal_handle, 50, f"{side_label}已松开，保持 {hold_duration:.0f}s...")
        time.sleep(hold_duration)

    # ================================================================
    # 松手逻辑
    # ================================================================

    def _left_hand_release(self, goal_handle, context) -> TaskResult:
        """左手松手：
          1. 左手 hand 的 6 个电机控制量设为 [0,0,0,0,0,0]
          2. 手臂控制量不变
          3. 维持 1s
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "左手松手开始")

        self._release_hand_and_hold(robot_body, 'left', goal_handle, HAND_RELEASE_HOLD_TIME)

        send_vla_feedback(goal_handle, 100, "左手松手完成")
        return TaskResult(True)

    def _right_hand_release(self, goal_handle, context) -> TaskResult:
        """右手松手：
          1. 右手 hand 的 6 个电机控制量设为 [0,0,0,0,0,0]
          2. 手臂控制量不变
          3. 维持 1s
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "右手松手开始")

        self._release_hand_and_hold(robot_body, 'right', goal_handle, HAND_RELEASE_HOLD_TIME)

        send_vla_feedback(goal_handle, 100, "右手松手完成")
        return TaskResult(True)

    def _both_hand_release(self, goal_handle, context) -> TaskResult:
        """双手松手：
          1. 左右两只手 hand 的 6 个电机控制量分别设为 [0,0,0,0,0,0]
          2. 手臂控制量不变
          3. 维持 1s
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "双手松手开始")

        self._release_hand_and_hold(robot_body, 'both', goal_handle, HAND_RELEASE_HOLD_TIME)

        send_vla_feedback(goal_handle, 100, "双手松手完成")
        return TaskResult(True)
