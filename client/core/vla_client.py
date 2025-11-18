import cv2
import time
import threading
import logging
import numpy as np
from ml_collections import ConfigDict

from concurrent.futures import ThreadPoolExecutor

from client.utils import misc
from client.utils.util import run_time_decorator
from client.utils.multi_thread_timer import MultiThreadTimer
from client.core.zmq_client import ZMQClient
from client.core.trajectory_generator import TrajectoryGenerator
from client.core.realtime_data_manager import RealtimeDataManager
from client.core.save_lerobot import LeRobotDatasetWriter
from visual.websocket_server import VLAWebSocketServer

class VLAClient():
    """VLA (Vision-Language-Action) Client for real-time robot control.
    
    This class manages the complete pipeline for VLA-based robot control, including:
    - Observation data collection from robot sensors
    - Communication with VLA inference server
    - Trajectory generation and fitting
    - Real-time robot control
    - Data recording for dataset creation
    """
    def __init__(self, config: ConfigDict, rdm: RealtimeDataManager, traj_generator: TrajectoryGenerator, zmq_client: ZMQClient, robot: None):
        """Initialize the VLA Client.
        
        Args:
            config (ConfigDict): Configuration dictionary containing all system parameters
            rdm (RealtimeDataManager): Real-time data manager for handling observation and action data
            traj_generator (TrajectoryGenerator): Trajectory generator for action smoothing and fitting
            zmq_client (ZMQClient): ZMQ client for communication with VLA inference server
            robot: Robot interface for observation collection and action execution
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.config.observer.period = 1.0 / self.config.observer.fps
        self.rdm = rdm
        self.traj_generator = traj_generator
        self.zmq_client = zmq_client
        self.robot = robot
        self.running = False
        self.is_running_action = True
        self.language = self.config.language[0]
        self.allow_language_switch = True  # Flag to control automatic language switching
        
        # Define image preprocess function
        if self.config.preprocess != 'none':
            preprocess_func = getattr(misc, self.config.preprocess)
            height, width = self.config.preprocess_size
            self._preprocess_func = lambda img: preprocess_func(img, target_height=height, target_width=width)
        else:
            self._preprocess_func = None

        self.observe_thread = threading.Thread(target=self._observe_thread_fun, daemon=True)
        self.inference_thread = threading.Thread(target=self._inference_thread_fun, daemon=True)
        self.control_thread_timer = MultiThreadTimer(self.config.controller.period, self._control_thread_fun)
        
        self.thread_lock = threading.Lock()
        self.show_thread_lock = threading.Lock()
        
        # Inference variables
        self.infer_count = 0
        self.infer_flag = False
        self.wait_frame_count = 0
        self.infer_thread_lock = threading.Lock()

        if self.config.record.switch:
            # Initialize the dataset writer with the provided recording configuration
            self.dataset_write = LeRobotDatasetWriter(record_config=self.config.record)

        # Create Visualization WebSocket server
        self.websocket_server = VLAWebSocketServer.get_instance()
        self.vis_global_step = 0
        self.vis_idx_count = 0
        self.vis_origin_chunk_action = None
        self.vis_ratio = (1.0 / self.config.observer.fps) / (self.config.fitting_time_step / 1000.0) # (64 - 1) * ratio -> 420
        self.vis_prev_action, self.vis_prev_state, self.vis_prev_origin = None, None, None
        self.vis_prev_action_vel, self.vis_prev_state_vel, self.vis_prev_origin_vel = None, None, None
        self.vis_prev_origin_idx = None

        # Information for monitoring current action and state (left arm 7 + right arm 7 + left gripper 1 + right gripper 1)
        self.info_current_action = [0.0] * 16
        self.info_current_state = [0.0] * 16
        self.info_obs, self.info_act = {}, {}
        self.debug_info = 'The debug information or trace information will be displayed here. \nPress "Enter" for more commands.'

    def _observe_thread_fun(self):
        """Observation thread function for continuous data collection from robot sensors.
        
        This method runs in a separate thread and continuously:
        - Retrieves observations from the robot
        - Processes the observation data
        - Adds processed data to the real-time data manager
        - Records data if recording is enabled
        """
        while self.running:
            if not self.is_running_action:
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
        
        # Clear action data to ensure fresh action retrieval
        self.rdm.clear_action_data()
        # Wait for observation changes after reset, then retrieve fresh obs for inference
        observations = self.robot.retrieve_observation()
        if observations is not None:
            data = self._process_data(observations)
            self.rdm.add_observe_data(data)
        # time.sleep(self.config.sleep_time_after_reset)
        
        # Get observation data (thread-safe function, no lock needed)
        data = self.rdm.pop_observe_data(num_samples = 1 if not self.config.history_frame else 2)
        if data is not None:
            # Record inference start timestamp for control timestamp updates
            self.rdm.set_infer_time_marker()
            self.rdm.add_infer_count()
            
            # Send data for inference and wait for results
            self.zmq_client.sendMessage(data)
            result = self.zmq_client.recvMessage()
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
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted = self._traj_fitting(num_samples=self.config.fitting_num_samples)

            # Record control timestamp
            self.rdm.set_control_time_marker()
            self.rdm.update_action_chunk_fitted(action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted, chunk_trans_mode=self.config.chunk_trans_mode)

            # Compute average inference and trajectory fitting times
            self.rdm.compute_avg_infer_time()
            self.rdm.compute_avg_traj_time()
            
        # Re-enable automatic language switching
        # self.language = saved_language
        self.allow_language_switch = True
    
    @run_time_decorator
    def inference_step(self):
        """Regular inference step for continuous VLA inference.
        
        This method performs regular inference steps after the first inference:
        - Retrieves observation data from the data manager
        - Sends data to VLA server for inference
        - Processes the returned action predictions
        - Updates trajectory fitting with smoothing and search options
        - Computes timing statistics
        """
        if not self.is_running_action:
            return
        
        # Get observation data (thread-safe function, no lock needed)
        data = self.rdm.pop_observe_data(num_samples = 1 if not self.config.history_frame else 2)
        if data is not None:
            # Record inference start timestamp
            self.rdm.set_infer_time_marker()
            self.rdm.add_infer_count()
            
            # Send data for inference and wait for results
            self.zmq_client.sendMessage(data)
            result = self.zmq_client.recvMessage()
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
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted = self._traj_fitting(num_samples=self.config.fitting_num_samples)

            # Record control timestamp
            self.rdm.set_control_time_marker()
            
            # Get prob_progress from action data if available
            prob_progress = None
            if 'ext' in action_data and 'prob_progress' in action_data['ext']:
                prob_progress = action_data['ext']['prob_progress']
                # Check if prob_progress length > 1 to enable alignment processing
                if not (isinstance(prob_progress, np.ndarray) and len(prob_progress) > 1):
                    self.info_act['current_prob_progress'] = prob_progress
                    if prob_progress >= self.config.thre_prob_progress and self.allow_language_switch:
                        self.language = self.config.language[(self.config.language.index(self.language) + 1) % len(self.config.language)]
                    prob_progress = None
            self.rdm.update_action_chunk_fitted(action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted, prob_progress=prob_progress, search_action=self.config.search_action, search_length=self.config.search_length, smooth_action=self.config.smooth_action, smooth_length=self.config.smooth_length, gripper_offset=self.config.gripper_offset, chunk_trans_mode=self.config.chunk_trans_mode)

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
        if not self.is_running_action:
            return

        action = self.rdm.get_action_fitted()
        if action is not None:
            self.info_current_action = action.tolist() if hasattr(action, 'tolist') else list(action)
            
            # Only use alignment processing if prob_progress array length > 1
            prob_progress = self.rdm.get_prob_progress()
            if prob_progress is not None:
                self.info_act['current_prob_progress'] = prob_progress

            if self.config.record.switch and self.is_running_action and self.running:
                self.dataset_write.async_write_action(action, time.perf_counter())
            
            self.info_act['action'] = action.shape
            self.robot.control_robot(action)
            
            self.vis_action_state(action)

    @run_time_decorator
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
        timestamps, action_chunk = self.rdm.pop_action_chunk(time_offset=0.0, num_samples=num_samples)
        self.logger.debug(f'timestamps for fitting: {timestamps[::10]}')
        
        start_time = timestamps[0]
        end_time = timestamps[-1]
        action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted = self.traj_generator.traj_fitting(
            timestamps=timestamps, 
            action_chunk=action_chunk, 
            start_time=start_time, 
            end_time=end_time, 
            deg=self.config.fitting_deg, 
            time_step=self.config.fitting_time_step/1000
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
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, 80]
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
            self.info_obs[key] = processed.shape
            processed_imgs[key] = processed
        # Send images to visualization interface
        self.websocket_server.update_image_data(processed_imgs)
        return encoded_imgs

    @run_time_decorator
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

    def run(self):
        """Start the VLA client and all associated threads.
        
        This method initializes and starts the observation, control, and inference
        threads for real-time robot operation. It uses thread locks to ensure
        thread-safe startup and begins the main control loop.
        """
        with self.thread_lock:
            self.running = True
    
        # Start threads
        self.observe_thread.start()
        self.inference_thread.start()
        self.control_thread_timer.start()
        self.websocket_server.run()
        
        self.logger.info('Inference client started.')
    
    def stop(self):
        """Stop the VLA client and wait for threads to finish.
        
        This method safely stops the VLA client by setting the running flag to False
        and waiting for the observation and control threads to finish with a timeout.
        The inference thread continues running for potential future operations.
        """
        with self.thread_lock:
            self.running = False
        self.observe_thread.join(timeout=1.0)
        self.control_thread_timer.join(timeout=1.0)
        self.logger.info('Inference client stopped.')

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
            self.running = False
        
        self.observe_thread.join(timeout=1.0)
        self.inference_thread.join(timeout=1.0)
        
        # Stop and join control thread timer
        self.control_thread_timer.stop()
        self.control_thread_timer.join(timeout=1.0)
        
        if self.config.record.switch:
            time.sleep(1)
            self.dataset_write.close()
        
        self.zmq_client.close()
        self.websocket_server.stop_server()
        
        self.logger.info('Inference client closed.')

    def _inference_thread_fun(self):
        while self.running:
            if self.rdm.infer_count == 0:
                self.inference_first()
                # time.sleep(self.config.controller.wait_step * self.config.controller.control_period/1000)
                time.sleep(self.config.sleep_time)
            else:
                self.inference_step()
                # self.inferenceFirstThreadFun()
                time.sleep(self.config.sleep_time)
            # print(f'\rInference count: {self.rdm.infer_count}, current infer time: {self.rdm.start_traj_marker-self.rdm.start_infer_marker:.4f}s, current traj time: {self.rdm.start_ctrl_marker-self.rdm.start_traj_marker:.4f}s', end='', flush=True)
            symbol = '=' * 10

    def vis_action_state(self, action):
        """
        Visualize action and state data for debugging and monitoring.
        
        Args:
            action: Predicted action values for robot joints
        """
        list_data = [{
                'tab': 'position',
                'type': 'action',
                'x': self.vis_global_step,
                'joints_y': action.tolist()
            }, {
                'tab': 'position',
                'type': 'state',
                'x': self.vis_global_step,
                'joints_y': self.robot.current_state.tolist()
            }]
        action_np = np.asarray(action)
        state_np = np.asarray(self.robot.current_state)
        dt_ctrl = self.config.controller.period / 1000.0

        if self.vis_prev_action is None:
            action_vel = np.zeros_like(action_np)
            action_acc = np.zeros_like(action_np)
        else:
            action_vel = (action_np - self.vis_prev_action) / dt_ctrl
            if self.vis_prev_action_vel is None:
                action_acc = np.zeros_like(action_np)
            else:
                action_acc = (action_vel - self.vis_prev_action_vel) / dt_ctrl

        if self.vis_prev_state is None:
            state_vel = np.zeros_like(state_np)
            state_acc = np.zeros_like(state_np)
        else:
            state_vel = (state_np - self.vis_prev_state) / dt_ctrl
            if self.vis_prev_state_vel is None:
                state_acc = np.zeros_like(state_np)
            else:
                state_acc = (state_vel - self.vis_prev_state_vel) / dt_ctrl

        list_data.extend([
            {
                'tab': 'velocity',
                'type': 'action',
                'x': self.vis_global_step,
                'joints_y': action_vel.tolist()
            },
            {
                'tab': 'velocity',
                'type': 'state',
                'x': self.vis_global_step,
                'joints_y': state_vel.tolist()
            },
            {
                'tab': 'acceleration',
                'type': 'action',
                'x': self.vis_global_step,
                'joints_y': action_acc.tolist()
            },
            {
                'tab': 'acceleration',
                'type': 'state',
                'x': self.vis_global_step,
                'joints_y': state_acc.tolist()
            },
        ])

        origin_idx = self.vis_idx_count // int(self.vis_ratio) + 4
        if (self.vis_idx_count % int(self.vis_ratio) == 0 and origin_idx < len(self.vis_origin_chunk_action)):
            origin_np = np.asarray(self.vis_origin_chunk_action[origin_idx])
            list_data.append({
                'tab': 'position',
                'type': 'origin',
                'x': self.vis_global_step,
                'joints_y': origin_np.tolist()
            })
            if self.vis_prev_origin_idx is None:
                dt_origin = self.config.observer.period
            else:
                delta_idx = origin_idx - self.vis_prev_origin_idx
                dt_origin = max(delta_idx, 1) * (self.config.fitting_time_step / 1000.0)
            if self.vis_prev_origin is None:
                origin_vel = np.zeros_like(origin_np)
                origin_acc = np.zeros_like(origin_np)
            else:
                origin_vel = (origin_np - self.vis_prev_origin) / dt_origin
                if self.vis_prev_origin_vel is None:
                    origin_acc = np.zeros_like(origin_np)
                else:
                    origin_acc = (origin_vel - self.vis_prev_origin_vel) / dt_origin

            list_data.extend([
                {
                    'tab': 'velocity',
                    'type': 'origin',
                    'x': self.vis_global_step,
                    'joints_y': origin_vel.tolist()
                },
                {
                    'tab': 'acceleration',
                    'type': 'origin',
                    'x': self.vis_global_step,
                    'joints_y': origin_acc.tolist()
                }
            ])
            self.vis_prev_origin = origin_np
            self.vis_prev_origin_vel = origin_vel
            self.vis_prev_origin_idx = origin_idx

        self.vis_prev_action = action_np
        self.vis_prev_action_vel = action_vel
        self.vis_prev_state = state_np
        self.vis_prev_state_vel = state_vel
        self.websocket_server.update_chart_data(list_data)
        self.vis_global_step += 1
        self.vis_idx_count += 1
        
if __name__ == "__main__":
    pass
