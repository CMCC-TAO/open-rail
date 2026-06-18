"""
放置任务 - 基于录制轨迹回放（左手/右手/单手/双手）

从 replay_data/ 加载 parquet 轨迹数据，进行插值+平滑后回放。
支持从任意当前位置过渡到轨迹起始位置，回放完成后打开手部释放物体。

任务接口:
  {
    "task": "left arm place",    # 左手放置
    "target": "none",
    "waypoint": "none"
  }
  {
    "task": "right arm place",   # 右手放置
    "target": "none",
    "waypoint": "none"
  }
  {
    "task": "one arm place",     # 单手放置（自动判断哪只手有物体）
    "target": "none",
    "waypoint": "none"
  }
  {
    "task": "both arm place",    # 双手放置
    "target": "none",
    "waypoint": "none"
  }
"""

import sys
import os
import time
import numpy as np

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pandas as pd

from action_server.action_base import (
    AbstractTaskHandler, TaskResult, send_vla_feedback,
    ERR_PLACE_LEFT_EMPTY, ERR_PLACE_RIGHT_EMPTY,
    ERR_PLACE_ONE_HAND_BOTH_EMPTY, ERR_PLACE_BOTH_HAND_NOT_BOTH,
    ERR_PLACE_ONE_HAND_STILL_HOLDING,
)


# ==============================================
# 常量
# ==============================================
_REPLAY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "replay_data")

CONTROL_INTERVAL = 0.02          # 50Hz
SRC_HZ = 30.0                    # 录制数据频率
DST_HZ = 50.0                    # 回放目标频率
TRANSITION_DURATION = 1.5        # 过渡阶段时长（秒）
HAND_OPEN_HOLD_TIME = 1.5        # 手部打开后保持时间（秒）
ARM_DIM = 7                      # 单臂关节数
HAND_DIM = 6                     # 单手手指数
FULL_DIM = 26                    # 完整动作维度 [左臂7, 右臂7, 左手6, 右手6]

# 轨迹文件映射
_PLACE_FILES = {
    "left arm place":  "left_hand_place.parquet",
    "right arm place": "right_hand_place.parquet",
    "both arm place":  "both_hand_place.parquet",
}

# 平滑窗口（必须为奇数）
SMOOTH_WINDOW = 5


class PlaceHandler(AbstractTaskHandler):
    """放置任务处理器

    由 dispatcher 路由到以下 4 个 task name 之一:
      - "left arm place"
      - "right arm place"
      - "one arm place"
      - "both arm place"
    """

    @property
    def task_name(self) -> str:
        return "place"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        task = params.get("task", "")

        if task == "left arm place":
            return self._left_arm_place(goal_handle, context)
        elif task == "right arm place":
            return self._right_arm_place(goal_handle, context)
        elif task == "one arm place":
            return self._one_arm_place(goal_handle, context)
        elif task == "both arm place":
            return self._both_arm_place(goal_handle, context)
        else:
            self.send_feedback(goal_handle, 0, f"未知放置子任务: {task}")
            return TaskResult(False, error_code=99,
                              error_message=f'Unknown place sub-task: "{task}"')

    # ================================================================
    # 工具方法
    # ================================================================

    def _get_current_full_state(self, robot_body) -> np.ndarray | None:
        """获取当前 26 维完整状态 [左臂7, 右臂7, 左手6, 右手6]

        优先级:
          1. robot_body.current_state（由 VLA 观察线程缓存）
          2. 直接从 robot_body.robot 的 ROS2 订阅缓存读取（不依赖相机）
          3. retrieve_observation() 回退（需要相机数据）
        """
        # 优先级 1: 使用 VLA 缓存的状态
        try:
            cs = getattr(robot_body, 'current_state', None)
            if cs is not None:
                return cs.copy()
        except Exception:
            pass

        # 优先级 2: 直接从 ROS2 缓存读取关节状态（不依赖相机）
        try:
            robot = robot_body.robot
            la = robot.latest_left_arm
            ra = robot.latest_right_arm
            lh = robot.latest_left_hand
            rh = robot.latest_right_hand
            if all(x is not None for x in (la, ra, lh, rh)):
                la_msg, _ = la
                ra_msg, _ = ra
                lh_msg, _ = lh
                rh_msg, _ = rh
                if (la_msg and ra_msg and lh_msg and rh_msg
                        and la_msg.position and ra_msg.position
                        and lh_msg.position and rh_msg.position):
                    state = np.array(
                        list(la_msg.position)
                        + list(ra_msg.position)
                        + list(lh_msg.position)
                        + list(rh_msg.position),
                        dtype=float,
                    )
                    robot_body.current_state = state.copy()
                    return state
        except Exception:
            pass

        # 优先级 3: 回退 retrieve_observation（需要相机数据）
        for _ in range(20):
            obs = robot_body.retrieve_observation()
            if obs is not None and "obs.state" in obs:
                state = obs["obs.state"]
                return state
            time.sleep(0.05)
        return None

    def _load_parquet_trajectory(self, parquet_path: str, key: str = "action") -> np.ndarray:
        """加载 parquet 轨迹数据

        Returns:
            (N, D) numpy 数组，D 为动作维度
        """
        df = pd.read_parquet(parquet_path)
        if key not in df.columns:
            raise KeyError(f"Parquet missing column '{key}': {list(df.columns)}")

        actions = df[key].tolist()
        traj = np.array([np.asarray(a, dtype=np.float64).flatten() for a in actions])
        return traj

    def _upsample_trajectory(self, traj: np.ndarray) -> np.ndarray:
        """将轨迹从 SRC_HZ 线性插值到 DST_HZ"""
        n_src = len(traj)
        if n_src <= 1:
            return traj

        duration = (n_src - 1) / SRC_HZ
        src_times = np.linspace(0, duration, n_src)
        dst_times = np.arange(0, duration, 1.0 / DST_HZ)
        # 确保包含终点
        if len(dst_times) == 0 or abs(dst_times[-1] - duration) > 1e-6:
            dst_times = np.append(dst_times, duration)

        n_dst = len(dst_times)
        d = traj.shape[1]
        result = np.zeros((n_dst, d), dtype=np.float64)
        for dim in range(d):
            result[:, dim] = np.interp(dst_times, src_times, traj[:, dim])
        return result

    def _smooth_trajectory(self, traj: np.ndarray) -> np.ndarray:
        """移动平均平滑"""
        n = len(traj)
        if n < SMOOTH_WINDOW:
            return traj
        half = SMOOTH_WINDOW // 2
        kernel = np.ones(SMOOTH_WINDOW) / SMOOTH_WINDOW
        result = traj.copy()
        for dim in range(traj.shape[1]):
            # 边界值填充，使卷积结果长度不变
            padded = np.pad(traj[:, dim], (half, half), mode='edge')
            smoothed = np.convolve(padded, kernel, mode='valid')
            result[:, dim] = smoothed
        return result

    def _load_and_process_trajectory(self, parquet_path: str) -> np.ndarray:
        """完整流水线：加载 → 插值 → 平滑，返回 (M, D) 轨迹"""
        traj = self._load_parquet_trajectory(parquet_path)
        traj = self._upsample_trajectory(traj)
        traj = self._smooth_trajectory(traj)

        # 确保维度为 26
        if traj.shape[1] < FULL_DIM:
            pad = np.zeros((traj.shape[0], FULL_DIM - traj.shape[1]))
            traj = np.concatenate([traj, pad], axis=1)
        elif traj.shape[1] > FULL_DIM:
            traj = traj[:, :FULL_DIM]

        return traj

    def _transition_to_trajectory(
        self, robot_body, current_state: np.ndarray,
        first_action: np.ndarray,
        goal_handle, start_progress: int, end_progress: int,
        which_arm: str = "both",
    ) -> bool:
        """从当前位置线性插值到轨迹起始位置

        Args:
            which_arm: "left" / "right" / "both" — 哪一侧手臂需要过渡
        """
        num_steps = max(1, int(TRANSITION_DURATION / CONTROL_INTERVAL))
        actual_interval = TRANSITION_DURATION / num_steps

        robot = robot_body.robot
        orig_relative = getattr(robot, 'enable_relative_clamp', True)
        robot.enable_relative_clamp = False
        try:
            for step in range(num_steps):
                t = (step + 1) / num_steps
                action = current_state.copy()

                if which_arm in ("left", "both"):
                    action[0:ARM_DIM] = (
                        current_state[0:ARM_DIM]
                        + t * (first_action[0:ARM_DIM] - current_state[0:ARM_DIM])
                    )
                if which_arm in ("right", "both"):
                    action[ARM_DIM:2 * ARM_DIM] = (
                        current_state[ARM_DIM:2 * ARM_DIM]
                        + t * (first_action[ARM_DIM:2 * ARM_DIM] - current_state[ARM_DIM:2 * ARM_DIM])
                    )
                # 手掌保持当前值，避免中途松开
                robot.send_robot_action(action)

                pct = start_progress + int((end_progress - start_progress) * (step + 1) / num_steps)
                send_vla_feedback(goal_handle, pct,
                                  f"过渡到轨迹起始... {t * 100:.0f}%")
                time.sleep(actual_interval)
        finally:
            robot.enable_relative_clamp = orig_relative

        return True

    def _replay_full_trajectory(
        self, robot_body, trajectory: np.ndarray,
        current_state: np.ndarray,
        goal_handle, start_progress: int, end_progress: int,
        which_arm: str = "both",
    ) -> None:
        """回放完整轨迹

        只控制指定手臂跟随轨迹，非活跃手臂保持当前位置，手掌保持当前值。
        """
        robot = robot_body.robot
        orig_relative = getattr(robot, 'enable_relative_clamp', True)
        robot.enable_relative_clamp = False
        try:
            n_frames = len(trajectory)
            for i, frame in enumerate(trajectory):
                action = current_state.copy()
                # 手臂跟随轨迹
                if which_arm in ("left", "both"):
                    action[0:ARM_DIM] = frame[0:ARM_DIM]
                if which_arm in ("right", "both"):
                    action[ARM_DIM:2 * ARM_DIM] = frame[ARM_DIM:2 * ARM_DIM]
                # 手掌保持当前值（末尾统一打开）
                robot.send_robot_action(action)

                pct = start_progress + int((end_progress - start_progress) * (i + 1) / n_frames)
                send_vla_feedback(goal_handle, pct,
                                  f"轨迹回放中... {i + 1}/{n_frames}")
                time.sleep(CONTROL_INTERVAL)
        finally:
            robot.enable_relative_clamp = orig_relative

    def _open_hand_and_verify(
        self, robot_body, hand_side: str,
        goal_handle, grasp_detector=None,
    ) -> bool:
        """打开手部并验证物体已释放

        Returns:
            True 表示释放成功，False 表示仍有物体
        """
        current_state = self._get_current_full_state(robot_body)
        if current_state is None:
            return False

        action = current_state.copy()
        zero_hand = np.zeros(HAND_DIM)

        if hand_side in ('left', 'both'):
            action[14:20] = zero_hand
        if hand_side in ('right', 'both'):
            action[20:26] = zero_hand

        robot_body.control_robot(action)
        side_label = {'left': '左手', 'right': '右手', 'both': '双手'}.get(hand_side, hand_side)
        send_vla_feedback(goal_handle, 95, f"{side_label}已打开，确认释放...")
        time.sleep(HAND_OPEN_HOLD_TIME)

        # 用 grasp_detector 验证是否已释放
        if grasp_detector is not None:
            gs = grasp_detector.grasp_state
            if hand_side == 'left' and gs[0]:
                return False
            if hand_side == 'right' and gs[1]:
                return False
            if hand_side == 'both' and (gs[0] or gs[1]):
                return False
        return True

    # ================================================================
    # 放置逻辑
    # ================================================================

    def _do_place(
        self, goal_handle, context,
        which_arm: str,
    ) -> TaskResult:
        """通用放置流程"""
        robot_body = context.robot_body

        # 1. 加载轨迹
        task_key = f"{which_arm} arm place"
        parquet_file = _PLACE_FILES.get(task_key)
        if parquet_file is None:
            return TaskResult(False, error_code=99,
                              error_message=f"No parquet file for {task_key}")
        parquet_path = os.path.join(_REPLAY_DIR, parquet_file)
        if not os.path.exists(parquet_path):
            return TaskResult(False, error_code=99,
                              error_message=f"Parquet file not found: {parquet_path}")

        send_vla_feedback(goal_handle, 5, f"{which_arm}放置开始")
        trajectory = self._load_and_process_trajectory(parquet_path)
        if len(trajectory) == 0:
            return TaskResult(False, error_code=99,
                              error_message="Loaded empty trajectory from parquet")

        # 2. 获取当前状态
        current_state = self._get_current_full_state(robot_body)
        if current_state is None:
            return TaskResult(False, error_code=99,
                              error_message="Failed to get current robot state")

        # 3. 过渡阶段：从当前位置 → 轨迹起始
        self._transition_to_trajectory(
            robot_body, current_state, trajectory[0],
            goal_handle, start_progress=10, end_progress=20,
            which_arm=which_arm,
        )

        # 4. 回放完整轨迹（手掌保持当前值，不随轨迹变化）
        self._replay_full_trajectory(
            robot_body, trajectory, current_state,
            goal_handle, start_progress=20, end_progress=90,
            which_arm=which_arm,
        )

        # 5. 打开手部释放物体
        hand_side = which_arm
        released = self._open_hand_and_verify(
            robot_body, hand_side,
            goal_handle,
            grasp_detector=context.grasp_detector,
        )

        final_msg = f"{which_arm}放置完成"
        if not released:
            final_msg += "（但物体可能未完全释放）"
        send_vla_feedback(goal_handle, 100, final_msg)

        if not released and which_arm == "both":
            return TaskResult(False, error_code=ERR_PLACE_ONE_HAND_STILL_HOLDING,
                              error_message="One hand still holding object after both arm place")

        return TaskResult(True)

    def _left_arm_place(self, goal_handle, context) -> TaskResult:
        """左手放置"""
        grasp_state = context.grasp_detector.grasp_state
        if not grasp_state[0]:
            send_vla_feedback(goal_handle, 0, "左手没有物体，无法放置")
            return TaskResult(False, error_code=ERR_PLACE_LEFT_EMPTY,
                              error_message="Left hand is empty, cannot do left arm place")
        return self._do_place(goal_handle, context, which_arm="left")

    def _right_arm_place(self, goal_handle, context) -> TaskResult:
        """右手放置"""
        grasp_state = context.grasp_detector.grasp_state
        if not grasp_state[1]:
            send_vla_feedback(goal_handle, 0, "右手没有物体，无法放置")
            return TaskResult(False, error_code=ERR_PLACE_RIGHT_EMPTY,
                              error_message="Right hand is empty, cannot do right arm place")
        return self._do_place(goal_handle, context, which_arm="right")

    def _one_arm_place(self, goal_handle, context) -> TaskResult:
        """单手放置：自动判断哪只手有物体"""
        grasp_state = context.grasp_detector.grasp_state

        if grasp_state[1]:   # 右手有物体 → 右手放置
            send_vla_feedback(goal_handle, 5, "检测到右手有物体，执行右手放置")
            return self._right_arm_place(goal_handle, context)
        elif grasp_state[0]:  # 左手有物体 → 左手放置
            send_vla_feedback(goal_handle, 5, "检测到左手有物体，执行左手放置")
            return self._left_arm_place(goal_handle, context)
        else:
            send_vla_feedback(goal_handle, 0, "双手都没有物体，无法放置")
            return TaskResult(False, error_code=ERR_PLACE_ONE_HAND_BOTH_EMPTY,
                              error_message="Both hands are empty, cannot do one arm place")

    def _both_arm_place(self, goal_handle, context) -> TaskResult:
        """双手放置：双手必须同时有物体"""
        grasp_state = context.grasp_detector.grasp_state
        if not (grasp_state[0] and grasp_state[1]):
            send_vla_feedback(goal_handle, 0, "双手没有同时有物体，无法放置")
            return TaskResult(False, error_code=ERR_PLACE_BOTH_HAND_NOT_BOTH,
                              error_message="Not both hands have objects, cannot do both arm place")
        return self._do_place(goal_handle, context, which_arm="both")
