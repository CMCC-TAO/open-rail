import threading
import time
import traceback
import select
import sys
import argparse
import os
import signal
import subprocess
from ml_collections import ConfigDict
from conf.client_conf import get_client_config
from conf.robots_conf import RobotType
from conf.logging_conf import setup_logging
from client.core.vla_client import VLAClientAsync
from client.core.zmq_client import ZMQClient
from client.core.inter_chunk_fuser import InterChunkFuser
from client.core.intra_chunk_smoother import IntraChunkSmoother
from client.core.realtime_data_manager import RealtimeDataManager
from client.core.task_language_manager import TaskLanguageManager
from client.core.visualize_server import VisualizeServer
from client.utils.util import load_user_config, apply_user_config
from extra.dispatch.client import DispatchClient


def safely_release_visualize_port(self, port):
    """Release an occupied visualization port without invoking an empty shell kill."""
    try:
        result = subprocess.run(
            ['lsof', '-t', f'-i:{port}'],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return
    for value in result.stdout.split():
        if value.isdigit() and int(value) != os.getpid():
            os.kill(int(value), signal.SIGKILL)


VisualizeServer.kill_port = safely_release_visualize_port

def get_robot(config: ConfigDict):
    """Create and return a robot instance based on configuration
    
    Args:
        config: Configuration object containing robot type and settings
        
    Returns:
        RobotBody: Robot instance for the specified type
        
    Raises:
        ValueError: If robot type is not supported
    """
    robot_type = RobotType(config.robots.type)
    robot_config = getattr(config.robots, robot_type.value, None)
    if robot_config is None:
        raise ValueError(f'Configuration for robot type {robot_type.value} is missing')

    if robot_type == RobotType.A2D:
        from client.robots.a2d.body_robot import RobotBody
        return RobotBody(robot_config)
    elif robot_type == RobotType.MOCK:
        from client.robots.mock.body_robot import RobotBody
        return RobotBody(robot_config)
    elif robot_type == RobotType.NAVI_WA2:
        from client.robots.navi_wa2.body_robot import RobotBody
        return RobotBody(robot_config)
    else:
        raise ValueError(f'Invalid Robot Type: {robot_type}')

def parse_args():
    """Parse command line arguments for VLA-RAIL Client
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='VLA Client')
    parser.add_argument('--debug', action='store_true', help='Print runtime status')
    parser.add_argument('--fps', type=int, help='FPS')
    parser.add_argument('--wait_time', type=int, help='Wait time for the next inference step in milliseconds')
    parser.add_argument('--gripper_offset', type=int, help='Gripper forward offset')
    parser.add_argument('--search_length', type=int, help='Forward search length')
    parser.add_argument('--intra_chunk_mode', type=str, choices=['raw', 'interpolation', 'fitting'], help='Intra-chunk processing mode: interpolation=process with interpolation')
    parser.add_argument('--inter_chunk_mode', type=str, choices=['search_action', 'smooth_velocity', 'min_jerk', 'sync'], help='The method to bridge action chunks')
    parser.add_argument('--record', action='store_true', help='Enable recording mode')
    parser.add_argument('--robots_type', type=str, choices=[item.value for item in RobotType], help='Robot type')
    parser.add_argument('--task_progress_threshold', type=float, help='Probability threshold for switching language instructions')
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
    if args.wait_time is not None:
        config.controller.wait_time = args.wait_time
    if args.gripper_offset is not None:
        config.controller.gripper_offset = args.gripper_offset
    if args.intra_chunk_mode is not None:
        config.intra_chunk.intra_chunk_mode = args.intra_chunk_mode
    if args.search_length is not None:
        config.inter_chunk.search_action.search_length = args.search_length
    if args.inter_chunk_mode is not None:
        config.inter_chunk.inter_chunk_mode = args.inter_chunk_mode
    if args.record:
        config.record.switch = True
    if args.robots_type is not None:
        config.robots.type = RobotType(args.robots_type)
    if args.task_progress_threshold is not None:
        config.language.task_progress_threshold = args.task_progress_threshold
    if args.preprocess is not None:
        config.vision.preprocess = args.preprocess
    if args.preprocess_size is not None:
        config.vision.preprocess_size = args.preprocess_size
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


def pause_vla_client_actions(vla_client):
    if hasattr(vla_client, 'pause'):
        vla_client.pause()
        return
    if hasattr(vla_client, 'is_observe_thread_running'):
        vla_client.is_observe_thread_running = False
    if hasattr(vla_client, 'is_inference_thread_running'):
        vla_client.is_inference_thread_running = False
    if hasattr(vla_client, 'is_control_thread_running'):
        vla_client.is_control_thread_running = False
    if hasattr(vla_client, 'is_running_action'):
        vla_client.is_running_action = False


def resume_vla_client_actions(vla_client):
    if hasattr(vla_client, 'resume'):
        vla_client.resume()
        return
    if hasattr(vla_client, 'is_observe_thread_running'):
        vla_client.is_observe_thread_running = True
    if hasattr(vla_client, 'is_inference_thread_running'):
        vla_client.is_inference_thread_running = True
    if hasattr(vla_client, 'is_control_thread_running'):
        vla_client.is_control_thread_running = True
    if hasattr(vla_client, 'is_running_action'):
        vla_client.is_running_action = True


def handle_user_input(vla_client, robot):
    """Handle user input
    
    This function handles interactive command input when user presses Enter.
    It provides a menu-driven interface for robot control commands.
    """
    pause_vla_client_actions(vla_client)
    cmd = input('\nProgram paused, please enter command, press Enter to continue:\nr: reset robot\nc: control robot\nl: modify language instruction\ns: save data (if recording enabled)\nd: delete data (if recording enabled)\nq: quit\n')
    language_reset_pos = getattr(vla_client.config, 'language_reset_pos', None)
        
    if cmd == 'l':
        # Show preset language options
        print("Available preset language instructions:")
        for i, lang in enumerate(vla_client.task_language_manager.task_language_map["make_coffee"], 1):
            print(f"{i}: {lang}")
            
        language_input = input(f'#Current language: "{vla_client.task_language_manager.currt_language_instruction}". \nPlease enter new language instruction or preset number, press Enter to confirm: ')
        if language_input.strip().isdigit():
            index = int(language_input.strip()) - 1
            if 0 <= index < len(vla_client.task_language_manager.task_language_map["make_coffee"]):
                vla_client.task_language_manager.currt_language_instruction = vla_client.task_language_manager.task_language_map["make_coffee"][index]
                print(f"Language instruction has been set to preset #{language_input.strip()}: {vla_client.task_language_manager.currt_language_instruction}")
            else:
                print(f"Invalid preset number: {language_input.strip()}. Please enter a number between 1 and {len(vla_client.config.language)}")
        else:
            vla_client.task_language_manager.currt_language_instruction = language_input.strip()
            print(f"Language instruction has been modified to: {vla_client.language}")
        ys_cmd = input('Whether to reset the robot? (y/n): ')
        if ys_cmd == 'y':
            if language_reset_pos is None:
                robot.reset_robot(mode='default')
                vla_client._inference_first()
                input('\nRobot reset completed, program paused, press Enter to continue...')
            else:
                lang_idx = vla_client.task_language_manager.task_language_map["make_coffee"].index(vla_client.task_language_manager.currt_language_instruction)
                target_pose = language_reset_pos[lang_idx]
                robot.reset_robot(target_pose=target_pose)
                vla_client._inference_first()
                input('\nRobot reset completed, program paused, press Enter to continue...')
    elif cmd == 'r':
        if language_reset_pos is None:
            robot.reset_robot(mode='default')
            vla_client._inference_first()
            input('\nRobot reset completed, program paused, press Enter to continue...')
        else:
            lang_idx = vla_client.task_language_manager.task_language_map["make_coffee"].index(vla_client.task_language_manager.currt_language_instruction)
            target_pose = language_reset_pos[lang_idx]
            robot.reset_robot(target_pose=target_pose)
            vla_client._inference_first()
            input('\nRobot reset completed, program paused, press Enter to continue...')
    elif cmd == 's' and vla_client.config.record.switch:
        # vla_client.data_recorder.save_writed_data()
        input('Data saved, press Enter to continue...')
    elif cmd == 'd' and vla_client.config.record.switch:
        # vla_client.data_recorder.abandon_record_data()
        input('Data deleted, press Enter to continue...')
    elif cmd == 'q':
        return False  # Signal to quit
        
    vla_client._inference_first() # avoid pause/restart shaking
    resume_vla_client_actions(vla_client)
    return True  # Continue running

if __name__ == "__main__":
    args = parse_args()
    # Initialize logging configuration
    logger = setup_logging("client.log", __name__)
    
    # Get configuration and apply command line arguments
    config = get_client_config()
    
    # Load and apply user configuration if provided
    if args.user_conf:
        user_config = load_user_config(args.user_conf)
        config = apply_user_config(config, user_config)
    
    config = override_config_with_args(config, args)
    # print(config)
    # The zmq client to communicate with VLA server
    vla_zmq_client = ZMQClient(config.vla_zmq)
    
    robot = get_robot(config)
    robot_cfg = getattr(config.robots, config.robots.type.value, None)
    if robot_cfg is not None and hasattr(robot_cfg, 'action_layout'):
        config.rdm.action_layout = robot_cfg.action_layout
        config.intra_chunk.action_layout = robot_cfg.action_layout
    realtime_data_manager = RealtimeDataManager(config.rdm)
    inter_chunk_fuser = InterChunkFuser(config=config.inter_chunk)
    intra_chunk_smoother = IntraChunkSmoother(config=config.intra_chunk)
    task_language_manager = TaskLanguageManager(config=config.language)
    vla_client = VLAClientAsync(
        config=config,
        realtime_data_manager=realtime_data_manager,
        inter_chunk_fuser=inter_chunk_fuser,
        intra_chunk_smoother=intra_chunk_smoother,
        task_language_manager=task_language_manager,
        vla_zmq_client=vla_zmq_client,
        robot=robot
        )

    # extra
    if args.extra_dispatch_mode[0] != '0':
        dispatch_client = DispatchClient(vla_client, robot, args)
        dispatch_client.start()
    
    try:
        vla_client.start()

        print("Client started, press Enter to show commands")
        if args.extra_dispatch_mode[0] == '2':
            mock_task_thread = threading.Thread(target=dispatch_client.mock_task)
            mock_task_thread.daemon = True
            mock_task_thread.start()

        stdin_open = sys.stdin.isatty()
        last_status_time = 0.0
        while True:
            time.sleep(0.1)
            if args.debug and time.time() - last_status_time >= 1.0:
                print(f"\rinfer_count: {vla_client.realtime_data_manager.infer_count}, avg_infer_time: {vla_client.realtime_data_manager.avg_infer_time: .4f}s, "
                        f"task_info: {task_language_manager.currt_language_instruction}", end='', flush=True)
                last_status_time = time.time()

            # Check for user input using select
            if stdin_open and select.select([sys.stdin], [], [], 0.001)[0]:
                user_input = sys.stdin.readline()
                if user_input == '':
                    stdin_open = False
                    logger.info('Standard input closed; interactive commands disabled.')
                elif user_input.strip() == '':
                    # Handle interactive command input
                    if not handle_user_input(vla_client, robot):
                        break  # Quit if user chose to quit

    except KeyboardInterrupt:
        logger.error('Program interrupted')
    except Exception as e:
        error_trace = traceback.format_exc()
        print(error_trace, file=sys.stderr, flush=True)
        logger.error(f'Exception occurred: {str(e)}\nStack trace:\n{error_trace}')
    finally:
        vla_client.close()
        robot.close()
