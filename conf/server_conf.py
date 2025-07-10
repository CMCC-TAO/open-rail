from enum import Enum
from ml_collections import ConfigDict
from conf.zmq_conf import get_zmq_config
from conf.model_conf import get_model_config

def get_server_config():
    """Generate config for Client

    Returns:
        ConfigDict: Configuration for Client.
    """
    config = ConfigDict()
    config.zmq = get_zmq_config()
    # MAIN_CLIENT_ID = 'ZROBOT'
    config.max_workers = 1  # 推理线程池最大工作线程数，1表示不支持并发推理
<<<<<<< HEAD
    # config.model = ModelType.ACT
    # config.model = ModelType.SMOLVLA
    config.model = ModelType.GR00T_N1_5
    return config
=======
    config.model = get_model_config()
    return config
>>>>>>> master
