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
        # FIX: The state/action sub-component indices for unitree_g1
        # embodiment were originally based on the raw 41-DOF array
        # (e.g. left_arm: [15:22]), but the model internally uses
        # contiguous 0-based indices (concatenated left_arm at [0:7]).
        # Fix to 0-based to match model output dimension
        # (max_action_dim=32) and avoid out-of-bounds.
        #
        # Key point: decode_action() in
        # processing_tao_flow_matching_model.py creates new instances
        # via EMBODIMENTS.get(embodiment_tag)(), so the registry must
        # also be fixed. Otherwise new instances would still use the
        # old 41D indices.
        #
        # Important: Only correct index values; keep original
        # sub_component names (e.g. left_eef/right_eef) unchanged
        # because transformations and normalization parameters are
        # indexed by original name. Renaming would cause KeyError
        # or IndexError.
        # ============================================================
        if embodiment_tag == 'unitree_g1':
            from tao.registry import EMBODIMENTS

            # Determine whether fix is needed: only when 41-DOF indices detected (left_arm.start == 15)
            _needs_fix = False
            state_subs = {}
            if hasattr(self.policy, 'embodiment') and hasattr(self.policy.embodiment, 'indices'):
                indices = self.policy.embodiment.indices
                state_subs = indices.get('state', {}).get('sub_components', {})
                if state_subs.get('left_arm', {}).get('start') == 15:
                    _needs_fix = True

            if _needs_fix:
                # Read names and dimensions from existing sub_components, only modify index values
                # Default 0-based layout: arm(7) + arm(7) + eef/hand(6) + eef/hand(6) = 26
                sub_keys = list(state_subs.keys())  # Preserve original names
                offsets = [0, 7, 14, 20, 26]  # 0-based 连续索引边界
                new_state_subs = {}
                new_action_subs = {}
                for i, key in enumerate(sub_keys):
                    new_state_subs[key] = {"start": offsets[i], "end": offsets[i+1]}
                    new_action_subs[key] = {"start": offsets[i], "end": offsets[i+1]}

                print(f'[TAO] Fixing unitree_g1 41-DOF indices to 0-based. '
                      f'sub_components: {sub_keys}', flush=True)

                # Fix 1: Fix the existing self.policy.embodiment instance
                if hasattr(self.policy, 'embodiment') and hasattr(self.policy.embodiment, 'indices'):
                    self.policy.embodiment.indices['state']['sub_components'] = new_state_subs
                    self.policy.embodiment.indices['action']['sub_components'] = new_action_subs

                # Fix 2: Fix the registry so that new instances created in decode_action also use corrected indices
                if 'unitree_g1' in EMBODIMENTS._mapping:
                    original_cls = EMBODIMENTS._mapping['unitree_g1']
                    _fixed_state = dict(new_state_subs)
                    _fixed_action = dict(new_action_subs)
                    def _make_fixed_unitree_g1(original_cls_=original_cls,
                                               _fs=_fixed_state, _fa=_fixed_action):
                        inst = original_cls_()
                        inst.indices['state']['sub_components'] = dict(_fs)
                        inst.indices['action']['sub_components'] = dict(_fa)
                        return inst
                    EMBODIMENTS._mapping['unitree_g1'] = _make_fixed_unitree_g1
            else:
                print(f'[TAO] unitree_g1 indices already 0-based, skipping fix. '
                      f'sub_components: {list(state_subs.keys()) if state_subs else "N/A"}',
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
            'state': obs['state'][None][None], # (B,T,D) where D=26
            'language':[obs['language']]
        }
        # State is passed directly as 26-dimensional because embodiment indices
        # have been corrected to contiguous 0-based
        # (no need to pad to 41 dimensions; see index fix logic in __init__)
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
