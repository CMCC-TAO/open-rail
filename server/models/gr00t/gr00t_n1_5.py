import os
import time
import numpy as np
import torch
import gr00t
from gr00t.model.policy import Gr00tPolicy
from gr00t.data.schema import EmbodimentTag
from gr00t.experiment.data_config import DATA_CONFIG_MAP

class ModelVLA:
    """GR00T N1.5 Vision-Language-Action Model
    
    This class implements the GR00T N1.5 policy for robotic manipulation tasks,
    providing inference capabilities for vision-language-action models.
    """
    
    def __init__(self, config):
        """Initialize the GR00T N1.5 VLA model with configuration
        
        Args:
            config: Dictionary containing model configuration parameters
        """
        self.cfg = config
        model_path = self.cfg['model_path']
        # model_path = '/home/gaohan/Code/VLA/models/GR00TN1.5/pickbottle_184_1000_20250630_161111_n4_b64_s60000/checkpoint-60000'
        # embodiment_tag = EmbodimentTag.NEW_EMBODIMENT
        embodiment_tag = 'a2d'
        device = "cuda" if torch.cuda.is_available() else "cpu"
        data_config = DATA_CONFIG_MAP["a2d_arms_only"]
        modality_config = data_config.modality_config()
        modality_transform = data_config.transform()

        self.policy = Gr00tPolicy(
            model_path=model_path,
            embodiment_tag=embodiment_tag,
            modality_config=modality_config,
            modality_transform=modality_transform,
            device=device,
            denoising_steps=4,
        )
        self.policy.model.action_horizon=64
        print(self.policy.model)

        modality_config = self.policy.modality_config
        print(modality_config.keys())
        for key, value in modality_config.items():
            if isinstance(value, np.ndarray):
                print(key, value.shape)
            else:
                print(key, value)

    def infer(self, sequence):
        """Perform inference on input sequence data
        
        Args:
            sequence: List containing observation data and metadata
            
        Returns:
            dict: Inference result containing predicted actions and timestamps
        """
        data = sequence[0]
        obs = data['obs'].copy()
        obs['state'] = obs['state'][None]
        inp_obs = {
            # "video.cam_right_high": obs['cam.head'][None],
            "video.cam_top_head": obs['cam.head'][None],
            "video.cam_left_wrist": obs['cam.hand_left'][None],
            "video.cam_right_wrist": obs['cam.hand_right'][None],
            # "depth.cam_top":obs['cam.depth.head'][None],
            "state.left_arm": obs['state'][:, 0:7],
            "state.right_arm": obs['state'][:, 7:14],
            "state.left_hand": obs['state'][:, 14:15],
            "state.right_hand": obs['state'][:, 15:16],
            # "state": np.random.rand(1, 20),
            "annotation.human.task_description": obs['language'],
        }
        time1 = time.time()
        ext_result = {}
        predicted_action = self.policy.get_action(inp_obs)
        if isinstance(predicted_action, dict) and 'prob_progress' in predicted_action:
            ext_result['prob_progress'] = predicted_action['prob_progress']
            del predicted_action['prob_progress']
        predicted_action = np.concatenate([
            v.reshape(-1, 1) if v.ndim == 1 else v 
            for v in predicted_action.values()
        ], axis=1)
        print(time.time() - time1, 'action shape:', predicted_action.shape)
        return {"type": "vla_action", "pred_action": predicted_action, "ref_timestamp": data["ref_timestamp"], 'loc_timestamp': data['loc_timestamp'], 'ext': ext_result}

if __name__ == "__main__":
    # 其它vla模型参照下面的代码，测试通过即可
    model = ModelVLA()
    obs = {
        'cam.head': np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),
        'cam.hand_left': np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),
        'cam.hand_right': np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),
        'cam.depth.head': np.random.randint(0, 2**16, (480, 640), dtype=np.uint16),
        'state': np.random.rand(20,),
        'language': ['pick bottle into the box'],
    }
    return_key = ['type', 'pred_action', 'ref_timestamp']
    while True:
        result = model.infer([{'obs': obs, 'ref_timestamp': []}])
        # check result
        for key in return_key:
            if key not in result:
                raise ValueError(f'result key错误，未找到{key}')
        if result[return_key[0]] != 'vla_action':
            raise ValueError(f"result.{return_key[0]}错误，应为vla_action，实际为{result[return_key[0]]}")
        if not isinstance(result[return_key[1]], np.ndarray):
            raise ValueError(f"result.{return_key[1]}类型错误，应为ndarray，实际为{type(result[return_key[1]])}")
        if not isinstance(result[return_key[2]], list):
            raise ValueError(f"result.{return_key[0]}类型错误，应为list，实际为{type(result[return_key[2]])}")
