import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from message_center.msg import Jointpos
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
from collections import deque
import threading
import time
import numpy as np

_DEBUG_PRINT_INTERVAL = 1.0
_last_debug_time = 0.0


def _dprint(msg):
    global _last_debug_time
    now = time.time()
    if now - _last_debug_time >= _DEBUG_PRINT_INTERVAL:
        print(f"[DBG UnitreeG1Robot] {msg}")
        _last_debug_time = now


class UnitreeG1Robot(Node):
    """Unitree G1 机器人 ROS2 驱动（纯 ROS2 模式，纯灵巧手，无夹爪/腿部）

    26 维动作接口:
        action[0:7]   -> 左臂 (7 关节)
        action[7:14]  -> 右臂 (7 关节)
        action[14:20] -> 左手 (6 手指)
        action[20:26] -> 右手 (6 手指)
    """

    def __init__(self):
        super().__init__("unitree_g1_robot_node")

        # ======================
        # 订阅话题（状态读取）
        # ======================
        self.topic_joint_states = "/joint_state"
        self.topic_left_hand = "/left_hand/get_angle"
        self.topic_right_hand = "/right_hand/get_angle"

        # ======================
        # 发布话题（控制输出）
        # ======================
        self.topic_left_arm_cmd = "/left_arm/joint_pos"
        self.topic_right_arm_cmd = "/right_arm/joint_pos"
        self.topic_left_hand_cmd = "/left_hand/set_angle"
        self.topic_right_hand_cmd = "/right_hand/set_angle"

        print(f"[DBG UnitreeG1Robot] Subscribed topics:")
        print(f"[DBG UnitreeG1Robot]   - {self.topic_joint_states}")
        print(f"[DBG UnitreeG1Robot]   - {self.topic_left_hand}")
        print(f"[DBG UnitreeG1Robot]   - {self.topic_right_hand}")
        print(f"[DBG UnitreeG1Robot]   (pubs: {self.topic_left_arm_cmd}, {self.topic_right_arm_cmd}, {self.topic_left_hand_cmd}, {self.topic_right_hand_cmd})")

        # 最新状态缓存
        self.latest_left_arm = None
        self.latest_right_arm = None
        self.latest_left_hand = None
        self.latest_right_hand = None

        # 队列缓存（用于时间戳对齐）
        self.queue_left_arm = deque(maxlen=30)
        self.queue_right_arm = deque(maxlen=30)
        self.queue_left_hand = deque(maxlen=30)
        self.queue_right_hand = deque(maxlen=30)

        # QoS 匹配机器人驱动
        qos_correct = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=10
        )
        qos_pub = QoSProfile(depth=10)

        # ======================
        # 订阅（读取状态）
        # ======================
        self.create_subscription(JointState, self.topic_joint_states, self._cb_joint_states, qos_correct)
        self.create_subscription(JointState, self.topic_left_hand, self._cb_left_hand, qos_correct)
        self.create_subscription(JointState, self.topic_right_hand, self._cb_right_hand, qos_correct)

        # ======================
        # 发布（控制机器人）
        # ======================
        self.pub_left_arm = self.create_publisher(Jointpos, self.topic_left_arm_cmd, qos_pub)
        self.pub_right_arm = self.create_publisher(Jointpos, self.topic_right_arm_cmd, qos_pub)
        self.pub_left_hand = self.create_publisher(JointState, self.topic_left_hand_cmd, qos_pub)
        self.pub_right_hand = self.create_publisher(JointState, self.topic_right_hand_cmd, qos_pub)

        # 固定关节名
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

        self.running = True

        # ######################
        # 新增: 去重标记，避免采样线程重复入队相同时间戳的数据
        # ######################
        self._last_queue_ts_left_arm = 0.0
        self._last_queue_ts_right_arm = 0.0
        self._last_queue_ts_left_hand = 0.0
        self._last_queue_ts_right_hand = 0.0

        # 采样线程
        self.sample_thread = threading.Thread(target=self._sample_loop, daemon=True)
        self.sample_thread.start()

        self.get_logger().info("UnitreeG1Robot ready")

    # ======================
    # 【核心控制函数】26 维动作输入
    # ======================
    def send_robot_action(self, action):
        """发送 26 维动作到机器人

        Args:
            action (array-like): [左臂7, 右臂7, 左手6, 右手6]
        """
        action = np.asarray(action).flatten()
        left_arm_act = action[0:7]
        right_arm_act = action[7:14]
        left_hand_act = action[14:20]
        right_hand_act = action[20:26]

        # 左臂
        if left_arm_act[-1] > -100:
            msg = Jointpos()
            msg.joint = left_arm_act.tolist()
            msg.type = 1  # left arm
            msg.dof = 7
            self.pub_left_arm.publish(msg)

        # 右臂
        if right_arm_act[-1] > -100:
            msg = Jointpos()
            msg.joint = right_arm_act.tolist()
            msg.type = 2  # right arm
            msg.dof = 7
            self.pub_right_arm.publish(msg)

        # 左手（带防抖：差值 > 50 才发送）
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

        # 右手（带防抖：差值 > 50 才发送）
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
    # 订阅回调
    # ======================
    def _cb_joint_states(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

        # 按 joint name 构建 name->index 映射
        name_to_idx = {name: i for i, name in enumerate(msg.name)}

        # 按名称提取左臂位置
        left_positions = []
        for name in self.left_arm_joint_names:
            if name in name_to_idx:
                left_positions.append(msg.position[name_to_idx[name]])

        # 按名称提取右臂位置
        right_positions = []
        for name in self.right_arm_joint_names:
            if name in name_to_idx:
                right_positions.append(msg.position[name_to_idx[name]])

        # 构造合成 JointState 保持下游兼容
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
    # 采样线程
    # ======================
    def _sample_loop(self):
        print("[DBG UnitreeG1Robot] _sample_loop started")
        loop_count = 0
        while self.running:
            loop_count += 1
            # ######################
            # 修改: 时间戳去重（浮点比较使用 1ms 阈值）
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
    # 时间戳对齐
    # ======================
    def _find_nearest(self, queue, target_ts):
        if not queue:
            return (None, 0.0)
        return min(queue, key=lambda x: abs(x[1] - target_ts))

    def get_arm_hand_states_nearest_func(self, ref_timestamp):
        """以 ref_timestamp 为基准，对齐左右臂/手的状态

        Args:
            ref_timestamp (float): 参考时间戳（通常来自头部相机）

        Returns:
            dict: 包含各部位状态和时间戳
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
# main：纯机器人驱动测试（无需相机）
# ==============================================
def main():
    rclpy.init()

    robot = UnitreeG1Robot()

    # 启动自旋线程，让 ROS2 回调正常工作
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
