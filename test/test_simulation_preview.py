import base64
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import cv2
import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from client.simulation.preview import CameraPreview
from client.simulation.vla_client import VLAClientAsync
from web_client import simulation


def test_preview_reuses_encoded_cameras(tmp_path):
    path = tmp_path / 'preview.json'
    names = {'head': 'left_view', 'hand_left': 'right_view', 'hand_right': 'wrist_view'}
    images, shapes = {}, {}
    for i, role in enumerate(names):
        image = np.full((16, 24, 3), i * 60, dtype=np.uint8)
        images[f'cam.{role}'] = cv2.imencode('.jpg', image)[1]
        shapes[f'cam.{role}'] = image.shape
    preview = CameraPreview(path, names)
    preview.publish(images, shapes)
    preview.close()
    snapshot = json.loads(path.read_text())
    assert [f['camera_id'] for f in snapshot['frames']] == [0, 1, 2]
    assert [f['name'] for f in snapshot['frames']] == list(names.values())
    for frame, role in zip(snapshot['frames'], names):
        assert base64.b64decode(frame['jpeg']) == images[f'cam.{role}'].tobytes()
        assert (frame['height'], frame['width']) == (16, 24)
    preview.publish(images, shapes)


def test_preview_drops_frames_when_writer_is_busy(tmp_path, monkeypatch):
    preview = CameraPreview(tmp_path / 'preview.json', {}, fps=1000)
    entered, release = threading.Event(), threading.Event()
    written = []
    def write(images, shapes):
        entered.set()
        release.wait(5)
        written.append(images)
    monkeypatch.setattr(preview, '_write', write)
    try:
        preview.publish({'first': b'jpeg'}, {})
        assert entered.wait(2)
        for _ in range(100):
            preview.publish({'next': b'jpeg'}, {})
    finally:
        release.set()
        preview.close()
    assert written == [{'first': b'jpeg'}]


def test_observation_encoding_publishes_all_cameras(tmp_path):
    client = VLAClientAsync.__new__(VLAClientAsync)
    client.camera_shape_dict = None
    client.image_process_time = 0.0
    client.visualize_server = SimpleNamespace(update_image_data=lambda images: None)
    client.camera_preview = CameraPreview(tmp_path / 'preview.json', {})
    client._process_image_thread_fun = lambda key, image: (key, cv2.imencode('.jpg', image)[1])
    images = {f'cam.{role}': np.zeros((16, 24, 3), dtype=np.uint8) for role in ('head', 'hand_left', 'hand_right')}
    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            client._img_executor = pool
            encoded = client._process_image(images)
    finally:
        client.camera_preview.close()
    snapshot = json.loads((tmp_path / 'preview.json').read_text())
    assert len(snapshot['frames']) == 3
    assert base64.b64decode(snapshot['frames'][0]['jpeg']) == encoded['cam.head'].tobytes()


def test_preview_endpoint_hides_stale_and_finished_job_frames(tmp_path, monkeypatch):
    manager = simulation.EvaluationJobs(tmp_path)
    monkeypatch.setattr(simulation, 'manager', manager)
    now = time.time()
    manager.jobs['test'] = {
        'id': 'test', 'status': 'running', 'started': now - 1,
        'config': {'env_name': 'PickPlaceCounterToCabinet'},
    }
    folder = manager.directory / 'test'
    folder.mkdir(parents=True)
    app = FastAPI()
    app.include_router(simulation.router)
    with TestClient(app) as client:
        assert client.get('/api/simulation/preview').json()['frames'] == []
        path = folder / 'preview.json'
        path.write_text(json.dumps({'timestamp': now, 'frames': [{'camera_id': 0}]}))
        result = client.get('/api/simulation/preview').json()
        assert result['job']['id'] == 'test' and result['frames'] == [{'camera_id': 0}]
        path.write_text(json.dumps({'timestamp': now - 10, 'frames': [{'camera_id': 0}]}))
        assert client.get('/api/simulation/preview').json()['frames'] == []
        manager.jobs['test']['status'] = 'completed'
        assert client.get('/api/simulation/preview').json()['job'] is None
