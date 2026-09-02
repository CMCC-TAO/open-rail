# 贡献指南

感谢你为 OPEN-RAIL 贡献代码、模型适配器、机器人适配器、平滑策略、测试或文档。

## 开始之前

请先阅读：

- [项目中文 README](README.zh-CN.md)
- [中文架构说明](docs/architecture.zh-CN.md)
- [中文配置说明](docs/configuration.zh-CN.md)
- [机器人接入指南](docs/guides/add-new-robot.zh-CN.md)
- [VLA 模型接入指南](docs/guides/add-new-vla-model.zh-CN.md)

涉及新增机器人或模型适配器时，建议先提交 issue，说明使用场景、依赖、输入输出契约和验证方式。

## 开发环境

项目要求 Python 3.10 或更高版本。建议使用独立的 Conda 或虚拟环境：

```bash
conda create -n open-rail-dev python=3.10 -y
conda activate open-rail-dev
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

`pyproject.toml` 是依赖和命令行入口的权威来源。模型专属依赖应安装在服务端模型环境中，机器人 SDK 或 ROS 依赖应安装在客户端环境中，避免把两类环境强行绑定。

## 分支与提交

- 从最新主分支创建主题分支，不要直接在主分支上开发。
- 每个提交只解决一个明确问题，避免混入无关格式化或生成文件。
- 提交信息应简洁说明变更目的，例如 `docs: update architecture guide` 或 `feat: add robot adapter`。
- 不要提交模型 checkpoint、原始录制视频、运行日志、缓存目录或本地配置密钥。
- 提交前检查 `git diff`，确认没有包含个人路径、设备地址、访问令牌或其他敏感信息。

## 模块边界

请保持以下依赖方向：

```text
Robot adapter -> Client control loop -> message contract -> Server inference -> model adapter
```

- 机器人硬件和 SDK 调用放在 `client/robots/`。
- 观测采集、本地状态、动作调度、平滑和指令下发放在 Client 侧。
- 模型加载和 `infer()` 实现放在 `server/models/`。
- `server/core/vla_server.py` 负责推理流程，不调用机器人 SDK 或执行机器人动作。
- `client/core/zmq_client.py` 和 `server/core/zmq_server.py` 只负责传输、路由、心跳和请求关联，不承载业务策略。
- 数据记录、评测和可视化通过独立接口或队列接入，不应阻塞实时推理和控制链路。

新增模块时，请优先复用现有配置、适配器和队列接口，不要在多个边界之间复制同一份业务逻辑。

## 新增机器人适配器

在 `client/robots/` 下创建机器人目录，继承 `RobotBase`，至少实现：

- `retrieve_observation()`：返回相机、本体状态和必要的时间戳。
- `execute_action()`：接收客户端动作并转换为机器人指令。

同时完成以下内容：

- 在 `conf/robots_conf.py` 注册机器人类型和配置。
- 明确相机名称、动作维度和 `action_layout`。
- 将厂商 SDK、ROS 话题和设备通信代码限制在机器人适配器内。
- 在没有模型服务端时先验证观测读取和动作转换。
- 说明真实硬件、SDK、ROS 版本和安全前提。

详细接口要求见 [机器人接入指南](docs/guides/add-new-robot.zh-CN.md)。

## 新增 VLA 模型适配器

在 `server/models/` 下创建模型目录并实现 `ModelVLA`，提供初始化和 `infer(sequence)` 接口：

- 从输入序列读取观测和元数据。
- 将相机、状态和语言输入转换为模型需要的格式。
- 返回符合现有客户端协议的 `pred_action` 和必要元数据。
- 在 `run_server.py:get_model()` 和 `conf/models_conf.py` 注册模型类型。
- 在模型环境中记录 checkpoint、外部源码和专属依赖要求。

模型代码不应直接操作 ZMQ socket、机器人 SDK 或 Client API。详细格式见 [VLA 模型接入指南](docs/guides/add-new-vla-model.zh-CN.md)。

## 测试与检查

当前仓库没有独立的自动化测试文件，也没有统一的 lint 或 format 配置。提交前至少完成与改动范围匹配的检查：

```bash
python -m pytest
python -m compileall client server conf web_client
```

如果只修改文档，可检查 Markdown 代码围栏、相对链接和 `git diff --check`：

```bash
git diff --check
```

涉及模型、机器人或通信层时，还应记录：

- 使用的 Python 环境和关键依赖版本。
- 是否需要 GPU、CUDA、ROS 或厂商 SDK。
- 使用的模型 checkpoint、数据集或模拟输入。
- 启动命令、预期结果和实际验证结果。

不要把大型 checkpoint、原始视频或本地数据集提交到仓库；请在说明中记录获取方式或使用约束。

## 文档要求

- 中文文档链接中文版本，英文文档链接英文版本。
- 新增命令必须与实际入口参数一致，不要使用不存在的参数或路径。
- 说明默认值、配置文件位置和运行环境，尤其是跨平台差异。
- 代码行为尚未实测时，使用“需要验证”或“以具体模型/硬件为准”，不要把推测写成保证。
- 更新目录结构、入口命令或配置字段时，同步检查 README 和 `docs/` 中的相关说明。

## Pull Request 清单

提交 Pull Request 前，请确认：

- [ ] 变更范围和动机已说明。
- [ ] 新增或修改的模块遵守 Client、Server 和通信层边界。
- [ ] 已运行与改动相关的测试或检查，并记录未能运行的项目。
- [ ] 没有提交 checkpoint、录制数据、日志、个人配置或敏感信息。
- [ ] 相关中文/英文文档和链接已同步。
- [ ] 涉及机器人控制时，已说明硬件安全验证范围。

## 许可证

本项目使用 Apache License 2.0。提交代码和文档即表示你有权按该许可证贡献相应内容，并同意其按项目许可证发布。
