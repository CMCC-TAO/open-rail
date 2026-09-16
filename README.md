<div align="center">


# OPEN-RAIL

**A Universal Substrate for Asynchronously Linking VLA Model Inference and Robot Execution**

[![Paper](https://img.shields.io/badge/arXiv-2512.24673-b31b1b)](https://arxiv.org/abs/2512.24673)
[![License](https://img.shields.io/badge/License-Apache--2.0-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](pyproject.toml)
[![Gitee](https://img.shields.io/badge/Repository-Gitee-c71d23)](https://gitee.com/cmcc-tao/open-rail)
[![GitHub](https://img.shields.io/badge/Repository-GitHub-181717)](https://github.com/CMCC-TAO/open-rail)
[![Huanxin Community](https://img.shields.io/badge/Repository-Huanxin_Community-6f42c1)](https://aihuanxin.cn/#/embodiedAi/embodiedBrandDetail/106)
[![Docs](https://img.shields.io/badge/Docs-online-2496ed)](https://cmcc-tao.github.io/open-rail/)

<!-- TODO: add CI status and version badges; Stars / Issues dynamic badges once the public repository is bound. -->

[English](README.md) | [中文](README.zh-CN.md)

</div>

<video controls width="100%" preload="metadata">
  <source src="data/media/OPEN-RAIL_demo.mp4" type="video/mp4">
  <a href="data/media/OPEN-RAIL_demo.mp4">Play the OPEN-RAIL demo video</a>
</video>

VLA models keep multiplying, and real-robot deployment is now the accepted answer in embodied AI. What remains unsolved is the stretch of engineering between a model checkpoint and the robot: jerky, jittery motion, stream dropouts over long runs, and execution data that never flows back into model iteration.

**OPEN-RAIL is exactly that link** — a lightweight server-client framework that connects any VLA model to any adapted robot and wires the closed loop of **infer** (real-robot inference and execution) → **collect** (capture data as it runs) → **evaluate** (data-driven iteration) end-to-end into every run.

It currently adapts **4 heterogeneous robots** (including a LeRobot simulation backend) and supports **10 mainstream VLA models** (7 families), with joint acceleration standard deviation reduced from **10+ to 0.1 rad/s²**.

- 🤖 **VLA researchers** — a ready-to-use real-robot deployment environment; focus on model innovation, not on building the pipeline
- 🔧 **Robotics engineers** — a toolkit for fast algorithm validation, without reimplementing drivers and plumbing
- 🎓 **Startups and university labs** — lower the entry cost of real-robot experiments and shorten the path from simulation to hardware

---
<details>
<summary><b>Table of contents</b></summary>

- [📰 Changelog](#-changelog)
- [✨ Features](#-features)
- [🤖 Supported Robots & Models](#-supported-robots--models)
- [🚀 Quick Start](#-quick-start)
- [🎛️ Usage](#️-usage)
- [🏗️ Architecture](#️-architecture)
- [📊 Data & Evaluation](#-data--evaluation)
- [📚 Documentation](#-documentation)
- [📅 TODO List](#todolist)
- [🤝 Contributing](#-contributing)
- [💬 Community](#-community)
- [📖 Citation](#-citation)
- [⚖️ License](#️-license)
- [🙏 Acknowledgements](#-acknowledgements)

</details>

---

## 📰 Changelog

- **2026-09 · First open-source release** — Renamed to **OPEN-RAIL** (formerly VLA-RAIL), opening four layers — **infer / collect / evaluate / adapt**: three-thread asynchronous pipeline with two-level online smoothing, inference-as-collection, evaluation data written on every run, and adaptation for 4 heterogeneous robots and 10 VLA models
- **2025-12 · Preprint release** — [VLA-RAIL: A Real-Time Asynchronous Inference Linker for VLA Models and Robots](https://arxiv.org/abs/2512.24673): asynchronous inference with intra-/inter-chunk two-level online smoothing

<!-- TODO: confirm the exact date and version number of the first open-source release; add a new entry at the top of this section for each subsequent release, noting which axis (models / hardware / scenarios) it widened. -->

## ✨ Features

| Pain point | What OPEN-RAIL does | Effect |
| --- | --- | --- |
| ⚡ Inference can't keep up with the control cycle; motion stutters and jitters | Three-thread asynchronous pipeline (observation / inference / control) + two-level online smoothing (intra-/inter-chunk) | Joint acceleration std **10+ → 0.1 rad/s²**, eliminating a **30–50×** frequency gap |
| ☁️ Robot-side compute can't run large models | Server-client split, with non-overlapping dependency trees | Embedded devices can drive large models; device / edge / cloud switching with **zero code changes** |
| 🔌 Every new robot means redoing the interface | Lightweight hardware abstraction layer `RobotBase` + unified `action_layout` indexing | **4 heterogeneous robots** adapted; onboarding a new robot **from weeks to hours** |
| 🧩 Every new model means rewriting the pipeline | Unified model integration contract + automatic server-side routing | **10 models** supported; new models integrate in **≤ 100 lines** |
| 📊 Inference and collection are split; data never reaches the training pipeline | Collection built into every inference run, LeRobot-style Parquet, appendable episodes | Every run produces usable training data, **at zero extra cost** |
| 🎮 When inference drifts, there is no timely way to correct it | Three modes (pure inference / pure teleop / hybrid) + pause–intervene–resume with state pre-alignment (opening in October) | Every human correction is a **high-quality demonstration**, with no post-processing |

Smoothing happens at the **framework level** — no model changes, no training augmentation required; diffusion, flow-matching, and autoregressive architectures all work.

## 🤖 Supported Robots & Models

### Robots

| Robot | Type | Status | Adapter |
| --- | --- | --- | --- |
| A2D | Bimanual humanoid (head + waist + wheeled base) | ✅ Adapted | `client/robots/a2d/` |
| Ti5 T170C | Bimanual wheeled robot (ROS 2) | ✅ Adapted | `client/robots/ti5_t170c/` |
| Navi WA2 (Zhejiang Humanoid) | Folding wheel-legged humanoid (ROS 1) | ✅ Adapted | `client/robots/navi_wa2/` |
| Mock | LeRobot-based simulation backend | ✅ Adapted | `client/robots/mock/` |
| _Your robot_ | — | 🔜 Planned | [Integration guide](docs/guides/add-new-robot.md) |

### Models

| Model family | Members | Status |
| --- | --- | --- |
| ACT | ACT | ✅ Supported |
| GR00T N1 series | GR00T N1, N1.5, N1.6 | ✅ Supported |
| RDT | RDT-1B | ✅ Supported |
| SmolVLA | SmolVLA | ✅ Supported |
| GO1 | AgiBot GO-1 | ✅ Supported |
| π series | Pi0, Pi0.5 | ✅ Supported |
| TAO | TAO | ✅ Supported |
| _Your model_ | — | 🔜 [Integration guide](docs/guides/add-new-vla-model.md) |

## 🚀 Quick Start

All commands below are run from the repository root.

### 1. Prerequisites

- **Python ≥ 3.10**
- **Server**: the NVIDIA GPU, CUDA, PyTorch, and model-specific dependencies required by the chosen model; version requirements follow each model's official documentation
- **Client**: depends on the robot — A2D needs the vendor SDK, Ti5 T170C needs ROS 2, Navi WA2 needs ROS 1; the Mock simulation backend has no extra hardware requirements
- **Network**: the two sides communicate over ZMQ; being on the same LAN or mutually reachable is enough
- **OS**: Linux is the primary runtime environment today

### 2. Install

The code is open-source in sync on GitHub, Gitee, and the Huanxin Community. The example below uses Gitee; substitute the matching repository URL for the others.

```bash
git clone https://gitee.com/cmcc-tao/open-rail.git
cd open-rail
conda create -y -n open-rail python=3.10 && conda activate open-rail
pip install -e .
```

`pip install -e .` registers two console entry points, `vla-server` and `vla-web-client`, equivalent to the launch scripts below. Older workflows can still use `pip install -r requirements.txt`; dependencies follow `pyproject.toml`.

### 3. Start the server

The server hosts the VLA model runtime and exposes an inference endpoint over ZMQ.

```bash
python run_server.py --model_type <model_type> --model_path <checkpoint_path>
```

| Argument | Description | Default |
| --- | --- | --- |
| `--model_type` | Registered model adapter, e.g. `tao` | — |
| `--model_path` | Model checkpoint directory | — |

<details>
<summary><b>Full example</b></summary>

```bash
python run_server.py --model_type tao \
  --model_path /path/to/checkpoints/tao_v0/checkpoint-30000
```

</details>

### 4. Start the web client

```bash
python run_web_client.py
```

By default it reads `conf/default_conf.yaml` and listens on `0.0.0.0:9000`. Custom config files go under `conf/` and are selected with the `--conf` argument:

```bash
python run_web_client.py --conf custom_conf.yaml
```

| Argument | Description | Default |
| --- | --- | --- |
| `--host` | Bind address | `0.0.0.0` |
| `--port` | HTTP / UI port | `9000` |
| `--conf` | Config file under `conf/` | `default_conf.yaml` |


### 5. Verify

Open http://localhost:9000 in your browser. When the web UI, camera feeds, and robot status are up, the system is running; pick a task and drive the robot.

## 🎛️ Usage

Configuration entry points at a glance:

| File | Purpose |
| --- | --- |
| `conf/*.yaml` | Main config: `robots.type` selects the robot adapter, plus camera topics, `action_layout`, and proprioception parameters |
| `conf/robots_conf.py` | Robot hardware parameters; set `dataset_path` here for the Mock backend |
| Server network address | The only thing that changes between device / edge / cloud deployments; field name in [docs/configuration.md](docs/configuration.md) |

### Simulation loop (no real robot needed)

Without real robot hardware, the Mock backend can replay an existing LeRobot dataset: set `dataset_path` in the Mock section of `conf/robots_conf.py`, and prepare the matching Parquet episodes and camera videos. On the server side, `--model_type mock` generates random actions to verify the service path; to evaluate a real model, you still need your own checkpoint and the model's own environment.

Minimal Mock dataset layout:

```text
<dataset>/
├── data/chunk-000/episode_000000.parquet
├── videos/chunk-000/observation.images.head_rgb/episode_000000.mp4
├── videos/chunk-000/observation.images.left_wrist_rgb/episode_000000.mp4
├── videos/chunk-000/observation.images.right_wrist_rgb/episode_000000.mp4
└── meta/info.json                       # optional, for reading fps
```

The mock model only returns random actions and cannot stand in for real model evaluation.

### Real-robot execution

Set `robots.type` in `conf/*.yaml` to the target robot adapter (`a2d` / `ti5_t170c` / `navi_wa2`), configure camera topics, `action_layout`, and proprioception parameters per [docs/configuration.md](docs/configuration.md), then start with the same two commands.

### Hybrid mode: inference + live teleoperation correction (opening in October)

> 🚧 Opening in October, not part of the current version.

Switch between three run modes in the client — pure inference / pure teleop / hybrid. In hybrid mode you can **pause → take over → resume** at any time; state pre-alignment keeps the takeover free of jumps. Correction trajectories are timestamp-aligned with inference trajectories and saved in parallel, so every human correction is a demonstration that goes straight into the training pipeline.

![Data recording and teleoperation integration](data/media/data-teleop.png)

## 🏗️ Architecture

![OPEN-RAIL Architecture](data/media/framework.png)

OPEN-RAIL uses a **server-client distributed architecture**; the inference path and the visualization path run independently and never interfere. The **server** handles model inference; the **client** runs on the robot side and takes care of observation collection, task execution, command dispatch, and data recording, tying robot configuration and model inference into one workflow.

The server owns the model environment and the client owns the robot environment, so the two dependency trees never collide — the CUDA / PyTorch versions the model needs don't conflict with the ROS versions the robot drivers need. This is also what makes device / edge / cloud switching a zero-code-change operation: moving the deployment only means changing the server's network address.


```text
.
├── client/                 # Client runtime, robot adapters, recording, and utilities
│   ├── core/               # Observation, inference, control, transport, visualization, and recording
│   ├── robots/             # RobotBase and robot/simulation adapters
│   └── utils/              # Client utilities and visualization tools
├── server/                 # Model runtime and inference service
│   ├── core/               # VLAServer, ZMQServer, and visualization service
│   ├── models/             # VLA model adapters and model-specific implementations
│   └── utils/              # Server utilities
├── conf/                   # Client, server, robot, and recording configuration
├── web_client/             # Web UI, HTTP API, and WebSocket service
├── visual/                 # Standalone visualization assets and data push service
├── extra/                  # Dispatch and communication helpers
├── scripts/                # CUDA, dataset display, and evaluation scripts
├── docs/                   # Getting started, architecture, configuration, troubleshooting, and guides
│   └── guides/             # Robot and VLA model integration guides
├── data/                   # Local data, media assets, and recording output
│   ├── media/              # Demo videos, architecture diagrams, and illustrations
│   └── README.md           # Data directory notes
├── test/                   # Tests and experiments
├── run_server.py           # Server entry point
├── run_web_client.py       # Web client entry point
├── pyproject.toml          # Package metadata and runtime dependencies
├── requirements.txt        # Compatibility dependency list
├── README.md               # English documentation
├── README.zh-CN.md         # Chinese documentation
├── LICENSE                 # Apache License 2.0
└── CITATION.cff            # Citation metadata
```

### Execution link: async pipeline + two-level online smoothing

VLA inference and control are separated by an order-of-magnitude frequency gap: a model needs hundreds of milliseconds to emit one action chunk, while the control loop runs at tens to hundreds of hertz. In a synchronous design, the control cycle's latency floor is the model latency — this is where stutter and jitter come from.

OPEN-RAIL closes that gap with **three decoupled threads**:

![OPEN-RAIL three-thread asynchronous pipeline](data/media/async-pipeline.png)
<!-- 🖼️ Placeholder: three-thread asynchronous pipeline diagram — the observation / inference / control threads each run at their own pace; recommended 1600×900, <1MB, path data/media/async-pipeline.png -->

Each thread runs at its own pace, and none of them wait:

1. **Observation thread** captures camera and proprioceptive data at sensor frequency and streams it upstream to the server without waiting for inference to return
2. **Inference thread** emits action chunks at the model's own pace; one inference result is reused across many subsequent control cycles
3. **Control thread** executes at control frequency: it interpolates the chunk it already holds, folds in new chunks online as they arrive, and never idles

Once the frequency gap is absorbed, the jitter that remains comes from the action chunks themselves — a chunk may be discontinuous internally, and the seam between chunks can jump. OPEN-RAIL handles this with two levels of online smoothing:

- **Intra-chunk smoothing** — removes discrete jumps inside a single chunk
- **Inter-chunk smoothing** — removes discontinuities at the seam between adjacent chunks

Implementation details (smoothing algorithms and windows, chunk merge policy, the fallback on inference timeout, buffer structure and capacity) are documented in [docs/architecture.md](docs/architecture.md).

## 📊 Data & Evaluation

Inference, data collection, and evaluation are usually three separate workflows; OPEN-RAIL builds all of them into every run.

### Collect: capture as you run

- 📡 Data is written by the client-side data manager in parallel with the inference path and does not affect the control frequency
- 🗂️ **LeRobot-style Parquet**, with appendable episodes suited to long-horizon runs and incremental training
- 🎮 Segments produced by human correction can be used directly as demonstrations, with no extra processing (opening in October)

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

Parquet stores observations, states, and actions; videos are saved in per-camera directories.

### Evaluate: evaluation on every run

Every run writes two evaluation logs under `eval/`: `eval_log.json` keeps the raw statistic arrays, and `eval_log.csv` aggregates the timings into averages; both are aligned to a single time base.

| Metric | Field | Description |
| --- | --- | --- |
| Inference time | `avg_infer_time` | Average call latency per inference round |
| Image preprocessing time | `img_proc_time` | Time to preprocess observation images |
| Intra-chunk trajectory time | `avg_intra_traj_time` | Processing time inside a single action chunk |
| Inter-chunk trajectory time | `avg_inter_traj_time` | Processing time at the seam between adjacent chunks |
| Communication time | `avg_comm_time` | Uplink observation and downlink command latency |
| Observation frame rate | `obv_fps` | Actual frame rate, to confirm the observation link is not dropping frames |

- 🧾 **Run configuration recorded alongside results** — model, control period, smoothing modes, and chunk settings, so a run can be reproduced and compared across runs
- 🚨 **Deviations recorded too** — inference timeouts, missing data, or manual aborts are logged as well, so the record is not limited to the runs that went smoothly
- 📈 **Visualization while running** — raw-versus-smoothed action curves and joint-state trajectories shown live, so problems surface before the retrospective

## 📚 Documentation

| Document | Description |
| --- | --- |
| 🚀 [docs/getting-started.md](docs/getting-started.md) | Installation and first run |
| 🏗️ [docs/architecture.md](docs/architecture.md) | Architecture deep dive and async pipeline internals |
| ⚙️ [docs/configuration.md](docs/configuration.md) | Full configuration reference |
| 🔧 [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues and fixes |
| 🤖 [docs/guides/add-new-robot.md](docs/guides/add-new-robot.md) | How to add a robot adapter |
| 🧠 [docs/guides/add-new-vla-model.md](docs/guides/add-new-vla-model.md) | How to add a VLA model adapter |
| 📦 [docs/demo-running-on-dataset.md](docs/demo-running-on-dataset.md) | End-to-end example: running GR00T-N1.5 on the AgiBotWorld 2026 dataset |

## TODO List 📅 <a name="todolist"></a>

**Infer — model to robot execution**

- [x] Three-thread asynchronous pipeline + two-level online smoothing — joint acceleration std **10+ → 0.1 rad/s²**
- [x] async / sync inference modes; heartbeat detection and auto-reconnect
- [x] Server-Client split — device / edge / cloud switching with zero code changes
- [ ] Three run modes + real-time teleop intervention (October)
  - [ ] Pure inference / pure teleop / hybrid run modes
  - [ ] Pause → intervene → resume with state pre-alignment

**Collect — inference-as-collection (LeRobot-style Parquet)**

- [x] Recording built into every inference run, with appendable episodes
- [ ] Correction trajectories saved in parallel, timestamp-aligned with inference trajectories

**Evaluate — evaluation on every run**

- [x] eval logs (JSON / CSV) covering inference, trajectory, and communication timings
- [x] Run configuration recorded for reproducibility; live visualization while running
- [ ] Release an atomic-skill real-robot benchmark
- [ ] Scenario library and scoring protocol — task scenarios, scoring rules, and result submission

**Train — training framework**

- [ ] Release an in-house training framework
- [ ] Dataset conventions — a unified format and organization spec for training data

**Adapt — multi-model and multi-robot control**

- [x] 4 heterogeneous robots (A2D / Ti5 T170C / Navi WA2 + a LeRobot simulation backend)
- [x] 10 VLA models across 7 families
- [x] Visualization abstracted as its own layer — a control entry for non-developers
- [ ] WAM integration (October)
  - [ ] dreamzero
  - [ ] cosmos
- [ ] Multi-robot orchestration — one server scheduling multiple clients
- [ ] Simulator integration

Legend: ✅ released · (October) opening in October.

## 🤝 Contributing

Contributions of robot adapters, model adapters, smoothing strategies, test cases, and documentation improvements are welcome; community-driven items, especially robot and model adapters, are particularly welcome. Before opening a PR:

1. Open an issue to discuss the change first (especially for new robot / model adapters)
2. Follow the adapter conventions in `docs/guides/`
3. Make sure new code does not break existing robot / model backends

For development, install the project in editable mode:

```bash
python -m pip install -e ".[dev]"
```

Code style and test conventions are in [CONTRIBUTING.md](CONTRIBUTING.md). When submitting code, keep changes focused, and follow the contribution guidelines on what may not be committed: checkpoints, recordings, logs, and local configs.

## 💬 Community

The code is open-source in sync on GitHub, Gitee, and the Huanxin Community; the three are identical.

| Entry | Link |
| --- | --- |
| Repository (Gitee) | [gitee.com/cmcc-tao/open-rail](https://gitee.com/cmcc-tao/open-rail) |
| Repository (GitHub) | [github.com/CMCC-TAO/open-rail](https://github.com/CMCC-TAO/open-rail) |
| Repository (Huanxin Community) | [aihuanxin.cn/#/embodiedAi/embodiedBrandDetail/106](https://aihuanxin.cn/#/embodiedAi/embodiedBrandDetail/106) |
| Docs site | [cmcc-tao.github.io/open-rail](https://cmcc-tao.github.io/open-rail/) |
| Issues and requests | Repository Issues — bugs, documentation problems, and feature requests; for new robot / model adapters, open an issue to discuss first |

<!-- TODO: add a community chat / discussion entry. -->

## 📖 Citation

Cite this repository (OPEN-RAIL, code and documentation):

```bibtex
@misc{openrail2026,
  title        = {OPEN-RAIL},
  author       = {Zhao, Yongsheng and Zhao, Lei and Cheng, Baoping and Yao, Gongxin and Wen, Xuanzhang and Gao, Han},
  year         = {2026},
  howpublished = {\url{https://github.com/CMCC-TAO/open-rail}},
  note         = {Open-source framework connecting VLA model inference with robot execution}
}
```

Cite the paper (this repository is published under the name **VLA-RAIL** in the following preprint):

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

## ⚖️ License

Apache License 2.0. See [LICENSE](LICENSE).

## 🙏 Acknowledgements

- Dataset format and tooling follow [LeRobot](https://github.com/huggingface/lerobot)'s Parquet and video organization conventions
- Model adapters are based on each model's official implementation: GR00T ([NVIDIA Isaac-GR00T](https://github.com/NVIDIA/Isaac-GR00T)), RDT ([thu-ml](https://github.com/thu-ml/RoboticsDiffusionTransformer)), ACT, SmolVLA, GO1, π series, TAO
- The DETR portion of the ACT adapter is adapted from [facebookresearch/detr](https://github.com/facebookresearch/detr) (Apache 2.0), and the diffusion-policy implementations reference [real-stanford/diffusion_policy](https://github.com/real-stanford/diffusion_policy)
- Robot adapters rely on each vendor's SDK and drivers: A2D, Ti5 T170C, Navi WA2 (Zhejiang Humanoid)

---

**Inference ends where the real robot begins.** Give OPEN-RAIL a star, join the community, and let models, hardware, and scenarios turn together. ⭐
