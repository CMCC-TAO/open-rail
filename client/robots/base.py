import time
import cv2
import numpy as np
# from collections import deque
from ml_collections import ConfigDict
# from utils import misc

class RobotBase():
    def __init__(self, observer_config: ConfigDict, controller_config: ConfigDict):
        # self.name_cameras = ['head', 'hand_left', 'hand_right']
        self.observer_config = observer_config
        self.controller_config = controller_config
        # self.name_cameras = ['head', 'hand_left', 'hand_right']
        self.currt_timestamp = 0
        # self.obs_buffer = deque(maxlen=10)
        # time.sleep(1)

    def control_robot(self, data):
        print(data)

    def retrieve_observation(self):
        return None

    # def get_obs_buffer(self):
    #     return self.obs_buffer

    def close(self):
        pass
