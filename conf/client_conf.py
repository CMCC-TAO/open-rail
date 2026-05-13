from enum import Enum
from ml_collections import ConfigDict
from conf.rdm_conf import get_rdm_config
from conf.control_conf import get_controller_config
from conf.observe_conf import get_observer_config
from conf.zmq_conf import get_vla_zmq_config, get_vis_zmq_config
from conf.save_conf import get_record_data_config
from conf.chunk_conf import get_intra_chunk_config, get_inter_chunk_config
from conf.robots_conf import get_robots_config
from conf.visual_conf import get_visual_config

def get_client_config():
    """Generate configuration for VLA inference client.
    
    This function creates a comprehensive configuration dictionary that includes
    settings for real-time data management, trajectory generation, robot control,
    observation handling, ZMQ communication, data recording, and various inference
    parameters.

    Returns:
        ConfigDict: Complete configuration dictionary for the VLA client containing:
            - rdm: Real-time data manager configuration
            - intra_chunk: Intra-chunk smoothing/fitting configuration
            - controller: Robot controller configuration
            - observer: Observation system configuration
            - robots: Robot-specific configuration
            - zmq: ZMQ communication configuration
            - record: Data recording configuration
            - Various inference and control parameters
    """
    config = ConfigDict()
    config.rdm = get_rdm_config()
    config.intra_chunk = get_intra_chunk_config()
    config.inter_chunk = get_inter_chunk_config()
    config.controller = get_controller_config()
    config.observer = get_observer_config()
    config.robots = get_robots_config()
    config.vla_zmq = get_vla_zmq_config()
    config.vis_zmq = get_vis_zmq_config()
    config.vis_action_length = 1000
    config.visual = get_visual_config()
    config.record = get_record_data_config()  # Data recording configuration
    config.show_action_cams_qt = False  # QT-based action-camera visualization. If set as True, run /client/utils/vis_action_camera.py.py to launch the visualization server
    config.record_exp_data = False  # Enable/disable logging action, velocity, and acceleration data to files
    # config.show_img = False  # Enable/disable image display
    # config.intra_chunk.strategy = 'fitting'  # Trajectory strategy, choices = ('fitting', 'interpolation')
    config.gripper_offset = 5  # Gripper forward offset. Note: positive value, gripper slow, increase it.
    config.sleep_time = 0.002  # Sleep time after each inference frame in seconds. Note: robot to hesitate, increase it.
    config.vision = get_vision_config()
    config.language = get_language_config()
    # config.language = [
    #     'Grasp the bottle selected by the finger with the nearer gripper and pass it to the hand carefully. If and only if the bottle is caught by hand, release the gripper.',
    #     'default language instruction',
    # ]
    return config

def get_language_config() -> ConfigDict:
    config = ConfigDict()
    config.file_path = 'lang_cmd.json'  # Path to language configuration file, must in conf dir.
    config.task_id = 'pour_tea'
    config.sub_task_id = 1
    config.auto_mode = True  # If True, automatically switch language instructions based on probability threshold
    config.task_progress_threshold = 9.9  # Probability threshold for switching language instructions
    return config

def get_vision_config() -> ConfigDict:
    config = ConfigDict()
    config.history_frame = False  # Enable/disable historical frame usage
    config.preprocess = 'pad_and_resize'
    config.preprocess_size = [640, 640]  # [height, width]
    return config