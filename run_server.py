import time
from conf.config import get_server_config
from server.core.vla_server import VLAServer
from server.core.zmq_server import ZMQServer
from server.models.gr00t import ModelVLA

if __name__ == "__main__":
    config = get_server_config()
    # print(config)
    zmq_server = ZMQServer(config.zmq)
    model = ModelVLA()
    vla_server = VLAServer(config, zmq_server, model)
    
    try:
        vla_server.run()
    except KeyboardInterrupt:
        print("程序被中断")
    finally:
        vla_server.close()