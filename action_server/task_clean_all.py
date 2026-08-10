"""
全流程桌面清洁任务 - init_clean + clean + finish_clean

协议触发方式: task="clean" + target="all" 时，执行完整的清洁全流程：
  1. init (clean-init-none):   安全抬臂 -> 准备姿态，并启动 VLA obs+infer
  2. clean (start):            VLA 推理执行桌面整理（固定多步语言指令）
  3. finish (clean-finish-none): 安全抬臂 -> 垂直复位，清理 VLA 组件

无失败重试逻辑 —— 采集数据已包含重试内容，
因此简单串联 init -> clean -> finish 三个子处理器即可。

不修改原有三个模块（task_init.py / task_clean.py / task_finish.py）。
导入其 Handler 类进行复用。
"""

import sys
import os
import time

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.task_init import InitHandler
from action_server.task_clean import CleanHandler
from action_server.task_finish import FinishHandler
from action_server.action_base import (
    AbstractTaskHandler, TaskResult,
    ERR_SUCCESS, ERR_MSG, ERR_INIT_CLEAN_FAILED, ERR_FINISH_CLEAN_FAILED,
)


class CleanAllHandler(AbstractTaskHandler):
    """'clean' task + target='all' 任务处理器 — 全流程桌面清洁

    完整流程:
      1. init (clean-init-none): 安全抬臂 -> 准备姿态，并启动 VLA obs+infer
      2. clean (start):           VLA 推理执行桌面整理（固定多步语言指令）
      3. finish (clean-finish-none): 安全抬臂 -> 垂直复位，清理 VLA 组件

    无重试逻辑：采集数据已包含重试内容，推理结果直接透传。
    无论 clean 成功还是失败，finish 都会执行（保证机器人复位 + VLA 资源清理）。
    """

    @property
    def task_name(self) -> str:
        return "clean"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        _t0 = time.time()
        send_fb = self.send_feedback

        # 子处理器（复用各模块配置驱动的点位序列与推理逻辑）
        init_handler = InitHandler()
        clean_handler = CleanHandler()
        finish_handler = FinishHandler()

        send_fb(goal_handle, 2, "全流程桌面清洁开始")

        # ===== 步骤 1: Init（clean-init-none: 安全抬臂 -> 准备姿态 + 启动 VLA 线程）=====
        send_fb(goal_handle, 5, "正在执行初始化: 过渡到准备姿态...")
        init_result = init_handler.execute(
            goal_handle,
            {"task": "clean", "target": "init", "waypoint": "none"},
            context,
        )
        if not init_result.success:
            return TaskResult(False, error_code=ERR_INIT_CLEAN_FAILED,
                              error_message="Init clean failed in clean_all flow")

        # ===== 步骤 2: Clean（VLA 推理执行桌面整理，无重试）=====
        send_fb(goal_handle, 30, "正在执行桌面整理 (VLA 推理)...")
        clean_result = clean_handler.execute(
            goal_handle,
            {"task": "clean", "target": "start", "waypoint": "none"},
            context,
        )

        # ===== 步骤 3: Finish（无论整理成功还是失败都执行: 复位 + 清理组件）=====
        send_fb(goal_handle, 85, "正在执行完成复位...")
        finish_result = finish_handler.execute(
            goal_handle,
            {"task": "clean", "target": "finish", "waypoint": "none"},
            context,
        )
        if not finish_result.success:
            return TaskResult(False, error_code=ERR_FINISH_CLEAN_FAILED,
                              error_message="Finish clean failed in clean_all flow")

        _elapsed = time.time() - _t0

        # ===== 步骤 4: 返回结果 =====
        if clean_result.success:
            send_fb(goal_handle, 100, f"全流程桌面清洁成功！耗时 {_elapsed:.1f}s")
            return TaskResult(True, error_code=ERR_SUCCESS,
                              error_message=ERR_MSG[ERR_SUCCESS])
        else:
            send_fb(goal_handle, 0,
                    f"全流程桌面清洁失败: {clean_result.error_message}")
            return clean_result
