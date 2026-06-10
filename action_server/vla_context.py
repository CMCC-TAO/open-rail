"""
VLA Context - 共享组件容器

由 VLAActionDispatcher 创建并管理生命周期，传递给各 task handler。

职责划分:
    VLAContext (共享, 长生命周期)
        ├─ config        系统配置（只读）
        └─ robot_body    机器人驱动 (ROS2, 连接成本高)

    create_vla_components() → per-task (轻量, 用完即销毁)
        ├─ vla_zmq          ZMQ 通信客户端
        ├─ rdm              实时数据管理器
        ├─ traj_generator   轨迹生成器
        └─ vla_client       VLA 客户端 (观测→推理→控制)
"""

import sys
import os
import time

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


class VLAContext:
    """共享的 VLA 组件容器

    由 VLAActionDispatcher 创建，传递给各 task handler 的 execute() 方法。

    注意: robot_body 采用懒加载（首次访问时创建），
    避免在 dispatcher 初始化阶段创建机器人 ROS2 节点导致 DDS wait set 竞争。
    """

    def __init__(self):
        from conf.client_conf import get_client_config

        self.config = get_client_config()
        self._robot_body = None  # 懒加载

    # ================================================================
    # robot_body 懒加载属性
    # ================================================================

    @property
    def robot_body(self):
        """获取 RobotBody 实例（懒加载，首次访问时创建）"""
        if self._robot_body is None:
            from client.robots.unitree_g1.body_robot import RobotBody

            self._robot_body = RobotBody(self.config)
        return self._robot_body

    @robot_body.setter
    def robot_body(self, value):
        self._robot_body = value

    # ================================================================
    # Per-task VLA 组件工厂
    # ================================================================

    def create_vla_components(self) -> dict:
        """创建 VLA 推理所需的 per-task 组件

        Returns:
            dict: {
                'vla_client': VLAClientAsync,
                'vla_zmq':    ZMQClient,
                'rdm':        RealtimeDataManager,
                'traj_generator': TrajectoryGenerator,
            }
        """
        from client.core.zmq_client import ZMQClient
        from client.core.realtime_data_manager import RealtimeDataManager
        from client.core.trajectory_generator import TrajectoryGenerator
        from client.core.vla_client import VLAClientAsync

        vla_zmq = ZMQClient(self.config.vla_zmq)
        rdm = RealtimeDataManager(self.config.rdm)
        traj_generator = TrajectoryGenerator(config=self.config.traj)
        vla_client = VLAClientAsync(
            config=self.config,
            rdm=rdm,
            traj_generator=traj_generator,
            vla_zmq_client=vla_zmq,
            robot=self.robot_body,
        )
        return {
            'vla_client': vla_client,
            'vla_zmq': vla_zmq,
            'rdm': rdm,
            'traj_generator': traj_generator,
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

    def close(self) -> None:
        """清理所有共享资源（dispatcher 关闭时调用）"""
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
