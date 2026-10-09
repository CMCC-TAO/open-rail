import os
import time
import json
import numpy as np
import torch

from tao.serving.policy import PolicyTao



class ModelVLA:
    """TAO Vision-Language-Action Model
    
    This class implements the TAO policy for robotic manipulation tasks,
    providing inference capabilities for vision-language-action models.
    """
    
    def __init__(self, config):
        """Initialize the TAO VLA model with configuration
        
        Args:
            config: Dictionary containing model configuration parameters
        """
        self.cfg = config
        model_path = self.cfg['model_path']
        embodiment_tag = self.cfg['embodiment_tag']
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.policy = PolicyTao(
            model_path=model_path,
            device=device, 
            embodiment_tag=embodiment_tag
        )
        self._reported_action_order = False
        
    def infer(self, sequence, verbose:bool=False):
        """Perform inference on input sequence data
        
        Args:
            sequence: List containing observation data and metadata
            
        Returns:
            dict: Inference result containing predicted actions and timestamps
        """
        data = sequence[0]
        obs = data['obs'].copy()

        video_keys = list(self.cfg.get('video_keys', ['base_image', 'left_wrist_image', 'right_wrist_image']))
        if len(video_keys) != 3 or len(set(video_keys)) != 3:
            raise ValueError('video_keys must contain three distinct camera keys')
        head_key, left_wrist_key, right_wrist_key = video_keys
        inp_obs = {
            'video':{
                head_key: obs['cam.head'][None][None], # (B,T,H,W,C)
                left_wrist_key: obs['cam.hand_left'][None][None],
                right_wrist_key: obs['cam.hand_right'][None][None],
            },
            'state': obs['state'][None][None], # (B,T,D)
            'language':[obs['language']]
        }
        if verbose:
            for key in inp_obs['video'].keys():
                print(key, inp_obs['video'][key].shape)
            print('state', inp_obs['state'].shape)
            print('language', inp_obs['language'])
        time1 = time.time()
        ext_result = {}
        predicted_action = self.policy.get_action(inp_obs)
        if isinstance(predicted_action, dict) and 'progress' in predicted_action:
            ext_result['prob_progress'] = predicted_action['progress'][0, :, -1]
            del predicted_action['progress']
        action_dict = predicted_action['action']
        action_keys = list(self.cfg.get('action_keys', []))
        robocasa_keys = [
            'end_effector_position',
            'end_effector_rotation',
            'gripper_close',
            'base_motion',
            'control_mode',
        ]
        if not action_keys and all(key in action_dict for key in robocasa_keys):
            action_keys = robocasa_keys
        if not action_keys and all(f'action.{key}' in action_dict for key in robocasa_keys):
            action_keys = [f'action.{key}' for key in robocasa_keys]
        if action_keys:
            missing = [key for key in action_keys if key not in action_dict]
            if missing:
                raise KeyError(f'TAO action output is missing configured keys: {missing}')
            action_values = [action_dict[key] for key in action_keys]
        else:
            action_values = list(action_dict.values())
        if not self._reported_action_order:
            print(f'TAO action order: {action_keys or list(action_dict.keys())}')
            self._reported_action_order = True
        predicted_action = np.concatenate([value.squeeze(0) for value in action_values], axis=1)
        print(time.time() - time1, 'action shape:', predicted_action.shape)
        return {"type": "vla_action", "pred_action": predicted_action, "ref_timestamp": data["ref_timestamp"], 'loc_timestamp': data['loc_timestamp'], 'ext': ext_result}
