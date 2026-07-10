"""
任务处理器基类 - 所有 task handler 的抽象接口 + 通用工具
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ==============================================
# 全局错误码定义
# 各 handler 共享，新增错误码请追加（避免冲突）
# ==============================================

# 成功
ERR_SUCCESS = 0

# 通用 (91-99)
ERR_TASK_CANCELLED = 91
ERR_ROBOT_RESET_FAILED = 92
ERR_INFERENCE_START_FAILED = 93
ERR_TASK_TIMEOUT = 94
ERR_MONITOR_ERROR = 95

# task_init_grasp 专用 (1)
ERR_INIT_GRASP_FAILED = 1

# task_grasp 专用 (11-19)
ERR_GRASP_TIMEOUT = 11
ERR_ONE_HAND_FAILED = 12
ERR_TWO_HAND_LEFT_FAILED = 13
ERR_TWO_HAND_RIGHT_FAILED = 14
ERR_TWO_HAND_BOTH_FAILED = 15
ERR_MISSING_TARGET = 16
ERR_UNKNOWN_TARGET = 17

# task_finish_grasp 专用 (18)
ERR_FINISH_GRASP_FAILED = 18

# task_grasp_all 专用 (19)
ERR_GRASP_ALL_RETRIES_EXHAUSTED = 19

# task_deliver 专用 (21-26)
ERR_DELIVER_TIMEOUT = 21
ERR_DELIVER_LEFT_EMPTY = 22
ERR_DELIVER_RIGHT_EMPTY = 23
ERR_DELIVER_ONE_HAND_BOTH_EMPTY = 24
ERR_DELIVER_BOTH_HAND_NOT_BOTH = 25
ERR_DELIVER_ONE_HAND_STILL_HOLDING = 26

# task_place 专用 (31-36)
ERR_PLACE_TIMEOUT = 31
ERR_PLACE_LEFT_EMPTY = 32
ERR_PLACE_RIGHT_EMPTY = 33
ERR_PLACE_ONE_HAND_BOTH_EMPTY = 34
ERR_PLACE_BOTH_HAND_NOT_BOTH = 35
ERR_PLACE_ONE_HAND_STILL_HOLDING = 36

# task_reset 专用 (41)
ERR_RESET_NO_STATE = 41

# task_release 专用 (42)
ERR_RELEASE_NO_STATE = 42

ERR_MSG = {
    ERR_SUCCESS: "none",
    # 通用
    ERR_TASK_CANCELLED: "Task cancelled by external signal",
    ERR_ROBOT_RESET_FAILED: "Robot reset failed",
    ERR_INFERENCE_START_FAILED: "Failed to start inference",
    ERR_TASK_TIMEOUT: "Task timed out",
    ERR_MONITOR_ERROR: "Internal monitoring error",

    # task_init_grasp 专用
    ERR_INIT_GRASP_FAILED: "Init grasp failed",
    
    # task_finish_grasp 专用
    ERR_FINISH_GRASP_FAILED: "Finish grasp failed",

    # task_grasp_all 专用
    ERR_GRASP_ALL_RETRIES_EXHAUSTED: "All 3 grasp attempts exhausted",

    # task_grasp 专用
    ERR_GRASP_TIMEOUT: "Grasp task timed out",
    ERR_ONE_HAND_FAILED: "One-hand grasp failed",
    ERR_TWO_HAND_LEFT_FAILED: "Left hand grasp failed",
    ERR_TWO_HAND_RIGHT_FAILED: "Right hand grasp failed",
    ERR_TWO_HAND_BOTH_FAILED: "Both hands grasp failed",
    ERR_MISSING_TARGET: 'Missing "target" field in params',
    ERR_UNKNOWN_TARGET: "Unknown target",

    # task_deliver 专用
    ERR_DELIVER_TIMEOUT: "Deliver task timed out",
    ERR_DELIVER_LEFT_EMPTY: "Left hand is empty but left arm deliver requested",
    ERR_DELIVER_RIGHT_EMPTY: "Right hand is empty but right arm deliver requested",
    ERR_DELIVER_ONE_HAND_BOTH_EMPTY: "Both hands are empty but one arm deliver requested",
    ERR_DELIVER_BOTH_HAND_NOT_BOTH: "Not both hands have objects but both arm deliver requested",
    ERR_DELIVER_ONE_HAND_STILL_HOLDING: "One hand still holding object after both arm deliver",

    # task_place 专用
    ERR_PLACE_TIMEOUT: "Place task timed out",
    ERR_PLACE_LEFT_EMPTY: "Left hand is empty but left arm place requested",
    ERR_PLACE_RIGHT_EMPTY: "Right hand is empty but right arm place requested",
    ERR_PLACE_ONE_HAND_BOTH_EMPTY: "Both hands are empty but one arm place requested",
    ERR_PLACE_BOTH_HAND_NOT_BOTH: "Not both hands have objects but both arm place requested",
    ERR_PLACE_ONE_HAND_STILL_HOLDING: "One hand still holding object after both arm place",

    # task_reset 专用
    ERR_RESET_NO_STATE: "Failed to get current robot state for arm reset",

    # task_release 专用
    ERR_RELEASE_NO_STATE: "Failed to get current robot state for hand release",
}


# ==============================================
# 任务执行结果
# ==============================================
@dataclass
class TaskResult:
    """统一的 handler 返回值

    Attributes:
        success:      是否成功
        result_code:  SUCCESS=1 / FAILED=2 (与 ExecutionUnit.action 对齐)
        error_code:   自定义错误码, 0 表示无错误
        error_message: 错误描述
    """
    success: bool
    error_code: int = 0
    error_message: str = ''

    @property
    def result_code(self) -> int:
        return 1 if self.success else 2


# ==============================================
# 抽象任务处理器
# ==============================================
class AbstractTaskHandler(ABC):
    """所有 task handler 的基类

    子类必须实现:
        - task_name: 返回任务名称字符串（与 params 中的 task 字段匹配）
        - execute(): 执行任务逻辑
    """

    @property
    @abstractmethod
    def task_name(self) -> str:
        """任务名称，用于路由匹配 (对应 params['task'] 的值)"""
        ...

    @abstractmethod
    def execute(self, goal_handle: Any, params: dict, context: Any) -> TaskResult:
        """执行任务

        Args:
            goal_handle: ROS2 Action goal_handle，用于 publish_feedback
            params:      解析后的参数字典（含 task / target / waypoint 等）
            context:     VLAContext 共享组件容器（含 robot_body 等）

        Returns:
            TaskResult: 任务执行结果
        """
        ...

    # ================================================================
    # 工具方法
    # ================================================================

    @staticmethod
    def send_feedback(goal_handle, progress: int, message: str,
                      feedback_code: int = 0, need_process: bool = True) -> None:
        """发送 feedback（线程安全）

        Args:
            goal_handle: ROS2 Action goal_handle
            progress:    进度百分比 (0-100)
            message:     文本描述
            feedback_code: 状态码, 0=心跳
            need_process:  是否需要外部处理
        """
        from message_center.action import ExecutionUnit

        fb = ExecutionUnit.Feedback()
        fb.need_process = need_process
        fb.feedback_code = feedback_code
        fb.message = f"[progress={progress}%] {message}"
        goal_handle.publish_feedback(fb)

    @staticmethod
    def build_feedback(progress: int, message: str,
                       feedback_code: int = 0, need_process: bool = True) -> Any:
        """构建但不发送 feedback 对象（用于需要自定义发送时机的场景）"""
        from message_center.action import ExecutionUnit

        fb = ExecutionUnit.Feedback()
        fb.need_process = need_process
        fb.feedback_code = feedback_code
        fb.message = f"[progress={progress}%] {message}"
        return fb

# ==============================================
# VLA 推理监控（模块级函数，所有 handler 共享）
# ==============================================

# 默认监控参数
_DEFAULT_MAX_DURATION = 60.0          # 最大执行时间（秒）
_DEFAULT_THRE_PROGRESS = 0.9          # 进度完成阈值
_DEFAULT_STABLE_COUNT = 20            # 连续稳定计数阈值
_DEFAULT_STABILITY_RATIO = 0.05       # 变异系数阈值
_DEFAULT_FEEDBACK_INTERVAL = 1.0 / 3.0  # 3Hz


def run_vla_inference(
    goal_handle,
    vla_client,
    language_instruction: str,
    robot_body=None,
    reset_robot: bool = True,
    max_duration: float = _DEFAULT_MAX_DURATION,
    thre_progress: float = _DEFAULT_THRE_PROGRESS,
    stable_count_threshold: int = _DEFAULT_STABLE_COUNT,
    stability_ratio_thresh: float = _DEFAULT_STABILITY_RATIO,
    feedback_interval: float = _DEFAULT_FEEDBACK_INTERVAL,
    fixed_duration: float = 0,
) -> TaskResult:
    """运行 VLA 推理全流程（复位 → 启动推理 → 监控进度 → 完成/超时）

    步骤:
        1. [可选] 复位机器人到安全姿态
        2. 设置语言指令 → inference_first() → run()
        3. 监控进度：
           - fixed_duration > 0: 固定时长模式，运行指定秒数后完成
           - fixed_duration = 0: prob_progress 稳定性检测模式
        4. 停止 VLA 客户端线程

    Args:
        goal_handle:          ROS2 Action goal_handle
        vla_client:           VLAClientAsync 实例
        language_instruction: 语言指令文本
        robot_body:           RobotBody 实例（reset_robot=True 时必填）
        reset_robot:          是否在启动前复位机器人
        max_duration:         最大执行时间（秒）
        thre_progress:        进度阈值，超过后开始稳定性检测
        stable_count_threshold: 连续稳定次数阈值
        stability_ratio_thresh:  变异系数阈值
        feedback_interval:     feedback 发送间隔
        fixed_duration:        固定执行时长（秒），>0 时启用，不依赖 prob_progress

    Returns:
        TaskResult: success=True 完成 / False 失败+原因
    """
    import time

    # ========== 步骤 1: 复位机器人（可选） ==========
    if reset_robot:
        if robot_body is None:
            return TaskResult(False, error_code=ERR_ROBOT_RESET_FAILED,
                              error_message='reset_robot=True but robot_body is None')
        send_vla_feedback(goal_handle, 5, "正在复位机器人到安全姿态...")
        try:
            robot_body.reset_robot(mode='default')
            time.sleep(1.0)
        except Exception as e:
            return TaskResult(False, error_code=ERR_ROBOT_RESET_FAILED,
                              error_message=f'Robot reset failed: {str(e)}')

    # ========== 步骤 2: 启动推理 ==========
    try:
        vla_client.task_language_manager.currt_language_instruction = language_instruction
        vla_client.is_running_action = False

        send_vla_feedback(goal_handle, 10, "正在启动 VLA 推理...")
        vla_client.start()                    # 先启动观察/控制/WebSocket 线程
        # time.sleep(3.5)                     # 等待观测数据积累
        # 注意: 不要在这里调 inference_first()!
        # _inference_thread_fun 内部已经有 infer_count==0 的自调用首帧逻辑
        # 如果这里再调一次，会与推理线程 (Thread-43) 竞争同一个 ZMQ socket
        # 导致响应被错抢 → 推理线程永久阻塞 → prob_progress 卡死
        vla_client.is_running_action = True # 允许推理线程持续推理
    except Exception as e:
        return TaskResult(False, error_code=ERR_INFERENCE_START_FAILED,
                          error_message=f'Failed to start inference: {str(e)}')

    # ========== 步骤 3 + 4: 监控进度 + 稳定性检测 ==========
    if fixed_duration > 0:
        # 固定时长模式：运行指定秒数后完成
        result = _monitor_fixed_duration(
            goal_handle=goal_handle,
            vla_client=vla_client,
            fixed_duration=fixed_duration,
            feedback_interval=feedback_interval,
        )
    else:
        # prob_progress 稳定性检测模式
        result = _monitor_vla_progress(
            goal_handle=goal_handle,
            vla_client=vla_client,
            max_duration=max_duration,
            thre_progress=thre_progress,
            stable_count_threshold=stable_count_threshold,
            stability_ratio_thresh=stability_ratio_thresh,
            feedback_interval=feedback_interval,
        )

    # ========== 步骤 5: 停止 VLA 客户端线程 ==========
    _stop_vla_client(vla_client)

    return result


def _monitor_vla_progress(
    goal_handle,
    vla_client,
    max_duration: float = _DEFAULT_MAX_DURATION,
    thre_progress: float = _DEFAULT_THRE_PROGRESS,
    stable_count_threshold: int = _DEFAULT_STABLE_COUNT,
    stability_ratio_thresh: float = _DEFAULT_STABILITY_RATIO,
    feedback_interval: float = _DEFAULT_FEEDBACK_INTERVAL,
) -> TaskResult:
    """监控 VLA 推理进度循环

    每 ~0.33s:
        1. 读取 prob_progress
        2. 发送 feedback（含进度百分比 + 已用时间）
        3. prob_progress > thre_progress 时触发稳定性检测
        4. 滑动窗口变异系数 < threshold 且连续稳定计数达到 → 任务完成
        5. 超时 → 返回超时错误

    Returns:
        TaskResult
    """
    import time
    import numpy as np

    progress_start = time.time()
    stable_count = 0
    stability_window = []
    last_prob = -1.0
    stuck_count = 0
    loop_count = 0

    print(f'[DEBUG _monitor_vla_progress] ENTER max_duration={max_duration}s thre_progress={thre_progress} stable_threshold={stable_count_threshold}')

    try:
        while True:
            loop_count += 1
            # 检查外部停止信号
            if not vla_client.is_running_action:
                # is_running_action=False → 外部停止
                send_vla_feedback(goal_handle, 0, "VLA task stopped by external signal")
                return TaskResult(False, error_code=ERR_TASK_CANCELLED,
                                  error_message='VLA task cancelled')

            # 检查超时
            elapsed_total = time.time() - progress_start
            if elapsed_total > max_duration:
                # 超时
                send_vla_feedback(goal_handle, 0,
                                  f'Task timed out after {elapsed_total:.1f}s')
                return TaskResult(False, error_code=ERR_TASK_TIMEOUT,
                                  error_message=f'Task timed out after {elapsed_total:.1f}s')

            # 读取进度
            current_prob_progress = vla_client.current_prob_progress
            elapsed = time.time() - progress_start
            progress_pct = min(int(current_prob_progress * 100), 99)

            # 检测 prob_progress 是否卡住
            if abs(current_prob_progress - last_prob) < 5e-4:
                stuck_count += 1
            else:
                stuck_count = 0
            last_prob = current_prob_progress
            if stuck_count > 0 and stuck_count % 10 == 0:
                pass

            # 发送 feedback
            send_vla_feedback(
                goal_handle, progress_pct,
                f"[elapsed={int(elapsed)}s] prob_progress={current_prob_progress:.3f}",
            )

            # ===== 条件 1: prob_progress > 80% → 立即完成（无需等待稳定性）+ =====
            if current_prob_progress > 0.80:
                send_vla_feedback(goal_handle, 100,
                                  f'Task completed (prob_progress={current_prob_progress:.3f})! Elapsed: {elapsed:.1f}s')
                return TaskResult(True)

            # ===== 条件 2: prob_progress 稳定性检测（原有逻辑，低于80%时兜底）=====
            if current_prob_progress > thre_progress:
                stability_window.append(current_prob_progress)
                if len(stability_window) > 50:
                    stability_window.pop(0)

                if len(stability_window) >= 3:
                    window_std = float(np.std(stability_window))
                    window_mean = float(np.mean(stability_window))
                    stability_ratio = window_std / (window_mean + 1e-6)

                    if stability_ratio < stability_ratio_thresh:
                        stable_count += 1
                    else:
                        stable_count = 0

                    if stable_count >= stable_count_threshold:
                        send_vla_feedback(goal_handle, 100,
                                          f'Task completed (prob stable)! Total time: {elapsed:.1f}s')
                        return TaskResult(True)
            else:
                stable_count = 0
                stability_window.clear()

            time.sleep(feedback_interval)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return TaskResult(False, error_code=ERR_MONITOR_ERROR,
                          error_message=f'Monitoring error: {str(e)}')


def _monitor_fixed_duration(
    goal_handle,
    vla_client,
    fixed_duration: float,
    feedback_interval: float = _DEFAULT_FEEDBACK_INTERVAL,
) -> TaskResult:
    """固定时长监控模式 — 运行指定秒数后直接标记完成

    用于不返回 prob_progress 的模型（如 GR00T）。
    """
    import time

    start_time = time.time()
    try:
        while True:
            elapsed = time.time() - start_time

            # 检查外部停止信号
            if not vla_client.is_running_action:
                send_vla_feedback(goal_handle, 0, "VLA task stopped by external signal")
                return TaskResult(False, error_code=ERR_TASK_CANCELLED,
                                  error_message='VLA task cancelled')

            # 发送进度反馈
            progress_percent = min(100, int((elapsed / fixed_duration) * 100))
            send_vla_feedback(
                goal_handle,
                progress_percent,
                f'Running... {elapsed:.1f}s / {fixed_duration:.1f}s',
            )

            # 达到固定时长，任务完成
            if elapsed >= fixed_duration:
                send_vla_feedback(goal_handle, 100,
                                  f'Task completed! Total time: {elapsed:.1f}s')
                return TaskResult(True)

            time.sleep(feedback_interval)

    except Exception as e:
        return TaskResult(False, error_code=ERR_MONITOR_ERROR,
                          error_message=f'Monitoring error: {str(e)}')


def _stop_vla_client(vla_client) -> None:
    """安全停止 VLA 客户端线程"""
    import time
    try:
        vla_client.is_running_action = False
        time.sleep(0.1)
    except Exception:
        pass


def send_vla_feedback(goal_handle, progress: int, message: str,
                      feedback_code: int = 0, need_process: bool = True) -> None:
    """发送 VLA 推理 feedback（模块级函数，方便各 handler 直接调用）"""
    from message_center.action import ExecutionUnit

    fb = ExecutionUnit.Feedback()
    fb.need_process = need_process
    fb.feedback_code = feedback_code
    fb.message = f"[progress={progress}%] {message}"
    goal_handle.publish_feedback(fb)
