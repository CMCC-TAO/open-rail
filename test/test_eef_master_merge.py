import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest

from conf.models_conf import ModelType, get_xvla_eef_config
from conf.server_conf import get_vla_server_config
from run_server import override_config_with_args, parse_args


@pytest.mark.parametrize('model_type', ['gr00t_n1_7_eef', 'xvla_eef'])
def test_eef_server_options_preserve_simulation_overrides(monkeypatch, model_type):
    monkeypatch.setattr(sys, 'argv', [
        'run_server.py', '--model_type', model_type,
        '--model_path', '/checkpoint', '--server_port', '5588',
    ])
    config = override_config_with_args(get_vla_server_config(), parse_args())
    assert config.models.type == ModelType(model_type)
    assert config.models[model_type].model_path == '/checkpoint'
    assert config.zmq.port == '5588'
    assert Path(config.models[model_type].urdf_path).is_file()
    assert config.image_pad_and_resize == (model_type == 'gr00t_n1_7_eef')


def test_xvla_initializes_with_default_ik_settings(monkeypatch, tmp_path):
    model = Mock(action_mode='ee6d', action_space=SimpleNamespace(dim_action=20),
                 config=SimpleNamespace(num_domains=1))
    model.to.return_value = model
    solver = Mock()
    for name, attributes in {
        'torch': {'cuda': SimpleNamespace(is_available=lambda: False),
                  'device': lambda value: value, 'float32': 'float32',
                  'bfloat16': 'bfloat16'},
        'server.utils.eef_utils.action_to_joints': {'ActionIKSolver': solver},
        'models.modeling_xvla': {'XVLA': SimpleNamespace(
            from_pretrained=Mock(return_value=model))},
        'models.processing_xvla': {'XVLAProcessor': SimpleNamespace(
            from_pretrained=Mock())},
    }.items():
        module = ModuleType(name)
        module.__dict__.update(attributes)
        monkeypatch.setitem(sys.modules, name, module)
    path = Path(__file__).parents[1] / 'server/models/xvla/xvla_eef.py'
    spec = importlib.util.spec_from_file_location('server.models.xvla._merge_check', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = get_xvla_eef_config()
    config.model_path = str(tmp_path)
    adapter = module.ModelVLA(config)
    solver.assert_called_once()
    assert solver.call_args.kwargs['rotation_type'] == 'rot6d'
    assert adapter.model is model
    model.eval.assert_called_once()
