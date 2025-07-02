import time
from conf.config import get_server_config
from conf.config import ModelType
from server.core.vla_server import VLAServer
from server.core.zmq_server import ZMQServer
from server.models.gr00t import ModelVLA as GR00T
from server.models.act import ModelVLA as ACT
from server.models.rdt import ModelVLA as RDT

def get_model(model_type: ModelType):
    if model_type == ModelType.ACT:
        return ACT()
    elif model_type == ModelType.GR00T:
        return GR00T()
    elif model_type == ModelType.RDT:
        return RDT()
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