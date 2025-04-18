import os
import zmq
import time
import json
import pickle
import numpy as np
import threading
import cv2
import queue
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from models.gr00t import vla_model

class Config:
    SEQUENCE_LENGTH = 8
    ZMQ_ADDR = 'tcp://*:5566'
    MAIN_CLIENT_ID = 'ZROBOT'
    MAX_WORKERS = 2  # 线程池最大工作线程数

class SequenceManager:
    def __init__(self, max_length=Config.SEQUENCE_LENGTH):
        self.max_length = max_length
        self.sequence = deque(maxlen=max_length)
        self.sequence_lock = threading.Lock()
        self.start_frame = -1
        self.end_frame = -1
    
    def add_data(self, data) -> int:
        with self.sequence_lock:
            self.sequence.append(data)
            return len(self.sequence)
        
    def remove_oldest(self) -> int:
        with self.sequence_lock:
            if self.sequence:
                self.sequence.popleft()
            return len(self.sequence)
    
    def get_sequence(self):
        with self.sequence_lock:
            return list(self.sequence)
    
    def clear(self):
        with self.sequence_lock:
            self.sequence.clear()

class ServerVLA:
    def __init__(self):
        self.context = zmq.Context()
        # 创建ROUTER套接字，除了ROUTER还有很多其他模式，比如PAIR一对一模式
        self.router = self.context.socket(zmq.ROUTER)
        # self.router.setsockopt(zmq.SNDTIMEO, 5000)  # 5秒超时
        self.router.setsockopt(zmq.SNDHWM, 1)  # 设置发送缓冲区为1条消息
        self.router.bind(Config.ZMQ_ADDR)
        self.client_identities = {} # 客户端标识

        self.sequence_manager = SequenceManager()
        self.model = vla_model.ModelVLA()
        self.running = True
        self.last_inference_time = 0
        
        # 创建线程池用于处理推理任务
        self.executor = ThreadPoolExecutor(max_workers=Config.MAX_WORKERS)
        # 创建推理任务队列，避免重复提交相同的推理任务
        self.inference_queue = queue.Queue()
        self.inference_in_progress = False
        # 创建锁来保护inference_in_progress变量
        self.inference_lock = threading.Lock()
        
        # 启动推理任务处理线程
        self.inference_thread = threading.Thread(target=self._process_inference_queue)
        self.inference_thread.daemon = True
        self.inference_thread.start()
    
    def _process_inference_queue(self):
        while self.running:
            try:
                # 从队列中获取推理任务（阻塞等待）
                sequence = self.inference_queue.get(timeout=1)
                with self.inference_lock:
                    self.inference_in_progress = True
                # 提交推理任务到线程池
                future = self.executor.submit(self.model.infer, sequence)
                future.add_done_callback(self._inference_callback)
                # 标记队列任务已处理
                self.inference_queue.task_done()
            except queue.Empty:
                time.sleep(0.001)
            except Exception as e:
                print(f"处理推理队列时出错: {e}")
                import traceback
                traceback.print_exc()
    
    def _inference_callback(self, future):
        try:
            result = future.result() # 获取线程结果
            self.send_message(result)
            with self.inference_lock:
                self.inference_in_progress = False
        except Exception as e:
            print(f"推理回调时出错: {e}")
            import traceback
            traceback.print_exc()
            
            # 确保在出错时也重置推理状态
            with self.inference_lock:
                self.inference_in_progress = False
    
    def receive_messages(self):
        while self.running:
            try:
                # 接收消息（阻塞），ROUTER套接字接收消息时会包含发送者的标识和多部分消息
                parts = self.router.recv_multipart()
                client_id = parts[0] # 0是客户端标识
                self.client_identities[Config.MAIN_CLIENT_ID] = client_id
                message_obj = {}
                if len(parts) >= 2:
                    message_obj['data'] = pickle.loads(parts[1]) # 1是二进制数据
                    message_obj['meta'] = json.loads(parts[2].decode('utf8')) # 2是元数据JSON
                self.process_received_message(message_obj)
            except Exception as e:
                print(f"接收消息时出错: {e}")
                import traceback
                traceback.print_exc()
    
    def process_received_message(self, message):
        data = message['data']
        if data['type'] == 'vla':
            img_keys = data['img_keys']
            for img_key in img_keys:
                data['obs'][img_key] = cv2.imdecode(data['obs'][img_key], cv2.IMREAD_COLOR)
            self.sequence_manager.add_data(data)
            self.send_message({'type': 'obs_received', 'ref_timestamp': data['ref_timestamp']})  # obs已收到，通知客户端可以保存
            # cv2.imwrite('received.jpg', data['obs'][img_keys[0]])
        elif data['type'] == 'get_vla_action':
            # 检查序列长度，如果达到要求且当前没有推理任务正在进行，则提交推理任务
            list_model_input = []
            ref_timestamp = data['ref_timestamp']
            sequence = self.sequence_manager.get_sequence()
            for i in range(len(sequence) - 1, -1, -1):
                # 以此倒查历史obs
                if sequence[i]['ref_timestamp'][0] == ref_timestamp[0]:
                    for j in range(data['history_length']):
                        list_model_input.append(sequence[i - j])
                    break
            if len(list_model_input) >0:
                with self.inference_lock:
                    if not self.inference_in_progress and self.inference_queue.empty():
                        self.inference_queue.put(list_model_input) # 添加到推理队列开始推理

    def send_message(self, data, meta={}):
        try:
            client_id = self.client_identities.get(Config.MAIN_CLIENT_ID)
            if not client_id:
                print("未找到client标识，无法发送消息")
                return
            # 图像send前需编码：_, img_encoded = cv2.imencode('.jpg', data), 收到需要解码: img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            data = pickle.dumps(data) # data字典转为字节流
            meta = json.dumps(meta).encode('utf8')
            self.router.send_multipart([client_id, data, meta], flags=zmq.NOBLOCK) # 非阻塞发送
        except Exception as e:
            print(f"发送消息时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def close(self):
        self.running = False
        self.executor.shutdown(wait=False)
        self.router.close()
        self.context.term()


if __name__ == "__main__":
    message_handler = ServerVLA()
    receive_thread = threading.Thread(target=message_handler.receive_messages)
    receive_thread.daemon = True
    receive_thread.start()
    print(f"原神server: {Config.ZMQ_ADDR}, 已启动...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序被中断")
    finally:
        message_handler.close()
