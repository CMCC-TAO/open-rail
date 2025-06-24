import time
import torch
import random
import lerobot
import numpy as np
# from collections import deque
from pprint import pprint
from ml_collections import ConfigDict
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset, LeRobotDatasetMetadata
# from utils import misc

class RobotA2DMock():
    def __init__(self, observer_config: ConfigDict, controller_config: ConfigDict, repo_id: str = None, root: str = None):
        # self.name_cameras = ['head', 'hand_left', 'hand_right']
        self.observer_config = observer_config
        self.controller_config = controller_config
        self.dataset = LeRobotDataset(repo_id=repo_id if repo_id is not None else 'task_39_only1',
                                root=root if root is not None else '/home/robot/Music/task_39_only1',
                                local_files_only=True)
        self.dataloader = iter(torch.utils.data.DataLoader(
            self.dataset,
            num_workers=1,
            batch_size=1,
            shuffle=False,
        ))
        # And see how many frames you have:
        print(f"Selected episodes: {self.dataset.episodes}")
        print(f"Number of episodes selected: {self.dataset.num_episodes}")
        print(f"Number of frames selected: {self.dataset.num_frames}")
        print(f"Dataset fps: {self.dataset.meta.fps}")
        # self.name_cameras = ['head', 'hand_left', 'hand_right']
        self.init_timestamp = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        self.currt_index = 0
        self.period = 1.0 / self.dataset.meta.fps # in seconds
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
        if random.random() < 0.001:
            print(f'Mock control robot...')
        # self.robot.move_arm(action[0:14].tolist())
        # self.robot.move_gripper(action[14:16].tolist())
        # action = data['pred_action']
        # obs_state = data['obs_state']
        # # action = misc.smooth_each_dim_with_spline(np.concatenate([action[0], action[-1]], axis=0), num_smooth_points=50, s=0.05)
        # for i, act in enumerate(action):
        #     self.robot.move_arm(action[i, 0:14].tolist())
        #     self.robot.move_gripper(action[i, 14:16].tolist())
        #     time.sleep(0.01)

    def retrieveObservation(self):
        start_time = time.time()
        result = {}
        if self.currt_index >= self.dataset.num_frames:
            print(f'End of dataset, currt_index: {self.currt_index}, num_frames: {self.dataset.num_frames}')
            self.dataloader = iter(torch.utils.data.DataLoader(
                self.dataset,
                num_workers=1,
                batch_size=1,
                shuffle=False,
            ))
            self.currt_index = 0
            # self.currt_index = self.dataset.num_frames - 1
            # return None
        # data = self.dataset[self.currt_index]
        self.currt_index += 1
        data = next(self.dataloader)
        # print(batch['observation.state'])
        # data_keys(['observation.images.top_head', 'observation.images.hand_left', 'observation.images.hand_right', 'observation.state', 'action', 'episode_index', 'frame_index', 'index', 'task_index', 'timestamp'])
        # print(data.keys())
        # print(data['observation.images.top_head'].permute(1, 2, 0).shape)
        # print(data["observation.state"].cpu().numpy())
        # print(data["timestamp"].cpu().numpy())
        # head camera is required
        if 'head' not in self.observer_config.camera_names:
            print(f'head camera is required: {self.observer_config.camera_names}')
            return None
        
        image, ref_timestamp = (data['observation.images.top_head'][0].permute(1, 2, 0).cpu().numpy()* 255).astype(np.uint8), time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        # print(image.dtype)

        # fps = self.camera.get_fps('head')
        # print(f'ref_timestamp: {ref_timestamp}, fps: {fps}')
        # print(ref_timestamp)
        result['ref_timestamp'] = ref_timestamp
        # print(f'ref_timestamp: {ref_timestamp}, state: {data["observation.state"].cpu().numpy()[0][:5]}')
        result['obs.cam.head'] = image

        for camera in self.observer_config.camera_names:
            if camera != 'head':
                image = (data[f'observation.images.{camera}'][0].permute(1, 2, 0).cpu().numpy()* 255).astype(np.uint8)
                # TODO: check time offset between the current camera and head camera using abs(timestamp - ref_timestamp)
                result[f'obs.cam.{camera}'] = image

        # joint_states = []
        # for proprio in self.observer_config.proprio_names:
        #     joint_states_nearest_fun = getattr(self.robot, f'{proprio}_joint_states_nearest')
        #     currt_joint_states, time_stamp = joint_states_nearest_fun(ref_timestamp)
        #     joint_states.extend(currt_joint_states)
        result[f'obs.state'] = data["observation.state"][0].cpu().numpy()
        # print(result[f'obs.state'].shape)
        # print(result[f'obs.state'])
        # # self.obs_buffer.append(result)
        # # print('aaaaaaaaaaaaaaaaa', max(result['list_timestamp']) - min(result['list_timestamp']), result['list_timestamp'], result['ref_timestamp'], '\n')
        # cv2.imshow('head', result['obs.cam.head'])
        # # cv2.imshow('hand_left', result['obs.cam.hand_left'])
        # # cv2.imshow('hand_right', result['obs.cam.hand_right'])
        # cv2.waitKey(1)
        end_time = time.time()
        # print(f'get obs time: {(end_time - start_time)*1000} ms, end_time: {end_time}')
        if end_time-start_time < self.period:
            sleep_time = self.period - (end_time - start_time)
            # print(f'sleep time: {sleep_time}')
            time.sleep(sleep_time)
        end_time = time.time()
        # print(f'get obs time: {(end_time - start_time)*1000} ms, end_time: {end_time}')
        return result

    # def get_obs_buffer(self):
    #     return self.obs_buffer

    def close(self):
        print('Close mock robot...')
        # self.camera.close()
        # self.robot.shutdown()

if __name__ == '__main__':
    import sys
    sys.path.append('/home/robot/Gits/jupyter/vla_infer')
    from conf.config import get_client_config
    config = get_client_config()
    repo_id = 'task_39_only1'
    root = '/home/robot/Music/task_39_only1'
    robot = RobotA2DMock(config.observer, config.controller, repo_id, root)
    try:
        while True:
            result = robot.retrieveObservation()
            # print(result.keys())
            time.sleep(0.1)  # 控制循环频率
    except KeyboardInterrupt:
        robot.close()

# import matplotlib.pyplot as plt

# # 创建一个新的figure
# plt.figure(figsize=(10, 4))

# # 添加一个新的子图到figure中
# plt.subplot(1, 3, 1)
# # 显示图像
# plt.imshow(data["observation.images.top_head"].permute(1, 2, 0).cpu().numpy())
# plt.axis('off')  # 关闭坐标轴
# plt.subplot(1, 3, 2)
# # 显示图像
# plt.imshow(data["observation.images.hand_left"].permute(1, 2, 0).cpu().numpy())
# plt.axis('off')  # 关闭坐标轴
# plt.subplot(1, 3, 3)
# # 显示图像
# plt.imshow(data["observation.images.hand_right"].permute(1, 2, 0).cpu().numpy())
# plt.axis('off')  # 关闭坐标轴
# plt.tight_layout()

# # 显示所有图像
# # plt.show()
# plt.savefig('test.png')
# plt.show()
# input("Press enter to continue...")