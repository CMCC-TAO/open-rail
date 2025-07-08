from ml_collections import ConfigDict

# 定义模型类型的枚举类
def get_rdm_config():
    """Generate config for RealtimeDataManager

    Returns:
        ConfigDict: Configuration for RealtimeDataManager.
    """
    config = ConfigDict()
    config.max_len = 100 # Max length of the sequence to store observe data
    # config.control_max_len = 1000 # Max length of the sequence to store control data
    config.record_data = False # True to record data, False to not record data
    # config.show_data = False # True to show data, False to not show data
    return config
