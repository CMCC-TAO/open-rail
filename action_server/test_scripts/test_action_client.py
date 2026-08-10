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
from typing import cast

# 项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from message_center.action import ExecutionUnit

# 全流程抓取配置表（单一数据源）
# 新增物体只需在 task_grasp.py 映射表 + task_grasp_all.py 配置表登记，
# 此处自动出现对应测试条目，无需手动维护。
from action_server.task_grasp_all import GRASP_ALL_SEQUENCES


# ============================================================
# 可用任务清单
# ============================================================
AVAILABLE_TASKS = {
    # ==================== 0-9: 初始化 (init) ====================
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
        "name": "init zero",
        "desc": "直接初始化 — 一步到位过渡到默认准备姿态（终点=init grasp，跳过中间安全姿态）",
        "params": {
            "task": "zero",
            "target": "init",
            "waypoint": "none",
        },
    },
    "3": {
        "name": "init clean",
        "desc": "初始化清理 — 机器人双臂从当前状态过渡到准备桌面清理姿态",
        "params": {
            "task": "clean",
            "target": "init",
            "waypoint": "none",
        },
    },
    # (4-9 预留: 更多初始化任务)

    # ==================== 10-19: 完成复位 (finish) ====================
    "10": {
        "name": "finish grasp",
        "desc": "抓取完成复位 — reset_robot 经安全中间姿态过渡到垂直复位姿态",
        "params": {
            "task": "grasp",
            "target": "finish",
            "waypoint": "none",
        },
    },
    "11": {
        "name": "finish grasp drainer",
        "desc": "抓取完成平衡点 — 双臂过渡到平衡点(默认全零)，手掌保持当前状态",
        "params": {
            "task": "grasp",
            "target": "finish",
            "waypoint": "drainer",
        },
    },
    # (12-19 预留: 更多 finish 任务)

    # ==================== 20+: 常规功能 ====================
    "20": {
        "name": "grasp one water",
        "desc": "单手抓取 — 使用一只手从娃哈哈堆中抓取一瓶",
        "params": {
            "task": "grasp",
            "target": "one water",
            "waypoint": "none",
        },
    },
    "21": {
        "name": "grasp one Coca-Cola",
        "desc": "单手抓取 — 使用一只手从可口可乐堆中抓取一瓶",
        "params": {
            "task": "grasp",
            "target": "one Coca-Cola",
            "waypoint": "none",
        },
    },
    "22": {
        "name": "grasp two water",
        "desc": "双手抓取 — 使用两只手从娃哈哈堆中抓取最近的两瓶",
        "params": {
            "task": "grasp",
            "target": "two water",
            "waypoint": "none",
        },
    },
    "23": {
        "name": "grasp two Coca-Cola",
        "desc": "双手抓取 — 使用两只手从可口可乐堆中抓取最近的两瓶",
        "params": {
            "task": "grasp",
            "target": "two Coca-Cola",
            "waypoint": "none",
        },
    },
    "29": {
        "name": "left arm deliver",
        "desc": "左手递物 — 3s 线性插值到左递物位姿 → 左手全开 → 保持 1s",
        "params": {
            "task": "deliver",
            "target": "left arm",
            "waypoint": "none",
        },
    },
    "30": {
        "name": "right arm deliver",
        "desc": "右手递物 — 3s 线性插值到右递物位姿 → 右手全开 → 保持 1s",
        "params": {
            "task": "deliver",
            "target": "right arm",
            "waypoint": "none",
        },
    },
    "31": {
        "name": "one arm deliver",
        "desc": "单手递物 — 自动判断哪只手有物体，路由到左手/右手递物",
        "params": {
            "task": "deliver",
            "target": "one arm",
            "waypoint": "none",
        },
    },
    "32": {
        "name": "both arm deliver",
        "desc": "双手递物 — 双臂同时递物，需双手都有物体",
        "params": {
            "task": "deliver",
            "target": "both arm",
            "waypoint": "none",
        },
    },
    "33": {
        "name": "left arm place",
        "desc": "左手放置 — 录制轨迹回放（左手），过渡+插补+平滑",
        "params": {
            "task": "place",
            "target": "left arm",
            "waypoint": "none",
        },
    },
    "34": {
        "name": "right arm place",
        "desc": "右手放置 — 录制轨迹回放（右手），过渡+插补+平滑",
        "params": {
            "task": "place",
            "target": "right arm",
            "waypoint": "none",
        },
    },
    "35": {
        "name": "one arm place",
        "desc": "单手放置 — 自动判断哪只手有物体，路由到左手/右手放置",
        "params": {
            "task": "place",
            "target": "one arm",
            "waypoint": "none",
        },
    },
    "36": {
        "name": "both arm place",
        "desc": "双手放置 — 录制轨迹回放（双手），需双手都有物体",
        "params": {
            "task": "place",
            "target": "both arm",
            "waypoint": "none",
        },
    },
    "37": {
        "name": "left hand release",
        "desc": "左手松手 — 左手 hand 的 6 个电机控制量设为 0，维持 1s",
        "params": {
            "task": "release",
            "target": "left hand",
            "waypoint": "none",
        },
    },
    "38": {
        "name": "right hand release",
        "desc": "右手松手 — 右手 hand 的 6 个电机控制量设为 0，维持 1s",
        "params": {
            "task": "release",
            "target": "right hand",
            "waypoint": "none",
        },
    },
    "39": {
        "name": "both hand release",
        "desc": "双手松手 — 双手 hand 的 6 个电机控制量设为 0，维持 1s",
        "params": {
            "task": "release",
            "target": "both hand",
            "waypoint": "none",
        },
    },
    "40": {
        "name": "left arm reset",
        "desc": "左手复位 — 3s 线性插值到左复位姿态 [0,0.3,0,1.3,0,0,0]，手掌不变",
        "params": {
            "task": "reset",
            "target": "left arm",
            "waypoint": "none",
        },
    },
    "41": {
        "name": "right arm reset",
        "desc": "右手复位 — 3s 线性插值到右复位姿态 [0,-0.3,0,1.3,0,0,0]，手掌不变",
        "params": {
            "task": "reset",
            "target": "right arm",
            "waypoint": "none",
        },
    },
    "42": {
        "name": "both arm reset",
        "desc": "双手复位 — 3s 线性插值双臂同时到复位姿态，手掌不变",
        "params": {
            "task": "reset",
            "target": "both arm",
            "waypoint": "none",
        },
    },
    "43": {
        "name": "clean start",
        "desc": "桌面清洁开始 — 固定语言指令调用 VLA 推理执行桌面清洁（收带垃圾的盘子/收空盘/清理散落垃圾）",
        "params": {
            "task": "clean",
            "target": "start",
            "waypoint": "none",
        },
    },
    "44": {
        "name": "clean all",
        "desc": "全流程桌面清洁（无重试）— init_clean + clean + finish_clean，target=all",
        "params": {
            "task": "clean",
            "target": "all",
            "waypoint": "none",
        },
    },
}


# ============================================================
# 全流程抓取条目：动态生成（与 task_grasp_all.GRASP_ALL_SEQUENCES 保持同步）
# 新增物体只需在 task_grasp.py 两个映射表 + task_grasp_all.py 配置表登记，
# 此处自动出现对应测试条目，无需手动维护编号。
# ============================================================
_grasp_all_items: list[tuple[str, str]] = []  # (编号, 名称)
_next_id = 24
for _target in GRASP_ALL_SEQUENCES:
    _key = str(_next_id)
    _next_id += 1
    AVAILABLE_TASKS[_key] = {
        "name": f"grasp all {_target}",
        "desc": f"全流程抓取（带重试）— init_grasp + grasp + finish_grasp，target={_target}",
        "params": {
            "task": "grasp",
            "target": _target,
            "waypoint": "all",
        },
    }
    _grasp_all_items.append((_key, f"grasp all {_target}"))

# 最大任务编号（用于交互提示）
_last_id = max(int(k) for k in AVAILABLE_TASKS)


# ============================================================
# 按源文件分组的任务结构（用于菜单展示）
# ============================================================
TASK_GROUPS = [
    {
        "title": "init",
        "items": [
            ("1", "init grasp"),
            ("2", "init zero"),
            ("3", "init clean"),
        ],
    },
    {
        "title": "finish",
        "items": [
            ("10", "finish grasp"),
            ("11", "finish grasp drainer"),
        ],
    },
    {
        "title": "grasp",
        "items": [
            ("20", "grasp one water"),
            ("21", "grasp one Coca-Cola"),
            ("22", "grasp two water"),
            ("23", "grasp two Coca-Cola"),
            *_grasp_all_items,
        ],
    },
    {
        "title": "deliver",
        "items": [
            ("29", "left arm deliver"),
            ("30", "right arm deliver"),
            ("31", "one arm deliver"),
            ("32", "both arm deliver"),
        ],
    },
    {
        "title": "place",
        "items": [
            ("33", "left arm place"),
            ("34", "right arm place"),
            ("35", "one arm place"),
            ("36", "both arm place"),
        ],
    },
    {
        "title": "release",
        "items": [
            ("37", "left hand release"),
            ("38", "right hand release"),
            ("39", "both hand release"),
        ],
    },
    {
        "title": "reset",
        "items": [
            ("40", "left arm reset"),
            ("41", "right arm reset"),
            ("42", "both arm reset"),
        ],
    },
    {
        "title": "clean",
        "items": [
            ("43", "clean start"),
            ("44", "clean all"),
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
        choice = input(f'请选择任务编号 (1-{_last_id} / q): ').strip().lower()

        if choice == 'q':
            print('退出测试客户端。')
            break

        if choice not in AVAILABLE_TASKS:
            print(f'⚠  无效选择: "{choice}"，请输入 1-{_last_id} 或 q')
            continue

        task = AVAILABLE_TASKS[choice]
        print(f'\n▶ 执行任务: {task["name"]}')
        print(f'  params = {json.dumps(task["params"], ensure_ascii=False)}')
        print()

        # 发送 goal（task_src=2 表示图形化编程/测试来源）
        params = cast(dict[str, object], task["params"])
        success = client.send_goal(task_src=2, params=params)

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
