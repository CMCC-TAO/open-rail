import os
import time
import json
import numpy as np
import torch
from gr00t.policy.gr00t_policy import Gr00tPolicy
from gr00t.data.embodiment_tags import EmbodimentTag

class ModelVLA:
    """GR00T N1.6 Vision-Language-Action Model
    
    This class implements the GR00T N1.6 policy for robotic manipulation tasks,
    providing inference capabilities for vision-language-action models.
    """
    
    def __init__(self, config):
        """Initialize the GR00T N1.6 VLA model with configuration
        
        Args:
            config: Dictionary containing model configuration parameters
        """
        self.cfg = config
        model_path = self.cfg['model_path']
        # model_path = '/path/to/model'

        self.policy = Gr00tPolicy(
            model_path=model_path,
            embodiment_tag=EmbodimentTag.A2D,
            device="cuda" if torch.cuda.is_available() else "cpu",
        )
        # print(self.policy.model)

    def infer(self, sequence):
        """Perform inference on input sequence data
        
        Args:
            sequence: List containing observation data and metadata
            
        Returns:
            dict: Inference result containing predicted actions and timestamps
        """
        data = sequence[0]
        obs = data['obs'].copy()
        obs['state'] = obs['state'].astype(np.float32)[None, None]
        inp_obs = {
            # (B, T, H, W, 3)
            "video": {
                # "video.cam_right_high": obs['cam.head'][None, None],
                "cam_top_head": obs['cam.head'][None, None],
                "cam_left_wrist": obs['cam.hand_left'][None, None],
                "cam_right_wrist": obs['cam.hand_right'][None, None],
                # "depth.cam_top":obs['cam.depth.head'][None， None],
            },
            # (B, T, D)
            "state": {
                "left_arm": obs['state'][..., 0:7],
                "right_arm": obs['state'][..., 7:14],
                "left_hand": obs['state'][..., 14:15],
                "right_hand": obs['state'][..., 15:16],
                # "state": np.random.rand(1, 20),
            },
            # (B, 1)
            "language": {
                "annotation.human.task_description": [obs['language']],
            }
        }

        time1 = time.time()
        ext_result = {}
        predicted_action, info = self.policy.get_action(inp_obs)
        # info['prob_progress'] = np.random.rand(64,)
        if isinstance(info, dict) and 'prob_progress' in info:
            # print('prob_progress: ', info['prob_progress'])
            ext_result['prob_progress'] = info['prob_progress'][0]
        predicted_action = np.concatenate([v[0] for v in predicted_action.values()], axis=1)
        print(time.time() - time1, 'action shape:', predicted_action.shape)
        return {"type": "vla_action", "pred_action": predicted_action, "ref_timestamp": data["ref_timestamp"], 'loc_timestamp': data['loc_timestamp'], 'ext': ext_result}
