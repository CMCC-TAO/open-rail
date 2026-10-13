"""Read task catalogs without initializing simulators."""

import ast
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
import subprocess


@lru_cache(maxsize=8)
def task_catalog(platform, python, robotwin_root, project_root):
    if platform == 'robotwin':
        tasks = []
        for path in sorted((Path(robotwin_root) / 'envs').glob('*.py')):
            if path.stem.startswith('_'):
                continue
            if any(isinstance(node, ast.ClassDef) and node.name == path.stem
                   for node in ast.parse(path.read_text()).body):
                tasks.append(path.stem)
        if not tasks:
            raise ValueError('No RoboTwin tasks found; check robotwin_root.')
        return {'tasks': tasks, 'suites': [{'id': 'all_tasks', 'tasks': tasks, 'split': None}]}

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
