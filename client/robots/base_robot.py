import time
import cv2
import numpy as np
import ruckig

class RobotBase():
    def __init__(self):
        self.robot = None

    def control_robot(self, action):
        """
        Control robot to execute action
        Args:
            action: action array, order same as obs['state']
        """
        raise NotImplementedError('control_robot is not implemented')

    def retrieve_observation(self):
        """
        Get current observation from robot
        Returns:
            obs: current robot observation, obs['state'] is current pose
        """
        raise NotImplementedError('retrieve_observation is not implemented')
    
    def reset_robot(self, target_pose='default'):
        """
        Reset robot to specified pose
        Args:
            target_pose: target pose, 'default' means default pose, 'zero' means zero pose, format: [7 left arm + 7 right arm + 2 gripper + 2 head + 2 waist + 2 wheels]
        """
        if target_pose == 'default':
            target_pose = np.array([-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0])
        elif target_pose == 'zero':
            target_pose = np.array([0] * 14 + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0])
        elif isinstance(target_pose, list):
            target_pose = np.array(target_pose)
        
        current_obs = self.retrieve_observation()
        current_positions = current_obs['obs.state'][:14]
        target_positions = target_pose[:14]
        # Calculate joint position differences
        dis = np.abs(current_positions - target_positions)
        mask = dis > np.deg2rad(0.01)  # Decide whether to use interpolation strategy
        # If difference is small, move directly to target position
        if not np.any(mask):
            target_pose[:14] = target_positions
            self.control_robot(target_pose)
            time.sleep(0.01)
            return
        # Otherwise plan trajectory
        trajs = self._ruckig_planning(current_positions, target_positions)
        for i, traj in enumerate(trajs):
            # print(f"Executing trajectory point {i}: {traj}")
            print(f'\r{i}', end='')
            target_pose[:14] = traj
            self.control_robot(target_pose)
            time.sleep(0.01)
    
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
    
    def close(self):
        pass
