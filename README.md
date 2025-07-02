# VLA大模型推理框架
* 开发者： 赵永生、赵磊、文宣章
* 使用者： 赵永生、赵磊、文宣章、高晗。。。

## 1. 框架概述
xxxx

## 2. 框架使用

### 2.1 Config
框架所有配置项在conf/config.py中定义，具体请看源码。

### 2.2 Client
客户端主要负责从机器人获取观测数据和机器人本体状态数据，将数据发送给服务端，并接收服务端返回的推理结果，将结果发送给机器人。
* 设置A2D环境
```
cd a2d_sdk
source env.zsh
python robot_service.py -s -c ./conf/hybrid_deploy_depth53.pbtxt
cd ..
```

* 运行客户端
需要先配置lerobot环境
* 设置lerobot环境
```
conda activate lerobot
```

```
python run_client.py
```

### 2.3 Server
* 设置gr00t环境
```
conda activate gr00t
```
* 运行客户端
```
python run_server.py
```