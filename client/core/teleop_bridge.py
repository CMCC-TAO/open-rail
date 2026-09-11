"""Runtime bridges that feed human teleoperation commands into the VLA client.

The bridge layer has two responsibilities:

* receive teleoperation commands and convert them into the client's action
  vector layout;
* publish the client's teleop anchor state so external teleop devices can seed
  their IK/current-command state without calling the robot interface again.

The ROS2 bridge is the main path used by Quest3 and Daimon.  A small ZMQ bridge
is kept for lightweight external producers that can send action arrays directly.
"""

import json
import logging
import os
from pathlib import Path
import signal
import shlex
import subprocess
import sys
import threading
import time
from abc import ABC, abstractmethod
from typing import Callable, Optional, Sequence

import numpy as np


LEFT_ARM_JOINTS = tuple(f"left_arm_joint{i}" for i in range(1, 8))
RIGHT_ARM_JOINTS = tuple(f"right_arm_joint{i}" for i in range(1, 8))
LEFT_GRIPPER_JOINT = "left_hand_joint1"
RIGHT_GRIPPER_JOINT = "right_hand_joint1"
REQUIRED_JOINTS = LEFT_ARM_JOINTS + RIGHT_ARM_JOINTS + (LEFT_GRIPPER_JOINT, RIGHT_GRIPPER_JOINT)
DEFAULT_CLIENT_JOINT_STATE_TOPIC = "/client_robot/joint_states"
DEFAULT_CLIENT_JOINT_STATE_NAMES = (
    LEFT_ARM_JOINTS
    + RIGHT_ARM_JOINTS
    + (LEFT_GRIPPER_JOINT, RIGHT_GRIPPER_JOINT)
    + ("joint_head_yaw", "joint_head_pitch", "joint_lift_body", "joint_body_pitch")
)
RESET_MODES = {"topic", "joint_command", "none"}


def _brief_array(values, limit: int = 4) -> str:
    """Return compact numeric diagnostics suitable for periodic runtime logs."""

    arr = np.asarray(values, dtype=float).reshape(-1)
    if arr.size == 0:
        return "shape=(0,)"
    head = np.array2string(arr[:limit], precision=4, separator=", ")
    tail = np.array2string(arr[-limit:], precision=4, separator=", ") if arr.size > limit else head
    return f"shape={arr.shape} min={arr.min():.4f} max={arr.max():.4f} head={head} tail={tail}"


def joint_state_to_action(msg, *, action_dim: int = 16) -> np.ndarray:
    """Convert a command ``JointState`` into the fixed VLA action layout.

    Quest3 and Daimon publish commands by joint name.  The VLA client executes a
    flat action vector, so this function validates the required bridge joint
    names and places them in the canonical order:

    left arm 7, right arm 7, left gripper 1, right gripper 1.
    """

    if len(msg.name) != len(msg.position):
        raise ValueError("JointState name and position lengths differ")
    positions = {str(name): float(position) for name, position in zip(msg.name, msg.position)}
    missing = [name for name in REQUIRED_JOINTS if name not in positions]
    if missing:
        raise ValueError("JointState missing required joints: " + ", ".join(missing))

    action = np.zeros(int(action_dim), dtype=float)
    ordered = LEFT_ARM_JOINTS + RIGHT_ARM_JOINTS + (LEFT_GRIPPER_JOINT, RIGHT_GRIPPER_JOINT)
    if len(ordered) > action.shape[0]:
        raise ValueError(f"action_dim {action_dim} is smaller than required command size {len(ordered)}")
    for index, name in enumerate(ordered):
        action[index] = positions[name]
    return action


def _cfg_get(config, key, default=None):
    """Read either ConfigDict/object attributes or plain dictionary values."""

    if config is None:
        return default
    if isinstance(config, dict):
        return config.get(key, default)
    return getattr(config, key, default)


def _cfg_has(config, key) -> bool:
    if config is None:
        return False
    if isinstance(config, dict):
        return key in config
    return hasattr(config, key)


def _normalize_reset_mode(value) -> str:
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
        raise ValueError(f"Unsupported teleop reset_mode {value!r}; expected one of {sorted(RESET_MODES)}")
    return mode


def _read_quest3_config_reset_mode(device_cfg) -> Optional[str]:
    config_path = _cfg_get(device_cfg, "config_path", "teleop/quest3/config/a2d.yaml")
    repo_root = Path(__file__).resolve().parents[2]
    path = Path(str(config_path)).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    if not isinstance(data, dict) or "reset_mode" not in data:
        return None
    return str(data["reset_mode"])


def _action_values_to_array(values, *, action_dim: int) -> np.ndarray:
    """Normalize an arbitrary numeric payload into a fixed-size action array."""

    action_values = np.asarray(values, dtype=float).reshape(-1)
    action_dim = int(action_dim)
    if action_values.shape[0] > action_dim:
        raise ValueError(f"Teleop action size {action_values.shape[0]} is larger than action_dim {action_dim}")
    action = np.zeros(action_dim, dtype=float)
    action[:action_values.shape[0]] = action_values
    return action


def parse_zmq_teleop_message(message, *, action_dim: int = 16) -> np.ndarray:
    """Parse a ZMQ JSON message into an action vector.

    Supported payloads are intentionally small: either ``{"action": [...]}``,
    ``{"positions": [...]}``, or an ndarray-like dictionary with ``data``,
    optional ``dtype``, and optional ``shape``.
    """

    if isinstance(message, bytes):
        message = message.decode("utf-8")
    if isinstance(message, str):
        message = json.loads(message)
    if not isinstance(message, dict):
        raise ValueError("ZMQ teleop message must be a JSON object")

    action_payload = message.get("action", message.get("positions"))
    if action_payload is None:
        raise ValueError("ZMQ teleop message missing 'action'")

    if isinstance(action_payload, dict):
        data = action_payload.get("data")
        if data is None:
            raise ValueError("ZMQ ndarray-like action missing 'data'")
        dtype = action_payload.get("dtype", "float64")
        shape = action_payload.get("shape")
        values = np.asarray(data, dtype=np.dtype(dtype))
        if shape is not None:
            values = values.reshape(tuple(int(v) for v in shape))
        return _action_values_to_array(values, action_dim=action_dim)

    return _action_values_to_array(action_payload, action_dim=action_dim)


class TeleopBridgeBase(ABC):
    """Minimal lifecycle shared by concrete bridge implementations."""

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    def publish_joint_state(self) -> None:
        """Publish the latest teleop anchor state when the bridge supports it."""

        return


class TeleopDeviceProcess:
    """Own an optional external teleop device process.

    The ROS bridge can start Quest3 or Daimon automatically so enabling
    ``use_teleop`` from the web UI brings up the whole human-control path.  The
    process is started in a new session so ``stop`` can terminate its subprocess
    tree cleanly.
    """

    def __init__(
        self,
        *,
        device: str,
        config,
        command_topic: str,
        joint_state_topic: str,
        reset_topic: str,
        reset_mode: str = "joint_command",
    ):
        self.device = str(device or "none").lower()
        self.config = config
        self.command_topic = command_topic
        self.joint_state_topic = joint_state_topic
        self.reset_topic = reset_topic
        self.reset_mode = _normalize_reset_mode(reset_mode)
        self.logger = logging.getLogger(__name__)
        self.process: Optional[subprocess.Popen] = None

    def start(self) -> None:
        """Start the configured device unless it is already running."""

        if self.process is not None and self.process.poll() is None:
            return
        if self.device in ("", "none", "manual", "external"):
            return

        cmd, env, cwd = self._build_command()
        if not cmd:
            return
        self.process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            start_new_session=True,
        )
        # print(f"[ZLA][teleop_bridge][device] started device={self.device} pid={self.process.pid} cmd={cmd}", flush=True)

    def stop(self) -> None:
        """Terminate the device process group with a short graceful timeout."""

        if self.process is None:
            return
        proc = self.process
        self.process = None
        if proc.poll() is not None:
            return
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            proc.terminate()
        try:
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                proc.kill()
            proc.wait(timeout=1.0)

    def _build_command(self):
        """Build the subprocess command, environment, and working directory.

        Users can override the default command with ``teleop.devices.<name>.command``.
        If no override is present, Quest3 is launched as this repository's Python
        module, while Daimon is launched from its local Python package source.
        """

        device_cfg = _cfg_get(_cfg_get(self.config, "devices", None), self.device, None)
        custom_command = _cfg_get(device_cfg, "command", None)
        repo_root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        cwd = str(repo_root)
        if custom_command:
            if isinstance(custom_command, str):
                return shlex.split(custom_command), env, cwd
            return [str(v) for v in custom_command], env, cwd

        if self.device == "quest3":
            config_path = _cfg_get(device_cfg, "config_path", "teleop/quest3/config/a2d.yaml")
            config_path = self._resolve_repo_path(config_path, repo_root)
            python = _cfg_get(device_cfg, "python", sys.executable or "python3")
            cmd = [
                str(python),
                "-m",
                "teleop.quest3.quest3",
                "--config",
                str(config_path),
                "--joint-command-topic",
                self.command_topic,
                "--joint-states-topic",
                self.joint_state_topic,
                "--reset-mode",
                self.reset_mode,
            ]
            if self.reset_mode == "topic":
                cmd.extend(["--reset-topic", self.reset_topic])
            if bool(_cfg_get(device_cfg, "no_adb_reverse", False)):
                cmd.append("--no-adb-reverse")
            listen_port = _cfg_get(device_cfg, "listen_port", None)
            if listen_port is not None:
                cmd.extend(["--listen-port", str(listen_port)])
            return cmd, env, cwd

        if self.device == "daimon":
            python = _cfg_get(device_cfg, "python", sys.executable or "python3")
            package_src = self._resolve_repo_path(_cfg_get(
                device_cfg,
                "package_src",
                str(repo_root / "teleop/daimon/mine/src/a2d_exton2_teleop"),
            ), repo_root)
            env["PYTHONPATH"] = str(package_src) + os.pathsep + env.get("PYTHONPATH", "")
            urdf_path = self._resolve_repo_path(_cfg_get(
                device_cfg,
                "urdf_path",
                str(repo_root / "teleop/daimon/mine/src/a2d_description/urdf/a2d_vla_zero_state.urdf"),
            ), repo_root)
            cmd = [
                str(python),
                "-m",
                "a2d_exton2_teleop.a2d_ik_teleop_node",
                "--ros-args",
                "-p",
                f"joint_states_topic:={self.joint_state_topic}",
                "-p",
                f"joint_commands_topic:={self.command_topic}",
                "-p",
                f"urdf_path:={urdf_path}",
            ]
            return cmd, env, cwd

        raise ValueError(f"Unsupported teleop control_device: {self.device}")

    @staticmethod
    def _resolve_repo_path(path, repo_root: Path) -> Path:
        """Resolve user-configured paths relative to the repository root."""

        resolved = Path(str(path)).expanduser()
        if not resolved.is_absolute():
            resolved = repo_root / resolved
        return resolved


class RosTeleopBridge(TeleopBridgeBase):
    """ROS2 bridge for named joint commands and client robot state feedback.

    Subscriptions:
    * ``topic`` receives teleop command ``JointState`` messages.
    * ``reset_topic`` receives reset edges when a reset handler is provided.

    Publications:
    * ``joint_state_topic`` publishes the latest client teleop anchor state
      obtained from ``joint_state_provider``.  This lets Quest3/Daimon
      initialize IK from the command stream when available, with robot feedback
      as fallback, while keeping all direct robot observation calls in the VLA
      observe thread.
    """

    def __init__(
        self,
        submit_action: Callable[[np.ndarray, float], None],
        reset_handler: Optional[Callable[[], None]] = None,
        joint_state_provider: Optional[Callable[[], Optional[Sequence[float]]]] = None,
        topic: str = "/target_robot/joint_commands",
        reset_topic: str = "/custom/custom_a",
        joint_state_topic: str = DEFAULT_CLIENT_JOINT_STATE_TOPIC,
        joint_state_names: Sequence[str] = DEFAULT_CLIENT_JOINT_STATE_NAMES,
        joint_state_publish_rate: float = 30.0,
        action_dim: int = 16,
        node_name: str = "vla_infer_teleop_bridge",
        reset_threshold: float = 0.5,
        reset_mode: str = "joint_command",
        control_device: str = "quest3",
        device_config=None,
    ):
        self.submit_action = submit_action
        self.reset_handler = reset_handler
        self.joint_state_provider = joint_state_provider
        self.topic = topic
        self.reset_topic = reset_topic
        self.joint_state_topic = joint_state_topic
        self.joint_state_names = tuple(str(name) for name in joint_state_names)
        self.joint_state_publish_rate = max(float(joint_state_publish_rate), 0.0)
        self.action_dim = int(action_dim)
        self.node_name = node_name
        self.reset_threshold = float(reset_threshold)
        self.reset_mode = _normalize_reset_mode(reset_mode)
        self.control_device = str(control_device or "none").lower()
        self.device_config = device_config
        self.logger = logging.getLogger(__name__)
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._rclpy = None
        self._node = None
        self._JointState = None
        self._joint_state_pub = None
        self._device_process: Optional[TeleopDeviceProcess] = None
        self._debug_count = 0
        self._last_debug_s = 0.0
        self._state_debug_count = 0
        self._last_state_debug_s = 0.0
        self._reset_active = False

    def start(self) -> None:
        """Create the ROS node, start spinning, and launch the selected device."""

        if self._running:
            return
        try:
            import rclpy
            from sensor_msgs.msg import JointState
            from std_msgs.msg import Float64
        except ImportError as exc:
            raise RuntimeError("ROS 2 rclpy, sensor_msgs and std_msgs are required for teleop recording") from exc

        self._rclpy = rclpy
        self._JointState = JointState
        if not rclpy.ok():
            rclpy.init(args=None)
        self._node = rclpy.create_node(self.node_name)
        self._node.create_subscription(JointState, self.topic, self._command_cb, 10)
        if self.reset_handler is not None and self.reset_mode == "topic":
            self._node.create_subscription(Float64, self.reset_topic, self._reset_cb, 10)
        if self.joint_state_provider is not None:
            self._joint_state_pub = self._node.create_publisher(JointState, self.joint_state_topic, 10)
            if self.joint_state_publish_rate > 0:
                self._node.create_timer(1.0 / self.joint_state_publish_rate, self.publish_joint_state)
        self._running = True
        self._thread = threading.Thread(target=self._spin, name="ros-teleop-bridge", daemon=True)
        self._thread.start()
        self._device_process = TeleopDeviceProcess(
            device=self.control_device,
            config=self.device_config,
            command_topic=self.topic,
            joint_state_topic=self.joint_state_topic,
            reset_topic=self.reset_topic,
            reset_mode=self.reset_mode,
        )
        self._device_process.start()
        self.logger.info("ROS teleop bridge subscribed to %s", self.topic)
        # print(
        #     f"[ZLA][teleop_bridge][ros2] started topic={self.topic} "
        #     f"joint_state_topic={self.joint_state_topic} control_device={self.control_device} "
        #     f"reset_mode={self.reset_mode} "
        #     f"reset_topic={self.reset_topic if self.reset_handler is not None and self.reset_mode == 'topic' else 'disabled'} "
        #     f"node={self.node_name} action_dim={self.action_dim}",
        #     flush=True,
        # )

    def stop(self) -> None:
        """Stop ROS spinning, destroy the node, and stop any device subprocess."""

        self._running = False
        if self._device_process is not None:
            self._device_process.stop()
            self._device_process = None
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        if self._node is not None:
            self._node.destroy_node()
            self._node = None
        self._joint_state_pub = None

    def _spin(self) -> None:
        """Drive ROS callbacks from a private thread owned by the bridge."""

        while self._running and self._rclpy is not None and self._node is not None:
            try:
                self._rclpy.spin_once(self._node, timeout_sec=0.05)
            except Exception as exc:
                if self._is_ros_shutdown_exception(exc):
                    break
                self.logger.exception("ROS teleop bridge spin failed")
                break

    @staticmethod
    def _is_ros_shutdown_exception(exc: Exception) -> bool:
        """Return True for exceptions raised by normal ROS context shutdown."""

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

    def publish_joint_state(self) -> None:
        """Publish the latest cached client teleop anchor state as a ROS ``JointState``.

        This is called both by the periodic heartbeat timer and immediately after
        a robot command succeeds.  The event-driven call keeps Quest3's activation
        anchor from waiting for the next timer tick.  The provider returns only
        positions.  Names come from VLAClient and are robot-specific.  Position
        vectors are padded or truncated to match the configured name list so
        malformed lengths do not crash the ROS callback.
        """

        if self._joint_state_pub is None or self._JointState is None or self.joint_state_provider is None:
            return
        try:
            values = self.joint_state_provider()
            if values is None:
                return
            positions = np.asarray(values, dtype=float).reshape(-1)
            if positions.shape[0] < len(self.joint_state_names):
                positions = np.pad(positions, (0, len(self.joint_state_names) - positions.shape[0]))
            positions = positions[:len(self.joint_state_names)]
        except Exception as exc:
            self.logger.warning("Drop invalid client robot joint state", exc_info=True)
            # print(f"[ZLA][teleop_bridge][ros2] drop client joint state error={exc}", flush=True)
            return

        msg = self._JointState()
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.name = list(self.joint_state_names)
        msg.position = [float(v) for v in positions]
        self._joint_state_pub.publish(msg)
        self._state_debug_count += 1
        now = time.perf_counter()
        if now - self._last_state_debug_s >= 1.0:
            self._last_state_debug_s = now
            # print(
            #     f"[ZLA][teleop_bridge][ros2] publish client_joint_states "
            #     f"count={self._state_debug_count} topic={self.joint_state_topic} "
            #     f"names={len(msg.name)} state={_brief_array(positions)}",
            #     flush=True,
            # )

    def _command_cb(self, msg) -> None:
        """Receive a named teleop command and submit it to VLA action arbitration."""

        self._debug_count += 1
        try:
            action = joint_state_to_action(msg, action_dim=self.action_dim)
        except Exception as exc:
            self.logger.warning("Drop invalid teleop JointState", exc_info=True)
            # print(
            #     f"[ZLA][teleop_bridge][ros2] drop invalid JointState "
            #     f"count={self._debug_count} names={len(msg.name)} positions={len(msg.position)} "
            #     f"first_names={list(msg.name[:6])} error={exc}",
            #     flush=True,
            # )
            return
        now = time.perf_counter()
        if now - self._last_debug_s >= 1.0:
            self._last_debug_s = now
            # print(
            #     f"[ZLA][teleop_bridge][ros2] recv count={self._debug_count} "
            #     f"names={len(msg.name)} first_names={list(msg.name[:6])} action={_brief_array(action)}",
            #     flush=True,
            # )
        self.submit_action(action, time.perf_counter())

    def _reset_cb(self, msg) -> None:
        """Convert a reset-topic rising edge into one reset callback invocation."""

        value = float(getattr(msg, "data", 0.0))
        active = value >= self.reset_threshold
        if not active:
            self._reset_active = False
            return
        if self.reset_handler is None or self._reset_active:
            return
        self._reset_active = True
        # print(f"[ZLA][teleop_bridge][ros2] reset request received topic={self.reset_topic} value={value:.3f}", flush=True)
        try:
            self.reset_handler()
        except Exception as exc:
            self.logger.error("Teleop reset handler failed: %s", exc, exc_info=True)
            # print(f"[ZLA][teleop_bridge][ros2] reset handler failed error={exc}", flush=True)


class ZmqTeleopBridge(TeleopBridgeBase):
    """ZMQ bridge for producers that send action arrays directly."""

    def __init__(
        self,
        submit_action: Callable[[np.ndarray, float], None],
        endpoint: str = "tcp://127.0.0.1:5570",
        action_dim: int = 16,
        identity: str = "vla-infer-teleop",
        poll_timeout_ms: int = 50,
        heartbeat_s: float = 1.0,
    ):
        self.submit_action = submit_action
        self.endpoint = endpoint
        self.action_dim = int(action_dim)
        self.identity = identity
        self.poll_timeout_ms = int(poll_timeout_ms)
        self.heartbeat_s = float(heartbeat_s)
        self.logger = logging.getLogger(__name__)
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._context = None
        self._socket = None
        self._poller = None
        self._zmq = None
        self._debug_count = 0
        self._last_debug_s = 0.0

    def start(self) -> None:
        """Connect the DEALER socket and start the receive loop."""

        if self._running:
            return
        try:
            import zmq
        except ImportError as exc:
            raise RuntimeError("pyzmq is required for ZMQ teleop recording") from exc

        self._zmq = zmq
        self._context = zmq.Context.instance()
        self._socket = self._context.socket(zmq.DEALER)
        self._socket.setsockopt(zmq.IDENTITY, str(self.identity).encode("utf-8"))
        self._socket.setsockopt(zmq.RCVHWM, 1)
        self._socket.setsockopt(zmq.SNDHWM, 1)
        self._socket.connect(self.endpoint)
        self._poller = zmq.Poller()
        self._poller.register(self._socket, zmq.POLLIN)
        self._running = True
        self._thread = threading.Thread(target=self._recv_loop, name="zmq-teleop-bridge", daemon=True)
        self._thread.start()
        self.logger.info("ZMQ teleop bridge connected to %s with DEALER identity %s", self.endpoint, self.identity)
        # print(
        #     f"[ZLA][teleop_bridge][zmq] started endpoint={self.endpoint} "
        #     f"identity={self.identity} action_dim={self.action_dim}",
        #     flush=True,
        # )

    def stop(self) -> None:
        """Stop the receive loop and close the ZMQ socket without lingering."""

        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        if self._socket is not None:
            try:
                self._socket.close(linger=0)
            finally:
                self._socket = None
        self._poller = None

    def _send_ready(self) -> None:
        """Send a heartbeat so an external router can discover this bridge."""

        if self._socket is None:
            return
        payload = {
            "type": "teleop_bridge_ready",
            "identity": self.identity,
            "time": time.time(),
        }
        try:
            self._socket.send_json(payload, flags=self._zmq.NOBLOCK)
        except Exception:
            self.logger.debug("Failed to send ZMQ teleop ready heartbeat", exc_info=True)

    def _recv_loop(self) -> None:
        """Poll for ZMQ messages, parse them, and submit valid action arrays."""

        next_heartbeat = 0.0
        while self._running and self._socket is not None and self._poller is not None:
            now = time.perf_counter()
            if now >= next_heartbeat:
                self._send_ready()
                next_heartbeat = now + self.heartbeat_s

            events = dict(self._poller.poll(self.poll_timeout_ms))
            if self._socket not in events:
                continue

            try:
                frames = self._socket.recv_multipart(flags=self._zmq.NOBLOCK)
                payload = frames[-1] if frames else b""
                action = parse_zmq_teleop_message(payload, action_dim=self.action_dim)
            except Exception as exc:
                self.logger.warning("Drop invalid ZMQ teleop message", exc_info=True)
                # print(
                #     f"[ZLA][teleop_bridge][zmq] drop invalid message "
                #     f"frames={len(frames) if 'frames' in locals() else 'unknown'} error={exc}",
                #     flush=True,
                # )
                continue
            self._debug_count += 1
            now = time.perf_counter()
            if now - self._last_debug_s >= 1.0:
                self._last_debug_s = now
                # print(
                #     f"[ZLA][teleop_bridge][zmq] recv count={self._debug_count} "
                #     f"action={_brief_array(action)}",
                #     flush=True,
                # )
            self.submit_action(action, time.perf_counter())


def create_teleop_bridge(
    config,
    *,
    submit_action: Callable[[np.ndarray, float], None],
    action_dim: int,
    reset_handler: Optional[Callable[[], None]] = None,
    joint_state_provider: Optional[Callable[[], Optional[Sequence[float]]]] = None,
    joint_state_names: Optional[Sequence[str]] = None,
):
    """Construct the configured teleoperation bridge implementation.

    ``joint_state_provider`` and ``joint_state_names`` are used only by ROS2,
    where external teleop nodes need a live ``/client_robot/joint_states`` feed.
    ZMQ producers send full action arrays and therefore do not need robot-state
    publication.
    """

    bridge_type = str(_cfg_get(config, "bridge_type", "ros2")).lower()
    # print(f"[ZLA][teleop_bridge] create bridge_type={bridge_type} action_dim={action_dim}", flush=True)
    if bridge_type in ("ros", "ros2"):
        ros_cfg = _cfg_get(config, "ros2", None)
        device = _cfg_get(config, "control_device", _cfg_get(config, "device", "quest3"))
        device_cfg = _cfg_get(_cfg_get(config, "devices", None), str(device or "").lower(), None)
        if _cfg_has(ros_cfg, "reset_mode"):
            reset_mode_value = _cfg_get(ros_cfg, "reset_mode")
        elif _cfg_has(device_cfg, "reset_mode"):
            reset_mode_value = _cfg_get(device_cfg, "reset_mode")
        elif _cfg_has(config, "reset_mode"):
            reset_mode_value = _cfg_get(config, "reset_mode")
        elif str(device or "").lower() == "quest3":
            reset_mode_value = _read_quest3_config_reset_mode(device_cfg)
        else:
            reset_mode_value = None
        reset_mode = _normalize_reset_mode(reset_mode_value or "joint_command")
        return RosTeleopBridge(
            submit_action=submit_action,
            reset_handler=reset_handler,
            joint_state_provider=joint_state_provider,
            topic=_cfg_get(ros_cfg, "topic", "/target_robot/joint_commands"),
            reset_topic=_cfg_get(ros_cfg, "reset_topic", "/custom/custom_a"),
            joint_state_topic=_cfg_get(ros_cfg, "joint_state_topic", DEFAULT_CLIENT_JOINT_STATE_TOPIC),
            joint_state_names=joint_state_names or _cfg_get(ros_cfg, "joint_state_names", DEFAULT_CLIENT_JOINT_STATE_NAMES),
            joint_state_publish_rate=_cfg_get(ros_cfg, "joint_state_publish_rate", 30.0),
            action_dim=action_dim,
            node_name=_cfg_get(ros_cfg, "node_name", "vla_infer_teleop_bridge"),
            reset_threshold=_cfg_get(ros_cfg, "reset_threshold", 0.5),
            reset_mode=reset_mode,
            control_device=device,
            device_config=config,
        )
    if bridge_type == "zmq":
        zmq_cfg = _cfg_get(config, "zmq", None)
        return ZmqTeleopBridge(
            submit_action=submit_action,
            endpoint=_cfg_get(zmq_cfg, "endpoint", "tcp://127.0.0.1:5570"),
            action_dim=action_dim,
            identity=_cfg_get(zmq_cfg, "identity", "vla-infer-teleop"),
            poll_timeout_ms=_cfg_get(zmq_cfg, "poll_timeout_ms", 50),
            heartbeat_s=_cfg_get(zmq_cfg, "heartbeat_s", 1.0),
        )
    raise ValueError(f"Unsupported teleop bridge_type: {bridge_type}")
