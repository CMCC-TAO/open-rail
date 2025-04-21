from collections import deque
from ml_collections import ConfigDict
class RealtimeDataManager():
    def __init__(self, rdm_config: ConfigDict):
        self.rdm_config = rdm_config
        self.observe_buffer = deque(maxlen=rdm_config.max_len)
        if rdm_config.record_data:
            pass #

    def add(self, msg):
        self.buffer.append(msg)

    def get_closest(self, target_stamp):
        # 找到时间最接近的消息
        closest = min(self.buffer, key=lambda x: abs(x['timestamp'] - target_stamp))
        return closest