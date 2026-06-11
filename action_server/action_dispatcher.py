"""
VLA Action Dispatcher - 任务分发型 ROS2 Action Server

以 params 中的 task 字段为路由键，将 goal 分发给对应的 handler 执行。
"""

import sys
import os
import time
import json

# 项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import rclpy
from rclpy.action import ActionServer, CancelResponse
from rclpy.node import Node
from message_center.action import ExecutionUnit

from action_server.action_base import AbstractTaskHandler, TaskResult
from action_server.vla_context import VLAContext


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

    def __init__(self):
        super().__init__('vla_action_server')

        self.get_logger().info('VLA Action Dispatcher starting...')

        # 创建共享上下文（config + robot_body 等长生命周期资源）
        self._context = VLAContext()
        self.get_logger().info('VLA context created (robot_body lazy, will init on first use)')

        # 任务处理器注册表: task_name -> AbstractTaskHandler
        self._handlers: dict[str, AbstractTaskHandler] = {}

        # 注册内置 handler
        self._register_builtin_handlers()

        # 创建 Action Server
        self._action_server = ActionServer(
            self,
            ExecutionUnit,
            'vla_task',
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
            self.register_handler(InitGraspHandler())
        except ImportError as e:
            self.get_logger().warn(f'Failed to load init_grasp handler: {e}')

        try:
            from action_server.task_grasp import GraspHandler
            self.register_handler(GraspHandler())
        except ImportError as e:
            self.get_logger().warn(f'Failed to load grasp handler: {e}')

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
        handler = self._handlers.get(task_name)
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
    rclpy.init(args=args)

    dispatcher = None
    try:
        dispatcher = VLAActionDispatcher()

        # 预初始化 robot_body：在 spin 循环启动前完成所有 ROS2 节点的创建，
        # 避免 execute_callback 中懒加载新节点导致 wait set 重建时
        # 产生 "wait set index too big" 错误。
        dispatcher.get_logger().info('Pre-initializing robot_body (may take a few seconds)...')
        _ = dispatcher._context.robot_body
        dispatcher.get_logger().info('robot_body pre-initialized, wait set is stable')

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
