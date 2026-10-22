from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from client.simulation.evaluation import build_parser, configure_pipeline
from client.simulation.io_adapter import (
    SimulationIOAdapter, fields_from_layout, load_profile,
)
from conf.client_conf import get_client_config
from conf.robots_conf import get_robocasa_pandas_config, get_robotwin_aloha_config
from web_client import simulation


CONFIG_PATH = Path(__file__).resolve().parents[1] / 'conf' / 'simulation.yml'


class SimulationConfigTests(unittest.TestCase):
    def test_benchmark_action_conversion_is_preserved(self):
        for config, expected in (
            (get_robocasa_pandas_config(), [5, 6, 7, 8, 9, 10, 11, 0, 1, 2, 3, 4]),
            (get_robotwin_aloha_config(), list(range(14))),
        ):
            with self.subTest(profile=config.io_profile):
                robot = SimpleNamespace(
                    config=config,
                    describe_io=lambda: {'action': fields_from_layout(config.action_layout)},
                )
                adapter = SimulationIOAdapter(robot, SimpleNamespace())
                result = adapter.decode({'data': {
                    'type': 'vla_action', 'pred_action': [list(range(len(expected)))],
                }}, {})
                np.testing.assert_array_equal(result['data']['pred_action'], [expected])

    def test_standalone_profile_remains_supported(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'layout.yml'
            path.write_text('action:\n  - {name: arm, width: 7}\n')
            self.assertEqual(load_profile(path), {'action': [{'name': 'arm', 'width': 7}]})

    def test_no_override_preserves_empty_profile(self):
        self.assertEqual(load_profile(''), {})

    def test_combined_config_requires_named_selection(self):
        with self.assertRaisesRegex(ValueError, 'Select a simulation IO profile'):
            load_profile(CONFIG_PATH)
        with self.assertRaisesRegex(ValueError, 'Unknown simulation IO profile'):
            load_profile(f'{CONFIG_PATH}#missing')
        with self.assertRaisesRegex(ValueError, 'Expected a YAML path'):
            load_profile(f'{CONFIG_PATH}#')

    def test_invalid_named_profiles_are_rejected(self):
        for content, error in (
            ('io_profiles: []', 'Unknown simulation IO profile'),
            ('io_profiles: {custom: []}', 'must be a YAML mapping'),
            ('io_profiles: {custom: {action: [{name: arm, width: 0}]}}', 'Invalid width'),
        ):
            with self.subTest(content=content), TemporaryDirectory() as folder:
                path = Path(folder) / 'invalid.yml'
                path.write_text(content)
                with self.assertRaisesRegex(ValueError, error):
                    load_profile(f'{path}#custom')

    def test_cli_preserves_selector_when_resolving_relative_path(self):
        path = 'conf/simulation.yml#robotwin_aloha'
        args = build_parser().parse_args(['--env_name', 'example', '--io_profile', path])
        config = get_client_config()
        configure_pipeline(config, args)
        expected = f'{Path("conf/simulation.yml").resolve()}#robotwin_aloha'
        self.assertEqual(config.vla_zmq.io_profile, expected)
        self.assertEqual(len(load_profile(config.vla_zmq.io_profile)['action']), 4)

    def test_web_defaults_ignore_io_profiles_and_keep_override_order(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'simulation.yml'
            path.write_text(
                'defaults: {record_fps: 17, video_fps: 19}\n'
                'platforms:\n  robocasa: {video_fps: 23}\n'
                'io_profiles: {custom: {history_frames: 2}}\n'
            )
            with patch.object(simulation, 'DEFAULTS_PATH', path):
                options = simulation.options('robocasa')
            self.assertEqual(options['record_fps'], 17)
            self.assertEqual(options['video_fps'], 23)
            self.assertNotIn('io_profiles', options)

    def test_web_worker_command_preserves_profile_selector(self):
        profile = f'{CONFIG_PATH}#robocasa'
        config = simulation.EvaluationConfig(env_name='PickPlaceCounterToCabinet', io_profile=profile)
        command = simulation.manager.command(config, 'config-test')
        self.assertEqual(command[command.index('--io_profile') + 1], profile)


if __name__ == '__main__':
    unittest.main()
