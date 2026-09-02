# 常见问题

[English Version](troubleshooting.md)

# 常见问题

[English Version](troubleshooting.md)

## Web 客户端

### Web 客户端无法启动

- 确认当前终端位于包含 `pyproject.toml` 的项目根目录。
- 确认已激活正确的 Python/Conda 环境，并执行过 `python -m pip install -e .`。
- 默认启动命令为：

	```bash
	python run_web_client.py
	```

- 默认配置文件是 `conf/default_conf.yaml`。自定义配置应放在 `conf/` 下，并使用 `--conf custom_conf.yaml` 指定。

### 端口被占用或浏览器无法连接

- 默认 Web 端口是 `9000`，可使用 `--port 9001` 换端口。
- Linux/macOS 下启动脚本会尝试释放主 Web 端口；Windows 下请在任务管理器中关闭占用进程，或直接改用其他端口。
- 远程访问时使用 `--host 0.0.0.0`，并检查系统防火墙和网络连通性。
- `8080` 和 `8765` 是可视化附属服务使用的端口；连接失败时也要检查它们是否被占用。

## Server 与模型

### 页面打开但 Server 状态为空

Client 和 Server 是两个独立进程。检查：

- Server 是否已经启动，且没有模型依赖或 checkpoint 加载异常。
- Client 与 Server 的 ZMQ 地址和端口是否一致。
- Server 的 `--model_type` 是否是 `run_server.py` 支持的类型。
- 跨机器运行时，Server 端口是否可以从 Client 访问。

### 模型加载失败

- 确认 `--model_path` 指向正确的 checkpoint 目录。
- 确认在 Server 所用环境中安装了对应模型的依赖；GR00T、RDT、OpenPI、TAO 等模型可能需要额外源码和 CUDA/PyTorch 环境。
- `--model_type mock` 不加载真实 checkpoint，只生成随机动作，只能验证服务和通信链路，不能用于验证模型效果。

## Mock 机器人与数据集

### Mock 回放提示找不到 Parquet 或视频

- `robots.mock.dataset_path` 必须指向数据集根目录，而不是 `data/` 子目录或某个 episode 文件。
- 确认存在 `data/chunk-*/episode_*.parquet`。
- 确认每个配置相机都有对应的视频：`videos/chunk-*/<video_key>/episode_*.mp4`。
- 视频目录名必须匹配 `conf/robots_conf.py` 中 `robots.mock.camera.names` 的值。
- Parquet 和视频必须使用相同的 chunk 编号与 episode 编号。

### Mock 机器人启动后没有观测

- 检查 Parquet 是否能被 `pandas.read_parquet()` 读取，并确认已安装 `pyarrow`。
- 检查视频是否能被 OpenCV 打开，编码格式和文件是否完整。
- `meta/info.json` 不是必需文件；缺少它时回放帧率默认使用 30 FPS。
- Mock 机器人的 `execute_action()` 不会驱动物理设备，返回动作只用于验证控制链路。

## 机器人适配

### 真实机器人控制不可用

- 先用 Mock 数据集验证 Client、Server 和通信链路，再检查厂商 SDK、ROS 话题/节点、相机流和机器人网络。
- 确认机器人类型、相机配置和 `action_layout` 已在 `conf/robots_conf.py` 中正确注册。
- 机器人适配器应实现 `retrieve_observation()` 和 `execute_action()`；不要在 Server 中直接调用机器人 SDK。