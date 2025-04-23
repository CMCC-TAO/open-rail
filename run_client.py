import time
from client.core import zmq_client
from conf.config import get_client_config
from client.robots.a2d import RobotA2D
from client.robots.base import RobotBase
from client.core.vla_client import VLAClient
from client.core.zmq_client import ZMQClient
from client.core.realtime_data_manager import RealtimeDataManager

if __name__ == "__main__":
    config = get_client_config()
    # print(config)
    zmq_client = ZMQClient(config.zmq)
    robot = RobotA2D(config.observer, config.controller)
    rdm = RealtimeDataManager(config.rdm)
    vla_client = VLAClient(config, rdm, zmq_client, robot)
    
    try:
        vla_client.run()
    except KeyboardInterrupt:
        print("程序被中断")
    finally:
        # pass
        robot.close()
        vla_client.close()