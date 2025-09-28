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
from client.utils.util import create_layout, load_user_config, apply_user_config
from extra.dispatch.client import DispatchClient

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
    parser.add_argument('--gripper_offset', type=int, help='Gripper forward offset')
    parser.add_argument('--search_length', type=int, help='Forward search length')
    parser.add_argument('--show_data', action='store_true', help='Show data visualization')
    parser.add_argument('--record', action='store_true', help='Enable recording mode')
    parser.add_argument('--robots_type', type=str, choices=['a2d', 'mock'], help='Robot type')
    parser.add_argument('--thre_prob_progress', type=float, help='Probability threshold for switching language instructions')
    parser.add_argument('--preprocess', type=str, choices=['crop_and_resize', 'pad_and_resize', 'resize', 'none'], help='Image preprocessing method')
    parser.add_argument('--preprocess_size', nargs='+', type=int, help='Image preprocessing target size [height, width]')
    parser.add_argument('--language', nargs='+', type=str, help='Language instruction options')
    parser.add_argument('--user_conf', type=str, help='Path to user configuration file')
    parser.add_argument('--extra_dispatch_mode', nargs='+', type=str, default=['0'], help='Extra dispatch mode and target robot. First param: 0=disable, 1=enable, 2=mock. Second param (optional): target robot (robotB, robotC, robotD, etc.). Example: --extra_dispatch_mode 2 robotB')
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
    if args.gripper_offset is not None:
        config.gripper_offset = args.gripper_offset
    if args.show_data:
        config.show_data = True
    if args.record:
        config.record.switch = True
    if args.robots_type is not None:
        config.robots.type = RobotType(args.robots_type)
    if args.thre_prob_progress is not None:
        config.thre_prob_progress = args.thre_prob_progress
    if args.preprocess is not None:
        config.preprocess = args.preprocess
    if args.preprocess_size is not None:
        config.preprocess_size = args.preprocess_size
    if args.language is not None:
        config.language = args.language
    return config

# TODO: global variable
wheel_thread_running = False
wheel_pos = [0, 0]

def wheel_control_loop(robot):
    global wheel_thread_running, wheel_pos
    while wheel_thread_running:
        robot.execute_action({'wheel': wheel_pos})
        time.sleep(0.05)

def handle_user_input(vla_client, robot, live):
    """Handle user input
    
    This function handles interactive command input when user presses Enter.
    It provides a menu-driven interface for robot control commands.
    """
    if live is not None:
        live.stop()
    
    try:
        vla_client.is_running_action = False
        cmd = input('\nProgram paused, please enter command, press Enter to continue:\nr: reset robot\nc: control robot\nl: modify language instruction\ns: save data (if recording enabled)\nd: delete data (if recording enabled)\nq: quit\n')
        
        if cmd == 'l':
            # Show preset language options
            print("Available preset language instructions:")
            for i, lang in enumerate(vla_client.config.language, 1):
                print(f"{i}: {lang}")
            
            language_input = input(f'#Current language: "{vla_client.language}". \nPlease enter new language instruction or preset number, press Enter to confirm: ')
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
            ys_cmd = input('Whether to reset the robot? (y/n): ')
            if ys_cmd == 'y':
                robot.reset_robot(mode='default')
                vla_client.inference_first()
        elif cmd == 'r':
            robot.reset_robot(mode='default')
            vla_client.inference_first()
            input('\nRobot reset completed, program paused, press Enter to continue...')
        elif cmd == 'c':
            print("Control robot cmd:\n1. open gripper\n2. close gripper\n3. control gripper\n4. control head\n5. control waist\n6. control wheel\nq. quit control robot")
            while True:
                cmd = input("Please input new control robot cmd number: ")
                if cmd == 'q':
                    break
                elif cmd == '1':
                    robot.execute_action({'gripper': [0.0, 0.0]})
                elif cmd == '2':
                    robot.execute_action({'gripper': [1.0, 1.0]})
                elif cmd == '3':
                    gripper_pos = input("Please input gripper position (left right, e.g.: 0.5 0.5): ")
                    gripper_pos = [float(x) for x in gripper_pos.split()]
                    if len(gripper_pos) > 0:
                        print(f'gripper_pos: {gripper_pos}')
                        robot.execute_action({'gripper': gripper_pos})
                elif cmd == '4':
                    head_pos = input("Please input head position (yaw pitch, e.g.: 0.0 0.436): ")
                    head_pos = [float(x) for x in head_pos.split()]
                    if len(head_pos) > 0:
                        print(f'head_pos: {head_pos}')
                        robot.execute_action({'head': head_pos})
                elif cmd == '5':
                    waist_pos = input("Please input waist position (pitch_rad height_cm, e.g.: 0.297 20.0): ")
                    waist_pos = [float(x) for x in waist_pos.split()]
                    if len(waist_pos) > 0:
                        print(f'waist_pos: {waist_pos}')
                        robot.execute_action({'waist': waist_pos})
                elif cmd == '6':
                    global wheel_thread_running, wheel_pos
                    
                    wheel_thread_running = True
                    wheel_pos = [0, 0]
                    wheel_thread = threading.Thread(target=wheel_control_loop, args=(robot,))
                    wheel_thread.daemon = True
                    wheel_thread.start()
                    
                    print("Wheel control thread started. w: forward, s: backward, a: left, d: right, Enter: stop, q: quit wheel control")
                    while True:
                        wheel_cmd = input()
                        if wheel_cmd == 'w':
                            wheel_pos = [0.1, 0.]
                        elif wheel_cmd == 's':
                            wheel_pos = [-0.1, 0]
                        elif wheel_cmd == 'a':
                            wheel_pos = [0, 0.1]
                        elif wheel_cmd == 'd':
                            wheel_pos = [0, -0.1]
                        elif wheel_cmd == '':
                            wheel_pos = [0, 0]
                        elif wheel_cmd == 'q':
                            wheel_thread_running = False
                            wheel_thread.join(timeout=1.0)
                            print("Wheel control thread stopped.")
                            break
                        print(f'send cmd: {wheel_pos}')
                else:
                    print("Invalid cmd number")
                print('Control robot cmd completed!')
            vla_client.inference_first()
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
    
    # Load and apply user configuration if provided
    if args.user_conf:
        user_config = load_user_config(args.user_conf)
        config = apply_user_config(config, user_config)
    
    config = override_config_with_args(config, args)
    
    if not config.show_data:
        matplotlib.use('Agg')
    # print(config)
    zmq_client = ZMQClient(config.zmq)
    
    robot = get_robot(config)
    rdm = RealtimeDataManager(config.rdm)
    traj_generator = TrajectoryGenerator(config=config.traj)
    vla_client = VLAClient(config=config, rdm=rdm, traj_generator=traj_generator, zmq_client=zmq_client, robot=robot)

    # extra
    if args.extra_dispatch_mode[0] != '0':
        dispatch_client = DispatchClient(vla_client, robot, args)
        dispatch_client.start()
    
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
            if args.extra_dispatch_mode[0] == '2':
                mock_task_thread = threading.Thread(target=dispatch_client.mock_task)
                mock_task_thread.daemon = True
                mock_task_thread.start()

        while True:
            time.sleep(0.1)
            info = {'config': config, 'vla_client': vla_client}

            if live is not None:
                terminal_size = console.size
                live.update(create_layout(info, terminal_size))
            elif args.debug:
                print(f"\rinfer_count: {vla_client.rdm.infer_count}, avg_infer_time: {vla_client.rdm.avg_infer_time: .4f}s, "
                        f"task_info: {vla_client.language}", end='')

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
