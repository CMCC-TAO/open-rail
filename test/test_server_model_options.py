from contextlib import redirect_stderr
import io
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from conf.models_conf import ModelType
from conf.server_conf import get_vla_server_config
from client.simulation.model_bridge import SimulationModelBridge
from run_server import override_config_with_args, parse_args


def configure(*arguments, config=None):
    with patch.object(sys, 'argv', ['run_server.py', *arguments]):
        return override_config_with_args(
            config if config is not None else get_vla_server_config(), parse_args()
        )


class ServerModelOptionsTests(unittest.TestCase):
    def test_no_tag_preserves_configured_defaults(self):
        config = configure()
        self.assertEqual(config.models.gr00t.embodiment_tag, 'a2d')
        self.assertEqual(config.models.gr00t.data_config_key, 'a2d_arms_only')

    def test_tao_tag_does_not_change_gr00t_settings(self):
        config = configure('--model_type', 'tao', '--embodiment_tag', 'robotwin_aloha')
        self.assertEqual(config.models.type, ModelType.TAO)
        self.assertEqual(config.models.tao.embodiment_tag, 'aloha_robotwin')
        self.assertEqual(config.models.gr00t.data_config_key, 'a2d_arms_only')

    def test_gr00t_tag_selects_data_configuration(self):
        for tag, sdk_tag, key in (
            ('a2d', 'a2d', 'a2d_arms_only'),
            ('robocasa_pandas_omron', 'robocasa_panda_omron', 'panda_omron'),
        ):
            with self.subTest(tag=tag):
                config = configure('--model_type', 'gr00t_n1_5', '--embodiment_tag', tag)
                self.assertEqual(config.models.gr00t.embodiment_tag, sdk_tag)
                self.assertEqual(config.models.gr00t.data_config_key, key)

    def test_gr00t_aliases_can_be_configured(self):
        config = get_vla_server_config()
        config.models.gr00t.data_config_by_embodiment = {'a2d': 'custom_dataset'}
        configure('--embodiment_tag', 'a2d', config=config)
        self.assertEqual(config.models.gr00t.data_config_key, 'custom_dataset')

    def test_removed_options_are_rejected(self):
        for option, values in (
            ('--data_config_key', ['panda_omron']),
            ('--action_keys', ['left_arm', 'right_arm']),
            ('--video_keys', ['head', 'left', 'right']),
        ):
            with self.subTest(option=option), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    configure(option, *values)
                self.assertEqual(error.exception.code, 2)

    def test_other_models_start_without_removed_attributes(self):
        config = configure('--model_type', 'mock', '--server_port', '6001')
        self.assertEqual(config.models.type, ModelType.MOCK)
        self.assertEqual(config.zmq.port, '6001')
        with self.assertRaisesRegex(ValueError, 'has no simulation adaptation'):
            configure('--model_type', 'mock', '--embodiment_tag', 'robotwin_aloha')

    def test_tao_derives_camera_roles_and_action_order(self):
        seen = {}

        def get_action(observation):
            seen.update(observation)
            return {'action': {'right_hand': 4, 'right_arm': 3, 'left_hand': 2, 'left_arm': 1}}

        policy = SimpleNamespace(
            get_action=get_action,
            embodiment=SimpleNamespace(
                observations={'video': dict.fromkeys(('cam_top_head', 'cam_left_wrist', 'cam_right_wrist'))},
                indices={'action': {'sub_components': {
                    'right_arm': {'start': 7}, 'left_hand': {'start': 6},
                    'right_hand': {'start': 13}, 'left_arm': {'start': 0},
                }}},
            ),
        )
        model = SimpleNamespace(cfg={}, policy=policy)
        SimulationModelBridge(model, 'tao')
        result = model.policy.get_action({'video': {
            'base_image': 'head', 'left_wrist_image': 'left', 'right_wrist_image': 'right',
        }})
        self.assertEqual(seen['video'], {
            'cam_top_head': 'head', 'cam_left_wrist': 'left', 'cam_right_wrist': 'right',
        })
        self.assertEqual(list(result['action']), ['left_arm', 'left_hand', 'right_arm', 'right_hand'])


if __name__ == '__main__':
    unittest.main()
