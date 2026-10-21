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
    elif config.type == ModelType.GR00T_N1_7_EEF:
        from server.models.gr00t.gr00t_n1_7_eef import ModelVLA as GR00T_N1_7_EEF
        return GR00T_N1_7_EEF(config.gr00t_n1_7_eef)
    elif config.type == ModelType.XVLA_EEF:
        from server.models.xvla.xvla_eef import ModelVLA as XVLA_EEF
        return XVLA_EEF(config.xvla_eef)
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
    elif config.type == ModelType.PI05_PYTORCH:
        from server.models.openpi.pi05_pytorch import ModelVLA as PI05_PYTORCH
        return PI05_PYTORCH(config.pi05_pytorch)
    elif config.type == ModelType.TAO:
        from server.models.tao import ModelVLA as TAO
        return TAO(config.tao)
    elif config.type == ModelType.DM05:
        from server.models.dm05 import ModelVLA as DM05
        return DM05(config.dm05)
    elif config.type == ModelType.WALLX:
        from server.models.wallx import ModelVLA as WallX
        return WallX(config.wallx)
    else:
        raise ValueError("Invalid model type")

def parse_args():
    """Parse command line arguments for VLA Server
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='VLA Server')
    
    # Keep only the most commonly used parameters
    parser.add_argument('--model_type', type=str, choices=['mock', 'act', 'gr00t_n1', 'gr00t_n1_5', 'gr00t_n1_6', 'gr00t_n1_7_eef', 'xvla_eef', 'rdt', 'smolvla','go1', 'pi0', 'pi05', 'pi05_pytorch', 'tao', 'dm05', 'wallx'],
                       help='Model type to use for inference')
    parser.add_argument('--model_path', type=str, help='Path to the model checkpoint')
    parser.add_argument('--embodiment_tag', type=str, help='Model embodiment tag')
    parser.add_argument('--data_config_key', type=str, help='GR00T data configuration key')
    parser.add_argument('--action_keys', nargs='+', help='Explicit TAO action output order')
    parser.add_argument('--video_keys', nargs=3, help='TAO camera keys: head, left wrist, right wrist')
    parser.add_argument('--server_port', type=int, help='Override model service port')
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
        elif config.models.type == ModelType.GR00T_N1_7_EEF:
            config.models.gr00t_n1_7_eef.model_path = args.model_path
            config.image_pad_and_resize = True
        elif config.models.type == ModelType.XVLA_EEF:
            config.models.xvla_eef.model_path = args.model_path
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
        elif config.models.type == ModelType.PI05_PYTORCH:
            config.models.pi05_pytorch.model_path = args.model_path
        elif config.models.type == ModelType.TAO:
            config.models.tao.model_path = args.model_path
        elif config.models.type == ModelType.DM05:
            config.models.dm05.model_path = args.model_path
        elif config.models.type == ModelType.WALLX:
            config.models.wallx.model_path = args.model_path

    if args.embodiment_tag:
        if config.models.type == ModelType.TAO:
            config.models.tao.embodiment_tag = args.embodiment_tag
        elif config.models.type == ModelType.GR00T_N1_5:
            config.models.gr00t.embodiment_tag = args.embodiment_tag
        else:
            raise ValueError(f'{config.models.type.value} does not support --embodiment_tag')
    if args.data_config_key:
        if config.models.type != ModelType.GR00T_N1_5:
            raise ValueError('--data_config_key is only supported by GR00T N1.5')
        config.models.gr00t.data_config_key = args.data_config_key
    if args.action_keys:
        if config.models.type != ModelType.TAO:
            raise ValueError('--action_keys is only supported by TAO')
        config.models.tao.action_keys = args.action_keys

    if getattr(args, 'video_keys', None):
        if config.models.type != ModelType.TAO:
            raise ValueError('--video_keys is only supported by TAO')
        if len(set(args.video_keys)) != 3:
            raise ValueError('--video_keys must contain three distinct keys')
        config.models.tao.video_keys = args.video_keys
    if getattr(args, 'server_port', None) is not None:
        if not 1 <= args.server_port <= 65535:
            raise ValueError('--server_port must be in [1, 65535]')
        config.zmq.port = str(args.server_port)

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
