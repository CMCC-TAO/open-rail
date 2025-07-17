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
        # 不要取消注释，打印太多数据，影响调试
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
    # 创建一个空列表，用于存储关节块
    joint_chunks = []
    # 获取动作块的维度
    action_dim = len(action_chunk[0])
    # 遍历动作块的维度，创建一个空列表，用于存储每个关节块
    for index in range(action_dim):
        joint_chunks.append([])
    
    # 遍历动作块，将每个动作的每个维度添加到对应的关节块中
    for action in action_chunk:
        for index in range(action_dim):
            joint_chunks[index].append(action[index])
    # 返回关节块
    return joint_chunks

def get_closest_index(candidates, target):
    """Returns the index of the closest element in a list to a target value. The element is preferred to be float value

    Args:
        candidates (list): The list of candidate elements.
        target (float): The target value.

    Returns:
        int: The index of the closest element.
    """
    # 计算每个元素与目标值的差值的绝对值
    differences = [abs(candidate - target) for candidate in candidates]
    # 找到最小差值的索引
    closest_index = differences.index(min(differences))
    return closest_index

def command_prompt(info: dict):
    from rich.table import Table
    # from rich.console import Console

    # console = Console()
    table = Table(title="VLA Inference Framework")

    # table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("key", style="magenta")
    table.add_column("value", style="green")

    for key, value in info.items():
        table.add_row(key, str(value))

    # table.add_row("1", "张三", "在线")
    # table.add_row("2", "李四", "离线")
    # table.add_row("3", "王五", "[bold red]异常[/bold red]")

    # console.print(table)
    return table

    # print(f'Press Enter to input command: ', end='\n', flush=True)
    # print(f'\treset: make the robot go to the initial position', end='\n', flush=True)
    # print(f'\t save: save the current data as a new episode', end='\n', flush=True)
    # print(f'\t  run: continue to inference and control', end='\n', flush=True)
    # print(f'\t exit: exit the program', end='\n', flush=True)

def create_layout(info: dict):
    row_layout = Layout()
    col_layout = Layout()
    # panels = []
    print_info = ''
    for key, value in info.items():
        if key in ['infer_count', 'avg_infer_time', 'avg_traj_time']:
        # panels.append(Layout(Panel(f'{key}: {value}', title=''))),
            print_info += f'{key:>15}: {value}\n'
    debug_info = info.get('debug_info', None) 

    # table = Table(title="Metrics")
    # table.add_column("Param")
    # table.add_column("Value")
    # table.add_column("Param")
    # table.add_column("Value")
    # table.add_row('fps', '30', 'period', '5ms')
    key_param_panels = [
        Panel(print_info, subtitle='', subtitle_align='center'),
        Panel(print_info, subtitle='', subtitle_align='center'),
        Panel(print_info, subtitle='', subtitle_align='center'),
    ]

    key_param_columns = Columns(key_param_panels, title='VLA Client', equal=True, expand=True)
    col_layout.split_row(
        # Layout(key_param_columns, ratio=1),
        Layout(Panel(print_info, subtitle='', subtitle_align='center', height=8)),
        Layout(Panel(print_info, subtitle='', subtitle_align='center', height=8)),
        Layout(Panel(print_info, subtitle='', subtitle_align='center', height=8)),
    )
    cmd_text = info.get('cmd_key', '')
    row_layout.split_column(
    # group = Group(
        col_layout,
        Layout(Panel(print_info, subtitle='Inference Stats', subtitle_align='right', height=8)),
        Layout(Panel(f'STATUS\n\t Left--Arm: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], Gripper: [0.0]\n\tRight--Arm: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], Gripper: [0.0]\nCOMMAND\n\t Left--Arm: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], Gripper: [0.0]\n\tRight--Arm: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], Gripper: [0.0]', subtitle='Robot Status', subtitle_align='right', height=9)),
        Layout(Panel(f'{debug_info}', subtitle='Debug Info', subtitle_align='right', height=8)),
        Layout(Panel(f'Please input command and press Enter to execute: {cmd_text}\n\treset: make the robot go to the initial position\n\t save: save the current data as a new episode\n\t  run: continue to inference and control\n\t exit: exit the program', subtitle='Command Prompt', subtitle_align='right', height=8)),
        # fit=False
        # *panels,
    )
    return Panel(row_layout, title='VLA Client', title_align='center', height=44)

# title="Status",
#     subtitle="Updated: now",
#     title_align="left",
#     subtitle_align="right",
#     border_style="bold cyan",
#     box=box.ROUNDED,
#     padding=(1, 2)