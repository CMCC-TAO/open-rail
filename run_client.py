import threading
import time
import matplotlib
import traceback
import select
import sys
import logging
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
from rich.console import Console
from client.utils.util import create_layout

def get_robot(config: ConfigDict):
    """Create and return a robot instance based on configuration
    
    Args:
        config: Configuration object containing robot type and settings
        
    Returns:
        RobotBody: Robot instance for the specified type
        
    Raises:
        ValueError: If robot type is not supported
    """
    if config.robots.type == RobotType.A2D:
        from client.robots.a2d.body_robot import RobotBody
        return RobotBody(config)
    elif config.robots.type == RobotType.MOCK:
        from client.robots.mock.body_robot import RobotBody
        return RobotBody(config)
    else:
        raise ValueError(f'Invalid Robot Type: {config.robots.type}')

def parse_args():
    """Parse command line arguments for VLA Client
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='VLA Client')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode, disable Live interface')
    parser.add_argument('--fps', type=int, help='FPS')
    parser.add_argument('--sleep_time', type=float, help='Inference sleep time')
    parser.add_argument('--show_data', action='store_true', help='Show data visualization')
    parser.add_argument('--record', action='store_true', help='Enable recording mode')
    parser.add_argument('--robots_type', type=str, help='Robot type')
    parser.add_argument('--thre_prob_progress', type=float, help='Probability threshold for switching language instructions')
    parser.add_argument('--preprocess', type=str, choices=['crop_and_resize', 'pad_and_resize', 'resize', 'none'], help='Image preprocessing method')
    parser.add_argument('--preprocess_size', nargs='+', type=int, help='Image preprocessing target size [height, width]')
    return parser.parse_args()

def override_config_with_args(config, args):
    """Override configuration with command line arguments
    
    Args:
        config: Original configuration object
        args: Command line arguments
        
    Returns:
        config: Updated configuration object
    """
    if args.fps is not None:
        config.observer.fps = args.fps
    if args.sleep_time is not None:
        config.sleep_time = args.sleep_time
    if args.show_data:
        config.show_data = True
    if args.record:
        config.record.switch = True
    if args.robots_type is not None:
        config.robots.type = args.robots_type
    if args.thre_prob_progress is not None:
        config.thre_prob_progress = args.thre_prob_progress
    if args.preprocess is not None:
        config.preprocess = args.preprocess
    if args.preprocess_size is not None:
        config.preprocess_size = args.preprocess_size
    return config

def handle_user_input(vla_client, robot, live):
    """Handle user input
    
    This function handles interactive command input when user presses Enter.
    It provides a menu-driven interface for robot control commands.
    """
    if live is not None:
        live.stop()
    
    try:
        vla_client.is_running_action = False
        cmd = input('Program paused, please enter command, press Enter to continue:\nr: Reset robot\nl: Modify language instruction\ns: Save data (if recording enabled)\nd: Delete data (if recording enabled)\nq: Quit\n')
        
        if cmd == 'l':
            # Show preset language options
            print("Available preset language instructions:")
            for i, lang in enumerate(vla_client.config.language, 1):
                print(f"{i}: {lang}")
            
            language_input = input('Please enter new language instruction or preset number, press Enter to confirm: ')
            if language_input.strip().isdigit():
                index = int(language_input.strip()) - 1
                if 0 <= index < len(vla_client.config.language):
                    vla_client.language = vla_client.config.language[index]
                    print(f"Language instruction has been set to preset #{language_input.strip()}: {vla_client.language}")
                else:
                    print(f"Invalid preset number: {language_input.strip()}. Please enter a number between 1 and {len(vla_client.config.language)}")
            else:
                vla_client.language = language_input.strip()
                print(f"Language instruction has been modified to: {vla_client.language}")
                
        elif cmd == 'r':
            robot.reset_robot(target_pose='default')
            vla_client.inference_first()
            input('Robot reset completed, program paused, press Enter to continue...')
            
        elif cmd == 's' and vla_client.config.record.switch:
            vla_client.dataset_write.save_writed_data()
            input('Data saved, press Enter to continue...')
            
        elif cmd == 'd' and vla_client.config.record.switch:
            vla_client.dataset_write.abandon_record_data()
            input('Data deleted, press Enter to continue...')
            
        elif cmd == 'q':
            return False  # Signal to quit
            
        vla_client.is_running_action = True
        return True  # Continue running
        
    finally:
        if live is not None:
            live.start()

if __name__ == "__main__":
    args = parse_args()
    # Initialize logging configuration    
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    
    # Get configuration and apply command line arguments
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
    
    live = None
    console = Console()
    try:
        vla_client.run()
        
        if not args.debug:
            terminal_size = console.size
            live = Live(create_layout({}, terminal_size), refresh_per_second=4)
            live.start()
        else:
            print("Debug mode enabled, press Enter to show commands")
        
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
                'robots_type': config.robots.type,
                'thre_prob_progress': config.thre_prob_progress
            }
            info['ctrl_info'] = {
                'language': vla_client.language,
                'is_running_action': vla_client.is_running_action,
            }
            info['obs_act_info'] = {
                'preprocess': config.preprocess,
                **vla_client.info_obs,
                **vla_client.info_act,
            }

            if live is not None:
                terminal_size = console.size
                live.update(create_layout(info, terminal_size))
            elif args.debug:
                print(f"infer_count: {info['infer_count']}, avg_infer_time: {info['avg_infer_time']}, "
                        f"avg_traj_time: {info['avg_traj_time']}, task_info: {info['ctrl_info']['language']}")

            # Check for user input using select
            if select.select([sys.stdin,], [], [], 0.001)[0]:
                user_input = sys.stdin.readline().strip()
                if user_input == '':
                    # Handle interactive command input
                    if not handle_user_input(vla_client, robot, live):
                        break  # Quit if user chose to quit

    except KeyboardInterrupt:
        logger.error('Program interrupted')
    except Exception as e:
        logger.error(f'Exception occurred: {str(e)}\nStack trace:\n{traceback.format_exc()}')
    finally:
        # Stop Live interface
        if live is not None:
            live.stop()
        
        vla_client.close()
        robot.close()
