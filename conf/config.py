from enum import Enum
from ml_collections import ConfigDict

# 定义模型类型的枚举类
class ModelType(str, Enum):
    ACT = 'act'
    GR00T = 'gr00t'

class RobotType(str, Enum):
    A2D = 'a2d'
    MOCK = 'mock'

period = 5
def get_realtime_data_manager_config():
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

def get_controller_config():
    """Generate config for Controller

    Returns:
        ConfigDict: Configuration for Controller.
    """
    config = ConfigDict()
    config.wait_step = 4 # Time delay for robot controller, in milliseconds [ms]
    config.period = period # Control period to control robot, in milliseconds [ms]
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
    config.period = 33 # Observation period to get robot observations, in milliseconds [ms]
    return config

def get_trajectory_config():
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

def get_client_config():
    """Generate config for Client

    Returns:
        ConfigDict: Configuration for Client.
    """
    config = ConfigDict()
    config.robot = RobotType.A2D
    config.rdm = get_realtime_data_manager_config()
    config.traj = get_trajectory_config()
    config.controller = get_controller_config()
    config.observer = get_observer_config()
    # config.zmq_addr = 'tcp://172.18.12.24:5566'  # server address and port
    config.zmq = get_zmq_config()
    config.show_data = False # True to show data, False to not show data
    config.traj_strategy = 'fitting' # Trajectory strategy, choices = ('fitting', 'interpolation')
    config.fitting_time_step = period # 轨迹拟合的时间步长，单位为毫秒
    config.fitting_deg = 3 #多项式拟合的阶数
    config.chunk_strategy = 'latest' # Action Chunk Strategy, choices = ('fusion', 'latest')
    # config.chunk_strategy = 'fusion' # Action Chunk Strategy, choices = ('fusion', 'latest')
    return config

def get_zmq_config():
    """Generate config for zmq

    Returns:
        ConfigDict: Configuration for zmq.
    """
    config = ConfigDict()
    config.client_addr = 'tcp://localhost:5566'  # server address and port
    # config.server_addr = 'tcp://*:5566' # server address and port
    config.server_addr = 'tcp://localhost:5566' # server address and port
    return config

def get_server_config():
    """Generate config for Client

    Returns:
        ConfigDict: Configuration for Client.
    """
    config = ConfigDict()
    config.zmq = get_zmq_config()
    # MAIN_CLIENT_ID = 'ZROBOT'
    config.max_workers = 1  # 推理线程池最大工作线程数，1表示不支持并发推理
    # config.model = ModelType.ACT
    config.model = ModelType.GR00T
    return config