from enum import Enum
from ml_collections import ConfigDict

# 定义模型类型的枚举类
class ModelType(str, Enum):
    ACT = 'act'
    GR00T_N1 = 'gr00t_n1'
    GR00T_N1_5 = 'gr00t_n1_5'
    RDT = 'rdt'
    SMOLVLA = 'smolvla'

def get_gr00t_config():
    config = ConfigDict()
    # config.model_path = "/home/robot/Downloads/pickbottle_499_chunk64_20250507_192258_b24/checkpoint-60000"
    # config.model_path = '/home/gaohan/Code/VLA/models/GR00TN1.5/pickbottle_184_1000_20250630_161111_n4_b64_s60000/checkpoint-60000'
    config.model_path = '/home/robot/Desktop/checkpoint-30000'
    return config

def get_act_config():
    config = ConfigDict()
    config.model_path = '/media/gaohan/Elements/act_model/save_model_milk_minmax_195_arms_pad/policy_best.ckpt'
    return config

def get_rdt_config():
    config = ConfigDict()
    config.model_path = '/media/gaohan/Elements1/rdt1Bft-a2d-pnpstd-aftAgiBot/'
    config.config_path = '/home/gaohan/Code/VLA/zhaolei/zl/server/models/rdt/rdt_train_a2d/configs/base.yaml'
    config.vision_encoder_name_or_path = '/media/gaohan/Elements1/rdt1Bft-a2d-pnpstd-aftAgiBot/'
    config.lang_embd_path = '/media/gaohan/Elements1/weights/lang_embds/place_bottle.pt'
    return config

def get_models_config():
    config = ConfigDict()
    config.type = ModelType.GR00T_N1_5
    config.gr00t = get_gr00t_config()
    config.act = get_act_config()
    config.rdt = get_rdt_config()
    return config
