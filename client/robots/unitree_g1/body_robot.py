import time
import logging
import numpy as np

from ..base_robot import RobotBase


class RobotBody(RobotBase):
    """Template robot adapter for Unitree G1.

    This file is intentionally kept close to the style of existing robot adapters.
    Replace TODO blocks with your real G1 SDK integration.
    """

    def __init__(self, config):
        """Initialize Unitree G1 robot adapter.

        Args:
            config (dict): Full project config.
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.cfg, self.ori_cfg = config['robots']['unitree_g1'], config
        self.action_layout = dict(self.cfg.get('action_layout', {}))
        self.action_dim = max([v['end'] for v in self.action_layout.values()]) if self.action_layout else 0

        self.current_state = np.zeros(self.action_dim, dtype=np.float32)
        self.current_timestamp = 0

        self.gripper_count = 0
        self.head_count = 0

        # TODO(unitree_g1): Initialize your G1 SDK objects here.
        # Example placeholders:
        # self.camera = YourG1CameraSDK(...)
        # self.robot = YourG1ControlSDK(...)
        self.camera = None
        self.robot = None

        self.logger.info('Unitree G1 RobotBody initialized (template mode).')

    def control_robot(self, action):
        """Control robot by splitting full action vector using action_layout.

        Args:
            action (array-like): Full action vector from controller.
        """
        action = np.asarray(action)
        segments = {name: action[v['start']:v['end']] for name, v in self.action_layout.items()}

        # Keep same calling style as a2d implementation.
        if 'arm' in segments:
            self.execute_action({'arm': segments['arm'].tolist()})

        if 'gripper' in segments and self.gripper_count % self.cfg.get('gripper_freq', 1) == 0:
            self.gripper_count = 0
            self.execute_action({'gripper': segments['gripper'].tolist()})
        self.gripper_count += 1

        if 'head' in segments and self.head_count % self.cfg.get('head_freq', 1) == 0:
            self.head_count = 0
            self.execute_action({'head': segments['head'].tolist()})
        self.head_count += 1

        if 'waist' in segments:
            self.execute_action({'waist': segments['waist'].tolist()})

        if 'wheel' in segments:
            self.execute_action({'wheel': segments['wheel'].tolist()})

    def execute_action(self, data):
        """Execute low-level action command with your G1 SDK.

        Args:
            data (dict): Action dictionary, e.g. {'arm': [...], 'gripper': [...]}.
        """
        # TODO(unitree_g1): Map these keys to your real SDK APIs.
        # Suggested mapping style (example only):
        # if 'arm' in data:
        #     self.robot.move_arm(data['arm'])
        # if 'gripper' in data:
        #     self.robot.move_gripper(data['gripper'])
        # if 'head' in data:
        #     self.robot.move_head(data['head'])
        # if 'waist' in data:
        #     self.robot.move_waist(data['waist'])
        # if 'wheel' in data:
        #     self.robot.move_wheel(data['wheel'][0], data['wheel'][1])
        if self.robot is None:
            self.logger.debug(f'execute_action skipped (template mode), data keys: {list(data.keys())}')

    def reset_robot(self, target_pose=None, mode='default'):
        """Reset robot to safe/default pose.

        Args:
            target_pose (array-like | None): Target pose.
            mode (str): Reset mode.
        """
        if target_pose is None:
            if mode == 'default':
                target_pose = np.array(self.cfg.get('reset_robot_pos', []), dtype=np.float32)
            elif mode == 'zero':
                target_pose = np.zeros(self.action_dim, dtype=np.float32)
            else:
                self.logger.warning('target_pose is None and mode is unsupported, skip reset.')
                return
        else:
            target_pose = np.array(target_pose, dtype=np.float32)

        # TODO(unitree_g1): Implement smooth reset with real SDK if needed.
        # You can also reuse self.ruckig_planning(...) for arm joints.
        self.current_state = target_pose.copy()

        segments = {name: target_pose[v['start']:v['end']] for name, v in self.action_layout.items()}
        if 'arm' in segments:
            self.execute_action({'arm': segments['arm'].tolist()})
        if 'gripper' in segments:
            self.execute_action({'gripper': segments['gripper'].tolist()})
        if 'head' in segments:
            self.execute_action({'head': segments['head'].tolist()})
        if 'waist' in segments:
            self.execute_action({'waist': segments['waist'].tolist()})

    def retrieve_observation(self):
        """Retrieve observation from Unitree G1 SDK.

        Returns:
            dict or None: Must follow framework contract:
                - ref_timestamp
                - cam.<name> image arrays
                - obs.state numpy array
        """
        # TODO(unitree_g1): Read synchronized camera frames and robot state from your SDK.
        # Contract example:
        # result = {
        #     'ref_timestamp': ref_timestamp,
        #     'cam.head': image_head,
        #     'cam.hand_left': image_left,
        #     'cam.hand_right': image_right,
        #     'obs.state': np.array(joint_states, dtype=np.float32),
        # }
        # return result

        # Template fallback: return None when no SDK data source is wired yet.
        return None

    def close(self):
        """Release hardware resources."""
        # TODO(unitree_g1): Close camera/robot SDK sessions here.
        self.logger.info('Close Unitree G1 robot (template mode).')


if __name__ == '__main__':
    from conf.robots_conf import get_robots_config

    cfg = get_robots_config()
    robot = RobotBody(cfg)
    try:
        while True:
            obs = robot.retrieve_observation()
            if obs is None:
                time.sleep(0.01)
                continue
            print(f"obs keys: {list(obs.keys())}")
    except KeyboardInterrupt:
        robot.close()
