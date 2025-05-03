# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
"""
DETR model and criterion classes.
"""
import torch
from torch import nn
from torch.autograd import Variable
from .backbone import build_backbone
from .back_bone_film import build_backbone as build_backbone_film
from .transformer import build_transformer, TransformerEncoder, TransformerEncoderLayer

import numpy as np

import IPython
e = IPython.embed


def reparametrize(mu, logvar):
    std = logvar.div(2).exp()
    eps = Variable(std.data.new(std.size()).normal_())
    return mu + std * eps

#返回的结果是一个 3D 的张量，表示一个包含所有位置编码的 batch。
def get_sinusoid_encoding_table(n_position, d_hid):
    def get_position_angle_vec(position):
        return [position / np.power(10000, 2 * (hid_j // 2) / d_hid) for hid_j in range(d_hid)]

    sinusoid_table = np.array([get_position_angle_vec(pos_i) for pos_i in range(n_position)])
    sinusoid_table[:, 0::2] = np.sin(sinusoid_table[:, 0::2])  # dim 2i
    sinusoid_table[:, 1::2] = np.cos(sinusoid_table[:, 1::2])  # dim 2i+1

    return torch.FloatTensor(sinusoid_table).unsqueeze(0)


class TaskCompletionNetwork(nn.Module):
    def __init__(self, input_dim, dropout_rate=0.1):
        super(TaskCompletionNetwork, self).__init__()

        # 只有一层映射
        # self.fc1 = nn.Linear(input_dim, 1)  # 输入维度根据你的数据决定，输出一个值
        #
        # # Dropout层
        # self.dropout = nn.Dropout(p=dropout_rate)
        #
        # # Sigmoid 激活函数用于输出任务完成度 (0, 1)
        # self.sigmoid = nn.Sigmoid()

        self.dropout = nn.Dropout(0.1)
        self.norm = nn.LayerNorm(input_dim)
        self.relu = nn.ReLU()
        self.fc = nn.Linear(input_dim, 1)

    def forward(self, x):
        x = torch.mean(x, dim=1)
        x = self.dropout(x)  # 应用dropout
        x = self.norm(x)
        x = self.relu(x)
        x = self.fc(x)  # 输出任务完成度 (0, 1)
        return x


class DETRVAE(nn.Module):
    """ This is the DETR module that performs object detection """
    def __init__(
            self,
            backbones,
            transformer,
            encoder,
            state_dim,
            num_queries,
            camera_names,
            use_language=False,
            use_film=False,
            use_is_done = True,
            use_history = False,
    ):
        """ Initializes the model.
        Parameters:
            backbones: torch module of the backbone to be used. See backbone.py
            transformer: torch module of the transformer architecture. See transformer_ori.py
            state_dim: robot state dimension of the environment
            num_queries: number of object queries, ie detection slot. This is the maximal number of objects
                         DETR can detect in a single image. For COCO, we recommend 100 queries.
            aux_loss: True if auxiliary decoding losses (loss at each decoder layer) are to be used.
        """
        super().__init__()
        self.num_queries = num_queries
        self.camera_names = camera_names
        self.transformer = transformer
        self.encoder = encoder
        self.hidden_dim = hidden_dim = transformer.d_model
        self.use_language = use_language
        self.use_film = use_film
        self.use_history = use_history
        if self.use_language:
            self.lang_embed_proj = nn.Linear(
                768, hidden_dim
            )  # 512 / 768 for clip / distilbert

        self.is_done = use_is_done
        if self.is_done:
            #self.action_head = nn.Linear(hidden_dim, state_dim+1)
            self.action_done_head = TaskCompletionNetwork(hidden_dim)
        self.action_head = nn.Linear(hidden_dim, state_dim)
        self.is_pad_head = nn.Linear(hidden_dim, 1)
        self.query_embed = nn.Embedding(num_queries, hidden_dim)

        #state_dim ### (aloha 14, real robot 16)
        if backbones is not None:
            self.input_proj = nn.Conv2d(backbones[0].num_channels, hidden_dim, kernel_size=1)
            self.backbones = nn.ModuleList(backbones)
            if state_dim == 22:
                self.input_proj_robot_state = nn.Linear(state_dim-2, hidden_dim)
            else:
                self.input_proj_robot_state = nn.Linear(state_dim, hidden_dim)
        else:
            # input_dim = 14 + 7 # robot_state + env_state
            self.input_proj_robot_state = nn.Linear(14, hidden_dim)
            self.input_proj_env_state = nn.Linear(7, hidden_dim)
            self.pos = torch.nn.Embedding(2, hidden_dim)
            self.backbones = None

        # encoder extra parameters
        self.latent_dim = 32 # final size of latent z # TODO tune
        self.cls_embed = nn.Embedding(1, hidden_dim) # extra cls token embedding
        self.encoder_action_proj = nn.Linear(state_dim, hidden_dim) # project action to embedding
        if state_dim ==22:
            self.encoder_joint_proj = nn.Linear(state_dim-2, hidden_dim)
        else:
            self.encoder_joint_proj = nn.Linear(state_dim, hidden_dim)  # project qpos to embedding
        self.latent_proj = nn.Linear(hidden_dim, self.latent_dim*2) # project hidden state to latent std, var
        self.register_buffer('pos_table', get_sinusoid_encoding_table(1+1+num_queries, hidden_dim)) # [CLS], qpos, a_seq

        # decoder extra parameters
        self.latent_out_proj = nn.Linear(self.latent_dim, hidden_dim) # project latent sample to embedding
        pos_embed_dim = 3 if self.use_language else 2
        self.additional_pos_embed = nn.Embedding(pos_embed_dim, hidden_dim) # learned position embedding for proprio and latent

    def forward(self, qpos, image, env_state, actions=None, is_pad=None, command_embedding=None):
        """
        qpos: batch, qpos_dim
        image: batch, num_cam, channel, height, width
            use history :
            image: batch, num_cam, sequence, channel, height, width
        env_state: None
        actions: batch, seq, action_dim
        """
        # if self.is_done and actions is not None:
        #     actions = actions[:, :, :-1]
            #print(actions.shape)
        is_training = actions is not None # train or val
        bs, _ = qpos.shape
        #command_embedding = None
        # Project the command embedding to the required dimension
        if command_embedding is not None and self.use_language:
            if self.use_language:
                command_embedding_proj = self.lang_embed_proj(command_embedding)
            else:
                raise NotImplementedError
        ### Obtain latent z from action sequence
        # print("actions shape in train",actions.shape)  #([8, 100, 16])
        # print("qpos shape in traing", qpos.shape)
        if is_training:
            # project action sequence to embedding dim, and concat with a CLS token
            action_embed = self.encoder_action_proj(actions) # (bs, seq, hidden_dim)
            qpos_embed = self.encoder_joint_proj(qpos)  # (bs, hidden_dim)
            qpos_embed = torch.unsqueeze(qpos_embed, axis=1)  # (bs, 1, hidden_dim)
            cls_embed = self.cls_embed.weight # (1, hidden_dim)
            cls_embed = torch.unsqueeze(cls_embed, axis=0).repeat(bs, 1, 1) # (bs, 1, hidden_dim)
            encoder_input = torch.cat([cls_embed, qpos_embed, action_embed], axis=1) # (bs, seq+1, hidden_dim)
            encoder_input = encoder_input.permute(1, 0, 2) # (seq+1, bs, hidden_dim)
            # do not mask cls token
            cls_joint_is_pad = torch.full((bs, 2), False).to(qpos.device) # False: not a padding
            is_pad = torch.cat([cls_joint_is_pad, is_pad], axis=1)  # (bs, seq+1)
            # obtain position embedding
            pos_embed = self.pos_table.clone().detach()
            pos_embed = pos_embed.permute(1, 0, 2)  # (seq+1, 1, hidden_dim)
            # query model
            encoder_output = self.encoder(encoder_input, pos=pos_embed, src_key_padding_mask=is_pad)
            encoder_output = encoder_output[0] # take cls output only
            latent_info = self.latent_proj(encoder_output)
            mu = latent_info[:, :self.latent_dim]
            logvar = latent_info[:, self.latent_dim:]
            latent_sample = reparametrize(mu, logvar)
            latent_input = self.latent_out_proj(latent_sample)
        else:
            mu = logvar = None
            latent_sample = torch.zeros([bs, self.latent_dim], dtype=torch.float32).to(qpos.device)
            latent_input = self.latent_out_proj(latent_sample)
        #print("latent input shape",latent_input.shape)#（batch,hidden_dim）
        #print("self.backbones",self.backbones)
        if self.backbones is not None:
            # Image observation features and position embeddings
            all_cam_features = []
            all_cam_pos = []
            for cam_id, cam_name in enumerate(self.camera_names):
                #features, pos = self.backbones[0](image[:, cam_id]) # HARDCODED
                #print("before encode image shape",image[:, cam_id].shape)
                if self.use_history:
                    frame_features = []
                    frame_pos = []
                    #print("image shape",image.shape)
                    for frame_id in range(image.shape[2]):
                        if self.use_film:
                            features, pos = self.backbones[cam_id](
                                image[:, cam_id,frame_id], command_embedding
                            )
                        else:
                            #print("image[:, cam_id,frame_id].shape",image[:, cam_id,frame_id].shape)
                            features, pos = self.backbones[cam_id](image[:, cam_id,frame_id])
                        features = features[0]  # take the last layer feature
                        pos = pos[0]  ## 图像的位置序列
                        frame_features.append(self.input_proj(features))
                        frame_pos.append(pos)
                    all_cam_features.append(torch.cat(frame_features, axis=2))
                    all_cam_pos.append(torch.cat(frame_pos, axis=2))
                    #print("history features shape in one cam ",all_cam_features[-1].shape)
                else:
                    if self.use_film:
                        features, pos = self.backbones[cam_id](
                            image[:, cam_id], command_embedding
                        )
                    else:
                        print("shape",image[:, cam_id].shape)
                        features, pos = self.backbones[cam_id](image[:, cam_id])

                        #features, pos = self.backbones[cam_id]( torch.cat([image[:, cam_id],image[:, cam_id]], axis=3))
                    features = features[0] # take the last layer feature
                    pos = pos[0]  ## 图像的位置序列
                    # features =  torch.cat([features[0],features[0]],axis=2)
                    # pos = torch.cat([pos[0],pos[0]],axis=2)
                    #print("image feature shape",features.shape)  #（batch,hidden_dim,H,W)

                    all_cam_features.append(self.input_proj(features))
                    all_cam_pos.append(pos)
                    #print("image feature shape 1",all_cam_features[-1].shape)

            # proprioception features
            #print("qpos shape",qpos.shape)
            proprio_input = self.input_proj_robot_state(qpos)
            #print("proprio_input shape", proprio_input.shape)
            # fold camera dimension into width dimension
            src = torch.cat(all_cam_features, axis=3)
            #print("all image feature shape", src.shape)
            pos = torch.cat(all_cam_pos, axis=3)
            # Only append the command embedding if we are using one-hot
            command_embedding_to_append = (
                command_embedding_proj if self.use_language else None
            )

            hs = self.transformer(
                src,
                None,
                self.query_embed.weight,
                pos,
                latent_input,
                proprio_input,
                self.additional_pos_embed.weight,
                command_embedding = command_embedding_to_append,
            )[0]
        else:
            qpos = self.input_proj_robot_state(qpos)
            env_state = self.input_proj_env_state(env_state)
            transformer_input = torch.cat([qpos, env_state], axis=1) # seq length = 2
            hs = self.transformer(transformer_input, None, self.query_embed.weight, self.pos.weight)[0]
        a_hat = self.action_head(hs)
        is_pad_hat = self.is_pad_head(hs)
        if self.is_done:
            is_done = self.action_done_head(hs)

            return a_hat,is_done, is_pad_hat, [mu, logvar]
        #print("action feature shape", a_hat.shape)
        return a_hat, is_pad_hat, [mu, logvar]



class CNNMLP(nn.Module):
    def __init__(self, backbones, state_dim, camera_names):
        """ Initializes the model.
        Parameters:
            backbones: torch module of the backbone to be used. See backbone.py
            transformer: torch module of the transformer architecture. See transformer_ori.py
            state_dim: robot state dimension of the environment
            num_queries: number of object queries, ie detection slot. This is the maximal number of objects
                         DETR can detect in a single image. For COCO, we recommend 100 queries.
            aux_loss: True if auxiliary decoding losses (loss at each decoder layer) are to be used.
        """
        super().__init__()
        self.camera_names = camera_names
        self.action_head = nn.Linear(1000, state_dim) # TODO add more
        if backbones is not None:
            self.backbones = nn.ModuleList(backbones)
            backbone_down_projs = []
            for backbone in backbones:
                down_proj = nn.Sequential(
                    nn.Conv2d(backbone.num_channels, 128, kernel_size=5),
                    nn.Conv2d(128, 64, kernel_size=5),
                    nn.Conv2d(64, 32, kernel_size=5)
                )
                backbone_down_projs.append(down_proj)
            self.backbone_down_projs = nn.ModuleList(backbone_down_projs)

            mlp_in_dim = 768 * len(backbones) + 14
            self.mlp = mlp(input_dim=mlp_in_dim, hidden_dim=1024, output_dim=14, hidden_depth=2)
        else:
            raise NotImplementedError

    def forward(self, qpos, image, env_state, actions=None):
        """
        qpos: batch, qpos_dim
        image: batch, num_cam, channel, height, width
        env_state: None
        actions: batch, seq, action_dim
        """
        is_training = actions is not None # train or val
        bs, _ = qpos.shape
        # Image observation features and position embeddings
        all_cam_features = []
        for cam_id, cam_name in enumerate(self.camera_names):
            features, pos = self.backbones[cam_id](image[:, cam_id])
            features = features[0] # take the last layer feature
            pos = pos[0] # not used
            all_cam_features.append(self.backbone_down_projs[cam_id](features))
        # flatten everything
        flattened_features = []
        for cam_feature in all_cam_features:
            flattened_features.append(cam_feature.reshape([bs, -1]))
        flattened_features = torch.cat(flattened_features, axis=1) # 768 each
        features = torch.cat([flattened_features, qpos], axis=1) # qpos: 14
        a_hat = self.mlp(features)
        return a_hat


def mlp(input_dim, hidden_dim, output_dim, hidden_depth):
    if hidden_depth == 0:
        mods = [nn.Linear(input_dim, output_dim)]
    else:
        mods = [nn.Linear(input_dim, hidden_dim), nn.ReLU(inplace=True)]
        for i in range(hidden_depth - 1):
            mods += [nn.Linear(hidden_dim, hidden_dim), nn.ReLU(inplace=True)]
        mods.append(nn.Linear(hidden_dim, output_dim))
    trunk = nn.Sequential(*mods)
    return trunk


def build_encoder(args):
    d_model = args.hidden_dim # 256
    dropout = args.dropout # 0.1
    nhead = args.nheads # 8
    dim_feedforward = args.dim_feedforward # 2048
    num_encoder_layers = args.enc_layers # 4 # TODO shared with VAE decoder
    normalize_before = args.pre_norm # False
    activation = "relu"

    encoder_layer = TransformerEncoderLayer(d_model, nhead, dim_feedforward,
                                            dropout, activation, normalize_before)
    encoder_norm = nn.LayerNorm(d_model) if normalize_before else None
    encoder = TransformerEncoder(encoder_layer, num_encoder_layers, encoder_norm)

    return encoder


def build(args):
    #state_dim = 14 # TODO hardcode
    #state_dim = 2*(7+1)
    #state_dim = (7+2)
    #agibot
    state_dim = 22
    ## if is_done
    #state_dim = 9+1


    # From state
    # backbone = None # from state for now, no need for conv nets
    # From image
    backbones = []
    #backbone = build_backbone(args)
    #backbones.append(backbone)
    for _ in args.camera_names:
        backbone = build_backbone_film(args)
        backbones.append(backbone)


    transformer = build_transformer(args)

    encoder = build_encoder(args)

    print("backbone",args.backbone)
    print(args.use_language)

    model = DETRVAE(
        backbones,
        transformer,
        encoder,
        state_dim=state_dim,
        num_queries=args.num_queries,
        camera_names=args.camera_names,
        use_language=args.use_language,
        use_film="film" in args.backbone,
    )

    n_parameters = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print("number of parameters: %.2fM" % (n_parameters/1e6,))

    return model

def build_cnnmlp(args):
    state_dim = 14 # TODO hardcode

    # From state
    # backbone = None # from state for now, no need for conv nets
    # From image
    backbones = []
    for _ in args.camera_names:
        backbone = build_backbone(args)
        backbones.append(backbone)

    model = CNNMLP(
        backbones,
        state_dim=state_dim,
        camera_names=args.camera_names,
    )

    n_parameters = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print("number of parameters: %.2fM" % (n_parameters/1e6,))

    return model

