from enum import Enum
from ml_collections import ConfigDict
import os

class ModelType(str, Enum):
    MOCK = 'mock'
    ACT = 'act'
    GR00T_N1 = 'gr00t_n1'
    GR00T_N1_5 = 'gr00t_n1_5'
    GR00T_N1_6 = 'gr00t_n1_6'
    RDT = 'rdt'
    SMOLVLA = 'smolvla'
    GO1 = 'go1'
    PI0 = 'pi0'
    PI05 = 'pi05'
    TAO = 'tao'

def get_mock_config():
    """Generate configuration for MOCK model.
    
    Returns:
        ConfigDict: Configuration dictionary containing model path for MOCK.
    """
    config = ConfigDict()
    config.model_path = '/path/to/model'
    return config

def get_gr00t_config():
    """Generate configuration for GR00T model.
    
    Returns:
        ConfigDict: Configuration dictionary containing model path for GR00T.
    """
    config = ConfigDict()
    config.model_path = '/path/to/model'
    config.embodiment_tag = 'a2d'
    config.data_config_key = 'a2d_arms_only'
    return config

def get_act_config():
    """Generate configuration for ACT model.
    
    Returns:
        ConfigDict: Configuration dictionary containing model path for ACT.
    """
    config = ConfigDict()
    config.model_path = '/path/to/model'
    return config

def get_rdt_config():
    """Generate configuration for RDT model.
    
    Returns:
        ConfigDict: Configuration dictionary containing paths for RDT model, config file, vision encoder, and language embeddings.
    """
    config = ConfigDict()
    config.model_path = '/path/to/model'
    config.config_path = '/path/to/config'
    config.vision_encoder_name_or_path = '/path/to/vision_encoder'
    config.lang_embd_path = '/path/to/lang_embds/place_bottle.pt'
    return config

def get_smolvla_config():
    """Generate configuration for RDT model.
    
    Returns:
        ConfigDict: Configuration dictionary containing paths for RDT model, config file, vision encoder, and language embeddings.
    """
    config = ConfigDict()
    config.model_path = '/path/to/model'
    config.root_path = '/home/rm/wxz/EmbodiedAI/vla_infer_remote/vla_infer/model/checkpoint_5w5/055000/data'
    return config

def get_go1_config():
    cfg = ConfigDict()
    cfg.model_path = "/path/to/model"      # 权重目录

    cfg.exp_path   = "/path/to/exppath" #  能 import evaluate.deploy
    cfg.data_stats_path = cfg.data_stats_path = os.path.join(cfg.model_path, "dataset_stats.json")                  
    return cfg

def get_pi0_config():
    """Generate configuration for pi model.
    
    Returns:
        ConfigDict: Configuration dictionary containing model path for pi.
    """
    config = ConfigDict()
    config.config = 'pi0_a2d'
    config.model_path = '/path/to/model'
    config.is_hand = False
    return config


def get_pi05_config():
    """Generate configuration for pi model.
    
    Returns:
        ConfigDict: Configuration dictionary containing model path for pi.
    """
    config = ConfigDict()
    config.config = 'pi05_a2d'
    config.model_path = '/path/to/model'
    config.is_hand = False
    return config


def get_tao_config():
    """Generate configuration for TAO model.
    
    Returns:
        ConfigDict: Configuration dictionary containing model path for TAO.
    """
    config = ConfigDict()
    config.model_path = '/path/to/model'
    config.embodiment_tag = 'Ti5'

    return config

def get_models_config():
    """Generate configuration for all available VLA models.
    
    This function creates a comprehensive configuration dictionary that includes
    settings for all supported VLA models (GR00T, ACT, RDT) and specifies
    which model type to use by default.
    
    Returns:
        ConfigDict: Configuration dictionary containing:
            - type: Default model type to use
            - gr00t: GR00T model configuration
            - act: ACT model configuration  
            - rdt: RDT model configuration
    """
    config = ConfigDict()
    config.type = ModelType.GR00T_N1_5
    config.mock = get_mock_config()
    config.gr00t = get_gr00t_config()
    config.act = get_act_config()
    config.rdt = get_rdt_config()
    config.go1 = get_go1_config()
    config.smolvla = get_smolvla_config()
    config.pi0 = get_pi0_config()
    config.pi05 = get_pi05_config()
    config.tao = get_tao_config()
    return config
