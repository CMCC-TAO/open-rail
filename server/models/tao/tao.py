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
        # FIX: unitree_g1 embodiment 的 state/action 子组件索引原本基于
        # 原始 41-DOF 数组 (如 left_arm: [15:22])，但模型内部使用连续
        # 0-based 索引 (拼接后 left_arm 在 [0:7])。修复为 0-based 以
        # 适配模型输出维度 (max_action_dim=32) 避免越界。
        #
        # 关键: decode_action() 在 processing_tao_flow_matching_model.py 中
        # 会通过 EMBODIMENTS.get(embodiment_tag)() 创建新实例，因此必须
        # 同时修复 registry，否则新实例仍使用旧的 41D 索引。
        # ============================================================
        if embodiment_tag == 'unitree_g1':
            from tao.registry import EMBODIMENTS

            # Fix 1: 修复已存在的 self.policy.embodiment 实例 (供 _to_vla_step_data 使用)
            if hasattr(self.policy, 'embodiment') and hasattr(self.policy.embodiment, 'indices'):
                indices = self.policy.embodiment.indices
                state_subs = indices.get('state', {}).get('sub_components', {})
                if state_subs.get('left_arm', {}).get('start') == 15:
                    state_subs['left_arm'] = {"start": 0, "end": 7}
                    state_subs['right_arm'] = {"start": 7, "end": 14}
                    state_subs['left_hand'] = {"start": 14, "end": 20}
                    state_subs['right_hand'] = {"start": 20, "end": 26}
                action_subs = indices.get('action', {}).get('sub_components', {})
                if action_subs.get('left_arm', {}).get('start') == 15:
                    action_subs['left_arm'] = {"start": 0, "end": 7}
                    action_subs['right_arm'] = {"start": 7, "end": 14}
                    action_subs['left_hand'] = {"start": 14, "end": 20}
                    action_subs['right_hand'] = {"start": 20, "end": 26}

            # Fix 2: 修复 registry，使 decode_action 中创建的新实例也使用修正后的索引
            if 'unitree_g1' in EMBODIMENTS._mapping:
                original_cls = EMBODIMENTS._mapping['unitree_g1']
                def _make_fixed_unitree_g1(original_cls_=original_cls):
                    inst = original_cls_()
                    # 新实例的 indices 是 fresh dict，直接替换子组件映射
                    inst.indices['state']['sub_components'] = {
                        'left_arm': {'start': 0, 'end': 7},
                        'right_arm': {'start': 7, 'end': 14},
                        'left_hand': {'start': 14, 'end': 20},
                        'right_hand': {'start': 20, 'end': 26},
                    }
                    inst.indices['action']['sub_components'] = {
                        'left_arm': {'start': 0, 'end': 7},
                        'right_arm': {'start': 7, 'end': 14},
                        'left_hand': {'start': 14, 'end': 20},
                        'right_hand': {'start': 20, 'end': 26},
                    }
                    return inst
                EMBODIMENTS._mapping['unitree_g1'] = _make_fixed_unitree_g1
        
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
        # state 直接使用 26 维传入，因为 embodiment 索引已修正为连续 0-based
        # (无需再填充到 41 维，详见 __init__ 中的索引修正逻辑)
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
