import cv2
import time
import threading
import logging
import numpy as np
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor

from client.utils import misc
from client.utils.util import run_time_decorator, parse_action_layout
from client.utils.multi_thread_timer import MultiThreadTimer
from client.core.zmq_client import ZMQClient
from client.core.inter_chunk_fuser import InterChunkFuser
from client.core.intra_chunk_smoother import IntraChunkSmoother
from client.core.realtime_data_manager import RealtimeDataManager
from client.core.task_language_manager import TaskLanguageManager
from client.core.visualize_server import VisualizeServer
from client.core.save_lerobot import LeRobotDatasetWriter
from client.robots.base_robot import RobotBase


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
        self.action_layout = dict(self.config.action_layout) if hasattr(self.config, 'action_layout') else {}
        self.action_dim, self.joint_indices, self.step_indices = parse_action_layout(self.action_layout)
        self.is_running = False
        self.is_observe_thread_running = False
        self.is_inference_thread_running = False
        self.is_control_thread_running = False
        
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
        self.control_thread_timer = MultiThreadTimer(float(self.config.controller.period), self._control_thread_fun)
        self.visualize_thread_timer = MultiThreadTimer(float(self.config.controller.period), self._visualize_thread_fun)
        
        self.show_thread_lock = threading.Lock()

        # Shared thread pool for image encoding (avoid per-frame pool creation overhead)
        self._img_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="img_enc")

        # Inference variables
        self.config.observer.period = 1.0 / self.config.observer.fps
        self._request_id = 0

        # Initialize the dataset writer with the provided recording configuration
        self.dataset_write = LeRobotDatasetWriter(
            record_config=self.config.record,
            task=getattr(self.config.language, 'task_id', None)
        )

        # Create visualization WebSocket server for live image and trajectory updates
        self.visualize_server = VisualizeServer(visualize_config=self.config.visualize)
        self.vis_global_step = 0
        self.vis_prev_action, self.vis_prev_state, self.vis_prev_origin = None, None, None
        self.vis_prev_action_vel, self.vis_prev_state_vel, self.vis_prev_origin_vel = None, None, None

        # Information for monitoring current action and state (left arm 7 + right arm 7 + left gripper 1 + right gripper 1)
        action_dim = self.action_dim if self.action_dim > 0 else 16
        # self.info_current_action = [0.0] * action_dim
        # self.info_current_state = [0.0] * action_dim
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

    def update_camera_shape(self) -> dict:
        """Pop one observation from RDM and update recorder camera shapes by runtime image size."""
        if not hasattr(self, "dataset_write") or self.dataset_write is None:
            self.logger.warning("dataset_write is not initialized, skip update_camera_shape.")
            return {}

        # print(f"Debug: camera_shape_dict: {camera_shape_dict}")
        self.dataset_write.update_camera_shape_dict(self.camera_shape_dict)
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

    def run(self):
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
        
        if self.observe_thread.is_alive():
            self.observe_thread.join(timeout=1.0)
        if self.inference_thread.is_alive():
            self.inference_thread.join(timeout=1.0)

        # Stop and join timer threads
        if self.control_thread_timer.is_alive():
            self.control_thread_timer.stop(timeout=1.0)
        if self.visualize_thread_timer.is_alive():
            self.visualize_thread_timer.stop(timeout=1.0)
        
        if hasattr(self, 'dataset_write') and self.dataset_write is not None:
            self.dataset_write.close()

        self.vla_zmq.close()
        self.visualize_server.stop_server()

        if hasattr(self, '_img_executor') and self._img_executor is not None:
            self._img_executor.shutdown(wait=False)

        self.logger.info('Inference client closed.')

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
                if self.config.record.switch :
                    self.dataset_write.add_observation_async(observations, self.task_language_manager.get_current_language(), time.perf_counter())
                    # timestamp_2 = time.time()
                    # print(f"Debug: record time={(timestamp_2-timestamp_1) * 1000} ms")
                # Decide whether to change language instruction based on the task progress predicted by the VLA model
                data = self._process_data(observations)
                # timestamp_3 = time.time()
                # print(f"Debug: process time={((timestamp_3-timestamp_1) if timestamp_2 is None else (timestamp_3-timestamp_2)) * 1000} ms")
                self.realtime_data_manager.add_observe_data(data)
                # timestamp_4 = time.time()
                # print(f"Debug: add time={(timestamp_4-timestamp_3)*1000} ms")
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
            # print(f'\rInference count: {self.realtime_data_manager.infer_count}, current infer time: {self.realtime_data_manager.start_traj_marker-self.realtime_data_manager.start_infer_marker:.4f}s, current traj time: {self.realtime_data_manager.start_ctrl_marker-self.realtime_data_manager.start_traj_marker:.4f}s', end='', flush=True)
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

        action_fitted, action_raw, vel_fitted, acc_fitted = self.realtime_data_manager.get_action_fitted()

        if action_fitted is not None:
            self.robot.control_robot(action_fitted)
            # with self.show_thread_lock:
                # self.info_current_action = action_fitted.tolist() if hasattr(action_fitted, 'tolist') else list(action_fitted)
            
            if self.config.record.switch and self.is_control_thread_running and self.is_running:
                self.dataset_write.add_action_async(action_fitted, time.perf_counter())
            
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
        self.vis_action_state(action_fitted, vel_fitted, acc_fitted, action_raw, current_state)

    def _visualize_thread_fun(self):
        # Send state data to visualization server for live plotting when control thread is not running
        if not self.is_control_thread_running:
            current_state = getattr(self.robot, 'current_state', None) if self.is_observe_thread_running else None
            action_fitted, action_raw, vel_fitted, acc_fitted = self.realtime_data_manager.get_action_fitted(mode='visualize') if self.is_inference_thread_running else (None, None, None, None)
            self.vis_action_state(action_fitted=action_fitted,
                                vel_fitted=vel_fitted,
                                acc_fitted=acc_fitted,
                                action_raw=action_raw,
                                current_state=current_state)
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
            result = self._request_inference(data, timeout_ms=500)
            if result is None or 'data' not in result:
                # print("Debug: infer first timeout.")
                return
            self.realtime_data_manager.add_infer_count()

            action_data = result['data']
            
            # Get current data timestamp and update timestamps
            action_chunk, timestamp_chunk, loc_timestamp = self._process_action_chunk(action_data)
            self.realtime_data_manager.set_observe_time_marker(loc_timestamp)
            
            # Add action data (thread-safe function, no lock needed)
            self.realtime_data_manager.set_init_observe_timestamp(timestamp=timestamp_chunk[0])
            self.realtime_data_manager.update_action_chunk_raw(action_chunk, timestamp_chunk)

            # Record trajectory fitting timestamp
            self.realtime_data_manager.set_traj_time_marker()
            timestamps, action_chunk = self.realtime_data_manager.pop_action_chunk(time_offset=0.0)
            prob_progress = None
            if 'ext' in action_data and 'prob_progress' in action_data['ext']:
                prob_progress = action_data['ext']['prob_progress']
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted, task_progress_fitted = self.intra_chunk_smoother.process(
                timestamps,
                action_chunk,
                task_progress=prob_progress)

            # Record control timestamp
            self.realtime_data_manager.set_control_time_marker()
            target_chunk_index = self.realtime_data_manager.get_start_chunk_index(timestamps_fitted)
            # joint_indices = self.realtime_data_manager._get_joint_indices(action_chunk_fitted)
            # step_indices = self.realtime_data_manager._get_step_indices(action_chunk_fitted)
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
            self.realtime_data_manager.update_action_chunk_fitted(
                action_chunk_smoothed=action_chunk_smoothed,
                vel_chunk_smoothed=vel_chunk_smoothed,
                acc_chunk_smoothed=acc_chunk_smoothed,
                timestamps_smoothed=timestamps_fitted,
                target_chunk_index=target_chunk_index,
                prob_progress=task_progress_fitted
            )

            # Compute average inference and trajectory fitting times
            self.realtime_data_manager.compute_avg_infer_time()
            self.realtime_data_manager.compute_avg_traj_time()
    
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
            result = self._request_inference(data, timeout_ms = 500)
            if result is None:
                self.logger.warning("Inference result is None.")
                return
            if 'data' not in result:
                self.logger.warning("Inference result doesn't have data.")
                return
            self.realtime_data_manager.add_infer_count()
            action_data = result['data']
            
            # Get current data timestamp and update timestamps
            action_chunk, timestamp_chunk, loc_timestamp = self._process_action_chunk(action_data)
            self.realtime_data_manager.set_observe_time_marker(loc_timestamp)
            
            # Add action data (thread-safe function, no lock needed)
            self.realtime_data_manager.update_action_chunk_raw(action_chunk, timestamp_chunk)

            # Record trajectory fitting timestamp
            self.realtime_data_manager.set_traj_time_marker()

            timestamps, action_chunk = self.realtime_data_manager.pop_action_chunk(time_offset=0.0)
            if timestamps is None:
                self.logger.warning("Return None when pop action chunk from realtime_data_manager.")
                return
            prob_progress = None
            if 'ext' in action_data and 'prob_progress' in action_data['ext']:
                prob_progress = action_data['ext']['prob_progress']
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted, task_progress_fitted = self.intra_chunk_smoother.process(timestamps, action_chunk, task_progress=prob_progress)

            # Record control timestamp
            self.realtime_data_manager.set_control_time_marker()
            
            # Get prob_progress from action data if available

            target_chunk_index = self.realtime_data_manager.get_start_chunk_index(timestamps_fitted)
            joint_indices = self.realtime_data_manager._get_joint_indices(action_chunk_fitted)
            step_indices = self.realtime_data_manager._get_step_indices(action_chunk_fitted)
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
                joint_indices=joint_indices if self.is_control_thread_running else None,
                step_indices=step_indices if self.is_control_thread_running else None,
            )
            self.realtime_data_manager.update_action_chunk_fitted(
                action_chunk_smoothed=action_chunk_smoothed,
                vel_chunk_smoothed=vel_chunk_smoothed,
                acc_chunk_smoothed=acc_chunk_smoothed,
                timestamps_smoothed=timestamps_fitted,
                target_chunk_index=target_chunk_index,
                prob_progress=task_progress_fitted
            )

            # Compute average inference and trajectory fitting times
            self.realtime_data_manager.compute_avg_infer_time()
            self.realtime_data_manager.compute_avg_traj_time()
            if self.config.language.auto_mode == True:
                self.task_language_manager.reset_task_progress(
                    language_instruction=currt_language_instruction,
                    task_progress_next=task_progress_fitted
                )
        else:
            self.logger.warning("No observe data, skip inference.")

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

        # Calculate processing time in milliseconds
        self.image_process_time = self.image_process_time * 0.8 +  (time.perf_counter() - start_time) * 1000 * 0.2
        # Send images to visualization interface
        self.visualize_server.update_image_data(encoded_imgs)

        return encoded_imgs

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
            ref_timestamp = action_raw['ref_timestamp']
            loc_timestamp = action_raw['loc_timestamp']
            # Generate action and timestamp chunks
            for index, action in enumerate(pred_action):
                action_chunk.append(action)
                timestamp_chunk.append(self.config.observer.period * index)
            
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
        if not self.vla_zmq.sendMessage(data, meta={'request_id': request_id}):
            return None

        deadline = time.perf_counter() + timeout_ms / 1000.0
        while True:
            remain_s = deadline - time.perf_counter()
            if remain_s <= 0:
                return None
            msg = self.vla_zmq.recvMessage(timeout_ms=max(1, int(remain_s * 1000)))
            if msg is None:
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

    def vis_action_state(self, action_fitted=None, vel_fitted=None, acc_fitted=None, action_raw=None, current_state=None):
        """
        Visualize action and state data for debugging and monitoring.

        Args:
            action_fitted: Predicted action values for robot joints
            vel_fitted: Predicted velocity values (of action_fitted) for robot joints
            acc_fitted: Predicted acceleration values (of action_fitted) for robot joints
            action_raw: Raw action values before fitting
            current_state: Current robot joint state
        """
        # Convert non-None inputs to numpy arrays
        # action_np = np.asarray(action_fitted) if action_fitted is not None else None
        # action_vel = np.asarray(vel_fitted) if vel_fitted is not None else None
        # action_acc = np.asarray(acc_fitted) if acc_fitted is not None else None
        # state_np = np.asarray(current_state) if current_state is not None else None

        # Control period in seconds
        dt_ctrl = self.config.controller.period / 1000.0

        list_data = []

        # Position data
        if action_fitted is not None:
            list_data.append({
                'tab': 'position',
                'type': 'action_fitted',
                'x': self.vis_global_step,
                'joints_y': action_fitted.tolist()
            })
        if current_state is not None:
            list_data.append({
                'tab': 'position',
                'type': 'state',
                'x': self.vis_global_step,
                'joints_y': current_state.tolist()
            })

        # TODO: use real velocity/acceleration
        # Velocity/acceleration for state (derived from state)
        state_vel = None
        state_acc = None
        if current_state is not None:
            if self.vis_prev_state is None:
                state_vel = np.zeros_like(current_state)
                state_acc = np.zeros_like(current_state)
            else:
                try:
                    state_vel = (current_state - self.vis_prev_state) / dt_ctrl
                    if self.vis_prev_state_vel is None:
                        state_acc = np.zeros_like(current_state)
                    else:
                        state_acc = (state_vel - self.vis_prev_state_vel) / dt_ctrl
                except Exception as e:
                    self.logger.warning(f"Error computing state velocity/acceleration: {e}")
                    state_vel = np.zeros_like(current_state)
                    state_acc = np.zeros_like(current_state)

            list_data.append({
                'tab': 'velocity',
                'type': 'state',
                'x': self.vis_global_step,
                'joints_y': state_vel.tolist()
            })
            list_data.append({
                'tab': 'acceleration',
                'type': 'state',
                'x': self.vis_global_step,
                'joints_y': state_acc.tolist()
            })

        # Velocity/acceleration for action (direct input)
        if vel_fitted is not None:
            list_data.append({
                'tab': 'velocity',
                'type': 'action_fitted',
                'x': self.vis_global_step,
                'joints_y': vel_fitted.tolist()
            })
        if acc_fitted is not None:
            list_data.append({
                'tab': 'acceleration',
                'type': 'action_fitted',
                'x': self.vis_global_step,
                'joints_y': acc_fitted.tolist()
            })

        # Origin (raw action) series
        if action_raw is not None:
            origin_np = np.asarray(action_raw)
            list_data.append({
                'tab': 'position',
                'type': 'action_raw',
                'x': self.vis_global_step,
                'joints_y': origin_np.tolist()
            })

            dt_origin = self.config.observer.period
            if self.vis_prev_origin is None:
                origin_vel = np.zeros_like(origin_np)
                origin_acc = np.zeros_like(origin_np)
            else:
                origin_vel = (origin_np - self.vis_prev_origin) / dt_origin
                if self.vis_prev_origin_vel is None:
                    origin_acc = np.zeros_like(origin_np)
                else:
                    origin_acc = (origin_vel - self.vis_prev_origin_vel) / dt_origin

            list_data.append({
                'tab': 'velocity',
                'type': 'action_raw',
                'x': self.vis_global_step,
                'joints_y': origin_vel.tolist()
            })
            list_data.append({
                'tab': 'acceleration',
                'type': 'action_raw',
                'x': self.vis_global_step,
                'joints_y': origin_acc.tolist()
            })
            self.vis_prev_origin = origin_np
            self.vis_prev_origin_vel = origin_vel

        if list_data:
            self.visualize_server.update_chart_data(list_data)
            self.vis_global_step += 1

        # Update previous values only for available inputs
        if action_fitted is not None:
            self.vis_prev_action = action_fitted
        if vel_fitted is not None:
            self.vis_prev_action_vel = vel_fitted
        if current_state is not None:
            self.vis_prev_state = current_state
        if state_vel is not None:
            self.vis_prev_state_vel = state_vel

if __name__ == "__main__":
    pass
