"""Robot-bound mappings between normalized teleop hand commands and native hands.

Continuous teleop modes (incremental / proportional) drive one normalized
scalar per hand. A hand range is a pair of native command vectors
``(at_0, at_1)``: the scalar ``0.0`` maps to ``at_0``, ``1.0`` maps to ``at_1``
and values in between are linearly interpolated per coordinate. Coordinates
where both endpoints are equal stay fixed, so a range such as
``[0, 0, 1000, 1000, 0, 0] -> [1000, 0, 1000, 1000, 0, 1000]`` only moves the
first and last joints.

Ranges are configured per robot in the teleop YAML as
``left_hand_continuous_range`` and ``right_hand_continuous_range``, written
like ``left_hand_discrete_values``.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

HandRange = tuple[list[float], list[float]]

HAND_CONTROL_MODES = {"incremental", "proportional", "discrete"}


def normalize_hand_range(value: Any, *, name: str) -> HandRange:
    """Validate a YAML ``[[at_0...], [at_1...]]`` hand range."""

    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{name} must be a list of two native hand vectors [at_0, at_1]")
    endpoints = []
    for index, vector in enumerate(value):
        if not isinstance(vector, (list, tuple)) or not vector:
            raise ValueError(f"{name}[{index}] must be a non-empty list")
        values = []
        for item in vector:
            try:
                number = float(item)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{name}[{index}] contains a non-numeric value: {item!r}") from exc
            if not math.isfinite(number):
                raise ValueError(f"{name}[{index}] values must be finite")
            values.append(number)
        endpoints.append(values)
    start, end = endpoints
    if len(start) != len(end):
        raise ValueError(f"{name} endpoints must have the same width, got {len(start)} and {len(end)}")
    if start == end:
        raise ValueError(f"{name} endpoints are identical; at least one coordinate must change")
    return start, end


def normalize_hand_control_mode(value: Any) -> str:
    """Canonicalize a hand-control mode name."""

    mode = str(value or "incremental").strip().lower().replace("-", "_")
    aliases = {
        "button": "incremental",
        "buttons": "incremental",
        "legacy": "incremental",
        "binary": "incremental",
        "increment": "incremental",
        "direct": "proportional",
        "analog": "proportional",
        "trigger": "proportional",
        "stepped": "discrete",
        "step": "discrete",
    }
    mode = aliases.get(mode, mode)
    if mode not in HAND_CONTROL_MODES:
        raise ValueError(
            f"Unsupported hand control mode {value!r}; expected one of {sorted(HAND_CONTROL_MODES)}"
        )
    return mode


def normalize_discrete_values(values: Any, *, name: str, width: int) -> list[list[float]]:
    """Validate a per-hand list of full-width discrete hand commands."""

    if values is None:
        raise ValueError(f"{name} is required in discrete hand-control mode")
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError(f"{name} must be a non-empty YAML list")
    normalized = []
    for index, value in enumerate(values):
        if not isinstance(value, (list, tuple)) or len(value) != width:
            raise ValueError(f"{name}[{index}] must contain {width} values")
        vector = []
        for item in value:
            try:
                number = float(item)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{name}[{index}] contains a non-numeric value: {item!r}") from exc
            if not math.isfinite(number):
                raise ValueError(f"{name}[{index}] values must be finite")
            vector.append(number)
        normalized.append(vector)
    return normalized


def hand_output_width(mode: str, hand_range: HandRange | None, *, robot_width: int) -> int:
    """Return the native command width produced by one hand control mode."""

    if str(mode) == "discrete":
        return int(robot_width)
    if hand_range is not None:
        return len(hand_range[0])
    if int(robot_width) == 1:
        return 1
    raise ValueError(
        "A multi-coordinate robot hand requires a continuous range mapping; "
        f"got robot width {robot_width} without a hand range"
    )


def hand_command_to_native(
    command: Sequence[float],
    *,
    mode: str,
    hand_range: HandRange | None,
    robot_width: int,
) -> list[float]:
    """Expand one internal hand command to the target robot's native width."""

    values = [float(value) for value in command]
    if str(mode) == "discrete":
        if len(values) != int(robot_width):
            raise ValueError(f"Discrete hand command has {len(values)} values, expected {robot_width}")
        return values
    if len(values) != 1:
        raise ValueError(f"Continuous hand command must have one scalar, got {len(values)}")
    if hand_range is not None:
        return expand_hand_scalar(values[0], hand_range)
    if int(robot_width) != 1:
        raise ValueError(
            f"Continuous hand command cannot be expanded to robot width {robot_width} without a hand range"
        )
    return values


def hand_feedback_to_control(
    values: Sequence[float],
    *,
    mode: str,
    hand_range: HandRange | None,
    robot_width: int,
) -> list[float]:
    """Convert native robot hand feedback to the internal control representation."""

    native = [float(value) for value in values]
    if len(native) != int(robot_width):
        raise ValueError(f"Hand feedback has {len(native)} values, expected {robot_width}")
    if str(mode) == "discrete":
        return native
    if hand_range is not None:
        if len(hand_range[0]) != int(robot_width):
            raise ValueError(
                f"Hand range width {len(hand_range[0])} does not match robot hand width {robot_width}"
            )
        return [project_hand_vector(native, hand_range)]
    if int(robot_width) == 1:
        return native
    raise ValueError(
        f"Cannot project {robot_width}-coordinate hand feedback without a hand range mapping"
    )


def nearest_discrete_index(values: Sequence[Sequence[float]], current: Sequence[float]) -> int:
    """Return the discrete hand vector with the smallest Manhattan distance."""

    if not values:
        return -1
    current_arr = [float(value) for value in current]
    widths = {len(value) for value in values}
    if widths != {len(current_arr)}:
        return -1
    distances = [
        sum(abs(float(value) - target) for value, target in zip(vector, current_arr))
        for vector in values
    ]
    return int(min(range(len(distances)), key=distances.__getitem__))


def expand_hand_scalar(value: float, hand_range: HandRange) -> list[float]:
    """Map a normalized hand scalar onto its native hand range."""

    alpha = min(max(float(value), 0.0), 1.0)
    start, end = hand_range
    return [a + alpha * (b - a) for a, b in zip(start, end)]


def project_hand_vector(values: Sequence[float], hand_range: HandRange) -> float:
    """Return the normalized scalar whose range point is closest to ``values``."""

    start, end = hand_range
    if len(values) != len(start):
        raise ValueError(f"hand vector has {len(values)} values, expected {len(start)}")
    span = [b - a for a, b in zip(start, end)]
    denom = sum(d * d for d in span)
    alpha = sum((float(v) - a) * d for v, a, d in zip(values, start, span)) / denom
    return min(max(alpha, 0.0), 1.0)


