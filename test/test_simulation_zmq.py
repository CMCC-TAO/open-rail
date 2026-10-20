import json
import pickle
import queue
import threading
from types import SimpleNamespace

import numpy as np
import pytest
import zmq

from client.core.zmq_client import ZMQClient
from client.robots.robocasa_pandas.body_robot import RobotBody as CasaRobot
from client.robots.robotwin_aloha.body_robot import RobotBody as TwinRobot
from client.simulation.evaluation import (
    build_client, get_simulation_config, start_episode, wait_for_episode, wait_for_server,
)
from test_robocasa_master_merge import FakeEnvironment
from test_robotwin_evaluation import FakeTask


@pytest.mark.parametrize('benchmark', ['robocasa', 'robotwin'])
@pytest.mark.parametrize('mode', ['sync', 'async'])
def test_evaluation_with_real_zmq_releases_socket_on_inference_thread(monkeypatch, benchmark, mode):
    stop = threading.Event()
    ready = queue.Queue()
    errors = []
    action_dim = 12 if benchmark == 'robocasa' else 14

    def serve():
        context = zmq.Context()
        socket = context.socket(zmq.ROUTER)
        try:
            ready.put(socket.bind_to_random_port('tcp://127.0.0.1'))
            while not stop.is_set():
                if not socket.poll(50):
                    continue
                identity, payload, metadata = socket.recv_multipart()
                frame = pickle.loads(payload)
                if frame.get('type') == 'heartbeat':
                    response = frame
                    metadata = json.dumps({'action': 'pong'}).encode()
                else:
                    response = {
                        'type': 'vla_action',
                        'pred_action': np.full((8, action_dim), 0.1),
                        'ref_timestamp': frame['ref_timestamp'],
                        'loc_timestamp': frame['loc_timestamp'],
                    }
                socket.send_multipart([identity, pickle.dumps(response), metadata])
        except Exception as error:
            errors.append(error)
        finally:
            socket.close(linger=0)
            context.term()

    server = threading.Thread(target=serve, daemon=True)
    server.start()
    config = get_simulation_config()
    config.vla_zmq.ip = '127.0.0.1'
    config.vla_zmq.port = str(ready.get(timeout=3))
    config.vla_zmq.infer_timeout = 500
    config.rdm.mode = mode
    config.rdm.skip_initial_frames = 0
    config.rdm.action_consume_mode = 'sequential'
    config.rdm.latency_compensation = False
    config.rdm.max_async_observation_lag_steps = 7
    config.intra_chunk.intra_chunk_mode = 'raw'
    config.inter_chunk.inter_chunk_mode = 'sync'
    config.controller.period = 1.0
    config.controller.gripper_offset = 0
    config.vision.preprocess.method = 'none'
    monkeypatch.setattr('client.simulation.vla_client.DataRecordManager',
                        lambda **kwargs: SimpleNamespace(close=lambda: None))
    monkeypatch.setattr('client.core.visualize_server.VisualizeServer.kill_port',
                        lambda *args: None)
    if benchmark == 'robocasa':
        config.robots.robocasa_pandas.max_episode_steps = 16
        environment = FakeEnvironment(config.robots.robocasa_pandas)
        monkeypatch.setattr(CasaRobot, '_create_env', lambda self: environment)
        robot = CasaRobot(config.robots.robocasa_pandas)
    else:
        task = FakeTask()
        task.step_lim = 16
        robot = TwinRobot(config.robots.robotwin_aloha, task, 'Move the object')
    transport = ZMQClient(config.vla_zmq)
    client = None
    try:
        wait_for_server(transport, 3)
        client = build_client(config, robot, transport)
        start_episode(client, robot, False)
        assert wait_for_episode(client, 0, 10, 5, 30)
        assert client.pipeline_error is None
        assert robot.get_episode_result()['steps'] == 16
        assert transport._data_owner == client.inference_thread.ident
        client.close()
        assert not client.inference_thread.is_alive()
        assert transport._data_released.is_set()
        assert transport.context.closed
    finally:
        if client is not None:
            client.close()
        transport.close()
        robot.close()
        stop.set()
        server.join(timeout=3)
    assert not server.is_alive()
    assert not errors
