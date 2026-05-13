import cv2
import zmq
import os
import sys
import time
import json
import base64
import numpy as np
import argparse
import logging

# Add the project root directory to Python path to ensure proper module imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import project modules
from client.core.vla_client import VLAClient
from client.core.zmq_client import ZMQClient
from conf.logging_conf import setup_logging
from conf.client_conf import get_client_config

from client.utils.util import load_user_config, apply_user_config


def init_camera(camera_id=0):
    """
    Initialize camera device
    
    Args:
        camera_id (int): Camera device ID, default is 0
        
    Returns:
        cv2.VideoCapture: Camera capture object
        
    Raises:
        RuntimeError: Raised when camera cannot be opened
    """
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        raise RuntimeError("Failed to open camera")
    return cap


def read_and_process_frame(cap):
    """
    Read camera frame and process it: convert color space, resize, encode to jpg format
    
    Args:
        cap (cv2.VideoCapture): Camera capture object
        
    Returns:
        dict: Dictionary containing processed image data
        
    Raises:
        RuntimeError: Raised when reading camera frame fails
    """
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Failed to read camera frame")
    
    # Convert BGR format to RGB format
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Resize image to 640x640
    img_processed = cv2.resize(frame, (640, 640))
    # Encode image to jpg format
    img_encoded = cv2.imencode('.jpg', img_processed)[1]

    # Construct observation data dictionary, simulating image data from multiple cameras
    obs = {
        "cam.top_head": img_encoded,      # Top camera image
        "cam.left_wrist": img_encoded,    # Left wrist camera image
        "cam.right_wrist": img_encoded,   # Right wrist camera image
    }

    data = {"obs": obs}
    return data


def send_data_zmq(socket, data):
    """
    Send JSON formatted data through ZMQ
    
    Args:
        socket: ZMQ socket object
        data (dict): Data dictionary to be sent
    """
    msg = json.dumps(data)
    socket.send_string(msg)


def print_keys(dictionary, prefix=''):
    """
    Recursively print the key structure of a dictionary
    
    Args:
        dictionary (dict): Dictionary to print
        prefix (str): Key name prefix
    """
    for key, value in dictionary.items():
        print(prefix + str(key))
        if isinstance(value, dict):
            print_keys(value, prefix + key + '.')


def main_loop(vis_action_cams_zmq_client):
    """
    Main loop function: continuously read camera data, process it, and send to ZMQ client
    
    Args:
        vis_action_cams_zmq_client (ZMQClient): ZMQ client used for sending data
    """
    # Initialize camera
    cap = init_camera()

    print("Start sending simulated data to visualization ZMQ (Ctrl+C to exit)")
 
    sending_count = 0
    try:
        while True:
            # Read and process camera frame
            data = read_and_process_frame(cap)
            # Print data structure
            print_keys(data)
            # Add randomly generated action data (simulation)
            data['actions_fitted'] = np.random.rand(1000, 16)  # Fitted action data
            data['actions_raw'] = np.random.rand(1000, 16)     # Raw action data
            # Send data to ZMQ client
            vis_action_cams_zmq_client.sendMessage(data)
            print("="*120)
            print("sending_count: ", sending_count)
            sending_count += 1
            time.sleep(0.1)   # Delay to control sending frequency, approximately 10 frames per second
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        # Release camera resources
        cap.release()


def parse_args():
    """
    Parse command line arguments
    
    Returns:
        argparse.Namespace: Parsed command line arguments object
    """
    parser = argparse.ArgumentParser(description='VLA Client Application')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode, disable live interface')
    parser.add_argument('--fps', type=int, help='Frame rate setting')
    parser.add_argument('--sleep_time', type=float, help='Inference sleep time')
    parser.add_argument('--gripper_offset', type=int, help='Gripper forward offset')
    parser.add_argument('--search_length', type=int, help='Forward search length')
    parser.add_argument('--show_action_state', action='store_true', help='Show action and state visualization')
    parser.add_argument('--show_action_cams', action='store_true', help='Show action and camera images visualization')
    parser.add_argument('--record', action='store_true', help='Enable recording mode')
    parser.add_argument('--robots_type', type=str, choices=['a2d', 'mock'], help='Robot type')
    parser.add_argument('--task_progress_threshold', type=float, help='Probability threshold for switching language instructions')
    parser.add_argument('--preprocess', type=str, choices=['crop_and_resize', 'pad_and_resize', 'resize', 'none'], help='Image preprocessing method')
    parser.add_argument('--preprocess_size', nargs='+', type=int, help='Image preprocessing target size [height, width]')
    parser.add_argument('--language', nargs='+', type=str, help='Language instruction options')
    parser.add_argument('--user_conf', type=str, help='Path to user configuration file')
    parser.add_argument('--extra_dispatch_mode', nargs='+', type=str, default=['0'], help='Extra dispatch mode and target robot. First param: 0=disable, 1=enable, 2=mock. Second param (optional): target robot (robotB, robotC, robotD, etc.). Example: --extra_dispatch_mode 2 robotB')
    return parser.parse_args()


def override_config_with_args(config, args):
    """
    Override configuration with command line arguments
    
    Args:
        config: Original configuration object
        args: Command line arguments object
        
    Returns:
        config: Updated configuration object
    """
    if args.fps is not None:
        config.observer.fps = args.fps
    if args.sleep_time is not None:
        config.sleep_time = args.sleep_time
    if args.gripper_offset is not None:
        config.gripper_offset = args.gripper_offset
    if args.show_action_state:
        config.show_action_state = True
    if args.show_action_cams:
        config.show_action_cams = True
    if args.record:
        config.record.switch = True
    if args.robots_type is not None:
        config.robots.type = RobotType(args.robots_type)
    if args.task_progress_threshold is not None:
        config.language.task_progress_threshold = args.task_progress_threshold
    if args.preprocess is not None:
        config.preprocess = args.preprocess
    if args.preprocess_size is not None:
        config.preprocess_size = args.preprocess_size
    if args.language is not None:
        config.language = args.language
    return config


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    # Initialize logging configuration
    logger = setup_logging("client.log", __name__)
    
    # Get configuration and apply command line arguments
    config = get_client_config()
    
    # Load and apply user configuration if provided
    if args.user_conf:
        user_config = load_user_config(args.user_conf)
        config = apply_user_config(config, user_config)
    
    # Override configuration with command line arguments
    config = override_config_with_args(config, args)

    # Create ZMQ client for visualizing actions and camera data
    vis_action_cams_zmq_client = ZMQClient(config.vis_zmq)

    # Run main loop
    main_loop(vis_action_cams_zmq_client)
