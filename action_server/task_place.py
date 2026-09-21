"""
Model-controlled place task.

The place target selects the language instruction sent to the VLA model. The
VLA components are created and their observation/inference threads are started
by the corresponding init task, just like the grasp task.
"""

import os
import sys

import numpy as np

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.task_init import (
    _SAFE_LEFT_ARM,
    _SAFE_RIGHT_ARM,
    _get_init_grasp_pose,
)
from action_server.action_base import (
    AbstractTaskHandler,
    TaskResult,
    run_vla_control_only,
    ERR_INFERENCE_START_FAILED,
    ERR_PLACE_LEFT_EMPTY,
    ERR_PLACE_RIGHT_EMPTY,
    ERR_PLACE_ONE_HAND_BOTH_EMPTY,
    ERR_PLACE_BOTH_HAND_NOT_BOTH,
    ERR_PLACE_TIMEOUT,
    ERR_TASK_TIMEOUT,
    ERR_UNKNOWN_TARGET,
)


LEFT_PLACE_LANGUAGE_INSTRUCTION = (
    "Place the object in your left hand onto the table."
)
RIGHT_PLACE_LANGUAGE_INSTRUCTION = (
    "Place the object in your right hand onto the table."
)
BOTH_PLACE_LANGUAGE_INSTRUCTION = (
    "Place the objects in both hands onto the table."
)

PLACE_LANGUAGE_MAP: dict[str, str] = {
    "left arm": LEFT_PLACE_LANGUAGE_INSTRUCTION,
    "right arm": RIGHT_PLACE_LANGUAGE_INSTRUCTION,
    "both arm": BOTH_PLACE_LANGUAGE_INSTRUCTION,
}


def _get_grasp_state(context):
    """Return the latest [left_grasped, right_grasped] state."""
    return context.grasp_detector.grasp_state


def _resolve_target(target: str, context):
    """Resolve one-arm placement to the hand currently holding an object."""
    target = target.strip()
    grasp_state = _get_grasp_state(context)

    if target == "one arm":
        if grasp_state[1]:
            target = "right arm"
        elif grasp_state[0]:
            target = "left arm"
        else:
            return None, None, ERR_PLACE_ONE_HAND_BOTH_EMPTY

    if target == "left arm" and not grasp_state[0]:
        return None, None, ERR_PLACE_LEFT_EMPTY
    if target == "right arm" and not grasp_state[1]:
        return None, None, ERR_PLACE_RIGHT_EMPTY
    if target == "both arm" and not (grasp_state[0] and grasp_state[1]):
        return None, None, ERR_PLACE_BOTH_HAND_NOT_BOTH

    instruction = PLACE_LANGUAGE_MAP.get(target)
    if instruction is None:
        return None, None, ERR_UNKNOWN_TARGET

    return target, instruction, None


class PlaceHandler(AbstractTaskHandler):
    """Execute model-controlled placement for the requested hand(s)."""

    @property
    def task_name(self) -> str:
        return "place"

    def _move_to_initial_pose(self, goal_handle, robot_body, target, context):
        """Move to the initial pose and return its final commanded action."""
        self.send_feedback(goal_handle, 10, "放置前移动到安全姿态")

        safe_state = robot_body.move_arms(
            left_target=_SAFE_LEFT_ARM,
            right_target=_SAFE_RIGHT_ARM,
        )

        if safe_state is None:
            return TaskResult(
                False,
                error_code=ERR_PLACE_TIMEOUT,
                error_message="Failed to reach safe pose before place",
            )

        init_grasp_pose = _get_init_grasp_pose(context)
        self.send_feedback(goal_handle, 15, "放置前移动到初始姿态")

        init_state = robot_body.move_arms(
            left_target=init_grasp_pose[0:7],
            right_target=init_grasp_pose[7:14],
        )

        if init_state is None:
            return TaskResult(
                False,
                error_code=ERR_PLACE_TIMEOUT,
                error_message="Failed to reach initial pose before place",
            )

        self.send_feedback(goal_handle, 20, "已到初始姿态，开始模型放置")
        return np.asarray(init_state, dtype=np.float64).copy()

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        requested_target = params.get("target", "")
        target, instruction, error_code = _resolve_target(requested_target, context)

        if error_code is not None:
            self.send_feedback(goal_handle, 0,
                               f"无法执行放置目标: {requested_target}")
            messages = {
                ERR_PLACE_LEFT_EMPTY: "Left hand is empty, cannot place",
                ERR_PLACE_RIGHT_EMPTY: "Right hand is empty, cannot place",
                ERR_PLACE_ONE_HAND_BOTH_EMPTY: (
                    "Both hands are empty, cannot do one arm place"
                ),
                ERR_PLACE_BOTH_HAND_NOT_BOTH: (
                    "Not both hands have objects, cannot do both arm place"
                ),
                ERR_UNKNOWN_TARGET: f'Unknown place target: "{requested_target}"',
            }
            return TaskResult(
                False,
                error_code=error_code,
                error_message=messages.get(error_code, "Invalid place target"),
            )

        components_created = context.vla_components is None
        try:
            components = context.ensure_vla_components()
        except Exception as exc:
            self.send_feedback(goal_handle, 0,
                               f"无法创建 VLA 组件（不改变手掌状态）: {exc}")
            return TaskResult(
                False,
                error_code=ERR_INFERENCE_START_FAILED,
                error_message=f"Failed to create VLA components for place: {exc}",
            )

        vla_client = components["vla_client"]
        task_language_manager = components["task_language_manager"]
        robot_body = context.robot_body

        task_language_manager.currt_language_instruction = instruction
        task_language_manager.config.sub_task_id = 0
        self.send_feedback(goal_handle, 5,
                           f"放置目标: {target}, 语言指令: {instruction}")

        if components_created:
            try:
                self.send_feedback(goal_handle, 7, "启动放置任务的观测和推理线程")
                vla_client.start_observe()
                vla_client.start_inference()
                vla_client.start_visualize()
                vla_client.is_running_action = True
            except Exception as exc:
                context.clear_vla_components()
                self.send_feedback(goal_handle, 0,
                                   f"无法启动放置任务推理: {exc}")
                return TaskResult(
                    False,
                    error_code=ERR_INFERENCE_START_FAILED,
                    error_message=f"Failed to start place inference: {exc}",
                )

        try:
            context._active_vla_client = vla_client

            initial_action = self._move_to_initial_pose(
                goal_handle, robot_body, target, context
            )
            if isinstance(initial_action, TaskResult):
                return initial_action

            blend_config = {
                "start_action": initial_action,
                "duration": 3.0,
            }

            result = run_vla_control_only(
                goal_handle=goal_handle,
                vla_client=vla_client,
                language_instruction=instruction,
                max_duration=30.0,
                complete_threshold=0.45,
                complete_hold_time=1.0,
                blend_config=blend_config,
            )

            if not result.success:
                if result.error_code == ERR_TASK_TIMEOUT:
                    return TaskResult(
                        False,
                        error_code=ERR_PLACE_TIMEOUT,
                        error_message="Place task timed out",
                    )
                return result

            return result

        finally:
            context._active_vla_client = None