"""
finish place 任务 - 放置完成后过渡到安全位姿（双臂和双手）

两段式复位（与 task_finish_grasp.py 对称）:
  1. reset_robot 到安全抬臂姿态（保持当前手掌状态，避免碰撞桌子）
  2. reset_robot 到垂直复位姿态（保持当前手掌状态）
"""

import sys
import os
import numpy as np
from typing import Any

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.action_base import AbstractTaskHandler, TaskResult, ERR_SUCCESS, ERR_FINISH_PLACE_FAILED, ERR_MSG


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


class FinishPlaceHandler(AbstractTaskHandler):
    """'finish place' 任务处理器

    流程:
        1. 获取当前手掌状态
        2. reset_robot 到安全抬臂姿态（手掌不变）
        3. reset_robot 到垂直复位姿态（手掌不变）
        4. 完成
    """

    @property
    def task_name(self) -> str:
        return "finish place"

    def _get_current_hands(self, robot_body) -> np.ndarray:
        """获取当前 12 维手掌状态（最新下发量）"""
        try:
            robot = robot_body.robot
            lh = robot.latest_left_hand_action
            rh = robot.latest_right_hand_action
            if all(x is not None for x in (lh, rh)):
                lh_msg, _ = lh
                rh_msg, _ = rh
                if lh_msg and rh_msg and lh_msg.position and rh_msg.position:
                    return np.array(
                        list(lh_msg.position) + list(rh_msg.position),
                        dtype=float,
                    )
        except Exception:
            pass
        # 兜底：全开（安全值）
        return np.zeros(12, dtype=float)

    def execute(self, goal_handle, params: dict, context: Any) -> TaskResult:
        robot_body = context.robot_body
        try:
            # ===== 步骤 1: 确认机器人连接 =====
            self.send_feedback(goal_handle, 10, "正在确认机器人连接...")

            # ===== 检查手掌数据是否可用 =====
            self.send_feedback(goal_handle, 15, "正在检查机器人手掌数据...")
            robot = robot_body.robot
            lh = robot.latest_left_hand_action
            rh = robot.latest_right_hand_action
            if lh is None or rh is None:
                err_msg = f"{ERR_MSG[ERR_FINISH_PLACE_FAILED]}: 未收到机器人手掌数据"
                self.send_feedback(goal_handle, 0, err_msg)
                return TaskResult(False, error_code=ERR_FINISH_PLACE_FAILED, error_message=err_msg)

            # ===== 步骤 2: 获取当前手掌状态 =====
            hands = self._get_current_hands(robot_body)

            # ===== 步骤 3: 过渡到安全中间姿态（抬臂，手掌不变）=====
            self.send_feedback(goal_handle, 30, "正在过渡到安全中间姿态...")
            safe_pose = np.array([
                *_SAFE_LEFT_ARM,
                *_SAFE_RIGHT_ARM,
                *hands,
            ])
            robot_body.reset_robot(target_pose=safe_pose)

            # ===== 步骤 4: 过渡到垂直复位姿态（手掌不变）=====
            self.send_feedback(goal_handle, 60, "正在过渡到垂直复位姿态...")
            reset_pose = np.array([
                *_LEFT_RESET_POSE,
                *_RIGHT_RESET_POSE,
                *hands,
            ])
            robot_body.reset_robot(target_pose=reset_pose)

            # ===== 步骤 5: 完成 =====
            self.send_feedback(goal_handle, 100, "放置完成复位，机器人已就绪")
            return TaskResult(True, error_code=ERR_SUCCESS, error_message=ERR_MSG[ERR_SUCCESS])

        except Exception as e:
            err_code = ERR_FINISH_PLACE_FAILED
            err_msg = f"{ERR_MSG[err_code]}: {str(e)}"
            self.send_feedback(goal_handle, 0, err_msg)
            return TaskResult(False, error_code=err_code, error_message=err_msg)
