from enum import Enum
from ml_collections import ConfigDict
from conf.rdm_conf import get_rdm_config
from conf.control_conf import get_controller_config
from conf.observe_conf import get_observer_config
from conf.zmq_conf import get_zmq_config
from conf.save_conf import get_record_data_config
from conf.traj_conf import get_traj_config
from conf.robots_conf import get_robots_config

def get_client_config():
    """Generate configuration for VLA inference client.
    
    This function creates a comprehensive configuration dictionary that includes
    settings for real-time data management, trajectory generation, robot control,
    observation handling, ZMQ communication, data recording, and various inference
    parameters.

    Returns:
        ConfigDict: Complete configuration dictionary for the VLA client containing:
            - rdm: Real-time data manager configuration
            - traj: Trajectory generation configuration  
            - controller: Robot controller configuration
            - observer: Observation system configuration
            - robots: Robot-specific configuration
            - zmq: ZMQ communication configuration
            - record: Data recording configuration
            - Various inference and control parameters
    """
    config = ConfigDict()
    config.rdm = get_rdm_config()
    config.traj = get_traj_config()
    config.controller = get_controller_config()
    config.observer = get_observer_config()
    config.robots = get_robots_config()
    config.zmq = get_zmq_config()
    config.record = get_record_data_config()  # Data recording configuration
    config.show_data = False  # Enable/disable data visualization
    config.show_img = False  # Enable/disable image display
    config.traj_strategy = 'fitting'  # Trajectory strategy, choices = ('fitting', 'interpolation')
    config.fitting_num_samples = 64
    config.fitting_time_step = 5  # Time step for trajectory fitting in milliseconds
    config.fitting_deg = 4  # Polynomial fitting degree
    config.search_action = True  # Enable forward search for smooth actions
    config.search_length = 100  # Forward search length. Note: robot to hesitate, increase it.
    config.smooth_action = False  # Enable action smoothing (Beta)
    config.smooth_length = 150  # Action smoothing length
    config.smooth_base = 0.0  # Base value for action smoothing, smaller values mean more smoothing
    config.smooth_ratio = 0.75  # Action smoothing ratio, recommended 0.5
    config.gripper_offset = 5  # Gripper forward offset. Note: positive value, gripper slow, increase it.
    config.sleep_time = 0.4  # Sleep time after each inference frame in seconds. Note: robot to hesitate, increase it.
    config.history_frame = False  # Enable/disable historical frame usage
    config.chunk_strategy = 'latest'  # Action chunk strategy, choices = ('fusion', 'latest')
    config.preprocess = 'pad_and_resize'
    config.preprocess_size = [640, 640] # [height, width]
    # Language instruction options, default index 0
    config.language = [
        'Use the left arm to grasp the teapot of green tea first, and then carefully pour the green tea into the cup.',
        'Use the right arm to grasp the teapot of black tea first, and then carefully pour the black tea into the cup.',
        'Place the green tea cup on the tray with left arm',
        'Place the black tea cup on the tray with right arm',
        '[PRIMARY_ARM=LEFT] Use the left gripper to pick up the topmost steamer on the left',
        '[PRIMARY_ARM=RIGHT] Use the right gripper to pick up the topmost steamer on the right',
        '[PRIMARY_ARM=LEFT] Use the left gripper to place the topmost steamer on the plate',
        '[PRIMARY_ARM=RIGHT] Use the right gripper to place the topmost steamer on the plate',
        'pick the bottle into the basket',
        'open the microwave door, put the sandwish into it, and close the microwave door',
        'take the sandwitch out from the oven',
        'grasp the oven handle and gently pull to open the oven door',
        'carefully place the prepared sandwich onto the oven tray inside the cavity',
        'close the oven door securely by pushing it until it latches',
        'locate and press the start button to initiate the heating process',
        'wait patiently while the oven heats the sandwich to the desired temperature',
    ]
    config.thre_prob_progress = 9.9  # Probability threshold for switching language instructions
    return config
