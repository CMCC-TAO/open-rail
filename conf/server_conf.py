from enum import Enum
from ml_collections import ConfigDict
from conf.zmq_conf import get_zmq_config

# 定义模型类型的枚举类
class ModelType(str, Enum):
    ACT = 'act'
    GR00T = 'gr00t'
    GR00T_N1_5 = 'gr00t_n1_5'
    RDT = 'rdt'
    SMOLVLA = 'smolvla'

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
    # config.model = ModelType.SMOLVLA
    config.model = ModelType.GR00T_N1_5
    return config