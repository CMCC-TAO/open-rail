import time
import cv2
import numpy as np
import pandas as pd
from a2d_sdk.robot import RobotDds as Robot
from a2d_sdk.robot import CosineCamera as Camera
from ..base_robot import RobotBase

class RobotBody(RobotBase):
    def __init__(self, config):
        """Initialize the A2D robot body with camera and robot instances.
        
        Args:
            config (dict): Configuration dictionary containing robot and camera settings
        """
        super().__init__()
        self.cfg, self.ori_cfg = config['robots']['a2d'], config
        self.camera= Camera(list(self.cfg['camera']['names'].values()))
        self.robot = Robot()
        self.current_state = np.zeros(20)
        self.current_timestamp = 0
        self.gripper_count = 0
        self.gripper_cmd = [0.0, 0.0]
        time.sleep(1)

    def control_robot(self, action):
        """Control the robot arm and gripper based on the given action.
        
        Args:
            action (array-like): Action array containing arm commands (0:14) and gripper commands (14:16)
        """
        self.execute_action({'arm': action[0:14].tolist()})
        # Count gripper value changes and send gripper command when accumulated changes reach threshold
        new_gripper_cmd = action[14:16]
        if abs(new_gripper_cmd[0] - self.gripper_cmd[0]) > 0.75 or abs(new_gripper_cmd[1] - self.gripper_cmd[1]) > 0.75:
            self.gripper_count += 1
        if self.gripper_count > self.cfg['gripper_freq']:
            self.execute_action({self.cfg['hand_type']: new_gripper_cmd.tolist()})
            self.gripper_cmd = new_gripper_cmd
            self.gripper_count = 0
    
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
        if 'wheel' in data:
            self.robot.move_wheel(data['wheel'][0], data['wheel'][1])
        if 'hand' in data:
            self.robot.move_hand(data['hand'])
    
    def reset_robot(self, target_pose=None, mode='default'):
        """Reset the robot to its default position.
        """
        if target_pose is None:
            if mode == 'default':
                target_pose = np.array(self.cfg['reset_robot_pos'])
            elif mode == 'zero':
                target_pose = np.array([0] * 14 + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0])
            else:
                print('[WARN] target_pose is None, can NOT execute reset_robot')
                return
        else:
            target_pose = np.array(target_pose)
        
        current_obs = self.retrieve_observation()
        current_positions = current_obs['obs.state'][:14]
        target_positions = target_pose[:14]
        # Calculate joint position differences
        dis = np.abs(current_positions - target_positions)
        mask = dis > np.deg2rad(0.01)  # Decide whether to use interpolation strategy
        # If difference is small, move directly to target position
        if not np.any(mask):
            self.execute_action({'arm': target_positions.tolist()})
            time.sleep(0.01)
            return
        # Otherwise plan trajectory
        trajs = self.ruckig_planning(current_positions, target_positions)
        for i, traj in enumerate(trajs):
            # print(f"Executing trajectory point {i}: {traj}")
            print(f'\r{i}', end='')
            self.execute_action({'arm': traj})
            time.sleep(0.01)

        if 'gripper' in self.cfg['hand_type']:
            self.execute_action({self.cfg['hand_type']: target_pose[14:16].tolist()})
            self.execute_action({'head': target_pose[16:18].tolist()})
            self.execute_action({'waist': target_pose[18:20].tolist()})
        elif self.cfg['hand_type'] == 'hand':
            self.execute_action({'hand': target_pose[14:26].tolist()})
            self.execute_action({'head': target_pose[26:28].tolist()})
            self.execute_action({'waist': target_pose[28:30].tolist()})

    def retrieve_observation(self):
        """Retrieve current observation data including camera images and joint states.
        
        Returns:
            dict or None: Dictionary containing camera images, joint states, and timestamp.
                         Returns None if no new data is available.
        """
        try:
            result = {}
            cam_names, cam_ref = self.cfg['camera']['names'], self.cfg['camera']['ref']
            image, ref_timestamp = self.camera.get_latest_image(cam_names[cam_ref])
            if self.current_timestamp == ref_timestamp:
                return None
            else:
                self.current_timestamp = ref_timestamp

            result['ref_timestamp'] = ref_timestamp
            result[f'cam.{cam_ref}'] = image
            for key, value in cam_names.items():
                if key == cam_ref:
                    continue
                image, timestamp = self.camera.get_image_nearest(value, ref_timestamp)
                if key == 'depth_head':
                    key = 'depth.head'
                result[f'cam.{key}'] = image

            joint_states = []
            for proprio in self.cfg['proprio_names']:
                joint_states_nearest_fun = getattr(self.robot, f'{proprio}_joint_states_nearest')
                currt_joint_states, timestamp = joint_states_nearest_fun(ref_timestamp)
                joint_states.extend(currt_joint_states)
            result['obs.state'] = np.array(joint_states)
            self.current_state = result['obs.state']
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
            if 'hand' in self.hand_type:
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

    def replay_trajectories(self, parquet_path):
        try:
            trajs = self.load_action_data(parquet_path=parquet_path)
            accelerate = True
            if "place" in parquet_path:
                accelerate = False
            for idx, traj in enumerate(trajs):
                if accelerate:
                    if idx % 2 == 0:
                        self.execute_action({'arm': traj[0:14].tolist()})
                        if 'place_fruit' in parquet_path and idx < len(trajs)-30 and idx > 200:
                            traj[14] = 1.0
                            traj[15] = 0.0
                        self.execute_action({self.cfg['hand_type']: traj[14:16].tolist()})
                        time.sleep(0.05)
                else:
                    self.execute_action({'arm': traj[0:14].tolist()})
                    if 'place_fruit' in parquet_path and idx < len(trajs)-30 and idx > 200:
                        traj[14] = 1.0
                        traj[15] = 0.0
                    self.execute_action({self.cfg['hand_type']: traj[14:16].tolist()})
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