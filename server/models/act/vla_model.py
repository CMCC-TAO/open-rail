import os
import time
import numpy as np
import torch
import sys
# sys.path.append('/home/robot/Music/ACT_code_checkpoint/act')
from einops import rearrange
import argparse
import time
from omegaconf import OmegaConf
import matplotlib.pyplot as plt
#from process_utils.process_utils import initialize_model_and_tokenizer, encode_text
import cv2
from pathlib import Path
from torch.utils.data import Subset
from .lerobot_utils.data_utils import load_stats,load_command_dict
from .lerobot_utils.normalize import Normalize, Unnormalize
from .policy import ACTPolicy,DPolicy
torch.set_printoptions(precision=6, sci_mode=False)  



class ModelVLA:
    def __init__(self, args=None):
        if args is None:
            args = {
                'ckpt_dir':'/home/robot/Music/ACT_code_checkpoint/save_model/pick_bottle/data_349',
                'policy_class':'ACT',
                'chunk_size':60,
                'task_name':'pick_bread',
                'use_language':False
            }
        self.config = self.get_config(args)
        self.set_seed(self.config['seed'])
        #print(self.config)
        self.policy = None
        self.stats = {}
        self.state_dim = self.config['state_dim']
        self.camera_names = self.config['camera_names']
        self.root = Path(self.config['ckpt_dir'])
        self.normalize = True
        self.arm_only = False
        self.load_model()
        print("self.state_dim",self.state_dim)
        if self.state_dim == 22 and self.normalize:
            self.normalize_init()
        if self.config["use_language"]:
            print("use language")
            self.command_dict = load_command_dict(self.root)
        

    def normalize_init(self):
        #print("******** normalize***********")
        input_shapes = {
            "observation.state": [20],
        }
        output_shapes = {
        "action": [22],
        }       
        input_normalization_modes = {
            "observation.state": "min_max",
        }
        output_normalization_modes = {
                "action": "min_max",
            }
        self.normalize_inputs = Normalize(
        input_shapes, input_normalization_modes, self.stats
        )
        self.normalize_targets = Normalize(
            output_shapes, output_normalization_modes, self.stats
        )
        self.unnormalize_outputs = Unnormalize(
            output_shapes, output_normalization_modes, self.stats
        )

    def load_model(self):
        ckpt_dir = self.config['ckpt_dir']
        #policy_config = self.config['policy_config']

        # 加载模型
        ckpt_path = os.path.join(ckpt_dir, f'policy_best.ckpt')
        print("ckpt path",ckpt_path)
        if self.config["policy_class"] == "ACT":
            self.policy = ACTPolicy(self.config)
        elif self.config["policy_class"] == "Diffusion":
            cfg = OmegaConf.load("./detr/models/diffusion/diffusion.yaml")
            self.policy = DPolicy(cfg)
        loading_status = self.policy.load_state_dict(torch.load(ckpt_path))
        self.policy.cuda()
        self.policy.eval()
        print(f'Loaded model: {ckpt_path}')
        self.stats = load_stats(self.root)

    def set_seed(self, seed):
            torch.manual_seed(seed)
            np.random.seed(seed)
    
    def get_config(self, args):
        # from constants import Real_TASK_CONFIGS
        # task_config = Real_TASK_CONFIGS[args['task_name']]
        camera_names = ['head','left_arm','right_arm']

        state_dim = 22
        lr_backbone = 1e-5
        #backbone = 'resnet18'
        policy_class = args['policy_class']
        use_language = args['use_language']
        language_encoder = 'distilbert'

        if policy_class == 'ACT' or policy_class == 'Diffusion':
            enc_layers = 4
            dec_layers = 7
            nheads = 8
            policy_config = {
                'num_queries': args['chunk_size'],
                'kl_weight': 10,
                'hidden_dim': 512,
                'dim_feedforward': 3200,
                'lr_backbone': lr_backbone,
                'backbone': 'resnet18',
                'enc_layers': enc_layers,
                'dec_layers': dec_layers,
                'nheads': nheads,
                'camera_names': camera_names,
            }
        config = {
            'num_queries': args['chunk_size'],
            'state_dim': state_dim,
            'kl_weight': 10,
            'hidden_dim': 512,
            'dim_feedforward': 3200,
            'lr_backbone': lr_backbone,
            'backbone': 'resnet18',
            'enc_layers': enc_layers,
            'dec_layers': dec_layers,
            'nheads': nheads,
            'camera_names': camera_names,
            'ckpt_dir': args['ckpt_dir'],
            'num_epochs':2000,
            'episode_len': 100,
            'task_name': 'pick_bread',
            'seed': 0,
            'temporal_agg': False,
            'camera_names': camera_names,
            'policy_class': policy_class,
            "use_language": use_language,
            "language_encoder": language_encoder,

        }
        return config
    
    def get_image(self, observations, camera_names):
        curr_images = []
        for cam_name in camera_names:
            # output_path = "./"+cam_name+'.png'  # 保存路径和文件名
            # cv2.imwrite(output_path, observations[f'images/{cam_name}'])

            curr_image = rearrange(observations[cam_name], 'h w c -> c h w')
            curr_images.append(curr_image)


        curr_image = np.stack(curr_images, axis=0)
        curr_image = torch.from_numpy(curr_image / 255.0).float().cuda().unsqueeze(dim=0)
        return curr_image

    def infer(self, sequence):
        data = sequence[0]
        print(data.keys())
        # obs = data['obs'].copy()
        obs = data.copy()
        # obs['state'] = obs['state'][None]
        #print(obs['video.cam_right_high'].shape, obs['state'].shape)
        aaa = time.time()

        with torch.inference_mode():
            
            obs['observation.state'] = torch.tensor(obs['state'],dtype=torch.float32)

            obs = self.normalize_inputs(obs)
            if not self.arm_only :
                obs['observation.state'][:,8:] = torch.tensor([0.726373, -0.437754, -0.721693, 0.638622,
    0.711874, -0.632738, -0.671046, 0.000000, -0.379791, -0.378923,
    0.286311, 0.293441])

            if self.config["use_language"]:
                command_embediing  = self.command_dict.get(instruction)
                command_embedding = torch.tensor(command_embediing, dtype=torch.float32).cuda()
            #qpos = torch.from_numpy(observations['observation.state']).float().cuda().unsqueeze(0)
            if "cam.head" in obs.keys():
                # print(obs['video.cam_right_high'].shape)
                # print("*********")
                expected_image_keys = ["cam.head", "cam.hand_left","cam.hand_right"]
                expected_image_keys = expected_image_keys[0:len(self.camera_names)]
                # if len(expected_image_keys) > 0:
                #     curr_image = torch.stack([obs[k] for k in expected_image_keys], dim=-4).cuda().squeeze(0)
                # print(curr_image.shape)
                curr_image = self.get_image(obs, expected_image_keys)
            else:
                curr_image = self.get_image(obs, self.camera_names)

            #print("curr_image shape",curr_image.shape) #([1, 3, 3, 480, 640])
            # print("command embedding shape",command_embedding.shape)
            if not self.config["use_language"]:
                command_embedding = None
                #print("not use action")
            if self.arm_only:
                # print("arm only")
                # print(obs['observation.state'].shape)
                qpos = obs['observation.state'][:,0:16].cuda()
            else:
                qpos = obs['observation.state'].cuda()
            pre_data = self.policy(qpos, curr_image,command_embedding=command_embedding)
                        #print("len data",len(data))
            if len(pre_data )== 2:
                all_actions ,action_done = pre_data 
        
            action_done = action_done.squeeze(0).cpu().numpy()
            #print("action shape",all_actions.shape)
            if self.arm_only:
                head_waist = torch.randn(6)
                head_waist = head_waist.unsqueeze(0).unsqueeze(0).repeat(1, 60, 1).cuda()
                all_actions = torch.cat((all_actions,head_waist),dim=2)
            predicted_action = self.unnormalize_outputs({"action": all_actions.cpu()[0]})["action"].numpy()[:,0:16]

            #predicted_action = self.policy.get_action(obs)
            print(time.time() - aaa, obs.keys())
            print('predicted_action', predicted_action.shape)
            return {"type": "action", "pred_action": predicted_action, 'obs_state': obs['state'], "ref_timestamp": data["ref_timestamp"]}

    def test_policy(self, obs):
        aaa = time.time()
        result = self.infer([obs])
        bbb = time.time()
        print(f"time cost {bbb-aaa}")
        return result
        #return {"type": "action", "data": predicted_action}


if __name__ == "__main__":
    import time

    obs = {
        "head": np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),
        "left_arm": np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),
        "right_arm": np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),
        # "state.left_arm": np.random.rand(1, 7),
        # "state.right_arm": np.random.rand(1, 7),
        # "state.left_hand": np.random.rand(1, 1),
        # "state.right_hand": np.random.rand(1, 1),
        "ref_timestamp": time.clock_gettime_ns(time.CLOCK_MONOTONIC),
        "state": np.random.rand(1, 20),
        "annotation.human.action.task_description": ["do your thing!"],
    }
    model = ModelVLA()
    result = model.test_policy(obs)
    print(result)
