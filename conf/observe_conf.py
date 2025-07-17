from ml_collections import ConfigDict

# 定义模型类型的枚举类

def get_observer_config():
    """Generate config for Observer

    Returns:
        ConfigDict: Configuration for Observer.
    """
    config = ConfigDict()
    config.fps = 30 # Observation period to get robot observations, in milliseconds [ms]
    return config
