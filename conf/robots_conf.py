from enum import Enum
from ml_collections import ConfigDict

class RobotType(str, Enum):
    A2D = 'a2d'
    MOCK = 'mock'

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
    config.manual_arm_interval = 0.01
    config.action_layout = {
        'arm': {
            'start': 0, 'end': 14, 'policy': 'gradual',
            'presets': {
                'left': [{'name': 'Default', 'value': [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869]}],
                'right': [{'name': 'Default', 'value': [1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873]}],
            },
        },
        'gripper': {
            'start': 14, 'end': 16, 'policy': 'stepwise',
            'presets': {
                'left': [{'name': 'Default', 'value': [0.0]}, {'name': 'Close', 'value': [1.0]}],
                'right': [{'name': 'Default', 'value': [0.0]}, {'name': 'Close', 'value': [1.0]}],
            },
        },
        # policy='none' is robot/Web-only and must stay after all model policies.
        'head': {
            'start': 16, 'end': 18, 'policy': 'none',
            'presets': [{'name': 'Default', 'value': [0.0, 0.4363]}],
        },
        'waist': {
            'start': 18, 'end': 20, 'policy': 'none',
            'presets': [{'name': 'Default', 'value': [0.4012, 27.0]}],
        },
        'wheel': {
            'start': 20, 'end': 22, 'policy': 'none',
            'presets': [{'name': 'Default', 'value': [0, 0]}, {'name': 'Forward', 'value': [0.1, 0.]}, {'name': 'Backward', 'value': [-0.1, 0]}, {'name': 'Left', 'value': [0, 0.1]}, {'name': 'Right', 'value': [0, -0.1]}],
        },
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
    config.camera.names = {'head': 'observation.images.top_head',
                           'hand_left': 'observation.images.hand_left',
                           'hand_right': 'observation.images.hand_right'}
    config.action_layout = {
        'arm': {
            'start': 0, 'end': 14, 'policy': 'gradual',
            'presets': {
                'left': [{'name': 'Default', 'value': [0.0] * 7}],
                'right': [{'name': 'Default', 'value': [0.0] * 7}],
            },
        },
        'gripper': {
            'start': 14, 'end': 16, 'policy': 'stepwise',
            'presets': {
                'left': [{'name': 'Default', 'value': [0.0]}],
                'right': [{'name': 'Default', 'value': [0.0]}],
            },
        },
        # 'head': {'start': 16, 'end': 18, 'policy': 'none'},
        # 'waist': {'start': 18, 'end': 20, 'policy': 'none'},
    }
    config.manual_arm_interval = 0.01
    config.dataset_path = '/home/robot/Music/task_39_only1'
    # config.dataset_path = '/home/robot/Music'
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
    return config

if __name__ == '__main__':
    config = get_robots_config()
    print(config)
