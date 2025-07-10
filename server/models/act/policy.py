import torch
import torch.nn as nn
from torch.nn import functional as F
import torchvision.transforms as transforms

from detr.main import build_ACT_model_and_optimizer, build_CNNMLP_model_and_optimizer,build_diffusion_optimizer
import IPython
e = IPython.embed


class FocalLoss(nn.Module):
    def __init__(self, alpha=1, gamma=2, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha  # 控制正负样本权重
        self.gamma = gamma  # 控制难易样本的权重
        self.reduction = reduction  # 'mean', 'sum', 'none'

    def forward(self, inputs, targets):
        # 使用 sigmoid 函数将输入转换为 [0, 1] 之间的概率值
        sigmoid_p = torch.sigmoid(inputs)  # 计算输出的概率
        p_t = sigmoid_p * targets + (1 - sigmoid_p) * (1 - targets)  # 计算目标类别的概率

        # 计算交叉熵损失
        BCE_loss = F.binary_cross_entropy_with_logits(inputs, targets, reduction='none')

        # Focal Loss 公式
        focal_loss = self.alpha * (1 - p_t) ** self.gamma * BCE_loss

        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss



class ACTPolicy(nn.Module):
    def __init__(self, args_override):
        super().__init__()
        print(222)
        model, optimizer = build_ACT_model_and_optimizer(args_override)
        print(333)
        self.model = model # CVAE decoder
        self.optimizer = optimizer
        self.kl_weight = args_override['kl_weight']
        self.is_done = True
        print(f'KL Weight {self.kl_weight}')

    def __call__(self, qpos, image, actions=None, is_pad=None,action_done = None,command_embedding = None):
        env_state = None
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                         std=[0.229, 0.224, 0.225])
        image = normalize(image)
        #print("actions.shape",actions.shape)
        # print("action data 1 ", actions[..., -1])
        if actions is not None: # training time
            if (actions.shape[-1]==10 or actions.shape[-1]==19):
                action_done = actions[:, 0, -1]
                actions = actions[:, :, :-1]
                actions = actions[:, :self.model.num_queries]
                is_pad = is_pad[:, :self.model.num_queries]
                # print("***************",action_done)
                # exit()
            action_done = action_done.reshape(-1,1)

            if self.is_done:
                a_hat, a_done_hat,is_pad_hat, (mu, logvar) = self.model(qpos, image, env_state, actions, is_pad,command_embedding)
            else:
                a_hat, is_pad_hat, (mu, logvar) = self.model(qpos, image, env_state, actions, is_pad,command_embedding)
            total_kld, dim_wise_kld, mean_kld = kl_divergence(mu, logvar)
            loss_dict = dict()
            all_l1 = F.l1_loss(actions, a_hat, reduction='none')
            #print(all_l1)
            l1 = (all_l1 * ~is_pad.unsqueeze(-1)).mean()
            if actions.shape[-1] == 9:
                hand_l1 = F.l1_loss(actions[...,7:9],a_hat[...,7:9],reduction='none')
                hand_l1 = (hand_l1 * ~is_pad.unsqueeze(-1)).mean()
            if actions.shape[-1] == 18:
                hand_l1_lhand = F.l1_loss(actions[..., 7:9], a_hat[..., 7:9], reduction='none')
                hand_l1_rhand = F.l1_loss(actions[..., 16:18], a_hat[..., 16:18], reduction='none')
                hand_l1_lhand = (hand_l1_lhand * ~is_pad.unsqueeze(-1)).mean()
                hand_l1_rhand = (hand_l1_rhand * ~is_pad.unsqueeze(-1)).mean()
                # actions_concat = torch.cat((actions[..., 7:9], actions[..., 16:18]), dim=-1)
                # # 拼接 a_hat[..., 7:9] 和 a_hat[..., 16:18]
                # a_hat_concat = torch.cat((a_hat[..., 7:9], a_hat[..., 16:18]), dim=-1)
                # # 计算拼接后的 L1 损失
                # hand_l1 = F.l1_loss(actions_concat, a_hat_concat, reduction='none')
            #print(hand_l1)
            # done_l1 = F.l1_loss(actions[...,9],a_hat[...,9],reduction='none')
            # done_l1 = (done_l1 * ~is_pad).mean()
            #print("action done ",a_done_hat,action_done)
            criterion = nn.MSELoss()  # 不进行求和或平均，保留每个样本的损失
            #criterion = FocalLoss(alpha=0.2, gamma=2, reduction='mean')
            # 计算每个样本的 BCELoss
            #done_loss = criterion(a_done_hat, is_action_done.float().unsqueeze(dim=-1))  # 不做任何归约，计算每个位置的损失
            # print("a_done_hat",a_done_hat.shape)
            # print("action done",action_done.shape)
            done_loss = criterion(a_done_hat,action_done)
            # 使用 mask（is_pad）来只保留非填充部分的损失，填充部分的损失为 0
            #done_loss = (bce_loss * ~is_pad.unsqueeze(-1)).mean()  # 对应位置是填充时，损失为0
            #print(done_loss)
            #criterion = FocalLoss(alpha=1, gamma=2, reduction='mean')
            # criterion = nn.BCEWithLogitsLoss()
            # done_bool_loss = criterion(a_done_hat, is_action_done.float().unsqueeze(dim=-1))

            #exit()
            loss_dict['l1'] = l1
            loss_dict['kl'] = total_kld[0]
            if actions.shape[-1] == 9:
                loss_dict['hand_l1'] = hand_l1
            elif actions.shape[-1] == 18:
                loss_dict['hand_l1_l'] = hand_l1_lhand
                loss_dict['hand_l1_r'] = hand_l1_rhand

            #loss_dict['done_l1'] = done_loss
            loss_dict['done_l1'] = done_loss

            loss_dict['loss'] = loss_dict['l1'] + loss_dict['done_l1'] + loss_dict['kl']*self.kl_weight

            return loss_dict
        else: # inference time
            #print("command_embedding",command_embedding.shape)
            if self.is_done:
                a_hat,a_done_hat, _, (_, _) = self.model(qpos, image, env_state,command_embedding=command_embedding)
                #a_done_hat = torch.sigmoid(a_done_hat)
                # print(a_done_hat)
                # exit()
                return a_hat,a_done_hat
            else:
                a_hat, _, (_, _) = self.model(qpos, image, env_state,command_embedding=command_embedding) # no action, sample from prior
            return a_hat

    def configure_optimizers(self):
        return self.optimizer


from detr.models.diffusion.configuration_diffusion import DiffusionConfig
from detr.models.diffusion.modeling_diffusion import DiffusionPolicy
#from detr.factory import _policy_cfg_from_hydra_cfg


class  DPolicy(nn.Module):

    def __init__(self, cfg):
        super().__init__()
        # self.model = make_policy(
        #     hydra_cfg=cfg,
        #     dataset_stats= None,
        #     pretrained_policy_name_or_path =  None,
        # )
        #policy_cfg = _policy_cfg_from_hydra_cfg(DiffusionConfig, cfg)
        policy_cfg = None
        self.cfg = cfg
        self.model = DiffusionPolicy(policy_cfg, None)

        assert isinstance(self.model, nn.Module)
        # Create optimizer and scheduler
        # Temporary hack to move optimizer out of policy
        self.optimizer, self.lr_scheduler = build_diffusion_optimizer(cfg, self.model)

    def __call__(self, qpos, image, actions=None, is_pad=None):
        env_state = None
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                         std=[0.229, 0.224, 0.225])
        image = normalize(image)

        """
        batch: dict[str, Tensor]
                This function expects `batch` to have (at least):
                {
                    "observation.state": (B, n_obs_steps, state_dim)

                    "observation.images": (B, n_obs_steps, num_cameras, C, H, W)
                        AND/OR
                    "observation.environment_state": (B, environment_dim)

                    "action": (B, horizon, action_dim)
                    "action_is_pad": (B, horizon)
                }
        """
        batch = {}

        if actions is not None:  # training time
            batch["observation.state"] = qpos.unsqueeze(1)
            batch["observation.images"] = image.unsqueeze(1)
            batch["action"] = actions[:, :self.cfg.policy.horizon]
            batch["action_is_pad"] = is_pad[:, :self.cfg.policy.horizon]


            loss_dict = self.model(batch)
            # loss_dict['l1'] = l1
            # loss_dict['hand_l1'] = hand_l1
            #loss_dict['loss'] = loss_dict['l1'] + loss_dict['kl'] * self.kl_weight

            return loss_dict
        else:  # inference time
            batch["observation.state"] = qpos
            batch["observation.images"] = image
            action = self.model.select_action(batch)
            # no action, sample from prior
            return action

    def configure_optimizers(self):
        return self.optimizer,self.lr_scheduler


class CNNMLPPolicy(nn.Module):
    def __init__(self, args_override):
        super().__init__()
        model, optimizer = build_CNNMLP_model_and_optimizer(args_override)
        self.model = model # decoder
        self.optimizer = optimizer

    def __call__(self, qpos, image, actions=None, is_pad=None):
        env_state = None # TODO
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                         std=[0.229, 0.224, 0.225])
        image = normalize(image)
        if actions is not None: # training time
            actions = actions[:, 0]
            a_hat = self.model(qpos, image, env_state, actions)
            mse = F.mse_loss(actions, a_hat)
            loss_dict = dict()
            loss_dict['mse'] = mse
            loss_dict['loss'] = loss_dict['mse']
            return loss_dict
        else: # inference time
            a_hat = self.model(qpos, image, env_state) # no action, sample from prior
            return a_hat

    def configure_optimizers(self):
        return self.optimizer

def kl_divergence(mu, logvar):
    batch_size = mu.size(0)
    assert batch_size != 0
    if mu.data.ndimension() == 4:
        mu = mu.view(mu.size(0), mu.size(1))
    if logvar.data.ndimension() == 4:
        logvar = logvar.view(logvar.size(0), logvar.size(1))

    klds = -0.5 * (1 + logvar - mu.pow(2) - logvar.exp())
    total_kld = klds.sum(1).mean(0, True)
    dimension_wise_kld = klds.mean(0)
    mean_kld = klds.mean(1).mean(0, True)

    return total_kld, dimension_wise_kld, mean_kld
