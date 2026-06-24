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
    config.camera.names = {'head': 'observation.images.top_head',
                           'hand_left': 'observation.images.hand_left',
                           'hand_right': 'observation.images.hand_right'}
    config.action_layout = {
        'arm': {'start': 0, 'end': 14, 'policy': 'gradual'},
        'gripper': {'start': 14, 'end': 16, 'policy': 'stepwise'},
        # 'head': {'start': 16, 'end': 18, 'policy': 'gripper'},
        # 'waist': {'start': 18, 'end': 20, 'policy': 'gripper'},
    }
    config.dataset_path = '/home/robot/Music/task_39_only1'
    # config.dataset_path = '/home/robot/Music'
    return config

def get_unitree_g1_config():
    """Generate configuration for Unitree G1 humanoid robot.

    Unitree G1 uses a 26-dimensional action/state interface:
        action[0:7]   -> left arm (7 joints)
        action[7:14]  -> right arm (7 joints)
        action[14:20] -> left hand (6 fingers)
        action[20:26] -> right hand (6 fingers)

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
    # Default reset pose = ready-to-grasp pose (arms extended forward, hands slightly open)
    config.reset_robot_pos = [
        # ===== Left arm (7) =====
        0.30, 0.15, -0.15, -0.30, 0.0, -0.30, 0.0,
        # ===== Right arm (7) =====
        0.30, -0.15, 0.15, -0.30, 0.0, -0.30, 0.0,
        # ===== Left hand (6) ===== (open)
        100.0, 100.0, 100.0, 100.0, 150.0, 50.0,
        # ===== Right hand (6) ===== (open)
        100.0, 100.0, 100.0, 100.0, 150.0, 50.0,
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
    config.type = RobotType.UNITREE_G1  # Default to Unitree G1 robot
    config.a2d = get_a2d_config()
    config.mock = get_mock_config()
    config.unitree_g1 = get_unitree_g1_config()
    return config

if __name__ == '__main__':
    config = get_robots_config()
    print(config)
