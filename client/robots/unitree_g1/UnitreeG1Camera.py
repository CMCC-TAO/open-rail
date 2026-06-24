import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge
import cv2
import os
import threading
import time
from collections import deque

_DEBUG_ENABLED = False          # Toggle: True=print, False=silent
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

# If using display window, do not force offscreen platform by default to avoid Qt plugin initialization failure
if "QT_QPA_PLATFORM" in os.environ:
    os.environ.pop("QT_QPA_PLATFORM")
cv2.setNumThreads(1)

class UnitreeG1Camera(Node):
    def __init__(self, queue_size=30, fps=100, ros_context=None):
        super().__init__("unitree_g1_camera_node", context=ros_context)
        self.bridge = CvBridge()
        self.fps = fps
        self.period = 1.0 / fps

        # Camera topics (Unitree G1 ROS2 actual topics)
        self.topic_head = "/head/color/image"
        self.topic_left = "/left/color/image"
        self.topic_right = "/right/color/image"

        print(f"[DBG UnitreeG1Camera] Subscribed topics:")
        print(f"[DBG UnitreeG1Camera]   - {self.topic_head}")
        print(f"[DBG UnitreeG1Camera]   - {self.topic_left}")
        print(f"[DBG UnitreeG1Camera]   - {self.topic_right}")

        # Cache queues
        self.queue_head = deque(maxlen=queue_size)
        self.queue_left = deque(maxlen=queue_size)
        self.queue_right = deque(maxlen=queue_size)

        # Subscriptions
        self.create_subscription(CompressedImage, self.topic_head, self._cb_head, 1)
        self.create_subscription(CompressedImage, self.topic_left, self._cb_left, 1)
        self.create_subscription(CompressedImage, self.topic_right, self._cb_right, 1)

        self.get_logger().info("UnitreeG1Camera ready (no internal spin)")

    # Camera callbacks
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

    # External image retrieval, align left/right wrist based on head camera timestamp
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
        # Snapshot: avoid deque being appended by ROS2 callback thread during iteration,
        # causing "deque mutated during iteration" exception
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

                # Print only once, does not affect per-frame display
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
