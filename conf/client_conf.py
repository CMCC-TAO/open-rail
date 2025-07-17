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
    """Generate config for Client

    Returns:
        ConfigDict: Configuration for Client.
    """
    config = ConfigDict()
    config.rdm = get_rdm_config()
    config.traj = get_traj_config()
    config.controller = get_controller_config()
    config.observer = get_observer_config()
    config.robots = get_robots_config()
    # config.zmq_addr = 'tcp://172.18.12.24:5566'  # server address and port
    config.zmq = get_zmq_config()
    config.record = get_record_data_config() # record data config
    config.show_data = False # True to show data, False to not show data
    config.show_img = False # True to show data, False to not show data
    config.traj_strategy = 'fitting' # Trajectory strategy, choices = ('fitting', 'interpolation')
    config.fitting_num_samples = 64
    config.fitting_time_step = 5 # 轨迹拟合的时间步长，单位为毫秒
    config.fitting_deg = 4 #多项式拟合的阶数
    config.search_action = True # 是否前向搜索平滑动作
    config.search_length = 100 # 前向搜索的长度
    config.smooth_action = False # 是否平滑动作
    config.smooth_length = 150 # 平滑动作的长度
    config.smooth_base = 0.0 # 平滑动作的基础值，基础值约小表示约平滑
    config.smooth_ratio = 0.75 # 平滑动作的比例，推荐0.5
    config.gripper_offset = 5 # 夹爪向前偏移量
    config.wait_frame = 15 # 每一帧推理完成后的休眠帧数，每一帧33ms, 已废弃
    config.sleep_time = 0.4 # 每一帧推理完成后的休眠时间，单位为秒
    config.history_frame = False # 是否使用历史帧，True表示使用历史帧，False表示不使用历史帧
    config.chunk_strategy = 'latest' # Action Chunk Strategy, choices = ('fusion', 'latest')
    # config.chunk_strategy = 'fusion' # Action Chunk Strategy, choices = ('fusion', 'latest')
    config.preprocess = 'pad_and_resize'
    # 语言指令及cmd备选，默认0
    config.language = [
        'pick bottle into box',
        'pour milk into the box',
        'put the sandwich in the microwave',
    ]
    return config
