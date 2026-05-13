import cv2
import os
import json
import time
from datetime import datetime
import threading
import logging
import numpy as np
from ml_collections import ConfigDict
from collections import deque

from concurrent.futures import ThreadPoolExecutor

from client.utils import misc
from client.utils.util import run_time_decorator, get_action_layout_info
from client.utils.multi_thread_timer import MultiThreadTimer
from client.core.zmq_client import ZMQClient
from client.core.intra_chunk_smoother import IntraChunkSmoother
from client.core.realtime_data_manager import RealtimeDataManager
from client.core.save_lerobot import LeRobotDatasetWriter
from visual.websocket_server import VLAWebSocketServer


class VLAClientSync():
    """VLA (Vision-Language-Action) Client [Synchronous Policy Inference] for real-time robot control.
    
    This class manages the complete pipeline for VLA-based robot control, including:
    - Observation data collection from robot sensors
    - Communication with VLA inference server
    - Real-time robot control
    - Data recording for dataset creation
    """
    def __init__(self, config: ConfigDict, rdm: RealtimeDataManager, intra_chunk_smoother: IntraChunkSmoother, vla_zmq_client: ZMQClient, robot: None):
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
        self.config.observer.period = 1.0 / 30  # The teleoperation imaging frequency is 30 fps
        self.rdm = rdm
        if self.config.inter_chunk.inter_chunk_mode == 'sync':
            self.rdm.sync_running = True
            self.action_length = None
        self.intra_chunk_smoother = intra_chunk_smoother
        self.vla_zmq = vla_zmq_client
        self.robot = robot
        self.action_layout = dict(self.config.action_layout) if hasattr(self.config, 'action_layout') else {}
        self.action_dim, self.joint_indices, self.step_indices = get_action_layout_info(self.action_layout)
        self.running = False
        self.is_running_action = True
        self.action_count = 0
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
        self.control_thread_timer = MultiThreadTimer((1.0/30)*1000, self._control_thread_fun)   # The teleoperation imaging frequency is 30 fps ( 33.33ms = 1s / 30fps)
        
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

        if self.config.record.switch:
            # Initialize the dataset writer with the provided recording configuration
            self.dataset_write = LeRobotDatasetWriter(record_config=self.config.record)

        # Create Visualization WebSocket server
        self.websocket_server = VLAWebSocketServer.get_instance()
        camera_cfg = getattr(getattr(self.config, 'visual', None), 'camera', None)
        if camera_cfg is not None:
            self.websocket_server.update_camera_open_config(camera_cfg)
        self.vis_global_step = 0
        self.vis_idx_count = 0
        self.vis_origin_chunk_action = None
        self.vis_ratio = (1.0 / self.config.observer.fps) / (self.config.intra_chunk.fitting_time_step / 1000.0) # (64 - 1) * ratio -> 420
        self.vis_prev_action, self.vis_prev_state, self.vis_prev_origin = None, None, None
        self.vis_prev_action_vel, self.vis_prev_state_vel, self.vis_prev_origin_vel = None, None, None
        self.vis_prev_origin_idx = None

        # The zmq client to communicate with action-state visualization server
        # if self.config.show_action_state:
        #    self.vis_action_state_zmq = vis_action_state.ZmqPlotClient()
        #    self.vis_chunk_idx = 0
        #    self.vis_global_step = 0

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
        target_path = file_path if os.path.isabs(file_path) else os.path.join(root_dir, file_path)
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
        if self.action_length is None or self.rdm.getCurrentActionIndex() == self.action_length - 1:
            pass
        else:
            return


        # Disable automatic language switching during reset (but don't save/restore language)
        # saved_language = self.language
        self.allow_language_switch = False
        
        # Wait for observation changes after reset, then retrieve fresh obs for inference
        observations = self.robot.retrieve_observation()
        if observations is not None:
            self.rdm.clear_action_data()
            data = self._process_data(observations)
            self.rdm.add_observe_data(data)
            # Clear action data to ensure fresh action retrieval
        # time.sleep(self.config.sleep_time_after_reset)
        
        # Get observation data (thread-safe function, no lock needed)
        data = self.rdm.pop_observe_data(num_samples = 1 if not self.config.vision.history_frame else 2)
        if data is not None:
            # Record inference start timestamp for control timestamp updates
            self.rdm.set_infer_time_marker()
            
            # Send data for inference and wait for results
            if not self.vla_zmq.sendMessage(data):
                return
            result = self.vla_zmq.recvMessage()
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
            action_chunk_fitted = np.vstack(action_chunk)
            action_chunk_fitted = action_chunk_fitted.T
            vel_chunk_fitted = np.zeros_like(action_chunk_fitted)
            acc_chunk_fitted = np.zeros_like(action_chunk_fitted)
            timestamps_fitted = np.array(timestamp_chunk)
            self.action_length = len(action_chunk)

            # Record control timestamp
            self.rdm.set_control_time_marker()
            self.rdm.update_action_chunk_fitted(action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted)

            # Compute average inference and trajectory fitting times
            self.rdm.compute_avg_infer_time()
            self.rdm.compute_avg_traj_time()
            
        # Re-enable automatic language switching
        # self.language = saved_language
        self.allow_language_switch = True
    

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
            self.action_count = 0
            return

        action_fitted, action_raw, vel_fitted, acc_fitted = self.rdm.get_action_fitted()

        if action_fitted is not None:
            
            self.robot.control_robot(action_fitted)

            # tmp data buffer writing
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

            if self.config.record.switch and self.is_running_action and self.running:
                self.dataset_write.async_write_action(action_fitted, time.perf_counter())
            
            self.info_act['action'] = action_fitted.shape
            
            self.vis_action_state(action_fitted, vel_fitted, acc_fitted, action_raw)

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
        self.websocket_server.update_image_data(processed_imgs)

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
            # pred_action = pred_action[:,0:16]
            # # temp = pred_action.copy()
            # # pred_action[:, 0:7] = temp[:, 7:14]
            # # pred_action[:, 7:14] = temp[:, 0:7]
            # # pred_action[:, 14] = temp[:, 15]
            # # pred_action[:, 15] = temp[:, 14]
            # # print(pred_action.shape)
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

        if self.config.show_action_cams_qt:
            self.vis_action_cams_thread.start()

        self.data_write_thread.start()
        
        self.logger.info('Inference client started.')
    
    def pause(self):
        """Pause inference and robot commands without releasing resources."""
        self.is_running_action = False
        self.logger.info('Inference client paused (inference and robot commands paused).')

    def resume(self):
        """Resume inference and robot commands."""
        if self.is_running_action:
            return
        # self.inference_first()
        self.is_running_action = True
        self.logger.info('Inference client resumed.')

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
            self.running = False
        
        self.observe_thread.join(timeout=1.0)
        self.inference_thread.join(timeout=1.0)

        if self.config.show_action_cams_qt:
            self.vis_action_cams_thread.join(timeout=1.0)

        self.data_write_thread.join(timeout=1.0)
        
        # Stop and join control thread timer
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
        self.websocket_server.stop_server()

        # close file IO writer
        for f in self.files.values():
            f.close()

        self.logger.info('Inference client closed.')

    def _inference_thread_fun(self):
        while self.running:
            if not self.is_running_action:
                time.sleep(0.001)
                continue

            self.inference_first()
            time.sleep(self.config.sleep_time)

            # print(f'\rInference count: {self.rdm.infer_count}, current infer time: {self.rdm.start_traj_marker-self.rdm.start_infer_marker:.4f}s, current traj time: {self.rdm.start_ctrl_marker-self.rdm.start_traj_marker:.4f}s', end='', flush=True)
            symbol = '=' * 10

    def vis_action_state(self, action_fitted, vel_fitted, acc_fitted, action_raw):
        """
        Visualize action and state data for debugging and monitoring.
        
        Args:
            action_fitted: Predicted action values for robot joints
            vel_fitted: Predicted velocity values (of action_fitted) for robot joints
            aacc_fittedction: Predicted acceleration values (of action_fitted) for robot joints
        """
        # # Update action_fitted velocity and acceleration ==================================================================
        list_data = [{
                'tab': 'position',
                'type': 'action_fitted',
                'x': self.vis_global_step,
                'joints_y': action_fitted.tolist()
            }, {
                'tab': 'position',
                'type': 'state',
                'x': self.vis_global_step,
                'joints_y': self.robot.current_state.tolist()
            }]
        action_np = np.asarray(action_fitted)
        action_vel = np.asarray(vel_fitted)
        action_acc = np.asarray(acc_fitted)

        # # Calculate robot state velocity and acceleration ==================================================================
        state_np = np.asarray(self.robot.current_state)
        dt_ctrl = self.config.controller.period / 1000.0

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
                'type': 'action_fitted',
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
                'type': 'action_fitted',
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

        # # Calculate action_raw velocity and acceleration ==================================================================
        origin_idx = self.vis_idx_count // int(self.vis_ratio) + 4
        if (self.vis_idx_count % int(self.vis_ratio) == 0 and origin_idx < len(self.vis_origin_chunk_action)):
            origin_np = np.asarray(action_raw)
            list_data.append({
                'tab': 'position',
                'type': 'action_raw',
                'x': self.vis_global_step,
                'joints_y': origin_np.tolist()
            })
            if self.vis_prev_origin_idx is None:
                dt_origin = self.config.observer.period
            else:
                delta_idx = origin_idx - self.vis_prev_origin_idx
                dt_origin = max(delta_idx, 1) * (self.config.intra_chunk.fitting_time_step / 1000.0)
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
                    'type': 'action_raw',
                    'x': self.vis_global_step,
                    'joints_y': origin_vel.tolist()
                },
                {
                    'tab': 'acceleration',
                    'type': 'action_raw',
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

    def send_action_cams_to_vis_server(self):
        """
        This method sends actions and camera images to
        the visualization system via ZMQ.
        """
        while self.running:

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
        while self.running:
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
