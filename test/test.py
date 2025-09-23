import threading
import time

def inner_thread_task():
    """Inner thread task that prints current timestamp."""
    print(f"[{time.time()}] Inner thread running...")

def outer_thread_task():
    """Outer thread task that spawns multiple inner threads."""
    print(f"[{time.strftime('%X')}] Outer thread started")
    counter = 0
    while counter < 20:
        start_time = time.time()
        # Start a new thread within the outer thread
        t = threading.Thread(target=inner_thread_task)
        t.start()
        counter += 1
        end_time = time.time()
        time.sleep(max(0, 0.002-end_time+start_time))
    # t.join()
    print(f"[{time.strftime('%X')}] Outer thread finished")

# Main thread starts the outer thread
outer = threading.Thread(target=outer_thread_task)
outer.start()
# outer.join()
print("Main thread finished")