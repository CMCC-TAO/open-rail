"""Robot-facing teleop action layouts and JointState conversion.

This module owns the contract between the teleop nodes under ``teleop/`` and the
VLA client bridge.  A teleop producer publishes one value per target-robot
action dimension, already expressed in the robot's native hand units.  The
bridge therefore only validates/passes through the ordered message and never
decides hand widths or continuous-vs-discrete semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from teleop.config import config_get as _cfg_get

LEFT_ARM_JOINT_NAMES = tuple(f"left_arm_joint{i}" for i in range(1, 8))
RIGHT_ARM_JOINT_NAMES = tuple(f"right_arm_joint{i}" for i in range(1, 8))
ARM_JOINT_NAMES = LEFT_ARM_JOINT_NAMES + RIGHT_ARM_JOINT_NAMES

HAND_LAYOUT_KEYS = ("hand", "gripper", "hand_as_gripper")

@dataclass(frozen=True)
class TeleopActionLayout:
    """Canonical action layout for one robot end-effector profile."""

    action_names: tuple[str, ...]
    left_hand_names: tuple[str, ...]
    right_hand_names: tuple[str, ...]
    hand_value_scale: float = 1.0

    @property
    def action_dim(self) -> int:
        return len(self.action_names)

    @property
    def hand_widths(self) -> tuple[int, int]:
        return len(self.left_hand_names), len(self.right_hand_names)

    @property
    def left_hand_slice(self) -> slice:
        return slice(14, 14 + len(self.left_hand_names))

    @property
    def right_hand_slice(self) -> slice:
        return slice(14 + len(self.left_hand_names), self.action_dim)


def _robot_hand_layout(robot_config) -> tuple[dict, dict]:
    action_layout = _cfg_get(robot_config, "action_layout", None)
    if not action_layout:
        raise ValueError("Robot configuration must define action_layout for teleop")
    arm_layout = _cfg_get(action_layout, "arm", None)
    hand_layout = None
    for key in HAND_LAYOUT_KEYS:
        candidate = _cfg_get(action_layout, key, None)
        if candidate is not None:
            hand_layout = candidate
            break
    if arm_layout is None or hand_layout is None:
        raise ValueError("Robot action_layout must contain arm and hand/gripper segments")
    if (int(_cfg_get(arm_layout, "start", -1)), int(_cfg_get(arm_layout, "end", -1))) != (0, 14):
        raise ValueError("Teleop currently requires a 14-D arm segment at action indices 0:14")
    return arm_layout, hand_layout


def _hand_preset_scale(hand_layout) -> float:
    """Infer the native hand value scale from configured side presets."""

    presets = _cfg_get(hand_layout, "presets", None)
    maximum = 1.0
    for side in ("left", "right"):
        side_presets = _cfg_get(presets, side, None)
        if not side_presets:
            continue
        values = side_presets.values() if hasattr(side_presets, "values") else []
        for value in values:
            try:
                maximum = max(maximum, *(abs(float(item)) for item in value))
            except (TypeError, ValueError):
                continue
    return maximum


def action_layout_from_robot_config(robot_config) -> TeleopActionLayout:
    """Derive teleop joint names and hand widths from a robot config."""

    _, hand_layout = _robot_hand_layout(robot_config)
    hand_start = int(_cfg_get(hand_layout, "start", 14))
    hand_end = int(_cfg_get(hand_layout, "end", 14))
    width = hand_end - hand_start
    if width <= 0:
        raise ValueError(f"Robot hand/gripper width must be positive, got {width}")

    presets = _cfg_get(hand_layout, "presets", None)
    left_preset = _cfg_get(_cfg_get(presets, "left", None), "Default", None)
    right_preset = _cfg_get(_cfg_get(presets, "right", None), "Default", None)
    if left_preset is not None and right_preset is not None:
        left_width, right_width = len(left_preset), len(right_preset)
        if left_width + right_width != width:
            raise ValueError(
                f"Robot hand preset widths {left_width}+{right_width} do not match action width {width}"
            )
    elif width % 2 == 0:
        left_width = right_width = width // 2
    else:
        raise ValueError(
            f"Robot hand width {width} is odd and requires left/right preset dimensions"
        )
    left_names = tuple(f"left_hand_joint{i}" for i in range(1, left_width + 1))
    right_names = tuple(f"right_hand_joint{i}" for i in range(1, right_width + 1))
    return TeleopActionLayout(
        action_names=ARM_JOINT_NAMES + left_names + right_names,
        left_hand_names=left_names,
        right_hand_names=right_names,
        hand_value_scale=_hand_preset_scale(hand_layout),
    )


def action_layout_from_action_names(
    action_names: Sequence[str],
    *,
    hand_value_scale: float = 1.0,
) -> TeleopActionLayout:
    """Rebuild a canonical layout from a serialized action-name list."""

    names = tuple(str(name) for name in action_names)
    if len(names) < 16 or names[:14] != ARM_JOINT_NAMES:
        raise ValueError("Action names must start with the 14 canonical arm joint names")
    hand_names = names[14:]
    try:
        split = hand_names.index("right_hand_joint1")
    except ValueError as exc:
        raise ValueError("Action names must contain right_hand_joint1") from exc
    left_names = hand_names[:split]
    right_names = hand_names[split:]
    if not left_names or not right_names:
        raise ValueError("Action names must contain both left and right hand dimensions")
    expected_left = tuple(f"left_hand_joint{i}" for i in range(1, len(left_names) + 1))
    expected_right = tuple(f"right_hand_joint{i}" for i in range(1, len(right_names) + 1))
    if left_names != expected_left or right_names != expected_right:
        raise ValueError("Action hand names must use contiguous left_hand_jointN/right_hand_jointN names")
    return TeleopActionLayout(
        action_names=names,
        left_hand_names=left_names,
        right_hand_names=right_names,
        hand_value_scale=float(hand_value_scale),
    )


def action_layout_for_robot(robot_type: str) -> TeleopActionLayout:
    """Return the teleop action layout registered for ``robot_type``."""

    from conf.robots_conf import get_robot_config

    robot_config = get_robot_config(robot_type)
    if robot_config is None:
        raise ValueError(f"No robot configuration registered for {robot_type!r}")
    return action_layout_from_robot_config(robot_config)
