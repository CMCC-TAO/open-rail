from collections import deque
from ml_collections import ConfigDict
class RealtimeDataManager():
    def __init__(self, rdm_config: ConfigDict):
        self.rdm_config = rdm_config
        self.observe_buffer = deque(maxlen=rdm_config.max_len)
        self.control_buffer = []
        if rdm_config.record_data:
            pass #

        if rdm_config.show_data:
            pass #

        self.init_timestamp = None
        self.frame_count = 0
        self.currt_timestamp = None


    def addObserveData(self, frame):
        # 将传入的消息msg添加到buffer列表中
        self.frame_count += 1
        # 前面几帧数据不稳定，丢弃
        if self.init_timestamp is None and self.frame_count > 5:
            self.init_timestamp = frame['ref_timestamp']
            self.frame_count = 1
        if self.init_timestamp is not None:
            self.observe_buffer.append(frame)
        
        # print(f'frame_count: {self.frame_count}, observe_buffer len: {len(self.observe_buffer)}')
    
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