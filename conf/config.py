from ml_collections import ConfigDict
def get_realtime_data_manager_config():
    """Generate config for RealtimeDataManager

    Returns:
        ConfigDict: Configuration for RealtimeDataManager.
    """
    config = ConfigDict()
    config.max_len = 100 # Max length of the sequence to store data
    config.record_data = False # True to record data, False to not record data
    config.show_data = False # True to show data, False to not show data
    return config

def get_controller_config():
    """Generate config for Controller

    Returns:
        ConfigDict: Configuration for Controller.
    """
    config = ConfigDict()
    config.time_delay = 0 # Time delay for robot controller, in milliseconds [ms]
    config.control_period = 33 # Control period to control robot, in milliseconds [ms]
    config.strategy = 'step' # Control strategy, choices = ('Step', 'realtime', 'fusion)
    return config

def get_observer_config():
    """Generate config for Observer

    Returns:
        ConfigDict: Configuration for Observer.
    """
    config = ConfigDict()
    config.camera_names = ['head', 'hand_left', 'hand_right'] # Cameras used to get observations
    config.proprio_names = ['arm', 'gripper', 'head', 'waist']
    config.observe_period = 15 # Observation period to get robot observations, in milliseconds [ms]
    return config

def get_client_config():
    """Generate config for Client

    Returns:
        ConfigDict: Configuration for Client.
    """
    config = ConfigDict()
    config.rdm = get_realtime_data_manager_config()
    config.controller = get_controller_config()
    config.observer = get_observer_config()
    config.zmq_addr = 'tcp://172.18.12.24:5566'  # localhost
    return config