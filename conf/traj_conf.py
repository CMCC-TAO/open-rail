from ml_collections import ConfigDict

# 定义模型类型的枚举类
def get_traj_config():
    """Generate config for Trajectory Generator.

    Returns:
        ConfigDict: Configuration for Trajectory Generator.
    """
    config = ConfigDict()
    config.filter_window_size = 4 # Define the window size used to filter gripper action chunk, the real window size is filter_window_size * 2 + 1
    config.min_gripper_action_threshold = 0.05 # Define the minimum threshold of gripper action, if the gripper action is smaller than this threshold, it will be set as 0.0
    config.max_gripper_action_threshold = 0.95 # Define the maximum threshold of gripper action, if the gripper action is larger than this threshold, it will be set as 1.0
    config.max_joint_fitting_workers = 14
    config.max_gripper_fitting_workers = 2
    config.joint_dim = 14 # Degrees of freedom of dual arms
    config.gripper_dim = 2 # Degrees of freedom of dual grippers
    # config.max_len = 1000 # Max length of the sequence to store waypoints and trajectory points
    # config.dof = 14  # Degrees of Freedoms
    # config.fine_interval = 0.01  # Time interval
    # config.coarse_interval = 0.01  # Time interval
    # config.max_velocity = [2.0] * config.dof
    # config.max_acceleration = [1.0] * config.dof
    # config.max_jerk = [5.0] * config.dof
    return config
