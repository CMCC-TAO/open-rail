import cv2
import time
import logging
import threading
import numpy as np

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
from client.core.data_record_manager import DataRecordManager
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
        # Initialize the dataset writer with the provided recording configuration
        self.data_record_manager = DataRecordManager(record_config=self.config.record)
        # Create visualization WebSocket server for live image and trajectory updates
        self.visualize_server = VisualizeServer(visualize_config=self.config.visualize)
        self.vla_zmq = vla_zmq_client
        self.robot = robot
        self.is_running = False
        self.is_observe_thread_running = False
        self.is_inference_thread_running = False
        self.is_control_thread_running = False
        
        # Define image preprocess function
        self.update_preprocess_func()

        self.observe_thread = threading.Thread(target=self._observe_thread_fun, daemon=True)
        self.inference_thread = threading.Thread(target=self._inference_thread_fun, daemon=True)
        self.control_thread_timer = MultiThreadTimer(self.config.controller.period, self._control_thread_fun)
        self.visualize_thread_timer = MultiThreadTimer(self.config.controller.period, self._visualize_thread_fun)
        
        self.show_thread_lock = threading.Lock()

        # Shared thread pool for image encoding (avoid per-frame pool creation overhead)
        # self._img_executor = ThreadPoolExecutor(max_workers=3*1, thread_name_prefix="img_enc")

        # Inference variables
        self.set_observe_period(speed=self.config.controller.speed)
        self._request_id = 0


        # Information for monitoring current action and state (left arm 7 + right arm 7 + left gripper 1 + right gripper 1)
        self.image_process_time = 0.0
        self.current_prob_progress = 0.0
        # self.info_obs, self.info_act = {}, {}
        self.camera_shape_dict = None
        self.logger.info('VLAClient initialized.')

    ######################### VLAClient APIs #########################
    def start_observe(self):
        """
        Starts the observation process by activating the observation thread.

        This method sets the running and observation thread flags to True, and starts the observation thread if it is not currently alive.

        Returns:
            None
        """
        self.is_running = True
        self.is_observe_thread_running = True
        if not self.observe_thread.is_alive():
            self.observe_thread.start()
        self.logger.info('VLAClient observe thread started.')

    def stop_observe(self):
        self.is_observe_thread_running = False
        self.logger.info('VLAClient observe thread stopped.')

    def start_inference(self):
        self.is_running = True
        self.is_inference_thread_running = True
        if not self.inference_thread.is_alive():
            self.inference_thread.start()
        self.logger.info('VLAClient inference thread started.')

    def stop_inference(self):
        self.is_inference_thread_running = False
        self.logger.info('VLAClient inference thread stopped.')

    def start_control(self):
        self.is_running = True
        self.is_control_thread_running = True
        if not self.control_thread_timer.is_alive():
            self.control_thread_timer.start()
        # start new task in task_language manager for auto mode
        self.task_language_manager.new_task()

    def stop_control(self):
        self.is_control_thread_running = False
    
    def set_control_period(self, period) -> None:
        self.control_thread_timer.set_interval(period)
        self.visualize_thread_timer.set_interval(period)
    
    def set_observe_period(self, speed) -> None:
        self.observe_period = 1.0 / speed / self.config.controller.raw_fps
        # print(f"Debug: control speed = {speed}")
    
    def _stop_control_thread_on_error(self):
        self.is_control_thread_running = False
        if self.control_thread_timer.is_alive():
            self.control_thread_timer.stop(timeout=1.0)

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
        self.is_observe_thread_running = False
        self.is_inference_thread_running = False
        self.is_control_thread_running = False
        self.is_running = False
        
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

        self.vla_zmq.close()
        self.visualize_server.stop_server()

        # if hasattr(self, '_img_executor') and self._img_executor is not None:
        #     self._img_executor.shutdown(wait=False)

        self.logger.info('Inference client closed.')
    def reset(self):
        self.image_process_time = 0.0
    
    @property
    def thread_status(self):
        return {
        "observe_running": self.is_observe_thread_running,
        "inference_running": self.is_inference_thread_running,
        "control_running": self.is_control_thread_running
        }

    @property
    def runtime_status(self):
        status = {
            "img_proc_time": self.image_process_time,
            "current_prob_progress": self.current_prob_progress
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
            # timestamp_1 = time.time()
            observations = self.robot.retrieve_observation()
            # timestamp_2 = time.time()
            # self.logger.debug(f"Robot retrieve observation time: {(timestamp_2-timestamp_1) * 1000: .4f}ms, observations is {'None' if observations is None else 'dict'}")
            # observations keys=dict_keys(['ref_timestamp', 'cam.hand_left', 'cam.hand_right', 'cam.head', 'obs.state', 'action'])
            # print(f"Debug: observations keys={observations.keys()}")
            # timestamp_1 = time.time()
            # timestamp_2 = None
            if observations is not None:
                # Decide whether to change language instruction based on the task progress predicted by the VLA model
                data, record_data = self._process_data(observations)
                # timestamp_3 = time.time()
                # print(f"Debug: process time={((timestamp_3-timestamp_1) if timestamp_2 is None else (timestamp_3-timestamp_2)) * 1000} ms")
                self.realtime_data_manager.add_observe_data(data)
                # timestamp_4 = time.time()
                # print(f"Debug: add time={(timestamp_4-timestamp_3)*1000} ms")
                if self.config.record.switch:
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
                    self.data_record_manager.add_observation_async(observation=record_data, extra_info=extra_info, timestamp=time.perf_counter())
                    # timestamp_3 = time.time()
                    # self.logger.debug(f'Data recorder add observation time: {(timestamp_3-timestamp_2) * 1000: .4f}ms')
                    # timestamp_2 = time.time()
                    # print(f"Debug: record time={(timestamp_2-timestamp_1) * 1000} ms")
            # time.sleep(0.001)
    
    def _inference_thread_fun(self):
        while self.is_running:
            if not self.is_inference_thread_running:
                time.sleep(0.001)
                continue

            if self.realtime_data_manager.infer_count == 0:
                self._inference_first()
                self.realtime_data_manager.wait_for_next(mode=self.config.rdm.mode, wait_time=self.config.controller.wait_time/1000)
                # self.realtime_data_manager.wait_for_next(mode='sync', wait_time=self.config.controller.wait_time/1000)
            else:
                self._inference_step()
                # self.inferenceFirstThreadFun()
                self.realtime_data_manager.wait_for_next(mode=self.config.rdm.mode, wait_time=self.config.controller.wait_time/1000)
                # self.realtime_data_manager.wait_for_next(mode='sync', wait_time=self.config.controller.wait_time/1000)
            # print(f'\rInference count: {self.realtime_data_manager.infer_count}, current infer time: {self.realtime_data_manager.start_intra_traj_marker-self.realtime_data_manager.start_infer_marker:.4f}s, current traj time: {self.realtime_data_manager.start_ctrl_marker-self.realtime_data_manager.start_intra_traj_marker:.4f}s', end='', flush=True)
            # symbol = '=' * 10
    def _control_thread_fun(self):
        if not self.is_control_thread_running:
            return

        action_fitted, action_raw, vel_fitted, acc_fitted = self.realtime_data_manager.get_action_fitted()

        if action_fitted is not None:
            try:
                self.robot.control_robot(action_fitted)
            except Exception as exc:
                self._stop_control_thread_on_error()
                self.logger.error("Robot control failed: %s", exc)
                raise
            # with self.show_thread_lock:
                # self.info_current_action = action_fitted.tolist() if hasattr(action_fitted, 'tolist') else list(action_fitted)
            
            if self.config.record.switch:
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
                self.task_language_manager.try_advance_subtask()
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
        data = self.realtime_data_manager.pop_observe_data(num_samples = 1 if not self.config.vision.history_frame else 2)
        if data is not None:
            # Record inference start timestamp for control timestamp updates
            self.realtime_data_manager.set_infer_time_marker()
            
            # Send data for inference and wait for results
            result = self._request_inference(data, timeout_ms=self.config.vla_zmq.infer_timeout * 4)
            if result is None or 'data' not in result:
                # print("Debug: infer first timeout.")
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
            )

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
                joint_indices=self.robot.get_joint_indices() if self.is_control_thread_running else None,
                step_indices=self.robot.get_step_indices() if self.is_control_thread_running else None,
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
        encode_result, img_encoded = cv2.imencode(ext, img_for_infer)
        if not encode_result:
            self.logger.warning(f"Image encoding failed for {key}.")
        return key, value, img_encoded

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
        raw_imgs = {}
        for key, value in cam_items:
            key, raw_img, encoded_img = self._process_image_thread_fun(key, value)
            raw_imgs[key] = raw_img
            encoded_imgs[key] = encoded_img

        if self.camera_shape_dict is None and raw_imgs:
            self.camera_shape_dict = {key: img.shape for key, img in raw_imgs.items()}

        self.image_process_time = self.image_process_time * 0.8 +  (time.perf_counter() - start_time) * 1000 * 0.2
        self.visualize_server.update_image_data(encoded_imgs)
        return encoded_imgs, raw_imgs
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
        encoded_imgs, raw_imgs = self._process_image(frame)

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

        record_data = {
            'type': 'vla_obs',
            'ref_timestamp': frame['ref_timestamp'],
            'loc_timestamp': loc_timestamp,
            'obs': {
                **raw_imgs,
                'state': obs_state,
                'language': language,
            },
        }
        return infer_data, record_data

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
