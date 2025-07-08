from ml_collections import ConfigDict

# 定义模型类型的枚举类
def get_traj_config():
    """Generate config for Trajectory Generator.

    Returns:
        ConfigDict: Configuration for Trajectory Generator.
    """
    config = ConfigDict()
    config.max_len = 1000 # Max length of the sequence to store waypoints and trajectory points
    config.dof = 14  # Degrees of Freedoms
    config.fine_interval = 0.01  # Time interval
    config.coarse_interval = 0.01  # Time interval
    config.max_velocity = [2.0] * config.dof
    config.max_acceleration = [1.0] * config.dof
    config.max_jerk = [5.0] * config.dof
    return config
