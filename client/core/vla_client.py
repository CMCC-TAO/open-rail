import cv2
import time
import queue
import threading
import numpy as np
from matplotlib  import pyplot as plt
from ml_collections import ConfigDict

# from core.obs_robot import RobotObs
# from core.action_robot import RobotAction
from ..robots.a2d import RobotA2D
from ..robots.mock_a2d import RobotA2DMock
from ..utils import misc
from ..utils.util import run_time_decorator
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
        self.interpolate_thread = threading.Thread(target=self.interpolateThreadFun, daemon=True)
        self.control_thread = threading.Thread(target=self.controlThreadFun, daemon=True)
        
        self.thread_lock = threading.Lock()
        self.receive_callback = None
        self.inference_count = 0
        
        if config.show_data:
            self.action_queue = queue.Queue(maxsize=1000)
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
                time.sleep(self.config.controller.wait_step * self.config.controller.control_period/1000)
            # 第二次推理
            elif self.inference_count < 20:
                self.inferenceStep()
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
            self.rdm.addActionData(action_chunk, timestamp_chunk)
            if self.config.show_data:
                for action in action_chunk:
                    self.action_queue.put(action[0])
            self.inference_count += 1
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
            self.rdm.addActionData(action_chunk, timestamp_chunk)
            if self.config.show_data:
                for action in action_chunk:
                    self.action_queue.put(action[0])
            self.inference_count += 1
        else:
            print("没有观测数据，跳过推理")

    def controlThreadFun(self):
        print('控制线程已启动...')
        while self.running:
            # popActionData函数是线程安全的，不需要加锁
            start_time = time.time()
            action_chunk, timestamp_chunk = self.rdm.popActionData()
            if action_chunk is not None:
                # print(f'action_chunk shape: {action_chunk.shape}')
                # print(action)
                # print(action['ref_timestamp'])
                # print(action['pred_action'])
                # for action in action_chunk:
                self.robot.controlRobot(action_chunk)
                end_time = time.time()
                time_diff = end_time - start_time
                if time_diff < self.config.controller.control_period/1000:
                    time.sleep(self.config.controller.control_period/1000 - time_diff)
            else:
                # print("没有动作数据，跳过控制")
                time.sleep(0.010)
                continue
            # 获取当前时间戳
    
    def interpolateThreadFun(self):
        print('轨迹插值线程已启动...')
        while self.running:
            # popActionData函数是线程安全的，不需要加锁
            start_time = time.time()
            action_chunk, timestamp_chunk = self.rdm.popActionData()
            if action_chunk is not None:
                # print(f'action_chunk shape: {action_chunk.shape}')
                # print(action)
                # print(action['ref_timestamp'])
                # print(action['pred_action'])
                # for action in action_chunk:
                self.traj_generator.addWayPoint(action_chunk)
                end_time = time.time()
                time_diff = end_time - start_time
                # 根据control_period控制轨迹执行的时间
                if time_diff < self.config.controller.control_period/1000:
                    time.sleep(self.config.controller.control_period/1000 - time_diff)
            else:
                print("没有动作数据，跳过轨迹插值")
                time.sleep(0.010)
                continue
            # 获取当前时间戳

    def processData(self, frame):
        start_time = time.time()
        img_head = misc.crop_and_resize(frame['obs.cam.head'])
        img_hand_left = misc.crop_and_resize(frame['obs.cam.hand_left'])
        img_hand_right = misc.crop_and_resize(frame['obs.cam.hand_right'])
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
                'annotation.human.action.task_description': ['pour milk'],
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
                timestamp =  ref_timestamp + self.config.controller.control_period * index * 1000000
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
        self.interpolate_thread.start()
        # self.control_thread.start()

        if self.config.show_data:
            self.show_action_data()

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
        self.interpolate_thread.join(timeout=1.0)
        self.control_thread.join(timeout=1.0)
        print('推理框架客户端已关闭。')

    def close(self):
        with self.thread_lock:
            self.running = False
        self.observe_thread.join(timeout=1.0)
        self.inference_thread.join(timeout=1.0)
        self.interpolate_thread.join(timeout=1.0)
        self.control_thread.join(timeout=1.0)
        self.zmq_client.close()
        self.traj_generator.close()
    
    def show_action_data(self,):
        plt.ion()  # 开启交互模式
        fig, ax = plt.subplots()
        x_data, y_data = [], []

        def update_plot(frame):
            if not self.action_queue.empty():
                data = self.action_queue.get()
                x_data.append(frame)
                y_data.append(data)
                ax.clear()
                ax.plot(x_data, y_data)
            return ax,

        ani = plt.FuncAnimation(fig, update_plot, frames=range(16), blit=True, interval=50)
        plt.show()


if __name__ == "__main__":
    pass