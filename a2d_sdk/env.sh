#!/bin/bash

# usage: source env.sh [ros_domain_id]

# if [ -z "$1" ]; then
#     export ROS_DOMAIN_ID=88
# else
#     export ROS_DOMAIN_ID=$1
# fi

#CURRENT_SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
CURRENT_SCRIPT_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
LOG_DIR="$CURRENT_SCRIPT_DIR/log"
mkdir -p $LOG_DIR

# 获取本地 IP 地址
local_ip=$(ip -o -4 addr list | grep '10.42.0.' | awk '{print $4}' | cut -d/ -f1)

# 检查是否获取到 IP 地址
if [ -z "$local_ip" ]; then
    echo "no ip in 10.42.0.* found, can not communicate with robot"
else
    export LOCATOR_IP=${local_ip}
    export AORTA_DISCOVERY_URI=http://10.42.0.101:2379
fi

export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
export DYLOG_log_dir=$LOG_DIR
export DYLOG_LOG_SIZE=20000
export DYLOG_DEFAULT_LEVEL=FATAL

# 存在ros2则source
if [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
    export ROS_VERSION=2
    export ROS_PYTHON_VERSION=3
    export ROS_DOMAIN_ID=0
    export ROS_LOCALHOST_ONLY=1
    export ROS_DISTRO=humble
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    ros2 daemon stop
    ros2 daemon start

    # 检查是否存在forwarder/app/bin/forwarder
    if [ -f "${CURRENT_SCRIPT_DIR}/forwarder/app/bin/forwarder" ]; then
        source ${CURRENT_SCRIPT_DIR}/forwarder/app/share/genie_msgs/local_setup.bash
        ln -s /opt/ros/humble/opt ${CURRENT_SCRIPT_DIR}/forwarder/app/opt
    fi
fi