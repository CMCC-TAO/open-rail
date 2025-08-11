from ml_collections import ConfigDict

def get_controller_config():
    """Generate configuration for robot controller system.
    
    This function creates configuration settings for the robot control system,
    including timing parameters and control strategies.

    Returns:
        ConfigDict: Configuration dictionary for Controller containing:
            - wait_step: Time delay for robot controller in milliseconds
            - period: Control period for robot control in milliseconds
            - strategy: Control strategy type
    """
    config = ConfigDict()
    config.wait_step = 4  # Time delay for robot controller in milliseconds
    config.period = 5  # Control period for robot control in milliseconds
    config.strategy = 'step'  # Control strategy, choices = ('step', 'realtime', 'fusion')
    return config