"""
统一初始化任务 - 机器人从当前状态过渡到准备姿态（双臂和双手）

通过 (task, target, waypoint) 组合键选择点位序列:
    key = f"{task}-{target}-{waypoint}"

内置组合键 → 点位序列（点位构建器定义在下方 POSE_BUILDERS）:
  - "zero-init-none":      ["init"]                    # 1 点: 直接一步到位
  - "grasp-init-none":     ["safe", "mid1", "mid2", "init"]   # 4 点: 完整过渡
  - "clean-init-none":     ["safe", "init"]            # 2 点: 去掉两个中间过渡
  - "grasp-init-drainer":  ["safe", "init"]            # 2 点: 去掉两个中间过渡

新增任务时只需在 INIT_POSE_SEQUENCES 中添加组合键与点位序列，
在 INIT_LANGUAGE_MAP 中配置对应的语言指令（缺省不设置，沿用客户端默认指令），
并在 action_dispatcher.py 中注册对应的 "task:init" key。

流程:
  1. 确认机器人连接并检查手掌数据
  2. 按序列依次 reset_robot 到各点位
  3. 创建 VLA 组件并启动 obs+infer
  4. 完成（不销毁组件，由对应 finish_* 清理）
"""

import sys
import os
import numpy as np
from typing import Any, Callable

# 项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.action_base import (
    AbstractTaskHandler, TaskResult, ERR_SUCCESS, ERR_MSG,
    ERR_INIT_GRASP_FAILED, ERR_INIT_CLEAN_FAILED,
)
from action_server.task_clean import CLEAN_LANGUAGE_INSTRUCTION
from action_server.task_grasp import TARGET_LANGUAGE_MAP


# ==============================================
# 点位定义（写在文件顶部，便于配置）
# ==============================================
# 准备姿态从 robots_conf.py 的 reset_robot_pos 读取
def _get_init_grasp_pose(context):
    """从配置中获取准备姿态"""
    robot_type = context.config.robots.type.value
    robot_cfg = getattr(context.config.robots, robot_type)
    return np.array(robot_cfg.reset_robot_pos, dtype=np.float64)


# 安全抬臂握拳姿态（避免碰撞桌子）
_SAFE_LEFT_ARM = np.array([1.2,   0.3, 0.0, -0.4, 0.0, -0.5,  0.0])
_SAFE_RIGHT_ARM = np.array([1.2, -0.3, 0.0, -0.4, 0.0, -0.5,  0.0])

# 第二中间过渡姿态（落臂但保持收手）
_MID_LEFT_ARM = np.array([0.33,   0.15, -0.15, -0.0,  0.0, -0.3,  0.7])
_MID_RIGHT_ARM = np.array([0.33, -0.15,  0.15, -0.0,  0.0, -0.3, -0.7])

# 第三中间过渡姿态（进一步落臂）
_MID_LEFT_ARM_2 = np.array([0.30,   0.15, -0.30, -0.1,  0.0, -0.3,  0.0])
_MID_RIGHT_ARM_2 = np.array([0.30, -0.15,  0.30, -0.1,  0.0, -0.3, -0.0])


# ==============================================
# 点位构建器（统一签名: builder(context) -> np.ndarray 26维）
# ==============================================
def _build_safe_pose(_context):
    """安全抬臂握拳: 双臂抬起 + 双手全握拳(1000)"""
    return np.array([
        *_SAFE_LEFT_ARM, *_SAFE_RIGHT_ARM,
        1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0,
        1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0,
    ])


def _build_mid_pose(_context):
    """第二中间过渡: 落臂 + 双手张开(0)"""
    return np.array([
        *_MID_LEFT_ARM, *_MID_RIGHT_ARM,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    ])


def _build_mid_pose_2(_context):
    """第三中间过渡: 进一步落臂 + 双手张开(0)"""
    return np.array([
        *_MID_LEFT_ARM_2, *_MID_RIGHT_ARM_2,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    ])


def _build_init_pose(context):
    """准备姿态: 从配置读取（含手掌）"""
    return _get_init_grasp_pose(context)


POSE_BUILDERS: dict[str, Callable[[Any], Any]] = {
    "safe": _build_safe_pose,
    "mid1": _build_mid_pose,
    "mid2": _build_mid_pose_2,
    "init": _build_init_pose,
}


# ==============================================
# 组合键 → 点位序列
# ==============================================
INIT_POSE_SEQUENCES: dict[str, list[str]] = {
    "zero-init-none":     ["init"],
    "grasp-init-none":    ["safe", "mid1", "mid2", "init"],
    "clean-init-none":    ["safe", "init"],
    "grasp-init-drainer": ["safe", "init"],
}


# ==============================================
# 组合键 → 语言指令（init 启动推理线程时设置到 VLA，新 push 的 obs 会携带该指令）
# ==============================================
# 直接引用 task_grasp.TARGET_LANGUAGE_MAP / task_clean.CLEAN_LANGUAGE_INSTRUCTION，
# 语言文案统一维护在对应任务文件里；也可以直接写死字符串覆盖。
INIT_LANGUAGE_MAP: dict[str, str] = {
    "zero-init-none":     TARGET_LANGUAGE_MAP["one water"],   # "use one hand to grab one bottle from a pile of drinks."
    "grasp-init-none":    TARGET_LANGUAGE_MAP["one water"],   # "use one hand to grab one bottle from a pile of drinks."
    "clean-init-none":    CLEAN_LANGUAGE_INSTRUCTION,         # 桌面清洁多步骤指令（见 task_clean.py）
    "grasp-init-drainer": TARGET_LANGUAGE_MAP["drainer"],     # "Lift up the drainer in front of you with both hands and keep it balanced."
}


class InitHandler(AbstractTaskHandler):
    """统一 init 任务处理器 — 按组合键 f"{task}-{target}-{waypoint}" 查询点位序列

    适用于: task="grasp" / "clean" / "zero" 且 target="init"。
    不同任务通过 INIT_POSE_SEQUENCES 配置各自的点位序列。
    """

    @property
    def task_name(self) -> str:
        return "init"

    def execute(self, goal_handle, params: dict[str, Any], context: Any) -> TaskResult:
        robot_body = context.robot_body
        task_name = params.get('task', '')

        # 按 task 选择错误码，保持与旧实现一致
        err_code = ERR_INIT_CLEAN_FAILED if task_name == "clean" else ERR_INIT_GRASP_FAILED

        # 组合键
        key = f"{task_name}-{params.get('target', '')}-{params.get('waypoint', '')}"
        sequence = INIT_POSE_SEQUENCES.get(key)
        if sequence is None:
            err_msg = f"{ERR_MSG[err_code]}: 未知初始化组合 key='{key}'，可用: {list(INIT_POSE_SEQUENCES.keys())}"
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

            # ===== 步骤 2: 按序列依次过渡到各点位 =====
            total = len(sequence)
            for idx, pose_name in enumerate(sequence):
                progress = 20 + int((idx + 1) / total * 45)
                self.send_feedback(goal_handle, progress,
                                   f"正在过渡到点位[{idx + 1}/{total}] ({pose_name})...")
                pose = POSE_BUILDERS[pose_name](context)
                robot_body.reset_robot(target_pose=pose,
                                       max_velocity=1.5, max_acceleration=1.0, max_jerk=3.0)

            # ===== 步骤 3: 创建 VLA 组件并启动 obs+infer =====
            self.send_feedback(goal_handle, 70, "正在创建 VLA 推理组件...")
            components = context.ensure_vla_components()
            vla_client = components["vla_client"]

            # 设置与组合键对应的语言指令（须在 start_observe 之前设置，
            # 之后 push 的 obs 会携带该指令进入推理）
            instruction = INIT_LANGUAGE_MAP.get(key)
            if instruction:
                vla_client.task_language_manager.currt_language_instruction = instruction
                print(f'[InitHandler] language instruction set (key={key}): {instruction}')
            else:
                print(f'[InitHandler] keep default language instruction (key={key})')

            # 启动 observe 和 inference 线程（多次调用安全，内部有 is_alive 保护）
            self.send_feedback(goal_handle, 85, "正在启动观测和推理线程...")
            vla_client.start_observe()
            vla_client.start_inference()
            vla_client.start_visualize()
            vla_client.is_running_action = True
            print(f'[InitHandler] VLA obs+infer threads started (key={key})')

            # ===== 步骤 4: 完成（不销毁组件，由对应 finish_* 清理）=====
            context._initialized = True
            self.send_feedback(goal_handle, 100, "机器人已就绪，VLA 观测推理已启动")
            return TaskResult(True, error_code=ERR_SUCCESS, error_message=ERR_MSG[ERR_SUCCESS])

        except Exception as e:
            err_msg = f"{ERR_MSG[err_code]}: {str(e)}"
            self.send_feedback(goal_handle, 0, err_msg)
            return TaskResult(False, error_code=err_code, error_message=err_msg)

        # 无需 finally 清理 — robot_body 由 dispatcher 统一管理
