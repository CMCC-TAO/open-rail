from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from client.robots.robocasa.profiling import install_mujoco_timing, log_render_device, measure_native


def test_native_timing_is_thread_local_and_does_not_double_count(monkeypatch):
    import client.robots.robocasa.profiling as profiling

    ticks = iter(range(100))
    monkeypatch.setattr(profiling.time, 'perf_counter', lambda: next(ticks))
    module = SimpleNamespace(mj_step1=lambda: 'done')
    module.mj_step = lambda: module.mj_step1()
    install_mujoco_timing(module)
    wrapped = module.mj_step
    install_mujoco_timing(module)
    assert module.mj_step is wrapped
    sample = {}
    with measure_native(sample):
        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(module.mj_step).result() == 'done'
        assert sample == {}
        assert module.mj_step() == 'done'
    assert sample == {'physics_s': 1}
    module.mj_step()
    assert sample == {'physics_s': 1}


def test_native_timing_restores_context_after_failure():
    def fail():
        raise RuntimeError('native failure')

    module = SimpleNamespace(mjr_readPixels=fail)
    install_mujoco_timing(module)
    sample = {}
    with pytest.raises(RuntimeError, match='native failure'), measure_native(sample):
        module.mjr_readPixels()
    assert sample['readback_s'] >= 0
    previous = dict(sample)
    with pytest.raises(RuntimeError):
        module.mjr_readPixels()
    assert sample == previous


def test_render_device_reports_actual_process_gpu(monkeypatch, caplog):
    import logging
    import client.robots.robocasa.profiling as profiling

    monkeypatch.setattr(profiling.os, 'getpid', lambda: 123)
    xml = '<nvidia_smi_log><gpu><uuid>other</uuid></gpu><gpu><uuid>actual</uuid><product_name>H100</product_name><processes><process_info><pid>123</pid></process_info></processes></gpu></nvidia_smi_log>'
    monkeypatch.setattr(profiling.subprocess, 'run', lambda *a, **kw: SimpleNamespace(stdout=xml))
    with caplog.at_level(logging.INFO):
        log_render_device(logging.getLogger('device_test'))
    assert "'index': 1" in caplog.text
    assert "'uuid': 'actual'" in caplog.text
    assert "'uuid': 'other'" not in caplog.text


def test_render_device_query_failure_is_nonfatal(monkeypatch, caplog):
    import logging
    import client.robots.robocasa.profiling as profiling

    def unavailable(*args, **kwargs):
        raise FileNotFoundError('nvidia-smi missing')

    monkeypatch.setattr(profiling.subprocess, 'run', unavailable)
    with caplog.at_level(logging.INFO):
        log_render_device(logging.getLogger('device_test'))
    assert 'gpu_query_error' in caplog.text
