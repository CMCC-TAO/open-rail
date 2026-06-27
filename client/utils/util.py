import time
import logging
import os
import importlib.util
from functools import wraps
from rich.layout import Layout
from rich.panel import Panel

logger = logging.getLogger(__name__)
def run_time_decorator(func):
    """Decorator to measure the execution time of a function.

    Args:
        func (func): The function to be decorated.

    Returns:
        func: The decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        bound_logger = logger
        if args:
            instance_logger = getattr(args[0], "logger", None)
            if isinstance(instance_logger, logging.Logger):
                bound_logger = instance_logger

        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception:
            bound_logger.exception(f"{func.__name__} failed")
            raise

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        bound_logger.info(f"{func.__name__} takes {elapsed_time*1000:.4f} milliseconds to execute.")
        return result
    return wrapper

def action_chunk_2_joint_chunk(action_chunk):
    """Converts an action chunk to a joint chunk.

    Args:
        action_chunk (list): The action chunk to convert with format [action_1, action_2, ..., action_n], action_n is the n-th frame of action with format [joint_1, joint_2, ..., joint_n]

    Returns:
        list: The converted joint chunk with format [joint_1_chunk, joint_2_chunk, ..., joint_n_chunk]
    """
    # Create an empty list to store joint chunks
    joint_chunks = []
    # Get the dimension of the action chunk
    action_dim = len(action_chunk[0])
    # Iterate through action chunk dimensions, create empty list for each joint chunk
    for index in range(action_dim):
        joint_chunks.append([])
    
    # Iterate through action chunk, add each dimension of each action to corresponding joint chunk
    for action in action_chunk:
        for index in range(action_dim):
            joint_chunks[index].append(action[index])
    # Return joint chunks
    return joint_chunks

def get_closest_index(candidates, target):
    """Returns the index of the closest element in a list to a target value. The element is preferred to be float value

    Args:
        candidates (list): The list of candidate elements.
        target (float): The target value.

    Returns:
        int: The index of the closest element.
    """
    # Calculate the absolute difference between each element and the target value
    differences = [abs(candidate - target) for candidate in candidates]
    # Find the index of the minimum difference
    closest_index = differences.index(min(differences))
    return closest_index

def load_user_config(user_conf_path):
    """Load user configuration from specified file
    
    Args:
        user_conf_path (str): Path to user configuration file
        
    Returns:
        dict: User configuration dictionary, or None if loading fails
    """
    if not os.path.exists(user_conf_path):
        print(f"Warning: User configuration file not found: {user_conf_path}")
        return None
    
    try:
        # Load the module dynamically
        spec = importlib.util.spec_from_file_location("user_config", user_conf_path)
        user_config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_config_module)
        
        # Get the user configuration function
        if hasattr(user_config_module, 'get_user_config'):
            user_config = user_config_module.get_user_config()
            print(f"Successfully loaded user configuration from: {user_conf_path}")
            return user_config
        else:
            print(f"Warning: No 'get_user_config' function found in {user_conf_path}")
            return None
            
    except Exception as e:
        print(f"Error loading user configuration from {user_conf_path}: {e}")
        return None

def apply_user_config(config, user_config):
    """Apply user configuration to the main config object with support for nested configurations
    
    Args:
        config: Main configuration object (ConfigDict)
        user_config (dict): User configuration dictionary
        
    Returns:
        config: Updated configuration object
    """
    if user_config is None:
        return config
    
    def _apply_nested_config(target_config, nested_config, path=""):
        """Recursively apply nested configuration
        
        Args:
            target_config: Target configuration object to update
            nested_config: Nested configuration dictionary to apply
            path: Current configuration path for logging
        """
        for key, value in nested_config.items():
            current_path = f"{path}.{key}" if path else key
            
            if hasattr(target_config, key):
                current_attr = getattr(target_config, key)
                
                # If both are dictionaries/ConfigDict, recursively apply
                if isinstance(value, dict) and hasattr(current_attr, '__dict__'):
                    print(f"Applying nested config at: {current_path}")
                    _apply_nested_config(current_attr, value, current_path)
                else:
                    # Handle special cases for type conversion
                    try:
                        # For enum types, try to convert string to enum
                        if hasattr(current_attr, '__class__') and hasattr(current_attr.__class__, '__bases__'):
                            # Check if it's an enum type
                            if any('Enum' in str(base) for base in current_attr.__class__.__bases__):
                                if isinstance(value, str):
                                    # Try to find the enum value
                                    enum_class = current_attr.__class__
                                    if hasattr(enum_class, value.upper()):
                                        value = getattr(enum_class, value.upper())
                                    elif hasattr(enum_class, value):
                                        value = getattr(enum_class, value)
                                    else:
                                        # Try to find by value
                                        for enum_item in enum_class:
                                            if enum_item.value == value:
                                                value = enum_item
                                                break
                        
                        # Direct value assignment
                        setattr(target_config, key, value)
                        print(f"Applied user config: {current_path} = {value}")
                    except Exception as e:
                        print(f"Warning: Failed to apply config '{current_path}' = {value}: {e}")
            else:
                print(f"Warning: Unknown configuration key '{current_path}' in user config")
    
    _apply_nested_config(config, user_config)
    
    return config

def parse_action_layout(action_layout):
    """
    Parses the action layout.

    Args:
        action_layout (dict): A dictionary describing the action layout.
            Example: {'arm': {'start': 0, 'end': 7, 'policy': 'gradual'}, 'gripper': {'start': 7, 'end': 8, 'policy': 'stepwise'}}

    Returns:
        tuple[int, list[int], list[int]]: A tuple containing:
            - action_dim (int): The total dimension of the action space.
            - gradual_indices (list[int]): Action indices for the 'gradual' policy.
            - stepwise_indices (list[int]): Action indices for the 'stepwise' policy.
    """
    action_dim = max([v['end'] for v in action_layout.values()]) if action_layout else 0
    gradual_indices, stepwise_indices = [], []
    for v in action_layout.values():
        if v['policy'] == 'gradual':
            gradual_indices.extend(range(v['start'], v['end']))
        elif v['policy'] == 'stepwise':
            stepwise_indices.extend(range(v['start'], v['end']))
    return action_dim, gradual_indices, stepwise_indices

def command_prompt(info: dict):
    """Create a command prompt table for VLA inference framework.
    
    Args:
        info (dict): Dictionary containing information to display in the table
        
    Returns:
        Table: Rich table object with the information
    """
    from rich.table import Table

    table = Table(title="VLA Inference Framework")
    table.add_column("key", style="magenta")
    table.add_column("value", style="green")

    for key, value in info.items():
        table.add_row(key, str(value))

    return table

def create_layout(info: dict, terminal_size=None):
    """Create a rich layout for displaying VLA client information.
    
    Args:
        info (dict): Dictionary containing various information sections.
        terminal_size: Rich Console size object containing width and height,
                      used for dynamic layout sizing. If None, uses fixed heights.
                    
    Returns:
        Panel: Rich panel containing the complete layout with adaptive sizing
    """
    row_layout = Layout()
    col_layout1, col_layout2 = Layout(), Layout()
    config, vla_client = info.get('config', {}), info.get('vla_client', None)
    if config is None or vla_client is None:
        return row_layout

    # Format status and command display with terminal width awareness
    def format_robot_data(data, label):
        if len(data) >= 16:
            left_arm = [f'{x:.3f}' for x in data[:7]]
            right_arm = [f'{x:.3f}' for x in data[7:14]]
            left_gripper = f'{data[14]:.3f}' if len(data) > 14 else '0.000'
            right_gripper = f'{data[15]:.3f}' if len(data) > 15 else '0.000'
            
            return f"{label}\n L-Arm: [{', '.join(left_arm)}], L-Grip: [{left_gripper}]\n R-Arm: [{', '.join(right_arm)}], R-Grip: [{right_gripper}]"
        else:
            return f'{label}\n\tData not available or incomplete'
    
    status_text = format_robot_data(vla_client.info_current_state, 'STATUS')
    command_text = format_robot_data(vla_client.info_current_action, 'COMMAND')
    robot_status_text = f'{status_text}\n{command_text}'
    
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
    
    col_layout1_info1 = (
        f"language: {vla_client.language}\n"
        f"record: {config.record.switch}\n"
        f"robots_type: {config.robots.type}\n"
        f"task_progress_threshold: {config.language.task_progress_threshold}\n"
    )
    col_layout1_info2 = (
        f"fps: {config.observer.fps}\n"
        f"wait_time: {config.controller.wait_time}\n"
        f"gripper_offset: {config.controller.gripper_offset}\n"
        f"history_frame: {config.vision.history_frame}\n"
    )
    col_layout1_info3 = (
        f"fps: {config.observer.fps}\n"
        f"fit_num_samples: {config.intra_chunk.fitting_num_samples}\n"
        f"fit_time_step: {config.intra_chunk.fitting_time_step}\n"
    )
    col_layout1.split_row(
        Layout(Panel(col_layout1_info1, subtitle='', subtitle_align='center', height=col_height)),
        Layout(Panel(col_layout1_info2, subtitle='', subtitle_align='center', height=col_height)),
        Layout(Panel(col_layout1_info3, subtitle='', subtitle_align='center', height=col_height)),
    )
    
    col_layout2_info1 = (
        f"infer_count: {vla_client.realtime_data_manager.infer_count}\n"
        f"avg_infer_time: {vla_client.realtime_data_manager.avg_infer_time: .4f}s\n"
        f"avg_intra_traj_time: {vla_client.realtime_data_manager.avg_intra_traj_time: .4f}s\n"
        f"avg_inter_traj_time: {vla_client.realtime_data_manager.avg_inter_traj_time: .4f}s\n"
    )
    obs_act_info = {
        "preprocess": config.vision.preprocess,
        # **vla_client.info_obs,
        # **vla_client.info_act,
    }
    col_layout2_info2 = ''
    for key, value in obs_act_info.items():
        col_layout2_info2 += f'{key:>0}: {value}\n'
    col_layout2.split_row(
        Layout(Panel(col_layout2_info1, subtitle='', subtitle_align='center', height=col_height)),
        Layout(Panel(col_layout2_info2, subtitle='', subtitle_align='center', height=col_height)),
    )

    row_layout.split_column(
        col_layout1,
        col_layout2,
        Layout(Panel(robot_status_text, subtitle='Robot Status', subtitle_align='right', height=robot_height)),
        Layout(Panel(f'{vla_client.debug_info}', subtitle='Debug Info', subtitle_align='right', height=debug_height)),
        # Layout(Panel('Press Enter for commands', subtitle='Command', subtitle_align='right', height=command_height)),
    )
    return Panel(row_layout, title='VLA Client (Press Enter for Commands)', title_align='center', height=total_panel_height)