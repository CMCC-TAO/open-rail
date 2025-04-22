import time
from conf.config import get_server_config
from server.vla_server import VLAServer

if __name__ == "__main__":
    config = get_server_config()
    # print(config)
    vla_server = VLAServer(config)
    
    try:
        vla_server.run()
    except KeyboardInterrupt:
        print("程序被中断")
    finally:
        vla_server.close()