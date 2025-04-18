import time
import threading
import cv2
import numpy as np
from collections import deque
from utils import misc

# 对于没提供get_obs_nearest进行软同步的机器人，使用类似的方法自行实现
class MessageBuffer:
    def __init__(self, maxlen=100):
        self.buffer = deque(maxlen=maxlen)

    def add(self, msg):
        self.buffer.append(msg)

    def get_closest(self, target_stamp):
        # 找到时间最接近的消息
        closest = min(self.buffer, key=lambda x: abs(x['timestamp'] - target_stamp))
        return closest

class RobotObs():
    def __init__(self, robot, client_vla):
        self.robot = robot
        self.client_vla = client_vla
        self.obs_thread = threading.Thread(target=self.send_obs_thread)
        self.threading_lock = threading.Lock()

    def send_obs_thread(self):
        while True:
            try:
                # time.sleep(1)
                # obs = None
                with self.threading_lock:
                    obs = self.robot.get_obs_nearest()
                if obs is None:
                    continue
                img_head = misc.crop_and_resize(obs['obs.cam.head'])
                img_hand_left = misc.crop_and_resize(obs['obs.cam.hand_left'])
                img_hand_right = misc.crop_and_resize(obs['obs.cam.hand_right'])
                data = {
                    'type': 'vla',
                    'img_keys': ['cam.head', 'cam.hand_left', 'cam.hand_right'],
                    'ref_timestamp': obs['ref_timestamp'],
                    'obs': {
                        'cam.head': cv2.imencode('.jpg', img_head)[1],
                        'cam.hand_left': cv2.imencode('.jpg', img_hand_left)[1],
                        'cam.hand_right': cv2.imencode('.jpg', img_hand_right)[1],
                        'state': obs['obs.state'],
                        'annotation.human.action.task_description': ['pour milk'],
                    },
                }
                self.client_vla.send_message(data)
            except Exception as e:
                print(f"send_obs_thread出错: {e}")
                import traceback
                traceback.print_exc()

    def run(self):
        self.obs_thread.start()