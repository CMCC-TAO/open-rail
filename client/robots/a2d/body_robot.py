import time
import cv2
import numpy as np
from a2d_sdk.robot import RobotDds as Robot
from a2d_sdk.robot import CosineCamera as Camera
from ..base_robot import RobotBase

class RobotBody(RobotBase):
    def __init__(self, config):
        """Initialize the A2D robot body with camera and robot instances.
        
        Args:
            config (dict): Configuration dictionary containing robot and camera settings
        """
        super().__init__()
        self.cfg, self.ori_cfg = config['robots']['a2d'], config
        self.camera= Camera(list(self.cfg['camera']['names'].values()))
        self.robot = Robot()
        self.currt_timestamp = 0
        self.gripper_count = 0
        self.gripper_cmd = [0.0, 0.0]
        time.sleep(1)

    def control_robot(self, action):
        """Control the robot arm and gripper based on the given action.
        
        Args:
            action (array-like): Action array containing arm commands (0:14) and gripper commands (14:16)
        """
        self.robot.move_arm(action[0:14].tolist())
        # Count gripper value changes and send gripper command when accumulated changes reach threshold
        new_gripper_cmd = action[14:16]
        if abs(new_gripper_cmd[0] - self.gripper_cmd[0]) > 0.75 or abs(new_gripper_cmd[1] - self.gripper_cmd[1]) > 0.75:
            self.gripper_count += 1
        if self.gripper_count > self.cfg['gripper_freq']:
            self.robot.move_gripper(new_gripper_cmd.tolist())
            self.gripper_cmd = new_gripper_cmd
            self.gripper_count = 0

    def retrieve_observation(self):
        """Retrieve current observation data including camera images and joint states.
        
        Returns:
            dict or None: Dictionary containing camera images, joint states, and timestamp.
                         Returns None if no new data is available.
        """
        result = {}
        cam_names, cam_ref = self.cfg['camera']['names'], self.cfg['camera']['ref']
        image, ref_timestamp = self.camera.get_latest_image(cam_names[cam_ref])
        if self.currt_timestamp == ref_timestamp:
            return None
        else:
            self.currt_timestamp = ref_timestamp

        result['ref_timestamp'] = ref_timestamp
        result[cam_ref] = image
        for key, value in cam_names.items():
            if key == cam_ref:
                continue
            image, timestamp = self.camera.get_image_nearest(value, ref_timestamp)
            result[key] = image

        joint_states = []
        for proprio in self.cfg['proprio_names']:
            joint_states_nearest_fun = getattr(self.robot, f'{proprio}_joint_states_nearest')
            currt_joint_states, timestamp = joint_states_nearest_fun(ref_timestamp)
            joint_states.extend(currt_joint_states)
        result[f'obs.state'] = np.array(joint_states)
        return result

    def get_obs_only_state(self):
        """Get only the robot state (joint positions) without camera data.
        
        Returns:
            np.ndarray: Combined array of normalized arm and gripper joint states
        """
        # Convert protobuf format arm_states to list
        arm_states, timestamp = self.robot.arm_joint_states()
        gripper_states, timestamp = self.robot.gripper_states()
        vmin, vmax = 35, 120
        gripper_states = (np.array(list(gripper_states)) - vmin) / (vmax - vmin) # normalize
        # gripper_states = np.array(list(gripper_states)) * (vmax - vmin) + vmin # re-normalize
        return np.array(list(arm_states) + list(gripper_states))

    def close(self):
        """Close and shutdown the robot and camera connections.
        
        This method properly releases all hardware resources.
        """
        self.camera.close()
        self.robot.shutdown()
        print('close robot')

if __name__ == '__main__':
    import yaml
    with open('../../../conf/robots_conf.yaml', 'r') as file:
        config = yaml.safe_load(file)
    robot = RobotBody(config)
    try:
        while True:
            result = robot.retrieve_observation()
            if result is None:
                continue
            for key, value in result.items():
                if 'cam.' not in key:
                    continue
                if 'depth.' in key:
                    img_depth_norm = cv2.normalize(value, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                    img_show = cv2.applyColorMap(img_depth_norm, cv2.COLORMAP_JET)
                else:
                    img_show = cv2.cvtColor(value, cv2.COLOR_RGB2BGR)
                cv2.imshow(key, img_show)
                cv2.waitKey(1)
            # time.sleep(0.001)  # Control loop frequency
    except KeyboardInterrupt:
        robot.close()