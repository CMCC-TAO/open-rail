import os
import time
import numpy as np
import threading
import cv2
import queue
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from .zmq_server import ZMQServer
# from .models.gr00t import vla_model
# from ..models.gr00t import ModelVLA as GR00T
# from ..models.act import ModelVLA as ACT
class VLAServer:
    def __init__(self, config: ConfigDict, zmq_server: ZMQServer,  model= None):
        self.config = config
        self.zmq_server = zmq_server
        self.model = model

        # self.sequence_manager = SequenceManager()
        self.running = False
        self.last_inference_time = 0
        
        # 创建线程池用于处理推理任务
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        # 创建线程池用于并行解码图像数据
        self.image_decode_executor = ThreadPoolExecutor(max_workers=3)
        # 创建推理任务队列，避免重复提交相同的推理任务
        # self.inference_queue = queue.Queue()
        # self.inference_in_progress = False
        # 创建锁来保护inference_in_progress变量
        self.thread_lock = threading.Lock()
        
        # # 启动推理任务处理线程
        # self.inference_thread = threading.Thread(target=self._process_inference_queue)
        # self.inference_thread.daemon = True
        # self.inference_thread.start()
        
        self.receive_thread = threading.Thread(target=self.recvThreadFun, daemon=True)

    def run(self):
        # 启动接收线程
        self.running = True
        self.receive_thread.start()
        # 等待线程结束
        self.receive_thread.join()
    
    def image_decode(self, key, data):
        data['obs'][key] = cv2.imdecode(data['obs'][key], cv2.IMREAD_COLOR)
    
    def inference(self, data):
        try:
            # 解码图像数据，TODO： 1. 多线程解码，提升效率; 2. 支持多帧数据
            start_time = time.time()
            if isinstance(data, list):
                # TODO: 并行化处理
                for data_item in data:
                    cam_keys = [key for key in data_item['obs'] if 'cam.' in key]
                    images_data = [(key, data_item['obs'][key]) for key in cam_keys]
                    with ThreadPoolExecutor() as executor:
                        decoded_images = list(executor.map(lambda d: cv2.imdecode(d[1], cv2.IMREAD_ANYDEPTH if 'depth.' in d[0] else cv2.IMREAD_COLOR), images_data))
                    for key, img in zip(cam_keys, decoded_images):
                        data_item['obs'][key] = img
            else:
                # 使用线程池并行解码图像
                cam_keys = [key for key in data['obs'] if 'cam.' in key]
                images_data = [(key, data['obs'][key]) for key in cam_keys]
                with ThreadPoolExecutor() as executor:
                    decoded_images = list(executor.map(lambda d: cv2.imdecode(d[1], cv2.IMREAD_ANYDEPTH if 'depth.' in d[0] else cv2.IMREAD_COLOR), images_data))
                for key, img in zip(cam_keys, decoded_images):
                    data['obs'][key] = img
                print(f'data[obs] keys: {data.keys()}')
            # future.add_done_callback(self._inference_callback)
            end_time = time.time()
            # 计算并打印运行时间
            elapsed_time = (end_time - start_time) * 1000
            print(f"图像解码时间: {elapsed_time} ms")

            # cv2.imshow('head', data['obs']['cam.head'])
            # cv2.imshow('hand_left', data['obs']['cam.hand_left'])
            # cv2.imshow('hand_right', data['obs']['cam.hand_right'])
            # cv2.waitKey(1)
            # cv2.imwrite('head.jpg', data['obs']['cam.head'])
            # cv2.imwrite('hand_left.jpg', data['obs']['cam.hand_left'])
            # cv2.imwrite('hand_right.jpg', data['obs']['cam.hand_right'])
            # cv2.waitKey(1)
            # 提交推理任务到线程池
            future = self.executor.submit(self.model.infer, data if isinstance(data, list) else [data])
            future.add_done_callback(self.inference_callback)
        except Exception as e:
            print(f"处理推理队列时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def inference_callback(self, future):
        try:
            result = future.result() # 获取线程结果
            print(result)
            self.zmq_server.sendMessage(result)
        except Exception as e:
            print(f"推理回调时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def recvThreadFun(self):
        print('Start to receive data and infer...')
        while self.running:
            message = self.zmq_server.recvMessage()
            self.inference(message['data'])
        print('Stop to receive data...')
    
    def close(self):
        # 关闭线程
        with self.thread_lock:
            self.running = False
        self.executor.shutdown(wait=False)
        self.zmq_server.close()


# if __name__ == "__main__":
#     message_handler = VLAServer()
#     # receive_thread = threading.Thread(target=message_handler.receive_messages)
#     # receive_thread.daemon = True
#     # receive_thread.start()
#     # print(f"原神server: {Config.ZMQ_ADDR}, 已启动...")
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("程序被中断")
#     finally:
#         message_handler.close()
