#! /usr/bin/env python3
# coding: utf-8
#

import subprocess
import logging
import os
import sys
import argparse
import zmq
import time

os.environ["DYLOG_DEFAULT_LEVEL"] = "FATAL"

from google.protobuf import text_format
from a2d_sdk.robot import CosineCamera
from a2d_sdk.robot import RobotDds as Robot

from cosine_bus.agibotdds_py3 import agibotdds

from a2d_sdk.proto.mode_switch_pb2 import ModeSwitchRequest, Mode

robot_service_logger = logging.getLogger("robot_service")
robot_service_logger.setLevel(logging.INFO)
robot_service_logger.addHandler(logging.StreamHandler())

current_dir = os.path.dirname(os.path.abspath(__file__))
camera_receiver_path = os.path.join(current_dir, 'camera/camera_receiver_zmq.py')
camera_bridge_path = os.path.join(current_dir, 'camera/camera_bridge.py')
log_dir = os.path.join(current_dir, "log")

def client(config : object):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://10.42.0.101:8848")

    message = text_format.MessageToString(config)
    socket.send_string(message)

    response = socket.recv_string()
    print(f"Received response: {response}")

def clear_folder(path):
    try:
        if os.path.exists(path):
            for file in os.listdir(path):
                os.remove(os.path.join(path, file))
    except Exception as e:
        robot_service_logger.error(f"Error clearing folder {path}: {e}")

def check_camera_receiver_status(camera_model):
    # check if all camera image are saved in log_dir
    # common = ["head", "back_left_fisheye", "back_right_fisheye", \
    #             "head_center_fisheye", "head_left_fisheye", "head_right_fisheye"]
    # common = ["head"]
    # group_53 = ["hand_left", "hand_right"]
    # group_71 = ["hand_left_fisheye", "hand_right_fisheye"]
    print("Waiting for camera receiver to start...")
    camera_names_71 = ["/camera/head_color", "/camera/head_center_fisheye", "/camera/hand_left_fisheye", "/camera/hand_right_fisheye", "/camera/head_depth"]
    camera_names_53 = ["/camera/head_color", "/camera/hand_left_color", "/camera/hand_right_color","/camera/head_depth"]
    camera_names = camera_names_71 + camera_names_53

    cameras = CosineCamera(camera_names)
    worked_camera = []
    for i in range(30): # 30s timeout
        worked_camera = []
        for camera_name in camera_names:
            if cameras.get_fps(camera_name) > 0:
                worked_camera.append(camera_name)
        else:
            # robot_service_logger.info(f"Waiting for service to start...{i+1}")
            time.sleep(1)

    for camera_name in worked_camera:
        robot_service_logger.info(f"Camera {camera_name}...OK")
    return True, "All cameras started successfully"

def check_robot_status():
    # run ros2 topic echo /sdk/waist_state --once and check if $? is 0
    print("Waiting for robot to start...")
    robot = Robot()
    for i in range(20):
        try:
            result = robot.waist_joint_states()
            if result[0] is not None and result[1] is not None:
                robot_service_logger.info(f"Robot is ready")
                return True, "Robot is ready"
            else:
                # robot_service_logger.info(f"Waiting for robot to start...{i+1}")
                time.sleep(1)
        except Exception as e:
            robot_service_logger.info(f"Waiting for robot to start...{i+1}")
            time.sleep(1)
    error_msg = "Robot hal issue, check errors in http://10.42.0.101:8611/hal_console.txt"
    robot_service_logger.info(error_msg)
    return False, error_msg

def mkdir_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def kill_process(process_keyword):
    try:
        ps_command = f"ps aux | grep {process_keyword}" + " | grep -v grep | awk '{print $2}'"
        result = subprocess.check_output(ps_command, shell=True, text=True)

        pids = result.strip().split()
        if pids:
            robot_service_logger.info(f"Found PIDs: {pids}, killing...")
            kill_command = f"kill -9 {' '.join(pids)}"
            subprocess.run(kill_command, shell=True, check=True)
            robot_service_logger.info(f"{process_keyword} processes killed successfully.")
        else:
            robot_service_logger.info(f"No {process_keyword} processes found.")
        return True
    except subprocess.CalledProcessError as e:
        robot_service_logger.error(f"Error executing command: {e}")
        return False
    except Exception as e:
        robot_service_logger.error(f"Unexpected error: {e}")
        return False


def stop_local_camera_receiver():
    return kill_process("camera_receiver")

def stop_local_camera_bridge():
    return kill_process("camera_bridge")

def control_ros(action):
    """控制Ros启动/停止"""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    ros_script = os.path.join(script_dir, ".", "scripts", "ros_env_wrapper.sh")
    
    try:
        # Start the process in the background
        my_env = os.environ.copy()
        my_env['LD_LIBRARY_PATH'] = ''
        
        # 使用 Popen 并等待进程完成以获取输出
        process = subprocess.Popen(
            ["nohup", "/bin/bash", ros_script, action, "&"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            env=my_env
        )

        # 检查进程forwarder是否存在
        if action == "start":
            time.sleep(2)
            ps_command = f"ps aux | grep forwarder" + " | grep -v grep | awk '{print $2}'"
            result = subprocess.check_output(ps_command, shell=True, text=True)
            if result:
                robot_service_logger.info(f"✅  {action} ros 环境命令已发送")
                return True
            else:
                robot_service_logger.error(f"❌ 执行Ros {action}失败: forwarder进程不存在")
                return False
        else:
            robot_service_logger.info(f"✅  {action} ros 环境命令已发送")
            return True
    except Exception as e:
        robot_service_logger.error(f"❌ 执行Ros {action}失败: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start", action="store_true", help="Start the robot service")
    parser.add_argument("-t", "--stop", action="store_true", help="Stop the robot service")
    parser.add_argument("-c", "--config", type=str, default=f"{current_dir}/conf/hybrid_deploy.pbtxt", help="config_file_path")
    parser.add_argument("--no-ros", action="store_true", help="Do not start/stop ROS environment")
    args = parser.parse_args()

    mkdir_if_not_exists(log_dir)

    time.sleep(10)
    if args.start:
        try:
            clear_folder(log_dir)
            config = ModeSwitchRequest()
            
            with open(args.config, "r") as f:
                text_format.Merge(f.read(), config)
            
            client(config)
            
            if config.mode == Mode.COPILOT:
                robot_status, robot_msg = check_robot_status()
                camera_status, camera_msg = check_camera_receiver_status(config.hybrid_deploy_config.camera_model)
                
                if camera_status and robot_status:
                    print("success")  # 成功标记
                    robot_service_logger.info("Robot service started successfully")
                    if not args.no_ros:
                        control_ros("start")
                    agibotdds.shutdown()
                    sys.exit(0)
                else:
                    error_msg = f"Start failed: Camera: {camera_msg}, Robot: {robot_msg}"
                    robot_service_logger.error(error_msg)
                    print(error_msg)
                    agibotdds.shutdown()
                    sys.exit(1)
            else:
                control_ros("stop")
                print("success")  # 成功标记
                sys.exit(0)
                
        except Exception as e:
            error_msg = f"Error during startup: {str(e)}"
            robot_service_logger.error(error_msg)
            print(error_msg)
            sys.exit(1)
    elif args.stop:
        stop_local_camera_receiver()
    else:
        print("Please use -s to start or -t to stop the robot service")
    agibotdds.shutdown()