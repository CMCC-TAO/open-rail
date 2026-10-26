from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
import yaml

from client.simulation.evaluation import build_parser, configure_pipeline
from client.simulation.io_adapter import SimulationIOAdapter, fields_from_layout
from client.simulation.model_bridge import SimulationModelBridge, build_model
from conf import embodiments_conf
from conf.client_conf import get_client_config
from conf.embodiments_conf import simulation_embodiment
from conf.models_conf import ModelType
from conf.robots_conf import get_robotwin_aloha_config
from conf.server_conf import get_vla_server_config
from run_server import override_config_with_args, parse_args
from web_client.simulation import EvaluationConfig, manager


def configure(model_type, tag):
    with patch.object(sys, 'argv', ['run_server.py', '--model_type', model_type, '--embodiment_tag', tag]):
        return override_config_with_args(get_vla_server_config(), parse_args()).models


def observation(state=None):
    return [{
        'ref_timestamp': 123, 'loc_timestamp': 456,
        'obs': {
            'state': np.arange(14) if state is None else state,
            'language': ['stack the bowls'],
            **{f'cam.{role}': np.zeros((4, 4, 3), dtype=np.uint8)
               for role in ('head', 'hand_left', 'hand_right')},
        },
    }]


class SimulationEmbodimentTests(unittest.TestCase):
    def test_all_model_types_use_the_same_selector_and_reject_unadapted_pairs(self):
        for tag in ('robotwin_aloha', 'robocasa_pandas_omron'):
            embodiment = simulation_embodiment(tag)
            for model_type in ModelType:
                with self.subTest(tag=tag, model=model_type.value):
                    if model_type.value not in embodiment.models:
                        with self.assertRaisesRegex(ValueError, 'has no simulation adaptation'):
                            configure(model_type.value, tag)
                        continue
                    models = configure(model_type.value, tag)
                    group = 'gr00t' if model_type == ModelType.GR00T_N1_5 else model_type.value
                    self.assertEqual(models[group].simulation_embodiment, embodiment.name)
                    self.assertEqual(models[group].simulation_io_profile, embodiment.io_profile)

    def test_aliases_resolve_to_canonical_names_and_sdk_settings(self):
        for tag in ('robotwin_aloha', 'aloha_robotwin'):
            self.assertEqual(simulation_embodiment(tag).name, 'robotwin_aloha')
        config = configure('tao', 'robotwin_aloha').tao
        self.assertEqual(config.simulation_embodiment, 'robotwin_aloha')
        self.assertEqual(config.embodiment_tag, 'aloha_robotwin')
        for tag in ('robocasa', 'robocasa_pandas', 'robocasa_panda_omron', 'robocasa_pandas_omron'):
            self.assertEqual(simulation_embodiment(tag).name, 'robocasa_pandas')
        config = configure('gr00t_n1_5', 'robocasa_pandas_omron').gr00t
        self.assertEqual(config.embodiment_tag, 'robocasa_panda_omron')
        self.assertEqual(config.data_config_key, 'panda_omron')

    def test_dm05_preserves_checkpoint_contract_and_deployment_settings(self):
        config = configure('dm05', 'robotwin_aloha').dm05
        self.assertIsNone(config.get('robot_type'))
        self.assertIsNone(config.get('dataset_name'))
        self.assertIsNone(config.get('action_dim'))
        self.assertEqual(config.execute_horizon, 16)

    def test_explicit_model_settings_can_register_an_external_training_config(self):
        settings = yaml.safe_load(embodiments_conf.SIMULATION_CONFIG.read_text())
        settings['embodiments']['robotwin_aloha']['models']['pi0'] = {'config': 'custom_pi0_aloha'}
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'simulation.yml'
            path.write_text(yaml.safe_dump(settings))
            with patch.object(embodiments_conf, 'SIMULATION_CONFIG', path):
                self.assertEqual(configure('pi0', 'robotwin_aloha').pi0.config, 'custom_pi0_aloha')

    def test_model_mapping_cannot_replace_explicit_checkpoint_path(self):
        settings = yaml.safe_load(embodiments_conf.SIMULATION_CONFIG.read_text())
        settings['embodiments']['robotwin_aloha']['models']['dm05'] = {'model_path': 'wrong'}
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'simulation.yml'
            path.write_text(yaml.safe_dump(settings))
            with patch.object(embodiments_conf, 'SIMULATION_CONFIG', path):
                with self.assertRaisesRegex(ValueError, 'Invalid model settings'):
                    configure('dm05', 'robotwin_aloha')

    def test_unknown_dm05_tag_is_rejected(self):
        with redirect_stderr(io.StringIO()) as output:
            with self.assertRaises(SystemExit) as error:
                configure('dm05', 'misspelled_robot')
        self.assertEqual(error.exception.code, 2)
        self.assertIn('invalid choice', output.getvalue())
        self.assertIn('robotwin_aloha', output.getvalue())

    def test_evaluator_selects_same_profile_and_checks_platform(self):
        args = build_parser().parse_args([
            '--env_name', 'example', '--embodiment_tag', 'aloha_robotwin',
        ])
        config = get_client_config()
        configure_pipeline(config, args, platform='robotwin')
        self.assertEqual(config.vla_zmq.embodiment_tag, 'robotwin_aloha')
        self.assertEqual(config.vla_zmq.io_profile, configure('dm05', 'robotwin_aloha').dm05.simulation_io_profile)
        with self.assertRaisesRegex(ValueError, 'requires robotwin'):
            configure_pipeline(get_client_config(), args, platform='robocasa')

    def test_evaluator_uses_saved_tag_and_explicit_profile_override(self):
        config = get_client_config()
        config.vla_zmq.embodiment_tag = 'robotwin_aloha'
        args = build_parser().parse_args(['--env_name', 'example', '--io_profile', '/tmp/custom.yml'])
        configure_pipeline(config, args, platform='robotwin')
        self.assertEqual(config.vla_zmq.io_profile, '/tmp/custom.yml')

    def test_saved_profile_override_is_not_lost_when_selecting_a_tag(self):
        config = get_client_config()
        config.vla_zmq.embodiment_tag = 'robotwin_aloha'
        config.vla_zmq.io_profile = '/tmp/custom.yml'
        args = build_parser().parse_args(['--env_name', 'example'])
        configure_pipeline(config, args, platform='robotwin')
        self.assertEqual(config.vla_zmq.io_profile, '/tmp/custom.yml')

    def test_web_jobs_forward_and_validate_the_same_tag(self):
        config = EvaluationConfig(
            env_name='example', platform='robotwin', embodiment_tag='aloha_robotwin',
        )
        command = manager.command(config, 'embodiment-test')
        self.assertEqual(command[command.index('--embodiment_tag') + 1], 'robotwin_aloha')
        with self.assertRaisesRegex(ValueError, 'does not match'):
            EvaluationConfig(env_name='example', platform='robocasa', embodiment_tag='robotwin_aloha')


class SimulationEmbodimentBridgeTests(unittest.TestCase):
    def make_bridge(self, actions=None):
        config = configure('dm05', 'robotwin_aloha').dm05
        model = SimpleNamespace(cfg=config, infer=Mock(return_value={
            'type': 'vla_action',
            'pred_action': np.zeros((16, 14)) if actions is None else actions,
        }))
        return SimulationModelBridge(model, 'dm05'), model

    def test_invalid_state_is_rejected_before_model_inference(self):
        for state in (np.zeros(16), np.zeros((1, 14)), np.full(14, np.nan)):
            with self.subTest(shape=state.shape):
                bridge, model = self.make_bridge()
                with self.assertRaisesRegex(ValueError, 'Invalid state'):
                    bridge.infer(observation(state))
                model.infer.assert_not_called()

    def test_missing_camera_is_rejected(self):
        bridge, model = self.make_bridge()
        sequence = observation()
        del sequence[0]['obs']['cam.hand_left']
        with self.assertRaisesRegex(ValueError, 'Missing simulation camera'):
            bridge.infer(sequence)
        model.infer.assert_not_called()

    def test_incompatible_actions_are_rejected(self):
        for actions in (np.zeros((16, 16)), np.zeros((0, 14)), np.zeros((14,)), np.full((16, 14), np.nan)):
            with self.subTest(shape=actions.shape):
                bridge, _ = self.make_bridge(actions)
                with self.assertRaisesRegex(ValueError, 'requires finite actions'):
                    bridge.infer(observation())

    def test_status_responses_pass_through(self):
        bridge, model = self.make_bridge()
        model.infer.return_value = {'type': 'vla_status', 'status': 'not_ready'}
        self.assertEqual(bridge.infer(observation()), model.infer.return_value)

    def test_tao_native_state_and_action_order_are_converted_by_name(self):
        layout = {
            'right_arm': {'start': 0, 'end': 6}, 'right_hand': {'start': 6, 'end': 7},
            'left_arm': {'start': 7, 'end': 13}, 'left_hand': {'start': 13, 'end': 14},
        }
        policy = SimpleNamespace(embodiment=SimpleNamespace(
            observations={'video': dict.fromkeys(('head', 'left', 'right'))},
            indices={'state': {'sub_components': layout}, 'action': {'sub_components': layout}},
        ))
        model = SimpleNamespace(
            cfg=configure('tao', 'robotwin_aloha').tao, policy=policy,
            infer=Mock(return_value={'type': 'vla_action', 'pred_action': np.arange(14)[None]}),
        )
        result = SimulationModelBridge(model, 'tao').infer(observation())
        expected = [7, 8, 9, 10, 11, 12, 13, 0, 1, 2, 3, 4, 5, 6]
        np.testing.assert_array_equal(model.infer.call_args.args[0][0]['obs']['state'], expected)
        np.testing.assert_array_equal(result['pred_action'], [expected])

    def test_dm05_adapter_to_simulation_client_with_stubbed_sdk(self):
        from server.models.dm05.dm05 import ModelVLA

        actions = np.arange(64 * 14, dtype=np.float32).reshape(64, 14)
        policy = SimpleNamespace(
            backend_label='stub', last_latency_sec=0.001, predict=Mock(return_value=actions),
        )
        sdk = SimpleNamespace(DM05Policy=SimpleNamespace(from_checkpoint=Mock(return_value=policy)))
        models = configure('dm05', 'robotwin_aloha')
        with patch.dict(sys.modules, {'opendm.infer.policy': sdk}), patch(
            'server.models.dm05.dm05._ensure_repo_on_path',
        ), redirect_stdout(io.StringIO()):
            bridge = build_model(models, lambda cfg: ModelVLA(cfg.dm05))
            sequence = observation()
            result = bridge.infer(sequence)
        robot_config = get_robotwin_aloha_config()
        robot = SimpleNamespace(config=robot_config, describe_io=lambda: {
            'state': fields_from_layout(robot_config.action_layout),
            'action': fields_from_layout(robot_config.action_layout),
        })
        adapter = SimulationIOAdapter(robot, SimpleNamespace())
        decoded = adapter.decode({'data': result}, {})['data']
        np.testing.assert_array_equal(decoded['pred_action'], actions[:16])
        self.assertEqual(decoded['ref_timestamp'], 123)
        self.assertEqual(decoded['loc_timestamp'], 456)
        self.assertEqual(policy.predict.call_args.kwargs['prompt'], 'stack the bowls')
        self.assertEqual(policy.predict.call_args.kwargs['state'], list(range(14)))
        self.assertIsNone(sdk.DM05Policy.from_checkpoint.call_args.kwargs['robot_type'])


if __name__ == '__main__':
    unittest.main()
