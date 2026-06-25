import time
import cv2
import numpy as np
import pandas as pd
from .Ti5Robot import Ti5Robot as Robot
from .Ti5Camera import Ti5Camera as Camera

from ..base_robot import RobotBase

import rclpy
import threading

class RobotBody(RobotBase):
    def __init__(self, config):
        """Initialize the A2D robot body with camera and robot instances.
        
        Args:
            config (dict): Configuration dictionary containing robot and camera settings
        """
        super().__init__(config)
        self.cfg = config
        
        # ======================
        # 初始化 rclpy，再创建 ROS 节点
        # ======================
        if not rclpy.ok():
            rclpy.init()

        self.camera = Camera(self.cfg)
        self.robot = Robot(self.cfg)

        # ======================
        # 统一自旋
        # ======================
        self.running = True
        self._start_spin_thread()

        # 夹爪状态缓存
        self.gripper_cmd = np.zeros(2)
        self.gripper_count = 0
        self.current_timestamp = 0
        self.current_state = None
        
        print("✅ RobotBody 初始化完成！")
        time.sleep(2.0)


    def _start_spin_thread(self):
        def spin_worker():
            while self.running:
                rclpy.spin_once(self.camera, timeout_sec=0.005)
                rclpy.spin_once(self.robot, timeout_sec=0.005)
        spin_thread = threading.Thread(target=spin_worker, daemon=True)
        spin_thread.start()

    # ==================================================================
    # 控制机器人（接收 26 维动作！）
    # ==================================================================
    def control_robot(self, action):
        """
        action序列拼接顺序：
        action = 26 维
        0~7   left_arm
        7~14  right_arm
        14~20 left_hand
        20~26 right_hand
        """
        action = np.array(action).flatten()
        assert len(action) == 26, "必须输入 26 维动作"
        
        # 直接发送给新版机器人
        self.robot.send_robot_action(action)

    # ==================================================================
    # 控制机器人部分关节
    # ==================================================================
    def control_robot_partial(self, name="default", action=[0.0]):

        action = np.array(action).flatten()
        
        # 直接发送给新版机器人
        self.robot.send_partial_action(name, action)

    # ==================================================================
    # 复位机器人（使用 26 维动作）
    # ==================================================================
    def reset_robot(self, target_pose=None, mode='default'):
        if target_pose is None:
            if mode == 'default':
                target_pose = np.array(self.cfg['reset_robot_pos'])
            elif mode == 'zero':
                target_pose = np.zeros(26)
            else:
                print('[WARN] target_pose is None, can NOT execute reset_robot')
                return

        target_pose = np.array(target_pose)
        self.robot.send_robot_action(target_pose[:26])
        time.sleep(1.0)
        print("✅ 机器人复位完成")

    # ==================================================================
    # 获取观测（图像 + 对齐后的关节角）
    # ==================================================================
    def retrieve_observation(self):
        try:
            result = {}
            cam_data = self.camera.get_latest_image()
            if not cam_data:
                return None

            head_img, head_ts, left_img, left_ts, right_img, right_ts = cam_data
            if self.current_timestamp == head_ts:
                return None

            self.current_timestamp = head_ts

            # 图像
            result['cam.head'] = head_img
            result['cam.hand_left'] = left_img
            result['cam.hand_right'] = right_img
            result['ref_timestamp'] = head_ts

            # 机器人状态对齐
            robot_state = self.robot.get_arm_hand_states_nearest_func(head_ts)

            # 拼接成 state 向量
            state = []
            
            # 左臂
            if robot_state['left_arm'] is not None:
                state.extend(robot_state['left_arm'].position)
            else:
                state.extend([0]*7)

            # 右臂
            if robot_state['right_arm'] is not None:
                state.extend(robot_state['right_arm'].position)
            else:
                state.extend([0]*7)

            # 左手
            if robot_state['left_hand'] is not None:
                state.extend(robot_state['left_hand'].position)
            else:
                state.extend([0]*6)

            # 右手
            if robot_state['right_hand'] is not None:
                state.extend(robot_state['right_hand'].position)
            else:
                state.extend([0]*6)

            result['obs.state'] = np.array(state)
            self.current_state = result['obs.state']
            return result

        except Exception as e:
            print("观测获取失败:", e)
            return None

    # ==================================================================
    # 关闭
    # ==================================================================
    def close(self):
        self.running = False
        print('✅ RobotBody 已安全关闭')


# ==============================================
# 测试脚本（直接运行此文件即可测试）
# ==============================================
def test_robot_body():
    # rclpy.init()
    print("=" * 60)
    print("🤖 开始测试 RobotBody + Ti5Camera + Ti5Robot")
    print("=" * 60)

    default_action = [
        -1.681951211214541, 1.5263110171042418, 2.2737134617553534, -0.23620356347006893, -0.5204031154482495, 0.1292378813793631, 0.19059726269759902
      ] + \
      [
        1.3119088393316176, 1.4473110065281325, -1.6156086726673602, -1.665472635653567, 0.4101313352460489, -0.2251850174207321, 0.3232027944991513
      ] + \
      [
        1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0
      ] + \
      [
        650.0, 650.0, 650.0, 650.0, 650.0, 250.0
      ]

    # 模拟配置（你真实运行时会从配置文件加载）
    mock_config = {
        'robots': {
            'ti5_t170c': {
                'reset_robot_pos': default_action,
                'gripper_freq': 5
            }
        }
    }

    # 初始化
    robot_body = RobotBody(mock_config)
    time.sleep(1.0)

    # ----------------------
    # 测试 1：获取观测（图像 + 26维状态）
    # ----------------------
    print("\n📷 测试1：获取观测数据...")
    for _ in range(10):
        obs = robot_body.retrieve_observation()
        if obs is not None:
            print("✅ 观测获取成功！")
            print(f"   时间戳: {obs['ref_timestamp']:.6f}")
            print(f"   状态维度: {obs['obs.state'].shape} (正确=26)")
            print(f"   头部图像: {obs['cam.head'].shape}")
            print(f"   左手图像: {obs['cam.hand_left'].shape}")
            print(f"   右手图像: {obs['cam.hand_right'].shape}")
            break
        time.sleep(0.1)
    else:
        print("❌ 未获取到观测数据")

    # ----------------------
    # 测试 2：动作控制（右手握拳）
    # ----------------------
    print("\n🎮 测试2：发送26维动作 - 右手握拳...")
    action = np.zeros(26)
    action[20:26] = [650.0, 650.0, 650.0, 650.0, 650.0, 250.0]
    robot_body.control_robot(action)
    print("✅ 右手握拳指令已发送！")
    time.sleep(1.5)

    # ----------------------
    # 测试 3：复位机器人
    # ----------------------
    print("\n🔄 测试3：机器人复位...")
    robot_body.reset_robot(mode='default')
    time.sleep(0.5)

    # 结束
    robot_body.close()
    print("\n" + "=" * 60)
    print("🎉 所有测试全部通过！")
    print("=" * 60)


if __name__ == '__main__':
    test_robot_body()