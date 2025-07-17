from enum import Enum
from ml_collections import ConfigDict

class RobotType(str, Enum):
    A2D = 'a2d'
    MOCK = 'mock'

def get_a2d_config():
    config = ConfigDict()
    config.camera = ConfigDict()
    config.camera.ref = 'head'
    # ConfigDict不能使用带点的key，change 'cam.head' to 'head'
    config.camera.names = {'head': 'head',
                           'hand_left': 'hand_left',
                           'hand_right': 'hand_right',
                           # depth_head: 'head_depth'
                           }
    config.proprio_names = ['arm', 'gripper', 'head', 'waist']
    config.gripper_freq = 40
    return config

def get_mock_config():
    config = ConfigDict()
    config.camera = ConfigDict()
    config.camera.ref = 'head'
    config.camera.names = {'head': 'observation.images.top_head',
                           'hand_left': 'observation.images.hand_left',
                           'hand_right': 'observation.images.hand_right'}
    config.root = '/home/robot/Music/task_39_only1'
    config.repo_id = 'task_39_only1'
    return config

def get_robots_config():
    config = ConfigDict()
    config.type = RobotType.A2D
    config.a2d = get_a2d_config()
    config.mock = get_mock_config()
    return config

if __name__ == '__main__':
    config = get_robots_config()
    print(config)