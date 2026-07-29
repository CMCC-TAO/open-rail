"""
grasp_all 任务 - 全流程抓取（init_grasp + grasp + finish_grasp）

当 waypoint="all" 时，执行完整的抓取全流程：
  1. init_grasp: 安全抬臂握拳 -> 准备抓取姿态
  2. grasp: VLA 推理执行抓取（最多 3 次重试）
  3. finish_grasp: 安全抬臂 -> 垂直复位

不修改原有三个文件（task_init_grasp.py / task_grasp.py / task_finish_grasp.py）。
导入其模块级函数和常量进行复用。
"""

import sys
import os
import time
import numpy as np

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.task_init_grasp import _get_init_grasp_pose, _SAFE_LEFT_ARM, _SAFE_RIGHT_ARM
from action_server.task_grasp import (
    _get_language_instruction,
    TARGET_HAND_MAP,
)
from action_server.task_reset import _LEFT_RESET_POSE, _RIGHT_RESET_POSE
from action_server.action_base import (
    AbstractTaskHandler, TaskResult, run_vla_control_only, send_vla_feedback,
    ERR_SUCCESS, ERR_MSG, ERR_INIT_GRASP_FAILED, ERR_GRASP_TIMEOUT,
    ERR_MISSING_TARGET, ERR_UNKNOWN_TARGET,
    ERR_ONE_HAND_FAILED, ERR_TWO_HAND_LEFT_FAILED, ERR_TWO_HAND_RIGHT_FAILED,
    ERR_TWO_HAND_BOTH_FAILED, ERR_FINISH_GRASP_FAILED,
    ERR_GRASP_ALL_RETRIES_EXHAUSTED,
)

# ==============================================
# 常量
# ==============================================
MAX_GRASP_RETRIES = 3


# ==============================================
# 工具函数
# ==============================================

def _get_current_hands(robot_body) -> np.ndarray:
    """获取当前 12 维手掌状态（最新下发量）"""
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
    return np.zeros(12, dtype=float)


def _do_init_grasp(goal_handle, context, send_feedback_fn) -> bool:
    """执行 init_grasp 阶段：安全抬臂握拳 -> 准备抓取姿态

    Returns:
        True 成功, False 失败
    """
    try:
        robot_body = context.robot_body
        init_grasp_pose = _get_init_grasp_pose(context)

        # 检查手掌数据
        robot = robot_body.robot
        lh = robot.latest_left_hand_action
        rh = robot.latest_right_hand_action
        if lh is None or rh is None:
            send_feedback_fn(goal_handle, 0, "未收到机器人手掌数据")
            return False

        # 过渡到安全中间姿态（抬臂握拳）
        send_feedback_fn(goal_handle, 5, "正在过渡到安全中间姿态...")
        safe_pose = np.array([
            *_SAFE_LEFT_ARM,
            *_SAFE_RIGHT_ARM,
            1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0,
            1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0,
        ])
        robot_body.reset_robot(target_pose=safe_pose,
                               max_velocity=1.5, max_acceleration=1.0, max_jerk=3.0)

        # 过渡到准备抓取姿态
        send_feedback_fn(goal_handle, 15, "正在过渡到准备抓取姿态...")
        robot_body.reset_robot(target_pose=init_grasp_pose,
                               max_velocity=1.5, max_acceleration=1.0, max_jerk=3.0)

        return True
    except Exception as e:
        send_feedback_fn(goal_handle, 0, f"Init grasp 失败: {e}")
        return False


def _do_single_grasp(goal_handle, context, target: str, instruction: str,
                     attempt: int, send_feedback_fn) -> TaskResult:
    """执行单次抓取

    Args:
        attempt: 当前第几次尝试 (1-based)

    Returns:
        TaskResult: success=True 表示抓取成功, False 表示失败
    """
    robot_body = context.robot_body

    # 第 2+ 次重试：先复位到默认准备抓取位置（含手臂和手掌）
    if attempt > 1:
        send_feedback_fn(goal_handle, 20, f"第 {attempt} 次重试：复位到默认位置...")
        init_grasp_pose = _get_init_grasp_pose(context)
        robot_body.reset_robot(target_pose=init_grasp_pose,
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
            hand_type = TARGET_HAND_MAP.get(target.strip(), "one hand")

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


def _do_finish_grasp(goal_handle, context, send_feedback_fn) -> bool:
    """执行 finish_grasp 阶段：获取手掌 -> 安全抬臂 -> 垂直复位

    Returns:
        True 成功, False 失败
    """
    try:
        robot_body = context.robot_body

        # 检查手掌数据
        robot = robot_body.robot
        lh = robot.latest_left_hand_action
        rh = robot.latest_right_hand_action
        if lh is None or rh is None:
            send_feedback_fn(goal_handle, 0, "未收到机器人手掌数据")
            return False

        # 获取当前手掌状态（保持抓取物体）
        hands = _get_current_hands(robot_body)

        # 过渡到安全中间姿态（抬臂，手掌不变）
        send_feedback_fn(goal_handle, 90, "正在过渡到安全中间姿态...")
        safe_pose = np.array([*_SAFE_LEFT_ARM, *_SAFE_RIGHT_ARM, *hands])
        robot_body.reset_robot(target_pose=safe_pose,
                               max_velocity=1.5, max_acceleration=1.0, max_jerk=3.0)
        _wait_for_movement(robot_body, safe_pose)  # 等待机器人物理到位

        # 过渡到垂直复位姿态（手掌不变）
        send_feedback_fn(goal_handle, 95, "正在过渡到垂直复位姿态...")
        reset_pose = np.array([*_LEFT_RESET_POSE, *_RIGHT_RESET_POSE, *hands])
        robot_body.reset_robot(target_pose=reset_pose,
                               max_velocity=1.5, max_acceleration=1.0, max_jerk=3.0)
        _wait_for_movement(robot_body, reset_pose)  # 等待机器人物理到位

        return True
    except Exception as e:
        send_feedback_fn(goal_handle, 0, f"Finish grasp 失败: {e}")
        return False


# ==============================================
# GraspAllHandler
# ==============================================

class GraspAllHandler(AbstractTaskHandler):
    """'grasp_all' 任务处理器 — 全流程抓取

    完整流程:
      1. init_grasp: 安全抬臂握拳 -> 准备抓取姿态
      2. grasp (最多 3 次重试):
         - VLA 推理执行抓取
         - 成功后验证抓取状态
         - 失败后复位到默认位置重试
      3. finish_grasp: 安全抬臂 -> 垂直复位
    """

    @property
    def task_name(self) -> str:
        return "grasp_all"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        _t0 = time.time()
        send_fb = self.send_feedback

        # ===== 步骤 1: 解析 target =====
        target = params.get("target", "")
        if not target:
            send_fb(goal_handle, 0, "缺少 target 字段")
            return TaskResult(False, error_code=ERR_MISSING_TARGET,
                              error_message='Missing "target" field in params')

        instruction = _get_language_instruction(target)
        if instruction is None:
            send_fb(goal_handle, 0, f"未知 target: {target}")
            return TaskResult(False, error_code=ERR_UNKNOWN_TARGET,
                              error_message=f'Unknown target="{target}"')

        send_fb(goal_handle, 2, f"全流程抓取开始: target={target}")

        # ===== 步骤 2: Init grasp =====
        if not _do_init_grasp(goal_handle, context, send_fb):
            return TaskResult(False, error_code=ERR_INIT_GRASP_FAILED,
                              error_message="Init grasp failed in grasp_all flow")
        context._initialized = True

        # ===== 步骤 3: Grasp retry loop =====
        grasp_success = False
        final_grasp_result = None

        for attempt in range(1, MAX_GRASP_RETRIES + 1):
            result = _do_single_grasp(
                goal_handle, context, target, instruction,
                attempt, send_fb,
            )
            if result.success:
                grasp_success = True
                send_fb(goal_handle, 50, f"第 {attempt} 次抓取成功")
                break
            else:
                send_fb(goal_handle, 30,
                        f"第 {attempt} 次抓取失败，准备重试...")
                final_grasp_result = result

        # ===== 步骤 4: Finish grasp（无论抓取成功还是失败都执行）=====
        if not _do_finish_grasp(goal_handle, context, send_fb):
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
                    f"全流程抓取失败，{MAX_GRASP_RETRIES} 次均未抓到")
            return TaskResult(False, error_code=ERR_GRASP_ALL_RETRIES_EXHAUSTED,
                              error_message=f"All {MAX_GRASP_RETRIES} grasp attempts exhausted")
