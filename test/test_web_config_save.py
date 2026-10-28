import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from conf.client_conf import get_client_config
from web_client import server


class WebConfigSaveTests(unittest.IsolatedAsyncioTestCase):
    async def test_save_as_writes_current_config_instead_of_empty_mapping(self):
        config = get_client_config()
        config.controller.wait_time = 123

        original_config = server.client_state.config
        original_conf_file = server.client_state.conf_file
        server.client_state.config = config
        try:
            with tempfile.TemporaryDirectory(dir=server.ROOT) as temp_dir:
                save_path = Path(temp_dir) / 'saved_config.yaml'
                with patch.object(server, '_config_path', return_value=save_path):
                    result = await server.save_config_file(
                        server.ConfigFileRequest(path='saved_config.yaml')
                    )

                saved_config = yaml.safe_load(save_path.read_text(encoding='utf-8'))
                self.assertEqual(result['status'], 'ok')
                self.assertEqual(saved_config['controller']['wait_time'], 123)
                self.assertIn('robots', saved_config)
                self.assertIn('teleop', saved_config)
        finally:
            server.client_state.config = original_config
            server.client_state.conf_file = original_conf_file

    async def test_save_as_refuses_to_overwrite_with_empty_config(self):
        original_config = server.client_state.config
        server.client_state.config = {}
        try:
            with tempfile.TemporaryDirectory(dir=server.ROOT) as temp_dir:
                save_path = Path(temp_dir) / 'existing_config.yaml'
                save_path.write_text('keep: this\n', encoding='utf-8')
                with patch.object(server, '_config_path', return_value=save_path):
                    with self.assertRaises(server.HTTPException):
                        await server.save_config_file(
                            server.ConfigFileRequest(path='existing_config.yaml')
                        )

                self.assertEqual(save_path.read_text(encoding='utf-8'), 'keep: this\n')
        finally:
            server.client_state.config = original_config

    def test_config_to_dict_accepts_already_converted_nested_config(self):
        config = get_client_config()
        converted = server._config_to_dict(config)

        self.assertEqual(server._config_to_dict(converted), converted)
        self.assertIn('controller', converted)


if __name__ == '__main__':
    unittest.main()
