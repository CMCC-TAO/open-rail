# 快速开始（中文版）

[English Version](getting-started.md) | **中文版**

> 📌 本文档用于**完整的环境配置和功能接入**。  
> 如果只想先确认 Web 服务是否能访问，可以**只执行第二步**；此时不需要启动 Server，但客户端业务状态、机器人状态和推理结果可能不可用。  
> 如需 30 秒极速体验，请返回 [README 快速开始](../README.md#快速开始)。

---

## 前置条件

- **操作系统**：Linux/macOS 为主要适配环境；Windows 可运行 Python 服务，但机器人 SDK、ROS 和端口管理需要单独验证。
- **Python**：3.10 或更高版本
- **Git**：用于获取代码
- **模型权重**：运行推理时必须准备自己的 checkpoint
- **GPU**：由所选模型决定
- **真实机器人（可选）**：如需部署到物理本体，需准备厂商提供的 SDK、驱动程序及对应网络环境（网线/串口/Wi-Fi 等）

### 环境建议（二选一）

- **方案 A（推荐）**：准备两个独立的 Conda 环境，避免依赖冲突。
  - `vla-rail-client`：安装本仓库依赖，运行 Web 客户端和机器人适配器。
  - `vla-rail-server`：安装模型专属依赖（如 PyTorch、Transformers 等）。
- **方案 B（快速验证）**：使用同一个 Conda 环境，适合初期快速测试。

## 🛠️ 第一步：安装与环境配置

### 1. 获取代码

```bash
git clone <仓库地址>
cd open-rail
```

如果代码已经位于本地，直接进入项目根目录即可。以下命令都应在包含 `pyproject.toml` 的目录执行。

### 2. 创建 Python 环境并安装项目

Linux/macOS：

```bash
conda create -n vla-rail-client python=3.10 -y
conda activate vla-rail-client
python -m pip install --upgrade pip
python -m pip install -e .
```

Windows PowerShell：

```powershell
conda create -n vla-rail-client python=3.10 -y
conda activate vla-rail-client
python -m pip install --upgrade pip
python -m pip install -e .
```

如需使用兼容依赖列表，可以执行：

```bash
python -m pip install -r requirements.txt
```

## 🌐 第二步：启动 Web 客户端（可独立运行）
**此步骤不需要 Server 和模型，用于确认管理界面是否正常。**
在终端执行：

```bash
python run_web_client.py
```

不带参数时，程序默认读取 `conf/default_conf.yaml`，并监听 `0.0.0.0:9000`。如果使用自定义配置文件，文件名通过 `--conf` 传入，并放在 `conf/` 目录下：

```bash
python run_web_client.py --conf custom_conf.yaml
```

打开浏览器访问 `http://localhost:9000`，预期看到 VLA-RAIL Web 控制台、客户端状态和配置面板；在 Server 尚未连接或机器人未正确配置时，推理结果和机器人状态可能为空。

> **端口说明**：
> - `9000`：主 Web 服务端口（由 `uvicorn` 提供 REST API 和 WebSocket）。
> - `8080` / `8765`：由 `VLAClient.run()` 自动启动的**可视化附属服务**（静态资源 + 数据推送），无需手动干预。
> - Linux/macOS 下，`run_web_client.py` 会尝试自动释放被占用的主 Web 端口；Windows 下请手动关闭占用进程或改用其他端口。


## 🧪 第三步：启动 Server 并接入模型

Server 负责模型推理，不负责读取机器人或下发机器人动作。建议在另一个终端、模型专属环境中执行：

Linux/macOS：

```bash
PYTHONPATH=<模型源码目录>:$PYTHONPATH python run_server.py --model_type <模型类型> --model_path <检查点路径>
```

Windows PowerShell：

```powershell
$env:PYTHONPATH = "<模型源码目录>;" + $env:PYTHONPATH
python run_server.py --model_type <模型类型> --model_path <检查点路径>
```

示例： TAO 模型：

```bash
PYTHONPATH=/path/to/TAO/src:$PYTHONPATH python run_server.py --model_type tao --model_path /path/to/checkpoint
```
> **模型类型**：已支持的模型列表参见 `conf/server_conf.py` 中的注册信息。  
> **新增模型**：如需接入新 VLA 模型，参见 [新增 VLA 模型指南](guides/add-new-vla-model.zh-CN.md)。

## 🎬 第四步：Mock 机器人（可选，用于无真机场景）

> 如果你有真实机器人，**直接跳到第五步**。

Mock 机器人会从 LeRobot 格式的数据集中回放历史观测，适合演示和离线调试。

**数据格式要求**：
```text
<dataset_root>/
├── data/chunk-*/episode_*.parquet
├── videos/chunk-*/<video_key>/episode_*.mp4
└── meta/info.json          # 可选，用于读取 fps
```

**操作步骤**：
1. 在 `conf/default_conf.yaml` 的 `robots.mock` 中填写 `dataset_path`。
2. 确保相机名称与视频目录名一致。
3. 在 Web 控制台的配置面板中选择 **Mock 机器人**。
4. 启动客户端任务，即可看到观测回放和随机动作响应。

详细配置参见 [Mock Robot 说明](../client/robots/mock/README.md)。

---


## 🔧 第五步：配置真实机器人

**真实机器人逻辑由 Client 侧的适配器负责，Server 只做推理，不调用 SDK。**

### 使用已适配机器人

如果你的机器人型号已在项目支持列表中，**无需编写任何代码**，只需在 Web 控制台的配置面板中选择对应机器人类型，并填写通信参数（IP、端口、串口号等）即可。

> 已适配的机器人列表参见 `conf/robots_conf.py` 中的注册信息。

### 新增机器人适配器

如果项目尚未支持你的机器人型号，请按以下步骤新增适配器：

1. 在 `client/robots/` 下新增目录和实现文件。
2. 继承 `client/robots/base_robot.py` 中的 `RobotBase` 类。
3. 实现 `retrieve_observation()` 和 `execute_action()` 方法。
4. 在 `conf/robots_conf.py` 中注册机器人类型和参数。
5. 在 Client 环境安装厂商 SDK，先脱离模型单独验证观测/动作接口。
6. 再连接 Server，确认推理结果与动作执行流程正常。

完整接口规范参见 [机器人适配指南](guides/add-new-robot.zh-CN.md)。

## 下一步

- [项目架构](../README.zh-CN.md#项目架构)：理解 Client、Server 和 ZMQ 通信层的职责边界。
- [配置说明](configuration.zh-CN.md)：查看客户端、Server、机器人和记录配置。
- [新增 VLA 模型指南](guides/add-new-vla-model.zh-CN.md)：接入新的 checkpoint/模型实现。
- [机器人适配指南](guides/add-new-robot.zh-CN.md)：接入真实机器人。
- [故障排查](troubleshooting.zh-CN.md)：查看运行期间的常见问题。
- [Mock Robot 说明](../client/robots/mock/README.md)：配置离线数据集回放。