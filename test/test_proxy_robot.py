"""Temporary fake robot used to validate client/robots/robot_proxy.py.

Deleted after the validation run.
"""

import time

import numpy as np

from client.robots.base_robot import RobotBase


class RobotBody(RobotBase):
    def __init__(self, config):
        super().__init__(config)
        self.n = 0
        self.closed = False

    def retrieve_observation(self):
        time.sleep(0.02)
        self.n += 1
        if self.n % 5 == 0:
            return None
        self.current_state = np.arange(self.state_dim, dtype=np.float32) + self.n
        return {
            'ref_timestamp': 1_700_000_000_000_000_000 + self.n * 20_000_000,
            'obs.state': self.current_state.copy(),
            'cam.head': np.full((48, 64, 3), self.n % 255, dtype=np.uint8),
            'cam.hand_left': np.full((24, 32, 3), (self.n + 1) % 255, dtype=np.uint8),
        }

    def control_robot(self, action):
        return len(np.asarray(action).ravel())

    def execute_action(self, data):
        return 'exec-ok'

    def _control_robot(self, data):
        return None

    def reset_robot(self, target_pose=None, mode='default'):
        return f'reset:{mode}'

    def close(self):
        self.closed = True
