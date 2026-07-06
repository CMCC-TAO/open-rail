"""
init zero 任务 - 机器人直接从当前状态过渡到默认准备姿态（不加中间过渡）

与 init grasp 的区别：不经过安全中间姿态（抬臂握拳），直接一步到目标位姿。
最终点位与 init grasp 的终点完全一致。
"""

import sys
import os
import numpy as np
from typing import Any

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.action_base import AbstractTaskHandler, TaskResult, ERR_SUCCESS, ERR_INIT_GRASP_FAILED, ERR_MSG


def _get_init_grasp_pose(context):
    """从配置中获取准备抓取姿态（与 task_init_grasp.py 完全相同）"""
    robot_type = context.config.robots.type.value
    robot_cfg = getattr(context.config.robots, robot_type)
    return np.array(robot_cfg.reset_robot_pos, dtype=np.float64)


class InitZeroHandler(AbstractTaskHandler):
    """'init zero' 任务处理器

    流程:
        1. 确认机器人连接
        2. reset_robot 直接到默认准备姿态（无中间过渡，终点 = init grasp 终点）
    """

    @property
    def task_name(self) -> str:
        return "init zero"

    def execute(self, goal_handle, params: dict, context: Any) -> TaskResult:
        robot_body = context.robot_body
        target_pose = _get_init_grasp_pose(context)
        try:
            self.send_feedback(goal_handle, 10, "正在确认机器人连接...")
            self.send_feedback(goal_handle, 30, "正在过渡到默认准备姿态（无中间过渡）...")
            robot_body.reset_robot(target_pose=target_pose)

            self.send_feedback(goal_handle, 100, "机器人已就绪，准备姿态完成（直连模式）")
            return TaskResult(True, error_code=ERR_SUCCESS, error_message=ERR_MSG[ERR_SUCCESS])

        except Exception as e:
            err_code = ERR_INIT_GRASP_FAILED
            err_msg = f"{ERR_MSG[err_code]}: {str(e)}"
            self.send_feedback(goal_handle, 0, err_msg)
            return TaskResult(False, error_code=err_code, error_message=err_msg)
