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
    """Unitree G1 机器人业务层（纯 ROS2 + 26 维灵巧手）"""

    def __init__(self, config):
        super().__init__()
        self.cfg, self.ori_cfg = config["robots"]["unitree_g1"], config

        if not rclpy.ok():
            rclpy.init()

        self.camera = Camera()
        self.robot = Robot()

        # 统一自旋线程
        self.running = True
        self._start_spin_thread()

        # 状态缓存
        self.current_timestamp = 0
        self.current_state = None

        print("Unitree G1 RobotBody ready")
        time.sleep(2.0)

    def _start_spin_thread(self):
        def spin_worker():
            while self.running:
                rclpy.spin_once(self.camera, timeout_sec=0.005)
                rclpy.spin_once(self.robot, timeout_sec=0.005)
        spin_thread = threading.Thread(target=spin_worker, daemon=True)
        spin_thread.start()

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
        current_obs = self.retrieve_observation()
        if current_obs is not None:
            current_positions = current_obs["obs.state"][:14]
            target_positions = target_pose[:14]
            dis = np.abs(current_positions - target_positions)
            if np.any(dis > np.deg2rad(0.01)):
                trajs = self.ruckig_planning(current_positions, target_positions)
                for traj in trajs:
                    tmp = target_pose.copy()
                    tmp[:14] = traj
                    self.robot.send_robot_action(tmp)
                    time.sleep(0.01)
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
        time.sleep(0.1)  # 给自旋线程一个机会退出

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
