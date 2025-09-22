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
    config.camera = ConfigDict()
    config.hand_type = 'gripper' # 'gripper' or 'hand_as_gripper' or 'hand'
    config.camera.ref = 'head'
    # ConfigDict cannot use dotted keys, so 'cam.head' becomes 'head'
    config.camera.names = {'head': 'head',
                           'hand_left': 'hand_left' if 'gripper' in config.hand_type else 'hand_left_fisheye',
                           'hand_right': 'hand_right' if 'gripper' in config.hand_type else 'hand_right_fisheye'}
    config.proprio_names = ['arm', config.hand_type, 'head', 'waist']
    config.gripper_freq = 40
    config.reset_robot_pos = [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0]
    return config

def get_mock_config():
    """Generate configuration for mock robot (simulation/testing).
    
    Returns:
        ConfigDict: Configuration dictionary containing camera mappings,
                   data root path, and repository ID for mock robot.
    """
    config = ConfigDict()
    config.camera = ConfigDict()
    config.hand_type = 'gripper' # 'gripper' or 'hand_as_gripper' or 'hand'
    config.camera.ref = 'head'
    config.camera.names = {'head': 'observation.images.top_head',
                           'hand_left': 'observation.images.hand_left',
                           'hand_right': 'observation.images.hand_right'}
    config.root = '/home/robot/Music/task_39_only1'
    config.repo_id = 'task_39_only1'
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