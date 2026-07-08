#!/usr/bin/env bash
# ============================================================
# VLA Action Server — 三终端 tmux 启动脚本
#
# 左上窗格: action_dispatcher.py (服务端)
# 右上窗格: test_action_client.py (测试客户端)
# 下窗格:   action_web_vision Web 可视化 (http://localhost:9000)
# 光标:     停留在右上窗格，可直接选择任务
# ============================================================

SESSION_NAME="vla_action_test"

# 如果 session 已存在，先关闭
tmux kill-session -t "$SESSION_NAME" 2>/dev/null

# 创建新 session，仅创建窗口但不附加
tmux new-session -d -s "$SESSION_NAME" -n "action_test"

# 左上窗格：Action Server
tmux send-keys -t "$SESSION_NAME" "cd $(dirname "$0")" Enter
tmux send-keys -t "$SESSION_NAME" "conda activate gr00t && python3 action_server/action_dispatcher.py --robot_type unitree_g1" Enter

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
