import time
from conf.config import get_client_config
from client.robots.a2d.robot_a2d import RobotA2D

if __name__ == "__main__":
    config = get_client_config()
    # print(config)
    robot = RobotA2D(config.observer, config.controller)
    try:
        while True:
            observations = robot.retrieve_observation()
            if observations is not None:
                print(observations['ref_timestamp'])
                print(observations['obs.state'])
            time.sleep(0.001)  # 控制循环频率
    except KeyboardInterrupt:
        robot.close()