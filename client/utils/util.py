import time
from functools import wraps

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
        print(f"Function {func.__name__} called and took {elapsed_time*1000:.4f} milliseconds to execute.")
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