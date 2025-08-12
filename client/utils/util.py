import time
import logging
from functools import wraps
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.console import Group

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
        start_time = time.perf_counter()  # Record the start time
        result = func(*args, **kwargs)  # Call the function
        end_time = time.perf_counter()  # Record the end time
        elapsed_time = end_time - start_time  # Calculate the elapsed time
        # Do not uncomment, too much data output affects debugging
        logger.info(f"Function {func.__name__} called and took {elapsed_time*1000:.4f} milliseconds to execute.")
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
        info (dict): Dictionary containing various information sections including:
                    - config_info: Configuration parameters
                    - ctrl_info: Control information
                    - obs_act_info: Observation and action information
                    - robot_current_state: Current robot state
                    - robot_current_action: Current robot action
                    - debug_info: Debug information
        terminal_size: Rich Console size object containing width and height,
                      used for dynamic layout sizing. If None, uses fixed heights.
                    
    Returns:
        Panel: Rich panel containing the complete layout with adaptive sizing
    """
    row_layout = Layout()
    col_layout = Layout()
    print_info = ''
    for key, value in info.items():
        if key in ['infer_count', 'avg_infer_time', 'avg_traj_time']:
            print_info += f'{key:>1}: {value}\n'
    config_info = ''
    for key, value in info.get('config_info', {}).items():
        config_info += f'{key:>1}: {value}\n'
    ctrl_info = ''
    for key, value in info.get('ctrl_info', {}).items():
        ctrl_info += f'{key:>1}: {value}\n'
    obs_act_info = ''
    for key, value in info.get('obs_act_info', {}).items():
        obs_act_info += f'{key:>1}: {value}\n'
    debug_info = info.get('debug_info', None) 
    # Get robot status and command data
    robot_current_state = info.get('robot_current_state', [0.0] * 16)
    robot_current_action = info.get('robot_current_action', [0.0] * 16)
    
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
    
    status_text = format_robot_data(robot_current_state, 'STATUS')
    command_text = format_robot_data(robot_current_action, 'COMMAND')
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
    
    col_layout.split_row(
        Layout(Panel(ctrl_info, subtitle='', subtitle_align='center', height=col_height)),
        Layout(Panel(config_info, subtitle='', subtitle_align='center', height=col_height)),
        Layout(Panel(obs_act_info, subtitle='', subtitle_align='center', height=col_height)),
    )
    row_layout.split_column(
        col_layout,
        Layout(Panel(print_info, subtitle='Inference Stats', subtitle_align='right', height=stats_height)),
        Layout(Panel(robot_status_text, subtitle='Robot Status', subtitle_align='right', height=robot_height)),
        Layout(Panel(f'{debug_info}', subtitle='Debug Info', subtitle_align='right', height=debug_height)),
        # Layout(Panel('Press Enter for commands', subtitle='Command', subtitle_align='right', height=command_height)),
    )
    return Panel(row_layout, title='VLA Client (Press Enter for commands)', title_align='center', height=total_panel_height)
