import time
import cv2
from collections import deque
import threading
from a2d_sdk.robot import RobotDds as Robot
from a2d_sdk.robot import CosineCamera as Camera

class MessageBuffer:
    def __init__(self, maxlen=10):
        self.buffer = deque(maxlen=maxlen)
    
    def add(self, msg):
        self.buffer.append((msg.header.stamp, msg))
    
    def get_closest(self, target_stamp):
        # 找到时间最接近的消息
        closest = min(self.buffer, key=lambda x: abs(x[0] - target_stamp))
        return closest[1]

# 线程安全双端队列（支持阻塞和非阻塞操作）
class ThreadSafeDeque:
    def __init__(self):
        self._deque = deque()
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)  # 独立条件变量

    def append(self, item):
        """非阻塞插入右端"""
        with self._lock:
            self._deque.append(item)
            self._cond.notify()

    def appendleft(self, item):
        """非阻塞插入左端"""
        with self._lock:
            self._deque.appendleft(item)
            self._cond.notify()

    def popleft_blocking(self):
        """阻塞取出左端元素"""
        with self._lock:
            while not self._deque:
                self._cond.wait()
            return self._deque.popleft()

    def peek(self):
        """非阻塞查看左端元素"""
        with self._lock:
            return self._deque[0] if self._deque else None

    def peek(self):
        """非阻塞查看左端元素"""
        with self._lock:
            return self._deque[0] if self._deque else None

    def get_last(self):
        """非阻塞查看右端元素"""
        with self._lock:
            return self._deque[-1] if self._deque else None

    def is_empty(self):
        with self._lock:
            return len(self._deque) == 0

# 数据采集线程（每个线程独立队列）
class DataFetcher(threading.Thread):
    def __init__(self, thread_id, deque, camera):
        super().__init__(daemon=True)
        self.thread_id = thread_id
        self.deque = deque
        self.camera = camera
        self._running = True

    def run(self):
        while self._running:
            image, time_stamp = None, None
            if self.thread_id == 0:
                image, time_stamp = self.camera.get_latest_image('head')
            elif self.thread_id == 1:
                image, time_stamp = self.camera.get_latest_image('hand_left')
            elif self.thread_id == 2:
                image, time_stamp = self.camera.get_latest_image('hand_right')
            data = {
                'thread_id': self.thread_id,
                'timestamp': time_stamp / 1e9,
                'image': image
            }
            self.deque.append(data)

    def stop(self):
        self._running = False

class RobotA2D():
    def __init__(self):
        self.robot = Robot(name='4568')
        self.name_cameras = ['head', 'hand_left', 'hand_right']
        self.camera= Camera(self.name_cameras)
        imu_buffer = MessageBuffer(maxlen=20)
        gps_buffer = MessageBuffer(maxlen=20)
        time.sleep(1)

        # 创建三个独立双端队列
        self.deques = [ThreadSafeDeque() for _ in range(3)]
        # 启动三个数据线程
        threads = [DataFetcher(i, self.deques[i], self.camera) for i in range(3)]
        for t in threads:
            t.start()

    def get_cameras(self, timestamp=None):
        list_time = []
        for name in self.name_cameras:
            print(f"Getting camera: {name}")
            timeaaa = time.time()
            image, time_stamp = self.camera.get_latest_image(name)
            print(f"get image time: {time.time() - timeaaa}")
            list_time.append(time_stamp / 1e9)
            fps = self.camera.get_fps(name)
            latency = self.camera.get_latency_stats(name, window_seconds=5.0)
            # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            # cv2.imshow(name, image)
        body_states = self.robot.body_pose_joint_states()
        arm_states, time_stamp1 = self.robot.arm_joint_states()
        list_time.append(time_stamp1 / 1e9)
        gripper_states, time_stamp2 = self.robot.gripper_states()
        list_time.append(time_stamp2 / 1e9)
        max1 = max(list_time)
        min1 = min(list_time)
        print(max1 - min1, list_time)

    def get_deques(self):
        list_time = []
        deque1 = self.deques[0].get_last()
        deque2 = self.deques[1].get_last()
        deque3 = self.deques[2].get_last()
        if deque1 is None:
            return
        arm_states, time_stamp1 = self.robot.arm_joint_states()
        list_time.append(time_stamp1 / 1e9)
        gripper_states, time_stamp2 = self.robot.gripper_states()
        list_time.append(time_stamp2 / 1e9)
        list_time = list_time + [deque1['timestamp'], deque2['timestamp'], deque3['timestamp']]
        print(max(list_time) - min(list_time), list_time)

    def close(self):
        self.camera.close()

if __name__ == '__main__':
    robot = RobotA2D()
    try:
        while True:
            # robot.get_cameras()
            robot.get_deques()
            time.sleep(0.1)  # 控制循环频率
    except KeyboardInterrupt:
        robot.close()
