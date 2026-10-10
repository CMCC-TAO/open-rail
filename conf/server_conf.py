from enum import Enum
from ml_collections import ConfigDict
from conf.zmq_conf import get_vla_zmq_config, get_vis_zmq_config
from conf.models_conf import get_models_config

def get_vla_server_config():
    """Generate configuration for VLA inference server.
    
    This function creates configuration settings for the VLA inference server,
    including ZMQ communication settings, worker thread configuration, and
    model configurations.

    Returns:
        ConfigDict: Configuration dictionary for the server containing:
            - zmq: ZMQ communication configuration
            - max_workers: Maximum number of inference worker threads
            - models: Model configuration settings
            - image_pad_and_resize: Whether to pad and resize decoded images
            - image_target_height/image_target_width: Target image dimensions in pixels
    """
    config = ConfigDict()
    config.zmq = get_vla_zmq_config()
    config.max_infer_workers = 3  # Maximum inference worker threads, 1 means no concurrent inference support
    config.max_decode_workers = 9  # Maximum inference worker threads, 1 means no concurrent inference support
    config.image_pad_and_resize = False  # Enable aspect-ratio-preserving padding and resizing
    config.image_target_height = 640
    config.image_target_width = 640
    config.models = get_models_config()
    return config


def get_vis_server_config():
    """Generate configuration for VLA inference server.
    
    This function creates configuration settings for the VLA inference server,
    including ZMQ communication settings, worker thread configuration, and
    model configurations.

    Returns:
        ConfigDict: Configuration dictionary for the server containing:
            - zmq: ZMQ communication configuration
            - max_workers: Maximum number of inference worker threads
            - models: Model configuration settings
    """
    config = ConfigDict()
    config.zmq = get_vis_zmq_config()
    return config
