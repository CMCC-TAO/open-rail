import time
import torch
import cv2
import random
import logging
import numpy as np
from pprint import pprint
from ..base_robot import RobotBase

try:
    from lerobot.datasets.lerobot_dataset import LeRobotDataset, LeRobotDatasetMetadata
except ImportError:
    pass

class RobotBody(RobotBase):
    def __init__(self, config):
        """Initialize the mock robot body using LeRobot dataset for simulation.
        
        Args:
            config (dict): Configuration dictionary containing mock robot settings
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.cfg, self.ori_cfg = config['robots']['mock'], config
        self.current_state = np.zeros(20)
        try:
            self.dataset = LeRobotDataset(repo_id=self.cfg['repo_id'], root=self.cfg['root'])
            self.dataloader = iter(torch.utils.data.DataLoader(
                self.dataset,
                num_workers=1,
                batch_size=1,
                shuffle=False,
            ))
            # And see how many frames you have:
            self.logger.info(f"Selected episodes: {self.dataset.episodes}")
            self.logger.info(f"Number of episodes selected: {self.dataset.num_episodes}")
            self.logger.info(f"Number of frames selected: {self.dataset.num_frames}")
            self.logger.info(f"Dataset fps: {self.dataset.meta.fps}")
            self.init_timestamp = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
            self.currt_index = 0
            self.period = 1.0 / self.dataset.meta.fps # in seconds
            time.sleep(1)
        except Exception as e:
            self.dataset = None

    def control_robot(self, action):
        """Mock robot control function that simulates robot movement.
        
        Args:
            action (array-like): Action array containing robot commands (currently unused in mock)
        """
        if random.random() < 0.001:
            pass

    def retrieve_observation(self):
        """Retrieve observation data from the LeRobot dataset for simulation.
        
        Returns:
            dict: Dictionary containing camera images, joint states, and timestamp from dataset
        """
        # Use random data if dataset is not available
        if self.dataset is None:
            result = {}
            cam_names, cam_ref = self.cfg['camera']['names'], self.cfg['camera']['ref']
            image, ref_timestamp = np.random.randint(0, 256, (640, 640, 3), dtype=np.uint8), time.clock_gettime_ns(time.CLOCK_MONOTONIC)
            result['ref_timestamp'] = ref_timestamp
            result[f'cam.{cam_ref}'] = image
            for key, value in cam_names.items():
                if key == cam_ref:
                    continue
                image = np.random.randint(0, 256, (640, 640, 3), dtype=np.uint8)
                if key == 'depth_head':
                    key = 'depth.head'
                    image = np.random.randint(0, 2**16, (640, 640), dtype=np.uint16)
                result[f'cam.{key}'] = image
            result['obs.state'] = np.random.rand(20,)
            self.current_state = result['obs.state']
            return result

        start_time = time.time()
        result = {}
        if self.currt_index >= self.dataset.num_frames:
            self.logger.info(f'End of dataset, currt_index: {self.currt_index}, num_frames: {self.dataset.num_frames}')
            self.dataloader = iter(torch.utils.data.DataLoader(
                self.dataset,
                num_workers=1,
                batch_size=1,
                shuffle=False,
            ))
            self.currt_index = 0
        
        self.currt_index += 1
        data = next(self.dataloader)
        
        cam_names, cam_ref = self.cfg['camera']['names'], self.cfg['camera']['ref']
        image, ref_timestamp = (data[cam_names[cam_ref]][0].permute(1, 2, 0).cpu().numpy()* 255).astype(np.uint8), time.clock_gettime_ns(time.CLOCK_MONOTONIC)

        result['ref_timestamp'] = ref_timestamp
        result[f'cam.{cam_ref}'] = image
        for key, value in cam_names.items():
            self.logger.debug(f'mock robot camera key: {key}, value: {value}')
            if key == cam_ref:
                continue
            image = (data[value][0].permute(1, 2, 0).cpu().numpy()* 255).astype(np.uint8)
            if key == 'depth_head':
                key = 'depth.head'
            result[f'cam.{key}'] = image
    
        result['obs.state'] = data["observation.state"][0].cpu().numpy()
        self.current_state = result['obs.state']
        end_time = time.time()
        if end_time-start_time < self.period:
            sleep_time = self.period - (end_time - start_time)
            time.sleep(sleep_time)
        end_time = time.time()
        return result

    def close(self):
        """Close the mock robot and clean up resources.
        
        This method performs cleanup for the mock robot simulation.
        """
        self.logger.info('Close mock robot...')

if __name__ == '__main__':
    from conf.robots_conf import get_robots_config
    config = get_robots_config()
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
    except KeyboardInterrupt:
        robot.close()