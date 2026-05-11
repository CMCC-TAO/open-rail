import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, Bool
from sensor_msgs.msg import JointState
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
from collections import deque
import threading
import time
import numpy as np

class Ti5Robot(Node):
    def __init__(self):
        super().__init__("ti5_robot_node")

        # ======================
        # 订阅话题（状态读取）
        # ======================
        # self.hand_cmd_counter = 0

        self.current_right_hand_state = None
        self.current_left_hand_state = None
        self.arm_mode = 'ros' # ros

        if self.arm_mode != 'ros':
            from .tianji.tj_dual_arm import TJDualArm
            self.tj_arm = TJDualArm()

        if self.arm_mode == 'ros':  
            self.topic_left_arm = "/left_arm/joint_states"
            self.topic_right_arm = "/right_arm/joint_states"
        self.topic_left_hand = "/left_hand/angle_state"
        self.topic_right_hand = "/right_hand/angle_state"
        self.topic_leg_pos = "/leg_motor/joint_states"

        # ======================
        # 发布话题（控制输出）
        # ======================
        self.topic_head_cmd = "/head_motor/joint_cmd"

        if self.arm_mode == 'ros':
            self.topic_left_arm_cmd = "/left_arm/joint_cmd"
            self.topic_right_arm_cmd = "/right_arm/joint_cmd"

        self.topic_left_hand_cmd = "/left_hand/angle_cmd"
        self.topic_right_hand_cmd = "/right_hand/angle_cmd"
        self.topic_leg_cmd = "/leg_motor/set_height"

        # 最新状态缓存
        self.latest_left_arm = None
        self.latest_right_arm = None
        self.latest_left_hand = None
        self.latest_right_hand = None
        self.latest_leg_pos = None

        # 队列缓存
        if self.arm_mode == 'ros':
            self.queue_left_arm = deque(maxlen=30)
            self.queue_right_arm = deque(maxlen=30)
        self.queue_left_hand = deque(maxlen=30)
        self.queue_right_hand = deque(maxlen=30)
        self.queue_leg = deque(maxlen=30)

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

        if self.arm_mode == 'ros':
            self.create_subscription(JointState, self.topic_left_arm, self._cb_left_arm, qos_correct)
            self.create_subscription(JointState, self.topic_right_arm, self._cb_right_arm, qos_correct)
        self.create_subscription(JointState, self.topic_left_hand, self._cb_left_hand, qos_correct)
        self.create_subscription(JointState, self.topic_right_hand, self._cb_right_hand, qos_correct)
        self.create_subscription(JointState, self.topic_leg_pos, self._cb_leg_pos, qos_correct)
        # ======================
        # 发布（控制机器人）
        # ======================
        
        if self.arm_mode == 'ros':
            self.pub_left_arm = self.create_publisher(JointState, self.topic_left_arm_cmd, qos_pub)
            self.pub_right_arm = self.create_publisher(JointState, self.topic_right_arm_cmd, qos_pub)
        self.pub_left_hand = self.create_publisher(JointState, self.topic_left_hand_cmd, qos_pub)
        self.pub_right_hand = self.create_publisher(JointState, self.topic_right_hand_cmd, qos_pub)
        self.pub_leg = self.create_publisher(Float64MultiArray, self.topic_leg_cmd, qos_pub)

        # 固定关节名

        if self.arm_mode == 'ros':
            self.left_arm_joint_names = [
                "L_SHOULDER_P_JOINT",
                "L_SHOULDER_R_JOINT",
                "L_SHOULDER_Y_JOINT",
                "L_ELBOW_JOINT",
                "L_WRIST_Y_JOINT",
                "L_WRIST_R_JOINT",
                "L_WRIST_P_JOINT",
            ]

            self.right_arm_joint_names = [
                "R_SHOULDER_P_JOINT",
                "R_SHOULDER_R_JOINT",
                "R_SHOULDER_Y_JOINT",
                "R_ELBOW_JOINT",
                "R_WRIST_Y_JOINT",
                "R_WRIST_R_JOINT",
                "R_WRIST_P_JOINT",
            ]
        
        self.hand_joint_names = ["thumb", "index", "middle", "ring", "pinky", "thumb_rotation"]


        self.running = True

        # 采样线程
        self.sample_thread = threading.Thread(target=self._sample_loop, daemon=True)
        self.sample_thread.start()

        self.get_logger().info("✅ Ti5Robot 已启动：读取 + 控制 全部就绪")

    def clear_state_buffer(self):
        self.queue_head.clear()

        if self.arm_mode == 'ros':
            self.queue_left_arm.clear()
            self.queue_right_arm.clear()
        self.queue_left_hand.clear()

        self.queue_right_hand.clear()
        self.queue_waist.clear()
        self.queue_leg.clear()


    # ======================
    # 【核心控制函数】26维动作输入
    # ======================
    def send_robot_action(self, action):
        action = np.asarray(action).flatten()
        left_arm_act = action[0:7]
        right_arm_act = action[7:14]
        left_hand_act = action[14:20]
        right_hand_act = action[20:26]
        try:
            leg_act = action[26:27]
        except:
            leg_act = None

        # 左臂
        if left_arm_act[-1] > -100:
            if self.arm_mode == 'ros':
                msg = JointState()
                msg.name = self.left_arm_joint_names
                msg.position = left_arm_act.tolist()
                self.pub_left_arm.publish(msg)
            else:
                left_arm_joints = {'left_arm':left_arm_act}
                self.tj_arm.set_joints(left_arm_joints)

        # 右臂
        if right_arm_act[-1] > -100:

            if self.arm_mode == 'ros':
                msg = JointState()
                msg.name = self.right_arm_joint_names
                msg.position = right_arm_act.tolist()
                self.pub_right_arm.publish(msg)
            else:
                right_arm_joints = {'right_arm':right_arm_act}
                self.tj_arm.set_joints(right_arm_joints)

        # 左手
        if left_hand_act[-1] > -100:
            # if self.hand_cmd_counter > 100000:
            #     self.hand_cmd_counter = 0
            # if self.hand_cmd_counter % 5 == 0:
            
            if self.current_left_hand_state is not None:
                left_diff = np.abs(left_hand_act - self.current_left_hand_state).sum()
            else:
                left_diff = 0
            if self.current_left_hand_state is None or left_diff > 50:
                # print("###"*30)
                # print(left_diff)
                msg = JointState()
                msg.name = self.hand_joint_names
                msg.position = left_hand_act.tolist()
                self.pub_left_hand.publish(msg)
                self.current_left_hand_state = left_hand_act
                # self.hand_cmd_counter += 1


        # 右手
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

        # 腿
        if leg_act is not None:
            msg = Float64MultiArray()
            msg.data = leg_act.tolist()
            self.pub_leg.publish(msg)


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
    def _cb_leg_pos(self, msg):
        self.latest_leg_pos = msg


    # ======================
    # 30fps 采样
    # ======================
    def _sample_loop(self):
        while self.running:
            start = time.time()
            if self.latest_left_arm:
                self.queue_left_arm.append(self.latest_left_arm)
            if self.latest_right_arm:
                self.queue_right_arm.append(self.latest_right_arm)
            if self.latest_left_hand:
                self.queue_left_hand.append(self.latest_left_hand)
            if self.latest_right_hand:
                self.queue_right_hand.append(self.latest_right_hand)

            elapsed = time.time() - start
            time.sleep(0.002)
            # if elapsed < 1/100:
            #     time.sleep(1/100 - elapsed)

    # ======================
    # 时间戳对齐
    # ======================
    def _find_nearest(self, queue, target_ts):
        if not queue:
            return (None, 0.0)
        return min(queue, key=lambda x: abs(x[1] - target_ts))

    def get_arm_hand_states_nearest_func(self, ref_timestamp):
        if self.arm_mode == 'ros':
            left_arm, left_arm_ts = self._find_nearest(self.queue_left_arm, ref_timestamp)
            right_arm, right_arm_ts = self._find_nearest(self.queue_right_arm, ref_timestamp)
        else:
            arm_state = self.tj_arm.get_current_joints()
            left_arm = arm_state['left_arm'].tolist()
            right_arm = arm_state['right_arm'].tolist()
            left_arm_ts = arm_state['timestamp']
            right_arm_ts = arm_state['timestamp']
        left_hand, left_hand_ts = self._find_nearest(self.queue_left_hand, ref_timestamp)
        right_hand, right_hand_ts = self._find_nearest(self.queue_right_hand, ref_timestamp)

        return {
            "left_arm": left_arm,
            "right_arm": right_arm,
            "left_hand": left_hand,
            "right_hand": right_hand,
            "leg_pos": self.latest_leg_pos,
            "ref_timestamp": ref_timestamp,
            "left_arm_timestamp": left_arm_ts,
            "right_arm_timestamp": right_arm_ts,
            "left_hand_timestamp": left_hand_ts,
            "right_hand_timestamp": right_hand_ts
        }

    def stop(self):
        self.running = False

# ==============================================
# main：统一管理两个节点 + 统一 spin + 动作控制测试
# ==============================================
def main():
    rclpy.init()

    from Ti5Camera import Ti5Camera
    print("⏳ 启动 Ti5Camera + Ti5Robot...")
    camera = Ti5Camera()
    robot = Ti5Robot()

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
    action = [-1.0072, 1.4473, 1.6156, -1.8399, -0.4101, -0.2185, -0.3232, 1.0072, 1.4473, -1.6156, -1.8399, 0.4101, -0.2252, 0.3232, -1000.0, -1000.0, -1000.0, -1000.0, -1000.0, -1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 0.6]
    
    robot.send_robot_action(action)
    print(f"✅ 动作已发送！")
    print("==================================================")

    time.sleep(1.5)

    # 退出
    running = False
    robot.stop()
    print("\n🎉 全部测试成功！")

if __name__ == '__main__':
    main()
