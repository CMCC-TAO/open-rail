"""
init place 任务 - 放置前过渡到安全位姿（双臂和双手）

两段式过渡（与 task_init_grasp.py 对称）:
  1. reset_robot 到安全抬臂姿态（保持当前手掌状态，避免碰撞桌子）
  2. reset_robot 到默认抓取姿态（保持当前手掌状态，为放置做准备）
"""

import sys
import os
import numpy as np
from typing import Any

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.action_base import AbstractTaskHandler, TaskResult, ERR_SUCCESS, ERR_INIT_PLACE_FAILED, ERR_MSG


def _get_default_pose(context):
    """从配置中获取默认抓取姿态"""
    robot_type = context.config.robots.type.value
    robot_cfg = getattr(context.config.robots, robot_type)
    return np.array(robot_cfg.reset_robot_pos, dtype=np.float64)


# ==============================================
# 安全中间姿态（与 task_init_grasp.py 一致）
# ==============================================
_SAFE_LEFT_ARM = np.array([1.5,   0.5, 0.0, -0.8, 0.0, -0.8,  0.0])
_SAFE_RIGHT_ARM = np.array([1.5, -0.5, 0.0, -0.8, 0.0, -0.8,  0.0])


class InitPlaceHandler(AbstractTaskHandler):
    """'init place' 任务处理器

    流程:
        1. 获取当前手掌状态（保持物体不松手）
        2. reset_robot 到安全抬臂姿态（手掌不变）
        3. reset_robot 到默认抓取姿态（手掌不变，为放置做准备）
        4. 完成
    """

    @property
    def task_name(self) -> str:
        return "init place"

    def _get_current_hands(self, robot_body) -> np.ndarray:
        """获取当前 12 维手掌状态（最新下发量），保持抓取物体不松手"""
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
        default_pose = _get_default_pose(context)
        try:
            # ===== 步骤 1: 确认机器人连接 =====
            self.send_feedback(goal_handle, 10, "正在确认机器人连接...")

            # ===== 检查手掌数据是否可用 =====
            self.send_feedback(goal_handle, 15, "正在检查机器人手掌数据...")
            robot = robot_body.robot
            lh = robot.latest_left_hand_action
            rh = robot.latest_right_hand_action
            if lh is None or rh is None:
                err_msg = f"{ERR_MSG[ERR_INIT_PLACE_FAILED]}: 未收到机器人手掌数据"
                self.send_feedback(goal_handle, 0, err_msg)
                return TaskResult(False, error_code=ERR_INIT_PLACE_FAILED, error_message=err_msg)

            # ===== 步骤 2: 获取当前手掌状态（保持抓取物体）=====
            hands = self._get_current_hands(robot_body)

            # ===== 步骤 3: 过渡到安全中间姿态（抬臂，手掌不变）=====
            self.send_feedback(goal_handle, 30, "正在过渡到安全中间姿态...")
            safe_pose = np.array([
                *_SAFE_LEFT_ARM,
                *_SAFE_RIGHT_ARM,
                *hands,
            ])
            robot_body.reset_robot(target_pose=safe_pose)

            # ===== 步骤 4: 过渡到默认抓取姿态（手掌不变）=====
            self.send_feedback(goal_handle, 60, "正在过渡到默认抓取姿态...")
            target_pose = np.array([
                *default_pose[0:7],
                *default_pose[7:14],
                *hands,
            ])
            robot_body.reset_robot(target_pose=target_pose)

            # ===== 步骤 5: 完成 =====
            self.send_feedback(goal_handle, 100, "放置初始化完成，机器人已就绪")
            return TaskResult(True, error_code=ERR_SUCCESS, error_message=ERR_MSG[ERR_SUCCESS])

        except Exception as e:
            err_code = ERR_INIT_PLACE_FAILED
            err_msg = f"{ERR_MSG[err_code]}: {str(e)}"
            self.send_feedback(goal_handle, 0, err_msg)
            return TaskResult(False, error_code=err_code, error_message=err_msg)
