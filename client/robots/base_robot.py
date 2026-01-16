import time
import cv2
import numpy as np

try:
    import ruckig
except ImportError:
    pass

class RobotBase():
    def __init__(self):
        self.robot = None

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
        """
        raise NotImplementedError('reset_robot is not implemented')

    def ruckig_planning(self, current_pose, target_pose, dof=14, interval=0.01):
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
