import os
import sys
sys.path.append('/home/gaohan/Code/VLA/zhaolei/zl/server/models/rdt/rdt_train_a2d')

import time
import yaml
import numpy as np
import torch
from PIL import Image as PImage

from scripts.agilex_model import create_model

class ModelVLA:
    def __init__(self, config):
        self.cfg = config
        model_path = self.cfg['model_path']
        with open(self.cfg['config_path'], "r") as f:
            rdt_config = yaml.safe_load(f)
        vision_encoder_name_or_path = self.cfg['vision_encoder_name_or_path']
        self.lang_embd_path = self.cfg['lang_embd_path']

        self.policy = create_model(
            args=rdt_config,
            dtype=torch.bfloat16,
            pretrained=model_path,
            pretrained_vision_encoder_name_or_path=vision_encoder_name_or_path,
            control_frequency=30,
        )
        print(self.policy)

    def infer(self, sequence):
        obs_curr = sequence[0]['obs'].copy()
        obs_prev = sequence[1]['obs'].copy()

        obs_curr['state'] = obs_curr['state'][None]
        obs_prev['state'] = obs_prev['state'][None]

        visual_obs = [
            obs_prev["cam.head"],
            obs_prev["cam.hand_right"],
            obs_prev["cam.hand_left"],

            obs_curr["cam.head"],
            obs_curr["cam.hand_right"],
            obs_curr["cam.hand_left"],
        ]
	
        print(obs_curr["state"].shape)
	
        state = np.concatenate(
            [
                obs_curr["state"][:, 0:7], obs_curr['state'][:, 14:15],
                obs_curr['state'][:, 7:14], obs_curr['state'][:, 15:16]
            ],
            axis=-1
        )


        time1 = time.time()

        _predicted_action = self.policy.step(
            proprio=torch.from_numpy(state),
            images=[
                PImage.fromarray(arr) if arr is not None else None
                for arr in visual_obs
            ],
            text_embeds=torch.load(self.lang_embd_path)["embeddings"]
        )[0].cpu().numpy()  # (chunk_size, 7+1+7+1)

        predicted_action = np.concatenate(
            [
                _predicted_action[:, :7], _predicted_action[:, 8:15],
                _predicted_action[:, 7:8], _predicted_action[:, 15:16]
            ],
            axis=1
        )  # (chunk_size, 7+7+1+1)

        print(time.time() - time1, 'action shape:', predicted_action.shape)
        return {"type": "vla_action", "pred_action": predicted_action, "ref_timestamp": sequence[0]["ref_timestamp"], 'loc_timestamp': sequence[0]['loc_timestamp']}

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
        result = model.infer([{'obs': obs, 'ref_timestamp': []}, {'obs': obs, 'ref_timestamp': []}])
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
