import logging
import numpy as np
from scipy.interpolate import CubicSpline, interp1d
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor
from client.utils.util import run_time_decorator, parse_action_layout

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
        self.logger = logging.getLogger(__name__)
        self.config = config
        # Create thread pools for parallel trajectory fitting
        # self.joint_fitting_executor = ThreadPoolExecutor(max_workers=config.max_joint_fitting_workers,
        #                                                 thread_name_prefix="joint_fitting_thread")
        # self.gripper_fitting_executor = ThreadPoolExecutor(max_workers=config.max_gripper_fitting_workers,
        #                                                 thread_name_prefix="gripper_fitting_thread")
        
        # Initialize trajectory data storage
        # self.traj = None
        # self.traj_fitted = None
        # self.vel_fitted = None
        # self.acc_fitted = None
        # self.timestamps = None
        # self.timestamps_fitted = None
        
        # self.frame = 0
    def set_action_layout(self, action_layout: dict = {}):
        self.action_layout = action_layout
        self.action_dim, self.joint_indices, self.step_indices = parse_action_layout(action_layout)

    def process(self, timestamps, action_chunk, time_step=3.75, task_progress=None, joint_indices=None, step_indices=None):
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
        time_step = time_step / 1000 # convert milliseconds to seconds
        
        if self.config.intra_chunk_mode == 'raw':
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted = self._traj_raw(
                timestamps=timestamps, 
                action_chunk=action_chunk,
                start_time=start_time,
                end_time=end_time,
                time_step=time_step
            ) 
            task_progress_fitted = task_progress  # directly use the original task progress without interpolation
        elif self.config.intra_chunk_mode == 'interpolation':
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted = self._traj_interpolation(
                timestamps=timestamps,
                action_chunk=action_chunk,
                start_time=start_time,
                end_time=end_time,
                time_step=time_step,
                step_indices=step_indices
            )
            task_progress_fitted = self._task_progress_interpolation(
                timestamps=timestamps,
                task_progress=task_progress,
                start_time=start_time,
                end_time=end_time,
                time_step=time_step
            ) if task_progress is not None else None
        elif self.config.intra_chunk_mode == 'fitting':
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted = self._traj_fitting(
                timestamps=timestamps, 
                action_chunk=action_chunk, 
                start_time=start_time, 
                end_time=end_time,
                time_step=time_step,
                joint_indices=joint_indices,
                step_indices=step_indices
            )
            task_progress_fitted = self._task_progress_interpolation(
                timestamps=timestamps,
                task_progress=task_progress,
                start_time=start_time,
                end_time=end_time,
                time_step=time_step
            ) if task_progress is not None else None
        else:  # fit mode (default)
            action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted = self._traj_fitting(
                timestamps=timestamps, 
                action_chunk=action_chunk, 
                start_time=start_time, 
                end_time=end_time,
                time_step=time_step,
                joint_indices=joint_indices,
                step_indices=step_indices
            )
            task_progress_fitted = self._task_progress_interpolation(
                timestamps=timestamps,
                task_progress=task_progress,
                start_time=start_time,
                end_time=end_time,
                time_step=time_step
            ) if task_progress is not None else None
        return action_chunk_fitted, vel_chunk_fitted, acc_chunk_fitted, timestamps_fitted, task_progress_fitted

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
        # joint_chunk_fitted = np.polyval(coefficients, x)
        
        # Calculate joint velocities using the derivative
        derivative_polynomial = np.poly1d(derivative_coefficients)
        velocity_chunk_fitted = derivative_polynomial(x)
        # velocity_chunk_fitted = np.polyval(derivative_coefficients, x)

        # Calculate joint acceleration using the second derivative
        second_derivative_polynomial = np.poly1d(second_derivative_coefficients)
        acceleration_chunk_fitted = second_derivative_polynomial(x)
        # acceleration_chunk_fitted = np.polyval(second_derivative_coefficients, x)
        # print(f"fitting degree: {deg}, time_step: {time_step}")
        return index, joint_chunk_fitted, velocity_chunk_fitted, acceleration_chunk_fitted
    def _joint_traj_fitting_batch(self, timestamps, joint_chunks, start_time, end_time, deg = 5, time_step = 0.001):
        """Batch polynomial fitting for multiple joints.

        Args:
            timestamps (np.ndarray): shape [num_points]
            joint_chunks (np.ndarray): shape [num_joints, num_points]
        Returns:
            tuple: fitted trajectory / velocity / acceleration,
                each in shape [num_joints, num_fitted_points]
        """
        timestamps = np.asarray(timestamps, dtype=float).reshape(-1)
        joint_chunks = np.asarray(joint_chunks, dtype=float)

        if joint_chunks.ndim != 2:
            raise ValueError(f"joint_chunks must be 2D, got shape {joint_chunks.shape}")

        num_joints, num_points = joint_chunks.shape
        if num_points != timestamps.size:
            raise ValueError(
                f"timestamps length ({timestamps.size}) must match joint_chunks.shape[1] ({num_points})"
            )

        # Fit degree cannot exceed num_points - 1
        fit_deg = int(min(deg, max(num_points - 1, 0)))

        # Solve polynomial coefficients for all joints together.
        # coeffs shape: [fit_deg + 1, num_joints], highest power first.
        vander = np.vander(timestamps, N=fit_deg + 1)
        coeffs, _, _, _ = np.linalg.lstsq(vander, joint_chunks.T, rcond=None)

        # Derivative coefficients in batch (avoid np.polyder on 2D arrays).
        # p'(x): c_k * (n-k), where k iterates over coefficient index.
        if fit_deg >= 1:
            deriv1_weights = np.arange(fit_deg, 0, -1, dtype=coeffs.dtype)[:, None]
            deriv1_coeffs = coeffs[:-1, :] * deriv1_weights
        else:
            deriv1_coeffs = np.zeros((0, num_joints), dtype=coeffs.dtype)

        if fit_deg >= 2:
            deriv2_weights = np.arange(fit_deg - 1, 0, -1, dtype=coeffs.dtype)[:, None]
            deriv2_coeffs = deriv1_coeffs[:-1, :] * deriv2_weights
        else:
            deriv2_coeffs = np.zeros((0, num_joints), dtype=coeffs.dtype)

        # Generate fitted timestamps and evaluate in batch via Vandermonde matrices.
        x = np.arange(start_time, end_time, time_step)
        num_x = x.size

        vander_x = np.vander(x, N=fit_deg + 1)
        joint_chunk_fitted = (vander_x @ coeffs).T

        if deriv1_coeffs.shape[0] > 0:
            vander_x_d1 = np.vander(x, N=deriv1_coeffs.shape[0])
            velocity_chunk_fitted = (vander_x_d1 @ deriv1_coeffs).T
        else:
            velocity_chunk_fitted = np.zeros((num_joints, num_x), dtype=coeffs.dtype)

        if deriv2_coeffs.shape[0] > 0:
            vander_x_d2 = np.vander(x, N=deriv2_coeffs.shape[0])
            acceleration_chunk_fitted = (vander_x_d2 @ deriv2_coeffs).T
        else:
            acceleration_chunk_fitted = np.zeros((num_joints, num_x), dtype=coeffs.dtype)

        return joint_chunk_fitted, velocity_chunk_fitted, acceleration_chunk_fitted

    def _gripper_traj_fitting(self, timestamps, gripper_chunk, index, start_time, end_time, time_step = 0.001):
        """Fit one gripper trajectory (legacy single-dimension API kept for compatibility)."""
        gripper_chunk = np.asarray(gripper_chunk, dtype=float).reshape(1, -1)
        gripper_fitted, velocity_fitted, acceleration_fitted = self._gripper_traj_fitting_batch(
            timestamps=timestamps,
            gripper_chunks=gripper_chunk,
            start_time=start_time,
            end_time=end_time,
            time_step=time_step
        )
        return index, gripper_fitted[0], velocity_fitted[0], acceleration_fitted[0]

    def _gripper_traj_fitting_batch(self, timestamps, gripper_chunks, start_time, end_time, time_step=0.001):
        """Batch fitting for multiple gripper trajectories using numpy vectorization.

        Args:
            timestamps (np.ndarray): shape [num_points]
            gripper_chunks (np.ndarray): shape [num_grippers, num_points]

        Returns:
            tuple: fitted trajectory / velocity / acceleration,
                each in shape [num_grippers, num_fitted_points]
        """
        timestamps = np.asarray(timestamps, dtype=float).reshape(-1)
        gripper_chunks = np.asarray(gripper_chunks, dtype=float)

        if gripper_chunks.ndim != 2:
            raise ValueError(f"gripper_chunks must be 2D, got shape {gripper_chunks.shape}")

        num_grippers, length = gripper_chunks.shape
        if length != timestamps.size:
            raise ValueError(
                f"timestamps length ({timestamps.size}) must match gripper_chunks.shape[1] ({length})"
            )

        if length == 0:
            return np.zeros((num_grippers, 0)), np.zeros((num_grippers, 0)), np.zeros((num_grippers, 0))

        # Sliding-window mean + threshold snap, vectorised over every output
        # index at once via a cumulative sum.
        #
        # BEHAVIOUR CHANGE: the loop this replaces wrote each result back into
        # the array it was also reading from, so a window averaged values that
        # had already been filtered -- an accidental IIR,
        #     f[i] = clamp(mean(f[i-h .. i-1], x[i .. i+h])).
        # This now averages the raw input only, which is what the config names
        # describe (`filter_window_size`, and the 0.05 / 0.95 thresholds that
        # snap the smoothed command to fully open / fully closed).
        #
        # Window bounds are preserved exactly: every window has the same width
        # w = 2h+1 (clamped to `length`), and at the edges the window slides as
        # a whole instead of shrinking. That matches the previous three-branch
        # logic branch by branch, including the case where length < 2h+1 and
        # the left/right branches overlap (the left branch won).
        window_size_half = int(self.config.filter_window_size)
        w = min(2 * window_size_half + 1, length)

        # prefix[i] = sum of columns [0, i); window [a, a+w) -> prefix[a+w]-prefix[a]
        prefix = np.cumsum(
            np.concatenate([np.zeros((num_grippers, 1)), gripper_chunks], axis=1),
            axis=1,
        )
        window_min = np.clip(np.arange(length) - window_size_half, 0, length - w)
        mean_all = (prefix[:, window_min + w] - prefix[:, window_min]) / w

        filtered = np.where(
            mean_all > self.config.max_gripper_action_threshold,
            1.0,
            np.where(mean_all < self.config.min_gripper_action_threshold, 0.0, mean_all)
        )

        # Keep interpolation behavior consistent with legacy implementation.
        timestamps_fitted = np.arange(start_time, end_time, time_step)
        if timestamps_fitted.size == 0:
            return np.zeros((num_grippers, 0)), np.zeros((num_grippers, 0)), np.zeros((num_grippers, 0))

        # Bracket each fitted timestamp with its neighbouring raw timestamps.
        # Replaces the previous incremental scan; equivalent as long as raw
        # timestamp spacing >= time_step (holds for the configured control period).
        right_index = np.searchsorted(timestamps, timestamps_fitted, side='left')
        left_index = np.maximum(right_index - 1, 0)
        gripper_chunk_fitted = (
            filtered[:, left_index] + filtered[:, np.minimum(right_index, length - 1)]
        ) / 2.0

        zero_like = np.zeros_like(gripper_chunk_fitted)
        return gripper_chunk_fitted, zero_like, zero_like  # Gripper velocity and acceleration are not considered

    @run_time_decorator
    def _traj_fitting(self, timestamps, action_chunk, start_time, end_time, time_step, joint_indices, step_indices):
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
        deg=self.config.fitting_deg 
        action_dim = action_chunk.shape[0]
        final_joint_results = [None] * action_dim
        final_velocity_results = [None] * action_dim
        final_acceleration_results = [None] * action_dim

        # futures = []
        for name, seg in self.action_layout.items():
            if seg['policy'] == 'manual':
                continue
            elif seg['policy'] == 'gradual':
                joint_chunks = np.array(action_chunk[seg['start']:seg['end'], :])
                # Compute all joints in this segment in parallel at once
                j_fitted, v_fitted, a_fitted = self._joint_traj_fitting_batch(
                    timestamps, joint_chunks, start_time, end_time, deg, time_step
                )
                # Store the results into the final result arrays
                final_joint_results[seg['start']:seg['end']] = j_fitted
                final_velocity_results[seg['start']:seg['end']] = v_fitted
                final_acceleration_results[seg['start']:seg['end']] = a_fitted
            elif seg['policy'] == 'stepwise':
                gripper_chunks = np.array(action_chunk[seg['start']:seg['end'], :])
                g_fitted, g_vel_fitted, g_acc_fitted = self._gripper_traj_fitting_batch(
                    timestamps=timestamps,
                    gripper_chunks=gripper_chunks,
                    start_time=start_time,
                    end_time=end_time,
                    time_step=time_step
                )
                final_joint_results[seg['start']:seg['end']] = g_fitted
                final_velocity_results[seg['start']:seg['end']] = g_vel_fitted
                final_acceleration_results[seg['start']:seg['end']] = g_acc_fitted

                # Legacy per-dimension calling logic (kept for reference):
                # for index in range(seg['start'], seg['end']):
                #     joint_chunk = np.array(action_chunk[index, :])
                #     futures.append(self.gripper_fitting_executor.submit(
                #         self._gripper_traj_fitting, timestamps, joint_chunk, index, start_time, end_time, time_step
                #     ))
            else:
                raise ValueError(f"Unknown policy: {seg['policy']}")

            # for index in range(seg['start'], seg['end']):
            #     joint_chunk = np.array(action_chunk[index, :])
            #     if seg['policy'] == 'gradual':
            #         futures.append(self.joint_fitting_executor.submit(
            #             self._joint_traj_fitting, timestamps, joint_chunk, index, start_time, end_time, deg, time_step
            #         ))
            #     elif seg['policy'] == 'stepwise':
            #         futures.append(self.gripper_fitting_executor.submit(
            #             self._gripper_traj_fitting, timestamps, joint_chunk, index, start_time, end_time, time_step
            #         ))
            #     else:
            #         raise ValueError(f"Unknown policy: {seg['policy']}")

        # results = [future.result() for future in futures]
        
        # Parse results - joint_results represent joint angle data, velocity_results represent joint velocity data
        
        # for index, joint_chunk_fitted, velocity_chunk_fitted, acceleration_chunk_fitted in results:
        #     final_joint_results[index] = joint_chunk_fitted
        #     final_velocity_results[index] = velocity_chunk_fitted
        #     final_acceleration_results[index] = acceleration_chunk_fitted
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
    
    @run_time_decorator
    def _traj_raw(self, timestamps, action_chunk, start_time, end_time, time_step):
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
    
    @run_time_decorator
    def _traj_interpolation(self, timestamps, action_chunk, start_time, end_time, time_step, step_indices):
        """Interpolate trajectories for both joints and grippers using CubicSpline.
        
        Args:
            timestamps (np.array): Timestamps for the action chunk.
            action_chunk (np.array): Action data to be interpolated.
            start_time (float): Start time for the interpolated trajectory.
            end_time (float): End time for the interpolated trajectory.
        """
        # Use CubicSpline interpolation for sparse raw chunks
        # action_chunk = np.asarray(action_chunk)
        # timestamps = np.asarray(timestamps)
        
        # Create dense timestamps for interpolation
        timestamps_fitted = np.arange(start_time, end_time, time_step)
        
        # Interpolate each joint dimension using CubicSpline
        n_joints = action_chunk.shape[0]
        traj_fitted = np.zeros((n_joints, len(timestamps_fitted)))
        vel_fitted = np.zeros((n_joints, len(timestamps_fitted)))
        acc_fitted = np.zeros((n_joints, len(timestamps_fitted)))
        
        step_index_set = set(step_indices)
        for j in range(n_joints):
            # Gripper and head dimensions use zero-order hold interpolation (step-like)
            if j in step_index_set:
                interp_1d = interp1d(timestamps, action_chunk[j], kind='previous', bounds_error=False, fill_value='extrapolate')
                traj_fitted[j] = interp_1d(timestamps_fitted)
                vel_fitted[j] = np.zeros(len(timestamps_fitted))
                acc_fitted[j] = np.zeros(len(timestamps_fitted))
                continue
            cubic_spline = CubicSpline(timestamps, action_chunk[j])
            traj_fitted[j] = cubic_spline(timestamps_fitted)
            vel_fitted[j] = cubic_spline(timestamps_fitted, 1)  # 1st derivative
            acc_fitted[j] = cubic_spline(timestamps_fitted, 2)  # 2nd derivative
        return traj_fitted, vel_fitted, acc_fitted, timestamps_fitted
    
    def _task_progress_interpolation(self, timestamps, task_progress, start_time, end_time, time_step):
        """Interpolate task progress using linear interpolation.
        
        Args:
            timestamps (np.array): Timestamps for the task progress data.
            task_progress (np.array): Task progress data to be interpolated.
            start_time (float): Start time for the interpolated task progress.
            end_time (float): End time for the interpolated task progress.
        """
        timestamps_fitted = np.arange(start_time, end_time, time_step)
        interp_1d = interp1d(timestamps, task_progress, kind='linear', bounds_error=False, fill_value='extrapolate')
        task_progress_fitted = interp_1d(timestamps_fitted)
        # self.logger.debug(f"Task progress interpolation: original task progress: {task_progress}, fitted task progress: {task_progress_fitted}")
        return task_progress_fitted

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
