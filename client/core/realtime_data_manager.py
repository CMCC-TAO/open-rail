import copy
import time
import threading
import matplotlib.pyplot as plt
import numpy as np

from collections import deque
from ml_collections import ConfigDict

from client.utils.util import run_time_decorator
class RealtimeDataManager():
    def __init__(self, rdm_config: ConfigDict):
        self.rdm_config = rdm_config
        self.observe_buffer = deque(maxlen=rdm_config.max_len)
        # self.control_action_buffer = deque(maxlen=rdm_config.control_max_len)
        # self.control_timestamp_buffer = deque(maxlen=rdm_config.control_max_len)
        self.action_chunks = []
        self.timestamp_chunks = []
        # self.ref_timestamp = 0
        self.action_thread_lock = threading.Lock()
        self.observe_thread_lock = threading.Lock()
        self.polynomial_thread_lock = threading.Lock()
        if rdm_config.record_data:
            pass #

        # if rdm_config.show_data:
        #     pass #
        # self.action_data_received = False

        self.init_observe_timestamp = None # Timestamp of the first observe data to inference
        # self.init_control_timestamp = None # Timestamp of the first action to execute
        # self.init_control_time = 0.0 # Time of the first action to execute in seconds with respect to the first observe timestamp
        # self.update_control_time = False # update control time when first action executed
        # self.currt_time = None
        self.frame_count = 0
        self.action_chunk_fitted = None
        self.vel_chunk_fitted = None
        self.timestamps_fitted = None
        self.action_chunk_index = None

        # to draw
        self.action_chunk_last = None
        self.timestamp_last = None
        self.isDraw = False

        # inference, trajectory fitting and control marker
        self.start_infer_marker = None
        self.start_traj_marker = None
        self.start_ctrl_marker = None
        # self.last_control_timestamp = None
        self.avg_infer_time = 0.0
        self.avg_traj_time = 0.0
        self.infer_count = 0
        # self.currt_infer_time = 0.0
        # self.currt_traj_time = 0.0
        # self.last_infer_time = 0.0
        # self.last_traj_time = 0.0
    def addInferCount(self):
        self.infer_count += 1

    def setInitObserveTimestamp(self, timestamp):
        self.init_observe_timestamp = timestamp
    
    # def setInitControlTime(self):
    #     currt_infer_time = (self.start_traj_marker - self.start_infer_marker)
    #     currt_traj_time = (self.start_ctrl_marker - self.start_traj_marker)
    #     self.init_control_time = currt_infer_time + currt_traj_time # in seconds
    # 用于统计推理时间和轨迹拟合时间
    def setObserveTimeMarker(self, timestamp):
        self.observe_marker = timestamp
    def setInferTimeMarker(self):
        self.start_infer_marker = time.perf_counter()
    # 用于统计推理时间和轨迹拟合时间
    def setTrajTimeMarker(self):
        self.start_traj_marker = time.perf_counter()
    # 用于统计推理时间和轨迹拟合时间
    def setControlTimeMarker(self):
        # self.last_control_timestamp = self.start_control_timestamp
        self.start_ctrl_marker = time.perf_counter()
    
    def setAvgInferTime(self):
        # self.last_infer_time = self.currt_infer_time
        currt_infer_time = self.start_traj_marker - self.start_infer_marker
        self.avg_infer_time = (self.avg_infer_time * (self.infer_count - 1) + currt_infer_time) / self.infer_count
        print(f'avg infer time: {self.avg_infer_time}')

    def setAvgTrajTime(self):
        # self.last_traj_time = self.currt_traj_time
        currt_traj_time = self.start_ctrl_marker - self.start_traj_marker
        self.avg_traj_time = (self.avg_traj_time * (self.infer_count - 1) + currt_traj_time) / self.infer_count
        print(f'avg traj time: {self.avg_traj_time}')
    
    def getAvgInferTime(self):
        return self.avg_infer_time

    def getAvgTrajTime(self):
        return self.avg_traj_time

    def addObserveData(self, frame):
        # 将传入的消息msg添加到buffer列表中
        self.frame_count += 1
        # 前面几帧数据不稳定，丢弃
        if self.frame_count > 5:
            with self.observe_thread_lock:
                self.observe_buffer.append(frame)
        # if self.init_observe_timestamp is None and self.frame_count > 5:
        #     self.init_observe_timestamp = frame['ref_timestamp']
        #     self.frame_count = 1
        # if self.init_observe_timestamp is not None:
        #     with self.observe_thread_lock:
        #         self.observe_buffer.append(frame)
    def updateControlTimeStamp(self):
        # TODO: using clock_gettime_ns instead of time()
        # currt_timestamp = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        # print(f'init_control_timestamp: {self.init_control_timestamp}')
        # currt_time = time.time()
        # self.init_control_timestamp = self.init_control_timestamp + int((currt_time - self.init_control_time) * 1e9)
        # print(f'init_control_timestamp updated: {self.init_control_timestamp}, time_offset: {(currt_time - self.init_control_time) * 1000} ms')
        # self.init_control_time = currt_time
        # self.update_control_time = True
        pass

    def addActionData(self, action_chunk, timestamp_chunk, strategy = 'latest'):
        # 第一次添加数据的时候，记录初始时间戳,作为控制的开始时间
        # if self.init_control_timestamp is None or len(self.action_chunks) == 0:
        #     self.init_control_timestamp = timestamp_chunk[0]
        #     self.init_control_time = time.time()
        #     # 首次添加数据，直接添加到action_chunks和timestamp_chunks中
        #     timestamp_chunk_new = [(timestamp - self.init_control_timestamp) / 1e9 for timestamp in timestamp_chunk]
        #     if self.action_chunk_last is None:
        #         self.action_chunk_last = action_chunk
        #         self.timestamp_last = timestamp_chunk_new
        #     with self.action_thread_lock:
        #         if strategy == 'fusion':
        #             self.action_chunks.extend(action_chunk)
        #             self.timestamp_chunks.extend(timestamp_chunk_new)
        #         elif strategy == 'latest':
        #             self.action_chunks = action_chunk
        #             self.timestamp_chunks = timestamp_chunk_new
        #         else:
        #             raise ValueError(f'Invalid strategy: {strategy}')
        #     # print(f'timestamp_chunks: {self.timestamp_chunks}')
        # else:
        #     # self.currt_time = time.time()
        #     # time_duration = int((self.currt_time - self.init_control_time) * 1e9)
        #     # print(f'currt_timestamp: {time_duration}')
        #     # print(f'time duration in local: {(self.currt_time - self.init_control_time) * 1000} ms')
        #     # print(f'time duration in a2d: {(timestamp_chunk[0] - self.init_control_timestamp) / 1e6} ms')
        #     # 新的action_chunk需要跟已有的进行融合
        #     # 首先对齐时间戳
        #     timestamp_chunk_new = [(timestamp - self.init_control_timestamp) / 1e9 for timestamp in timestamp_chunk]

        #     # if not self.isDraw:
        #     #     self.isDraw = True
        #     #     # plot and save action chunk
        #     #     fig, ax = plt.subplots()
        #     #     # 绘制旧轨迹
        #     #     ax.plot(self.timestamp_last, self.toJointChunk(self.action_chunk_last)[0], label='last_action_chunk', color='red', linestyle='-')
        #     #     # 绘制新轨迹
        #     #     ax.plot(timestamp_chunk_new, self.toJointChunk(action_chunk)[0], label='last_action_chunk', color='blue', linestyle='-')
        #     #     # 添加图例
        #     #     ax.legend()
        #     #     # 添加标题和标签
        #     #     ax.set_title(f'joint {0}')
        #     #     ax.set_xlabel('time [s]')
        #     #     ax.set_ylabel('joint value')

        #     #     # 保存图片
        #     #     plt.savefig(f'joint_{0}_{0}.png', dpi=300)

        #     # 确保线程安全
        #     with self.action_thread_lock:
        #         if strategy == 'fusion':
        #             self.fusionActionChunks(action_chunk, timestamp_chunk_new)
        #         elif strategy == 'latest':
        #             self.action_chunks = action_chunk
        #             self.timestamp_chunks = timestamp_chunk_new
        #         else:
        #             raise ValueError(f'Invalid strategy: {strategy}')
        
        # # print(f'init_control_timestamp: {self.init_control_timestamp}, init_observe_timestamp: {self.init_observe_timestamp}')
        # rounded = [round(x, 4) for x in self.timestamp_chunks]
        # print(f'timestamp_chunks: {rounded}')
                # print(f'动作融合花费时间: {(end_time - start_time) * 1000} ms')
        pass

    def updateActionChunk(self, action_chunk, timestamp_chunk):
        # Action Chunk的时间戳跟观测数据时间戳保持一致
        # 确保线程安全
        with self.action_thread_lock:
            # 根据观测数据时间戳对Action Chunk进行对齐
            # 需要减掉开始控制的时间，首帧是0，后续帧是首帧推理和轨迹拟合的时间之和
            # print(f'init_observe_timestamp: {self.init_observe_timestamp}, init_control_time: {self.init_control_time}, currt_ref_timestamp: {timestamp_chunk[0]}')
            # timestamp_chunk[0] = (timestamp_chunk[0] - self.init_observe_timestamp) / 1e9 - self.init_control_time - 0.1
            timestamp_chunk[0] = 0.0
            for index in range(1, len(timestamp_chunk)):
                timestamp_chunk[index] = timestamp_chunk[index] + timestamp_chunk[0]
            # if not self.timestamp_chunks.isEmpty():
            #     self.ref_timestamp = self.timestamp_chunks[0]
            self.action_chunks = action_chunk
            self.timestamp_chunks = timestamp_chunk
        
        # print(f'init_control_timestamp: {self.init_control_timestamp}, init_observe_timestamp: {self.init_observe_timestamp}')
        rounded = [round(x, 4) for x in self.timestamp_chunks]
        print(f'timestamp_chunks: {rounded}')
    @run_time_decorator
    def fusionActionChunks(self, action_chunk, timestamp_chunk):
        candidate_index = 0
        for index in range(len(timestamp_chunk)):
            if timestamp_chunk[index] > self.timestamp_chunks[0]:
                candidate_index = index
                break
        assign_index = self.getClosestIndex(self.timestamp_chunks, timestamp_chunk[candidate_index])
        # 然后进行融合
        target_chunk_len = len(self.timestamp_chunks)
        currt_chunk_len = len(action_chunk)
        for index in range(currt_chunk_len - candidate_index):
            if assign_index + index < target_chunk_len:
                self.action_chunks[assign_index + index] = (self.action_chunks[assign_index + index] + action_chunk[candidate_index + index]) / 2.0
                self.timestamp_chunks[assign_index + index] = (self.timestamp_chunks[assign_index + index] + timestamp_chunk[candidate_index + index]) / 2.0
            else:
                self.action_chunks.append(action_chunk[candidate_index + index])
                self.timestamp_chunks.append(timestamp_chunk[candidate_index + index])
        
    def popActionData(self, num_samples=32):
        # 确保线程安全
        with self.action_thread_lock:
            # action_chunk_size = len(self.action_chunks)
            if self.action_chunks:
                return self.action_chunks.pop(0), self.timestamp_chunks.pop(0)
            else:
                return None, None
    
    @run_time_decorator
    # 将动作块转换为关节块
    def toJointChunk(self, action_chunk):
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

    # def popActionChunk(self, index_offset = 0, num_samples=32):
    #     # 为了补偿轨迹拟合的时间，需要使用未来的轨迹进行拟合，轨迹拟合时间一般为10ms
    #     # index_offset 是拟合后的序列，1个step对应1ms
    #     # 进行两部分工作：
    #     # 1. 准备用于轨迹曲线拟合的数据；
    #     # 2. 管理ActionChunk和Timestamps队列，丢弃掉过期数据；
    #     # 备注： 过期数据指的是时间戳在当前时间之前的数据
    #     # currt_time = time.time() - self.init_control_time
    #     future_time = self.getFutureTime(index_offset=index_offset)
    #     print(f'future_time: {future_time}')
    #     # 找到首帧有效数据的index
    #     valid_index = None
    #     for index, timestamp in enumerate(self.timestamp_chunks):
    #         if timestamp > future_time:
    #             valid_index = index
    #             break
    #     if valid_index is None:
    #         # TODO:  处理无有效数据
    #         print("[Error] No valid data in action chunk.")
    #         return None, None
        
    #     # 数据拟合需要往前找3帧，防止出现拟合结果不平顺的情况，TODO：可以将这部分变成可配置的参数
    #     # start_index = max(0, valid_index - num_samples // 4)
    #     start_index = max(0, valid_index)
    #     end_index = min(len(self.action_chunks), start_index + num_samples)
    #     # 使用deepcopy防止丢弃过期数据后丢失数据
    #     timestamps = copy.deepcopy(self.timestamp_chunks[start_index:end_index])
    #     action_chunks = copy.deepcopy(self.action_chunks[start_index:end_index])
    #     # start_time = self.timestamp_chunks[start_index]
    #     # end_time = self.timestamp_chunks[end_index - 1]

    #     # 丢掉过期数据，需要保证线程安全
    #     # with self.action_thread_lock:
    #     #     del self.action_chunks[:start_index]
    #     #     del self.timestamp_chunks[:start_index]
        
    #     # print(f'timestamps for curve fitting: {timestamps}, start_time: {start_time}, end_time: {end_time}')
    #     return np.array(timestamps), np.array(self.toJointChunk(action_chunks))
    
    def popActionChunk(self, time_offset = 0.0, num_samples=32):
        # 为了补偿轨迹拟合的时间，需要使用未来的轨迹进行拟合，轨迹拟合时间一般为10ms
        # index_offset 是拟合后的序列，1个step对应1ms
        # 进行两部分工作：
        # 1. 准备用于轨迹曲线拟合的数据；
        # 2. 管理ActionChunk和Timestamps队列，丢弃掉过期数据；
        # 备注： 过期数据指的是时间戳在当前时间之前的数据
        # currt_time = time.time() - self.init_control_time
        # currt_time = self.getCurrentTime()
        currt_time = 0.0
        target_time = currt_time + time_offset
        print(f'currt_time: {currt_time}, target_time: {target_time}')
        # 找到首帧有效数据的index
        valid_index = None
        for index, timestamp in enumerate(self.timestamp_chunks):
            if timestamp > target_time:
                valid_index = index
                break
        if valid_index is None:
            # TODO:  处理无有效数据
            print("[Error] No valid data in action chunk.")
            return None, None
        
        # 数据拟合需要往前找3帧，防止出现拟合结果不平顺的情况，TODO：可以将这部分变成可配置的参数
        # start_index = max(0, valid_index - num_samples // 4)
        start_index = max(0, valid_index-1)
        end_index = min(len(self.action_chunks), start_index + num_samples)
        # 使用deepcopy防止丢弃过期数据后丢失数据
        # timestamps = copy.deepcopy(self.timestamp_chunks[start_index:end_index])
        # action_chunks = copy.deepcopy(self.action_chunks[start_index:end_index])
        
        # print(f'timestamps for curve fitting: {timestamps}, start_time: {start_time}, end_time: {end_time}')
        return np.array(self.timestamp_chunks[start_index:end_index]), np.array(self.toJointChunk(self.action_chunks[start_index:end_index]))
    # def popActionChunk(self, num_samples=32):
    #     # 将当前Action Chunk与上一个Action Chunk时间对齐后，返回轨迹拟合之后的数据
    #     # 进行两部分工作：
    #     # 1. 当前Action Chunk与上一个Action Chunk时间对齐；
    #     # 2. 根据当前时间、轨迹拟合的平均时间截取指定数量的Action Chunk；
    #     chunk_time_offset = 0
    #     chunk_time_offset = 0
    #     if self.ref_timestamp > 0:
    #         observe_time_offset = self.timestamp_chunks[0] - self.ref_timestamp
    #         # 当前Action Chunk相对于上一个Action Chunk的偏移时间
    #         assign_time_offset = observe_time_offset - self.last_infer_time - self.last_traj_time
    #         # 上一个Action Chunk控制持续的时间
    #         control_time = time.perf_counter() - self.last_control_time
    #         # 根据对齐时间和控制持续时间, 计算当前Action Chunk的偏移时间（有效起始时间）
    #         chunk_time_offset = max(0, control_time - assign_time_offset)
    #     total_time_offset = chunk_time_offset + self.avg_traj_time

    #     # 根据time_offset找到首帧有效数据的index
    #     valid_index = None
    #     for index, timestamp in enumerate(self.timestamp_chunks):
    #         if timestamp > total_time_offset:
    #             valid_index = index
    #             break
    #     if valid_index is None:
    #         # TODO:  处理无有效数据
    #         print("[Error] No valid data in action chunk.")
    #         return None, None
        
    #     # 数据拟合需要往前找3帧，防止出现拟合结果不平顺的情况，TODO：可以将这部分变成可配置的参数
    #     # start_index = max(0, valid_index - num_samples // 4)
    #     start_index = max(0, valid_index-1)
    #     end_index = min(len(self.action_chunks), start_index + num_samples)
    #     # 使用deepcopy防止丢弃过期数据后丢失数据
    #     # timestamps = copy.deepcopy(self.timestamp_chunks[start_index:end_index])
    #     # action_chunks = copy.deepcopy(self.action_chunks[start_index:end_index])
    #     # 不需要深度拷贝，数据在更新之前肯定能使用完
    #     timestamps = self.timestamp_chunks[start_index:end_index]
    #     action_chunks = self.action_chunks[start_index:end_index]

    #     # timestamps是相对于当前ActionChunk的起始时间的，需要返回assign_time_offset，用于上一帧时间数据的对齐
    #     return np.array(timestamps), np.array(self.toJointChunk(action_chunks)), assign_time_offset, total_time_offset

    def getCurrentTime(self):
        # 使用with语句获取锁，保证线程安全
        with self.polynomial_thread_lock:
            # 如果action_chunk_index为None，则返回0.0
            if self.action_chunk_index is None:
                return 0.0
            # 否则返回timestamps_fitted中action_chunk_index对应的值
            else:
                return self.timestamps_fitted[self.action_chunk_index]
        # return time.time() - self.init_control_time
    def getFutureTime(self, index_offset=0):
        # 使用with语句获取锁，保证线程安全
        with self.polynomial_thread_lock:
            # 如果action_chunk_index为None，则返回0.0
            if self.action_chunk_index is None:
                return 0.0
            # 否则返回timestamps_fitted中action_chunk_index对应的值
            else:
                length = len(self.timestamps_fitted)
                return self.timestamps_fitted[min(length - 1, self.action_chunk_index + index_offset)]
        # return time.time() - self.init_control_time

    def getFittedActionChunk(self, index_offset=0, num_samples=20):
        # 获取未来动作块
        with self.polynomial_thread_lock:
            # 如果动作块索引为空，则返回空数组
            if self.action_chunk_index is None or num_samples <= 0:
                return None, None
            else:
                # 获取总长度
                total_len = len(self.timestamps_fitted)
                # 计算起始索引
                start_index = min(self.action_chunk_index + index_offset, total_len-1) 
                # 计算结束索引
                end_index = min(self.action_chunk_index + index_offset + num_samples, total_len)
                # 返回动作块和对应的时间戳
                return self.timestamps_fitted[start_index:end_index], self.action_chunk_fitted[:, start_index:end_index]
                # return copy.deepcopy(self.timestamps_fitted[start_index:end_index]), copy.deepcopy(self.action_chunk_fitted[:, start_index:end_index])

    def getFutureActionChunkIndex(self):
        with self.polynomial_thread__lock:
            if self.actionChunkIndex is None or not len(self.timestamps) > 0:
                return -1
            else:
                currt = time.time() - self.initControlTime  # 当前时间戳，单位：秒。这里假设当前时间为60s。该值应该由控制器提供或自增。

        for i in range(len(self._timestamp)):# 遍历所有帧的时间戳并找到第一个大于当前时间的索引i（并不是严格等于）；如果找不到这样的索引，则返回-1表示没有未来数据。这个函数的作用是找到下一个需要发送的数据的索引，以便在控制循环中处理这些数据。通过这种方式可以确保在控制循环中只处理未来的数据而不是过去的数据，从而避免了不必要
                return self.timestamps_fitted[self.action_chunk_index]
    
    def updateActionChunkFitted(self, action_chunk_fitted, vel_chunk_fitted, timestamps_fitted, search_action = False, search_length = 20, smooth_action = False, smooth_length = 20):
        # 更新index, 首次更新;
        if self.action_chunk_index is None:
            with self.polynomial_thread_lock:
                self.action_chunk_index = 0
                self.action_chunk_fitted = action_chunk_fitted
                self.vel_chunk_fitted = vel_chunk_fitted
                self.timestamps_fitted = timestamps_fitted
        else: # 后续融合更新
            # print(f'action_chunk_index old: {self.action_chunk_index}')
            # 统计从收到观测数据到完成轨迹拟合所需要的时间
            # currt_timestamp = self.timestamps_fitted[self.action_chunk_index]
            target_chunk_index = 0
            time_offset = self.start_ctrl_marker - self.observe_marker
            print(f'total inference time: {time_offset} s')
            # action = self.action_chunk_fitted[:, self.action_chunk_index]
            # self.action_chunk_index = self.getClosestIndex(timestamps_fitted, currt_timestamp)
            # print(f'currt_timestamp: {currt_timestamp}, timestamps_fitted: {timestamps_fitted[::5]}')
            for index in range(len(timestamps_fitted)):
                if timestamps_fitted[index] > time_offset:
                    target_chunk_index = index
                    break
            # target_chunk_index += 12
            currt_action = None
            currt_vel = None
            if search_action:
                candidate_action_chunk = None
                candidate_action_chunk = copy.deepcopy(action_chunk_fitted[:, target_chunk_index:target_chunk_index + search_length])
                with self.polynomial_thread_lock:
                    currt_action = self.action_chunk_fitted[:, self.action_chunk_index]
                    currt_vel = self.vel_chunk_fitted[:, self.action_chunk_index]
                index_offset = self.searchSmoothAction(currt_action, currt_vel, candidate_action_chunk, search_length)
                target_chunk_index += index_offset

            # self.action_chunk_index = 30
            # 解决本部分耗时问题
            # target_chunk_index += 0
            print(f'action_chunk_index: {target_chunk_index}')

            if smooth_action:
                base_ratio = 0.75
                if currt_action is None:
                    with self.polynomial_thread_lock:
                        currt_action = self.action_chunk_fitted[:, self.action_chunk_index]
                for index in range(smooth_length):
                    ratio = (1 - base_ratio) * index / smooth_length
                    action_chunk_fitted[:14, target_chunk_index + index] = (base_ratio + ratio) * action_chunk_fitted[:14, target_chunk_index + index] + (1 - base_ratio - ratio) * currt_action[:14]
                # currt_action = self.action_chunk_fitted[:, self.action_chunk_index]
                # currt_vel = self.vel_chunk_fitted[:, self.action_chunk_index]
                # smoothed_action_chunk = self.smoothActionTraj(currt_action, currt_vel, candidate_action_chunk, max_acc, smooth_length)
                # self.action_chunk_fitted[:, target_chunk_index:target_chunk_index + smooth_length]
                
            # print(f'currt_timestamp: {currt_timestamp}, update_timestamp: {timestamps_fitted[self.action_chunk_index]}')
            # print(f'old action: {action}')
            # self.action_chunk_index = offset
            gripper_offset = 25
            with self.polynomial_thread_lock:
                self.action_chunk_index = target_chunk_index
                self.action_chunk_fitted = action_chunk_fitted
                self.vel_chunk_fitted = vel_chunk_fitted
                self.timestamps_fitted = timestamps_fitted
                self.action_chunk_fitted[14:, :-gripper_offset] = action_chunk_fitted[14:, gripper_offset:]
            # action = self.action_chunk_fitted[:, self.action_chunk_index]
            # print(f'new action: {action}')
            # print(f'action_chunk_index: {self.action_chunk_index}')
            # print(f'action_chunk_fitted shape: {self.action_chunk_fitted.shape}')
            # print(f'action_chunk_fitted: {self.action_chunk_fitted[:, -2]}')
            # print(f'action_chunk_fitted: {self.action_chunk_fitted[:, -1]}')
    def searchSmoothAction(self, currt_action, currt_vel, candidate_action_chunk, search_length):
        valid_joints = [index for index, value in enumerate(abs(currt_vel) > 5e-3) if value]
        print(f'valid_joints: {valid_joints}')
        currt_action = currt_action[valid_joints]
        currt_vel = currt_vel[valid_joints]
        print(f'currt_vel: {currt_vel}')
        target_index = 0
        valid_joint_num = len(valid_joints)
        qualified_joint_num = 0
        for candidate_index in range(0, search_length, 5):
            candidate_action = candidate_action_chunk[valid_joints, candidate_index]
            action_diff = candidate_action - currt_action
            # print(f'currt_vel: {currt_vel}')
            print(f'candidate action diff: {action_diff}')
            qualified_count = 0
            for index in range(valid_joint_num):
                # v = 0.0 是夹爪的速度，不考虑夹爪的情况；当速度很小时，默认手臂静止，不考虑该种情况
                if action_diff[index] * currt_vel[index] > 0.0:
                    qualified_count += 1
            print(f'candidate_index: {candidate_index}, qualified count: {qualified_count}')
            if qualified_count == valid_joint_num:
                target_index = candidate_index
                qualified_joint_num = qualified_count
                break
            else:
                if qualified_count > qualified_joint_num:
                    target_index = candidate_index
                    qualified_joint_num = qualified_count
        print(f'target_index: {target_index}, qualified dim: {qualified_joint_num}')
        return target_index
    def smoothActionTrajOLD(self, currt_action, currt_vel, candidate_action_chunk, max_acc, smooth_length=15):
        action_dim = len(currt_action)
        max_accs = np.array([max_acc] * len(currt_action))
        period = 0.005
        for index in range(smooth_length):
            candidate_action = candidate_action_chunk[:, index]
            action_diff = candidate_action - currt_action
            acc_flag = np.array([1.0 if joint_diff > 0.0 else -1.0 for joint_diff in action_diff])
            next_max_vel = currt_vel + acc_flag * max_accs * period
            next_max_action = currt_action + currt_vel * period + 0.5 * acc_flag * max_accs * period * period
            for joint_index in range(action_dim):
                if acc_flag[joint_index] == 1.0:
                    if candidate_action[joint_index] > next_max_action[joint_index]:
                        candidate_action[joint_index] = next_max_action[joint_index]
                        currt_vel[joint_index] = next_max_vel[joint_index]
                    else:
                        currt_vel[joint_index] = (candidate_action[joint_index] - currt_action[joint_index]) / period
                elif acc_flag[joint_index] == -1.0:
                    if candidate_action[joint_index] < next_max_action[joint_index]:
                        candidate_action[joint_index] = next_max_action[joint_index]
                        currt_vel[joint_index] = next_max_vel[joint_index]
                    else:
                        currt_vel[joint_index] = (candidate_action[joint_index] - currt_action[joint_index]) / period
                else:
                    pass
            print(f'currt_action: {currt_action[:7]}')
            print(f'candi_action: {candidate_action[:7]}')
            currt_action = candidate_action
        return candidate_action_chunk
    
    def getActionFitted(self):
        with self.polynomial_thread_lock:
            if self.action_chunk_index is None:
                return None
            # if not self.update_control_time:
            #     self.updateControlTimeStamp()
            self.action_chunk_index = min(self.action_chunk_index + 1, self.action_chunk_fitted.shape[1] - 1)
            action = self.action_chunk_fitted[:, self.action_chunk_index]
            # print(f'action_chunk_index: {self.action_chunk_index}, joint_0: {action[0]}, joint_1: {action[1]}')
            return self.action_chunk_fitted[:, self.action_chunk_index]
    
    def getActionChunk(self):
        # 确保线程安全
        with self.action_thread_lock:
            return copy.copy(self.action_chunks)
    
    def getObserveData(self, num_samples = 1):
        with self.observe_thread_lock:
            if len(self.observe_buffer) >= num_samples:
                data = self.observe_buffer.pop() if num_samples == 1 else [self.observe_buffer.pop() for _ in range(num_samples)]
                return data
            else:
                return None  # or handle the empty case appropriately
        # return self.observe_buffer.pop()
    
    def getObserveDataLeft(self):
        if self.observe_buffer:
            return self.observe_buffer.popleft()
        else:
            return None  # or handle the empty case appropriately

    def get_closest(self, target_stamp):
        # 找到时间最接近的消息
        closest = min(self.buffer, key=lambda x: abs(x['timestamp'] - target_stamp))
        return closest
    
    @run_time_decorator
    def getClosestIndex(self, timestamp_list, target_timestamp):
        # 计算每个元素与目标值的差值的绝对值
        differences = [abs(timestamp - target_timestamp) for timestamp in timestamp_list]
        # 找到最小差值的索引
        closest_index = differences.index(min(differences))
        return closest_index# 数据可视化函数
    