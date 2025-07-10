import time
from conf.model_conf import ModelType
from conf.server_conf import get_server_config
# from conf.config import ModelType
from server.core.vla_server import VLAServer
from server.core.zmq_server import ZMQServer

def get_model(config):
    if config.type == ModelType.ACT:
        from server.models.act import ModelVLA as ACT
        return ACT(config.act)
    elif config.type == ModelType.GR00T:
        from server.models.gr00t.gr00t_n1 import ModelVLA as GR00T
        return GR00T(config.gr00t)
    elif config.type == ModelType.GR00T_N1_5:
        from server.models.gr00t.gr00t_n1_5 import ModelVLA as GR00T_N1_5
        return GR00T_N1_5(config.gr00t)
    elif config.type == ModelType.RDT:
        from server.models.rdt import ModelVLA as RDT
        return RDT(config.rdt)
    elif config.type == ModelType.SMOLVLA:
        from server.models.smolvla import ModelVLA as SMOLVLA
        return SMOLVLA()
    else:
        raise ValueError("Invalid model type")

if __name__ == "__main__":
    config = get_server_config()
    # print(config)
    zmq_server = ZMQServer(config.zmq)
    model = get_model(config.model)
    vla_server = VLAServer(config, zmq_server, model)
    
    try:
        vla_server.run()
    except KeyboardInterrupt:
        print("程序被中断")
    finally:
        vla_server.close()
