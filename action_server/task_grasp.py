"""
抓取任务 - 根据 target 选择语言指令，调用 VLA 模型推理执行抓取

grasb 是一个大类，通过 target 字段区分具体的抓取动作（单手/双手、目标物体）。
"""

import sys
import os

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.action_base import (
    AbstractTaskHandler, TaskResult, run_vla_inference,
)

# ==============================================
# target → 语言指令映射表
# ==============================================
# key 为 params.target（不区分大小写），value 为对应的语言指令
TARGET_LANGUAGE_MAP: dict[str, str] = {
    "one Wahaha": "Use one hand to grab one bottle from a pile of Wahaha drinks.",
    "one Coca-Cola": "Use one hand to grab one bottle from a pile of Coca-Cola drinks.",
    "two Wahaha": "Use both hands to grab the two nearest bottles from a pile of Wahaha drinks.",
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


class GraspHandler(AbstractTaskHandler):
    """'grasb' 任务处理器 — 抓取大类

    流程:
        1. 根据 params.target 查找对应的语言指令
        2. 创建 VLA 推理组件（vla_client 等）
        3. 调用 run_vla_inference() 执行推理
        4. 清理 per-task 组件
    """

    @property
    def task_name(self) -> str:
        return "grasb"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        # ===== 步骤 1: 解析 target 并获取语言指令 =====
        target = params.get("target", "")
        if not target:
            self.send_feedback(goal_handle, 0, "缺少 target 字段", feedback_code=1)
            return TaskResult(False, error_code=2,
                              error_message='Missing "target" field in params')

        instruction = _get_language_instruction(target)
        if instruction is None:
            self.send_feedback(goal_handle, 0,
                               f"未知 target: {target}", feedback_code=1)
            return TaskResult(False, error_code=3,
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
                max_duration=10.0,
                thre_progress=1.5,  # 禁止 prob_progress 稳定性检测，靠 >95% 直接完成或 10s 超时
                stable_count_threshold=999,
            )
            return result

        finally:
            # ===== 步骤 4: 清理 per-task 组件 =====
            context._active_vla_client = None
            context.destroy_vla_components(components)
