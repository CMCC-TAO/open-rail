"""
init grasp 任务 - 机器人从当前状态过渡到准备抓取姿态（双臂和双手）

复用 RobotBody.reset_robot() 实现轨迹过渡，自身只负责定义目标姿态。
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


class InitGraspHandler(AbstractTaskHandler):
    """'init grasp' 任务处理器

    流程:
        1. 建立 RobotBody 连接
        2. 读取当前机器人状态
        3. 规划平滑轨迹并过渡到准备抓取姿态
        4. 清理资源
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

            # ===== 步骤 2: 过渡到准备抓取姿态 =====
            # 关闭相对限幅，让大范围期望轨迹可以完整下发
            robot_body.robot.enable_relative_clamp = False
            try:
                self.send_feedback(goal_handle, 30, "正在过渡到准备抓取姿态...")
                robot_body.reset_robot(target_pose=init_grasp_pose)
            finally:
                robot_body.robot.enable_relative_clamp = True

            # ===== 步骤 3: 完成 =====
            context._initialized = True
            self.send_feedback(goal_handle, 100, "机器人已就绪，准备抓取姿态完成")
            return TaskResult(True, error_code=ERR_SUCCESS, error_message=ERR_MSG[ERR_SUCCESS])

        except Exception as e:
            err_code = ERR_INIT_GRASP_FAILED
            err_msg = f"{ERR_MSG[err_code]}: {str(e)}"
            self.send_feedback(goal_handle, 0, err_msg)
            return TaskResult(False, error_code=err_code, error_message=err_msg)

        # 无需 finally 清理 — robot_body 由 dispatcher 统一管理
