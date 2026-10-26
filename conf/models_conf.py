from enum import Enum
from ml_collections import ConfigDict
import os
from pathlib import Path

class ModelType(str, Enum):
    MOCK = 'mock'
    ACT = 'act'
    GR00T_N1 = 'gr00t_n1'
    GR00T_N1_5 = 'gr00t_n1_5'
    GR00T_N1_6 = 'gr00t_n1_6'
    GR00T_N1_7 = 'gr00t_n1_7'
    GR00T_N1_7_EEF = 'gr00t_n1_7_eef'
    XVLA_EEF = 'xvla_eef'
    RDT = 'rdt'
    SMOLVLA = 'smolvla'
    GO1 = 'go1'
    PI0 = 'pi0'
    PI05 = 'pi05'
    PI05_PYTORCH = 'pi05_pytorch'
    TAO = 'tao'
    DM05 = 'dm05'
    WALLX = 'wallx'

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

def get_gr00t_1_7_config():
    """Generate configuration for the GR00T N1.7 model.

    N1.7 removed the A2D embodiment tag; finetuned A2D checkpoints register
    under the 'new_embodiment' tag, so reusing ``get_gr00t_config()`` (which
    sets ``embodiment_tag='a2d'``) would fail ``EmbodimentTag.resolve``.

    Returns:
        ConfigDict: Configuration dictionary containing model path for GR00T N1.7.
    """
    config = ConfigDict()
    config.model_path = '/path/to/model'
    config.embodiment_tag = 'new_embodiment'
    config.denoising_steps = 4
    return config



def _get_a2d_eef_config():
    config = ConfigDict()
    config.model_path = '/path/to/model'
    config.ref_frame = 'world'
    config.joint_action_key = {
        'left_arm': [0, 9], 'right_arm': [9, 18],
        'left_hand': [18, 19], 'right_hand': [19, 20],
    }
    config.joint_state_key = {
        'left_arm': [0, 7], 'right_arm': [7, 14],
        'left_hand': [14, 15], 'right_hand': [15, 16],
    }
    config.link_name = {
        'left_base': 'base_link_l', 'left_tip': 'gripper_center',
        'right_base': 'base_link_r', 'right_tip': 'right_gripper_center',
    }
    config.q_left_init = [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869]
    config.q_right_init = [1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873]
    # Full URDF order: body, left arm/hand, right arm/hand, head.
    config.reset_position = (
        [0.19999335706233978, 0.2967000901699066]
        + config.q_left_init + [0.0] * 8
        + config.q_right_init + [0.0] * 8
        + [0.0, 0.4362976849079132]
    )
    return config


def get_gr00t_n1_7_eef_config():
    config = _get_a2d_eef_config()
    config.embodiment_tag = 'new_embodiment'
    config.urdf_path = str(
        Path(__file__).resolve().parents[1]
        / 'server/utils/eef_utils/urdf/a2d_vla_zero_state.urdf'
    )
    config.rotation_type = 'rot6d'
    config.rot6d_convention = 'rows'
    return config


def get_xvla_eef_config():
    config = _get_a2d_eef_config()
    config.eef_action_key = config.joint_action_key
    config.urdf_path = str(
        Path(__file__).resolve().parents[1]
        / 'server/utils/eef_utils/urdf/a2d_vla_zero_state.urdf'
    )
    config.rotation_type = 'rot6d'
    config.rot6d_convention = 'rows'
    config.domain_id = 0  # task_261 checkpoint
    config.denoising_steps = 10
    config.ik = ConfigDict()
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
    config.root_path = '/path/to/root'
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


def get_pi05_pytorch_config():
    """PyTorch pi0.5 with the training config from pi05_base."""
    config = ConfigDict()
    config.config = 'pi05_a2d'
    config.model_path = '/path/to/model'  # Contains model.safetensors and assets/.
    config.compile_mode = 'max-autotune'  # Options: None (off, no quotes), 'default', 'reduce-overhead', 'max-autotune', 'max-autotune-no-cudagraphs'.
    config.execute_horizon = 50
    return config


def get_tao_config():
    """Generate configuration for TAO model.
    
    Returns:
        ConfigDict: Configuration dictionary containing model path for TAO.
    """
    config = ConfigDict()
    config.model_path = '/path/to/model'
    config.embodiment_tag = 'ti5_gripper'
    return config

def get_dm05_config():
    """Generate configuration for the DM0.5 (OpenDM) model.

    Returns:
        ConfigDict: Configuration dictionary for the DM05 in-process policy.
    """
    config = ConfigDict()
    config.model_path = '/path/to/model'
    config.repo_path = '/path/to/repo'
    config.action_mode = 'absolute' # relative | absolute
    config.backend = 'fast'  # 'fast' | 'default' | 'compile'
    config.vision_trt_engine_path = '/path/to/dm05_vision.engine'
    config.diffusion_steps = 10
    config.vision_attn_implementation = 'flash_attention_2'
    config.execute_horizon = 16  # steps actually sent to the robot per cycle
    return config


def get_wallx_config():
    config = ConfigDict()
    config.model_path = '/path/to/model'
    config.repo_path = str(Path(__file__).resolve().parents[2] / 'wall-x')
    config.embodiment_tag = 'a2d_gripper'
    config.device = 'cuda:0'
    config.flow_steps = 10
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
    config.gr00t1_7 = get_gr00t_1_7_config()
    config.gr00t_n1_7_eef = get_gr00t_n1_7_eef_config()
    config.xvla_eef = get_xvla_eef_config()
    config.act = get_act_config()
    config.rdt = get_rdt_config()
    config.go1 = get_go1_config()
    config.smolvla = get_smolvla_config()
    config.pi0 = get_pi0_config()
    config.pi05 = get_pi05_config()
    config.pi05_pytorch = get_pi05_pytorch_config()
    config.tao = get_tao_config()
    config.dm05 = get_dm05_config()
    config.wallx = get_wallx_config()
    return config
