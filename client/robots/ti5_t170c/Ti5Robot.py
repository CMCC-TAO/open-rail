import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
from collections import deque
import threading
import time
import numpy as np
from ml_collections import ConfigDict

# ====== 新增：导入String消息类型 ======
from std_msgs.msg import String


class Ti5Robot(Node):
    def __init__(self, config):
        super().__init__("ti5_robot_node")

        # ======================
        # 订阅话题（状态读取）
        # ======================
        # self.topic_left_arm = "/left_arm/joint_states"
        # self.topic_right_arm = "/right_arm/joint_states"
        # self.topic_left_hand = "/left_hand/angle_state"
        # self.topic_right_hand = "/right_hand/angle_state"
        self.topic_left_arm = config.arms.left_arm_joint_states_topic
        self.topic_right_arm = config.arms.right_arm_joint_states_topic
        self.topic_left_hand = config.hands.left_hand_joint_states_topic
        self.topic_right_hand = config.hands.right_hand_joint_states_topic
        
        # ====== 新增：交互机器人语音唤醒专用ros话题 ======
        self.topic_wake_up = "/robot/listen/wake_up"

        # ======================
        # 发布话题（控制输出）
        # ======================
        # self.topic_left_arm_cmd = "/left_arm/joint_cmd"
        # self.topic_right_arm_cmd = "/right_arm/joint_cmd"
        # self.topic_left_hand_cmd = "/left_hand/angle_cmd"
        # self.topic_right_hand_cmd = "/right_hand/angle_cmd"
        # self.topic_head_cmd = "/head_motor/joint_cmd"
        # self.topic_waist_cmd = "/waist_motor/joint_cmd"
        self.topic_left_arm_cmd = config.arms.left_arm_joint_cmd_topic
        self.topic_right_arm_cmd = config.arms.right_arm_joint_cmd_topic
        self.topic_left_hand_cmd = config.hands.left_hand_joint_cmd_topic
        self.topic_right_hand_cmd = config.hands.right_hand_joint_cmd_topic 
        self.topic_head_cmd = config.head.head_joint_cmd_topic
        self.topic_waist_cmd = config.waist.waist_joint_cmd_topic

        # 最新状态缓存
        self.latest_left_arm = None
        self.latest_right_arm = None
        self.latest_left_hand = None
        self.latest_right_hand = None
        # ====== 新增：唤醒消息缓存 ======
        self.latest_wake_up = None

        # 队列缓存
        self.queue_left_arm = deque(maxlen=30)
        self.queue_right_arm = deque(maxlen=30)
        self.queue_left_hand = deque(maxlen=30)
        self.queue_right_hand = deque(maxlen=30)
        self.state_lock = threading.Lock()

        # QoS 匹配机器人
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
        # ====== 新增：订阅唤醒话题 ======
        self.create_subscription(String, self.topic_wake_up, self._cb_wake_up, qos_correct)

        # ======================
        # 发布（控制机器人）
        # ======================
        self.pub_left_arm = self.create_publisher(JointState, self.topic_left_arm_cmd, qos_pub)
        self.pub_right_arm = self.create_publisher(JointState, self.topic_right_arm_cmd, qos_pub)
        self.pub_left_hand = self.create_publisher(JointState, self.topic_left_hand_cmd, qos_pub)
        self.pub_right_hand = self.create_publisher(JointState, self.topic_right_hand_cmd, qos_pub)
        self.pub_head = self.create_publisher(JointState, self.topic_head_cmd, qos_pub)
        self.pub_waist = self.create_publisher(JointState, self.topic_waist_cmd, qos_pub)

        # 固定关节名
        # self.left_arm_joint_names = [
        #     "L_SHOULDER_P_JOINT",
        #     "L_SHOULDER_R_JOINT",
        #     "L_SHOULDER_Y_JOINT",
        #     "L_ELBOW_JOINT",
        #     "L_WRIST_Y_JOINT",
        #     "L_WRIST_R_JOINT",
        #     "L_WRIST_P_JOINT",
        # ]
        self.left_arm_joint_names = config.arms.left_arm_joint_names

        # self.right_arm_joint_names = [
        #     "R_SHOULDER_P_JOINT",
        #     "R_SHOULDER_R_JOINT",
        #     "R_SHOULDER_Y_JOINT",
        #     "R_ELBOW_JOINT",
        #     "R_WRIST_Y_JOINT",
        #     "R_WRIST_R_JOINT",
        #     "R_WRIST_P_JOINT",
        # ]
        self.right_arm_joint_names = config.arms.right_arm_joint_names
        
        # self.hand_joint_names = ["pinky", "ring", "middle", "index", "thumb", "thumb_rot"]
        # self.head_joint_names = ["NECK_Y_JOINT", "NECK_P_JOINT", "NECK_R_JOINT"]
        # self.waist_joint_names = ["WAIST_Y_JOINT", "WAIST_R_JOINT", "WAIST_P_JOINT"]
        self.hand_joint_names = config.hands.hand_joint_names
        self.head_joint_names = config.head.head_joint_names
        self.waist_joint_names = config.waist.waist_joint_names

        self.running = True

        # 采样线程
        self.sample_thread = threading.Thread(target=self._sample_loop, daemon=True)
        self.sample_thread.start()

        self.get_logger().info("✅ Ti5Robot 已启动：状态读取 + 电机控制 全部就绪")

    # ======================
    # 【新增】唤醒话题回调函数  
    # ======================
    def _cb_wake_up(self, msg):
        """
        接收 /robot/listen/wake_up 字符串消息
        消息内容存在 msg.data 中
        """
        ts = self.get_clock().now().nanoseconds / 1e9  # 本机时间戳
        with self.state_lock:
            self.latest_wake_up = (msg.data, ts)
        self.get_logger().info(f"🔔 收到唤醒指令：{msg.data}")

    # ======================
    # 【新增】获取最新唤醒指令（外部调用）
    # ======================
    def get_latest_wake_up(self):
        """
        返回：(指令字符串, 时间戳)
        如果未收到过，返回 (None, None)
        """
        with self.state_lock:
            if self.latest_wake_up is None:
                return (None, None)
            return self.latest_wake_up

    # ======================
    # 【核心控制函数】26维动作输入
    # ======================
    def send_robot_action(self, action):
        action = np.asarray(action).flatten()

        left_arm_act = action[0:7]
        right_arm_act = action[7:14]
        left_hand_act = action[14:20]
        right_hand_act = action[20:26]

        # 左臂
        msg = JointState()
        msg.name = self.left_arm_joint_names
        msg.position = left_arm_act.tolist()
        self.pub_left_arm.publish(msg)

        # 右臂
        msg = JointState()
        msg.name = self.right_arm_joint_names
        msg.position = right_arm_act.tolist()
        self.pub_right_arm.publish(msg)

        # 左手
        msg = JointState()
        msg.name = self.hand_joint_names
        msg.position = left_hand_act.tolist()
        self.pub_left_hand.publish(msg)

        # 右手
        msg = JointState()
        msg.name = self.hand_joint_names
        msg.position = right_hand_act.tolist()
        self.pub_right_hand.publish(msg)

    def send_partial_action(self, part_name, action):
        action = np.asarray(action).flatten()

        # 左臂
        if part_name == "left_arm":
            assert len(action) == 7, "左臂动作长度必须是 7..."
            msg = JointState()
            msg.name = self.left_arm_joint_names
            msg.position = action.tolist()
            self.pub_left_arm.publish(msg)
        elif part_name == "right_arm":
            assert len(action) == 7, "右臂动作长度必须是 7..."
            msg = JointState()
            msg.name = self.right_arm_joint_names
            msg.position = action.tolist()
            self.pub_right_arm.publish(msg)
        elif part_name == "left_hand":
            assert len(action) == 6, "左手动作长度必须是 6..."
            msg = JointState()
            msg.name = self.hand_joint_names
            msg.position = action.tolist()
            self.pub_left_hand.publish(msg)
        elif part_name == "right_hand":
            assert len(action) == 6, "右手动作长度必须是 6..."
            msg = JointState()
            msg.name = self.hand_joint_names
            msg.position = action.tolist()
            self.pub_right_hand.publish(msg)
        elif part_name == "head":
            print("#"*60)
            assert len(action) == 3, "头部动作长度必须是 3..."
            msg = JointState()
            msg.name = self.head_joint_names
            msg.position = action.tolist()
            self.pub_head.publish(msg)
        elif part_name == "waist":
            print("="*60)
            assert len(action) == 3, "腰部动作长度必须是 3..."
            msg = JointState()
            msg.name = self.waist_joint_names
            msg.position = action.tolist()
            self.pub_waist.publish(msg)
        else:
            pass

    # ======================
    # 订阅回调
    # ======================
    def _cb_left_arm(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        with self.state_lock:
            self.latest_left_arm = (msg, ts)

    def _cb_right_arm(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        with self.state_lock:
            self.latest_right_arm = (msg, ts)

    def _cb_left_hand(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        with self.state_lock:
            self.latest_left_hand = (msg, ts)

    def _cb_right_hand(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        with self.state_lock:
            self.latest_right_hand = (msg, ts)

    # ======================
    # 30fps 采样
    # ======================
    def _sample_loop(self):
        while self.running:
            start = time.time()
            with self.state_lock:
                if self.latest_left_arm:
                    self.queue_left_arm.append(self.latest_left_arm)
                if self.latest_right_arm:
                    self.queue_right_arm.append(self.latest_right_arm)
                if self.latest_left_hand:
                    self.queue_left_hand.append(self.latest_left_hand)
                if self.latest_right_hand:
                    self.queue_right_hand.append(self.latest_right_hand)

            elapsed = time.time() - start
            if elapsed < 1/30:
                time.sleep(1/30 - elapsed)

    # ======================
    # 时间戳对齐
    # ======================
    def _find_nearest(self, queue, target_ts):
        with self.state_lock:
            queue_snapshot = list(queue)
        if not queue_snapshot:
            return (None, 0.0)
        return min(queue_snapshot, key=lambda x: abs(x[1] - target_ts))

    def get_arm_hand_states_nearest_func(self, ref_timestamp):
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
            "right_hand_timestamp": right_hand_ts
        }

    def stop(self):
        self.running = False



def get_ti5_t170c_config():
    """Generate configuration for Ti5 T170C robot (ROS2 bridge)."""
    config = ConfigDict()

    config.camera = ConfigDict()
    config.camera.head_camera_topic = "/camera/d435i/color/image_raw"
    config.camera.left_hand_camera_topic = "/camera/d405_1/color/image_raw"
    config.camera.right_hand_camera_topic = "/camera/d405_2/color/image_raw"

    config.arms = ConfigDict()
    config.arms.left_arm_joint_cmd_topic = "/left_arm/joint_cmd"
    config.arms.right_arm_joint_cmd_topic = "/right_arm/joint_cmd"
    config.arms.left_arm_joint_states_topic = "/left_arm/joint_states"
    config.arms.right_arm_joint_states_topic = "/right_arm/joint_states"

    config.arms.left_arm_joint_names = [
        "L_SHOULDER_P_JOINT",
        "L_SHOULDER_R_JOINT",
        "L_SHOULDER_Y_JOINT",
        "L_ELBOW_JOINT",
        "L_WRIST_Y_JOINT",
        "L_WRIST_R_JOINT",
        "L_WRIST_P_JOINT",
    ]
    config.arms.right_arm_joint_names = [
        "R_SHOULDER_P_JOINT",
        "R_SHOULDER_R_JOINT",
        "R_SHOULDER_Y_JOINT",
        "R_ELBOW_JOINT",
        "R_WRIST_Y_JOINT",
        "R_WRIST_R_JOINT",
        "R_WRIST_P_JOINT",
    ]

    config.hands = ConfigDict()
    config.hands.left_hand_joint_cmd_topic = "/left_hand/angle_cmd"
    config.hands.right_hand_joint_cmd_topic = "/right_hand/angle_cmd"
    config.hands.left_hand_joint_states_topic = "/left_hand/angle_state"
    config.hands.right_hand_joint_states_topic = "/right_hand/angle_state"

    config.hands.hand_joint_names = [
        "pinky", "ring", "middle", "index", "thumb", "thumb_rot"
    ]

    config.waist = ConfigDict()
    config.waist.waist_joint_cmd_topic = "/waist_motor/joint_cmd"
    config.waist.waist_joint_states_topic = "/waist_motor/joint_states"

    config.waist.waist_joint_names = [
        "WAIST_Y_JOINT", "WAIST_R_JOINT", "WAIST_P_JOINT"
    ]

    config.head = ConfigDict()
    config.head.head_joint_cmd_topic = "/head_motor/joint_cmd"
    config.head.head_joint_states_topic = "/head_motor/joint_states"

    config.head.head_joint_names = [
        "NECK_Y_JOINT", "NECK_P_JOINT", "NECK_R_JOINT"
    ]

    config.reset_robot_pos = \
      [
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

    config.zero_pos = \
      [
        -1.681951211214541, 1.5263110171042418, 2.2737134617553534, -0.23620356347006893, -0.5204031154482495, 0.1292378813793631, 0.19059726269759902
      ] + \
      [
        1.4875488405961936, 1.5339806547275607, -1.4787018194549504, -0.32055631145539876, 0.1102380912144111, -0.05337579029191015, 0.20508064790415614
      ] + \
      [
        1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0
      ] + \
      [
        1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0
      ]

    return config



# ==============================================
# main：统一管理两个节点 + 统一 spin + 动作控制测试
# ==============================================
def main():
    config = get_ti5_t170c_config()
    rclpy.init()

    from Ti5Camera import Ti5Camera
    print("⏳ 启动 Ti5Camera + Ti5Robot...")
    camera = Ti5Camera(config)
    robot = Ti5Robot(config)

    # ======================
    # 统一自旋线程
    # ======================
    running = True
    def spin_worker():
        while running:
            rclpy.spin_once(camera, timeout_sec=0.005)
            rclpy.spin_once(robot, timeout_sec=0.005)

    spin_thread = threading.Thread(target=spin_worker, daemon=True)
    spin_thread.start()

    print("⏳ 等待相机、机器人数据...")
    time.sleep(2.5)

    # ======================
    # 读取相机
    # ======================
    cam_data = camera.get_latest_image()
    if not cam_data:
        print("❌ 未读到相机数据")
        running = False
        return

    head_img, head_ts, left_img, left_ts, right_img, right_ts = cam_data
    print("\n✅ 相机同步完成")
    print(f"  头部时间戳: {head_ts:.6f}, Shape: {head_img.shape}")

    # ======================
    # 机器人状态对齐
    # ======================
    robot_state = robot.get_arm_hand_states_nearest_func(head_ts)
    print("\n✅ 机器人状态对齐完成")
    print(f"  基准时间: {robot_state['ref_timestamp']:.6f}")

    # ======================
    # 动作控制测试
    # ======================
    print("\n==================================================")
    print("🤖 测试：发送26维动作 → 右手握拳")
    action = [
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
    
    robot.send_robot_action(action)
    print(f"✅ 动作已发送！")
    print("==================================================")

    VLA_head_pos = [0.0, 0.0, 0.0]
    hand_pos = [
        650.0, 650.0, 650.0, 650.0, 650.0, 250.0
      ] 
    robot.send_partial_action("head", VLA_head_pos)
    print(f"✅ 头部动作已发送！")
    print("==================================================")

    time.sleep(1.5)

    # 退出
    # running = False
    # robot.stop()
    print("\n🎉 全部测试成功！")

    # while True:
    #     time.sleep(0.2)
    #     a = robot.get_latest_wake_up()
    #     print(a)

if __name__ == '__main__':
    main()
