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

from action_server.action_base import AbstractTaskHandler, TaskResult

# ==============================================
# 准备抓取姿态 (26 维)
#
# action[0:7]   -> 左臂 (7 关节)
# action[7:14]  -> 右臂 (7 关节)
# action[14:20] -> 左手 (6 手指)
# action[20:26] -> 右手 (6 手指)
#
# 此姿态使机器人双臂前伸、微外展、肘部微屈，
# 双手微微张开，处于"准备抓取"状态。
# ==============================================
INIT_GRASP_POSE = np.array([
    # ===== 左臂 (7) =====
    # left_shoulder_pitch, left_shoulder_roll, left_shoulder_yaw,
    # left_elbow, left_wrist_roll, left_wrist_pitch, left_wrist_yaw
    0.30,    # shoulder_pitch: 前伸  (限幅 -0.80~0.80)
    0.15,    # shoulder_roll:  微外展 (限幅 -0.15~0.25)
    -0.15,   # shoulder_yaw:   微前旋 (限幅 -0.50~0.36)
    -0.30,   # elbow:          微屈   (限幅 -0.50~1.35)
    0.0,     # wrist_roll:     中立   (限幅 -0.50~0.86)
    -0.30,   # wrist_pitch:    微俯   (限幅 -1.36~0.40)
    0.0,     # wrist_yaw:      中立   (限幅 -0.58~1.16)

    # ===== 右臂 (7) ===== (镜像)
    0.30,    # shoulder_pitch: 前伸  (限幅 -0.80~0.80)
    -0.15,   # shoulder_roll:  微外展 (限幅 -0.52~0.10)
    0.15,    # shoulder_yaw:   微前旋 (限幅 -0.48~0.42)
    -0.30,   # elbow:          微屈   (限幅 -0.70~1.30)
    0.0,     # wrist_roll:     中立   (限幅 -0.73~0.45)
    -0.30,   # wrist_pitch:    微俯   (限幅 -1.28~0.36)
    0.0,     # wrist_yaw:      中立   (限幅 -0.80~0.60)

    # ===== 左手 (6) ===== (张开)
    # little_finger, ring_finger, middle_finger, index_finger,
    # thumb_bend, thumb_rotate
    100.0,   # little_finger
    100.0,   # ring_finger
    100.0,   # middle_finger
    100.0,   # index_finger
    150.0,   # thumb_bend:   微弯
    50.0,    # thumb_rotate: 中立

    # ===== 右手 (6) ===== (张开)
    100.0,   # little_finger
    100.0,   # ring_finger
    100.0,   # middle_finger
    100.0,   # index_finger
    150.0,   # thumb_bend:   微弯
    50.0,    # thumb_rotate: 中立
], dtype=np.float64)


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
        try:
            # ===== 步骤 1: 确认机器人连接 =====
            self.send_feedback(goal_handle, 10, "正在确认机器人连接...")

            # ===== 步骤 2: 过渡到准备抓取姿态 =====
            # 关闭相对限幅，让大范围期望轨迹可以完整下发
            robot_body.robot.enable_relative_clamp = False
            try:
                self.send_feedback(goal_handle, 30, "正在过渡到准备抓取姿态...")
                robot_body.reset_robot(target_pose=INIT_GRASP_POSE)
            finally:
                robot_body.robot.enable_relative_clamp = True

            # ===== 步骤 3: 完成 =====
            context._initialized = True
            self.send_feedback(goal_handle, 100, "机器人已就绪，准备抓取姿态完成")
            return TaskResult(True)

        except Exception as e:
            err_msg = f"init grasp 执行失败: {str(e)}"
            self.send_feedback(goal_handle, 0, err_msg, feedback_code=99)
            return TaskResult(False, error_code=99, error_message=err_msg)

        # 无需 finally 清理 — robot_body 由 dispatcher 统一管理
