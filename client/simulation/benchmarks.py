"""Benchmark registration and lightweight discovery, without importing simulators."""

import ast
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
import re
import subprocess
from typing import Callable


COMMON_CLI_FIELDS = frozenset('''
gpu n_episodes n_envs n_action_steps control_period_ms seed mode intra_chunk_mode
intra_chunk_sample_ratio inter_chunk_mode async_replenish_threshold
max_async_observation_lag_steps max_episode_steps episode_timeout stall_timeout
worker_episodes max_native_restarts server_reconnect_interval server_reconnect_timeout
server_ip server_port preprocess record_fps video_fps video_layout
'''.split())
COMMON_CLIENT_FIELDS = (
    'python', 'gpu', 'n_envs', 'seed', 'video_fps', 'video_layout',
)


@dataclass(frozen=True)
class BenchmarkSpec:
    id: str
    robot_type: str
    label: str
    script: str
    dependencies: tuple[str, ...]
    catalog: Callable
    cli_fields: frozenset[str] = COMMON_CLI_FIELDS
    client_fields: tuple[str, ...] = COMMON_CLIENT_FIELDS
    defaults: dict = field(default_factory=dict)
    form_fields: tuple[str, ...] = ()
    named_suites: bool = False
    resampling_modes: tuple[str, ...] = ('raw', 'interpolation', 'fitting')
    validate: Callable | None = None
    prepare: Callable | None = None

    def describe(self):
        return {
            'id': self.id, 'robot_type': self.robot_type, 'label': self.label,
            'form_fields': list(self.form_fields), 'named_suites': self.named_suites,
            'resampling_modes': list(self.resampling_modes),
        }


BENCHMARKS = {}


def register_benchmark(spec):
    if not re.fullmatch(r'[a-z][a-z0-9_]*', spec.id):
        raise ValueError(f'Invalid benchmark ID: {spec.id}')
    if spec.id in BENCHMARKS or any(item.robot_type == spec.robot_type for item in BENCHMARKS.values()):
        raise ValueError(f'Benchmark or robot type already registered: {spec.id}')
    BENCHMARKS[spec.id] = spec
    return spec


def get_benchmark(name):
    try:
        return BENCHMARKS[name]
    except KeyError as error:
        raise ValueError(f'Unknown simulation benchmark: {name}') from error


def benchmark_for_robot(robot_type):
    for spec in BENCHMARKS.values():
        if spec.robot_type == robot_type:
            return spec
    choices = ', '.join(spec.robot_type for spec in BENCHMARKS.values())
    raise ValueError(f'Select a simulation robot in Configuration: {choices}')


def _robocasa_catalog(python, settings, project_root):
    probe = subprocess.run(
        [python, '-c', 'import importlib.util; s=importlib.util.find_spec("robocasa"); print(s.origin if s else "")'],
        capture_output=True, text=True, timeout=15, check=True,
    )
    origin = probe.stdout.strip()
    project = Path(project_root)
    candidates = ([Path(origin).parent / 'utils/dataset_registry.py'] if origin else []) + [
        parent / 'robocasa/robocasa/utils/dataset_registry.py' for parent in (project.parent, project.parent.parent)
    ]
    path = next((path for path in candidates if path.is_file()), None)
    if path is None:
        raise ValueError('RoboCasa task registry not found; check the configured Python environment.')
    assignments = []
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign):
            assignments.append(node)
            if any(isinstance(target, ast.Name) and target.id == 'TASK_SET_REGISTRY' for target in node.targets):
                break
    namespace = {'OrderedDict': OrderedDict}
    exec(compile(ast.Module(body=assignments, type_ignores=[]), str(path), 'exec'), namespace)
    registry = namespace['TASK_SET_REGISTRY']
    return {'tasks': list(registry['all_tasks']), 'suites': [
        {'id': name, 'tasks': tasks,
         'split': 'target' if name in ('target50', 'atomic_seen', 'composite_seen', 'composite_unseen')
         else 'pretrain' if name.startswith(('pretrain', 'lifelong_learning')) or name == 'mg_dataset_tasks' else None}
        for name, tasks in registry.items()
    ]}


def _robotwin_catalog(python, settings, project_root):
    tasks = []
    for path in sorted((Path(settings['robotwin_root']) / 'envs').glob('*.py')):
        if path.stem.startswith('_'):
            continue
        if any(isinstance(node, ast.ClassDef) and node.name == path.stem
               for node in ast.parse(path.read_text()).body):
            tasks.append(path.stem)
    if not tasks:
        raise ValueError('No RoboTwin tasks found; check robotwin_root.')
    return {'tasks': tasks, 'suites': [{'id': 'all_tasks', 'tasks': tasks, 'split': None}]}


def _validate_robotwin(config):
    if config.env_name and not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', config.env_name):
        raise ValueError('Invalid RoboTwin task name')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', config.task_config):
        raise ValueError('Invalid RoboTwin task config')
    if config.no_expert_check and not config.instruction.strip():
        raise ValueError('Disabling expert check requires a fixed instruction')
    if config.max_seed_attempts > config.seed_stride:
        raise ValueError('Seed attempts must not exceed seed stride')
    if config.seed < 0:
        raise ValueError('RoboTwin seed must be non-negative')


def _prepare_robotwin(config):
    root = Path(config.robotwin_root).expanduser().resolve()
    if not (root / 'envs').is_dir() or not (root / 'task_config' / (config.task_config + '.yml')).is_file():
        raise ValueError('RoboTwin root or task config is unavailable')
    if config.env_name and not (root / 'envs' / (config.env_name + '.py')).is_file():
        raise ValueError('RoboTwin task is unavailable')
    config.robotwin_root = str(root)
    if config.task_suite:
        from scripts.aloha_robotwin_eval import _task_names

        selection = Path(config.task_suite).expanduser()
        if ',' not in config.task_suite and selection.is_file():
            config.task_suite = str(selection.resolve())
        task_names = _task_names(config.task_suite)
        config.task_suite = ','.join(task_names)
        for name in task_names:
            if not (root / 'envs' / (name + '.py')).is_file():
                raise ValueError(f'RoboTwin task is unavailable: {name}')


register_benchmark(BenchmarkSpec(
    id='robocasa', robot_type='robocasa_pandas', label='RoboCasa_Pandas', script='robocasa_eval.py',
    dependencies=('robocasa', 'robosuite', 'zmq', 'numpy'), catalog=_robocasa_catalog,
    cli_fields=COMMON_CLI_FIELDS | {'split', 'mujoco_gl'},
    client_fields=COMMON_CLIENT_FIELDS + ('split', 'max_episode_steps'),
    defaults={'gpu': '2'}, form_fields=('split',), named_suites=True,
))
register_benchmark(BenchmarkSpec(
    id='robotwin', robot_type='robotwin_aloha', label='RoboTwin_ALOHA', script='aloha_robotwin_eval.py',
    dependencies=('zmq', 'numpy', 'sapien', 'torch', 'yaml', 'curobo'), catalog=_robotwin_catalog,
    cli_fields=COMMON_CLI_FIELDS | {
        'robotwin_root', 'task_config', 'instruction_type', 'render_observation_mode', 'instruction',
        'max_transition_steps', 'max_seed_attempts', 'seed_stride', 'seed_selection_timeout', 'no_expert_check',
    },
    client_fields=COMMON_CLIENT_FIELDS + ('robotwin_root', 'task_config', 'instruction_type', 'render_observation_mode'),
    defaults={'n_action_steps': 50, 'seed': 0},
    form_fields=('task_config', 'instruction_type', 'render_observation_mode'),
    resampling_modes=('interpolation',), validate=_validate_robotwin, prepare=_prepare_robotwin,
))
