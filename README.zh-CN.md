<div align="center">


# OPEN-RAIL

**一套异步连接 VLA 模型推理与机器人执行的通用底座**

[![Paper](https://img.shields.io/badge/论文-arXiv-2512.24673-red)](https://arxiv.org/abs/2512.24673)
[![License](https://img.shields.io/badge/许可证-Apache--2.0-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](pyproject.toml)

<!-- TODO:暂不添加 Stars/Issues 动态徽章：当前 README 未绑定公开仓库地址。 -->

[English](README.md) | [中文](README.zh-CN.md)

</div>

<video controls width="100%" preload="metadata">
  <source src="data/media/%E5%AE%A3%E4%BC%A0%E8%A7%86%E9%A2%91%EF%BC%88%E4%B8%AD%E6%96%87%E7%89%88%EF%BC%89.mp4" type="video/mp4">
  <a href="data/media/%E5%AE%A3%E4%BC%A0%E8%A7%86%E9%A2%91%EF%BC%88%E4%B8%AD%E6%96%87%E7%89%88%EF%BC%89.mp4">播放 OPEN-RAIL 中文宣传视频</a>
</video>

VLA 模型越来越多，真机已是当下具身智能的版本答案。但没有解决的是模型 checkpoint 与机器人之间的那段工程链路——动作卡顿抖动、长时运行断流、执行数据回不到模型迭代。

**OPEN-RAIL 就是这段链路**：一套轻量级服务端-客户端框架，把任意 VLA 模型接到任意已适配机器人上，并把「**推**（真机推理执行）→ **采**（运行即采集）→ **评**（数据驱动迭代）」的闭环端到端接进每一次运行。

目前已适配 **3 款异构机器人**（另含 LeRobot 仿真后端）、支持 **10 个主流 VLA 模型**（7 个系列），关节加速度标准差 **10+ → 0.1 rad/s²**。

- 🤖 **VLA 研究者** — 开箱即用的真机部署环境，专注模型创新，不搭工程管线
- 🔧 **机器人工程师** — 快速验证算法的工具集，无需重复实现驱动与管线
- 🎓 **初创团队与高校实验室** — 降低真机实验启动成本，缩短从仿真到实物的周期
---
<details>
<summary><b>目录</b></summary>

- [✨ 功能特性](#-功能特性)
- [🚀 快速开始](#-快速开始)
- [🎛️ 使用方式](#️-使用方式)
- [🤖 支持的机器人与模型](#-支持的机器人与模型)
- [🏗️ 系统架构](#️-系统架构)
- [📊 数据采集](#-数据采集)
- [📚 文档](#-文档)
- [🗺️ 路线图](#️-路线图)
- [🤝 参与贡献](#-参与贡献)
- [📖 引用](#-引用)
- [⚖️ 许可证](#️-许可证)

</details>
---

## ✨ 功能特性

| 痛点 | OPEN-RAIL 做法 | 效果 |
| --- | --- | --- |
| ⚡ 推理跟不上控制周期，动作又卡又抖 | 三线程异步流水（观测 / 推理 / 控制）+ 块内/块间两级在线平滑 | 关节加速度标准差 **10+ → 0.1 rad/s²**；**30–50 倍**频率差消除 |
| ☁️ 机器人端算力跑不动大模型 | 服务端-客户端分离，两侧依赖树互不干涉 | 嵌入式设备也能驱动大模型；端 / 边 / 云**代码零改动**切换 |
| 🔌 换一台机器人就要重做接口 | 轻量硬件抽象层 `RobotBase` + 统一 `action_layout` 索引 | 已适配 **3 款异构机器人**；新机器人接入**从周级降到小时级** |
| 🧩 每接一个新模型都要重写工程管线 | 统一模型接入约定 + 服务端自动路由 | 已支持 **10 个模型**；新模型接入 **≤ 100 行** |
| 📊 推理与数采割裂，数据进不了训练管线 | 采集内置于每次推理，LeRobot 风格 Parquet，episode 可追加 | 每次运行产出可用训练数据，**零额外成本** |
| 🎮 模型推理跑偏，没法及时纠正 | 三模式（纯推理 / 纯遥操 / 混合）+ 暂停-介入-恢复与状态预对齐 | 每次人工纠偏即**高质量教学样本**，无需后处理 |

平滑在**框架层**完成，不改动模型、不要求训练增强，扩散、流匹配、自回归架构通吃

## 🚀 快速开始

### 1. 环境要求

- **Python ≥ 3.10**
- **服务端**：按所选模型配备对应的 NVIDIA GPU、CUDA、PyTorch 和模型专属依赖。仓库没有统一的最低显存或 CUDA 版本；请以具体模型目录 README 和模型官方要求为准
- **客户端**：随机器人而定——A2D 需厂商 SDK，Ti5 T170C 需 ROS 2，Navi WA2 需 ROS 1；使用 Mock 仿真后端则无额外硬件门槛
- **网络**：两侧通过 ZMQ 通信，同一局域网或互相可达即可
- **操作系统**：Linux 是当前主要运行环境

### 2. 安装

```bash
git clone <仓库地址>
cd OPEN-RAIL
conda create -y -n open-rail python=3.10 && conda activate open-rail
pip install -e .
```

兼容旧工作流时也可用 `pip install -r requirements.txt`。`pyproject.toml` 是运行时依赖与命令行脚本的权威来源，两者冲突时以它为准。

### 3. 启动服务端

服务端承载 VLA 模型运行时，通过 ZMQ 暴露推理端点。

```bash
PYTHONPATH=<项目源码目录>:$PYTHONPATH python run_server.py \
  --model_type <模型类型> --model_path <权重路径>
```

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--model_type` | 已注册的模型适配器，如 `tao` | — |
| `--model_path` | 模型 checkpoint 目录 | — |

<details>
<summary><b>完整示例</b></summary>

```bash
PYTHONPATH=/path/to/open-rail:$PYTHONPATH \
  python run_server.py --model_type tao \
  --model_path /path/to/checkpoints/tao_v0/checkpoint-30000
```

</details>

### 4. 启动 Web 客户端

```bash
python run_web_client.py
```

默认使用 `conf/default_conf.yaml`，默认监听 `0.0.0.0:9000`。如需指定自定义配置文件，文件名必须作为 `--conf` 参数的值，并放在 `conf/` 目录下：

```bash
python run_web_client.py --conf custom_conf.yaml
```

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--host` | 监听地址 | `0.0.0.0` |
| `--port` | HTTP / UI 端口 | `9000` |
| `--conf` | `conf/` 下的配置文件 | `default_conf.yaml` |


### 5. 验证

浏览器打开 http://localhost:9000，看到 Web 界面与相机画面、机器人状态就绪，即启动成功；选择任务后即可驱动机器人。

## 🎛️ 使用方式

配置入口速查：

| 文件 | 作用 |
| --- | --- |
| `conf/*.yaml` | 主配置：`robots.type` 选择机器人适配器，相机话题、`action_layout` 与本体感知参数 |
| `conf/robots_conf.py` | 机器人硬件参数；Mock 后端在此设置 `dataset_path` |
| 服务端网络地址 | 端 / 边 / 云切换只需修改此项，字段名见 [docs/configuration.md](docs/configuration.md) |

### 仿真闭环（无真机起步）

不需要真实机器人硬件时，可以用 Mock 后端回放已有的 LeRobot 数据集。但它不是零配置流程：需要在 `conf/robots_conf.py` 的 Mock 配置中设置 `dataset_path`，并准备对应的 Parquet episode 与相机视频。服务端可以使用 `--model_type mock` 生成随机动作验证服务链路，但要验证真实模型效果，仍必须提供自己的 checkpoint 和模型专属环境。

Mock 数据集的最小目录结构如下：

```text
<dataset>/
├── data/chunk-000/episode_000000.parquet
├── videos/chunk-000/observation.images.head_rgb/episode_000000.mp4
├── videos/chunk-000/observation.images.left_wrist_rgb/episode_000000.mp4
├── videos/chunk-000/observation.images.right_wrist_rgb/episode_000000.mp4
└── meta/info.json                       # 可选，用于读取 fps
```

Mock 模型只返回随机动作，不能替代真实模型评测。

### 真机执行

修改 `conf/*.yaml` 中的 `robots.type` 为目标机器人适配器（`a2d` / `ti5_t170c` / `navi_wa2`），并按 [docs/configuration.md](docs/configuration.md) 配置相机话题、`action_layout` 与本体感知参数，随后同样是两条命令启动。

### 混合模式：推理 + 实时遥操纠偏

在客户端中切换三种运行模式——纯推理 / 纯遥操 / 混合。混合模式下可随时**暂停 → 介入纠偏 → 恢复**，状态预对齐保证接管瞬间无跳变；纠偏轨迹与推理轨迹按时间戳对齐、并行保存，每一段人工纠偏都是可直接进训练管线的教学样本。

![数据沉淀与遥操接入示意](data/media/data-teleop.png)

## 🤖 支持的机器人与模型

### 机器人

| 机器人 | 类型 | 状态 | 适配器 |
| --- | --- | --- | --- |
| A2D | 双臂人形（头 + 腰 + 轮式底盘） | ✅ 已适配 | `client/robots/a2d/` |
| Ti5 T170C | 双臂轮式机器人（ROS 2） | ✅ 已适配 | `client/robots/ti5_t170c/` |
| Navi WA2（浙江人形） | 折叠轮臂人形（ROS 1） | ✅ 已适配 | `client/robots/navi_wa2/` |
| Mock | 基于 LeRobot 的仿真后端 | ✅ 已适配 | `client/robots/mock/` |
| _你的机器人_ | — | 🔜 计划中 | [接入指南](docs/guides/add-new-robot.zh-CN.md) |

### 模型

| 模型系列 | 成员 | 状态 |
| --- | --- | --- |
| ACT | ACT | ✅ 已支持 |
| GR00T N1 系列 | GR00T N1、N1.5、N1.6 | ✅ 已支持 |
| RDT | RDT-1B | ✅ 已支持 |
| SmolVLA | SmolVLA | ✅ 已支持 |
| GO1 | 智元 GO-1 | ✅ 已支持 |
| π 系列 | Pi0、Pi0.5 | ✅ 已支持 |
| TAO | TAO | ✅ 已支持 |
| _你的模型_ | — | 🔜 [接入指南](docs/guides/add-new-vla-model.zh-CN.md) |

## 🏗️ 系统架构

![OPEN-RAIL 架构图](data/media/architecture.png)

OPEN-RAIL 采用 **服务端-客户端分布式架构**，推理主链路与可视化链路独立解耦、互不干扰。**服务端**负责模型推理；**客户端**部署于机器人侧，负责状态采集、任务执行、指令下发和数据记录，将机器人配置与模型推理整合为统一工作流。

正因为服务端独占模型环境、客户端独占机器人环境，两侧依赖树互不干涉——模型需要的 CUDA / PyTorch 版本和机器人驱动需要的 ROS 版本不会互相冲突。这也是端 / 边 / 云「代码零改动切换」的前提：换部署位置只需修改服务端网络地址。


```text
.
├── client/                 # 客户端运行时、机器人适配器、数据记录和工具
│   ├── core/               # 观测、推理、控制、通信、可视化和数据记录
│   ├── robots/             # RobotBase 及各机器人/仿真适配器
│   └── utils/              # 客户端通用工具和可视化工具
├── server/                 # 模型运行时和推理服务
│   ├── core/               # VLAServer、ZMQServer 和可视化服务
│   ├── models/             # VLA 模型适配器与模型专属实现
│   └── utils/              # 服务端通用工具
├── conf/                   # 客户端、服务端、机器人和记录配置
├── web_client/             # Web UI、HTTP API 和 WebSocket 服务
├── visual/                 # 独立可视化资源与数据推送服务
├── extra/                  # 额外的调度和通信辅助模块
├── scripts/                # CUDA、数据展示和评测可视化脚本
├── docs/                   # 快速开始、架构、配置、排障和接入指南
│   └── guides/             # 机器人与 VLA 模型接入指南
├── data/                   # 本地数据、媒体资源和录制输出
│   ├── media/              # 宣传视频、架构图和可视化示意图
│   └── README.md           # 数据目录说明
├── test/                   # 测试/实验
├── run_server.py           # Server 启动入口
├── run_web_client.py       # Web Client 启动入口
├── pyproject.toml          # 包元数据与运行时依赖
├── requirements.txt        # 兼容性依赖清单
├── README.md               # 英文文档
├── README.zh-CN.md         # 中文文档
├── LICENSE                 # Apache License 2.0
└── CITATION.cff            # 引用元数据
```

### 核心机制：异步流水线

异步不是「加个线程」这么简单。VLA 推理与控制之间存在数量级的频率差：模型出一次 action chunk 要几百毫秒，而机器人控制回路跑在几十到几百赫兹。同步方案里控制周期的延迟下界就是模型延迟——这是动作卡顿与抖动的根源。

OPEN-RAIL 用**三条互相解耦的流水线**消除这个差距：

![OPEN-RAIL 三线程异步流水线](data/media/promo-thumb.png)

三条线程各按自己的节奏跑，互不等待：

1. **观测线程**按传感器频率采集相机与本体感知数据，异步上行给服务端，不等推理返回
2. **推理线程**按模型自身节奏产出动作块，一次推理结果被后续多个控制周期复用
3. **控制线程**按控制频率执行：拿已有 chunk 做插值，新 chunk 到达时在线并入，从不空等

频率差被吸收后，残余抖动来自动作分块本身——动作块内部可能不连续，动作块与动作块的接缝会跳变。OPEN-RAIL 用两级在线平滑处理：

- **块内平滑** — 消除单个动作块内部的离散跳变
- **块间平滑** — 消除相邻动作块接缝处的突变

实现细节（平滑算法与窗口、chunk 并入策略、推理超时降级策略、缓冲区结构与容量）见 [docs/architecture.zh-CN.md](docs/architecture.zh-CN.md)。

## 📊 数据采集

「推理即采集」是 OPEN-RAIL 与推理/数采分离方案的分水岭——每一次运行都在产出可直接进训练管线的数据，不需要额外跑一遍采集流程。

- 📡 数据由客户端数据管理器写入，与推理主链路并行，不影响控制频率
- 🗂️ **LeRobot 风格 Parquet**，数据片段支持追加，适配长周期运行与增量训练
- 🎮 人工纠偏产生的片段同样是高质量教学样本，无需后处理

```text
data/
└── recording/<task_name>_<YYYYMMDD>/
  ├── data/chunk-000/episode_000000.parquet
  ├── videos/chunk-000/<video_key>/episode_000000.mp4
  ├── meta/episodes.jsonl
  └── eval/
    ├── eval_log.json
    └── eval_log.csv
```

Parquet 保存观测、状态和动作；视频按相机 key 分目录保存。评测 JSON 保留原始统计数组，CSV 将推理、轨迹和通信耗时聚合为平均值，具体字段见 [docs/vla_rail_learning_notes.md](docs/vla_rail_learning_notes.md)。


## 📚 文档

| 文档                                                         | 说明                         |
| ------------------------------------------------------------ | ---------------------------- |
| 🚀 [docs/getting-started.zh-CN.md](docs/getting-started.zh-CN.md)         | 安装与首次运行               |
| 🏗️ [docs/architecture.zh-CN.md](docs/architecture.zh-CN.md)               | 架构详解与异步流水线实现细节 |
| ⚙️ [docs/configuration.zh-CN.md](docs/configuration.zh-CN.md)             | 完整配置项参考               |
| 🔧 [docs/troubleshooting.zh-CN.md](docs/troubleshooting.zh-CN.md)         | 常见问题与排查               |
| 🤖 [docs/guides/add-new-robot.zh-CN.md](docs/guides/add-new-robot.zh-CN.md)     | 如何新增机器人适配器         |
| 🧠 [docs/guides/add-new-vla-model.zh-CN.md](docs/guides/add-new-vla-model.zh-CN.md) | 如何新增 VLA 模型适配器      |

路线图见 [ROADMAP.md](ROADMAP.md) · [中文](ROADMAP.zh-CN.md)。

## 🗺️ 路线图

- [x] 三线程异步流水 + 两级在线平滑——关节加速度标准差 **10+ → 0.1 rad/s²**
- [x] **3 款异构机器人 + 10 个 VLA 模型**（7 系列）适配，端 / 边 / 云零改动切换
- [x] 推理即采集（LeRobot 风格 Parquet）+ 三模式运行与实时遥操纠偏
- [ ] 🚧 评估工具集——量化每次运行的平滑质量、延迟与数据产出
- [ ] 🚧 容器镜像——服务端与客户端 Docker 预置镜像
- [ ] 🔜 仿真器对接——Isaac Sim / MuJoCo / Genesis 共用同一套适配器接口
- [ ] 🔜 多机器人编排——一个 Server 调度多个 Client
- [ ] 🔜 数据集与基准约定、社区模型适配器注册表

完整路线图（含中长期规划与治理方式）见 [ROADMAP.zh-CN.md](ROADMAP.zh-CN.md)。
<!-- TODO：补充 ROADMAP.md 与 ROADMAP.zh-CN.md 文件，并在功能、模型、机器人和发布计划发生变化时同步更新。 -->

## 🤝 参与贡献

欢迎贡献机器人适配器、模型适配器、平滑策略、测试用例与文档改进。提交 PR 前：

1. 先开 issue 讨论变更（尤其是新增机器人 / 模型适配器）
2. 遵循 `docs/guides/` 中的适配器约定
3. 确保新代码不破坏已有机器人 / 模型后端

开发环境使用项目的可编辑安装：

```bash
python -m pip install -e ".[dev]"
```

代码规范与测试约定见 [CONTRIBUTING.md](CONTRIBUTING.md)。


## 📖 引用

OPEN-RAIL 在以下预印本中以 **VLA-RAIL** 为名发表。若在研究或产品原型中使用本项目，请引用：

```bibtex
@misc{zhao2025vlarailrealtimeasynchronousinference,
  title={VLA-RAIL: A Real-Time Asynchronous Inference Linker for VLA Models and Robots},
  author={Yongsheng Zhao and Lei Zhao and Baoping Cheng and Gongxin Yao and Xuanzhang Wen and Han Gao},
  year={2025},
  eprint={2512.24673},
  archivePrefix={arXiv},
  primaryClass={cs.RO},
  url={https://arxiv.org/abs/2512.24673}
}
```

## ⚖️ 许可证

Apache License 2.0，详见 [LICENSE](LICENSE)。

---

**推理的终点，是真机的起点。** 给 OPEN-RAIL 一个 Star，加入社区，让模型、硬件、场景，在这里一起转起来。 ⭐
