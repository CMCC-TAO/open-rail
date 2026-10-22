import time
import numpy as np
import torch
from gr00t.policy.gr00t_policy import Gr00tPolicy
from gr00t.data.embodiment_tags import EmbodimentTag

class ModelVLA:
    """GR00T N1.7 Vision-Language-Action Model

    This class implements the GR00T N1.7 policy for robotic manipulation tasks,
    providing inference capabilities for vision-language-action models.

    N1.7 differences from gr00t_n1_6.py:
      - EmbodimentTag.A2D no longer exists; finetuned A2D checkpoints are
        registered under EmbodimentTag.NEW_EMBODIMENT ('new_embodiment').
      - The modality keys follow the A2D finetune config
        (examples/a2d/agibot_a2d_config.py): video {top_head, hand_left,
        hand_right}, state {left_arm, right_arm, left_gripper, right_gripper}.
      - denoising_steps is no longer a Gr00tPolicy constructor argument; the
        action head reads num_inference_timesteps at sampling time.
    """

    def __init__(self, config):
        """Initialize the GR00T N1.7 VLA model with configuration

        Args:
            config: Dictionary containing model configuration parameters:
                model_path (str): Path to the model checkpoint (required)
                embodiment_tag (str): Embodiment tag name or value
                    (default: 'new_embodiment')
                denoising_steps (int): Number of denoising steps at sampling
                    time (default: 4)
        """
        self.cfg = config
        model_path = self.cfg['model_path']
        # model_path = '/path/to/model'
        embodiment_tag = self.cfg.get('embodiment_tag', 'new_embodiment')
        denoising_steps = self.cfg.get('denoising_steps', 4)

        self.policy = Gr00tPolicy(
            model_path=model_path,
            embodiment_tag=EmbodimentTag.resolve(embodiment_tag),
            device="cuda" if torch.cuda.is_available() else "cpu",
        )
        # N1.7 reads the number of denoising steps from the action head at
        # sampling time (no longer a Gr00tPolicy constructor argument).
        self.policy.model.action_head.num_inference_timesteps = denoising_steps
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
                "top_head": obs['cam.head'][None, None],
                "hand_left": obs['cam.hand_left'][None, None],
                "hand_right": obs['cam.hand_right'][None, None],
            },
            # (B, T, D)
            "state": {
                "left_arm": obs['state'][..., 0:7],
                "right_arm": obs['state'][..., 7:14],
                "left_gripper": obs['state'][..., 14:15],
                "right_gripper": obs['state'][..., 15:16],
            },
            # (B, 1): each batch item is a single-element list holding the
            # language string. obs['language'] from the client is already a
            # list ([str]), so wrap it once to get [['instruction']].
            "language": {
                "annotation.human.task_description": [obs['language']],
            },
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
