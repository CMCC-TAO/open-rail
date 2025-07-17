import threading
import time
import matplotlib
import traceback
import select
import sys
import logging
import readchar
from ml_collections import ConfigDict
from client.core import zmq_client
from conf.client_conf import get_client_config
from conf.robots_conf import RobotType
from conf.logging_conf import LOGGING_CONFIG
from client.core.vla_client import VLAClient
from client.core.zmq_client import ZMQClient
from client.core.trajectory_generator import TrajectoryGenerator
from client.core.realtime_data_manager import RealtimeDataManager
from rich.live import Live
from client.utils.util import create_layout

def get_robot(config: ConfigDict):
    if config.robots.type == RobotType.A2D:
        from client.robots.a2d.body_robot import RobotBody
        return RobotBody(config)
    elif config.robots.type == RobotType.MOCK:
        from client.robots.mock.body_robot import RobotBody
        return RobotBody(config)
    else:
        raise ValueError(f'Invalid Robot Type: {config.robots.type}')

def key_thread():
    global cmd_text
    while True:
        key = readchar.readkey()
        if key == readchar.key.ENTER:
            cmd_text = ''
        elif key == readchar.key.BACKSPACE:
            cmd_text = cmd_text[:-1]
        else:
            if cmd_text == '|':
                cmd_text = key
            else:
                cmd_text = cmd_text + key
        # time.sleep(0.05)

if __name__ == "__main__":
    # 初始化日志配置    
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    # logger.info("This is a info level log")
    # logger.debug("This is a debug level log")
    config = get_client_config()
    if not config.show_data:
        matplotlib.use('Agg')
    # print(config)
    zmq_client = ZMQClient(config.zmq)
    
    robot = get_robot(config)
    rdm = RealtimeDataManager(config.rdm)
    traj_generator = TrajectoryGenerator(config=config.traj)
    vla_client = VLAClient(config=config, rdm=rdm, traj_generator=traj_generator, zmq_client=zmq_client, robot=robot)
    
    cmd_text = ''


    try:
        vla_client.run()
        threading.Thread(target=key_thread, daemon=True).start()
        with Live(create_layout({}), refresh_per_second=4) as live:
            while True:
                time.sleep(0.1)
                info = {}
                info['infer_count'] = vla_client.rdm.infer_count
                info['avg_infer_time'] = f'{vla_client.rdm.avg_infer_time: .4f}s'
                info['avg_traj_time'] = f'{vla_client.rdm.avg_traj_time: .4f}s'
                info['task_info'] = 'Pick the bottle to the black box.'
                info['debug_info'] = vla_client.debug_info
                if cmd_text == '':
                    cmd_text = '|'
                elif cmd_text == '|':
                    cmd_text = ''
                info['cmd_key'] = cmd_text
                # if select.select([sys.stdin,], [], [], 0.001)[0]:
                #     user_input = sys.stdin.readline().strip()
                #     if user_input == '':
                #         live.stop()
                #         try:
                #             vla_client.is_running_action = False
                #             # cmd = input('程序暂停，请输入指令，按Enter键继续：\nr：复位机器人\nl：修改语言指令\n')
                #             cmd = input('Please input command:')
                #             vla_client.is_running_action = True
                #             if cmd == 'l':
                #                 vla_client.is_running_action = False
                #                 language = input('请输入新的语言指令，按Enter键确认：')
                #                 vla_client.is_running_action = True
                #                 vla_client.language = language.strip()
                #                 print(f"语言指令已修改为: {vla_client.language}")
                #             elif cmd == 'r':
                #                 vla_client.is_running_action = False
                #                 robot.reset_robot(target_pose='default')
                #                 input('机器人复位完成，程序暂停，按Enter键继续...')
                #                 vla_client.is_running_action = True
                #         finally:
                #             live.start()
                live.update(create_layout(info))
        # while True:
        #     time.sleep(0.1)
        #     # 检查是否有输入可用，超时：0.001s
        #     if select.select([sys.stdin,], [], [], 0.001)[0]:
        #         user_input = sys.stdin.readline().strip()
        #         if user_input == '':
        #             vla_client.is_running_action = False
        #             cmd = input('程序暂停，请输入指令，按Enter键继续：\nr：复位机器人\nl：修改语言指令\n')
        #             vla_client.is_running_action = True
        #             if cmd == 'l':
        #                 vla_client.is_running_action = False
        #                 language = input('请输入新的语言指令，按Enter键确认：')
        #                 vla_client.is_running_action = True
        #                 vla_client.language = language.strip()
        #                 print(f"语言指令已修改为: {vla_client.language}")
        #             elif cmd == 'r':
        #                 vla_client.is_running_action = False
        #                 robot.reset_robot(target_pose='default')
        #                 input('机器人复位完成，程序暂停，按Enter键继续...')
        #                 vla_client.is_running_action = True
                        # self.initialize() # 状态已不在原来的位置，需要初始化，重新获取动作块
    except KeyboardInterrupt:
        logger.error('程序被中断')
    except Exception as e:
        logger.error(f'发生异常: {str(e)}\n堆栈信息:\n{traceback.format_exc()}')
    finally:
        # pass
        vla_client.close()
        robot.close()
