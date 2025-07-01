import os
import time
import numpy as np
import torch
import gr00t
from gr00t.model.policy import Gr00tPolicy
from gr00t.data.schema import EmbodimentTag
from gr00t.experiment.data_config import DATA_CONFIG_MAP

class ModelVLA:
    def __init__(self):
        # MODEL_PATH = "/home/robot/Downloads/checkpoint-60000"
        MODEL_PATH = "/home/robot/Downloads/pickbottle_499_chunk64_20250507_192258_b24/checkpoint-60000"
        # MODEL_PATH = "/home/robot/Downloads/pickbottle_10xx_chunk_size_64_20250503_143309_b6/checkpoint-60000"
        # EMBODIMENT_TAG = "gr1"
        EMBODIMENT_TAG = EmbodimentTag.NEW_EMBODIMENT
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"

        device = "cuda" if torch.cuda.is_available() else "cpu"
        data_config = DATA_CONFIG_MAP["a2d_arms_only"]
        modality_config = data_config.modality_config()
        modality_transform = data_config.transform()

        self.policy = Gr00tPolicy(
            model_path=MODEL_PATH,
            embodiment_tag=EMBODIMENT_TAG,
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

    def infer(self, data):
        print(f'data keys: {data.keys()}')
        obs = data['obs'].copy()
        print(f'obs keys: {obs.keys()}')
        obs['state'] = obs['state'][None]
        image_shape = obs['cam.head'].shape
        print(f'image shape: {image_shape}')
        state_shape = obs['state'].shape
        print(f'state shape: {state_shape}')
        inp_obs = {
            "video.cam_right_high": obs['cam.head'][None],
            "video.cam_left_wrist": obs['cam.hand_left'][None],
            "video.cam_right_wrist": obs['cam.hand_right'][None],
            "state.left_arm": obs['state'][:, 0:7],
            "state.right_arm": obs['state'][:, 7:14],
            "state.left_hand": obs['state'][:, 14:15],
            "state.right_hand": obs['state'][:, 15:16],
            # "state": np.random.rand(1, 20),
            "annotation.human.action.task_description": obs['annotation.human.action.task_description'],
        }
        start_time = time.time()
        predicted_action = self.policy.get_action(inp_obs)
        end_time = time.time()
        print(f'infer time: {(end_time - start_time) * 1000: .02f} ms')
        predicted_action = np.concatenate([
            v.reshape(-1, 1) if v.ndim == 1 else v 
            for v in predicted_action.values()
        ], axis=1)
        print(f'predicted_action shape: {predicted_action.shape}')
        return {
            "type": "action",
            "pred_action": predicted_action,
            'obs_state': obs['state'],
            "ref_timestamp": data["ref_timestamp"],
            'loc_timestamp': data['loc_timestamp']
            }

    def test_policy(self, obs):
        obs = obs.copy()
        obs['state'] = obs['state'][None]
        obs['state.left_arm'] = obs['state'][:, 0:7]
        obs['state.right_arm'] = obs['state'][:, 7:14]
        obs['state.left_hand'] = obs['state'][:, 14:15]
        obs['state.right_hand'] = obs['state'][:, 15:16]
        # del obs['state']
        aaa = time.time()
        predicted_action = self.policy.get_action(obs)
        print(time.time() - aaa, obs.keys())
        for key, value in predicted_action.items():
            print(key, value.shape)
        predicted_action = np.concatenate([
            v.reshape(-1, 1) if v.ndim == 1 else v 
            for v in predicted_action.values()
        ], axis=1)
        print('predicted_action', predicted_action.shape)
        return {"type": "action", "action": predicted_action}


if __name__ == "__main__":
    import time

    obs = {
        "video.cam_right_high": np.random.randint(0, 256, (1, 480, 640, 3), dtype=np.uint8),
        "video.cam_left_wrist": np.random.randint(0, 256, (1, 480, 640, 3), dtype=np.uint8),
        "video.cam_right_wrist": np.random.randint(0, 256, (1, 480, 640, 3), dtype=np.uint8),
        # "state.left_arm": np.random.rand(1, 7),
        # "state.right_arm": np.random.rand(1, 7),
        # "state.left_hand": np.random.rand(1, 1),
        # "state.right_hand": np.random.rand(1, 1),
        "state": np.random.rand(20,),
        "annotation.human.action.task_description": ["do your thing!"],
    }
    model = ModelVLA()
    while True:
        result = model.test_policy(obs)
