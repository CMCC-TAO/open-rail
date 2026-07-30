"""
Grasp Detector — 双模式抓取状态检测
   力传感器模式：触觉传感器判断抓取状态
   无力传感器模式：关节角度差判断抓取状态（回退方案）

对外接口（由 action_dispatcher 使用）：
  - GraspDetector(node, force_sensor_enabled)
  - .grasp_state -> [left_grasped, right_grasped]  (bool list)
  - .stop()
  - .set_verbose(enabled)      # 力传感器模式调试打印
  - .get_angle_diffs() -> dict # 关节角度模式调试
"""

import sys
import os
import time
import threading
from collections import deque
import numpy as np

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
from sensor_msgs.msg import JointState
from rclpy.node import Node

# 判断触觉传感器消息类型是否可用
try:
    from message_center.msg import TouchStatus  # noqa: F401
    _HAS_TOUCH_STATUS = True
except ImportError:
    TouchStatus = None
    _HAS_TOUCH_STATUS = False


# ════════════════════════════════════════════════════════════════
# 抓取检测配置参数 —— 关节角度方案（无力传感器时回退）
# 判定条件：thumb_bend diff > GRASP_ANGLE_DIFF_THRESHOLD
#       且 middle finger diff > GRASP_MIDDLE_DIFF_THRESHOLD
#       持续 GRASP_HOLD_DURATION_SEC 秒
# ════════════════════════════════════════════════════════════════
GRASP_ANGLE_DIFF_THRESHOLD = 200.0     # 拇指弯曲角度差阈值
GRASP_MIDDLE_DIFF_THRESHOLD = 100.0    # 中指角度差阈值
GRASP_HOLD_DURATION_SEC = 0.5          # 差值需持续超过阈值的最短时间（秒）

# ════════════════════════════════════════════════════════════════
# 抓取检测配置参数 —— 触觉方案（有力传感器时使用）
# 抓取条件（两项同时满足并持续 TOUCH_GRASP_HOLD_SEC）：
#   1. nf_sum > TOUCH_NF_THRESHOLD
#   2. tf_sum > TOUCH_TF_THRESHOLD
# ════════════════════════════════════════════════════════════════
TOUCH_NF_THRESHOLD = 1000             # 法向力总和阈值
TOUCH_TF_THRESHOLD = 1000             # 切向力总和阈值
TOUCH_PER_FINGER_NF = 40             # 单指 NF 阈值（仅用于调试显示）
TOUCH_GRASP_HOLD_SEC = 0.5           # 条件持续满足多久才判定抓取成功（秒）


class GraspDetector:
    """双模式抓取状态检测器

    力传感器模式（force_sensor_enabled=True 且 touch 消息可用）：
        通过触觉传感器判断抓取状态，判定条件（两项同时满足且持续 TOUCH_GRASP_HOLD_SEC）：
          1. nf_sum > TOUCH_NF_THRESHOLD
          2. tf_sum > TOUCH_TF_THRESHOLD

    无力传感器模式（force_sensor_enabled=False 或 touch 不可用）：
        通过比较手部 set_angle 与 get_angle 的多个手指差值来检测抓取状态。
        判定条件（同时满足下两个条件并持续超过 GRASP_HOLD_DURATION_SEC 秒）：
          - set_angle[thumb_bend] - get_angle[thumb_bend] > GRASP_ANGLE_DIFF_THRESHOLD (200)
          - set_angle[middle]     - get_angle[middle]     > GRASP_MIDDLE_DIFF_THRESHOLD (100)

    内部维护 [左手抓取, 右手抓取] 的 bool 列表，实时更新。
    """

    # 手部关节顺序: little, ring, middle, index, thumb_bend, thumb_rotate
    THUMB_BEND_INDEX = 4
    MIDDLE_FINGER_INDEX = 2

    def __init__(self, node: Node, force_sensor_enabled: bool = True):
        self._node = node
        self._lock = threading.Lock()
        self._force_sensor_enabled = force_sensor_enabled

        # ── 抓取状态 ──
        self._grasp_state = [False, False]

        # ── 触觉缓存（力传感器模式）──
        self._left_nf_sum: int = 0
        self._left_tf_sum: int = 0
        self._left_contact: int = 0
        self._left_nf_per_finger: list = []

        self._right_nf_sum: int = 0
        self._right_tf_sum: int = 0
        self._right_contact: int = 0
        self._right_nf_per_finger: list = []

        self._left_touch_hold_since: float = 0.0
        self._right_touch_hold_since: float = 0.0

        # ── 关节角度缓存（无力传感器回退方案）──
        self._angle_cache = {
            'left_set': None, 'left_get': None,
            'right_set': None, 'right_get': None,
        }
        self._left_exceed_since = 0.0
        self._right_exceed_since = 0.0

        # ── 触觉是否可用（编译期检查 TouchStatus 消息类型是否存在）──
        self._touch_available = _HAS_TOUCH_STATUS

        # ── 调试打印状态（力传感器模式专用）──
        self._verbose = False
        self._print_running = True
        self._print_thread = threading.Thread(target=self._print_loop, daemon=True)
        self._print_thread.start()

        # ── 订阅（根据模式选择）──
        qos_correct = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=10,
        )

        if self._touch_available and self._force_sensor_enabled:
            # 力传感器模式：订阅触觉
            node.create_subscription(
                TouchStatus, '/left_hand/touch_status',
                self._cb_left_touch, 10)
            node.create_subscription(
                TouchStatus, '/right_hand/touch_status',
                self._cb_right_touch, 10)
            mode_name = '力传感器'
        else:
            # 无力传感器模式：订阅关节角度
            node.create_subscription(
                JointState, '/left_hand/set_angle',
                lambda msg: self._on_angle('left_set', msg), qos_correct)
            node.create_subscription(
                JointState, '/left_hand/get_angle',
                lambda msg: self._on_angle('left_get', msg), qos_correct)
            node.create_subscription(
                JointState, '/right_hand/set_angle',
                lambda msg: self._on_angle('right_set', msg), qos_correct)
            node.create_subscription(
                JointState, '/right_hand/get_angle',
                lambda msg: self._on_angle('right_get', msg), qos_correct)
            mode_name = '关节角度'

        touch_info = (
            f'nf>{TOUCH_NF_THRESHOLD} tf>{TOUCH_TF_THRESHOLD} '
            f'hold={TOUCH_GRASP_HOLD_SEC}s'
        ) if self._touch_available else '触觉不可用'
        node.get_logger().info(
            f'[GraspDetector] Started | 模式={mode_name} | {touch_info}'
        )

    # ── 调试打印（力传感器模式）───────────────────────────────────

    def set_verbose(self, enabled: bool):
        """开启/关闭调试打印（grasp 任务期间开启，其他时间关闭）"""
        self._verbose = enabled

    def _print_loop(self):
        """每秒打印抓取状态（仅 verbose=True 时）"""
        while self._print_running:
            time.sleep(1.0)
            if not self._verbose:
                continue
            with self._lock:
                state = list(self._grasp_state)
                l_info = (self._left_nf_sum, self._left_tf_sum, self._left_contact,
                          list(self._left_nf_per_finger))
                r_info = (self._right_nf_sum, self._right_tf_sum, self._right_contact,
                          list(self._right_nf_per_finger))

            self._print_hand('L', state[0], l_info)
            self._print_hand('R', state[1], r_info)

    @staticmethod
    def _print_hand(tag, grasped, info):
        nf_sum, tf_sum, contact, nf_pf = info
        if nf_pf:
            finger_s = ''.join(
                'T' if nf >= TOUCH_PER_FINGER_NF else ('t' if nf > 0 else '.')
                for nf in nf_pf
            )
        else:
            finger_s = '?'
        state_mark = "*" if grasped else " "
        print(
            f"[GraspDetector] [{state_mark}] {tag}: "
            f"nf={nf_sum:4d} tf={tf_sum:4d} cnt={contact} "
            f"fingers=[{finger_s}]"
        )

    # ── 触觉回调（力传感器模式）───────────────────────────────────

    def _cb_left_touch(self, msg):
        nf_sum, tf_sum, contact, nf_pf = self._extract_touch_data(msg)
        with self._lock:
            self._left_nf_sum = nf_sum
            self._left_tf_sum = tf_sum
            self._left_contact = contact
            self._left_nf_per_finger = nf_pf
            self._evaluate_grasp()

    def _cb_right_touch(self, msg):
        nf_sum, tf_sum, contact, nf_pf = self._extract_touch_data(msg)
        with self._lock:
            self._right_nf_sum = nf_sum
            self._right_tf_sum = tf_sum
            self._right_contact = contact
            self._right_nf_per_finger = nf_pf
            self._evaluate_grasp()

    @staticmethod
    def _extract_touch_data(msg) -> tuple:
        """从 TouchStatus 消息提取触觉特征。
        Returns: (nf_sum, tf_sum, contact_count, nf_per_finger)"""
        nf_sum = 0
        tf_sum = 0
        contact = 0
        nf_pf = []
        for f in msg.fingers:
            nf = f.normal_force1 + f.normal_force2 + f.normal_force3
            tf = f.tangential_force1 + f.tangential_force2 + f.tangential_force3
            nf_sum += nf
            tf_sum += tf
            nf_pf.append(nf)
            if nf > TOUCH_PER_FINGER_NF:
                contact += 1
        return nf_sum, tf_sum, contact, nf_pf

    # ── 关节角度回调（无力传感器回退方案）────────────────────────

    def _on_angle(self, key: str, msg):
        """缓存全关节 position 数组（用于计算多个手指差值），然后更新抓取判定"""
        if msg.position and len(msg.position) > max(self.THUMB_BEND_INDEX, self.MIDDLE_FINGER_INDEX):
            with self._lock:
                self._angle_cache[key] = [float(v) for v in msg.position]
                self._evaluate_grasp()

    # ── 核心判定逻辑 ───────────────────────────────────────────────

    def _evaluate_grasp(self):
        """评估左右手抓取状态（必须在 _lock 内调用）

        根据 force_sensor_enabled 和 touch_available 自动选择判定方式。
        """
        if self._touch_available and self._force_sensor_enabled:
            # ── 力传感器模式：触觉方案 ──
            g0, self._left_touch_hold_since = self._eval_one_hand(
                time.time(), self._left_nf_sum, self._left_tf_sum,
                self._left_touch_hold_since)
            self._grasp_state[0] = g0

            g1, self._right_touch_hold_since = self._eval_one_hand(
                time.time(), self._right_nf_sum, self._right_tf_sum,
                self._right_touch_hold_since)
            self._grasp_state[1] = g1
        else:
            # ── 无力传感器模式：关节角度方案 ──
            now = time.time()

            def _both_over_threshold(set_key: str, get_key: str) -> bool:
                thumb_diff = self._compute_diff(set_key, get_key, self.THUMB_BEND_INDEX)
                mid_diff = self._compute_diff(set_key, get_key, self.MIDDLE_FINGER_INDEX)
                if thumb_diff is None or mid_diff is None:
                    return False
                return thumb_diff > GRASP_ANGLE_DIFF_THRESHOLD and mid_diff > GRASP_MIDDLE_DIFF_THRESHOLD

            # ── 左手 ──
            if _both_over_threshold('left_set', 'left_get'):
                if self._left_exceed_since == 0.0:
                    self._left_exceed_since = now
                if now - self._left_exceed_since >= GRASP_HOLD_DURATION_SEC:
                    self._grasp_state[0] = True
            else:
                self._left_exceed_since = 0.0
                self._grasp_state[0] = False

            # ── 右手 ──
            if _both_over_threshold('right_set', 'right_get'):
                if self._right_exceed_since == 0.0:
                    self._right_exceed_since = now
                if now - self._right_exceed_since >= GRASP_HOLD_DURATION_SEC:
                    self._grasp_state[1] = True
            else:
                self._right_exceed_since = 0.0
                self._grasp_state[1] = False

    def _eval_one_hand(self, now, nf_sum, tf_sum, hold_since):
        """触觉方案：条件满足且持续 TOUCH_GRASP_HOLD_SEC -> 抓取成功。
        返回 (grasped, hold_since)。"""
        if not self._touch_available:
            return False, 0.0
        touch_ok = (nf_sum > TOUCH_NF_THRESHOLD and tf_sum > TOUCH_TF_THRESHOLD)
        if touch_ok:
            if hold_since == 0.0:
                hold_since = now
            grasped = (now - hold_since >= TOUCH_GRASP_HOLD_SEC)
        else:
            hold_since = 0.0
            grasped = False
        return grasped, hold_since

    def _compute_diff(self, set_key: str, get_key: str, index: int):
        """计算指定关节索引的 set_angle - get_angle 差值，数据缺失时返回 None"""
        set_val = self._angle_cache[set_key]
        get_val = self._angle_cache[get_key]
        if set_val is None or get_val is None:
            return None
        if len(set_val) <= index or len(get_val) <= index:
            return None
        return set_val[index] - get_val[index]

    # ── 公开接口 ──────────────────────────────────────────────────

    @property
    def grasp_state(self) -> list:
        """返回 [left_grasped, right_grasped]"""
        with self._lock:
            return list(self._grasp_state)

    def get_angle_diffs(self) -> dict:
        """返回当前左右手的 set/get 角度差（调试用），含 thumb 和 middle"""
        with self._lock:
            return {
                'left_thumb': self._compute_diff('left_set', 'left_get', self.THUMB_BEND_INDEX),
                'left_mid':   self._compute_diff('left_set', 'left_get', self.MIDDLE_FINGER_INDEX),
                'right_thumb': self._compute_diff('right_set', 'right_get', self.THUMB_BEND_INDEX),
                'right_mid':   self._compute_diff('right_set', 'right_get', self.MIDDLE_FINGER_INDEX),
            }

    def stop(self):
        """停止后台线程"""
        self._print_running = False
