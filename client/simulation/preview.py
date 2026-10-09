import base64
import json
import logging
import threading
import time
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


class CameraPreview:
    def __init__(self, path, names, fps=5):
        self.path = Path(path)
        self.names = names
        self.period = 1 / fps
        self.last_publish = 0.0
        self.future = None
        self.closed = False
        self.lock = threading.Lock()
        self.stream_id = uuid.uuid4().hex
        self.trajectory_samples = deque(maxlen=120)
        self.trajectory_labels = []
        self.sequence = 0
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='camera_preview')

    def publish(self, images, shapes, trajectory=None):
        with self.lock:
            if self.closed:
                return
            if trajectory:
                self.sequence += 1
                self.trajectory_labels = list(trajectory['labels'])
                self.trajectory_samples.append({
                    'sequence': self.sequence, 'timestamp': time.time(),
                    'state': list(trajectory['state']),
                })
            now = time.monotonic()
            if self.closed or now - self.last_publish < self.period or (self.future and not self.future.done()):
                return
            self.last_publish = now
            trajectory_snapshot = {
                'stream_id': self.stream_id, 'labels': list(self.trajectory_labels),
                'samples': list(self.trajectory_samples),
            }
            self.future = self.executor.submit(self._write, dict(images), dict(shapes), trajectory_snapshot)

    def _write(self, images, shapes, trajectory=None):
        try:
            frames = []
            for camera_id, role in enumerate(('head', 'hand_left', 'hand_right')):
                key = f'cam.{role}'
                if key not in images:
                    continue
                frames.append({
                    'camera_id': camera_id,
                    'name': self.names.get(role, role),
                    'jpeg': base64.b64encode(images[key]).decode('ascii'),
                    'height': int(shapes[key][0]),
                    'width': int(shapes[key][1]),
                })
            payload = {'timestamp': time.time(), 'frames': frames}
            if trajectory:
                payload['trajectory'] = trajectory
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix('.tmp')
            temporary.write_text(json.dumps(payload), encoding='utf-8')
            temporary.replace(self.path)
        except Exception:
            logging.getLogger(__name__).exception('Failed to publish simulation camera preview')

    def close(self):
        with self.lock:
            self.closed = True
        self.executor.shutdown(wait=True)
