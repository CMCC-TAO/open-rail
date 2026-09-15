"""
VLA Action Server - ROS2 Action Server 模块化实现

每个任务功能独立为一个文件，由 action_dispatcher.py 统一分发。
"""

# 注意：本包 **不** 在此处再导出子模块。
# RobotProxy 的 worker 子进程会 `import action_server.robot_body_ext`
# （通过 robot_module 注入），而任何对 action_server 子模块的导入都会先执行
# 本文件。这里如果顺手拉起 action_dispatcher / vla_context，就会把 rclpy、
# message_center 等重依赖带进只负责机器人 I/O 的 worker 进程，既拖慢启动
# 又平添失败面。需要这些符号的调用方请直接导入对应子模块，例如：
#     from action_server.action_dispatcher import VLAActionDispatcher
