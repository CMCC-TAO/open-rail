import time
import threading
import cv2
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from ml_collections import ConfigDict
from .zmq_server import ZMQServer


class VISServer:
    """VLA Server: only handle data receiving and processing, no GUI"""

    def __init__(self, config: ConfigDict, zmq_server: ZMQServer):
        self.config = config
        self.zmq_server = zmq_server
        self.running = False

        # Buffers
        self.recv_buffer = deque(maxlen=1)
        self.decoded_img_buffer = deque(maxlen=1)
        self.actions_fitted = deque(maxlen=1)
        self.actions_raw = deque(maxlen=1)

        # Locks
        self.buffer_io_lock = threading.Lock()

        # Thread pool for decoding
        self.image_decode_executor = ThreadPoolExecutor(max_workers=3)

        # Threads
        self.receive_thread = threading.Thread(target=self.recvThreadFun, daemon=True)
        self.process_thread = threading.Thread(target=self.processThreadFun, daemon=True)

    def run(self):
        """Start receive and process threads"""
        self.running = True
        self.receive_thread.start()
        self.process_thread.start()

    def recvThreadFun(self):
        time.sleep(1)
        print("Start receiving data...")
        while self.running:
            message = self.zmq_server.recvMessage()
            if message is not None:
                self.recv_buffer.append(message['data'])
            time.sleep(0.001)

    def processThreadFun(self):
        while self.running:
            if self.recv_buffer:
                data = self.recv_buffer.pop()
                try:
                    cam_keys = [k for k in data['obs'] if "cam." in k]
                    images_data = [(key, data['obs'][key]) for key in cam_keys]

                    decoded_images = []
                    for key, img_bytes in images_data:
                        if isinstance(img_bytes, (bytes, bytearray, memoryview)):
                            img_bytes = np.frombuffer(img_bytes, dtype=np.uint8)
                        elif not isinstance(img_bytes, np.ndarray):
                            img_bytes = np.asarray(img_bytes, dtype=np.uint8)
                        img = cv2.imdecode(
                            img_bytes,
                            cv2.IMREAD_ANYDEPTH if "depth." in key else cv2.IMREAD_COLOR
                        )
                        decoded_images.append(img)

                    with self.buffer_io_lock:
                        self.decoded_img_buffer.append({k: img for (k, _), img in zip(images_data, decoded_images)})
                        self.actions_fitted.append(data['actions_fitted'])
                        self.actions_raw.append(data['actions_raw'])

                except Exception as e:
                    print(f"Error processing data: {e}")
            else:
                time.sleep(0.001)

    def get_latest_data(self):
        """Get latest images and actions for GUI"""
        with self.buffer_io_lock:
            if not self.decoded_img_buffer:
                return None, None, None
            imgs = self.decoded_img_buffer.pop()
            action_fitted = self.actions_fitted.pop()
            action_raw = self.actions_raw.pop()
            return imgs, action_fitted, action_raw

    def close(self):
        self.running = False
        self.zmq_server.close()
