"""
init grasp 任务 - 机器人从当前状态过渡到准备抓取姿态（双臂和双手）
"""

import sys
import os
import time
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


def _linear_interpolate(current: np.ndarray, target: np.ndarray,
                        num_steps: int = 800) -> list:
    """生成线性插值轨迹（按固定步数均分）

    Args:
        current:   当前关节角度 (ndarray)
        target:    目标关节角度 (ndarray)
        num_steps: 插值总步数

    Returns:
        list[ndarray]: 共 num_steps 个插值点
    """
    if num_steps < 1:
        return [target.copy()]

    displacement = target - current
    max_disp = float(np.max(np.abs(displacement)))

    # 差异极小，直接返回目标
    if max_disp < 1e-6:
        return [target.copy()]

    return [
        current + (i / num_steps) * displacement
        for i in range(1, num_steps + 1)
    ]


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
            self.send_feedback(goal_handle, 5, "正在确认机器人连接...")
            self.send_feedback(goal_handle, 15, "机器人连接成功")

            # ===== 步骤 2: 读取当前状态 =====
            self.send_feedback(goal_handle, 25, "正在读取当前关节状态...")

            obs = robot_body.retrieve_observation()
            if obs is None:
                # 重试一次
                time.sleep(0.5)
                obs = robot_body.retrieve_observation()

            if obs is None:
                err_msg = "无法获取机器人观测数据（状态/图像未就绪）"
                self.send_feedback(goal_handle, 30, err_msg, feedback_code=1)
                return TaskResult(False, error_code=10, error_message=err_msg)

            current_state = obs["obs.state"]
            self.send_feedback(goal_handle, 35,
                               f"当前关节状态已读取, 维度={len(current_state)}")

            # ===== 步骤 3: 计算轨迹并执行过渡 =====
            self.send_feedback(goal_handle, 45, "正在规划过渡轨迹...")

            target_pose = INIT_GRASP_POSE.copy()
            current_arm = current_state[:14]
            target_arm = target_pose[:14]

            # 固定时长 3 秒，按 267Hz 下发
            DURATION = 3.0
            CONTROL_HZ = 267
            STEP_SLEEP = 1.0 / CONTROL_HZ
            NUM_STEPS = int(DURATION * CONTROL_HZ)

            # 判断是否需要平滑规划
            arm_diff = np.abs(current_arm - target_arm)
            if np.any(arm_diff > np.deg2rad(0.01)):
                # 关闭相对限幅，让大范围期望轨迹可以完整下发
                robot_body.robot.enable_relative_clamp = False
                try:
                    # 使用线性插值平滑过渡
                    trajs = _linear_interpolate(current_arm, target_arm,
                                                num_steps=NUM_STEPS)
                    n_points = len(trajs)
                    self.send_feedback(goal_handle, 50,
                                       f"轨迹规划完成, 3s@{CONTROL_HZ}Hz = {n_points} 个插值点")

                    # 逐步执行轨迹（带进度反馈）
                    report_interval = max(1, n_points // 20)  # 约每 5% 报告一次
                    for i, traj in enumerate(trajs):
                        tmp = target_pose.copy()
                        tmp[:14] = traj
                        robot_body.robot.send_robot_action(tmp)
                        time.sleep(STEP_SLEEP)

                        # 定期发送进度反馈
                        if i % report_interval == 0 or i == n_points - 1:
                            pct = int(50 + (i + 1) / n_points * 40)
                            self.send_feedback(
                                goal_handle, pct,
                                f"正在过渡到准备姿态... [{i + 1}/{n_points}]",
                            )
                finally:
                    # 恢复相对限幅，防止后续 VLA 推理输出失控
                    robot_body.robot.enable_relative_clamp = True
            else:
                # 差异很小，直接发送目标姿态
                robot_body.robot.send_robot_action(target_pose)
                self.send_feedback(goal_handle, 70, "关节已接近目标，直接定位")

            # 设置手部初始状态缓存（让后续控制知道手部最新位置）
            robot_body.robot.current_left_hand_state = target_pose[14:20]
            robot_body.robot.current_right_hand_state = target_pose[20:26]

            self.send_feedback(goal_handle, 92, "手部状态已同步")

            # ===== 步骤 4: 等待稳定 =====
            time.sleep(0.5)
            self.send_feedback(goal_handle, 100, "机器人已就绪，准备抓取姿态完成")

            return TaskResult(True)

        except Exception as e:
            err_msg = f"init grasp 执行失败: {str(e)}"
            self.send_feedback(goal_handle, 0, err_msg, feedback_code=99)
            return TaskResult(False, error_code=99, error_message=err_msg)

        # 无需 finally 清理 — robot_body 由 dispatcher 统一管理
