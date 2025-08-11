import time
import argparse
from conf.models_conf import ModelType
from conf.server_conf import get_server_config
from server.core.vla_server import VLAServer
from server.core.zmq_server import ZMQServer

def get_model(config):
    """Create and return a VLA model instance based on configuration
    
    Args:
        config: Configuration object containing model type and settings
        
    Returns:
        ModelVLA: VLA model instance for the specified type
        
    Raises:
        ValueError: If model type is not supported
    """
    if config.type == ModelType.ACT:
        from server.models.act import ModelVLA as ACT
        return ACT(config.act)
    elif config.type == ModelType.GR00T_N1:
        from server.models.gr00t.gr00t_n1 import ModelVLA as GR00T_N1
        return GR00T_N1(config.gr00t)
    elif config.type == ModelType.GR00T_N1_5:
        from server.models.gr00t.gr00t_n1_5 import ModelVLA as GR00T_N1_5
        return GR00T_N1_5(config.gr00t)
    elif config.type == ModelType.RDT:
        from server.models.rdt import ModelVLA as RDT
        return RDT(config.rdt)
    elif config.type == ModelType.SMOLVLA:
        from server.models.smolvla import ModelVLA as SMOLVLA
        return SMOLVLA()
    else:
        raise ValueError("Invalid model type")

def parse_args():
    """Parse command line arguments for VLA Server
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='VLA Server')
    
    # Keep only the most commonly used parameters
    parser.add_argument('--model_type', type=str, choices=['act', 'gr00t_n1', 'gr00t_n1_5', 'rdt', 'smolvla'],
                       help='Model type to use for inference')
    parser.add_argument('--model_path', type=str, help='Path to the model checkpoint')
    
    return parser.parse_args()

def override_config_with_args(config, args):
    """Override configuration with command line arguments
    
    Args:
        config: Original configuration object
        args: Command line arguments
    
    Returns:
        config: Updated configuration object
    """
    # Override model type
    if args.model_type:
        config.models.type = ModelType(args.model_type)
    
    # Override model path
    if args.model_path:
        if config.models.type == ModelType.GR00T_N1 or config.models.type == ModelType.GR00T_N1_5:
            config.models.gr00t.model_path = args.model_path
        elif config.models.type == ModelType.ACT:
            config.models.act.model_path = args.model_path
        elif config.models.type == ModelType.RDT:
            config.models.rdt.model_path = args.model_path
    
    return config

if __name__ == "__main__":
    """Main entry point for VLA Server
    
    This script initializes and runs the VLA server with the specified
    configuration and model type.
    """
    args = parse_args()
    # Get default configuration
    config = get_server_config()
    config = override_config_with_args(config, args)
    
    # Initialize server components
    zmq_server = ZMQServer(config.zmq)
    model = get_model(config.models)
    vla_server = VLAServer(config, zmq_server, model)
    
    try:
        # Run server
        print(f"Starting VLA Server with model type: {config.models.type}")
        vla_server.run()
    except KeyboardInterrupt:
        print("Program interrupted")
    finally:
        vla_server.close()
