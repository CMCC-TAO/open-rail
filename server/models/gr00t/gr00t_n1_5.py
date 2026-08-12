import os
import time
import json
import numpy as np
import torch
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
        # model_path = '/path/to/model'
        meta_data_path = os.path.join(model_path, 'experiment_cfg/metadata.json') 
        with open(meta_data_path, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
        data_config_key = list(meta_data.keys())[0]
        meta_data_state = meta_data[data_config_key]['modalities']['state']
    
        # configure state of observations
        self.delta_indices = {}
        start_index = 0
        for key in meta_data_state.keys():
            modality_shape = meta_data_state[key]['shape'][0]
            end_index = int(start_index + modality_shape)
            self.delta_indices[f'state.{key}'] = {}
            self.delta_indices[f'state.{key}']['start_index'] = start_index
            self.delta_indices[f'state.{key}']['end_index'] = end_index
            start_index += modality_shape

        # get data config and transforms
        device = "cuda" if torch.cuda.is_available() else "cpu"
        data_config = DATA_CONFIG_MAP[self.cfg['data_config_key']]
        self.video_keys = list(data_config.video_keys)
        self.language_keys = list(data_config.language_keys)
        self.action_keys = list(data_config.action_keys)
        modality_config = data_config.modality_config()
        modality_transform = data_config.transform()

        self.policy = Gr00tPolicy(
            model_path=model_path,
            embodiment_tag=self.cfg['embodiment_tag'],
            modality_config=modality_config,
            modality_transform=modality_transform,
            device=device,
            denoising_steps=4,
        )
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
        camera_values = [obs['cam.head'], obs['cam.hand_left'], obs['cam.hand_right']]
        if len(self.video_keys) != len(camera_values):
            raise ValueError(f'Expected {len(self.video_keys)} camera inputs, got {len(camera_values)}')
        inp_obs = {
            key: value[None]
            for key, value in zip(self.video_keys, camera_values)
        }
        if len(self.language_keys) != 1:
            raise ValueError(f'Expected one language key, got {self.language_keys}')
        inp_obs[self.language_keys[0]] = obs['language']
        for key in self.delta_indices.keys():
            start_index = self.delta_indices[key]['start_index']
            end_index = self.delta_indices[key]['end_index']
            inp_obs[key] = obs['state'][:, start_index:end_index]

        time1 = time.time()
        ext_result = {}
        predicted_action = self.policy.get_action(inp_obs)
        print(f"predicted_action keys: {predicted_action.keys()}, shapes: {{k: v.shape for k, v in predicted_action.items() if isinstance(v, np.ndarray)}}")
        # predicted_action['prob_progress'] = np.random.rand(64,)
        if isinstance(predicted_action, dict) and 'prob_progress' in predicted_action:
            ext_result['prob_progress'] = predicted_action['prob_progress']
            del predicted_action['prob_progress']
        missing = [key for key in self.action_keys if key not in predicted_action]
        if missing:
            raise KeyError(f'GR00T action output is missing configured keys: {missing}')
        predicted_action = np.concatenate([
            predicted_action[key].reshape(-1, 1)
            if predicted_action[key].ndim == 1 else predicted_action[key]
            for key in self.action_keys
        ], axis=1)
        print(time.time() - time1, 'action shape:', predicted_action.shape)
        return {"type": "vla_action", "pred_action": predicted_action, "ref_timestamp": data["ref_timestamp"], 'loc_timestamp': data['loc_timestamp'], 'ext': ext_result}

if __name__ == "__main__":
    model = ModelVLA({'model_path': ''})
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
        result = model.infer([{'obs': obs, 'ref_timestamp': [], 'loc_timestamp': []}])
        # check result
        for key in return_key:
            if key not in result:
                raise ValueError(f'result key error, not found {key}')
        if result[return_key[0]] != 'vla_action':
            raise ValueError(f"result.{return_key[0]} error, should be vla_action, but got {result[return_key[0]]}")
        if not isinstance(result[return_key[1]], np.ndarray):
            raise ValueError(f"result.{return_key[1]} error, should be ndarray, but got {type(result[return_key[1]])}")
        if not isinstance(result[return_key[2]], list):
            raise ValueError(f"result.{return_key[2]} error, should be list, but got {type(result[return_key[2]])}")
