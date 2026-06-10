#!/usr/bin/env python3
"""
VLA Action Server 测试客户端

交互式 CLI，向 action_server/action_dispatcher.py 发送 ExecutionUnit goal，
实时显示 feedback 并输出最终 result。

使用方式:
    # 先启动 action server（另一个终端）
    python3 action_server/action_dispatcher.py

    # 再启动测试客户端
    python3 action_server/test_scripts/test_action_client.py
"""

import sys
import os
import json
import time

# 项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from message_center.action import ExecutionUnit


# ============================================================
# 可用任务清单
# ============================================================
AVAILABLE_TASKS = {
    "1": {
        "name": "init grasp",
        "desc": "初始化抓取 — 机器人双臂从当前状态过渡到准备抓取姿态",
        "params": {
            "task": "init grasp",
            "target": "none",
            "waypoint": "none",
        },
    },
    "2": {
        "name": "one hand grasb",
        "desc": "单手抓取 — 使用 VLA 模型抓取指定目标（如 Wahaha）",
        "params": {
            "task": "one hand grasb",
            "target": "Wahaha",
            "waypoint": "none",
        },
    },
}


class VLAActionTestClient(Node):
    """VLA Action 测试客户端"""

    def __init__(self):
        super().__init__('vla_action_test_client')
        self._client = ActionClient(self, ExecutionUnit, 'vla_task')
        self.get_logger().info('VLA Action 测试客户端启动，等待 Action Server...')

    def wait_for_server(self, timeout_sec: float = 10.0) -> bool:
        """等待 Action Server 就绪"""
        return self._client.wait_for_server(timeout_sec=timeout_sec)

    def send_goal(self, task_src: int, params: dict) -> bool:
        """发送 action goal 并监控执行过程

        Args:
            task_src: 1=scheduler, 2=scratch
            params:   参数字典

        Returns:
            bool: 是否成功
        """
        goal_msg = ExecutionUnit.Goal()
        goal_msg.task_src = task_src
        goal_msg.params = json.dumps(params, ensure_ascii=False)

        self.get_logger().info('─' * 55)
        self.get_logger().info(f'发送 goal: task_src={task_src}')
        self.get_logger().info(f'         params={goal_msg.params}')
        self.get_logger().info('─' * 55)

        # 发送 goal，注册 feedback 回调和 result 回调
        send_goal_future = self._client.send_goal_async(
            goal_msg,
            feedback_callback=self._feedback_callback,
        )

        # 等待 goal 被接受
        rclpy.spin_until_future_complete(self, send_goal_future, timeout_sec=5.0)
        if not send_goal_future.done():
            self.get_logger().error('发送 goal 超时（5s），Server 未响应')
            return False

        goal_handle = send_goal_future.result()

        if not goal_handle.accepted:
            self.get_logger().error('Goal 被 Server 拒绝')
            return False

        self.get_logger().info('✔ Goal 被接受，等待执行结果...\n')

        # 等待 result
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=120.0)

        if not result_future.done():
            self.get_logger().error('等待 result 超时（120s）')
            return False

        result = result_future.result()
        self._print_result(result)
        return result.result.result == 1  # GetResult.Response.result.result == SUCCESS

    # ============================================================
    # 回调
    # ============================================================

    def _feedback_callback(self, feedback_msg):
        """实时打印 feedback"""
        fb = feedback_msg.feedback
        ts = time.strftime('%H:%M:%S')
        print(f'  [{ts}] {fb.message}')

    # ============================================================
    # 输出
    # ============================================================

    @staticmethod
    def _print_result(result):
        """格式化打印 result"""
        # result = GetResult.Response → .result = ExecutionUnit.Result → .result = uint8 状态码
        result_msg = result.result
        r = result_msg.result
        status = '✅ SUCCESS' if r == 1 else '❌ FAILED'
        print()
        print('═' * 55)
        print(f'  结果:     {status}')
        print(f'  错误码:   {result_msg.error_code}')
        print(f'  错误信息: {result_msg.error_message}')
        print('═' * 55)
        print()


# ============================================================
# 交互菜单
# ============================================================

def print_banner():
    """打印启动横幅"""
    print()
    print('╔═══════════════════════════════════════════════════╗')
    print('║        VLA Action Server — 测试客户端               ║')
    print('╚═══════════════════════════════════════════════════╝')
    print()


def print_menu():
    """打印任务菜单"""
    print()
    print('可用任务:')
    print('─' * 50)
    for key, task in AVAILABLE_TASKS.items():
        print(f'  [{key}] {task["name"]}')
        print(f'       {task["desc"]}')
        print(f'       params: {json.dumps(task["params"], ensure_ascii=False)}')
        print()
    print('  [q] 退出')
    print('─' * 50)


def main():
    rclpy.init()

    client = VLAActionTestClient()

    # 等待 server
    if not client.wait_for_server(timeout_sec=10.0):
        client.get_logger().error(
            'Action Server 未就绪！请确保 action_dispatcher.py 已在运行。'
        )
        client.destroy_node()
        rclpy.shutdown()
        sys.exit(1)

    client.get_logger().info('Action Server 已就绪 ✓\n')

    print_banner()

    while True:
        print_menu()
        choice = input('请选择任务编号 (1-2 / q): ').strip().lower()

        if choice == 'q':
            print('退出测试客户端。')
            break

        if choice not in AVAILABLE_TASKS:
            print(f'⚠  无效选择: "{choice}"，请输入 1-2 或 q')
            continue

        task = AVAILABLE_TASKS[choice]
        print(f'\n▶ 执行任务: {task["name"]}')
        print(f'  params = {json.dumps(task["params"], ensure_ascii=False)}')
        print()

        # 发送 goal（task_src=2 表示图形化编程/测试来源）
        success = client.send_goal(task_src=2, params=task["params"])

        if success:
            print('  ↳ 任务执行成功 ✓')
        else:
            print('  ↳ 任务执行失败 ✗')

        input('\n按 Enter 继续...')

    client.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
