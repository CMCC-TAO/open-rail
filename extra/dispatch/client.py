import time
from collections import deque
import numpy as np
from extra.dispatch.conf import get_dispatch_config
from extra.dispatch.zmq import DispatchZMQClient

class DispatchClient:
    def __init__(self, vla_client, robot):
        self.config_root = get_dispatch_config()
        self.config = self.config_root.robot
        self.vla_client = vla_client
        self.robot = robot
        self.client = DispatchZMQClient(
            robot_type=self.config.robot_name,
            server_task_address=self.config_root.server_task_address,
            server_response_address=self.config_root.server_response_address,
            heartbeat_interval=3.0,
            reconnect_interval=2.0,
            receive_timeout=30.0  # 30秒未收到消息触发重连
        )
        
        # 稳定性检测变量
        self.stable_count = 0  # 连续满足条件的计数
        self.required_stable_count = self.config.required_stable_count  # 需要连续满足条件的次数
        self.stability_window = deque(maxlen=50)  # 滑动窗口存储最近的progress值
        self.thre_stability_ratio = self.config.thre_stability_ratio
        
        # 滤波相关配置
        self.enable_progress_filtering = True  # 是否启用进度值滤波
        self.progress_history = deque(maxlen=10)  # 存储历史进度值用于滤波
        
    def start(self):
        self.client.set_task_handler(self.handle_task)
        self.client.start()
        
        # 程序启动：先恢复默认姿态，再暂停程序
        self.vla_client.language = self.config.language['default']
        self.vla_client.is_running_action = False
        time.sleep(0.1)
        self.robot.reset_robot(target_pose=self.config.reset_pose['default'])

    def handle_connection(self, connected):
        """连接状态回调"""
        status = "connected" if connected else "disconnected"

    def smooth_progress(self, values, process_variance=1e-5, measurement_variance=1e-2):
        """
        使用卡尔曼滤波对进度序列进行平滑处理

        参数:
            values: list/ndarray/deque，进度值序列 (0~1)
            process_variance: float，过程噪声方差 Q
            measurement_variance: float，测量噪声方差 R

        返回:
            smoothed: ndarray，平滑后的结果
        """
        if isinstance(values, deque):
            values = list(values)
        values = np.array(values, dtype=float)

        n = len(values)
        smoothed = np.zeros(n)

        # 初始化
        x_est = values[0]  # 初始状态估计
        P = 1.0            # 初始估计协方差

        Q = process_variance
        R = measurement_variance

        for i in range(n):
            # 预测步骤
            x_pred = x_est
            P_pred = P + Q

            # 更新步骤
            K = P_pred / (P_pred + R)  # 卡尔曼增益
            x_est = x_pred + K * (values[i] - x_pred)
            P = (1 - K) * P_pred

            smoothed[i] = x_est

        return smoothed

    # 设置回调函数
    def handle_task(self, task_data):
        """处理任务回调"""
        print('\n当前机器人配置：', self.config.robot_name, '\ntask_data: ', task_data)

        target_object = task_data['target_object']
        if target_object != '':
            target_object = f"_{task_data['target_object']}"
        key = f"{task_data['skill_type']}{target_object}"
        self.client.send_status_update(task_data['task_id'], 'pending')

        if self.config.reset_pose[key] is not None:
            print(f'\n复位机器人：{key}\n')
            self.vla_client.is_running_action = False
            time.sleep(0.1)
            self.robot.reset_robot(target_pose=self.config.reset_pose[key])
            time.sleep(self.config.reset_sleep)
            self.vla_client.inference_first()

        if 'replay:' not in self.config.language[key]:
            print(f'\n语言指令：{self.config.language[key]}\n')
            self.vla_client.language = self.config.language[key]
            self.vla_client.is_running_action = True
            # 需等待current_prob_progress更新，避免还是上次任务的值
            time.sleep(1.0)
            self.vla_client.info_act['current_prob_progress'] = 0.0
        else:
            print(f'\n播放轨迹：{self.config.language[key]}\n')
            self.vla_client.is_running_action = False
            time.sleep(0.1)
            path_replay = self.config.language[key].split(':')[-1]
            self.robot.replay_trajectories(path_replay)

        # 重置稳定性检测变量
        self.stable_count = 0
        self.stability_window.clear()
        
        while True:
            time.sleep(0.05) # 禁止修改
            if 'replay:' not in self.config.language[key]:
                thre_finish = self.config.thre_progress_finish[key]
                if 'current_prob_progress' in self.vla_client.info_act:
                    raw_progress = self.vla_client.info_act['current_prob_progress']
                    
                    if self.enable_progress_filtering:
                        self.progress_history.append(raw_progress)
                        if len(self.progress_history) >= 3:
                            smoothed_values = self.smooth_progress(self.progress_history)
                            current_progress = smoothed_values[-1]  # 使用最新的滤波值
                            print(f'current_prob_progress: {raw_progress:.4f} -> filtered: {current_progress:.4f}')
                        else:
                            current_progress = raw_progress
                            print(f'current_prob_progress: {current_progress:.4f} (no filtering, insufficient data)')
                    else:
                        current_progress = raw_progress
                        print('current_prob_progress: ', current_progress)
                    
                    self.stability_window.append(current_progress)
                    if current_progress > thre_finish:
                        self.stable_count += 1
                        print(f'稳定计数: {self.stable_count}/{self.required_stable_count}')
                        
                        # 滑动窗口内的方差检查
                        if len(self.stability_window) >= 3:
                            recent_values = list(self.stability_window)
                            window_std = np.std(recent_values)
                            window_mean = np.mean(recent_values)
                            stability_ratio = window_std / (window_mean + 1e-6)
                            print(f'稳定性指标 - 标准差: {window_std:.4f}, 变异系数: {stability_ratio:.4f}')

                            if self.stable_count >= self.required_stable_count and stability_ratio < self.thre_stability_ratio:
                                print('✅ 检测到稳定的进度值，任务完成')
                                break
                    else:
                        if self.stable_count > 0:
                            print('进度值下降，重置稳定计数')
                        self.stable_count = 0
            else:
                print('replay轨迹执行完毕')
                break

        self.client.send_status_update(task_data['task_id'], 'completed')
        print(f'\n任务完成，暂停：{key}\n')
        self.vla_client.is_running_action = False
        time.sleep(0.1)
        # if self.config.reset_pose[key] is not None:
        #     self.robot.reset_robot(target_pose=self.config.reset_pose[key])
        #     self.vla_client.inference_first()
        return {"success": True, "message": "Task completed"}

    def mock_task(self):
        result = self.handle_task({
            "version": "1.0",
            "type": "task",
            "robot_type": "ARM_B",
            "task_id": "ARM_B_1640995200123",
            "skill_type": "pick",
            "target_object": "shrimpdumpling",
            "target_location": "",
            "source": "service"
        })
        print('任务B1执行结果：', result)
        input('\n模型暂停推理，模拟等待，按Enter结束等待...\n')
        self.vla_client.is_running_action = True
        if result['success']:
            result = self.handle_task({
                "version": "1.0",
                "type": "task",
                "robot_type": "ARM_B",
                "task_id": "ARM_B_1640995200123",
                "skill_type": "place",
                "target_object": "shrimpdumpling",
                "target_location": "",
                "source": "service"
            })
            print('任务B2执行结果：', result)

        # result = self.handle_task({
        #     "version": "1.0",
        #     "type": "task",
        #     "robot_type": "ARM_C",
        #     "task_id": "ARM_C_1640995200123",
        #     "skill_type": "pour_water",
        #     "target_object": "blacktea",
        #     "target_location": "",
        #     "source": "service"
        # })
        # print('任务C1执行结果：', result)
        # input('\n模型暂停推理，模拟等待，按Enter结束等待...\n')
        # self.vla_client.is_running_action = True
        # if result['success']:
        #     result = self.handle_task({
        #         "version": "1.0",
        #         "type": "task",
        #         "robot_type": "ARM_B",
        #         "task_id": "ARM_B_1640995200123",
        #         "skill_type": "place",
        #         "target_object": "blacktea",
        #         "target_location": "",
        #         "source": "service"
        #     })
        #     print('任务C2执行结果：', result)

        # result = self.handle_task({
        #     "version": "1.0",
        #     "type": "task",
        #     "robot_type": "ARM_D",
        #     "task_id": "ARM_D_1640995200123",
        #     "skill_type": "open_door",
        #     "target_object": "",
        #     "target_location": "",
        #     "source": "service"
        # })
        # print('任务D1执行结果：', result)
        # if result['success']:
        #     result = self.handle_task({
        #         "version": "1.0",
        #         "type": "task",
        #         "robot_type": "ARM_D",
        #         "task_id": "ARM_D_1640995200123",
        #         "skill_type": "pick",
        #         "target_object": "apple",
        #         "target_location": "",
        #         "source": "service"
        #     })
        #     print('任务D2执行结果：', result)
        #     input('\n模型暂停推理，模拟等待，按Enter结束等待...\n')
        #     self.vla_client.is_running_action = True
        #     if result['success']:
        #         result = self.handle_task({
        #             "version": "1.0",
        #             "type": "task",
        #             "robot_type": "ARM_D",
        #             "task_id": "ARM_D_1640995200123",
        #             "skill_type": "place",
        #             "target_object": "apple",
        #             "target_location": "",
        #             "source": "service"
        #         })
        #         print('任务D3执行结果：', result)
        #         if result['success']:
        #             result = self.handle_task({
        #                 "version": "1.0",
        #                 "type": "task",
        #                 "robot_type": "ARM_D",
        #                 "task_id": "ARM_D_1640995200123",
        #                 "skill_type": "close_door",
        #                 "target_object": "",
        #                 "target_location": "",
        #                 "source": "service"
        #             })
        #             print('任务D3执行结果：', result)
