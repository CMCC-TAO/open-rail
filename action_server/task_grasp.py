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
    AbstractTaskHandler, TaskResult, run_vla_control_only,
    ERR_MISSING_TARGET, ERR_UNKNOWN_TARGET,
    ERR_INFERENCE_START_FAILED,
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
    "drainer": "two hand",
}

# ==============================================
# target → 语言指令映射表
# ==============================================
# key 为 params.target（不区分大小写），value 为对应的语言指令
TARGET_LANGUAGE_MAP: dict[str, str] = {
    "one water": "use one hand to grab one bottle from a pile of drinks.",
    "one Coca-Cola": "use one hand to grab one can from a pile of canned drinks.",
    "two water": "use both hands to grab the two nearest bottles from a pile of drinks.",
    "two Coca-Cola": "use both hands to grab the two nearest cans from a pile of canned drinks.",
    "drainer": "Lift up the drainer in front of you with both hands and keep it balanced.",
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
    left_hand = robot_body.get_current_hand_state('left')
    right_hand = robot_body.get_current_hand_state('right')

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
        robot_body.send_robot_action(action)
        time.sleep(0.02)

    print('[GraspHandler] 双臂回归默认位置完成')


class GraspHandler(AbstractTaskHandler):
    """'grasp' 任务处理器 — 抓取大类

    流程:
        1. 根据 params.target 查找对应的语言指令
        2. 创建 VLA 推理组件（vla_client 等）
        3. 调用 run_vla_control_only() 执行推理
        4. 清理 per-task 组件
    """

    @property
    def task_name(self) -> str:
        return "grasp"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        import time
        import numpy as np
        import threading as _thr
        _tname = _thr.current_thread().name
        _t0 = time.time()
        print(f'[DEBUG GraspHandler] ENTER on {_tname}, params={params}')
        
        # ===== 步骤 1: 解析 target 并获取语言指令 =====
        target = params.get("target", "")
        if not target:
            self.send_feedback(goal_handle, 0, "缺少 target 字段")
            print(f'[DEBUG GraspHandler] EXIT early: missing target')
            return TaskResult(False, error_code=ERR_MISSING_TARGET,
                              error_message='Missing "target" field in params')

        instruction = _get_language_instruction(target)
        if instruction is None:
            self.send_feedback(goal_handle, 0,
                               f"未知 target: {target}")
            print(f'[DEBUG GraspHandler] EXIT early: unknown target={target}')
            return TaskResult(False, error_code=ERR_UNKNOWN_TARGET,
                              error_message=f'Unknown target="{target}". '
                                            f'Supported: {list(TARGET_LANGUAGE_MAP.keys())}')

        self.send_feedback(goal_handle, 5,
                           f"抓取目标: {target}, 语言指令: {instruction}")
        print(f'[DEBUG GraspHandler] target={target} instruction="{instruction}" → creating VLA components...')

        # ===== 步骤 2: 获取持久化 VLA 组件（由 init_grasp 创建） =====
        components = context.vla_components
        if components is None:
            self.send_feedback(goal_handle, 0, "VLA 组件未就绪，请先执行 init_grasp")
            print(f'[DEBUG GraspHandler] EXIT early: no persistent VLA components (run init_grasp first)')
            return TaskResult(False, error_code=ERR_INFERENCE_START_FAILED,
                              error_message='VLA components not ready. Run init_grasp first.')
        vla_client = components["vla_client"]
        task_language_manager = components["task_language_manager"]
        robot_body = context.robot_body

        # Override language instruction
        print(f'[DEBUG GraspHandler] Overriding language instruction: "{instruction}"')
        task_language_manager.currt_language_instruction = instruction
        task_language_manager.config.sub_task_id = 0

        print(f'[DEBUG GraspHandler] Using persistent VLA components, starting control only...')

        try:
            # ===== 步骤 3: 执行 VLA 推理（只启动 control） =====
            context._active_vla_client = vla_client

            # 构建平滑过渡配置：从当前 action 过渡到模型轨迹
            blend_config = None
            try:
                cur_act = robot_body._get_reset_current_action()
                if cur_act is not None:
                    blend_config = {'start_action': np.asarray(cur_act, dtype=np.float64), 'duration': 3.0}
            except Exception:
                pass

            result = run_vla_control_only(
                goal_handle=goal_handle,
                vla_client=vla_client,
                language_instruction=instruction,
                max_duration=30.0,
                thre_progress=0.75,
                complete_hold_time=1.0,
                blend_config=blend_config,
            )

            # ===== 步骤 4: 分析结果 =====
            if not result.success:
                if result.error_code == 6:
                    return TaskResult(False, error_code=ERR_GRASP_TIMEOUT,
                                      error_message="Grasp task timed out")
                return result

            # VLA 推理成功，验证实际抓握状态
            hand_type = TARGET_HAND_MAP.get(target.strip(), "one hand")
            grasp_state = context.grasp_detector.grasp_state

            if hand_type == "one hand":
                if not (grasp_state[0] or grasp_state[1]):
                    return TaskResult(False, error_code=ERR_ONE_HAND_FAILED,
                                      error_message="One-hand grasp failed")
                return result

            if grasp_state[0] and grasp_state[1]:
                return result
            if not grasp_state[0] and not grasp_state[1]:
                return TaskResult(False, error_code=ERR_TWO_HAND_BOTH_FAILED,
                                  error_message="Both hands grasp failed")
            if not grasp_state[0]:
                return TaskResult(False, error_code=ERR_TWO_HAND_LEFT_FAILED,
                                  error_message="Left hand grasp failed")
            return TaskResult(False, error_code=ERR_TWO_HAND_RIGHT_FAILED,
                              error_message="Right hand grasp failed")

        finally:
            # ===== 步骤 5: 清理（仅清除 active 引用，不销毁组件） =====
            context._active_vla_client = None
            _elapsed = time.time() - _t0
            print(f'[DEBUG GraspHandler] EXIT after {_elapsed:.1f}s (components preserved for reuse)')
