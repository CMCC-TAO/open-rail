import time
import matplotlib
from ml_collections import ConfigDict
from client.core import zmq_client
from conf.client_conf import get_client_config, RobotType
from client.robots.a2d.a2d import RobotA2D
from client.core.vla_client import VLAClient
from client.core.zmq_client import ZMQClient
from client.core.trajectory_generator import TrajectoryGenerator
from client.core.realtime_data_manager import RealtimeDataManager
import traceback
import select
import sys

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
        while True:
            time.sleep(0.1)
            # 检查是否有输入可用，超时：0.001s
            if select.select([sys.stdin,], [], [], 0.001)[0]:
                user_input = sys.stdin.readline().strip()
                if user_input == '':
                    vla_client.is_running_action = False
                    cmd = input('程序暂停，请输入指令，按Enter键继续：\nr：复位机器人\nl：修改语言指令\n')
                    vla_client.is_running_action = True
                    if cmd == 'l':
                        vla_client.is_running_action = False
                        language = input('请输入新的语言指令，按Enter键确认：')
                        vla_client.is_running_action = True
                        vla_client.language = language.strip()
                        print(f"语言指令已修改为: {vla_client.language}")
                    elif cmd == 'r':
                        vla_client.is_running_action = False
                        robot.reset_robot(target_pose='default')
                        input('机器人复位完成，程序暂停，按Enter键继续...')
                        vla_client.is_running_action = True
                        # self.initialize() # 状态已不在原来的位置，需要初始化，重新获取动作块
    except KeyboardInterrupt:
        print("程序被中断")
    except Exception as e:
        print(f"发生异常: {str(e)}\n堆栈信息:\n{traceback.format_exc()}")
    finally:
        # pass
        vla_client.close()
        robot.close()
