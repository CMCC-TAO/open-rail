import time
import cv2
import logging
import numpy as np
import pandas as pd
from a2d_sdk.robot import RobotDds as Robot
from a2d_sdk.robot import CosineCamera as Camera
from ..base_robot import RobotBase
# from copy import copy


class RobotBody(RobotBase):
    def __init__(self, config):
        """Initialize the A2D robot body with camera and robot instances.
        
        Args:
            config (dict): Configuration dictionary containing robot and camera settings
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__) # required for correct logging output
        self.camera= Camera(list(self.config['camera']['names'].values()))
        self.robot = Robot()
        self.current_state = np.zeros(self.action_dim)
        self.current_timestamp = 0
        self.gripper_count = 0
        self.gripper_cmd = [0.0, 0.0]
        self.head_count = 0
        time.sleep(1)

    def control_robot(self, action):
        """Control the robot arm, gripper, and head based on the given action.
        
        Args:
            action (array-like): Action array containing arm commands (0:14), gripper commands (14:16), and head commands (16:18)
        """
        action = np.asarray(action)
        segments = {
            name: action[v['start']:v['end']]
            for name, v in self.action_layout.items()
            if v['end'] <= action.size
        }
        if 'arm' in segments:
            self.execute_action({'arm': segments['arm'].tolist()})

        if 'gripper' in segments and self.gripper_count % self.config['gripper_freq'] == 0:
            self.gripper_count = 0
            arr = np.clip(segments['gripper'], 0, 1)
            gripper_optimized = True
            if gripper_optimized:
                gamma = 4
                # adjusted = arr * gamma / (arr * gamma + (1 - arr) ** gamma)
                adjusted = arr ** gamma / (arr ** gamma + (1 - arr) ** gamma)
                arr = np.clip(adjusted, 0, 1)
            self.execute_action({self.config['hand_type']: arr.tolist()})
        self.gripper_count += 1

        if 'head' in segments:
            if self.head_count % self.config.get('head_freq', 40) == 0:
                self.head_count = 0
                head_action = segments['head']
                self.execute_action({'head': head_action.tolist()})
            self.head_count += 1
        if 'waist' in segments:
            self.execute_action({'waist': segments['waist'].tolist()})

        # Count gripper value changes and send gripper command when accumulated changes reach threshold
        # new_gripper_cmd = action[14:16]
        # if abs(new_gripper_cmd[0] - self.gripper_cmd[0]) > 0.75 or abs(new_gripper_cmd[1] - self.gripper_cmd[1]) > 0.75:
        #     self.gripper_count += 1
        # if self.gripper_count > self.config['gripper_freq']:
        #     self.execute_action({self.config['hand_type']: new_gripper_cmd.tolist()})
        #     self.gripper_cmd = new_gripper_cmd
        #     self.gripper_count = 0
    
    def execute_action(self, data):
        """Execute action interface without strategy.
        
        Args:
            data (dict): Dictionary containing arm and gripper commands
        """
        if 'arm' in data:
            self.robot.move_arm(data['arm'])
        if 'gripper' in data:
            self.robot.move_gripper(data['gripper'])
        if 'hand_as_gripper' in data:
            self.robot.move_hand_as_gripper(data['hand_as_gripper'])
        if 'head' in data:
            self.robot.move_head(data['head'])
        if 'waist' in data:
            self.robot.move_waist(data['waist'])
        if 'body' in data:
            self.robot.move_wbc_waist(data['body'])
        if 'wheel' in data:
            self.robot.move_wheel(data['wheel'][0], data['wheel'][1])
        if 'hand' in data:
            self.robot.move_hand(data['hand'])
    
    def retrieve_observation(self):
        """Retrieve current observation data including camera images and joint states.
        
        Returns:
            dict or None: Dictionary containing camera images, joint states, and timestamp. Returns None if no new data is available.
        """
        try:
            result = {}
            cam_names, cam_ref = self.config['camera']['names'], self.config['camera']['ref']
            image, ref_timestamp = self.camera.get_latest_image(cam_names[cam_ref])
            if self.current_timestamp == ref_timestamp:
                return None
            else:
                self.logger.debug(f'Retrieve image time: {(ref_timestamp-self.current_timestamp)/1e6: .3f}ms')
                self.current_timestamp = ref_timestamp

            result['ref_timestamp'] = ref_timestamp
            result[f'cam.{cam_ref}'] = image[:, :, ::-1].copy() # RGB -> BGR, cam_ref = head
            # print(f"Debug:cam.cam_ref={cam_ref}")
            for key, value in cam_names.items():
                if key == cam_ref:
                    continue
                image, timestamp = self.camera.get_image_nearest(value, ref_timestamp)
                # if key == 'depth_head':
                #     key = 'depth.head'
                result[f'cam.{key}'] = image[:, :, ::-1].copy() # BGR -> RGB, key=hand_left/hand_right
                # print(f"Debug:cam.{key}={key}")

            joint_states, gripper_start = [], 0
            for proprio in self.config['proprio_names']:
                joint_states_nearest_fun = getattr(self.robot, f'{proprio}_joint_states_nearest')
                currt_joint_states, timestamp = joint_states_nearest_fun(ref_timestamp)
                if proprio == 'gripper':
                    gripper_start = len(joint_states)
                joint_states.extend(currt_joint_states)
            result['obs.state'] = np.array(joint_states)
            if self.current_state.size < result['obs.state'].size:
                self.current_state = np.zeros(result['obs.state'].size)
            self.current_state[:result['obs.state'].size] = result['obs.state'].copy()
            vmin, vmax = 35, 120
            self.current_state[gripper_start:gripper_start + 2] = (self.current_state[gripper_start:gripper_start + 2] - vmin) / (vmax - vmin) # norm
            # currt_joint_states = np.array(list(currt_joint_states)) * (vmax - vmin) + vmin # re-norm
            return result
        except Exception as e:
            print(e)
            return None

    def close(self):
        """Close and shutdown the robot and camera connections.
        
        This method properly releases all hardware resources.
        """
        self.camera.close()
        self.robot.shutdown()
        print('close robot')

    def load_action_data(self, parquet_path, key="action"):
        """ read specific data from parquet file

        Args:
            parquet_path: the parquet file path 
            key: key of data, for example, action, observation.state
        """
        # read parquet file
        df = pd.read_parquet(parquet_path)
        data = df[key].tolist()
        # process data of dexterous hand to gripper format
        processed_data = []
        for idx, ele in enumerate(data):
            if 'hand' in self.config['hand_type']:
                data_temp = np.zeros(20)
                data_temp[:14] = ele[:14]
                left_hand = ele[15:19].mean()
                if left_hand > 0.1:
                    left_hand = 1.0
                right_hand = ele[20:23].mean()
                if right_hand < 0.1:
                    right_hand = 0
                data_temp[14] = left_hand
                data_temp[15] = right_hand
                processed_data.append(data_temp)
            else:
                processed_data.append(ele)
        return processed_data

    def default_replay_trajectories(self, parquet_path, accelerate:bool=True, accelerate_times: int=2):
        trajs = self.load_action_data(parquet_path=parquet_path)
        if not accelerate:
            accelerate_times = 1
        for idx, traj in enumerate(trajs):
            if idx % accelerate_times == 0:
                self.execute_action({'arm': traj[0:14].tolist()})
                self.execute_action({self.config['hand_type']: traj[14:16].tolist()})
                time.sleep(0.05)

    def replay_trajectories(self, parquet_path, use_default: bool=True, accelerate:bool=True, accelerate_times: int=2, exclude_path=['place'], progress_fn=None):
        """replay trajectory based on teleoperation data"""
        try:
            if 'hand' in self.config['hand_type']:
                use_default = False

            if use_default:
                self.default_replay_trajectories(parquet_path=parquet_path, accelerate=accelerate, accelerate_times=accelerate_times)
            else:
                trajs = self.load_action_data(parquet_path=parquet_path)
                for ele in exclude_path:
                    if ele in parquet_path:
                        accelerate = False
                for idx, traj in enumerate(trajs):
                    if progress_fn is not None:
                        progress_fn(idx, len(trajs), traj)

                    if accelerate:
                        if idx % accelerate_times == 0:
                            self.execute_action({'arm': traj[0:14].tolist()})
                            if 'place_fruit' in parquet_path and idx < len(trajs)-30 and idx > 200:
                                traj[14] = 1.0
                                traj[15] = 0.0
                            self.execute_action({self.config['hand_type']: traj[14:16].tolist()})
                            time.sleep(0.05)
                    else:
                        self.execute_action({'arm': traj[0:14].tolist()})
                        if 'place_fruit' in parquet_path and idx < len(trajs)-30 and idx > 200:
                            traj[14] = 1.0
                            traj[15] = 0.0
                        self.execute_action({self.config['hand_type']: traj[14:16].tolist()})
                        time.sleep(0.05)
        except Exception as e:
            print(f"Replay {parquet_path} failed, error: {e}")

if __name__ == '__main__':
    from conf.robots_conf import get_robots_config
    config = get_robots_config()
    robot = RobotBody(config)
    try:
        while True:
            result = robot.retrieve_observation()
            if result is None:
                continue
            for key, value in result.items():
                if 'cam.' not in key:
                    continue
                if 'depth.' in key:
                    img_depth_norm = cv2.normalize(value, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                    img_show = cv2.applyColorMap(img_depth_norm, cv2.COLORMAP_JET)
                else:
                    img_show = cv2.cvtColor(value, cv2.COLOR_RGB2BGR)
                cv2.imshow(key, img_show)
                cv2.waitKey(1)
    except KeyboardInterrupt:
        robot.close()
