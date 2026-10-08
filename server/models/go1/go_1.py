import sys
import time
import numpy as np
import torch
import cv2
from PIL import Image


class ModelVLA:
    """GO-1 Vision-Language-Action Model"""

    def __init__(self, config):
        self.cfg = config
        self.model_path = self.cfg['model_path']
        self.data_stats_path = self.cfg.get('data_stats_path', None)

        # Ensure evaluate.deploy can be imported
        exp_path = self.cfg.get('exp_path')
        if exp_path and (exp_path not in sys.path):
            sys.path.append(exp_path)

        import evaluate.deploy as _ed
        print("evaluate.deploy 实际文件：", _ed.__file__)
        
        from evaluate.deploy import GO1Infer, multi_image_get_item
        self.multi_image_get_item = multi_image_get_item
        
        # Initialize GO1Infer (handles model loading and transform construction internally)
        self.policy = GO1Infer(
            model_path=self.model_path,
            data_stats_path=self.data_stats_path,
        )

        # If model requires normalization but stats not provided, raise error early
        if getattr(self.policy.config, "norm", False) and self.data_stats_path is None:
            raise ValueError(
                "GO1 model config.norm=True, but data_stats_path is None. "
                "Please provide dataset stats json via config['data_stats_path']."
            )

        print(self.policy.go1)

    def infer(self, sequence):
        data = sequence[0]
        obs = data['obs']

        
        def bgr_to_rgb(img):
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if img is not None else None

        top = bgr_to_rgb(obs.get('cam.head'))
        left = bgr_to_rgb(obs.get('cam.hand_left'))
        right = bgr_to_rgb(obs.get('cam.hand_right'))

        # Prepare instruction
        instruction = obs.get('language', "")
        if isinstance(instruction, list):
            instruction = instruction[0] if len(instruction) > 0 else ""
        # Prepare raw_target in the format expected by multi_image_get_item
        raw_target = {
            'cam_head_color': Image.fromarray(top) if top is not None else None,
            'cam_hand_left_color': Image.fromarray(left) if left is not None else None,
            'cam_hand_right_color': Image.fromarray(right) if right is not None else None,
            'final_prompt': f"What action should the robot take to {instruction}?",
            'ntp_target': "",  # Empty for inference
        }

        # Process images using multi_image_get_item (openloop_eval)
        inputs = self.multi_image_get_item(
            raw_target=raw_target,
            img_transform=self.policy.img_transform,
            text_tokenizer=self.policy.text_tokenizer,
            num_image_token=self.policy.num_image_token,
            dynamic_image_size=self.policy.dynamic_image_size,
            use_thumbnail=self.policy.config.use_thumbnail,
            min_dynamic_patch=self.policy.config.min_dynamic_patch,
            max_dynamic_patch=self.policy.config.max_dynamic_patch,
            image_size=self.policy.image_size,
        )

        state_1 = np.asarray(obs['state'], dtype=np.float32).reshape(-1)  # (D,)
        T = int(getattr(self.policy.config, "action_chunk_size", 1))       

        state = np.expand_dims(state_1, axis=0)    # (1, D)
        ctrl_freqs = np.array([30.0], dtype=np.float32)  # (1,)

        inputs['state'] = torch.from_numpy(state)          # (1, D)
        inputs['ctrl_freqs'] = torch.from_numpy(ctrl_freqs)  # (1,)

        # Call predict_action directly
        t0 = time.time()
        predicted_action = self.policy.predict_action(inputs) 
        dt = time.time() - t0
        
        print(f"infer time: {dt:.4f}s, action shape: {predicted_action.shape}")

        return {
            "type": "vla_action",
            "pred_action": predicted_action,
            "ref_timestamp": data.get("ref_timestamp", []),
            "loc_timestamp": data.get("loc_timestamp", []),
        }


if __name__ == "__main__":
    # Test the model adapter
    model = ModelVLA({
        # 'model_path': '/data/shared_checkpoints/GO-1/experiment/BOTTLE-496/checkpoint-23000',
        'model_path': '/path/to/model',
        'exp_path': '/path/to/exe',
        # 'data_stats_path': '/data/shared_checkpoints/GO-1/experiment/BOTTLE-496/checkpoint-23000/dataset_stats.json'
        'data_stats_path': '/path/to/dataset_stats.json'

    })

    obs = {
        'cam.head': np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),
        'cam.hand_left': np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),
        'cam.hand_right': np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),
        'cam.depth.head': np.random.randint(0, 2**16, (480, 640), dtype=np.uint16),
        'state': np.random.rand(20,).astype(np.float32),
        'language': ['pick bottle into the box'],
    }

    return_key = ['type', 'pred_action', 'ref_timestamp']

    result = model.infer([{'obs': obs, 'ref_timestamp': [], 'loc_timestamp': []}])

    # Check result
    for key in return_key:
        if key not in result:
            raise ValueError(f'result key error, not found {key}')

    if result[return_key[0]] != 'vla_action':
        raise ValueError(f"result.{return_key[0]} error, should be vla_action, but got {result[return_key[0]]}")

    if not isinstance(result[return_key[1]], np.ndarray):
        raise ValueError(f"result.{return_key[1]} error, should be ndarray, but got {type(result[return_key[1]])}")

    if not isinstance(result[return_key[2]], list):
        raise ValueError(f"result.{return_key[2]} error, should be list, but got {type(result[return_key[2]])}")

    print("Test passed!")