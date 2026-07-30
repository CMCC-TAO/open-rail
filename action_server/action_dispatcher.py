"""
VLA Action Dispatcher - 任务分发型 ROS2 Action Server

以 params 中的 task 字段为路由键，将 goal 分发给对应的 handler 执行。
"""

# ════════════════════════════════════════════════════════════════
# 抓取检测配置参数 —— 修改此处即可调节抓取判定灵敏度
# ════════════════════════════════════════════════════════════════

# ── 触觉方案 ──
# 抓取条件（两项同时满足并持续 TOUCH_GRASP_HOLD_SEC）：
#   1. nf_sum > TOUCH_NF_THRESHOLD
#   2. tf_sum > TOUCH_TF_THRESHOLD
TOUCH_NF_THRESHOLD = 1000             # 法向力总和阈值
TOUCH_TF_THRESHOLD = 1000             # 切向力总和阈值
TOUCH_PER_FINGER_NF = 40             # 单指 NF 阈值（仅用于调试显示）
TOUCH_GRASP_HOLD_SEC = 0.5           # 条件持续满足多久才判定抓取成功（秒）

import sys
import os
import time
import json
import threading
from collections import deque

# 项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import asyncio
import rclpy
from rclpy.action import ActionServer, CancelResponse
from rclpy.node import Node
from message_center.action import ExecutionUnit

from action_server.action_base import AbstractTaskHandler, TaskResult
from action_server.vla_context import VLAContext

# 判断触觉传感器消息类型是否可用
try:
    from message_center.msg import TouchStatus  # noqa: F401
    _HAS_TOUCH_STATUS = True
except ImportError:
    _HAS_TOUCH_STATUS = False


# ════════════════════════════════════════════════════════════════
# Grasp Detector — 触觉传感器判断抓取状态
# ════════════════════════════════════════════════════════════════
class GraspDetector:
    """通过触觉传感器判断抓取状态。

    判定条件（两项同时满足且持续 TOUCH_GRASP_HOLD_SEC）：
        1. nf_sum > TOUCH_NF_THRESHOLD
        2. tf_sum > TOUCH_TF_THRESHOLD
    """

    def __init__(self, node: Node):
        self._node = node
        self._lock = threading.Lock()

        # ── 抓取状态 ──
        self._grasp_state = [False, False]
        self._verbose = False  # 是否打印调试信息（grasp 任务期间才开启）

        # ── 触觉缓存 ──
        self._left_nf_sum: int = 0
        self._left_tf_sum: int = 0
        self._left_contact: int = 0          # 调试显示用
        self._left_nf_per_finger: list = []   # 调试显示用

        self._right_nf_sum: int = 0
        self._right_tf_sum: int = 0
        self._right_contact: int = 0
        self._right_nf_per_finger: list = []

        # 触觉抓取计时器
        self._left_touch_hold_since: float = 0.0
        self._right_touch_hold_since: float = 0.0

        # ── 定时打印线程 ──
        self._print_running = True
        self._print_thread = threading.Thread(target=self._print_loop, daemon=True)
        self._print_thread.start()

        # ── 订阅触觉 ──
        self._touch_available = _HAS_TOUCH_STATUS
        if self._touch_available:
            node.create_subscription(
                TouchStatus, '/left_hand/touch_status',
                self._cb_left_touch, 10)
            node.create_subscription(
                TouchStatus, '/right_hand/touch_status',
                self._cb_right_touch, 10)

        touch_info = (
            f'nf>{TOUCH_NF_THRESHOLD} tf>{TOUCH_TF_THRESHOLD} '
            f'hold={TOUCH_GRASP_HOLD_SEC}s'
        ) if self._touch_available else '触觉不可用'
        node.get_logger().info(f'[GraspDetector] Started | {touch_info}')

    # ── 定时打印 ──────────────────────────────────────────────────

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

    def _print_hand(self, tag, grasped, info):
        nf_sum, tf_sum, contact, nf_pf = info

        if nf_pf:
            finger_s = ''.join(
                'T' if nf >= TOUCH_PER_FINGER_NF else ('t' if nf > 0 else '.')
                for nf in nf_pf
            )
        else:
            finger_s = '?'

        state_mark = "✓" if grasped else " "
        print(
            f"[GraspDetector] [{state_mark}] {tag}: "
            f"nf={nf_sum:4d} tf={tf_sum:4d} cnt={contact} "
            f"fingers=[{finger_s}]"
        )

    def stop(self):
        self._print_running = False

    # ── 触觉回调 ──────────────────────────────────────────────────

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

    # ── 核心判定逻辑 ───────────────────────────────────────────────

    def _evaluate_grasp(self):
        """评估左右手抓取状态（必须在 _lock 内调用）"""
        now = time.time()

        g0, self._left_touch_hold_since = self._eval_one_hand(
            now, self._left_nf_sum, self._left_tf_sum,
            self._left_touch_hold_since)
        self._grasp_state[0] = g0

        g1, self._right_touch_hold_since = self._eval_one_hand(
            now, self._right_nf_sum, self._right_tf_sum,
            self._right_touch_hold_since)
        self._grasp_state[1] = g1

    def _eval_one_hand(self, now, nf_sum, tf_sum, hold_since):
        """条件满足且持续 TOUCH_GRASP_HOLD_SEC → 抓取成功。
        返回 (grasped, hold_since)。"""
        if not self._touch_available:
            return False, 0.0

        touch_ok = (nf_sum > TOUCH_NF_THRESHOLD
                    and tf_sum > TOUCH_TF_THRESHOLD)

        if touch_ok:
            if hold_since == 0.0:
                hold_since = now
            grasped = (now - hold_since >= TOUCH_GRASP_HOLD_SEC)
        else:
            hold_since = 0.0
            grasped = False

        return grasped, hold_since

    # ── 公开接口 ──────────────────────────────────────────────────

    @property
    def grasp_state(self) -> list:
        with self._lock:
            return list(self._grasp_state)


# ════════════════════════════════════════════════════════════════
# Observation Data Bridge — 把观测数据推送到内部 WebSocket 端口
# 供 action_web_vision 消费，避免 web 服务器重复创建 RobotBody
# ════════════════════════════════════════════════════════════════
class ObsDataBridge:
    """在 dispatcher 进程内持续读取 robot_body 观测数据，
    通过内部 WebSocket(9001) 推送给 action_web_vision 服务器。

    架构：
        推送线程 → 写入共享队列 → asyncio data_sender 循环 → WS 客户端
    """

    def __init__(self, vla_context: VLAContext, grasp_detector: 'GraspDetector' = None):
        self._ctx = vla_context
        self._grasp_detector = grasp_detector
        self._running = False
        # 共享数据队列：推送线程写，asyncio 服务器线程读
        self._send_queue = deque(maxlen=500)
        self._queue_lock = threading.Lock()
        self._ws_clients = set()
        self._ws_lock = threading.Lock()

    def start(self):
        self._running = True
        # 启动 asyncio WebSocket 服务器（含 data_sender 循环）
        self._ws_thread = threading.Thread(target=self._run_ws_server, daemon=True)
        self._ws_thread.start()
        # 启动数据推送线程
        self._push_thread = threading.Thread(target=self._push_loop, daemon=True)
        self._push_thread.start()
        print("[ObsBridge] Started on ws://127.0.0.1:9001")

    def stop(self):
        self._running = False
        print("[ObsBridge] Stopped")

    # ── 数据入队（推送线程调用）──
    def _enqueue(self, data):
        """将数据放入发送队列，供 asyncio 线程读取"""
        with self._queue_lock:
            self._send_queue.append(data)

    # ── WebSocket 服务器（asyncio 线程）──
    def _run_ws_server(self):
        asyncio.run(self._async_server())

    async def _async_server(self):
        import websockets, socket, signal, subprocess, re

        async def handler(ws, path=None):
            with self._ws_lock:
                self._ws_clients.add(ws)
            try:
                # 保持连接，等待客户端断开
                async for msg in ws:
                    pass  # 不处理客户端消息
            except Exception:
                pass
            finally:
                with self._ws_lock:
                    self._ws_clients.discard(ws)

        # 手动创建 socket，避免旧进程残留导致 "address already in use"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", 9001))
        except OSError:
            # 旧进程还活着，找到它并杀掉
            try:
                ss_out = subprocess.run(
                    ["ss", "-tlnp", "sport = :9001"],
                    capture_output=True, text=True, timeout=3
                ).stdout
                m = re.search(r'pid=(\d+)', ss_out)
                if m:
                    old_pid = int(m.group(1))
                    print(f"[ObsBridge] Old process PID={old_pid} holds port 9001, killing...")
                    os.kill(old_pid, signal.SIGTERM)
                    for _ in range(20):
                        time.sleep(0.1)
                        try:
                            os.kill(old_pid, 0)
                        except OSError:
                            break
                    else:
                        os.kill(old_pid, signal.SIGKILL)
                        time.sleep(0.5)
                    print(f"[ObsBridge] Port 9001 released, rebinding...")
                    sock.close()
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.bind(("127.0.0.1", 9001))
            except Exception:
                pass
        sock.listen()

        async with websockets.serve(handler, sock=sock, max_size=2**23) as server:
            print("[ObsBridge] WS server listening on 9001")
            # data_sender 循环：从共享队列取数据并广播
            while self._running:
                await self._flush_queue()
                await asyncio.sleep(0.005)  # ~200Hz

    async def _flush_queue(self):
        """从共享队列取出所有待发数据并广播给 WS 客户端"""
        with self._queue_lock:
            items = list(self._send_queue)
            self._send_queue.clear()

        if not items or not self._ws_clients:
            return

        dead = set()
        clients = list(self._ws_clients)
        for item in items:
            for ws in clients:
                try:
                    if isinstance(item, bytes):
                        await ws.send(item)
                    else:
                        await ws.send(item)
                except Exception:
                    dead.add(ws)
        if dead:
            with self._ws_lock:
                self._ws_clients -= dead

    # ── 数据推送线程 ──
    def _push_loop(self):
        """持续读取 robot_body 观测，写入共享队列"""
        import cv2

        # 等待 robot_body 就绪
        robot_body = None
        for _ in range(120):  # 最多等 60s
            if not self._running:
                return
            try:
                robot_body = self._ctx.robot_body
                break
            except Exception:
                pass
            time.sleep(0.5)

        if robot_body is None:
            print("[ObsBridge] robot_body not available, bridge inactive")
            return

        print("[ObsBridge] robot_body ready, starting data push")

        camera_id_map = {
            "cam.head": 0,
            "cam.hand_left": 1,
            "cam.hand_right": 2,
        }
        last_push_time = 0.0   # 上次推送的 wall clock 时间（用于限流）
        last_ros_ts = 0.0      # 上次推送的 ROS 时间戳（用于去重）
        last_state_ts = 0.0
        last_grasp_ts = 0.0

        while self._running:
            try:
                cam = robot_body.camera
                robot = robot_body.robot
                now = time.time()

                # ── 相机帧 ──
                #   root cause: 原代码用 last_cam_ts = head_ts（ROS 时间戳）
                #   同时作为去重和限流的基准，但 now - ROS_timestamp 可正可负
                #   （ROS 时钟与系统时钟不同步），导致条件永远无法满足。
                #   修复：去重用 ROS 时间戳，限流用 wall clock，各自独立
                if cam is not None:
                    cam_data = cam.get_latest_image()
                    if cam_data is not None:
                        head_img, head_ts, left_img, left_ts, right_img, right_ts = cam_data

                        # 条件1：ROS 时间戳变化（新帧去重）
                        # 条件2：距离上次推送 >= 33ms（wall clock 限流）
                        if head_ts != last_ros_ts and now - last_push_time >= 0.033:
                            last_push_time = now
                            last_ros_ts = head_ts
                            for cam_key, cam_id in camera_id_map.items():
                                img = None
                                if cam_key == "cam.head" and head_img is not None:
                                    img = head_img
                                elif cam_key == "cam.hand_left" and left_img is not None:
                                    img = left_img
                                elif cam_key == "cam.hand_right" and right_img is not None:
                                    img = right_img
                                if img is None:
                                    continue
                                try:
                                    _, jpeg_bytes = cv2.imencode(
                                        ".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 70]
                                    )
                                    header = {
                                        "type": "camera_data_binary",
                                        "camera_id": cam_id,
                                        "timestamp": now,
                                        "data_size": len(jpeg_bytes),
                                    }
                                    header_bytes = json.dumps(header).encode("utf-8")
                                    header_len = len(header_bytes)
                                    message = (
                                        header_len.to_bytes(4, byteorder="big")
                                        + header_bytes
                                        + jpeg_bytes.tobytes()
                                    )
                                    self._enqueue(message)
                                except Exception:
                                    pass

                # ── 抓取状态推送（独立于关节限流，与话题频率对齐）──
                if self._grasp_detector is not None and now - last_grasp_ts >= 0.033:
                    grasp_msg = json.dumps({
                        "type": "grasp_state",
                        "data": self._grasp_detector.grasp_state,
                    })
                    self._enqueue(grasp_msg)
                    last_grasp_ts = now

                # ── 关节状态 ──
                if robot is not None and now - last_state_ts >= 0.033:
                    arm_state = robot._get_current_arm_state()
                    lh = robot.latest_left_hand
                    rh = robot.latest_right_hand
                    if arm_state is not None:
                        state_list = arm_state.tolist()
                        if lh is not None and lh[0] is not None and lh[0].position:
                            state_list.extend([float(x) for x in lh[0].position[:6]])
                        else:
                            state_list.extend([0.0] * 6)
                        if rh is not None and rh[0] is not None and rh[0].position:
                            state_list.extend([float(x) for x in rh[0].position[:6]])
                        else:
                            state_list.extend([0.0] * 6)

                        msg = json.dumps({
                            "type": "joint_data",
                            "data": {
                                "tab": "position",
                                "type": "state",
                                "joints_y": state_list,
                                "timestamp": now,
                                "task_progress": self._ctx.current_task_progress,
                                "inference_running": self._ctx.is_inference_running,
                                "infer_count": self._ctx.infer_count,
                            },
                        })
                        self._enqueue(msg)
                        last_state_ts = now

            except Exception as e:
                print(f"[ObsBridge] Push error: {e}")
            time.sleep(0.008)


class VLAActionDispatcher(Node):
    """VLA Action Dispatcher - 任务分发型 ROS2 Action Server

    功能:
        1. 接收 ExecutionUnit goal（含 task_src 和 params JSON）
        2. 解析 params 中的 task 字段
        3. 路由到已注册的 handler 执行
        4. 返回 result（SUCCESS / FAILED + error_code + error_message）

    通过 register_handler() 注册新的任务处理器。
    """

    # ================================================================
    # 超时 / 常量
    # ================================================================
    MAX_TASK_DURATION = 120.0  # 单次任务最大执行时间（秒）

    def __init__(self, robot_type: str = None, sim_mode: bool = False):
        super().__init__('vla_action_server')

        self.get_logger().info('VLA Action Dispatcher starting...')

        # 创建共享上下文（config + robot_body 等长生命周期资源）
        self._context = VLAContext(robot_type=robot_type, sim_mode=sim_mode)
        self.get_logger().info('VLA context created (robot_body lazy, will init on first use)')

        # 任务处理器注册表: task_name -> AbstractTaskHandler
        self._handlers: dict[str, AbstractTaskHandler] = {}

        # 注册内置 handler
        self._register_builtin_handlers()

        # 创建抓取检测器（订阅 set_angle/get_angle 话题，判断抓取状态）
        self._grasp_detector = GraspDetector(self)
        self._context.grasp_detector = self._grasp_detector

        # 创建 Action Server
        self._action_server = ActionServer(
            self,
            ExecutionUnit,
            '/vla/action_ctrl',
            self.execute_callback,
            cancel_callback=self.cancel_callback,
        )

        # 列出已注册的任务
        names = list(self._handlers.keys())
        self.get_logger().info(
            f'VLA Action Dispatcher ready. '
            f'Registered tasks ({len(names)}): {names}'
        )

    # ================================================================
    # 任务注册
    # ================================================================

    def register_handler(self, handler: AbstractTaskHandler) -> None:
        """注册一个任务处理器

        Args:
            handler: 继承自 AbstractTaskHandler 的实例
        """
        name = handler.task_name
        if name in self._handlers:
            self.get_logger().warn(f'Overwriting existing handler for task="{name}"')
        self._handlers[name] = handler
        self.get_logger().info(f'Registered handler for task="{name}"')

    def _register_builtin_handlers(self) -> None:
        """注册内置任务处理器"""
        try:
            from action_server.task_init_grasp import InitGraspHandler
            self._handlers["grasp:init"] = InitGraspHandler()
            self.get_logger().info('Registered handler for task="grasp:init"')
        except ImportError as e:
            self.get_logger().warn(f'Failed to load init_grasp handler: {e}')

        try:
            from action_server.task_init_zero import InitZeroHandler
            self.register_handler(InitZeroHandler())
        except ImportError as e:
            self.get_logger().warn(f'Failed to load init_zero handler: {e}')

        try:
            from action_server.task_finish_grasp import FinishGraspHandler
            self._handlers["grasp:finish"] = FinishGraspHandler()
            self.get_logger().info('Registered handler for task="grasp:finish"')
        except ImportError as e:
            self.get_logger().warn(f'Failed to load finish_grasp handler: {e}')

        try:
            from action_server.task_grasp import GraspHandler
            self.register_handler(GraspHandler())
        except ImportError as e:
            self.get_logger().warn(f'Failed to load grasp handler: {e}')

        try:
            from action_server.task_grasp_all import GraspAllHandler
            self.register_handler(GraspAllHandler())
        except ImportError as e:
            self.get_logger().warn(f'Failed to load grasp_all handler: {e}')

        try:
            from action_server.task_deliver import DeliverHandler
            handler = DeliverHandler()
            for target in ["left arm", "right arm", "one arm", "both arm"]:
                self._handlers[f"deliver:{target}"] = handler
            self.get_logger().info(f'Registered deliver handler for 4 target variants')
        except ImportError as e:
            self.get_logger().warn(f'Failed to load deliver handler: {e}')

        try:
            from action_server.task_place import PlaceHandler
            handler = PlaceHandler()
            for target in ["left arm", "right arm", "one arm", "both arm"]:
                self._handlers[f"place:{target}"] = handler
            self.get_logger().info(f'Registered place handler for 4 target variants')
        except ImportError as e:
            self.get_logger().warn(f'Failed to load place handler: {e}')

        try:
            from action_server.task_release import ReleaseHandler
            handler = ReleaseHandler()
            for target in ["left hand", "right hand", "both hand"]:
                self._handlers[f"release:{target}"] = handler
            self.get_logger().info(f'Registered release handler for 3 target variants')
        except ImportError as e:
            self.get_logger().warn(f'Failed to load release handler: {e}')

        try:
            from action_server.task_reset import ResetHandler
            handler = ResetHandler()
            for target in ["left arm", "right arm", "both arm"]:
                self._handlers[f"reset:{target}"] = handler
            self.get_logger().info(f'Registered reset handler for 3 target variants')
        except ImportError as e:
            self.get_logger().warn(f'Failed to load reset handler: {e}')

    # ================================================================
    # Action 回调
    # ================================================================

    def cancel_callback(self, goal_handle):
        """处理取消请求"""
        self.get_logger().warn('Received cancel request')
        return CancelResponse.ACCEPT

    async def execute_callback(self, goal_handle):
        """主执行回调 - 解析 goal → 路由 → 执行 → 返回 result

        Args:
            goal_handle: ROS2 Action goal handle
        """
        # ROS2 Humble: goal 通过 request 属性获取，而非 get_goal()
        goal = goal_handle.request
        task_src = goal.task_src
        params_json = goal.params

        self.get_logger().info(
            f'Received goal: task_src={task_src}, params={params_json}'
        )

        # ========== 1. 解析 JSON ==========
        try:
            params = json.loads(params_json) if params_json else {}
        except json.JSONDecodeError as e:
            self.get_logger().error(f'Invalid params JSON: {e}')
            return self._abort(goal_handle, error_code=1,
                               error_message=f'Invalid JSON: {str(e)}')

        if not isinstance(params, dict):
            return self._abort(goal_handle, error_code=1,
                               error_message='params must be a JSON object')

        task_name = params.get('task', '')

        if not task_name:
            return self._abort(goal_handle, error_code=2,
                               error_message='Missing "task" field in params')

        # ========== 2. 路由到 handler ==========
        # 复合键优先: "task:target" → 回退到 "task"
        target = params.get('target', '')
        compound_key = f"{task_name}:{target}" if target else task_name
        handler = self._handlers.get(compound_key) or self._handlers.get(task_name)
        if handler is None:
            known = list(self._handlers.keys())
            return self._abort(goal_handle, error_code=3,
                               error_message=f'Unknown task="{task_name}". '
                                             f'Known tasks: {known}')

        self.get_logger().info(
            f'Dispatching task="{task_name}" to {handler.__class__.__name__}'
        )

        # ========== 3. 执行 handler ==========
        start_time = time.time()

        try:
            task_result: TaskResult = handler.execute(goal_handle, params, self._context)
        except Exception as e:
            self.get_logger().error(f'Handler raised unexpected exception: {e}')
            return self._abort(goal_handle, error_code=99,
                               error_message=f'Handler error: {str(e)}')

        elapsed = time.time() - start_time
        self.get_logger().info(
            f'Task="{task_name}" completed in {elapsed:.1f}s: '
            f'success={task_result.success} '
            f'(code={task_result.error_code}, msg={task_result.error_message})'
        )

        # ========== 4. 返回结果 ==========
        if task_result.success:
            return self._succeed(goal_handle)
        else:
            return self._abort(goal_handle,
                               error_code=task_result.error_code,
                               error_message=task_result.error_message)

    # ================================================================
    # 内部工具
    # ================================================================

    @staticmethod
    def _succeed(goal_handle):
        """构建 SUCCESS result 并标记 goal 完成

        注意: ROS2 Humble 中 succeed() 不接受参数，result 通过返回值传递。
        """
        result = ExecutionUnit.Result()
        result.result = 1  # SUCCESS
        result.error_code = 0
        result.error_message = ''
        goal_handle.succeed()
        return result

    @staticmethod
    def _abort(goal_handle, error_code: int, error_message: str):
        """构建 FAILED result 并标记 goal 中止"""
        result = ExecutionUnit.Result()
        result.result = 2  # FAILED
        result.error_code = error_code
        result.error_message = error_message
        goal_handle.abort()
        return result


# ==============================================
# Main
# ==============================================

def main(args=None):
    # 先解析自定义参数（--robot_type 等），避免传入 ROS2
    import argparse as _argparse
    _parser = _argparse.ArgumentParser(description='VLA Action Dispatcher')
    _parser.add_argument('--robot_type', type=str, default=None,
                        help='Robot type, e.g. unitree_g1, a2d (default: a2d)')
    _parser.add_argument('--sim', action='store_true',
                        help='Simulation mode: disable relative position limits')
    _custom_args, _remaining = _parser.parse_known_args()

    # 显式传 args=[] 避免 sys.argv 干扰 ROS2 参数解析
    rclpy.init(args=_remaining if args is None else [])

    dispatcher = None
    try:
        dispatcher = VLAActionDispatcher(robot_type=_custom_args.robot_type, sim_mode=_custom_args.sim)

        # 预初始化 robot_body：在 spin 循环启动前完成所有 ROS2 节点的创建，
        # 避免 execute_callback 中懒加载新节点导致 wait set 重建时
        # 产生 "wait set index too big" 错误。
        dispatcher.get_logger().info('Pre-initializing robot_body (may take a few seconds)...')
        _ = dispatcher._context.robot_body
        dispatcher.get_logger().info('robot_body pre-initialized, wait set is stable')

        # 启动观测数据桥接（供 action_web_vision 服务器消费）
        dispatcher._obs_bridge = ObsDataBridge(dispatcher._context, dispatcher._grasp_detector)
        dispatcher._obs_bridge.start()
        dispatcher.get_logger().info('ObsDataBridge started (ws://127.0.0.1:9001)')

        # 使用 MultiThreadedExecutor 确保 action 回调在独立线程执行，
        # 不会阻塞 spin 线程的 wait set 管理。
        from rclpy.executors import MultiThreadedExecutor
        executor = MultiThreadedExecutor()
        executor.add_node(dispatcher)
        executor.spin()
    except KeyboardInterrupt:
        print('\nShutting down VLA Action Dispatcher...')
    except Exception as e:
        print(f'Fatal error: {e}')
    finally:
        if dispatcher is not None:
            # 停止抓取检测器打印线程
            if hasattr(dispatcher, '_grasp_detector'):
                try:
                    dispatcher._grasp_detector.stop()
                except Exception:
                    pass
            # 停止观测数据桥接
            if hasattr(dispatcher, '_obs_bridge'):
                try:
                    dispatcher._obs_bridge.stop()
                except Exception:
                    pass
            # 清理共享资源 (robot_body 等)
            try:
                dispatcher._context.close()
            except Exception as e:
                print(f'VLAContext cleanup error: {e}')
            dispatcher.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
