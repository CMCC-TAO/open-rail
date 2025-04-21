import time
from conf.config import get_client_config
from client.robots.a2d.robot_a2d import RobotA2D
from client.core.realtime_data_manager import RealtimeDataManager
from client.core.vla_client import VLAClient

if __name__ == "__main__":
    config = get_client_config()
    # print(config)
    robot = RobotA2D(config.observer, config.controller)
    rdm = RealtimeDataManager(config.rdm)
    vla_client = VLAClient(config, rdm, robot)
    vla_client.startObserve()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序被中断")
    finally:
        robot.close()
        vla_client.close()