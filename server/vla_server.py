import os
import zmq
import time
import json
import pickle
import numpy as np
import threading
import cv2
import queue
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor
from collections import deque
# from .models.gr00t import vla_model
class VLAServer:
    def __init__(self, config: ConfigDict, model = None):
        self.config = config
        self.model = model
        self.context = zmq.Context()
        # 创建ROUTER套接字，除了ROUTER还有很多其他模式，比如PAIR一对一模式
        self.router = self.context.socket(zmq.ROUTER)
        # self.router.setsockopt(zmq.SNDTIMEO, 5000)  # 5秒超时
        self.router.setsockopt(zmq.SNDHWM, 1)  # 设置发送缓冲区为1条消息
        self.router.bind(config.zmq_addr)
        print(f"zmq server: {config.zmq_addr}, is started...")
        self.client_id = None # 客户端标识 TODO： 支持多客户端并发请求

        # self.sequence_manager = SequenceManager()
        self.running = False
        self.last_inference_time = 0
        
        # 创建线程池用于处理推理任务
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        # 创建推理任务队列，避免重复提交相同的推理任务
        # self.inference_queue = queue.Queue()
        # self.inference_in_progress = False
        # 创建锁来保护inference_in_progress变量
        self.thread_lock = threading.Lock()
        
        # # 启动推理任务处理线程
        # self.inference_thread = threading.Thread(target=self._process_inference_queue)
        # self.inference_thread.daemon = True
        # self.inference_thread.start()
        
        self.receive_thread = threading.Thread(target=self.receive_thread_fun, daemon=True)

    def run(self):
        # 启动接收线程
        self.running = True
        self.receive_thread.start()
        # 等待线程结束
        self.receive_thread.join()
    
    def inference(self, data):
        try:
            # 解码图像数据，TODO： 1. 多线程解码，提升效率; 2. 支持多帧数据
            img_keys = data['img_keys']
            for img_key in img_keys:
                data['obs'][img_key] = cv2.imdecode(data['obs'][img_key], cv2.IMREAD_COLOR)
            
            # 提交推理任务到线程池
            future = self.executor.submit(self.model.infer, data)
            future.add_done_callback(self.inference_callback)
        except Exception as e:
            print(f"处理推理队列时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def inference_callback(self, future):
        try:
            result = future.result() # 获取线程结果
            self.send_message(result)
        except Exception as e:
            print(f"推理回调时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def receive_thread_fun(self):
        print('Start to receive data and infer...')
        while self.running:
            try:
                # 接收消息（阻塞），ROUTER套接字接收消息时会包含发送者的标识和多部分消息
                parts = self.router.recv_multipart()
                self.client_id = parts[0] # 0是客户端标识
                # message_obj = {}
                if len(parts) >= 2:
                    data = pickle.loads(parts[1]) # 1是二进制数据
                    meta = json.loads(parts[2].decode('utf8')) # 2是元数据JSON
                # print(f"收到消息: {message_obj.keys()}")
                self.inference(data)
            except Exception as e:
                print(f"接收消息时出错: {e}")
                import traceback
                traceback.print_exc()
    
    def send_message(self, data, meta={}):
        try:
            # client_id = self.client_identities.get(Config.MAIN_CLIENT_ID)
            if self.client_id is None:
                print("未找到client标识，无法发送消息")
                return
            # 图像send前需编码：_, img_encoded = cv2.imencode('.jpg', data), 收到需要解码: img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            data = pickle.dumps(data) # data字典转为字节流
            meta = json.dumps(meta).encode('utf8')
            self.router.send_multipart([self.client_id, data, meta], flags=zmq.NOBLOCK) # 非阻塞发送
        except Exception as e:
            print(f"发送消息时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def close(self):
        # 关闭线程
        with self.thread_lock:
            self.running = False
        self.executor.shutdown(wait=False)
        self.router.close()
        self.context.term()


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
