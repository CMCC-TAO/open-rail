import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

from conf.models_conf import get_gr00t_config, get_tao_config


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


@pytest.mark.parametrize('tag', ['a2d_gripper', 'robocasa_panda_omron', 'aloha_robotwin'])
@pytest.mark.parametrize('explicit', [False, True])
def test_tao_default_camera_mapping(monkeypatch, tag, explicit):
    seen = {}

    class Policy:
        def get_action(self, observation):
            seen.update(observation)
            return {'action': {'test': np.zeros((1, 2, 1))}}

    module = load_backend(monkeypatch, Path(__file__).parents[1] / 'server/models/tao/tao.py', {
        'torch': {}, 'tao.serving.policy': {'PolicyTao': Policy},
    })
    model = module.ModelVLA.__new__(module.ModelVLA)
    model.cfg = get_tao_config()
    model.cfg.embodiment_tag = tag
    if explicit:
        model.cfg.video_keys = ['custom_head', 'custom_left', 'custom_right']
    model.policy = Policy()
    model._reported_action_order = False
    obs = {key: np.full((2, 2, 3), index) for index, key in enumerate(
        ['cam.head', 'cam.hand_left', 'cam.hand_right'])}
    obs.update(state=np.zeros(14), language=['test'])
    model.infer([{'ref_timestamp': 1, 'loc_timestamp': 2, 'obs': obs}])
    expected = (['custom_head', 'custom_left', 'custom_right'] if explicit else
                ['cam_top_head', 'cam_left_wrist', 'cam_right_wrist']
                if tag == 'aloha_robotwin' else
                ['base_image', 'left_wrist_image', 'right_wrist_image'])
    assert list(seen['video']) == expected
    for index, key in enumerate(expected):
        np.testing.assert_array_equal(seen['video'][key], np.full((1, 1, 2, 2, 3), index))


@pytest.mark.parametrize('prefix', ['', 'action.'])
@pytest.mark.parametrize('explicit', [False, True])
def test_tao_robotwin_camera_and_action_mapping(monkeypatch, prefix, explicit):
    seen = {}
    class Policy:
        def get_action(self, observation):
            seen.update(observation)
            return {'action': {prefix + 'right_gripper': np.full((1, 2, 1), 4),
                               prefix + 'left_arm': np.full((1, 2, 6), 1),
                               prefix + 'right_arm': np.full((1, 2, 6), 3),
                               prefix + 'left_gripper': np.full((1, 2, 1), 2)}}
    module = load_backend(monkeypatch, Path(__file__).parents[1] / 'server/models/tao/tao.py', {
        'torch': {}, 'tao.serving.policy': {'PolicyTao': Policy},
    })
    model = module.ModelVLA.__new__(module.ModelVLA)
    order = ['left_arm', 'left_gripper', 'right_arm', 'right_gripper']
    model.cfg = {'video_keys': ['head_camera', 'left_camera', 'right_camera'],
                 'action_keys': [prefix + key for key in reversed(order)] if explicit else []}
    model.policy = Policy()
    model._reported_action_order = False
    frame = {'ref_timestamp': 1, 'loc_timestamp': 2, 'obs': {
        'cam.head': np.zeros((2, 2, 3)), 'cam.hand_left': np.zeros((2, 2, 3)),
        'cam.hand_right': np.zeros((2, 2, 3)), 'state': np.zeros(14), 'language': ['test'],
    }}
    result = model.infer([frame])
    assert list(seen['video']) == model.cfg['video_keys']
    expected = ([4] + [3] * 6 + [2] + [1] * 6) if explicit else ([1] * 6 + [2] + [3] * 6 + [4])
    np.testing.assert_array_equal(result['pred_action'][0], expected)


@pytest.mark.parametrize('prefix', ['', 'action.'])
@pytest.mark.parametrize('hand_key', ['hand', 'gripper'])
def test_tao_unitree_expansion_keeps_both_arms_before_hands(monkeypatch, prefix, hand_key):
    class Policy:
        def get_action(self, observation):
            return {'action': {
                prefix + 'right_arm': np.full((1, 2, 7), 2),
                prefix + 'left_' + hand_key: np.full((1, 2, 1), 400),
                prefix + 'left_arm': np.full((1, 2, 7), 1),
                prefix + 'right_' + hand_key: np.full((1, 2, 1), 200),
            }}

    module = load_backend(monkeypatch, Path(__file__).parents[1] / 'server/models/tao/tao.py', {
        'torch': {}, 'tao.serving.policy': {'PolicyTao': Policy},
    })
    model = module.ModelVLA.__new__(module.ModelVLA)
    model.cfg = {'embodiment_tag': 'unitree_g1'}
    model.policy = Policy()
    model._reported_action_order = False
    frame = {'ref_timestamp': 1, 'loc_timestamp': 2, 'obs': {
        'cam.head': np.zeros((2, 2, 3)), 'cam.hand_left': np.zeros((2, 2, 3)),
        'cam.hand_right': np.zeros((2, 2, 3)), 'state': np.zeros(26), 'language': ['test'],
    }}
    result = model.infer([frame])
    np.testing.assert_array_equal(result['pred_action'], np.tile(
        [1] * 7 + [2] * 7 + [300, 400, 400, 400, 400, 750]
        + [200, 200, 200, 200, 200, 750], (2, 1),
    ))
