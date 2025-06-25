import copy
import cv2
import time
import queue
import threading
import numpy as np
from matplotlib  import pyplot as plt
from matplotlib.animation import FuncAnimation
from ml_collections import ConfigDict

# from core.obs_robot import RobotObs
# from core.action_robot import RobotAction
from ..robots.a2d import RobotA2D
from ..robots.mock_a2d import RobotA2DMock
from ..utils import misc
from ..utils.util import run_time_decorator
from ..utils.multi_thread_timer import MultiThreadTimer
from .zmq_client import ZMQClient
from .trajectory_generator import TrajectoryGenerator
from .realtime_data_manager import RealtimeDataManager

# VLA客户端
class VLAClient():
    def __init__(self, config: ConfigDict, rdm: RealtimeDataManager, traj_generator: TrajectoryGenerator, zmq_client: ZMQClient, robot: RobotA2D | RobotA2DMock):
        self.config = config
        self.rdm = rdm
        self.traj_generator = traj_generator
        self.zmq_client = zmq_client
        self.robot = robot
        self.running = False

        self.observe_thread = threading.Thread(target=self.observeThreadFun, daemon=True)
        self.inference_thread = threading.Thread(target=self.inferenceThreadFun, daemon=True)
        self.interpolate_thread = None
        # self.control_thread = threading.Thread(target=self.controlThreadFun, daemon=True)
        self.control_thread_timer = MultiThreadTimer(self.config.controller.period, self.controlThreadFun)
        
        self.thread_lock = threading.Lock()
        self.show_thread_lock = threading.Lock()
        self.receive_callback = None
        self.inference_count = 0
        
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

    def observeThreadFun(self):
        print('观测线程已启动...')
        while self.running:
            observations = self.robot.retrieveObservation()
            if observations is not None:
                # print(observations.keys())
                # print(observations['ref_timestamp'])
                # print(observations['obs.state'])
                data = self.processData(observations)
                self.rdm.addObserveData(data)
            time.sleep(0.001)  # 控制循环频率
    
    def inferenceThreadFun(self):
        print('推理线程已启动...')
        while self.running:
            # 第一次推理
            if self.inference_count == 0:
                self.inferenceFirstTime()
                # time.sleep(self.config.controller.wait_step * self.config.controller.control_period/1000)
                time.sleep(0.5)
            # 第二次推理
            elif self.inference_count < 10000:
                self.inferenceStep()
                time.sleep(0.1)
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
    @run_time_decorator
    def inferenceFirstTime(self):
        # 第一次推理，getObserveData函数是线程安全的，不需要加锁
        data = self.rdm.getObserveData()
        if data is not None:
            # data = self.prepareData(frame)
            # 首先发送数据进行推理,然后阻塞等待推理结果
            # print(data['obs']['state'])
            # obs_state = data['obs']['state']
            # for state in obs_state:
            #     print(type(state))
            self.zmq_client.sendMessage(data)
            result = self.zmq_client.recvMessage()
            action_data = result['data']
            # print(result)
            # ref_timestamp = action_data['ref_timestamp']
            # print(f'当前动作时间戳: {ref_timestamp}')
            # 获取当前数据的时间戳,更新时间戳
            # with self.thread_lock:
            data = self.rdm.getObserveData()
            ref_timestamp = data['ref_timestamp']
            # print(f'当前数据时间戳: {ref_timestamp}')
            action_data['ref_timestamp'] = ref_timestamp
            # ref_timestamp = action_data['ref_timestamp']
            # print(f'当前动作时间戳: {ref_timestamp}')
            action_chunk, timestamp_chunk = self.processAction(action_data)
            # print(timestamp_chunk)
            # with self.thread_lock:
            self.rdm.addActionData(action_chunk, timestamp_chunk, strategy=self.config.chunk_strategy)

            self.interpolate_thread = threading.Thread(target=self.interpolateThreadFun, kwargs={'num_samples_fitted': 0, 'num_samples_raw': 48}, daemon=True)
            self.interpolate_thread.start()
            # 初次推理需要等待等待插值完成，更新init_control_timestamp
            self.interpolate_thread.join()
            self.rdm.updateControlTimeStamp()
            # if self.config.show_data:
            #     with self.show_thread_lock:
            #         self.action_chunk = [action[0] for action in action_chunk]
                # self.show_thread.start()
            self.inference_count += 1
            print('初次推理完成')
        else:
            print("没有观测数据，跳过推理")
    @run_time_decorator
    def inferenceStep(self):
        # getObserveData函数是线程安全的，不需要加锁
        
        data = self.rdm.getObserveData()
        if data is not None:
            # 首先发送数据进行推理,然后阻塞等待推理结果
            self.zmq_client.sendMessage(data)
            result = self.zmq_client.recvMessage()
            action_data = result['data']
            # print(result)
            # ref_timestamp = action_data['ref_timestamp']
            # print(f'当前动作时间戳: {ref_timestamp}')
            # 获取当前数据的时间戳,更新时间戳
            action_chunk, timestamp_chunk = self.processAction(action_data)
            # print(timestamp_chunk)
            # addActionData函数是线程安全的，不需要加锁
            self.rdm.addActionData(action_chunk, timestamp_chunk, strategy=self.config.chunk_strategy)

            self.interpolate_thread = threading.Thread(target=self.interpolateThreadFun, kwargs={'num_samples_fitted': 0, 'num_samples_raw': 48}, daemon=True)
            self.interpolate_thread.start()
            # if self.config.show_data:
            #     with self.show_thread_lock:
            #         self.action_chunk = [action[0] for action in action_chunk]
            # if self.config.show_data:
            #     for action in action_chunk:
            #         self.action_queue.put(action[0])
            self.inference_count += 1
        else:
            print("没有观测数据，跳过推理")

    def controlThreadFun(self):
        # print(f'[{time.time()}]控制线程已启动...')
        action = self.rdm.getActionFitted()
        # action, timestamp = self.rdm.popActionData()
        if action is not None:
            # pass
            # print(f'[{time.time()}]控制线程已启动...')
            self.robot.controlRobot(action)
            if self.config.show_data:
                with self.show_thread_lock:
                    # show raw action chunk
                    self.ydata0.append(action[14])
                    self.ydata1.append(action[15])
                    self.xdata.append(len(self.ydata0))
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
        #         self.robot.controlRobot(action_chunk)
        #         end_time = time.time()
        #         time_diff = end_time - start_time
        #         if time_diff < self.config.controller.control_period/1000:
        #             time.sleep(self.config.controller.control_period/1000 - time_diff)
        #     else:
        #         # print("没有动作数据，跳过控制")
        #         time.sleep(0.010)
        #         continue
            # 获取当前时间戳
    
    def interpolateThreadFun(self, num_samples_fitted, num_samples_raw):
        print(f'轨迹插值/拟合线程已启动, {self.config.traj_strategy}...')
        if self.config.traj_strategy == 'interpolation':
            # self.traj_generator.interpolateTrajectory()
            pass
        elif self.config.traj_strategy == 'fitting':
            # 准备轨迹拟合用的数据
            # 首先准备拟合的数据
            timestamps_fitted, action_chunk_fitted = self.rdm.getFittedActionChunk(index_offset=0, num_samples=num_samples_fitted)
            timestamps, action_chunk = self.rdm.popActionChunk(index_offset=0, num_samples=num_samples_raw) #轨迹拟合需要10ms左右的时间
            if timestamps_fitted is not None:
                print(f'timestamps_fitted: {timestamps_fitted}')
                print(f'timestamps: {timestamps}')
                timestamps = np.concatenate((timestamps_fitted, timestamps), axis=0)
            # print(f'action_chunk_fitted shape: {action_chunk_fitted.shape}, action_chunk shape: {action_chunk.shape}')
            if action_chunk_fitted is not None:
                action_chunk = np.concatenate((action_chunk_fitted, action_chunk), axis=1)
            print(f'timestamps_all shape: {timestamps.shape}, action_chunk_all shape: {action_chunk.shape}')
            start_time = np.amin(timestamps)
            end_time = np.amax(timestamps)
            # trajFitting(self, timestamps, action_chunk, start_time, end_time, deg = 3, time_step = 0.001)
            
            action_chunk_fitted, timestamps_fitted = self.traj_generator.trajFitting(timestamps=timestamps, action_chunk=action_chunk, start_time=start_time, end_time=end_time, deg=self.config.fitting_deg, time_step=self.config.fitting_time_step/1000)
            # print(f'action_chunk_fitted shape: {action_chunk_fitted.shape}')
            # action_chunk_fitted shape: (16, 1548)
            #TODO: 根据time_step 计算出offset
            # offset = int((self.rdm.getCurrentTime() - start_time) * 1000) # 1/time_step
            self.rdm.updateActionChunkFitted(action_chunk_fitted, timestamps_fitted)
            # pass
        else:
            print(f'未知的轨迹策略: {self.config.traj_strategy}')
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

    def processData(self, frame):
        start_time = time.time()
        # img_head = misc.crop_and_resize(frame['obs.cam.head'])
        # img_hand_left = misc.crop_and_resize(frame['obs.cam.hand_left'])
        # img_hand_right = misc.crop_and_resize(frame['obs.cam.hand_right'])
        img_head = misc.pad_and_resize(frame['obs.cam.head'])
        img_hand_left = misc.pad_and_resize(frame['obs.cam.hand_left'])
        img_hand_right = misc.pad_and_resize(frame['obs.cam.hand_right'])
        # if frame['obs.state'][-1] is None:
        #     frame['obs.state'][-1] = 0.0
        data = {
            'type': 'vla',
            'img_keys': ['cam.head', 'cam.hand_left', 'cam.hand_right'],
            'ref_timestamp': frame['ref_timestamp'],
            'obs': {
                'cam.head': cv2.imencode('.jpg', img_head)[1],
                'cam.hand_left': cv2.imencode('.jpg', img_hand_left)[1],
                'cam.hand_right': cv2.imencode('.jpg', img_hand_right)[1],
                'state': frame['obs.state'],
                'annotation.human.action.task_description': ['pick bottle into box'],
            },
        }
        end_time = time.time()
        # 计算并打印运行时间
        elapsed_time = (end_time - start_time) * 1000
        # print(f"图像编码时间: {elapsed_time} ms")
        return data
    @run_time_decorator
    def processAction(self, action):
        # {'type': 'action', 'pred_action': array([[-1.0059779 ,  0.58745086,  0.32646954, -1.2613511 ,  0.7208374 ,
        #  1.4398973 , -0.1548205 ,  1.0740726 , -0.6103424 , -0.28125978,
        #  1.2830431 , -0.72958744, -1.4945612 ,  0.18649821,  0.00195312,
        #  0.        ],], dtype=float32), 'ref_timestamp': 1745389475305775776}
        # 将传入的消息msg添加到buffer列表中
        action_chunk = []
        timestamp_chunk = []
        action_type = action['type']
        if action_type == 'action':
            pred_action = action['pred_action']
            ref_timestamp = action['ref_timestamp']
            for index, action in enumerate(pred_action):
                timestamp =  ref_timestamp + self.config.observer.period * index * 1000000 # observer.period单位是毫秒，需要转换成纳秒，即*1e6
                action_chunk.append(action)
                timestamp_chunk.append(timestamp)
            
            return action_chunk, timestamp_chunk
            # print(type(pred_action))
            # print(ref_timestamp)
        else:
            print(f'数据类型出错: {action_type}')
            return None, None

    def run(self):
        with self.thread_lock:
            self.running = True
    
        # 启动线程
        self.observe_thread.start()
        self.inference_thread.start()
        # self.interpolate_thread.start()
        # self.control_thread.start()
        self.control_thread_timer.start()
        if self.config.show_data:
            self.showActionChunk()
        # 等待线程结束
        self.observe_thread.join()
        # self.inference_thread.join()
        # self.control_thread.join()
        print('推理框架客户端已启动。')
    
    
    def stop(self):
        with self.thread_lock:
            self.running = False
        self.observe_thread.join(timeout=1.0)
        self.inference_thread.join(timeout=1.0)
        # self.interpolate_thread.join(timeout=1.0)
        # self.control_thread.join(timeout=1.0)
        self.control_thread_timer.join(timeout=1.0)
        print('推理框架客户端已关闭。')

    def close(self):
        with self.thread_lock:
            self.running = False
        plt.close()
        self.observe_thread.join(timeout=1.0)
        self.inference_thread.join(timeout=1.0)
        # self.interpolate_thread.join(timeout=1.0)
        # self.control_thread.join(timeout=1.0)
        self.control_thread_timer.join(timeout=1.0)
        self.zmq_client.close()
        self.traj_generator.close()
        print('推理框架客户端已关闭。')

    def updateVisualization(self, frame):
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
        return lines

        # # 动态调整X轴范围（保持最新数据在视图中）
        # if new_x > max_data_points:
        #     ax.set_xlim(new_x - max_data_points, new_x)
        # else:
        #     ax.set_xlim(0, max_data_points)
        
        # self.ax.relim()          # 重新计算数据范围
        # self.ax.autoscale_view() # 自动缩放Y轴
        # return self.line,
    def showActionChunk(self):
        # 创建动画对象
        ani = FuncAnimation(
            fig=self.fig,
            func=self.updateVisualization,
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


if __name__ == "__main__":
    pass