import time
import queue
import threading
import numpy as np
import matplotlib.pyplot as plt
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor
from client.utils.util import run_time_decorator

class TrajectoryGenerator():
    """Trajectory generator for robot motion planning and control.
    
    This class provides functionality for fitting and generating smooth trajectories
    for robot joints and grippers using polynomial fitting and filtering techniques.
    """
    def __init__(self, config: ConfigDict):
        """Initialize the trajectory generator.
        
        Args:
            config (ConfigDict): Configuration parameters for trajectory generation.
        """
        self.config = config
        # Create thread pools for parallel trajectory fitting
        self.joint_fitting_executor = ThreadPoolExecutor(max_workers=config.max_joint_fitting_workers)
        self.gripper_fitting_executor = ThreadPoolExecutor(max_workers=config.max_gripper_fitting_workers)
        
        # Initialize trajectory data storage
        self.traj = None
        self.traj_fitted = None
        self.vel_fitted = None
        self.timestamps = None
        self.timestamps_fitted = None
        
        self.frame = 0

    def _joint_traj_fitting(self, timestamps, joint_chunk, index, start_time, end_time, deg = 3, time_step = 0.001):
        """Fit a joint trajectory using polynomial fitting with deg parameter and return the fitted trajectory defined by start_time, end_time and time_step.

        Args:
            timestamps (np.array): The timestamps of the joint trajectory in seconds.
            joint_chunk (np.array): The joint trajectory to be fitted in radians.
            index (int): The index of the joint.
            start_time (float): The start time of the fitted trajectory in seconds.
            end_time (float): The end time of the fitted trajectory in seconds.
            deg (int, optional): The degree of the polynomial to be fitted. Defaults to 3.
            time_step (float, optional): The time step to compute the fitted trajectory. Defaults to 0.001.

        Returns:
            tuple(int, np.array, np.array): The index of the joint, the fitted trajectory and the velocity of the fitted trajectory.
        """
        # x = np.array(timestamps)
        # y = np.array(joint_chunk)
        # Perform polynomial fitting
        coefficients = np.polyfit(timestamps, joint_chunk, deg=deg)
        # Calculate polynomial derivative coefficients
        derivative_coefficients = np.polyder(coefficients)
        
        # Calculate fitted joint angles using the polynomial
        polynomial = np.poly1d(coefficients)
        x = np.arange(start_time, end_time, time_step)
        joint_chunk_fitted = polynomial(x)
        
        # Calculate joint velocities using the derivative
        derivative_polynomial = np.poly1d(derivative_coefficients)
        velocity_chunk_fitted = derivative_polynomial(x)
        return index, joint_chunk_fitted, velocity_chunk_fitted

    def _gripper_traj_fitting(self, timestamps, gripper_chunk, index, start_time, end_time, time_step = 0.001):
        """Fit a gripper trajectory using mean filtering and return the fitted trajectory defined by start_time, end_time and time_step.

        Args:
            timestamps (np.array): The timestamps of the joint trajectory in seconds.
            gripper_chunk (np.array): The gripper trajectory to be fitted.
            index (int): The index of the gripper with respect to the arms
            start_time (float): The start time of the fitted trajectory in seconds.
            end_time (float): The end time of the fitted trajectory in seconds.
            time_step (float, optional): The time step to compute the fitted trajectory. Defaults to 0.001.

        Returns:
            tuple(int, np.array, np.array): The index of the joint, the fitted trajectory and the velocity of the fitted trajectory.
        """
        # Remove outliers using mean filtering
        length = len(gripper_chunk)
        window_size_half = self.config.filter_window_size
        for currt_index in range(length):
            if currt_index < window_size_half:
                window_min = 0
                window_max = min(length, window_size_half * 2 + 1)
            elif currt_index >= length - window_size_half:
                window_min = max(0, length - window_size_half * 2 -1)
                window_max = length
            else:
                window_min = currt_index - window_size_half
                window_max = currt_index + window_size_half + 1
            mean = np.mean(gripper_chunk[window_min:window_max])

            if mean > self.config.max_gripper_action_threshold:
                mean = 1.0
            elif mean < self.config.min_gripper_action_threshold:
                mean = 0.0
            else:
                pass
            gripper_chunk[currt_index] = mean
        
        # Interpolate the trajectory using linear interpolation
        timestamp_fitted = np.arange(start_time, end_time, time_step)
        gripper_chunk_fitted = []
        currt_index = 0
        for timestamp in timestamp_fitted:
            if timestamp > timestamps[currt_index]:
                currt_index = min(length, currt_index + 1)
            gripper_chunk_fitted.append((gripper_chunk[max(currt_index - 1, 0)] + gripper_chunk[min(currt_index, length - 1)]) / 2.0)

        return index, gripper_chunk_fitted, np.zeros_like(gripper_chunk_fitted)  # Gripper velocity is not considered

    @run_time_decorator
    def traj_fitting(self, timestamps, action_chunk, start_time, end_time, deg = 3, time_step = 0.001):
        """Fit trajectories for both joints and grippers.
        
        Args:
            timestamps (np.array): Timestamps for the action chunk.
            action_chunk (np.array): Action data to be fitted.
            start_time (float): Start time for the fitted trajectory.
            end_time (float): End time for the fitted trajectory.
            deg (int, optional): Polynomial degree for joint fitting. Defaults to 3.
            time_step (float, optional): Time step for the fitted trajectory. Defaults to 0.001.
            
        Returns:
            tuple: (fitted_trajectory, fitted_velocity, fitted_timestamps)
        """
        # Preprocess action data - convert from action dimension format to joint dimension format
        joint_futures = [self.joint_fitting_executor.submit(self._joint_traj_fitting, timestamps, np.array(joint_chunk), index, start_time, end_time, deg, time_step) for index, joint_chunk in enumerate(action_chunk[0:self.config.joint_dim, :])]
        gripper_futures = [self.gripper_fitting_executor.submit(self._gripper_traj_fitting, timestamps, np.array(joint_chunk), self.config.joint_dim+index, start_time, end_time, time_step) for index, joint_chunk in enumerate(action_chunk[self.config.joint_dim:, :])]

        # Wait for all tasks to complete and get results
        gripper_results = [future.result() for future in gripper_futures]
        joint_results = [future.result() for future in joint_futures]
        results = joint_results + gripper_results
        
        # Parse results - joint_results represent joint angle data, velocity_results represent joint velocity data
        final_joint_results = [None] * len(results)
        final_velocity_results = [None] * len(results)
        
        for index, joint_chunk_fitted, velocity_chunk_fitted in results:
            final_joint_results[index] = joint_chunk_fitted
            final_velocity_results[index] = velocity_chunk_fitted
        if self.traj_fitted is None:
            self.traj_fitted = np.array(final_joint_results)
            self.vel_fitted = np.array(final_velocity_results)
            self.traj = action_chunk
            self.timestamps_fitted = np.arange(start_time, end_time, time_step)
            self.timestamps = timestamps
        else:
            traj_fitted_new = np.array(final_joint_results)
            vel_fitted_new = np.array(final_velocity_results)
            timestamps_fitted_new = np.arange(start_time, end_time, time_step)

            self.traj_fitted = traj_fitted_new
            self.vel_fitted = vel_fitted_new
            self.timestamps_fitted = timestamps_fitted_new
            self.traj = action_chunk
            self.timestamps = timestamps

        return self.traj_fitted, self.vel_fitted, self.timestamps_fitted

if __name__ == '__main__':
    import os
    import sys
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(f'root_dir: {root_dir}')
    sys.path.append(root_dir)
    from conf.traj_conf import get_traj_config
    config = get_traj_config()
    print(config)
    traj_generator = TrajectoryGenerator(config=config)
