#!/usr/bin/env bash
# ============================================================
# VLA Action Server — 仿真模式 tmux 启动脚本
#
# 与 run_action_test.sh 的区别：
#   传递 --sim 标志，禁用相对位置限幅（允许大幅轨迹规划）
#
# 左上窗格: action_dispatcher.py (服务端, --sim 模式)
# 右上窗格: test_action_client.py (测试客户端)
# 下窗格:   action_web_vision Web 可视化 (http://localhost:9000)
# 光标:     停留在右上窗格，可直接选择任务
# ============================================================

SESSION_NAME="vla_action_sim"

# 如果 session 已存在，先关闭
tmux kill-session -t "$SESSION_NAME" 2>/dev/null

# 创建新 session，仅创建窗口但不附加
tmux new-session -d -s "$SESSION_NAME" -n "action_sim"

# 左上窗格：Action Server（--sim 仿真模式）
tmux send-keys -t "$SESSION_NAME" "cd $(dirname "$0")" Enter
tmux send-keys -t "$SESSION_NAME" "conda activate gr00t && python3 action_server/action_dispatcher.py --robot_type unitree_g1 --sim" Enter

# 等待一下让 server 启动显示日志
sleep 1.5

# 右上窗格：垂直分割 → 测试客户端
tmux split-window -h -t "$SESSION_NAME"
tmux send-keys -t "$SESSION_NAME" "cd $(dirname "$0")" Enter
tmux send-keys -t "$SESSION_NAME" "sleep 1 && python3 action_server/test_scripts/test_action_client.py" Enter

# 下窗格：垂直分割 → Web 可视化服务器
tmux split-window -v -t "$SESSION_NAME"
tmux send-keys -t "$SESSION_NAME" "cd $(dirname "$0")" Enter
tmux send-keys -t "$SESSION_NAME" "sleep 3 && conda activate gr00t && python3 action_server/action_web_vision/server.py" Enter

# 光标聚焦到右上窗格（索引 1）- 测试客户端
tmux select-pane -t "$SESSION_NAME:.1"

# 附加到 session（显示给用户）
tmux attach-session -t "$SESSION_NAME"
