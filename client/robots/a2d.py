import time
import cv2
import numpy as np
# from collections import deque
from ml_collections import ConfigDict
# from utils import misc
from a2d_sdk.robot import RobotDds as Robot
from a2d_sdk.robot import CosineCamera as Camera
from .base import RobotBase

class RobotA2D(RobotBase):
    def __init__(self, observer_config: ConfigDict, controller_config: ConfigDict):
        super().__init__(observer_config, controller_config)
        # self.name_cameras = ['head', 'hand_left', 'hand_right']
        # self.name_cameras = ['head', 'hand_left', 'hand_right']
        self.camera= Camera(observer_config.camera_names)
        self.robot = Robot()

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

    def control_robot(self, data):
        print(data)
        # action = data['pred_action']
        # obs_state = data['obs_state']
        # # action = misc.smooth_each_dim_with_spline(np.concatenate([action[0], action[-1]], axis=0), num_smooth_points=50, s=0.05)
        # for i, act in enumerate(action):
        #     self.robot.move_arm(action[i, 0:14].tolist())
        #     self.robot.move_gripper(action[i, 14:16].tolist())
        #     time.sleep(0.01)

    def retrieve_observation(self):
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
        result['obs.cam.head'] = image

        for camera in self.observer_config.camera_names:
            if camera != 'head':
                image, timestamp = self.camera.get_image_nearest(camera, ref_timestamp)
                # TODO: check time offset between the current camera and head camera using abs(timestamp - ref_timestamp)
                result[f'obs.cam.{camera}'] = image

        joint_states = []
        for proprio in self.observer_config.proprio_names:
            joint_states_nearest_fun = getattr(self.robot, f'{proprio}_joint_states_nearest')
            currt_joint_states, time_stamp = joint_states_nearest_fun(ref_timestamp)
            joint_states.extend(currt_joint_states)
        result[f'obs.state'] = np.array(joint_states)
        # # self.obs_buffer.append(result)
        # # print('aaaaaaaaaaaaaaaaa', max(result['list_timestamp']) - min(result['list_timestamp']), result['list_timestamp'], result['ref_timestamp'], '\n')
        # cv2.imshow('head', result['obs.cam.head'])
        # # cv2.imshow('hand_left', result['obs.cam.hand_left'])
        # # cv2.imshow('hand_right', result['obs.cam.hand_right'])
        # cv2.waitKey(1)
        return result

    # def get_obs_buffer(self):
    #     return self.obs_buffer

    def close(self):
        self.camera.close()
        self.robot.shutdown()

if __name__ == '__main__':
    robot = RobotA2D()
    try:
        while True:
            robot.get_obs_nearest()
            time.sleep(0.001)  # 控制循环频率
    except KeyboardInterrupt:
        robot.close()
