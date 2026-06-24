import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from message_center.msg import Jointpos
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
from collections import deque
import threading
import time
import numpy as np


# ==============================================
# Arm joint **relative** limits (radians/control step)
# Meaning: maximum allowed deviation between single-step action and current state
#
# Data source: statistical analysis from training set stats_relative.json
#   Inference step delta = max(5 * avg_std, range * 0.3)
#   Control step delta = inference step delta / RATIO
#
# Considering G1 joint execution precision (tracking error ~0.01-0.03 rad),
# delta lower bound set to ~0.015 rad to avoid:
#   1. Tracking error > delta causing action to be continuously clamped, arm doesn't move
#   2. Encoder noise at boundaries causing jitter
# Wrist joints have large motion range, delta relaxed to 0.050 rad appropriately
# ==============================================
# Ratio of control frequency to inference frequency
_CONTROL_INFER_RATIO = 9  # 30Hz(~33.3ms) / 267Hz(3.75ms)

#                        lsp     lsr     lsy     le      lwr     lwp     lwy
_LEFT_ARM_DELTA_LIMITS = [0.15, 0.15, 0.15, 0.15, 0.50, 0.25, 0.20]

#                         rsp     rsr     rsy     re      rwr     rwp     rwy
_RIGHT_ARM_DELTA_LIMITS = [0.20, 0.15, 0.15, 0.15, 0.50, 0.25, 0.20]

# Absolute safety limits (final fallback, prevent flying out when relative limits fail)
_LEFT_ARM_ABS_LIMITS = [
    (-0.80, 0.80),   # left_shoulder_pitch
    (-0.15, 0.25),   # left_shoulder_roll
    (-0.50, 0.36),   # left_shoulder_yaw
    (-0.50, 1.35),   # left_elbow
    (-0.50, 0.86),   # left_wrist_roll
    (-1.36, 0.40),   # left_wrist_pitch
    (-0.58, 1.16),   # left_wrist_yaw
]
_RIGHT_ARM_ABS_LIMITS = [
    (-0.80, 0.80),   # right_shoulder_pitch
    (-0.52, 0.10),   # right_shoulder_roll
    (-0.48, 0.42),   # right_shoulder_yaw
    (-0.70, 1.30),   # right_elbow
    (-0.73, 0.45),   # right_wrist_roll
    (-1.28, 0.36),   # right_wrist_pitch
    (-0.80, 0.60),   # right_wrist_yaw
]


def _clamp_arm_actions(action: np.ndarray, current_arm_state: np.ndarray = None,
                       enable_relative: bool = True,
                       enable_absolute: bool = True) -> np.ndarray:
    """Clamp arm actions in 26-dim action vector

    Supports two independent switches, both enabled by default for backward compatibility.

    Args:
        action: 26-dim action vector [left_arm7, right_arm7, left_hand6, right_hand6]
        current_arm_state: 14-dim current arm state; if None, only absolute limits applied
        enable_relative:   Whether to enable relative limits (single-step delta protection)
        enable_absolute:   Whether to enable absolute limits (safety fallback)
    """
    if enable_relative and current_arm_state is not None and len(current_arm_state) >= 14:
        # —— Relative limits: action cannot deviate from current state beyond delta ——
        for i, delta in enumerate(_LEFT_ARM_DELTA_LIMITS):
            lo = current_arm_state[i] - delta
            hi = current_arm_state[i] + delta
            action[i] = np.clip(action[i], lo, hi)
        for i, delta in enumerate(_RIGHT_ARM_DELTA_LIMITS):
            lo = current_arm_state[7 + i] - delta
            hi = current_arm_state[7 + i] + delta
            action[7 + i] = np.clip(action[7 + i], lo, hi)

    if enable_absolute:
        # —— Absolute limits fallback ——
        for i, (lo, hi) in enumerate(_LEFT_ARM_ABS_LIMITS):
            action[i] = np.clip(action[i], lo, hi)
        for i, (lo, hi) in enumerate(_RIGHT_ARM_ABS_LIMITS):
            action[7 + i] = np.clip(action[7 + i], lo, hi)

    return action

_DEBUG_ENABLED = False          # Toggle: True=print, False=silent
_DEBUG_PRINT_INTERVAL = 1.0
_last_debug_time = 0.0


def _dprint(msg):
    if not _DEBUG_ENABLED:
        return
    global _last_debug_time
    now = time.time()
    if now - _last_debug_time >= _DEBUG_PRINT_INTERVAL:
        print(f"[DBG UnitreeG1Robot] {msg}")
        _last_debug_time = now


class UnitreeG1Robot(Node):
    """Unitree G1 Robot ROS2 Driver (Pure ROS2 Mode, Pure Dexterous Hand, No Gripper/Legs)

    26-dim Action Interface:
        action[0:7]   -> Left arm (7 joints)
        action[7:14]  -> Right arm (7 joints)
        action[14:20] -> Left hand (6 fingers)
        action[20:26] -> Right hand (6 fingers)
    """

    def __init__(self, ros_context=None):
        super().__init__("unitree_g1_robot_node", context=ros_context)

        # ======================
        # Subscription topics (state reading)
        # ======================
        self.topic_joint_states = "/joint_state"
        self.topic_left_hand = "/left_hand/get_angle"
        self.topic_right_hand = "/right_hand/get_angle"

        # ======================
        # Publish topics (control output)
        # ======================
        self.topic_left_arm_cmd = "/left_arm/joint_pos"
        self.topic_right_arm_cmd = "/right_arm/joint_pos"
        self.topic_left_hand_cmd = "/left_hand_cmd"
        self.topic_right_hand_cmd = "/right_hand_cmd"

        print(f"[DBG UnitreeG1Robot] Subscribed topics:")
        print(f"[DBG UnitreeG1Robot]   - {self.topic_joint_states}")
        print(f"[DBG UnitreeG1Robot]   - {self.topic_left_hand}")
        print(f"[DBG UnitreeG1Robot]   - {self.topic_right_hand}")
        print(f"[DBG UnitreeG1Robot]   (pubs: {self.topic_left_arm_cmd}, {self.topic_right_arm_cmd}, {self.topic_left_hand_cmd}, {self.topic_right_hand_cmd})")

        # Latest state cache
        self.latest_left_arm = None
        self.latest_right_arm = None
        self.latest_left_hand = None
        self.latest_right_hand = None

        # Queue cache (for timestamp alignment)
        self.queue_left_arm = deque(maxlen=30)
        self.queue_right_arm = deque(maxlen=30)
        self.queue_left_hand = deque(maxlen=30)
        self.queue_right_hand = deque(maxlen=30)

        # QoS matching robot driver
        qos_correct = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=10
        )
        qos_pub = QoSProfile(depth=10)

        # ======================
        # Subscriptions (read state)
        # ======================
        self.create_subscription(JointState, self.topic_joint_states, self._cb_joint_states, qos_correct)
        self.create_subscription(JointState, self.topic_left_hand, self._cb_left_hand, qos_correct)
        self.create_subscription(JointState, self.topic_right_hand, self._cb_right_hand, qos_correct)

        # ======================
        # Publishers (control robot)
        # ======================
        self.pub_left_arm = self.create_publisher(Jointpos, self.topic_left_arm_cmd, qos_pub)
        self.pub_right_arm = self.create_publisher(Jointpos, self.topic_right_arm_cmd, qos_pub)
        self.pub_left_hand = self.create_publisher(JointState, self.topic_left_hand_cmd, qos_pub)
        self.pub_right_hand = self.create_publisher(JointState, self.topic_right_hand_cmd, qos_pub)

        # Fixed joint names
        self.left_arm_joint_names = [
            "left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint",
            "left_elbow_joint", "left_wrist_roll_joint", "left_wrist_pitch_joint", "left_wrist_yaw_joint",
        ]
        self.right_arm_joint_names = [
            "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint",
            "right_elbow_joint", "right_wrist_roll_joint", "right_wrist_pitch_joint", "right_wrist_yaw_joint",
        ]
        self.hand_joint_names = ["little_finger", "ring_finger", "middle_finger", "index_finger", "thumb_bend", "thumb_rotate"]

        self.current_left_hand_state = None
        self.current_right_hand_state = None

        # ======================
        # Limit switches (all on by default, maintain backward compatibility)
        # ======================
        self.enable_relative_clamp = True   # Relative limits (single-step delta protection)
        self.enable_absolute_clamp = True   # Absolute limits (safety fallback)

        self.running = True

        # ######################
        # NEW: Deduplication flag, avoid sampling thread enqueueing same timestamp data repeatedly
        # ######################
        self._last_queue_ts_left_arm = 0.0
        self._last_queue_ts_right_arm = 0.0
        self._last_queue_ts_left_hand = 0.0
        self._last_queue_ts_right_hand = 0.0

        # Sampling thread
        self.sample_thread = threading.Thread(target=self._sample_loop, daemon=True)
        self.sample_thread.start()

        self.get_logger().info("UnitreeG1Robot ready")

    def _get_current_arm_state(self) -> np.ndarray:
        """Get current 14-dim arm joint positions [left_arm7, right_arm7] from ROS2 callback cache

        Returns:
            np.ndarray or None: 14-dim joint positions; returns None if data missing
        """
        la = self.latest_left_arm
        ra = self.latest_right_arm
        if la is None or ra is None:
            return None
        la_msg, _ = la
        ra_msg, _ = ra
        if la_msg is None or ra_msg is None:
            return None
        if not la_msg.position or not ra_msg.position:
            return None
        return np.array(list(la_msg.position) + list(ra_msg.position), dtype=float)

    # ======================
    # [Core Control Function] 26-dim action input
    # ======================
    def send_robot_action(self, action):
        """Send 26-dim action to robot

        Args:
            action (array-like): [left_arm7, right_arm7, left_hand6, right_hand6]
        """
        action = np.asarray(action).flatten()

        # Relative limit protection: limit maximum single-step deviation based on current arm state
        current_arm = self._get_current_arm_state()
        action = _clamp_arm_actions(
            action, current_arm,
            enable_relative=self.enable_relative_clamp,
            enable_absolute=self.enable_absolute_clamp,
        )

        left_arm_act = action[0:7]
        right_arm_act = action[7:14]
        left_hand_act = action[14:20]
        right_hand_act = action[20:26]

        # Left arm
        if left_arm_act[-1] > -100:
            msg = Jointpos()
            msg.joint = left_arm_act.tolist()
            msg.type = 1  # left arm
            msg.dof = 7
            self.pub_left_arm.publish(msg)

        # Right arm
        if right_arm_act[-1] > -100:
            msg = Jointpos()
            msg.joint = right_arm_act.tolist()
            msg.type = 2  # right arm
            msg.dof = 7
            self.pub_right_arm.publish(msg)

        # Left hand (with debounce: send only if difference > 50)
        if left_hand_act[-1] > -100:
            if self.current_left_hand_state is not None:
                left_diff = np.abs(left_hand_act - self.current_left_hand_state).sum()
            else:
                left_diff = 0
            if self.current_left_hand_state is None or left_diff > 50:
                msg = JointState()
                msg.name = self.hand_joint_names
                msg.position = left_hand_act.tolist()
                self.pub_left_hand.publish(msg)
                self.current_left_hand_state = left_hand_act

        # Right hand (with debounce: send only if difference > 50)
        if right_hand_act[-1] > -100:
            if self.current_right_hand_state is not None:
                right_diff = np.abs(right_hand_act - self.current_right_hand_state).sum()
            else:
                right_diff = 0
            if self.current_right_hand_state is None or right_diff > 50:
                msg = JointState()
                msg.name = self.hand_joint_names
                msg.position = right_hand_act.tolist()
                self.pub_right_hand.publish(msg)
                self.current_right_hand_state = right_hand_act

    # ======================
    # Subscription callbacks
    # ======================

    def _cb_joint_states(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

        # Build name->index mapping by joint name
        name_to_idx = {name: i for i, name in enumerate(msg.name)}

        # Extract left arm positions by name
        left_positions = []
        for name in self.left_arm_joint_names:
            if name in name_to_idx:
                left_positions.append(msg.position[name_to_idx[name]])

        # Extract right arm positions by name
        right_positions = []
        for name in self.right_arm_joint_names:
            if name in name_to_idx:
                right_positions.append(msg.position[name_to_idx[name]])

        # Construct synthetic JointState for downstream compatibility
        la_ok = len(left_positions) == len(self.left_arm_joint_names)
        ra_ok = len(right_positions) == len(self.right_arm_joint_names)
        if la_ok:
            left_msg = JointState()
            left_msg.header = msg.header
            left_msg.name = list(self.left_arm_joint_names)
            left_msg.position = [float(p) for p in left_positions]
            self.latest_left_arm = (left_msg, ts)

        if ra_ok:
            right_msg = JointState()
            right_msg.header = msg.header
            right_msg.name = list(self.right_arm_joint_names)
            right_msg.position = [float(p) for p in right_positions]
            self.latest_right_arm = (right_msg, ts)

        if la_ok and ra_ok:
            _dprint(f"_cb_joint_states OK: ts={ts:.6f}, la={left_positions[:3]}..., ra={right_positions[:3]}...")
        elif not la_ok and not ra_ok:
            _dprint(f"_cb_joint_states BOTH FAIL: la_found={len(left_positions)}/{len(self.left_arm_joint_names)} "
                    f"ra_found={len(right_positions)}/{len(self.right_arm_joint_names)} "
                    f"topic_joint_names={list(msg.name)}")
        elif not la_ok:
            _dprint(f"_cb_joint_states LEFT FAIL: la_found={len(left_positions)}/{len(self.left_arm_joint_names)}")
        else:
            _dprint(f"_cb_joint_states RIGHT FAIL: ra_found={len(right_positions)}/{len(self.right_arm_joint_names)}")

    def _cb_left_hand(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self.latest_left_hand = (msg, ts)
        _dprint(f"_cb_left_hand received: ts={ts:.6f}, positions={msg.position[:3]}...")

    def _cb_right_hand(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self.latest_right_hand = (msg, ts)
        _dprint(f"_cb_right_hand received: ts={ts:.6f}, positions={msg.position[:3]}...")

    # ======================
    # Sampling thread
    # ======================
    def _sample_loop(self):
        print("[DBG UnitreeG1Robot] _sample_loop started")
        loop_count = 0
        while self.running:
            loop_count += 1
            # ######################
            # MODIFIED: Timestamp deduplication (use 1ms threshold for float comparison)
            # ######################
            eps = 1e-4
            if self.latest_left_arm:
                ts = self.latest_left_arm[1]
                if abs(ts - self._last_queue_ts_left_arm) > eps:
                    self.queue_left_arm.append(self.latest_left_arm)
                    self._last_queue_ts_left_arm = ts
            if self.latest_right_arm:
                ts = self.latest_right_arm[1]
                if abs(ts - self._last_queue_ts_right_arm) > eps:
                    self.queue_right_arm.append(self.latest_right_arm)
                    self._last_queue_ts_right_arm = ts
            if self.latest_left_hand:
                ts = self.latest_left_hand[1]
                if abs(ts - self._last_queue_ts_left_hand) > eps:
                    self.queue_left_hand.append(self.latest_left_hand)
                    self._last_queue_ts_left_hand = ts
            if self.latest_right_hand:
                ts = self.latest_right_hand[1]
                if abs(ts - self._last_queue_ts_right_hand) > eps:
                    self.queue_right_hand.append(self.latest_right_hand)
                    self._last_queue_ts_right_hand = ts
            if loop_count % 500 == 0:
                _dprint(f"queues: left_arm={len(self.queue_left_arm)} right_arm={len(self.queue_right_arm)} "
                        f"left_hand={len(self.queue_left_hand)} right_hand={len(self.queue_right_hand)} "
                        f"latest: la={'Y' if self.latest_left_arm else 'N'} ra={'Y' if self.latest_right_arm else 'N'} "
                        f"lh={'Y' if self.latest_left_hand else 'N'} rh={'Y' if self.latest_right_hand else 'N'}")
            time.sleep(0.002)

    # ======================
    # Timestamp alignment
    # ======================
    def _find_nearest(self, queue, target_ts):
        if not queue:
            return (None, 0.0)
        # Snapshot: avoid deque being appended by sampling thread during iteration,
        # causing "deque mutated during iteration" exception
        snapshot = list(queue)
        if not snapshot:
            return (None, 0.0)
        return min(snapshot, key=lambda x: abs(x[1] - target_ts))

    def get_arm_hand_states_nearest_func(self, ref_timestamp):
        """Align left/right arm/hand states based on ref_timestamp

        Args:
            ref_timestamp (float): Reference timestamp (usually from head camera)

        Returns:
            dict: Contains states and timestamps for each part
        """
        left_arm, left_arm_ts = self._find_nearest(self.queue_left_arm, ref_timestamp)
        right_arm, right_arm_ts = self._find_nearest(self.queue_right_arm, ref_timestamp)
        left_hand, left_hand_ts = self._find_nearest(self.queue_left_hand, ref_timestamp)
        right_hand, right_hand_ts = self._find_nearest(self.queue_right_hand, ref_timestamp)

        return {
            "left_arm": left_arm,
            "right_arm": right_arm,
            "left_hand": left_hand,
            "right_hand": right_hand,
            "ref_timestamp": ref_timestamp,
            "left_arm_timestamp": left_arm_ts,
            "right_arm_timestamp": right_arm_ts,
            "left_hand_timestamp": left_hand_ts,
            "right_hand_timestamp": right_hand_ts,
        }

    def stop(self):
        self.running = False


# ==============================================
# main: Pure robot driver test (no camera required)
# ==============================================
def main():
    rclpy.init()

    robot = UnitreeG1Robot()

    # Start spin thread to let ROS2 callbacks work properly
    running = True
    def spin_worker():
        while running:
            rclpy.spin_once(robot, timeout_sec=0.005)

    spin_thread = threading.Thread(target=spin_worker)
    spin_thread.start()

    print("Monitoring robot states. Press Ctrl+C to stop.\n")
    print(f"  Sub: {robot.topic_joint_states}, {robot.topic_left_hand}, {robot.topic_right_hand}")
    print(f"  Pub: {robot.topic_left_arm_cmd}, {robot.topic_right_arm_cmd}, "
          f"{robot.topic_left_hand_cmd}, {robot.topic_right_hand_cmd}")
    print()

    count = 0
    try:
        while running:
            time.sleep(0.05)

            la = robot.latest_left_arm
            ra = robot.latest_right_arm
            lh = robot.latest_left_hand
            rh = robot.latest_right_hand

            la_pos = la[0].position if la and la[0] and la[0].position else [None]*7
            ra_pos = ra[0].position if ra and ra[0] and ra[0].position else [None]*7
            lh_pos = lh[0].position if lh and lh[0] and lh[0].position else [None]*6
            rh_pos = rh[0].position if rh and rh[0] and rh[0].position else [None]*6

            if la is not None and ra is not None and lh is not None and rh is not None:
                action = np.zeros(26, dtype=float)
                action[0:7] = la_pos
                action[7:14] = ra_pos
                action[14:20] = lh_pos
                action[20:26] = rh_pos
                robot.send_robot_action(action)

            count += 1
            if count % 10 != 0:  # 每秒打印一次
                continue

            print("=" * 70)
            print(f"  left_arm(7):  [{', '.join(f'{v:8.4f}' if v is not None else '    None' for v in la_pos)}]")
            print(f"  right_arm(7): [{', '.join(f'{v:8.4f}' if v is not None else '    None' for v in ra_pos)}]")
            print(f"  left_hand(6): [{', '.join(f'{v:8.4f}' if v is not None else '    None' for v in lh_pos)}]")
            print(f"  right_hand(6):[{', '.join(f'{v:8.4f}' if v is not None else '    None' for v in rh_pos)}]")


    except KeyboardInterrupt:
        print("\nStopped by user")

    running = False
    robot.stop()
    spin_thread.join(timeout=1.0)
    rclpy.shutdown()
    print("Robot driver test done")


if __name__ == "__main__":
    main()
