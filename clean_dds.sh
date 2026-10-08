#!/bin/bash
# ============================================================
# clean_dds.sh — 清理 CycloneDDS / ROS2 残留进程与共享内存
#
# 用法:
#   bash scripts/clean_dds.sh          # 查看 + 清理
#   bash scripts/clean_dds.sh --dry    # 仅查看，不清理
# ============================================================

set -euo pipefail

DRY_RUN=false
[[ "${1:-}" == "--dry" ]] && DRY_RUN=true

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo "  DDS / ROS2 残留清理工具"
echo "============================================"

# ── 1. 查找残留进程 ──
echo ""
echo -e "${YELLOW}[1/3] 查找残留的 DDS/ROS2 相关进程...${NC}"

# 匹配: python run_web_client / run_client / run_server,
#        ros2, rviz, robot_state_publisher, unitree_g1_drivers
ORPHAN_PIDS=$(ps -eo pid,ppid,cmd \
    | grep -E '(vla_action|action_dispatcher|run_web_client|run_client|run_server|ros2|rviz|robot_state_publisher|unitree_g1_drivers)' \
    | grep -v grep \
    | grep -v "clean_dds" \
    || true)

# 也通过端口查找残留（更精准，不依赖进程名）
# 已知端口：9000(web_client), 9001(ObsBridge), 8765(visual WS), 8080(visual static)
PORT_PIDS=""
for port in 9000 9001 8765 8080; do
    SS_OUT=$(ss -tlnp "sport = :$port" 2>/dev/null || true)
    if [[ -n "$SS_OUT" ]]; then
        PORT_PID=$(echo "$SS_OUT" | grep -oP 'pid=\K\d+' || true)
        if [[ -n "$PORT_PID" ]]; then
            PORT_PIDS="$PORT_PIDS $PORT_PID"
        fi
    fi
done

# 合并端口发现的 PID 到 ORPHAN_PIDS
if [[ -n "$PORT_PIDS" ]]; then
    for pid in $PORT_PIDS; do
        if ! echo "$ORPHAN_PIDS" | awk '{print $1}' | grep -qw "$pid"; then
            CMD_LINE=$(ps -p "$pid" -o pid=,ppid=,cmd= 2>/dev/null || true)
            if [[ -n "$CMD_LINE" ]]; then
                ORPHAN_PIDS=$(printf "%s\n%s" "$ORPHAN_PIDS" "$CMD_LINE")
            fi
        fi
    done
fi

if [[ -z "$ORPHAN_PIDS" ]]; then
    echo -e "${GREEN}  没有发现残留进程 ✓${NC}"
else
    echo -e "${RED}  发现残留进程:${NC}"
    echo "$ORPHAN_PIDS" | awk '{printf "    PID=%-8s PPID=%-8s %s\n", $1, $2, substr($0, index($0,$3))}'

    # 高亮 PPID=1 的孤儿
    ORPHAN_ONLY=$(echo "$ORPHAN_PIDS" | awk '$2 == 1 {print $1}')
    if [[ -n "$ORPHAN_ONLY" ]]; then
        echo ""
        echo -e "${RED}  其中 PPID=1 的孤儿进程 (必须清理):${NC}"
        echo "$ORPHAN_PIDS" | awk '$2 == 1 {printf "    PID=%-8s %s\n", $1, substr($0, index($0,$3))}'
    fi
fi

# ── 2. 查找共享内存残留 ──
echo ""
echo -e "${YELLOW}[2/3] 查找 /dev/shm 中的 DDS 共享内存残留...${NC}"

SHM_FILES=$(ls /dev/shm/ 2>/dev/null | grep -iE 'cyclonedds|dds|fastrtps|iceoryx|iox' || true)

if [[ -z "$SHM_FILES" ]]; then
    echo -e "${GREEN}  没有发现共享内存残留 ✓${NC}"
else
    echo -e "${RED}  发现残留文件:${NC}"
    echo "$SHM_FILES" | sed 's/^/    /'
fi

# ── 3. 清理 ──
echo ""
echo -e "${YELLOW}[3/3] 执行清理...${NC}"

if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}  --dry 模式，跳过清理${NC}"
    echo ""
    echo "提示: 去掉 --dry 参数即可执行实际清理"
    exit 0
fi

# 杀进程
if [[ -n "$ORPHAN_PIDS" ]]; then
    KILL_PIDS=$(echo "$ORPHAN_PIDS" | awk '{print $1}' | tr '\n' ' ')
    echo -n "  正在 kill: $KILL_PIDS ... "
    kill -9 $KILL_PIDS 2>/dev/null || true
    sleep 0.5
    # 确认是否杀干净
    REMAINING=$(ps -p $KILL_PIDS -o pid= 2>/dev/null || true)
    if [[ -z "$REMAINING" ]]; then
        echo -e "${GREEN}完成 ✓${NC}"
    else
        echo -e "${RED}部分进程未能终止: $REMAINING${NC}"
    fi
else
    echo "  无需清理进程"
fi

# 清共享内存
if [[ -n "$SHM_FILES" ]]; then
    echo -n "  正在清理 /dev/shm ... "
    rm -f /dev/shm/*cyclonedds* /dev/shm/*dds* /dev/shm/*fastrtps* /dev/shm/*iceoryx* /dev/shm/*iox* /dev/shm/sem.fastrtps* 2>/dev/null
    echo -e "${GREEN}完成 ✓${NC}"
else
    echo "  无需清理共享内存"
fi

echo ""
echo -e "${GREEN}============================================"
echo "  清理完成！可以安全启动 web_client 了"
echo "============================================${NC}"
