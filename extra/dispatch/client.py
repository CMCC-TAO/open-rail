import time
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

    def start(self):
        self.client.set_task_handler(self.handle_task)
        self.client.start()
        
        # 程序启动：先恢复默认姿态，再暂停程序
        self.robot.reset_robot(target_pose=self.config.reset_pose['default'])
        self.vla_client.inference_first()
        self.vla_client.is_running_action = False

    def handle_connection(self, connected):
        """连接状态回调"""
        status = "connected" if connected else "disconnected"

    # 设置回调函数
    def handle_task(self, task_data):
        """处理任务回调"""
        print('\naaaaa', task_data)

        target_object = task_data['target_object']
        if target_object != '':
            target_object = f"_{task_data['target_object']}"
        key = f"{task_data['skill_type']}{target_object}"
        self.client.send_status_update(task_data['task_id'], 'pending')

        if self.config.reset_pose[key] is not None:
            print(f'\n复位机器人：{key}')
            self.robot.reset_robot(target_pose=self.config.reset_pose[key])
            self.vla_client.inference_first()

        if 'replay:' not in self.config.language[key]:
            print(f'\n语言指令：{self.config.language[key]}')
            self.vla_client.language = self.config.language[key]
            self.vla_client.is_running_action = True
        else:
            print(f'\n播放轨迹：{self.config.language[key]}')
            path_replay = self.config.language[key].split(':')[-1]
            self.robot.replay_trajectories(path_replay)

        while True:
            if 'replay:' in self.config.language[key]:
                print('replay轨迹执行完毕')
                break
            else:
                # thre_finish = self.config.thre_progress_finish[key]
                # if 'current_prob_progress' in self.vla_client.info_act and self.vla_client.info_act['current_prob_progress'] > thre_finish:
                #     break

                time.sleep(3)
                print('VLA任务进度执行完毕')
                break
            time.sleep(0.05)
        
        self.client.send_status_update(task_data['task_id'], 'completed')
        return {"success": True, "message": "Task completed"}

    def mock_task(self):
        # result = self.handle_task({
        #     "version": "1.0",
        #     "type": "task",
        #     "robot_type": "ARM_B",
        #     "task_id": "ARM_B_1640995200123",
        #     "skill_type": "pick",
        #     "target_object": "shrimpdumpling",
        #     "target_location": "",
        #     "source": "service"
        # })
        # print('任务B1执行结果：', result)
        # if result['success']:
        #     result = self.handle_task({
        #         "version": "1.0",
        #         "type": "task",
        #         "robot_type": "ARM_B",
        #         "task_id": "ARM_B_1640995200123",
        #         "skill_type": "place",
        #         "target_object": "shrimpdumpling",
        #         "target_location": "",
        #         "source": "service"
        #     })
        #     print('任务B2执行结果：', result)

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

        result = self.handle_task({
            "version": "1.0",
            "type": "task",
            "robot_type": "ARM_D",
            "task_id": "ARM_D_1640995200123",
            "skill_type": "open_door",
            "target_object": "",
            "target_location": "",
            "source": "service"
        })
        print('任务D1执行结果：', result)
        if result['success']:
            result = self.handle_task({
                "version": "1.0",
                "type": "task",
                "robot_type": "ARM_D",
                "task_id": "ARM_D_1640995200123",
                "skill_type": "pick",
                "target_object": "apple",
                "target_location": "",
                "source": "service"
            })
            print('任务D2执行结果：', result)
            if result['success']:
                result = self.handle_task({
                    "version": "1.0",
                    "type": "task",
                    "robot_type": "ARM_D",
                    "task_id": "ARM_D_1640995200123",
                    "skill_type": "place",
                    "target_object": "apple",
                    "target_location": "",
                    "source": "service"
                })
                print('任务D3执行结果：', result)
                if result['success']:
                    result = self.handle_task({
                        "version": "1.0",
                        "type": "task",
                        "robot_type": "ARM_D",
                        "task_id": "ARM_D_1640995200123",
                        "skill_type": "close_door",
                        "target_object": "",
                        "target_location": "",
                        "source": "service"
                    })
                    print('任务D3执行结果：', result)
