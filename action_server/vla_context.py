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

    def __init__(self, robot_type: str = None, sim_mode: bool = False):
        from conf.client_conf import get_client_config

        self.config = get_client_config()
        self._sim_mode = sim_mode

        # ════════════════════════════════════════════════════════════
        # 加载 default_conf.yaml 覆盖 Python 默认值
        # （与 web_client/server.py:_lifespan 的初始化一致）
        # ════════════════════════════════════════════════════════════
        _yaml_path = os.path.join(_project_root, 'conf', 'default_conf.yaml')
        if os.path.exists(_yaml_path):
            try:
                import yaml
                with open(_yaml_path, 'r') as _f:
                    _yaml_data = yaml.safe_load(_f)
                if isinstance(_yaml_data, dict):
                    self._apply_yaml_overrides(self.config, _yaml_data)
            except Exception as e:
                print(f'[VLAContext] Warning: failed to load default_conf.yaml: {e}')

        # 如果传入了 robot_type，覆盖默认配置
        if robot_type is not None:
            from conf.robots_conf import RobotType
            self.config.robots.type = RobotType(robot_type)

        # 将机器人专属 action_layout 传播到 rdm / intra_chunk 子配置
        # （与 run_client.py / web_client 的初始化逻辑对齐）
        robot_cfg = getattr(self.config.robots, self.config.robots.type.value, None)
        if robot_cfg is not None and hasattr(robot_cfg, 'action_layout'):
            self.config.action_layout = robot_cfg.action_layout
            self.config.rdm.action_layout = robot_cfg.action_layout
            self.config.intra_chunk.action_layout = robot_cfg.action_layout

        self._robot_body = None  # 懒加载
        self._robot_context = None  # robot_body 专属 ROS2 context（隔离 wait set）
        self._active_vla_client = None  # 当前活跃的 VLA 客户端（供 ObsDataBridge 读取进度）
        self._initialized = False  # 是否已执行过 init_grasp（跳过复位）
        self.grasp_detector = None  # 抓取状态检测器（由 dispatcher 注入）

        # ════════════════════════════════════════════════════════════
        # 持久化 VLA 组件（跨任务复用，由 init_grasp 创建，finish_grasp 销毁）
        # ════════════════════════════════════════════════════════════
        self._vla_components = None

        # ════════════════════════════════════════════════════════════
        # 创建共享 ZMQ 客户端（dispatcher 启动时即建立连接，
        # 避免每个 task 首次推理因连接未就绪而超时）
        # ════════════════════════════════════════════════════════════
        _start = time.time()
        from client.core.zmq_client import ZMQClient
        self._shared_zmq = ZMQClient(self.config.vla_zmq)
        print(f'[VLAContext] Shared ZMQ client created, waiting for connection...')
        while time.time() - _start < 3.0:
            if getattr(self._shared_zmq, 'is_connected', False):
                print(f'[VLAContext] ZMQ connected in {time.time()-_start:.1f}s')
                break
            time.sleep(0.05)
        else:
            print(f'[VLAContext] WARNING: ZMQ not connected within 3s, continuing anyway')

        # ── 定时打印初始化标志（约 2s 间隔，便于调试）──
        self._print_init_running = True
        self._print_init_thread = threading.Thread(target=self._print_init_loop, daemon=True)
        self._print_init_thread.start()

    # ────────────────────────────────────────────────────────────────
    # YAML 配置覆盖（只修改已有键，不创建新键）
    # ────────────────────────────────────────────────────────────────

    @staticmethod
    def _apply_yaml_overrides(config, yaml_data: dict):
        """将 yaml 数据以 flat-patch 方式覆盖到 config 的已有键上。"""
        # 将 yaml 数据展平为点分键字典
        flat = {}
        def _flatten(d, prefix=''):
            for k, v in d.items():
                full = f'{prefix}.{k}' if prefix else k
                if isinstance(v, dict):
                    _flatten(v, full)
                else:
                    flat[full] = v
        _flatten(yaml_data)

        # 遍历 config 叶子节点，匹配则打补丁
        def _walk(node, prefix=''):
            from ml_collections import ConfigDict
            keys = list(node.keys()) if isinstance(node, (dict, ConfigDict)) else []
            for k in keys:
                child = node[k]
                path = f'{prefix}.{k}' if prefix else k
                if isinstance(child, (dict, ConfigDict)):
                    _walk(child, path)
                elif path in flat:
                    val = flat[path]
                    # 处理 Enum 类型
                    import enum as _enum
                    if isinstance(child, _enum.Enum):
                        enum_cls = child.__class__
                        try:
                            val = enum_cls(val)
                        except Exception:
                            pass
                    node[k] = val
        _walk(config)

    # ================================================================
    # robot_body 懒加载属性
    # ================================================================

    @property
    def robot_body(self):
        """获取机器人对象（懒加载，首次访问时创建）。

        走 master 的进程化框架：真实 ``RobotBody`` 与厂商 SDK 跑在 spawn
        子进程里，父进程只持有 ``RobotProxy``（消除与 VLA 客户端之间的 GIL
        争抢，并隔离 SDK 崩溃 / rclpy executor 冲突）。

        子进程里实例化的类由 ``robot_module`` 指定为 action_server 自己的
        子类（``robot_body_ext.RobotBody``，见该文件说明），因此状态查询方法
        在代理上可用，同时 client/ 下没有任何改动。
        """
        if self._robot_body is None:
            from client.robots.robot_proxy import RobotProxy

            # 跨进程前必须摘掉 record 子树：它带点号键（record.lerobot['cam.head']），
            # ConfigDict 无法 pickle 往返（__setstate__ 会在恢复 allow_dotted_keys
            # 之前按字段名重新校验，连 deepcopy 都失败），而 worker 根本不读它。
            # 与 web_client/server.py:_create_robot 的处理保持一致。
            _saved_record = self.config.record
            self.config.record = None
            try:
                self._robot_body = RobotProxy(
                    self.config.robots.type.value,
                    self.config,
                    robot_module='action_server.robot_body_ext',
                )
            finally:
                self.config.record = _saved_record

            # 仿真模式：禁用相对限幅和绝对限幅，允许大幅轨迹规划
            if self._sim_mode:
                self._robot_body.set_clamp_enabled(relative=False, absolute=False)
                print('[VLAContext] SIM MODE: Relative & absolute limits disabled')
        return self._robot_body

    @robot_body.setter
    def robot_body(self, value):
        self._robot_body = value

    # ================================================================
    # 任务进度（供 ObsDataBridge 读取）
    # ================================================================

    @property
    def is_inference_running(self) -> bool:
        """当前推理线程是否在运行"""
        vc = self._active_vla_client
        if vc is None:
            return False
        try:
            return bool(getattr(vc, 'is_inference_thread_running', False))
        except Exception:
            return False

    @property
    def infer_count(self) -> int:
        """当前已完成的推理步数"""
        vc = self._active_vla_client
        if vc is None:
            return 0
        try:
            rdm = getattr(vc, 'realtime_data_manager', None)
            if rdm is not None:
                return int(getattr(rdm, 'infer_count', 0))
            return 0
        except Exception:
            return 0

    @property
    def current_task_progress(self) -> float:
        """当前推理任务进度 (0.0~1.0)，无活跃任务时返回 0.0"""
        vc = self._active_vla_client
        if vc is None:
            return 0.0
        try:
            return float(getattr(vc, 'current_prob_progress', 0.0))
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
                'vla_client':           VLAClient,
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
        from client.core.vla_client import VLAClient

        # 使用共享的 ZMQ 客户端（避免 task 内首次 inference 超时）
        vla_zmq = self._shared_zmq
        self.config.language.auto_mode = False

        rdm = RealtimeDataManager(self.config.rdm)
        inter_chunk_fuser = InterChunkFuser(config=self.config.inter_chunk)
        intra_chunk_smoother = IntraChunkSmoother(config=self.config.intra_chunk)
        task_language_manager = TaskLanguageManager(config=self.config.language)

        vla_client = VLAClient(
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

    # ================================================================
    # 持久化 VLA 组件（跨任务复用）
    # ================================================================

    def ensure_vla_components(self) -> dict:
        """获取持久化的 VLA 组件

        如果组件尚未创建，则创建它们。
        可跨任务复用（init_grasp 创建，finish_grasp 销毁）。
        """
        if self._vla_components is None:
            self._vla_components = self.create_vla_components()
            vc = self._vla_components.get('vla_client')
            if vc is not None:
                self._active_vla_client = vc
                print('[VLAContext] Persistent VLA components created')
        return self._vla_components

    def clear_vla_components(self) -> None:
        """清理持久化的 VLA 组件"""
        if self._vla_components is not None:
            print('[VLAContext] Clearing persistent VLA components...')
            self._active_vla_client = None
            self.destroy_vla_components(self._vla_components)
            self._vla_components = None
            print('[VLAContext] Persistent VLA components cleared')

    @property
    def vla_components(self) -> dict | None:
        """获取持久化的 VLA 组件（可能为 None）"""
        return self._vla_components

    def destroy_vla_components(self, components: dict) -> None:
        """销毁 per-task VLA 组件（不关闭共享 ZMQ 连接）

        手动执行 vla_client.close() 的全部清理逻辑，但跳过 ZMQ 关闭，
        因为 ZMQ 连接由 VLAContext 统一管理。

        Args:
            components: create_vla_components() 返回的字典
        """
        vla_client = components.get('vla_client')
        if vla_client is None:
            return

        try:
            vla_client.is_running_action = False
            time.sleep(0.1)

            # 手动执行 vla_client.close() 的所有清理步骤，跳过 ZMQ
            vla_client.is_observe_thread_running = False
            vla_client.is_inference_thread_running = False
            vla_client.is_control_thread_running = False
            vla_client.is_running = False

            if vla_client.observe_thread.is_alive():
                vla_client.observe_thread.join(timeout=1.0)
            # process_observe_thread 也要 join：它是 _raw_observe_queue 的消费端，
            # 还在解码共享内存帧时就去关 shm 会与它竞争（对照 VLAClient.close()）
            if vla_client.process_observe_thread.is_alive():
                vla_client.process_observe_thread.join(timeout=1.0)
            if vla_client.inference_thread.is_alive():
                vla_client.inference_thread.join(timeout=1.0)
            if vla_client.control_thread_timer.is_alive():
                vla_client.control_thread_timer.stop(timeout=1.0)
            # 注意：旧版 VLAClient 的 visualize_thread_timer 已被移除
            # （client/core/vla_client.py 中该属性全部为注释，从未赋值）。
            # 这里一旦访问它就抛 AttributeError，会被下面的 except Exception 吞掉，
            # 导致其后所有清理步骤（录制器 / 可视化 / 线程池 / 共享内存）全部被跳过。
            # 可视化服务停在下方的 visualize_server.stop_server() 里。

            if hasattr(vla_client, 'data_record_manager') and vla_client.data_record_manager is not None:
                vla_client.data_record_manager.close()

            # 不关闭 vla_zmq（共享连接，由 VLAContext 管理）
            vla_client.visualize_server.stop_server()

            if hasattr(vla_client, '_img_executor') and vla_client._img_executor is not None:
                vla_client._img_executor.shutdown(wait=False)

            # ── 共享内存（SharedMemoryManager）释放 ──
            # VLAClient.close() 会执行以下两步，手工复刻时曾漏掉，
            # 导致 ring_size(30) × 相机数 个 shm 块永久残留在 /dev/shm。
            from client.core.shared_memory_manager import SharedMemoryManager

            if hasattr(vla_client, '_clear_raw_observe_queue'):
                vla_client._clear_raw_observe_queue()
            _shm_cache = getattr(vla_client, '_raw_observe_shm_cache', None)
            if _shm_cache:
                # reader 侧：只解除映射，不影响生产端
                SharedMemoryManager.close_reader(_shm_cache)
            _shm_mgr = getattr(vla_client, 'shared_memory_manager', None)
            if _shm_mgr is not None:
                # producer 侧：本客户端自己的池，需要 close + unlink
                _shm_mgr.close()

            # 清空共享 ZMQ 上的残留响应
            # 上一个 task 销毁时，可能在 ZMQ dealer socket 上留有未消费的
            # inference 响应，如果不清理，下一个 task 的 _inference_first()
            # 会收到 stale response 导致超时重试，造成首帧推理延迟 ~2.5s
            zmq_client = components.get('vla_zmq')
            if zmq_client is not None:
                _dealer = getattr(zmq_client, 'dealer', None)
                if _dealer is not None:
                    _drained = 0
                    import zmq as _zmq
                    for _ in range(100):
                        try:
                            if _dealer.poll(timeout=1) == 0:
                                break
                            _dealer.recv_multipart(flags=_zmq.NOBLOCK)
                            _drained += 1
                        except (_zmq.ZMQError, Exception):
                            break
                    if _drained > 0:
                        print(f'[VLAContext] Drained {_drained} stale ZMQ message(s)')

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

        # 清理持久化 VLA 组件
        self.clear_vla_components()

        # 关闭共享 ZMQ 客户端
        if hasattr(self, '_shared_zmq') and self._shared_zmq is not None:
            try:
                self._shared_zmq.close()
                print(f'[VLAContext] Shared ZMQ client closed')
            except Exception:
                pass
            self._shared_zmq = None

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
