import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os
import threading
import time
from collections import deque
from ml_collections import ConfigDict

os.environ["QT_QPA_PLATFORM"] = "offscreen"
cv2.setNumThreads(1)

class Ti5Camera(Node):
    def __init__(self, config, queue_size=30, fps=30):
        super().__init__("ti5_camera_node")
        self.bridge = CvBridge()
        self.fps = fps
        self.period = 1.0 / fps

        # 相机话题
        # self.topic_head = "/camera/d435i/color/image_raw"
        # self.topic_left = "/camera/d405_1/color/image_raw"
        # self.topic_right = "/camera/d405_2/color/image_raw"
        self.topic_head = config.camera.head_camera_topic
        self.topic_left = config.camera.left_hand_camera_topic 
        self.topic_right = config.camera.right_hand_camera_topic

        # 缓存队列
        self.queue_head = deque(maxlen=queue_size)
        self.queue_left = deque(maxlen=queue_size)
        self.queue_right = deque(maxlen=queue_size)
        self.queue_lock = threading.Lock()

        # 订阅
        self.create_subscription(Image, self.topic_head, self._cb_head, 10)
        self.create_subscription(Image, self.topic_left, self._cb_left, 10)
        self.create_subscription(Image, self.topic_right, self._cb_right, 10)

        self.get_logger().info("✅ Ti5Camera 已启动（无内部 spin）")

    # 相机回调
    def _cb_head(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        img = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        with self.queue_lock:
            self.queue_head.append((img, ts))

    def _cb_left(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        img = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        with self.queue_lock:
            self.queue_left.append((img, ts))

    def _cb_right(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        img = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        with self.queue_lock:
            self.queue_right.append((img, ts))

    # 外部获取图像
    def get_latest_image(self):
        with self.queue_lock:
            if not self.queue_head:
                return None
            head_img, head_ts = self.queue_head[-1]
            left_queue = list(self.queue_left)
            right_queue = list(self.queue_right)
        left_img, left_ts = self._find_closest(left_queue, head_ts)
        right_img, right_ts = self._find_closest(right_queue, head_ts)
        return [head_img, head_ts, left_img, left_ts, right_img, right_ts]

    def _find_closest(self, queue, target_ts):
        if not queue:
            return (None, None)
        return min(queue, key=lambda x: abs(x[1] - target_ts))


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

def main():
    config = get_ti5_t170c_config()
    rclpy.init()
    camera = Ti5Camera(config)

    running = True
    def spin_worker():
        while running:
            # 关键：轮流 spin 两个节点
            rclpy.spin_once(camera, timeout_sec=0.005)

    spin_thread = threading.Thread(target=spin_worker, daemon=True)
    spin_thread.start()

    # 等待相机数据进来
    print("等待相机数据...")
    time.sleep(2.0)

    # 调用一次
    images = camera.get_latest_image()

    if images:
        head_img, head_ts, left_img, left_ts, right_img, right_ts = images
        print("✅ 调用成功！")
        print("头部图像:", head_img.shape, head_ts)
        print("左手图像:", left_img.shape, left_ts)
        print("右手图像:", right_img.shape, right_ts)
    else:
        print("❌ 未读到相机数据")

if __name__ == '__main__':
    main()
