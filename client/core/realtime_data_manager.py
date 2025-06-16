import copy
import time
import threading
from collections import deque
from ml_collections import ConfigDict

from client.utils.util import run_time_decorator
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
        self.polynomial_thread_lock = threading.Lock()
        if rdm_config.record_data:
            pass #

        # if rdm_config.show_data:
        #     pass #
        # self.action_data_received = False

        self.init_observe_timestamp = None # TimeStamp of the first observe data received
        self.init_control_timestamp = None # TimeStamp of the first action received
        self.init_control_time = None # Local PC time of the first action received
        # self.currt_time = None
        self.frame_count = 0
        self.action_chunk_fitted = None
        self.timestamps_fitted = None
        self.action_chunk_index = None


    def addObserveData(self, frame):
        # 将传入的消息msg添加到buffer列表中
        self.frame_count += 1
        # 前面几帧数据不稳定，丢弃
        if self.init_observe_timestamp is None and self.frame_count > 5:
            self.init_observe_timestamp = frame['ref_timestamp']
            self.frame_count = 1
        if self.init_observe_timestamp is not None:
            with self.observe_thread_lock:
                self.observe_buffer.append(frame)
    
    def addActionData(self, action_chunk, timestamp_chunk):
        # 第一次添加数据的时候，记录初始时间戳,作为控制的开始时间
        if self.init_control_timestamp is None or len(self.action_chunks) == 0:
            self.init_control_timestamp = timestamp_chunk[0]
            self.init_control_time = time.time()
            print(f'init_control_timestamp: {self.init_control_timestamp}, init_observe_timestamp: {self.init_observe_timestamp}')
            # 首次添加数据，直接添加到action_chunks和timestamp_chunks中
            timestamp_chunk_new = [(timestamp -self.init_control_timestamp) / 1e9 for timestamp in timestamp_chunk]
            with self.action_thread_lock:
                self.action_chunks.extend(action_chunk)
                self.timestamp_chunks.extend(timestamp_chunk_new)
            print(f'timestamp_chunks: {self.timestamp_chunks}')
        else:
            # self.currt_time = time.time()
            # time_duration = int((self.currt_time - self.init_control_time) * 1e9)
            # print(f'currt_timestamp: {time_duration}')
            # print(f'time duration in local: {(self.currt_time - self.init_control_time) * 1000} ms')
            # print(f'time duration in a2d: {(timestamp_chunk[0] - self.init_control_timestamp) / 1e6} ms')
            # 新的action_chunk需要跟已有的进行融合
            # 首先对齐时间戳
            timestamp_chunk_new = [(timestamp -self.init_control_timestamp) / 1e9 for timestamp in timestamp_chunk]
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
    
    def popActionData(self, num_samples=32):
        # 确保线程安全
        with self.action_thread_lock:
            action_chunk_size = len(self.action_chunks)
            if self.action_chunks:
                return self.action_chunks.pop(0), self.timestamp_chunks.pop(0)
            else:
                return None, None
    
    def popActionChunk(self, num_samples=32):
        # 进行两部分工作：
        # 1. 准备用于轨迹曲线拟合的数据；
        # 2. 管理ActionChunk和Timestamps队列，丢弃掉过期数据；
        # 备注： 过期数据指的是时间戳在当前时间之前的数据
        currt_time = time.time() - self.init_control_time
        print(f'currt_time: {currt_time}')
        # 找到首帧有效数据的index
        valid_index = None
        for index, timestamp in enumerate(self.timestamp_chunks):
            if timestamp > currt_time:
                valid_index = index
                break
        if valid_index is None:
            # TODO:  处理无有效数据
            print("[Error] No valid data in action chunk.")
            return None
        # 数据拟合需要往前找3帧，防止出现拟合结果不平顺的情况，TODO：可以将这部分变成可配置的参数
        start_index = max(0, valid_index - 16)
        end_index = min(len(self.action_chunks), start_index + num_samples)
        # 使用deepcopy防止丢弃过期数据后丢失数据
        timestamps = copy.deepcopy(self.timestamp_chunks[start_index:end_index])
        action_chunks = copy.deepcopy(self.action_chunks[start_index:end_index])
        start_time = self.timestamp_chunks[start_index]
        end_time = self.timestamp_chunks[end_index - 1]

        # 丢掉过期数据，需要保证线程安全
        # with self.action_thread_lock:
        #     del self.action_chunks[:valid_index]
        #     del self.timestamp_chunks[:valid_index]
        
        print(f'timestamps for curve fitting: {timestamps}, start_time: {start_time}, end_time: {end_time}')
        return timestamps, action_chunks, start_time, end_time
    def getCurrentTime(self):
        return time.time() - self.init_control_time
    
    def updateActionChunkFitted(self, action_chunk_fitted, timestamps_fitted):
        with self.polynomial_thread_lock:
            # 更新index
            if self.action_chunk_index is None:
                self.action_chunk_index = -1
            else:
                currt_timestamp = self.timestamps_fitted[self.action_chunk_index]
                self.action_chunk_index = self.get_closest_index(timestamps_fitted, currt_timestamp)
                print(f'action_chunk_index: {self.action_chunk_index}')
                print(f'currt_timestamp: {currt_timestamp}, update_timestamp: {timestamps_fitted[self.action_chunk_index]}')
                # self.action_chunk_index = offset
            self.action_chunk_fitted = action_chunk_fitted
            self.timestamps_fitted = timestamps_fitted
            # print(f'action_chunk_index: {self.action_chunk_index}')
            # print(f'action_chunk_fitted shape: {self.action_chunk_fitted.shape}')
            # print(f'action_chunk_fitted: {self.action_chunk_fitted[:, -2]}')
            # print(f'action_chunk_fitted: {self.action_chunk_fitted[:, -1]}')
    
    def getActionFitted(self):
        with self.polynomial_thread_lock:
            if self.action_chunk_index is None:
                return None
            self.action_chunk_index = min(self.action_chunk_index + 1, self.action_chunk_fitted.shape[1] - 1)
            return self.action_chunk_fitted[:, self.action_chunk_index]
    
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
    
    @run_time_decorator
    def get_closest_index(self, timestamp_list, target_timestamp):
        # 计算每个元素与目标值的差值的绝对值
        differences = [abs(timestamp - target_timestamp) for timestamp in timestamp_list]
        # 找到最小差值的索引
        closest_index = differences.index(min(differences))
        return closest_index# 数据可视化函数
    