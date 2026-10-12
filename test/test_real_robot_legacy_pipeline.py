import unittest

import numpy as np
from ml_collections import ConfigDict

from client.core.inter_chunk_fuser import InterChunkFuser
from client.core.intra_chunk_smoother import IntraChunkSmoother
from client.core.realtime_data_manager import RealtimeDataManager


class RealRobotLegacyPipelineTest(unittest.TestCase):
    def test_simulation_sampling_options_do_not_change_real_trajectory(self):
        config = ConfigDict({
            'intra_chunk_mode': 'fitting',
            'fitting_deg': 4,
            'output_sample_ratio': 1.0,
            'preserve_input_timestamps': True,
        })
        timestamps = np.linspace(0, 7 / 30, 8)
        actions = np.tile(np.linspace(0, 1, 8), (2, 1))
        layout = {'arm': {'start': 0, 'end': 2, 'policy': 'gradual'}}

        outputs = []
        for simulation_mode in (False, True):
            smoother = IntraChunkSmoother(config, simulation_mode=simulation_mode)
            smoother.set_action_layout(layout)
            outputs.append(smoother.process(
                timestamps, actions, time_step=3.75,
                joint_indices=[0, 1], step_indices=[],
            ))

        self.assertEqual(outputs[0][0].shape[1], 63)
        self.assertAlmostEqual(np.diff(outputs[0][3])[0], 0.00375)
        self.assertEqual(outputs[1][0].shape[1], 8)

    def test_simulation_transition_limit_does_not_change_real_fusion(self):
        config = ConfigDict({'inter_chunk_mode': 'sync', 'max_transition_steps': 5})
        actions = np.tile(np.arange(8, dtype=float), (2, 1))
        zeros = np.zeros_like(actions)
        timestamps = np.arange(8, dtype=float) / 30

        real = InterChunkFuser(config).process(actions, zeros, zeros, timestamps, 0)
        simulation = InterChunkFuser(config, simulation_mode=True).process(
            actions, zeros, zeros, timestamps, 0,
        )

        self.assertTrue(np.any(real[1] != 0))
        self.assertTrue(np.all(simulation[1] == 0))

    def test_simulation_warmup_override_does_not_change_real_observation_buffer(self):
        config = ConfigDict({
            'max_len': 10,
            'observe_fps_window_size': 2,
            'skip_initial_frames': 0,
        })
        real = RealtimeDataManager(config)
        simulation = RealtimeDataManager(config, simulation_mode=True)

        real.add_observe_data({'step': 1})
        simulation.add_observe_data({'step': 1})

        self.assertIsNone(real.pop_observe_data())
        self.assertEqual(simulation.pop_observe_data(), {'step': 1})


if __name__ == '__main__':
    unittest.main()
