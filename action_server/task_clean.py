"""
桌面清洁任务 - 根据固定语言指令调用 VLA 模型推理执行桌面清洁

clean 是清洁大类，通过 target 字段区分阶段:
  - target="start": 桌面清洁开始（本文件）

流程:
  1. 获取由 init_clean 创建的持久化 VLA 组件
  2. 设置桌面清洁语言指令（多步骤: 收带垃圾的盘子/收空盘/清理散落垃圾）
  3. 调用 run_vla_control_only() 只启动 control 线程执行推理（obs+infer 已由 init_clean 启动）
  4. 清理 active 引用（组件保留，由 finish_clean 统一清理）
"""

import sys
import os
import numpy as np

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.action_base import (
    AbstractTaskHandler, TaskResult, run_vla_control_only,
    ERR_INFERENCE_START_FAILED,
    ERR_TASK_TIMEOUT, ERR_CLEAN_TIMEOUT,
)


# ==============================================
# 桌面清洁语言指令（固定，多步骤）
# ==============================================
CLEAN_LANGUAGE_INSTRUCTION = (
    "Tidy up the table: [Step 1] Pick up dishes with garbage, empty the garbage "
    "and place the dishes on the right rack. [Step 2] Pick up each empty dish "
    "on the table, place on the right rack. Continue until no dishes left."
    "[Step 3] Pick up loose garbage on the table, place into the left trash bin. "
    "Continue until no garbage left."
)


class CleanHandler(AbstractTaskHandler):
    """'clean' task + target='start' 任务处理器 — 桌面清洁开始

    流程:
        1. 获取由 init_clean 创建的持久化 VLA 组件
        2. 执行 VLA 推理（只启动 control；obs+infer 已由 init_clean 启动）
        3. 清理 active 引用（组件保留，由 finish_clean 统一清理）
    """

    @property
    def task_name(self) -> str:
        return "clean"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        # ===== 步骤 1: 获取持久化 VLA 组件（由 init_clean 创建） =====
        components = context.vla_components
        if components is None:
            self.send_feedback(goal_handle, 0, "VLA 组件未就绪，请先执行 init_clean")
            return TaskResult(False, error_code=ERR_INFERENCE_START_FAILED,
                              error_message='VLA components not ready. Run init_clean first.')
        vla_client = components["vla_client"]
        task_language_manager = components["task_language_manager"]
        robot_body = context.robot_body

        # Override language instruction
        task_language_manager.currt_language_instruction = CLEAN_LANGUAGE_INSTRUCTION
        task_language_manager.config.sub_task_id = 0

        self.send_feedback(goal_handle, 5, f"桌面清洁开始: {CLEAN_LANGUAGE_INSTRUCTION[:80]}...")

        try:
            # ===== 步骤 2: 执行 VLA 推理（只启动 control） =====
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
                language_instruction=CLEAN_LANGUAGE_INSTRUCTION,
                max_duration=120.0,
                thre_progress=0.8,
                complete_hold_time=2.0,
                blend_config=blend_config,
            )

            # ===== 步骤 3: 分析结果 =====
            if not result.success:
                if result.error_code == ERR_TASK_TIMEOUT:
                    return TaskResult(False, error_code=ERR_CLEAN_TIMEOUT,
                                      error_message="Clean task timed out")
                return result

            return result

        finally:
            # ===== 步骤 4: 清理（仅清除 active 引用，不销毁组件） =====
            context._active_vla_client = None
