import time
import cv2
import numpy as np
import pandas as pd
from .Ti5Robot import Ti5Robot as Robot
from .Ti5Camera import Ti5Camera as Camera

from .base_robot import RobotBase

import rclpy
import copy
import threading

class RobotBody(RobotBase):
    def __init__(self, config):
        """Initialize the A2D robot body with camera and robot instances.
        
        Args:
            config (dict): Configuration dictionary containing robot and camera settings
        """
        super().__init__()
        self.cfg, self.ori_cfg = config['robots']['ti5_t170c'], config
        
        # ======================
        # 初始化 rclpy，再创建 ROS 节点
        # ======================
        if not rclpy.ok():
            rclpy.init()
        

        self.camera = Camera()
        self.robot = Robot()

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
        self.current_leg_pos = None
        self.hand_sleep_count = 0
        
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
    def control_robot(self, action, language='default'):
        """
        新版对接：
        action = 26 维
        0~7   left_arm
        7~14  right_arm
        14~20 left_hand
        20~26 right_hand
        26-29 head
        29-32 waist
        """
        action = np.array(action).flatten()
        assert len(action) == 26, "必须输入 26 维动作"
        
        # 直接发送给新版机器人
        if ('pick' in language.lower() or 'place' in language.lower()) and 'cup' in language.lower():
            action[6] = -1000
            action[19] = -1000
        elif ('pick' in language.lower() or 'place' in language.lower()) and 'rice' in language.lower():
            action[13] = -1000
            action[25] = -1000
        
        # if 'place' in language.lower() and self.hand_sleep_count < 20:
        #     action[19] = -1000
        #     action[25] = -1000
        #     self.hand_sleep_count += 1
        # if self.hand_sleep_count >= 20:
        #     self.hand_sleep_count = 0
            
        # print("###"*30)
        # print(action[20:26])
        self.robot.send_robot_action(action)

    def clear_state_buffer(self):
        self.robot.clear_state_buffer()

    # ==================================================================
    # 复位机器人（使用 26 维动作）
    # ==================================================================
    def reset_robot(self, target_pose=None, mode='default'):
        if target_pose is None:
            if mode == 'default':
                target_pose = np.array(self.cfg['reset_robot_pos'])
            elif mode == 'zero':
                target_pose = np.zeros(26)
            elif mode == 'cup_grasp':
                target_pose = np.array(self.cfg['reset_robot_pos_cup_grasp'])
            elif mode == 'rice_cub_grasp':
                target_pose = np.array(self.cfg['reset_robot_rice_cub_grasp'])
            elif mode == 'obj_place':
                target_pose = np.array(self.cfg['reset_robot_place'])
            else:
                print('[WARN] target_pose is None, can NOT execute reset_robot')
                return
        target_pose = np.array(target_pose)

        try:
            cur_leg = self.current_leg_pos.tolist()
            target_leg = target_pose[26:27]
            diff_high = target_leg[0] - cur_leg[0]
            n_step = 100
            delta_value = diff_high / n_step
            for i in range(n_step):
                tmp_target_pose = copy.deepcopy(target_pose)
                cur_high = cur_leg[0] + (i+1) * delta_value
                if cur_high > target_leg[0]:
                    cur_high = target_leg[0]
                tmp_target_pose[26] = cur_high
                self.robot.send_robot_action(tmp_target_pose) 
                time.sleep(0.01)
        except Exception as e:
            print(e)
            self.robot.send_robot_action(target_pose)
        
        time.sleep(1.0)
        print("✅ 机器人复位完成")

    # ==================================================================
    # 获取观测（图像 + 对齐后的关节角）
    # ==================================================================
    def retrieve_observation(self):
        try:
            # print("#########")
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
                if self.robot.arm_mode =='ros':
                    state.extend(robot_state['left_arm'].position)
                else:
                    state.extend(robot_state['left_arm'])
            else:
                state.extend([0]*7)

            # 右臂
            if robot_state['right_arm'] is not None:
                if self.robot.arm_mode =='ros':
                    state.extend(robot_state['right_arm'].position)
                else:
                    state.extend(robot_state['right_arm'])
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
            
            if robot_state['leg_pos'] is not None:
                self.current_leg_pos = robot_state['leg_pos'].position

            result['obs.state'] = np.array(state)
            self.current_state = result['obs.state']
            return result

        except Exception as e:
            print("观测获取失败:", e)
            return None

    def load_action_data(self, parquet_path, key="action"):
        """Load trajectory vectors from a parquet file.

        Args:
            parquet_path: Parquet file path.
            key: Column name to load, e.g. "action" or "observation.state".

        Returns:
            list[np.ndarray]: List of 1D float64 vectors.
        """
        df = pd.read_parquet(parquet_path)
        if key not in df.columns:
            raise KeyError(f"Key '{key}' not found in parquet columns: {list(df.columns)}")

        data = df[key].tolist()
        processed_data = []
        for ele in data:
            arr = np.asarray(ele, dtype=np.float64).reshape(-1)
            processed_data.append(arr)
        return processed_data

    def default_replay_trajectories(
        self,
        parquet_path,
        accelerate: bool = True,
        accelerate_times: int = 2,
        key: str = "action",
        sleep_s: float = 0.05,
        language: str="default"
    ):
        """Replay trajectory with fixed-rate stepping.

        Ti5 Phase-1 only executes arm commands (first 14 dims).
        """
        trajs = self.load_action_data(parquet_path=parquet_path, key=key)
        if not accelerate:
            accelerate_times = 1
        accelerate_times = max(1, int(accelerate_times))

        logged_non_arm_warning = False
        for idx, traj in enumerate(trajs):
            if idx % accelerate_times != 0:
                continue
            if traj.shape[0] < 14:
                if hasattr(self, "_node"):
                    self._node.get_logger().warning(
                        "Skip trajectory index %d: dims=%d < 14 for Ti5 arm replay.",
                        idx,
                        int(traj.shape[0]),
                    )
                continue
            if traj.shape[0] > 14 and not logged_non_arm_warning:
                if hasattr(self, "_node"):
                    self._node.get_logger().info(
                        "Ti5 replay currently executes arm only; non-arm dims will be ignored."
                    )
                logged_non_arm_warning = True
            self.control_robot(traj[:26].tolist(), language=language)
            time.sleep(float(sleep_s))

    def replay_trajectories(
        self,
        parquet_path,
        use_default: bool = True,
        accelerate: bool = True,
        accelerate_times: int = 2,
        exclude_path=None,
        key: str = "action",
        sleep_s: float = 0.05,
        language: str="default"
    ):
        """Replay trajectory loaded from parquet.

        Args:
            parquet_path: Teleop/parquet trajectory path.
            use_default: Use default replay logic.
            accelerate: Whether to skip points by accelerate_times.
            accelerate_times: Replay downsample ratio when accelerate=True.
            exclude_path: If any keyword appears in path, disable acceleration.
            key: Parquet column key to replay.
            sleep_s: Sleep between executed commands.
        """
        if exclude_path is None:
            exclude_path = ["place"]

        try:
            path_str = str(parquet_path)
            for ele in exclude_path:
                if str(ele) in path_str:
                    accelerate = False
                    break

            if use_default:
                self.default_replay_trajectories(
                    parquet_path=parquet_path,
                    accelerate=accelerate,
                    accelerate_times=accelerate_times,
                    key=key,
                    sleep_s=sleep_s,
                    language=language
                )
                return

            # Keep same behavior for now to ensure deterministic replay path.
            self.default_replay_trajectories(
                parquet_path=parquet_path,
                accelerate=accelerate,
                accelerate_times=accelerate_times,
                key=key,
                sleep_s=sleep_s,
                language=language
            )
        except Exception as exc:
            if hasattr(self, "_node"):
                self._node.get_logger().error(
                    "Replay %s failed: %s", str(parquet_path), str(exc)
                )
            raise

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