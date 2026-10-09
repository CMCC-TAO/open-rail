import cv2
import os
import time
import logging
import threading
import numpy as np
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
from client.simulation.data_record_manager import DataRecordManager
from client.robots.base_robot import RobotBase, RobotStepResult


class VLAClientAsync():
    """VLA (Vision-Language-Action) Client for real-time robot control.

    This class manages the complete pipeline for VLA-based robot control, including:
    - Observation data collection from robot sensors
    - Communication with VLA inference server
    - Trajectory generation and fitting
    - Real-time robot control
    - Data recording for dataset creation
    """
    def __init__(self, config: ConfigDict,
                realtime_data_manager: RealtimeDataManager,
                inter_chunk_fuser: InterChunkFuser,
                intra_chunk_smoother: IntraChunkSmoother,
                task_language_manager: TaskLanguageManager,
                vla_zmq_client: ZMQClient,
                robot: RobotBase):
        """Initialize the VLA Client.

        Args:
            config (ConfigDict): Configuration dictionary containing all system parameters
            realtime_data_manager (RealtimeDataManager): Real-time data manager for handling observation and action data
            intra_chunk_smoother (IntraChunkSmoother): Intra-chunk smoother for action smoothing and fitting
            zmq_client (ZMQClient): ZMQ client for communication with VLA inference server
            vis_action_cams_zmq_client (ZMQClient): ZMQ client for communication with camera-action visualization server
            robot: Robot interface for observation collection and action execution
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.realtime_data_manager = realtime_data_manager
        self.inter_chunk_fuser = inter_chunk_fuser
        self.intra_chunk_smoother = intra_chunk_smoother
        self.task_language_manager = task_language_manager
        self.vla_zmq = vla_zmq_client
        self.robot = robot
        self.camera_preview = None
        preview_path = os.environ.get('VLA_SIM_PREVIEW_PATH')
        if preview_path and robot.config.get('preview_worker_index') in (None, 0):
            from client.simulation.preview import CameraPreview

            self.camera_preview = CameraPreview(preview_path, dict(robot.config.camera.names))
        self.intra_chunk_smoother.set_action_layout(robot.config.action_layout)
        self.is_running = False
        self.is_observe_thread_running = False
        self.is_inference_thread_running = False
        self.is_control_thread_running = False
        self.episode_done_event = threading.Event()
        self.last_step_result = None
        self.pipeline_error = None

        # Define image preprocess function
        self.update_preprocess_func()
        # if self.config.vision.preprocess.method != 'none':
        #     preprocess_func = getattr(misc, self.config.vision.preprocess.method)
        #     self._preprocess_func = lambda img: preprocess_func(
        #         img,
        #         target_height=self.config.vision.preprocess.height,
        #         target_width=self.config.vision.preprocess.width,
        #         keep_ratio=self.config.vision.preprocess.keep_ratio)
        # else:
        #     self._preprocess_func = None

        self.observe_thread = threading.Thread(target=self._observe_thread_fun, daemon=True)
        self.inference_thread = threading.Thread(target=self._inference_thread_fun, daemon=True)
        self.control_thread_timer = MultiThreadTimer(self.config.controller.period, self._control_thread_fun)
        self.visualize_thread_timer = MultiThreadTimer(self.config.controller.period, self._visualize_thread_fun)

        self.show_thread_lock = threading.Lock()

        # Shared thread pool for image encoding (avoid per-frame pool creation overhead)
        self._img_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="img_enc")

        # Inference variables
        self.set_observe_period(speed=self.config.controller.speed)
        self._request_id = 0
        self._step_meta_lock = threading.Lock()
        self._latest_observation_step = None
        self._latest_applied_action_step = None
        self._last_accepted_observation_step = None
        self._control_in_flight = False
        self._inference_in_flight = False
        self._episode_generation = 0
        self._inference_cycle_lock = threading.Lock()

        # Initialize the dataset writer with the provided recording configuration
        self.data_record_manager = DataRecordManager(record_config=self.config.record)

        # Create visualization WebSocket server for live image and trajectory updates
        self.config.visualize.auto_start = False
        self.visualize_server = VisualizeServer(visualize_config=self.config.visualize)

        # Information for monitoring current action and state (left arm 7 + right arm 7 + left gripper 1 + right gripper 1)
        self.image_process_time = 0.0
        self.current_prob_progress = 0.0
        # self.info_obs, self.info_act = {}, {}
        self.camera_shape_dict = None
        # self.debug_info = 'The debug information or trace information will be displayed here. \nPress "Enter" for more commands.'
    #################### VLA Client APIs ####################
    def start_observe(self):
        self.is_running = True
        self.is_observe_thread_running = True
        if not self.observe_thread.is_alive():
            self.observe_thread.start()

    def stop_observe(self):
        self.is_observe_thread_running = False

    def start_inference(self):
        self.is_running = True
        self.is_inference_thread_running = True
        if not self.inference_thread.is_alive():
            self.inference_thread.start()

    def stop_inference(self):
        self.is_inference_thread_running = False

    def start_control(self):
        self.is_running = True
        self.is_control_thread_running = True
        if not self.control_thread_timer.is_alive():
            self.control_thread_timer.start()

    def stop_control(self):
        self.is_control_thread_running = False

    def set_control_period(self, period) -> None:
        self.control_thread_timer.set_interval(period)
        self.visualize_thread_timer.set_interval(period)

    def set_observe_period(self, speed) -> None:
        self.observe_period = 1.0 / speed / self.config.controller.raw_fps
        # print(f"Debug: control speed = {speed}")

    def _stop_control_thread_on_error(self, exc=None):
        self.is_control_thread_running = False
        self.is_inference_thread_running = False
        if exc is not None:
            self.pipeline_error = exc
        self.realtime_data_manager.cancel_waiters()
        self.episode_done_event.set()
        if self.control_thread_timer.is_alive():
            self.control_thread_timer.stop(timeout=1.0)

    def update_camera_shape(self) -> dict:
        """Pop one observation from RDM and update recorder camera shapes by runtime image size."""
        if not hasattr(self, "data_record_manager") or self.data_record_manager is None:
            self.logger.warning("data_record_manager is not initialized, skip update_camera_shape.")
            return {}

        # print(f"Debug: camera_shape_dict: {camera_shape_dict}")
        self.data_record_manager.update_camera_shape_dict(self.camera_shape_dict)
        self.logger.info(f"Update camera shape from runtime observation: {self.camera_shape_dict}")
        return self.camera_shape_dict

    def start_visualize(self):
        self.visualize_server.start_server()
        if not self.visualize_thread_timer.is_alive():
            self.visualize_thread_timer.start()
    def stop_visualize(self):
        self.visualize_server.stop_server()
        if self.visualize_thread_timer.is_alive():
            self.visualize_thread_timer.stop(timeout=1.0)

    def start(self):
        """Start the VLA client and all associated threads.

        This method initializes and starts the observation, control, and inference
        threads for real-time robot operation. It uses thread locks to ensure
        thread-safe startup and begins the main control loop.
        """
        self.is_running = True

        self.start_observe()
        self.start_inference()
        self.start_control()
        self.start_visualize()

        self.logger.info('VLA client started.')

    def pause(self):
        """Pause observation, inference and control without releasing resources."""
        self.stop_observe()
        self.stop_inference()
        self.stop_control()
        self.realtime_data_manager.cancel_waiters()
        timeout = max(1.0, self.config.vla_zmq.infer_timeout * 4 / 1000.0 + 1.0)
        if not self.wait_for_inference_idle(timeout):
            raise TimeoutError('Timed out while waiting for the inference cycle to stop')
        self.stop_visualize()
        self.logger.info('VLA client paused.')

    def resume(self):
        """Resume observation, inference and control."""
        if self.is_observe_thread_running and self.is_inference_thread_running and self.is_control_thread_running:
            return
        # self._inference_first()
        self.start_observe()
        self.start_inference()
        self.start_control()
        self.start_visualize()
        self.logger.info('VLA client resumed.')

    def stop(self):
        """Backward-compatible alias of pause()."""
        self.pause()
        time.sleep(self.realtime_data_manager.avg_infer_time * 1.5) # make sure inference thread is stopped.
        self.image_process_time = 0.0
        self.task_language_manager.reset()
        self.realtime_data_manager.clear()
        with self.show_thread_lock:
            self.current_prob_progress = 0.0
        # TODO: Robot reset

    def close(self):
        """Close the VLA client and clean up all resources.

        This method performs a complete shutdown of the VLA client by:
        - Stopping all running threads with timeouts
        - Closing dataset recording if enabled
        - Closing ZMQ client connections
        - Stopping visualization components
        - Cleaning up all allocated resources
        """
        self.is_observe_thread_running = False
        self.is_inference_thread_running = False
        self.is_control_thread_running = False
        self.is_running = False
        self.realtime_data_manager.cancel_waiters()

        if self.observe_thread.is_alive():
            self.observe_thread.join(timeout=1.0)
        if self.inference_thread.is_alive():
            self.inference_thread.join(timeout=1.0)

        # Stop and join timer threads
        if self.control_thread_timer.is_alive():
            self.control_thread_timer.stop(timeout=1.0)
        if self.visualize_thread_timer.is_alive():
            self.visualize_thread_timer.stop(timeout=1.0)

        if hasattr(self, 'data_record_manager') and self.data_record_manager is not None:
            self.data_record_manager.close()
        if self.camera_preview is not None:
            self.camera_preview.close()

        self.vla_zmq.close()
        self.visualize_server.stop_server()

        if hasattr(self, '_img_executor') and self._img_executor is not None:
            self._img_executor.shutdown(wait=False)

        self.logger.info('Inference client closed.')
    def reset(self):
        self.image_process_time = 0.0
        self.last_step_result = None
        self.pipeline_error = None
        with self._step_meta_lock:
            self._episode_generation += 1
            self._latest_observation_step = None
            self._latest_applied_action_step = None
            self._last_accepted_observation_step = None
            self._control_in_flight = False
        self.episode_done_event.clear()

    def wait_for_inference_idle(self, timeout):
        acquired = self._inference_cycle_lock.acquire(timeout=timeout)
        if acquired:
            self._inference_cycle_lock.release()
        return acquired
    #################### VLA Client Inline functions ####################
    def _observe_thread_fun(self):
        """Observation thread function for continuous data collection from robot sensors.

        This method runs in a separate thread and continuously:
        - Retrieves observations from the robot
        - Processes the observation data
        - Adds processed data to the real-time data manager
        - Records data if recording is enabled
        """
        while self.is_running:
            if not self.is_observe_thread_running:
                time.sleep(0.001)
                continue
            observations = self.robot.retrieve_observation()
            # observations keys=dict_keys(['ref_timestamp', 'cam.hand_left', 'cam.hand_right', 'cam.head', 'obs.state', 'action'])
            # print(f"Debug: observations keys={observations.keys()}")
            # timestamp_1 = time.time()
            # timestamp_2 = None
            if observations is not None:
                self._ingest_observation(observations)
            else:
                time.sleep(0.001)

    def _inference_thread_fun(self):
        while self.is_running:
            if not self.is_inference_thread_running:
                time.sleep(0.001)
                continue

            with self._inference_cycle_lock:
                if not self.is_inference_thread_running:
                    continue
                try:
                    if self.realtime_data_manager.infer_count == 0:
                        inference_ok = self._inference_first()
                    else:
                        inference_ok = self._inference_step()
                except Exception as exc:
                    self.pipeline_error = exc
                    self.is_inference_thread_running = False
                    self.is_control_thread_running = False
                    self.realtime_data_manager.cancel_waiters()
                    self.episode_done_event.set()
                    self.logger.exception("Inference pipeline failed")
                    continue
            if inference_ok:
                self.realtime_data_manager.wait_for_next(mode=self.config.rdm.mode, wait_time=self.config.controller.wait_time/1000)
            else:
                time.sleep(max(0.01, self.config.controller.wait_time / 1000))
            # print(f'\rInference count: {self.realtime_data_manager.infer_count}, current infer time: {self.realtime_data_manager.start_intra_traj_marker-self.realtime_data_manager.start_infer_marker:.4f}s, current traj time: {self.realtime_data_manager.start_ctrl_marker-self.realtime_data_manager.start_intra_traj_marker:.4f}s', end='', flush=True)
            # symbol = '=' * 10
    def _control_thread_fun(self):
        """Control thread function for real-time robot action execution.

        This method runs periodically to:
        - Retrieve fitted actions from the data manager
        - Send actions to the robot for execution
        - Record actions if recording is enabled
        - Update visualization if enabled
        - Update monitoring information
        """
        if not self.is_control_thread_running:
            return

        with self._step_meta_lock:
            action_fitted, action_raw, vel_fitted, acc_fitted = (
                self.realtime_data_manager.get_action_fitted()
            )
            self._control_in_flight = action_fitted is not None

        if action_fitted is not None:
            episode_done = False
            recorded_step = False
            try:
                step_result = self.robot.control_robot(action_fitted)
                if isinstance(step_result, RobotStepResult):
                    self.last_step_result = step_result
                    self._track_step_result(step_result)
                    if step_result.observation is not None:
                        if self.config.record.switch:
                            record_action = action_fitted
                            if hasattr(self.robot, 'to_dataset_action'):
                                record_action = self.robot.to_dataset_action(action_fitted)
                            self.data_record_manager.add_step(
                                step_result.observation,
                                record_action,
                                self.task_language_manager.get_current_language(),
                            )
                            recorded_step = True
                        self._ingest_observation(step_result.observation, record=False)
                    episode_done = bool(
                        step_result.success or step_result.terminated or step_result.truncated
                    )
                if episode_done:
                    self.is_inference_thread_running = False
                    self.is_control_thread_running = False
                    self.realtime_data_manager.cancel_waiters()
                    self.episode_done_event.set()
                else:
                    self.realtime_data_manager.mark_action_executed()
            except Exception as exc:
                self._stop_control_thread_on_error(exc)
                self.logger.error("Robot control failed: %s", exc)
                raise
            finally:
                with self._step_meta_lock:
                    self._control_in_flight = False
            # with self.show_thread_lock:
                # self.info_current_action = action_fitted.tolist() if hasattr(action_fitted, 'tolist') else list(action_fitted)

            if self.config.record.switch and not recorded_step:
                self.data_record_manager.add_action_async(action_fitted, time.perf_counter())

            # with self.show_thread_lock:
            #     self.info_act['action'] = action_fitted.shape

        # Only use alignment processing if prob_progress array length > 1
        prob_progress = self.realtime_data_manager.get_prob_progress()
        if prob_progress is not None:
            with self.show_thread_lock:
                self.current_prob_progress = prob_progress
            # print(f"current prob_progress: {prob_progress}")
            if self.config.language.auto_mode == True:
                # Automatically switch language instruction based on prob_progress changes
                self.task_language_manager.add_task_progress(progress=prob_progress)
                self.task_language_manager.advance_subtask()
        current_state = getattr(self.robot, 'current_state', None)
        self.visualize_server.update_chart_data(
            action_fitted=action_fitted,
            vel_fitted=vel_fitted,
            acc_fitted=acc_fitted,
            action_raw=action_raw,
            current_state=current_state,
            observe_period=self.observe_period / 1000,
            control_period=self.config.controller.period / 1000
            )

    def _ingest_observation(self, observations, record=True):
        """Process one observation and publish it to the shared inference buffer."""
        if record and self.config.record.switch:
            self.data_record_manager.add_observation_async(
                observations,
                self.task_language_manager.get_current_language(),
                time.perf_counter(),
            )
        data = self._process_data(observations)
        self._track_observation_meta(data.get('meta', {}))
        self.realtime_data_manager.add_observe_data(data)

    @staticmethod
    def _optional_int(value):
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _observation_meta_from_frame(self, frame):
        meta = {}
        mapping = {
            '_observation_step': 'observation_step',
            '_applied_action_step': 'applied_action_step',
            '_sim_time': 'sim_time',
            '_observation_mode': 'observation_mode',
            '_observation_source': 'observation_source',
        }
        for source_key, target_key in mapping.items():
            if source_key in frame:
                meta[target_key] = frame[source_key]
        return meta

    def _track_observation_meta(self, meta):
        observation_step = self._optional_int(meta.get('observation_step'))
        applied_action_step = self._optional_int(meta.get('applied_action_step'))
        with self._step_meta_lock:
            if observation_step is not None:
                self._latest_observation_step = observation_step
            if applied_action_step is not None:
                self._latest_applied_action_step = applied_action_step

    def _track_step_result(self, step_result):
        observation_step = self._optional_int(step_result.observation_step)
        applied_action_step = self._optional_int(step_result.applied_action_step)
        with self._step_meta_lock:
            self._control_in_flight = False
            if observation_step is not None:
                self._latest_observation_step = observation_step
            if applied_action_step is not None:
                self._latest_applied_action_step = applied_action_step

    def _effective_observation_step_locked(self):
        if self._latest_observation_step is None:
            return None
        return self._latest_observation_step + int(self._control_in_flight)

    def _request_observation_step(self, data):
        frames = data if isinstance(data, list) else [data]
        steps = [
            self._optional_int(frame.get('meta', {}).get('observation_step'))
            for frame in frames
            if isinstance(frame, dict)
        ]
        steps = [step for step in steps if step is not None]
        return max(steps) if steps else None

    def _action_buffer_needs_replenishment(self):
        if not self.is_control_thread_running:
            return True
        threshold = getattr(self.config.rdm, 'action_replenish_threshold', 0)
        return self.realtime_data_manager.needs_action_replenishment(threshold)

    def _prepare_action_data_for_current_step(self, action_data, request_observation_step):
        if self.config.rdm.mode != 'async' or request_observation_step is None:
            return action_data
        with self._step_meta_lock:
            current_step = self._effective_observation_step_locked()
            last_accepted_step = self._last_accepted_observation_step
        if last_accepted_step is not None and request_observation_step < last_accepted_step:
            self.logger.warning(
                'Drop inference result from older observation step %s; last accepted step is %s.',
                request_observation_step,
                last_accepted_step,
            )
            return None
        prepared = dict(action_data)
        if current_step is None:
            prepared['_async_alignment_step'] = request_observation_step
            return prepared

        lag_steps = max(0, int(current_step) - int(request_observation_step))
        max_lag = getattr(self.config.rdm, 'max_async_observation_lag_steps', None)
        if max_lag is not None and lag_steps > int(max_lag):
            self.logger.warning(
                'Drop stale inference result: observation_step=%s, current_step=%s, lag_steps=%s.',
                request_observation_step,
                current_step,
                lag_steps,
            )
            return None
        if lag_steps <= 0:
            prepared['_async_alignment_step'] = current_step
            return prepared

        pred_action = action_data.get('pred_action')
        if pred_action is None or len(pred_action) <= lag_steps:
            self.logger.warning(
                'Drop inference result because lag_steps=%s consumes the whole action chunk.',
                lag_steps,
            )
            return None
        prepared['pred_action'] = pred_action[int(lag_steps):]
        prepared['_async_alignment_step'] = current_step
        self.logger.info(
            'Trim %s stale action(s) from async inference result based on observation_step=%s.',
            lag_steps,
            request_observation_step,
        )
        return prepared

    def _commit_async_action_chunk(
        self,
        action_data,
        source_action_count,
        action_chunk_fitted,
        vel_chunk_fitted,
        acc_chunk_fitted,
        timestamps_fitted,
        task_progress_fitted,
    ):
        with self._step_meta_lock:
            aligned_step = self._optional_int(action_data.get('_async_alignment_step'))
            current_step = self._effective_observation_step_locked()
            additional_lag = (
                max(0, current_step - aligned_step)
                if current_step is not None and aligned_step is not None
                else 0
            )
            if additional_lag:
                fitted_count = action_chunk_fitted.shape[1]
                sample_ratio = fitted_count / max(1, int(source_action_count))
                offset = max(1, int(round(additional_lag * sample_ratio)))
                if offset >= fitted_count - 1:
                    self.logger.warning(
                        'Drop async action chunk because %s additional simulation step(s) '
                        'consume the processed trajectory.',
                        additional_lag,
                    )
                    return False
                action_chunk_fitted = action_chunk_fitted[:, offset:]
                vel_chunk_fitted = vel_chunk_fitted[:, offset:]
                acc_chunk_fitted = acc_chunk_fitted[:, offset:]
                timestamps_fitted = timestamps_fitted[offset:]
                if (
                    task_progress_fitted is not None
                    and np.ndim(task_progress_fitted) > 0
                    and len(task_progress_fitted) >= offset
                ):
                    task_progress_fitted = task_progress_fitted[offset:]
                self.logger.info(
                    'Trim %s additional processed action sample(s) before async commit.',
                    offset,
                )

            self.realtime_data_manager.set_inter_traj_time_marker()
            target_chunk_index = self.realtime_data_manager.get_start_chunk_index(
                timestamps_fitted
            )
            currt_action, currt_vel, currt_acc = (
                self.realtime_data_manager.get_current_state()
            )
            action_chunk_smoothed, vel_chunk_smoothed, acc_chunk_smoothed, target_chunk_index = (
                self.inter_chunk_fuser.process(
                    next_action_chunk=action_chunk_fitted,
                    next_vel_chunk=vel_chunk_fitted,
                    next_acc_chunk=acc_chunk_fitted,
                    next_timestamps=timestamps_fitted,
                    target_chunk_index=target_chunk_index,
                    currt_action=currt_action if self.is_control_thread_running else None,
                    currt_vel=currt_vel if self.is_control_thread_running else None,
                    currt_acc=currt_acc if self.is_control_thread_running else None,
                    joint_indices=(
                        self.robot.get_joint_indices()
                        if self.is_control_thread_running else None
                    ),
                    step_indices=(
                        self.robot.get_step_indices()
                        if self.is_control_thread_running else None
                    ),
                )
            )
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
            )
            return True

    def _mark_inference_result_accepted(self, request_observation_step):
        if request_observation_step is None:
            return
        with self._step_meta_lock:
            if (
                self._last_accepted_observation_step is None
                or request_observation_step > self._last_accepted_observation_step
            ):
                self._last_accepted_observation_step = request_observation_step

    def _begin_inference_request(self):
        with self._step_meta_lock:
            if self._inference_in_flight:
                return None
            self._inference_in_flight = True
            return self._episode_generation

    def _finish_inference_request(self):
        with self._step_meta_lock:
            self._inference_in_flight = False

    def _inference_request_is_current(self, generation):
        with self._step_meta_lock:
            return (
                generation == self._episode_generation
                and self.is_inference_thread_running
            )

    def _visualize_thread_fun(self):
        # Send state data to visualization server for live plotting when control thread is not running
        if not self.is_control_thread_running:
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
        data = self.realtime_data_manager.pop_observe_data(
            num_samples=1 if not self.config.vision.history_frame else 2,
            latest_only=self.config.rdm.mode == 'async',
        )
        if data is not None:
            request_generation = self._begin_inference_request()
            if request_generation is None:
                self.realtime_data_manager.restore_observe_data(
                    data,
                    only_if_empty=self.config.rdm.mode == 'async',
                )
                return False
            request_observation_step = self._request_observation_step(data)
            # Record inference start timestamp for control timestamp updates
            self.realtime_data_manager.set_infer_time_marker()

            # Send data for inference and wait for results
            try:
                result = self._request_inference(data, timeout_ms=self.config.vla_zmq.infer_timeout * 4)
            finally:
                self._finish_inference_request()
            if not self._inference_request_is_current(request_generation):
                return False
            if result is None or 'data' not in result:
                self.realtime_data_manager.restore_observe_data(
                    data,
                    only_if_empty=self.config.rdm.mode == 'async',
                )
                return False
            # Record trajectory fitting timestamp
            avg_infer_time = result.get('meta', {}).get('avg_infer_time', 0.0)
            self.realtime_data_manager.set_intra_traj_time_marker()
            self.realtime_data_manager.add_infer_count()

            action_data = self._prepare_action_data_for_current_step(
                result['data'],
                request_observation_step,
            )
            if action_data is None:
                return False

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
            # currt_action, currt_vel, currt_acc = self.realtime_data_manager.get_current_state()
            action_chunk_smoothed, vel_chunk_smoothed, acc_chunk_smoothed, target_chunk_index = self.inter_chunk_fuser.process(
                next_action_chunk=action_chunk_fitted,
                next_vel_chunk=vel_chunk_fitted,
                next_acc_chunk=acc_chunk_fitted,
                next_timestamps=timestamps_fitted,
                target_chunk_index=target_chunk_index,
                currt_action=None,
                currt_vel=None,
                currt_acc=None,
                joint_indices=None,
                step_indices=self.robot.get_step_indices(),
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
            )
            self._mark_inference_result_accepted(request_observation_step)

            # Compute average inference and trajectory fitting times
            self.realtime_data_manager.compute_avg_comm_infer_time()
            self.realtime_data_manager.compute_avg_intra_traj_time()
            self.realtime_data_manager.compute_avg_inter_traj_time()
            self.realtime_data_manager.compute_avg_comm_time(avg_infer_time=avg_infer_time)
            return True
        return False

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
            return False
        if not self._action_buffer_needs_replenishment():
            return False

        # Get observation data (thread-safe function, no lock needed)
        data = self.realtime_data_manager.pop_observe_data(
            num_samples=1 if not self.config.vision.history_frame else 2,
            latest_only=self.config.rdm.mode == 'async',
        )
        request_observation_step = self._request_observation_step(data) if data is not None else None
        if isinstance(data, dict):
            currt_language_instruction = data.get("obs", {}).get("language")[0]
        elif isinstance(data, list):
            currt_language_instruction = data[1].get("obs", {}).get("language")[0]
        else:
            currt_language_instruction = ''
        # print(f"data keys: {data.keys() if data is not None else None}, infer_count: {self.realtime_data_manager.infer_count}")
        if data is not None:
            request_generation = self._begin_inference_request()
            if request_generation is None:
                self.realtime_data_manager.restore_observe_data(
                    data,
                    only_if_empty=self.config.rdm.mode == 'async',
                )
                return False
            # Record inference start timestamp
            self.realtime_data_manager.set_infer_time_marker()

            # Send data for inference and wait for results
            try:
                result = self._request_inference(data, timeout_ms = self.config.vla_zmq.infer_timeout)
            finally:
                self._finish_inference_request()
            if not self._inference_request_is_current(request_generation):
                return False
            if result is None:
                self.logger.warning("Inference result is None.")
                self.realtime_data_manager.restore_observe_data(
                    data,
                    only_if_empty=self.config.rdm.mode == 'async',
                )
                return False
            if 'data' not in result:
                self.logger.warning("Inference result doesn't have data.")
                self.realtime_data_manager.restore_observe_data(
                    data,
                    only_if_empty=self.config.rdm.mode == 'async',
                )
                return False

            avg_infer_time = result.get('meta', {}).get('avg_infer_time', 0.0)
            # Record trajectory fitting timestamp
            self.realtime_data_manager.set_intra_traj_time_marker()
            self.realtime_data_manager.add_infer_count()
            action_data = self._prepare_action_data_for_current_step(
                result['data'],
                request_observation_step,
            )
            if action_data is None:
                return False

            # Get current data timestamp and update timestamps
            action_chunk, timestamp_chunk, loc_timestamp = self._process_action_chunk(action_data)
            self.realtime_data_manager.set_observe_time_marker(loc_timestamp)

            # Add action data (thread-safe function, no lock needed)
            self.realtime_data_manager.update_action_chunk_raw(action_chunk, timestamp_chunk)


            timestamps, action_chunk = self.realtime_data_manager.pop_action_chunk(time_offset=0.0)
            if timestamps is None:
                self.logger.warning("Return None when pop action chunk from realtime_data_manager.")
                return False
            source_action_count = action_chunk.shape[1]
            prob_progress = self._parse_prob_progress(action_data)
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted, task_progress_fitted = self.intra_chunk_smoother.process(
                timestamps,
                action_chunk,
                time_step=self.config.controller.period,
                task_progress=prob_progress,
                joint_indices=self.robot.get_joint_indices(),
                step_indices=self.robot.get_step_indices())

            if not self._commit_async_action_chunk(
                action_data=action_data,
                source_action_count=source_action_count,
                action_chunk_fitted=action_chunk_fitted,
                vel_chunk_fitted=vel_chunk_fitted,
                acc_chunk_fitted=acc_chunk_fitted,
                timestamps_fitted=timestamps_fitted,
                task_progress_fitted=task_progress_fitted,
            ):
                return False
            self._mark_inference_result_accepted(request_observation_step)

            # Compute average inference and trajectory fitting times
            self.realtime_data_manager.compute_avg_comm_infer_time()
            self.realtime_data_manager.compute_avg_intra_traj_time()
            self.realtime_data_manager.compute_avg_inter_traj_time()
            self.realtime_data_manager.compute_avg_comm_time(avg_infer_time=avg_infer_time)
            if self.config.language.auto_mode == True:
                self.task_language_manager.reset_task_progress(
                    language_instruction=currt_language_instruction,
                    task_progress_next=task_progress_fitted
                )
            return True
        else:
            return False

    def _process_image_thread_fun(self, key, value):
        """Process image data by padding, resize and encoding.

        Args:
            key (str): Image key identifier.
            value (np.ndarray): Raw image data from robot sensors.

        Returns:
            tuple: A tuple containing:
                - key (str): Original image key
                - img_encoded (np.ndarray): Encoded image data for transmission
        """
        ext = '.png' if 'depth.' in key else '.jpg'
        # print(f"Debug: raw image shape: {value.shape}")
        # print(f"Debug: preprocess_fun={self._preprocess_func}")
        img_processed = self._preprocess_func(value) if self._preprocess_func else value
        # print(f"Debug: processed image shape: {value.shape}")
        # encode_params = [cv2.IMWRITE_JPEG_QUALITY, 80]
        # img_encoded = cv2.imencode(ext, img_processed, encode_params)[1]
        # image is encoded in BGR space, default for OpenCV
        encode_result, img_encoded = cv2.imencode(ext, img_processed)
        if not encode_result:
            self.logger.warning(f"Image encoding failed for {key}.")
        return key, img_encoded

    def _process_image(self, frame):
        """Process multiple images in threads.

        Args:
            frame (dict): A dictionary containing observation data, including image data, proprioception state data.

        Returns:
            dict: The encoded images with key and values.
        """
        start_time = time.perf_counter()

        cam_items = [(key, value) for key, value in frame.items() if 'cam.' in key]
        if self.camera_shape_dict is None:
            self.camera_shape_dict = {key: value.shape for key, value in cam_items}
            # print(f"Debug: camera shape dict={self.camera_shape_dict}")
        # Use shared thread pool to parallel process all cameras (avoid per-frame pool creation)
        futures = [self._img_executor.submit(self._process_image_thread_fun, key, value) for key, value in cam_items]
        results = [future.result() for future in futures]  # Wait for all tasks to complete
        encoded_imgs = {}
        for key, encoded_img in results:
            encoded_imgs[key] = encoded_img
            # Print the size of encoded_img in MB
            # Encoded image size for cam.hand_left: 66376 bytes (0.0633 MB)
            # Encoded image size for cam.hand_right: 69349 bytes (0.0661 MB)
            # Encoded image size for cam.head: 94484 bytes (0.0901 MB)
            # encoded_img_size_mb = len(encoded_img) / (1024 * 1024)
            # print(f"Encoded image size for {key}: {len(encoded_img)} bytes ({encoded_img_size_mb:.4f} MB)")

        # Calculate processing time in milliseconds
        self.image_process_time = self.image_process_time * 0.8 +  (time.perf_counter() - start_time) * 1000 * 0.2
        # Send images to visualization interface
        self.visualize_server.update_image_data(encoded_imgs)
        if self.camera_preview is not None:
            self.camera_preview.publish(encoded_imgs, self.camera_shape_dict, frame.get('_joint_trajectory'))
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
        observation_meta = self._observation_meta_from_frame(frame)

        # with self.show_thread_lock:
            # if 'obs.state' in frame and frame['obs.state'] is not None:
            #     self.info_current_state = frame['obs.state'].tolist() if hasattr(frame['obs.state'], 'tolist') else list(frame['obs.state'])
            # self.info_obs['state'] = frame['obs.state'].shape
        data = {
            'type': 'vla_obs',
            'ref_timestamp': frame['ref_timestamp'],
            'loc_timestamp': loc_timestamp,
            'obs': {
                **encoded_imgs,
                'state': frame['obs.state'],
                'language': [self.task_language_manager.get_current_language()],
            },
        }
        if observation_meta:
            data['meta'] = observation_meta
        # data['obs'] keys = dict_keys(['cam.hand_left', 'cam.hand_right', 'cam.head', 'state', 'language'])
        # print(f"Debug: {data['obs'].keys()}")
        return data

    @run_time_decorator
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
            action_steps = getattr(self.config.controller, 'action_steps', None)
            if action_steps is not None:
                pred_action = pred_action[:int(action_steps)]
            if len(pred_action) == 0:
                raise ValueError('pred_action must contain at least one action')
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
        started = time.perf_counter()
        result = None
        try:
            result = self._receive_inference(data, timeout_ms)
            return result
        finally:
            if getattr(getattr(self, 'robot', None), 'DATASET_ROBOT_TYPE', None) == 'PandaOmron':
                elapsed = time.perf_counter() - started
                count = getattr(self, '_inference_timing_count', 0) + 1
                self._inference_timing_count = count
                if count == 1 or count % 16 == 0 or result is None:
                    self.logger.info(
                        'RoboCasa inference wait: request=%d duration=%.6fs status=%s server_avg_s=%s',
                        count, elapsed, 'ok' if result is not None else 'failed',
                        (result.get('meta') or {}).get('avg_infer_time') if result else None,
                    )

    def _receive_inference(self, data, timeout_ms):
        request_id = self._next_request_id()
        request_meta = {'request_id': request_id}
        observation_step = self._request_observation_step(data)
        if observation_step is not None:
            request_meta['observation_step'] = observation_step
        # start_time = time.time()
        if not self.vla_zmq.sendMessage(data, meta=request_meta):
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
                self.logger.error(
                    "No inference response from %s within %d ms; check the model server output",
                    self.vla_zmq.client_addr,
                    timeout_ms,
                )
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
