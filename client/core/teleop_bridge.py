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
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

import numpy as np

from client.core.action_arbiter import (
    ActionArbiter,
    ActionSource,
    ActionTransitionFilter,
    SelectedAction,
)
from conf.client_conf import get_teleop_config_path
from conf.robots_conf import canonical_robot_type
from teleop.action_mapping import action_layout_from_robot_config
from teleop.config import config_get as _cfg_get
from teleop.config import normalize_reset_mode
from teleop.status import teleop_enabled, teleop_status_snapshot

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
        self.log_path: Optional[Path] = None
        self.log_file = None
        self._last_status_signature = None

    def start(self) -> None:
        """Start the configured device unless it is already running."""

        if self.process is not None and self.process.poll() is None:
            return
        if self.device in ("", "none", "manual", "external"):
            return

        self._close_log_file()
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
        device_cfg = _cfg_get(_cfg_get(self.config, "devices", None), self.device, None)
        log_path = _cfg_get(device_cfg, "log_path", "logs/quest3_teleop.log")
        repo_root = Path(__file__).resolve().parents[2]
        self.log_path = self._resolve_repo_path(log_path, repo_root)
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_file = self.log_path.open("a", encoding="utf-8", buffering=1)
            self.log_file.write(
                f"\n=== Quest3 process starting {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n"
            )
        except OSError:
            self.logger.exception("Failed to open Quest3 teleop log; inheriting stdio")
            self.log_file = None
        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                start_new_session=True,
                stdout=self.log_file,
                stderr=subprocess.STDOUT,
            )
        except Exception:
            self._close_log_file()
            self._remove_status_file()
            raise

    def stop(self) -> None:
        """Terminate the device process group with a short graceful timeout."""

        if self.process is None:
            self._close_log_file()
            self._remove_status_file()
            return
        proc = self.process
        self.process = None
        if proc.poll() is not None:
            self._close_log_file()
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
            self._close_log_file()
            self._remove_status_file()

    def _close_log_file(self) -> None:
        handle, self.log_file = self.log_file, None
        if handle is not None:
            try:
                handle.close()
            except Exception:
                pass

    def _record_status_transition(self, status: dict) -> None:
        """Log teleop process/connection/tracking changes once per transition."""
        signature = (
            status.get("state"),
            bool(status.get("device_connected", False)),
            bool(status.get("process_running", False)),
            status.get("left_tracking_valid"),
            status.get("right_tracking_valid"),
        )
        if signature == self._last_status_signature:
            return
        previous = self._last_status_signature
        self._last_status_signature = signature
        was_connected = bool(previous and previous[1])
        level = logging.WARNING if (
            status.get("state") == "error"
            or (was_connected and not status.get("device_connected", False))
        ) else logging.INFO
        self.logger.log(
            level,
            "Quest3 teleop status: state=%s connected=%s process_running=%s "
            "tracking(left=%s,right=%s) packets=%s packet_age=%s status_age=%s: %s",
            status.get("state"),
            status.get("device_connected"),
            status.get("process_running"),
            status.get("left_tracking_valid"),
            status.get("right_tracking_valid"),
            status.get("total_packets"),
            status.get("last_packet_age_s"),
            status.get("status_age_s"),
            status.get("message"),
        )

    def status(self) -> dict:
        """Return process liveness and the Quest3 TCP handshake state."""
        status = self._status_snapshot()
        self._record_status_transition(status)
        return status

    def _status_snapshot(self) -> dict:
        """Build one status snapshot without emitting transition logs."""
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
        process_is_running = True
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
        if payload.get("error"):
            message = f"{message} {payload['error']}"

        left_tracking = payload.get("left_tracking_valid")
        right_tracking = payload.get("right_tracking_valid")
        if connected and (left_tracking is False or right_tracking is False):
            lost = [
                side
                for side, valid in (("left", left_tracking), ("right", right_tracking))
                if valid is False
            ]
            message = f"{message} Controller tracking lost: {', '.join(lost)}."

        updated_at = payload.get("updated_at")
        status_age_s = None
        try:
            status_age_s = max(time.time() - float(updated_at), 0.0)
        except (TypeError, ValueError):
            pass
        if process_is_running and status_age_s is not None and status_age_s > 5.0:
            device_state = "error"
            connected = False
            message = (
                f"Quest3 status heartbeat is stale ({status_age_s:.1f}s); "
                "restart teleop or check the headset connection."
            )

        status.update(
            device_connected=connected,
            state=device_state,
            message=message,
            remote=payload.get("remote"),
            log_path=None if self.log_path is None else str(self.log_path),
            total_packets=int(payload.get("total_packets") or 0),
            last_packet_at=payload.get("last_packet_at"),
            last_packet_age_s=payload.get("last_packet_age_s"),
            left_tracking_valid=left_tracking,
            right_tracking_valid=right_tracking,
            status_age_s=status_age_s,
            error=payload.get("error"),
            updated_at=updated_at,
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
        submit_action: Callable[..., None],
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
        mask = self._command_mask(msg, action.shape[0])
        if mask is None:
            self.submit_action(action, time.perf_counter())
        else:
            self.submit_action(action, time.perf_counter(), mask=mask)

    def _command_mask(self, msg, action_dim: int) -> Optional[np.ndarray]:
        """Read the optional per-joint teleop mask carried in ``JointState.effort``.

        Producers that leave ``effort`` empty (reset interpolation, external
        publishers) yield ``None``, which the client treats as fully valid.
        """

        effort = getattr(msg, "effort", None)
        if effort is None or len(effort) == 0:
            return None
        try:
            values = np.asarray(effort, dtype=float).reshape(-1)
        except (TypeError, ValueError):
            values = None
        if values is None or values.shape[0] != action_dim or not np.all(np.isfinite(values)):
            self.logger.warning("Ignore malformed teleop command mask in JointState.effort")
            return None
        return values > 0.5

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
        submit_action: Callable[..., None],
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


@dataclass(frozen=True)
class TeleopControlDecision:
    """One action selected by the teleop runtime for the VLA control tick."""

    action: np.ndarray
    source: ActionSource
    mask: Optional[np.ndarray] = None
    policy_action: Optional[np.ndarray] = None


class TeleopRuntime:
    """Teleop state and helpers shared by the VLA client and Web runtime.

    This runtime keeps teleop-specific lifecycle, outlier validation, policy
    handoff, status, and recording logic out of the core VLA control loop.
    """

    _config_get = staticmethod(_cfg_get)

    def __init__(self, client) -> None:
        """Bind the runtime to the owning VLA client without taking over its lifecycle."""

        self.client = client

    def initialize(self) -> None:
        """Initialize teleop-only state on the owning VLA client."""

        client = self.client
        teleop_config = client.config.teleop
        self.client.action_arbiter = ActionArbiter(
            action_timeout_s=float(getattr(teleop_config, 'teleop_timeout_s', 0.15)),
            policy_timeout_s=float(getattr(teleop_config, 'policy_timeout_s', 0.5)),
        )
        self.client.action_transition_filter = ActionTransitionFilter(
            transition_steps=int(getattr(teleop_config, 'action_transition_steps', 64)),
            max_delta_per_step=getattr(teleop_config, 'action_transition_max_delta_per_step', None),
        )
        self.client.teleop_bridge = None
        self.client._teleop_outlier_reject_count = 0
        self.client._teleop_outlier_last_log_s = 0.0
        self.client._last_executed_action = None
        self.client._last_executed_action_lock = threading.Lock()
        self.client._action_select_last_debug_s = 0.0
        self.client._teleop_policy_handoff_active = False
        self.client._teleop_policy_handoff_hold_action = None
        self.client._teleop_policy_handoff_started_s = None
        self.client._policy_generation = 0
        self.client._policy_generation_lock = threading.Lock()

    def _reset_teleop_command_state(self) -> None:
        """Drop all command/handoff state that belongs before a robot reset."""

        self.client.action_arbiter.clear()
        self.client.action_transition_filter.reset()
        self._reset_teleop_policy_handoff()

    def _teleop_bridge_config(self):
        """Return the grouped teleop config, if present."""
        return getattr(self.client.config, 'teleop', None)

    def _use_teleop_enabled(self) -> bool:
        """Return whether bridge-based human teleoperation is enabled."""

        return teleop_enabled(self.client.config)

    def set_teleop_enabled(self, enabled: bool):
        """Enable or disable the teleop bridge at runtime."""
        teleop_cfg = self._teleop_bridge_config()
        if teleop_cfg is not None:
            teleop_cfg.use_teleop = bool(enabled)
        elif hasattr(self.client.config, 'use_teleop'):
            self.client.config.use_teleop = bool(enabled)
        if bool(enabled) and self.client.is_running:
            self.start_teleop_bridge()
        else:
            self.stop_teleop_bridge()
            self.client.action_arbiter.clear()
            self.client.action_transition_filter.reset()
            self._reset_teleop_policy_handoff()

    def _resolve_teleop_device_config(self) -> bool:
        """Resolve the Quest3 YAML from the selected robot type when enabled."""
        teleop_cfg = self._teleop_bridge_config()
        device = str(self._config_get(teleop_cfg, 'control_device', '') or '').lower()
        if device != 'quest3':
            return True
        device_cfg = self._config_get(self._config_get(teleop_cfg, 'devices', None), 'quest3', None)
        if device_cfg is None:
            self.client.logger.warning("Quest3 teleop device config is missing; teleop bridge will not start.")
            return False
        # This is an internal, non-user-editable setting. Keep it forced on for
        # every bridge start so a persisted path can never override the mapping.
        device_cfg.auto_config_path = True
        robot_type = self._config_get(getattr(self.client.config, 'robots', None), 'type', '')
        if hasattr(robot_type, 'value'):
            robot_type = robot_type.value
        robot_type = str(robot_type or '').lower()
        config_path = get_teleop_config_path(robot_type)
        if not config_path:
            self.client.logger.warning(
                "Quest3 teleop is not supported for robot type %r; teleop bridge will not start.",
                robot_type,
            )
            return False
        device_cfg.config_path = str(config_path)
        self.client.logger.info("Resolved Quest3 teleop config for robot type %s: %s", robot_type, config_path)
        return True

    def start_teleop_bridge(self):
        """Create and start the configured teleop bridge."""
        if not self._use_teleop_enabled():
            return
        if not self._resolve_teleop_device_config():
            return
        if self.client.teleop_bridge is None:
            robot_type = self._config_get(getattr(self.client.config, 'robots', None), 'type', '')
            if hasattr(robot_type, 'value'):
                robot_type = robot_type.value
            robot_type = str(robot_type or '')
            robot_config_name = canonical_robot_type(robot_type)
            robot_cfg = self._config_get(
                getattr(self.client.config, 'robots', None),
                robot_config_name,
                None,
            )
            action_layout = action_layout_from_robot_config(robot_cfg)
            robot_action_dim = int(getattr(self.client.robot, 'action_dim', 0) or 0)
            if robot_action_dim and robot_action_dim != action_layout.action_dim:
                raise ValueError(
                    f"Teleop layout for {robot_config_name!r} has {action_layout.action_dim} "
                    f"dims but the robot reports {robot_action_dim}"
                )
            action_dim = robot_action_dim or action_layout.action_dim
            self.client.teleop_bridge = create_teleop_bridge(
                self._teleop_bridge_config(),
                submit_action=self.submit_teleop_bridge_action,
                action_dim=action_dim,
                reset_handler=self.client.reset_robot,
                joint_state_provider=self.get_teleop_joint_state,
                action_names=action_layout.action_names,
                native_reset_action=self._config_get(robot_cfg, 'reset_robot_pos', None),
            )
        self.client.teleop_bridge.start()

    def stop_teleop_bridge(self):
        """Stop the bridge and clear fresh-human-action state."""
        if self.client.teleop_bridge is not None:
            self.client.teleop_bridge.stop()
        self.client.action_arbiter.clear_source(ActionSource.TELEOP)
        self._reset_teleop_policy_handoff()
        self._reset_teleop_outlier_guard()

    def restart_teleop_bridge(self):
        """Recreate the bridge after device/topic/joint-name config changes."""
        was_running = self.client.teleop_bridge is not None and self.client.teleop_bridge.running
        self.stop_teleop_bridge()
        self.client.teleop_bridge = None
        self.client.action_arbiter.clear()
        self.client.action_transition_filter.reset()
        self._reset_teleop_policy_handoff()
        if was_running or (self.client.is_running and self._use_teleop_enabled()):
            self.start_teleop_bridge()

    def submit_teleop_bridge_action(self, action, timestamp=None, mask=None):
        """Receive one teleop action from the bridge and submit it to arbitration.

        ``mask`` optionally marks which entries are real human control data;
        ``None`` means the whole action is treated as human-controlled.
        """
        if timestamp is None:
            timestamp = time.perf_counter()
        action_arr = self._validate_teleop_bridge_action(action, timestamp=timestamp)
        if action_arr is None:
            self._hold_teleop_after_rejected_action(timestamp)
            return
        mask_arr = None
        if mask is not None:
            mask_arr = np.asarray(mask, dtype=bool).reshape(-1)
            if mask_arr.shape != action_arr.shape:
                self.client.logger.warning(
                    'Ignore teleop mask with shape %s for action shape %s', mask_arr.shape, action_arr.shape
                )
                mask_arr = None
        self.client.action_arbiter.submit(ActionSource.TELEOP, action_arr, timestamp, mask=mask_arr)
        self.client._teleop_outlier_reject_count = 0

    def _validate_teleop_bridge_action(self, action, timestamp: Optional[float] = None) -> Optional[np.ndarray]:
        """Reject malformed or implausibly large teleop jumps before arbitration."""
        if timestamp is None:
            timestamp = time.perf_counter()
        try:
            action_arr = np.asarray(action, dtype=float).reshape(-1)
        except (TypeError, ValueError):
            self._log_teleop_outlier('non-numeric teleop action')
            return None
        if action_arr.size == 0:
            self._log_teleop_outlier('empty teleop action')
            return None
        if not np.all(np.isfinite(action_arr)):
            self._log_teleop_outlier('non-finite teleop action')
            return None
        action_layout = self._teleop_action_layout()
        if action_arr.size != action_layout.action_dim:
            self._log_teleop_outlier(
                f'teleop action width {action_arr.size} does not match target layout '
                f'{action_layout.action_dim}'
            )
            return None
        teleop_config = self.client.config.teleop
        if not bool(getattr(teleop_config, 'teleop_outlier_guard_enabled', True)):
            return action_arr

        baseline, baseline_source = self._teleop_outlier_baseline_snapshot(
            action_arr.shape[0], now=timestamp
        )
        if baseline is None:
            return action_arr
        if baseline.shape != action_arr.shape:
            self._log_teleop_outlier(
                f'teleop baseline shape mismatch action={action_arr.shape} baseline={baseline.shape}'
            )
            return None

        delta = np.abs(action_arr - baseline)
        arm_count = min(14, delta.shape[0])
        if arm_count:
            max_arm_joint_delta = getattr(teleop_config, 'teleop_outlier_max_arm_joint_delta', 0.5)
            if max_arm_joint_delta is not None and np.max(delta[:arm_count]) > float(max_arm_joint_delta):
                self.client._teleop_outlier_reject_count += 1
                joint_index = int(np.argmax(delta[:arm_count]))
                joint_name = action_layout.action_names[joint_index]
                self._log_teleop_outlier(
                    'arm joint %s[%d] jump %.4f exceeds %.4f; '
                    'incoming=%.6f baseline=%.6f baseline_source=%s; reject_count=%d'
                    % (
                        joint_name,
                        joint_index,
                        float(delta[joint_index]),
                        float(max_arm_joint_delta),
                        float(action_arr[joint_index]),
                        float(baseline[joint_index]),
                        baseline_source,
                        self.client._teleop_outlier_reject_count,
                    )
                )
                return None
            max_arm_norm_delta = getattr(teleop_config, 'teleop_outlier_max_arm_norm_delta', 1.2)
            if max_arm_norm_delta is not None and np.linalg.norm(delta[:arm_count]) > float(max_arm_norm_delta):
                self.client._teleop_outlier_reject_count += 1
                self._log_teleop_outlier(
                    'arm norm jump %.4f exceeds %.4f; baseline_source=%s; reject_count=%d'
                    % (
                        float(np.linalg.norm(delta[:arm_count])),
                        float(max_arm_norm_delta),
                        baseline_source,
                        self.client._teleop_outlier_reject_count,
                    )
                )
                return None
        if delta.shape[0] > 14:
            max_hand_delta = getattr(teleop_config, 'teleop_outlier_max_gripper_delta', 1.0)
            if max_hand_delta is not None:
                max_hand_delta = float(max_hand_delta) * action_layout.hand_value_scale
            if max_hand_delta is not None and np.max(delta[14:]) > float(max_hand_delta):
                self.client._teleop_outlier_reject_count += 1
                self._log_teleop_outlier(
                    'hand jump %.4f exceeds %.4f; reject_count=%d'
                    % (float(np.max(delta[14:])), float(max_hand_delta), self.client._teleop_outlier_reject_count)
                )
                return None
        return action_arr

    def _teleop_robot_config(self):
        """Return the active robot configuration used by teleop conversion."""

        robots_cfg = getattr(self.client.config, 'robots', None)
        robot_type = self._config_get(robots_cfg, 'type', '')
        if hasattr(robot_type, 'value'):
            robot_type = robot_type.value
        return self._config_get(robots_cfg, canonical_robot_type(robot_type), None)

    def _teleop_action_layout(self):
        """Return the target robot layout used by the teleop producer."""

        return action_layout_from_robot_config(self._teleop_robot_config())

    @staticmethod
    def _teleop_record_fields(executed_action, selected_source, teleop_mask=None, policy_action=None) -> dict:
        """Build the per-frame teleop intervention fields for data recording.

        - ``teleop_action``: the executed action while a human is in control, else zeros.
        - ``teleop_action_mask``: entries of ``teleop_action`` carrying real human
          control data; all True when the producer did not provide a mask.
        - ``rejected_action``: the policy action that would have been executed,
          when a human overrode an available policy action, else zeros.
        - ``rejected_action_mask``: entries of ``rejected_action`` actually replaced
          by human control.
        - ``is_teleop``: whether fresh human input selected this action.
        """
        executed = np.asarray(executed_action, dtype=np.float32).reshape(-1)
        width = executed.shape[0]
        is_teleop = selected_source == ActionSource.TELEOP
        if is_teleop:
            teleop_action = executed.copy()
            if teleop_mask is None:
                teleop_mask = np.ones(width, dtype=bool)
            else:
                teleop_mask = np.asarray(teleop_mask, dtype=bool).reshape(-1).copy()
        else:
            teleop_action = np.zeros(width, dtype=np.float32)
            teleop_mask = np.zeros(width, dtype=bool)

        if is_teleop and policy_action is not None:
            rejected_action = np.asarray(policy_action, dtype=np.float32).reshape(-1).copy()
            rejected_mask = np.zeros(rejected_action.shape[0], dtype=bool)
            overlap = min(rejected_mask.shape[0], teleop_mask.shape[0])
            rejected_mask[:overlap] = teleop_mask[:overlap]
        else:
            rejected_action = np.zeros(width, dtype=np.float32)
            rejected_mask = np.zeros(width, dtype=bool)

        return {
            'teleop_action': teleop_action,
            'teleop_action_mask': teleop_mask,
            'rejected_action': rejected_action,
            'rejected_action_mask': rejected_mask,
            'is_teleop': bool(is_teleop),
        }

    def _teleop_outlier_baseline_snapshot(
        self,
        action_dim: int,
        now: Optional[float] = None,
    ) -> tuple[Optional[np.ndarray], str]:
        """Return the outlier baseline and the source used to build it."""
        if now is None:
            now = time.perf_counter()
        last_teleop_s = self.client.action_arbiter.last_submitted_at(ActionSource.TELEOP)
        timeout_s = float(getattr(self.client.config.teleop, 'teleop_timeout_s', 0.15))
        if last_teleop_s is not None and now - last_teleop_s <= timeout_s:
            last_teleop_action = self.client.action_arbiter.latest_action(ActionSource.TELEOP)
            if last_teleop_action is not None:
                return last_teleop_action, 'teleop(age=%.3fs)' % (now - last_teleop_s)
        baseline = self._coerce_state_to_action_shape(self._get_last_executed_action(), action_dim)
        if baseline is not None:
            return baseline, 'last_executed'
        baseline = self._coerce_state_to_action_shape(getattr(self.client.robot, 'current_state', None), action_dim)
        if baseline is not None:
            return baseline, 'measured_state'
        return None, 'unavailable'

    def _teleop_outlier_baseline(self, action_dim: int, now: Optional[float] = None) -> Optional[np.ndarray]:
        """Return a current-safe baseline for backward-compatible callers."""
        baseline, _ = self._teleop_outlier_baseline_snapshot(action_dim, now=now)
        return baseline

    @staticmethod
    def _coerce_state_to_action_shape(values, action_dim: int) -> Optional[np.ndarray]:
        """Map a robot state/action vector into the flat teleop action layout."""
        if values is None:
            return None
        try:
            arr = np.asarray(values, dtype=float).reshape(-1)
        except (TypeError, ValueError):
            return None
        if arr.shape[0] == action_dim:
            return arr.copy()
        if arr.shape[0] >= action_dim:
            return arr[:action_dim].copy()
        return None

    def _hold_teleop_after_rejected_action(self, timestamp: float) -> None:
        """Hold only a live session's safe action, or release a bad stream."""
        reject_threshold = max(int(getattr(
            self.client.config.teleop, 'teleop_outlier_reanchor_after_rejects', 5
        )), 1)
        if self.client._teleop_outlier_reject_count >= reject_threshold:
            if self.client._teleop_outlier_reject_count == reject_threshold:
                self.client.logger.warning(
                    'Release teleop ownership after %d consecutive rejected actions.',
                    self.client._teleop_outlier_reject_count,
                )
            self.client.action_arbiter.clear_source(ActionSource.TELEOP)
            return

        last_teleop_s = self.client.action_arbiter.last_submitted_at(ActionSource.TELEOP)
        timeout_s = float(getattr(self.client.config.teleop, 'teleop_timeout_s', 0.15))
        if last_teleop_s is None or float(timestamp) - last_teleop_s > timeout_s:
            return

        hold_action = self.client.action_arbiter.latest_action(ActionSource.TELEOP)
        if hold_action is None:
            return
        hold_mask = self.client.action_arbiter.latest_mask(ActionSource.TELEOP)
        hold_action = np.asarray(hold_action, dtype=float).copy()
        self.client.action_arbiter.submit(ActionSource.TELEOP, hold_action, timestamp, mask=hold_mask)

    def _reset_teleop_outlier_guard(self) -> None:
        self.client._teleop_outlier_reject_count = 0

    def _log_teleop_outlier(self, reason: str) -> None:
        now = time.perf_counter()
        interval_s = float(getattr(self.client.config.teleop, 'teleop_outlier_log_interval_s', 1.0))
        if now - self.client._teleop_outlier_last_log_s < interval_s:
            return
        self.client._teleop_outlier_last_log_s = now
        self.client.logger.warning('Drop teleop outlier action: %s', reason)

    def get_teleop_joint_state(self):
        """Return command-biased robot state for Quest3 IK feedback."""
        state = getattr(self.client.robot, 'current_state', None)
        state = None if state is None else np.asarray(state, dtype=float).reshape(-1).copy()
        last_action = self._get_last_executed_action()
        if last_action is None:
            return state
        if state is None:
            return last_action
        merged = state.copy()
        if merged.shape[0] < last_action.shape[0]:
            merged = np.pad(merged, (0, last_action.shape[0] - merged.shape[0]))
        command_dim = min(merged.shape[0], last_action.shape[0])
        merged[:command_dim] = last_action[:command_dim]
        return merged

    def _get_last_executed_action(self):
        with self.client._last_executed_action_lock:
            return None if self.client._last_executed_action is None else self.client._last_executed_action.copy()

    def _set_last_executed_action(self, action) -> None:
        value = None if action is None else np.asarray(action, dtype=float).reshape(-1).copy()
        with self.client._last_executed_action_lock:
            self.client._last_executed_action = value

    def is_teleop_human_active(self) -> bool:
        """Return whether fresh teleop input is currently controlling the robot."""
        if self.client.teleop_bridge is None or not self.client.teleop_bridge.running:
            return False
        last_teleop_s = self.client.action_arbiter.last_submitted_at(ActionSource.TELEOP)
        if last_teleop_s is None:
            return False
        timeout_s = float(getattr(self.client.config.teleop, 'teleop_timeout_s', 0.15))
        return time.perf_counter() - last_teleop_s <= timeout_s

    def _publish_teleop_anchor_state(self) -> None:
        """Publish command-biased feedback while no human input is active."""

        if (
            self.client.teleop_bridge is not None
            and self.client.teleop_bridge.running
            and not self.is_teleop_human_active()
        ):
            try:
                self.client.teleop_bridge.publish_joint_state()
            except Exception:
                self.client.logger.warning("Failed to publish teleop anchor state", exc_info=True)

    @property
    def teleop_status(self) -> dict:
        """Return teleop bridge and managed device connectivity state."""

        return teleop_status_snapshot(self.client.config, bridge=self.client.teleop_bridge)

    def _action_for_selected_source(self, selected: SelectedAction) -> np.ndarray:
        if selected.source == ActionSource.TELEOP:
            action = np.asarray(selected.action, dtype=float).copy()
            # Keep the transition filter seeded with the exact human command so a
            # later policy handoff starts from the robot's actual last command.
            self.client.action_transition_filter.reset(last_output=action)
            return action
        return self.client.action_transition_filter.filter(selected)

    def _reset_teleop_policy_handoff(self) -> None:
        """Clear teleop-to-policy handoff state."""
        self.client._teleop_policy_handoff_active = False
        self.client._teleop_policy_handoff_hold_action = None
        self.client._teleop_policy_handoff_started_s = None

    def _current_policy_generation(self) -> int:
        with self.client._policy_generation_lock:
            return self.client._policy_generation

    def _invalidate_policy_generation(self) -> int:
        with self.client._policy_generation_lock:
            self.client._policy_generation += 1
            return self.client._policy_generation

    def _is_policy_generation_current(self, generation: int) -> bool:
        with self.client._policy_generation_lock:
            return generation == self.client._policy_generation

    def _start_teleop_policy_handoff(self, hold_action) -> bool:
        """Hold the final teleop action until a fresh policy chunk arrives.

        The policy generation is invalidated so inference replies that were
        already in flight when teleop ended cannot be applied. Existing policy
        chunks are cleared because their time base belongs to the pre-handoff
        state; the next fresh reply will be fused from the held human action.
        """
        if hold_action is None:
            return False
        self.client._teleop_policy_handoff_hold_action = np.asarray(hold_action, dtype=float).copy()
        self.client._teleop_policy_handoff_active = True
        self.client._teleop_policy_handoff_started_s = time.perf_counter()
        self._invalidate_policy_generation()
        self.client.realtime_data_manager.clear_policy_actions()
        self.client.action_arbiter.clear_source(ActionSource.POLICY)
        self.client.action_arbiter.clear_source(ActionSource.TELEOP)
        self.client.action_transition_filter.reset(last_output=self.client._teleop_policy_handoff_hold_action)
        self._reset_teleop_outlier_guard()
        self.client.logger.info("Teleop exited; holding final teleop action until a fresh policy chunk is available.")
        return True

    def _select_teleop_policy_handoff_action(self):
        """Return the held teleop action while waiting for fresh policy output."""
        if not self.client._teleop_policy_handoff_active:
            return None, None, None
        hold_action = self.client._teleop_policy_handoff_hold_action
        if hold_action is None:
            self._reset_teleop_policy_handoff()
            return None, None, None
        return hold_action.copy(), ActionSource.HOLD, None

    def _teleop_policy_handoff_state_for_fusion(self, action_dim: int):
        """Return the held teleop action as the inter-chunk fusion anchor."""
        if not self.client._teleop_policy_handoff_active or self.client._teleop_policy_handoff_hold_action is None:
            return None, None, None
        currt_action = self._coerce_state_to_action_shape(
            self.client._teleop_policy_handoff_hold_action,
            action_dim,
        )
        if currt_action is None:
            return None, None, None
        currt_vel = np.zeros_like(currt_action)
        currt_acc = np.zeros_like(currt_action)
        return currt_action, currt_vel, currt_acc

    def _complete_teleop_policy_handoff(self, action_chunk_smoothed, target_chunk_index: int) -> None:
        """Finish handoff after the fused policy chunk has been published."""
        first_policy_action = np.asarray(action_chunk_smoothed[:, int(target_chunk_index)], dtype=float).copy()
        self.client.action_transition_filter.reset(last_output=first_policy_action)
        self.client.action_arbiter.clear()
        self.client.action_arbiter.submit(ActionSource.POLICY, first_policy_action, time.perf_counter())
        self._reset_teleop_policy_handoff()

    def _resolve_teleop_control_action(
        self,
        policy_action,
        *,
        now: Optional[float] = None,
    ) -> Optional[TeleopControlDecision]:
        """Resolve policy, teleop, HOLD, and teleop-to-policy handoff for one tick."""

        if now is None:
            now = time.perf_counter()

        if self.client._teleop_policy_handoff_active:
            last_teleop_s = self.client.action_arbiter.last_submitted_at(ActionSource.TELEOP)
            new_teleop_after_handoff = (
                last_teleop_s is not None
                and self.client._teleop_policy_handoff_started_s is not None
                and last_teleop_s > self.client._teleop_policy_handoff_started_s
            )
            if new_teleop_after_handoff:
                self.client.logger.info("Fresh teleop input interrupted teleop-to-policy handoff.")
                self._reset_teleop_policy_handoff()
            else:
                hold_action, hold_source, hold_policy_action = self._select_teleop_policy_handoff_action()
                if hold_action is None:
                    return None
                return TeleopControlDecision(
                    action=np.asarray(hold_action, dtype=float),
                    source=hold_source,
                    policy_action=hold_policy_action,
                )

        if policy_action is not None:
            self.client.action_arbiter.submit(ActionSource.POLICY, policy_action, now)

        selected = self.client.action_arbiter.select(now=now)
        if selected is None:
            return None

        if (
            selected.previous_source == ActionSource.TELEOP
            and selected.source != ActionSource.TELEOP
        ):
            last_executed_action = self._get_last_executed_action()
            hold_action = last_executed_action if last_executed_action is not None else selected.action
            if self._start_teleop_policy_handoff(hold_action):
                hold_action, hold_source, hold_policy_action = self._select_teleop_policy_handoff_action()
                if hold_action is None:
                    return None
                return TeleopControlDecision(
                    action=np.asarray(hold_action, dtype=float),
                    source=hold_source,
                    policy_action=hold_policy_action,
                )

        action = self._action_for_selected_source(selected)
        if now - self.client._action_select_last_debug_s >= 1.0:
            self.client._action_select_last_debug_s = now
            self.client.logger.debug("Action arbiter selected source=%s", selected.source.value)
        return TeleopControlDecision(
            action=action,
            source=selected.source,
            mask=selected.mask,
            policy_action=policy_action,
        )


def create_teleop_bridge(
    config,
    *,
    submit_action: Callable[..., None],
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
