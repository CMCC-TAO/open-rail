"""action_server 专用的 RobotBody 扩展 —— 不改动 client/ 下任何文件。

背景
----
master 的 ``RobotProxy`` 只把 worker 子进程里 RobotBody 的**公开 callable**
转发给父进程（见 ``client/robots/robot_proxy.py`` 的 ``_collect_metadata`` /
``__getattr__``），所以 ``robot_body.robot.latest_left_arm`` 这类**普通属性**
在代理对象上取不到。

``RobotProxy(robot_type, config, robot_module=...)`` 允许覆盖 worker 里实际
实例化的类（``robot_proxy.py:73-84``：``__import__(module_name,
fromlist=['RobotBody'])`` → ``module.RobotBody(config)``）。于是这里用**子类**
把 action_server 需要的状态查询包成**方法**，并只返回纯数值。

这样做的三点好处
    1. 改动全部落在 ``action_server/`` 内，``client/`` 与 master 零分叉；
    2. 所有方法都是公开 callable，``RobotProxy`` 会自动转发，无需改代理；
    3. 进程内（直接用本类）与进程外（RobotProxy 通过 robot_module 注入本类）
       两种部署方式，上层调用完全一致。

用法
----
进程内::

    from action_server.robot_body_ext import RobotBody
    robot_body = RobotBody(config, ros_context=ctx)

进程外（master 框架）::

    from client.robots.robot_proxy import RobotProxy
    robot_body = RobotProxy('unitree_g1', config,
                            robot_module='action_server.robot_body_ext')

只返回纯数值是刻意设计：``latest_*`` 内部存的是 ``(ROS消息, 时间戳)`` 元组，
跨进程需要 pickle，搬运 ROS 消息对象既慢又脆，因此一律在此处取好数值再返回。
"""

import numpy as np

from client.robots.unitree_g1.body_robot import RobotBody as _BaseRobotBody


class RobotBody(_BaseRobotBody):
    """在 unitree_g1 原生 RobotBody 上增加跨进程可用的状态查询接口。"""

    # ==================================================================
    # 动作下发转发
    # ------------------------------------------------------------------
    # 这两个接口定义在**内层** UnitreeG1Robot 上，原生 RobotBody 并没有
    # 暴露它们（body_robot.py 只有 control_robot / execute_action /
    # reset_robot / move_arms / retrieve_observation / close）。而
    # RobotProxy 只转发 worker 里那个 RobotBody 的公开 callable，
    # 所以这里显式转发，让 `robot.send_robot_action(...)` 在进程内/进程外
    # 都能用。
    # ==================================================================

    def send_robot_action(self, action):
        """下发 26 维动作（手臂 14 + 左手 6 + 右手 6）。"""
        return self.robot.send_robot_action(action)

    def reset_robot_with_motion(self, target_pose=None, mode='default',
                                max_velocity=None, max_acceleration=None,
                                max_jerk=None):
        """带运动参数的复位。

        为什么不直接用 ``reset_robot``：``RobotProxy`` 上**显式定义**了
        ``reset_robot(target_pose=None, mode='default')``
        （``client/robots/robot_proxy.py:526-528``），签名比真实实现窄
        （``body_robot.py:122-123`` 还有 max_velocity/max_acceleration/max_jerk）。
        显式方法会遮蔽 ``__getattr__`` 的通用方法转发，所以带运动参数调用会直接
        TypeError（web_client 不传这些参数，因此没暴露该问题）。

        本方法名在代理上没有定义，会被正常转发到 worker 中的本类实现，
        从而在进程内 / 进程外两种部署下行为一致。
        """
        return super().reset_robot(
            target_pose=target_pose,
            mode=mode,
            max_velocity=max_velocity,
            max_acceleration=max_acceleration,
            max_jerk=max_jerk,
        )

    def get_current_arm_state(self):
        """当前双臂关节状态（14 维 ndarray）。"""
        return self.robot._get_current_arm_state()

    # ==================================================================
    # 状态查询接口（跨进程安全）
    # ==================================================================

    def has_force_sensor(self) -> bool:
        """是否已收到触觉传感器数据（力传感器模式的可用性判断）。"""
        return bool(getattr(self.robot, 'has_force_sensor', False))

    def get_latest_touch_tf_sum(self, side: str):
        """返回指定手最新一帧的切向力总和。

        Returns:
            int   —— 有触觉数据时的切向力总和；
            None  —— 尚无触觉数据（**刻意与 0 区分**：调用方在拖拽检测的
                     滚动基线里用 `drop = baseline - tf` 判断，若把"无数据"
                     当成 0，会得到 drop≈baseline 而误触发）。
        """
        touch = getattr(self.robot, f'latest_{side}_touch', None)
        if not touch:
            return None
        msg = touch[0]
        if msg is None:
            return None
        try:
            return int(self.robot.get_touch_tf_sum(msg))
        except Exception:
            return None

    def _latest_msg_position(self, name: str):
        """取 self.robot.<name> = (msg, ts) 里的 msg.position；不可用返回 None。"""
        entry = getattr(self.robot, name, None)
        if not entry:
            return None
        msg = entry[0]
        if msg is None or not getattr(msg, 'position', None):
            return None
        return np.asarray(msg.position, dtype=float)

    def get_latest_arm_positions(self, side: str):
        """指定臂最新一帧的关节位置（ndarray）；无数据返回 None。"""
        return self._latest_msg_position(f'latest_{side}_arm')

    def get_latest_hand_positions(self, side: str):
        """指定手最新一帧的关节位置（ndarray）；无数据返回 None。"""
        return self._latest_msg_position(f'latest_{side}_hand')

    def get_latest_arm_action(self, side: str):
        """指定臂最新一次下发的目标位置（ndarray）；无数据返回 None。"""
        return self._latest_msg_position(f'latest_{side}_arm_action')

    def get_latest_hand_action(self, side: str):
        """指定手最新一次下发的目标位置（ndarray）；无数据返回 None。"""
        return self._latest_msg_position(f'latest_{side}_hand_action')

    def get_current_hand_state(self, side: str):
        """指定手当前的实测关节状态（ndarray）；无数据返回 None。"""
        state = getattr(self.robot, f'current_{side}_hand_state', None)
        if state is None:
            return None
        return np.asarray(state, dtype=float)

    def set_clamp_enabled(self, relative=None, absolute=None) -> bool:
        """开/关相对限幅与绝对限幅（仿真模式需要关闭）。

        Args:
            relative: True / False / None(保持不动)
            absolute: True / False / None(保持不动)
        """
        if relative is not None:
            self.robot.enable_relative_clamp = bool(relative)
        if absolute is not None:
            self.robot.enable_absolute_clamp = bool(absolute)
        return True
