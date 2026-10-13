import sys
import subprocess
from types import ModuleType

import pytest

from web_client.task_catalog import task_catalog


def test_robotwin_catalog_excludes_helpers(tmp_path):
    envs = tmp_path / 'envs'
    envs.mkdir()
    (envs / 'stack.py').write_text('class stack: pass')
    (envs / 'helper.py').write_text('class Other: pass')
    (envs / '_private.py').write_text('class _private: pass')
    result = task_catalog('robotwin', sys.executable, str(tmp_path), str(tmp_path))
    assert result['tasks'] == ['stack']
    assert result['suites'][0]['tasks'] == ['stack']


def test_robocasa_catalog_does_not_import_simulator(tmp_path, monkeypatch):
    monkeypatch.setattr('web_client.task_catalog.subprocess.run',
                        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, '', ''))
    project = tmp_path / 'project'
    registry = tmp_path / 'robocasa/robocasa/utils/dataset_registry.py'
    registry.parent.mkdir(parents=True)
    registry.write_text(
        'import unavailable_simulator\n'
        'TASK_SET_REGISTRY = dict(all_tasks=["A", "B"], target50=["B"], pretrain50=["A"])\n'
        'raise RuntimeError("Do not initialize datasets")\n'
    )
    result = task_catalog('robocasa', sys.executable, '', str(project))
    assert result['tasks'] == ['A', 'B']
    assert result['suites'][1] == {'id': 'target50', 'tasks': ['B'], 'split': 'target'}
    assert result['suites'][2]['split'] == 'pretrain'


@pytest.mark.parametrize('selection,valid', [('A,B', True), ('A,A', False), ('A,Missing', False), ('A,', False)])
def test_custom_robocasa_task_subset(monkeypatch, selection, valid):
    registry = ModuleType('robocasa.utils.dataset_registry')
    registry.TASK_SET_REGISTRY = {'all_tasks': ['A', 'B']}
    monkeypatch.setitem(sys.modules, 'robocasa.utils.dataset_registry', registry)
    from scripts.robocasa_eval import _task_suite

    if valid:
        assert _task_suite(selection) == ['A', 'B']
    else:
        with pytest.raises(ValueError):
            _task_suite(selection)
