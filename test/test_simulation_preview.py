import base64
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import cv2
import numpy as np
import pytest
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
    def write(images, shapes, trajectory=None):
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


def test_preview_keeps_bounded_trajectory_history_between_image_updates(tmp_path):
    preview = CameraPreview(tmp_path / 'preview.json', {})
    try:
        for i in range(130):
            preview.publish({}, {}, {'labels': ['joint0'], 'state': [i / 100]})
        preview.future.result(timeout=5)
        preview.last_publish = 0
        preview.publish({}, {}, {'labels': ['joint0'], 'state': [1.3]})
    finally:
        preview.close()
    snapshot = json.loads((tmp_path / 'preview.json').read_text())
    trajectory = snapshot['trajectory']
    assert trajectory['labels'] == ['joint0']
    assert len(trajectory['samples']) == 120
    assert trajectory['samples'][-1]['sequence'] == 131
    assert trajectory['samples'][-1]['state'] == [1.3]


def test_preview_preserves_actions_between_camera_frames(tmp_path):
    path = tmp_path / 'preview.json'
    preview = CameraPreview(path, {})
    try:
        for value in (.1, .2, .3):
            preview.publish_trajectory({
                'labels': ['left_arm_0'], 'state': np.array([value - .01]),
                'action_fitted': np.array([value]), 'action_raw': np.array([.5]),
            })
        preview.publish({}, {})
    finally:
        preview.close()
    trajectory = json.loads(path.read_text())['trajectory']
    assert trajectory['sources'] == ['action_fitted', 'action_raw', 'state']
    assert [s['action_fitted'] for s in trajectory['samples']] == [[.1], [.2], [.3]]
    assert [s['action_raw'] for s in trajectory['samples']] == [[.5]] * 3
    np.testing.assert_allclose([s['state'] for s in trajectory['samples']], [[.09], [.19], [.29]])


def test_preview_switches_joint_layout_without_reusing_old_sources(tmp_path):
    preview = CameraPreview(tmp_path / 'preview.json', {})
    try:
        original_stream = preview.stream_id
        preview.publish_trajectory({
            'labels': ['a', 'b'], 'state': [1, 2], 'action_raw': [3, 4],
            'action_semantics': 'estimated_joint_angles',
        })
        preview.publish_trajectory({'labels': [], 'state': []})
        assert preview.trajectory_labels == ['a', 'b']
        preview.publish_trajectory({'labels': ['c'], 'state': [5]})
        assert preview.stream_id != original_stream
        assert list(preview.trajectory_samples)[0]['state'] == [5]
        assert len(preview.trajectory_samples) == 1
        assert preview.trajectory_sources == {'state'}
        assert preview.trajectory_action_semantics is None
    finally:
        preview.close()


def test_robocasa_trajectory_reads_joint_positions_not_end_effector_state():
    from client.robots.robocasa_pandas.body_robot import RobotBody

    native_robot = SimpleNamespace(
        _ref_arm_joint_pos_indexes=[1, 2], robot_arm_joints=['robot0_right_j0', 'robot0_right_j1'],
        robot_model=SimpleNamespace(naming_prefix='robot0_'),
        sim=SimpleNamespace(data=SimpleNamespace(qpos=np.array([99, .1, .2, 88]))),
    )
    obs = {'state.end_effector_position': np.array([3, 4, 5])}
    robot = RobotBody.__new__(RobotBody)
    robot.env = SimpleNamespace(
        unwrapped=SimpleNamespace(env=SimpleNamespace(robots=[native_robot])),
        step=lambda action: (obs, 0, False, False, {}),
    )
    result = robot._step_env({}, {})
    assert result[0]['_joint_trajectory'] == {'labels': ['right_j0', 'right_j1'], 'state': [.1, .2]}


@pytest.fixture
def robocasa_joint_robot():
    from client.robots.robocasa_pandas.body_robot import RobotBody
    from conf.robots_conf import get_robocasa_pandas_config

    robot = RobotBody.__new__(RobotBody)
    robot.action_layout = get_robocasa_pandas_config().action_layout
    robot.action_dim = 12
    robot._last_action = np.zeros(12)
    jacobian = np.eye(6, 7)
    data = SimpleNamespace(
        qpos=np.full(7, .1), site_xpos=np.zeros((1, 3)), site_xmat=np.eye(3)[None],
        get_site_jacp=lambda name: jacobian[:3], get_site_jacr=lambda name: jacobian[3:],
    )
    controller = SimpleNamespace(
        name='OSC_POSE', input_type='delta', impedance_mode='fixed',
        input_ref_frame='base', qpos_index=list(range(7)), qvel_index=list(range(7)),
        joint_index=list(range(7)), ref_name='eef', origin_pos=np.zeros(3),
        origin_ori=np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]]),
        goal_pos=np.zeros(3), goal_ori=np.array([[0., 1., 0.], [-1., 0., 0.], [0., 0., 1.]]),
        input_min=-np.ones(6), input_max=np.ones(6),
        output_min=-np.array([.05] * 3 + [.5] * 3), output_max=np.array([.05] * 3 + [.5] * 3),
    )
    native = SimpleNamespace(
        _ref_arm_joint_pos_indexes=list(range(7)), robot_arm_joints=[f'robot0_joint{i}' for i in range(7)],
        robot_model=SimpleNamespace(naming_prefix='robot0_'),
        composite_controller=SimpleNamespace(part_controllers={'right': controller}),
        sim=SimpleNamespace(data=data, model=SimpleNamespace(
            site_name2id=lambda name: 0, jnt_range=np.array([[-2., 2.]] * 7))),
    )

    def step(action):
        data.qpos += .5
        return {}, 0, False, False, {}

    robot.env = SimpleNamespace(unwrapped=SimpleNamespace(env=SimpleNamespace(robots=[native])), step=step)
    return robot, native, controller, jacobian


def test_robocasa_publishes_joint_only_sources_from_same_pre_step_state(robocasa_joint_robot, tmp_path):
    robot, native, controller, jacobian = robocasa_joint_robot
    robot._last_obs = robot._step_env({}, {})[0]
    fitted, raw = np.zeros(12), np.zeros(12)
    fitted[0], raw[0] = 1., -.5
    fitted[5] = 1.
    trajectory = robot.get_joint_trajectory(fitted, raw)
    assert trajectory['labels'] == [f'joint{i}' for i in range(7)]
    np.testing.assert_allclose(trajectory['state'], [.6] * 7)
    expected_fitted, expected_raw = np.full(7, .1), np.full(7, .1)
    expected_fitted[1] += .05 / 1.0025
    expected_fitted[5] += .5 / 1.0025
    expected_raw[1] -= .025 / 1.0025
    np.testing.assert_allclose(trajectory['action_fitted'], expected_fitted)
    np.testing.assert_allclose(trajectory['action_raw'], expected_raw)
    np.testing.assert_allclose(native.sim.data.qpos, [.6] * 7)
    np.testing.assert_allclose(controller.goal_pos, np.zeros(3))
    np.testing.assert_allclose(jacobian, np.eye(6, 7))
    preview = CameraPreview(tmp_path / 'preview.json', {})
    try:
        preview.publish_trajectory(trajectory)
        preview.publish({}, {}, robot.get_joint_trajectory())
    finally:
        preview.close()
    published = json.loads((tmp_path / 'preview.json').read_text())['trajectory']
    assert published['action_semantics'] == 'estimated_joint_angles'
    assert published['sources'] == ['action_fitted', 'action_raw', 'state']
    assert len(published['labels']) == 7


def test_robocasa_joint_estimates_respect_base_mode_and_singularities(robocasa_joint_robot):
    robot, native, controller, jacobian = robocasa_joint_robot
    controller.goal_pos = np.array([.2, 0., 0.])
    controller.goal_ori = np.eye(3)
    robot._last_obs = robot._step_env({}, {})[0]
    action = np.zeros(12)
    action[-1] = 1.
    estimate = robot.get_joint_trajectory(action, action)['action_fitted']
    assert estimate[1] == pytest.approx(.1 + .2 / 1.0025)
    assert estimate[5] == pytest.approx(.1 + np.pi / 2 / 1.0025)
    jacobian[:] = 0
    robot._last_obs = robot._step_env({}, {})[0]
    np.testing.assert_allclose(robot.get_joint_trajectory(action)['action_fitted'], [.6] * 7)


def test_robocasa_joint_estimates_respect_controller_and_joint_limits(robocasa_joint_robot):
    robot, native, controller, _ = robocasa_joint_robot
    native.sim.model.jnt_range[:, 1] = .12
    robot._last_obs = robot._step_env({}, {})[0]
    action = np.zeros(12)
    action[0] = 100
    estimate = robot.get_joint_trajectory(action)['action_fitted']
    assert estimate[1] == .12
    np.testing.assert_allclose(estimate[:1] + estimate[2:], [.1] * 6)


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
