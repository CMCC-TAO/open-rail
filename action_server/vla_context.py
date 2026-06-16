"""
VLA Context - 共享组件容器

由 VLAActionDispatcher 创建并管理生命周期，传递给各 task handler。

职责划分:
    VLAContext (共享, 长生命周期)
        ├─ config        系统配置（只读）
        └─ robot_body    机器人驱动 (ROS2, 连接成本高)

    create_vla_components() → per-task (轻量, 用完即销毁)
        ├─ vla_zmq              ZMQ 通信客户端
        ├─ rdm                  实时数据管理器
        ├─ inter_chunk_fuser    块间融合器
        ├─ intra_chunk_smoother 块内平滑器
        ├─ task_language_mgr    任务语言管理器
        └─ vla_client           VLA 客户端 (观测→推理→控制)
"""

import sys
import os
import time
import threading

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


class VLAContext:
    """共享的 VLA 组件容器

    由 VLAActionDispatcher 创建，传递给各 task handler 的 execute() 方法。

    注意: robot_body 采用懒加载（首次访问时创建），
    避免在 dispatcher 初始化阶段创建机器人 ROS2 节点导致 DDS wait set 竞争。

    robot_body 使用独立的 rclpy.Context，与 dispatcher 的默认 context 隔离，
    彻底消除 "wait set index too big" 错误。
    """

    def __init__(self):
        from conf.client_conf import get_client_config

        self.config = get_client_config()

        # 将机器人专属 action_layout 传播到 rdm / intra_chunk 子配置
        # （与 run_client.py / web_client 的初始化逻辑对齐）
        robot_cfg = getattr(self.config.robots, self.config.robots.type.value, None)
        if robot_cfg is not None and hasattr(robot_cfg, 'action_layout'):
            self.config.rdm.action_layout = robot_cfg.action_layout
            self.config.intra_chunk.action_layout = robot_cfg.action_layout

        self._robot_body = None  # 懒加载
        self._robot_context = None  # robot_body 专属 ROS2 context（隔离 wait set）
        self._active_vla_client = None  # 当前活跃的 VLA 客户端（供 ObsDataBridge 读取进度）
        self._initialized = False  # 是否已执行过 init_grasp（跳过复位）
        self.grasp_detector = None  # 抓取状态检测器（由 dispatcher 注入）

        # ── 定时打印初始化标志（约 2s 间隔，便于调试）──
        self._print_init_running = True
        self._print_init_thread = threading.Thread(target=self._print_init_loop, daemon=True)
        self._print_init_thread.start()

    # ================================================================
    # robot_body 懒加载属性
    # ================================================================

    @property
    def robot_body(self):
        """获取 RobotBody 实例（懒加载，首次访问时创建）"""
        if self._robot_body is None:
            import rclpy
            from client.robots.unitree_g1.body_robot import RobotBody

            # 先确保全局 rclpy 初始化（幂等保护），传 args=[] 避免
            # sys.argv（如 --port）干扰 rcl 参数解析
            if not rclpy.ok():
                rclpy.init(args=[])

            # 创建独立 ROS2 context，与 dispatcher 隔离 wait set
            self._robot_context = rclpy.Context()
            if not self._robot_context.ok():
                self._robot_context.init(args=[])

            self._robot_body = RobotBody(self.config, ros_context=self._robot_context)
        return self._robot_body

    @robot_body.setter
    def robot_body(self, value):
        self._robot_body = value

    # ================================================================
    # 任务进度（供 ObsDataBridge 读取）
    # ================================================================

    @property
    def current_task_progress(self) -> float:
        """当前推理任务进度 (0.0~1.0)，无活跃任务时返回 0.0"""
        vc = self._active_vla_client
        if vc is None:
            return 0.0
        try:
            return float(getattr(vc, 'info_act', {}).get('current_prob_progress', 0.0))
        except Exception:
            return 0.0

    # ================================================================
    # Per-task VLA 组件工厂
    # ================================================================

    def create_vla_components(self) -> dict:
        """创建 VLA 推理所需的 per-task 组件

        与 web_client/server.py 的初始化方式保持严格一致。

        Returns:
            dict: {
                'vla_client':           VLAClientAsync,
                'vla_zmq':              ZMQClient,
                'rdm':                  RealtimeDataManager,
                'inter_chunk_fuser':    InterChunkFuser,
                'intra_chunk_smoother': IntraChunkSmoother,
                'task_language_manager': TaskLanguageManager,
            }
        """
        from client.core.zmq_client import ZMQClient
        from client.core.realtime_data_manager import RealtimeDataManager
        from client.core.inter_chunk_fuser import InterChunkFuser
        from client.core.intra_chunk_smoother import IntraChunkSmoother
        from client.core.task_language_manager import TaskLanguageManager
        from client.core.vla_client import VLAClientAsync

        vla_zmq = ZMQClient(self.config.vla_zmq)
        rdm = RealtimeDataManager(self.config.rdm)
        inter_chunk_fuser = InterChunkFuser(config=self.config.inter_chunk)
        intra_chunk_smoother = IntraChunkSmoother(config=self.config.intra_chunk)
        task_language_manager = TaskLanguageManager(config=self.config.language)

        # Action Server 模式下，语言指令由 task handler 显式设置
        # （如 GraspHandler 中的 TARGET_LANGUAGE_MAP），
        # 必须关闭 auto_mode 防止推理线程的 advance_subtask()
        # 将语言指令自动切回 config 中的默认任务列表。
        self.config.language.auto_mode = False

        vla_client = VLAClientAsync(
            config=self.config,
            realtime_data_manager=rdm,
            inter_chunk_fuser=inter_chunk_fuser,
            intra_chunk_smoother=intra_chunk_smoother,
            task_language_manager=task_language_manager,
            vla_zmq_client=vla_zmq,
            robot=self.robot_body,
        )
        return {
            'vla_client': vla_client,
            'vla_zmq': vla_zmq,
            'rdm': rdm,
            'inter_chunk_fuser': inter_chunk_fuser,
            'intra_chunk_smoother': intra_chunk_smoother,
            'task_language_manager': task_language_manager,
        }

    @staticmethod
    def destroy_vla_components(components: dict) -> None:
        """销毁 per-task VLA 组件

        Args:
            components: create_vla_components() 返回的字典
        """
        vla_client = components.get('vla_client')
        if vla_client is None:
            return

        try:
            vla_client.is_running_action = False
            time.sleep(0.1)
            vla_client.close()
        except Exception:
            pass

    # ================================================================
    # 生命周期
    # ================================================================

    def _print_init_loop(self):
        """每隔约 2 秒打印一次初始化状态，便于调试"""
        while self._print_init_running:
            time.sleep(2.0)
            print(f"[VLAContext] initialized={self._initialized}")

    def close(self) -> None:
        """清理所有共享资源（dispatcher 关闭时调用）"""
        self._print_init_running = False
        if self._robot_body is None:
            return

        # 复位机器人到安全姿态
        try:
            self._robot_body.reset_robot(mode='default')
            time.sleep(0.5)
        except Exception:
            pass
        try:
            self._robot_body.close()
        except Exception:
            pass

        # 关闭独立的 ROS2 context
        if self._robot_context is not None:
            try:
                if self._robot_context.ok():
                    self._robot_context.shutdown()
            except Exception:
                pass
            self._robot_context = None
