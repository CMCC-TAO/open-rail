"""Step timing and optional MuJoCo diagnostics."""

import functools
import os
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from contextlib import contextmanager


class StepTimings:
    def __init__(self, logger, interval=30, label='Simulation'):
        self.logger = logger
        self.label = label
        self.interval = interval
        self.count = 0
        self.totals = {}
        self.maxima = {}
        self.last_report = 0.0

    def add(self, sample, episode, step):
        self.count += 1
        for key, value in sample.items():
            self.totals[key] = self.totals.get(key, 0.0) + value
            self.maxima[key] = max(self.maxima.get(key, 0.0), value)
        now = time.monotonic()
        if self.count >= self.interval or step == 1 or (
            sample.get('total_s', 0) >= 1 and now - self.last_report >= 5
        ):
            self.report(episode, step)

    def report(self, episode, step):
        if not self.count:
            return
        self.logger.info(
            '%s step timings: episode=%d step=%d samples=%d avg=%s max=%s',
            self.label,
            episode, step, self.count,
            {k: round(v / self.count, 6) for k, v in self.totals.items()},
            {k: round(v, 6) for k, v in self.maxima.items()},
        )
        self.count = 0
        self.totals.clear()
        self.maxima.clear()
        self.last_report = time.monotonic()


_local = threading.local()
_install_lock = threading.Lock()
_phases = {
    'mj_step': 'physics_s',
    'mj_step1': 'physics_s',
    'mj_step2': 'physics_s',
    'mj_forward': 'physics_s',
    'mjr_render': 'render_s',
    'mjr_readPixels': 'readback_s',
}


def install_mujoco_timing(module):
    with _install_lock:
        for name, phase in _phases.items():
            original = getattr(module, name, None)
            if original is None or getattr(original, '_simulation_mujoco_timing', False):
                continue

            @functools.wraps(original)
            def timed(*args, _original=original, _phase=phase, **kwargs):
                sample = getattr(_local, 'sample', None)
                if sample is None or _phase in _local.active:
                    return _original(*args, **kwargs)
                _local.active.add(_phase)
                started = time.perf_counter()
                try:
                    return _original(*args, **kwargs)
                finally:
                    sample[_phase] = sample.get(_phase, 0.0) + time.perf_counter() - started
                    _local.active.remove(_phase)

            timed._simulation_mujoco_timing = True
            setattr(module, name, timed)


@contextmanager
def measure_native(sample):
    previous = getattr(_local, 'sample', None), getattr(_local, 'active', set())
    _local.sample, _local.active = sample, set()
    try:
        yield
    finally:
        _local.sample, _local.active = previous


def log_render_device(logger):
    device = {
        'pid': os.getpid(),
        'backend': os.environ.get('MUJOCO_GL', 'default'),
        'CUDA_VISIBLE_DEVICES': os.environ.get('CUDA_VISIBLE_DEVICES', 'unset'),
        'MUJOCO_EGL_DEVICE_ID': os.environ.get('MUJOCO_EGL_DEVICE_ID', 'unset'),
    }
    try:
        result = subprocess.run(
            ['nvidia-smi', '-q', '-x'], capture_output=True, text=True, timeout=3,
            check=True,
        )
        gpus = []
        for index, gpu in enumerate(ET.fromstring(result.stdout).findall('gpu')):
            if any(p.findtext('pid') == str(os.getpid()) for p in gpu.findall('processes/process_info')):
                gpus.append({'index': index, 'uuid': gpu.findtext('uuid'), 'name': gpu.findtext('product_name')})
        device['process_gpus'] = gpus
    except (OSError, subprocess.SubprocessError, ET.ParseError) as exc:
        device['gpu_query_error'] = str(exc)
    logger.info('MuJoCo render device: %s', device)
