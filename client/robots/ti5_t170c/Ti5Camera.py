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

class Ti5Camera(Node):
    def __init__(self, queue_size=30, fps=100):
        super().__init__("ti5_camera_node")
        self.bridge = CvBridge()
        self.fps = fps
        self.period = 1.0 / fps

        # 相机话题
        self.topic_head = "/camera/d435i/color/image_raw"
        self.topic_left = "/camera/d405_1/color/image_raw"
        self.topic_right = "/camera/d405_2/color/image_raw"

        # self.topic_head = "/camera/d435i/color/image_raw"
        # self.topic_left = "/camera/d405_1/color/image_rect_raw"
        # self.topic_right = "/camera/d405_2/color/image_rect_raw"

        # 缓存队列
        self.queue_head = deque(maxlen=queue_size)
        self.queue_left = deque(maxlen=queue_size)
        self.queue_right = deque(maxlen=queue_size)

        # 订阅
        self.create_subscription(Image, self.topic_head, self._cb_head, 1)
        self.create_subscription(Image, self.topic_left, self._cb_left, 1)
        self.create_subscription(Image, self.topic_right, self._cb_right, 1)

        self.get_logger().info("✅ Ti5Camera 已启动（无内部 spin）")

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

    # 外部获取图像
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
    camera = Ti5Camera()

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




# import rclpy
# from rclpy.node import Node
# from sensor_msgs.msg import Image
# from cv_bridge import CvBridge, CvBridgeError
# from collections import deque
# import threading
# import numpy as np

# class Ti5Camera(Node):
#     def __init__(self, queue_size=10, fps=30, sync_threshold_ms=30):
#         super().__init__("ti5_camera_node")
#         self.bridge = CvBridge()
#         self.fps = fps
#         self.period = 1.0 / fps
#         # 同步阈值：30ms，超过则认为不同步
#         self.sync_threshold = sync_threshold_ms * 1e6  # 纳秒

#         # 相机话题
#         self.topic_head = "/camera/d435i/color/image_raw"
#         self.topic_left = "/camera/d405_1/color/image_rect_raw"
#         self.topic_right = "/camera/d405_2/color/image_rect_raw"

#         # 线程锁：解决多线程竞争（核心修复）
#         self.lock = threading.Lock()

#         # 缓存队列（减小长度，降低延迟）
#         self.queue_head = deque(maxlen=queue_size)
#         self.queue_left = deque(maxlen=queue_size)
#         self.queue_right = deque(maxlen=queue_size)

#         # 订阅：队列设为1，低延迟（核心修复）
#         self.create_subscription(Image, self.topic_head, 
#             lambda msg: self._generic_cb(msg, self.queue_head), 1)
#         self.create_subscription(Image, self.topic_left, 
#             lambda msg: self._generic_cb(msg, self.queue_left), 1)
#         self.create_subscription(Image, self.topic_right, 
#             lambda msg: self._generic_cb(msg, self.queue_right), 1)

#         self.get_logger().info("✅ Ti5Camera 已启动")

#     # 通用回调：消除代码冗余 + 异常捕获
#     def _generic_cb(self, msg, queue):
#         try:
#             # 纳秒时间戳：无精度丢失
#             ts = msg.header.stamp.sec * 10**9 + msg.header.stamp.nanosec
#             img = self.bridge.imgmsg_to_cv2(msg, "bgr8")
#             # 加锁写入队列
#             with self.lock:
#                 queue.append((img, ts))
#         except CvBridgeError as e:
#             self.get_logger().error(f"图像转换失败: {str(e)}")

#     # 带阈值的同步匹配：核心修复
#     def _find_closest(self, queue, target_ts):
#         with self.lock:
#             if not queue:
#                 return (None, None)
#             # 找时间最近的帧
#             best = min(queue, key=lambda x: abs(x[1] - target_ts))
#             best_img, best_ts = best
#             # 超过阈值，返回None（不同步）
#             if abs(best_ts - target_ts) > self.sync_threshold:
#                 return (None, None)
#             return (best_img, best_ts)

#     # 外部获取图像：加锁 + 判空
#     def get_latest_image(self):
#         with self.lock:
#             if not self.queue_head:
#                 return None
#             # 取最新主相机帧
#             head_img, head_ts = self.queue_head[-1]
        
#         # 同步左右相机
#         left_img, left_ts = self._find_closest(self.queue_left, head_ts)
#         right_img, right_ts = self._find_closest(self.queue_right, head_ts)
        
#         return [head_img, head_ts, left_img, left_ts, right_img, right_ts]
