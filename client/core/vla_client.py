import cv2
import time
import threading
import logging
import numpy as np
from matplotlib  import pyplot as plt
from matplotlib.animation import FuncAnimation
from ml_collections import ConfigDict

from concurrent.futures import ThreadPoolExecutor

# from core.obs_robot import RobotObs
# from core.action_robot import RobotAction
# from client.robots.a2d import RobotA2D
# from ..robots.mock_a2d import RobotA2DMock
from client.utils import misc, vis
from client.utils.util import run_time_decorator, command_prompt
from client.utils.multi_thread_timer import MultiThreadTimer
from client.core.zmq_client import ZMQClient
from client.core.trajectory_generator import TrajectoryGenerator
from client.core.realtime_data_manager import RealtimeDataManager
from client.core.save_lerobot import LeRobotDatasetWriter
# from rich.live import Live

# try:
#     sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
#     from reset_robot import robot_a2d
# except ImportError:
#     print('导入tools模块出错')

# VLA客户端
class VLAClient():
    def __init__(self, config: ConfigDict, rdm: RealtimeDataManager, traj_generator: TrajectoryGenerator, zmq_client: ZMQClient, robot: None):
        self.logger = logging.getLogger(__name__)
        # self.live =  Live(command_prompt(), auto_refresh=False, screen=False)
        self.config = config
        self.config.observer.period = 1.0 / self.config.observer.fps
        self.rdm = rdm
        self.traj_generator = traj_generator
        self.zmq_client = zmq_client
        self.robot = robot
        self.running = False
        self.is_running_action = True
        self.language = self.config.language[0]
        
        # Define image preprocess function, i.e. pad and resize
        self._preprocess_func = (getattr(misc, self.config.preprocess) if self.config.preprocess != 'none' else None)

        self.observe_thread = threading.Thread(target=self._observe_thread_fun, daemon=True)
        # self.inference_thread = None
        self.inference_thread = threading.Thread(target=self._inference_thread_fun, daemon=True)
        # self.interpolate_thread = None
        # self.control_thread = threading.Thread(target=self.controlThreadFun, daemon=True)
        self.control_thread_timer = MultiThreadTimer(self.config.controller.period, self._control_thread_fun)
        
        self.thread_lock = threading.Lock()
        self.show_thread_lock = threading.Lock()
        # self.receive_callback = None
        
        # inference variables
        self.infer_count = 0
        self.infer_flag = False
        self.wait_frame_count = 0
        self.infer_thread_lock = threading.Lock()
        # record variables
        # self.record = config.record.switch

        if self.config.record.switch:
            # Initialize thread pool executors for concurrent observation and recording tasks
            self.record_obs_executor = ThreadPoolExecutor(max_workers=2)
            self.record_action_executor = ThreadPoolExecutor(max_workers=4)
            # Initialize the dataset writer with the provided recording configuration
            self.dataset_write = LeRobotDatasetWriter(record_config=self.config.record)

        if config.show_data:
            # 创建画布和折线图
            self.fig, self.axs = plt.subplots(2, 1, figsize=(10, 4))
            # print(self.axs)
            self.line = self.axs[0].plot([], [], 'b-', lw=1)
            self.line = self.axs[1].plot([], [], 'r-', lw=1)
            self.axs[0].set_ylabel('Joint Value')
            self.axs[0].set_xlabel('Time Step')
            self.axs[0].set_title('Predicted Action Chunk')
            self.axs[1].set_ylabel('Joint Value')
            self.axs[1].set_xlabel('Time Step')
            self.xdata = []
            self.ydata0 = []
            self.ydata1 = []
            # self.xdata = queue.Queue(maxsize=100)
            # self.ydata = queue.Queue(maxsize=100)
            # self.fig, self.ax = plt.subplots()
            # self.action_chunk = None
            # self.show_thread = threading.Thread(target=self.showThreadFun, daemon=True)
            # x_data, y_data = [], []
            # self.action_queue = queue.Queue(maxsize=1000)
        # self.set_receive_callback(self.receive_callback)
        # self.server_received_buffer = deque(maxlen=10)

        self.vis_zmq = vis.ZmqPlotClient()
        self.vis_chunk_idx = 0
        self.vis_global_step = 0
        self.debug_info = 'The debug information or trace information will be displayed here.'

    def async_write_obs(self,observations):
        """
        Asynchronously writes observation data into the dataset.

        Args:
            observations (dict):A dictionary containing observation with the following keys:
                - 'cam.*': np.ndarray,
                - 'obs.state': np.ndarray
        """
        self.dataset_write.add_obs(observations, self.language, time.perf_counter())

    def async_write_action(self,action):
        """
        Asynchronously writes action data into the dataset.

        Args:
            action (np.ndarray): A dictionary containing action data from the environment.
        """
        self.dataset_write.add_action(action, time.perf_counter())
    
    def _observe_thread_fun(self):
        # print('观测线程已启动...')
        while self.running:
            if not self.is_running_action:
                time.sleep(0.001)
                continue
            observations = self.robot.retrieve_observation()
            if observations is not None:
                # print(observations.keys())
                # print(observations['ref_timestamp'])
                # print(observations['obs.state'])
                if self.config.record.switch :
                    self.record_obs_executor.submit(self.async_write_obs, observations)
                data = self._process_data(observations)
                self.rdm.add_observe_data(data)
                # with self.infer_thread_lock:
                #     # infer_flag == False，表示当前没有推理任务，可以开始推理
                #     if self.infer_flag == False:
                #         if self.wait_frame_count < self.config.wait_frame:
                #             self.wait_frame_count += 1
                #         else:
                #             self.wait_frame_count = 0
                #             self.infer_flag = True
                #             # 开启推理线程，infer_count == 0，则开启首次推理
                #             if self.rdm.infer_count == 0:
                #                 self.inference_thread = threading.Thread(target=self.inferenceFirstThreadFun, daemon=True)
                #                 self.inference_thread.start()
                #             # infer_count > 0，则开启非
                #             elif self.rdm.infer_count < 10:
                #                 self.inference_thread = threading.Thread(target=self.inferenceStepThreadFun, daemon=True)
                #                 self.inference_thread.start()
            time.sleep(0.001)  # 控制循环频率
    
    @run_time_decorator
    def inference_first(self):
        """Fist inference step, which is different with other inference steps.
        """
        # getObserveData函数是线程安全的，不需要加锁
        data = self.rdm.pop_observe_data(num_samples = 1 if self.config.history_frame == False else 2)
        if data is not None:
            # 首次推理需要记录开始推理的时间戳，用于更新控制时间戳
            self.rdm.set_infer_time_marker()
            self.rdm.add_infer_count()
            # 首先发送数据进行推理,然后阻塞等待推理结果
            self.zmq_client.sendMessage(data)
            result = self.zmq_client.recvMessage()
            action_data = result['data']
            # print(result)
            # ref_timestamp = action_data['ref_timestamp']
            # print(f'当前动作时间戳: {ref_timestamp}')
            # 获取当前数据的时间戳,更新时间戳
            action_chunk, timestamp_chunk, loc_timestamp = self._process_action_chunk(action_data) #loc_timestamp是接收到观测数据的本机时间戳
            self.rdm.set_observe_time_marker(loc_timestamp)
            # print(timestamp_chunk)
            # addActionData函数是线程安全的，不需要加锁
            self.rdm.set_init_observe_timestamp(timestamp=timestamp_chunk[0])
            self.rdm.update_action_chunk_raw(action_chunk, timestamp_chunk)

            # 记录轨迹拟合的时间戳
            self.rdm.set_traj_time_marker()
            action_chunk_fitted, vel_chunk_fitted, timestamps_fitted = self._traj_fitting(num_samples=self.config.fitting_num_samples)

            # 记录控制的时间戳
            # TODO: 应该在此处开启控制线程
            self.rdm.set_control_time_marker()
            self.rdm.update_action_chunk_fitted(action_chunk_fitted, vel_chunk_fitted, timestamps_fitted)
            # self.rdm.setInitControlTime()

            # 统计平均推理时间和平均轨迹拟合时间
            self.rdm.compute_avg_infer_time()
            self.rdm.compute_avg_traj_time()
            # if self.config.show_data:
            #     with self.show_thread_lock:
            #         self.action_chunk = [action[0] for action in action_chunk]
            # if self.config.show_data:
            #     for action in action_chunk:
            #         self.action_queue.put(action[0])
            # self.inference_count += 1
        else:
            time11 =1 
            # print("No observe data, skip inference.")
        
        # 推理结束后将正在推理标记设置为False，便于开启下一次推理
        # with self.infer_thread_lock:
        #     self.infer_flag = False
    @run_time_decorator
    def inference_step(self):
        """Regular inference step, which is different with the first inference step.
        """
        if not self.is_running_action:
            return
        
        # getObserveData函数是线程安全的，不需要加锁
        data = self.rdm.pop_observe_data(num_samples = 1 if self.config.history_frame == False else 2)
        if data is not None:
            # 记录开始推理的时间戳
            self.rdm.set_infer_time_marker()
            self.rdm.add_infer_count()
            # 首先发送数据进行推理,然后阻塞等待推理结果
            self.zmq_client.sendMessage(data)
            result = self.zmq_client.recvMessage()
            action_data = result['data']
            # print(result)
            # ref_timestamp = action_data['ref_timestamp']
            # print(f'当前动作时间戳: {ref_timestamp}')
            # 获取当前数据的时间戳,更新时间戳
            action_chunk, timestamp_chunk, loc_timestamp = self._process_action_chunk(action_data) #loc_timestamp是接收到观测数据的本机时间戳
            self.rdm.set_observe_time_marker(loc_timestamp)
            # print(timestamp_chunk)
            # addActionData函数是线程安全的，不需要加锁
            self.rdm.update_action_chunk_raw(action_chunk, timestamp_chunk)

            # 记录轨迹拟合的时间戳
            self.rdm.set_traj_time_marker()
            action_chunk_fitted, vel_chunk_fitted, timestamps_fitted = self._traj_fitting(num_samples=self.config.fitting_num_samples)

            # # 记录控制的时间戳
            self.rdm.set_control_time_marker()
            
            self.rdm.update_action_chunk_fitted(action_chunk_fitted, vel_chunk_fitted, timestamps_fitted, search_action=self.config.search_action, search_length=self.config.search_length, smooth_action=self.config.smooth_action, smooth_length=self.config.smooth_length, gripper_offset=self.config.gripper_offset)

            # 统计平均推理时间和平均轨迹拟合时间
            self.rdm.compute_avg_infer_time()
            self.rdm.compute_avg_traj_time()
            # if self.config.show_data:
            #     with self.show_thread_lock:
            #         self.action_chunk = [action[0] for action in action_chunk]
            # if self.config.show_data:
            #     for action in action_chunk:
            #         self.action_queue.put(action[0])
            # self.inference_count += 1
        else:
            # print("没有观测数据，跳过推理")
            self.logger.warning("No observe data, skip inference.")
        
        # 推理结束后将正在推理标记设置为False，便于开启下一次推理
        # with self.infer_thread_lock:
        #     self.infer_flag = False

    def _control_thread_fun(self):
        if not self.is_running_action:
            return

        # print(f'[{time.time()}]控制线程已启动...')
        action = self.rdm.get_action_fitted()
        # action, timestamp = self.rdm.popActionData()
        if action is not None:
            # pass
            # print(f'[{time.time()}]控制线程已启动...')
            # timestamp = time.perf_counter()
            if self.config.record.switch and self.is_running_action and self.running:
                self.record_action_executor.submit(self.async_write_action, action)
            # print(f'send action using {(time.perf_counter() - timestamp)*1000:.2f}ms')
            self.robot.control_robot(action)
            if self.config.show_data:
                self.vis_action_state(action)

            # if self.config.show_data:
            #     with self.show_thread_lock:
            #         # if len(self.ydata0) < 200:
            #             # show raw action chunk
            #         self.ydata0.append(action[14])
            #         self.ydata1.append(action[15])
            #         self.xdata.append(len(self.ydata0))
                    # print(f'step: {len(self.ydata0)}')
            # print(f'action: {action}')
        # while self.running:
        #     # popActionData函数是线程安全的，不需要加锁
        #     start_time = time.time()
        #     action_chunk, timestamp_chunk = self.rdm.popActionData()
        #     if action_chunk is not None:
        #         # print(f'action_chunk shape: {action_chunk.shape}')
        #         # print(action)
        #         # print(action['ref_timestamp'])
        #         # print(action['pred_action'])
        #         # for action in action_chunk:
        #         self.robot.control_robot(action_chunk)
        #         end_time = time.time()
        #         time_diff = end_time - start_time
        #         if time_diff < self.config.controller.control_period/1000:
        #             time.sleep(self.config.controller.control_period/1000 - time_diff)
        #     else:
        #         # print("没有动作数据，跳过控制")
        #         time.sleep(0.010)
        #         continue
            # 获取当前时间戳
    
    # @run_time_decorator
    # def interpolateThreadFun(self, num_samples_fitted, num_samples_raw):
    #     print(f'轨迹插值/拟合线程已启动, {self.config.traj_strategy}...')
    #     if self.config.traj_strategy == 'interpolation':
    #         # self.traj_generator.interpolateTrajectory()
    #         pass
    #     elif self.config.traj_strategy == 'fitting':
    #         # 准备轨迹拟合用的数据
    #         # 首先准备拟合的数据
    #         timestamps_fitted, action_chunk_fitted = self.rdm.getFittedActionChunk(index_offset=0, num_samples=num_samples_fitted)
    #         timestamps, action_chunk = self.rdm.popActionChunk(index_offset=0, num_samples=num_samples_raw) #轨迹拟合需要10ms左右的时间
    #         if timestamps_fitted is not None:
    #             print(f'timestamps_fitted: {timestamps_fitted}')
    #             print(f'timestamps: {timestamps}')
    #             timestamps = np.concatenate((timestamps_fitted, timestamps), axis=0)
    #         # print(f'action_chunk_fitted shape: {action_chunk_fitted.shape}, action_chunk shape: {action_chunk.shape}')
    #         if action_chunk_fitted is not None:
    #             action_chunk = np.concatenate((action_chunk_fitted, action_chunk), axis=1)
    #         print(f'timestamps_all shape: {timestamps.shape}, action_chunk_all shape: {action_chunk.shape}')
    #         start_time = np.amin(timestamps)
    #         end_time = np.amax(timestamps)
            
    #         action_chunk_fitted, timestamps_fitted = self.traj_generator.trajFitting(timestamps=timestamps, action_chunk=action_chunk, start_time=start_time, end_time=end_time, deg=self.config.fitting_deg, time_step=self.config.fitting_time_step/1000)
    #         # print(f'action_chunk_fitted shape: {action_chunk_fitted.shape}')
    #         # action_chunk_fitted shape: (16, 1548)
    #         #TODO: 根据time_step 计算出offset
    #         # offset = int((self.rdm.getCurrentTime() - start_time) * 1000) # 1/time_step
    #         self.rdm.updateActionChunkFitted(action_chunk_fitted, timestamps_fitted)
    #         # pass
    #     else:
    #         print(f'未知的轨迹策略: {self.config.traj_strategy}')
    #     # while self.running:
    #     #     # popActionData函数是线程安全的，不需要加锁
    #     #     start_time = time.time()
    #     #     action_chunk, timestamp_chunk = self.rdm.popActionData()
    #     #     print(f'popActionData: {timestamp_chunk}')
    #     #     if action_chunk is not None:
    #     #         # self.xdata.put(action_chunk[0])
    #     #         # self.ydata.put(timestamp_chunk[0]/1e9)
    #     #         self.xdata.append(timestamp_chunk/1e9)
    #     #         self.ydata0.append(action_chunk[0])
    #     #         self.ydata1.append(action_chunk[1])
    #     #         # print(f'action_chunk shape: {action_chunk.shape}')
    #     #         # print(action)
    #     #         # print(action['ref_timestamp'])
    #     #         # print(action['pred_action'])
    #     #         # for action in action_chunk:
    #     #         self.traj_generator.addWayPoint(action_chunk)
    #     #         end_time = time.time()
    #     #         time_diff = end_time - start_time
    #     #         # 根据control_period控制轨迹执行的时间
    #     #         if time_diff < self.config.controller.control_period/1000:
    #     #             time.sleep(self.config.controller.control_period/1000 - time_diff)
    #     #     else:
    #     #         print("没有动作数据，跳过轨迹插值")
    #     #         time.sleep(0.010)
    #     #         continue
    #         # 获取当前时间戳
    # @run_time_decorator
    # def trajFittingStep(self, num_samples_fitted, num_samples_raw):
    #     # 首先根据平均轨迹拟合时间和控制时间间隔，计算取拟合轨迹数据的偏移量
    #     index_offset = math.floor(self.rdm.getAvgTrajTime() * 1000 / self.config.controller.period)
    #     timestamps_fitted, action_chunk_fitted = self.rdm.getFittedActionChunk(index_offset=index_offset, num_samples=num_samples_fitted)
    #     timestamps, action_chunk = self.rdm.popActionChunk(time_offset=self.rdm.getAvgTrajTime(), num_samples=num_samples_raw) #轨迹拟合需要10ms左右的时间
    #     if timestamps_fitted is not None:
    #         print(f'timestamps_fitted: {timestamps_fitted}')
    #         print(f'timestamps: {timestamps}')
    #         timestamps = np.concatenate((timestamps_fitted, timestamps), axis=0)
    #     # print(f'action_chunk_fitted shape: {action_chunk_fitted.shape}, action_chunk shape: {action_chunk.shape}')
    #     if action_chunk_fitted is not None:
    #         action_chunk = np.concatenate((action_chunk_fitted, action_chunk), axis=1)
    #     print(f'timestamps_all shape: {timestamps.shape}, action_chunk_all shape: {action_chunk.shape}')
    #     start_time = np.amin(timestamps)
    #     end_time = np.amax(timestamps)
    #     # trajFitting(self, timestamps, action_chunk, start_time, end_time, deg = 3, time_step = 0.001)
        
    #     action_chunk_fitted, timestamps_fitted = self.traj_generator.trajFitting(timestamps=timestamps, action_chunk=action_chunk, start_time=start_time, end_time=end_time, deg=self.config.fitting_deg, time_step=self.config.fitting_time_step/1000)
    #     # print(f'action_chunk_fitted shape: {action_chunk_fitted.shape}')
    #     # action_chunk_fitted shape: (16, 1548)
    #     #TODO: 根据time_step 计算出offset
    #     # offset = int((self.rdm.getCurrentTime() - start_time) * 1000) # 1/time_step
    #     self.rdm.updateActionChunkFitted(action_chunk_fitted, timestamps_fitted)
    #     # pass
    #     # while self.running:
    #     #     # popActionData函数是线程安全的，不需要加锁
    #     #     start_time = time.time()
    #     #     action_chunk, timestamp_chunk = self.rdm.popActionData()
    #     #     print(f'popActionData: {timestamp_chunk}')
    #     #     if action_chunk is not None:
    #     #         # self.xdata.put(action_chunk[0])
    #     #         # self.ydata.put(timestamp_chunk[0]/1e9)
    #     #         self.xdata.append(timestamp_chunk/1e9)
    #     #         self.ydata0.append(action_chunk[0])
    #     #         self.ydata1.append(action_chunk[1])
    #     #         # print(f'action_chunk shape: {action_chunk.shape}')
    #     #         # print(action)
    #     #         # print(action['ref_timestamp'])
    #     #         # print(action['pred_action'])
    #     #         # for action in action_chunk:
    #     #         self.traj_generator.addWayPoint(action_chunk)
    #     #         end_time = time.time()
    #     #         time_diff = end_time - start_time
    #     #         # 根据control_period控制轨迹执行的时间
    #     #         if time_diff < self.config.controller.control_period/1000:
    #     #             time.sleep(self.config.controller.control_period/1000 - time_diff)
    #     #     else:
    #     #         print("没有动作数据，跳过轨迹插值")
    #     #         time.sleep(0.010)
    #     #         continue
    #         # 获取当前时间戳
    @run_time_decorator
    def _traj_fitting(self, num_samples):
        timestamps, action_chunk = self.rdm.pop_action_chunk(time_offset=0.0, num_samples=num_samples) #轨迹拟合需要10ms左右的时间
        self.logger.debug(f'timestamps for fitting: {timestamps[::10]}')
        # start_time = np.amin(timestamps)
        # end_time = np.amax(timestamps)
        start_time = timestamps[0]
        end_time = timestamps[-1]
        action_chunk_fitted, vel_chunk_fitted, timestamps_fitted = self.traj_generator.traj_fitting(timestamps=timestamps, action_chunk=action_chunk, start_time=start_time, end_time=end_time, deg=self.config.fitting_deg, time_step=self.config.fitting_time_step/1000)
        # print(f'action_chunk_fitted shape: {action_chunk_fitted.shape}')
        # action_chunk_fitted shape: (16, 1548)
        #TODO: 根据time_step 计算出offset
        # offset = int((self.rdm.getCurrentTime() - start_time) * 1000) # 1/time_step
        return action_chunk_fitted, vel_chunk_fitted, timestamps_fitted
        # pass
        # while self.running:
        #     # popActionData函数是线程安全的，不需要加锁
        #     start_time = time.time()
        #     action_chunk, timestamp_chunk = self.rdm.popActionData()
        #     print(f'popActionData: {timestamp_chunk}')
        #     if action_chunk is not None:
        #         # self.xdata.put(action_chunk[0])
        #         # self.ydata.put(timestamp_chunk[0]/1e9)
        #         self.xdata.append(timestamp_chunk/1e9)
        #         self.ydata0.append(action_chunk[0])
        #         self.ydata1.append(action_chunk[1])
        #         # print(f'action_chunk shape: {action_chunk.shape}')
        #         # print(action)
        #         # print(action['ref_timestamp'])
        #         # print(action['pred_action'])
        #         # for action in action_chunk:
        #         self.traj_generator.addWayPoint(action_chunk)
        #         end_time = time.time()
        #         time_diff = end_time - start_time
        #         # 根据control_period控制轨迹执行的时间
        #         if time_diff < self.config.controller.control_period/1000:
        #             time.sleep(self.config.controller.control_period/1000 - time_diff)
        #     else:
        #         print("没有动作数据，跳过轨迹插值")
        #         time.sleep(0.010)
        #         continue
            # 获取当前时间戳

    def _process_image(self, key, value):
        """Process image data by padding, resize and encoding.

        Args:
            key (str): Image key.
            value (np.ndarray): Image data.

        Returns:
            tuple(str, np.ndarray, np.ndarray): Raw image key, preprocessed image and encoded image.
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
        # 使用线程池并行处理所有摄像头
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self._process_image, key, value) for key, value in cam_items]
            results = [future.result() for future in futures] # 等待所有任务完成
        encoded_imgs, processed_imgs = {}, {}
        for key, processed, encoded in results:
            encoded_imgs[key] = encoded
            if self.config.show_img:
                processed_imgs[key] = processed
                if 'depth.' in key:
                    img_depth_norm = cv2.normalize(processed, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                    img_show = cv2.applyColorMap(img_depth_norm, cv2.COLORMAP_JET)
                else:
                    img_show = cv2.cvtColor(processed, cv2.COLOR_RGB2BGR)
                # 线程内无法显示
                cv2.imwrite(f'{key}.png', img_show)
                # cv2.imshow(key, img_show)
                # cv2.waitKey(1)
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
        # if frame['obs.state'][-1] is None:
        #     frame['obs.state'][-1] = 0.0
        data = {
            'type': 'vla_obs',
            'img_keys': ['cam.head', 'cam.hand_left', 'cam.hand_right'],
            'ref_timestamp': frame['ref_timestamp'],
            'loc_timestamp': loc_timestamp,
            'obs': {
                **encoded_imgs,
                'state': frame['obs.state'],
                'language': [self.language],
            },
        }
        # end_time = time.time()
        # 计算并打印运行时间
        # elapsed_time = (end_time - start_time) * 1000
        # print(f"图像编码时间: {elapsed_time} ms")
        return data
    # @run_time_decorator
    # def processAction(self, action):
    #     # {'type': 'action', 'pred_action': array([[-1.0059779 ,  0.58745086,  0.32646954, -1.2613511 ,  0.7208374 ,
    #     #  1.4398973 , -0.1548205 ,  1.0740726 , -0.6103424 , -0.28125978,
    #     #  1.2830431 , -0.72958744, -1.4945612 ,  0.18649821,  0.00195312,
    #     #  0.        ],], dtype=float32), 'ref_timestamp': 1745389475305775776}
    #     # 将传入的消息msg添加到buffer列表中
    #     action_chunk = []
    #     timestamp_chunk = []
    #     action_type = action['type']
    #     if action_type == 'action':
    #         pred_action = action['pred_action']
    #         ref_timestamp = action['ref_timestamp']
    #         for index, action in enumerate(pred_action):
    #             timestamp =  ref_timestamp + self.config.observer.period * index * 1e9 # observer.period单位是秒，需要转换成纳秒，即*1e9
    #             action_chunk.append(action)
    #             timestamp_chunk.append(timestamp)
            
    #         return action_chunk, timestamp_chunk
    #         # print(type(pred_action))
    #         # print(ref_timestamp)
    #     else:
    #         print(f'数据类型出错: {action_type}')
    #         return None, None
    @run_time_decorator
    def _process_action_chunk(self, action):
        """Process an action chunk by generating reference timestamp chunk and passing local timestamp.

        Args:
            action (dict): The inference result from vla_server. It is a dictionary with keys i.e. type, pred_action, ref_timestamp, loc_timestamps.

        Returns:
            tuple(list, list, int): The predicted action chunk, reference timestamp chunk and local timestamp.
        """
        # timestamp_chunk的逻辑发生了变化，首帧是观测数据的时间戳ref_timestamp, 后续帧是相对时间
        # {'type': 'vla_action', 'pred_action': array([[-1.0059779 ,  0.58745086,  0.32646954, -1.2613511 ,  0.7208374 ,
        #  1.4398973 , -0.1548205 ,  1.0740726 , -0.6103424 , -0.28125978,
        #  1.2830431 , -0.72958744, -1.4945612 ,  0.18649821,  0.00195312,
        #  0.        ],], dtype=float32), 'ref_timestamp': 1745389475305775776}
        # 将传入的消息msg添加到buffer列表中
        action_chunk = []
        timestamp_chunk = []
        action_type = action['type']
        if action_type == 'vla_action':
            pred_action = action['pred_action']
            ref_timestamp = action['ref_timestamp']
            loc_timestamp = action['loc_timestamp']
            for index, action in enumerate(pred_action):
                action_chunk.append(action)
                # timestamp_chunk.append(self.config.observer.period * index * 1e9) # observer.period单位是秒，需要转换成纳秒，即*1e9
                timestamp_chunk.append(self.config.observer.period * index) # observer.period单位是秒
            timestamp_chunk[0] = ref_timestamp # 首帧是观测数据的时间戳ref_timestamp
            return action_chunk, timestamp_chunk, loc_timestamp
            # print(type(pred_action))
            # print(ref_timestamp)
        else:
            self.logger.error(f'wrong action type: {action_type}')
            return None, None, None

    def run(self):
        with self.thread_lock:
            self.running = True
    
        # 启动线程
        self.observe_thread.start()
        self.inference_thread.start()
        # self.interpolate_thread.start()
        # self.control_thread.start()
        self.control_thread_timer.start()
        # if self.config.show_data:
        #     self._show_action_chunk()
        # 等待线程结束
        # self.observe_thread.join()
        # self.inference_thread.join()
        # self.control_thread.join()
        # print('推理框架客户端已启动。')
        self.logger.info('Inference client started.')
    
    
    def stop(self):
        with self.thread_lock:
            self.running = False
        self.observe_thread.join(timeout=1.0)
        # self.inference_thread.join(timeout=1.0)
        # self.interpolate_thread.join(timeout=1.0)
        # self.control_thread.join(timeout=1.0)
        self.control_thread_timer.join(timeout=1.0)
        # print('推理框架客户端已关闭。')
        self.logger.info('Inference client stopped.')

    def close(self):
        with self.thread_lock:
            self.running = False
        # print('推理框架客户端开始关闭。')
        # plt.close()
        self.observe_thread.join(timeout=1.0)
        self.inference_thread.join(timeout=1.0)
        # self.interpolate_thread.join(timeout=1.0)
        # self.control_thread.join(timeout=1.0)
        ## ADD stop to exit
        self.control_thread_timer.stop()
        self.control_thread_timer.join(timeout=1.0)
        if self.config.record.switch:
            time.sleep(1)
            self.record_obs_executor.shutdown(wait=True)
            self.record_action_executor.shutdown(wait=True)
            self.dataset_write.writer_thread.join(timeout=1.0)
            self.dataset_write.close()
        self.zmq_client.close()
        self.vis_zmq.stop()
        self.logger.info('Inference client closed.')
        # self.traj_generator.close()
        # print('推理框架客户端已关闭。')

    def _update_visualization(self, frame):
        # 更新图表数据
        # print(f'updateVisualization: {frame}')
        # print(f'self.xdata: {self.xdata}')
        # print(f'self.ydata: {self.ydata1}')
        # self.line.set_data(self.xdata, self.ydata)
        if len(self.xdata) > 0:
            x_min= min(self.xdata[:])
            x_max= max(self.xdata[:])
            y0_min= min(self.ydata0[:])
            y0_max= max(self.ydata0[:])
            y1_min= min(self.ydata1[:])
            y1_max= max(self.ydata1[:])
        else:
            x_min = 0.0
            x_max = 0.5
            y0_min = -1.0
            y0_max = 1.0
            y1_min = -1.0
            y1_max = 1.0
        self.axs[0].set_xlim(x_min, x_max)
        self.axs[0].set_ylim(y0_min, y0_max)
        self.axs[1].set_xlim(x_min, x_max)
        self.axs[1].set_ylim(y1_min, y1_max)

        # lines = self.axs[0].plot(self.xdata[-32:], self.ydata0[-32:], 'b-', lw=1) + self.axs[1].plot(self.xdata[-32:], self.ydata1[-32:], 'r-', lw=1)
        lines = self.axs[0].plot(self.xdata[:], self.ydata0[:], 'b-', lw=1) + self.axs[1].plot(self.xdata[:], self.ydata1[:], 'r-', lw=1)
        # return self.ax.plot(self.xdata, self.ydata, 'b-', lw=1)
        print(self.ydata0)
        return lines

        # # 动态调整X轴范围（保持最新数据在视图中）
        # if new_x > max_data_points:
        #     ax.set_xlim(new_x - max_data_points, new_x)
        # else:
        #     ax.set_xlim(0, max_data_points)
        
        # self.ax.relim()          # 重新计算数据范围
        # self.ax.autoscale_view() # 自动缩放Y轴
        # return self.line,
    def _show_action_chunk(self):
        # 创建动画对象
        ani = FuncAnimation(
            fig=self.fig,
            func=self._update_visualization,
            # init_func=init,
            frames=None,        # 无限循环
            interval=30,        # 更新间隔50ms（约20帧/秒）
            blit=True,          # 优化渲染性能
            cache_frame_data=False
        )

        plt.show()
        # while True:
        #     if self.action_chunk is None:
        #         time.sleep(0.5)
        #         continue
        #     with self.show_thread_lock:
        #         action_chunk = copy.copy(self.action_chunk)
        #     self.ax.clear()
        #     self.ax.plot(range(len(action_chunk)), action_chunk)
        #     print('show action chunk')
        #     plt.show()
            # time.sleep(0.1)
        # plt.ion()  # 开启交互模式
        # fig, ax = plt.subplots()
        # x_data, y_data = [], []


        # def update_plot(frame):
        #     print('update_plot')
        #     try:
        #         if not self.action_queue.empty():
        #             data = self.action_queue.get(block=True)
        #             x_data.append(frame)
        #             y_data.append(data)
        #             ax.clear()
        #             ax.plot(x_data, y_data)
        #         return ax
        #     except Exception as e:
        #         print(f"Error: {e}")
        #         # return ax

        # ani = FuncAnimation(fig, update_plot, frames=range(16), blit=True, interval=50)

    def _inference_thread_fun(self):
        # print('推理线程已启动...')
        while self.running:
            # 第一次推理
            if self.rdm.infer_count == 0:
                self.inference_first()
                # time.sleep(self.config.controller.wait_step * self.config.controller.control_period/1000)
                time.sleep(self.config.sleep_time)
                # char = input("Press 'q' to quit: ")
            # 第二次推理
            elif self.rdm.infer_count < 10000:
                self.inference_step()
                # self.inferenceFirstThreadFun()
                # char = input("Press 'q' to quit: ")
                # char = input("Press 'q' to quit: ")
                time.sleep(self.config.sleep_time)
            # print(f'\rInference count: {self.rdm.infer_count}, current infer time: {self.rdm.start_traj_marker-self.rdm.start_infer_marker:.4f}s, current traj time: {self.rdm.start_ctrl_marker-self.rdm.start_traj_marker:.4f}s', end='', flush=True)
            symbol = '=' * 10
            # print(f'\r{symbol}VLA Inference Framework{symbol}Inference count: {self.rdm.infer_count}, average infer time: {self.rdm.avg_infer_time:.4f}s, average traj time: {self.rdm.avg_traj_time:.4f}s', end='', flush=True)
            # command_prompt()
            # with self.live:
            #     self.live.update(command_prompt())
                # char = input("Press 'q' to quit: ") 
            #     print(f'wait time: {self.config.controller.time_delay/1000}')
            #     time.sleep(self.config.controller.time_delay/1000)
            #     with self.thread_lock:
            #         frame = self.rdm.getObserveData()
            #     if frame is not None:
            #         data = self.prepareData(frame)
            #         self.send_message(data)
            #         result = self.receive_messages()
            #         print(result)
            #         self.inference_count += 1
            #     else:
            #         print("没有观测数据，跳过推理")
            #         time.sleep(0.010)
            #         continue
            # else:
            #     # 后续推理，贪心
            #     with self.thread_lock:
            #         frame = self.rdm.getObserveData()
            #     if frame is not None:
            #         data = self.prepareData(frame)
            #         self.send_message(data)
            #         result = self.receive_messages()
            #         print(result)
            #         self.inference_count += 1
            #     else:
            #         print("没有观测数据，跳过推理")
            #         time.sleep(0.010)
            #         continue
            # 请求服务端推理最新指定时间戳的obs
            # time.sleep(0.1)

    # @run_time_decorator
    # def inferenceFirstTime(self):
    #     # 第一次推理，getObserveData函数是线程安全的，不需要加锁
    #     data = self.rdm.getObserveData()
    #     if data is not None:
    #         # data = self.prepareData(frame)
    #         # 首先发送数据进行推理,然后阻塞等待推理结果
    #         # print(data['obs']['state'])
    #         # obs_state = data['obs']['state']
    #         # for state in obs_state:
    #         #     print(type(state))
    #         self.zmq_client.sendMessage(data)
    #         result = self.zmq_client.recvMessage()
    #         action_data = result['data']
    #         # print(result)
    #         # ref_timestamp = action_data['ref_timestamp']
    #         # print(f'当前动作时间戳: {ref_timestamp}')
    #         # 获取当前数据的时间戳,更新时间戳
    #         # with self.thread_lock:
    #         data = self.rdm.getObserveData()
    #         ref_timestamp = data['ref_timestamp']
    #         # print(f'当前数据时间戳: {ref_timestamp}')
    #         action_data['ref_timestamp'] = ref_timestamp
    #         # ref_timestamp = action_data['ref_timestamp']
    #         # print(f'当前动作时间戳: {ref_timestamp}')
    #         action_chunk, timestamp_chunk = self.processAction(action_data)
    #         # print(timestamp_chunk)
    #         # with self.thread_lock:
    #         self.rdm.addActionData(action_chunk, timestamp_chunk, strategy=self.config.chunk_strategy)

    #         self.interpolate_thread = threading.Thread(target=self.interpolateThreadFun, kwargs={'num_samples_fitted': 0, 'num_samples_raw': 48}, daemon=True)
    #         self.interpolate_thread.start()
    #         # 初次推理需要等待等待插值完成，更新init_control_timestamp
    #         self.interpolate_thread.join()
    #         self.rdm.updateControlTimeStamp()
    #         # if self.config.show_data:
    #         #     with self.show_thread_lock:
    #         #         self.action_chunk = [action[0] for action in action_chunk]
    #             # self.show_thread.start()
    #         self.inference_count += 1
    #         print('初次推理完成')
    #     else:
    #         print("没有观测数据，跳过推理")
    # @run_time_decorator
    # def inferenceStep(self):
    #     # getObserveData函数是线程安全的，不需要加锁
        
    #     data = self.rdm.getObserveData()
    #     if data is not None:
    #         # 首先发送数据进行推理,然后阻塞等待推理结果
    #         self.zmq_client.sendMessage(data)
    #         result = self.zmq_client.recvMessage()
    #         action_data = result['data']
    #         # print(result)
    #         # ref_timestamp = action_data['ref_timestamp']
    #         # print(f'当前动作时间戳: {ref_timestamp}')
    #         # 获取当前数据的时间戳,更新时间戳
    #         action_chunk, timestamp_chunk = self.processAction(action_data)
    #         # print(timestamp_chunk)
    #         # addActionData函数是线程安全的，不需要加锁
    #         self.rdm.addActionData(action_chunk, timestamp_chunk, strategy=self.config.chunk_strategy)

    #         self.interpolate_thread = threading.Thread(target=self.interpolateThreadFun, kwargs={'num_samples_fitted': 0, 'num_samples_raw': 48}, daemon=True)
    #         self.interpolate_thread.start()
    #         # if self.config.show_data:
    #         #     with self.show_thread_lock:
    #         #         self.action_chunk = [action[0] for action in action_chunk]
    #         # if self.config.show_data:
    #         #     for action in action_chunk:
    #         #         self.action_queue.put(action[0])
    #         self.inference_count += 1
    #     else:
    #         print("没有观测数据，跳过推理")

    def vis_action_state(self, action):
        current_state = self.robot.get_obs_only_state()
        line_data = []
        for joint_idx, value in enumerate(action):
            # if joint_idx != 10:
            #     continue
            # joint_idx = 0
            if joint_idx >= current_state.shape[0]:
                continue
            line_data.append({
                'subplot': joint_idx,
                'y': [value],
                'x': [self.vis_global_step],
                'line_idx': 0,
                'line_props': {
                    'show_line': True,
                    'color': 'purple',
                    'marker': 'o',
                    'markersize': 1,
                    'label': 'action'
                }
            })
            line_data.append({
                'subplot': joint_idx,
                'y': [current_state[joint_idx]],
                'x': [self.vis_global_step],
                'line_idx': 1,
                'line_props': {
                    'show_line': True,
                    'color': 'orange',
                    'marker': 'o',
                    'markersize': 1,
                    'label': 'state'
                }
            })
        self.vis_zmq.send({'line_data': line_data})
        self.vis_global_step += 1

if __name__ == "__main__":
    pass
