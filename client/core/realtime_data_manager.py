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

        self.currt_timestamp = None


    def add(self, msg):
        # 将传入的消息msg添加到buffer列表中
        self.observe_buffer.append(msg)
        self.observe_buffer.pop()

    def get_closest(self, target_stamp):
        # 找到时间最接近的消息
        closest = min(self.buffer, key=lambda x: abs(x['timestamp'] - target_stamp))
        return closest