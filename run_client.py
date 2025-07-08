import time
import matplotlib
from ml_collections import ConfigDict
from client.core import zmq_client
from conf.client_conf import get_client_config, RobotType
from client.robots.a2d.a2d import RobotA2D
from client.robots.base import RobotBase
from client.core.vla_client import VLAClient
from client.core.zmq_client import ZMQClient
from client.core.trajectory_generator import TrajectoryGenerator
from client.core.realtime_data_manager import RealtimeDataManager

def get_robot(config: ConfigDict):
    if config.robot == RobotType.A2D:
        return RobotA2D(config.observer, config.controller)
    elif config.robot == RobotType.MOCK:
        from client.robots.mock_a2d import RobotA2DMock
        repo_id = 'task_39_only1'
        root = '/home/robot/Music/task_39_only1'
        return RobotA2DMock(config.observer, config.controller, repo_id, root)
    else:
        raise ValueError(f'Invalid Robot Type: {config.robot}')
    
if __name__ == "__main__":
    config = get_client_config()
    if not config.show_data:
        matplotlib.use('Agg')
    # print(config)
    zmq_client = ZMQClient(config.zmq)

    # import subprocess
    # subprocess.run("source robots/a2d/a2d_sdk/env.zsh", shell=True) # 无效

    robot = get_robot(config=config)
    rdm = RealtimeDataManager(config.rdm)
    traj_generator = TrajectoryGenerator(config=config.traj)
    vla_client = VLAClient(config=config, rdm=rdm, traj_generator=traj_generator, zmq_client=zmq_client, robot=robot)
    
    try:
        vla_client.run()
    except KeyboardInterrupt:
        print("程序被中断")
    finally:
        # pass
        vla_client.close()
        robot.close()
