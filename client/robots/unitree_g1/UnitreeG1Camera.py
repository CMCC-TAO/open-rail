import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge
import cv2
import os
import threading
import time
from collections import deque

_DEBUG_ENABLED = False          # 开关：True=打印, False=静默
_DEBUG_PRINT_INTERVAL = 1.0
_last_debug_time = 0.0


def _dprint(msg):
    if not _DEBUG_ENABLED:
        return
    global _last_debug_time
    now = time.time()
    if now - _last_debug_time >= _DEBUG_PRINT_INTERVAL:
        print(f"[DBG UnitreeG1Camera] {msg}")
        _last_debug_time = now

# 如果使用显示窗口，默认不强制 offscreen 平台，避免 Qt 插件初始化失败
if "QT_QPA_PLATFORM" in os.environ:
    os.environ.pop("QT_QPA_PLATFORM")
cv2.setNumThreads(1)

class UnitreeG1Camera(Node):
    def __init__(self, queue_size=30, fps=100, ros_context=None):
        super().__init__("unitree_g1_camera_node", context=ros_context)
        self.bridge = CvBridge()
        self.fps = fps
        self.period = 1.0 / fps

        # 相机话题（Unitree G1 ROS2 实际 topic）
        self.topic_head = "/head/color/image"
        self.topic_left = "/left/color/image"
        self.topic_right = "/right/color/image"

        print(f"[DBG UnitreeG1Camera] Subscribed topics:")
        print(f"[DBG UnitreeG1Camera]   - {self.topic_head}")
        print(f"[DBG UnitreeG1Camera]   - {self.topic_left}")
        print(f"[DBG UnitreeG1Camera]   - {self.topic_right}")

        # 缓存队列
        self.queue_head = deque(maxlen=queue_size)
        self.queue_left = deque(maxlen=queue_size)
        self.queue_right = deque(maxlen=queue_size)

        # 订阅
        self.create_subscription(CompressedImage, self.topic_head, self._cb_head, 1)
        self.create_subscription(CompressedImage, self.topic_left, self._cb_left, 1)
        self.create_subscription(CompressedImage, self.topic_right, self._cb_right, 1)

        self.get_logger().info("UnitreeG1Camera ready (no internal spin)")

    # 相机回调
    def _cb_head(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        img = self.bridge.compressed_imgmsg_to_cv2(msg, "bgr8")
        self.queue_head.append((img, ts))
        _dprint(f"_cb_head: ts={ts:.6f}, img.shape={img.shape}")

    def _cb_left(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        img = self.bridge.compressed_imgmsg_to_cv2(msg, "bgr8")
        self.queue_left.append((img, ts))
        _dprint(f"_cb_left: ts={ts:.6f}, img.shape={img.shape}")

    def _cb_right(self, msg):
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        img = self.bridge.compressed_imgmsg_to_cv2(msg, "bgr8")
        self.queue_right.append((img, ts))
        _dprint(f"_cb_right: ts={ts:.6f}, img.shape={img.shape}")

    # 外部获取图像，以头部相机时间戳对齐左右腕
    def get_latest_image(self):
        qs = f"head={len(self.queue_head)} left={len(self.queue_left)} right={len(self.queue_right)}"
        if not self.queue_head:
            _dprint(f"get_latest_image FAIL: queue_head empty ({qs})")
            return None
        head_img, head_ts = self.queue_head[-1]
        left_img, left_ts = self._find_closest(self.queue_left, head_ts)
        right_img, right_ts = self._find_closest(self.queue_right, head_ts)
        _dprint(f"get_latest_image OK: head_ts={head_ts:.6f} ({qs})")
        return [head_img, head_ts, left_img, left_ts, right_img, right_ts]

    def _find_closest(self, queue, target_ts):
        if not queue:
            return (None, None)
        # 快照：避免 deque 在迭代时被 ROS2 回调线程 append 导致
        # "deque mutated during iteration" 异常
        snapshot = list(queue)
        if not snapshot:
            return (None, None)
        return min(snapshot, key=lambda x: abs(x[1] - target_ts))


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
    start_time = time.time()
    while time.time() - start_time < 3.0 and not camera.queue_head:
        time.sleep(0.05)

    cv2.namedWindow("head", cv2.WINDOW_NORMAL)
    cv2.namedWindow("left", cv2.WINDOW_NORMAL)
    cv2.namedWindow("right", cv2.WINDOW_NORMAL)

    try:
        last_head_ts = None
        while True:
            images = camera.get_latest_image()
            if images:
                head_img, head_ts, left_img, left_ts, right_img, right_ts = images
                if head_ts != last_head_ts:
                    last_head_ts = head_ts
                    if head_img is not None:
                        cv2.imshow("head", head_img)
                    if left_img is not None:
                        cv2.imshow("left", left_img)
                    if right_img is not None:
                        cv2.imshow("right", right_img)

                # 只打印一次，不影响每帧显示
                print(f"head ts={head_ts:.6f}", end="\r")
                key = cv2.waitKey(1) & 0xFF
            else:
                key = cv2.waitKey(100) & 0xFF

            if key == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    finally:
        running = False
        cv2.destroyAllWindows()
        camera.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
