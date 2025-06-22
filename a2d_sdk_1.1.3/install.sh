#!/bin/bash
set -e

cosine_bus=cosine_bus-1.4.0-cp310-cp310-linux_x86_64.whl
genie_msgs_pb=genie_msgs_pb-0.2.0-py3-none-any.whl
forward_package=forwarder_x86_v1.1.3.tar.gz
SDK_PACK_DIR="/home/agi/app/a2d_sdk/pack/a2d_sdk_server.tar.gz"
CURRENT_SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
CURRENT_SDK_PATH=$CURRENT_SCRIPT_DIR/a2d_sdk

# 安装sshpass
function install_sshpass() {
    # 检查是否已安装sshpass
    if ! command -v sshpass &> /dev/null; then
        sudo apt update
        sudo apt-get install sshpass -y
    else
        echo "sshpass 已安装"
    fi
}

# 将a2d上的package拷贝到本地并解压缩
function copy_sdk_package() {
    install_sshpass
    sshpass -p 1 scp -o StrictHostKeyChecking=no agi@10.42.0.101:$SDK_PACK_DIR ./
    tar -zxvf a2d_sdk_server.tar.gz
    rm a2d_sdk_server.tar.gz
}

function install_sdk_package() {
    pip install $CURRENT_SDK_PATH/$cosine_bus --force-reinstall

    # 安装genie_msgs_pb
    pip install $CURRENT_SDK_PATH/$genie_msgs_pb --force-reinstall --no-deps

    # 安装a2d_sdk
    a2d_sdk_whl=$(ls -t $CURRENT_SDK_PATH/a2d_sdk-*.whl | head -n 1)
    pip3 install $a2d_sdk_whl --force-reinstall

    # 安装forward_package
    mkdir -p $CURRENT_SDK_PATH/forwarder
    tar -zxvf $CURRENT_SDK_PATH/$forward_package -C $CURRENT_SDK_PATH/forwarder
    
    rm $a2d_sdk_whl
    rm $CURRENT_SDK_PATH/$genie_msgs_pb
    rm $CURRENT_SDK_PATH/$cosine_bus
    rm $CURRENT_SDK_PATH/$forward_package
}

function modify_bashrc() {
    read -p "是否要修改 bashrc 来source env.sh? (y/n): " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
    # 检查是否存在 .bashrc 文件
        if [ -f "$HOME/.bashrc" ]; then
            # 备份原文件
            if [ ! -f "$HOME/.bashrc.backup" ]; then
                cp "$HOME/.bashrc" "$HOME/.bashrc.backup"
            fi
            
            # 检查是否存在环境变量
            if ! grep -q "source $CURRENT_SDK_PATH/env.sh" "$HOME/.bashrc"; then
                echo "source $CURRENT_SDK_PATH/env.sh" >> "$HOME/.bashrc"
            fi
            
            echo "bashrc 已修改,原文件已备份为 .bashrc.backup"
        else
            echo "未找到 .bashrc 文件"
        fi
    else
        echo "未进行任何修改"
    fi
}

function check_old_msgs() {
    CHECK_DIR=/usr/local/genie/
    if [ -d "$CHECK_DIR" ]; then
        echo "检查到历史版本遗留文件，需要删除"
        rm -rf $CHECK_DIR
    fi
}

function install_a2d_sdk_server() {
    if [ -d "$CURRENT_SDK_PATH" ]; then
        read -p "是否要删除现有的a2d_sdk, 或者将其备份? (y/n): " answer
        if [[ "$answer" =~ ^[Yy]$ ]]; then
            rm -rf $CURRENT_SDK_PATH
        else
            mv $CURRENT_SDK_PATH $CURRENT_SDK_PATH.backup
        fi
    fi
    mkdir -p $CURRENT_SDK_PATH
    copy_sdk_package
    install_sdk_package
    modify_bashrc
    check_old_msgs
}

install_a2d_sdk_server
echo "安装完成"
