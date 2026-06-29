"""
init grasp 任务 - 机器人从当前状态过渡到准备抓取姿态（双臂和双手）

共两段:
  1. reset_robot 到安全抬臂握拳姿态（避免碰撞桌子）
  2. reset_robot 到准备抓取姿态
"""

import sys
import os
import numpy as np
from typing import Any

# 项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.action_base import AbstractTaskHandler, TaskResult, ERR_SUCCESS, ERR_INIT_GRASP_FAILED, ERR_MSG


# ==============================================
# 准备抓取姿态从 robots_conf.py 的 reset_robot_pos 读取
# ==============================================


def _get_init_grasp_pose(context):
    """从配置中获取准备抓取姿态"""
    robot_type = context.config.robots.type.value
    robot_cfg = getattr(context.config.robots, robot_type)
    return np.array(robot_cfg.reset_robot_pos, dtype=np.float64)


# ==============================================
# 安全中间姿态
# ==============================================
_SAFE_LEFT_ARM = np.array([1.5,   0.5, 0.0, -0.8, 0.0, -0.8,  0.0])
_SAFE_RIGHT_ARM = np.array([1.5, -0.5, 0.0, -0.8, 0.0, -0.8,  0.0])


class InitGraspHandler(AbstractTaskHandler):
    """'init grasp' 任务处理器

    流程:
        1. 建立 RobotBody 连接
        2. reset_robot 到安全抬臂握拳姿态
        3. reset_robot 到准备抓取姿态
        4. 完成
    """

    @property
    def task_name(self) -> str:
        return "init grasp"

    def execute(self, goal_handle, params: dict, context: Any) -> TaskResult:
        robot_body = context.robot_body
        init_grasp_pose = _get_init_grasp_pose(context)
        try:
            # ===== 步骤 1: 确认机器人连接 =====
            self.send_feedback(goal_handle, 10, "正在确认机器人连接...")

            # ===== 检查手掌数据是否可用 =====
            self.send_feedback(goal_handle, 15, "正在检查机器人手掌数据...")
            robot = robot_body.robot
            lh = robot.latest_left_hand_action
            rh = robot.latest_right_hand_action
            if lh is None or rh is None:
                err_msg = f"{ERR_MSG[ERR_INIT_GRASP_FAILED]}: 未收到机器人手掌数据"
                self.send_feedback(goal_handle, 0, err_msg)
                return TaskResult(False, error_code=ERR_INIT_GRASP_FAILED, error_message=err_msg)

            # ===== 步骤 2: 过渡到安全中间姿态（抬臂握拳）=====
            self.send_feedback(goal_handle, 20, "正在过渡到安全中间姿态...")

            safe_pose = np.array([
                # Left arm: raised
                *_SAFE_LEFT_ARM,
                # Right arm: raised
                *_SAFE_RIGHT_ARM,
                # Both hands: fist (1000)
                1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0,
                1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0,
            ])
            robot_body.reset_robot(target_pose=safe_pose)

            # ===== 步骤 3: 过渡到准备抓取姿态 =====
            self.send_feedback(goal_handle, 50, "正在过渡到准备抓取姿态...")
            robot_body.reset_robot(target_pose=init_grasp_pose)

            # ===== 步骤 4: 完成 =====
            context._initialized = True
            self.send_feedback(goal_handle, 100, "机器人已就绪，准备抓取姿态完成")
            return TaskResult(True, error_code=ERR_SUCCESS, error_message=ERR_MSG[ERR_SUCCESS])

        except Exception as e:
            err_code = ERR_INIT_GRASP_FAILED
            err_msg = f"{ERR_MSG[err_code]}: {str(e)}"
            self.send_feedback(goal_handle, 0, err_msg)
            return TaskResult(False, error_code=err_code, error_message=err_msg)

        # 无需 finally 清理 — robot_body 由 dispatcher 统一管理
