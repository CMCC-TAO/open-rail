import cv2
import zmq
import time
import json
import threading
import pickle
from ml_collections import ConfigDict

# from core.obs_robot import RobotObs
# from core.action_robot import RobotAction
# from robots.a2d import robot_a2d
from utils import misc
from .realtime_data_manager import RealtimeDataManager

class BaseClient():
    def __init__(self, config: ConfigDict, rdm: RealtimeDataManager):
        self.config = config
        self.rdm = rdm
        self.context = zmq.Context()
        self.dealer = self.context.socket(zmq.DEALER)
        # self.dealer.setsockopt(zmq.SNDTIMEO, 5000)  # 5秒超时
        self.dealer.setsockopt(zmq.SNDHWM, 1)  # 设置发送缓冲区为1条消息
        self.dealer.connect(config.zmq_addr)
        print(f'zmq client: {config.zmq_addr} is started...')
        self.running = False
        self.observe_thread = threading.Thread(target=self.observe_thread_fun, daemon=True)
        # self.receive_thread.start()
        self.inference_thread = threading.Thread(target=self.inference_thread_fun, daemon=True)
        self.control_thread = threading.Thread(target=self.control_thread_fun, daemon=True)
        
        self.thread_lock = threading.Lock()
        self.receive_callback = None
        self.inference_count = 0

    def observe_thread_fun(self):
        pass
        # while self.running:
        #     with self.thread_lock:
        #         if self.observe_thread is not None:
        #             self.observe_thread()
        #         else:
        #             print("未设置observe_thread")
    
    def inference_thread_fun(self):
        pass

    def receive_messages(self):
        try:
            # 阻塞接收，在线程中使用
            if self.dealer.poll() != 0:
                message = {}
                parts = self.dealer.recv_multipart() # 接收多部分消息
                if len(parts) >= 2:
                    message['data'] = pickle.loads(parts[0]) # 0是二进制数据
                    message['meta'] = json.loads(parts[1].decode('utf8')) # 1是元数据JSON
                    return message
                else:
                    print("返回数据有问题")
                    return None
                    # with self.result_lock:
                    #     if self.receive_callback:
                    #         self.receive_callback(message_obj)
                    #     else:
                    #         print(f"收到消息，但未设置回调处理。msg: {message_obj}")
        except Exception as e:
            print(f"接收消息时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def send_message(self, data, meta={}):
        try:
            # 图像send前需编码：_, img_encoded = cv2.imencode('.jpg', data), 收到需要解码: img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            data = pickle.dumps(data) # data字典转为字节流
            meta = json.dumps(meta).encode('utf8')
            self.dealer.send_multipart([data, meta], flags=zmq.NOBLOCK) # 非阻塞发送
        except Exception as e:
            print(f"发送消息时出错: {e}")
            import traceback
            traceback.print_exc()

    def control_thread_fun(self):
        pass
        # while self.running:
        #     with self.thread_lock:
        #         if self.control_thread is not None:
        #             self.control_thread()
        #         else:
        #             print("未设置control_thread")
    
    def startAll(self):
        with self.thread_lock:
            self.running = True
        self.observe_thread.start()
        self.inference_thread.start()
        self.control_thread.start()
    
    def startObserve(self):
        with self.thread_lock:
            self.running = True
        self.observe_thread.start()
    
    def stopAll(self):
        with self.thread_lock:
            self.running = False
        self.observe_thread.join(timeout=1.0)
        self.inference_thread.join(timeout=1.0)
        self.control_thread.join(timeout=1.0)
        self.dealer.close()
        self.context.term()

    # def set_receive_callback(self, callback):
    #     self.receive_callback = callback

    
    # def receive_messages(self):
    #     while self.running:
    #         try:
    #             # 非阻塞接收，超时时间为10ms
    #             if self.dealer.poll(10) != 0:
    #                 message_obj = {}
    #                 parts = self.dealer.recv_multipart() # 接收多部分消息
    #                 if len(parts) >= 2:
    #                     message_obj['data'] = pickle.loads(parts[0]) # 0是二进制数据
    #                     message_obj['meta'] = json.loads(parts[1].decode('utf8')) # 1是元数据JSON

    #                     with self.result_lock:
    #                         if self.receive_callback:
    #                             self.receive_callback(message_obj)
    #                         else:
    #                             print(f"收到消息，但未设置回调处理。msg: {message_obj}")
    #         except Exception as e:
    #             print(f"接收消息时出错: {e}")
    #             import traceback
    #             traceback.print_exc()
    
    # def send_message(self, data, meta={}):
    #     try:
    #         # 图像send前需编码：_, img_encoded = cv2.imencode('.jpg', data), 收到需要解码: img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    #         data = pickle.dumps(data) # data字典转为字节流
    #         meta = json.dumps(meta).encode('utf8')
    #         self.dealer.send_multipart([data, meta], flags=zmq.NOBLOCK) # 非阻塞发送
    #     except Exception as e:
    #         print(f"发送消息时出错: {e}")
    #         import traceback
    #         traceback.print_exc()

    def close(self):
        self.running = False
        if self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
        self.dealer.close()
        self.context.term()

# VLA客户端
class VLAClient(BaseClient):
    def __init__(self, config: ConfigDict, rdm: RealtimeDataManager, robot):
        super().__init__(config, rdm)
        self.config = config
        # self.vla_data = None
        self.robot = robot
        # self.set_receive_callback(self.receive_callback)
        # self.server_received_buffer = deque(maxlen=10)

    def observe_thread_fun(self):
        while self.running:
            observations = self.robot.retrieve_observation()
            if observations is not None:
                # print(observations.keys())
                # print(observations['ref_timestamp'])
                # print(observations['obs.state'])
                with self.thread_lock:
                    self.rdm.addObserveData(observations)
            time.sleep(0.001)  # 控制循环频率
    
    def inference_thread_fun(self):
        while self.running:
            if self.inference_count == 0:
                # 第一次推理
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

if __name__ == "__main__":
    pass
    # robot = robot_a2d.RobotA2D()
    # client_vla = ClientVLA(robot)
    # robot_obs = RobotObs(robot, client_vla)
    # robot_obs.run()
    # robot_action = RobotAction(robot, client_vla)
    # robot_action.run()
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("程序被中断")
    # finally:
    #     robot.close()
    #     client_vla.close()

# # EXAMPLE: robot端按照下面的方式写
# if __name__ == "__main__":
#     import cv2
#     import numpy as np

#     vla_data = None

#     def receive_callback(message):
#         global vla_data
#         data = message['data']
#         if data['type'] == 'action':
#             # print(data)
#             vla_data = data
#         elif data['type'] == 'image_delay':
#             print(f"收发延迟：{time.time() - data['timestamp']}")

#     def get_vla_action():
#         global vla_data
#         vla_data = None
#         data = {'type': 'get_vla_action', 'timestamp': time.time()}
#         client_vla.send_message(data)
#         while True:
#             time.sleep(0.01)
#             if vla_data:
#                 return vla_data
    
#     def send_obs_thread():
#         while True:
#             try:
#                 ret, frame = cap.read()
#                 if not ret:
#                     print("Video stream ended or error reading frame.")
#                     break
#                 data = {
#                     'type': 'vla',
#                     'timestamp': time.time(),
#                     'img_keys': ['video.cam_right_high', 'video.cam_left_wrist', 'video.cam_right_wrist'],
#                     'obs': {
#                         "video.cam_right_high": cv2.imencode('.jpg', frame)[1],
#                         "video.cam_left_wrist": cv2.imencode('.jpg', frame)[1],
#                         "video.cam_right_wrist": cv2.imencode('.jpg', frame)[1],
#                         # "state.left_arm": np.random.rand(1, 7),
#                         # "state.right_arm": np.random.rand(1, 7),
#                         # "state.left_hand": np.random.rand(1, 1),
#                         # "state.right_hand": np.random.rand(1, 1),
#                         "state": np.random.rand(1, 20),
#                         "annotation.human.action.task_description": ["do your thing!"],
#                     },
#                 }
#                 client_vla.send_message(data)
#             except Exception as e:
#                 print(f"发送出错: {e}")
#                 import traceback
#                 traceback.print_exc()

#     cap = cv2.VideoCapture(6)
#     client_vla = ClientVLA()
#     client_vla.set_receive_callback(receive_callback)
#     obs_thread = threading.Thread(target=send_obs_thread)
#     obs_thread.daemon = True
#     obs_thread.start()
#     print(f'原神client: {Config.ZMQ_ADDR}, 已启动...')
#     try:
#         while True:
#             time.sleep(1)
#             if input('输入a请求action: ') == 'a':
#                 aaa = time.time()
#                 data = get_vla_action()
#                 print(time.time() - aaa, data['type'])
#     except KeyboardInterrupt:
#         print("程序被中断")
#     finally:
#         cap.release()
