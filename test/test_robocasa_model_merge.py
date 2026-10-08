import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

from conf.models_conf import get_gr00t_config


ACTION_SIZES = {'end_effector_position': 3, 'end_effector_rotation': 3,
                'gripper_close': 1, 'base_motion': 4, 'control_mode': 1}


def load_backend(monkeypatch, path, imports):
    for name, attributes in imports.items():
        module = ModuleType(name)
        module.__dict__.update(attributes)
        monkeypatch.setitem(sys.modules, name, module)
    spec = importlib.util.spec_from_file_location('merge_model_check', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('metadata_key', ['panda_omron', 'robocasa_panda_omron', 'checkpoint_robot'])
def test_gr00t_metadata_and_modality_mapping(monkeypatch, tmp_path, metadata_key):
    model_dir = tmp_path / 'experiment_cfg'
    model_dir.mkdir()
    (model_dir / 'metadata.json').write_text(json.dumps({metadata_key: {
        'modalities': {'state': {'base': {'shape': [3]}}}}}))
    data_config = SimpleNamespace(
        video_keys=['video.left', 'video.right', 'video.wrist'],
        language_keys=['annotation.human.task_description'],
        action_keys=[f'action.{key}' for key in ACTION_SIZES],
        modality_config=lambda: {}, transform=lambda: None,
    )
    class Policy:
        model = 'fake'
        modality_config = {}

        def __init__(self, **kwargs):
            pass

        def get_action(self, observation):
            self.observation = observation
            return {f'action.{key}': np.full((2, size), index)
                    for index, (key, size) in reversed(list(enumerate(ACTION_SIZES.items())))}
    path = Path(__file__).parents[1] / 'server/models/gr00t/gr00t_n1_5.py'
    module = load_backend(monkeypatch, path, {
        'torch': {'cuda': SimpleNamespace(is_available=lambda: False)},
        'gr00t.model.policy': {'Gr00tPolicy': Policy},
        'gr00t.data.schema': {'EmbodimentTag': object},
        'gr00t.experiment.data_config': {'DATA_CONFIG_MAP': {'panda_omron': data_config}},
    })
    config = get_gr00t_config()
    config.model_path = str(tmp_path)
    config.data_config_key = 'panda_omron'
    config.embodiment_tag = 'robocasa_panda_omron'
    model = module.ModelVLA(config)
    frame = {'ref_timestamp': 1, 'loc_timestamp': 2, 'obs': {
        'cam.head': np.ones((2, 2, 3)), 'cam.hand_left': np.ones((2, 2, 3)) * 2,
        'cam.hand_right': np.ones((2, 2, 3)) * 3, 'state': np.zeros(3),
        'language': ['test'],
    }}
    result = model.infer([frame])
    expected = [0] * 3 + [1] * 3 + [2] + [3] * 4 + [4]
    np.testing.assert_array_equal(result['pred_action'][0], expected)
    assert set(model.policy.observation) == {
        'video.left', 'video.right', 'video.wrist',
        'annotation.human.task_description', 'state.base',
    }


@pytest.mark.parametrize('prefix', ['', 'action.'])
def test_tao_action_order_does_not_follow_dictionary_order(monkeypatch, prefix):
    class Policy:
        def get_action(self, observation):
            return {'action': {prefix + key: np.full((1, 2, size), index)
                    for index, (key, size) in reversed(list(enumerate(ACTION_SIZES.items())))}}
    path = Path(__file__).parents[1] / 'server/models/tao/tao.py'
    module = load_backend(monkeypatch, path, {
        'torch': {}, 'tao.serving.policy': {'PolicyTao': Policy},
    })
    model = module.ModelVLA.__new__(module.ModelVLA)
    model.cfg = {'action_keys': []}
    model.policy = Policy()
    model._reported_action_order = False
    frame = {'ref_timestamp': 1, 'loc_timestamp': 2, 'obs': {
        'cam.head': np.zeros((2, 2, 3)), 'cam.hand_left': np.zeros((2, 2, 3)),
        'cam.hand_right': np.zeros((2, 2, 3)), 'state': np.zeros(3), 'language': ['test'],
    }}
    result = model.infer([frame])
    np.testing.assert_array_equal(result['pred_action'][0],
                                  [0] * 3 + [1] * 3 + [2] + [3] * 4 + [4])
