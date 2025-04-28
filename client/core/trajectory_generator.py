import time
import threading
import queue
from ml_collections import ConfigDict
from ruckig import InputParameter, OutputParameter, Result, Ruckig
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
        self.generate_thread.start()

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
