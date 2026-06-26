from enum import Enum
from ml_collections import ConfigDict

class RobotType(str, Enum):
    A2D = 'a2d'
    MOCK = 'mock'
    NAVI_WA2 = 'navi_wa2'

def get_a2d_config():
    """Generate configuration for A2D robot.
    
    Returns:
        ConfigDict: Configuration dictionary containing camera settings,
                   proprioception names, and gripper frequency for A2D robot.
    """
    config = ConfigDict()
    config.hand_type = 'gripper' # 'gripper' or 'hand_as_gripper' or 'hand'
    config.camera = ConfigDict()
    config.camera.ref = 'head'
    # ConfigDict cannot use dotted keys, so 'cam.head' becomes 'head'
    
    config.camera.names = {'head': 'head',
                           'hand_left': 'hand_left_fisheye' if 'hand' in config.hand_type else 'hand_left',
                           'hand_right': 'hand_right_fisheye' if 'hand' in config.hand_type else 'hand_right'}
    config.proprio_names = ['arm', 'hand' if 'hand' in config.hand_type else 'gripper', 'head', 'waist']
    config.gripper_freq = 40
    config.head_freq = 40
    config.reset_robot_pos = [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.4012, 27.0] + [0.0, 0.0] # default pose (teleoperation default pose)
    config.action_layout = {
        'arm': {'start': 0, 'end': 14, 'policy': 'gradual'},
        'gripper': {'start': 14, 'end': 16, 'policy': 'stepwise'},
        # 'head': {'start': 16, 'end': 18, 'policy': 'gripper'},
        # 'waist': {'start': 18, 'end': 20, 'policy': 'gripper'},
    }
    return config

def get_mock_config():
    """Generate configuration for mock robot (simulation/testing).
    
    Returns:
        ConfigDict: Configuration dictionary containing camera mappings,
                   data root path, and repository ID for mock robot.
    """
    config = ConfigDict()
    config.camera = ConfigDict()
    # config.hand_type = 'gripper' # 'gripper' or 'hand_as_gripper' or 'hand'
    config.camera.ref = 'head'
    config.camera.names = {'head': 'observation.images.head_rgb',
                           'hand_left': 'observation.images.left_wrist_rgb',
                           'hand_right': 'observation.images.right_wrist_rgb'}
    config.action_layout = {
        'arm': {'start': 0, 'end': 16, 'policy': 'gradual'},
        'gripper': {'start': 16, 'end': 28, 'policy': 'stepwise'},
        # 'head': {'start': 16, 'end': 18, 'policy': 'gripper'},
        # 'waist': {'start': 18, 'end': 20, 'policy': 'gripper'},
    }
    config.state_action_range = [[0, 16], [58, 70]]
    config.dataset_path = '/home/lza/code/dataset/use_coffee_machine/zjrobot_v3_handpose/2026-0411-pick_coffee_left'
    # config.dataset_path = '/home/robot/Music'
    return config

def get_navi_wa2_config():
    config = ConfigDict()
    config.tt = 0.033
    config.gain = 900
    config.camera = ConfigDict()
    config.camera.topic_dict = {
        'head': '/zj_humanoid/sensor/realsense_head/color/image_raw/compressed',
        'hand_left': '/zj_humanoid/sensor/left_wrist/image_raw/compressed',
        'hand_right': '/zj_humanoid/sensor/right_wrist/image_raw/compressed',
    }
    config.action_layout = {
        'arm': {'start': 0, 'end': 16, 'policy': 'gradual'},
        'hand': {'start': 16, 'end': 28, 'policy': 'stepwise'}
        }
    config.reset_position = [0.182591655739083, 0.32575521044236666, 0.639202615644364, 0.03292066673111549, -1.9789475037079458, 0.5495126798768879, -0.1635420177877668, -0.039264356176110845,-0.22653780968994397, 0.19016568609004025, -0.6990877950829599, 0.17601231608296075, -1.888115764960776, -0.5459413807557212, -0.38742182124429064, -0.27196253226160444]+\
        [-0.6062110066413879, 0.9023351669311523, 0.006108652334660292, 0.006108652334660292, 0.00901753455400467, 0.015126187354326248,-0.5980661511421204, 0.8994263410568237, 0.012217304669320583, 0.006108652334660292, 0.004363323096185923, 0.0]

    return config

def get_robots_config():
    """Generate configuration for all supported robot types.
    
    This function creates a comprehensive configuration dictionary that includes
    settings for all supported robot types and specifies which robot type
    to use by default.
    
    Returns:
        ConfigDict: Configuration dictionary containing:
            - type: Default robot type to use
            - a2d: A2D robot configuration
            - mock: Mock robot configuration for testing
    """
    config = ConfigDict()
    config.type = RobotType.A2D
    config.a2d = get_a2d_config()
    config.mock = get_mock_config()
    config.navi_wa2 = get_navi_wa2_config()
    return config

if __name__ == '__main__':
    config = get_robots_config()
    print(config)
