import logging
import numpy as np
# from numba import njit
from ml_collections import ConfigDict
from client.utils.util import run_time_decorator


class InterChunkFuser:
    """Independent inter-chunk fusion utilities for action trajectory transition."""

    def __init__(self, config: ConfigDict):
        self.logger = logging.getLogger(__name__)
        self.config = config

    def _mode_config(self, mode):
        cfg = getattr(self.config, mode, None)
        return cfg if cfg is not None else ConfigDict()

    def _cfg_value(self, cfg, key, default):
        return getattr(cfg, key, getattr(self.config, key, default))

    def process(self, 
            next_action_chunk,
            next_vel_chunk,
            next_acc_chunk,
            next_timestamps,
            target_chunk_index,
            currt_action=None,
            currt_vel=None,
            currt_acc=None,
            joint_indices= None,
            step_indices = None):
        mode = self.config.inter_chunk_mode
        mode_cfg = self._mode_config(mode)
        # self.logger.info(f"mode = {mode}")
        # print(f"DEBUG: mode={mode}")
        # process first inference
        if joint_indices is None:
            joint_indices = list(range(next_action_chunk.shape[0]))
        if currt_action is None and currt_vel is None and currt_acc is None:
            # print(f"DEBUG: NONE")
            next_vel_chunk = np.zeros_like(next_action_chunk)
            next_vel_chunk[:, 1:] = (next_action_chunk[:, 1:] - next_action_chunk[:, :-1]) / (next_timestamps[1] - next_timestamps[0])
            next_vel_chunk[:, 0] = next_vel_chunk[:, 1]

            next_acc_chunk = np.zeros_like(next_acc_chunk)
            next_acc_chunk[:, 1:] = (next_vel_chunk[:, 1:] - next_vel_chunk[:, :-1]) / (next_timestamps[1] - next_timestamps[0])
            next_acc_chunk[:, 0] = next_acc_chunk[:, 1]
            
            return next_action_chunk, next_vel_chunk, next_acc_chunk, target_chunk_index


        if mode == 'search_action':
            action_chunk_smoothed, target_chunk_index = self._search_smooth_action(
                next_action_chunk,
                target_chunk_index,
                currt_action,
                currt_vel,
                self._cfg_value(mode_cfg, 'search_length', 100),
                search_step = 5)
        elif mode == 'smooth_velocity':
            # sim_action, sim_vel, sim_acc = self._smooth_velocity_transition(target_action_segment, currt_action, currt_vel, currt_acc, delat_t)
            action_chunk_smoothed, target_chunk_index = self._smooth_velocity_transition_numba(
                next_action_chunk,
                next_timestamps,
                target_chunk_index,
                currt_action,
                currt_vel,
                currt_acc,
                joint_indices=joint_indices,
                max_vel=self._cfg_value(mode_cfg, 'max_vel', 2.0),
                max_acc=self._cfg_value(mode_cfg, 'max_acc', 5.0),
                kp=self._cfg_value(mode_cfg, 'kp', 5.0),
                kd=self._cfg_value(mode_cfg, 'kd', 2.0))
            # vel_chunk_fitted[joint_indices, target_chunk_index:] = sim_vel
            # acc_chunk_fitted[joint_indices, target_chunk_index:] = sim_acc 
        elif mode == 'min_jerk':
            action_chunk_smoothed, target_chunk_index = self._min_jerk_chunk_transition_numpy(
                next_action_chunk,
                next_vel_chunk,
                next_acc_chunk,
                next_timestamps,
                target_chunk_index,
                currt_action,
                currt_vel,
                currt_acc,
                joint_indices=joint_indices,
                blend_threshold=self._cfg_value(mode_cfg, 'blend_threshold', 0.7),
                adaptive_factor=self._cfg_value(mode_cfg, 'adaptive_factor', -1)
            )
        elif mode == 'sync':
            action_chunk_smoothed = next_action_chunk.copy()
        else:
            self.logger.warning(f"Unknown inter_chunk_mode={mode}, use next action chunk directly.")
            action_chunk_smoothed = next_action_chunk.copy()
            
        # # calculate velocity and acceleration in a unified format
        # TODO: Calculate velocity and acceleration in methods;
        action_future = action_chunk_smoothed[joint_indices, target_chunk_index:].copy()
        action_future_1 = np.concatenate((currt_action[joint_indices, None], action_future[:, :-1]), axis=1)
        vel_future = (action_future - action_future_1) / (next_timestamps[1] - next_timestamps[0])
        
        vel_future_1 = np.concatenate((currt_vel[joint_indices, None], vel_future[:, :-1]), axis=1)
        acc_future = (vel_future - vel_future_1) / (next_timestamps[1] - next_timestamps[0])

        # # Update velocity and acceleration sequences
        vel_chunk_smoothed = next_vel_chunk.copy()
        vel_chunk_smoothed[joint_indices, target_chunk_index:] = vel_future
        acc_chunk_smoothed = next_acc_chunk.copy()
        acc_chunk_smoothed[joint_indices, target_chunk_index:] = acc_future 

        return action_chunk_smoothed, vel_chunk_smoothed, acc_chunk_smoothed, target_chunk_index
    # @staticmethod
    # @njit(fastmath=True, cache=True)
    # def _smooth_velocity_transition_numba_cp(joint_seq, init_pos, init_vel, init_acc, dt=0.005, max_vel=2.0, max_acc=5.0, kp=5.0, kd=2.0):
    #     """
    #     This strategy uses position error and velocity feedback to compute acceleration in real time, generating a continuous and smooth velocity sequence.
    #     Note: Under the same parameter settings, this strategy is slower than 'search_action'.
    #     Please refer to [this YuQue docs](https://www.yuque.com/zhaoyongsheng-qjvyk/wkh5s4/ghfyxptztpot0pyt) for acceleration, or contact the developers for assistance.

    #     This function is **accelerated by Numba** using `@njit`, which compiles the
    #     Python code into optimized machine code in *nopython mode*.
    #     Key acceleration strategies:
    #     1. `@njit`: eliminates Python interpreter overhead by compiling to native code.
    #     2. Loop-based implementation (no Python objects or dynamic typing),
    #         enabling efficient JIT optimization.
    #     3. `fastmath=True`: allows aggressive floating-point optimizations
    #         (acceptable for control / smoothing tasks with tolerance to small
    #         numerical errors).
    #     4. `cache=True`: caches the compiled binary to disk to avoid recompilation
    #         on subsequent runs.

    #     Note:
    #     - All inputs must be NumPy arrays with fixed dtypes (e.g., float32/float64).
    #     - Dynamic Python features and object operations are intentionally avoided
    #         to ensure compatibility with Numba's nopython mode.

    #     Parameters
    #     ----------
    #     joint_seq : ndarray of shape (dof, T)
    #         Target joint position sequence to be tracked.
    #     init_pos : ndarray of shape (dof,)
    #         Initial joint positions.
    #     init_vel : ndarray of shape (dof,)
    #         Initial joint velocities.
    #     init_acc : ndarray of shape (dof,)
    #         Initial joint accelerations.
    #     dt : float, optional
    #         Time step for discrete integration.
    #     max_vel : float, optional
    #         Maximum allowed joint velocity (symmetric bound).
    #     max_acc : float, optional
    #         Maximum allowed joint acceleration (symmetric bound).
    #     kp : float, optional
    #         Proportional gain of the PD controller.
    #     kd : float, optional
    #         Derivative gain of the PD controller.

    #     Returns
    #     -------
    #     pos_seq : ndarray of shape (dof, T)
    #         Smoothed joint position sequence.
    #     vel_seq : ndarray of shape (dof, T)
    #         Corresponding joint velocity sequence.
    #     acc_seq : ndarray of shape (dof, T)
    #         Corresponding joint acceleration sequence.
    #     """
    #     dof, T = joint_seq.shape

    #     pos = init_pos.copy()
    #     vel = init_vel.copy()
    #     acc = init_acc.copy()

    #     pos_seq = np.zeros((dof, T))
    #     vel_seq = np.zeros((dof, T))
    #     acc_seq = np.zeros((dof, T))

    #     for i in range(T):
    #         target = joint_seq[:, i]
    #         for j in range(dof):
    #             acc[j] = kp * (target[j] - pos[j]) - kd * vel[j]

    #             if acc[j] > max_acc:
    #                 acc[j] = max_acc
    #             elif acc[j] < -max_acc:
    #                 acc[j] = -max_acc

    #             vel[j] += acc[j] * dt

    #             if vel[j] > max_vel:
    #                 vel[j] = max_vel
    #             elif vel[j] < -max_vel:
    #                 vel[j] = -max_vel

    #             pos[j] += vel[j] * dt

    #             pos_seq[j, i] = pos[j]
    #             vel_seq[j, i] = vel[j]
    #             acc_seq[j, i] = acc[j]

    #     return pos_seq, vel_seq, acc_seq

    # @staticmethod
    # @njit(fastmath=True, cache=True)
    def _smooth_velocity_transition_numba(self,
                                    next_action_chunk,
                                    next_timestamps,
                                    target_chunk_index,
                                    init_pos,
                                    init_vel,
                                    init_acc,
                                    joint_indices,
                                    max_vel=2.0,
                                    max_acc=5.0,
                                    kp=5.0,
                                    kd=2.0):
        """
        This strategy uses position error and velocity feedback to compute acceleration in real time, generating a continuous and smooth velocity sequence.
        Note: Under the same parameter settings, this strategy is slower than 'search_action'.
        Please refer to [this YuQue docs](https://www.yuque.com/zhaoyongsheng-qjvyk/wkh5s4/ghfyxptztpot0pyt) for acceleration, or contact the developers for assistance.

        This function is **accelerated by Numba** using `@njit`, which compiles the
        Python code into optimized machine code in *nopython mode*.
        Key acceleration strategies:
        1. `@njit`: eliminates Python interpreter overhead by compiling to native code.
        2. Loop-based implementation (no Python objects or dynamic typing),
            enabling efficient JIT optimization.
        3. `fastmath=True`: allows aggressive floating-point optimizations
            (acceptable for control / smoothing tasks with tolerance to small
            numerical errors).
        4. `cache=True`: caches the compiled binary to disk to avoid recompilation
            on subsequent runs.

        Note:
        - All inputs must be NumPy arrays with fixed dtypes (e.g., float32/float64).
        - Dynamic Python features and object operations are intentionally avoided
            to ensure compatibility with Numba's nopython mode.

        Parameters
        ----------
        next_action_chunk : ndarray of shape (dof, T)
            Target joint position sequence to be tracked.
        next_timestamps : ndarray of shape (T,)
            Timestamps corresponding to the action chunk.
        target_chunk_index : int
            Index of the first timestamp in the current chunk.
        init_pos : ndarray of shape (dof,)
            Initial joint positions.
        init_vel : ndarray of shape (dof,)
            Initial joint velocities.
        init_acc : ndarray of shape (dof,)
            Initial joint accelerations.
        joint_indices : list of int, optional
            Indices of the joints to be considered. If None, all joints are considered.
        max_vel : float, optional
            Maximum allowed joint velocity (symmetric bound).
        max_acc : float, optional
            Maximum allowed joint acceleration (symmetric bound).
        kp : float, optional
            Proportional gain of the PD controller.
        kd : float, optional
            Derivative gain of the PD controller.

        Returns
        -------
        pos_seq : ndarray of shape (dof, T)
            Smoothed joint position sequence.
        vel_seq : ndarray of shape (dof, T)
            Corresponding joint velocity sequence.
        acc_seq : ndarray of shape (dof, T)
            Corresponding joint acceleration sequence.
        """
        init_pos = init_pos[joint_indices]
        init_vel = init_vel[joint_indices]
        init_acc = init_acc[joint_indices]
        target_action_chunk = next_action_chunk[joint_indices, target_chunk_index:]
        dt = next_timestamps[1] - next_timestamps[0]
        dof, chunk_size = target_action_chunk.shape

        pos = init_pos.copy()
        vel = init_vel.copy()
        acc = init_acc.copy()

        pos_seq = np.zeros((dof, chunk_size))
        vel_seq = np.zeros((dof, chunk_size))
        acc_seq = np.zeros((dof, chunk_size))

        for i in range(chunk_size):
            target_action = target_action_chunk[:, i]
            for j in range(dof):
                acc[j] = kp * (target_action[j] - pos[j]) - kd * vel[j]

                if acc[j] > max_acc:
                    acc[j] = max_acc
                elif acc[j] < -max_acc:
                    acc[j] = -max_acc

                vel[j] += acc[j] * dt

                if vel[j] > max_vel:
                    vel[j] = max_vel
                elif vel[j] < -max_vel:
                    vel[j] = -max_vel

                pos[j] += vel[j] * dt

                pos_seq[j, i] = pos[j]
                vel_seq[j, i] = vel[j]
                acc_seq[j, i] = acc[j]

        # return pos_seq, vel_seq, acc_seq
        action_chunk_smoothed = next_action_chunk.copy()
        action_chunk_smoothed[joint_indices, target_chunk_index:] = pos_seq
        return action_chunk_smoothed, target_chunk_index 


    @run_time_decorator
    def _min_jerk_chunk_transition(self,
        next_action_chunk,
        next_vel_chunk,
        next_acc_chunk,
        next_timestamps,
        target_chunk_index,
        current_pos,
        current_vel,
        current_acc,
        joint_indices,
        blend_threshold = 0.7,
        adaptive_factor = -1,
    ):
        """
        Smooths the transition to a new action chunk using a minimum-jerk trajectory.

        This method generates a smooth path from the current robot state (position, velocity,
        and acceleration) to a target state within the new action chunk. The trajectory
        is a quintic polynomial that minimizes jerk (the third derivative of position),
        resulting in a very smooth and natural-looking motion. The transition length is
        adaptively determined based on the difference between the current and target states.

        Args:
            next_action_chunk (np.ndarray): The upcoming chunk of actions (positions).
            next_vel_chunk (np.ndarray): The upcoming chunk of velocities.
            next_acc_chunk (np.ndarray): The upcoming chunk of accelerations.
            next_timestamps (np.ndarray): Timestamps corresponding to the action chunk.
            target_chunk_index (int): The index in the next_action_chunk where the transition should start.
            current_pos (np.ndarray): The current position of the robot joints.
            current_vel (np.ndarray): The current velocity of the robot joints.
            current_acc (np.ndarray): The current acceleration of the robot joints.
            joint_indices (list, optional): Indices of the joints to apply the transition to.
                                            If None, applies to all joints. Defaults to None.

        Returns:
            np.ndarray: The action chunk with the smoothed transition applied.
        """
        if current_pos is None or current_vel is None:
            return next_action_chunk

        # Define the target state for the transition.
        target_pos = next_action_chunk[:, target_chunk_index].copy()
        target_vel = next_vel_chunk[:, target_chunk_index].copy()
        target_acc = next_acc_chunk[:, target_chunk_index].copy() if next_acc_chunk is not None else np.zeros_like(target_vel)

        # Calculate the difference (magnitude) between current and target states.
        pos_diff = np.linalg.norm(current_pos[joint_indices] - target_pos[joint_indices])
        vel_diff = np.linalg.norm(current_vel[joint_indices] - target_vel[joint_indices])
        acc_diff = np.linalg.norm(current_acc[joint_indices] - target_acc[joint_indices])

        # Adaptively determine the transition length based on the state differences.
        # A larger difference results in a longer transition. A non-negative configured
        # adaptive_factor manually fixes the ratio and is clamped to [0, 1].
        base_transition = next_action_chunk.shape[1]
        if adaptive_factor < 0:
            adaptive_factor = min(1.0, 0.25 + pos_diff * 1.0 + vel_diff * 0.75 + acc_diff * 0.15)
        else:
            adaptive_factor = min(1.0, max(0.0, float(adaptive_factor)))
        transition_length = min(int(base_transition * adaptive_factor), next_action_chunk.shape[1] - target_chunk_index)

        # If the transition is too short, skip smoothing.
        if transition_length <= 1:
            return next_action_chunk

        action_chunk_smoothed = next_action_chunk.copy()

        # Calculate time step (dt) and total transition duration (T).
        dt = next_timestamps[1] - next_timestamps[0] if len(next_timestamps) > 1 else 0.005
        T = transition_length * dt

        # Determine the end index for the transition within the chunk.
        end_index = min(target_chunk_index + transition_length - 1, next_action_chunk.shape[1] - 1)

        # Generate the trajectory for each joint.
        for joint_idx in joint_indices:
            # Define initial conditions (at tau=0).
            x0 = current_pos[joint_idx]
            v0 = current_vel[joint_idx] * T  # Scale velocity by T for normalized time.
            a0 = current_acc[joint_idx] * T * T  # Scale acceleration by T^2 for normalized time.

            # Define final conditions (at tau=1).
            xf = next_action_chunk[joint_idx, end_index]
            vf = next_vel_chunk[joint_idx, end_index] * T if end_index < next_vel_chunk.shape[1] else 0.0
            af = (
                (next_acc_chunk[joint_idx, end_index] * T * T)
                if (next_acc_chunk is not None and end_index < next_acc_chunk.shape[1])
                else 0.0
            )

            # Apply the quintic polynomial for each step in the transition.
            for i in range(transition_length):
                # tau is the normalized time, from 0 to 1.
                tau = i / (transition_length - 1) if transition_length > 1 else 1.0
                tau2 = tau * tau
                tau3 = tau2 * tau
                tau4 = tau3 * tau
                tau5 = tau4 * tau

                # These are the basis functions (quintic polynomials) for a minimum-jerk trajectory.
                # They blend the initial and final position, velocity, and acceleration.
                h0 = 1 - 10 * tau3 + 15 * tau4 - 6 * tau5
                h1 = tau - 6 * tau3 + 8 * tau4 - 3 * tau5
                h2 = 0.5 * tau2 - 1.5 * tau3 + 1.5 * tau4 - 0.5 * tau5
                h3 = 10 * tau3 - 15 * tau4 + 6 * tau5
                h4 = -4 * tau3 + 7 * tau4 - 3 * tau5
                h5 = 0.5 * tau3 - tau4 + 0.5 * tau5

                # Calculate the smoothed position by combining the basis functions with the boundary conditions.
                smoothed_pos = h0 * x0 + h1 * v0 + h2 * a0 + h3 * xf + h4 * vf + h5 * af

                # Blend the end of the smoothed trajectory with the original target trajectory
                # to ensure a seamless continuation.
                if tau > blend_threshold:
                    blend_ratio = (tau - blend_threshold) / (1.0 - blend_threshold)
                    target_pos_at_i = (
                        next_action_chunk[joint_idx, target_chunk_index + i]
                        if (target_chunk_index + i) < next_action_chunk.shape[1]
                        else xf
                    )
                    smoothed_pos = (1 - blend_ratio) * smoothed_pos + blend_ratio * target_pos_at_i

                # Update the action chunk with the new smoothed position.
                if target_chunk_index + i < action_chunk_smoothed.shape[1]:
                    action_chunk_smoothed[joint_idx, target_chunk_index + i] = smoothed_pos
        return action_chunk_smoothed, target_chunk_index


    @run_time_decorator
    def _min_jerk_chunk_transition_numpy(self,
        next_action_chunk,
        next_vel_chunk,
        next_acc_chunk,
        next_timestamps,
        target_chunk_index,
        current_pos,
        current_vel,
        current_acc,
        joint_indices,
        blend_threshold=0.7,
        adaptive_factor=-1,
    ):
        """
        Vectorized NumPy version of minimum-jerk chunk transition.
        Keeps `_min_jerk_chunk_transition` unchanged and computes
        joint/time dimensions in parallel for better performance.
        """
        if current_pos is None or current_vel is None:
            return next_action_chunk, target_chunk_index

        target_pos = next_action_chunk[:, target_chunk_index].copy()
        target_vel = next_vel_chunk[:, target_chunk_index].copy()
        target_acc = next_acc_chunk[:, target_chunk_index].copy() if next_acc_chunk is not None else np.zeros_like(target_vel)

        pos_diff = np.linalg.norm(current_pos[joint_indices] - target_pos[joint_indices])
        vel_diff = np.linalg.norm(current_vel[joint_indices] - target_vel[joint_indices])
        acc_diff = np.linalg.norm(current_acc[joint_indices] - target_acc[joint_indices])

        base_transition = next_action_chunk.shape[1]
        if adaptive_factor < 0:
            adaptive_factor = min(1.0, 0.25 + pos_diff * 1.0 + vel_diff * 0.75 + acc_diff * 0.15)
        else:
            adaptive_factor = min(1.0, max(0.0, float(adaptive_factor)))
        transition_length = min(int(base_transition * adaptive_factor), next_action_chunk.shape[1] - target_chunk_index)

        if transition_length <= 1:
            return next_action_chunk, target_chunk_index

        action_chunk_smoothed = next_action_chunk.copy()

        dt = next_timestamps[1] - next_timestamps[0] if len(next_timestamps) > 1 else 0.005
        T = transition_length * dt

        end_index = min(target_chunk_index + transition_length - 1, next_action_chunk.shape[1] - 1)

        # Boundary conditions for selected joints, all in shape (num_joints, 1)
        x0 = current_pos[joint_indices][:, None]
        v0 = (current_vel[joint_indices] * T)[:, None]
        a0 = (current_acc[joint_indices] * T * T)[:, None]

        xf = next_action_chunk[joint_indices, end_index][:, None]
        vf = (
            (next_vel_chunk[joint_indices, end_index] * T)[:, None]
            if end_index < next_vel_chunk.shape[1]
            else np.zeros_like(xf)
        )
        af = (
            (next_acc_chunk[joint_indices, end_index] * T * T)[:, None]
            if (next_acc_chunk is not None and end_index < next_acc_chunk.shape[1])
            else np.zeros_like(xf)
        )

        # Normalized time basis in shape (1, transition_length)
        tau = np.linspace(0.0, 1.0, transition_length, dtype=next_action_chunk.dtype)[None, :]
        tau2 = tau * tau
        tau3 = tau2 * tau
        tau4 = tau3 * tau
        tau5 = tau4 * tau

        h0 = 1 - 10 * tau3 + 15 * tau4 - 6 * tau5
        h1 = tau - 6 * tau3 + 8 * tau4 - 3 * tau5
        h2 = 0.5 * tau2 - 1.5 * tau3 + 1.5 * tau4 - 0.5 * tau5
        h3 = 10 * tau3 - 15 * tau4 + 6 * tau5
        h4 = -4 * tau3 + 7 * tau4 - 3 * tau5
        h5 = 0.5 * tau3 - tau4 + 0.5 * tau5

        # Parallel compute for (num_joints, transition_length)
        smoothed_pos = h0 * x0 + h1 * v0 + h2 * a0 + h3 * xf + h4 * vf + h5 * af

        # Blend tail with original target trajectory for seamless continuation
        blend_mask = tau[0] > blend_threshold
        if np.any(blend_mask):
            blend_ratio = (tau[0, blend_mask] - blend_threshold) / (1.0 - blend_threshold)
            target_segment = next_action_chunk[
                joint_indices,
                target_chunk_index : target_chunk_index + transition_length,
            ]
            smoothed_pos[:, blend_mask] = (
                (1.0 - blend_ratio)[None, :] * smoothed_pos[:, blend_mask]
                + blend_ratio[None, :] * target_segment[:, blend_mask]
            )

        action_chunk_smoothed[
            joint_indices,
            target_chunk_index : target_chunk_index + transition_length,
        ] = smoothed_pos

        return action_chunk_smoothed, target_chunk_index


    @run_time_decorator
    def _search_smooth_action(self,
                            next_action_chunk,
                            target_chunk_index,
                            currt_action,
                            currt_vel,
                            search_length=100,
                            search_step=5
                            ):
        """
        Searches for a smooth transition point within a candidate action chunk.

        This method aims to find an index in the candidate action chunk that represents a good
        point to start a transition from the current action. It prioritizes points where the
        direction of the candidate action matches the direction of the current velocity for
        as many moving joints as possible. This helps to avoid jerky movements by ensuring
        the new action continues the current motion smoothly.

        Args:
            next_action_chunk (np.ndarray): The next action chunk that contains candidate future actions.
            target_chunk_index (int): The starting index in the action chunk from which to search for a smooth transition point.
            currt_action (np.ndarray): The current action (position) of the robot.
            currt_vel (np.ndarray): The current velocity of the robot.
            candidate_action_chunk (np.ndarray): The chunk of candidate future actions.
            search_length (int): The number of steps to search within the candidate chunk.
            search_step (int, optional): The step size for iterating through the candidate chunk. Defaults to 5.

        Returns:
            int: The index in the candidate chunk that is best suited for a smooth transition.
        """
        candidate_action_chunk = next_action_chunk[:, target_chunk_index : target_chunk_index + search_length]
        # Identify joints that are currently in motion (velocity is above a threshold).
        valid_joints = [index for index, value in enumerate(abs(currt_vel) > 5e-3) if value]
        if not valid_joints:
            # If no joints are moving, any point is fine, so start from the beginning.
            return next_action_chunk, 0

        # Filter the current state to only consider the moving joints.
        currt_action = currt_action[valid_joints]
        currt_vel = currt_vel[valid_joints]
        target_index_offset = 0
        valid_joint_num = len(valid_joints)
        qualified_joint_num = 0

        # Iterate through the candidate actions to find the best match.
        for candidate_index in range(0, search_length, search_step):
            if candidate_index >= candidate_action_chunk.shape[1]:
                break
            candidate_action = candidate_action_chunk[valid_joints, candidate_index]
            action_diff = candidate_action - currt_action
            qualified_count = 0

            # Check how many joints continue moving in the same direction.
            for index in range(valid_joint_num):
                # This condition is true if the change in action and the current velocity have the same sign.
                # It means the joint is being commanded to continue its current motion.
                if action_diff[index] * currt_vel[index] > 0.0:
                    qualified_count += 1

            # If all moving joints are qualified, we found a perfect transition point.
            if qualified_count == valid_joint_num:
                target_index_offset = candidate_index
                qualified_joint_num = qualified_count
                break

            # Otherwise, keep track of the point with the most qualified joints found so far.
            if qualified_count > qualified_joint_num:
                target_index_offset = candidate_index
                qualified_joint_num = qualified_count

        if self.logger is not None:
            self.logger.debug(f"Search smooth action: target_index_offset = {target_index_offset}, qualified dim = {qualified_joint_num}")
        return next_action_chunk, target_chunk_index + target_index_offset
