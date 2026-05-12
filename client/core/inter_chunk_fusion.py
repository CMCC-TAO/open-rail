import numpy as np
from numba import njit


@njit(fastmath=True, cache=True)
def _smooth_velocity_transition_numba(joint_seq, init_pos, init_vel, init_acc, dt=0.005, max_vel=2.0, max_acc=5.0, kp=5.0, kd=2.0):
    """
        This strategy uses position error and velocity feedback to compute acceleration in real time, generating a continuous and smooth velocity sequence.
        Note: Under the same parameter settings, the robot's operation speed using this strategy is slower than 'search_action' and 'poly'. 
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
        joint_seq : ndarray of shape (dof, T)
            Target joint position sequence to be tracked.
        init_pos : ndarray of shape (dof,)
            Initial joint positions.
        init_vel : ndarray of shape (dof,)
            Initial joint velocities.
        init_acc : ndarray of shape (dof,)
            Initial joint accelerations.
        dt : float, optional
            Time step for discrete integration.
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
    dof, T = joint_seq.shape

    pos = init_pos.copy()
    vel = init_vel.copy()
    acc = init_acc.copy()

    pos_seq = np.zeros((dof, T))
    vel_seq = np.zeros((dof, T))
    acc_seq = np.zeros((dof, T))

    for i in range(T):
        target = joint_seq[:, i]
        for j in range(dof):
            acc[j] = kp * (target[j] - pos[j]) - kd * vel[j]

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

    return pos_seq, vel_seq, acc_seq


class InterChunkFusion:
    """Independent inter-chunk fusion utilities for action trajectory transition."""

    def __init__(self, logger=None):
        self.logger = logger

    @staticmethod
    def smooth_velocity_transition_numba(joint_seq, init_pos, init_vel, init_acc, dt=0.005, max_vel=2.0, max_acc=5.0, kp=5.0, kd=2.0):
        return _smooth_velocity_transition_numba(joint_seq, init_pos, init_vel, init_acc, dt, max_vel, max_acc, kp, kd)

    @staticmethod
    def _get_joint_indices(action_chunk, joint_indices=None):
        if joint_indices:
            return joint_indices
        return list(range(action_chunk.shape[0]))

    def poly_chunk_transition(
        self,
        new_action_chunk,
        new_vel_chunk,
        new_timestamps,
        target_index,
        current_pos,
        current_vel,
        current_acc,
        joint_indices=None,
    ):
        """
        Smooths the transition to a new action chunk using a quintic polynomial.

        This method creates a trajectory that matches the position, velocity, and acceleration
        at both the start (current state) and end (a point in the new chunk) of the transition.
        It solves a system of linear equations to find the coefficients of a 5th-degree
        polynomial that satisfies these boundary conditions. This ensures a C2-continuous
        transition. If solving fails (e.g., due to a singular matrix), it falls back to a
        cubic Hermite spline which only matches position and velocity.

        Args:
            new_action_chunk (np.ndarray): The upcoming chunk of actions (positions).
            new_vel_chunk (np.ndarray): The upcoming chunk of velocities.
            new_timestamps (np.ndarray): Timestamps corresponding to the action chunk.
            target_index (int): The index in the new_action_chunk where the transition should start.
            current_pos (np.ndarray): The current position of the robot joints.
            current_vel (np.ndarray): The current velocity of the robot joints.
            current_acc (np.ndarray): The current acceleration of the robot joints.
            joint_indices (list, optional): Indices of the joints to apply the transition to.
                                            If None, applies to all joints. Defaults to None.

        Returns:
            np.ndarray: The action chunk with the smoothed transition applied.
        """
        if current_pos is None or current_vel is None:
            return new_action_chunk

        # Estimate the acceleration at the target index using finite differences.
        new_vel = new_vel_chunk[:, target_index]
        if target_index < new_vel_chunk.shape[1] - 1:
            next_vel = new_vel_chunk[:, target_index + 1]
            dt = new_timestamps[target_index + 1] - new_timestamps[target_index]
            new_acc = (next_vel - new_vel) / dt if dt > 0 else np.zeros_like(new_vel)
        else:
            new_acc = np.zeros_like(new_vel)

        # Determine the length of the transition period.
        transition_length = min(new_action_chunk.shape[1] // 2, new_action_chunk.shape[1] - target_index)
        if transition_length <= 1:
            return new_action_chunk

        smoothed_chunk = new_action_chunk.copy()
        end_index = target_index + transition_length - 1
        resolved_joint_indices = self._get_joint_indices(new_action_chunk, joint_indices)

        # Generate the trajectory for each joint.
        for joint_idx in resolved_joint_indices:
            # Define initial and final boundary conditions.
            p0, v0, a0 = current_pos[joint_idx], current_vel[joint_idx], current_acc[joint_idx]
            pf = new_action_chunk[joint_idx, end_index]
            vf = new_vel_chunk[joint_idx, end_index]
            af = new_acc[joint_idx] if end_index < len(new_acc) else 0.0

            # Normalize time for the transition to be from t=0 to t=1.
            t_transition = np.linspace(0, 1, transition_length)

            # The matrix 'A' is derived from the quintic polynomial p(t) = c0 + c1*t + ... + c5*t^5
            # and its derivatives p'(t) and p''(t), evaluated at t=0 and t=1.
            # This sets up a system of linear equations to solve for the coefficients [c0, ..., c5].
            A = np.array(
                [
                    [1, 0, 0, 0, 0, 0],  # p(0) = p0
                    [0, 1, 0, 0, 0, 0],  # p'(0) = v0
                    [0, 0, 2, 0, 0, 0],  # p''(0) = a0
                    [1, 1, 1, 1, 1, 1],  # p(1) = pf
                    [0, 1, 2, 3, 4, 5],  # p'(1) = vf
                    [0, 0, 2, 6, 12, 20],  # p''(1) = af
                ]
            )

            # The vector 'b' contains the desired boundary conditions.
            b = np.array([p0, v0, a0, pf, vf, af])

            try:
                # Solve the system A * coeffs = b to find the polynomial coefficients.
                coeffs = np.linalg.solve(A, b)
                for i, t in enumerate(t_transition):
                    # Evaluate the polynomial at time t to get the smoothed position.
                    smoothed_pos = (
                        coeffs[0]
                        + coeffs[1] * t
                        + coeffs[2] * t**2
                        + coeffs[3] * t**3
                        + coeffs[4] * t**4
                        + coeffs[5] * t**5
                    )
                    smoothed_chunk[joint_idx, target_index + i] = smoothed_pos

            except np.linalg.LinAlgError:
                # If the matrix A is singular, quintic solution is not possible.
                # Fall back to a cubic Hermite spline, which matches only position and velocity.
                if self.logger is not None:
                    self.logger.warning(f"Singular matrix for joint {joint_idx}, using cubic interpolation")
                for i, t in enumerate(t_transition):
                    # Hermite basis functions for cubic interpolation.
                    h00 = 2 * t**3 - 3 * t**2 + 1
                    h10 = t**3 - 2 * t**2 + t
                    h01 = -2 * t**3 + 3 * t**2
                    h11 = t**3 - t**2

                    # Interpolate using the initial/final position and velocity.
                    smoothed_pos = h00 * p0 + h10 * v0 + h01 * pf + h11 * vf
                    smoothed_chunk[joint_idx, target_index + i] = smoothed_pos

        return smoothed_chunk

    def min_jerk_chunk_transition(
        self,
        new_action_chunk,
        new_vel_chunk,
        new_acc_chunk,
        new_timestamps,
        target_index,
        current_pos,
        current_vel,
        current_acc,
        joint_indices=None,
    ):
        """
        Smooths the transition to a new action chunk using a minimum-jerk trajectory.

        This method generates a smooth path from the current robot state (position, velocity,
        and acceleration) to a target state within the new action chunk. The trajectory
        is a quintic polynomial that minimizes jerk (the third derivative of position),
        resulting in a very smooth and natural-looking motion. The transition length is
        adaptively determined based on the difference between the current and target states.

        Args:
            new_action_chunk (np.ndarray): The upcoming chunk of actions (positions).
            new_vel_chunk (np.ndarray): The upcoming chunk of velocities.
            new_acc_chunk (np.ndarray): The upcoming chunk of accelerations.
            new_timestamps (np.ndarray): Timestamps corresponding to the action chunk.
            target_index (int): The index in the new_action_chunk where the transition should start.
            current_pos (np.ndarray): The current position of the robot joints.
            current_vel (np.ndarray): The current velocity of the robot joints.
            current_acc (np.ndarray): The current acceleration of the robot joints.
            joint_indices (list, optional): Indices of the joints to apply the transition to.
                                            If None, applies to all joints. Defaults to None.

        Returns:
            np.ndarray: The action chunk with the smoothed transition applied.
        """
        if current_pos is None or current_vel is None:
            return new_action_chunk

        # Define the target state for the transition.
        target_pos = new_action_chunk[:, target_index].copy()
        target_vel = new_vel_chunk[:, target_index].copy()
        target_acc = new_acc_chunk[:, target_index].copy() if new_acc_chunk is not None else np.zeros_like(target_vel)

        # Determine which joints to apply the smoothing to.
        resolved_joint_indices = self._get_joint_indices(new_action_chunk, joint_indices)

        # Calculate the difference (magnitude) between current and target states.
        pos_diff = np.linalg.norm(current_pos[resolved_joint_indices] - target_pos[resolved_joint_indices])
        vel_diff = np.linalg.norm(current_vel[resolved_joint_indices] - target_vel[resolved_joint_indices])
        acc_diff = np.linalg.norm(current_acc[resolved_joint_indices] - target_acc[resolved_joint_indices])

        # Adaptively determine the transition length based on the state differences.
        # A larger difference results in a longer transition.
        base_transition = new_action_chunk.shape[1] // 2
        adaptive_factor = min(2.0, 0.5 + pos_diff * 2.0 + vel_diff * 1.5 + acc_diff * 0.3)
        transition_length = min(int(base_transition * adaptive_factor), new_action_chunk.shape[1] - target_index)

        # If the transition is too short, skip smoothing.
        if transition_length <= 1:
            return new_action_chunk

        smoothed_chunk = new_action_chunk.copy()

        # Calculate time step (dt) and total transition duration (T).
        dt = new_timestamps[1] - new_timestamps[0] if len(new_timestamps) > 1 else 0.005
        T = transition_length * dt

        # Determine the end index for the transition within the chunk.
        end_index = min(target_index + transition_length - 1, new_action_chunk.shape[1] - 1)

        # Generate the trajectory for each joint.
        for joint_idx in resolved_joint_indices:
            # Define initial conditions (at tau=0).
            x0 = current_pos[joint_idx]
            v0 = current_vel[joint_idx] * T  # Scale velocity by T for normalized time.
            a0 = current_acc[joint_idx] * T * T  # Scale acceleration by T^2 for normalized time.

            # Define final conditions (at tau=1).
            xf = new_action_chunk[joint_idx, end_index]
            vf = new_vel_chunk[joint_idx, end_index] * T if end_index < new_vel_chunk.shape[1] else 0.0
            af = (
                (new_acc_chunk[joint_idx, end_index] * T * T)
                if (new_acc_chunk is not None and end_index < new_acc_chunk.shape[1])
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
                blend_start = 0.7
                if tau > blend_start:
                    blend_ratio = (tau - blend_start) / (1.0 - blend_start)
                    target_pos_at_i = (
                        new_action_chunk[joint_idx, target_index + i]
                        if (target_index + i) < new_action_chunk.shape[1]
                        else xf
                    )
                    smoothed_pos = (1 - blend_ratio) * smoothed_pos + blend_ratio * target_pos_at_i

                # Update the action chunk with the new smoothed position.
                if target_index + i < smoothed_chunk.shape[1]:
                    smoothed_chunk[joint_idx, target_index + i] = smoothed_pos

        return smoothed_chunk

    def bspline_chunk_transition(
        self,
        new_action_chunk,
        new_vel_chunk,
        new_timestamps,
        target_index,
        current_pos,
        current_vel,
        num_control_points=6,
    ):
        """
        Smooths the transition between the current state and a new action chunk using a B-spline.

        This method creates a smooth trajectory from the current robot position to the beginning of a new
        action sequence. It uses a B-spline interpolation to generate a transition that respects
        velocity constraints at the boundaries, ensuring a physically plausible and smooth motion.
        If spline generation fails, it falls back to linear interpolation.

        Args:
            new_action_chunk (np.ndarray): The upcoming chunk of actions (positions).
            new_vel_chunk (np.ndarray): The upcoming chunk of velocities.
            new_timestamps (np.ndarray): Timestamps corresponding to the action chunk.
            target_index (int): The index in the new_action_chunk where the transition should start.
            current_pos (np.ndarray): The current position of the robot joints.
            current_vel (np.ndarray): The current velocity of the robot joints.
            num_control_points (int, optional): The number of control points to use for the spline.
                                               Defaults to 6.

        Returns:
            np.ndarray: The action chunk with a smoothed transition applied.
        """
        from scipy.interpolate import make_interp_spline

        # If there's no current position, no transition can be made.
        if current_pos is None:
            return new_action_chunk

        # Determine the length of the transition. It's a fraction of the chunk size,
        # but not longer than the remaining part of the chunk.
        transition_length = min(new_action_chunk.shape[1] // 3, new_action_chunk.shape[1] - target_index)

        # If the transition is too short, it's not worth smoothing.
        if transition_length <= 3:
            return new_action_chunk

        smoothed_chunk = new_action_chunk.copy()
        dt = new_timestamps[1] - new_timestamps[0] if len(new_timestamps) > 1 else 0.005

        # Select indices for control points, spaced evenly through the transition period.
        control_indices = np.linspace(0, transition_length - 1, num_control_points).astype(int)

        # Apply smoothing for each joint independently.
        for joint_idx in range(min(14, new_action_chunk.shape[0])):
            control_points = []
            control_times = []

            # The first control point is the current position at time 0.
            control_points.append(current_pos[joint_idx])
            control_times.append(0.0)

            # Subsequent control points are sampled from the new action chunk.
            for idx in control_indices[1:]:
                actual_idx = min(target_index + idx, new_action_chunk.shape[1] - 1)
                control_points.append(new_action_chunk[joint_idx, actual_idx])
                control_times.append(idx * dt)

            control_points = np.array(control_points)
            control_times = np.array(control_times)

            try:
                # Create a cubic B-spline (k=3).
                # We set boundary conditions (bc_type) for the derivatives (velocity).
                # The start velocity is the current velocity, and the end velocity is taken
                # from the new velocity chunk at the end of the transition.
                bc_type = (
                    (1, current_vel[joint_idx]),  # (1, v) means 1st derivative is v
                    (1, new_vel_chunk[joint_idx, min(target_index + transition_length - 1, new_vel_chunk.shape[1] - 1)]),
                )
                spline = make_interp_spline(control_times, control_points, k=3, bc_type=bc_type)

                # Sample the spline to get the smoothed trajectory for the transition period.
                sample_times = np.linspace(0, control_times[-1], transition_length)
                smoothed_positions = spline(sample_times)

                # Replace the original action chunk with the new smoothed positions.
                for i in range(transition_length):
                    if target_index + i < smoothed_chunk.shape[1]:
                        smoothed_chunk[joint_idx, target_index + i] = smoothed_positions[i]

            except Exception as e:
                # If B-spline creation fails, fall back to simple linear interpolation.
                # TODO: Fix this exception
                if self.logger is not None:
                    self.logger.warning(f"B-Spline failed for joint {joint_idx}: {e}, using linear interpolation")
                for i in range(transition_length):
                    t = i / (transition_length - 1) if transition_length > 1 else 1.0
                    target_idx = min(target_index + transition_length - 1, new_action_chunk.shape[1] - 1)
                    if target_index + i < smoothed_chunk.shape[1]:
                        # Interpolate from current position to the target position at the end of the transition.
                        smoothed_chunk[joint_idx, target_index + i] = (1 - t) * current_pos[joint_idx] + t * new_action_chunk[joint_idx, target_idx]

        return smoothed_chunk

    def search_smooth_action(self, currt_action, currt_vel, candidate_action_chunk, search_length):
        """
        Searches for a smooth transition point within a candidate action chunk.

        This method aims to find an index in the candidate action chunk that represents a good
        point to start a transition from the current action. It prioritizes points where the
        direction of the candidate action matches the direction of the current velocity for
        as many moving joints as possible. This helps to avoid jerky movements by ensuring
        the new action continues the current motion smoothly.

        Args:
            currt_action (np.ndarray): The current action (position) of the robot.
            currt_vel (np.ndarray): The current velocity of the robot.
            candidate_action_chunk (np.ndarray): The chunk of candidate future actions.
            search_length (int): The number of steps to search within the candidate chunk.

        Returns:
            int: The index in the candidate chunk that is best suited for a smooth transition.
        """
        # Identify joints that are currently in motion (velocity is above a threshold).
        valid_joints = [index for index, value in enumerate(abs(currt_vel) > 5e-3) if value]
        if not valid_joints:
            # If no joints are moving, any point is fine, so start from the beginning.
            return 0

        # Filter the current state to only consider the moving joints.
        currt_action = currt_action[valid_joints]
        currt_vel = currt_vel[valid_joints]
        target_index = 0
        valid_joint_num = len(valid_joints)
        qualified_joint_num = 0

        # Iterate through the candidate actions to find the best match.
        for candidate_index in range(0, search_length, 5):
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
                target_index = candidate_index
                qualified_joint_num = qualified_count
                break

            # Otherwise, keep track of the point with the most qualified joints found so far.
            if qualified_count > qualified_joint_num:
                target_index = candidate_index
                qualified_joint_num = qualified_count

        if self.logger is not None:
            self.logger.debug(f"target_index: {target_index}, qualified dim: {qualified_joint_num}")
        return target_index