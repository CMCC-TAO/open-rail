from enum import Enum
from ml_collections import ConfigDict

class RobotType(str, Enum):
    A2D = 'a2d'
    MOCK = 'mock'
    UNITREE_G1 = 'unitree_g1'

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
                           'hand_left': 'hand_left_fisheye' if 'hand' in config.hand_type else 'hand_left',
                           'hand_right': 'hand_right_fisheye' if 'hand' in config.hand_type else 'hand_right'}
    config.proprio_names = ['arm', 'hand' if 'hand' in config.hand_type else 'gripper', 'head', 'waist']
    config.gripper_freq = 40
    config.head_freq = 40
    config.reset_robot_pos = [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0] # default pose (teleoperation default pose)
    config.action_layout = {
        'arm': {'start': 0, 'end': 14, 'policy': 'joint'},
        'gripper': {'start': 14, 'end': 16, 'policy': 'gripper'},
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
    config.hand_type = 'gripper' # 'gripper' or 'hand_as_gripper' or 'hand'
    config.camera.ref = 'head'
    config.camera.names = {'head': 'observation.images.top_head',
                           'hand_left': 'observation.images.hand_left',
                           'hand_right': 'observation.images.hand_right'}
    config.action_layout = {
        'arm': {'start': 0, 'end': 14, 'policy': 'joint'},
        'gripper': {'start': 14, 'end': 16, 'policy': 'gripper'},
        # 'head': {'start': 16, 'end': 18, 'policy': 'gripper'},
        # 'waist': {'start': 18, 'end': 20, 'policy': 'gripper'},
    }
    config.root = '/home/robot/Music/task_39_only1'
    config.repo_id = 'task_39_only1'
    return config

def get_unitree_g1_config():
    """Generate configuration for Unitree G1 humanoid robot.

    Unitree G1 使用 26 维动作/状态接口:
        action[0:7]   -> 左臂 (7 关节)
        action[7:14]  -> 右臂 (7 关节)
        action[14:20] -> 左手 (6 手指)
        action[20:26] -> 右手 (6 手指)

    Returns:
        ConfigDict: Configuration dictionary for unitree_g1 robot adapter.
    """
    config = ConfigDict()
    config.camera = ConfigDict()
    config.hand_type = 'hand'
    config.camera.ref = 'head'
    config.camera.names = {
        'head': 'head',
        'hand_left': 'hand_left',
        'hand_right': 'hand_right',
    }
    config.proprio_names = ['arm', 'hand']
    # 默认复位姿态，请根据实际机器人修改此值
    config.reset_robot_pos = [
        # 左臂 (7)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        # 右臂 (7)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        # 左手 (6)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        # 右手 (6)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    ]
    config.action_layout = {
        'arm': {'start': 0, 'end': 14, 'policy': 'joint'},
        'hand': {'start': 14, 'end': 26, 'policy': 'hand'},
    }
    return config

def get_robots_config():
    """Generate configuration for all supported robot types.
    
    This function creates a comprehensive configuration dictionary that includes
    settings for all supported robot types and specifies which robot type
    to use by default.
    
    Returns:
        ConfigDict: Configuration dictionary containing:
            - type: Default robot type to use (default: unitree_g1)
            - a2d: A2D robot configuration
            - mock: Mock robot configuration for testing
            - unitree_g1: Unitree G1 robot configuration
    """
    config = ConfigDict()
    config.type = RobotType.UNITREE_G1  # 默认使用 Unitree G1 机器人
    config.a2d = get_a2d_config()
    config.mock = get_mock_config()
    config.unitree_g1 = get_unitree_g1_config()
    return config

if __name__ == '__main__':
    config = get_robots_config()
    print(config)
