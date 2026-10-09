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
    assert command[command.index('--record_dir') + 1] == 'data/robocasa_web/jobs/test/lerobot'
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
    assert args.record_dir == 'data/robocasa_web/jobs/test/lerobot'
    with pytest.raises(ValidationError):
        simulation.EvaluationConfig(platform='robotwin', env_name='Task', no_expert_check=True)
    with pytest.raises(ValidationError):
        simulation.EvaluationConfig(platform='robotwin', env_name='Task', intra_chunk_mode='local')


def test_robotwin_preflight_does_not_require_robocasa(tmp_path, monkeypatch):
    root = tmp_path / 'RoboTwin'
    (root / 'envs').mkdir(parents=True)
    (root / 'task_config').mkdir()
    (root / 'envs/Task.py').write_text('')
    (root / 'task_config/demo_clean.yml').write_text('')
    manager = simulation.EvaluationJobs(tmp_path)
    seen = []
    def check(command, **kwargs):
        seen.append(command)
        return subprocess.CompletedProcess(command, 1, 'sapien', '')
    monkeypatch.setattr(simulation.subprocess, 'run', check)
    with pytest.raises(ValueError, match='sapien'):
        manager.start(simulation.EvaluationConfig(platform='robotwin', env_name='Task', python=sys.executable,
                                                robotwin_root=str(root)))
    assert 'sapien' in seen[0] and 'robocasa' not in seen[0]
