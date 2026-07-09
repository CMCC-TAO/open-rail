"""
复位任务 - 将手臂复位到预设姿态（左手/右手/双手）

不需要 VLA 推理，直接使用预设的复位位姿 + 线性插值轨迹。

任务接口:
  {
    "task": "reset",           # 左手复位
    "target": "left arm",      # 抓取的目标
    "waypoint": "none"
  }
  {
    "task": "reset",           # 右手复位
    "target": "right arm",     # 抓取的目标
    "waypoint": "none"
  }
  {
    "task": "reset",           # 双手复位
    "target": "both arm",      # 抓取的目标
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
_LEFT_RESET_POSE  = np.array([0.28,  0.22, 0, 1.0, 0, 0, 0])
_RIGHT_RESET_POSE = np.array([0.28, -0.22, 0, 1.0, 0, 0, 0])

# ==============================================
# 时间常量
# ==============================================


class ResetHandler(AbstractTaskHandler):
    """复位任务处理器

    由 dispatcher 路由到以下 3 个 task:target 复合键之一:
      - "reset:left arm"
      - "reset:right arm"
      - "reset:both arm"
    """

    @property
    def task_name(self) -> str:
        return "reset"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        target = params.get("target", "")

        if target == "left arm":
            return self._left_arm_reset(goal_handle, context)
        elif target == "right arm":
            return self._right_arm_reset(goal_handle, context)
        elif target == "both arm":
            return self._both_arm_reset(goal_handle, context)
        else:
            self.send_feedback(goal_handle, 0, f"未知复位目标: {target}")
            return TaskResult(False, error_code=99,
                              error_message=f'Unknown reset target: "{target}"')

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

        current_state = robot_body.move_arms(
            left_target=_LEFT_RESET_POSE,
            right_target=None,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_RESET_NO_STATE,
                              error_message="Failed to get current robot state for left arm reset")
        send_vla_feedback(goal_handle, 95, "左手复位到位")

        send_vla_feedback(goal_handle, 100, "左手复位完成")
        return TaskResult(True)

    def _right_arm_reset(self, goal_handle, context) -> TaskResult:
        """右手复位：
          1. 3s 线性插值 → 右手复位位姿 [0,-0.3,0,1.3,0,0,0]
          2. 右手掌不变
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "右手复位开始")

        current_state = robot_body.move_arms(
            left_target=None,
            right_target=_RIGHT_RESET_POSE,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_RESET_NO_STATE,
                              error_message="Failed to get current robot state for right arm reset")
        send_vla_feedback(goal_handle, 95, "右手复位到位")

        send_vla_feedback(goal_handle, 100, "右手复位完成")
        return TaskResult(True)

    def _both_arm_reset(self, goal_handle, context) -> TaskResult:
        """双手复位：
          1. 3s 线性插值，双臂同时到复位位姿
          2. 手掌不变
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "双手复位开始")

        current_state = robot_body.move_arms(
            left_target=_LEFT_RESET_POSE,
            right_target=_RIGHT_RESET_POSE,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_RESET_NO_STATE,
                              error_message="Failed to get current robot state for both arm reset")
        send_vla_feedback(goal_handle, 95, "双手复位到位")

        send_vla_feedback(goal_handle, 100, "双手复位完成")
        return TaskResult(True)
