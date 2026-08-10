"""
统一完成复位任务 - 任务完成后过渡到安全/复位姿态（双臂和双手）

通过 (task, target, waypoint) 组合键选择点位序列:
    key = f"{task}-{target}-{waypoint}"

内置组合键 → 点位序列（点位构建器定义在下方 POSE_BUILDERS）:
  - "grasp-finish-none":  ["safe", "reset"]   # 2 点: 安全抬臂 → 垂直复位
  - "clean-finish-none":  ["safe", "reset"]   # 2 点: 与 grasp 相同（后续可拆）

新增任务时只需在 FINISH_POSE_SEQUENCES 中添加组合键与点位序列，
并在 action_dispatcher.py 中注册对应的 "task:finish" key。

流程:
  1. 确认机器人连接并检查手掌数据
  2. 按序列依次 reset_robot 到各点位（保持当前手掌状态，避免松手掉物）
  3. 清理 VLA 组件（由 init 创建，finish 统一销毁）
  4. 完成
"""

import sys
import os
import numpy as np
from typing import Any, Callable

# 项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.task_init import _SAFE_LEFT_ARM, _SAFE_RIGHT_ARM
from action_server.task_reset import _LEFT_RESET_POSE, _RIGHT_RESET_POSE
from action_server.action_base import (
    AbstractTaskHandler, TaskResult, ERR_SUCCESS, ERR_MSG,
    ERR_FINISH_GRASP_FAILED, ERR_FINISH_CLEAN_FAILED,
)


# ==============================================
# 点位定义（写在文件顶部，便于配置）
# ==============================================
# 安全抬臂姿态（避免碰撞桌子，与 task_init 共用）
# _SAFE_LEFT_ARM / _SAFE_RIGHT_ARM 从 task_init 导入

# 垂直复位姿态（与 task_reset 共用）
# _LEFT_RESET_POSE / _RIGHT_RESET_POSE 从 task_reset 导入

# 平衡点姿态（7 关节，弧度；后续调试按需修改）
_BALANCE_LEFT_ARM  = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
_BALANCE_RIGHT_ARM = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])


# ==============================================
# 点位构建器（统一签名: builder(context) -> np.ndarray 26维）
# ==============================================
def _get_current_hands(context) -> np.ndarray:
    """获取当前 12 维手掌状态（最新下发量），保持抓取物体不松手"""
    robot_body = context.robot_body
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
    # 兜底：全开（安全值，松开任何意外抓取）
    return np.zeros(12, dtype=float)


def _build_safe_pose(context):
    """安全抬臂姿态: 双臂抬起 + 保持当前手掌状态"""
    return np.array([
        *_SAFE_LEFT_ARM, *_SAFE_RIGHT_ARM,
        *_get_current_hands(context),
    ])


def _build_reset_pose(context):
    """垂直复位姿态: 双臂复位 + 保持当前手掌状态"""
    return np.array([
        *_LEFT_RESET_POSE, *_RIGHT_RESET_POSE,
        *_get_current_hands(context),
    ])


def _build_balance_pose(context):
    """平衡点姿态: 双臂到平衡点(默认全零) + 保持当前手掌状态"""
    return np.array([
        *_BALANCE_LEFT_ARM, *_BALANCE_RIGHT_ARM,
        *_get_current_hands(context),
    ])


POSE_BUILDERS: dict[str, Callable[[Any], Any]] = {
    "safe": _build_safe_pose,
    "reset": _build_reset_pose,
    "balance": _build_balance_pose,
}


# ==============================================
# 组合键 → 点位序列
# ==============================================
FINISH_POSE_SEQUENCES: dict[str, list[str]] = {
    "grasp-finish-none": ["safe", "reset"],
    "clean-finish-none": ["safe", "reset"],
    "grasp-finish-drainer": ["balance"],
}


class FinishHandler(AbstractTaskHandler):
    """统一 finish 任务处理器 — 按组合键 f"{task}-{target}-{waypoint}" 查询点位序列

    适用于: task="grasp" / "clean" 且 target="finish"。
    不同任务通过 FINISH_POSE_SEQUENCES 配置各自的点位序列。
    """

    @property
    def task_name(self) -> str:
        return "finish"

    def execute(self, goal_handle, params: dict[str, Any], context: Any) -> TaskResult:
        robot_body = context.robot_body
        task_name = params.get('task', '')

        # 按 task 选择错误码，保持与旧实现一致
        err_code = ERR_FINISH_CLEAN_FAILED if task_name == "clean" else ERR_FINISH_GRASP_FAILED

        # 组合键
        key = f"{task_name}-{params.get('target', '')}-{params.get('waypoint', '')}"
        sequence = FINISH_POSE_SEQUENCES.get(key)
        if sequence is None:
            err_msg = f"{ERR_MSG[err_code]}: 未知完成复位组合 key='{key}'，可用: {list(FINISH_POSE_SEQUENCES.keys())}"
            self.send_feedback(goal_handle, 0, err_msg)
            return TaskResult(False, error_code=err_code, error_message=err_msg)

        try:
            # ===== 步骤 1: 确认机器人连接 =====
            self.send_feedback(goal_handle, 10, "正在确认机器人连接...")

            # ===== 检查手掌数据是否可用 =====
            self.send_feedback(goal_handle, 15, "正在检查机器人手掌数据...")
            robot = robot_body.robot
            lh = robot.latest_left_hand_action
            rh = robot.latest_right_hand_action
            if lh is None or rh is None:
                err_msg = f"{ERR_MSG[err_code]}: 未收到机器人手掌数据"
                self.send_feedback(goal_handle, 0, err_msg)
                return TaskResult(False, error_code=err_code, error_message=err_msg)

            # ===== 步骤 2: 按序列依次过渡到各点位（保持当前手掌状态）=====
            total = len(sequence)
            for idx, pose_name in enumerate(sequence):
                progress = 30 + int((idx + 1) / total * 40)
                self.send_feedback(goal_handle, progress,
                                   f"正在过渡到点位[{idx + 1}/{total}] ({pose_name})...")
                pose = POSE_BUILDERS[pose_name](context)
                robot_body.reset_robot(target_pose=pose,
                                       max_velocity=1.5, max_acceleration=1.0, max_jerk=3.0)

            # ===== 步骤 3: 清理 VLA 组件（init 创建，finish 统一销毁）=====
            self.send_feedback(goal_handle, 85, "正在清理 VLA 推理资源...")
            context.clear_vla_components()
            context._initialized = False

            # ===== 步骤 4: 完成 =====
            self.send_feedback(goal_handle, 100, "完成复位，VLA 资源已清理，机器人已就绪")
            return TaskResult(True, error_code=ERR_SUCCESS, error_message=ERR_MSG[ERR_SUCCESS])

        except Exception as e:
            err_msg = f"{ERR_MSG[err_code]}: {str(e)}"
            self.send_feedback(goal_handle, 0, err_msg)
            return TaskResult(False, error_code=err_code, error_message=err_msg)
