import time
import cv2
import numpy as np
from collections import deque
from utils import misc
from a2d_sdk.robot import RobotDds as Robot
from a2d_sdk.robot import CosineCamera as Camera

class RobotA2D():
    def __init__(self):
        self.name_cameras = ['head', 'hand_left', 'hand_right']
        self.camera= Camera(self.name_cameras)
        self.robot = Robot()
        self.obs_buffer = deque(maxlen=10)
        time.sleep(1)

    def get_cameras(self, timestamp=None):
        list_time = []
        for name in self.name_cameras:
            image, time_stamp = self.camera.get_latest_image(name)
            # fps = self.camera.get_fps(name)
            # latency = self.camera.get_latency_stats(name, window_seconds=5.0)
            # print(f"get image time: {time.time() - timeaaa}, {fps}, {latency['max_latency_ms']}")
            # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            # cv2.imshow(name, image)
        body_states = self.robot.body_pose_joint_states()
        arm_states, time_stamp1 = self.robot.arm_joint_states()
        list_time.append(time_stamp1 / 1e9)
        gripper_states, time_stamp2 = self.robot.gripper_states()
        list_time.append(time_stamp2 / 1e9)
        print(max(list_time) - min(list_time), list_time)

    def control_robot(self, data):
        action = data['pred_action']
        obs_state = data['obs_state']
        action = misc.smooth_each_dim_with_spline(np.concatenate([action[0], action[-1]], axis=0), num_smooth_points=50, s=0.05)
        for i, act in enumerate(action):
            self.robot.move_arm(action[i, 0:14].tolist())
            self.robot.move_gripper(action[i, 14:16].tolist())
            time.sleep(0.01)

    def get_obs_nearest(self):
        result = {'list_timestamp': []}
        image, ref_timestamp = self.camera.get_latest_image('head')
        result['ref_timestamp'] = [ref_timestamp / 1e9, time.time()]  # [0] - [1] = -0.06s
        result['obs.cam.head'] = image
        # 无阻塞，image每个5ms左右，因此需要判断舍弃
        if len(self.obs_buffer) > 0:
            latest_obs = self.obs_buffer[-1]
            if latest_obs['ref_timestamp'][0] == ref_timestamp / 1e9:
                return None

        result['list_timestamp'].append(ref_timestamp / 1e9)
        image, timestamp = self.camera.get_image_nearest('hand_left', ref_timestamp)
        result['obs.cam.hand_left'] = image
        result['list_timestamp'].append(timestamp / 1e9)
        image, timestamp= self.camera.get_image_nearest('hand_right', ref_timestamp)
        result['obs.cam.hand_right'] = image
        result['list_timestamp'].append(timestamp / 1e9)

        arm_states, time_stamp = self.robot.arm_joint_states_nearest(ref_timestamp)
        result['obs.state.arm'] = arm_states
        result['list_timestamp'].append(time_stamp / 1e9)
        gripper_states, timestamp = self.robot.gripper_joint_states_nearest(ref_timestamp)
        result['obs.state.gripper'] = gripper_states
        result['list_timestamp'].append(timestamp / 1e9)
        head_states, time_stamp = self.robot.head_joint_states_nearest(ref_timestamp)
        result['obs.state.head'] = head_states
        result['list_timestamp'].append(time_stamp / 1e9)
        waist_states, time_stamp = self.robot.waist_joint_states_nearest(ref_timestamp)
        result['obs.state.waist'] = waist_states
        result['list_timestamp'].append(time_stamp / 1e9)
        result['obs.state'] = np.array(arm_states + gripper_states + head_states + waist_states)
        self.obs_buffer.append(result)
        # print('aaaaaaaaaaaaaaaaa', max(result['list_timestamp']) - min(result['list_timestamp']), result['list_timestamp'], result['ref_timestamp'], '\n')
        # cv2.imshow('head', result['obs.cam.head'])
        # cv2.imshow('hand_left', result['obs.cam.hand_left'])
        # cv2.imshow('hand_right', result['obs.cam.hand_right'])
        # cv2.waitKey(1)
        return result

    def get_obs_buffer(self):
        return self.obs_buffer

    def close(self):
        self.camera.close()
        self.robot.shutdown()

if __name__ == '__main__':
    robot = RobotA2D()
    try:
        while True:
            robot.get_obs_nearest()
            time.sleep(0.1)  # 控制循环频率
    except KeyboardInterrupt:
        robot.close()
