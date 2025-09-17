import time
import cv2
import numpy as np
import ruckig
import pandas as pd

class RobotBase():
    def __init__(self):
        self.robot = None
        self.current_state = np.zeros(20)

    def control_robot(self, data):
        """
        The default robot control is the same as execute_action. You can implement it with a fine-grained strategy.
        Args:
            data: data to control robot
        """
        self.execute_action(data)

    def execute_action(self, data):
        """
        Execute action interface without strategy
        Args:
            data: must be dict, execute arm/gripper/head/waist/wheel. e.g.:
            {'arm': [0, 0, 0, 0, 0, 0], 'gripper': [0, 0], 'head': [0, 0], 'waist': [0, 0], 'wheel': [0, 0]}
        """
        raise NotImplementedError('execute_action is not implemented')

    def retrieve_observation(self):
        """
        Get current observation from robot
        Returns:
            obs: current robot observation, obs['state'] is current pose
        """
        raise NotImplementedError('retrieve_observation is not implemented')

    def reset_robot(self, target_pose=None, mode='default'):
        """
        Reset robot to specified pose
        Args:
            target_pose: target pose, format: [7 left arm + 7 right arm + 2 gripper + 2 head + 2 waist + 2 wheels]
        """
        if target_pose is None:
            print('[WARN] target_pose is None, can NOT execute reset_robot')
            return
        if isinstance(target_pose, list):
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
        trajs = self._ruckig_planning(current_positions, target_positions)
        for i, traj in enumerate(trajs):
            # print(f"Executing trajectory point {i}: {traj}")
            print(f'\r{i}', end='')
            self.execute_action({'arm': traj})
            time.sleep(0.01)

        if 'gripper' in self.cfg['hand_type']:
            self.execute_action({'gripper': target_pose[14:16].tolist()})
            self.execute_action({'head': target_pose[16:18].tolist()})
            self.execute_action({'waist': target_pose[18:20].tolist()})
        elif self.cfg['hand_type'] == 'hand':
            self.execute_action({'hand': target_pose[14:26].tolist()})
            self.execute_action({'head': target_pose[26:28].tolist()})
            self.execute_action({'waist': target_pose[28:30].tolist()})
    
    def _ruckig_planning(self, current_pose, target_pose, dof=14, interval=0.01):
        """
        Trajectory planning using Ruckig
        Args:
            current_pose: current joint pose
            target_pose: target joint pose
            dof: degrees of freedom
            interval: time interval
        Returns:
            list of trajectory points
        """
        rk = ruckig.Ruckig(dof, interval)
        rk_input = ruckig.InputParameter(dof)
        rk_output = ruckig.OutputParameter(dof)
        
        # Set current state
        rk_input.current_position = current_pose
        rk_input.current_velocity = [0.0] * dof
        rk_input.current_acceleration = [0.0] * dof
        
        # Set target state
        rk_input.target_position = target_pose
        rk_input.target_velocity = [0.0] * dof
        rk_input.target_acceleration = [0.0] * dof
        
        # Set motion constraints
        rk_input.max_velocity = [2.0] * dof
        rk_input.max_acceleration = [1.0] * dof
        rk_input.max_jerk = [5.0] * dof
        
        # Generate trajectory
        trajs = []
        while rk.update(rk_input, rk_output) == ruckig.Result.Working:
            trajs.append(rk_output.new_position)
            rk_output.pass_to_input(rk_input)
        
        return trajs

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
        return processed_data

    def replay_trajectories(self, parquet_path):
        try:
            trajs = self.load_action_data(parquet_path=parquet_path)
            for idx, traj in enumerate(trajs):
                self.execute_action({'arm': traj[0:14].tolist()})
                if 'place_fruit' in parquet_path and idx < len(trajs)-30 and idx > 200:
                    traj[14] = 1.0
                    traj[15] = 1.0
                self.execute_action({'hand': traj[14:16].tolist()})
                time.sleep(0.05)
        except Exception as e:
            print(f"Replay {parquet_path} failed, error: {e}")

    def close(self):
        pass
