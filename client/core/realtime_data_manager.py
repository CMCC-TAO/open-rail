import time
from collections import deque
from ml_collections import ConfigDict
class RealtimeDataManager():
    def __init__(self, rdm_config: ConfigDict):
        self.rdm_config = rdm_config
        self.observe_buffer = deque(maxlen=rdm_config.max_len)
        self.action_chunks = []
        self.timestamp_chunks = []
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
            self.observe_buffer.append(frame)
    
    def addActionData(self, action_chunk, timestamp_chunk):
        # 第一次添加数据的时候，记录初始时间戳,作为控制的开始时间
        if self.init_control_timestamp is None:
            self.init_control_timestamp = timestamp_chunk[0]
            self.start_time = time.time()
        else:
            self.currt_time = time.time()
            time_duration = int((self.currt_time - self.start_time) * 1e9)
            currt_timestamp = self.init_control_timestamp + time_duration
            print(f'currt_timestamp: {currt_timestamp}')
            # print(f'time duration in local: {(self.currt_time - self.start_time) * 1000} ms')
            # print(f'time duration in a2d: {(timestamp_chunk[0] - self.init_control_timestamp) / 1e6} ms')
        self.action_chunks.append(action_chunk)
        self.timestamp_chunks.append(timestamp_chunk)
        print(f'timestamp_chunks: {timestamp_chunk}')
    
    def getActionData(self):
        if self.action_chunks:
            return self.action_chunks.pop(), self.timestamp_chunks.pop()
        else:
            return None, None
    def getObserveData(self):
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