"""Runtime transport bridges between teleop producers and the VLA client.

Teleop semantics (joint layout, hand dimensions, continuous/discrete mapping)
live under :mod:`teleop`.  This module only moves already-processed state/action
messages over ROS2 or ZMQ and forwards valid action vectors to the client.
"""

import json
import logging
import os
from pathlib import Path
import signal
import shlex
import subprocess
import sys
import tempfile
import threading
import time
from abc import ABC, abstractmethod
from typing import Callable, Optional, Sequence

import numpy as np

from teleop.config import config_get as _cfg_get
from teleop.config import normalize_reset_mode

DEFAULT_CLIENT_JOINT_STATE_TOPIC = "/client_robot/joint_states"


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

    @property
    def running(self) -> bool:
        """Return whether the concrete bridge has been started."""

        return bool(getattr(self, "_running", False))

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    def publish_joint_state(self) -> None:
        """Publish the latest teleop anchor state when the bridge supports it."""

        return

    def status(self) -> dict:
        """Return a JSON-serializable snapshot of bridge and device state."""

        return {"bridge_running": False, "device_connected": False, "state": "disabled"}


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
        action_names: Optional[Sequence[str]] = None,
        native_reset_action: Optional[Sequence[float]] = None,
    ):
        self.device = str(device or "none").lower()
        self.config = config
        self.command_topic = command_topic
        self.joint_state_topic = joint_state_topic
        self.reset_topic = reset_topic
        self.reset_mode = normalize_reset_mode(reset_mode)
        self.action_names = None if action_names is None else [str(name) for name in action_names]
        self.native_reset_action = (
            None if native_reset_action is None else [float(value) for value in native_reset_action]
        )
        self.logger = logging.getLogger(__name__)
        self.process: Optional[subprocess.Popen] = None
        self.status_file: Optional[Path] = None

    def start(self) -> None:
        """Start the configured device unless it is already running."""

        if self.process is not None and self.process.poll() is None:
            return
        if self.device in ("", "none", "manual", "external"):
            return

        self._remove_status_file()
        if self.device == "quest3":
            fd, status_path = tempfile.mkstemp(prefix="openrail_quest3_", suffix=".json")
            os.close(fd)
            self.status_file = Path(status_path)
            try:
                self.status_file.unlink()
            except FileNotFoundError:
                pass
        cmd, env, cwd = self._build_command()
        if not cmd:
            return
        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                start_new_session=True,
            )
        except Exception:
            self._remove_status_file()
            raise

    def stop(self) -> None:
        """Terminate the device process group with a short graceful timeout."""

        if self.process is None:
            self._remove_status_file()
            return
        proc = self.process
        self.process = None
        if proc.poll() is not None:
            self._remove_status_file()
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
        finally:
            self._remove_status_file()

    def status(self) -> dict:
        """Return process liveness and the Quest3 TCP handshake state."""

        status = {
            "device": self.device,
            "process_running": False,
            "process_pid": None,
            "device_connected": False,
            "state": "unavailable",
            "message": "Teleop device process is not running.",
        }
        if self.device in ("", "none", "manual", "external"):
            status.update(state="disabled", message="No managed teleop device is configured.")
            return status
        if self.process is None:
            return status

        status["process_pid"] = self.process.pid
        return_code = self.process.poll()
        if return_code is not None:
            status.update(
                state="error",
                message=f"Quest3 process exited with code {return_code}.",
            )
            return status

        status.update(process_running=True, state="starting", message="Quest3 process is starting.")
        if self.status_file is None or not self.status_file.is_file():
            return status
        try:
            payload = json.loads(self.status_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return status
        if not isinstance(payload, dict):
            return status

        device_state = str(payload.get("state") or "starting")
        connected = bool(payload.get("connected", False))
        message = {
            "starting": "Quest3 process is starting.",
            "listening": "Quest3 bridge is listening; waiting for Quest3 to connect.",
            "connected": "Quest3 device connected.",
            "stopped": "Quest3 bridge stopped.",
            "error": "Quest3 bridge failed to start.",
        }.get(device_state, f"Quest3 device state: {device_state}.")
        if device_state == "error" and payload.get("error"):
            message = f"{message} {payload['error']}"
        status.update(
            device_connected=connected,
            state=device_state,
            message=message,
            remote=payload.get("remote"),
            total_packets=int(payload.get("total_packets") or 0),
            error=payload.get("error"),
            updated_at=payload.get("updated_at"),
        )
        return status

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
        if self.status_file is not None:
            env["OPENRAIL_TELEOP_STATUS_FILE"] = str(self.status_file)
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
            if self.action_names is not None:
                cmd.extend(["--action-names", json.dumps(self.action_names)])
            if self.native_reset_action is not None:
                cmd.extend(["--native-reset-action", json.dumps(self.native_reset_action)])
            if bool(_cfg_get(device_cfg, "no_adb_reverse", False)):
                cmd.append("--no-adb-reverse")
            listen_port = _cfg_get(device_cfg, "listen_port", None)
            if listen_port is not None:
                cmd.extend(["--listen-port", str(listen_port)])
            if self.status_file is not None:
                cmd.extend(["--status-file", str(self.status_file)])
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

    def _remove_status_file(self) -> None:
        if self.status_file is None:
            return
        try:
            self.status_file.unlink()
        except FileNotFoundError:
            pass
        self.status_file = None


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
        action_names: Optional[Sequence[str]] = None,
        joint_state_publish_rate: float = 30.0,
        node_name: str = "vla_infer_teleop_bridge",
        reset_threshold: float = 0.5,
        reset_mode: str = "joint_command",
        control_device: str = "quest3",
        device_config=None,
        native_reset_action=None,
    ):
        self.submit_action = submit_action
        self.reset_handler = reset_handler
        self.joint_state_provider = joint_state_provider
        self.topic = topic
        self.reset_topic = reset_topic
        self.joint_state_topic = joint_state_topic
        if not action_names:
            raise ValueError("RosTeleopBridge requires the target robot action_names")
        self.action_names = tuple(str(name) for name in action_names)
        self.joint_state_publish_rate = max(float(joint_state_publish_rate), 0.0)
        self.action_dim = len(self.action_names)
        self.node_name = node_name
        self.reset_threshold = float(reset_threshold)
        self.reset_mode = normalize_reset_mode(reset_mode)
        self.control_device = str(control_device or "none").lower()
        self.device_config = device_config
        self.native_reset_action = native_reset_action
        self.logger = logging.getLogger(__name__)
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._rclpy = None
        self._node = None
        self._JointState = None
        self._joint_state_pub = None
        self._device_process: Optional[TeleopDeviceProcess] = None
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
            action_names=self.action_names,
            native_reset_action=self.native_reset_action,
        )
        self._device_process.start()
        self.logger.info("ROS teleop bridge subscribed to %s", self.topic)

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
            if positions.shape[0] < len(self.action_names):
                positions = np.pad(positions, (0, len(self.action_names) - positions.shape[0]))
            positions = positions[:len(self.action_names)]
        except Exception as exc:
            self.logger.warning("Drop invalid client robot joint state", exc_info=True)
            return

        msg = self._JointState()
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.name = list(self.action_names)
        msg.position = [float(v) for v in positions]
        self._joint_state_pub.publish(msg)

    def status(self) -> dict:
        """Expose ROS bridge and managed device connectivity for the Web UI."""

        status = {
            "bridge_running": bool(self._running),
            "device": self.control_device,
            "device_connected": False,
            "state": "disabled" if not self._running else "starting",
            "message": "Teleop bridge is stopped.",
            "topic": self.topic,
        }
        if self._device_process is not None:
            status.update(self._device_process.status())
        elif self._running and self.control_device in ("", "none", "manual", "external"):
            status.update(
                state="external",
                message="External teleop producer is expected on the configured ROS topic.",
            )
        return status

    def _command_cb(self, msg) -> None:
        """Receive a named teleop command and submit it to VLA action arbitration."""

        try:
            if len(msg.name) != len(msg.position):
                raise ValueError("JointState name and position lengths differ")
            if tuple(str(name) for name in msg.name) != self.action_names:
                raise ValueError(
                    "Teleop action JointState names do not match the target action layout"
                )
            action = np.asarray(msg.position, dtype=float)
        except Exception as exc:
            self.logger.warning("Drop invalid teleop JointState", exc_info=True)
            return
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
        try:
            self.reset_handler()
        except Exception as exc:
            self.logger.error("Teleop reset handler failed: %s", exc, exc_info=True)


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

    def status(self) -> dict:
        return {
            "bridge_running": bool(self._running),
            "device": "zmq",
            "device_connected": bool(self._running),
            "state": "connected" if self._running else "disabled",
            "message": "ZMQ teleop bridge is running." if self._running else "ZMQ teleop bridge is stopped.",
            "topic": self.endpoint,
        }

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
                continue
            self.submit_action(action, time.perf_counter())


def create_teleop_bridge(
    config,
    *,
    submit_action: Callable[[np.ndarray, float], None],
    action_dim: int,
    reset_handler: Optional[Callable[[], None]] = None,
    joint_state_provider: Optional[Callable[[], Optional[Sequence[float]]]] = None,
    action_names: Optional[Sequence[str]] = None,
    native_reset_action: Optional[Sequence[float]] = None,
):
    """Construct the configured teleoperation bridge implementation.

    ``action_names`` is the target robot action layout produced by the teleop
    mapping layer.  ROS2 uses the same names for the state and command topics.
    ZMQ producers send target-native arrays directly.
    """

    bridge_type = str(_cfg_get(config, "bridge_type", "ros2")).lower()
    if bridge_type in ("ros", "ros2"):
        ros_cfg = _cfg_get(config, "ros2", None)
        device = _cfg_get(config, "control_device", _cfg_get(config, "device", "quest3"))
        device_cfg = _cfg_get(_cfg_get(config, "devices", None), str(device or "").lower(), None)
        if str(device or "").lower() == "quest3":
            reset_mode_value = _read_quest3_config_reset_mode(device_cfg)
        else:
            reset_mode_value = _cfg_get(config, "reset_mode", None)
        reset_mode = normalize_reset_mode(reset_mode_value or "joint_command")
        return RosTeleopBridge(
            submit_action=submit_action,
            reset_handler=reset_handler,
            joint_state_provider=joint_state_provider,
            topic=_cfg_get(ros_cfg, "topic", "/target_robot/joint_commands"),
            reset_topic=_cfg_get(ros_cfg, "reset_topic", "/custom/custom_a"),
            joint_state_topic=_cfg_get(ros_cfg, "joint_state_topic", DEFAULT_CLIENT_JOINT_STATE_TOPIC),
            action_names=action_names,
            joint_state_publish_rate=_cfg_get(ros_cfg, "joint_state_publish_rate", 30.0),
            node_name=_cfg_get(ros_cfg, "node_name", "vla_infer_teleop_bridge"),
            reset_threshold=_cfg_get(ros_cfg, "reset_threshold", 0.5),
            reset_mode=reset_mode,
            control_device=device,
            device_config=config,
            native_reset_action=native_reset_action,
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
