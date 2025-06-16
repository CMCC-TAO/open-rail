import time
import queue
import threading
import numpy as np
import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor
from ruckig import InputParameter, OutputParameter, Result, Ruckig
from ..utils.util import run_time_decorator
class TrajectoryGenerator():
    def __init__(self, config: ConfigDict):
        self.config = config
        self.way_points = queue.Queue(maxsize=config.max_len)
        self.traj_points = queue.Queue(maxsize=config.max_len) # fine generated
        # self.traj_vel = queue.Queue(maxsize=config.max_len) # coarse_generated
        # self.control_action_buffer = deque(maxlen=rdm_config.control_max_len)
        # self.control_timestamp_buffer = deque(maxlen=rdm_config.control_max_len)
        # current_position = waypoints[0]
        self.fine_input_param = InputParameter(config.dof)
        # self.input_param.current_position = current_position
        self.fine_input_param.current_velocity = [0.0] * config.dof
        self.fine_input_param.current_acceleration = [0.0] * config.dof
        self.fine_input_param.max_velocity = config.max_velocity
        self.fine_input_param.max_acceleration = config.max_acceleration
        self.fine_input_param.max_jerk = config.max_jerk
        self.fine_output_param = OutputParameter(config.dof)
        self.fine_ruckig = Ruckig(config.dof, config.fine_interval)

        self.coarse_input_param = InputParameter(config.dof)
        # self.input_param.current_position = current_position
        self.coarse_input_param.current_velocity = [0.0] * config.dof
        self.coarse_input_param.current_acceleration = [0.0] * config.dof
        self.coarse_input_param.max_velocity = config.max_velocity
        self.coarse_input_param.max_acceleration = config.max_acceleration
        self.coarse_input_param.max_jerk = config.max_jerk
        self.coarse_output_param = OutputParameter(config.dof)
        self.coarse_ruckig = Ruckig(config.dof, config.coarse_interval)

        # 初始的目标速度为0
        self.target_vel = [0.0] * config.dof
        self.last_point = None

        self.generate_thread = threading.Thread(target=self.generateThreadFun, daemon=True)
        self.thread_lock = threading.Lock()

        self.is_initialized = False
        self.is_running = True

        self.frame = 0
        self.generate_thread.start()


        # 轨迹曲线拟合所需要的变量
        # 创建线程池用于并行轨迹曲线拟合
        self.fitting_executor = ThreadPoolExecutor(max_workers=16)


    def addWayPoint(self, point: list):
        # 添加Waypoint，若没有初始化,首先初始化
        print(f'add waypoint: {point[0:6]}')
        if self.is_initialized is False:
            self.fine_input_param.current_position = point
            self.coarse_input_param.current_position = point
            self.last_point = point
            self.is_initialized = True
        else:
            self.way_points.put(point)
        # print(f'added waypoint: {point}')
    
    def popTrajPoint(self):
        return self.traj_points.get()
    
    def generateThreadFun(self):
        while self.is_running:
            # 只要有waypoint，就持续运行生成轨迹
            target_point = self.way_points.get(block=True)
            print(f'vel = {(target_point - self.last_point)[0:6] * 30}')
            # print(f'target point len: {len(target_point)}')

            start_time = time.time()
            # 首先是粗略模式生成轨迹，粗略模式用于获取速度
            self.coarse_input_param.target_position = target_point[0:self.config.dof]
            self.coarse_input_param.target_velocity = self.target_vel
            # print(f'target_vel: {self.target_vel}')
            # 粗略模式，实时轨迹生成
            traj_vel = []
            while self.coarse_ruckig.update(self.coarse_input_param, self.coarse_output_param) == Result.Working:
                traj_vel.append(self.coarse_output_param.new_velocity)
                self.coarse_input_param.current_position = self.coarse_output_param.new_position
                self.coarse_input_param.current_velocity = self.coarse_output_param.new_velocity
                # print(f'traj len: {len(trajectory)}, velocity: {output_param.new_velocity}')
                self.coarse_input_param.current_acceleration = self.coarse_output_param.new_acceleration
            coarse_traj_len = len(traj_vel)
            end_time = time.time()
            time_diff = end_time - start_time
            print(f'coarse traj len: {coarse_traj_len}, traj time: {coarse_traj_len * self.config.coarse_interval: .4f} s, time used: {time_diff*1000: .4f}ms')
            self.target_vel = traj_vel[coarse_traj_len // 2]
            # for vel in traj_vel:
            #     print(vel[:7])
            # print('generate_thread start')
            # time.sleep(1.0)

    def getObserveData(self):
        with self.observe_thread_lock:
            if self.observe_buffer:
                return self.observe_buffer.pop()
            else:
                return None  # or handle the empty case appropriately
        # return self.observe_buffer.pop()
    
    def getObserveDataLeft(self):
        if self.observe_buffer:
            return self.observe_buffer.popleft()
        else:
            return None  # or handle the empty case appropriately
    
    def jointTrajFitting(self, timestamps, joint_chunk, index, start_time, end_time, deg = 3, time_step = 0.001):
        # x = np.array(timestamps)
        # y = np.array(joint_chunk)
        # 进行多项式拟合
        coefficients = np.polyfit(timestamps, joint_chunk, deg=deg)
        # 使用拟合得到的多项式计算y值
        polynomial = np.poly1d(coefficients)
        x = np.arange(start_time, end_time, time_step)
        joint_chunk_fitted = polynomial(x)

        # if index == 0:
        #     # 可视化
        #     # 创建一个新的图形
        #     fig, ax = plt.subplots()

        #     # 绘制第一条曲线，使用红色实线
        #     ax.plot(timestamps, joint_chunk, label='joint_chunk', color='red', linestyle='-')

        #     # 绘制第二条曲线，使用蓝色虚线
        #     ax.plot(x, joint_chunk_fitted, label='joint_chunk_fitted', color='blue', linestyle='--')

        #     # 添加图例
        #     ax.legend()

        #     # 添加标题和标签
        #     ax.set_title(f'joint {index}')
        #     ax.set_xlabel('time [s]')
        #     ax.set_ylabel('joint value')

        #     # 保存图片
        #     plt.savefig(f'joint_{index}_{self.frame}.png', dpi=300)
        #     self.frame += 1
        return index, joint_chunk_fitted

    @run_time_decorator
    def trajFitting(self, timestamps, action_chunk, start_time, end_time, deg = 3, time_step = 0.001):
        # 对Action进行预处理，action_chunk是动作维度的List格式[[action], [action], [action], ...]
        # 需要将action_chunk转换为关节维度的格式，以Numpy表示
        timestamps_np = np.array(timestamps)
        joint_chunks = self.toJointChunk(action_chunk)
        futures = [self.fitting_executor.submit(self.jointTrajFitting, timestamps_np, np.array(joint_chunk), index, start_time, end_time, deg, time_step) for index, joint_chunk in enumerate(joint_chunks)]
        # 等待所有任务完成并获取结果
        results = [future.result() for future in futures]
        # 解析结果
        final_results = [None] * len(results)
        for index, joint_chunk_fitted in results:
            final_results[index] = joint_chunk_fitted
        return np.array(final_results), np.arange(start_time, end_time, time_step)
    
    @run_time_decorator
    def toJointChunk(self, action_chunk):
        joint_chunks = []
        action_dim = len(action_chunk[0])
        for index in range(action_dim):
            joint_chunks.append([])
        
        for action in action_chunk:
            for index in range(action_dim):
                joint_chunks[index].append(action[index])
        return joint_chunks
    
    def run(self):
        with self.thread_lock:
            self.is_running = True
        self.generate_thread.start()
        self.generate_thread.join()
    
    def start(self):
        with self.thread_lock:
            self.is_running = True
        self.generate_thread.start()
        self.generate_thread.join()
    
    def stop(self):
        with self.thread_lock:
            self.is_running = False
        self.generate_thread.join(timeout=1.0)
    
    def close(self):
        with self.thread_lock:
            self.is_running = False
        self.generate_thread.join(timeout=1.0)

if __name__ == '__main__':
    import sys
    sys.path.append('/home/robot/Gits/jupyter/vla_infer')
    from conf.config import get_trajectory_config
    config = get_trajectory_config()
    traj_generator = TrajectoryGenerator(config=config)
    try:
        while True:
            # result = robot.retrieveObservation()
            # print(result.keys())
            time.sleep(1.0)  # 控制循环频率
    except KeyboardInterrupt:
        traj_generator.close()
