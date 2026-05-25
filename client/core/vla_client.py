import cv2
import os
import json
import time
import threading
import logging
import numpy as np
from datetime import datetime
from collections import deque
from ml_collections import ConfigDict
from scipy.interpolate import CubicSpline, interp1d

from concurrent.futures import ThreadPoolExecutor

from client.utils import misc
from client.utils.util import run_time_decorator, parse_action_layout
from client.utils.multi_thread_timer import MultiThreadTimer
from client.core.zmq_client import ZMQClient
from client.core.inter_chunk_fuser import InterChunkFuser
from client.core.intra_chunk_smoother import IntraChunkSmoother
from client.core.realtime_data_manager import RealtimeDataManager
from client.core.save_lerobot import LeRobotDatasetWriter
from visual.websocket_server import VLAWebSocketServer


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
                rdm: RealtimeDataManager,
                inter_chunk_fuser: InterChunkFuser,
                intra_chunk_smoother: IntraChunkSmoother,
                vla_zmq_client: ZMQClient,
                robot: None):
        """Initialize the VLA Client.
        
        Args:
            config (ConfigDict): Configuration dictionary containing all system parameters
            rdm (RealtimeDataManager): Real-time data manager for handling observation and action data
            intra_chunk_smoother (IntraChunkSmoother): Intra-chunk smoother for action smoothing and fitting
            zmq_client (ZMQClient): ZMQ client for communication with VLA inference server
            vis_action_cams_zmq_client (ZMQClient): ZMQ client for communication with camera-action visualization server
            robot: Robot interface for observation collection and action execution
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.rdm = rdm
        self.inter_chunk_fuser = inter_chunk_fuser
        self.intra_chunk_smoother = intra_chunk_smoother
        self.vla_zmq = vla_zmq_client
        self.robot = robot
        self.action_layout = dict(self.config.action_layout) if hasattr(self.config, 'action_layout') else {}
        self.action_dim, self.joint_indices, self.step_indices = parse_action_layout(self.action_layout)
        self.is_running = False
        self.is_observe_thread_running = False
        self.is_inference_thread_running = False
        self.is_control_thread_running = False
        self.language_tasks = self._load_language_tasks(getattr(self.config.language, 'file_path', ''))
        self.language = self._sync_language_from_config()
        self.allow_language_switch = True  # Flag to control automatic language switching
        
        # Define image preprocess function
        if self.config.vision.preprocess != 'none':
            preprocess_func = getattr(misc, self.config.vision.preprocess)
            height, width = self.config.vision.preprocess_size
            self._preprocess_func = lambda img: preprocess_func(img, target_height=height, target_width=width)
        else:
            self._preprocess_func = None

        self.observe_thread = threading.Thread(target=self._observe_thread_fun, daemon=True)
        self.inference_thread = threading.Thread(target=self._inference_thread_fun, daemon=True)
        self.config.observer.period = 1.0 / self.config.observer.fps
        control_period_ms = float(self.config.controller.period)
        self.control_thread_timer = MultiThreadTimer(control_period_ms, self._control_thread_fun)
        
        self.thread_lock = threading.Lock()
        self.show_thread_lock = threading.Lock()

        # visualization buffer and thread lock
        self.act_exe_fitted_buffer = deque(maxlen=self.config.vis_action_length)
        self.act_exe_raw_buffer = deque(maxlen=self.config.vis_action_length)
        self.vel_exe_fitted_buffer = deque(maxlen=self.config.vis_action_length)
        self.acc_exe_fitted_buffer = deque(maxlen=self.config.vis_action_length)
        self.vis_action_lock = threading.Lock()
        
        # Inference variables
        self.infer_count = 0
        self.infer_flag = False
        self.wait_frame_count = 0
        self.infer_thread_lock = threading.Lock()
        self._request_id = 0

        if self.config.record.switch:
            # Initialize the dataset writer with the provided recording configuration
            self.dataset_write = LeRobotDatasetWriter(record_config=self.config.record)

        # Create visualization WebSocket server for live image and trajectory updates
        self.visualization_server = VLAWebSocketServer.get_instance()
        camera_cfg = getattr(getattr(self.config, 'visual', None), 'camera', None)
        if camera_cfg is not None:
            self.visualization_server.update_camera_open_config(camera_cfg)
        self.vis_global_step = 0
        self.vis_idx_count = 0
        self.vis_origin_chunk_action = None
        self.vis_ratio = (1.0 / self.config.observer.fps) / (self.config.intra_chunk.fitting_time_step / 1000.0) # (64 - 1) * ratio -> 420
        self.vis_prev_action, self.vis_prev_state, self.vis_prev_origin = None, None, None
        self.vis_prev_action_vel, self.vis_prev_state_vel, self.vis_prev_origin_vel = None, None, None
        self.vis_prev_origin_idx = None

        # The zmq client to communicate with action-camera visualization server
        if self.config.show_action_cams_qt:
            self.vis_action_cams_zmq = ZMQClient(config.vis_zmq)
            self.vis_action_cams_thread = threading.Thread(target=self.send_action_cams_to_vis_server, daemon=True)
        
        # Information for monitoring current action and state (left arm 7 + right arm 7 + left gripper 1 + right gripper 1)
        action_dim = self.action_dim if self.action_dim > 0 else 16
        self.info_current_action = [0.0] * action_dim
        self.info_current_state = [0.0] * action_dim
        self.info_obs, self.info_act = {}, {}
        self.debug_info = 'The debug information or trace information will be displayed here. \nPress "Enter" for more commands.'

        # Record data (action, velocity, acceleration) thread
        if self.config.record_exp_data:
            date_str = datetime.now().strftime("%Y%m%d%H%M%S")
            out_dir = os.path.join("tmp", date_str)
            os.makedirs(out_dir, exist_ok=True)
            self.files = {
                'action': open(os.path.join(out_dir, 'action.txt'), 'a'),
                'velocity': open(os.path.join(out_dir, 'velocilty.txt'), 'a'),
                'acceleration': open(os.path.join(out_dir, 'acceleration.txt'), 'a')
            }
            self.data_write_thread = threading.Thread(target=self._writer_thread)
            self.act_write_buffer = deque(maxlen=1000)
            self.vel_write_buffer = deque(maxlen=1000)
            self.acc_write_buffer = deque(maxlen=1000)

    def _load_language_tasks(self, file_path: str) -> dict:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        target_path = file_path if os.path.isabs(file_path) else os.path.join(root_dir, 'conf', file_path)
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                return {'Default': [x for x in data if isinstance(x, str)]}
            if isinstance(data, dict):
                return {k: [x for x in v if isinstance(x, str)] for k, v in data.items() if isinstance(v, list)}
        except Exception as e:
            self.logger.warning(f'Failed to load language command file: {target_path}, error: {e}')
        return {}

    def _sync_language_from_config(self) -> str:
        task_id = getattr(self.config.language, 'task_id', '')
        sub_task_id = int(getattr(self.config.language, 'sub_task_id', 0))
        task_cmds = self.language_tasks.get(task_id, [])

        if not task_cmds and self.language_tasks:
            task_id = next(iter(self.language_tasks.keys()))
            self.config.language.task_id = task_id
            task_cmds = self.language_tasks.get(task_id, [])

        if not task_cmds:
            self.config.language.sub_task_id = 0
            return ''

        sub_task_id = max(0, min(sub_task_id, len(task_cmds) - 1))
        self.config.language.sub_task_id = sub_task_id
        return task_cmds[sub_task_id]

    def _advance_language_subtask(self):
        task_id = getattr(self.config.language, 'task_id', '')
        task_cmds = self.language_tasks.get(task_id, [])
        if not task_cmds:
            return
        sub_task_id = int(getattr(self.config.language, 'sub_task_id', 0))
        sub_task_id = (sub_task_id + 1) % len(task_cmds)
        self.config.language.sub_task_id = sub_task_id
        self.language = task_cmds[sub_task_id]

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
            if observations is not None:
                if self.config.record.switch :
                    self.dataset_write.async_write_obs(observations,self.language,time.perf_counter())
                data = self._process_data(observations)
                self.rdm.add_observe_data(data)
            time.sleep(0.001)
    
    @run_time_decorator
    def inference_first(self):
        """First inference step, which initializes the control pipeline.
        
        This method performs the initial inference that sets up the control system:
        - Waits for robot stabilization after reset
        - Retrieves fresh observation data
        - Performs VLA inference to get action predictions
        - Initializes trajectory fitting and control timestamps
        - Sets up the fitted action chunk for control
        """
        # Disable automatic language switching during reset (but don't save/restore language)
        # saved_language = self.language
        self.allow_language_switch = False
        
        # Wait for observation changes after reset, then retrieve fresh obs for inference
        observations, cnt = None, 0
        while observations is None or cnt < 3:
            # time.sleep(0.2)
            self.rdm.clear_action_data()
            observations = self.robot.retrieve_observation()
            cnt += 1

        if observations is not None:
            self.rdm.clear_action_data()
            data = self._process_data(observations)
            self.rdm.add_observe_data(data)
            # Clear action data to ensure fresh action retrieval
        
        # Get observation data (thread-safe function, no lock needed)
        data = self.rdm.pop_observe_data(num_samples = 1 if not self.config.vision.history_frame else 2)
        if data is not None:
            # Record inference start timestamp for control timestamp updates
            self.rdm.set_infer_time_marker()
            
            # Send data for inference and wait for results
            result = self._request_inference(data, timeout_ms=500)
            if result is None or 'data' not in result:
                return
            self.rdm.add_infer_count()

            action_data = result['data']
            
            # Get current data timestamp and update timestamps
            action_chunk, timestamp_chunk, loc_timestamp = self._process_action_chunk(action_data)
            self.rdm.set_observe_time_marker(loc_timestamp)
            self.vis_idx_count = 0
            self.vis_origin_chunk_action = action_chunk
            
            # Add action data (thread-safe function, no lock needed)
            self.rdm.set_init_observe_timestamp(timestamp=timestamp_chunk[0])
            self.rdm.update_action_chunk_raw(action_chunk, timestamp_chunk)

            # Record trajectory fitting timestamp
            self.rdm.set_traj_time_marker()
            timestamps, action_chunk = self.rdm.pop_action_chunk(time_offset=0.0)
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted = self.intra_chunk_smoother.process(timestamps, action_chunk)
            # action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted = self._traj_fitting(num_samples=self.config.intra_chunk.fitting_num_samples)

            # Record control timestamp
            self.rdm.set_control_time_marker()
            target_chunk_index = self.rdm.get_start_chunk_index(timestamps_fitted)
            # joint_indices = self.rdm._get_joint_indices(action_chunk_fitted)
            # step_indices = self.rdm._get_step_indices(action_chunk_fitted)
            # currt_action, currt_vel, currt_acc = self.rdm.get_current_state()
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
            self.rdm.update_action_chunk_fitted_1(
                action_chunk_smoothed=action_chunk_smoothed,
                vel_chunk_smoothed=vel_chunk_smoothed,
                acc_chunk_smoothed=acc_chunk_smoothed,
                timestamps_smoothed=timestamps_fitted,
                target_chunk_index=target_chunk_index,
            )
            # self.rdm.update_action_chunk_fitted(action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted)

            # Compute average inference and trajectory fitting times
            self.rdm.compute_avg_infer_time()
            self.rdm.compute_avg_traj_time()
            
        # Re-enable automatic language switching
        # self.language = saved_language
        self.allow_language_switch = True
    
    # @run_time_decorator
    def inference_step(self):
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
        data = self.rdm.pop_observe_data(num_samples = 1 if not self.config.vision.history_frame else 2)
        # print(f"data keys: {data.keys() if data is not None else None}, infer_count: {self.rdm.infer_count}")
        if data is not None:
            # Record inference start timestamp
            self.rdm.set_infer_time_marker()
            
            # Send data for inference and wait for results
            result = self._request_inference(data, timeout_ms=500)
            if result is None or 'data' not in result:
                return
            self.rdm.add_infer_count()
            action_data = result['data']
            
            # Get current data timestamp and update timestamps
            action_chunk, timestamp_chunk, loc_timestamp = self._process_action_chunk(action_data)
            self.rdm.set_observe_time_marker(loc_timestamp)
            self.vis_idx_count = 0
            self.vis_origin_chunk_action = action_chunk
            
            # Add action data (thread-safe function, no lock needed)
            self.rdm.update_action_chunk_raw(action_chunk, timestamp_chunk)

            # Record trajectory fitting timestamp
            self.rdm.set_traj_time_marker()

            timestamps, action_chunk = self.rdm.pop_action_chunk(time_offset=0.0)
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted = self.intra_chunk_smoother.process(timestamps, action_chunk)
            # action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted = self._traj_fitting(num_samples=self.config.intra_chunk.fitting_num_samples)

            # Record control timestamp
            self.rdm.set_control_time_marker()
            
            # Get prob_progress from action data if available
            # TODO: fix language command auto change
            prob_progress = None
            if 'ext' in action_data and 'prob_progress' in action_data['ext']:
                prob_progress = action_data['ext']['prob_progress']
                # Check if prob_progress length > 1 to enable alignment processing
                if not (isinstance(prob_progress, np.ndarray) and len(prob_progress) > 1):
                    self.info_act['current_prob_progress'] = prob_progress
                    if prob_progress >= self.config.language.task_progress_threshold and self.allow_language_switch and self.config.language.auto_mode:
                        self._advance_language_subtask()
                    prob_progress = None
                else:
                    # prob_progress: (64,), interplot prob_progress to (420,)
                    original_len, target_len = len(prob_progress), action_chunk_fitted.shape[1]
                    x_original, x_target = np.linspace(0, 1, original_len), np.linspace(0, 1, target_len)
                    interp_func = interp1d(x_original, prob_progress, kind='linear', fill_value='extrapolate')
                    prob_progress = interp_func(x_target)

            target_chunk_index = self.rdm.get_start_chunk_index(timestamps_fitted)
            joint_indices = self.rdm._get_joint_indices(action_chunk_fitted)
            step_indices = self.rdm._get_step_indices(action_chunk_fitted)
            currt_action, currt_vel, currt_acc = self.rdm.get_current_state()
            action_chunk_smoothed, vel_chunk_smoothed, acc_chunk_smoothed, target_chunk_index = self.inter_chunk_fuser.process(
                next_action_chunk=action_chunk_fitted,
                next_vel_chunk=vel_chunk_fitted,
                next_acc_chunk=acc_chunk_fitted,
                next_timestamps=timestamps_fitted,
                target_chunk_index=target_chunk_index,
                currt_action=currt_action,
                currt_vel=currt_vel,
                currt_acc=currt_acc,
                joint_indices=joint_indices,
                step_indices=step_indices,
            )
            self.rdm.update_action_chunk_fitted_1(
                action_chunk_smoothed=action_chunk_smoothed,
                vel_chunk_smoothed=vel_chunk_smoothed,
                acc_chunk_smoothed=acc_chunk_smoothed,
                timestamps_smoothed=timestamps_fitted,
                target_chunk_index=target_chunk_index,
                prob_progress=prob_progress
            )
            # self.rdm.update_action_chunk_fitted(
            #     action_chunk_fitted,
            #     vel_chunk_fitted,
            #     acc_chunk_fitted,
            #     timestamps_fitted,
            #     prob_progress=prob_progress,
            #     inter_chunk_mode=self.config.inter_chunk.inter_chunk_mode,
            #     search_length=self.config.inter_chunk.search_length,
            #     smooth_action=self.config.inter_chunk.smooth_action,
            #     smooth_length=self.config.inter_chunk.smooth_length,
            #     smooth_base=self.config.inter_chunk.smooth_base,
            #     smooth_ratio=self.config.inter_chunk.smooth_ratio,
            #     gripper_offset=self.config.controller.gripper_offset,
            # )

            # Compute average inference and trajectory fitting times
            self.rdm.compute_avg_infer_time()
            self.rdm.compute_avg_traj_time()
        else:
            self.logger.warning("No observe data, skip inference.")

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

        action_fitted, action_raw, vel_fitted, acc_fitted = self.rdm.get_action_fitted()

        if action_fitted is not None:

            self.robot.control_robot(action_fitted)

            # tmp data buffer writing
            if self.config.record_exp_data:
                self.act_write_buffer.append(action_fitted)
                self.vel_write_buffer.append(vel_fitted)
                self.acc_write_buffer.append(acc_fitted)

            with self.vis_action_lock:
                if self.config.show_action_cams_qt:
                    self.act_exe_fitted_buffer.append(action_fitted)
                    self.act_exe_raw_buffer.append(action_raw)
                    self.vel_exe_fitted_buffer.append(vel_fitted)
                    self.acc_exe_fitted_buffer.append(acc_fitted)

            self.info_current_action = action_fitted.tolist() if hasattr(action_fitted, 'tolist') else list(action_fitted)
            
            # Only use alignment processing if prob_progress array length > 1
            prob_progress = self.rdm.get_prob_progress()
            if prob_progress is not None:
                self.info_act['current_prob_progress'] = prob_progress

            if self.config.record.switch and self.is_control_thread_running and self.is_running:
                self.dataset_write.async_write_action(action_fitted, time.perf_counter())
            
            self.info_act['action'] = action_fitted.shape

        current_state = getattr(self.robot, 'current_state', None)
        self.vis_action_state(action_fitted, vel_fitted, acc_fitted, action_raw, current_state)

    # @run_time_decorator
    def _traj_fitting(self, num_samples):
        """Perform trajectory fitting for robot actions.
        
        This method retrieves action chunks from the real-time data manager,
        performs polynomial fitting using the trajectory generator to create
        smooth trajectories for robot control.
        
        Args:
            num_samples (int): Number of action samples to use for fitting
            
        Returns:
            tuple: A tuple containing:
                - action_chunk_fitted (np.ndarray): Fitted action trajectory
                - vel_chunk_fitted (np.ndarray): Fitted velocity trajectory  
                - timestamps_fitted (np.ndarray): Corresponding timestamps
        """
        timestamps, action_chunk = self.rdm.pop_action_chunk(time_offset=0.0)
        self.logger.debug(f'timestamps for fitting: {timestamps[::10]}')
        
        start_time = timestamps[0]
        end_time = timestamps[-1]
        
        if self.config.intra_chunk.intra_chunk_mode == 'raw':
            action_chunk_fitted = action_chunk
            vel_chunk_fitted = np.zeros_like(action_chunk)
            acc_chunk_fitted = np.zeros_like(action_chunk)
            timestamps_fitted = timestamps  # original sparse timestamps
        elif self.config.intra_chunk.intra_chunk_mode == 'interpolation':
            # Use CubicSpline interpolation for sparse raw chunks
            action_chunk = np.asarray(action_chunk)
            timestamps = np.asarray(timestamps)
            
            # Create dense timestamps for interpolation
            time_step = self.config.intra_chunk.fitting_time_step / 1000  # convert ms to seconds
            timestamps_fitted = np.arange(start_time, end_time, time_step)
            
            # Interpolate each joint dimension using CubicSpline
            n_joints = action_chunk.shape[0]
            action_chunk_fitted = np.zeros((n_joints, len(timestamps_fitted)))
            vel_chunk_fitted = np.zeros((n_joints, len(timestamps_fitted)))
            acc_chunk_fitted = np.zeros((n_joints, len(timestamps_fitted)))
            
            step_index_set = set(self.step_indices)
            for j in range(n_joints):
                # Gripper and head dimensions use zero-order hold interpolation (step-like)
                if j in step_index_set:
                    interp_func = interp1d(timestamps, action_chunk[j], kind='previous', bounds_error=False, fill_value='extrapolate')
                    action_chunk_fitted[j] = interp_func(timestamps_fitted)
                    vel_chunk_fitted[j] = np.zeros(len(timestamps_fitted))
                    acc_chunk_fitted[j] = np.zeros(len(timestamps_fitted))
                    continue
                cs = CubicSpline(timestamps, action_chunk[j])
                action_chunk_fitted[j] = cs(timestamps_fitted)
                vel_chunk_fitted[j] = cs(timestamps_fitted, 1)  # 1st derivative
                acc_chunk_fitted[j] = cs(timestamps_fitted, 2)  # 2nd derivative
        else:  # fit mode (default)
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted = self.intra_chunk_smoother._traj_fitting(
                timestamps=timestamps, 
                action_chunk=action_chunk, 
                start_time=start_time, 
                end_time=end_time, 
                # deg=self.config.intra_chunk.fitting_deg, 
                # time_step=self.config.intra_chunk.fitting_time_step / 1000
            )
        return action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted

    def _process_image(self, key, value):
        """Process image data by padding, resize and encoding.

        Args:
            key (str): Image key identifier.
            value (np.ndarray): Raw image data from robot sensors.

        Returns:
            tuple: A tuple containing:
                - key (str): Original image key
                - img_processed (np.ndarray): Preprocessed image data
                - img_encoded (np.ndarray): Encoded image data for transmission
        """
        ext = '.png' if 'depth.' in key else '.jpg'
        img_processed = self._preprocess_func(value) if self._preprocess_func else value
        img_encoded = cv2.imencode(ext, img_processed)[1]
        return key, img_processed, img_encoded

    def _thread_process_image(self, frame):
        """Process multiple images in threads.

        Args:
            frame (dict): A dictionary containing observation data, including image data, proprioception state data.

        Returns:
            dict: The encoded images with key and values.
        """
        cam_items = [(key, value) for key, value in frame.items() if 'cam.' in key]
        # Use thread pool to parallel process all cameras
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self._process_image, key, value) for key, value in cam_items]
            results = [future.result() for future in futures] # Wait for all tasks to complete
        encoded_imgs, processed_imgs = {}, {}
        for key, processed, encoded in results:
            encoded_imgs[key] = encoded
            processed_imgs[key] = processed

        # Send images to visualization interface
        self.visualization_server.update_image_data(processed_imgs)

        return encoded_imgs

    # @run_time_decorator
    def _process_data(self, frame):
        """Process observation data by adding local timestamp, encoding images and adding task name.

        Args:
            frame (dict): A dictionary containing observation data, including image data, proprioception state data.

        Returns:
            dict: The processed data by encoding images and adding local timestamp.
        """
        loc_timestamp = time.perf_counter()
        encoded_imgs = self._thread_process_image(frame)
        
        if 'obs.state' in frame and frame['obs.state'] is not None:
            self.info_current_state = frame['obs.state'].tolist() if hasattr(frame['obs.state'], 'tolist') else list(frame['obs.state'])

        self.info_obs['state'] = frame['obs.state'].shape
        data = {
            'type': 'vla_obs',
            'ref_timestamp': frame['ref_timestamp'],
            'loc_timestamp': loc_timestamp,
            'obs': {
                **encoded_imgs,
                'state': frame['obs.state'],
                'language': [self.language],
            },
        }
        return data

    @run_time_decorator
    def _process_action_chunk(self, action):
        """Process an action chunk by generating reference timestamp chunk and passing local timestamp.

        This method processes the inference result from the VLA server by:
        - Extracting predicted actions and timestamps
        - Handling language instruction switching based on progress
        - Generating timestamp chunks for trajectory control
        - Validating action type and format

        Args:
            action (dict): The inference result from vla_server. It is a dictionary with keys 
                          i.e. type, pred_action, ref_timestamp, loc_timestamps.

        Returns:
            tuple(list, list, int): A tuple containing:
                - action_chunk (list): The predicted action chunk
                - timestamp_chunk (list): Reference timestamp chunk
                - loc_timestamp (int): Local timestamp
        """
        action_chunk = []
        timestamp_chunk = []
        action_type = action['type']
        
        if action_type == 'vla_action':
            pred_action = action['pred_action']
            ref_timestamp = action['ref_timestamp']
            loc_timestamp = action['loc_timestamp']
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
        if not self.control_thread_timer._thread.is_alive():
            self.control_thread_timer.start()

    def stop_control(self):
        self.is_control_thread_running = False

    def start_visualize(self):
        self.visualization_server.run()
    def stop_visualize(self):
        self.visualization_server.stop_server()

    def run(self):
        """Start the VLA client and all associated threads.

        This method initializes and starts the observation, control, and inference
        threads for real-time robot operation. It uses thread locks to ensure
        thread-safe startup and begins the main control loop.
        """
        with self.thread_lock:
            self.is_running = True

        self.start_observe()
        self.start_inference()
        self.start_control()
        self.start_visualize()

        if self.config.show_action_cams_qt:
            self.vis_action_cams_thread.start()

        if self.config.record_exp_data:
            self.data_write_thread.start()

        self.logger.info('VLA client started.')

    def pause(self):
        """Pause observation, inference and control without releasing resources."""
        self.stop_observe()
        self.stop_inference()
        self.stop_control()
        self.logger.info('VLA client paused.')

    def resume(self):
        """Resume observation, inference and control."""
        if self.is_observe_thread_running and self.is_inference_thread_running and self.is_control_thread_running:
            return
        # self.inference_first()
        self.start_observe()
        self.start_inference()
        self.start_control()
        self.logger.info('VLA client resumed.')

    def stop(self):
        """Backward-compatible alias of pause()."""
        self.pause()

    def close(self):
        """Close the VLA client and clean up all resources.
        
        This method performs a complete shutdown of the VLA client by:
        - Stopping all running threads with timeouts
        - Closing dataset recording if enabled
        - Closing ZMQ client connections
        - Stopping visualization components
        - Cleaning up all allocated resources
        """
        with self.thread_lock:
            self.is_running = False
        
        if self.observe_thread.is_alive():
            self.observe_thread.join(timeout=1.0)
        if self.inference_thread.is_alive():
            self.inference_thread.join(timeout=1.0)

        if self.config.show_action_cams_qt and self.vis_action_cams_thread.is_alive():
            self.vis_action_cams_thread.join(timeout=1.0)

        if self.config.record_exp_data and self.data_write_thread.is_alive():
            self.data_write_thread.join(timeout=1.0)

        # Stop and join control thread timer
        if self.control_thread_timer._thread.is_alive():
            self.control_thread_timer.stop()
            self.control_thread_timer.join(timeout=1.0)
        
        if self.config.record.switch:
            time.sleep(1)
            self.dataset_write.close()
        
        self.vla_zmq.close()
        if self.config.show_action_cams_qt:
            try:
                self.vis_action_cams_zmq.close()
            except Exception:
                pass
        self.visualization_server.stop_server()

        # close file IO writer
        if self.config.record_exp_data:
            for f in self.files.values():
                f.close()

        self.logger.info('Inference client closed.')

    def _inference_thread_fun(self):
        while self.is_running:
            if not self.is_inference_thread_running:
                time.sleep(0.001)
                continue

            if self.rdm.infer_count == 0:
                self.inference_first()
                # time.sleep(self.config.controller.wait_time/1000)
                self.rdm.wait_for_next(mode='async', wait_time=self.config.controller.wait_time/1000)
                # self.rdm.wait_for_next(mode='sync', wait_time=self.config.controller.wait_time/1000)
            else:
                self.inference_step()
                # self.inferenceFirstThreadFun()
                # time.sleep(self.config.controller.wait_time/1000)
                self.rdm.wait_for_next(mode='async', wait_time=self.config.controller.wait_time/1000)
                # self.rdm.wait_for_next(mode='sync', wait_time=self.config.controller.wait_time/1000)
            # print(f'\rInference count: {self.rdm.infer_count}, current infer time: {self.rdm.start_traj_marker-self.rdm.start_infer_marker:.4f}s, current traj time: {self.rdm.start_ctrl_marker-self.rdm.start_traj_marker:.4f}s', end='', flush=True)
            # symbol = '=' * 10

    def vis_action_state(self, action_fitted, vel_fitted, acc_fitted, action_raw, current_state):
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
        action_np = np.asarray(action_fitted) if action_fitted is not None else None
        action_vel = np.asarray(vel_fitted) if vel_fitted is not None else None
        action_acc = np.asarray(acc_fitted) if acc_fitted is not None else None
        state_np = np.asarray(current_state) if current_state is not None else None

        # Control period in seconds
        dt_ctrl = self.config.controller.period / 1000.0

        list_data = []

        # Position data
        if action_np is not None:
            list_data.append({
                'tab': 'position',
                'type': 'action_fitted',
                'x': self.vis_global_step,
                'joints_y': action_np.tolist()
            })
        if state_np is not None:
            list_data.append({
                'tab': 'position',
                'type': 'state',
                'x': self.vis_global_step,
                'joints_y': state_np.tolist()
            })

        # Velocity/acceleration for state (derived from state)
        state_vel = None
        state_acc = None
        if state_np is not None:
            if self.vis_prev_state is None:
                state_vel = np.zeros_like(state_np)
                state_acc = np.zeros_like(state_np)
            else:
                state_vel = (state_np - self.vis_prev_state) / dt_ctrl
                if self.vis_prev_state_vel is None:
                    state_acc = np.zeros_like(state_np)
                else:
                    state_acc = (state_vel - self.vis_prev_state_vel) / dt_ctrl

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
        if action_vel is not None:
            list_data.append({
                'tab': 'velocity',
                'type': 'action_fitted',
                'x': self.vis_global_step,
                'joints_y': action_vel.tolist()
            })
        if action_acc is not None:
            list_data.append({
                'tab': 'acceleration',
                'type': 'action_fitted',
                'x': self.vis_global_step,
                'joints_y': action_acc.tolist()
            })

        # Origin (raw action) series
        origin_idx = self.vis_idx_count // int(self.vis_ratio) + 4
        has_origin_chunk = self.vis_origin_chunk_action is not None
        if action_raw is not None and has_origin_chunk and (self.vis_idx_count % int(self.vis_ratio) == 0 and origin_idx < len(self.vis_origin_chunk_action)):
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
            self.vis_prev_origin_idx = origin_idx

        if list_data:
            self.visualization_server.update_chart_data(list_data)
            self.vis_global_step += 1
            self.vis_idx_count += 1

        # Update previous values only for available inputs
        if action_np is not None:
            self.vis_prev_action = action_np
        if action_vel is not None:
            self.vis_prev_action_vel = action_vel
        if state_np is not None:
            self.vis_prev_state = state_np
        if state_vel is not None:
            self.vis_prev_state_vel = state_vel

    def send_action_cams_to_vis_server(self):
        """
        This method sends actions and camera images to
        the visualization system via ZMQ.
        """
        while self.is_running:

            if self.config.show_action_cams_qt:

                with self.vis_action_lock:
                    current_actions_fitted = self.act_exe_fitted_buffer.copy()
                    current_actions_raw = self.act_exe_raw_buffer.copy()
                    # self.act_exe_fitted_buffer.clear()
                    # self.act_exe_raw_buffer.clear()

                data = self.rdm.read_observe_data()
    
                if data is not None:
                    data['actions_fitted'] = current_actions_fitted
                    data['actions_raw'] = current_actions_raw
                    #============= sending to action-camera visualization server ================
                    try:
                        self.vis_action_cams_zmq.sendMessage(data)
                    except zmq.Again:
                        print("Send failed, action-camera visualization server probably offline")

            time.sleep(0.02)
    def _writer_thread(self):
        while self.is_running:
            # print("_writer_thread")
            if not self.act_write_buffer:
                time.sleep(0.001)
                continue
            else:
                af = self.act_write_buffer.popleft()
                vf = self.vel_write_buffer.popleft()
                ac = self.acc_write_buffer.popleft()

            # Ensure they are numpy arrays
            af = np.asarray(af)
            vf = np.asarray(vf)
            ac = np.asarray(ac)

            # Flatten into a single line for writing to each file
            line_af = ','.join(f'{x:.6f}' for x in af) + '\n'
            line_vf = ','.join(f'{x:.6f}' for x in vf) + '\n'
            line_ac = ','.join(f'{x:.6f}' for x in ac) + '\n'

            self.files['action'].write(line_af)
            self.files['velocity'].write(line_vf)
            self.files['acceleration'].write(line_ac)

if __name__ == "__main__":
    pass
