"""
init grasp 任务 - 机器人从当前状态过渡到准备抓取姿态（双臂和双手）

共四段:
  1. reset_robot 到安全抬臂握拳姿态（避免碰撞桌子）
  2. reset_robot 到第二个中间过渡姿态（落臂但保持收手）
  3. reset_robot 到第三个中间过渡姿态（进一步落臂）
  4. reset_robot 到准备抓取姿态
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
# _SAFE_LEFT_ARM = np.array([1.5,   0.5, 0.0, -0.8, 0.0, -0.8,  0.0])
# _SAFE_RIGHT_ARM = np.array([1.5, -0.5, 0.0, -0.8, 0.0, -0.8,  0.0])
_SAFE_LEFT_ARM = np.array([1.2,   0.3, 0.0, -0.4, 0.0, -0.5,  0.0])
_SAFE_RIGHT_ARM = np.array([1.2, -0.3, 0.0, -0.4, 0.0, -0.5,  0.0])


# ==============================================
# 第二个中间过渡姿态（只有这个文件使用）
# ==============================================
_MID_LEFT_ARM = np.array([0.33,   0.15, -0.15, -0.0,  0.0, -0.3,  0.7])
_MID_RIGHT_ARM = np.array([0.33, -0.15,  0.15, -0.0,  0.0, -0.3, -0.7])


# ==============================================
# 第三个中间过渡姿态 (只有这个文件使用)
# ==============================================
_MID_LEFT_ARM_2 = np.array([0.30,   0.15, -0.30, -0.1,  0.0, -0.3,  0.0])
_MID_RIGHT_ARM_2 = np.array([0.30, -0.15,  0.30, -0.1,  0.0, -0.3, -0.0])


class InitGraspHandler(AbstractTaskHandler):
    """'grasp' task + target='init' 任务处理器

    流程:
        1. 建立 RobotBody 连接
        2. reset_robot 到安全抬臂握拳姿态
        3. reset_robot 到第二个中间过渡姿态（落臂但保持收手）
        4. reset_robot 到第三个中间过渡姿态（进一步落臂）
        5. reset_robot 到准备抓取姿态
        6. 创建 VLA 组件并启动 obs+infer
        7. 完成
    """

    @property
    def task_name(self) -> str:
        return "grasp"

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
            robot_body.reset_robot(target_pose=safe_pose,
                                   max_velocity=1.5, max_acceleration=1.0, max_jerk=3.0)

            # ===== 步骤 3: 过渡到第二个中间姿态（落臂但保持收手）=====
            self.send_feedback(goal_handle, 35, "正在过渡到第二中间姿态...")

            mid_pose = np.array([
                # Left arm
                *_MID_LEFT_ARM,
                # Right arm
                *_MID_RIGHT_ARM,
                # Both hands: fist (1000)
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ])
            robot_body.reset_robot(target_pose=mid_pose,
                                   max_velocity=1.5, max_acceleration=1.0, max_jerk=3.0)

            # ===== 步骤 4: 过渡到第三个中间姿态（进一步落臂）=====
            self.send_feedback(goal_handle, 42, "正在过渡到第三中间姿态...")

            mid_pose_2 = np.array([
                # Left arm
                *_MID_LEFT_ARM_2,
                # Right arm
                *_MID_RIGHT_ARM_2,
                # Both hands: fist (1000)
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ])
            robot_body.reset_robot(target_pose=mid_pose_2,
                                   max_velocity=1.5, max_acceleration=1.0, max_jerk=3.0)

            # ===== 步骤 5: 过渡到准备抓取姿态 =====
            self.send_feedback(goal_handle, 50, "正在过渡到准备抓取姿态...")
            robot_body.reset_robot(target_pose=init_grasp_pose,
                                   max_velocity=1.5, max_acceleration=1.0, max_jerk=3.0)

            # ===== 步骤 6: 创建 VLA 组件并启动 obs+infer =====
            self.send_feedback(goal_handle, 70, "正在创建 VLA 推理组件...")
            components = context.ensure_vla_components()
            vla_client = components["vla_client"]

            # 启动 observe 和 inference 线程（多次调用安全，内部有 is_alive 保护）
            self.send_feedback(goal_handle, 85, "正在启动观测和推理线程...")
            vla_client.start_observe()
            vla_client.start_inference()
            vla_client.start_visualize()
            vla_client.is_running_action = True
            print(f'[InitGraspHandler] VLA obs+infer threads started')

            # ===== 步骤 7: 完成（不销毁组件，由 finish_grasp 清理）=====
            context._initialized = True
            self.send_feedback(goal_handle, 100, "机器人已就绪，VLA 观测推理已启动")
            return TaskResult(True, error_code=ERR_SUCCESS, error_message=ERR_MSG[ERR_SUCCESS])

        except Exception as e:
            err_code = ERR_INIT_GRASP_FAILED
            err_msg = f"{ERR_MSG[err_code]}: {str(e)}"
            self.send_feedback(goal_handle, 0, err_msg)
            return TaskResult(False, error_code=err_code, error_message=err_msg)

        # 无需 finally 清理 — robot_body 由 dispatcher 统一管理
