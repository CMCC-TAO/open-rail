import time
from functools import wraps

def run_time_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Record the start time
        result = func(*args, **kwargs)  # Call the function
        end_time = time.time()  # Record the end time
        elapsed_time = end_time - start_time  # Calculate the elapsed time
        # print(f"Function {func.__name__} called and took {elapsed_time*1000:.4f} milliseconds to execute.")
        return result
    return wrapper
