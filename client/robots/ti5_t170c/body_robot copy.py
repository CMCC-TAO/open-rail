import threading
import time
from typing import Optional

import numpy as np
import pandas as pd

from ..base_robot import RobotBase


class _Ti5RosNodeRunner:
    """Owns a rclpy Node and spins it in a background thread."""

    def __init__(self, node_name: str):
        try:
            import rclpy
            from rclpy.executors import SingleThreadedExecutor
            from rclpy.node import Node
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "Ti5_t170c robot requires ROS2 Python packages (rclpy, sensor_msgs). "
                "Please source ROS2 Humble and the ti5 workspace before running."
            ) from exc

        self._rclpy = rclpy
        if not rclpy.ok():
            rclpy.init(args=None)

        self.node = Node(node_name)
        self._executor = SingleThreadedExecutor()
        self._executor.add_node(self.node)

        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._running = False

    def start(self) -> None:
        self._running = True
        self._thread.start()

    def _spin(self) -> None:
        while self._running and self._rclpy.ok():
            self._executor.spin_once(timeout_sec=0.02)

    def close(self) -> None:
        self._running = False
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)
        try:
            self._executor.remove_node(self.node)
        except Exception:
            pass
        try:
            self.node.destroy_node()
        except Exception:
            pass


class RobotBody(RobotBase):
    """Ti5 T170C robot adapter based on ROS2 topics.

    This adapter matches the minimal contract expected by `VLAClient`:
    - `retrieve_observation()` returns dict with keys: `ref_timestamp`, `cam.*`, `obs.state`
    - `control_robot(action)` accepts a 16-dim action (14 arm + 2 gripper)

    Phase-1 constraints:
    - Cameras: three UDP/RTP streams (recv_stream) if enabled:
        port 5000 -> `cam.head`, 5001 -> `cam.hand_right`, 5002 -> `cam.hand_left`.
      Missing streams fall back to the same placeholder image per view.
    - Proprioception sources:
        - Arms are wired (from `/left_arm/joint_states` and `/right_arm/joint_states`).
        - Hand/neck/waist/leg are currently NOT wired into this adapter; corresponding dims stay 0.
    """

    def __init__(self, config):
        super().__init__()
        self.cfg = config["robots"]["ti5_t170c"]

        self._node_runner = _Ti5RosNodeRunner(node_name=self.cfg["ros"]["node_name"])
        self._node = self._node_runner.node

        # Use sensor-data QoS for state topics to avoid RELIABILITY mismatch with
        # publishers (many joint/angle state streams are BEST_EFFORT).
        from rclpy.qos import qos_profile_sensor_data
        self._qos_sensor_data = qos_profile_sensor_data

        from sensor_msgs.msg import JointState

        self._JointState = JointState
        self._lock = threading.Lock()

        self._last_state_ns = 0
        self._last_returned_state_ns = 0
        self._left_pos: Optional[np.ndarray] = None
        self._right_pos: Optional[np.ndarray] = None
        self._left_vel: Optional[np.ndarray] = None
        self._right_vel: Optional[np.ndarray] = None
        self._left_eff: Optional[np.ndarray] = None
        self._right_eff: Optional[np.ndarray] = None

        self._left_pub = self._node.create_publisher(
            JointState, self.cfg["arms"]["left_arm_joint_cmd_topic"], 10
        )
        self._right_pub = self._node.create_publisher(
            JointState, self.cfg["arms"]["right_arm_joint_cmd_topic"], 10
        )

        self._node.create_subscription(
            JointState,
            self.cfg["arms"]["left_arm_joint_states_topic"],
            self._on_left_state,
            self._qos_sensor_data,
        )
        self._node.create_subscription(
            JointState,
            self.cfg["arms"]["right_arm_joint_states_topic"],
            self._on_right_state,
            self._qos_sensor_data,
        )

        self._left_hand_pub = self._node.create_publisher(
            JointState, self.cfg["hands"]["left_hand_joint_cmd_topic"], 10
        )
        self._right_hand_pub = self._node.create_publisher(
            JointState, self.cfg["hands"]["right_hand_joint_cmd_topic"], 10
        )

        self._node.create_subscription(
            JointState, self.cfg["hands"]["left_hand_joint_states_topic"], self._on_left_hand_state, 
            self._qos_sensor_data,
        )
        self._node.create_subscription(
            JointState,
            self.cfg["hands"]["right_hand_joint_states_topic"],
            self._on_right_hand_state,
            self._qos_sensor_data,
        )

        self._leg_pos: Optional[np.ndarray] = None
        self._leg_vel: Optional[np.ndarray] = None
        self._leg_eff: Optional[np.ndarray] = None

        self._leg_pub = self._node.create_publisher(
            JointState, self.cfg["leg"]["leg_joint_cmd_topic"], 10
        )
        self._node.create_subscription(
            JointState, self.cfg["leg"]["leg_joint_states_topic"], self._on_leg_state, 
            self._qos_sensor_data,
        )

        self._waist_pos: Optional[np.ndarray] = None
        self._waist_vel: Optional[np.ndarray] = None
        self._waist_eff: Optional[np.ndarray] = None

        self._waist_pub = self._node.create_publisher(
            JointState, self.cfg["waist"]["waist_joint_cmd_topic"], 10
        )
        self._node.create_subscription(
            JointState, self.cfg["waist"]["waist_joint_states_topic"], self._on_waist_state, 
            self._qos_sensor_data
        )

        self._head_pos: Optional[np.ndarray] = None
        self._head_vel: Optional[np.ndarray] = None
        self._head_eff: Optional[np.ndarray] = None

        self._head_pub = self._node.create_publisher(
            JointState, self.cfg["head"]["head_joint_cmd_topic"], 10
        )
        self._node.create_subscription(
            JointState, self.cfg["head"]["head_joint_states_topic"], self._on_head_state, 
            self._qos_sensor_data,
        )

        self._left_hand_pos: Optional[np.ndarray] = None
        self._right_hand_pos: Optional[np.ndarray] = None
        self._head_pos: Optional[np.ndarray] = None
        self._waist_pos: Optional[np.ndarray] = None
        self._leg_pos: Optional[np.ndarray] = None
        self._left_hand_pos: Optional[np.ndarray] = None
        self._right_hand_pos: Optional[np.ndarray] = None
        self._head_pos: Optional[np.ndarray] = None
        self._waist_pos: Optional[np.ndarray] = None
        self._leg_pos: Optional[np.ndarray] = None

        #self._left_hand_pub = None
        #self._right_hand_pub = None
        #self._head_pub = None
        #self._waist_pub = None
        #self._leg_pub = None

        #self._try_init_extra_proprio_and_publishers(JointState)

        # observation.state layout (34 dims, names order from dataset spec):
        # 0:7   left arm
        # 7:14  right arm
        # 14:20 left hand
        # 20:26 right hand
        # 26:29 neck
        # 29:32 waist
        # 32:34 leg
        self._obs_state_dim = 34
        self._left_arm_slice = slice(0, 7)
        self._right_arm_slice = slice(7, 14)
        self._left_hand_slice = slice(14, 20)
        self._right_hand_slice = slice(20, 26)
        self._neck_slice = slice(26, 29)
        self._waist_slice = slice(29, 32)
        self._leg_slice = slice(32, 34)

        self.current_state = np.zeros(self._obs_state_dim, dtype=np.float64)
        self._placeholder_cam = np.zeros(
            (self.cfg["observation"]["placeholder_image_height"],
             self.cfg["observation"]["placeholder_image_width"],
             3),
            dtype=np.uint8,
        )

        # One RgbReceiver per UDP port (C++ side binds a single port per instance).
        self._rgb_receivers = {}
        self._use_stream_rgb_by_cam = {"head": False, "hand_right": False, "hand_left": False}
        self._use_stream_rgb = False
        self._last_rgb_ts_ns = 0
        self._last_rgb_ts_ns_by_cam = {"head": 0, "hand_right": 0, "hand_left": 0}
        self._logged_rgb_fallback = {"head": False, "hand_right": False, "hand_left": False}
        self._logged_unwired_obs_state_dims = False
        self._init_rgb_receiver()

        self._node_runner.start()
        time.sleep(0.2)

    def _init_rgb_receiver(self) -> None:
        stream_cfg = self.cfg.get("camera_stream", None)
        if stream_cfg is None or not bool(stream_cfg.get("enable", False)):
            self._node.get_logger().info(
                "Ti5 RGB streams disabled by config; using placeholder for cam.head, "
                "cam.hand_right, cam.hand_left."
            )
            return

        module_name = str(stream_cfg.get("module_name", "recv_stream_py"))
        ports = list(stream_cfg.get("ports", [5000, 5001, 5002]))
        payload_types = list(stream_cfg.get("payload_types", [96, 97, 98]))
        # ports[0]=head(5000), [1]=right wrist(5001), [2]=left wrist(5002)
        cam_order = [("head", 0), ("hand_right", 1), ("hand_left", 2)]

        try:
            recv_stream_py = __import__(module_name)
        except Exception:
            self._node.get_logger().warning(
                f"Ti5 RGB streams unavailable (module={module_name}); "
                "using placeholder for all cameras."
            )
            return

        latency_ms = int(stream_cfg.get("latency_ms", 20))
        disable_jitterbuffer = bool(stream_cfg.get("disable_jitterbuffer", False))
        decoder = str(stream_cfg.get("decoder", "nv"))

        started = []
        for cam_name, idx in cam_order:
            if idx >= len(ports) or idx >= len(payload_types):
                self._node.get_logger().warning(
                    f"Ti5 camera '{cam_name}' skipped: missing port/payload_types at index {idx}."
                )
                continue
            cfg = recv_stream_py.ReceiverConfig()
            cfg.ports = [int(ports[idx])]
            cfg.payload_types = [int(payload_types[idx])]
            cfg.stream_index = 0
            cfg.latency_ms = latency_ms
            cfg.disable_jitterbuffer = disable_jitterbuffer
            cfg.decoder = decoder

            receiver = recv_stream_py.RgbReceiver(cfg)
            if receiver.start():
                self._rgb_receivers[cam_name] = receiver
                self._use_stream_rgb_by_cam[cam_name] = True
                started.append("%s:udp:%d/pt:%d" % (cam_name, cfg.ports[0], cfg.payload_types[0]))
            else:
                self._node.get_logger().warning(
                    f"Ti5 RGB receiver failed to start for {cam_name} "
                    f"(port={cfg.ports[0]}, pt={cfg.payload_types[0]})."
                )

        self._use_stream_rgb = bool(self._use_stream_rgb_by_cam.get("head", False))
        if started:
            self._node.get_logger().info(
                f"Ti5 RGB streams via {module_name}: {', '.join(started)}"
            )
        else:
            self._node.get_logger().warning(
                "Ti5 RGB: no receiver started; using placeholders for head / hand_right / hand_left."
            )

    def _get_cam_rgb(self, cam_name: str):
        """Return latest HWC RGB uint8 for cam_name, or None."""
        by_cam = getattr(self, "_use_stream_rgb_by_cam", None)
        if not isinstance(by_cam, dict) or not by_cam.get(cam_name, False):
            return None
        receivers = getattr(self, "_rgb_receivers", None)
        if not isinstance(receivers, dict):
            return None
        receiver = receivers.get(cam_name)
        if receiver is None:
            return None
        try:
            item = receiver.get_latest_rgb()
            if item is None:
                return None
            img, ts_ns = item
            arr = np.asarray(img, dtype=np.uint8)
            if arr.ndim != 3 or arr.shape[2] != 3:
                return None
            ts = int(ts_ns)
            ts_by = getattr(self, "_last_rgb_ts_ns_by_cam", None)
            if not isinstance(ts_by, dict):
                ts_by = {}
                self._last_rgb_ts_ns_by_cam = ts_by
            ts_by[cam_name] = ts
            if cam_name == "head":
                self._last_rgb_ts_ns = ts
            return arr
        except Exception:
            return None

    def _resolve_cam_with_fallback(self, cam_name: str, label_for_log: str):
        """Get one camera image or placeholder; log once per cam if stream on but no frame yet."""
        img = self._get_cam_rgb(cam_name)
        if img is not None:
            fb = getattr(self, "_logged_rgb_fallback", None)
            if isinstance(fb, dict):
                fb[cam_name] = False
            return img
        out = self._placeholder_cam.copy()
        by_cam = getattr(self, "_use_stream_rgb_by_cam", None)
        if not isinstance(by_cam, dict):
            by_cam = {}
        fb = getattr(self, "_logged_rgb_fallback", None)
        if not isinstance(fb, dict):
            fb = {}
            self._logged_rgb_fallback = fb
        if by_cam.get(cam_name, False) and not fb.get(cam_name, False):
            if hasattr(self, "_node"):
                self._node.get_logger().warning(
                    f"Ti5 RGB enabled for {cam_name} but no frame yet; "
                    f"using placeholder {label_for_log}."
                )
            fb[cam_name] = True
        return out

    def _extract_joint_ordered(self, msg, joint_names):
        name_to_index = {n: i for i, n in enumerate(msg.name)} if msg.name else {}
        pos = np.zeros(len(joint_names), dtype=np.float64)
        vel = np.zeros(len(joint_names), dtype=np.float64)
        eff = np.zeros(len(joint_names), dtype=np.float64)

        for out_i, joint_name in enumerate(joint_names):
            idx = name_to_index.get(joint_name, None)
            if idx is None:
                continue
            if idx < len(msg.position):
                pos[out_i] = float(msg.position[idx])
            if idx < len(msg.velocity):
                vel[out_i] = float(msg.velocity[idx])
            if idx < len(msg.effort):
                eff[out_i] = float(msg.effort[idx])
        return pos, vel, eff

    def _try_init_extra_proprio_and_publishers(self, joint_state_type) -> None:
        """Optionally wire hands/head/waist/leg based on config keys."""
        # Hands
        hands_cfg = self.cfg.get("hands", None)
        if isinstance(hands_cfg, dict):
            try:
                self._left_hand_pub = self._node.create_publisher(
                    joint_state_type, hands_cfg["left_hand_joint_cmd_topic"], 10
                )
                self._right_hand_pub = self._node.create_publisher(
                    joint_state_type, hands_cfg["right_hand_joint_cmd_topic"], 10
                )
                self._node.create_subscription(
                    joint_state_type,
                    hands_cfg["left_hand_joint_states_topic"],
                    self._on_left_hand_state,
                    self._qos_sensor_data,
                )
                self._node.create_subscription(
                    joint_state_type,
                    hands_cfg["right_hand_joint_states_topic"],
                    self._on_right_hand_state,
                    self._qos_sensor_data,
                )
            except Exception:
                self._left_hand_pub = None
                self._right_hand_pub = None

        # Head
        head_cfg = self.cfg.get("head", None)
        if isinstance(head_cfg, dict):
            try:
                self._head_pub = self._node.create_publisher(
                    joint_state_type, head_cfg["head_joint_cmd_topic"], 10
                )
                self._node.create_subscription(
                    joint_state_type,
                    head_cfg["head_joint_states_topic"],
                    self._on_head_state,
                    self._qos_sensor_data,
                )
            except Exception:
                self._head_pub = None

        # Waist
        waist_cfg = self.cfg.get("waist", None)
        if isinstance(waist_cfg, dict):
            try:
                self._waist_pub = self._node.create_publisher(
                    joint_state_type, waist_cfg["waist_joint_cmd_topic"], 10
                )
                self._node.create_subscription(
                    joint_state_type,
                    waist_cfg["waist_joint_states_topic"],
                    self._on_waist_state,
                    self._qos_sensor_data,
                )
            except Exception:
                self._waist_pub = None

        # Leg
        leg_cfg = self.cfg.get("leg", None)
        if isinstance(leg_cfg, dict):
            try:
                self._leg_pub = self._node.create_publisher(
                    joint_state_type, leg_cfg["leg_joint_cmd_topic"], 10
                )
                self._node.create_subscription(
                    joint_state_type,
                    leg_cfg["leg_joint_states_topic"],
                    self._on_leg_state,
                    self._qos_sensor_data,
                )
            except Exception:
                self._leg_pub = None

    def _stamp_to_ns(self, stamp) -> int:
        sec = int(getattr(stamp, "sec", 0))
        nanosec = int(getattr(stamp, "nanosec", 0))
        return sec * 1_000_000_000 + nanosec

    def _on_left_state(self, msg) -> None:
        with self._lock:
            self._left_pos, self._left_vel, self._left_eff = self._extract_joint_ordered(
                msg, self.cfg["arms"]["left_arm_joint_names"]
            )
            self._last_state_ns = max(self._last_state_ns, self._stamp_to_ns(msg.header.stamp))

    def _on_right_state(self, msg) -> None:
        with self._lock:
            self._right_pos, self._right_vel, self._right_eff = self._extract_joint_ordered(
                msg, self.cfg["arms"]["right_arm_joint_names"]
            )
            self._last_state_ns = max(self._last_state_ns, self._stamp_to_ns(msg.header.stamp))

    def _on_left_hand_state(self, msg) -> None:
        with self._lock:
            joint_names = self.cfg.get("hands", {}).get("left_hand_joint_names", [])
            self._left_hand_pos, _, _ = self._extract_joint_ordered(msg, joint_names)
            self._last_state_ns = max(self._last_state_ns, self._stamp_to_ns(msg.header.stamp))

    def _on_right_hand_state(self, msg) -> None:
        with self._lock:
            joint_names = self.cfg.get("hands", {}).get("right_hand_joint_names", [])
            self._right_hand_pos, _, _ = self._extract_joint_ordered(msg, joint_names)
            self._last_state_ns = max(self._last_state_ns, self._stamp_to_ns(msg.header.stamp))

    def _on_head_state(self, msg) -> None:
        with self._lock:
            joint_names = self.cfg.get("head", {}).get("head_joint_names", [])
            self._head_pos, _, _ = self._extract_joint_ordered(msg, joint_names)
            self._last_state_ns = max(self._last_state_ns, self._stamp_to_ns(msg.header.stamp))

    def _on_waist_state(self, msg) -> None:
        with self._lock:
            joint_names = self.cfg.get("waist", {}).get("waist_joint_names", [])
            self._waist_pos, _, _ = self._extract_joint_ordered(msg, joint_names)
            self._last_state_ns = max(self._last_state_ns, self._stamp_to_ns(msg.header.stamp))

    def _on_leg_state(self, msg) -> None:
        with self._lock:
            joint_names = self.cfg.get("leg", {}).get("leg_joint_names", [])
            self._leg_pos, _, _ = self._extract_joint_ordered(msg, joint_names)
            self._last_state_ns = max(self._last_state_ns, self._stamp_to_ns(msg.header.stamp))

    def _publish_joint_position(self, pub, joint_names, positions) -> None:
        if pub is None:
            return
        arr = np.asarray(positions, dtype=np.float64).reshape(-1)
        msg = self._JointState()
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.name = list(joint_names)
        msg.position = arr.tolist()
        pub.publish(msg)

    def move_arm(self, arm) -> None:
        arm = np.asarray(arm, dtype=np.float64).reshape(-1)
        if arm.shape[0] < 14:
            raise ValueError(f"Ti5 move_arm expects 14 dims, got {arm.shape}")

        left = arm[:7].tolist()
        right = arm[7:14].tolist()

        stamp = self._node.get_clock().now().to_msg()

        left_msg = self._JointState()
        left_msg.header.stamp = stamp
        left_msg.name = list(self.cfg["arms"]["left_arm_joint_names"])
        left_msg.position = left

        right_msg = self._JointState()
        right_msg.header.stamp = stamp
        right_msg.name = list(self.cfg["arms"]["right_arm_joint_names"])
        right_msg.position = right

        self._left_pub.publish(left_msg)
        self._right_pub.publish(right_msg)
    def move_left_hand(self, data) -> None:
        hand_action = np.asarray(data, dtype=np.float64).reshape(-1)
        if hand_action.shape[0] != 6:
            raise ValueError(f"Control_hand expects 6 dims, got {hand_action.shape}")  

        left_hand = hand_action[:6].tolist()

        left_hand_msg = self._JointState()
        left_hand_msg.header.stamp = self._node.get_clock().now().to_msg()
        left_hand_msg.name = list(self.cfg["hands"]["left_hand_joint_names"])
        left_hand_msg.position = left_hand
        self._left_hand_pub.publish(left_hand_msg)

    def move_right_hand(self, data) -> None:
        hand_action = np.asarray(data, dtype=np.float64).reshape(-1)
        if hand_action.shape[0] != 6:
            raise ValueError(f"Control_hand expects 6 dims, got {hand_action.shape}")  

        right_hand = hand_action[:6].tolist()

        right_hand_msg = self._JointState()
        right_hand_msg.header.stamp = self._node.get_clock().now().to_msg()
        right_hand_msg.name = list(self.cfg["hands"]["right_hand_joint_names"])
        right_hand_msg.position = right_hand

        self._right_hand_pub.publish(right_hand_msg)

    #def move_right_hand(self, joints) -> None:
    #    joint_names = self.cfg.get("hands", {}).get("right_hand_joint_names", [])
    #    self._publish_joint_position(self._right_hand_pub, joint_names, joints)

    def move_head(self, data) -> None:
        head_action = np.asarray(data, dtype=np.float64).reshape(-1)
        # if head_action.shape[0] != 3:
        #     raise ValueError(f"Control_head expects 3 dims, got {head_action.shape}")  

        head = head_action[:3].tolist()

        head_msg = self._JointState()
        head_msg.header.stamp = self._node.get_clock().now().to_msg()
        head_msg.name = list(self.cfg["head"]["head_joint_names"])
        head_msg.position = head

        self._head_pub.publish(head_msg)

    def move_waist(self, data) -> None:
        waist_action = np.asarray(data, dtype=np.float64).reshape(-1)   
        if waist_action.shape[0] != 3:
            raise ValueError(f"Control_waist expects 3 dims, got {waist_action.shape}")  

        waist = waist_action[:3].tolist()

        waist_msg = self._JointState()
        waist_msg.header.stamp = self._node.get_clock().now().to_msg()
        waist_msg.name = list(self.cfg["waist"]["waist_joint_names"])
        waist_msg.position = waist

        self._waist_pub.publish(waist_msg)

    def move_leg(self, data) -> None:
        leg_action = np.asarray(data, dtype=np.float64).reshape(-1)
        if leg_action.shape[0] != 2:
            raise ValueError(f"Control_leg expects 2 dims, got {leg_action.shape}")  

        leg = leg_action[:2].tolist()

        leg_msg = self._JointState()
        leg_msg.header.stamp = self._node.get_clock().now().to_msg()
        leg_msg.name = list(self.cfg["leg"]["leg_joint_names"])
        leg_msg.position = leg

    '''
    def move_left_hand(self, joints) -> None:
        joint_names = self.cfg.get("hands", {}).get("left_hand_joint_names", [])
        self._publish_joint_position(self._left_hand_pub, joint_names, joints)

    def move_right_hand(self, joints) -> None:
        joint_names = self.cfg.get("hands", {}).get("right_hand_joint_names", [])
        self._publish_joint_position(self._right_hand_pub, joint_names, joints)

    def move_head(self, joints) -> None:
        joint_names = self.cfg.get("head", {}).get("head_joint_names", [])
        self._publish_joint_position(self._head_pub, joint_names, joints)

    def move_waist(self, joints) -> None:
        joint_names = self.cfg.get("waist", {}).get("waist_joint_names", [])
        self._publish_joint_position(self._waist_pub, joint_names, joints)

    def move_leg(self, joints) -> None:
        joint_names = self.cfg.get("leg", {}).get("leg_joint_names", [])
        self._publish_joint_position(self._leg_pub, joint_names, joints)

    '''
    def control_robot(self, action):
        action = np.asarray(action, dtype=np.float64).reshape(-1)
        if action.shape[0] < 14:
            raise ValueError(f"Ti5 control_robot expects >=14 dims, got {action.shape}")

        # Check ROS2 context is valid before publishing
        if not self._node_runner._rclpy.ok():
            return

        # Keep the same high-level contract as other robots: execute_action is the
        # unified "final dispatch" method.
        self.execute_action({"arm": action[:14].tolist()})
        
        # Handle hand/gripper based on actual action dimension
        # Standard VLA action: 14 arm + 2 gripper (left/right) = 16 dims
        # Full action: 14 arm + 12 hand + 3 head + 3 waist + 2 leg = 34 dims
        if action.shape[0] >= 20:
            # Full hand control (6 joints per hand)
            self.execute_action({"left_hand": action[14:20].tolist()})
            self.execute_action({"right_hand": action[20:26].tolist()})
        elif action.shape[0] >= 16:
            # Simple gripper control (1 value per gripper) - map to hand joints
            # Use the gripper value for all 6 hand joints as a simplified control
            left_gripper = float(action[14])
            right_gripper = float(action[15])
            # Map gripper value (0=open, 1=closed) to hand joints
            left_hand_cmd = [left_gripper] * 6
            right_hand_cmd = [right_gripper] * 6
            self.execute_action({"left_hand": left_hand_cmd})
            self.execute_action({"right_hand": right_hand_cmd})
        
        # Handle head if dimension available
        if action.shape[0] >= 29:
            self.execute_action({"head": action[26:29].tolist()})

    def execute_action(self, data):
        if not isinstance(data, dict):
            raise ValueError("execute_action expects a dict")

        if "arm" in data:
            self.move_arm(data["arm"])
        if "left_hand" in data:
            self.move_left_hand(data["left_hand"])
        if "right_hand" in data:
            self.move_right_hand(data["right_hand"])
        if "head" in data:
            self.move_head(data["head"])
        if "waist" in data:
            self.move_waist(data["waist"])
        if "leg" in data:
            self.move_leg(data["leg"])

    def retrieve_observation(self):
        with self._lock:
            if self._left_pos is None or self._right_pos is None:
                return None

            ref_timestamp = int(self._last_state_ns)
            if ref_timestamp <= 0:
                return None
            if ref_timestamp <= self._last_returned_state_ns:
                return None
            self._last_returned_state_ns = ref_timestamp

            obs_state_dim = int(getattr(self, "_obs_state_dim", 34))
            left_arm_slice = getattr(self, "_left_arm_slice", slice(0, 7))
            right_arm_slice = getattr(self, "_right_arm_slice", slice(7, 14))

            state = np.zeros(obs_state_dim, dtype=np.float64)
            state[left_arm_slice] = self._left_pos
            state[right_arm_slice] = self._right_pos
            left_hand_pos = getattr(self, "_left_hand_pos", None)
            right_hand_pos = getattr(self, "_right_hand_pos", None)
            head_pos = getattr(self, "_head_pos", None)
            waist_pos = getattr(self, "_waist_pos", None)
            leg_pos = getattr(self, "_leg_pos", None)

            if left_hand_pos is not None:
                state[self._left_hand_slice] = left_hand_pos
            if right_hand_pos is not None:
                state[self._right_hand_slice] = right_hand_pos
            # if head_pos is not None:
            #     state[self._neck_slice] = head_pos
            # if waist_pos is not None:
            #     state[self._waist_slice] = waist_pos
            # if leg_pos is not None:
            #     state[self._leg_slice] = leg_pos

            # Only log once, and only if ROS node logger is available.
            if not getattr(self, "_logged_unwired_obs_state_dims", False):
                missing = []
                if getattr(self, "_left_hand_pub", None) is None or getattr(self, "_right_hand_pub", None) is None:
                    missing.append("hands")
                if getattr(self, "_head_pub", None) is None:
                    missing.append("head")
                if getattr(self, "_waist_pub", None) is None:
                    missing.append("waist")
                if getattr(self, "_leg_pub", None) is None:
                    missing.append("leg")
                if missing and hasattr(self, "_node"):
                    self._node.get_logger().warning(
                        "Ti5_t170c obs.state is 34 dims; some groups are not wired and may stay 0: "
                        f"{', '.join(missing)}"
                    )
                self._logged_unwired_obs_state_dims = True

            self.current_state = state

            cam_head = self._resolve_cam_with_fallback("head", "cam.head")
            cam_hand_right = self._resolve_cam_with_fallback("hand_right", "cam.hand_right")
            cam_hand_left = self._resolve_cam_with_fallback("hand_left", "cam.hand_left")

            return {
                "ref_timestamp": ref_timestamp,
                "cam.head": cam_head,
                "cam.hand_right": cam_hand_right,
                "cam.hand_left": cam_hand_left,
                "obs.state": state,
            }

    def reset_robot(self, target_pose=None, mode="default"):

        if target_pose is None:
            if mode == 'default':
                target_pose = np.array(self.cfg['reset_robot_pos'])
            elif mode == 'zero':
                target_pose = np.array([0] * 14 + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0])
            else:
                print('[WARN] target_pose is None, can NOT execute reset_robot')
                return
        else:
            target_pose = np.array(target_pose)

        current_obs = self.retrieve_observation()
        current_positions = current_obs['obs.state'][:14]
        target_positions = target_pose[:14]
        # Calculate joint position differences
        dis = np.abs(current_positions - target_positions)
        mask = dis > np.deg2rad(0.01)  # Decide whether to use interpolation strategy
        # If difference is small, move directly to target position
        if not np.any(mask):
            self.execute_action({'arm': target_positions.tolist()})
            time.sleep(0.01)
            return
        trajs = self.ruckig_planning(current_positions, target_positions)
        for i, traj in enumerate(trajs):
            # print(f"Executing trajectory point {i}: {traj}")
            print(f'\r{i}', end='')
            self.execute_action({'arm': traj})
            time.sleep(0.01)
        
        self.execute_action({'left_hand': target_pose[14:20].tolist()})
        self.execute_action({'right_hand': target_pose[20:26].tolist()})

    def load_action_data(self, parquet_path, key="action"):
        """Load trajectory vectors from a parquet file.

        Args:
            parquet_path: Parquet file path.
            key: Column name to load, e.g. "action" or "observation.state".

        Returns:
            list[np.ndarray]: List of 1D float64 vectors.
        """
        df = pd.read_parquet(parquet_path)
        if key not in df.columns:
            raise KeyError(f"Key '{key}' not found in parquet columns: {list(df.columns)}")

        data = df[key].tolist()
        processed_data = []
        for ele in data:
            arr = np.asarray(ele, dtype=np.float64).reshape(-1)
            processed_data.append(arr)
        return processed_data

    def default_replay_trajectories(
        self,
        parquet_path,
        accelerate: bool = True,
        accelerate_times: int = 2,
        key: str = "action",
        sleep_s: float = 0.05,
    ):
        """Replay trajectory with fixed-rate stepping.

        Ti5 Phase-1 only executes arm commands (first 14 dims).
        """
        trajs = self.load_action_data(parquet_path=parquet_path, key=key)
        if not accelerate:
            accelerate_times = 1
        accelerate_times = max(1, int(accelerate_times))

        logged_non_arm_warning = False
        for idx, traj in enumerate(trajs):
            if idx % accelerate_times != 0:
                continue
            if traj.shape[0] < 14:
                if hasattr(self, "_node"):
                    self._node.get_logger().warning(
                        f"Skip trajectory index {idx}: dims={int(traj.shape[0])} < 14 "
                        "for Ti5 arm replay."
                    )
                continue
            if traj.shape[0] > 14 and not logged_non_arm_warning:
                if hasattr(self, "_node"):
                    self._node.get_logger().info(
                        "Ti5 replay currently executes arm only; non-arm dims will be ignored."
                    )
                logged_non_arm_warning = True
            self.execute_action({"arm": traj[:14].tolist()})
            self.execute_action({"left_hand": traj[14:20].tolist()})
            self.execute_action({"right_hand": traj[20:26].tolist()})
            self.execute_action({"head": traj[26:29].tolist()})
            time.sleep(float(sleep_s))

    def replay_trajectories(
        self,
        parquet_path,
        use_default: bool = True,
        accelerate: bool = True,
        accelerate_times: int = 2,
        exclude_path=None,
        key: str = "action",
        sleep_s: float = 0.05,
    ):
        """Replay trajectory loaded from parquet.

        Args:
            parquet_path: Teleop/parquet trajectory path.
            use_default: Use default replay logic.
            accelerate: Whether to skip points by accelerate_times.
            accelerate_times: Replay downsample ratio when accelerate=True.
            exclude_path: If any keyword appears in path, disable acceleration.
            key: Parquet column key to replay.
            sleep_s: Sleep between executed commands.
        """
        if exclude_path is None:
            exclude_path = ["place"]

        try:
            path_str = str(parquet_path)
            for ele in exclude_path:
                if str(ele) in path_str:
                    accelerate = False
                    break

            if use_default:
                self.default_replay_trajectories(
                    parquet_path=parquet_path,
                    accelerate=accelerate,
                    accelerate_times=accelerate_times,
                    key=key,
                    sleep_s=sleep_s,
                )
                return

            # Keep same behavior for now to ensure deterministic replay path.
            self.default_replay_trajectories(
                parquet_path=parquet_path,
                accelerate=accelerate,
                accelerate_times=accelerate_times,
                key=key,
                sleep_s=sleep_s,
            )
        except Exception as exc:
            if hasattr(self, "_node"):
                self._node.get_logger().error(
                    f"Replay {parquet_path} failed: {exc}"
                )
            raise

    def close(self):
        for _name, receiver in list(getattr(self, "_rgb_receivers", {}).items()):
            try:
                receiver.stop()
            except Exception:
                pass
        self._rgb_receivers.clear()
        self._node_runner.close()

