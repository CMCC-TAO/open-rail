<div align="center">


# Open-RAIL

**一套异步连接 VLA/WAM 模型推理与机器人执行的通用底座**

[![Paper](https://img.shields.io/badge/arXiv-2512.24673-b31b1b)](https://arxiv.org/abs/2512.24673)
[![License](https://img.shields.io/badge/许可证-Apache--2.0-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](pyproject.toml)
[![Gitee](https://img.shields.io/badge/代码仓库-Gitee-c71d23)](https://gitee.com/cmcc-tao/open-rail)
[![GitHub](https://img.shields.io/badge/代码仓库-GitHub-181717)](https://github.com/CMCC-TAO/open-rail)
[![焕新社区](https://img.shields.io/badge/代码仓库-焕新社区-6f42c1)](https://aihuanxin.cn/#/embodiedAi/embodiedBrandDetail/106)
[![Docs](https://img.shields.io/badge/文档主页-online-2496ed)](https://cmcc-tao.github.io/open-rail/)
[![部署站点](https://github.com/CMCC-TAO/open-rail/actions/workflows/deploy-site.yml/badge.svg)](https://github.com/CMCC-TAO/open-rail/actions/workflows/deploy-site.yml)
[![GitHub Stars](https://img.shields.io/github/stars/CMCC-TAO/open-rail)](https://github.com/CMCC-TAO/open-rail/stargazers)
[![GitHub Clones](https://raw.githubusercontent.com/CMCC-TAO/open-rail/traffic/github/CMCC-TAO/open-rail/total_clones.svg)](https://github.com/CMCC-TAO/open-rail/graphs/traffic)
[![GitHub Issues](https://img.shields.io/github/issues/CMCC-TAO/open-rail)](https://github.com/CMCC-TAO/open-rail/issues)

<!-- 本项目不使用正式软件版本号，改以公开里程碑记录发布进展。 -->

[English](README.md) | [中文](README.zh-CN.md)

</div>

<video controls width="100%" preload="metadata">
  <source src="data/media/OPEN-RAIL_demo.mp4" type="video/mp4">
  <a href="data/media/OPEN-RAIL_demo.mp4">播放 Open-RAIL 演示视频</a>
</video>

VLA/WAM 模型越来越多，真机已是当下具身智能的版本答案。但真正没解决的，是模型 checkpoint 与机器人之间的那段工程链路：动作卡顿抖动、长时运行断流、执行数据回不到模型迭代。

**Open-RAIL 就是这段链路**：一套轻量级服务端-客户端框架，把任意 VLA/WAM 模型接到任意已适配机器人上，并把「**推**（真机推理执行）→ **采**（运行即采集）→ **评**（数据驱动迭代）」的闭环端到端接进每一次运行。

目前已适配 **4 款异构机器人**（含 LeRobot 仿真后端）、支持 **10 个主流 VLA/WAM 模型**（7 个系列），关节加速度标准差 **10+ → 0.1 rad/s²**。

- 🤖 **VLA/WAM 模型研究人员** — 开箱即用的真机部署环境，专注模型创新，不搭工程管线
- 🔧 **机器人工程师** — 快速验证算法的工具集，无需重复实现驱动与管线
- 🎓 **初创团队与高校实验室** — 降低真机实验启动成本，缩短从仿真到实物的周期

---
<details>
<summary><b>目录</b></summary>

- [📰 更新日志](#-更新日志)
- [✨ 功能特性](#-功能特性)
- [🤖 支持的机器人与模型](#-支持的机器人与模型)
- [🚀 快速开始](#-快速开始)
- [🎛️ 使用方式](#️-使用方式)
- [🏗️ 系统架构](#️-系统架构)
- [📊 数据与评估](#-数据与评估)
- [📚 文档](#-文档)
- [📅 待办清单](#todolist)
- [🤝 参与贡献](#-参与贡献)
- [💬 社区与交流](#-社区与交流)
- [📖 引用](#-引用)
- [⚖️ 许可证](#️-许可证)
- [🙏 致谢](#-致谢)

</details>

---

## 📰 更新日志

- **2026-09-16 · 首次公开** — 项目更名为 **Open-RAIL**（原 VLA-RAIL），首次开放 **推 / 采 / 评 / 兼容** 四层：三线程异步流水与两级在线平滑、推理即采集、评估数据随每次运行落盘、4 款异构机器人与 10 个 VLA/WAM 模型适配
- **2025-12 · 预印本发布** — [VLA-RAIL: A Real-Time Asynchronous Inference Linker for VLA Models and Robots](https://arxiv.org/abs/2512.24673)：异步推理与块内 / 块间两级在线平滑

<!-- TODO：为首次公开版本确定并记录正式版本号；此后每次发版在本节顶部补一条，并注明拓宽了哪条轴（模型 / 硬件 / 场景）。 -->

## ✨ 功能特性

| 痛点 | Open-RAIL 做法 | 效果 |
| --- | --- | --- |
| ⚡ 推理跟不上控制周期，动作又卡又抖 | 三线程异步流水（观测 / 推理 / 控制）+ 块内/块间两级在线平滑 | 关节加速度标准差 **10+ → 0.1 rad/s²**，消除 **30–50 倍**频率差 |
| ☁️ 机器人端算力跑不动大模型 | 服务端-客户端分离，两侧依赖树互不干涉 | 嵌入式设备也能驱动大模型；端 / 边 / 云**代码零改动**切换 |
| 🔌 换一台机器人就要重做接口 | 轻量硬件抽象层 `RobotBase` + 统一 `action_layout` 索引 | 已适配 **4 款异构机器人**；新机器人接入**从周级降到小时级** |
| 🧩 每接一个新模型都要重写工程管线 | 统一模型接入约定 + 服务端自动路由 | 已支持 **10 个模型**；新模型接入 **≤ 100 行** |
| 📊 推理与数采割裂，数据进不了训练管线 | 采集内置于每次推理，LeRobot 风格 Parquet，episode 可追加 | 每次运行产出可用训练数据，**零额外成本** |
| 🎮 模型推理跑偏，没法及时纠正 | 三模式（纯推理 / 纯遥操 / 混合）+ 暂停-介入-恢复与状态预对齐（10 月开源） | 每次人工纠偏即**高质量教学样本**，无需后处理 |

平滑在**框架层**完成，不改动模型，也不要求训练增强，扩散、流匹配、自回归架构通吃。

## 🤖 支持的机器人与模型

### 机器人

| 机器人 | 类型 | 状态 | 适配器 |
| --- | --- | --- | --- |
| AgiBot G1 | 双臂人形（头 + 腰 + 轮式底盘） | ✅ 已适配 | `client/robots/agibot_g1/` |
| 中国移动灵犀（Ti5 T170C） | 双臂轮式机器人（ROS 2） | ✅ 已适配 | `client/robots/ti5_t170c/` |
| NAVIAI-WA2（浙江人形） | 折叠轮臂人形（ROS 1） | ✅ 已适配 | `client/robots/navi_wa2/` |
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
| π 系列 | π0、π0.5 | ✅ 已支持 |
| TAO | TAO | ✅ 已支持 |
| _你的模型_ | — | 🔜 [接入指南](docs-cn-backup/add-new-model.zh-CN.md) |

## 🚀 快速开始

以下命令均在仓库根目录执行。

### 1. 环境要求

- **Python ≥ 3.10**
- **服务端（Server）**：所选模型所需的 NVIDIA 显卡、CUDA、PyTorch，以及该模型特有的依赖；各组件的版本要求以对应模型的官方文档为准。
- **客户端（Client）**：取决于所接入的机器人：AgiBot G1 需安装厂商 SDK；中国移动灵犀（Ti5 T170C）需 ROS 2；NAVIAI-WA2 需 ROS 1；若使用 Mock 仿真机器人，则无需额外硬件。
- **网络**：服务端与客户端通过 ZMQ 通信，两者处于同一局域网或网络互通即可。
- **操作系统**：目前仅支持 Ubuntu（暂不支持 macOS）。

### 2. 安装

代码在 GitHub、Gitee 与焕新社区同步开源，以下以 GitHub 为例，其他平台替换为对应仓库地址即可。

```bash
git clone https://github.com/CMCC-TAO/open-rail.git
cd open-rail
conda create -y -n open-rail python=3.10 && conda activate open-rail
pip install -e .
```

旧工作流也可用 `pip install -r requirements.txt`，依赖以 `pyproject.toml` 为准。

### 3. 启动服务端

服务端承载 VLA/WAM 模型运行时，通过 ZMQ 暴露推理端点。

```bash
python run_server.py --model_type <模型类型> --model_path <权重路径>
```

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--model_type` | 已注册的模型适配器，如 `tao` | — |
| `--model_path` | 模型 checkpoint 目录 | — |

<details>
<summary><b>完整示例</b></summary>

```bash
python run_server.py --model_type tao \
  --model_path /path/to/checkpoints/tao_v0/checkpoint-30000
```

</details>

### 4. 启动 Web 客户端

```bash
python run_web_client.py
```

默认读取 `conf/default_conf.yaml`，监听 `0.0.0.0:9000`。自定义配置文件需要放在 `conf/` 目录下，并通过 `--conf` 参数指定文件名：

```bash
python run_web_client.py --conf custom_conf.yaml
```

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--host` | 监听地址 | `0.0.0.0` |
| `--port` | HTTP / UI 端口 | `9000` |
| `--conf` | `conf/` 下的配置文件 | `default_conf.yaml` |


### 5. 验证

浏览器打开 http://localhost:9000，能看到 Web 界面、相机画面与机器人状态就绪，说明启动成功；选择任务后就可以驱动机器人。

## 🎛️ 使用方式

配置入口速查：

| 文件 | 作用 |
| --- | --- |
| `conf/*.yaml` | 主配置：`robots.type` 选择机器人适配器，相机话题、`action_layout` 与本体感知参数 |
| `conf/robots_conf.py` | 机器人硬件参数；Mock 后端在此设置 `dataset_path` |
| 服务端网络地址 | 端 / 边 / 云切换只需修改此项，字段名见 [docs/configuration.zh-CN.md](docs/configuration.zh-CN.md) |

### 仿真闭环（无真机起步）

不需要真实机器人硬件时，可以用 Mock 后端回放已有的 LeRobot 数据集：在 `conf/robots_conf.py` 的 Mock 配置中设置 `dataset_path`，并准备对应的 Parquet episode 与相机视频。服务端可用 `--model_type mock` 生成随机动作验证服务链路；验证真实模型效果仍需提供自己的 checkpoint 和模型专属环境。

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

修改 `conf/*.yaml` 中的 `robots.type` 为目标机器人适配器（`agibot_g1` / `ti5_t170c` / `navi_wa2`），并按 [docs/configuration.zh-CN.md](docs/configuration.zh-CN.md) 配置相机话题、`action_layout` 与本体感知参数，然后同样用两条命令启动。

### 混合模式：推理 + 实时遥操纠偏

> 🚧 10 月开源

在客户端中切换三种运行模式——纯推理 / 纯遥操 / 混合。混合模式下可随时**暂停 → 介入纠偏 → 恢复**，状态预对齐保证接管瞬间无跳变；纠偏轨迹与推理轨迹按时间戳对齐、并行保存，每一段人工纠偏都是可直接进训练管线的教学样本。

![数据沉淀与遥操接入示意](data/media/data-teleop.png)

## 🏗️ 系统架构

![Open-RAIL 架构图](data/media/architecture.zh-CN.png)

Open-RAIL 采用 **服务端-客户端分布式架构**，推理主链路与可视化链路各自独立、互不干扰。**服务端**负责模型推理；**客户端**部署在机器人一侧，负责状态采集、任务执行、指令下发和数据记录，把机器人配置与模型推理整合成一条完整的工作流。

服务端独占模型环境，客户端独占机器人环境，两侧的依赖树因此互不干涉——模型需要的 CUDA / PyTorch 版本和机器人驱动需要的 ROS 版本不会互相冲突。这也是端 / 边 / 云「代码零改动切换」的前提：换部署位置，只需修改服务端网络地址。


```text
.
├── client/                 # 客户端运行时、机器人适配器、数据记录和工具
│   ├── core/               # 观测、推理、控制、通信、可视化和数据记录
│   ├── robots/             # RobotBase 及各机器人/仿真适配器
│   └── utils/              # 客户端通用工具和可视化工具
├── server/                 # 模型运行时和推理服务
│   ├── core/               # VLAServer、ZMQServer 和可视化服务
│   ├── models/             # VLA/WAM 模型适配器与模型专属实现
│   └── utils/              # 服务端通用工具
├── conf/                   # 客户端、服务端、机器人和记录配置
├── web_client/             # Web UI、HTTP API 和 WebSocket 服务
├── visual/                 # 独立可视化资源与数据推送服务
├── extra/                  # 额外的调度和通信辅助模块
├── scripts/                # CUDA、数据展示和评测可视化脚本
├── docs/                   # 快速开始、架构、配置、排障和接入指南
│   └── guides/             # 机器人与 VLA/WAM 模型接入指南
├── data/                   # 本地数据、媒体资源和录制输出
│   ├── media/              # 演示视频、架构图和可视化示意图
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

### 执行链路：异步流水 + 两级在线平滑

VLA 推理与控制之间存在数量级的频率差：模型出一次 action chunk 要几百毫秒，机器人控制回路却跑在几十到几百赫兹。同步方案里，控制周期的延迟下界就是模型延迟——动作卡顿与抖动正是从这里来的。

Open-RAIL 用**三条互相解耦的线程**消除这个差距：

![Open-RAIL 三线程异步流水线](data/media/async-pipeline.zh-CN.png)

三条线程各按自己的节奏跑，互不等待：

1. **观测线程**按传感器频率采集相机与本体感知数据，异步上行给服务端，不等推理返回
2. **推理线程**按模型自身节奏产出动作块，一次推理结果被后续多个控制周期复用
3. **控制线程**按控制频率执行：拿已有 chunk 做插值，新 chunk 到达时在线并入，从不空等

频率差吸收掉之后，剩下的抖动来自动作分块本身——动作块内部可能不连续，块与块的接缝处会跳变。Open-RAIL 用两级在线平滑处理：

- **块内平滑** — 消除单个动作块内部的离散跳变
- **块间平滑** — 消除相邻动作块接缝处的突变

实现细节（平滑算法与窗口、chunk 并入策略、推理超时降级策略、缓冲区结构与容量）见 [docs/architecture.zh-CN.md](docs/architecture.zh-CN.md)。

## 📊 数据与评估

推理、数采与评估通常是三套分开的流程，Open-RAIL 把它们都接进每一次运行。

### 采：运行即采集

- 📡 数据由客户端数据管理器写入，与推理主链路并行，不影响控制频率
- 🗂️ **LeRobot 风格 Parquet**，数据片段支持追加，适配长周期运行与增量训练
- 🎮 人工纠偏产生的片段可以直接当教学样本用，不需要额外处理（10 月开源）

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

Parquet 保存观测、状态和动作；视频按相机 key 分目录保存。

### 评：运行即评估

每次运行在 `eval/` 下落地两份评估日志：`eval_log.json` 保留原始统计数组，`eval_log.csv` 将各项耗时聚合为平均值，两者按统一时间基准对齐。

| 指标 | 字段 | 说明 |
| --- | --- | --- |
| 推理耗时 | `avg_infer_time` | 每轮推理的平均调用时延 |
| 图像预处理耗时 | `img_proc_time` | 观测图像预处理耗时 |
| 块内轨迹耗时 | `avg_intra_traj_time` | 单个动作块内部的处理耗时 |
| 块间轨迹耗时 | `avg_inter_traj_time` | 相邻动作块衔接的处理耗时 |
| 通信耗时 | `avg_comm_time` | 观测上行与指令下行的链路时延 |
| 观测帧率 | `obv_fps` | 实际帧率，用于确认观测链路没有掉帧 |

- 🧾 **运行配置随结果一并记录**——模型、控制周期、平滑模式与 chunk 配置，保证结果可复现、可跨运行对照
- 🚨 **异常同样留痕**——推理超时、数据缺失或人为中断都计入日志，记录不只保留顺利那次
- 📈 **运行即可视化**——动作原始值与平滑后结果的对照曲线、关节状态轨迹在线展示，问题不必等复盘才暴露

## 📚 文档

| 文档                                                         | 说明                         |
| ------------------------------------------------------------ | ---------------------------- |
| 🚀 [docs/getting-started.zh-CN.md](docs/getting-started.zh-CN.md)         | 安装与首次运行               |
| 🏗️ [docs/architecture.zh-CN.md](docs/architecture.zh-CN.md)               | 架构详解与异步流水线实现细节 |
| ⚙️ [docs/configuration.zh-CN.md](docs/configuration.zh-CN.md)             | 完整配置项参考               |
| 🔧 [docs/troubleshooting.zh-CN.md](docs/troubleshooting.zh-CN.md)         | 常见问题与排查               |
| 🤖 [docs/guides/add-new-robot.zh-CN.md](docs/guides/add-new-robot.zh-CN.md)     | 如何新增机器人适配器         |
| 🧠 [docs-cn-backup/add-new-model.zh-CN.md](docs-cn-backup/add-new-model.zh-CN.md) | 如何新增 VLA/WAM 模型适配器      |
| 📦 [docs/demo-running-on-dataset.zh-CN.md](docs/demo-running-on-dataset.zh-CN.md) | 端到端实例：在 AgiBotWorld 2026 数据集上运行 GR00T-N1.5 |

## 待办清单 📅 <a name="todolist"></a>

**推——模型到机器人执行**

- [x] 三线程异步流水 + 两级在线平滑——关节加速度标准差 **10+ → 0.1 rad/s²**
- [x] async / sync 两种推理模式；心跳检测与自动重连
- [x] 服务端-客户端分离——端 / 边 / 云零改动切换
- [ ] 三模式运行 + 实时遥操纠偏（10 月）
  - [ ] 纯推理 / 纯遥操 / 混合三种运行模式
  - [ ] 暂停 → 介入 → 恢复，状态预对齐

**采——推理即采集（LeRobot 风格 Parquet）**

- [x] 采集内置于每次推理，episode 可追加
- [ ] 纠偏轨迹与推理轨迹按时间戳对齐、并行保存

**评——运行即评估**

- [x] 评估日志（JSON / CSV）覆盖推理、轨迹与通信耗时
- [x] 运行配置留痕可复现；运行即可视化
- [ ] 发布基于原子技能的真机评测基准
- [ ] 场景库与评分口径——任务场景、评分规范与结果提交方式

**训——训练框架**

- [ ] 发布自研训练框架
- [ ] 数据集约定——训练数据的统一格式与组织规范

**兼容——多模型与多机器人控制**

- [x] 4 款异构机器人（AgiBot G1 / 中国移动灵犀（Ti5 T170C）/ NAVIAI-WA2 + 一套 LeRobot 仿真后端）
- [x] 10 个 VLA/WAM 模型（7 系列）
- [x] 可视化抽象为独立层——面向非开发人员的控制入口
- [ ] WAM 模型接入（10 月）
  - [ ] dreamzero
  - [ ] cosmos
- [ ] 多机器人编排——一个服务端调度多个客户端
- [ ] 仿真器对接

图例：✅ 已发布；（10 月）为 10 月放出。

## 🤝 参与贡献

欢迎贡献机器人适配器、模型适配器、平滑策略、测试用例与文档改进，社区驱动的条目尤其欢迎机器人与模型适配器。提交 PR 前：

1. 先开 issue 讨论变更（尤其是新增机器人 / 模型适配器）
2. 遵循 `docs/guides/` 中的适配器约定
3. 确保新代码不破坏已有机器人 / 模型后端

开发环境使用项目的可编辑安装：

```bash
python -m pip install -e ".[dev]"
```

代码规范与测试约定见 [CONTRIBUTING.md](CONTRIBUTING.md)。如需提交代码，请注意保持改动聚焦，并遵守贡献指南中对 checkpoint、录制数据、日志和本地配置的提交限制。

## 💬 社区与交流

代码在 GitHub、Gitee 与焕新社区同步开源，三处内容一致。

| 入口 | 地址 |
| --- | --- |
| 代码仓库（Gitee） | [gitee.com/cmcc-tao/open-rail](https://gitee.com/cmcc-tao/open-rail) |
| 代码仓库（GitHub） | [github.com/CMCC-TAO/open-rail](https://github.com/CMCC-TAO/open-rail) |
| 代码仓库（焕新社区） | [aihuanxin.cn/#/embodiedAi/embodiedBrandDetail/106](https://aihuanxin.cn/#/embodiedAi/embodiedBrandDetail/106) |
| 文档主页 | [cmcc-tao.github.io/open-rail](https://cmcc-tao.github.io/open-rail/) |
| 问题与需求 | 仓库 Issues——缺陷、文档问题与新功能需求；新增机器人 / 模型适配器建议先开 issue 讨论 |

<!-- TODO：补充交流群 / 讨论区入口。 -->

## 📖 引用

引用本仓库（Open-RAIL，代码与文档）：

```bibtex
@misc{openrail2026,
  title        = {Open-RAIL},
  author       = {Zhao, Yongsheng and Zhao, Lei and Cheng, Baoping and Yao, Gongxin and Wen, Xuanzhang and Gao, Han},
  year         = {2026},
  howpublished = {\url{https://github.com/CMCC-TAO/open-rail}},
  note         = {Open-source framework connecting VLA/WAM model inference with robot execution}
}
```

引用论文（本仓库在以下预印本中以 **VLA-RAIL** 为名发表）：

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

## 🙏 致谢

- 数据集格式与工具链借鉴 [LeRobot](https://github.com/huggingface/lerobot) 的 Parquet 与视频组织约定
- 模型适配基于各模型官方实现：GR00T（[NVIDIA Isaac-GR00T](https://github.com/NVIDIA/Isaac-GR00T)）、RDT（[thu-ml](https://github.com/thu-ml/RoboticsDiffusionTransformer)）、ACT、SmolVLA、GO1、π 系列、TAO
- ACT 适配中的 DETR 部分修改自 [facebookresearch/detr](https://github.com/facebookresearch/detr)（Apache 2.0），扩散策略相关实现参考 [real-stanford/diffusion_policy](https://github.com/real-stanford/diffusion_policy)
- 机器人适配依赖各厂商 SDK 与驱动：AgiBot G1、NAVIAI-WA2（浙江人形）、中国移动

---

**推理的终点，是真机的起点。** 给 Open-RAIL 一个 Star，加入社区，让模型、硬件、场景，在这里一起转起来。 ⭐
