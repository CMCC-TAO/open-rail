from enum import Enum
from ml_collections import ConfigDict
from conf.rdm_conf import get_rdm_config
from conf.control_conf import get_controller_config
from conf.observe_conf import get_observer_config
from conf.zmq_conf import get_vla_zmq_config, get_vis_zmq_config
from conf.save_conf import get_record_data_config
from conf.traj_conf import get_traj_config
from conf.robots_conf import get_robots_config

def get_client_config():
    """Generate configuration for VLA inference client.
    
    This function creates a comprehensive configuration dictionary that includes
    settings for real-time data management, trajectory generation, robot control,
    observation handling, ZMQ communication, data recording, and various inference
    parameters.

    Returns:
        ConfigDict: Complete configuration dictionary for the VLA client containing:
            - rdm: Real-time data manager configuration
            - traj: Trajectory generation configuration  
            - controller: Robot controller configuration
            - observer: Observation system configuration
            - robots: Robot-specific configuration
            - zmq: ZMQ communication configuration
            - record: Data recording configuration
            - Various inference and control parameters
    """
    config = ConfigDict()
    config.rdm = get_rdm_config()
    config.traj = get_traj_config()
    config.controller = get_controller_config()
    config.observer = get_observer_config()
    config.robots = get_robots_config()
    config.vla_zmq = get_vla_zmq_config()
    config.vis_zmq = get_vis_zmq_config()
    config.vis_action_length = 1000
    config.record = get_record_data_config()  # Data recording configuration
    config.show_action_cams_qt = False  # QT-based action-camera visualization. If set as True, then run /client/utils/vis_action_camera.py.py to launch the visualization server
    config.show_img = False  # Enable/disable image display
    config.traj_strategy = 'fitting'  # Trajectory strategy, choices = ('fitting', 'interpolation')
    config.fitting_num_samples = 64
    config.fitting_time_step = 3.75  # Time step for trajectory fitting in milliseconds
    config.fitting_deg = 4  # Polynomial fitting degree
    config.chunk_trans_mode = 'search_action'  # chunk transition mode, choices = ('search_action', 'poly', 'smooth_velocity')
    config.search_length = 100  # Forward search length. Note: robot to hesitate, increase it.
    config.smooth_action = False  # Enable action smoothing (Beta)
    config.smooth_length = 150  # Action smoothing length
    config.smooth_base = 0.0  # Base value for action smoothing, smaller values mean more smoothing
    config.smooth_ratio = 0.75  # Action smoothing ratio, recommended 0.5
    config.gripper_offset = 5  # Gripper forward offset. Note: positive value, gripper slow, increase it.
    config.sleep_time = 0.002  # Sleep time after each inference frame in seconds. Note: robot to hesitate, increase it.
    config.history_frame = False  # Enable/disable historical frame usage
    config.preprocess = 'pad_and_resize'
    config.preprocess_size = [640, 640] # [height, width]
    # Language instruction options, default index 0
    config.language = [
        'Grasp the bottle selected by the finger with the nearer gripper and pass it to the hand carefully. If and only if the bottle is caught by hand, release the gripper.',
        'default language instruction',
    ]
    config.thre_prob_progress = 9.9  # Probability threshold for switching language instructions
    return config
