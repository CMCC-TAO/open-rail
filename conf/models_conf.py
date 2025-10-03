from enum import Enum
from ml_collections import ConfigDict

class ModelType(str, Enum):
    ACT = 'act'
    GR00T_N1 = 'gr00t_n1'
    GR00T_N1_5 = 'gr00t_n1_5'
    RDT = 'rdt'
    SMOLVLA = 'smolvla'

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
        ConfigDict: Configuration dictionary containing paths for RDT model,
                   config file, vision encoder, and language embeddings.
    """
    config = ConfigDict()
    config.model_path = '/path/to/model'
    config.config_path = '/path/to/config'
    config.vision_encoder_name_or_path = '/path/to/vision_encoder'
    config.lang_embd_path = '/path/to/lang_embds/place_bottle.pt'
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
    config.gr00t = get_gr00t_config()
    config.act = get_act_config()
    config.rdt = get_rdt_config()
    return config
