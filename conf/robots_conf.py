from enum import Enum
from ml_collections import ConfigDict


def _ordered_config(value):
    if isinstance(value, dict):
        return ConfigDict(
            {key: _ordered_config(item) for key, item in value.items()},
            sort_keys=False,
        )
    if isinstance(value, list):
        return [_ordered_config(item) for item in value]
    return value


class RobotType(str, Enum):
    A2D = 'a2d'
    MOCK = 'mock'
    TI5_T170C = 'ti5_t170c'
    NAVI_WA2 = 'navi_wa2'

def get_a2d_config():
    """Generate configuration for A2D robot.
    
    Returns:
        ConfigDict: Configuration dictionary containing camera settings, proprioception names, and gripper frequency for A2D robot.
    """
    config = ConfigDict()
    config.hand_type = 'gripper' # 'gripper' or 'hand_as_gripper' or 'hand'
    config.camera = ConfigDict()
    config.camera.ref = 'head'
    # ConfigDict cannot use dotted keys, so 'cam.head' becomes 'head'
    
    config.camera.names = {'head': 'head',
                        'hand_left': 'hand_left_fisheye' if 'hand' in config.hand_type else 'hand_left',
                        'hand_right': 'hand_right_fisheye' if 'hand' in config.hand_type else 'hand_right'}
    # non-ref cameras are fetched with a persistent thread pool
    config.camera.non_ref_fetch_workers = 2
    config.proprio_names = ['arm', 'hand' if 'hand' in config.hand_type else 'gripper', 'head', 'waist']
    config.gripper_freq = 40
    config.head_freq = 40
    config.manual_arm_interval = 0.01
    config.action_layout = _ordered_config({
        'arm': {
            'start': 0, 'end': 14, 'policy': 'gradual',
            'presets': {
                'left': {'Default': [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869], 'Custom': [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869]},
                'right': {'Default': [1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873], 'Custom': [1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873]},
            },
        },
        'gripper': {
            'start': 14, 'end': 16, 'policy': 'stepwise',
            'presets': {
                'left': {'Default': [0.0], 'Custom': [0.5], 'Open': [0.0], 'Close': [1.0]},
                'right': {'Default': [0.0], 'Custom': [0.5], 'Open': [0.0], 'Close': [1.0]},
            },
        },
        # policy='manual' is robot/Web-only and must stay after all model policies.
        'head': {
            'start': 16, 'end': 18, 'policy': 'manual',
            'presets': {'Default': [0.0, 0.4363], 'Custom': [0.0, 0.4363]},
        },
        'waist': {
            'start': 18, 'end': 20, 'policy': 'manual',
            'presets': {'Default': [0.4012, 27.0], 'Custom': [0.4012, 27.0]},
        },
        'wheel': {
            'start': 20, 'end': 22, 'policy': 'manual',
            'presets': {'Default': [0, 0], 'Forward': [0.1, 0.], 'Backward': [-0.1, 0], 'Left': [0, 0.1], 'Right': [0, -0.1]},
        },
    })
    return config

def get_mock_config():
    """Generate configuration for mock robot (simulation/testing).
    
    Returns:
        ConfigDict: Configuration dictionary containing camera mappings, data root path, and repository ID for mock robot.
    """
    config = ConfigDict()
    config.camera = ConfigDict()
    # config.hand_type = 'gripper' # 'gripper' or 'hand_as_gripper' or 'hand'
    config.camera.ref = 'head'
    config.camera.names = {'head': 'observation.images.head_rgb',
                        'hand_left': 'observation.images.left_wrist_rgb',
                        'hand_right': 'observation.images.right_wrist_rgb'}
    config.action_layout = _ordered_config({
        'arm': {
            'start': 0, 'end': 14, 'policy': 'gradual',
            'presets': {
                'left': {'Default': [0.0] * 7, 'Custom': [0.0] * 7},
                'right': {'Default': [0.0] * 7, 'Custom': [0.0] * 7},
            },
        },
        'gripper': {
            'start': 14, 'end': 16, 'policy': 'stepwise',
            'presets': {
                'left': {'Default': [0.0], 'Custom': [0.0]},
                'right': {'Default': [0.0], 'Custom': [0.0]},
            },
        },
        # 'head': {'start': 16, 'end': 18, 'policy': 'manual'},
        # 'waist': {'start': 18, 'end': 20, 'policy': 'manual'},
    })
    config.manual_arm_interval = 0.01
    config.state_action_range = [[0, 16], [58, 70]]
    config.dataset_path = '/home/robot/Music/task_39_only1'
    # config.dataset_path = '/home/robot/Music'
    return config

def get_ti5_t170c_config():
    """Configuration for TI5 T170c (26-DOF arm+hand; matches VLA training)."""
    config = ConfigDict()
    config.hand_type = 'hand'
    config.camera = ConfigDict()
    config.camera.backend = 'remote_forwarder'
    config.camera.forwarder_uri = 'tcp://192.168.1.100:9100'
    config.camera.ref = 'head'
    config.camera.warmup_s = 3.0
    config.camera.names = {
        'head': 'head/color',
        'hand_left': 'hand_left/color',
        'hand_right': 'hand_right/color',
    }
    config.camera.depth_names = {
        'depth_head': 'head/depth',
        'depth_hand_left': 'hand_left/depth',
        'depth_hand_right': 'hand_right/depth',
    }
    config.proprio_names = ['arm', 'hand']
    # 1 = every control tick (same as arm); 40 was A2D gripper-style downsample (~6.7Hz).
    config.hand_freq = 1
    config.head_freq = 1
    # homing pose from tj_arm_config + open hands (26-dim: arm+hand; VLA only)
    _arm_reset = (
        [-1.3119088393316176, 1.4473110065281325, 1.6156086726673602, -1.665472635653567,
         -0.4101313352460489, -0.21850174207321, -0.3232027944991513]
        + [1.3119088393316176, 1.4473110065281325, -1.6156086726673602, -1.665472635653567,
           0.4101313352460489, -0.2251850174207321, 0.3232027944991513]
    )
    # Hand open pose in Inspire hardware units [0, 1000]
    config.reset_robot_pos = _arm_reset + [1000.0] * 12
    config.manual_arm_interval = 0.01
    _hand_open = [1000.0] * 6
    # Head: NECK_Y / NECK_P / NECK_R (rad). policy=manual → Web-only, not in VLA action_dim.
    _head_default = [0.0, 0.0, 0.0]
    config.action_layout = {
        'arm': {
            'start': 0,
            'end': 14,
            'policy': 'gradual',
            # Web Robot Control requires presets; without them UI stays disabled.
            'presets': {
                'left': {
                    'Default': list(_arm_reset[:7]),
                    'Custom': list(_arm_reset[:7]),
                },
                'right': {
                    'Default': list(_arm_reset[7:14]),
                    'Custom': list(_arm_reset[7:14]),
                },
            },
        },
        'hand': {
            'start': 14,
            'end': 26,
            'policy': 'gradual',
            # Web presets: Default/Custom only (edit Custom for open/close values).
            'presets': {
                'left': {
                    'Default': list(_hand_open),
                    'Custom': list(_hand_open),
                },
                'right': {
                    'Default': list(_hand_open),
                    'Custom': list(_hand_open),
                },
            },
        },
        # policy='manual' is robot/Web-only and must stay after all model policies.
        'head': {
            'start': 26,
            'end': 29,
            'policy': 'manual',
            'presets': {
                'Default': list(_head_default),
                'Custom': list(_head_default),
            },
        },
    }
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
    config.action_layout = _ordered_config({
        'arm': {'start': 0, 'end': 16, 'policy': 'gradual'},
        'hand': {'start': 16, 'end': 28, 'policy': 'stepwise'}
        })
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
    config.ti5_t170c = get_ti5_t170c_config()
    config.navi_wa2 = get_navi_wa2_config()
    return config

if __name__ == '__main__':
    config = get_robots_config()
    print(config)
