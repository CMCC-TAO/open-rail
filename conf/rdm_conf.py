from ml_collections import ConfigDict

def get_rdm_config():
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
