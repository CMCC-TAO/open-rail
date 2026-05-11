import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os
import threading
import time
from collections import deque

os.environ["QT_QPA_PLATFORM"] = "offscreen"
cv2.setNumThreads(1)

class UnitreeG1Camera(Node):
    def __init__(self, queue_size=30, fps=100):
        super().__init__("unitree_g1_camera_node")
        self.bridge = CvBridge()
        self.fps = fps
        self.period = 1.0 / fps

        # 相机话题（标准 Realsense 话题名）
        self.topic_head = "/camera/d435i/color/image_raw"
        self.topic_left = "/camera/d405_1/color/image_raw"
        self.topic_right = "/camera/d405_2/color/image_raw"

        # 缓存队列
        self.queue_head = deque(maxlen=queue_size)
        self.queue_left = deque(maxlen=queue_size)
        self.queue_right = deque(maxlen=queue_size)

        # 订阅
        self.create_subscription(Image, self.topic_head, self._cb_head, 1)
        self.create_subscription(Image, self.topic_left, self._cb_left, 1)
        self.create_subscription(Image, self.topic_right, self._cb_right, 1)

        self.get_logger().info("UnitreeG1Camera ready (no internal spin)")

    # 相机回调
    def _cb_head(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        img = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        self.queue_head.append((img, ts))

    def _cb_left(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        img = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        self.queue_left.append((img, ts))

    def _cb_right(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        img = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        self.queue_right.append((img, ts))

    # 外部获取图像，以头部相机时间戳对齐左右腕
    def get_latest_image(self):
        if not self.queue_head:
            return None
        head_img, head_ts = self.queue_head[-1]
        left_img, left_ts = self._find_closest(self.queue_left, head_ts)
        right_img, right_ts = self._find_closest(self.queue_right, head_ts)
        return [head_img, head_ts, left_img, left_ts, right_img, right_ts]

    def _find_closest(self, queue, target_ts):
        if not queue:
            return (None, None)
        return min(queue, key=lambda x: abs(x[1] - target_ts))


def main():
    rclpy.init()
    camera = UnitreeG1Camera()

    running = True
    def spin_worker():
        while running:
            rclpy.spin_once(camera, timeout_sec=0.005)

    spin_thread = threading.Thread(target=spin_worker, daemon=True)
    spin_thread.start()

    print("Waiting for camera data...")
    time.sleep(2.0)

    images = camera.get_latest_image()
    if images:
        head_img, head_ts, left_img, left_ts, right_img, right_ts = images
        print("Camera test OK")
        print("  head:", head_img.shape, head_ts)
        print("  left:", left_img.shape, left_ts)
        print("  right:", right_img.shape, right_ts)
    else:
        print("No camera data")

if __name__ == '__main__':
    main()
