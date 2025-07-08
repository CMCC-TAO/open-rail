from ml_collections import ConfigDict

def get_controller_config():
    """Generate config for Controller

    Returns:
        ConfigDict: Configuration for Controller.
    """
    config = ConfigDict()
    config.wait_step = 4 # Time delay for robot controller, in milliseconds [ms]
    config.period = 5 # Control period to control robot, in milliseconds [ms]
    config.strategy = 'step' # Control strategy, choices = ('Step', 'realtime', 'fusion)
    return config