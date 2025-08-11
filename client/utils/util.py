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

def create_layout(info: dict):
    """Create a rich layout for displaying VLA client information.
    
    Args:
        info (dict): Dictionary containing various information sections including:
                    - config_info: Configuration parameters
                    - ctrl_info: Control information
                    - obs_act_info: Observation and action information
                    - data_info: Data state information
                    - robot_current_state: Current robot state
                    - robot_current_action: Current robot action
                    - debug_info: Debug information
                    - cmd_key: Current command key input
                    
    Returns:
        Panel: Rich panel containing the complete layout
    """
    row_layout = Layout()
    col_layout = Layout()
    print_info = ''
    for key, value in info.items():
        if key in ['infer_count', 'avg_infer_time', 'avg_traj_time']:

            print_info += f'{key:>15}: {value}\n'
    config_info = ''
    for key, value in info.get('config_info', {}).items():
        config_info += f'{key:>25}: {value}\n'
    ctrl_info = ''
    for key, value in info.get('ctrl_info', {}).items():
        ctrl_info += f'{key:>25}: {value}\n'
    obs_act_info = ''
    for key, value in info.get('obs_act_info', {}).items():
        obs_act_info += f'{key:>25}: {value}\n'
    debug_info = info.get('debug_info', None) 


    key_param_panels = [
        Panel(print_info, subtitle='', subtitle_align='center'),
        Panel(print_info, subtitle='', subtitle_align='center'),
        Panel(print_info, subtitle='', subtitle_align='center'),
    ]

    key_param_columns = Columns(key_param_panels, title='VLA Client', equal=True, expand=True)
    col_layout.split_row(

        Layout(Panel(ctrl_info, subtitle='', subtitle_align='center', height=8)),
        Layout(Panel(config_info, subtitle='', subtitle_align='center', height=8)),
        Layout(Panel(obs_act_info, subtitle='', subtitle_align='center', height=8)),
    )
    cmd_text = info.get('cmd_key', '')
    
    # Get current state and prompt information
    cmd_current_state = info.get('data_info', {}).get('cmd_current_state', 'normal')
    prompt_text = ''
    
    default_prompt_text = f'Please input command and press Enter to execute: {cmd_text}\n\treset: reset robot to initial position\n\tlang: modify language instruction\n\tsave: save current data\n\tdelete: delete current data\n\tquit: exit program'
    if cmd_current_state == 'waiting_command':
        prompt_text = default_prompt_text
    elif cmd_current_state == 'waiting_language':
        preset_languages = info.get('data_info', {}).get('preset_languages', [])
        preset_list = ''
        if preset_languages:
            preset_list = '\n\tPreset Instructions:'
            for i, lang in enumerate(preset_languages, 1):
                preset_list += f'\n\t  {i}. {lang}'
        prompt_text = f'Please input new language instruction and press Enter: {cmd_text}{preset_list}\n\tEnter number (1-{len(preset_languages)}) for preset or type custom instruction'
    elif cmd_current_state == 'waiting_continue':
        prompt_text = f'Robot reset completed, press "con" + Enter to continue: {cmd_text}'
    elif cmd_current_state == 'waiting_save':
        prompt_text = f'Data saved successfully. Press "con" + Enter to continue: {cmd_text}'
    elif cmd_current_state == 'waiting_delete':
        prompt_text = f'Data deleted successfully. Press "con" + Enter to continue: {cmd_text}'
    elif cmd_current_state == 'paused':
        prompt_text = default_prompt_text
    else:
        prompt_text = default_prompt_text
    
    # Get robot status and command data
    robot_current_state = info.get('robot_current_state', [0.0] * 16)
    robot_current_action = info.get('robot_current_action', [0.0] * 16)
    
    # Format status and command display
    def format_robot_data(data, label):
        if len(data) >= 16:
            left_arm = [f'{x:.3f}' for x in data[:7]]
            right_arm = [f'{x:.3f}' for x in data[7:14]]
            left_gripper = f'{data[14]:.3f}' if len(data) > 14 else '0.000'
            right_gripper = f'{data[15]:.3f}' if len(data) > 15 else '0.000'
            return f"{label}\n\t Left--Arm: [{', '.join(left_arm)}], Gripper: [{left_gripper}]\n\tRight--Arm: [{', '.join(right_arm)}], Gripper: [{right_gripper}]"
        else:
            return f'{label}\n\tData not available or incomplete'
    
    status_text = format_robot_data(robot_current_state, 'STATUS')
    command_text = format_robot_data(robot_current_action, 'COMMAND')
    robot_status_text = f'{status_text}\n{command_text}'
    
    row_layout.split_column(
        col_layout,
        Layout(Panel(print_info, subtitle='Inference Stats', subtitle_align='right', height=8)),
        Layout(Panel(robot_status_text, subtitle='Robot Status', subtitle_align='right', height=8)),
        Layout(Panel(f'{debug_info}', subtitle='Debug Info', subtitle_align='right', height=8)),
        Layout(Panel(prompt_text, subtitle='Command Prompt', subtitle_align='right', height=10)),
    )
    return Panel(row_layout, title='VLA Client', title_align='center', height=48)
