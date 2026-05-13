from enum import Enum
from ml_collections import ConfigDict
from conf.zmq_conf import get_vla_zmq_config, get_vis_zmq_config
from conf.save_conf import get_record_data_config
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

def get_rdm_config() -> ConfigDict:
    """Generate configuration for Real-time Data Manager.
    
    This function creates configuration settings for the real-time data management
    system, including buffer sizes and data recording options.

    Returns:
        ConfigDict: Configuration dictionary for RealtimeDataManager containing:
            - max_len: Maximum length of observation data sequence buffer
            - record_data: Flag to enable/disable data recording
    """
    config = ConfigDict()
    config.max_len = 100  # Maximum length of observation data sequence buffer
    config.record_data = False  # Enable/disable data recording
    return config

def get_intra_chunk_config() -> ConfigDict:
    """Generate configuration for trajectory generation system.
    
    This function creates configuration settings for the trajectory generation
    and action filtering system, including gripper action thresholds, fitting
    parameters, and worker thread configurations.

    Returns:
        ConfigDict: Configuration dictionary for Trajectory Generator containing:
            - filter_window_size: Window size for gripper action filtering
            - min/max_gripper_action_threshold: Gripper action thresholds
            - max_joint/gripper_fitting_workers: Worker thread counts
            - joint_dim/gripper_dim: Degrees of freedom specifications
    """
    config = ConfigDict()
    config.filter_window_size = 4  # Window size for gripper action filtering (actual size = filter_window_size * 2 + 1)
    config.min_gripper_action_threshold = 0.05  # Minimum gripper action threshold, values below this are set to 0.0
    config.max_gripper_action_threshold = 0.95  # Maximum gripper action threshold, values above this are set to 1.0
    config.max_joint_fitting_workers = 14
    config.max_gripper_fitting_workers = 2
    config.max_head_fitting_workers = 2
    config.fitting_num_samples = 64
    config.fitting_time_step = 3.75  # Time step for trajectory fitting in milliseconds
    config.fitting_deg = 4  # Polynomial fitting degree
    config.intra_chunk_mode = 'fit'  # intra-chunk processing mode, choices = ('raw', 'raw_ipt', 'fit')
    config.joint_dim = 14  # Degrees of freedom for dual arms
    config.gripper_dim = 2  # Degrees of freedom for dual grippers
    config.head_dim = 2  # Degrees of freedom for head
    return config

def get_inter_chunk_config() -> ConfigDict:
    config = ConfigDict()
    config.inter_chunk_mode = 'min_jerk'  # inter-chunk transition mode, choices = ('search_action', 'poly', 'smooth_velocity', 'min_jerk', 'bspline', 'sync')
    config.search_length = 100  # Forward search length. Note: robot to hesitate, increase it.
    config.smooth_action = False  # Enable action smoothing (Beta)
    config.smooth_length = 150  # Action smoothing length
    config.smooth_base = 0.0  # Base value for action smoothing, smaller values mean more smoothing
    config.smooth_ratio = 0.75  # Action smoothing ratio, recommended 0.5
    return config

def get_controller_config() -> ConfigDict:
    """Generate configuration for robot controller system.
    
    This function creates configuration settings for the robot control system,
    including timing parameters and control strategies.

    Returns:
        ConfigDict: Configuration dictionary for Controller containing:
            - wait_step: Time delay for robot controller in milliseconds
            - period: Control period for robot control in milliseconds
            - strategy: Control strategy type
    """
    config = ConfigDict()
    config.wait_step = 4  # Time delay for robot controller in milliseconds
    config.period = 3.75   # Control period for robot control in milliseconds
    config.strategy = 'step'  # Control strategy, choices = ('step', 'realtime', 'fusion')
    return config

def get_observer_config() -> ConfigDict:
    """Generate configuration for the observation system.
    
    This function creates configuration settings for the robot observation system,
    including frame rate and other observation-related parameters.

    Returns:
        ConfigDict: Configuration dictionary for the Observer containing:
            - fps: Frames per second for observation data collection
    """
    config = ConfigDict()
    config.fps = 30  # Frames per second for robot observation data collection
    return config

def get_visual_config() -> ConfigDict:
    """Generate configuration for web visual panels."""
    config = ConfigDict()

    config.camera = ConfigDict()
    config.camera.open_head = True
    config.camera.open_wrist_left = True
    config.camera.open_wrist_right = True
    config.camera.update_interval_ms = 33

    config.trajectory = ConfigDict()
    config.trajectory.play = False
    config.trajectory.source = ['State']
    config.trajectory.selected_joints = [0, 1, 2, 3]
    config.trajectory.update_interval_ms = 50
    config.trajectory.window_span_sec = 10.0

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