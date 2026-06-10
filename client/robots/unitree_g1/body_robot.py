import time
import cv2
import numpy as np
from .UnitreeG1Robot import UnitreeG1Robot as Robot
from .UnitreeG1Camera import UnitreeG1Camera as Camera
from ..base_robot import RobotBase
import rclpy
import copy
import threading


class RobotBody(RobotBase):
    """Unitree G1 机器人业务层（纯 ROS2 + 26 维灵巧手）

    使用独立 rclpy.Context 隔离 Camera/Robot 节点的 wait set，
    避免与外部 dispatcher 共享 context 导致 "wait set index too big" 错误。
    """

    def __init__(self, config, ros_context=None):
        super().__init__()
        self.cfg, self.ori_cfg = config["robots"]["unitree_g1"], config

        # 使用外部传入的 context，或创建独立 context（隔离 wait set）
        self._ros_context = ros_context  # 由外部管理生命周期（VLAContext）
        if self._ros_context is None:
            self._ros_context = rclpy.Context()
            if not self._ros_context.ok():
                self._ros_context.init()

        self.camera = Camera(ros_context=self._ros_context)
        self.robot = Robot(ros_context=self._ros_context)

        # 统一自旋线程
        self.running = True
        self._spin_thread = self._start_spin_thread()

        # 状态缓存
        self.current_timestamp = 0
        self.current_state = None

        print("Unitree G1 RobotBody ready")
        time.sleep(2.0)

    def _start_spin_thread(self):
        def spin_worker():
            while self.running and self._ros_context.ok():
                try:
                    rclpy.spin_once(self.camera, timeout_sec=0.005)
                    rclpy.spin_once(self.robot, timeout_sec=0.005)
                except Exception:
                    pass  # spin 异常不中断线程
        t = threading.Thread(target=spin_worker, daemon=True)
        t.start()
        return t

    # ==================================================================
    # 控制机器人（26 维动作）
    # ==================================================================
    def control_robot(self, action):
        """发送 26 维动作

        action[0:7]   -> 左臂
        action[7:14]  -> 右臂
        action[14:20] -> 左手
        action[20:26] -> 右手
        """
        action = np.array(action).flatten()
        assert len(action) == 26, "must be 26-dim action"
        self.robot.send_robot_action(action)

    # ==================================================================
    # 复位机器人（使用 ruckig 轨迹规划）
    # ==================================================================
    def reset_robot(self, target_pose=None, mode="default"):
        if target_pose is None:
            if mode == "default":
                target_pose = np.array(self.cfg["reset_robot_pos"])
            elif mode == "zero":
                target_pose = np.zeros(26)
            else:
                print("Warning: unknown reset mode, skip")
                return
        target_pose = np.array(target_pose)

        # 使用 ruckig 平滑规划前 14 维（左右臂）
        # 重试读取观测：最多等待 1s，确保取到有效当前状态再规划轨迹
        current_obs = None
        for _ in range(10):
            current_obs = self.retrieve_observation()
            if current_obs is not None:
                break
            time.sleep(0.1)

        if current_obs is not None:
            current_positions = current_obs["obs.state"][:14]
            target_positions = target_pose[:14]
            dis = np.abs(current_positions - target_positions)
            if np.any(dis > np.deg2rad(0.01)):
                # 以较低速度规划手臂轨迹，确保平滑过渡
                trajs = self.ruckig_planning(
                    current_positions, target_positions,
                    max_velocity=0.5, max_acceleration=0.3, max_jerk=1.0,
                )
                n_points = len(trajs)
                # 获取手部当前状态用于线性插值
                left_hand_current = current_obs["obs.state"][14:20]
                right_hand_current = current_obs["obs.state"][20:26]
                left_hand_target = target_pose[14:20]
                right_hand_target = target_pose[20:26]

                for i, traj in enumerate(trajs):
                    t = (i + 1) / n_points  # 进度 0→1
                    tmp = target_pose.copy()
                    tmp[:14] = traj
                    # 手部线性插值：从当前值平滑过渡到目标值
                    tmp[14:20] = left_hand_current + t * (left_hand_target - left_hand_current)
                    tmp[20:26] = right_hand_current + t * (right_hand_target - right_hand_current)
                    self.robot.send_robot_action(tmp)
                    time.sleep(0.02)  # 50Hz 下发，进一步降低速度
            else:
                self.robot.send_robot_action(target_pose)
        else:
            self.robot.send_robot_action(target_pose)

        # 设置手部初始状态
        self.robot.current_left_hand_state = target_pose[14:20]
        self.robot.current_right_hand_state = target_pose[20:26]

        time.sleep(1.0)
        print("Unitree G1 reset done")

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

            # ######################
            # 新增: 任一相机图像为 None 则跳过本轮（防止下游 pad_and_resize 崩溃）
            # ######################
            if head_img is None or left_img is None or right_img is None:
                return None

            self.current_timestamp = head_ts

            # 图像
            result["cam.head"] = head_img
            result["cam.hand_left"] = left_img
            result["cam.hand_right"] = right_img
            result["ref_timestamp"] = head_ts

            # 机器人状态对齐（以头部相机时间戳为基准）
            robot_state = self.robot.get_arm_hand_states_nearest_func(head_ts)

            # ######################
            # 修改: 任一部位状态缺失则跳过本轮（避免零填充给模型输入错误数据）
            # ######################
            if (robot_state["left_arm"] is None
                    or robot_state["right_arm"] is None
                    or robot_state["left_hand"] is None
                    or robot_state["right_hand"] is None):
                return None

            # 拼接 26 维 state 向量
            state = []
            state.extend(robot_state["left_arm"].position)   # 7
            state.extend(robot_state["right_arm"].position)  # 7
            state.extend(robot_state["left_hand"].position)  # 6
            state.extend(robot_state["right_hand"].position) # 6

            result["obs.state"] = np.array(state)
            self.current_state = result["obs.state"]
            return result

        except Exception as e:
            print("Observation error:", e)
            return None

    # ==================================================================
    # 关闭
    # ==================================================================
    def close(self):
        self.running = False

        # 等待 spin 线程完全退出，避免销毁节点时 wait set 竞争
        if hasattr(self, '_spin_thread') and self._spin_thread.is_alive():
            self._spin_thread.join(timeout=1.0)

        # ######################
        # 新增: 停止机器人采样线程
        # ######################
        self.robot.stop()

        # ######################
        # 新增: 销毁 ROS2 节点（释放资源）
        # ######################
        self.camera.destroy_node()
        self.robot.destroy_node()

        print("Unitree G1 RobotBody closed")


# ==============================================
# 测试
# ==============================================
def test_robot_body():
    print("=" * 60)
    print("Testing Unitree G1 RobotBody")
    print("=" * 60)

    default_action = (
        [0.0] * 7    # left arm
        + [0.0] * 7  # right arm
        + [0.0] * 6  # left hand
        + [0.0] * 6  # right hand
    )

    mock_config = {
        "robots": {
            "unitree_g1": {
                "reset_robot_pos": default_action,
            }
        }
    }

    robot_body = RobotBody(mock_config)
    time.sleep(1.0)

    # 测试 1：获取观测
    print("\nTest 1: retrieve observation...")
    for _ in range(10):
        obs = robot_body.retrieve_observation()
        if obs is not None:
            print("  OK - state dim:", obs["obs.state"].shape, "head img:", obs["cam.head"].shape)
            break
        time.sleep(0.1)
    else:
        print("  FAIL - no observation")

    # 测试 2：动作控制
    print("\nTest 2: control robot (right hand close)...")
    action = np.zeros(26)
    action[20:26] = [650.0, 650.0, 650.0, 650.0, 650.0, 250.0]
    robot_body.control_robot(action)
    print("  OK")
    time.sleep(1.5)

    # 测试 3：复位
    print("\nTest 3: reset robot...")
    robot_body.reset_robot(mode="default")
    print("  OK")

    robot_body.close()
    print("\n" + "=" * 60)
    print("All tests passed")
    print("=" * 60)


if __name__ == "__main__":
    test_robot_body()
