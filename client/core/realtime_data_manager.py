import copy
import time
import threading
from collections import deque
from ml_collections import ConfigDict
class RealtimeDataManager():
    def __init__(self, rdm_config: ConfigDict):
        self.rdm_config = rdm_config
        self.observe_buffer = deque(maxlen=rdm_config.max_len)
        # self.control_action_buffer = deque(maxlen=rdm_config.control_max_len)
        # self.control_timestamp_buffer = deque(maxlen=rdm_config.control_max_len)
        self.action_chunks = []
        self.timestamp_chunks = []
        self.action_thread_lock = threading.Lock()
        self.observe_thread_lock = threading.Lock()
        if rdm_config.record_data:
            pass #

        if rdm_config.show_data:
            pass #

        self.init_timestamp = None
        self.init_control_timestamp = None #A2D TimeStamp
        self.start_time = None # Local PC TimeStamp
        self.currt_time = None
        self.frame_count = 0


    def addObserveData(self, frame):
        # 将传入的消息msg添加到buffer列表中
        self.frame_count += 1
        # 前面几帧数据不稳定，丢弃
        if self.init_timestamp is None and self.frame_count > 5:
            self.init_timestamp = frame['ref_timestamp']
            self.frame_count = 1
        if self.init_timestamp is not None:
            with self.observe_thread_lock:
                self.observe_buffer.append(frame)
    
    def addActionData(self, action_chunk, timestamp_chunk):
        # 第一次添加数据的时候，记录初始时间戳,作为控制的开始时间
        if self.init_control_timestamp is None or len(self.action_chunks) == 0:
            self.init_control_timestamp = timestamp_chunk[0]
            self.start_time = time.time()
            # 首次添加数据，直接添加到action_chunks和timestamp_chunks中
            timestamp_chunk_new = [timestamp -self.init_control_timestamp for timestamp in timestamp_chunk]
            with self.action_thread_lock:
                self.action_chunks.extend(action_chunk)
                self.timestamp_chunks.extend(timestamp_chunk_new)
                print(f'timestamp_chunks: {self.timestamp_chunks}')
        else:
            self.currt_time = time.time()
            # time_duration = int((self.currt_time - self.start_time) * 1e9)
            # print(f'currt_timestamp: {time_duration}')
            # print(f'time duration in local: {(self.currt_time - self.start_time) * 1000} ms')
            # print(f'time duration in a2d: {(timestamp_chunk[0] - self.init_control_timestamp) / 1e6} ms')
            # 新的action_chunk需要跟已有的进行融合
            # 首先对齐时间戳
            timestamp_chunk_new = [timestamp -self.init_control_timestamp for timestamp in timestamp_chunk]
            # 确保线程安全
            with self.action_thread_lock:
                start_time = time.time()
                candidate_index = 0
                for index in range(len(timestamp_chunk_new)):
                    if timestamp_chunk_new[index] > self.timestamp_chunks[0]:
                        candidate_index = index
                        break
                assign_index = self.get_closest_index(self.timestamp_chunks, timestamp_chunk_new[candidate_index])
                # 然后进行融合
                target_chunk_len = len(self.timestamp_chunks)
                currt_chunk_len = len(action_chunk)
                for index in range(currt_chunk_len - candidate_index):
                    if assign_index + index < target_chunk_len:
                        self.action_chunks[assign_index + index] = (self.action_chunks[assign_index + index] + action_chunk[candidate_index + index]) / 2.0
                        self.timestamp_chunks[assign_index + index] = timestamp_chunk_new[candidate_index + index]
                    else:
                        self.action_chunks.append(action_chunk[candidate_index + index])
                        self.timestamp_chunks.append(timestamp_chunk_new[candidate_index + index])
                end_time = time.time()
                print(f'timestamp_chunks: {self.timestamp_chunks}')
                # print(f'动作融合花费时间: {(end_time - start_time) * 1000} ms')
    
    def popActionData(self):
        # 确保线程安全
        with self.action_thread_lock:
            if self.action_chunks:
                return self.action_chunks.pop(0), self.timestamp_chunks.pop(0)
            else:
                return None, None
    
    def getActionChunk(self):
        # 确保线程安全
        with self.action_thread_lock:
            return copy.copy(self.action_chunks)
    
    def getObserveData(self):
        with self.observe_thread_lock:
            if self.observe_buffer:
                return self.observe_buffer.pop()
            else:
                return None  # or handle the empty case appropriately
        # return self.observe_buffer.pop()
    
    def getObserveDataLeft(self):
        if self.observe_buffer:
            return self.observe_buffer.popleft()
        else:
            return None  # or handle the empty case appropriately

    def get_closest(self, target_stamp):
        # 找到时间最接近的消息
        closest = min(self.buffer, key=lambda x: abs(x['timestamp'] - target_stamp))
        return closest
    
    def get_closest_index(self, timestamp_list, target_timestamp):
        # 计算每个元素与目标值的差值的绝对值
        differences = [abs(timestamp - target_timestamp) for timestamp in timestamp_list]
        # 找到最小差值的索引
        closest_index = differences.index(min(differences))
        return closest_index# 数据可视化函数
    