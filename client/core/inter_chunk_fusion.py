import numpy as np


class InterChunkFusion:
    """Inter-chunk fusion utilities for action trajectory transition."""

    def __init__(self, manager):
        self.manager = manager
        self.logger = manager.logger

    def _get_joint_indices(self, action_chunk):
        if self.manager.joint_indices:
            return self.manager.joint_indices
        return list(range(action_chunk.shape[0]))

    def poly_chunk_transition(self, new_action_chunk, new_vel_chunk, new_timestamps, target_index, current_index):
        if self.manager.action_chunk_fitted is None or self.manager.vel_chunk_fitted is None:
            return new_action_chunk

        with self.manager.polynomial_thread_lock:
            current_pos = self.manager.action_chunk_fitted[:, self.manager.action_chunk_index]
            current_vel = self.manager.vel_chunk_fitted[:, self.manager.action_chunk_index]

        if self.manager.action_chunk_index > 0:
            prev_vel = self.manager.vel_chunk_fitted[:, self.manager.action_chunk_index - 1]
            dt = self.manager.timestamps_fitted[self.manager.action_chunk_index] - self.manager.timestamps_fitted[self.manager.action_chunk_index - 1]
            current_acc = (current_vel - prev_vel) / dt if dt > 0 else np.zeros_like(current_vel)
        else:
            current_acc = np.zeros_like(current_vel)

        new_vel = new_vel_chunk[:, target_index]

        if target_index < new_vel_chunk.shape[1] - 1:
            next_vel = new_vel_chunk[:, target_index + 1]
            dt = new_timestamps[target_index + 1] - new_timestamps[target_index]
            new_acc = (next_vel - new_vel) / dt if dt > 0 else np.zeros_like(new_vel)
        else:
            new_acc = np.zeros_like(new_vel)

        transition_length = min(new_action_chunk.shape[1] // 2, new_action_chunk.shape[1] - target_index)
        if transition_length <= 1:
            return new_action_chunk

        smoothed_chunk = new_action_chunk.copy()
        end_index = target_index + transition_length - 1
        joint_indices = self._get_joint_indices(new_action_chunk)
        for joint_idx in joint_indices:
            p0, v0, a0 = current_pos[joint_idx], current_vel[joint_idx], current_acc[joint_idx]
            pf = new_action_chunk[joint_idx, end_index]
            vf = new_vel_chunk[joint_idx, end_index]
            af = new_acc[joint_idx] if end_index < len(new_acc) else 0.0

            t_transition = np.linspace(0, 1, transition_length)

            A = np.array([
                [1, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0],
                [0, 0, 2, 0, 0, 0],
                [1, 1, 1, 1, 1, 1],
                [0, 1, 2, 3, 4, 5],
                [0, 0, 2, 6, 12, 20]
            ])

            b = np.array([p0, v0, a0, pf, vf, af])

            try:
                coeffs = np.linalg.solve(A, b)
                for i, t in enumerate(t_transition):
                    smoothed_pos = (coeffs[0] + coeffs[1] * t + coeffs[2] * t ** 2 +
                                    coeffs[3] * t ** 3 + coeffs[4] * t ** 4 + coeffs[5] * t ** 5)
                    smoothed_chunk[joint_idx, target_index + i] = smoothed_pos

            except np.linalg.LinAlgError:
                print(f"Singular matrix for joint {joint_idx}, using cubic interpolation")
                for i, t in enumerate(t_transition):
                    h00 = 2 * t ** 3 - 3 * t ** 2 + 1
                    h10 = t ** 3 - 2 * t ** 2 + t
                    h01 = -2 * t ** 3 + 3 * t ** 2
                    h11 = t ** 3 - t ** 2

                    smoothed_pos = h00 * p0 + h10 * v0 + h01 * pf + h11 * vf
                    smoothed_chunk[joint_idx, target_index + i] = smoothed_pos

        return smoothed_chunk

    def min_jerk_chunk_transition(self, new_action_chunk, new_vel_chunk, new_acc_chunk, new_timestamps, target_index, current_index):
        if self.manager.action_chunk_fitted is None or self.manager.vel_chunk_fitted is None:
            return new_action_chunk

        with self.manager.polynomial_thread_lock:
            current_pos = self.manager.action_chunk_fitted[:, self.manager.action_chunk_index].copy()
            current_vel = self.manager.vel_chunk_fitted[:, self.manager.action_chunk_index].copy()
            current_acc = self.manager.acc_chunk_fitted[:, self.manager.action_chunk_index].copy() if self.manager.acc_chunk_fitted is not None else np.zeros_like(current_vel)

        target_pos = new_action_chunk[:, target_index].copy()
        target_vel = new_vel_chunk[:, target_index].copy()
        target_acc = new_acc_chunk[:, target_index].copy() if new_acc_chunk is not None else np.zeros_like(target_vel)

        joint_indices = self._get_joint_indices(new_action_chunk)
        pos_diff = np.linalg.norm(current_pos[joint_indices] - target_pos[joint_indices])
        vel_diff = np.linalg.norm(current_vel[joint_indices] - target_vel[joint_indices])
        acc_diff = np.linalg.norm(current_acc[joint_indices] - target_acc[joint_indices])

        base_transition = new_action_chunk.shape[1] // 2
        adaptive_factor = min(2.0, 0.5 + pos_diff * 2.0 + vel_diff * 1.5 + acc_diff * 0.3)
        transition_length = min(int(base_transition * adaptive_factor), new_action_chunk.shape[1] - target_index)

        if transition_length <= 1:
            return new_action_chunk

        smoothed_chunk = new_action_chunk.copy()

        dt = new_timestamps[1] - new_timestamps[0] if len(new_timestamps) > 1 else 0.005
        T = transition_length * dt

        end_index = min(target_index + transition_length - 1, new_action_chunk.shape[1] - 1)

        for joint_idx in joint_indices:
            x0 = current_pos[joint_idx]
            v0 = current_vel[joint_idx] * T
            a0 = current_acc[joint_idx] * T * T

            xf = new_action_chunk[joint_idx, end_index]
            vf = new_vel_chunk[joint_idx, end_index] * T if end_index < new_vel_chunk.shape[1] else 0.0
            af = (new_acc_chunk[joint_idx, end_index] * T * T) if (new_acc_chunk is not None and end_index < new_acc_chunk.shape[1]) else 0.0

            for i in range(transition_length):
                tau = i / (transition_length - 1) if transition_length > 1 else 1.0
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

                smoothed_pos = h0 * x0 + h1 * v0 + h2 * a0 + h3 * xf + h4 * vf + h5 * af

                blend_start = 0.7
                if tau > blend_start:
                    blend_ratio = (tau - blend_start) / (1.0 - blend_start)
                    target_pos_at_i = new_action_chunk[joint_idx, target_index + i] if (target_index + i) < new_action_chunk.shape[1] else xf
                    smoothed_pos = (1 - blend_ratio) * smoothed_pos + blend_ratio * target_pos_at_i

                if target_index + i < smoothed_chunk.shape[1]:
                    smoothed_chunk[joint_idx, target_index + i] = smoothed_pos

        return smoothed_chunk

    def bspline_chunk_transition(self, new_action_chunk, new_vel_chunk, new_timestamps, target_index, current_index, num_control_points=6):
        from scipy.interpolate import make_interp_spline

        if self.manager.action_chunk_fitted is None:
            return new_action_chunk

        with self.manager.polynomial_thread_lock:
            current_pos = self.manager.action_chunk_fitted[:, self.manager.action_chunk_index].copy()
            current_vel = self.manager.vel_chunk_fitted[:, self.manager.action_chunk_index].copy()

        transition_length = min(new_action_chunk.shape[1] // 3, new_action_chunk.shape[1] - target_index)

        if transition_length <= 3:
            return new_action_chunk

        smoothed_chunk = new_action_chunk.copy()
        dt = new_timestamps[1] - new_timestamps[0] if len(new_timestamps) > 1 else 0.005

        control_indices = np.linspace(0, transition_length - 1, num_control_points).astype(int)

        for joint_idx in range(min(14, new_action_chunk.shape[0])):
            control_points = []
            control_times = []

            control_points.append(current_pos[joint_idx])
            control_times.append(0.0)

            for i, idx in enumerate(control_indices[1:], 1):
                actual_idx = min(target_index + idx, new_action_chunk.shape[1] - 1)
                control_points.append(new_action_chunk[joint_idx, actual_idx])
                control_times.append(idx * dt)

            control_points = np.array(control_points)
            control_times = np.array(control_times)

            try:
                bc_type = ((1, current_vel[joint_idx]), (1, new_vel_chunk[joint_idx, min(target_index + transition_length - 1, new_vel_chunk.shape[1] - 1)]))
                spline = make_interp_spline(control_times, control_points, k=3, bc_type=bc_type)

                sample_times = np.linspace(0, control_times[-1], transition_length)
                smoothed_positions = spline(sample_times)

                for i in range(transition_length):
                    if target_index + i < smoothed_chunk.shape[1]:
                        smoothed_chunk[joint_idx, target_index + i] = smoothed_positions[i]

            except Exception as e:
                self.logger.warning(f"B-Spline failed for joint {joint_idx}: {e}, using linear interpolation")
                for i in range(transition_length):
                    t = i / (transition_length - 1) if transition_length > 1 else 1.0
                    target_idx = min(target_index + transition_length - 1, new_action_chunk.shape[1] - 1)
                    if target_index + i < smoothed_chunk.shape[1]:
                        smoothed_chunk[joint_idx, target_index + i] = (1 - t) * current_pos[joint_idx] + t * new_action_chunk[joint_idx, target_idx]

        return smoothed_chunk

    def search_smooth_action(self, currt_action, currt_vel, candidate_action_chunk, search_length):
        valid_joints = [index for index, value in enumerate(abs(currt_vel) > 5e-3) if value]
        currt_action = currt_action[valid_joints]
        currt_vel = currt_vel[valid_joints]
        target_index = 0
        valid_joint_num = len(valid_joints)
        qualified_joint_num = 0

        for candidate_index in range(0, search_length, 5):
            if candidate_index >= candidate_action_chunk.shape[1]:
                break
            candidate_action = candidate_action_chunk[valid_joints, candidate_index]
            action_diff = candidate_action - currt_action
            qualified_count = 0

            for index in range(valid_joint_num):
                if action_diff[index] * currt_vel[index] > 0.0:
                    qualified_count += 1

            if qualified_count == valid_joint_num:
                target_index = candidate_index
                qualified_joint_num = qualified_count
                break
            else:
                if qualified_count > qualified_joint_num:
                    target_index = candidate_index
                    qualified_joint_num = qualified_count

        self.logger.debug(f'target_index: {target_index}, qualified dim: {qualified_joint_num}')
        return target_index
