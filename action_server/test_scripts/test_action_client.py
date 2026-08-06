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
            "task": "grasp",
            "target": "init",
            "waypoint": "none",
        },
    },
    "2": {
        "name": "grasp one water",
        "desc": "单手抓取 — 使用一只手从娃哈哈堆中抓取一瓶",
        "params": {
            "task": "grasp",
            "target": "one water",
            "waypoint": "none",
        },
    },
    "3": {
        "name": "grasp one Coca-Cola",
        "desc": "单手抓取 — 使用一只手从可口可乐堆中抓取一瓶",
        "params": {
            "task": "grasp",
            "target": "one Coca-Cola",
            "waypoint": "none",
        },
    },
    "4": {
        "name": "grasp two water",
        "desc": "双手抓取 — 使用两只手从娃哈哈堆中抓取最近的两瓶",
        "params": {
            "task": "grasp",
            "target": "two water",
            "waypoint": "none",
        },
    },
    "5": {
        "name": "grasp two Coca-Cola",
        "desc": "双手抓取 — 使用两只手从可口可乐堆中抓取最近的两瓶",
        "params": {
            "task": "grasp",
            "target": "two Coca-Cola",
            "waypoint": "none",
        },
    },
    "6": {
        "name": "finish grasp",
        "desc": "抓取完成复位 — reset_robot 经安全中间姿态过渡到垂直复位姿态",
        "params": {
            "task": "grasp",
            "target": "finish",
            "waypoint": "none",
        },
    },
    "7": {
        "name": "grasp all one water",
        "desc": "全流程抓取（带重试）— init_grasp + grasp(最多3次) + finish_grasp，target=one water",
        "params": {
            "task": "grasp",
            "target": "one water",
            "waypoint": "all",
        },
    },
    "8": {
        "name": "left arm deliver",
        "desc": "左手递物 — 3s 线性插值到左递物位姿 → 左手全开 → 保持 1s",
        "params": {
            "task": "deliver",
            "target": "left arm",
            "waypoint": "none",
        },
    },
    "9": {
        "name": "right arm deliver",
        "desc": "右手递物 — 3s 线性插值到右递物位姿 → 右手全开 → 保持 1s",
        "params": {
            "task": "deliver",
            "target": "right arm",
            "waypoint": "none",
        },
    },
    "10": {
        "name": "one arm deliver",
        "desc": "单手递物 — 自动判断哪只手有物体，路由到左手/右手递物",
        "params": {
            "task": "deliver",
            "target": "one arm",
            "waypoint": "none",
        },
    },
    "11": {
        "name": "both arm deliver",
        "desc": "双手递物 — 双臂同时递物，需双手都有物体",
        "params": {
            "task": "deliver",
            "target": "both arm",
            "waypoint": "none",
        },
    },
    "12": {
        "name": "left arm place",
        "desc": "左手放置 — 录制轨迹回放（左手），过渡+插补+平滑",
        "params": {
            "task": "place",
            "target": "left arm",
            "waypoint": "none",
        },
    },
    "13": {
        "name": "right arm place",
        "desc": "右手放置 — 录制轨迹回放（右手），过渡+插补+平滑",
        "params": {
            "task": "place",
            "target": "right arm",
            "waypoint": "none",
        },
    },
    "14": {
        "name": "one arm place",
        "desc": "单手放置 — 自动判断哪只手有物体，路由到左手/右手放置",
        "params": {
            "task": "place",
            "target": "one arm",
            "waypoint": "none",
        },
    },
    "15": {
        "name": "both arm place",
        "desc": "双手放置 — 录制轨迹回放（双手），需双手都有物体",
        "params": {
            "task": "place",
            "target": "both arm",
            "waypoint": "none",
        },
    },
    "16": {
        "name": "left hand release",
        "desc": "左手松手 — 左手 hand 的 6 个电机控制量设为 0，维持 1s",
        "params": {
            "task": "release",
            "target": "left hand",
            "waypoint": "none",
        },
    },
    "17": {
        "name": "right hand release",
        "desc": "右手松手 — 右手 hand 的 6 个电机控制量设为 0，维持 1s",
        "params": {
            "task": "release",
            "target": "right hand",
            "waypoint": "none",
        },
    },
    "18": {
        "name": "both hand release",
        "desc": "双手松手 — 双手 hand 的 6 个电机控制量设为 0，维持 1s",
        "params": {
            "task": "release",
            "target": "both hand",
            "waypoint": "none",
        },
    },
    "19": {
        "name": "left arm reset",
        "desc": "左手复位 — 3s 线性插值到左复位姿态 [0,0.3,0,1.3,0,0,0]，手掌不变",
        "params": {
            "task": "reset",
            "target": "left arm",
            "waypoint": "none",
        },
    },
    "20": {
        "name": "right arm reset",
        "desc": "右手复位 — 3s 线性插值到右复位姿态 [0,-0.3,0,1.3,0,0,0]，手掌不变",
        "params": {
            "task": "reset",
            "target": "right arm",
            "waypoint": "none",
        },
    },
    "21": {
        "name": "both arm reset",
        "desc": "双手复位 — 3s 线性插值双臂同时到复位姿态，手掌不变",
        "params": {
            "task": "reset",
            "target": "both arm",
            "waypoint": "none",
        },
    },
    "22": {
        "name": "init zero",
        "desc": "直接初始化 — 一步到位过渡到默认准备姿态（终点=init grasp，跳过中间安全姿态）",
        "params": {
            "task": "init zero",
            "target": "none",
            "waypoint": "none",
        },
    },
}


# ============================================================
# 按源文件分组的任务结构（用于菜单展示）
# ============================================================
TASK_GROUPS = [
    {
        "title": "grasp",
        "items": [
            ("1", "init grasp"),
            ("2", "grasp one water"),
            ("3", "grasp one Coca-Cola"),
            ("4", "grasp two water"),
            ("5", "grasp two Coca-Cola"),
            ("6", "finish grasp"),
            ("7", "grasp all one water"),
        ],
    },
    {
        "title": "deliver",
        "items": [
            ("8", "left arm deliver"),
            ("9", "right arm deliver"),
            ("10", "one arm deliver"),
            ("11", "both arm deliver"),
        ],
    },
    {
        "title": "place",
        "items": [
            ("12", "left arm place"),
            ("13", "right arm place"),
            ("14", "one arm place"),
            ("15", "both arm place"),
        ],
    },
    {
        "title": "release",
        "items": [
            ("16", "left hand release"),
            ("17", "right hand release"),
            ("18", "both hand release"),
        ],
    },
    {
        "title": "reset",
        "items": [
            ("19", "left arm reset"),
            ("20", "right arm reset"),
            ("21", "both arm reset"),
            ("22", "init zero"),
        ],
    },
]


class VLAActionTestClient(Node):
    """VLA Action 测试客户端"""

    def __init__(self):
        super().__init__('vla_action_test_client')
        self._client = ActionClient(self, ExecutionUnit, '/vla/action_ctrl')
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
    """打印任务菜单（按功能模块分组，每组 3 列横向排列）"""
    col_width = 22
    print()
    for group in TASK_GROUPS:
        title = group["title"]
        items = group["items"]
        # 单行标题：——————task xxx——————
        content = f'task {title}'
        pad_total = 50 - len(content)
        left = pad_total // 2
        right = pad_total - left
        print(f'{"—" * left}{content}{"—" * right}')
        # 3 列布局
        for i in range(0, len(items), 3):
            row_items = items[i:i + 3]
            line_parts = []
            for key, name in row_items:
                line_parts.append(f'[{key}] {name}')
            while len(line_parts) < 3:
                line_parts.append('')
            print(f'{line_parts[0]:<{col_width}}{line_parts[1]:<{col_width}}{line_parts[2]}')
    print(f'[q] 退出')
    print(f'{"—" * 50}')


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
        choice = input('请选择任务编号 (1-22 / q): ').strip().lower()

        if choice == 'q':
            print('退出测试客户端。')
            break

        if choice not in AVAILABLE_TASKS:
            print(f'⚠  无效选择: "{choice}"，请输入 1-22 或 q')
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
