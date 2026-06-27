import time
import cv2
import numpy as np
import pandas as pd
from .Ti5Robot import Ti5Robot as Robot
from .Ti5Camera import Ti5Camera as Camera

from ..base_robot import RobotBase

import logging
import rclpy
import threading

class RobotBody(RobotBase):
    def __init__(self, config):
        """Initialize the Ti5_T170C robot body with camera and robot instances.
        
        Args:
            config (dict): Configuration dictionary containing robot and camera settings
        """
        super().__init__(config)
        self.cfg = config
        self.logger = logging.getLogger(__name__)
        
        # ============================================
        # Initialize rclpy and then create a ROS node
        # ============================================
        if not rclpy.ok():
            rclpy.init()

        # ============================================
        # Initialize Ti5 Robot & Camera Nodes
        # ============================================
        self.camera = Camera(self.cfg)
        self.robot = Robot(self.cfg)

        # =========================
        # Unified ROS Spinning
        # =========================
        self.running = True
        self._start_spin_thread()

        # =========================
        # Gripper State Cache
        # =========================
        self.gripper_cmd = np.zeros(2)
        self.gripper_count = 0
        self.current_timestamp = 0
        self.current_state = None
        
        self.logger.info("✅ RobotBody initialization completed!")
        time.sleep(2.0)


    def _start_spin_thread(self):
        def spin_worker():
            while self.running:
                rclpy.spin_once(self.camera, timeout_sec=0.005)
                rclpy.spin_once(self.robot, timeout_sec=0.005)
        spin_thread = threading.Thread(target=spin_worker, daemon=True)
        spin_thread.start()

    # ==================================================================
    # Control robot (receives 26-dimensional actions!)
    # ==================================================================
    def control_robot(self, action):
        """
        Action sequence concatenation order:
        action = 26-dimensional vector
        0~7    left_arm
        7~14   right_arm
        14~20  left_hand
        20~26  right_hand
        """
        action = np.array(action).flatten()
        assert len(action) == 26, "Action must be 26-dimensional"
        
        # Send commands directly to the new version robot
        self.robot.send_robot_action(action)

    # ==================================================================
    # Control partial joints of the robot
    # ==================================================================
    def control_robot_partial(self, name="default", action=[0.0]):

        action = np.array(action).flatten()
        
        # Send commands directly to the new version robot
        self.robot.send_partial_action(name, action)

    # ==================================================================
    # # Reset robot (uses 26-dimensional action)
    # ==================================================================
    def reset_robot(self, target_pose=None, mode='default'):
        if target_pose is None:
            if mode == 'default':
                target_pose = np.array(self.cfg['reset_robot_pos'])
            elif mode == 'zero':
                target_pose = np.zeros(26)
            else:
                self.logger.warning("[WARN] target_pose is None, cannot execute reset_robot")
                return

        target_pose = np.array(target_pose)
        self.robot.send_robot_action(target_pose[:26])
        time.sleep(1.0)
        self.logger.info("✅ Robot reset completed")

    # ==================================================================
    # # Get observation (image + aligned joint angles)
    # ==================================================================
    def retrieve_observation(self):
        try:
            result = {}
            cam_data = self.camera.get_latest_image()
            if not cam_data:
                return None

            head_img, head_ts, left_img, left_ts, right_img, right_ts = cam_data
            if self.current_timestamp == head_ts:
                return None

            self.current_timestamp = head_ts

            # camera images
            result['cam.head'] = head_img
            result['cam.hand_left'] = left_img
            result['cam.hand_right'] = right_img
            result['ref_timestamp'] = head_ts

            # Robot State Alignment
            robot_state = self.robot.get_arm_hand_states_nearest_func(head_ts)

            # Concatenate into state vector
            state = []
            
            # Left Arm
            if robot_state['left_arm'] is not None:
                state.extend(robot_state['left_arm'].position)
            else:
                state.extend([0]*7)

            # Right Arm
            if robot_state['right_arm'] is not None:
                state.extend(robot_state['right_arm'].position)
            else:
                state.extend([0]*7)

            # Left Hand
            if robot_state['left_hand'] is not None:
                state.extend(robot_state['left_hand'].position)
            else:
                state.extend([0]*6)

            # Right Hand
            if robot_state['right_hand'] is not None:
                state.extend(robot_state['right_hand'].position)
            else:
                state.extend([0]*6)

            result['obs.state'] = np.array(state)
            self.current_state = result['obs.state']
            return result

        except Exception as e:
            self.logger.error(f"Failed to get observation: {e}")
            return None

    # ==================================================================
    # Close Robot
    # ==================================================================
    def close(self):
        self.running = False
        self.logger.info("✅ RobotBody safely shut down")


# ======================================================
# # Joint test of robot camera and joint control
# ======================================================
def test_robot_body():
    # rclpy.init()
    print("=" * 60)
    print("🤖 Start testing RobotBody + Ti5Camera + Ti5Robot")
    print("=" * 60)

    default_action = [
        -1.681951211214541, 1.5263110171042418, 2.2737134617553534, -0.23620356347006893, -0.5204031154482495, 0.1292378813793631, 0.19059726269759902
      ] + \
      [
        1.3119088393316176, 1.4473110065281325, -1.6156086726673602, -1.665472635653567, 0.4101313352460489, -0.2251850174207321, 0.3232027944991513
      ] + \
      [
        1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0
      ] + \
      [
        650.0, 650.0, 650.0, 650.0, 650.0, 250.0
      ]

    # Simulation config (loaded from config file in real run)
    mock_config = {
        'robots': {
            'ti5_t170c': {
                'reset_robot_pos': default_action,
                'gripper_freq': 5
            }
        }
    }

    # RobotBody Initialization
    robot_body = RobotBody(mock_config)
    time.sleep(1.0)

    # ----------------------------------------------------------
    # Test 1: Get observation (image + 26-dimensional state)
    # ----------------------------------------------------------
    print("\n📷 Test 1: Retrieving observation data...")
    for _ in range(10):
        obs = robot_body.retrieve_observation()
        if obs is not None:
            print("✅ Observation retrieved successfully!")
            print(f"   Timestamp: {obs['ref_timestamp']:.6f}")
            print(f"   State dimension: {obs['obs.state'].shape} (Expected=26)")
            print(f"   Head camera image shape: {obs['cam.head'].shape}")
            print(f"   Left hand camera image shape: {obs['cam.hand_left'].shape}")
            print(f"   Right hand camera image shape: {obs['cam.hand_right'].shape}")
            break
        time.sleep(0.1)
    else:
        print("❌ Failed to retrieve observation data")

    # --------------------------------------------
    # Test 2: Action control (right hand grasp)
    # --------------------------------------------
    print("\n🎮 Test 2: Send 26-dimensional action - right hand grasp...")
    action = np.zeros(26)
    action[20:26] = [650.0, 650.0, 650.0, 650.0, 650.0, 250.0]
    robot_body.control_robot(action)
    print("✅ Right hand grasp command sent!")
    time.sleep(1.5)

    # ----------------------
    # Test 3: Reset robot
    # ----------------------
    print("\n🔄 Test 3: Resetting robot...")
    robot_body.reset_robot(mode='default')
    time.sleep(0.5)

    # End of test
    robot_body.close()
    print("\n" + "=" * 60)
    print("🎉 All tests passed!")
    print("=" * 60)


if __name__ == '__main__':
    test_robot_body()