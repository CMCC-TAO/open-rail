import time
import cv2
import numpy as np
# from collections import deque
from ml_collections import ConfigDict
# from utils import misc
from a2d_sdk.robot import RobotDds as Robot
from a2d_sdk.robot import CosineCamera as Camera
from ..base_robot import RobotBase

class RobotA2D(RobotBase):
    def __init__(self, observer_config: ConfigDict, controller_config: ConfigDict):
        super().__init__()
        # self.name_cameras = ['head', 'hand_left', 'hand_right']
        self.observer_config = observer_config
        self.controller_config = controller_config
        # self.name_cameras = ['head', 'hand_left', 'hand_right']
        self.camera= Camera(observer_config.camera_names)
        self.robot = Robot()
        self.currt_timestamp = 0
        self.gripper_count = 0
        self.gripper_cmd = [0.0, 0.0]
        # self.obs_buffer = deque(maxlen=10)
        time.sleep(1)

    # def get_cameras(self, timestamp=None):
    #     list_time = []
    #     for name in self.name_cameras:
    #         image, time_stamp = self.camera.get_latest_image(name)
    #         # fps = self.camera.get_fps(name)
    #         # latency = self.camera.get_latency_stats(name, window_seconds=5.0)
    #         # print(f"get image time: {time.time() - timeaaa}, {fps}, {latency['max_latency_ms']}")
    #         # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    #         # cv2.imshow(name, image)
    #     body_states = self.robot.body_pose_joint_states()
    #     arm_states, time_stamp1 = self.robot.arm_joint_states()
    #     list_time.append(time_stamp1 / 1e9)
    #     gripper_states, time_stamp2 = self.robot.gripper_states()
    #     list_time.append(time_stamp2 / 1e9)
    #     print(max(list_time) - min(list_time), list_time)

    def controlRobot(self, action):
        self.robot.move_arm(action[0:14].tolist())
        # gripper_cmd = np.clip(action[14:16], 0.0, 1.0)
        # self.robot.move_gripper(gripper_cmd.tolist())
        # print(f'gripper_states: {gripper_cmd.tolist()}')
        # 统计gripper值的变化，当变化积累到一定次数后，发送一次gripper命令
        new_gripper_cmd = action[14:16]
        if abs(new_gripper_cmd[0] - self.gripper_cmd[0]) > 0.75 or abs(new_gripper_cmd[1] - self.gripper_cmd[1]) > 0.75:
            self.gripper_count += 1
        if self.gripper_count > 40:
            self.robot.move_gripper(new_gripper_cmd.tolist())
            print(f'gripper_states: {new_gripper_cmd.tolist()}')
            self.gripper_cmd = new_gripper_cmd
            self.gripper_count = 0
        else:
            pass
            # print(f'gripper_cout: {self.gripper_count}')
        # action = data['pred_action']
        # obs_state = data['obs_state']
        # # action = misc.smooth_each_dim_with_spline(np.concatenate([action[0], action[-1]], axis=0), num_smooth_points=50, s=0.05)
        # for i, act in enumerate(action):
        #     self.robot.move_arm(action[i, 0:14].tolist())
        #     self.robot.move_gripper(action[i, 14:16].tolist())
        #     time.sleep(0.01)
    def controlGripper(self, gripper_cmd):
        self.robot.move_gripper(gripper_cmd)
        print(f'gripper_states: {gripper_cmd}')

    def retrieveObservation(self):
        result = {}
        # head camera is required
        if 'head' not in self.observer_config.camera_names:
            print(f'head camera is required: {self.observer_config.camera_names}')
            return None
        
        image, ref_timestamp = self.camera.get_latest_image('head')
        if self.currt_timestamp == ref_timestamp:
            return None
        else:
            self.currt_timestamp = ref_timestamp

        # fps = self.camera.get_fps('head')
        # print(f'ref_timestamp: {ref_timestamp}, fps: {fps}')
        # print(ref_timestamp)
        result['ref_timestamp'] = ref_timestamp
        result['cam.head'] = image

        for camera in self.observer_config.camera_names:
            if camera != 'head':
                image, timestamp = self.camera.get_image_nearest(camera, ref_timestamp)
                # TODO: check time offset between the current camera and head camera using abs(timestamp - ref_timestamp)
                # TODO: 相机名称映射
                result[f'cam.{camera}'] = image

        joint_states = []
        for proprio in self.observer_config.proprio_names:
            joint_states_nearest_fun = getattr(self.robot, f'{proprio}_joint_states_nearest')
            currt_joint_states, time_stamp = joint_states_nearest_fun(ref_timestamp)
            joint_states.extend(currt_joint_states)
        result[f'obs.state'] = np.array(joint_states)
        # print(result[f'obs.state'])
        # # self.obs_buffer.append(result)
        # # print('aaaaaaaaaaaaaaaaa', max(result['list_timestamp']) - min(result['list_timestamp']), result['list_timestamp'], result['ref_timestamp'], '\n')
        # cv2.imshow('head', result['obs.cam.head'])
        # # cv2.imshow('hand_left', result['obs.cam.hand_left'])
        # # cv2.imshow('hand_right', result['obs.cam.hand_right'])
        # cv2.waitKey(1)
        return result

    # def get_obs_buffer(self):
    #     return self.obs_buffer

    def get_obs_only_state(self):
        # 这里的arm_states等为protobuf格式，需要转为list
        arm_states, timestamp = self.robot.arm_joint_states()
        gripper_states, timestamp = self.robot.gripper_states()
        vmin, vmax = 35, 120
        gripper_states = (np.array(list(gripper_states)) - vmin) / (vmax - vmin) # norm
        # gripper_states = np.array(list(gripper_states)) * (vmax - vmin) + vmin # re-norm
        return np.array(list(arm_states) + list(gripper_states))

    def close(self):
        self.camera.close()
        self.robot.shutdown()
        print('close robot')

if __name__ == '__main__':
    import sys
    import os
    import random
    # 获取当前文件的绝对路径
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(current_dir)
    # 将当前目录添加到 sys.path
    sys.path.append(current_dir)
    from conf.client_conf import get_client_config
    config = get_client_config()
    robot = RobotA2D(config.observer, config.controller)
    try:
        while True:
            # if (random.random() < 0.5)
            # for index in range(20):
            #     robot.controlGripper([0.9, 0.9])
            #     time.sleep(0.005)
            # for index in range(2):
            #     robot.controlGripper([0.0, 0.0])
            #     time.sleep(0.005)
            char = input("Press 'q' to quit: ") 
            if char == 'q':
                break
            elif char == 'open':
                robot.controlGripper([0.0, 0.0])
            elif char == 'close':
                robot.controlGripper([0.9, 0.9])
            else:
                print(f'unknown command: {char}')

        # robot = RobotA2D(config.observer, config.controller)
        # # robot.get_cameras()
        # while True:
            
            # result = robot.retrieveObservation()
            # if result is not None:
            #     print(result.keys())
            #     print(f'ref_timestamp: {result["ref_timestamp"]}, obs.state: {result["obs.state"]}')
            # time.sleep(0.001)  # 控制循环频率
    except KeyboardInterrupt:
        robot.close()