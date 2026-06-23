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
    # config.vis_zmq = get_vis_zmq_config()
    config.visualize = get_visualize_config()
    config.record = get_record_data_config()  # Data recording configuration
    config.vision = get_vision_config()
    config.language = get_language_config()
    return config

def get_rdm_config() -> ConfigDict:
    """Generate configuration for Real-time Data Manager.
    
    This function creates configuration settings for the real-time data management
    system, including buffer sizes and data recording options.

    Returns:
        ConfigDict: Configuration dictionary for RealtimeDataManager containing:
            - max_len: Maximum length of observation data sequence buffer
            - observe_fps_window_size: Window size for FPS estimation
    """
    config = ConfigDict()
    config.mode = 'async'  # inference mode, choices = ('async', 'sync')
    config.max_len = 100  # Maximum length of observation data sequence buffer
    config.observe_fps_window_size = 10  # FPS estimation window size based on latest N added observation frames
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
    config.fitting_deg = 4  # Polynomial fitting degree
    config.intra_chunk_mode = 'fitting'  # intra-chunk processing mode, choices = ('raw', 'interpolation', 'fitting')
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
            - wait_time: Time delay for robot controller in milliseconds
            - period: Control period for robot control in milliseconds
            - gripper_offset: Gripper command forward offset with respect to arm command in frames
    """
    config = ConfigDict()
    config.wait_time = 200  # Wait time for the next inference step in millisecond. Note: if robot hesitate to action, increase it.
    config.period = 3.75   # Control period for sending command to robot in milliseconds
    config.gripper_offset = 5  # Gripper forward offset. Note: positive value, gripper slow, increase it.
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

def get_visualize_config() -> ConfigDict:
    """Generate configuration for web visual panels."""
    config = ConfigDict()

    config.server = ConfigDict()
    config.server.host = '0.0.0.0'
    config.server.port = 8765
    config.server.max_size = 10 * 1024 * 1024  # 10MB
    config.server.ping_interval = 20  # Ping interval in milliseconds
    config.server.ping_timeout = 10  # Ping timeout in seconds

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
    config.task_progress_threshold = 0.9  # Probability threshold for switching language instructions
    config.task_progress_win_size = 10 # Sliding window size to compute average task progress
    return config

def get_vision_config() -> ConfigDict:
    config = ConfigDict()
    config.history_frame = False  # Enable/disable historical frame usage
    config.preprocess = ConfigDict()
    config.preprocess.method = 'resize' # only support resize and none
    config.preprocess.keep_ratio = True 
    config.preprocess.height = 480
    config.preprocess.width = 640
    return config