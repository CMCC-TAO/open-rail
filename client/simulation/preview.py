import base64
import json
import logging
import threading
import time
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
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='camera_preview')

    def publish(self, images, shapes):
        with self.lock:
            now = time.monotonic()
            if self.closed or now - self.last_publish < self.period or (self.future and not self.future.done()):
                return
            self.last_publish = now
            self.future = self.executor.submit(self._write, dict(images), dict(shapes))

    def _write(self, images, shapes):
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
