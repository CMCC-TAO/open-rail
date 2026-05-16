import time
import queue
import threading
import numpy as np
import matplotlib.pyplot as plt
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor
from client.utils.util import run_time_decorator, get_action_layout_info

class IntraChunkSmoother():
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
        self.action_layout = dict(config.action_layout) if hasattr(config, 'action_layout') else {}
        self.action_dim, self.joint_indices, self.step_indices = get_action_layout_info(self.action_layout)
        # Create thread pools for parallel trajectory fitting
        self.joint_fitting_executor = ThreadPoolExecutor(max_workers=config.max_joint_fitting_workers)
        self.gripper_fitting_executor = ThreadPoolExecutor(max_workers=config.max_gripper_fitting_workers)
        
        # Initialize trajectory data storage
        # self.traj = None
        # self.traj_fitted = None
        # self.vel_fitted = None
        # self.acc_fitted = None
        # self.timestamps = None
        # self.timestamps_fitted = None
        
        self.frame = 0

    def process(self, action_chunk, timestamps, ):
        """Perform trajectory fitting for robot actions.
        
        This method retrieves action chunks from the real-time data manager,
        performs polynomial fitting using the trajectory generator to create
        smooth trajectories for robot control.
        
        Args:
            num_samples (int): Number of action samples to use for fitting
            
        Returns:
            tuple: A tuple containing:
                - action_chunk_fitted (np.ndarray): Fitted action trajectory
                - vel_chunk_fitted (np.ndarray): Fitted velocity trajectory  
                - timestamps_fitted (np.ndarray): Corresponding timestamps
        """
        
        start_time = timestamps[0]
        end_time = timestamps[-1]
        
        if self.config.intra_chunk_mode == 'raw':
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted = self._traj_raw(
                timestamps=timestamps, 
                action_chunk=action_chunk
            ) 
        elif self.config.intra_chunk_mode == 'interpolation':
            # Use CubicSpline interpolation for sparse raw chunks
            action_chunk = np.asarray(action_chunk)
            timestamps = np.asarray(timestamps)
            
            # Create dense timestamps for interpolation
            time_step = self.config.intra_chunk.fitting_time_step / 1000  # convert ms to seconds
            timestamps_fitted = np.arange(start_time, end_time, time_step)
            
            # Interpolate each joint dimension using CubicSpline
            n_joints = action_chunk.shape[0]
            action_chunk_fitted = np.zeros((n_joints, len(timestamps_fitted)))
            vel_chunk_fitted = np.zeros((n_joints, len(timestamps_fitted)))
            acc_chunk_fitted = np.zeros((n_joints, len(timestamps_fitted)))
            
            step_index_set = set(self.step_indices)
            for j in range(n_joints):
                # Gripper and head dimensions use zero-order hold interpolation (step-like)
                if j in step_index_set:
                    interp_func = interp1d(timestamps, action_chunk[j], kind='previous', bounds_error=False, fill_value='extrapolate')
                    action_chunk_fitted[j] = interp_func(timestamps_fitted)
                    vel_chunk_fitted[j] = np.zeros(len(timestamps_fitted))
                    acc_chunk_fitted[j] = np.zeros(len(timestamps_fitted))
                    continue
                cs = CubicSpline(timestamps, action_chunk[j])
                action_chunk_fitted[j] = cs(timestamps_fitted)
                vel_chunk_fitted[j] = cs(timestamps_fitted, 1)  # 1st derivative
                acc_chunk_fitted[j] = cs(timestamps_fitted, 2)  # 2nd derivative
        else:  # fit mode (default)
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted = self._traj_fitting(
                timestamps=timestamps, 
                action_chunk=action_chunk, 
                start_time=start_time, 
                end_time=end_time 
            )
        return action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted

    def _joint_traj_fitting(self, timestamps, joint_chunk, index, start_time, end_time, deg = 5, time_step = 0.001):
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
        # Second derivative (acceleration)
        second_derivative_coefficients = np.polyder(derivative_coefficients)

        x = np.arange(start_time, end_time, time_step)
        
        # Calculate fitted joint angles using the polynomial
        polynomial = np.poly1d(coefficients)
        joint_chunk_fitted = polynomial(x)
        
        # Calculate joint velocities using the derivative
        derivative_polynomial = np.poly1d(derivative_coefficients)
        velocity_chunk_fitted = derivative_polynomial(x)

        # Calculate joint acceleration using the second derivative
        second_derivative_polynomial = np.poly1d(second_derivative_coefficients)
        acceleration_chunk_fitted = second_derivative_polynomial(x)
        # print(f"fitting degree: {deg}, time_step: {time_step}")
        return index, joint_chunk_fitted, velocity_chunk_fitted, acceleration_chunk_fitted

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

        return index, gripper_chunk_fitted, np.zeros_like(gripper_chunk_fitted), np.zeros_like(gripper_chunk_fitted)  # Gripper velocity and acceleration are not considered

    @run_time_decorator
    def _traj_fitting(self, timestamps, action_chunk, start_time, end_time):
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
        # use config parameters for fitting degree and time step to allow dynamic adjustment without modifying code
        deg=self.config.intra_chunk.fitting_deg 
        time_step=self.config.intra_chunk.fitting_time_step / 1000 # convert ms to seconds

        futures = []
        for name, seg in self.action_layout.items():
            for index in range(seg['start'], seg['end']):
                joint_chunk = np.array(action_chunk[index, :])
                if seg['policy'] == 'joint':
                    futures.append(self.joint_fitting_executor.submit(
                        self._joint_traj_fitting, timestamps, joint_chunk, index, start_time, end_time, deg, time_step
                    ))
                else:
                    futures.append(self.gripper_fitting_executor.submit(
                        self._gripper_traj_fitting, timestamps, joint_chunk, index, start_time, end_time, time_step
                    ))

        results = [future.result() for future in futures]
        
        # Parse results - joint_results represent joint angle data, velocity_results represent joint velocity data
        action_dim = action_chunk.shape[0]
        final_joint_results = [None] * action_dim
        final_velocity_results = [None] * action_dim
        final_acceleration_results = [None] * action_dim
        
        for index, joint_chunk_fitted, velocity_chunk_fitted, acceleration_chunk_fitted in results:
            final_joint_results[index] = joint_chunk_fitted
            final_velocity_results[index] = velocity_chunk_fitted
            final_acceleration_results[index] = acceleration_chunk_fitted
        # if self.traj_fitted is None:
        traj_fitted = np.array(final_joint_results)
        vel_fitted = np.array(final_velocity_results)
        acc_fitted = np.array(final_acceleration_results)
        timestamps_fitted = np.arange(start_time, end_time, time_step)
        # else:
        #     traj_fitted_new = np.array(final_joint_results)
        #     vel_fitted_new = np.array(final_velocity_results)
        #     acc_fitted_new = np.array(final_acceleration_results)

        #     self.traj_fitted = traj_fitted_new
        #     self.vel_fitted = vel_fitted_new
        #     self.acc_fitted = acc_fitted_new
        #     self.timestamps_fitted = np.arange(start_time, end_time, time_step)
        #     self.traj = action_chunk
        #     self.timestamps = timestamps

        return traj_fitted, vel_fitted, acc_fitted, timestamps_fitted
    
    def _traj_raw(self, timestamps, action_chunk):
        """Return raw trajectories without fitting for both joints and grippers.
        
        Args:
            timestamps (np.array): Timestamps for the action chunk.
            action_chunk (np.array): Action data to be returned.
        """
        
        traj_fitted = action_chunk
        vel_fitted = np.zeros_like(action_chunk)
        acc_fitted = np.zeros_like(action_chunk)
        timestamps_fitted = timestamps  # original sparse timestamps
        return traj_fitted, vel_fitted, acc_fitted, timestamps_fitted

if __name__ == '__main__':
    import os
    import sys
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(f'root_dir: {root_dir}')
    sys.path.append(root_dir)
    from conf.client_conf import get_intra_chunk_config
    intra_chunk_config = get_intra_chunk_config()
    print(intra_chunk_config)
    intra_chunk_smoother = IntraChunkSmoother(config=intra_chunk_config)
