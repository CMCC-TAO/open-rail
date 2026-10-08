#!/usr/bin/env bash
set -u

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
restart_interval="${SERVER_RESTART_INTERVAL:-10}"
child_pid=""
stopping=0

stop_server() {
    stopping=1
    if [[ -n "$child_pid" ]]; then
        kill -TERM "$child_pid" 2>/dev/null || true
    fi
}

trap stop_server INT TERM
cd "$project_root"

server_command=(
    python run_server.py
    --model_path /data/users/huangkai/checkpoints/KEEP/Robocasa/20260623_pretrainbase_model_20260624_090504_n8_b64_s120000/checkpoint-120000
    --model_type tao
    --embodiment_tag robocasa_panda_omron
    --action_keys end_effector_position end_effector_rotation gripper_close base_motion control_mode
)

while (( ! stopping )); do
    "${server_command[@]}" &
    child_pid=$!
    wait "$child_pid"
    exit_code=$?
    child_pid=""
    if (( stopping )); then
        break
    fi
    printf 'VLA server exited with code %d; restarting in %ss\n' \
        "$exit_code" "$restart_interval" >&2
    sleep "$restart_interval" &
    child_pid=$!
    wait "$child_pid" || true
    child_pid=""
done
