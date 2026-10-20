import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from client.simulation.evaluation import worker_gpu


@pytest.mark.parametrize('gpu,index,expected', [
    (None, 0, None), ('', 1, None), ('2', 3, '2'),
    ('0,2', None, '0'), ('0,2', 0, '0'), ('0,2', 1, '2'),
    ('0,2', 2, '0'), ('0,2', 3, '2'),
])
def test_worker_gpu(gpu, index, expected):
    assert worker_gpu(gpu, index) == expected


@pytest.mark.parametrize('gpu', ['-1', 'abc', '0,,2', '0,', '0, 2'])
def test_worker_gpu_rejects_invalid_indices(gpu):
    with pytest.raises(ValueError, match='comma-separated'):
        worker_gpu(gpu)


@pytest.mark.parametrize('gpu,index,expected', [
    ('0,2', 0, '0'), ('0,2', 1, '2'), ('0,2', 3, '2'), ('', 1, '7'),
])
def test_mujoco_device_environment_is_process_local(monkeypatch, gpu, index, expected):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '7')
    monkeypatch.setenv('MUJOCO_EGL_DEVICE_ID', '7')
    code = (
        'import json,os,sys; '
        'from client.simulation.evaluation import configure_mujoco_gpu; '
        'configure_mujoco_gpu(sys.argv[1], int(sys.argv[2])); '
        'print(json.dumps([os.environ["CUDA_VISIBLE_DEVICES"], '
        'os.environ["MUJOCO_EGL_DEVICE_ID"]]))'
    )
    result = subprocess.run(
        [sys.executable, '-c', code, gpu, str(index)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, check=True,
    )
    assert json.loads(result.stdout) == [expected, expected]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '7'
    assert os.environ['MUJOCO_EGL_DEVICE_ID'] == '7'
