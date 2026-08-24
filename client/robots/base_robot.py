import time
import cv2
import numpy as np
import logging

from client.utils.util import parse_action_layout

try:
    import ruckig
except ImportError:
    ruckig = None

# Lightweight FPS stats: number of warmup frames to discard and target FPS
# used to estimate the theoretical frame count
FPS_STATS_WARMUP_FRAMES = 5
FPS_STATS_TARGET_FPS = 30.0


class RobotBase():
    def __init__(self, config):
        self.robot = None
        self.logger = logging.getLogger(__name__)
        self.config = config
        # TODO: Make action_layout value changing tasks effects in realtime
        if not hasattr(self.config, 'action_layout'):
            self.logger.error("Parameter action_layout is required, please check the configuration.")
        self.action_layout = dict(self.config.get('action_layout', {}))
        self.action_dim, self.joint_indices, self.step_indices = parse_action_layout(self.action_layout)
        self.state_dim = max((v['end'] for v in self.action_layout.values()), default=0)
        self.current_state = np.zeros(self.state_dim)

        # Lightweight FPS stats: counters plus two timestamps only, no per-frame data
        self._fps_warmup_left = FPS_STATS_WARMUP_FRAMES
        self._fps_stats_start = None
        self._fps_last_frame_time = None
        self._fps_actual_frames = 0
        self._fps_stats_logged = False
        self._install_fps_stats()

    def control_robot(self, data):
        """
        The default robot control is the same as execute_action. You can implement it with a fine-grained strategy.
        Args:
            data: data to control robot
        """
        self.execute_action(data)

    def execute_action(self, data):
        """
        Execute action interface without strategy.
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

    def _control_robot(self, data):
        """Execute manual Web controls using current values for -1000."""
        if not isinstance(data, dict):
            raise ValueError('action data must be a dict')
        if data.get('source') != 'manual':
            raise ValueError('manual control requires source=manual')

        cfg = getattr(self, 'cfg', {})
        interval = float(cfg.get('manual_arm_interval', 0.01)) if hasattr(cfg, 'get') else 0.01

        for action in ('arm', 'gripper', 'hand', 'hand_as_gripper'):
            left, right = data.get(f'l_{action}'), data.get(f'r_{action}')
            if left is None and right is None:
                continue
            current_pose = self._current_pose(action)
            if current_pose is None:
                continue
            if current_pose.size == 0 or current_pose.size % 2:
                raise ValueError(f'{action} dimension must be positive and even')
            side_dim = current_pose.size // 2
            target_pose = self._target_pose(
                current_pose,
                list(left if left is not None else [-1000] * side_dim)
                + list(right if right is not None else [-1000] * side_dim),
            )
            if action == 'arm':
                for trajectory in self.ruckig_planning(
                    current_pose, target_pose, current_pose.size, interval
                ):
                    self.execute_action({'arm': list(trajectory)})
                    if interval > 0:
                        time.sleep(interval)
            else:
                command = cfg.get('hand_type', action) if action == 'gripper' else action
                self.execute_action({command: target_pose.tolist()})

        for action in ('head', 'waist', 'body'):
            if action not in data:
                continue
            current_pose = self._current_pose(action)
            if current_pose is not None and current_pose.size > 0:
                self.execute_action({
                    action: self._target_pose(current_pose, data[action]).tolist()
                })

        for action in ('wheel', 'leg'):
            if action in data and action in self.action_layout:
                self.execute_action({action: list(data[action])})

    def _current_pose(self, action):
        layout = self.action_layout.get(action)
        if layout is None:
            return None
        current_obs = self.retrieve_observation() # update current_state
        if current_obs is None:
            return None
        if self.current_state is None:
            raise RuntimeError('current robot state is unavailable')
        return np.asarray(self.current_state, dtype=float)[layout['start']:layout['end']].copy()

    @staticmethod
    def _target_pose(current_pose, values):
        target_pose = np.asarray(values, dtype=float).reshape(-1)
        if target_pose.size != current_pose.size or not np.all(np.isfinite(target_pose)):
            raise ValueError(f'target must contain {current_pose.size} finite values')
        keep = target_pose == -1000
        target_pose[keep] = current_pose[keep]
        return target_pose
    
    @staticmethod
    def _default_preset(presets):
        if hasattr(presets, 'get'):
            return presets.get('Default')
        return next(
            (
                preset['value']
                for preset in presets
                if preset.get('key', preset.get('name')) == 'Default'
            ),
            None,
        )

    def reset_robot(self, target_pose=None, mode='default'):
        """Reset configured actions to their Default presets."""
        data = {'source': 'manual'}
        target_pose = None if target_pose is None else np.asarray(target_pose)
        for action, layout in self.action_layout.items():
            if target_pose is not None:
                value = target_pose[layout['start']:layout['end']].tolist()
                if action in ('arm', 'gripper', 'hand', 'hand_as_gripper'):
                    middle = len(value) // 2
                    data[f'l_{action}'], data[f'r_{action}'] = value[:middle], value[middle:]
                else:
                    data[action] = value
                continue

            presets = layout.get('presets', [])
            if hasattr(presets, 'get') and ('left' in presets or 'right' in presets):
                for side in ('left', 'right'):
                    value = self._default_preset(presets.get(side, []))
                    if value is not None:
                        data[f'{side[0]}_{action}'] = value
            else:
                value = self._default_preset(presets)
                if value is not None:
                    data[action] = value

        if len(data) > 1:
            self._control_robot(data)

    def get_joint_indices(self):
        """
        Get joint indices of robot
        Returns:
            joint_indices: joint indices of robot
        """
        return self.joint_indices

    def get_step_indices(self):
        """
        Get step indices of robot
        Returns:
            step_indices: step indices of robot
        """
        return self.step_indices

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
        if ruckig is None:
            raise RuntimeError('ruckig is required for manual arm trajectory planning')
        dof = int(dof)
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
        while True:
            result = rk.update(rk_input, rk_output)
            if result < 0:
                raise RuntimeError(f'Ruckig trajectory planning failed: {result}')
            trajs.append(list(rk_output.new_position))
            if result == ruckig.Result.Finished:
                break
            rk_output.pass_to_input(rk_input)
        
        return trajs

    def close(self):
        """Release robot resources.

        ``close`` is wrapped at construction time, so the FPS stats are logged
        automatically once shutdown finishes; subclasses need not care about it.
        """
        pass

    # ------------------------------------------------------------------
    # Lightweight FPS stats
    # ------------------------------------------------------------------
    def _install_fps_stats(self):
        """Wrap ``retrieve_observation`` / ``close`` to collect FPS stats.

        One-shot wrapping on the instance, subclass implementations untouched:
        - retrieve_observation: one integer increment plus one timestamp per frame;
        - close: emits the stats log on shutdown (``finally`` keeps it on errors).
        """
        original_retrieve = self.retrieve_observation
        original_close = self.close

        def retrieve_observation(*args, **kwargs):
            obs = original_retrieve(*args, **kwargs)
            if obs is not None:
                self._record_observation_frame()
            return obs

        def close(*args, **kwargs):
            try:
                return original_close(*args, **kwargs)
            finally:
                self._log_fps_stats()

        self.retrieve_observation = retrieve_observation
        self.close = close

    def _record_observation_frame(self):
        """Record one observation frame: start timing once the first N frames are discarded."""
        if self._fps_warmup_left > 0:
            self._fps_warmup_left -= 1
            if self._fps_warmup_left == 0:
                self._fps_stats_start = time.perf_counter()
            return
        self._fps_actual_frames += 1
        self._fps_last_frame_time = time.perf_counter()

    def _log_fps_stats(self):
        """Log runtime, theoretical frames, actual frames and drop rate on close."""
        if self._fps_stats_logged:
            return
        self._fps_stats_logged = True

        if self._fps_stats_start is None:
            self.logger.info('[FPS stats] fewer than %d observation frames collected '
                             '(warmup frames not fully discarded), no stats available',
                             FPS_STATS_WARMUP_FRAMES)
            return

        elapsed = (self._fps_last_frame_time or time.perf_counter()) - self._fps_stats_start
        actual_frames = self._fps_actual_frames
        theoretical_frames = elapsed * FPS_STATS_TARGET_FPS
        # Clamped at 0: a negative value would only mean the observation rate is
        # above the target FPS, which is not a frame drop.
        dropped_frames = max(theoretical_frames - actual_frames, 0.0)
        drop_rate = (dropped_frames / theoretical_frames * 100.0) if theoretical_frames > 0 else 0.0
        self.logger.info(
            '[FPS stats] after discarding first %d frames: runtime=%.3fs | '
            'theoretical_frames=%.1f (%g FPS) | actual_frames=%d | drop_rate=%.2f%%',
            FPS_STATS_WARMUP_FRAMES, elapsed, theoretical_frames,
            FPS_STATS_TARGET_FPS, actual_frames, drop_rate,
        )
