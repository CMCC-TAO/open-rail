from enum import Enum
from ml_collections import ConfigDict

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
        ConfigDict: Configuration dictionary containing camera mappings, data root path, and repository ID for mock robot.
    """
    config = ConfigDict()
    config.camera = ConfigDict()
    # config.hand_type = 'gripper' # 'gripper' or 'hand_as_gripper' or 'hand'
    config.camera.ref = 'head'
    config.camera.names = {'head': 'observation.images.head_rgb',
                        'hand_left': 'observation.images.left_wrist_rgb',
                        'hand_right': 'observation.images.right_wrist_rgb'}
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

def get_ti5_t170c_config():
    """Generate configuration for Ti5 T170C robot (ROS2 bridge)."""
    config = ConfigDict()

    config.camera = ConfigDict()
    config.camera.head_camera_topic = "/camera/d435i/color/image_raw"
    config.camera.left_hand_camera_topic = "/camera/d405_1/color/image_raw"
    config.camera.right_hand_camera_topic = "/camera/d405_2/color/image_raw"

    config.arms = ConfigDict()
    config.arms.left_arm_joint_cmd_topic = "/left_arm/joint_cmd"
    config.arms.right_arm_joint_cmd_topic = "/right_arm/joint_cmd"
    config.arms.left_arm_joint_states_topic = "/left_arm/joint_states"
    config.arms.right_arm_joint_states_topic = "/right_arm/joint_states"

    config.arms.left_arm_joint_names = [
        "L_SHOULDER_P_JOINT",
        "L_SHOULDER_R_JOINT",
        "L_SHOULDER_Y_JOINT",
        "L_ELBOW_JOINT",
        "L_WRIST_Y_JOINT",
        "L_WRIST_R_JOINT",
        "L_WRIST_P_JOINT",
    ]
    config.arms.right_arm_joint_names = [
        "R_SHOULDER_P_JOINT",
        "R_SHOULDER_R_JOINT",
        "R_SHOULDER_Y_JOINT",
        "R_ELBOW_JOINT",
        "R_WRIST_Y_JOINT",
        "R_WRIST_R_JOINT",
        "R_WRIST_P_JOINT",
    ]

    config.hands = ConfigDict()
    config.hands.left_hand_joint_cmd_topic = "/left_hand/angle_cmd"
    config.hands.right_hand_joint_cmd_topic = "/right_hand/angle_cmd"
    config.hands.left_hand_joint_states_topic = "/left_hand/angle_state"
    config.hands.right_hand_joint_states_topic = "/right_hand/angle_state"

    config.hands.hand_joint_names = [
        "pinky", "ring", "middle", "index", "thumb", "thumb_rot"
    ]

    config.waist = ConfigDict()
    config.waist.waist_joint_cmd_topic = "/waist_motor/joint_cmd"
    config.waist.waist_joint_states_topic = "/waist_motor/joint_states"

    config.waist.waist_joint_names = [
        "WAIST_Y_JOINT", "WAIST_R_JOINT", "WAIST_P_JOINT"
    ]

    config.head = ConfigDict()
    config.head.head_joint_cmd_topic = "/head_motor/joint_cmd"
    config.head.head_joint_states_topic = "/head_motor/joint_states"

    config.head.head_joint_names = [
        "NECK_Y_JOINT", "NECK_P_JOINT", "NECK_R_JOINT"
    ]

    config.reset_robot_pos = \
      [
        -1.681951211214541, 1.5263110171042418, 2.2737134617553534, -0.23620356347006893, -0.5204031154482495, 0.1292378813793631, 0.19059726269759902
      ] + \
      [
        1.3119088393316176, 1.4473110065281325, -1.6156086726673602, -1.665472635653567, 0.4101313352460489, -0.2251850174207321, 0.3232027944991513
      ] + \
      [
        1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0
      ] + \
      [
        650.0, 650.0, 650.0, 650.0, 650.0, 250.0
      ]

    config.zero_pos = \
      [
        -1.681951211214541, 1.5263110171042418, 2.2737134617553534, -0.23620356347006893, -0.5204031154482495, 0.1292378813793631, 0.19059726269759902
      ] + \
      [
        1.4875488405961936, 1.5339806547275607, -1.4787018194549504, -0.32055631145539876, 0.1102380912144111, -0.05337579029191015, 0.20508064790415614
      ] + \
      [
        1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0
      ] + \
      [
        1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0
      ]

    config.action_layout = {
        'arm': {'start': 0, 'end': 14, 'policy': 'gradual'},
        'gripper': {'start': 14, 'end': 26, 'policy': 'gradual'},
        # 'head': {'start': 16, 'end': 18, 'policy': 'gripper'},
        # 'waist': {'start': 18, 'end': 20, 'policy': 'gripper'},
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
    config.ti5_t170c = get_ti5_t170c_config()
    config.navi_wa2 = get_navi_wa2_config()
    return config

if __name__ == '__main__':
    config = get_robots_config()
    print(config)
