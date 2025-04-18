#!/bin/bash

# 获取脚本所在目录作为默认目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "$1" ]; then
  DIR="$SCRIPT_DIR"
else
  DIR="$1"
fi

for lib_dir in `find "$DIR" -type d -name "lib"`
do
  absolute_path=$(realpath "$lib_dir")
  export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$absolute_path"
done

echo "updated LD_LIBRARY_PATH: $LD_LIBRARY_PATH"

for bin_dir in `find "$DIR" -type d -name "bin"`
do
  absolute_path=$(realpath "$bin_dir")
  export PATH="$absolute_path:$PATH"
done

echo "updated PATH: $PATH"

# 获取本地 IP 地址 - 优先使用 ip 命令，如果不存在则尝试使用 ifconfig
if command -v ip &> /dev/null; then
    local_ip=$(ip -o -4 addr list | grep '10.42.0.' | awk '{print $4}' | cut -d/ -f1)
elif command -v ifconfig &> /dev/null; then
    local_ip=$(ifconfig | grep 'inet ' | awk '{print $2}' | grep '^10\.42\.0\.' | head -n 1)
else
    echo "警告: 未找到 ip 或 ifconfig 命令，无法获取网络地址"
    local_ip=""
fi

# 检查是否获取到 IP 地址
if [ -z "$local_ip" ]; then
    echo "no ip in 10.42.0.* found, can not communicate with robot"
    return 1
else
    export LOCATOR_IP=${local_ip}
    export AORTA_DISCOVERY_URI=http://10.42.0.101:2379
fi
