import time
from client.core import zmq_client
from conf.config import get_client_config
from client.robots.a2d import RobotA2D
from client.robots.base import RobotBase
from client.robots.mock_a2d import RobotA2DMock
from client.core.vla_client import VLAClient
from client.core.zmq_client import ZMQClient
from client.core.trajectory_generator import TrajectoryGenerator
from client.core.realtime_data_manager import RealtimeDataManager

if __name__ == "__main__":
    config = get_client_config()
    # print(config)
    zmq_client = ZMQClient(config.zmq)
    # robot = RobotA2D(config.observer, config.controller)
    repo_id = 'task_39_only1'
    root = '/home/robot/Music/task_39_only1'
    robot = RobotA2DMock(config.observer, config.controller, repo_id, root)
    rdm = RealtimeDataManager(config.rdm)
    traj_generator = TrajectoryGenerator(config=config.traj)
    vla_client = VLAClient(config=config, rdm=rdm, traj_generator=traj_generator, zmq_client=zmq_client, robot=robot)
    
    try:
        vla_client.run()
    except KeyboardInterrupt:
        print("程序被中断")
    finally:
        # pass
        robot.close()
        vla_client.close()