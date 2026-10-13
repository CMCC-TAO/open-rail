import json
import subprocess
import sys
import time
from pathlib import Path

import psutil
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from web_client import simulation


def test_validation_and_command(tmp_path):
    with pytest.raises(ValidationError):
        simulation.EvaluationConfig()
    with pytest.raises(ValidationError):
        simulation.EvaluationConfig(env_name='Task', async_replenish_threshold=16)
    manager = simulation.EvaluationJobs(tmp_path)
    config = simulation.EvaluationConfig(env_name='Task', record=True, video=False, mode='async', intra_chunk_mode='fitting')
    command = manager.command(config, 'test')
    assert '--record' in command and '--no_video' in command
    assert command[command.index('--record_dir') + 1] == 'data/simulation_web/jobs/test/lerobot'
    assert command[command.index('--run_id') + 1] == 'test'
    from scripts.robocasa_eval import build_parser
    args = build_parser().parse_args(command[3:])
    assert args.mode == 'async' and args.intra_chunk_mode == 'fitting'


@pytest.mark.parametrize('gpu,expected', [('2', '2'), ('', '7')])
def test_robocasa_gpu_environment_isolated(tmp_path, monkeypatch, gpu, expected):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '7')
    monkeypatch.setenv('MUJOCO_EGL_DEVICE_ID', '7')
    monkeypatch.setattr(simulation.subprocess, 'run', lambda *a, **kw: subprocess.CompletedProcess(a, 0, '', ''))
    manager = simulation.EvaluationJobs(tmp_path)
    output = tmp_path / 'devices.json'
    code = (
        'import json,os,pathlib; '
        f'pathlib.Path({str(output)!r}).write_text(json.dumps('
        '[os.getenv("CUDA_VISIBLE_DEVICES"),os.getenv("MUJOCO_EGL_DEVICE_ID")]))'
    )
    monkeypatch.setattr(manager, 'command', lambda c, i: [sys.executable, '-c', code])
    job = manager.start(simulation.EvaluationConfig(env_name='Task', gpu=gpu))
    deadline = time.monotonic() + 5
    try:
        while manager.get(job['id'])['status'] == 'running' and time.monotonic() < deadline:
            time.sleep(.02)
        assert json.loads(output.read_text()) == [expected, expected]
        assert simulation.os.environ['CUDA_VISIBLE_DEVICES'] == '7'
        assert simulation.os.environ['MUJOCO_EGL_DEVICE_ID'] == '7'
    finally:
        manager.close()


@pytest.mark.parametrize('gpu', ['0,1', '-1', 'abc'])
def test_robocasa_rejects_invalid_render_gpu(gpu):
    with pytest.raises(ValidationError):
        simulation.EvaluationConfig(env_name='Task', gpu=gpu)


def test_lifecycle_api_and_artifacts(tmp_path, monkeypatch):
    manager = simulation.EvaluationJobs(tmp_path)
    monkeypatch.setattr(simulation, 'manager', manager)
    app = FastAPI()
    app.include_router(simulation.router)
    client = TestClient(app)
    monkeypatch.setattr(simulation.subprocess, 'run', lambda *a, **kw: subprocess.CompletedProcess(a, 0, '', ''))
    script = tmp_path / 'fake.py'
    script.write_text("import pathlib,subprocess,sys,time\np=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)\npathlib.Path(sys.argv[1]).write_text(str(p.pid))\nprint('running',flush=True)\ntime.sleep(60)\n")
    monkeypatch.setattr(manager, 'command', lambda c, i: [sys.executable, '-u', str(script), str(tmp_path / 'child')])
    response = client.post('/api/simulation/jobs', json={'python': sys.executable, 'env_name': 'Task'})
    assert response.status_code == 200
    job_id = response.json()['id']
    try:
        assert client.post('/api/simulation/jobs', json={'env_name': 'Other'}).status_code == 400
        deadline = time.time() + 5
        while not (tmp_path / 'child').exists() and time.time() < deadline:
            time.sleep(.05)
        child = psutil.Process(int((tmp_path / 'child').read_text()))
        assert client.get(f'/api/simulation/jobs/{job_id}/logs').json()['text'].strip() == 'running'
        outside = tmp_path / 'secret.json'
        outside.write_text('secret')
        (manager.directory / job_id / 'escape.json').symlink_to(outside)
        assert client.get(f'/api/simulation/jobs/{job_id}/artifact/escape.json').status_code == 404
        assert 'escape.json' not in client.get(f'/api/simulation/jobs/{job_id}/files').json()
        assert client.post(f'/api/simulation/jobs/{job_id}/stop').json()['status'] == 'cancelled'
        assert not child.is_running() or child.status() == psutil.STATUS_ZOMBIE
        assert client.post(f'/api/simulation/jobs/{job_id}/resume').json()['id'] == job_id
    finally:
        manager.close()
    reloaded = simulation.EvaluationJobs(tmp_path)
    assert reloaded.get(job_id)['status'] == 'cancelled'


def test_suite_failure(tmp_path):
    manager = simulation.EvaluationJobs(tmp_path)
    folder = manager.directory / 'test' / 'output'
    folder.mkdir(parents=True)
    (folder / 'stats.json').write_text(json.dumps({'run_id': 'test', 'num_failed_tasks': 1}))
    manager.jobs['test'] = {'id': 'test', 'status': 'running'}
    process = subprocess.Popen([sys.executable, '-c', 'pass'])
    manager.processes['test'] = process
    manager._watch('test', process)
    assert manager.get('test')['status'] == 'failed'


def test_parallel_progress_deduplicates_episodes(tmp_path):
    manager = simulation.EvaluationJobs(tmp_path)
    manager.jobs['test'] = {'id': 'test', 'status': 'running'}
    output = manager.directory / 'test' / 'output'
    for name, episodes in [('task', [{'episode': 0, 'success': True}, {'episode': 1, 'success': False}]), ('worker', [{'episode': 0, 'success': True}])]:
        folder = output / name
        folder.mkdir(parents=True)
        (folder / 'stats.json').write_text(json.dumps({'run_id': 'test', 'env_name': 'Task', 'episodes': episodes}))
    progress = manager.get('test')['progress']
    assert progress == [{'env_name': 'Task', 'num_episodes': 2, 'success_rate': .5}]


def test_missing_environment_is_reported(tmp_path, monkeypatch):
    manager = simulation.EvaluationJobs(tmp_path)
    monkeypatch.setattr(simulation.subprocess, 'run', lambda *a, **kw: subprocess.CompletedProcess(a, 1, 'robocasa', ''))
    with pytest.raises(ValueError, match='robocasa'):
        manager.start(simulation.EvaluationConfig(python=sys.executable, env_name='Task'))
    assert not manager.processes


def test_robotwin_command_and_validation(tmp_path):
    from scripts.aloha_robotwin_eval import build_parser, validate_args
    manager = simulation.EvaluationJobs(tmp_path)
    config = simulation.EvaluationConfig(platform='robotwin', env_name='stack_bowls_three',
        robotwin_root='/tmp/RoboTwin', no_expert_check=True, instruction='Stack bowls', gpu='0',
        record=True, mode='async', intra_chunk_mode='fitting')
    command = manager.command(config, 'test')
    assert command[2].endswith('aloha_robotwin_eval.py')
    assert '--no_expert_check' in command
    assert '--mujoco_gl' not in command and '--split' not in command
    args = build_parser().parse_args(command[3:])
    validate_args(args)
    assert args.instruction == 'Stack bowls' and args.mode == 'async'
    assert args.record_dir == 'data/simulation_web/jobs/test/lerobot'
    with pytest.raises(ValidationError):
        simulation.EvaluationConfig(platform='robotwin', env_name='Task', no_expert_check=True)
    with pytest.raises(ValidationError):
        simulation.EvaluationConfig(platform='robotwin', env_name='Task', intra_chunk_mode='local')


@pytest.mark.parametrize('render_mode', ['chunk_boundary', 'per_action'])
def test_robotwin_render_mode_from_web_snapshot_reaches_cli(tmp_path, render_mode):
    from scripts import aloha_robotwin_eval as twin

    snapshot = {
        'robots': {'type': 'aloha_robotwin', 'aloha_robotwin': {'render_observation_mode': render_mode}},
        'rdm': {'mode': 'sync'},
    }
    config = simulation.EvaluationConfig(env_name='Task', client_config=snapshot)
    assert config.render_observation_mode == render_mode
    command = simulation.EvaluationJobs(tmp_path).command(config, 'test')
    args = twin.build_parser().parse_args(command[3:])
    assert args.render_observation_mode == render_mode
    snapshot_path = Path(args.user_conf)
    snapshot_path.parent.mkdir(parents=True)
    snapshot_path.write_text(f'def get_user_config():\n    return {snapshot!r}\n')
    initial_identity = twin._identity(args, 'Task')
    args.render_observation_mode = 'per_action' if render_mode == 'chunk_boundary' else 'chunk_boundary'
    assert twin._identity(args, 'Task') != initial_identity
    casa = simulation.EvaluationJobs(tmp_path).command(
        simulation.EvaluationConfig(env_name='Task'), 'casa'
    )
    assert '--render_observation_mode' not in casa


@pytest.mark.parametrize('suite', [False, True])
def test_robotwin_preflight_does_not_require_robocasa(tmp_path, monkeypatch, suite):
    root = tmp_path / 'RoboTwin'
    (root / 'envs').mkdir(parents=True)
    (root / 'task_config').mkdir()
    (root / 'envs/Task.py').write_text('')
    tasks = [f'task_name_{index:02}' for index in range(50)]
    for task in tasks:
        (root / 'envs' / f'{task}.py').write_text('')
    (root / 'task_config/demo_clean.yml').write_text('')
    manager = simulation.EvaluationJobs(tmp_path)
    seen = []
    def check(command, **kwargs):
        seen.append(command)
        return subprocess.CompletedProcess(command, 1, 'sapien', '')
    monkeypatch.setattr(simulation.subprocess, 'run', check)
    with pytest.raises(ValueError, match='sapien'):
        manager.start(simulation.EvaluationConfig(platform='robotwin', env_name='' if suite else 'Task',
                                                task_suite=','.join(tasks) if suite else '', python=sys.executable,
                                                robotwin_root=str(root)))
    assert 'sapien' in seen[0] and 'robocasa' not in seen[0]


def test_options_use_platform_presets_and_current_model_connection(tmp_path, monkeypatch):
    path = tmp_path / 'web_simulation.yaml'
    path.write_text('defaults:\n  video_fps: 15\nplatforms:\n  robotwin:\n    python: ""\n    robotwin_root: /configured/RoboTwin\n')
    monkeypatch.setattr(simulation, 'DEFAULTS_PATH', path)
    manager = simulation.EvaluationJobs(tmp_path)
    connection = ['192.0.2.10', 5566]
    manager.connection_provider = lambda: tuple(connection)
    monkeypatch.setattr(simulation, 'manager', manager)
    app = FastAPI()
    app.include_router(simulation.router)
    client = TestClient(app)
    casa = client.get('/api/simulation/options').json()
    twin = client.get('/api/simulation/options?platform=robotwin').json()
    assert casa['n_action_steps'] == 16 and casa['seed'] == 42
    assert twin['n_action_steps'] == 50 and twin['seed'] == 0
    assert twin['robotwin_root'] == '/configured/RoboTwin'
    assert twin['python'] == sys.executable
    assert twin['video_fps'] == 15
    assert twin['server_port'] == 5566
    connection[:] = ['192.0.2.20', 1117]
    updated = client.get('/api/simulation/options').json()
    assert updated['server_ip'] == '192.0.2.20' and updated['server_port'] == 1117


def test_client_configuration_drives_evaluation_and_rejects_invalid_shared_values():
    snapshot = {
        'robots': {'type': 'robocasa', 'robocasa': {'seed': 7, 'n_envs': 2}},
        'rdm': {'mode': 'async', 'action_replenish_threshold': 3, 'max_async_observation_lag_steps': 6},
        'controller': {'action_steps': 12, 'period': 4.5},
        'intra_chunk': {'intra_chunk_mode': 'fitting', 'fitting_deg': 3},
        'inter_chunk': {'inter_chunk_mode': 'min_jerk', 'min_jerk': {'blend_threshold': .6}},
        'vla_zmq': {'ip': '192.0.2.10', 'port': '5566'},
    }
    config = simulation.EvaluationConfig(env_name='Task', client_config=snapshot)
    assert config.mode == 'async' and config.n_action_steps == 12
    assert config.control_period_ms == 4.5 and config.intra_chunk_mode == 'fitting'
    assert config.async_replenish_threshold == 3 and config.seed == 7 and config.n_envs == 2
    assert config.server_ip == '192.0.2.10' and config.server_port == 5566
    snapshot['rdm']['action_replenish_threshold'] = 12
    with pytest.raises(ValidationError):
        simulation.EvaluationConfig(env_name='Task', client_config=snapshot)
    snapshot['robots']['type'] = 'mock'
    with pytest.raises(ValidationError, match='Select robocasa or aloha_robotwin'):
        simulation.EvaluationConfig(env_name='Task', client_config=snapshot)


@pytest.mark.parametrize('storage', ['robocasa_web', 'simulation_web'])
def test_history_storage_preserves_artifacts_and_resume_paths(tmp_path, monkeypatch, storage):
    folder = tmp_path / 'data' / storage / 'jobs' / 'saved'
    output = folder / 'output'
    output.mkdir(parents=True)
    config = simulation.EvaluationConfig(env_name='Task')
    (folder / 'job.json').write_text(json.dumps({
        'id': 'saved', 'status': 'failed', 'started': time.time(), 'config': config.model_dump(),
    }))
    stats = {'run_id': 'saved', 'env_name': 'Task', 'episodes': [{'episode': 0, 'success': True}]}
    (output / 'stats.json').write_text(json.dumps(stats))
    (folder / 'evaluation.log').write_text('saved evaluation log')
    manager = simulation.EvaluationJobs(tmp_path)
    monkeypatch.setattr(simulation, 'manager', manager)
    command = manager.command(config, 'saved')
    assert command[command.index('--output_dir') + 1] == str(output)
    assert command[command.index('--record_dir') + 1] == f'data/{storage}/jobs/saved/lerobot'
    assert manager.get('saved')['directory'] == f'data/{storage}/jobs/saved'
    assert manager.get('saved')['progress'][0]['num_episodes'] == 1
    app = FastAPI()
    app.include_router(simulation.router)
    with TestClient(app) as client:
        assert client.get('/api/simulation/jobs/saved/logs').json()['text'] == 'saved evaluation log'
        assert 'output/stats.json' in client.get('/api/simulation/jobs/saved/files').json()
        assert client.get('/api/simulation/jobs/saved/artifact/output/stats.json').json() == stats
    manager._save(manager.jobs['saved'])
    assert json.loads((folder / 'job.json').read_text())['status'] == 'failed'
    assert manager.job_directory('new') == tmp_path / 'data/simulation_web/jobs/new'


def test_job_saves_and_reloads_configuration_snapshot(tmp_path, monkeypatch):
    import runpy
    from conf.client_conf import get_client_config
    from client.utils.util import apply_user_config
    snapshot = {
        'robots': {'type': 'robocasa'},
        'rdm': {'mode': 'sync'},
        'intra_chunk': {'intra_chunk_mode': 'fitting', 'fitting_deg': 3},
        'inter_chunk': {'inter_chunk_mode': 'min_jerk', 'min_jerk': {'blend_threshold': .6}},
    }
    config = simulation.EvaluationConfig(env_name='Task', python=sys.executable, client_config=snapshot)
    manager = simulation.EvaluationJobs(tmp_path)
    command = manager.command(config, 'saved')
    assert '--client_config' not in command and '--user_conf' in command
    from scripts.robocasa_eval import build_parser
    assert build_parser().parse_args(command[3:]).control_period_ms == 1
    monkeypatch.setattr(simulation.subprocess, 'run', lambda *a, **kw: subprocess.CompletedProcess(a, 0, '', ''))
    monkeypatch.setattr(manager, 'command', lambda *args: [sys.executable, '-c', 'pass'])
    try:
        job = manager.start(config, 'saved')
        folder = manager.directory / job['id']
        loaded = runpy.run_path(str(folder / 'client_config.py'))['get_user_config']()
        assert loaded == snapshot == json.loads((folder / 'client_config.json').read_text())
        pipeline = apply_user_config(get_client_config(), loaded)
        assert pipeline.intra_chunk.fitting_deg == 3
        assert pipeline.inter_chunk.min_jerk.blend_threshold == .6
        restored = simulation.EvaluationConfig(**json.loads((folder / 'job.json').read_text())['config'])
        assert restored.client_config == snapshot and restored.intra_chunk_mode == 'fitting'
    finally:
        manager.close()
