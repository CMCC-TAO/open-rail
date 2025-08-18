import time
import threading
import numpy as np
from rich.layout import Layout
from rich.panel import Panel

def create_layout(info, terminal_size=None):
    """Create a rich layout for displaying VLA server information.
    
    Args:
        vla_server: VLAServer instance
        config: Server configuration
        start_time: Server start time
        terminal_size: Rich Console size object containing width and height,
                      used for dynamic layout sizing. If None, uses fixed heights.
                    
    Returns:
        Panel: Rich panel containing the complete layout with adaptive sizing
    """
    row_layout = Layout()
    col_layout1, col_layout2 = Layout(), Layout()
    config, vla_server, model, start_time = info['config'], info['vla_server'], info['model'], info['start_time']
    if config is None or vla_server is None:
        return row_layout

    def format_robot_data(data, label):
        if len(data) >= 0:
            arr = data.astype(float)
            mask = np.isnan(arr)
            formatted = np.char.mod('%.3f', arr)
            formatted[mask] = 'nan'
            data_str = ''
            for i in range(len(formatted)):
                if i >= 3:
                    break
                data_str += f'{formatted[i]}\n'
            data_str = data_str.replace("'", "")
            return f"{label} {formatted.shape}\n{data_str}"
        else:
            return f'{label}\n\tData not available or incomplete'
    pred_text = format_robot_data(vla_server.act_info.get('pred_action', np.zeros((16, 16))), 'PRED_ACTION_CHUNK')
    
    # Calculate current time and uptime
    current_time = time.time()
    uptime = current_time - start_time
    
    # Calculate dynamic heights based on terminal size
    if terminal_size is not None:
        terminal_height = terminal_size.height
        
        # Special handling for very small terminals
        if terminal_size.height < 20 or terminal_size.width < 60:
            # Minimal layout for small terminals
            col_height = 4
            stats_height = 4
            robot_height = 4
            debug_height = 4
            command_height = 2
            total_panel_height = min(terminal_height - 1, 15)
        else:
            # Reserve space for title, borders, and padding (approximately 2 lines)
            remaining_height = max(terminal_height - 2, 20)
            
            # Distribute remaining height proportionally
            col_height = max(int(remaining_height * 0.25), 6)
            stats_height = max(int(remaining_height * 0.25), 6)
            robot_height = max(int(remaining_height * 0.25), 6)
            debug_height = max(int(remaining_height * 0.25), 5)
            # command_height = max(int(remaining_height * 0.1), 0)
            
            # Adjust total height to fit terminal
            total_panel_height = min(terminal_height - 0, terminal_height)
    else:
        # Fallback to fixed heights if terminal_size is not available
        col_height = 8
        stats_height = 8
        robot_height = 8
        debug_height = 8
        command_height = 3
        total_panel_height = 48

    col_layout2_info1 = (
        f"status: {'Running' if getattr(vla_server, 'running', False) else 'Stopped'}\n"
        f"server_addr: {getattr(config.zmq, 'server_addr', 'N/A')}\n"
        f"language: {vla_server.obs_info.get('language', 'N/A')}\n"
    )
    col_layout2_info2 = (
        f"model_type: {str(config.models.type)}\n"
        f"model_loaded: {'Yes' if hasattr(vla_server, 'model') else 'No'}\n"
        f"model_path: {model.cfg['model_path']}\n"
    )
    col_layout1.split_row(
        Layout(Panel(col_layout2_info1, subtitle='', subtitle_align='center', height=col_height)),
        Layout(Panel(col_layout2_info2, subtitle='', subtitle_align='center', height=col_height)),
    )

    col_layout2_info1 = (
        f"request_count: {vla_server.request_count}\n"
        f"avg_infer_time: {vla_server.avg_inference_time: .4f}s\n"
        f"uptime: {uptime: .4f}s\n"
        f"threads_active: {threading.active_count()}\n"
        f"obs_comm_delay: {vla_server.obs_info.get('obs_comm_delay', 0.0): .4f}s\n"
    )
    col_layout2_info2 = ''
    for key, value in vla_server.obs_info.items():
        if 'language' in key or 'obs_comm_delay' in key:
            continue
        col_layout2_info2 += f"{key}: {value}\n"
    col_layout2.split_row(
        Layout(Panel(col_layout2_info1, subtitle='', subtitle_align='center', height=col_height)),
        Layout(Panel(col_layout2_info2, subtitle='', subtitle_align='center', height=col_height)),
    )

    row_layout.split_column(
        col_layout1,
        col_layout2,
        Layout(Panel(f'{pred_text}', subtitle='Prediction', subtitle_align='right', height=robot_height)),
        Layout(Panel(f'{vla_server.debug_info}', subtitle='Debug Info', subtitle_align='right', height=debug_height)),
        # Layout(Panel('Press Enter for commands', subtitle='Command', subtitle_align='right', height=command_height)),
    )
    return Panel(row_layout, title='VLA Server', title_align='center', height=total_panel_height)
