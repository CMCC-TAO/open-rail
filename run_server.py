import time
import argparse
import threading
from datetime import datetime
from conf.models_conf import ModelType
from conf.server_conf import get_vla_server_config
from server.core.vla_server import VLAServer
from server.core.zmq_server import ZMQServer
from rich.live import Live
from rich.console import Console
from server.utils.util import create_layout

def get_model(config):
    """Create and return a VLA model instance based on configuration
    
    Args:
        config: Configuration object containing model type and settings
        
    Returns:
        ModelVLA: VLA model instance for the specified type
        
    Raises:
        ValueError: If model type is not supported
    """
    if config.type == ModelType.MOCK:
        from server.models.mock.mock import ModelVLA as MOCK
        return MOCK(config.mock)
    elif config.type == ModelType.ACT:
        from server.models.act import ModelVLA as ACT
        return ACT(config.act)
    elif config.type == ModelType.GR00T_N1:
        from server.models.gr00t.gr00t_n1 import ModelVLA as GR00T_N1
        return GR00T_N1(config.gr00t)
    elif config.type == ModelType.GR00T_N1_5:
        from server.models.gr00t.gr00t_n1_5 import ModelVLA as GR00T_N1_5
        return GR00T_N1_5(config.gr00t)
    elif config.type == ModelType.GR00T_N1_6:
        from server.models.gr00t.gr00t_n1_6 import ModelVLA as GR00T_N1_6
        return GR00T_N1_6(config.gr00t)
    elif config.type == ModelType.RDT:
        from server.models.rdt import ModelVLA as RDT
        return RDT(config.rdt)
    elif config.type == ModelType.SMOLVLA:
        from server.models.smolvla import ModelVLA as SMOLVLA
        return SMOLVLA(config.smolvla)
    elif config.type == ModelType.GO1:
        from server.models.go1 import ModelVLA as GO1
        return GO1(config.go1)
    elif config.type == ModelType.PI0:
        from server.models.openpi.pi0 import ModelVLA as PI0
        return PI0(config.pi0)
    elif config.type == ModelType.PI05:
        from server.models.openpi.pi05 import ModelVLA as PI05
        return PI05(config.pi05)
    elif config.type == ModelType.TAO:
        from server.models.tao import ModelVLA as TAO
        return TAO(config.tao)
    elif config.type == ModelType.DM05:
        from server.models.dm05 import ModelVLA as DM05
        return DM05(config.dm05)
    else:
        raise ValueError("Invalid model type")

def parse_args():
    """Parse command line arguments for VLA Server
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='VLA Server')
    
    # Keep only the most commonly used parameters
    parser.add_argument('--model_type', type=str, choices=['mock', 'act', 'gr00t_n1', 'gr00t_n1_5', 'gr00t_n1_6', 'rdt', 'smolvla','go1', 'pi0', 'pi05', 'tao', 'dm05'],
                       help='Model type to use for inference')
    parser.add_argument('--model_path', type=str, help='Path to the model checkpoint')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode, disable Live interface')
    
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
        if config.models.type == ModelType.GR00T_N1 or config.models.type == ModelType.GR00T_N1_5 or config.models.type == ModelType.GR00T_N1_6:
            config.models.gr00t.model_path = args.model_path
        elif config.models.type == ModelType.ACT:
            config.models.act.model_path = args.model_path
        elif config.models.type == ModelType.RDT:
            config.models.rdt.model_path = args.model_path
        elif config.models.type == ModelType.GO1:
            config.models.go1.model_path = args.model_path
        elif config.models.type == ModelType.SMOLVLA:
            config.models.smolvla.model_path = args.model_path
        elif config.models.type == ModelType.PI0:
            config.models.pi0.model_path = args.model_path
        elif config.models.type == ModelType.PI05:
            config.models.pi05.model_path = args.model_path
        elif config.models.type == ModelType.TAO:
            config.models.tao.model_path = args.model_path
        elif config.models.type == ModelType.DM05:
            config.models.dm05.model_path = args.model_path

    return config

def main():
    """Main entry point for VLA Server
    
    This script initializes and runs the VLA server with the specified
    configuration and model type.
    """
    args = parse_args()
    # Get default configuration
    config = get_vla_server_config()
    config = override_config_with_args(config, args)
    
    # Initialize server components
    zmq_server = ZMQServer(config.zmq)
    model = get_model(config.models)
    vla_server = VLAServer(config, zmq_server, model)
    
    try:
        # Start server in a separate thread
        server_thread = threading.Thread(target=vla_server.run, daemon=True)
        server_thread.start()
        print(f"Starting VLA Server with model type: {config.models.type}")
        
        console = Console()
        start_time = time.time()
        live = None
        
        if not args.debug:
            # Rich Live display mode
            live = Live(console=console, refresh_per_second=4)
            live.start()
        else:
            print("Debug mode enabled")
        
        # Main display loop
        while getattr(vla_server, 'running', True):
            try:
                time.sleep(0.1)
                info = {'config': config, 'vla_server': vla_server, 'model': model, 'start_time': start_time}
                
                if live is not None:
                    # Update live display
                    layout = create_layout(info, console.size)
                    live.update(layout)
                elif args.debug:
                    # Debug mode: print simple status
                    uptime = time.time() - start_time
                    print(f"Uptime: {uptime:.1f}s, Infer count: {getattr(vla_server, 'infer_count', 0)}, "
                          f"Avg infer time: {getattr(vla_server, 'avg_inference_time', 0):.4f}s")
                    
            except Exception as e:
                if live is not None:
                    console.print(f"Display error: {e}")
                else:
                    print(f"\nDisplay error: {e}")
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nProgram interrupted")
    finally:
        # Stop Live interface if it was started
        if live is not None:
            live.stop()
        vla_server.close()
        print("Server shutdown complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
