#!/usr/bin/env python3
"""Quest3 VR whole-body teleop bridge node for ``client.core.teleop_bridge.RosTeleopBridge``.

=============================================================================
Architecture Overview
=============================================================================

This node replaces the old C++ whole-body command publishers with a pure Python
ROS2 node that speaks the VLA teleop bridge interface directly:

* Publishes ``sensor_msgs/JointState`` to ``/target_robot/joint_commands``
* Optionally publishes ``std_msgs/Float64`` reset edge to ``/custom/custom_a``

=============================================================================
Data Flow
=============================================================================

Quest3 VR headset ---[TCP JSON]---> QuestTcpServer ---> BridgeState
                                                          |
                                            VRWholeBodyBridgeNode._tick()
                                                          |
                                   ┌── Arm Control ──┼── Gripper Control ─┐
                                   │                  │                    │
                              FSM-driven IK    Incremental/proportional   Reset
                                   │                                       │
                                   └────── action[:14] ──── action[14:16] ──┘
                                                          |
                                            _publish_joint_command()
                                                          |
                                            /target_robot/joint_commands
                                                          |
                                            RosTeleopBridge._command_cb()
                                                          |
                                            VLA Client action_arbiter

=============================================================================
Arm Control State Machine
=============================================================================

        trigger pressed (trigger > threshold)
   AUTO ─────────────────────────────────────> MANUAL
    ^                                             │
    │                                             │ trigger released
    │                                             v
    └──────────────────────────────────── TRANSITION_EXIT
                 [fixed target hold completes]

During transitions:
  - ``trigger_ref_ee_pose`` is captured once on the trigger-press edge and
    remains fixed for the whole intervention.
  - Human controller deltas are applied at full scale immediately.
  - Releasing the trigger bakes the final target into a fixed exit-hold pose.

=============================================================================
Quest3 TCP JSON Packet Format (compatible with original
``vr_controller_bridge/tcp_receiver.py``)
=============================================================================
One JSON object per line, newline-delimited.
"""


from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Fixed JointState command order expected by the VLA teleop bridge.
# Layout: left arm 7 + right arm 7 + left gripper 1 + right gripper 1 = 16 dims
# ---------------------------------------------------------------------------
BRIDGE_JOINT_NAMES = [
    *(f"left_arm_joint{i}" for i in range(1, 8)),
    *(f"right_arm_joint{i}" for i in range(1, 8)),
    "left_hand_joint1",
    "right_hand_joint1",
]

# Supported reset behaviours
RESET_MODES = {"topic", "joint_command", "none"}
# Gripper control strategies
GRIPPER_CONTROL_MODES = {"incremental", "proportional"}

# ---------------------------------------------------------------------------
# Arm control FSM states
#   AUTO:               policy-driven, no human intervention
#   MANUAL:             full human control via IK immediately after trigger press
#   TRANSITION_EXIT:    trigger released → hold final target, then return to auto
# ---------------------------------------------------------------------------
ARM_CONTROL_AUTO = "auto"
ARM_CONTROL_MANUAL = "manual"
ARM_CONTROL_TRANSITION_EXIT = "transition_exit"


# ===========================================================================
# Config parsing helpers
# ===========================================================================

def _normalize_reset_mode(value: Any) -> str:
    """Canonicalize user-facing reset mode strings (topic / joint_command / none)."""
    mode = str(value or "joint_command").strip().lower().replace("-", "_")
    aliases = {
        "disabled": "none",
        "off": "none",
        "joint": "joint_command",
        "command": "joint_command",
        "joint_commands": "joint_command",
    }
    mode = aliases.get(mode, mode)
    if mode not in RESET_MODES:
        raise ValueError(f"Unsupported reset_mode {value!r}; expected one of {sorted(RESET_MODES)}")
    return mode


def _normalize_gripper_control_mode(value: Any) -> str:
    """Canonicalize gripper mode to incremental (button-based) or proportional (trigger-based)."""
    mode = str(value or "incremental").strip().lower().replace("-", "_")
    aliases = {
        "button": "incremental",
        "buttons": "incremental",
        "legacy": "incremental",
        "direct": "proportional",
        "analog": "proportional",
        "trigger": "proportional",
    }
    mode = aliases.get(mode, mode)
    if mode not in GRIPPER_CONTROL_MODES:
        raise ValueError(
            f"Unsupported gripper_control_mode {value!r}; expected one of {sorted(GRIPPER_CONTROL_MODES)}"
        )
    return mode


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML config file (requires PyYAML)."""
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to load VR whole-body bridge config.") from exc

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a YAML mapping: {path}")
    return data


def _resolve_relative_config_paths(config: dict[str, Any], config_path: Path) -> None:
    """Resolve file paths relative to the YAML config file's directory (e.g. urdf_path)."""
    ik_config = config.get("ik")
    if not isinstance(ik_config, dict):
        return
    urdf_path = ik_config.get("urdf_path")
    if not isinstance(urdf_path, str) or not urdf_path:
        return
    path = Path(urdf_path).expanduser()
    if not path.is_absolute():
        ik_config["urdf_path"] = str((config_path.parent / path).resolve())


def _as_array(values, *, length: int, default: float = 0.0) -> np.ndarray:
    """Coerce any value into a fixed-length float ndarray (fills default when None)."""
    if values is None:
        return np.full(length, default, dtype=float)
    arr = np.asarray(values, dtype=float).reshape(-1)
    if arr.size != length:
        raise ValueError(f"Expected {length} values, got {arr.size}")
    return arr


def _is_finite_vector(values, length: int | None = None) -> bool:
    """Return True if values form an all-finite vector (used for IK input validation)."""
    try:
        arr = np.asarray(values, dtype=float).reshape(-1)
    except (TypeError, ValueError):
        return False
    if length is not None and arr.size != length:
        return False
    return bool(np.all(np.isfinite(arr)))


def _as_rotation_matrix(values, *, name: str) -> np.ndarray:
    if values is None:
        return np.eye(3, dtype=float)
    arr = np.asarray(values, dtype=float)
    if arr.shape != (3, 3):
        raise ValueError(f"{name}.rotation_mat must be a 3x3 matrix, got shape {arr.shape}")
    if not np.allclose(arr.T @ arr, np.eye(3), atol=1e-6):
        raise ValueError(f"{name}.rotation_mat must be orthonormal")
    det = float(np.linalg.det(arr))
    if not math.isclose(det, 1.0, abs_tol=1e-6):
        raise ValueError(f"{name}.rotation_mat determinant must be 1.0, got {det}")
    return arr


# ===========================================================================
# Quaternion and rotation math utilities
# ===========================================================================

def _quat_mul(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """Hamilton product: q1 * q2. Result is normalized."""
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    out = np.array(
        [
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        ],
        dtype=float,
    )
    norm = np.linalg.norm(out)
    return out / norm if norm > 0 else np.array([0.0, 0.0, 0.0, 1.0], dtype=float)


def _quat_inv(q: np.ndarray) -> np.ndarray:
    """Inverse (conjugate) of a unit quaternion."""
    x, y, z, w = q
    return np.array([-x, -y, -z, w], dtype=float) / max(float(np.dot(q, q)), 1e-12)


def _quat_to_rotvec(q: np.ndarray) -> np.ndarray:
    """Convert a unit quaternion to an axis-angle rotation vector."""
    q = np.asarray(q, dtype=float)
    norm = np.linalg.norm(q)
    if norm <= 0:
        return np.zeros(3, dtype=float)
    x, y, z, w = q / norm
    w = float(np.clip(w, -1.0, 1.0))
    angle = 2.0 * math.acos(w)
    s = math.sqrt(max(1.0 - w * w, 0.0))
    if s < 1e-8:
        return np.zeros(3, dtype=float)
    return np.array([x, y, z], dtype=float) / s * angle


def _rotvec_to_quat(rotvec: np.ndarray) -> np.ndarray:
    """Convert an axis-angle rotation vector to a unit quaternion."""
    rotvec = np.asarray(rotvec, dtype=float).reshape(3)
    angle = float(np.linalg.norm(rotvec))
    if angle < 1e-8:
        return np.array([0.0, 0.0, 0.0, 1.0], dtype=float)
    axis = rotvec / angle
    half = angle / 2.0
    return np.array(
        [axis[0] * math.sin(half), axis[1] * math.sin(half), axis[2] * math.sin(half), math.cos(half)],
        dtype=float,
    )


def _rotmat_to_quat(r: np.ndarray) -> np.ndarray:
    """Convert a 3x3 rotation matrix to a unit quaternion (numerically stable)."""
    r = np.asarray(r, dtype=float).reshape(3, 3)
    trace = float(np.trace(r))
    if trace > 0:
        s = 0.5 / math.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (r[2, 1] - r[1, 2]) * s
        y = (r[0, 2] - r[2, 0]) * s
        z = (r[1, 0] - r[0, 1]) * s
    elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
        s = 2.0 * math.sqrt(max(1.0 + r[0, 0] - r[1, 1] - r[2, 2], 0.0))
        w = (r[2, 1] - r[1, 2]) / max(s, 1e-12)
        x = 0.25 * s
        y = (r[0, 1] + r[1, 0]) / max(s, 1e-12)
        z = (r[0, 2] + r[2, 0]) / max(s, 1e-12)
    elif r[1, 1] > r[2, 2]:
        s = 2.0 * math.sqrt(max(1.0 + r[1, 1] - r[0, 0] - r[2, 2], 0.0))
        w = (r[0, 2] - r[2, 0]) / max(s, 1e-12)
        x = (r[0, 1] + r[1, 0]) / max(s, 1e-12)
        y = 0.25 * s
        z = (r[1, 2] + r[2, 1]) / max(s, 1e-12)
    else:
        s = 2.0 * math.sqrt(max(1.0 + r[2, 2] - r[0, 0] - r[1, 1], 0.0))
        w = (r[1, 0] - r[0, 1]) / max(s, 1e-12)
        x = (r[0, 2] + r[2, 0]) / max(s, 1e-12)
        y = (r[1, 2] + r[2, 1]) / max(s, 1e-12)
        z = 0.25 * s
    quat = np.array([x, y, z, w], dtype=float)
    quat /= max(float(np.linalg.norm(quat)), 1e-12)
    return quat


def _quat_to_rotmat(q: np.ndarray) -> np.ndarray:
    """Convert a unit quaternion to a 3x3 rotation matrix."""
    q = np.asarray(q, dtype=float).reshape(4)
    q = q / max(float(np.linalg.norm(q)), 1e-12)
    x, y, z, w = q
    return np.array(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=float,
    )


def _matrix_to_position_quaternion(matrix_flat) -> tuple[np.ndarray, np.ndarray]:
    """Decompose a flat 16-element 4x4 homogeneous transform into position + quaternion."""
    if len(matrix_flat) != 16:
        raise ValueError("Expected a flat 4x4 matrix with 16 values")
    mat = np.asarray(matrix_flat, dtype=float).reshape(4, 4)
    position = mat[:3, 3].copy()
    return position, _rotmat_to_quat(mat[:3, :3])


def _is_valid_unity_transform(matrix_flat, *, origin_epsilon_m: float = 0.0) -> bool:
    """Return True when a Unity 4x4 controller transform is finite and physically plausible.

    Checks performed (in order, short-circuit on first failure):
      1. Type and length: must be list/tuple of exactly 16 floats.
      2. Convertible to a finite 4x4 numpy array.
      3. Homogeneous row must be [0, 0, 0, 1] (rigid-body transform).
      4. Translation norm must exceed ``origin_epsilon_m`` (reject near-zero poses,
         which usually indicate lost tracking when the headset reports identity).
      5. Rotation sub-matrix columns must be unit-length (no scale/shear).
      6. Rotation sub-matrix must be orthogonal (R^T R ≈ I).
      7. Determinant must be ±1 (no reflection / improper rotation).
    """
    # -- 1. Basic type & length guard ----------------------------------------
    if not isinstance(matrix_flat, (list, tuple)) or len(matrix_flat) != 16:
        return False
    # -- 2. Convert to 4x4 matrix, reject non-numeric garbage -----------------
    try:
        mat = np.asarray(matrix_flat, dtype=float).reshape(4, 4)
    except (TypeError, ValueError):
        return False
    # -- 3. Reject NaN / Inf values -------------------------------------------
    if not np.all(np.isfinite(mat)):
        return False
    # -- 4. Verify homogeneous row is [0, 0, 0, 1] ----------------------------
    if not np.allclose(mat[3, :], np.array([0.0, 0.0, 0.0, 1.0]), atol=1e-4):
        return False
    # -- 5. Reject identity / near-origin poses (tracking-loss indicator) -----
    if origin_epsilon_m > 0.0 and float(np.linalg.norm(mat[:3, 3])) <= origin_epsilon_m:
        return False
    # -- 6. Rotation matrix sanity: unit column norms -------------------------
    rot = mat[:3, :3]
    col_norms = np.linalg.norm(rot, axis=0)
    if not np.allclose(col_norms, np.ones(3), atol=1e-2):
        return False
    # -- 7. Rotation matrix orthogonality check -------------------------------
    if not np.allclose(rot.T @ rot, np.eye(3), atol=1e-2):
        return False
    # -- 8. Determinant check: must be proper rotation (det ≈ ±1) -------------
    det = float(np.linalg.det(rot))
    return math.isclose(abs(det), 1.0, rel_tol=1e-2, abs_tol=1e-2)


def _packet_bool(value: Any, *, default: bool = True) -> bool:
    """Parse optional bool-like fields from Quest TCP JSON packets.

    The Quest3 app may send tracking-validity flags in several different formats
    depending on the Unity / app version.  This helper normalises all of them:

    - ``None`` / missing → ``default`` (assume valid unless told otherwise).
    - Python ``bool`` → returned as-is.
    - Numeric (int/float) → standard truthiness (0 → False, non-zero → True).
    - String → case-insensitive match against known truthy / falsy keywords
      (e.g. ``"tracked"`` → True, ``"lost"`` → False).
    - Any other type → ``default``.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        # Truthy keywords (tracking is active / valid)
        if normalized in {"1", "true", "yes", "valid", "tracked", "tracking"}:
            return True
        # Falsy keywords (tracking is lost / invalid)
        if normalized in {"0", "false", "no", "invalid", "lost", "sleeping"}:
            return False
    return default


def _unity_to_ros(pos_u: np.ndarray, quat_u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Convert Unity's left-handed Y-up coordinate frame to ROS right-handed Z-up."""
    x_u, y_u, z_u = pos_u
    qx_u, qy_u, qz_u, qw_u = quat_u
    pos_r = np.array([z_u, -x_u, y_u], dtype=float)
    quat_r = np.array([-qz_u, qx_u, -qy_u, qw_u], dtype=float)
    quat_r /= max(float(np.linalg.norm(quat_r)), 1e-12)
    return pos_r, quat_r


def _apply_local_y_rotation(quat_xyzw: np.ndarray, angle_rad: float) -> np.ndarray:
    """Post-multiply a quaternion by a local Y-axis rotation (used for controller alignment)."""
    qy = np.array([0.0, math.sin(angle_rad / 2.0), 0.0, math.cos(angle_rad / 2.0)], dtype=float)
    return _quat_mul(quat_xyzw, qy)


# ===========================================================================
# Coordinate transform from VR frame to URDF / ROS frame
# ===========================================================================

@dataclass(frozen=True)
class CoordinateTransform:
    """VR-to-URDF coordinate transform loaded from robot config.

    Attributes:
        rotation_mat: 3x3 orthonormal rotation matrix.
        translation_xyz: 3-element translation vector (applied to absolute poses, not deltas).
    """

    rotation_mat: np.ndarray
    translation_xyz: np.ndarray

    @classmethod
    def from_config(
        cls,
        config: dict[str, Any],
        key: str,
        *,
        fallback_key: str | None = None,
    ) -> "CoordinateTransform":
        """Construct from a YAML config dict, optionally falling back to a shared key."""
        source_key = key
        entry = config.get(key)
        if entry is None and fallback_key is not None:
            source_key = fallback_key
            entry = config.get(fallback_key)
        entry = entry or {}
        if not isinstance(entry, dict):
            raise ValueError(f"{source_key} must be a YAML mapping")
        rotation_mat = _as_rotation_matrix(entry.get("rotation_mat"), name=source_key)
        translation_xyz = _as_array(entry.get("translation_xyz"), length=3, default=0.0)
        return cls(
            rotation_mat=rotation_mat,
            translation_xyz=translation_xyz,
        )

    def transform_relative_quat(self, quat_vr_xyzw: np.ndarray) -> np.ndarray:
        """Convert a relative rotation: R_urdf @ R_vr @ R_urdfᵀ (A2D convention)."""
        rot_vr = _quat_to_rotmat(quat_vr_xyzw)
        rot_urdf = self.rotation_mat @ rot_vr @ self.rotation_mat.T
        return _rotmat_to_quat(rot_urdf)

    def transform_relative_pos(self, pos_vr_xyz: np.ndarray) -> np.ndarray:
        """Convert a relative position delta (translation is not applied to deltas)."""
        return self.rotation_mat @ np.asarray(pos_vr_xyz, dtype=float).reshape(3)


# ===========================================================================
# Runtime state data structures
# ===========================================================================

@dataclass
class ControllerSide:
    """Live state and trigger-held reference state for one Quest controller (left or right).

    Key fields for arm control:
        trigger:            Arm trigger value (Quest "grip" button → teleop arm trigger).
        grip:               Gripper control value (Quest "trigger" button → hand).
        trigger_ref_*:      Snapshots taken when the trigger is first pressed; deltas
                            are measured from these reference values.
        exit_hold_*:        Frozen pose when trigger is released, to prevent drift.
        control_state:      Current FSM state (AUTO / MANUAL / TRANSITION_EXIT).
    """

    pose_pos: np.ndarray | None = None
    pose_quat: np.ndarray | None = None
    pose_valid: bool = False
    grip: float = 0.0
    trigger: float = 0.0
    secondary_button: bool = False
    primary_button: bool = False
    # Snapshots captured at trigger-press time (reference for delta calculation)
    trigger_ref_pos: np.ndarray | None = None
    trigger_ref_quat: np.ndarray | None = None
    trigger_ref_action: np.ndarray | None = None
    trigger_ref_ee_pose: np.ndarray | None = None
    # Frozen pose during exit transition
    exit_hold_pos: np.ndarray | None = None
    exit_hold_quat: np.ndarray | None = None
    # FSM state and exit-hold timing
    control_state: str = ARM_CONTROL_AUTO
    transition_elapsed_s: float = 0.0
    was_trigger_active: bool = False
    # Gripper control tracking
    gripper_control_active: bool = False
    gripper_command_initialized: bool = False


@dataclass
class BridgeState:
    """Shared mutable bridge state protected by a lock across ROS and TCP threads.

    Attributes:
        action:           The outgoing 16-D command vector and IK seed.
        reference_action: Latest robot feedback from /joint_states, used as the
                          activation-time seed and inactive-side fallback.
        joint_state_ready: True after at least one valid /joint_states message.
    """

    left: ControllerSide = field(default_factory=ControllerSide)
    right: ControllerSide = field(default_factory=ControllerSide)
    primary_pressed: bool = False
    action: np.ndarray = field(default_factory=lambda: np.zeros(16, dtype=float))
    reference_action: np.ndarray = field(default_factory=lambda: np.zeros(16, dtype=float))
    joint_state_ready: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)


# ===========================================================================
# TCP server for receiving Quest3 controller data
# ===========================================================================

class QuestTcpServer:
    """Newline-delimited JSON TCP server for Quest3 controller packets.

    Runs a dedicated daemon thread that:
    1. Accepts a single TCP client (the Quest3 app).
    2. Reads newline-delimited JSON lines.
    3. Parses left/right controller matrices and buttons.
    4. Updates the shared ``BridgeState`` under lock.

    Packet format (one JSON object per line):
        {
            "left_matrix":  [16 floats],    # 4x4 Unity transform
            "right_matrix": [16 floats],
            "left_is_valid": true,           # optional tracking-valid flag
            "right_is_valid": true,
            "left_buttons": {"grip": 0.0, "trigger": 0.0, "primary_button": false, ...},
            "right_buttons": {...}
        }
    """

    def __init__(
        self,
        node,
        state: BridgeState,
        port: int,
        controller_y_rotation_rad: float,
        invalid_origin_epsilon_m: float,
    ):
        self.node = node
        self.state = state
        self.port = int(port)
        self.controller_y_rotation_rad = float(controller_y_rotation_rad)
        self.invalid_origin_epsilon_m = max(float(invalid_origin_epsilon_m), 0.0)
        self.running = True
        self.server_sock = None
        self.client_sock = None
        self.recv_buffer = ""
        self.total_packets = 0
        self.thread = threading.Thread(target=self._run, name="quest3-tcp-receiver", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        for sock in (self.client_sock, self.server_sock):
            if sock is not None:
                try:
                    sock.close()
                except Exception:
                    pass
        if self.thread.is_alive() and threading.current_thread() is not self.thread:
            self.thread.join(timeout=1.0)

    def _run(self) -> None:
        """Main server loop: accept, receive, parse.

        Uses a 1-second accept timeout and 100ms recv timeout so the loop
        can check ``self.running`` and exit cleanly on shutdown."""
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind(("0.0.0.0", self.port))
        self.server_sock.listen(1)
        self.server_sock.settimeout(1.0)
        self.node.get_logger().info(f"Quest3 TCP server listening on 0.0.0.0:{self.port}")

        while self.running:
            if self.client_sock is None:
                try:
                    client, addr = self.server_sock.accept()
                    client.settimeout(0.1)
                    self.client_sock = client
                    self.recv_buffer = ""
                    self.node.get_logger().info(f"Quest3 client connected from {addr}")
                except socket.timeout:
                    continue
                except OSError:
                    break
                except Exception as exc:
                    self.node.get_logger().warning(f"Quest3 accept error: {exc}")
                    time.sleep(1.0)
                    continue

            try:
                data = self.client_sock.recv(131072)
                if not data:
                    self._close_client("Quest3 closed connection")
                    continue
                self.recv_buffer += data.decode("utf-8", "ignore")
                while "\n" in self.recv_buffer:
                    line, self.recv_buffer = self.recv_buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    self._process_packet(json.loads(line))
            except socket.timeout:
                continue
            except OSError as exc:
                if not self.running:
                    break
                self._close_client(f"Quest3 receive error: {exc}")
            except Exception as exc:
                self._close_client(f"Quest3 receive error: {exc}")

    def _close_client(self, reason: str) -> None:
        if self.running:
            self.node.get_logger().warning(reason)
        if self.client_sock is not None:
            try:
                self.client_sock.close()
            except Exception:
                pass
        self.client_sock = None
        self.recv_buffer = ""

    def _process_packet(self, packet: dict[str, Any]) -> None:
        """Parse one JSON packet and update left/right controller state under lock.

        - ``left_matrix`` / ``right_matrix``: 4x4 Unity transforms → VR pose.
        - Optional ``left_is_valid`` / ``right_is_valid``: controller tracking validity.
        - ``left_buttons`` / ``right_buttons``: button/trigger/grip values.

        Note: Quest "grip" button maps to ``trigger`` (arm teleop activation),
        and Quest "trigger" maps to ``grip`` (hand/gripper control).
        """
        self.total_packets += 1
        left_buttons = packet.get("left_buttons", {}) or {}
        right_buttons = packet.get("right_buttons", {}) or {}

        with self.state.lock:
            left_valid = self._packet_side_valid(packet, left_buttons, "left")
            right_valid = self._packet_side_valid(packet, right_buttons, "right")
            self._update_pose(self.state.left, packet.get("left_matrix"), left_valid)
            self._update_pose(self.state.right, packet.get("right_matrix"), right_valid)
            self._update_buttons(self.state.left, left_buttons)
            self._update_buttons(self.state.right, right_buttons)

    @staticmethod
    def _packet_side_valid(packet: dict[str, Any], buttons: dict[str, Any], side_name: str) -> bool:
        """Resolve the tracking-validity flag for one controller side.

        The Quest3 app reports tracking status in various JSON locations across
        different versions.  We probe multiple possible keys in priority order,
        falling back to the previous result when a key is absent:

        1. ``{side}_is_valid`` at the packet root (preferred, newest format).
        2. ``{side}_valid`` at the packet root (legacy format).
        3. ``is_valid`` / ``valid`` / ``tracking`` inside the buttons sub-object.

        If no key is found at any level the default is ``True`` (assume valid).
        """
        # Try packet-level keys first (most reliable)
        valid = _packet_bool(packet.get(f"{side_name}_is_valid"), default=True)
        valid = _packet_bool(packet.get(f"{side_name}_valid"), default=valid)
        # Fall back to buttons sub-object keys
        valid = _packet_bool(buttons.get("is_valid"), default=valid)
        valid = _packet_bool(buttons.get("valid"), default=valid)
        valid = _packet_bool(buttons.get("tracking"), default=valid)
        return valid

    def _update_pose(self, side: ControllerSide, matrix, is_valid: bool) -> None:
        """Convert a Unity 4x4 matrix to VR-frame position and quaternion."""
        if not is_valid or not _is_valid_unity_transform(
            matrix,
            origin_epsilon_m=self.invalid_origin_epsilon_m,
        ):
            side.pose_valid = False
            return
        pos_u, quat_u = _matrix_to_position_quaternion(matrix)
        pos_vr, quat_vr = _unity_to_ros(pos_u, quat_u)
        quat_vr = _apply_local_y_rotation(quat_vr, self.controller_y_rotation_rad)
        side.pose_pos = pos_vr
        side.pose_quat = quat_vr
        side.pose_valid = True

    @staticmethod
    def _update_buttons(side: ControllerSide, buttons: dict[str, Any]) -> None:
        """Map Quest button names to controller state fields.

        Naming convention from the original Unity bridge:
          - "grip"   → side.trigger  (arm teleop enable)
          - "trigger" → side.grip     (hand close/open)
        """
        side.trigger = float(buttons.get("grip", 0.0))
        side.grip = float(buttons.get("trigger", 0.0))
        side.primary_button = bool(buttons.get("primary_button", False))
        side.secondary_button = bool(buttons.get("secondary_button", False))


# ===========================================================================
# Inverse Kinematics solver adapter
# ===========================================================================

class KineOptTeleopIK:
    """Adapter that turns Quest controller deltas into per-arm IK solutions.

    Two solver backends are supported:
      - ``cpp``:   ``kine_solver_py.SingleArmKineSolver`` (fast native solver).
      - ``casadi``: ``casadi_ik_cpp.PinocchioCasadiChunkKineSolver`` (optimization-based).

    The IK pipeline works as follows:
    1. Compute a target end-effector pose from VR controller delta
       (``target_pose()``).
    2. Use the current joint positions as the IK seed.
    3. Call the solver backend.
    4. Return the solution or None on failure (caller holds previous command).

    For xacro URDF files, the adapter auto-expands them via the ``xacro`` CLI tool.
    """

    def __init__(
        self,
        config: dict[str, Any],
        *,
        position_scale: float,
        orientation_scale: float,
        control_dt: float | None,
        logger,
    ):
        self.enabled = bool(config.get("enabled", True))
        self.position_scale = float(position_scale)
        self.orientation_scale = float(orientation_scale)
        self.ref_frame = str(config.get("ref_frame", "world"))
        self.rotation_type = str(config.get("rotation_type", "quat"))
        self.solver_backend = str(config.get("solver_backend", "cpp")).lower()
        self.casadi_dt = float(config.get("dt", control_dt if control_dt is not None else 0.01))
        self.casadi_kwargs = {
            "pos_weight": float(config.get("pos_weight", 50.0)),
            "ori_weight": float(config.get("ori_weight", 10.0)),
            "smooth_weight": float(config.get("smooth_weight", 2.0)),
            "accel_smooth_weight": float(
                config.get("accel_smooth_weight", config.get("accel_weight", 0.1))
            ),
            "anchor_weight": float(config.get("anchor_weight", 1.0)),
            "rest_weight": float(config.get("rest_weight", 0.1)),
            "ipopt_max_iter": int(config.get("ipopt_max_iter", 200)),
        }
        self.logger = logger
        self._last_warn_s = 0.0
        self.solvers = {}
        self._tmpdir: tempfile.TemporaryDirectory[str] | None = None
        xacro_prefixes = config.get("xacro_ament_prefix_paths", [])
        if isinstance(xacro_prefixes, (str, Path)):
            xacro_prefixes = [str(xacro_prefixes)]
        self.xacro_ament_prefix_paths = [str(Path(p).expanduser()) for p in xacro_prefixes]

        if not self.enabled:
            return

        SingleArmKineSolver = self._import_solver()

        urdf_path = self._prepare_urdf_path(str(config["urdf_path"]))
        for side in ("left", "right"):
            side_cfg = config.get(side, {}) or {}
            if self.solver_backend == "casadi":
                self.solvers[side] = SingleArmKineSolver(
                    urdf_path,
                    str(side_cfg["base_link"]),
                    str(side_cfg["tip_link"]),
                    None,
                    **self.casadi_kwargs,
                )
            else:
                self.solvers[side] = SingleArmKineSolver(
                    urdf_path,
                    str(side_cfg["base_link"]),
                    str(side_cfg["tip_link"]),
                )
        logger.info(f"kine_opt IK initialized with backend={self.solver_backend}, URDF: {urdf_path}")

    def _import_solver(self):
        if self.solver_backend == "cpp":
            try:
                from kine_solver_py import SingleArmKineSolver
            except Exception as exc:
                raise RuntimeError(
                    "Cannot import kine_solver_py.SingleArmKineSolver. "
                    "Install /jiayindeng/kine_opt into the active system/ROS Python environment "
                    "before starting Quest3 teleop."
                ) from exc
            return SingleArmKineSolver

        if self.solver_backend == "casadi":
            try:
                from casadi_ik_cpp import PinocchioCasadiChunkKineSolver
            except Exception as exc:
                raise RuntimeError(
                    "Cannot import casadi_ik_cpp.PinocchioCasadiChunkKineSolver. "
                    "Install /jiayindeng/kine_opt with CasADi support into the active "
                    "system/ROS Python environment before starting Quest3 teleop."
                ) from exc
            return PinocchioCasadiChunkKineSolver

        if self.solver_backend != "cpp":
            raise RuntimeError(
                "Unsupported Quest3 IK backend "
                f"{self.solver_backend!r}; expected `cpp` or `casadi`."
            )

    def _pose_from_solver(self, pose: np.ndarray) -> np.ndarray:
        return np.asarray(pose, dtype=float).reshape(-1)

    def _pose_to_solver(self, pose: np.ndarray) -> np.ndarray:
        return np.asarray(pose, dtype=float).reshape(-1)

    def _prepare_urdf_path(self, urdf_path: str) -> str:
        """Resolve the URDF path; auto-expand .xacro files via the xacro CLI tool."""
        path = Path(urdf_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"kine_opt URDF does not exist: {path}")
        if path.suffix != ".xacro":
            return str(path)

        xacro = shutil.which("xacro")
        if not xacro:
            raise RuntimeError(f"kine_opt URDF is xacro but `xacro` is not available: {path}")

        self._tmpdir = tempfile.TemporaryDirectory(prefix="quest3_ik_")
        output = Path(self._tmpdir.name) / f"{path.stem}.urdf"
        try:
            env = os.environ.copy()
            if self.xacro_ament_prefix_paths:
                current_prefix = env.get("AMENT_PREFIX_PATH", "")
                env["AMENT_PREFIX_PATH"] = os.pathsep.join(
                    [*self.xacro_ament_prefix_paths, current_prefix]
                ).rstrip(os.pathsep)
            result = subprocess.run(
                [xacro, str(path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"Failed to expand xacro for kine_opt: {path}\n{exc.stderr.strip()}"
            ) from exc
        output.write_text(result.stdout, encoding="utf-8")
        self.logger.info(f"Expanded xacro for kine_opt: {path} -> {output}")
        return str(output)

    def forward_pose(self, side_name: str, q: np.ndarray) -> np.ndarray | None:
        """Compute forward kinematics: joint angles → 7-D end-effector pose (pos + quat)."""
        if not self.enabled:
            return None
        if not _is_finite_vector(q, 7):
            self._warn_throttled(f"Skip kine_opt FK for {side_name} arm because q is invalid.")
            return None
        solver = self.solvers[side_name]
        try:
            pose = self._pose_from_solver(
                solver.solve_fk_local_model(
                    np.asarray(q, dtype=float),
                    self.ref_frame,
                    self.rotation_type,
                )
            )
        except Exception as exc:
            self._warn_throttled(f"kine_opt FK failed for {side_name} arm: {exc}")
            return None
        if pose.size != 7:
            self._warn_throttled(f"kine_opt FK returned pose length {pose.size}, expected 7.")
            return None
        if not np.all(np.isfinite(pose)):
            self._warn_throttled(f"kine_opt FK returned non-finite pose for {side_name} arm.")
            return None
        return pose

    def solve(
        self,
        side_name: str,
        side: ControllerSide,
        q_init: np.ndarray,
        vr_to_urdf: CoordinateTransform,
        base_vr_to_urdf: CoordinateTransform,
    ) -> np.ndarray | None:
        """Run IK for one arm given the current controller state.

        Steps:
        1. Compute target end-effector pose from VR controller delta.
        2. Use ``q_init`` (current joint command) as the IK seed.
        3. Call the solver backend and return the 7-D joint solution.

        Returns None if IK fails or inputs are invalid; caller should hold.
        """
        if not self.enabled:
            return None
        if (
            side.pose_pos is None
            or side.pose_quat is None
            or side.trigger_ref_pos is None
            or side.trigger_ref_quat is None
            or side.trigger_ref_ee_pose is None
        ):
            return None

        target_pose = self.target_pose(side, vr_to_urdf, base_vr_to_urdf)
        if target_pose is None:
            return None

        solver = self.solvers[side_name]
        q_seed = np.asarray(q_init, dtype=float)
        if not _is_finite_vector(q_seed, 7):
            self._warn_throttled(f"Skip kine_opt IK for {side_name} arm because q_seed is invalid.")
            return None
        solver_target = self._pose_to_solver(target_pose)
        if not _is_finite_vector(solver_target, 7):
            self._warn_throttled(f"Skip kine_opt IK for {side_name} arm because target pose is invalid.")
            return None
        # CasADi and the older C++ backend expose slightly different solve APIs.
        try:
            if self.solver_backend == "casadi":
                q_solution, success_flags = solver.solve_ik_local_model_traj_simple(
                    solver_target.reshape(1, -1),
                    q_seed,
                    self.casadi_dt,
                    self.rotation_type,
                )
                success = bool(success_flags and success_flags[0])
                q_solution = np.asarray(q_solution, dtype=float).reshape(-1)[:7]
            else:
                q_solution, success = solver.solve_ik_local_model(
                    solver_target,
                    q_seed,
                    self.ref_frame,
                    self.rotation_type,
                )
                q_solution = np.asarray(q_solution, dtype=float).reshape(-1)[:7]
        except Exception as exc:
            self._warn_throttled(f"kine_opt IK failed for {side_name} arm: {exc}")
            return None
        if not success:
            self._warn_throttled(f"kine_opt IK failed for {side_name} arm; holding previous command.")
            return None
        if not _is_finite_vector(q_solution, 7):
            self._warn_throttled(f"kine_opt IK returned non-finite solution for {side_name} arm; holding previous command.")
            return None
        return q_solution

    def target_pose(
        self,
        side: ControllerSide,
        vr_to_urdf: CoordinateTransform,
        base_vr_to_urdf: CoordinateTransform,
    ) -> np.ndarray | None:
        """Compute the target end-effector pose (7-D: position + quaternion).

        The target is derived from:
          - trigger_ref_ee_pose:  the anchor EE pose at trigger-press time.
          - pose_pos / pose_quat: current VR controller pose.

        During TRANSITION_EXIT, the controller pose is frozen (exit_hold_*)
        so releasing the trigger does not cause positional drift.

        Returns the 7-D target pose or None if inputs are invalid.
        """
        if (
            side.pose_pos is None
            or side.pose_quat is None
            or side.trigger_ref_pos is None
            or side.trigger_ref_quat is None
            or side.trigger_ref_ee_pose is None
        ):
            return None

        if not (
            _is_finite_vector(side.pose_pos, 3)
            and _is_finite_vector(side.pose_quat, 4)
            and _is_finite_vector(side.trigger_ref_pos, 3)
            and _is_finite_vector(side.trigger_ref_quat, 4)
            and _is_finite_vector(side.trigger_ref_ee_pose, 7)
        ):
            self._warn_throttled("Skip kine_opt IK because teleop target inputs are invalid.")
            return None

        base_pose = np.asarray(side.trigger_ref_ee_pose, dtype=float).reshape(7)
        pose_pos = side.pose_pos
        pose_quat = side.pose_quat
        if side.control_state == ARM_CONTROL_TRANSITION_EXIT:
            pose_pos = side.exit_hold_pos if side.exit_hold_pos is not None else pose_pos
            pose_quat = side.exit_hold_quat if side.exit_hold_quat is not None else pose_quat
            if not (_is_finite_vector(pose_pos, 3) and _is_finite_vector(pose_quat, 4)):
                self._warn_throttled("Skip kine_opt IK because teleop exit-hold pose is invalid.")
                return None

        # Controller deltas are always measured from the pose captured when trigger was pressed.
        delta_pos_vr = pose_pos - side.trigger_ref_pos
        delta_pos = base_vr_to_urdf.transform_relative_pos(delta_pos_vr) * self.position_scale
        delta_quat_vr = _quat_mul(_quat_inv(side.trigger_ref_quat), pose_quat)
        # Match the C++ A2D controller: convert the relative rotation by R * delta_R * R.T.
        delta_quat_urdf = vr_to_urdf.transform_relative_quat(delta_quat_vr)
        delta_rot = _quat_to_rotvec(delta_quat_urdf)
        delta_quat = _rotvec_to_quat(delta_rot * self.orientation_scale)

        target_pose = np.empty(7, dtype=float)
        target_pose[:3] = base_pose[:3] + delta_pos
        target_pose[3:7] = _quat_mul(base_pose[3:7], delta_quat)
        if not np.all(np.isfinite(target_pose)):
            self._warn_throttled("Skip kine_opt IK because target pose became non-finite.")
            return None
        return target_pose

    def _warn_throttled(self, message: str, period_s: float = 1.0) -> None:
        """Log a warning at most once per ``period_s`` seconds to avoid log spam."""
        now = time.time()
        if now - self._last_warn_s >= period_s:
            self._last_warn_s = now
            self.logger.warning(message)


def _load_controller_transforms(config: dict[str, Any]) -> dict[str, CoordinateTransform]:
    """Load per-side transforms, falling back to one shared arm transform when present."""
    return {
        "head": CoordinateTransform.from_config(config, "rot_head_from_vr_to_urdf"),
        "base": CoordinateTransform.from_config(config, "rot_base_from_vr_to_urdf"),
        "left": CoordinateTransform.from_config(
            config,
            "rot_left_arm_from_vr_to_urdf",
            fallback_key="rot_arm_from_vr_to_urdf",
        ),
        "right": CoordinateTransform.from_config(
            config,
            "rot_right_arm_from_vr_to_urdf",
            fallback_key="rot_arm_from_vr_to_urdf",
        ),
    }


# ===========================================================================
# Main ROS2 bridge node
# ===========================================================================

class VRWholeBodyBridgeNode:
    """ROS2 node that publishes robot joint commands from Quest3 controller motion.

    This is the central coordinator that ties everything together:

    **Inputs:**
      - Quest3 controller data via ``QuestTcpServer`` (TCP JSON).
      - Robot joint state feedback via ``/joint_states`` subscription.

    **Outputs:**
      - Joint commands via ``/target_robot/joint_commands`` publication.
      - Optional reset signal via ``/custom/custom_a``.

    **Control loop** (``_tick()``, runs at ``control_frequency``):
      1. Check for reset edge (primary button rising edge).
      2. If reset interpolation is active, publish interpolated reset action.
      3. Otherwise, for each arm:
         a. Run the arm control state machine (AUTO ↔ MANUAL ↔ TRANSITION_EXIT).
         b. If any manual control is active, run IK and update the action vector.
         c. Update gripper control (incremental or proportional).
      4. Assemble and publish the final ``JointState`` command.

    **Key config parameters:**
      - ``trigger_threshold``:     Above this value, the trigger is considered "pressed" (default 0.9).
      - ``teleop_transition_duration_sec``: Compatibility key for the fixed exit-hold duration (default 0.25s).
      - ``control_frequency``:     Tick rate in Hz (default 200).
      - ``reset_mode``:            ``topic`` (publish reset edge), ``joint_command`` (interpolate to reset_action), or ``none``.
    """

    def __init__(self, config: dict[str, Any]):
        import rclpy
        from rclpy.node import Node
        from sensor_msgs.msg import JointState
        from std_msgs.msg import Float64

        class _Node(Node):
            pass

        self.rclpy = rclpy
        self.JointState = JointState
        self.Float64 = Float64
        self.node = _Node(f"quest3_{config.get('robot', 'robot')}_bridge")
        self.config = config
        self.joint_names = list(config.get("joint_names") or BRIDGE_JOINT_NAMES)
        if self.joint_names != BRIDGE_JOINT_NAMES:
            self.node.get_logger().warning(
                "RosTeleopBridge expects fixed bridge joint names; overriding configured joint_names."
            )
            self.joint_names = BRIDGE_JOINT_NAMES.copy()
        self.joint_state_names = list(config.get("joint_state_names") or self.joint_names)
        if len(self.joint_state_names) != len(self.joint_names):
            raise ValueError(
                f"joint_state_names must have {len(self.joint_names)} entries, "
                f"got {len(self.joint_state_names)}"
            )

        self.min_action = _as_array(config.get("min_action"), length=16, default=-math.inf)
        self.max_action = _as_array(config.get("max_action"), length=16, default=math.inf)
        self.position_scale = float(config.get("position_scale", 1.0))
        self.orientation_scale = float(config.get("orientation_scale", 1.0))
        self.grip_threshold = float(config.get("grip_threshold", 0.9))
        self.gripper_control_mode = _normalize_gripper_control_mode(config.get("gripper_control_mode", "incremental"))
        self.gripper_input_min = float(config.get("gripper_input_min", 0.0))
        self.gripper_input_max = float(config.get("gripper_input_max", 1.0))
        self.gripper_command_min = float(config.get("gripper_command_min", 0.0))
        self.gripper_command_max = float(config.get("gripper_command_max", 1.0))
        if math.isclose(self.gripper_input_min, self.gripper_input_max):
            raise ValueError("gripper_input_min and gripper_input_max must be different.")
        if self.gripper_command_min > self.gripper_command_max:
            raise ValueError("gripper_command_min must be less than or equal to gripper_command_max.")
        self.gripper_speed = max(float(config.get("gripper_speed", math.inf)), 0.0)
        self.trigger_threshold = float(config.get("trigger_threshold", 0.9))
        self.reset_mode = _normalize_reset_mode(config.get("reset_mode", "joint_command"))
        self.reset_press_value = float(config.get("reset_press_value", 1.0))
        self.reset_release_value = float(config.get("reset_release_value", 0.0))
        self.reset_pulse_on_press = bool(config.get("reset_pulse_on_press", True))
        self.control_frequency = max(float(config.get("control_frequency", 200.0)), 1.0)
        self.control_dt = 1.0 / self.control_frequency
        self.teleop_exit_hold_duration_s = max(float(config.get("teleop_transition_duration_sec", 0.25)), 0.0)
        self.reset_action = self._load_reset_action(config)
        reset_duration = max(float(config.get("reset_interp_duration_sec", 2.0)), 0.0)
        default_reset_steps = max(int(round(reset_duration * self.control_frequency)), 1)
        self.reset_interp_steps = max(int(config.get("reset_interp_steps", default_reset_steps)), 1)
        self.reset_start_hold_steps = max(
            int(round(max(float(config.get("reset_start_hold_sec", 0.0)), 0.0) * self.control_frequency)),
            0,
        )
        self._reset_running = False
        self._reset_start_action: np.ndarray | None = None
        self._reset_step = 0
        self._reset_hold_step = 0
        self.ik = KineOptTeleopIK(
            config.get("ik", {"enabled": True}),
            position_scale=self.position_scale,
            orientation_scale=self.orientation_scale,
            control_dt=self.control_dt,
            logger=self.node.get_logger(),
        )

        self.state = BridgeState()
        self._last_joint_state_wait_warn_s = 0.0
        self._last_invalid_joint_state_warn_s = 0.0
        # Commands are not published until /joint_states provides a feedback seed.
        self.pub = self.node.create_publisher(
            JointState,
            str(config.get("joint_command_topic", "/target_robot/joint_commands")),
            10,
        )
        self.reset_pub = None
        if self.reset_mode == "topic":
            self.reset_pub = self.node.create_publisher(
                Float64,
                str(config.get("reset_topic", "/custom/custom_a")),
                10,
            )
        self.node.create_subscription(
            JointState,
            str(config.get("joint_states_topic", "/joint_states")),
            self._joint_state_cb,
            10,
        )

        controller_y_rotation = math.radians(float(config.get("controller_y_rotation_deg", 35.0)))
        self.controller_transforms = _load_controller_transforms(config)
        self.tcp_server = QuestTcpServer(
            self.node,
            self.state,
            int(config.get("listen_port", 8002)),
            controller_y_rotation,
            float(config.get("invalid_origin_epsilon_m", 1e-3)),
        )
        self.tcp_server.start()

        self.node.create_timer(self.control_dt, self._tick)
        reset_desc = (
            f"reset Float64 to {config.get('reset_topic', '/custom/custom_a')}"
            if self.reset_mode == "topic"
            else f"reset_mode={self.reset_mode}"
        )
        self.node.get_logger().info(
            "Quest3 bridge publishing JointState to "
            f"{config.get('joint_command_topic', '/target_robot/joint_commands')} "
            f"and {reset_desc}; "
            f"reading joint state from {config.get('joint_states_topic', '/joint_states')}"
        )

    def _load_reset_action(self, config: dict[str, Any]) -> np.ndarray | None:
        if self.reset_mode != "joint_command":
            return None
        values = config.get("reset_action", config.get("home_action"))
        if values is None:
            raise ValueError("reset_mode `joint_command` requires a 16-element reset_action in config.")
        return np.clip(_as_array(values, length=16, default=0.0), self.min_action, self.max_action)

    def spin(self) -> None:
        try:
            self.rclpy.spin(self.node)
        except Exception as exc:
            if not self._is_ros_shutdown_exception(exc):
                raise
            self.node.get_logger().info("ROS context was shut down; stopping Quest3 bridge.")
        finally:
            self.tcp_server.stop()
            try:
                self.node.destroy_node()
            except Exception as exc:
                if not self._is_ros_shutdown_exception(exc):
                    raise

    @staticmethod
    def _is_ros_shutdown_exception(exc: Exception) -> bool:
        """Return True only for ROS exceptions caused by normal context shutdown."""
        try:
            from rclpy.executors import ExternalShutdownException
        except Exception:
            ExternalShutdownException = ()
        try:
            from rclpy._rclpy_pybind11 import RCLError
        except Exception:
            RCLError = ()

        if isinstance(exc, ExternalShutdownException):
            return True
        if isinstance(exc, RCLError):
            message = str(exc)
            return "context is not valid" in message and "rcl_shutdown" in message
        return False

    def _tick(self) -> None:
        """Main control loop callback (invoked by a ROS timer at ``control_frequency``).

        Order of operations per tick:
        1. Process reset button edge.
        2. If reset interpolation is active, publish the interpolated action.
        3. Otherwise, determine which arms/grippers need output:
           a. ``left_output_requested``: left trigger active OR left arm not in AUTO.
           b. ``right_output_requested``: same for right.
           c. ``gripper_output_requested``: either grip button active.
        4. If any output is requested and joint state is ready:
           - Run arm FSM + IK for each arm.
           - Update grippers.
           - Assemble the final action: arms that are not requested get reference_action
             from /joint_states; uninitialized grippers also use reference.
        5. Publish the action as a ``JointState`` message.
        """
        action_to_publish = None
        with self.state.lock:
            self._update_reset_edge_locked()
            reset_action = self._next_reset_action_locked()
            if reset_action is not None:
                action_to_publish = reset_action
            else:
                left_active = self.state.left.pose_valid and self.state.left.trigger > self.trigger_threshold
                right_active = self.state.right.pose_valid and self.state.right.trigger > self.trigger_threshold
                left_output_requested = left_active or self.state.left.control_state != ARM_CONTROL_AUTO
                right_output_requested = right_active or self.state.right.control_state != ARM_CONTROL_AUTO
                left_gripper_requested = self._is_gripper_control_requested(self.state.left)
                right_gripper_requested = self._is_gripper_control_requested(self.state.right)
                if not left_gripper_requested:
                    self.state.left.gripper_control_active = False
                if not right_gripper_requested:
                    self.state.right.gripper_control_active = False
                gripper_output_requested = left_gripper_requested or right_gripper_requested
                output_requested = left_output_requested or right_output_requested or gripper_output_requested
                if not output_requested:
                    self._update_arm_locked(self.state.left, slice(0, 7))
                    self._update_arm_locked(self.state.right, slice(7, 14))
                elif not self.state.joint_state_ready:
                    self._warn_waiting_for_joint_state_locked()
                else:
                    self._update_arm_locked(self.state.left, slice(0, 7))
                    self._update_arm_locked(self.state.right, slice(7, 14))
                    # Grippers are rate-limited separately from arm IK.
                    self._update_gripper_locked(self.state.left, 14)
                    self._update_gripper_locked(self.state.right, 15)
                    action = self.state.action.copy()
                    if not left_output_requested:
                        action[0:7] = self.state.reference_action[0:7]
                    if not right_output_requested:
                        action[7:14] = self.state.reference_action[7:14]
                    if not left_gripper_requested and not self.state.left.gripper_command_initialized:
                        action[14] = self.state.reference_action[14]
                    if not right_gripper_requested and not self.state.right.gripper_command_initialized:
                        action[15] = self.state.reference_action[15]
                    action_to_publish = np.clip(action, self.min_action, self.max_action).copy()

        if action_to_publish is not None:
            self._publish_joint_command(action_to_publish)

    def _publish_joint_command(self, action: np.ndarray) -> None:
        """Publish a JointState message with the given 16-D action vector.

        The message is published to ``/target_robot/joint_commands``, which is
        received by ``RosTeleopBridge._command_cb()`` in the VLA client."""
        msg = self.JointState()
        msg.header.stamp = self.node.get_clock().now().to_msg()
        msg.name = self.joint_names
        msg.position = [float(v) for v in action]
        self.pub.publish(msg)

    def _next_reset_action_locked(self) -> np.ndarray | None:
        """Return the next frame of the reset interpolation, or None if not active.

        The sequence is:
          1. Hold at start position for ``reset_start_hold_steps`` ticks.
          2. Linear interpolation from ``_reset_start_action`` to ``reset_action``
             over ``reset_interp_steps`` ticks.
          3. When complete, clear joint_state_ready so the system re-syncs with
             fresh /joint_states feedback.
        """
        if not self._reset_running or self._reset_start_action is None or self.reset_action is None:
            return None
        if self._reset_hold_step < self.reset_start_hold_steps:
            self._reset_hold_step += 1
            action = self._reset_start_action.copy()
        else:
            self._reset_step += 1
            alpha = min(self._reset_step / self.reset_interp_steps, 1.0)
            action = (1.0 - alpha) * self._reset_start_action + alpha * self.reset_action
            if alpha >= 1.0:
                self._reset_running = False
                self._reset_start_action = None
                self._reset_step = 0
                self._reset_hold_step = 0
                self.state.joint_state_ready = False
                self.node.get_logger().info("Reset joint-command interpolation completed; waiting for fresh joint state.")
        action = np.clip(action, self.min_action, self.max_action)
        self.state.action[:] = action
        return action.copy()

    def _start_reset_interpolation_locked(self) -> None:
        """Begin interpolating from current reference_action to the configured reset_action.

        Clears all arm control references and holds, then linearly interpolates
        the full 16-D action vector over ``reset_interp_steps`` ticks. An optional
        initial hold period (``reset_start_hold_steps``) keeps the start position
        steady before interpolation begins.
        """
        if self.reset_action is None:
            return
        if not self.state.joint_state_ready:
            self._warn_waiting_for_joint_state_locked()
            self.node.get_logger().warning("Reset request ignored because no current joint state is available.")
            return
        self._clear_arm_control_refs_locked(self.state.left)
        self._clear_arm_control_refs_locked(self.state.right)
        self.state.action[:] = self.state.reference_action
        self._reset_start_action = np.clip(self.state.reference_action, self.min_action, self.max_action).copy()
        self._reset_step = 0
        self._reset_hold_step = 0
        self._reset_running = True
        self.node.get_logger().info(
            "Reset request received; interpolating to reset_action over "
            f"{self.reset_interp_steps} command steps on joint_command_topic."
        )

    def _joint_state_cb(self, msg) -> None:
        """Receive /joint_states messages and update the reference action vector.

        This is the robot feedback path. Valid joint states set ``joint_state_ready = True``
        and populate ``reference_action``, which is used as:
          - The IK seed for arm control.
          - The FK reference for anchor blending.
          - The fallback for arms/grippers not under human control.
        """
        positions = dict(zip(msg.name, msg.position))
        if not positions:
            return
        missing = [name for name in self.joint_state_names if name not in positions]
        if missing:
            self._warn_invalid_joint_state(f"missing joints: {missing[:4]}")
            return
        try:
            values = np.asarray([positions[name] for name in self.joint_state_names], dtype=float)
        except (TypeError, ValueError):
            self._warn_invalid_joint_state("non-numeric joint positions")
            return
        if not np.all(np.isfinite(values)):
            self._warn_invalid_joint_state("non-finite joint positions")
            return
        with self.state.lock:
            self.state.reference_action[:] = values
            self.state.joint_state_ready = True

    def _warn_invalid_joint_state(self, reason: str, period_s: float = 1.0) -> None:
        now = time.time()
        if now - self._last_invalid_joint_state_warn_s >= period_s:
            self._last_invalid_joint_state_warn_s = now
            self.node.get_logger().warning(f"Drop invalid joint state feedback: {reason}.")

    def _update_reset_edge_locked(self) -> None:
        """Detect rising/falling edges on the primary button for reset behavior.

        Depending on ``reset_mode``:
          - ``topic``:           Publish a Float64 edge (rising=press_value, falling=release_value).
          - ``joint_command``:   Start interpolating toward the configured reset_action.
          - ``none``:           Just clear arm control references (safe fallback).
        """
        primary = self.state.left.primary_button or self.state.right.primary_button
        if primary == self.state.primary_pressed:
            return
        self.state.primary_pressed = primary
        if self.reset_mode == "topic":
            self._publish_reset_value_locked(self.reset_press_value if primary else self.reset_release_value)
            if primary:
                if self.reset_pulse_on_press:
                    self._publish_reset_value_locked(self.reset_release_value)
                # Wait for fresh feedback after reset instead of falling back to a configured home pose.
                self.state.joint_state_ready = False
                self._clear_arm_control_refs_locked(self.state.left)
                self._clear_arm_control_refs_locked(self.state.right)
                self.node.get_logger().info("Reset edge published to reset topic.")
            return
        if primary and self.reset_mode == "joint_command":
            self._start_reset_interpolation_locked()
            return
        if primary and self.reset_mode == "none":
            self._clear_arm_control_refs_locked(self.state.left)
            self._clear_arm_control_refs_locked(self.state.right)
            self.node.get_logger().info("Reset button pressed; reset is disabled by reset_mode=none.")

    def _publish_reset_value_locked(self, value: float) -> None:
        if self.reset_pub is None:
            return
        msg = self.Float64()
        msg.data = float(value)
        self.reset_pub.publish(msg)

    def _warn_waiting_for_joint_state_locked(self, period_s: float = 1.0) -> None:
        now = time.time()
        if now - self._last_joint_state_wait_warn_s >= period_s:
            self._last_joint_state_wait_warn_s = now
            self.node.get_logger().warning(
                "Quest3 teleop is active, but no joint state has been received yet; holding commands."
            )

    @staticmethod
    def _clear_arm_control_refs_locked(side: ControllerSide) -> None:
        """Reset all arm control state for one side back to AUTO.

        Clears all trigger snapshots, exit holds, exit timing state,
        and gripper initialization flags.
        """
        side.trigger_ref_pos = None
        side.trigger_ref_quat = None
        side.trigger_ref_action = None
        side.trigger_ref_ee_pose = None
        side.pose_valid = False
        side.exit_hold_pos = None
        side.exit_hold_quat = None
        side.control_state = ARM_CONTROL_AUTO
        side.transition_elapsed_s = 0.0
        side.was_trigger_active = False
        side.gripper_control_active = False
        side.gripper_command_initialized = False

    def _update_arm_locked(self, side: ControllerSide, arm_slice: slice) -> None:
        """Run the arm control state machine and IK for one arm.

        State transitions:
          AUTO/EXIT + trigger_active → _start_arm_intervention_locked (MANUAL)
          MANUAL + !trigger          → _start_arm_exit_transition_locked (EXIT)

        If in MANUAL or EXIT and all reference data is valid, keep the
        trigger-edge EE anchor fixed and run IK for the full human delta.

        Args:
            side:      ControllerSide for left or right controller.
            arm_slice: slice(0,7) for left arm, slice(7,14) for right arm.
        """
        side_name = "left" if arm_slice.start == 0 else "right"
        trigger_active = side.pose_valid and side.trigger > self.trigger_threshold
        if not trigger_active and side.control_state == ARM_CONTROL_AUTO:
            side.was_trigger_active = False
            return
        needs_reference_pose = trigger_active and side.control_state in (
            ARM_CONTROL_AUTO,
            ARM_CONTROL_TRANSITION_EXIT,
        )
        reference_pose = (
            self._current_reference_pose_locked(side_name, arm_slice)
            if needs_reference_pose
            else None
        )

        if trigger_active and side.control_state in (ARM_CONTROL_AUTO, ARM_CONTROL_TRANSITION_EXIT):
            self._start_arm_intervention_locked(side_name, side, arm_slice, reference_pose)
        elif not trigger_active and side.control_state == ARM_CONTROL_MANUAL:
            self._start_arm_exit_transition_locked(side_name, side)

        side.was_trigger_active = trigger_active
        if (
            side.control_state == ARM_CONTROL_AUTO
            or (not side.pose_valid and side.control_state != ARM_CONTROL_TRANSITION_EXIT)
            or side.pose_pos is None
            or side.pose_quat is None
            or side.trigger_ref_pos is None
            or side.trigger_ref_quat is None
            or side.trigger_ref_action is None
            or side.trigger_ref_ee_pose is None
        ):
            return

        exit_finished = self._advance_arm_transition_locked(side)

        q_solution = self.ik.solve(
            side_name,
            side,
            self.state.action[arm_slice],
            self.controller_transforms[side_name],
            self.controller_transforms["base"],
        )
        if q_solution is not None:
            self.state.action[arm_slice] = q_solution
        if exit_finished:
            self._clear_arm_control_refs_locked(side)

    def _current_reference_pose_locked(self, side_name: str, arm_slice: slice) -> np.ndarray | None:
        """Compute the current end-effector reference pose via FK.

        Prefers FK on ``reference_action`` (from /joint_states); falls back to
        FK on the current ``action`` (last command) if the reference FK fails.
        """
        q_reference = self.state.reference_action[arm_slice]
        pose = self.ik.forward_pose(side_name, q_reference)
        if pose is not None:
            return pose
        return self.ik.forward_pose(side_name, self.state.action[arm_slice])

    def _start_arm_intervention_locked(
        self,
        side_name: str,
        side: ControllerSide,
        arm_slice: slice,
        reference_pose: np.ndarray | None,
    ) -> None:
        """Capture a static trigger-edge anchor and enter MANUAL immediately.

        Steps:
        1. Reset the action arm slice to the current /joint_states reference
           (avoids IK jumping from a stale action value).
        2. Compute the anchor end-effector pose from the current reference via FK.
        3. Snapshot the current VR controller pose and reference action as the
           delta baseline (trigger_ref_*).

        The EE anchor captured here is intentionally immutable until the trigger
        is released.  In particular, subsequent command-biased joint-state
        feedback must not feed the generated motion back into the anchor.
        """
        if not side.pose_valid or side.pose_pos is None or side.pose_quat is None:
            return
        self.state.action[arm_slice] = self.state.reference_action[arm_slice]
        anchor_pose = reference_pose
        if anchor_pose is None:
            anchor_pose = self.ik.forward_pose(side_name, self.state.action[arm_slice])
        if anchor_pose is None:
            return

        side.trigger_ref_pos = side.pose_pos.copy()
        side.trigger_ref_quat = side.pose_quat.copy()
        side.trigger_ref_action = self.state.action[arm_slice].copy()
        side.trigger_ref_ee_pose = anchor_pose.copy()
        side.exit_hold_pos = None
        side.exit_hold_quat = None
        side.control_state = ARM_CONTROL_MANUAL
        side.transition_elapsed_s = 0.0

    def _start_arm_exit_transition_locked(
        self,
        side_name: str,
        side: ControllerSide,
    ) -> None:
        """Initiate the MANUAL → TRANSITION_EXIT → AUTO sequence.

        Steps:
        1. Bake the current human offset into the EE anchor so the anchor is
           already at the target (releasing won't snap back to old press-time position).
        2. Freeze the current VR controller pose (exit_hold_*) so the arm
           stays still during the exit-hold period.
        """
        if side.trigger_ref_ee_pose is None:
            self._clear_arm_control_refs_locked(side)
            return
        target_pose = self.ik.target_pose(
            side,
            self.controller_transforms[side_name],
            self.controller_transforms["base"],
        )
        if target_pose is not None:
            # Bake the current human offset into the anchor so release never
            # pulls the target back toward the original press-time anchor.
            side.trigger_ref_ee_pose = target_pose.copy()
            if side.pose_pos is not None:
                side.trigger_ref_pos = side.pose_pos.copy()
            if side.pose_quat is not None:
                side.trigger_ref_quat = side.pose_quat.copy()
        side.exit_hold_pos = None if side.pose_pos is None else side.pose_pos.copy()
        side.exit_hold_quat = None if side.pose_quat is None else side.pose_quat.copy()
        side.control_state = ARM_CONTROL_TRANSITION_EXIT
        side.transition_elapsed_s = 0.0

    def _advance_arm_transition_locked(self, side: ControllerSide) -> bool:
        """Advance the fixed-target hold after trigger release.

        Returns:
            True if the exit transition just finished, False otherwise.
        """
        if side.control_state != ARM_CONTROL_TRANSITION_EXIT:
            return False
        side.transition_elapsed_s += self.control_dt
        return (
            self.teleop_exit_hold_duration_s <= 0.0
            or side.transition_elapsed_s >= self.teleop_exit_hold_duration_s
        )

    def _update_gripper_locked(self, side: ControllerSide, index: int) -> None:
        """Update the gripper command for one hand.

        Two modes:
          - ``proportional``:  Map grip value linearly from [gripper_input_min, gripper_input_max]
                               to [gripper_command_min, gripper_command_max].
          - ``incremental``:   Step toward max when grip > grip_threshold,
                               step toward min when secondary_button is pressed.
                               Speed is governed by ``gripper_speed``.

        On first activation, the command is anchored to the reference_action value
        to avoid jumps.
        """
        requested = self._is_gripper_control_requested(side)
        if requested and not side.gripper_control_active:
            self._anchor_gripper_command_locked(side, index)
            side.gripper_control_active = True
            side.gripper_command_initialized = True
        elif not requested:
            side.gripper_control_active = False
            return

        if self.gripper_control_mode == "proportional":
            alpha = (float(side.grip) - self.gripper_input_min) / (self.gripper_input_max - self.gripper_input_min)
            alpha = float(np.clip(alpha, 0.0, 1.0))
            self.state.action[index] = (1.0 - alpha) * self.gripper_command_min + alpha * self.gripper_command_max
            return

        step = self.gripper_speed * self.control_dt
        if side.grip > self.grip_threshold:
            self.state.action[index] = min(float(self.state.action[index]) + step, self.gripper_command_max)
        elif side.secondary_button:
            self.state.action[index] = max(float(self.state.action[index]) - step, self.gripper_command_min)

    def _is_gripper_control_requested(self, side: ControllerSide) -> bool:
        if self.gripper_control_mode == "proportional":
            return float(side.grip) > self.gripper_input_min + 1e-6
        return side.grip > self.grip_threshold or side.secondary_button

    def _anchor_gripper_command_locked(self, side: ControllerSide, index: int) -> None:
        """Set the initial gripper command based on the current reference and intent.

        For incremental mode on first activation:
          - If gripping (grip > threshold): start from max(current, reference).
          - If releasing (secondary_button): start from min(current, reference).
          - Otherwise: use reference directly.

        This prevents the gripper from snapping to reference when the user
        was already at a different gripper position.
        """
        reference = float(self.state.reference_action[index])
        if self.gripper_control_mode != "incremental" or not side.gripper_command_initialized:
            self.state.action[index] = reference
            return

        current_command = float(self.state.action[index])
        if side.grip > self.grip_threshold:
            self.state.action[index] = max(current_command, reference)
        elif side.secondary_button:
            self.state.action[index] = min(current_command, reference)
        else:
            self.state.action[index] = reference


def _try_adb_reverse(port: int) -> None:
    """Set up ADB reverse port forwarding for Quest3 TCP connection.

    Only needed when the Quest3 app connects via USB (Android Debug Bridge).
    The command `adb reverse tcp:<port> tcp:<port>` forwards host port to device.
    """
    for cmd in (
        ["adb", "reverse", "--remove", f"tcp:{port}"],
        ["adb", "reverse", f"tcp:{port}", f"tcp:{port}"],
    ):
        try:
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            return


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments. Config file overrides are applied in main()."""
    parser = argparse.ArgumentParser(description="VR whole-body bridge to VLA RosTeleopBridge topics")
    parser.add_argument("--config", required=True, help="Path to a2d.yaml or ti5_t170c.yaml")
    parser.add_argument("--listen-port", type=int, help="Override Quest3 TCP listen port")
    parser.add_argument("--joint-command-topic", help="Override JointState topic")
    parser.add_argument("--joint-states-topic", help="Override source JointState topic")
    parser.add_argument(
        "--reset-mode",
        choices=("topic", "joint_command", "joint-command", "none"),
        help="Override reset behavior: publish reset topic, interpolate to reset_action on joint commands, or disable.",
    )
    parser.add_argument("--reset-topic", help="Override reset Float64 topic")
    parser.add_argument("--no-adb-reverse", action="store_true", help="Skip adb reverse tcp setup")
    return parser.parse_args()


def main() -> None:
    """Entry point: load config, apply CLI overrides, set up ADB, launch the bridge node.

    Usage example:
        python -m teleop.quest3.quest3 --config teleop/quest3/config/a2d.yaml
    """
    args = parse_args()
    config_path = Path(args.config).expanduser()
    config = _load_yaml(config_path)
    _resolve_relative_config_paths(config, config_path.resolve())
    if args.listen_port is not None:
        config["listen_port"] = args.listen_port
    if args.joint_command_topic:
        config["joint_command_topic"] = args.joint_command_topic
    if args.joint_states_topic:
        config["joint_states_topic"] = args.joint_states_topic
    if args.reset_mode:
        config["reset_mode"] = _normalize_reset_mode(args.reset_mode)
    if args.reset_topic:
        config["reset_topic"] = args.reset_topic

    if not args.no_adb_reverse:
        _try_adb_reverse(int(config.get("listen_port", 8002)))

    import rclpy

    rclpy.init(args=None)
    try:
        node = VRWholeBodyBridgeNode(config)
        node.spin()
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
