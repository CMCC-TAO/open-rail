import unittest
import sys
import types
from pathlib import Path


class _ConfigDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key, value):
        self[key] = value


if "ml_collections" not in sys.modules:
    module = types.ModuleType("ml_collections")
    module.ConfigDict = _ConfigDict
    sys.modules["ml_collections"] = module

from conf.client_conf import get_inter_chunk_config


class InterChunkConfigTest(unittest.TestCase):
    def test_inter_chunk_config_groups_mode_specific_parameters(self):
        config = get_inter_chunk_config()

        self.assertEqual(config.inter_chunk_mode, "min_jerk")
        self.assertIn("search_action", config)
        self.assertIn("smooth_velocity", config)
        self.assertIn("poly", config)
        self.assertIn("min_jerk", config)
        self.assertIn("bspline", config)
        self.assertIn("common", config)

        self.assertEqual(config.search_action.search_length, 100)
        self.assertEqual(config.poly.poly_length, 30)
        self.assertEqual(config.smooth_velocity.max_vel, 2.0)
        self.assertEqual(config.smooth_velocity.max_acc, 5.0)
        self.assertEqual(config.smooth_velocity.kp, 5.0)
        self.assertEqual(config.smooth_velocity.kd, 2.0)
        self.assertEqual(config.min_jerk.blend_threshold, 0.7)
        self.assertEqual(config.min_jerk.adaptive_factor, -1)
        self.assertNotIn("transition_length", config.min_jerk)
        self.assertEqual(config.bspline.num_control_points, 6)
        self.assertEqual(config.bspline.transition_length, 32)
        self.assertFalse(config.common.smooth_action)
        self.assertEqual(config.common.smooth_length, 150)
        self.assertEqual(config.common.smooth_base, 0.0)
        self.assertEqual(config.common.smooth_ratio, 0.75)

    def test_config_ui_has_inter_chunk_mode_driven_group_renderer(self):
        config_js = Path("web_client/static/modules/config.js").read_text(encoding="utf-8")

        self.assertIn("_buildInterChunkGroup", config_js)
        self.assertIn("data-inter-chunk-mode", config_js)
        self.assertIn("data-inter-chunk-common", config_js)

    def test_inter_chunk_fuser_reads_mode_specific_config_values(self):
        fuser_py = Path("client/core/inter_chunk_fuser.py").read_text(encoding="utf-8")

        for key in (
            "search_length",
            "poly_length",
            "max_vel",
            "max_acc",
            "kp",
            "kd",
            "blend_threshold",
            "adaptive_factor",
            "num_control_points",
        ):
            self.assertIn(f"self._cfg_value(mode_cfg, '{key}'", fuser_py)

        for key in ("smooth_action", "smooth_length", "smooth_base", "smooth_ratio"):
            self.assertIn(f"self._cfg_value(common_cfg, '{key}'", fuser_py)

    def test_min_jerk_auto_and_manual_adaptive_factor_paths_are_explicit(self):
        fuser_py = Path("client/core/inter_chunk_fuser.py").read_text(encoding="utf-8")

        self.assertIn("adaptive_factor = -1", fuser_py)
        self.assertIn("if adaptive_factor < 0:", fuser_py)
        self.assertIn("adaptive_factor = min(1.0, 0.25 + pos_diff * 1.0 + vel_diff * 0.75 + acc_diff * 0.15)", fuser_py)
        self.assertIn("adaptive_factor = min(1.0, max(0.0, float(adaptive_factor)))", fuser_py)

    def test_poly_and_bspline_lengths_use_configured_values(self):
        fuser_py = Path("client/core/inter_chunk_fuser.py").read_text(encoding="utf-8")

        self.assertIn("transition_length = min(int(poly_length), next_action_chunk.shape[1] - target_chunk_index)", fuser_py)
        self.assertIn("transition_length = min(int(transition_length), next_action_chunk.shape[1] - target_chunk_index)", fuser_py)
        self.assertNotIn("transition_length = min(next_action_chunk.shape[1] // 2, next_action_chunk.shape[1] - target_chunk_index)", fuser_py)
        self.assertNotIn("transition_length = min(next_action_chunk.shape[1] // 3, next_action_chunk.shape[1] - target_chunk_index)", fuser_py)


if __name__ == "__main__":
    unittest.main()
