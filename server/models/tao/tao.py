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

        # ============================================================
        # FIX: unitree_g1 embodiment state/action indices are based on
        # the original 41-DOF array (e.g. left_arm: [15:22]), but the
        # model uses contiguous 0-based indices internally (concatenated
        # left_arm at [0:7]). Correct to 0-based to match model output
        # dimension (max_action_dim=32) and avoid out-of-bounds errors.
        #
        # NOTE: decode_action() creates new instances via
        # EMBODIMENTS.get(tag)(), so the registry must also be fixed;
        # otherwise new instances would still use the old indices.
        # ============================================================
        if embodiment_tag == 'unitree_g1':
            from tao.registry import EMBODIMENTS

            # Check if fix is needed: left_arm.start == 15 means still 41-DOF indices
            indices = getattr(self.policy, 'embodiment', None)
            if indices is not None:
                indices = getattr(indices, 'indices', None)
            needs_fix = (indices is not None
                         and indices.get('state', {})
                         .get('sub_components', {})
                         .get('left_arm', {}).get('start') == 15)

            if needs_fix:
                sub_keys = list(
                    indices['state']['sub_components'].keys())
                # 0-based contiguous indices: arm(7)+arm(7)+eef(6)+eef(6)=26
                offsets = [0, 7, 14, 20, 26]
                new_state_subs = {}
                new_action_subs = {}
                for i, key in enumerate(sub_keys):
                    new_state_subs[key] = {
                        "start": offsets[i], "end": offsets[i+1]}
                    new_action_subs[key] = {
                        "start": offsets[i], "end": offsets[i+1]}

                print(f'[TAO] Fix unitree_g1 indices: 41-DOF -> 0-based. '
                      f'sub_components: {sub_keys}', flush=True)

                # Fix 1: fix current instance
                indices['state']['sub_components'] = new_state_subs
                indices['action']['sub_components'] = new_action_subs

                # Fix 2: fix registry (decode_action creates new instances)
                if 'unitree_g1' in EMBODIMENTS._mapping:
                    original_cls = EMBODIMENTS._mapping['unitree_g1']
                    _fixed_s = dict(new_state_subs)
                    _fixed_a = dict(new_action_subs)

                    def _make_fixed(orig=original_cls,
                                    _fs=_fixed_s, _fa=_fixed_a):
                        inst = orig()
                        inst.indices['state']['sub_components'] = dict(_fs)
                        inst.indices['action']['sub_components'] = dict(_fa)
                        return inst

                    EMBODIMENTS._mapping['unitree_g1'] = _make_fixed
            else:
                print(f'[TAO] unitree_g1 indices already 0-based, skip.',
                      flush=True)
        
    def infer(self, sequence, verbose:bool=False):
        """Perform inference on input sequence data
        
        Args:
            sequence: List containing observation data and metadata
            
        Returns:
            dict: Inference result containing predicted actions and timestamps
        """
        data = sequence[0]
        obs = data['obs'].copy()

        inp_obs = {
            'video':{
                'base_image': obs['cam.head'][None][None], # (B,T,H,W,C)
                'left_wrist_image': obs['cam.hand_left'][None][None],
                'right_wrist_image': obs['cam.hand_right'][None][None],
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
        predicted_action = np.concatenate([v.squeeze(0) for v in predicted_action['action'].values()], axis=1)
        print(time.time() - time1, 'action shape:', predicted_action.shape)
        return {"type": "vla_action", "pred_action": predicted_action, "ref_timestamp": data["ref_timestamp"], 'loc_timestamp': data['loc_timestamp'], 'ext': ext_result}
