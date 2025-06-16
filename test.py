import threading
import time

def inner_thread_task():
    print(f"[{time.time()}] 子线程运行中...")

def outer_thread_task():
    print(f"[{time.strftime('%X')}] 外部线程启动")
    counter = 0
    while counter < 20:
        start_time = time.time()
        # 在外部线程中启动一个新线程
        t = threading.Thread(target=inner_thread_task)
        t.start()
        counter += 1
        end_time = time.time()
        time.sleep(max(0, 0.002-end_time+start_time))
    # t.join()
    print(f"[{time.strftime('%X')}] 外部线程结束")

# 主线程启动外部线程
outer = threading.Thread(target=outer_thread_task)
outer.start()
# outer.join()
print("主线程结束")