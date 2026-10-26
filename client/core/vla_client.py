import cv2
import math
import time
import logging
import threading
import numpy as np

from queue import Queue, Empty, Full
from typing import Optional
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor

from client.utils import misc
from client.utils.util import run_time_decorator
from client.utils.multi_thread_timer import MultiThreadTimer
from client.core.zmq_client import ZMQClient
from client.core.inter_chunk_fuser import InterChunkFuser
from client.core.intra_chunk_smoother import IntraChunkSmoother
from client.core.realtime_data_manager import RealtimeDataManager
from client.core.task_language_manager import TaskLanguageManager
from client.core.visualize_server import VisualizeServer
from client.core.action_arbiter import ActionArbiter, ActionSource, ActionTransitionFilter, SelectedAction
from client.core.teleop_bridge import create_teleop_bridge
from client.core.data_record_manager import DataRecordManager
from client.core.shared_memory_manager import SharedMemoryManager
from client.robots.base_robot import RobotBase


class VLAClient():
    """VLA (Vision-Language-Action) Client for real-time robot control.
    
    This class manages the complete pipeline for VLA-based robot control, including:
    - Observation data collection from robot sensors
    - Communication with VLA inference server
    - Trajectory generation and fitting
    - Real-time robot control
    - Data recording for dataset creation

    Core functionalities and key methods include:
    - Pipeline Management: `start()`, `pause()`, `resume()`, and `close()` to control the lifecycle of observation, inference, control, and visualization threads.
    - Data Recording: `start_recording()`, `stop_recording()`, and `pause_recording()` for capturing observation and action data to build datasets.
    - Task Management: `reset_task()` and `reset_sub_task()` to handle language instructions and task progression.
    - Status Monitoring: Properties like `thread_status`, `runtime_status`, and `server_status` to monitor the real-time state of the system.

    Example:
        >>> config = load_config("config.yaml")
        >>> robot = MyRobot()
        >>> client = VLAClient(
        ...     config=config,
        ...     realtime_data_manager=rdm,
        ...     inter_chunk_fuser=fuser,
        ...     intra_chunk_smoother=smoother,
        ...     task_language_manager=task_mgr,
        ...     vla_zmq_client=zmq_client,
        ...     robot=robot
        ... )
        >>> client.start()
        >>> client.start_recording()
        >>> # ... perform robot tasks ...
        >>> client.stop_recording()
        >>> client.close()

    Args:
        config (ConfigDict): Configuration dictionary containing all system parameters.
        realtime_data_manager (RealtimeDataManager): Real-time data manager for handling observation and action data.
        inter_chunk_fuser (InterChunkFuser): Inter-chunk fuser for blending consecutive action chunks smoothly.
        intra_chunk_smoother (IntraChunkSmoother): Intra-chunk smoother for action smoothing and fitting within a single chunk.
        task_language_manager (TaskLanguageManager): Manager for handling task language instructions and sub-task progression.
        vla_zmq_client (ZMQClient): ZMQ client for communication with the VLA inference server.
        robot (RobotBase): Robot interface for observation collection and action execution.

    Notes:
        - Threading: This class internally manages multiple threads (observation, inference, control, and visualization). Ensure thread-safe operations when accessing shared resources externally.
        - Resource Cleanup: It is crucial to call `close()` to properly stop all running threads, close ZMQ connections, and release system resources before the object is destroyed to prevent zombie threads and memory leaks.
        - Network Dependency: Real-time inference heavily depends on the connection quality with the VLA server. Network latency or timeouts may cause the control loop to drop frames or pause temporarily.
    """
    def __init__(self, config: ConfigDict,
                realtime_data_manager: RealtimeDataManager,
                inter_chunk_fuser: InterChunkFuser,
                intra_chunk_smoother: IntraChunkSmoother,
                task_language_manager: TaskLanguageManager,
                vla_zmq_client: ZMQClient,
                robot: RobotBase):
        """
        Initialize the controller/manager instance with required configurations and components.

        Args:
            config (ConfigDict): The main configuration dictionary for the system.
            realtime_data_manager (RealtimeDataManager): Manager for handling real-time data streams.
            inter_chunk_fuser (InterChunkFuser): Fuser for integrating data across different chunks.
            intra_chunk_smoother (IntraChunkSmoother): Smoother for processing data within a single chunk.
            task_language_manager (TaskLanguageManager): Manager for handling task-level language instructions.
            vla_zmq_client (ZMQClient): ZeroMQ client for Vision-Language-Action (VLA) model communication.
            robot (RobotBase): The base robot instance to be controlled.
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.realtime_data_manager = realtime_data_manager
        self.inter_chunk_fuser = inter_chunk_fuser
        self.intra_chunk_smoother = intra_chunk_smoother
        self.task_language_manager = task_language_manager
        self.vla_zmq = vla_zmq_client
        self.robot = robot
        self.intra_chunk_smoother.set_action_layout(action_layout=self.robot.config.action_layout)
        # Initialize the dataset writer with the provided recording configuration
        self.shared_memory_manager = SharedMemoryManager(ring_size=30)
        self.data_record_manager = DataRecordManager(record_config=self.config.record)
        # Create visualization WebSocket server for live image and trajectory updates
        self.visualize_server = VisualizeServer(visualize_config=self.config.visualize)
        self.is_running = False
        self.is_observe_thread_running = False
        self.is_inference_thread_running = False
        self.is_control_thread_running = False

        # Human teleoperation can override model actions while its input is fresh.
        self.action_arbiter = ActionArbiter(
            action_timeout_s=float(getattr(self.config.controller, 'teleop_timeout_s', 0.5)),
            policy_timeout_s=float(getattr(self.config.controller, 'policy_timeout_s', 0.5)),
        )
        self.action_transition_filter = ActionTransitionFilter(
            transition_steps=int(getattr(self.config.controller, 'action_transition_steps', 64)),
            max_delta_per_step=getattr(self.config.controller, 'action_transition_max_delta_per_step', None),
        )
        self.teleop_bridge = None
        self._teleop_bridge_running = False
        self._last_teleop_action_s = None
        self._last_valid_teleop_action = None
        self._teleop_outlier_reject_count = 0
        self._teleop_outlier_last_log_s = 0.0
        self._last_selected_source = None
        self._last_executed_action = None
        self._last_executed_action_lock = threading.Lock()
        self._action_select_last_debug_s = 0.0
        self._teleop_policy_handoff_active = False
        self._teleop_policy_handoff_waiting_for_policy = False
        self._teleop_policy_handoff_hold_action = None
        self._teleop_policy_handoff_started_s = None
        self._policy_generation = 0
        self._policy_generation_lock = threading.Lock()

        # A proxy starts its worker during robot creation. Until Observe is
        # requested, it must not consume Mock episodes in the background.
        self.stop_observe()
        # Define image preprocess function
        self.update_preprocess_func()

        self.observe_thread = threading.Thread(target=self._observe_thread_fun, daemon=True)
        self.process_observe_thread = threading.Thread(target=self._process_observe_thread_fun, daemon=True)
        self.inference_thread = threading.Thread(target=self._inference_thread_fun, daemon=True)
        self.control_thread_timer = MultiThreadTimer(self.config.controller.period, self._control_thread_fun)
        # self.visualize_thread_timer = MultiThreadTimer(self.config.controller.period, self._visualize_thread_fun)

        self.show_thread_lock = threading.Lock()
        self._inference_execution_lock = threading.Lock()
        self._control_execution_lock = threading.Lock()

        # Raw observation queue: no frame dropping in VLA client pipeline.
        self._raw_observe_queue = Queue(maxsize=2)
        self._raw_observe_shm_cache = {}

        # The data socket belongs to the inference thread alone. Other threads
        # ask for work through this queue instead of touching the socket, and
        # use _inference_parked to learn when the thread sits at a safe point.
        self._inference_commands = Queue()
        self._inference_parked = threading.Event()

        # Shared thread pool for image encoding (avoid per-frame pool creation overhead)
        self._img_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="img_enc")

        # Inference variables
        self.set_observe_period(speed=self.config.controller.speed)
        self._request_id = 0
        self.inference_error = None
        self.inference_error_count = 0

        # Information for monitoring current action and state (left arm 7 + right arm 7 + left gripper 1 + right gripper 1)
        self.image_process_time = 0.0
        self.current_prob_progress = 0.0
        # self.info_obs, self.info_act = {}, {}
        self.camera_shape_dict = None
        self.control_thread_timer.start()
        self.logger.info('VLAClient initialized.')

    @staticmethod
    def _config_get(config, key, default=None):
        if config is None:
            return default
        if isinstance(config, dict):
            return config.get(key, default)
        return getattr(config, key, default)

    def _teleop_bridge_config(self):
        """Return the grouped teleop config, if present."""
        return getattr(self.config, 'teleop', None)

    def _use_teleop_enabled(self) -> bool:
        """Return whether bridge-based human teleoperation is enabled.

        ``teleop.use_teleop`` is authoritative when present. The root-level
        ``use_teleop`` field is kept only for loading older configurations that
        predate the grouped teleop config.
        """
        teleop_cfg = self._teleop_bridge_config()
        if teleop_cfg is not None and self._config_get(teleop_cfg, 'use_teleop', None) is not None:
            return bool(self._config_get(teleop_cfg, 'use_teleop'))
        return bool(getattr(self.config, 'use_teleop', False))

    def set_teleop_enabled(self, enabled: bool):
        """Enable or disable the teleop bridge at runtime."""
        teleop_cfg = self._teleop_bridge_config()
        if teleop_cfg is not None:
            teleop_cfg.use_teleop = bool(enabled)
        self.config.use_teleop = bool(enabled)
        if bool(enabled) and self.is_running:
            self.start_teleop_bridge()
        else:
            self.stop_teleop_bridge()
            self.action_arbiter.clear()
            self.action_transition_filter.reset()
            self._reset_teleop_policy_handoff()
            self._last_selected_source = None

    def _resolve_teleop_device_config(self) -> bool:
        """Resolve the Quest3 YAML from the selected robot type when enabled."""
        teleop_cfg = self._teleop_bridge_config()
        device = str(self._config_get(teleop_cfg, 'control_device', '') or '').lower()
        if device != 'quest3':
            return True
        device_cfg = self._config_get(self._config_get(teleop_cfg, 'devices', None), 'quest3', None)
        if device_cfg is None:
            self.logger.warning("Quest3 teleop device config is missing; teleop bridge will not start.")
            return False
        # This is an internal, non-user-editable setting. Keep it forced on for
        # every bridge start so a persisted path can never override the mapping.
        device_cfg.auto_config_path = True
        robot_type = self._config_get(getattr(self.config, 'robots', None), 'type', '')
        if hasattr(robot_type, 'value'):
            robot_type = robot_type.value
        robot_type = str(robot_type or '').lower()
        mapping = self._config_get(device_cfg, 'config_path_by_robot', None) or {}
        config_path = self._config_get(mapping, robot_type, None)
        if not config_path:
            self.logger.warning(
                "No Quest3 teleop config mapped for robot type %r; teleop bridge will not start.",
                robot_type,
            )
            return False
        device_cfg.config_path = str(config_path)
        self.logger.info("Resolved Quest3 teleop config for robot type %s: %s", robot_type, config_path)
        return True

    def start_teleop_bridge(self):
        """Create and start the configured teleop bridge."""
        if not self._use_teleop_enabled():
            return
        if not self._resolve_teleop_device_config():
            return
        if self.teleop_bridge is None:
            action_dim = int(getattr(self.robot, 'action_dim', 0) or 16)
            self.teleop_bridge = create_teleop_bridge(
                self._teleop_bridge_config(),
                submit_action=self.submit_teleop_bridge_action,
                action_dim=action_dim,
                reset_handler=self.reset_robot,
                joint_state_provider=self.get_teleop_joint_state,
                joint_state_names=self._teleop_joint_state_names(),
            )
        self.teleop_bridge.start()
        self._teleop_bridge_running = True

    def stop_teleop_bridge(self):
        """Stop the bridge and clear fresh-human-action state."""
        if self.teleop_bridge is not None:
            self.teleop_bridge.stop()
        self._teleop_bridge_running = False
        self.action_arbiter.clear_source(ActionSource.TELEOP)
        self._last_teleop_action_s = None
        self._last_selected_source = None
        self._reset_teleop_policy_handoff()
        self._reset_teleop_outlier_guard()

    def restart_teleop_bridge(self):
        """Recreate the bridge after device/topic/joint-name config changes."""
        was_running = self._teleop_bridge_running
        self.stop_teleop_bridge()
        self.teleop_bridge = None
        self.action_arbiter.clear()
        self.action_transition_filter.reset()
        self._reset_teleop_policy_handoff()
        if was_running or (self.is_running and self._use_teleop_enabled()):
            self.start_teleop_bridge()

    def submit_teleop_bridge_action(self, action, timestamp=None):
        """Receive one teleop action from the bridge and submit it to arbitration."""
        if timestamp is None:
            timestamp = time.perf_counter()
        action_arr = self._validate_teleop_bridge_action(action)
        if action_arr is None:
            self._hold_teleop_after_rejected_action(timestamp)
            return
        self.action_arbiter.submit(ActionSource.TELEOP, action_arr, timestamp)
        self._last_valid_teleop_action = action_arr.copy()
        self._teleop_outlier_reject_count = 0
        self._last_teleop_action_s = time.perf_counter()

    def _validate_teleop_bridge_action(self, action) -> Optional[np.ndarray]:
        """Reject malformed or implausibly large teleop jumps before arbitration."""
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
        if not bool(getattr(self.config.controller, 'teleop_outlier_guard_enabled', True)):
            return action_arr

        baseline = self._teleop_outlier_baseline(action_arr.shape[0])
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
            max_arm_joint_delta = getattr(self.config.controller, 'teleop_outlier_max_arm_joint_delta', 0.5)
            if max_arm_joint_delta is not None and np.max(delta[:arm_count]) > float(max_arm_joint_delta):
                self._teleop_outlier_reject_count += 1
                self._log_teleop_outlier(
                    'arm joint jump %.4f exceeds %.4f; reject_count=%d'
                    % (float(np.max(delta[:arm_count])), float(max_arm_joint_delta), self._teleop_outlier_reject_count)
                )
                return None
            max_arm_norm_delta = getattr(self.config.controller, 'teleop_outlier_max_arm_norm_delta', 1.2)
            if max_arm_norm_delta is not None and np.linalg.norm(delta[:arm_count]) > float(max_arm_norm_delta):
                self._teleop_outlier_reject_count += 1
                self._log_teleop_outlier(
                    'arm norm jump %.4f exceeds %.4f; reject_count=%d'
                    % (float(np.linalg.norm(delta[:arm_count])), float(max_arm_norm_delta), self._teleop_outlier_reject_count)
                )
                return None
        if delta.shape[0] > 14:
            max_gripper_delta = getattr(self.config.controller, 'teleop_outlier_max_gripper_delta', 1.0)
            if max_gripper_delta is not None and np.max(delta[14:]) > float(max_gripper_delta):
                self._teleop_outlier_reject_count += 1
                self._log_teleop_outlier(
                    'gripper jump %.4f exceeds %.4f; reject_count=%d'
                    % (float(np.max(delta[14:])), float(max_gripper_delta), self._teleop_outlier_reject_count)
                )
                return None
        return action_arr

    def _teleop_outlier_baseline(self, action_dim: int) -> Optional[np.ndarray]:
        """Return the latest trusted teleop action, then the last robot command/state."""
        if self._last_valid_teleop_action is not None:
            return np.asarray(self._last_valid_teleop_action, dtype=float).copy()
        baseline = self._coerce_state_to_action_shape(self._get_last_executed_action(), action_dim)
        if baseline is not None:
            return baseline
        return self._coerce_state_to_action_shape(getattr(self.robot, 'current_state', None), action_dim)

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
        if action_dim == 16 and arr.shape[0] >= 21:
            action = np.zeros(action_dim, dtype=float)
            action[:14] = arr[:14]
            action[14] = arr[14]
            action[15] = arr[20]
            return action
        if arr.shape[0] >= action_dim:
            return arr[:action_dim].copy()
        return None

    def _hold_teleop_after_rejected_action(self, timestamp: float) -> None:
        """Keep teleop ownership alive with the last safe action after a rejected packet."""
        hold_action = self._last_valid_teleop_action
        if hold_action is None:
            hold_action = self._get_last_executed_action()
        if hold_action is None:
            hold_action = self._coerce_state_to_action_shape(
                getattr(self.robot, 'current_state', None),
                int(getattr(self.robot, 'action_dim', 0) or 16),
            )
        if hold_action is None:
            if self._teleop_outlier_reject_count >= int(getattr(
                self.config.controller, 'teleop_outlier_reanchor_after_rejects', 5
            )):
                self.action_arbiter.clear_source(ActionSource.TELEOP)
                self._last_teleop_action_s = None
            return
        hold_action = np.asarray(hold_action, dtype=float).copy()
        self.action_arbiter.submit(ActionSource.TELEOP, hold_action, timestamp)
        self._last_valid_teleop_action = hold_action
        self._last_teleop_action_s = time.perf_counter()

    def _reset_teleop_outlier_guard(self) -> None:
        self._last_valid_teleop_action = None
        self._teleop_outlier_reject_count = 0

    def _log_teleop_outlier(self, reason: str) -> None:
        now = time.perf_counter()
        interval_s = float(getattr(self.config.controller, 'teleop_outlier_log_interval_s', 1.0))
        if now - self._teleop_outlier_last_log_s < interval_s:
            return
        self._teleop_outlier_last_log_s = now
        self.logger.warning('Drop teleop outlier action: %s', reason)

    def get_teleop_joint_state(self):
        """Return command-biased robot state for Quest3 IK feedback."""
        state = getattr(self.robot, 'current_state', None)
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
        with self._last_executed_action_lock:
            return None if self._last_executed_action is None else self._last_executed_action.copy()

    def _set_last_executed_action(self, action) -> None:
        value = None if action is None else np.asarray(action, dtype=float).reshape(-1).copy()
        with self._last_executed_action_lock:
            self._last_executed_action = value

    def _teleop_joint_state_names(self):
        """Return joint names matching the state/action vector published to Quest3."""
        teleop_cfg = self._teleop_bridge_config()
        ros_cfg = self._config_get(teleop_cfg, 'ros2', None)
        configured_names = self._config_get(ros_cfg, 'joint_state_names', None)
        if configured_names:
            return [str(name) for name in configured_names]
        robot_type = self._config_get(getattr(self.config, 'robots', None), 'type', '')
        if hasattr(robot_type, 'value'):
            robot_type = robot_type.value
        # 'agibot_g1' is the current name of the legacy 'a2d' robot body.
        if str(robot_type) in ('a2d', 'agibot_g1'):
            return [
                *(f'left_arm_joint{i}' for i in range(1, 8)),
                *(f'right_arm_joint{i}' for i in range(1, 8)),
                'left_hand_joint1',
                'right_hand_joint1',
                'joint_head_yaw',
                'joint_head_pitch',
                'joint_lift_body',
                'joint_body_pitch',
            ]
        state = getattr(self.robot, 'current_state', None)
        state_dim = int(np.asarray(state).reshape(-1).shape[0]) if state is not None else int(getattr(self.robot, 'action_dim', 0) or 16)
        return [f'{robot_type or "robot"}_joint{i + 1}' for i in range(state_dim)]

    def is_teleop_human_active(self) -> bool:
        """Return whether fresh teleop input is currently controlling the robot."""
        if not self._teleop_bridge_running or self._last_teleop_action_s is None:
            return False
        timeout_s = float(getattr(self.config.controller, 'teleop_timeout_s', 0.5))
        return time.perf_counter() - self._last_teleop_action_s <= timeout_s

    @property
    def teleop_human_connected(self) -> bool:
        return bool(self._teleop_bridge_running)

    def _action_for_selected_source(self, selected: SelectedAction) -> np.ndarray:
        if selected.source == ActionSource.TELEOP:
            action = np.asarray(selected.action, dtype=float).copy()
            # Keep the transition filter seeded with the exact human command so a
            # later policy handoff starts from the robot's actual last command.
            self.action_transition_filter.reset(last_output=action)
            return action
        return self.action_transition_filter.filter(selected)

    def _reset_teleop_policy_handoff(self) -> None:
        """Clear teleop-to-policy handoff state."""
        self._teleop_policy_handoff_active = False
        self._teleop_policy_handoff_waiting_for_policy = False
        self._teleop_policy_handoff_hold_action = None
        self._teleop_policy_handoff_started_s = None

    def _current_policy_generation(self) -> int:
        with self._policy_generation_lock:
            return self._policy_generation

    def _invalidate_policy_generation(self) -> int:
        with self._policy_generation_lock:
            self._policy_generation += 1
            return self._policy_generation

    def _is_policy_generation_current(self, generation: int) -> bool:
        with self._policy_generation_lock:
            return generation == self._policy_generation

    def _start_teleop_policy_handoff(self, hold_action) -> bool:
        """Hold the final teleop action until a fresh policy chunk arrives.

        The policy generation is invalidated so inference replies that were
        already in flight when teleop ended cannot be applied. Existing policy
        chunks are cleared because their time base belongs to the pre-handoff
        state; the next fresh reply will be fused from the held human action.
        """
        if hold_action is None:
            return False
        self._teleop_policy_handoff_hold_action = np.asarray(hold_action, dtype=float).copy()
        self._teleop_policy_handoff_active = True
        self._teleop_policy_handoff_waiting_for_policy = True
        self._teleop_policy_handoff_started_s = time.perf_counter()
        self._invalidate_policy_generation()
        self.realtime_data_manager.clear_policy_actions()
        self.action_arbiter.clear_source(ActionSource.POLICY)
        self.action_transition_filter.reset(last_output=self._teleop_policy_handoff_hold_action)
        self._reset_teleop_outlier_guard()
        self.logger.info("Teleop exited; holding final teleop action until a fresh policy chunk is available.")
        return True

    def _select_teleop_policy_handoff_action(self, action_fitted, now: float):
        """Return the held teleop action while waiting for fresh policy output."""
        if not self._teleop_policy_handoff_active:
            return None, None, None
        hold_action = self._teleop_policy_handoff_hold_action
        if hold_action is None:
            self._reset_teleop_policy_handoff()
            return None, None, None
        return hold_action.copy(), ActionSource.HOLD, None

    def _teleop_policy_handoff_state_for_fusion(self, action_dim: int):
        """Return the held teleop action as the inter-chunk fusion anchor."""
        if not self._teleop_policy_handoff_active or self._teleop_policy_handoff_hold_action is None:
            return None, None, None
        currt_action = self._coerce_state_to_action_shape(
            self._teleop_policy_handoff_hold_action,
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
        self.action_transition_filter.reset(last_output=first_policy_action)
        self.action_arbiter.clear()
        self.action_arbiter.submit(ActionSource.POLICY, first_policy_action, time.perf_counter())
        self._last_selected_source = ActionSource.POLICY
        self._teleop_policy_handoff_waiting_for_policy = False
        self._reset_teleop_policy_handoff()

    def reset_robot(self, mode='default'):
        """Handle a reset request coming from the external teleop device."""
        self.action_arbiter.clear()
        self.action_transition_filter.reset()
        self._reset_teleop_policy_handoff()
        self._last_selected_source = None
        return self.robot.reset_robot(mode=mode)

    ######################### VLAClient APIs #########################
    def start_observe(self):
        """
        Starts the observation process by activating the observation thread.

        This method sets the running and observation thread flags to True, and starts the observation thread if it is not currently alive.

        Returns:
            None
        """
        start_observe = getattr(self.robot, 'start_observe', None)
        if callable(start_observe):
            start_observe()
        self.is_running = True
        self.is_observe_thread_running = True
        if not self.observe_thread.is_alive():
            self.observe_thread.start()
        if not self.process_observe_thread.is_alive():
            self.process_observe_thread.start()
        self.logger.info('VLAClient observe thread started.')

    def stop_observe(self):
        self.is_observe_thread_running = False
        stop_observe = getattr(self.robot, 'stop_observe', None)
        if callable(stop_observe):
            stop_observe()
        self.logger.info('VLAClient observe thread stopped.')

    def start_inference(self):
        self.is_running = True
        if not self.inference_thread.is_alive():
            # A terminated Python Thread cannot be started a second time.
            if self.inference_thread.ident is not None:
                self.inference_thread = threading.Thread(target=self._inference_thread_fun, daemon=True)
            self.is_inference_thread_running = True
            try:
                self.inference_thread.start()
            except Exception:
                self.is_inference_thread_running = False
                raise
        else:
            self.is_inference_thread_running = True
        self.logger.info('VLAClient inference thread started.')

    def stop_inference(self):
        self.is_inference_thread_running = False
        self.realtime_data_manager.interrupt_wait_for_next()
        self.logger.info('VLAClient inference thread stopped.')

    def start_control(self):
        self.is_running = True
        with self._control_execution_lock:
            resume_controls = getattr(self.robot, 'resume_controls', None)
            if resume_controls is not None:
                resume_controls()
            self.is_control_thread_running = True
        if not self.control_thread_timer.is_alive():
            self.control_thread_timer.start()
        # start new task in task_language manager for auto mode
        self.task_language_manager.new_task()

    def stop_control(self):
        with self._control_execution_lock:
            self.is_control_thread_running = False
            pause_controls = getattr(self.robot, 'pause_controls', None)
            if pause_controls is not None:
                pause_controls()
            else:
                clear_control_actions = getattr(self.robot, 'clear_control_actions', None)
                if clear_control_actions is not None:
                    clear_control_actions()
        self.realtime_data_manager.interrupt_wait_for_next()
    
    def set_control_period(self, period) -> None:
        self.control_thread_timer.set_interval(period)
        # self.visualize_thread_timer.set_interval(period)
    
    def set_observe_period(self, speed) -> None:
        self.observe_period = 1.0 / speed / self.config.controller.raw_fps
        # print(f"Debug: control speed = {speed}")
    
    def _stop_control_thread_on_error(self):
        self.stop_control()
        if self.control_thread_timer.is_alive():
            self.control_thread_timer.stop(timeout=1.0)

    def start_visualize(self):
        self.visualize_server.start_server()
        # if not self.visualize_thread_timer.is_alive():
        #     self.visualize_thread_timer.start()
    def stop_visualize(self):
        self.visualize_server.stop_server()
        # if self.visualize_thread_timer.is_alive():
        #     self.visualize_thread_timer.stop(timeout=1.0)

    def start(self):
        """Start the VLA client and all associated threads.

        This method initializes and starts the observation, control, and inference
        threads for real-time robot operation. It uses thread locks to ensure
        thread-safe startup and begins the main control loop.
        """
        self.is_running = True

        self.start_observe()
        self.start_inference()
        self.start_teleop_bridge()
        self.start_control()
        self.start_visualize()

        self.logger.info('VLA client started.')

    def pause(self):
        """Pause observation, inference and control without releasing resources."""
        self.stop_teleop_bridge()
        self.stop_observe()
        self.stop_inference()
        self.stop_control()
        self.stop_visualize()
        self.logger.info('VLA client paused.')

    def resume(self):
        """Resume observation, inference and control."""
        if self.is_observe_thread_running and self.is_inference_thread_running and self.is_control_thread_running:
            return
        # self._inference_first()
        self.start_observe()
        self.start_inference()
        self.start_teleop_bridge()
        self.start_control()
        self.start_visualize()
        self.logger.info('VLA client resumed.')

    def request_inference_first(self, timeout: float = 3.0) -> bool:
        """Ask the inference thread to run a warm-up inference.

        Other threads must not call ``_inference_first`` directly: the ZMQ data
        socket belongs to the inference thread. The request is queued instead,
        and this returns True once that thread has finished it.

        Args:
            timeout (float): Seconds to wait for the acknowledgement.

        Returns:
            bool: True if the warm-up completed, False if it timed out or the
                inference thread is not running.
        """
        if not self.is_running or not self.inference_thread.is_alive():
            self.logger.warning('Inference thread is not running; warm-up skipped.')
            return False
        done = threading.Event()
        self._inference_commands.put(('inference_first', done))
        if not done.wait(timeout):
            self.logger.warning(f'Warm-up inference did not complete within {timeout}s.')
            return False
        return True

    def wait_inference_parked(self, timeout: float = 3.0) -> bool:
        """Block until the inference thread sits at a safe point.

        Used by shutdown and by interactive commands that need to know the
        inference thread is not in the middle of a request.

        Returns:
            bool: True if the thread is parked (or already finished).
        """
        if not self.inference_thread.is_alive():
            return True
        return self._inference_parked.wait(timeout)

    def stop(self):
        self.stop_teleop_bridge()
        self.stop_observe()
        self.stop_inference()
        self.stop_control()
        self.stop_visualize()
        # The inference thread owns the ZMQ socket. Wait until it is parked,
        # then take the execution lock so an in-flight step cannot race the clear.
        if not self.wait_inference_parked(timeout=1.0):
            self.logger.warning('Inference thread did not park before stop(); state is cleared anyway.')
        with self._inference_execution_lock:
            self.image_process_time = 0.0
            self.task_language_manager.reset()
            self.action_arbiter.clear()
            self.action_transition_filter.reset()
            self._last_selected_source = None
            self._set_last_executed_action(None)
            self.realtime_data_manager.clear()
            self._clear_raw_observe_queue()
        with self.show_thread_lock:
            self.current_prob_progress = 0.0
        self.logger.info('VLA client stopped.')
        # TODO: Robot reset

    def start_recording(self) -> str:
        # self._update_camera_shape()
        self.config.record.switch = True
        while self.camera_shape_dict is None:
            time.sleep(0.01)
        task_dir = self.data_record_manager.start_recording(task_id=self.config.language.task_id, 
                                                        sub_task_id=self.config.language.sub_task_id,
                                                        camera_shape=self.camera_shape_dict)
        return task_dir

    def stop_recording(self):
        self.config.record.switch = False
        self.data_record_manager.stop_recording()

    def pause_recording(self):
        if self.config.record.switch:
            self.data_record_manager.pause_recording()

    def resume_recording(self):
        if self.config.record.switch:
            self.data_record_manager.resume_recording()
    
    def reset_sub_task(self):
        self.task_language_manager.reset_sub_task()

    def reset_task(self):
        self.task_language_manager.new_task()

    def delete_recording_item(self, episode_id: Optional[str] = None, record_id: Optional[int] = None):
        if episode_id is not None:
            return self.data_record_manager.lerobot_recorder.delete_episode(episode_id=episode_id)
        if record_id is not None:
            return self.data_record_manager.eval_recorder.delete_record(record_id=record_id)

    def close(self):
        """Close the VLA client and clean up all resources.
        
        This method performs a complete shutdown of the VLA client by:
        - Stopping all running threads with timeouts
        - Closing dataset recording if enabled
        - Closing ZMQ client connections
        - Stopping visualization components
        - Cleaning up all allocated resources
        """
        self.stop_teleop_bridge()
        self.is_observe_thread_running = False
        self.is_inference_thread_running = False
        self.is_control_thread_running = False
        self.is_running = False
        
        if self.observe_thread.is_alive():
            self.observe_thread.join(timeout=1.0)
        if self.process_observe_thread.is_alive():
            self.process_observe_thread.join(timeout=1.0)
        if self.inference_thread.is_alive():
            # Must outlast the worst case single round: _inference_first waits
            # up to infer_timeout * 4, plus the bounded wait_for_next. The
            # inference thread releases the data socket on its way out, so this
            # join is what makes the later vla_zmq.close() safe.
            infer_join_timeout = self.config.vla_zmq.infer_timeout * 4 / 1000 + 1.0
            self.inference_thread.join(timeout=infer_join_timeout)
            if self.inference_thread.is_alive():
                self.logger.warning(
                    f'Inference thread still alive after {infer_join_timeout}s; '
                    f'its ZMQ socket will not be closed from this thread.')

        # Stop and join timer threads
        if self.control_thread_timer.is_alive():
            self.control_thread_timer.stop(timeout=1.0)
        # if self.visualize_thread_timer.is_alive():
        #     self.visualize_thread_timer.stop(timeout=1.0)
        
        self._clear_raw_observe_queue()
        SharedMemoryManager.close_reader(self._raw_observe_shm_cache)
        self._img_executor.shutdown(wait=False)

        self.data_record_manager.close()
        self.shared_memory_manager.close()
        self.vla_zmq.close()
        self.robot.close()
        self.visualize_server.stop_server()

        self.logger.info('VLA client closed.')

    def reset(self):
        # Prevent an in-flight inference from publishing stale actions or timing
        # measurements after Reset clears the data manager.
        with self._inference_execution_lock:
            self.realtime_data_manager.clear()
            self._clear_raw_observe_queue()
            self.image_process_time = 0.0

    @property
    def thread_status(self):
        return {
            "observe_running": self.is_observe_thread_running,
            "inference_running": self.is_inference_thread_running and self.inference_thread.is_alive(),
            "inference_thread_alive": self.inference_thread.is_alive(),
            "control_running": self.is_control_thread_running,
        }

    @property
    def runtime_status(self):
        status = {
            "img_proc_time": self.image_process_time,
            "current_prob_progress": self.current_prob_progress,
            "teleop_enabled": self._use_teleop_enabled(),
            "teleop_human_connected": self.teleop_human_connected,
            "teleop_human_active": self.is_teleop_human_active(),
            "last_selected_source": self._last_selected_source.value if self._last_selected_source is not None else None,
            "teleop_policy_handoff_active": self._teleop_policy_handoff_active,
            "inference_error": self.inference_error,
            "inference_error_count": self.inference_error_count,
        }
        status.update(self.realtime_data_manager.runtime_status)
        return status

    @property
    def language_status(self):
        return self.task_language_manager.status
    
    @property
    def server_status(self):
        return self.vla_zmq.status

    ####################========== VLA Client Inline functions ==========####################

    # def _update_camera_shape(self) -> dict:
    #     """Pop one observation from RDM and update recorder camera shapes by runtime image size."""
    #     if not hasattr(self, "data_record_manager") or self.data_record_manager is None:
    #         self.logger.warning("data_record_manager is not initialized, skip update_camera_shape.")
    #         return {}

    #     # print(f"Debug: camera_shape_dict: {camera_shape_dict}")
    #     self.data_record_manager.update_camera_shape_dict(self.camera_shape_dict)
    #     self.logger.info(f"Update camera shape from runtime observation: {self.camera_shape_dict}")
    #     return self.camera_shape_dict

    def _clear_raw_observe_queue(self):
        while True:
            try:
                self._raw_observe_queue.get_nowait()
                self._raw_observe_queue.task_done()
            except Empty:
                break

    def _observe_thread_fun(self):
        """Observation producer thread.

        This thread only retrieves observations from robot and enqueues them,
        so retrieval cadence is not blocked by image processing/encoding cost.
        """
        retrieve_try_num = 1.0
        while self.is_running:
            if not self.is_observe_thread_running:
                time.sleep(0.1)
                continue
            else:
                time.sleep(0.01/retrieve_try_num)
                retrieve_try_num = retrieve_try_num + 1.0

            observations = self.robot.retrieve_observation()
            if observations is not None:
                if self.camera_shape_dict is None:
                    cam_items = [(key, value) for key, value in observations.items() if 'cam.' in key]
                    if cam_items:
                        self.camera_shape_dict = {key: img.shape for key, img in cam_items}
                        camera_dtype_dict = {key: img.dtype for key, img in cam_items}
                        self.shared_memory_manager.init_pool(
                            self.camera_shape_dict,
                            camera_dtypes=camera_dtype_dict,
                        )
                encoded_observations = self.shared_memory_manager.encode_observation(observations)
                try:
                    self._raw_observe_queue.put_nowait(encoded_observations)
                except Full:
                    try:
                        self._raw_observe_queue.get_nowait()
                        self._raw_observe_queue.task_done()
                    except Empty:
                        pass
                    self._raw_observe_queue.put_nowait(encoded_observations)
                retrieve_try_num = 1.0

    def _process_observe_thread_fun(self):
        """Observation consumer thread.

        This thread processes raw observations and pushes processed data to RDM/recorder.
        No frame dropping is applied in this queue pipeline.
        """
        while self.is_running:
            if not self.is_observe_thread_running:
                time.sleep(0.001)
                continue
            try:
                observations = self._raw_observe_queue.get(timeout=0.01)
            except Empty:
                continue

            try:
                decoded_observations = SharedMemoryManager.decode_observation(observations, self._raw_observe_shm_cache)
                if decoded_observations is None:
                    continue
                infer_data, encoded_imgs = self._process_data(decoded_observations)
                if not self.realtime_data_manager.add_observe_data(
                    infer_data,
                    source_time=decoded_observations.get('_worker_publish_time'),
                ):
                    continue
                self.visualize_server.update_image_data(encoded_imgs)
                # record_data = self.shared_memory_manager.encode_observation(record_data)

                if self.config.record.switch:
                    packet_descriptors = observations.to_observation_descriptors()
                    record_data = {
                        **infer_data,
                        'obs': {
                            **{
                                camera_name: payload
                                for camera_name, payload in packet_descriptors.items()
                                if str(camera_name).startswith('cam.')
                            },
                            'state': infer_data['obs']['state'],
                            'language': infer_data['obs']['language'],
                        },
                    }
                    runtime_config = {
                        'mode': self.config.rdm.mode,
                        'wait_time': self.config.controller.wait_time,
                        'control_period': self.config.controller.period,
                        'control_speed': self.config.controller.speed,
                        'inter_chunk_mode': self.config.inter_chunk.inter_chunk_mode,
                        'intra_chunk_mode': self.config.intra_chunk.intra_chunk_mode,
                    }
                    extra_info = {
                        'runtime_status': self.runtime_status,
                        'language_status': self.language_status,
                        'server_status': self.server_status,
                        'runtime_config': runtime_config
                    }
                    self.data_record_manager.add_observation_async(
                        observation=record_data,
                        extra_info=extra_info,
                        timestamp=time.perf_counter())
            finally:
                self._raw_observe_queue.task_done()
    
    def _inference_thread_fun(self):
        """Inference loop. This thread is the sole owner of the ZMQ data socket.

        It claims the socket on first use and releases it on the way out, so no
        other thread ever creates, uses or closes it.
        """
        consecutive_errors = 0
        try:
            while self.is_running:
                # Commands are served even while parked: that is how other
                # threads get inference work done without touching the socket.
                if not self.is_inference_thread_running:
                    self._inference_parked.set()
                    with self._inference_execution_lock:
                        self._drain_inference_commands()
                    time.sleep(0.001)
                    continue

                self._inference_parked.clear()
                try:
                    with self._inference_execution_lock:
                        self._drain_inference_commands()
                        if not self.is_inference_thread_running:
                            continue
                        if self.realtime_data_manager.infer_count == 0:
                            self._inference_first()
                        else:
                            self._inference_step()

                    consecutive_errors = 0
                    self.inference_error = None
                    if self.is_inference_thread_running:
                        self.realtime_data_manager.wait_for_next(
                            mode=self.config.rdm.mode if self.is_control_thread_running else 'async',
                            wait_time=self.config.controller.wait_time / 1000,
                        )
                except Exception as exc:
                    consecutive_errors += 1
                    self.inference_error_count += 1
                    self.inference_error = f'{type(exc).__name__}: {exc}'
                    self.logger.exception('Inference step failed; clearing stale actions and retrying')
                    self.stop_control()
                    with self._inference_execution_lock:
                        self.realtime_data_manager.clear()
                    time.sleep(min(0.1 * 2 ** min(consecutive_errors - 1, 4), 1.6))
        finally:
            self._inference_parked.set()
            try:
                self.vla_zmq.release_data_socket()
            except Exception as exc:
                self.logger.error(f'Failed to release the data socket: {exc}')

    def _drain_inference_commands(self):
        """Execute queued requests from other threads, then acknowledge them."""
        while True:
            try:
                name, done = self._inference_commands.get_nowait()
            except Empty:
                return
            try:
                if name == 'inference_first':
                    self._inference_first()
                else:
                    self.logger.warning(f'Unknown inference command ignored: {name}')
            except Exception as exc:
                self.logger.error(f'Inference command {name} failed: {exc}')
            finally:
                done.set()

    def _control_thread_fun(self):
        if not self.is_control_thread_running:
            if self.visualize_server.vis_global_step % 5 == 0:
                current_state = getattr(self.robot, 'current_state', None) if self.is_observe_thread_running else None
                action_fitted, action_raw, vel_fitted, acc_fitted = self.realtime_data_manager.get_action_fitted(mode='visualize') if self.is_inference_thread_running else (None, None, None, None)
                self.visualize_server.update_chart_data(
                    action_fitted=action_fitted,
                    vel_fitted=vel_fitted,
                    acc_fitted=acc_fitted,
                    action_raw=action_raw,
                    current_state=current_state,
                    observe_period=self.observe_period / 1000,
                    control_period=self.config.controller.period / 1000
                    )
            else:
                self.visualize_server.vis_global_step += 1
            return

        teleop_enabled = self._use_teleop_enabled()
        # Values shared with the visualization helper below.
        action_fitted, action_raw, vel_fitted, acc_fitted = (None, None, None, None)
        selected_source = ActionSource.POLICY
        action_to_execute = None
        policy_action_for_record = None
        action_np = None

        def update_visualization(action_override=None):
            current_state = getattr(self.robot, 'current_state', None)
            self.visualize_server.update_chart_data(
                action_fitted=action_override if action_override is not None else action_fitted,
                vel_fitted=vel_fitted,
                acc_fitted=acc_fitted,
                action_raw=action_raw,
                current_state=current_state,
                observe_period=self.observe_period / 1000,
                control_period=self.config.controller.period / 1000
                )

        try:
            # Serialize action retrieval and submission with stop/start. A timer
            # callback from before Pause cannot submit an old action after Reset
            # or after controls are re-enabled on Resume.
            with self._control_execution_lock:
                if not self.is_control_thread_running:
                    return

                # Do not advance the policy chunk index while handoff is holding
                # the last human action. get_action_fitted() pre-increments the
                # index, so calling it here would make the first post-handoff
                # control tick skip a frame.
                if not (teleop_enabled and self._teleop_policy_handoff_active):
                    action_fitted, action_raw, vel_fitted, acc_fitted = self.realtime_data_manager.get_action_fitted()

                action_to_execute = action_fitted
                policy_action_for_record = action_fitted

                if teleop_enabled:
                    now = time.perf_counter()
                    handled_handoff = False
                    if self._teleop_policy_handoff_active:
                        new_teleop_after_handoff = (
                            self._last_teleop_action_s is not None
                            and self._teleop_policy_handoff_started_s is not None
                            and self._last_teleop_action_s > self._teleop_policy_handoff_started_s
                        )
                        if new_teleop_after_handoff:
                            self.logger.info("Fresh teleop input interrupted teleop-to-policy handoff.")
                            self._reset_teleop_policy_handoff()
                        else:
                            action_to_execute, selected_source, policy_action_for_record = self._select_teleop_policy_handoff_action(
                                action_fitted,
                                now,
                            )
                            if action_to_execute is None:
                                update_visualization()
                                return
                            self._last_selected_source = selected_source
                            handled_handoff = True
                    elif action_fitted is not None:
                        self.action_arbiter.submit(ActionSource.POLICY, action_fitted, now)

                    if not handled_handoff and not self._teleop_policy_handoff_active:
                        selected = self.action_arbiter.select(now=now)
                        if selected is None:
                            update_visualization()
                            return
                        if (
                            self._last_selected_source == ActionSource.TELEOP
                            and selected.source != ActionSource.TELEOP
                        ):
                            last_executed_action = self._get_last_executed_action()
                            hold_action = last_executed_action if last_executed_action is not None else selected.action
                            if self._start_teleop_policy_handoff(hold_action):
                                action_to_execute, selected_source, policy_action_for_record = self._select_teleop_policy_handoff_action(
                                    None,
                                    now,
                                )
                                if action_to_execute is None:
                                    update_visualization()
                                    return
                            else:
                                action_to_execute = self._action_for_selected_source(selected)
                                selected_source = selected.source
                                policy_action_for_record = action_fitted
                        else:
                            action_to_execute = self._action_for_selected_source(selected)
                            selected_source = selected.source
                            policy_action_for_record = action_fitted
                        self._last_selected_source = selected_source
                        if now - self._action_select_last_debug_s >= 1.0:
                            self._action_select_last_debug_s = now
                            self.logger.debug("Action arbiter selected source=%s", selected_source.value)

                if action_to_execute is not None:
                    action_np = np.asarray(action_to_execute)
                    # Teleop/hold commands keep their open-loop semantics: the
                    # robot proxy control queue is non-blocking and latest-wins,
                    # so the control timer never waits on the robot worker.
                    self.robot.control_robot(action_np)
                    self._set_last_executed_action(action_np)
                    if (
                        self._teleop_bridge_running
                        and self.teleop_bridge is not None
                        and not self.is_teleop_human_active()
                    ):
                        try:
                            self.teleop_bridge.publish_joint_state()
                        except Exception:
                            self.logger.warning("Failed to publish teleop anchor state", exc_info=True)

                    # Data recording remains unchanged: the existing recorder
                    # continues to receive the policy action exactly as before
                    # this handoff change.
                    if self.config.record.switch and action_fitted is not None:
                        self.data_record_manager.add_action_async(action_fitted, time.perf_counter())
        except Exception as exc:
            self._stop_control_thread_on_error()
            self.logger.error("Robot control failed: %s", exc)
            raise

        # Only use alignment processing if prob_progress array length > 1
        prob_progress = self.realtime_data_manager.get_prob_progress()
        if prob_progress is not None:
            with self.show_thread_lock:
                self.current_prob_progress = prob_progress
            if self.config.language.auto_mode == True:
                self.task_language_manager.add_task_progress(progress=prob_progress)
                self.task_language_manager.try_advance_subtask()

        update_visualization(action_np if action_np is not None else action_fitted)

    # def _visualize_thread_fun(self):
    #     # Send state data to visualization server for live plotting when control thread is not running
    #     if not self.is_control_thread_running:
    #         current_state = getattr(self.robot, 'current_state', None) if self.is_observe_thread_running else None
    #         action_fitted, action_raw, vel_fitted, acc_fitted = self.realtime_data_manager.get_action_fitted(mode='visualize') if self.is_inference_thread_running else (None, None, None, None)
    #         self.visualize_server.update_chart_data(
    #             action_fitted=action_fitted,
    #             vel_fitted=vel_fitted,
    #             acc_fitted=acc_fitted,
    #             action_raw=action_raw,
    #             current_state=current_state,
    #             observe_period=self.observe_period / 1000,
    #             control_period=self.config.controller.period / 1000
    #             )
    @run_time_decorator
    def _inference_first(self):
        """First inference step, which initializes the control pipeline.
        
        This method performs the initial inference that sets up the control system:
        - Waits for robot stabilization after reset
        - Retrieves fresh observation data
        - Performs VLA inference to get action predictions
        - Initializes trajectory fitting and control timestamps
        - Sets up the fitted action chunk for control
        """
        # Wait for observation changes after reset, then retrieve fresh obs for inference
        # observations, cnt = None, 0
        # while observations is None or cnt < 3:
        #     # time.sleep(0.2)
        #     self.realtime_data_manager.clear()
        #     observations = self.robot.retrieve_observation()
        #     cnt += 1

        # if observations is not None:
        #     self.realtime_data_manager.clear()
        #     data = self._process_data(observations)
        #     self.realtime_data_manager.add_observe_data(data)
            # Clear action data to ensure fresh action retrieval
        
        # Get observation data (thread-safe function, no lock needed)
        data = self.realtime_data_manager.pop_observe_data(num_samples = 1 if not self.config.vision.history_frame else 2)
        if data is not None:
            policy_generation = self._current_policy_generation()
            # Record inference start timestamp for control timestamp updates
            self.realtime_data_manager.set_infer_time_marker()
            
            # Send data for inference and wait for results
            result = self._request_inference(data, timeout_ms=self.config.vla_zmq.infer_timeout * 4)
            if result is None or 'data' not in result:
                # print("Debug: infer first timeout.")
                return
            if not self._is_policy_generation_current(policy_generation):
                self.logger.info("Drop stale first inference result after teleop-to-policy handoff.")
                return
            # Record trajectory fitting timestamp
            avg_infer_time = result.get('meta', {}).get('avg_infer_time', 0.0)
            self.realtime_data_manager.set_intra_traj_time_marker()
            self.realtime_data_manager.add_infer_count()

            action_data = result['data']
            
            # Get current data timestamp and update timestamps
            action_chunk, timestamp_chunk, loc_timestamp = self._process_action_chunk(action_data)
            self.realtime_data_manager.set_observe_time_marker(loc_timestamp)
            
            # Add action data (thread-safe function, no lock needed)
            self.realtime_data_manager.set_init_observe_timestamp(timestamp=timestamp_chunk[0])
            self.realtime_data_manager.update_action_chunk_raw(action_chunk, timestamp_chunk)

            timestamps, action_chunk = self.realtime_data_manager.pop_action_chunk(time_offset=0.0)
            prob_progress = self._parse_prob_progress(action_data)
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted, task_progress_fitted = self.intra_chunk_smoother.process(
                timestamps,
                action_chunk,
                time_step=self.config.controller.period,
                task_progress=prob_progress,
                joint_indices=self.robot.get_joint_indices(),
                step_indices=self.robot.get_step_indices())

            self.realtime_data_manager.set_inter_traj_time_marker()
            target_chunk_index = self.realtime_data_manager.get_start_chunk_index(timestamps_fitted)
            # During handoff, blend from the exact held human action over the
            # full fresh policy horizon instead of starting at the time-shifted
            # index computed from a now-stale policy timeline.
            currt_action, currt_vel, currt_acc = self._teleop_policy_handoff_state_for_fusion(action_chunk_fitted.shape[0])
            if currt_action is not None:
                target_chunk_index = 0
            action_chunk_smoothed, vel_chunk_smoothed, acc_chunk_smoothed, target_chunk_index = self.inter_chunk_fuser.process(
                next_action_chunk=action_chunk_fitted,
                next_vel_chunk=vel_chunk_fitted,
                next_acc_chunk=acc_chunk_fitted,
                next_timestamps=timestamps_fitted,
                target_chunk_index=target_chunk_index,
                currt_action=currt_action,
                currt_vel=currt_vel,
                currt_acc=currt_acc,
                joint_indices=None,
                step_indices=None,
            )
            # Record control timestamp
            self.realtime_data_manager.set_control_time_marker()
            self.realtime_data_manager.update_action_chunk_fitted(
                action_chunk_smoothed=action_chunk_smoothed,
                vel_chunk_smoothed=vel_chunk_smoothed,
                acc_chunk_smoothed=acc_chunk_smoothed,
                timestamps_smoothed=timestamps_fitted,
                target_chunk_index=target_chunk_index,
                prob_progress=task_progress_fitted,
                step_indices=self.robot.get_step_indices(),
                gripper_offset=self.config.controller.gripper_offset,
                next_action_chunk_index=max(0, target_chunk_index - 1) if currt_action is not None else None,
            )
            if currt_action is not None:
                self._complete_teleop_policy_handoff(action_chunk_smoothed, target_chunk_index)

            # Compute average inference and trajectory fitting times
            self.realtime_data_manager.compute_avg_comm_infer_time()
            self.realtime_data_manager.compute_avg_intra_traj_time()
            self.realtime_data_manager.compute_avg_inter_traj_time()
            self.realtime_data_manager.compute_avg_comm_time(avg_infer_time=avg_infer_time)
    
    # @run_time_decorator
    def _inference_step(self):
        """Regular inference step for continuous VLA inference.
        
        This method performs regular inference steps after the first inference:
        - Retrieves observation data from the data manager
        - Sends data to VLA server for inference
        - Processes the returned action predictions
        - Updates trajectory fitting with smoothing and search options
        - Computes timing statistics
        """
        if not self.is_inference_thread_running:
            return
        
        # Get observation data (thread-safe function, no lock needed)
        data = self.realtime_data_manager.pop_observe_data(num_samples = 1 if not self.config.vision.history_frame else 2)
        if isinstance(data, dict):
            currt_language_instruction = data.get("obs", {}).get("language")[0]
        elif isinstance(data, list):
            currt_language_instruction = data[1].get("obs", {}).get("language")[0]
        else:
            currt_language_instruction = ''
        # print(f"data keys: {data.keys() if data is not None else None}, infer_count: {self.realtime_data_manager.infer_count}")
        if data is not None:
            policy_generation = self._current_policy_generation()
            # Record inference start timestamp
            self.realtime_data_manager.set_infer_time_marker()
            
            # Send data for inference and wait for results
            result = self._request_inference(data, timeout_ms = self.config.vla_zmq.infer_timeout)
            if result is None:
                self.logger.warning("Inference result is None.")
                return
            if 'data' not in result:
                self.logger.warning("Inference result doesn't have data.")
                return
            if not self._is_policy_generation_current(policy_generation):
                self.logger.info("Drop stale inference result after teleop-to-policy handoff.")
                return

            avg_infer_time = result.get('meta', {}).get('avg_infer_time', 0.0)
            # Record trajectory fitting timestamp
            self.realtime_data_manager.set_intra_traj_time_marker()
            self.realtime_data_manager.add_infer_count()
            action_data = result['data']
            
            # Get current data timestamp and update timestamps
            action_chunk, timestamp_chunk, loc_timestamp = self._process_action_chunk(action_data)
            self.realtime_data_manager.set_observe_time_marker(loc_timestamp)
            
            # Add action data (thread-safe function, no lock needed)
            self.realtime_data_manager.update_action_chunk_raw(action_chunk, timestamp_chunk)


            timestamps, action_chunk = self.realtime_data_manager.pop_action_chunk(time_offset=0.0)
            if timestamps is None:
                self.logger.warning("Return None when pop action chunk from realtime_data_manager.")
                return
            prob_progress = self._parse_prob_progress(action_data)
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted, task_progress_fitted = self.intra_chunk_smoother.process(
                timestamps,
                action_chunk,
                time_step=self.config.controller.period,
                task_progress=prob_progress,
                joint_indices=self.robot.get_joint_indices(),
                step_indices=self.robot.get_step_indices())

            self.realtime_data_manager.set_inter_traj_time_marker()
            target_chunk_index = self.realtime_data_manager.get_start_chunk_index(timestamps_fitted)
            currt_action, currt_vel, currt_acc = self.realtime_data_manager.get_current_state()
            # A fresh policy chunk after teleoperation must be fused from the
            # last human command, not from a cleared/stale policy index. Start at
            # frame zero so the inter-chunk fuser has the full horizon available.
            handoff_action, handoff_vel, handoff_acc = self._teleop_policy_handoff_state_for_fusion(action_chunk_fitted.shape[0])
            handoff_fusion = handoff_action is not None
            if handoff_action is not None:
                currt_action, currt_vel, currt_acc = handoff_action, handoff_vel, handoff_acc
                target_chunk_index = 0
            # Use inter chunk fusion when control thread is running, otherwise use intra chunk smoother output directly for visualization and monitoring
            action_chunk_smoothed, vel_chunk_smoothed, acc_chunk_smoothed, target_chunk_index = self.inter_chunk_fuser.process(
                next_action_chunk=action_chunk_fitted,
                next_vel_chunk=vel_chunk_fitted,
                next_acc_chunk=acc_chunk_fitted,
                next_timestamps=timestamps_fitted,
                target_chunk_index=target_chunk_index,
                currt_action=currt_action if self.is_control_thread_running else None,
                currt_vel=currt_vel if self.is_control_thread_running else None,
                currt_acc=currt_acc if self.is_control_thread_running else None,
                # During handoff blend the full action vector from the human anchor.
                joint_indices=None if handoff_fusion else self.robot.get_joint_indices() if self.is_control_thread_running else None,
                step_indices=None if handoff_fusion else self.robot.get_step_indices() if self.is_control_thread_running else None,
            )
            # Record control timestamp
            self.realtime_data_manager.set_control_time_marker()
            self.realtime_data_manager.update_action_chunk_fitted(
                action_chunk_smoothed=action_chunk_smoothed,
                vel_chunk_smoothed=vel_chunk_smoothed,
                acc_chunk_smoothed=acc_chunk_smoothed,
                timestamps_smoothed=timestamps_fitted,
                target_chunk_index=target_chunk_index,
                prob_progress=task_progress_fitted,
                step_indices=self.robot.get_step_indices(),
                gripper_offset=self.config.controller.gripper_offset,
                # get_action_fitted() increments before indexing, so pin one
                # frame earlier to consume target_chunk_index first.
                next_action_chunk_index=max(0, target_chunk_index - 1) if handoff_fusion else None,
            )
            if handoff_fusion:
                self._complete_teleop_policy_handoff(action_chunk_smoothed, target_chunk_index)

            # Compute average inference and trajectory fitting times
            self.realtime_data_manager.compute_avg_comm_infer_time()
            self.realtime_data_manager.compute_avg_intra_traj_time()
            self.realtime_data_manager.compute_avg_inter_traj_time()
            self.realtime_data_manager.compute_avg_comm_time(avg_infer_time=avg_infer_time)
            if self.config.language.auto_mode == True:
                self.task_language_manager.confirm_advance_subtask(
                    language_instruction=currt_language_instruction,
                    task_progress_next=task_progress_fitted
                )
        else:
            self.logger.warning("No observe data, skip inference.")

    def _process_image_thread_fun(self, key, value):
        """Process image data for inference transport while preserving raw frame for recorder.

        Args:
            key (str): Image key identifier.
            value (np.ndarray): Raw image data from robot sensors.

        Returns:
            tuple: A tuple containing:
                - key (str): Original image key
                - img_raw (np.ndarray): Unmodified raw image from robot
                - img_encoded (np.ndarray): Encoded image data for network transmission
        """
        ext = '.png' if 'depth.' in key else '.jpg'
        img_for_infer = self._preprocess_func(value) if self._preprocess_func else value
        if 'depth.' not in key and getattr(img_for_infer, 'ndim', 0) == 3 and img_for_infer.shape[2] == 3:
            robot_config = self.config.robots[self.config.robots.type]
            color_order = str(robot_config.get('camera', {}).get('color_order', 'rgb')).lower()
            if color_order == 'rgb':
                # OpenCV encodes BGR; the viewer and inference share these JPEG bytes.
                img_for_infer = img_for_infer[:, :, ::-1]
            elif color_order != 'bgr':
                raise ValueError(f'Unsupported camera color_order: {color_order}')
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, 80] if ext == '.jpg' else []
        encode_result, img_encoded = cv2.imencode(ext, img_for_infer, encode_params)
        if not encode_result:
            self.logger.warning(f"Image encoding failed for {key}.")
        return key, memoryview(img_encoded) if encode_result else None

    def _process_image(self, frame):
        """Process multiple images and produce both encoded and raw outputs.

        Args:
            frame (dict): A dictionary containing observation data, including image data, proprioception state data.

        Returns:
            tuple[dict, dict]:
                - encoded images (for inference and visualization)
                - raw images from robot (for recording)
        """
        start_time = time.perf_counter()

        cam_items = [(key, value) for key, value in frame.items() if 'cam.' in key]

        encoded_imgs = {}
        # raw_imgs = {}
        if cam_items:
            results_iter = self._img_executor.map(
                lambda item: self._process_image_thread_fun(*item),
                cam_items
            )
            for key, encoded_img in results_iter:
                # raw_imgs[key] = raw_img
                if encoded_img is not None:
                    encoded_imgs[key] = encoded_img

        # if self.camera_shape_dict is None and raw_imgs:
        #     self.camera_shape_dict = {key: img.shape for key, img in raw_imgs.items()}
        #     self.shared_memory_manager.init_pool(self.camera_shape_dict)

        self.image_process_time = self.image_process_time * 0.8 + (time.perf_counter() - start_time) * 1000 * 0.2
        return encoded_imgs
    def _parse_prob_progress(self, action_data):
        prob_progress = None
        if 'ext' in action_data and 'prob_progress' in action_data['ext']:
            prob_progress = action_data['ext']['prob_progress']
            if np.isnan(prob_progress).any():
                prob_progress = None
                self.logger.warning("prob_progress contains nan values, return None")
        return prob_progress
    # @run_time_decorator
    # TODO: rename to pack_data
    def _process_data(self, frame):
        """Process observation data by adding local timestamp, encoding images and adding task name.

        Args:
            frame (dict): A dictionary containing observation data, including image data, proprioception state data.
            frame keys=dict_keys(['ref_timestamp', 'cam.hand_left', 'cam.hand_right', 'cam.head', 'obs.state', 'action'])

        Returns:
            dict: The processed data by encoding images and adding local timestamp.
        """
        loc_timestamp = time.perf_counter()
        encoded_imgs = self._process_image(frame)

        language = [self.task_language_manager.get_current_language()]
        obs_state = frame['obs.state']

        infer_data = {
            'type': 'vla_obs',
            'ref_timestamp': frame['ref_timestamp'],
            'loc_timestamp': loc_timestamp,
            'obs': {
                **encoded_imgs,
                'state': obs_state,
                'language': language,
            },
        }

        # record_data = {
        #     'type': 'vla_obs',
        #     'ref_timestamp': frame['ref_timestamp'],
        #     'loc_timestamp': loc_timestamp,
        #     'obs': {
        #         **raw_imgs,
        #         'state': obs_state,
        #         'language': language,
        #     },
        # }
        return infer_data, encoded_imgs

    # @run_time_decorator
    def _process_action_chunk(self, action_raw:dict):
        """Process an action chunk by generating reference timestamp chunk and passing local timestamp.

        This method processes the inference result from the VLA server by:
        - Extracting predicted actions and timestamps
        - Handling language instruction switching based on progress
        - Generating timestamp chunks for trajectory control
        - Validating action type and format

        Args:
            action (dict): The inference result from vla_server. It is a dictionary with keys, i.e.,  type, pred_action, ref_timestamp, loc_timestamps.

        Returns:
            tuple(list, list, int): A tuple containing:
                - action_chunk (list): The predicted action chunk
                - timestamp_chunk (list): Reference timestamp chunk
                - loc_timestamp (int): Local timestamp
        """
        action_chunk = []
        timestamp_chunk = []
        action_type = action_raw['type']
        
        if action_type == 'vla_action':
            pred_action = action_raw['pred_action']
            ref_timestamp = action_raw['ref_timestamp']
            loc_timestamp = action_raw['loc_timestamp']
            # Generate action and timestamp chunks
            for index, action in enumerate(pred_action):
                action_chunk.append(action)
                timestamp_chunk.append(self.observe_period * index)
            
            # Set first frame timestamp to observation reference timestamp
            timestamp_chunk[0] = ref_timestamp
            return action_chunk, timestamp_chunk, loc_timestamp
        else:
            self.logger.error(f'wrong action type: {action_type}')
            return None, None, None

    def _next_request_id(self):
        self._request_id += 1
        return f"{time.time_ns()}-{self._request_id}"

    def _request_inference(self, data, timeout_ms=500):
        # Observations may have been queued before a manual language switch.
        # Apply the current instruction when the inference request is sent.
        if not self.config.language.auto_mode:
            language = self.task_language_manager.get_current_language()
            frames = data if isinstance(data, list) else [data]
            for frame in frames:
                if isinstance(frame, dict) and isinstance(frame.get('obs'), dict):
                    frame['obs']['language'] = [language]
        request_id = self._next_request_id()
        # start_time = time.time()
        if not self.vla_zmq.sendMessage(data, meta={'request_id': request_id}):
            return None
        # end_time = time.time()
        # print(f"Debug: Net Time = {(end_time - start_time) * 1000} ms")

        deadline = time.perf_counter() + timeout_ms / 1000.0
        while True:
            remain_s = deadline - time.perf_counter()
            if remain_s <= 0:
                return None
            
            # start_time = time.time()
            msg = self.vla_zmq.recvMessage(timeout_ms=max(1, int(remain_s * 1000)))
            # end_time = time.time()
            # print(f"Debug: Infer Time = {(end_time - start_time) * 1000} ms")

            if msg is None:
                self.logger.error(f"Received None from server.")
                return None
            meta = msg.get('meta') or {}
            if meta.get('request_id') == request_id:
                return msg
            self.logger.warning(f"Drop stale response with unmatched request_id: {meta.get('request_id')}")
    def update_preprocess_func(self):
        """Update the preprocess function when vision.preprocess parameters change."""
        # print(f"Debug: vision.preprocess = {self.config.vision.preprocess}")
        if self.config.vision.preprocess.method != 'none':
            preprocess_func = getattr(misc, self.config.vision.preprocess.method)
            self._preprocess_func = lambda img: preprocess_func(
                img,
                target_height=self.config.vision.preprocess.height,
                target_width=self.config.vision.preprocess.width,
                keep_ratio=self.config.vision.preprocess.keep_ratio)
        else:
            self._preprocess_func = None

if __name__ == "__main__":
    pass
