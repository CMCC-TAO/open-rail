import threading
import time
import matplotlib
import traceback
import select
import sys
import logging
import readchar
import argparse
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

def parse_args():
    parser = argparse.ArgumentParser(description='VLA Client')
    parser.add_argument('--debug', action='store_true', help='启用调试模式，关闭Live界面')
    parser.add_argument('--fps', type=int, help='observer fps')
    parser.add_argument('--sleep_time', type=float, help='infer sleep time')
    parser.add_argument('--show_data', action='store_true', help='显示数据')
    parser.add_argument('--record', action='store_true', help='启用记录模式')
    return parser.parse_args()

def override_config_with_args(config, args):
    if args.fps is not None:
        config.observer.fps = args.fps
    if args.sleep_time is not None:
        config.sleep_time = args.sleep_time
    if args.show_data:
        config.show_data = True
    if args.record:
        config.record.switch = True
    return config

def key_thread():
    global cmd_text, exit_flag
    while not exit_flag:
        try:
            key = readchar.readkey()
            if key == readchar.key.ENTER:
                # 保存当前命令到last_cmd
                if cmd_text != '' and cmd_text != '|':
                    key_thread.last_cmd = cmd_text
                cmd_text = ''
            elif key == readchar.key.BACKSPACE:
                if cmd_text == '':
                    cmd_text = '|'
                else:
                    cmd_text = cmd_text[:-1]
                    if cmd_text == '':
                        cmd_text = '|'
            else:
                if cmd_text == '|':
                    cmd_text = key
                else:
                    cmd_text = cmd_text + key
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"键盘输入线程异常: {e}")
            time.sleep(0.1)

if __name__ == "__main__":
    args = parse_args()
    # 初始化日志配置    
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    # logger.info("This is a info level log")
    # logger.debug("This is a debug level log")
    
    # 获取配置并应用命令行参数
    config = get_client_config()
    config = override_config_with_args(config, args)
    
    if not config.show_data:
        matplotlib.use('Agg')
    # print(config)
    zmq_client = ZMQClient(config.zmq)
    
    robot = get_robot(config)
    rdm = RealtimeDataManager(config.rdm)
    traj_generator = TrajectoryGenerator(config=config.traj)
    vla_client = VLAClient(config=config, rdm=rdm, traj_generator=traj_generator, zmq_client=zmq_client, robot=robot)
    
    cmd_text, exit_flag = '', False
    cmd_current_state = 'normal'  # 状态管理：normal, waiting_command, waiting_language, waiting_continue, waiting_save, waiting_delete, paused
    
    live = None
    key_thread_obj = None
    try:
        vla_client.run()
        key_thread_obj = threading.Thread(target=key_thread, daemon=False)
        key_thread_obj.start()
        
        # 根据debug模式决定是否启用Live界面
        if not args.debug:
            live = Live(create_layout({}), refresh_per_second=4)
            live.start()
        else:
            print("调试模式已启用，可用命令: reset, language, save, delete, quit")
            
        while True:
            time.sleep(0.1)
            info = {}
            info['infer_count'] = vla_client.rdm.infer_count
            info['avg_infer_time'] = f'{vla_client.rdm.avg_infer_time: .4f}s'
            info['avg_traj_time'] = f'{vla_client.rdm.avg_traj_time: .4f}s'
            info['debug_info'] = vla_client.debug_info
            info['robot_current_action'] = vla_client.info_current_action
            info['robot_current_state'] = vla_client.info_current_state
            info['config_info'] = {
                'record': config.record.switch,
                'fps': config.observer.fps,
                'sleep_time': config.sleep_time,
            }
            info['ctrl_info'] = {
                'language': vla_client.language,
                'is_running_action': vla_client.is_running_action,
                'cmd_current_state': cmd_current_state,
            }
            # 只用来传递参数，不显示
            info['data_info'] = {
                'cmd_current_state': cmd_current_state,
                'preset_languages': vla_client.config.language,
            }
            
            if cmd_text == '':
                cmd_text = '|'
            elif cmd_text == '|':
                cmd_text = ''
            info['cmd_key'] = cmd_text
            
            # 检查是否开始输入时暂停
            if cmd_current_state == 'normal' and cmd_text != '|' and cmd_text != '':
                vla_client.is_running_action = False
                cmd_current_state = 'paused'
            
            # 检查是否有新命令
            if hasattr(key_thread, 'last_cmd'):
                cmd = key_thread.last_cmd
                delattr(key_thread, 'last_cmd')
                
                if cmd_current_state in ['normal', 'paused']:
                    if cmd == 'reset':
                        vla_client.is_running_action = False
                        robot.reset_robot(target_pose='default')
                        cmd_current_state = 'waiting_continue'
                    elif cmd == 'lang':
                        vla_client.is_running_action = False
                        cmd_current_state = 'waiting_language'
                    elif cmd == 'save' and vla_client.config.record.switch:
                        vla_client.is_running_action = False
                        vla_client.dataset_write.save_writed_data()
                        cmd_current_state = 'waiting_save'
                    elif cmd == 'delete' and vla_client.config.record.switch:
                        vla_client.is_running_action = False
                        vla_client.dataset_write.abandon_record_data()
                        cmd_current_state = 'waiting_delete'
                    elif cmd == 'quit':
                        break
                    else:
                        # 其他输入或空输入，恢复运行
                        vla_client.is_running_action = True
                        cmd_current_state = 'normal'
                elif cmd_current_state == 'waiting_language':
                    if cmd.strip():  # 有输入新的语言指令
                        if cmd.strip().isdigit():
                            index = int(cmd.strip()) - 1
                            if 0 <= index < len(vla_client.config.language):
                                vla_client.language = vla_client.config.language[index]
                                logger.info(f"language instruction has been set to preset #{cmd.strip()}: {vla_client.language}")
                            else:
                                logger.warning(f"Invalid preset number: {cmd.strip()}. Please enter a number between 1 and {len(vla_client.config.language)}")
                        else:
                            # 直接输入自定义语言指令
                            vla_client.language = cmd.strip()
                            logger.info(f"language instruction has been modified to: {vla_client.language}")
                    vla_client.is_running_action = True
                    cmd_current_state = 'normal'
                elif cmd_current_state in ['waiting_save', 'waiting_delete', 'waiting_continue']:
                    # 不需要进一步反馈处理的都继续程序
                    vla_client.is_running_action = True
                    cmd_current_state = 'normal'

            if live is not None:
                live.update(create_layout(info))
            elif args.debug:
                print(f"infer_count: {info['infer_count']}, avg_infer_time: {info['avg_infer_time']}, "
                        f"avg_traj_time: {info['avg_traj_time']}, task_info: {info['ctrl_info']['language']}, "
                        f"cmd_current_state: {info['ctrl_info']['cmd_current_state']}, cmd_key: {info['cmd_key']}")
    except KeyboardInterrupt:
        logger.error('程序被中断')
    except Exception as e:
        logger.error(f'发生异常: {str(e)}\n堆栈信息:\n{traceback.format_exc()}')
    finally:
        # 设置退出标志，让键盘线程退出
        exit_flag = True
        # 防止ctrl+c停不掉live
        if live is not None:
            live.stop()
        # 等待键盘线程结束
        if key_thread_obj is not None and key_thread_obj.is_alive():
            try:
                key_thread_obj.join(timeout=1.0)
            except Exception as e:
                print(f"等待键盘线程退出时出错: {e}")
        
        vla_client.close()
        robot.close()
