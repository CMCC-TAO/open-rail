#!/bin/bash

action=$1
if [ -z "$action" ]; then
    echo "Usage: $0 <start|stop>"
    exit 1
fi

if [ "$action" == "stop" ]; then
    pkill -9 forwarder
    exit 0
fi

# 检查是否已经启动了forwarder
if [ "$action" == "start" ]; then
    if pgrep -f "forwarder" > /dev/null; then
        echo "forwarder is already running"
        exit 0
    fi
fi

# 检查是否存在ros环境，不存在就退出
if [ ! -f "/opt/ros/humble/setup.sh" ]; then
    echo "NOT in ros environment"
    exit 1
fi

# 脚本当前路径
current_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -d "$current_dir/../forwarder" ]]; then
    echo "forwarder not found"
    exit 1
fi

export CB_PROC_THREADS_NUM=5
export AORTA_DISPATCHER_THREAD_NUM=5
export DYLOG_ASYNC_INTERVAL=5000
export DYLOG_log_dir=$current_dir/../forwarder/
export DYLOG_LOG_SIZE=20000

source $current_dir/../forwarder/app/env.sh $current_dir/../forwarder/app
# source $current_dir/../forwarder/app/share/genie_msgs/local_setup.bash
source $current_dir/../env.sh
$current_dir/../forwarder/app/bin/forwarder