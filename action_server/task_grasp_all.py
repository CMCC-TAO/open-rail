"""
全流程抓取任务 - init_grasp + grasp + finish_grasp（配置驱动）

协议触发方式: task="grasp" + waypoint="all" 时，按 target 查配置表 GRASP_ALL_SEQUENCES 执行完整流程：
  1. init_grasp:  按 init_key 从 task_init.INIT_POSE_SEQUENCES 取点位序列过渡
  2. grasp:       VLA 推理执行抓取（重试次数由配置 max_retries 决定）
  3. finish_grasp: 按 finish_key 从 task_finish.FINISH_POSE_SEQUENCES 取点位序列复位并清理

新增 target 只需在 GRASP_ALL_SEQUENCES 中添加一条配置（init/finish 点位序列、语言指令、
手数、重试次数均可独立配置），无需改任何逻辑代码。

语言指令与手数不在此配置：统一在 task_grasp.TARGET_LANGUAGE_MAP / TARGET_HAND_MAP 登记
（物体 → 手数/语言 的唯一数据源）。新增物体时先在 task_grasp.py 两个映射表各加一行，
再在 GRASP_ALL_SEQUENCES 添加流程配置。

不修改原有三个模块（task_init.py / task_grasp.py / task_finish.py）。
导入其模块级函数和常量进行复用。
"""

import sys
import os
import time
import numpy as np
from typing import TypedDict

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.task_init import (
    INIT_POSE_SEQUENCES,
    POSE_BUILDERS as INIT_POSE_BUILDERS,
)
from action_server.task_finish import (
    FINISH_POSE_SEQUENCES,
    POSE_BUILDERS as FINISH_POSE_BUILDERS,
)
from action_server.task_grasp import (
    TARGET_LANGUAGE_MAP,
    TARGET_HAND_MAP,
)
from action_server.action_base import (
    AbstractTaskHandler, TaskResult, run_vla_control_only,
    ERR_SUCCESS, ERR_MSG, ERR_INIT_GRASP_FAILED,
    ERR_MISSING_TARGET, ERR_UNKNOWN_TARGET,
    ERR_ONE_HAND_FAILED, ERR_TWO_HAND_LEFT_FAILED, ERR_TWO_HAND_RIGHT_FAILED,
    ERR_TWO_HAND_BOTH_FAILED, ERR_FINISH_GRASP_FAILED,
    ERR_GRASP_ALL_RETRIES_EXHAUSTED,
)

# ==============================================
# 全流程抓取配置表（target → 流程配置）
# ==============================================
# 新增 target 只需在此添加一条记录（语言指令/手数统一在 task_grasp.py 映射表登记）:
#   init_key:     task_init.INIT_POSE_SEQUENCES 中的组合键（init 点位序列）
#   max_retries:  失败重试次数（3 = 最多尝试 3 次；1 = 不重试）
#   finish_key:   task_finish.FINISH_POSE_SEQUENCES 中的组合键（finish 点位序列）
class GraspAllConfig(TypedDict):
    """单个 target 的全流程抓取配置（语言指令/手数在 task_grasp.py 映射表登记）"""
    init_key: str
    max_retries: int
    finish_key: str


GRASP_ALL_SEQUENCES: dict[str, GraspAllConfig] = {
    "drainer": {
        "init_key": "grasp-init-drainer",
        "max_retries": 1,
        "finish_key": "grasp-finish-none",
    },
    "one water": {
        "init_key": "grasp-init-none",
        "max_retries": 3,
        "finish_key": "grasp-finish-none",
    },
    "one Coca-Cola": {
        "init_key": "grasp-init-none",
        "max_retries": 3,
        "finish_key": "grasp-finish-none",
    },
    "two water": {
        "init_key": "grasp-init-none",
        "max_retries": 3,
        "finish_key": "grasp-finish-none",
    },
    "two Coca-Cola": {
        "init_key": "grasp-init-none",
        "max_retries": 3,
        "finish_key": "grasp-finish-none",
    },
}


# ==============================================
# 工具函数
# ==============================================

def _do_init_grasp(goal_handle, context, sequence_key: str, send_feedback_fn) -> bool:
    """执行 init 阶段：按 init_key 从 INIT_POSE_SEQUENCES 取点位序列依次过渡

    Args:
        sequence_key: task_init.INIT_POSE_SEQUENCES 中的组合键

    Returns:
        True 成功, False 失败
    """
    try:
        robot_body = context.robot_body
        sequence = INIT_POSE_SEQUENCES[sequence_key]

        # 检查手掌数据
        lh = robot_body.get_latest_hand_action('left')
        rh = robot_body.get_latest_hand_action('right')
        if lh is None or rh is None:
            send_feedback_fn(goal_handle, 0, "未收到机器人手掌数据")
            return False

        # 按序列依次过渡到各点位
        total = len(sequence)
        for idx, pose_name in enumerate(sequence):
            progress = 5 + int((idx + 1) / total * 15)
            send_feedback_fn(goal_handle, progress,
                             f"正在过渡到点位[{idx + 1}/{total}] ({pose_name})...")
            pose = INIT_POSE_BUILDERS[pose_name](context)
            robot_body.reset_robot_with_motion(target_pose=pose,
                                   max_velocity=1.5, max_acceleration=1.0, max_jerk=3.0)

        return True
    except Exception as e:
        send_feedback_fn(goal_handle, 0, f"Init grasp 失败: {e}")
        return False


def _do_single_grasp(goal_handle, context, instruction: str, hand_type: str,
                     attempt: int, send_feedback_fn) -> TaskResult:
    """执行单次抓取

    Args:
        instruction: VLA 语言指令
        hand_type: "one hand" / "two hand"（抓取验证用）
        attempt: 当前第几次尝试 (1-based)

    Returns:
        TaskResult: success=True 表示抓取成功, False 表示失败
    """
    robot_body = context.robot_body

    # 第 2+ 次重试：先复位到默认准备抓取位置（含手臂和手掌）
    if attempt > 1:
        send_feedback_fn(goal_handle, 20, f"第 {attempt} 次重试：复位到默认位置...")
        init_grasp_pose = INIT_POSE_BUILDERS["init"](context)
        robot_body.reset_robot_with_motion(target_pose=init_grasp_pose,
                               max_velocity=1.5, max_acceleration=1.0, max_jerk=3.0)
        time.sleep(0.5)

    send_feedback_fn(goal_handle, 25, f"第 {attempt} 次抓取尝试...")

    # 使用持久化 VLA 组件（由 InitGraspHandler 创建），
    # 避免多个 vla_client 共享同一个 ZMQ DEALER socket 造成响应劫持死锁。
    components = context.ensure_vla_components()
    vla_client = components["vla_client"]
    task_language_manager = components["task_language_manager"]

    try:
        # 启动 observe + inference（幂等安全，内部有 is_alive 保护）
        vla_client.start_observe()
        vla_client.start_inference()
        vla_client.start_visualize()
        vla_client.is_running_action = True

        # 设置语言指令
        task_language_manager.currt_language_instruction = instruction
        task_language_manager.config.sub_task_id = 0

        # 构建平滑过渡配置：从当前 action 过渡到模型轨迹
        blend_config = None
        try:
            cur_act = robot_body._get_reset_current_action()
            if cur_act is not None:
                blend_config = {'start_action': np.asarray(cur_act, dtype=np.float64), 'duration': 3.0}
        except Exception:
            pass

        # 执行推理（只启动 control，obs+infer 已在上面启动）
        context._active_vla_client = vla_client
        result = run_vla_control_only(
            goal_handle=goal_handle,
            vla_client=vla_client,
            language_instruction=instruction,
            max_duration=30.0,
            thre_progress=0.8,
            complete_hold_time=2.0,
            blend_config=blend_config,
        )

        # 不停 obs/infer（持久化组件，由 finish_grasp 统一销毁）
        # 控制线程已在 run_vla_control_only 的 finally 中停掉

        # 推理完成后读取抓取状态
        # _do_finish_grasp 会处理手臂复位，此处无需重复复位
        grasp_state = context.grasp_detector.grasp_state  # [left, right]

        if result.success:
            if hand_type == "one hand":
                if not (grasp_state[0] or grasp_state[1]):
                    return TaskResult(False, error_code=ERR_ONE_HAND_FAILED,
                                      error_message="One-hand grasp failed")
                return TaskResult(True)

            # two hand
            if grasp_state[0] and grasp_state[1]:
                return TaskResult(True)
            if not grasp_state[0] and not grasp_state[1]:
                return TaskResult(False, error_code=ERR_TWO_HAND_BOTH_FAILED,
                                  error_message="Both hands grasp failed")
            if not grasp_state[0]:
                return TaskResult(False, error_code=ERR_TWO_HAND_LEFT_FAILED,
                                  error_message="Left hand grasp failed")
            return TaskResult(False, error_code=ERR_TWO_HAND_RIGHT_FAILED,
                              error_message="Right hand grasp failed")

        # 推理失败
        return result

    finally:
        context._active_vla_client = None
        # 不销毁组件（持久化组件，由 finish_grasp 统一清理）


def _wait_for_movement(robot_body, target_pose: np.ndarray,
                       timeout: float = 5.0, tol: float = 0.5) -> bool:
    """等待机器人实际关节位置到达目标位置

    轮询 _get_reset_current_state() 读取实测关节位置，与目标对比。
    容差和超时逻辑跟 reset_robot 内部判断一致。

    Args:
        robot_body: RobotBody 实例
        target_pose: 26-dim 目标位姿
        timeout: 超时秒数
        tol: 关节角度容差 (rad)
    Returns:
        True 到位/超时都返回 True（有超时兜底，不卡死）
    """
    target_arms = target_pose[:14]
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = robot_body._get_reset_current_state()
        if state is not None:
            err = np.max(np.abs(state[:14] - target_arms))
            if err < tol:
                break
        time.sleep(0.01)
    return True


def _do_finish_grasp(goal_handle, context, sequence_key: str, send_feedback_fn) -> bool:
    """执行 finish 阶段：按 finish_key 从 FINISH_POSE_SEQUENCES 取点位序列复位 + 清理 VLA 组件

    Args:
        sequence_key: task_finish.FINISH_POSE_SEQUENCES 中的组合键

    Returns:
        True 成功, False 失败
    """
    try:
        robot_body = context.robot_body
        sequence = FINISH_POSE_SEQUENCES[sequence_key]

        # 检查手掌数据
        lh = robot_body.get_latest_hand_action('left')
        rh = robot_body.get_latest_hand_action('right')
        if lh is None or rh is None:
            send_feedback_fn(goal_handle, 0, "未收到机器人手掌数据")
            return False

        # 按序列过渡（构建器内部动态保持当前手掌状态，避免松手掉物）
        total = len(sequence)
        for idx, pose_name in enumerate(sequence):
            progress = 85 + int((idx + 1) / total * 10)
            send_feedback_fn(goal_handle, progress,
                             f"正在过渡到点位[{idx + 1}/{total}] ({pose_name})...")
            pose = FINISH_POSE_BUILDERS[pose_name](context)
            robot_body.reset_robot_with_motion(target_pose=pose,
                                   max_velocity=1.5, max_acceleration=1.0, max_jerk=3.0)
            _wait_for_movement(robot_body, pose)  # 等待机器人物理到位

        # 清理 VLA 组件（停止 observe/inference 线程，与 task_finish.py 对齐）
        send_feedback_fn(goal_handle, 97, "正在清理 VLA 推理资源...")
        context.clear_vla_components()

        return True
    except Exception as e:
        send_feedback_fn(goal_handle, 0, f"Finish grasp 失败: {e}")
        return False


# ==============================================
# GraspAllHandler
# ==============================================

class GraspAllHandler(AbstractTaskHandler):
    """'grasp' task + waypoint='all' 任务处理器 — 全流程抓取（配置驱动）

    完整流程:
      1. init_grasp:   按配置 init_key 过渡（安全抬臂 -> 准备抓取姿态）
      2. grasp:        VLA 推理执行抓取，成功后验证抓取状态，
                       失败按配置 max_retries 复位重试
      3. finish_grasp: 按配置 finish_key 过渡（安全抬臂 -> 垂直复位）
    """

    @property
    def task_name(self) -> str:
        return "grasp"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        _t0 = time.time()
        send_fb = self.send_feedback

        # ===== 步骤 1: 解析 target 并查配置表 =====
        target = params.get("target", "")
        if not target:
            send_fb(goal_handle, 0, "缺少 target 字段")
            return TaskResult(False, error_code=ERR_MISSING_TARGET,
                              error_message='Missing "target" field in params')

        cfg = GRASP_ALL_SEQUENCES.get(target.strip())
        if cfg is None:
            send_fb(goal_handle, 0, f"未知 target: {target}")
            return TaskResult(False, error_code=ERR_UNKNOWN_TARGET,
                              error_message='Unknown target="' + target + '", ' +
                                            '可用: ' + str(list(GRASP_ALL_SEQUENCES.keys())))

        # 语言指令/手数统一从 task_grasp.py 映射表查询（物体 → 手数/语言 的唯一登记处）
        instruction = TARGET_LANGUAGE_MAP.get(target.strip(), "")
        hand_type = TARGET_HAND_MAP.get(target.strip(), "one hand")
        max_retries = cfg.get("max_retries", 3)
        init_key = cfg["init_key"]
        finish_key = cfg["finish_key"]

        if not instruction:
            send_fb(goal_handle, 0,
                    f"target={target} 无语言指令（配置表为空且 task_grasp 映射中无记录）")
            return TaskResult(False, error_code=ERR_UNKNOWN_TARGET,
                              error_message='No language instruction for target="' + target + '"')

        send_fb(goal_handle, 2, f"全流程抓取开始: target={target}")

        # ===== 步骤 2: Init grasp =====
        if not _do_init_grasp(goal_handle, context, init_key, send_fb):
            return TaskResult(False, error_code=ERR_INIT_GRASP_FAILED,
                              error_message="Init grasp failed in grasp_all flow")
        context._initialized = True

        # ===== 步骤 3: Grasp retry loop（次数由配置决定）=====
        grasp_success = False

        for attempt in range(1, max_retries + 1):
            result = _do_single_grasp(
                goal_handle, context, instruction, hand_type,
                attempt, send_fb,
            )
            if result.success:
                grasp_success = True
                send_fb(goal_handle, 50, f"第 {attempt} 次抓取成功")
                break
            else:
                send_fb(goal_handle, 30,
                        f"第 {attempt} 次抓取失败，准备重试...")

        # ===== 步骤 4: Finish grasp（无论抓取成功还是失败都执行）=====
        if not _do_finish_grasp(goal_handle, context, finish_key, send_fb):
            return TaskResult(False, error_code=ERR_FINISH_GRASP_FAILED,
                              error_message="Finish grasp failed in grasp_all flow")

        _elapsed = time.time() - _t0

        # ===== 步骤 5: 返回结果 =====
        if grasp_success:
            send_fb(goal_handle, 100, f"全流程抓取成功！耗时 {_elapsed:.1f}s")
            return TaskResult(True, error_code=ERR_SUCCESS,
                              error_message=ERR_MSG[ERR_SUCCESS])
        else:
            send_fb(goal_handle, 0,
                    f"全流程抓取失败，{max_retries} 次均未抓到")
            return TaskResult(False, error_code=ERR_GRASP_ALL_RETRIES_EXHAUSTED,
                              error_message=f"All {max_retries} grasp attempts exhausted")
