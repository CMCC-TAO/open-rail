"""
放置任务 - 将物体放下（左手/右手/单手/双手）

不需要 VLA 推理，直接使用预设的放置位姿 + 线性插值轨迹。

任务接口:
  {
    "task": "place",              # 左手放置
    "target": "left arm",         # 抓取的目标
    "waypoint": "none"
  }
  {
    "task": "place",              # 右手放置
    "target": "right arm",        # 抓取的目标
    "waypoint": "none"
  }
  {
    "task": "place",              # 单手放置（自动判断哪只手有物体）
    "target": "one arm",          # 抓取的目标
    "waypoint": "none"
  }
  {
    "task": "place",              # 双手放置
    "target": "both arm",         # 抓取的目标
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

from action_server.task_init import _SAFE_LEFT_ARM, _SAFE_RIGHT_ARM, _get_init_grasp_pose
from action_server.task_reset import _LEFT_RESET_POSE, _RIGHT_RESET_POSE
from action_server.action_base import (
    AbstractTaskHandler, TaskResult, send_vla_feedback,
    ERR_PLACE_TIMEOUT, ERR_PLACE_LEFT_EMPTY, ERR_PLACE_RIGHT_EMPTY,
    ERR_PLACE_ONE_HAND_BOTH_EMPTY, ERR_PLACE_BOTH_HAND_NOT_BOTH,
    ERR_PLACE_ONE_HAND_STILL_HOLDING,
)

# ==============================================
# 放置目标位姿（7 关节，弧度）—— 请根据实测调节
# LEFT_PLACE_POSE = np.array([-0.0, 0.1, 0.0, 0.72, 0.0, -0.9, 0.0])
# RIGHT_PLACE_POSE = np.array([-0.0, -0.1, 0.0, 0.72, 0.0, -0.9, 0.0])
# ==============================================
LEFT_PLACE_POSE  = np.array([-0.1726,  0.1, 0.0, 1.045, 0.0, -1.393, 0.0])
RIGHT_PLACE_POSE = np.array([-0.1726, -0.1, 0.0, 1.045, 0.0, -1.393, 0.0])

# ==============================================
# 放置完成后回缩位姿（手掌打开后手臂后退一段距离）
# ==============================================
LEFT_RETRACT_POSE  = np.array([0.5,  0.1, 0.0, 0.0, 0.0, -0.8, 0.0])
RIGHT_RETRACT_POSE = np.array([0.5, -0.1, 0.0, 0.0, 0.0, -0.8, 0.0])


# ==============================================
# 时间常量
# ==============================================
HAND_OPEN_HOLD_TIME = 1.0       # 手掌打开后保持时长（秒）


class PlaceHandler(AbstractTaskHandler):
    """放置任务处理器

    由 dispatcher 路由到以下 4 个 task:target 复合键之一:
      - "place:left arm"
      - "place:right arm"
      - "place:one arm"
      - "place:both arm"
    """

    @property
    def task_name(self) -> str:
        return "place"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        target = params.get("target", "")

        if target == "left arm":
            return self._left_arm_place(goal_handle, context)
        elif target == "right arm":
            return self._right_arm_place(goal_handle, context)
        elif target == "one arm":
            return self._one_arm_place(goal_handle, context)
        elif target == "both arm":
            return self._both_arm_place(goal_handle, context)
        else:
            self.send_feedback(goal_handle, 0, f"未知放置目标: {target}")
            return TaskResult(False, error_code=99,
                              error_message=f'Unknown place target: "{target}"')

    # ================================================================
    # 工具方法
    # ================================================================

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
        zero_hand = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 700.0])

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
    # 放置逻辑
    # ================================================================

    def _left_arm_place(self, goal_handle, context) -> TaskResult:
        """左手放置 + 放置后复位

        完整序列:
          1. 5s 线性插值 → 左安全中间姿态
          2. 3s 线性插值 → 左初始抓取姿态（手掌不变）
          3. 3s 线性插值 → 左放置位姿
          4. 左手手掌全开，维持 1s
          5. 3s 线性插值 → 左回缩位姿
          6. 3s 线性插值 → 左安全中间姿态
          7. 5s 线性插值 → 左垂直复位姿态
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "左手放置开始")

        # 1. 5s 线性插值 → 安全中间姿态
        current_state = robot_body.move_arms(
            left_target=_SAFE_LEFT_ARM,
            right_target=None,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_PLACE_TIMEOUT,
                              error_message="Failed to get current robot state for left arm place")
        send_vla_feedback(goal_handle, 15, "已到安全中间姿态")

        # 2. 3s 线性插值 → 初始抓取姿态（手掌不变）
        init_grasp_pose = _get_init_grasp_pose(context)
        current_state = robot_body.move_arms(
            left_target=init_grasp_pose[0:7],
            right_target=None,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_PLACE_TIMEOUT,
                              error_message="Failed to get current robot state for left arm place")
        send_vla_feedback(goal_handle, 30, "已到初始抓取姿态")

        # 3. 3s 线性插值 → 放置位姿
        current_state = robot_body.move_arms(
            left_target=LEFT_PLACE_POSE,
            right_target=None,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_PLACE_TIMEOUT,
                              error_message="Failed to get current robot state for left arm place")
        send_vla_feedback(goal_handle, 50, "已到放置位姿")

        # 4. 打开左手，保持
        self._open_hand_and_hold(robot_body, 'left', goal_handle, HAND_OPEN_HOLD_TIME, base_state=current_state)

        # 5. 手臂回缩到安全位置
        robot_body.move_arms(
            left_target=LEFT_RETRACT_POSE,
            right_target=None,
        )
        send_vla_feedback(goal_handle, 70, "已回缩到安全位置")

        # 6. 过渡到安全中间姿态
        robot_body.move_arms(
            left_target=_SAFE_LEFT_ARM,
            right_target=None,
        )
        send_vla_feedback(goal_handle, 85, "已到安全中间姿态")

        # 7. 过渡到垂直复位姿态
        robot_body.move_arms(
            left_target=_LEFT_RESET_POSE,
            right_target=None,
        )
        send_vla_feedback(goal_handle, 99, "已到垂直复位姿态")

        send_vla_feedback(goal_handle, 100, "左手放置完成")
        return TaskResult(True)

    def _right_arm_place(self, goal_handle, context) -> TaskResult:
        """右手放置 + 放置后复位

        完整序列:
          1. 5s 线性插值 → 右安全中间姿态
          2. 3s 线性插值 → 右初始抓取姿态（手掌不变）
          3. 3s 线性插值 → 右放置位姿
          4. 右手手掌全开，维持 1s
          5. 3s 线性插值 → 右回缩位姿
          6. 3s 线性插值 → 右安全中间姿态
          7. 5s 线性插值 → 右垂直复位姿态
        """
        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "右手放置开始")

        # 1. 5s 线性插值 → 安全中间姿态
        current_state = robot_body.move_arms(
            left_target=None,
            right_target=_SAFE_RIGHT_ARM,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_PLACE_TIMEOUT,
                              error_message="Failed to get current robot state for right arm place")
        send_vla_feedback(goal_handle, 15, "已到安全中间姿态")

        # 2. 3s 线性插值 → 初始抓取姿态（手掌不变）
        init_grasp_pose = _get_init_grasp_pose(context)
        current_state = robot_body.move_arms(
            left_target=None,
            right_target=init_grasp_pose[7:14],
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_PLACE_TIMEOUT,
                              error_message="Failed to get current robot state for right arm place")
        send_vla_feedback(goal_handle, 30, "已到初始抓取姿态")

        # 3. 3s 线性插值 → 放置位姿
        current_state = robot_body.move_arms(
            left_target=None,
            right_target=RIGHT_PLACE_POSE,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_PLACE_TIMEOUT,
                              error_message="Failed to get current robot state for right arm place")
        send_vla_feedback(goal_handle, 50, "已到放置位姿")

        # 4. 打开右手，保持
        self._open_hand_and_hold(robot_body, 'right', goal_handle, HAND_OPEN_HOLD_TIME, base_state=current_state)

        # 5. 手臂回缩到安全位置
        robot_body.move_arms(
            left_target=None,
            right_target=RIGHT_RETRACT_POSE,
        )
        send_vla_feedback(goal_handle, 70, "已回缩到安全位置")

        # 6. 过渡到安全中间姿态
        robot_body.move_arms(
            left_target=None,
            right_target=_SAFE_RIGHT_ARM,
        )
        send_vla_feedback(goal_handle, 85, "已到安全中间姿态")

        # 7. 过渡到垂直复位姿态
        robot_body.move_arms(
            left_target=None,
            right_target=_RIGHT_RESET_POSE,
        )
        send_vla_feedback(goal_handle, 99, "已到垂直复位姿态")

        send_vla_feedback(goal_handle, 100, "右手放置完成")
        return TaskResult(True)

    def _one_arm_place(self, goal_handle, context) -> TaskResult:
        """单手放置：自动判断哪只手有物体"""
        grasp_state = context.grasp_detector.grasp_state  # [left_grasped, right_grasped]

        if grasp_state[1]:   # 右手有东西 → 右手放置
            return self._right_arm_place(goal_handle, context)
        elif grasp_state[0]:  # 左手有东西 → 左手放置
            return self._left_arm_place(goal_handle, context)
        else:
            # 双手都没东西
            send_vla_feedback(goal_handle, 0, "双手都没有物体，无法放置")
            return TaskResult(False, error_code=ERR_PLACE_ONE_HAND_BOTH_EMPTY,
                              error_message="Both hands are empty, cannot do one arm place")

    def _both_arm_place(self, goal_handle, context) -> TaskResult:
        """双手放置 + 放置后复位

        完整序列:
          1. 5s 线性插值 → 双臂安全中间姿态
          2. 3s 线性插值 → 双臂初始抓取姿态（手掌不变）
          3. 3s 线性插值 → 双臂放置位姿
          4. 同时打开双手，维持 1s
          5. 等待 0.5s 检测是否所有物体已放下
          6. 3s 线性插值 → 双臂回缩位姿
          7. 3s 线性插值 → 双臂安全中间姿态
          8. 5s 线性插值 → 双臂垂直复位姿态
        """
        grasp_state = context.grasp_detector.grasp_state  # [left_grasped, right_grasped]

        if not (grasp_state[0] and grasp_state[1]):
            send_vla_feedback(goal_handle, 0, "双手没有同时有物体，无法放置")
            return TaskResult(False, error_code=ERR_PLACE_BOTH_HAND_NOT_BOTH,
                              error_message="Not both hands have objects, cannot do both arm place")

        robot_body = context.robot_body
        send_vla_feedback(goal_handle, 5, "双手放置开始")

        # 1. 5s 线性插值 → 双臂安全中间姿态
        current_state = robot_body.move_arms(
            left_target=_SAFE_LEFT_ARM,
            right_target=_SAFE_RIGHT_ARM,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_PLACE_TIMEOUT,
                              error_message="Failed to get current robot state for both arm place")
        send_vla_feedback(goal_handle, 15, "已到安全中间姿态")

        # 2. 3s 线性插值 → 双臂初始抓取姿态（手掌不变）
        init_grasp_pose = _get_init_grasp_pose(context)
        current_state = robot_body.move_arms(
            left_target=init_grasp_pose[0:7],
            right_target=init_grasp_pose[7:14],
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_PLACE_TIMEOUT,
                              error_message="Failed to get current robot state for both arm place")
        send_vla_feedback(goal_handle, 30, "已到初始抓取姿态")

        # 3. 3s 线性插值，双臂同时到放置位姿
        current_state = robot_body.move_arms(
            left_target=LEFT_PLACE_POSE,
            right_target=RIGHT_PLACE_POSE,
        )
        if current_state is None:
            return TaskResult(False, error_code=ERR_PLACE_TIMEOUT,
                              error_message="Failed to get current robot state for both arm place")
        send_vla_feedback(goal_handle, 45, "已到放置位姿")

        # 4. 同时打开双手，保持 1s
        self._open_hand_and_hold(robot_body, 'both', goal_handle, HAND_OPEN_HOLD_TIME, base_state=current_state)

        # 5. 等待 0.5s 让 grasp_detector 更新
        time.sleep(0.5)
        final_grasp_state = context.grasp_detector.grasp_state
        if final_grasp_state[0] or final_grasp_state[1]:
            send_vla_feedback(goal_handle, 50, "有一只手未能放下物体")
            return TaskResult(False, error_code=ERR_PLACE_ONE_HAND_STILL_HOLDING,
                              error_message="One hand still holding object after both arm place")

        # 6. 双臂回缩
        robot_body.move_arms(
            left_target=LEFT_RETRACT_POSE,
            right_target=RIGHT_RETRACT_POSE,
        )
        send_vla_feedback(goal_handle, 70, "已回缩到安全位置")

        # 7. 双臂过渡到安全中间姿态
        robot_body.move_arms(
            left_target=_SAFE_LEFT_ARM,
            right_target=_SAFE_RIGHT_ARM,
        )
        send_vla_feedback(goal_handle, 85, "已到安全中间姿态")

        # 8. 双臂过渡到垂直复位姿态
        robot_body.move_arms(
            left_target=_LEFT_RESET_POSE,
            right_target=_RIGHT_RESET_POSE,
        )
        send_vla_feedback(goal_handle, 99, "已到垂直复位姿态")

        send_vla_feedback(goal_handle, 100, "双手放置完成")
        return TaskResult(True)
