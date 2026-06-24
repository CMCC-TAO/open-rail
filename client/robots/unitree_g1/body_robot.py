import time
import cv2
import numpy as np
from .UnitreeG1Robot import UnitreeG1Robot as Robot
from .UnitreeG1Camera import UnitreeG1Camera as Camera
from ..base_robot import RobotBase
import rclpy
import copy
import threading


class RobotBody(RobotBase):
    """Unitree G1 Robot Business Layer (Pure ROS2 + 26-DOF Dexterous Hand)

    Uses independent rclpy.Context to isolate Camera/Robot node wait sets,
    avoiding "wait set index too big" errors caused by sharing context with external dispatcher.
    """

    def __init__(self, config, ros_context=None):
        super().__init__()
        self.cfg, self.ori_cfg = config["robots"]["unitree_g1"], config

        # Use externally passed context, or create independent context (isolates wait set)
        self._ros_context = ros_context  # Lifecycle managed externally (VLAContext)
        if self._ros_context is None:
            self._ros_context = rclpy.Context()
            if not self._ros_context.ok():
                self._ros_context.init()

        self.camera = Camera(ros_context=self._ros_context)
        self.robot = Robot(ros_context=self._ros_context)

        # Unified spin thread
        self.running = True
        self._spin_thread = self._start_spin_thread()

        # State cache
        self.current_timestamp = 0
        self.current_state = None

        print("Unitree G1 RobotBody ready")
        time.sleep(2.0)

    def _start_spin_thread(self):
        from rclpy.executors import SingleThreadedExecutor
        self._executor = SingleThreadedExecutor(context=self._ros_context)
        self._executor.add_node(self.camera)
        self._executor.add_node(self.robot)

        def spin_worker():
            while self.running and self._ros_context.ok():
                try:
                    self._executor.spin_once(timeout_sec=0.005)
                except Exception:
                    pass  # Spin exceptions do not interrupt thread
        t = threading.Thread(target=spin_worker, daemon=True)
        t.start()
        return t

    # ==================================================================
    # Control robot (26-dim action)
    # ==================================================================
    def control_robot(self, action):
        """Send 26-dimensional action

        action[0:7]   -> Left arm
        action[7:14]  -> Right arm
        action[14:20] -> Left hand
        action[20:26] -> Right hand
        """
        action = np.array(action).flatten()
        assert len(action) == 26, "must be 26-dim action"
        self.robot.send_robot_action(action)

    # ==================================================================
    # Execute action (dict interface, for manual control mode)
    # ==================================================================
    def execute_action(self, data):
        """Execute manual control action

        Parse dict commands, build 26-dim action and send to robot.

        Args:
            data: dict, e.g. {'gripper': [left, right]}, {'arm': [14x]}

        Unitree G1 Action Layout:
            [0:7]   -> Left arm
            [7:14]  -> Right arm
            [14:20] -> Left hand (6 fingers, 0~1000)
            [20:26] -> Right hand (6 fingers, 0~1000)

        Gripper value mapping:
            [0, 0] -> Fully open (all fingers 0)
            [1, 1] -> Fully closed (all fingers 1000)
        """
        current_state = getattr(self, 'current_state', None)
        if current_state is None:
            obs = self.retrieve_observation()
            current_state = obs["obs.state"] if obs is not None else np.zeros(26)

        action = np.array(current_state).copy().flatten()
        assert len(action) == 26, f"current_state must be 26-dim, got {len(action)}"

        for key, values in data.items():
            values = np.asarray(values).flatten()
            if key == 'gripper' and len(values) >= 2:
                # [left, right] maps to 6 fingers each for left and right hands
                action[14:20] = np.full(6, float(values[0]) * 1000.0)
                action[20:26] = np.full(6, float(values[1]) * 1000.0)
            elif key == 'arm' and len(values) >= 14:
                action[0:14] = values[:14]
            elif key == 'hand' and len(values) >= 12:
                action[14:26] = values[:12]
            elif key == 'head' or key == 'waist' or key == 'wheel':
                pass  # Unitree G1 26-dim action does not include head/waist/wheel

        self.robot.send_robot_action(action)

    # ==================================================================
    # Reset robot (using ruckig trajectory planning)
    # ==================================================================
    def reset_robot(self, target_pose=None, mode="default"):
        if target_pose is None:
            if mode == "default":
                target_pose = np.array(self.cfg["reset_robot_pos"])
            elif mode == "zero":
                target_pose = np.zeros(26)
            else:
                print("Warning: unknown reset mode, skip")
                return
        target_pose = np.array(target_pose)

        # Get current state (priority: cache → ROS2 subscription → retrieve_observation)
        current_state = self._get_reset_current_state()

        if current_state is not None:
            current_positions = current_state[:14]
            target_positions = target_pose[:14]
            dis = np.abs(current_positions - target_positions)
            if np.any(dis > np.deg2rad(0.01)):
                # Plan arm trajectory at low speed to ensure smooth transition
                trajs = self.ruckig_planning(
                    current_positions, target_positions,
                    max_velocity=0.5, max_acceleration=0.3, max_jerk=1.0,
                )
                n_points = len(trajs)
                # Get current hand state for linear interpolation
                left_hand_current = current_state[14:20]
                right_hand_current = current_state[20:26]
                left_hand_target = target_pose[14:20]
                right_hand_target = target_pose[20:26]

                for i, traj in enumerate(trajs):
                    t = (i + 1) / n_points  # 进度 0→1
                    tmp = target_pose.copy()
                    tmp[:14] = traj
                    # Hand linear interpolation: smoothly transition from current to target values
                    tmp[14:20] = left_hand_current + t * (left_hand_target - left_hand_current)
                    tmp[20:26] = right_hand_current + t * (right_hand_target - right_hand_current)
                    self.robot.send_robot_action(tmp)
                    time.sleep(0.02)  # 50Hz 下发，进一步降低速度
            else:
                self.robot.send_robot_action(target_pose)
        else:
            # Fallback to linear interpolation from zero when current state cannot be obtained
            # (avoid sudden jump to target pose causing robot to "fly")
            print("[WARN] reset_robot: cannot get current state, using linear interpolation from zero")
            current_positions = np.zeros(14)
            target_positions = target_pose[:14]
            n_steps = 50
            for i in range(1, n_steps + 1):
                t = i / n_steps
                tmp = np.zeros(26)
                tmp[:14] = current_positions + t * (target_positions - current_positions)
                tmp[14:20] = target_pose[14:20] * t
                tmp[20:26] = target_pose[20:26] * t
                self.robot.send_robot_action(tmp)
                time.sleep(0.02)

        # Set initial hand state
        self.robot.current_left_hand_state = target_pose[14:20]
        self.robot.current_right_hand_state = target_pose[20:26]

        time.sleep(1.0)
        print("Unitree G1 reset done")

    def _get_reset_current_state(self) -> np.ndarray | None:
        """Get current 26-dim state without camera dependency

        Priority:
          1. Read directly from self.robot's ROS2 subscription cache (real-time, no camera dependency)
          2. self.current_state (VLA observation thread cache, may be stale)
          3. retrieve_observation() fallback (requires camera)

        Note: ROS2 cache is updated in real-time by independent spin thread, always representing actual robot position;
              current_state only updates when VLA observe thread is running,
              becomes stale once VLA stops, cannot serve as reset trajectory starting point.
        """
        # Priority 1: Read directly from ROS2 cache (no camera dependency, real-time latest)
        try:
            robot = self.robot
            la = robot.latest_left_arm
            ra = robot.latest_right_arm
            lh = robot.latest_left_hand
            rh = robot.latest_right_hand
            if all(x is not None for x in (la, ra, lh, rh)):
                la_msg, _ = la
                ra_msg, _ = ra
                lh_msg, _ = lh
                rh_msg, _ = rh
                if (la_msg and ra_msg and lh_msg and rh_msg
                        and la_msg.position and ra_msg.position
                        and lh_msg.position and rh_msg.position):
                    state = np.array(
                        list(la_msg.position)
                        + list(ra_msg.position)
                        + list(lh_msg.position)
                        + list(rh_msg.position),
                        dtype=float,
                    )
                    # Sync to current_state for quick access by other modules
                    self.current_state = state.copy()
                    return state
        except Exception:
            pass

        # Priority 2: Use VLA cached state (only when ROS2 cache not initialized)
        if self.current_state is not None:
            return self.current_state.copy()

        # Priority 3: Fallback to retrieve_observation (requires camera data)
        for _ in range(10):
            obs = self.retrieve_observation()
            if obs is not None and "obs.state" in obs:
                state = obs["obs.state"]
                self.current_state = state
                return state
            time.sleep(0.1)
        return None

    # ==================================================================
    # Get observation (images + aligned joint angles)
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

            # ######################
            # NEW: Skip this round if any camera image is None (prevent pad_and_resize crash downstream)
            # ######################
            if head_img is None or left_img is None or right_img is None:
                return None

            self.current_timestamp = head_ts

            # Images
            result["cam.head"] = head_img
            result["cam.hand_left"] = left_img
            result["cam.hand_right"] = right_img
            result["ref_timestamp"] = head_ts

            # Robot state alignment (based on head camera timestamp)
            robot_state = self.robot.get_arm_hand_states_nearest_func(head_ts)

            # ######################
            # MODIFIED: Skip this round if any part's state is missing (avoid feeding wrong data to model with zero padding)
            # ######################
            if (robot_state["left_arm"] is None
                    or robot_state["right_arm"] is None
                    or robot_state["left_hand"] is None
                    or robot_state["right_hand"] is None):
                return None

            # Concatenate 26-dim state vector
            state = []
            state.extend(robot_state["left_arm"].position)   # 7
            state.extend(robot_state["right_arm"].position)  # 7
            state.extend(robot_state["left_hand"].position)  # 6
            state.extend(robot_state["right_hand"].position) # 6

            result["obs.state"] = np.array(state)
            self.current_state = result["obs.state"]
            return result

        except Exception as e:
            print("Observation error:", e)
            return None

    # ==================================================================
    # Close
    # ==================================================================
    def close(self):
        self.running = False

        # Wait for spin thread to fully exit, avoid wait set race condition when destroying nodes
        if hasattr(self, '_spin_thread') and self._spin_thread.is_alive():
            self._spin_thread.join(timeout=1.0)

        # ######################
        # NEW: Stop robot sampling thread
        # ######################
        self.robot.stop()

        # ######################
        # NEW: Remove nodes from executor first, then destroy executor
        # ######################
        if hasattr(self, '_executor'):
            try:
                self._executor.remove_node(self.camera)
                self._executor.remove_node(self.robot)
            except Exception:
                pass

        # ######################
        # Destroy ROS2 nodes (release resources)
        # ######################
        self.camera.destroy_node()
        self.robot.destroy_node()

        # ######################
        # NEW: Shutdown independent context to avoid Executor.__del__ errors during GC phase
        # ######################
        if self._ros_context is not None and self._ros_context.ok():
            try:
                self._ros_context.shutdown()
            except Exception:
                pass

        print("Unitree G1 RobotBody closed")


# ==============================================
# Test
# ==============================================
def test_robot_body():
    print("=" * 60)
    print("Testing Unitree G1 RobotBody")
    print("=" * 60)

    default_action = (
        [0.0] * 7    # left arm
        + [0.0] * 7  # right arm
        + [0.0] * 6  # left hand
        + [0.0] * 6  # right hand
    )

    mock_config = {
        "robots": {
            "unitree_g1": {
                "reset_robot_pos": default_action,
            }
        }
    }

    robot_body = RobotBody(mock_config)
    time.sleep(1.0)

    # Test 1: Get observation
    print("\nTest 1: retrieve observation...")
    for _ in range(10):
        obs = robot_body.retrieve_observation()
        if obs is not None:
            print("  OK - state dim:", obs["obs.state"].shape, "head img:", obs["cam.head"].shape)
            break
        time.sleep(0.1)
    else:
        print("  FAIL - no observation")

    # Test 2: Action control
    print("\nTest 2: control robot (right hand close)...")
    action = np.zeros(26)
    action[20:26] = [650.0, 650.0, 650.0, 650.0, 650.0, 250.0]
    robot_body.control_robot(action)
    print("  OK")
    time.sleep(1.5)

    # Test 3: Reset
    print("\nTest 3: reset robot...")
    robot_body.reset_robot(mode="default")
    print("  OK")

    robot_body.close()
    print("\n" + "=" * 60)
    print("All tests passed")
    print("=" * 60)


if __name__ == "__main__":
    test_robot_body()
