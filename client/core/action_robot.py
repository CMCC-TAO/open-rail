import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor
import threading
from scipy.interpolate import CubicSpline
from collections import deque
import queue

class RobotAction():
    def __init__(self, robot, client_vla, interpolation_factor=5, lookahead_idx=12, execution_rate=0.05):
        self.robot = robot
        self.client_vla = client_vla
        self.interpolation_factor = interpolation_factor
        self.lookahead_idx = lookahead_idx
        self.execution_rate = execution_rate

        self.action_queue = deque() # 动作缓存队列
        self.prediction_queue = queue.Queue() # 预测结果队列
        
        # 线程池用于异步预测
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        # 状态控制
        self.running = False
        self.current_chunk = None
        self.next_chunk = None
        self.prediction_in_progress = False
        self.prediction_lock = threading.Lock()
        
        # 记录当前执行到的位置
        self.current_idx = 0

    def initialize(self):
        initial_chunk = self.client_vla.get_vla_action() # 获取第一个动作块
        self.current_chunk = self.interpolate_chunk(initial_chunk)
        self.current_idx = 0
        self.action_queue.extend(self.current_chunk)
        self.predict_next_chunk() # 立即请求下一个动作块

    def interpolate_chunk(self, chunk):
        chunk_size, joint_dim = chunk.shape
        x = np.arange(chunk_size)
        x_new = np.linspace(0, chunk_size-1, chunk_size * self.interpolation_factor - (self.interpolation_factor - 1))
        smooth_chunk = np.zeros((len(x_new), joint_dim))
        # 对每个关节维度进行插值
        for joint in range(joint_dim):
            cs = CubicSpline(x, chunk[:, joint], bc_type='natural')
            smooth_values = cs(x_new)
            # 低通滤波器减少高频抖动
            if len(smooth_values) > 3:
                kernel = np.array([0.1, 0.2, 0.4, 0.2, 0.1])  # 简单kernel
                kernel = kernel / np.sum(kernel)  # 归一化
                padded = np.pad(smooth_values, (2, 2), mode='edge')
                filtered = np.convolve(padded, kernel, mode='valid')  # 卷积
                # 确保滤波后的长度与原始长度一致
                smooth_chunk[:, joint] = filtered[:len(x_new)]
            else:
                smooth_chunk[:, joint] = smooth_values
        return smooth_chunk
        
    def transition_between_chunks(self, chunk1, chunk2, transition_start_idx):
        if transition_start_idx >= len(chunk1):
            return chunk2
        remaining_actions = len(chunk1) - transition_start_idx
        transition_chunk = np.copy(chunk2)
        
        return transition_chunk
    
    def predict_next_chunk(self):
        with self.prediction_lock:
            if self.prediction_in_progress:
                return
            self.prediction_in_progress = True
        
        def prediction_task():
            try:
                next_chunk = self.client_vla.get_vla_action()
                smooth_next_chunk = self.interpolate_chunk(next_chunk)
                self.prediction_queue.put(smooth_next_chunk)
            finally:
                with self.prediction_lock:
                    self.prediction_in_progress = False
        # 提交预测任务到线程池
        self.executor.submit(prediction_task)
    
    def check_and_request_next_chunk(self):
        actual_lookahead = self.lookahead_idx * self.interpolation_factor
        if self.current_idx >= actual_lookahead and not self.prediction_in_progress:
            self.predict_next_chunk()
        try:
            new_chunk = self.prediction_queue.get_nowait()
            if self.current_idx < len(self.current_chunk):
                # 计算从哪个索引开始应该使用新块
                offset_in_new_chunk = self.current_idx - actual_lookahead
                if offset_in_new_chunk < 0:
                    offset_in_new_chunk = 0
                
                # 创建过渡块
                transition_chunk = self.transition_between_chunks(
                    self.current_chunk, 
                    new_chunk, 
                    self.current_idx
                )
                
                # 清空队列并添加过渡后的动作
                self.action_queue.clear()
                self.action_queue.extend(transition_chunk[offset_in_new_chunk:])
            else:
                # 当前块已执行完毕，直接使用新块
                self.action_queue.clear()
                self.action_queue.extend(new_chunk)
            
            self.current_chunk = new_chunk
            self.current_idx = 0
        except queue.Empty:
            pass
    
    def get_next_action(self):
        if not self.action_queue:
            # 如果队列为空，返回最后一个已知动作
            if hasattr(self, 'last_action'):
                return self.last_action
            else:
                # 如果没有最后一个动作，返回全零动作
                return np.zeros(14)
        
        action = self.action_queue.popleft()
        self.last_action = action
        self.current_idx += 1
        return action
    
    def execute_action(self, action):
        print(f"执行动作: {action[:3]}...，共 {len(action)} 维")
        self.robot.control_robot(action)
    
    def run(self):
        self.running = True
        self.initialize()
        try:
            while self.running:
                self.check_and_request_next_chunk()
                action = self.get_next_action()
                self.execute_action(action)
        except KeyboardInterrupt:
            print("执行中断")
        finally:
            self.running = False
            self.executor.shutdown()
            print("执行循环已停止")
    
    def stop(self):
        self.running = False
