import cv2
import time
import threading
from ml_collections import ConfigDict

# from core.obs_robot import RobotObs
# from core.action_robot import RobotAction
from ..robots.base import RobotBase
from ..utils import misc
from .zmq_client import ZMQClient
from .realtime_data_manager import RealtimeDataManager

# VLA客户端
class VLAClient():
    def __init__(self, config: ConfigDict, rdm: RealtimeDataManager, zmq_client: ZMQClient, robot: RobotBase):
        self.config = config
        self.rdm = rdm
        self.zmq_client = zmq_client
        self.robot = robot
        self.running = False

        self.observe_thread = threading.Thread(target=self.observeThreadFun, daemon=True)
        self.inference_thread = threading.Thread(target=self.inferenceThreadFun, daemon=True)
        self.control_thread = threading.Thread(target=self.controlThreadFun, daemon=True)
        
        self.thread_lock = threading.Lock()
        self.receive_callback = None
        self.inference_count = 0
        # self.set_receive_callback(self.receive_callback)
        # self.server_received_buffer = deque(maxlen=10)

    def observeThreadFun(self):
        print('观测线程已启动...')
        while self.running:
            observations = self.robot.retrieve_observation()
            if observations is not None:
                # print(observations.keys())
                # print(observations['ref_timestamp'])
                # print(observations['obs.state'])
                with self.thread_lock:
                    self.rdm.addObserveData(observations)
            time.sleep(0.001)  # 控制循环频率
    
    def inferenceThreadFun(self):
        print('推理线程已启动...')
        while self.running:
            if self.inference_count == 0:
                # 第一次推理
                with self.thread_lock:
                    frame = self.rdm.getObserveData()
                if frame is not None:
                    data = self.prepareData(frame)
                    self.zmq_client.sendMessage(data)
                    result = self.zmq_client.recvMessage()
                    print(result)
                    self.inference_count += 1
                else:
                    print("没有观测数据，跳过推理")
                    time.sleep(0.010)
                    continue
            elif self.inference_count == 1:
                # 第二次推理
                print(f'wait time: {self.config.controller.time_delay/1000}')
                time.sleep(self.config.controller.time_delay/1000)
                with self.thread_lock:
                    frame = self.rdm.getObserveData()
                if frame is not None:
                    data = self.prepareData(frame)
                    self.send_message(data)
                    result = self.receive_messages()
                    print(result)
                    self.inference_count += 1
                else:
                    print("没有观测数据，跳过推理")
                    time.sleep(0.010)
                    continue
            else:
                # 后续推理，贪心
                with self.thread_lock:
                    frame = self.rdm.getObserveData()
                if frame is not None:
                    data = self.prepareData(frame)
                    self.send_message(data)
                    result = self.receive_messages()
                    print(result)
                    self.inference_count += 1
                else:
                    print("没有观测数据，跳过推理")
                    time.sleep(0.010)
                    continue
            # 请求服务端推理最新指定时间戳的obs
            # time.sleep(0.001)
    
    def controlThreadFun(self):
        print('控制线程已启动...')
        pass

    def prepareData(self, frame):
        img_head = misc.crop_and_resize(frame['obs.cam.head'])
        img_hand_left = misc.crop_and_resize(frame['obs.cam.hand_left'])
        img_hand_right = misc.crop_and_resize(frame['obs.cam.hand_right'])
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
        return data

    def run(self):
        with self.thread_lock:
            self.running = True
    
        # 启动线程
        self.observe_thread.start()
        self.inference_thread.start()
        self.control_thread.start()

        # 等待线程结束
        self.observe_thread.join()
        self.inference_thread.join()
        self.control_thread.join()

        print('推理框架客户端已启动。')
    
    
    def stop(self):
        with self.thread_lock:
            self.running = False
        self.observe_thread.join(timeout=1.0)
        self.inference_thread.join(timeout=1.0)
        self.control_thread.join(timeout=1.0)
        print('推理框架客户端已关闭。')

    def close(self):
        with self.thread_lock:
            self.running = False
        self.zmq_client.close()


if __name__ == "__main__":
    pass