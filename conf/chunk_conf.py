from ml_collections import ConfigDict

def get_intra_chunk_config():
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
