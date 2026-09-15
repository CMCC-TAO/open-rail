"""
Grasp Detector — 双模式抓取状态检测
   力传感器模式：触觉传感器判断抓取状态（优先）
   关节角度模式：set_angle / get_angle 差值判断抓取状态（回退方案）

模式选择（**启动时决定一次，本次运行不再改变**；force_sensor_enabled=True 只表示"优先"，
并不保证力信号存在）：
   force_sensor_enabled=False                → 直接锁定关节角度方案
   force_sensor_enabled=True 且启动探测期内收到触觉消息 → 锁定力传感器方案
   force_sensor_enabled=True 但收不到触觉消息           → 锁定关节角度方案（回退）
       （典型场景：无力信号输入、数据回放、无触觉硬件的分支）
   左右手各自独立判定：某侧没有力信号时只回退该侧，另一侧仍可用力传感器。

对外接口（由 action_dispatcher 使用）：
  - GraspDetector(node, force_sensor_enabled, touch_probe_timeout)
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
TOUCH_NF_THRESHOLD = 800             # 法向力总和阈值
TOUCH_TF_THRESHOLD = 800             # 切向力总和阈值
TOUCH_PER_FINGER_NF = 40             # 单指 NF 阈值（仅用于调试显示）
TOUCH_GRASP_HOLD_SEC = 0.5           # 条件持续满足多久才判定抓取成功（秒）

# ════════════════════════════════════════════════════════════════
# 抓取检测配置参数 —— 力信号探测（决定是否回退到关节角度方案）
# force_sensor_enabled=True 只表示"优先用力传感器"，并不保证力信号真的存在：
#   - 没有触觉硬件 / 数据回放：/left_hand/touch_status 一直没有消息
#   - 订阅存在但发布的是空消息（无手指数据）
# 判定时机：**启动时一次性决定，之后本次运行不再改变**（左右手各自独立）
#   - TOUCH_PROBE_TIMEOUT_SEC 内收到该侧任何**有效**触觉消息 → 锁定力传感器方案
#   - 探测期结束仍未收到                                  → 锁定关节角度方案
# 这样"用哪种方案"在启动后就固定下来，不会在运行中来回切换。
# ════════════════════════════════════════════════════════════════
TOUCH_PROBE_TIMEOUT_SEC = 5.0        # 启动后等待触觉消息的最长时间（秒）


class GraspDetector:
    """双模式抓取状态检测器

    力传感器模式（force_sensor_enabled=True 且该侧确实收到触觉消息）：
        通过触觉传感器判断抓取状态，判定条件（两项同时满足且持续 TOUCH_GRASP_HOLD_SEC）：
          1. nf_sum > TOUCH_NF_THRESHOLD
          2. tf_sum > TOUCH_TF_THRESHOLD

    关节角度模式（force_sensor_enabled=False，或开关为 True 但力信号缺失时自动回退）：
        通过比较手部 set_angle 与 get_angle 的多个手指差值来检测抓取状态。
        判定条件（同时满足下两个条件并持续超过 GRASP_HOLD_DURATION_SEC 秒）：
          - set_angle[thumb_bend] - get_angle[thumb_bend] > GRASP_ANGLE_DIFF_THRESHOLD (200)
          - set_angle[middle]     - get_angle[middle]     > GRASP_MIDDLE_DIFF_THRESHOLD (100)

    模式选择是**启动时一次性决定**的行为（见 _use_touch），左右手各自独立：
    force_sensor_enabled=True 只是"优先"，启动 TOUCH_PROBE_TIMEOUT_SEC 内收到该侧任何
    有效触觉消息即锁定力传感器方案，否则锁定关节角度方案；**锁定后本次运行不再改变**。

    内部维护 [左手抓取, 右手抓取] 的 bool 列表，实时更新。
    """

    # 手部关节顺序: little, ring, middle, index, thumb_bend, thumb_rotate
    THUMB_BEND_INDEX = 4
    MIDDLE_FINGER_INDEX = 2

    def __init__(self, node: Node, force_sensor_enabled: bool = True,
                 touch_probe_timeout: float = TOUCH_PROBE_TIMEOUT_SEC):
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

        # ── 模式选择状态（运行时判定，左右手各自独立）──
        # _touch_mode_requested：是否"优先使用力传感器"（开关打开 且 消息类型可用）
        self._touch_mode_requested = bool(force_sensor_enabled and _HAS_TOUCH_STATUS)
        self._touch_probe_timeout = float(touch_probe_timeout)
        self._start_time = time.time()
        self._touch_rx_count = {'left': 0, 'right': 0}        # 收到的有效触觉消息数
        self._touch_last_ts = {'left': 0.0, 'right': 0.0}
        # None=未定（探测期内） / True / False = 已锁定（之后不再改变）
        self._side_use_touch: dict[str, bool | None] = {'left': None, 'right': None}
        self._touch_topic = {
            'left': '/left_hand/touch_status', 'right': '/right_hand/touch_status',
        }
        self._angle_topic = {
            'left': '/left_hand/set_angle + /left_hand/get_angle',
            'right': '/right_hand/set_angle + /right_hand/get_angle',
        }

        # ── 调试打印状态（力传感器模式专用）──
        self._verbose = False
        self._print_running = True
        self._print_thread = threading.Thread(target=self._print_loop, daemon=True)
        self._print_thread.start()

        # ── 订阅 ──
        qos_correct = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=10,
        )

        # 关节角度话题：force_sensor_enabled=False 时直接使用；
        # True 时也预先订阅，供力信号缺失时回退使用（避免在回调线程里动态建订阅）。
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

        if self._touch_mode_requested:
            # 力传感器模式：订阅触觉（是否真正生效由 _use_touch 运行时决定）
            node.create_subscription(
                TouchStatus, '/left_hand/touch_status',
                self._cb_left_touch, 10)
            node.create_subscription(
                TouchStatus, '/right_hand/touch_status',
                self._cb_right_touch, 10)
            mode_name = '优先力传感器（无信号时自动回退关节角度）'
            policy = (f'启动探测 {self._touch_probe_timeout:.1f}s：收到触觉消息则该侧锁定'
                      f'力传感器方案，否则锁定关节角度方案（之后不再切换）')
        else:
            mode_name = '关节角度'
            policy = ('force_sensor_enabled=False' if not force_sensor_enabled
                      else 'TouchStatus 消息类型不可用')

        touch_info = (
            f'nf>{TOUCH_NF_THRESHOLD} tf>{TOUCH_TF_THRESHOLD} '
            f'hold={TOUCH_GRASP_HOLD_SEC}s'
        ) if self._touch_available else '触觉消息类型不可用'
        node.get_logger().info(
            f'[GraspDetector] Started | 模式={mode_name} | {touch_info} | {policy}'
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
            self._record_touch_rx('left', nf_pf)
            self._evaluate_grasp()

    def _cb_right_touch(self, msg):
        nf_sum, tf_sum, contact, nf_pf = self._extract_touch_data(msg)
        with self._lock:
            self._right_nf_sum = nf_sum
            self._right_tf_sum = tf_sum
            self._right_contact = contact
            self._right_nf_per_finger = nf_pf
            self._record_touch_rx('right', nf_pf)
            self._evaluate_grasp()

    def _record_touch_rx(self, side: str, nf_per_finger: list):
        """记录"收到有效触觉消息"（必须在 _lock 内调用）。

        只有带手指数据的消息才算有效力信号：订阅存在但一直发空消息的情况
        （某些回放/桩发布者）不应被当作有力传感器，否则会一直困在力传感器方案里。
        """
        if not nf_per_finger:
            return
        self._touch_rx_count[side] += 1
        self._touch_last_ts[side] = time.time()

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

        每侧独立决定判定方式：优先力传感器，收不到力信号则回退关节角度方案
        （见 _use_touch）。
        """
        now = time.time()
        for idx, side in enumerate(('left', 'right')):
            if self._use_touch(side, now):
                self._grasp_state[idx] = self._eval_touch_side(now, idx, side)
            else:
                self._grasp_state[idx] = self._eval_angle_side(now, idx, side)

    # ── 判定方式选择（运行时、每侧独立）────────────────────────────

    def _use_touch(self, side: str, now: float) -> bool:
        """该侧用力传感器方案还是关节角度方案（必须在 _lock 内调用）。

        **启动时决定一次，之后本次运行不再改变**（左右手各自独立）：
          - force_sensor_enabled=False 或 TouchStatus 类型不可用 → 锁定关节角度方案
          - 启动探测期内收到该侧任何有效触觉消息                 → 锁定力传感器方案
          - 探测期结束仍未收到该侧触觉消息                       → 锁定关节角度方案（回退）
        探测期内尚未定案时暂时返回 True（按力传感器方案等待数据，判定结果保持 False，不误判）。
        """
        decided = self._side_use_touch[side]
        if decided is not None:
            return decided                 # 已锁定，不再改变

        if not self._touch_mode_requested:
            # 配置决定（开关为 False 或消息类型不可用）：不是"回退"，不打回退日志
            self._side_use_touch[side] = False
            return False

        if self._touch_rx_count[side] > 0:
            self._side_use_touch[side] = True
            self._reset_side_timing(side)
            print(
                f"[GraspDetector] {side}: 检测到力信号"
                f"（{self._touch_topic[side]}），锁定力传感器方案（本次运行不再切换）"
            )
            return True

        if (now - self._start_time) < self._touch_probe_timeout:
            # 探测期内等待数据：暂不定案，也不打日志
            return True

        self._side_use_touch[side] = False
        self._reset_side_timing(side)
        print(
            f"[GraspDetector] {side}: 未检测到力信号"
            f"（{self._touch_topic[side]}，探测 {self._touch_probe_timeout:.1f}s），"
            f"锁定关节角度方案（{self._angle_topic[side]}，本次运行不再切换）"
        )
        return False

    def _reset_side_timing(self, side: str):
        """切换判定方式时清掉该侧的持续计时，避免沿用旧方案的计时误判"""
        if side == 'left':
            self._left_exceed_since = 0.0
            self._left_touch_hold_since = 0.0
        else:
            self._right_exceed_since = 0.0
            self._right_touch_hold_since = 0.0

    # ── 力传感器方案 ───────────────────────────────────────────────

    def _eval_touch_side(self, now: float, idx: int, side: str) -> bool:
        """触觉方案：nf/tf 同时超阈值并持续 TOUCH_GRASP_HOLD_SEC 判定抓取"""
        if side == 'left':
            grasped, self._left_touch_hold_since = self._eval_one_hand(
                now, self._left_nf_sum, self._left_tf_sum,
                self._left_touch_hold_since)
            nf_sum, tf_sum = self._left_nf_sum, self._left_tf_sum
        else:
            grasped, self._right_touch_hold_since = self._eval_one_hand(
                now, self._right_nf_sum, self._right_tf_sum,
                self._right_touch_hold_since)
            nf_sum, tf_sum = self._right_nf_sum, self._right_tf_sum
        if grasped and not self._grasp_state[idx]:
            print(
                f"[GraspDetector] {side} grasp succeeded (touch): "
                f"nf_sum={nf_sum}, tf_sum={tf_sum}"
            )
        return grasped

    # ── 关节角度方案（无信号时回退）────────────────────────────────

    def _eval_angle_side(self, now: float, idx: int, side: str) -> bool:
        """角度方案：thumb_bend 与 middle 的 set-get 差值同时超阈值并持续判定抓取"""
        set_key, get_key = f'{side}_set', f'{side}_get'
        thumb_diff = self._compute_diff(set_key, get_key, self.THUMB_BEND_INDEX)
        mid_diff = self._compute_diff(set_key, get_key, self.MIDDLE_FINGER_INDEX)
        over_threshold = (
            thumb_diff is not None and mid_diff is not None
            and thumb_diff > GRASP_ANGLE_DIFF_THRESHOLD
            and mid_diff > GRASP_MIDDLE_DIFF_THRESHOLD
        )
        hold_since = (self._left_exceed_since if side == 'left'
                      else self._right_exceed_since)
        if over_threshold:
            if hold_since == 0.0:
                hold_since = now
            grasped = (now - hold_since >= GRASP_HOLD_DURATION_SEC)
            if grasped and not self._grasp_state[idx]:
                print(
                    f"[GraspDetector] {side} grasp succeeded (angle): "
                    f"thumb_diff={thumb_diff:.1f} mid_diff={mid_diff:.1f}"
                )
        else:
            hold_since = 0.0
            grasped = False
        if side == 'left':
            self._left_exceed_since = hold_since
        else:
            self._right_exceed_since = hold_since
        return grasped

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
