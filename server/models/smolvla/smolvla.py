import os
import time
import numpy as np
import torch
from lerobot.common.utils.utils import (
    format_big_number,
    get_safe_torch_device,
    has_method,
    init_logging,
)
from lerobot.common.utils.wandb_utils import WandBLogger
from lerobot.configs import parser
# from lerobot.configs.train import TrainPipelineConfig
from lerobot.configs.inference import TrainPipelineConfig
import logging
import time
from contextlib import nullcontext
from pprint import pformat
from typing import Any

import torch
from termcolor import colored
from torch.amp import GradScaler
from torch.optim import Optimizer

from lerobot.common.datasets.factory import make_dataset
from lerobot.common.datasets.sampler import EpisodeAwareSampler
from lerobot.common.datasets.utils import cycle
from lerobot.common.envs.factory import make_env
from lerobot.common.optim.factory import make_optimizer_and_scheduler
from lerobot.common.policies.factory import make_policy
from lerobot.common.policies.pretrained import PreTrainedPolicy
from lerobot.common.policies.utils import get_device_from_parameters
from lerobot.common.utils.logging_utils import AverageMeter, MetricsTracker
from lerobot.common.utils.random_utils import set_seed
from lerobot.configs.default import DatasetConfig, EvalConfig, WandBConfig
from lerobot.configs.default import DatasetConfig
import cv2
from PIL import Image

import pandas as pd

OBSCAMERANAME= ["observation.images.top_head","observation.images.hand_left","observation.images.hand_right"]

def preprocess_image(img_origin,change_BGR_to_RGB=True, channel_first=True, dtype=np.float32):
    # BGR to RGB
    if change_BGR_to_RGB:
        img_array = img_origin[..., ::-1]  
    else:
        img_array = img_origin.copy()  
        # print('change BGR to RGB')
    # print(f'imageshape : {img_array.shape}')
    if channel_first:  # (b,H, W, C) -> (b,C, H, W)
        img_array = np.transpose(img_array, (0, 3, 1, 2))
    ##归一化

    img_array = img_array.astype(dtype)
    img_array /= 255.0


    # Convert to PyTorch tensor
    tensor_img = torch.from_numpy(img_array).float()  # 转换为tensor
    
    # # Add batch dimension to make it (B, C, H, W)
    # tensor_img = tensor_img.unsqueeze(0)
    # print(tensor_img.shape)
    return tensor_img

class ModelVLA:
    def __init__(self):
        print('vla model start init')
        model_path = '/home/robot/Downloads/lerobot/070000/pretrained_model'
        cfg = TrainPipelineConfig(dataset = DatasetConfig(...))
        from lerobot.common.utils.random_utils import set_seed
        ##设置随机数种子
        set_seed(cfg.seed)
        print('set seed',cfg.seed)
        #定义配置文件
        cfg.validate(model_path)
        print('set model path :' , model_path)
        cfg.dataset.root="/home/robot/Downloads/lerobot/task_158284_depth_test/task_158284_test"
        cfg.dataset.repo_id = "catch_box_440"
        self.device = get_safe_torch_device(cfg.policy.device, log=True)
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        logging.info("Creating dataset")
        #加载数据集
        dataset = make_dataset(cfg)

        #加载模型
        self.policy = make_policy(
            cfg=cfg.policy,
            ds_meta=dataset.meta
        )
        print('policy load finished!!')
        print('policy load finished!!')
        file_path = '/home/robot/Downloads/lerobot/task_158284_depth_test/task_158284_test/data/chunk-000/episode_000000.parquet'
        df = pd.read_parquet(file_path)
        self.init_state = df.iloc[0, 0]
        # self.policy.eval()
        self.policy.eval()


    def gengerate_state(self,state):
        state = np.squeeze(state)
        part1 = state[0:7]
        part2 = self.init_state[7:14]
        part3 = state[14:16]
        part4 = self.init_state[16:20]
        
        output = np.concatenate([part1, part2, part3, part4])
        
        print(f"output state {output}")
        return output[None]  # 添加batch维度


    def infer(self, data):
        # data = sequence[0]
        obs = data['obs']
        # print(obs)
        obs['state'] = obs['state'][None]
        print(f"state: {obs['state']}")
        only_left_state = self.gengerate_state(obs['state'])
        # print('headimage_shape: ',torch.from_numpy(obs['cam.head'][None]).float().shape)
        # 确保 obs 中的数据已全部转为 PyTorch Tensor
        inp_obs = {
            # "observation.images.top_head": torch.from_numpy(obs['cam.head'][None]).float().permute(0, 3, 1, 2) /255.0,
            # "observation.images.hand_left": torch.from_numpy(obs['cam.hand_left'][None]).float().permute(0, 3, 1, 2)/255.0,
            # "observation.images.hand_right": torch.from_numpy(obs['cam.hand_right'][None]).float().permute(0, 3, 1, 2)/255.0,
            "observation.images.top_head": preprocess_image(obs['cam.head'][None]),
            "observation.images.hand_left": preprocess_image(obs['cam.hand_left'][None]),
            "observation.images.hand_right": preprocess_image(obs['cam.hand_right'][None]),
            # "observation.state": torch.from_numpy(obs['state']).float(),
            "observation.state": torch.from_numpy(only_left_state).float(),
            "task": ['pick bottle into the box'],
        }

        # 如果模型在 GPU 上，记得将 tensor 移动到对应设备上
        # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        inp_obs = {
            k: v.clone().detach().to(self.device) if isinstance(v, torch.Tensor) else v
            for k, v in inp_obs.items()
        }
        time1 = time.time()
        predicted_action = self.policy.select_action(inp_obs)
        predicted_action = predicted_action.detach().cpu().numpy().squeeze(0)
        save_observation(inp_obs,predicted_action, "./output")  
        # print(f'predicted_action: {predicted_action}')
        # print('In infer, predicted_action 49 is: ', predicted_action[48])
        # print('In infer, predicted_action 50 is: ', predicted_action[49])
        # print(f'predicted_actionshape: {predicted_action.shape}')
        print(time.time() - time1, 'action shape:', predicted_action.shape)
        return {
            "type": "action",
            "pred_action": predicted_action,
            "ref_timestamp": data["ref_timestamp"],
            'loc_timestamp': data['loc_timestamp']
        }


def save_observation(observation,predicted_action, output_dir):
    """
    将 observation 中的图像和 state 保存到指定目录。

    参数:
        observation (dict): 包含图像和 state 的字典。
        output_dir (str): 保存文件的目录路径。
    """
    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)

    # 保存图像
    for name in OBSCAMERANAME:
        # 假设 image_tensor 是形状为 (b,C, H, W) 的 PyTorch 张量
        image_tensor = observation[name]
        image = image_tensor.cpu().numpy().transpose(0,2, 3, 1)  # 转换为 (H, W, C)
        #图像降维度
        image = np.squeeze(image)
        image = (image * 255).astype(np.uint8)  # 如果张量值在 [0, 1] 范围内，则转换为 [0, 255]
        img = Image.fromarray(image)
        img.save(os.path.join(output_dir, f"{name}.png"))

    # 保存 state
    if "observation.state" in observation:
        state = observation["observation.state"].cpu().numpy()
        np.save(os.path.join(output_dir, "state.npy"), state)
    # if predicted_action:
        np.save(os.path.join(output_dir, "predicted_action.npy"), predicted_action)

if __name__ == "__main__":
    # 其它vla模型参照下面的代码，测试通过即可
    # model = ModelVLA('/home/zhangjian/zhangjian/lerobot/070000/pretrained_model')
    model = ModelVLA('/home/zhangjian/zhangjian/lerobot/2025-07-02/left-hand-only/050000/pretrained_model')
    # model = ModelVLA('/home/rm/wxz/EmbodiedAI/lerobot/model/smol_vla/task_138_8w/pretrained_model')
    obs = {
        'cam.head': np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),
        'cam.hand_left': np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),
        'cam.hand_right': np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),
        'state': np.random.rand(20,),
        'task': ['pick bottle into the box'],
    }
    return_key = ['type', 'pred_action', 'ref_timestamp']
    while True:
        result = model.infer([{'obs': obs, 'ref_timestamp': []}])
        print ("result[pred_action] shape is: ", result["pred_action"].shape)
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
