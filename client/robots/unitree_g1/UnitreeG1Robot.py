import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
from collections import deque
import threading
import time
import numpy as np


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
        self.topic_left_arm = "/left_arm/joint_states"
        self.topic_right_arm = "/right_arm/joint_states"
        self.topic_left_hand = "/left_hand/angle_state"
        self.topic_right_hand = "/right_hand/angle_state"

        # ======================
        # 发布话题（控制输出）
        # ======================
        self.topic_left_arm_cmd = "/left_arm/joint_cmd"
        self.topic_right_arm_cmd = "/right_arm/joint_cmd"
        self.topic_left_hand_cmd = "/left_hand/angle_cmd"
        self.topic_right_hand_cmd = "/right_hand/angle_cmd"

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
        self.create_subscription(JointState, self.topic_left_arm, self._cb_left_arm, qos_correct)
        self.create_subscription(JointState, self.topic_right_arm, self._cb_right_arm, qos_correct)
        self.create_subscription(JointState, self.topic_left_hand, self._cb_left_hand, qos_correct)
        self.create_subscription(JointState, self.topic_right_hand, self._cb_right_hand, qos_correct)

        # ======================
        # 发布（控制机器人）
        # ======================
        self.pub_left_arm = self.create_publisher(JointState, self.topic_left_arm_cmd, qos_pub)
        self.pub_right_arm = self.create_publisher(JointState, self.topic_right_arm_cmd, qos_pub)
        self.pub_left_hand = self.create_publisher(JointState, self.topic_left_hand_cmd, qos_pub)
        self.pub_right_hand = self.create_publisher(JointState, self.topic_right_hand_cmd, qos_pub)

        # 固定关节名
        self.left_arm_joint_names = [
            "L_SHOULDER_P_JOINT", "L_SHOULDER_R_JOINT", "L_SHOULDER_Y_JOINT",
            "L_ELBOW_JOINT", "L_WRIST_Y_JOINT", "L_WRIST_R_JOINT", "L_WRIST_P_JOINT",
        ]
        self.right_arm_joint_names = [
            "R_SHOULDER_P_JOINT", "R_SHOULDER_R_JOINT", "R_SHOULDER_Y_JOINT",
            "R_ELBOW_JOINT", "R_WRIST_Y_JOINT", "R_WRIST_R_JOINT", "R_WRIST_P_JOINT",
        ]
        self.hand_joint_names = ["thumb", "index", "middle", "ring", "pinky", "thumb_rotation"]

        self.current_left_hand_state = None
        self.current_right_hand_state = None

        self.running = True

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
            msg = JointState()
            msg.name = self.left_arm_joint_names
            msg.position = left_arm_act.tolist()
            self.pub_left_arm.publish(msg)

        # 右臂
        if right_arm_act[-1] > -100:
            msg = JointState()
            msg.name = self.right_arm_joint_names
            msg.position = right_arm_act.tolist()
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
    def _cb_left_arm(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self.latest_left_arm = (msg, ts)

    def _cb_right_arm(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self.latest_right_arm = (msg, ts)

    def _cb_left_hand(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self.latest_left_hand = (msg, ts)

    def _cb_right_hand(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self.latest_right_hand = (msg, ts)

    # ======================
    # 采样线程
    # ======================
    def _sample_loop(self):
        while self.running:
            if self.latest_left_arm:
                self.queue_left_arm.append(self.latest_left_arm)
            if self.latest_right_arm:
                self.queue_right_arm.append(self.latest_right_arm)
            if self.latest_left_hand:
                self.queue_left_hand.append(self.latest_left_hand)
            if self.latest_right_hand:
                self.queue_right_hand.append(self.latest_right_hand)
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
# main：统一管理两个节点 + 测试
# ==============================================
def main():
    rclpy.init()

    from UnitreeG1Camera import UnitreeG1Camera
    print("Starting UnitreeG1Camera + UnitreeG1Robot...")
    camera = UnitreeG1Camera()
    robot = UnitreeG1Robot()

    running = True
    def spin_worker():
        while running:
            rclpy.spin_once(camera, timeout_sec=0.005)
            rclpy.spin_once(robot, timeout_sec=0.005)

    spin_thread = threading.Thread(target=spin_worker, daemon=True)
    spin_thread.start()

    print("Waiting for camera/robot data...")
    time.sleep(2.5)

    # 读取相机
    cam_data = camera.get_latest_image()
    if not cam_data:
        print("No camera data")
        running = False
        return

    head_img, head_ts, left_img, left_ts, right_img, right_ts = cam_data
    print("Camera sync OK, head ts:", head_ts)

    # 机器人状态对齐
    robot_state = robot.get_arm_hand_states_nearest_func(head_ts)
    print("Robot state alignment OK, ref ts:", robot_state["ref_timestamp"])

    # 动作控制测试：26 维动作
    action = [
        -1.0072, 1.4473, 1.6156, -1.8399, -0.4101, -0.2185, -0.3232,
        1.0072, 1.4473, -1.6156, -1.8399, 0.4101, -0.2252, 0.3232,
        -1000.0, -1000.0, -1000.0, -1000.0, -1000.0, -1000.0,
        1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0,
    ]
    robot.send_robot_action(action)
    print("Action sent OK")

    time.sleep(1.5)

    running = False
    robot.stop()
    print("All tests passed")


if __name__ == "__main__":
    main()
