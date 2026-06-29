"""
抓取任务 - 根据 target 选择语言指令，调用 VLA 模型推理执行抓取

grasp 是一个大类，通过 target 字段区分具体的抓取动作（单手/双手、目标物体）。
"""

import sys
import os

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.action_base import (
    AbstractTaskHandler, TaskResult, run_vla_inference,
    ERR_MISSING_TARGET, ERR_UNKNOWN_TARGET,
    ERR_GRASP_TIMEOUT, ERR_ONE_HAND_FAILED,
    ERR_TWO_HAND_LEFT_FAILED, ERR_TWO_HAND_RIGHT_FAILED,
    ERR_TWO_HAND_BOTH_FAILED,
)


# ==============================================
# Target → 手数映射
# ==============================================
# 显式映射，不依赖字符串前缀判断
TARGET_HAND_MAP: dict[str, str] = {
    "one water": "one hand",
    "one Coca-Cola": "one hand",
    "two water": "two hand",
    "two Coca-Cola": "two hand",
}

# ==============================================
# target → 语言指令映射表
# ==============================================
# key 为 params.target（不区分大小写），value 为对应的语言指令
TARGET_LANGUAGE_MAP: dict[str, str] = {
    "one water": "Use one hand to grab one bottle from a pile of Wahaha drinks.",
    "one Coca-Cola": "Use one hand to grab one bottle from a pile of Coca-Cola drinks.",
    "two water": "Use both hands to grab the two nearest bottles from a pile of Wahaha drinks.",
    "two Coca-Cola": "Use both hands to grab the two nearest bottles from a pile of Coca-Cola drinks.",
}


def _get_language_instruction(target: str) -> str | None:
    """根据 target 名称获取语言指令

    Args:
        target: params 中的 target 字段值

    Returns:
        语言指令字符串，未找到则返回 None
    """
    return TARGET_LANGUAGE_MAP.get(target.strip())


def _reset_arms_to_default(robot_body, context, duration=2.0):
    """将双臂在指定时间内线性过渡到默认位置，手掌保持当前控制量不变

    Args:
        robot_body: RobotBody 实例
        context: VLAContext 实例
        duration: 过渡时间（秒）
    """
    import numpy as np
    import time

    # 获取默认位置配置
    robot_type = context.config.robots.type.value
    robot_cfg = getattr(context.config.robots, robot_type)
    default_pose = np.array(robot_cfg.reset_robot_pos, dtype=np.float64)

    # 获取当前机器人完整状态（26维）
    current_state = robot_body._get_reset_current_state()
    if current_state is None:
        print('[GraspHandler] WARN: 无法获取当前机器人状态，跳过手臂复位')
        return

    current_arm = current_state[:14]  # 当前手臂位置

    # 获取当前手掌控制量（保持手掌不变）
    # 优先从 robot 的缓存状态中读取（由 VLA 推理过程中更新）
    left_hand = getattr(robot_body.robot, 'current_left_hand_state', None)
    right_hand = getattr(robot_body.robot, 'current_right_hand_state', None)

    # 如果缓存中无手掌状态，从当前状态中取
    if left_hand is None and len(current_state) >= 20:
        left_hand = current_state[14:20]
    if right_hand is None and len(current_state) >= 26:
        right_hand = current_state[20:26]

    # 兜底使用默认姿态的手掌值
    if left_hand is None:
        left_hand = default_pose[14:20]
    if right_hand is None:
        right_hand = default_pose[20:26]

    left_hand = np.asarray(left_hand, dtype=float)
    right_hand = np.asarray(right_hand, dtype=float)

    target_arm = default_pose[:14]

    # 计算手臂距离，如果已经接近则跳过
    arm_dist = np.max(np.abs(current_arm - target_arm))
    if arm_dist < np.deg2rad(0.5):
        print(f'[GraspHandler] 手臂已在默认位置附近 (max_diff={arm_dist:.4f} rad)，跳过复位')
        return

    n_steps = max(1, int(duration / 0.02))  # 50Hz
    print(f'[GraspHandler] 双臂回归默认位置 ({duration}s, {n_steps} steps)...')

    for i in range(1, n_steps + 1):
        t = i / n_steps
        action = np.zeros(26)
        action[:14] = current_arm + t * (target_arm - current_arm)
        action[14:20] = left_hand
        action[20:26] = right_hand
        robot_body.robot.send_robot_action(action)
        time.sleep(0.02)

    print('[GraspHandler] 双臂回归默认位置完成')


class GraspHandler(AbstractTaskHandler):
    """'grasp' 任务处理器 — 抓取大类

    流程:
        1. 根据 params.target 查找对应的语言指令
        2. 创建 VLA 推理组件（vla_client 等）
        3. 调用 run_vla_inference() 执行推理
        4. 清理 per-task 组件
    """

    @property
    def task_name(self) -> str:
        return "grasp"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        # ===== 步骤 1: 解析 target 并获取语言指令 =====
        target = params.get("target", "")
        if not target:
            self.send_feedback(goal_handle, 0, "缺少 target 字段")
            return TaskResult(False, error_code=ERR_MISSING_TARGET,
                              error_message='Missing "target" field in params')

        instruction = _get_language_instruction(target)
        if instruction is None:
            self.send_feedback(goal_handle, 0,
                               f"未知 target: {target}")
            return TaskResult(False, error_code=ERR_UNKNOWN_TARGET,
                              error_message=f'Unknown target="{target}". '
                                            f'Supported: {list(TARGET_LANGUAGE_MAP.keys())}')

        self.send_feedback(goal_handle, 5,
                           f"抓取目标: {target}, 语言指令: {instruction}")

        # ===== 步骤 2: 创建 VLA 组件 =====
        components = context.create_vla_components()
        vla_client = components["vla_client"]
        robot_body = context.robot_body

        try:
            # ===== 步骤 3: 执行 VLA 推理 =====
            context._active_vla_client = vla_client  # 供 ObsDataBridge 读取进度
            result = run_vla_inference(
                goal_handle=goal_handle,
                vla_client=vla_client,
                language_instruction=instruction,
                robot_body=robot_body,
                reset_robot=not context._initialized,
                max_duration=30.0,
                thre_progress=1.5,  # 禁止 prob_progress 稳定性检测，靠 >80% 直接完成或 30s 超时
                stable_count_threshold=999,
            )

            # ===== 无论推理成功还是失败，先将双臂回归默认位置（手掌不变）=====
            _reset_arms_to_default(robot_body, context, duration=2.0)

            # ===== 步骤 4: 分析结果，结合手势判断具体错误 =====
            if not result.success:
                # 超时 → 映射为抓取超时错误码
                if result.error_code == 6:
                    return TaskResult(False, error_code=ERR_GRASP_TIMEOUT,
                                      error_message="Grasp task timed out")
                # 其他错误（复位失败、推理未启动、取消等）→ 原样透传
                return result

            # VLA 推理成功 (prob_progress > 80%)，验证实际抓握状态
            hand_type = TARGET_HAND_MAP.get(target.strip(), "one hand")
            grasp_state = context.grasp_detector.grasp_state  # [left, right]

            if hand_type == "one hand":
                if not (grasp_state[0] or grasp_state[1]):  # 任一手抓到即成功
                    return TaskResult(False, error_code=ERR_ONE_HAND_FAILED,
                                      error_message="One-hand grasp failed")
                return result  # 抓握成功

            # two hand
            if grasp_state[0] and grasp_state[1]:
                return result  # 双手抓握成功
            if not grasp_state[0] and not grasp_state[1]:
                return TaskResult(False, error_code=ERR_TWO_HAND_BOTH_FAILED,
                                  error_message="Both hands grasp failed")
            if not grasp_state[0]:
                return TaskResult(False, error_code=ERR_TWO_HAND_LEFT_FAILED,
                                  error_message="Left hand grasp failed")
            # not grasp_state[1]
            return TaskResult(False, error_code=ERR_TWO_HAND_RIGHT_FAILED,
                              error_message="Right hand grasp failed")

        finally:
            # ===== 步骤 5: 清理 per-task 组件 =====
            context._active_vla_client = None
            context.destroy_vla_components(components)
