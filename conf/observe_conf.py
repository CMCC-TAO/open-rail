from ml_collections import ConfigDict

# 定义模型类型的枚举类

def get_observer_config():
    """Generate config for Observer

    Returns:
        ConfigDict: Configuration for Observer.
    """
    config = ConfigDict()
    config.camera_names = ['head', 'hand_left', 'hand_right'] # Cameras used to get observations
    config.proprio_names = ['arm', 'gripper', 'head', 'waist']
    config.fps = 30 # Observation period to get robot observations, in milliseconds [ms]
    return config
