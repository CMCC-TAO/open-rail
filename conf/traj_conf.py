from ml_collections import ConfigDict

def get_traj_config():
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
    config.joint_dim = 14  # Degrees of freedom for dual arms
    config.gripper_dim = 2  # Degrees of freedom for dual grippers
    config.head_dim = 2  # Degrees of freedom for head
    return config
