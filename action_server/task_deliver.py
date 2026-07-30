"""
递物任务 - 将物体递出（左手/右手/单手/双手）

不需要 VLA 推理，直接使用预设的递物位姿 + 线性插值轨迹。

任务接口:
  {
    "task": "deliver",        # 左手递物
    "target": "left arm",     # 抓取的目标
    "waypoint": "none"
  }
  {
    "task": "deliver",        # 右手递物
    "target": "right arm",    # 抓取的目标
    "waypoint": "none"
  }
  {
    "task": "deliver",        # 单手递物（自动判断哪只手有物体）
    "target": "one arm",      # 抓取的目标
    "waypoint": "none"
  }
  {
    "task": "deliver",        # 双手递物
    "target": "both arm",     # 抓取的目标
    "waypoint": "none"
  }
"""

import sys
import os
import time
import math
from collections import deque
import numpy as np

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.action_base import (
    AbstractTaskHandler, TaskResult, send_vla_feedback,
    ERR_DELIVER_TIMEOUT, ERR_DELIVER_LEFT_EMPTY, ERR_DELIVER_RIGHT_EMPTY,
    ERR_DELIVER_ONE_HAND_BOTH_EMPTY, ERR_DELIVER_BOTH_HAND_NOT_BOTH,
    ERR_DELIVER_ONE_HAND_STILL_HOLDING,
)

# 判断触觉传感器消息类型是否可用（决定使用触觉还是关节角度检测拖拽）
try:
    from message_center.msg import TouchStatus  # noqa: F401
    _HAS_TOUCH_STATUS = True
except ImportError:
    _HAS_TOUCH_STATUS = False

# ==============================================
# 递物目标位姿（7 关节，弧度）
# ==============================================
LEFT_DELIVER_POSE = np.array([-1.0, 0.1, 0.0, 0.5, 0.0, 0.0, 0.0])
RIGHT_DELIVER_POSE = np.array([-1.0, -0.1, 0.0, 0.5, 0.0, 0.0, 0.0])

# ==============================================
# 时间常量
# ==============================================
HAND_OPEN_HOLD_TIME = 1.0       # 手掌打开后保持时长（秒）

# ==============================================
# 拖拽检测参数（关节角度方案 - 回退用）
# ==============================================
TUG_DETECTION_THRESHOLD_DEG = 3.0   # 拖拽检测阈值（度），手腕关节偏差超过此值触发松手
TUG_DETECTION_TIMEOUT = 30.0        # 等待拖拽超时（秒），超时后强制松手
TUG_STABILIZE_TIME = 1.0            # 到位后等待 state 稳定的时间（秒）
TUG_MONITOR_INTERVAL = 0.05         # 监测周期（秒），~20Hz

# ==============================================
# 拖拽检测参数（触觉传感器方案 - 滚动基线）
# ==============================================
TOUCH_TF_DIFF_ABS = 100             # 切向力下降绝对阈值（兜底值）
TOUCH_TF_DIFF_RATIO = 0.1           # 切向力下降相对比例阈值
_TOUCH_ROLLING_SIZE = 20            # 滚动基线窗口帧数（0.05s × 20 = 1s）
                                    # 递送到位后持续维护 tf_sum 的 1 秒滑动窗口中位数作为实时基线
                                    # 缓慢漂移会被滚动基线自动吸收，只有快速下降才会触发


class DeliverHandler(AbstractTaskHandler):
    """递物任务处理器

    由 dispatcher 路由到以下 4 个 task:target 复合键之一:
      - "deliver:left arm"
      - "deliver:right arm"
      - "deliver:one arm"
      - "deliver:both arm"
    """

    @property
    def task_name(self) -> str:
        return "deliver"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        target = params.get("target", "")

        if target == "left arm":
            return self._left_arm_deliver(goal_handle, context)
        elif target == "right arm":
            return self._right_arm_deliver(goal_handle, context)
        elif target == "one arm":
            return self._one_arm_deliver(goal_handle, context)
        elif target == "both arm":
            return self._both_arm_deliver(goal_handle, context)
        else:
            self.send_feedback(goal_handle, 0, f"未知递物目标: {target}")
            return TaskResult(False, error_code=99,
                              error_message=f'Unknown deliver target: "{target}"')

    # ================================================================
    # 工具方法
    # ================================================================

    def _hold_and_wait_for_tug(
        self, robot_body, hand_side: str,
        goal_handle, base_state: np.ndarray,
    ) -> bool:
        """到位后保持位姿，同时使用触觉传感器和关节角度检测拖拽，任一触发即松手。

        触觉方案：采集切向力滚动基线，检测 drop > 阈值触发
        关节方案：采集 shoulder_pitch 基线，检测角度偏差 > 阈值触发

        Args:
            hand_side: 'left' / 'right' / 'both'
            base_state: 26-dim 目标位姿（手臂+手掌），持续下发保持

        Returns:
            True = 拖拽触发后松手, False = 超时后强制松手
        """
        robot = robot_body.robot

        # ── 判断触觉传感器是否可用 ──
        touch_available = (_HAS_TOUCH_STATUS
                           and hasattr(robot, 'latest_left_touch')
                           and hasattr(robot, 'latest_right_touch'))
        if touch_available:
            print('[Deliver] 同时使用触觉+关节角度检测拖拽（任一触发即松手）')
        else:
            print('[Deliver] 触觉传感器不可用，仅使用关节角度检测')

        # ================================================================
        # Step 1: 到位后持续下发保持位姿，等待 state 稳定
        # ================================================================
        robot.send_robot_action(base_state)
        print(f'[Deliver] 到位，等待 {TUG_STABILIZE_TIME}s 让 state 稳定...')
        t0 = time.time()
        while time.time() - t0 < TUG_STABILIZE_TIME:
            robot.send_robot_action(base_state)
            time.sleep(TUG_MONITOR_INTERVAL)

        # ================================================================
        # Step 2a: 采集触觉基线（如可用）
        # ================================================================
        touch_bl_left = None
        touch_bl_right = None
        th_touch_left = TOUCH_TF_DIFF_ABS
        th_touch_right = TOUCH_TF_DIFF_ABS

        if touch_available:
            left_samples, right_samples = [], []
            _BASELINE_SAMPLES = 10
            for _ in range(_BASELINE_SAMPLES):
                if hand_side in ('left', 'both'):
                    touch = robot.latest_left_touch
                    if touch is not None:
                        msg, _ = touch
                        tf = robot.get_touch_tf_sum(msg)
                        if tf > 0:
                            left_samples.append(tf)
                if hand_side in ('right', 'both'):
                    touch = robot.latest_right_touch
                    if touch is not None:
                        msg, _ = touch
                        tf = robot.get_touch_tf_sum(msg)
                        if tf > 0:
                            right_samples.append(tf)
                robot.send_robot_action(base_state)
                time.sleep(0.05)

            touch_bl_left = np.median(left_samples) if left_samples else None
            touch_bl_right = np.median(right_samples) if right_samples else None

            if touch_bl_left is not None:
                th_touch_left = max(TOUCH_TF_DIFF_ABS, int(touch_bl_left * TOUCH_TF_DIFF_RATIO))
                print(f'[Deliver] 触觉基线 tf_sum={touch_bl_left:.0f}, '
                      f'阈值={th_touch_left} (有效样本{len(left_samples)})')
            else:
                print(f'[WARN] 左手触觉基线采集失败，跳过触觉检测')

            if touch_bl_right is not None:
                th_touch_right = max(TOUCH_TF_DIFF_ABS, int(touch_bl_right * TOUCH_TF_DIFF_RATIO))
                print(f'[Deliver] 触觉基线 tf_sum={touch_bl_right:.0f}, '
                      f'阈值={th_touch_right} (有效样本{len(right_samples)})')
            else:
                print(f'[WARN] 右手触觉基线采集失败，跳过触觉检测')

        # ================================================================
        # Step 2b: 采集关节角度基线（始终可用）
        # ================================================================
        WRIST_IDXS = [0]  # shoulder_pitch
        joint_threshold = math.radians(TUG_DETECTION_THRESHOLD_DEG)
        joint_bl_left = None
        joint_bl_right = None

        left_j_samples, right_j_samples = [], []
        for _ in range(5):
            if hand_side in ('left', 'both'):
                arm = robot.latest_left_arm
                if arm is not None:
                    msg, _ = arm
                    left_j_samples.append(np.array([msg.position[i] for i in WRIST_IDXS]))
            if hand_side in ('right', 'both'):
                arm = robot.latest_right_arm
                if arm is not None:
                    msg, _ = arm
                    right_j_samples.append(np.array([msg.position[i] for i in WRIST_IDXS]))
            robot.send_robot_action(base_state)
            time.sleep(0.05)

        joint_bl_left = np.median(left_j_samples, axis=0) if left_j_samples else None
        joint_bl_right = np.median(right_j_samples, axis=0) if right_j_samples else None

        ls = joint_bl_left.round(4).tolist() if joint_bl_left is not None else "N/A"
        rs = joint_bl_right.round(4).tolist() if joint_bl_right is not None else "N/A"
        print(f'[Deliver] 关节基线(rad) - left: {ls}, right: {rs}')

        # ================================================================
        # Step 3: 持续下发保持 + 同时监测触觉和关节角度
        # ================================================================
        start_time = time.time()
        check_count = 0
        left_t_counter = 0      # 触觉连续触发计数
        right_t_counter = 0
        trigger_source = ""     # 记录触发来源

        # 滚动基线窗口：递送到位后持续维护 1s 滑动窗口中位数
        # 缓慢漂移会被滚动基线自动吸收，只有快速下降才会触发
        left_rolling = deque(maxlen=_TOUCH_ROLLING_SIZE)
        right_rolling = deque(maxlen=_TOUCH_ROLLING_SIZE)
        rolling_bl_left = touch_bl_left   # 初始用采集到的基线
        rolling_bl_right = touch_bl_right
        rolling_th_left = th_touch_left
        rolling_th_right = th_touch_right

        while time.time() - start_time < TUG_DETECTION_TIMEOUT:
            robot.send_robot_action(base_state)
            tug_detected = False

            # ── 触觉检测（连续 2 帧确认 + 滚动基线） ──
            if touch_available:
                if rolling_bl_left is not None:
                    touch = robot.latest_left_touch
                    if touch is not None:
                        msg, _ = touch
                        tf = robot.get_touch_tf_sum(msg)
                        if tf > 0:
                            left_rolling.append(tf)
                        # 滚动基线：用窗口满了之后的中位数替换初始基线
                        if len(left_rolling) >= _TOUCH_ROLLING_SIZE:
                            rolling_bl_left = np.median(left_rolling)
                            rolling_th_left = max(TOUCH_TF_DIFF_ABS,
                                                  int(rolling_bl_left * TOUCH_TF_DIFF_RATIO))
                        drop = rolling_bl_left - tf
                        if drop > rolling_th_left:
                            left_t_counter += 1
                            if left_t_counter >= 2:
                                print(f'[Deliver] 左手触觉触发！tf={tf}, '
                                      f'rolling_bl={rolling_bl_left:.0f}, drop={drop:.0f}, '
                                      f'threshold={rolling_th_left}')
                                tug_detected = True
                                trigger_source = '左手触觉（切向力下降）'
                        else:
                            left_t_counter = 0

                if not tug_detected and rolling_bl_right is not None:
                    touch = robot.latest_right_touch
                    if touch is not None:
                        msg, _ = touch
                        tf = robot.get_touch_tf_sum(msg)
                        if tf > 0:
                            right_rolling.append(tf)
                        if len(right_rolling) >= _TOUCH_ROLLING_SIZE:
                            rolling_bl_right = np.median(right_rolling)
                            rolling_th_right = max(TOUCH_TF_DIFF_ABS,
                                                   int(rolling_bl_right * TOUCH_TF_DIFF_RATIO))
                        drop = rolling_bl_right - tf
                        if drop > rolling_th_right:
                            right_t_counter += 1
                            if right_t_counter >= 2:
                                print(f'[Deliver] 右手触觉触发！tf={tf}, '
                                      f'rolling_bl={rolling_bl_right:.0f}, drop={drop:.0f}, '
                                      f'threshold={rolling_th_right}')
                                tug_detected = True
                                trigger_source = '右手触觉（切向力下降）'
                        else:
                            right_t_counter = 0

            # ── 关节角度检测（单帧触发） ──
            if not tug_detected:
                if joint_bl_left is not None:
                    arm = robot.latest_left_arm
                    if arm is not None:
                        msg, _ = arm
                        wrist = np.array([msg.position[i] for i in WRIST_IDXS])
                        diff = np.abs(wrist - joint_bl_left)
                        if np.any(diff > joint_threshold):
                            diff_deg = np.rad2deg(diff).round(2)
                            print(f'[Deliver] 左手关节触发！diff={diff_deg} deg')
                            tug_detected = True
                            trigger_source = f'左手关节（偏差 {diff_deg}°）'

            if not tug_detected:
                if joint_bl_right is not None:
                    arm = robot.latest_right_arm
                    if arm is not None:
                        msg, _ = arm
                        wrist = np.array([msg.position[i] for i in WRIST_IDXS])
                        diff = np.abs(wrist - joint_bl_right)
                        if np.any(diff > joint_threshold):
                            diff_deg = np.rad2deg(diff).round(2)
                            print(f'[Deliver] 右手关节触发！diff={diff_deg} deg')
                            tug_detected = True
                            trigger_source = f'右手关节（偏差 {diff_deg}°）'

            if tug_detected:
                print(f'[Deliver] 触发来源: {trigger_source}，松手！')
                self._open_hand_and_hold(robot_body, hand_side, goal_handle,
                                         HAND_OPEN_HOLD_TIME, base_state=base_state)
                return True

            time.sleep(TUG_MONITOR_INTERVAL)
            check_count += 1
            if check_count % 100 == 0:
                elapsed = time.time() - start_time
                print(f'[Deliver] 等待拖拽中... {elapsed:.0f}s / {TUG_DETECTION_TIMEOUT:.0f}s')

        # ================================================================
        # Step 4: 超时，强制松手
        # ================================================================
        side_label = {'left': '左手', 'right': '右手',
                      'both': '双手'}.get(hand_side, hand_side)
        print(f'[Deliver] 触发来源: 超时（{TUG_DETECTION_TIMEOUT}s未检测到拖拽），{side_label}强制松手')
        self._open_hand_and_hold(robot_body, hand_side, goal_handle,
                                 HAND_OPEN_HOLD_TIME, base_state=base_state)
        return False

    def _open_hand_and_hold(
        self, robot_body, hand_side: str,
        goal_handle, hold_duration: float,
        base_state: np.ndarray | None = None,
    ) -> None:
        """打开手部（全部手指设为 0.0）并保持指定时间

        Args:
            hand_side: 'left' / 'right' / 'both'
            base_state: 基础状态（含期望的手臂位置），None 则从 robot 读取
        """
        if base_state is not None:
            action = base_state.copy()
        else:
            current_state = robot_body._get_reset_current_action()
            if current_state is None:
                print('[WARN] _open_hand_and_hold: 无法获取当前机器人状态，跳过松手')
                return
            action = current_state.copy()
        zero_hand = np.zeros(6)

        if hand_side in ('left', 'both'):
            action[14:20] = zero_hand
        if hand_side in ('right', 'both'):
            action[20:26] = zero_hand

        # 注：只修改手掌[14:26]，手臂不变，delta 限幅不会触发
        side_label = {'left': '左手', 'right': '右手', 'both': '双手'}.get(hand_side, hand_side)
        robot_body.control_robot(action)
        send_vla_feedback(goal_handle, 95, f"{side_label}已打开，保持 {hold_duration:.0f}s...")
        time.sleep(hold_duration)

    # ================================================================
    # 递物逻辑
    # ================================================================

    def _left_arm_deliver(self, goal_handle, context) -> TaskResult:
        """左手递物：
          1. 3s 线性插值 → 左边递物位姿
          2. 左手手掌全开，维持 1s
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "左手递物开始")

        current_state = robot_body.move_arms(
            left_target=LEFT_DELIVER_POSE,
            right_target=None,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_DELIVER_TIMEOUT,
                              error_message="Failed to get current robot state for left arm deliver")
        send_vla_feedback(goal_handle, 90, "已到递物位姿")

        self._hold_and_wait_for_tug(robot_body, 'left', goal_handle, current_state)

        send_vla_feedback(goal_handle, 100, "左手递物完成")
        return TaskResult(True)

    def _right_arm_deliver(self, goal_handle, context) -> TaskResult:
        """右手递物：
          1. 3s 线性插值 → 右边递物位姿
          2. 右手手掌全开，维持 1s
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "右手递物开始")

        current_state = robot_body.move_arms(
            left_target=None,
            right_target=RIGHT_DELIVER_POSE,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_DELIVER_TIMEOUT,
                              error_message="Failed to get current robot state for right arm deliver")
        send_vla_feedback(goal_handle, 90, "已到递物位姿")

        self._hold_and_wait_for_tug(robot_body, 'right', goal_handle, current_state)

        send_vla_feedback(goal_handle, 100, "右手递物完成")
        return TaskResult(True)

    def _one_arm_deliver(self, goal_handle, context) -> TaskResult:
        """单手递物：自动判断哪只手有物体"""
        grasp_state = context.grasp_detector.grasp_state  # [left_grasped, right_grasped]

        if grasp_state[1]:   # 右手有东西 → 右手递物
            return self._right_arm_deliver(goal_handle, context)
        elif grasp_state[0]:  # 左手有东西 → 左手递物
            return self._left_arm_deliver(goal_handle, context)
        else:
            # 双手都没东西
            send_vla_feedback(goal_handle, 0, "双手都没有物体，无法递物")
            return TaskResult(False, error_code=ERR_DELIVER_ONE_HAND_BOTH_EMPTY,
                              error_message="Both hands are empty, cannot do one arm deliver")

    def _both_arm_deliver(self, goal_handle, context) -> TaskResult:
        """双手递物：两只手必须同时有物体"""
        grasp_state = context.grasp_detector.grasp_state  # [left_grasped, right_grasped]

        if not (grasp_state[0] and grasp_state[1]):
            send_vla_feedback(goal_handle, 0, "双手没有同时有物体，无法递物")
            return TaskResult(False, error_code=ERR_DELIVER_BOTH_HAND_NOT_BOTH,
                              error_message="Not both hands have objects, cannot do both arm deliver")

        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "双手递物开始")

        # 1. 3s 线性插值，双臂同时到递物位姿
        current_state = robot_body.move_arms(
            left_target=LEFT_DELIVER_POSE,
            right_target=RIGHT_DELIVER_POSE,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_DELIVER_TIMEOUT,
                              error_message="Failed to get current robot state for both arm deliver")
        send_vla_feedback(goal_handle, 85, "已到递物位姿")

        # 2. 保持位姿，等待拖拽检测，检测到后松手
        self._hold_and_wait_for_tug(robot_body, 'both', goal_handle, current_state)

        send_vla_feedback(goal_handle, 100, "双手递物完成")
        return TaskResult(True)
