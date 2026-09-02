# Getting Started

**English Version** | [中文版](getting-started.zh-CN.md)

> 📌 This document is for **complete environment setup and feature integration**.  
> If you just want to verify the Web service is accessible, you can **only execute Step 2**; Server is not required, but client business status, robot status, and inference results may be unavailable.  
> For a 30-second quick experience, return to the [README Quick Start](../README.md#quick-start).

---

## Prerequisites

- **Operating System**: Linux/macOS are the primary supported environments; Windows can run Python services, but robot SDKs, ROS, and port management require separate verification.
- **Python**: 3.10 or higher
- **Git**: For cloning the code
- **Model Weights**: Your own checkpoint is required for inference
- **GPU**: Depends on the selected model
- **Physical Robot (Optional)**: If deploying to a physical robot, prepare the vendor-provided SDK, drivers, and corresponding network environment (Ethernet/Serial/Wi-Fi, etc.)

### Environment Setup Options (Choose One)

- **Option A (Recommended)**: Prepare two separate Conda environments to avoid dependency conflicts.
  - `vla-rail-client`: Installs this repository's dependencies, runs the Web client and robot adapters.
  - `vla-rail-server`: Installs model-specific dependencies (e.g., PyTorch, Transformers, etc.).
- **Option B (Quick Validation)**: Use a single Conda environment, suitable for initial quick testing.

---

## 🛠️ Step 1: Installation and Environment Setup

### 1. Clone the Repository

```bash
git clone <repository_url>
cd vla_infer
```

If the code is already on your local machine, navigate directly to the project root directory. All commands below should be executed in the directory containing `pyproject.toml`.

### 2. Create Python Environment and Install the Project

Linux/macOS:

```bash
conda create -n vla-rail-client python=3.10 -y
conda activate vla-rail-client
python -m pip install --upgrade pip
python -m pip install -e .
```

Windows PowerShell:

```powershell
conda create -n vla-rail-client python=3.10 -y
conda activate vla-rail-client
python -m pip install --upgrade pip
python -m pip install -e .
```

If you need to use the compatibility dependency list:

```bash
python -m pip install -r requirements.txt
```

---

## 🌐 Step 2: Start the Web Client (Can Run Independently)

**This step does not require Server or models; it's used to verify the management interface is working.**

Run in the terminal:

```bash
python run_web_client.py
```

Without arguments, the program reads `conf/default_conf.yaml` by default and listens on `0.0.0.0:9000`. To use a custom config file, pass the filename via `--conf`, and place it in the `conf/` directory:

```bash
python run_web_client.py --conf custom_conf.yaml
```

Open your browser and visit `http://localhost:9000`. You should see the VLA-RAIL Web console, client status, and configuration panel; inference results and robot status may be empty until Server is connected and the robot is properly configured.

> **Port Details**:
> - `9000`: Main Web service port (provides REST API and WebSocket via `uvicorn`).
> - `8080` / `8765`: **Visualization auxiliary services** (static resources + data push) automatically started by `VLAClient.run()`; no manual intervention required.
> - On Linux/macOS, `run_web_client.py` attempts to auto-release occupied main Web ports; on Windows, please manually close the occupying process or use a different port.

---

## 🧪 Step 3: Start the Server and Load the Model

The Server is responsible for model inference and does not read from or send commands to robots. Run this in another terminal, within the model-specific environment.

Linux/macOS:

```bash
PYTHONPATH=<model_source_dir>:$PYTHONPATH python run_server.py --model_type <model_type> --model_path <checkpoint_path>
```

Windows PowerShell:

```powershell
$env:PYTHONPATH = "<model_source_dir>;" + $env:PYTHONPATH
python run_server.py --model_type <model_type> --model_path <checkpoint_path>
```

Example (TAO model):

```bash
PYTHONPATH=/path/to/TAO/src:$PYTHONPATH python run_server.py --model_type tao --model_path /path/to/checkpoint
```

> **Model Types**: See the registered model list in `conf/server_conf.py`.  
> **Adding New Models**: Refer to the [Add New VLA Model Guide](guides/add-new-vla-model.md).

---

## 🎬 Step 4: Mock Robot (Optional, for Environments Without a Physical Robot)

> If you have a physical robot, **skip to Step 5**.

The Mock Robot replays historical observations from LeRobot-format datasets, suitable for demonstration and offline debugging.

**Data Format Requirements**:
```text
<dataset_root>/
├── data/chunk-*/episode_*.parquet
├── videos/chunk-*/<video_key>/episode_*.mp4
└── meta/info.json          # Optional, for reading fps
```

**Steps**:
1. In `conf/default_conf.yaml`, fill in `dataset_path` under `robots.mock`.
2. Ensure camera names match the video directory names.
3. In the Web console configuration panel, select **Mock Robot**.
4. Start the client task; you should see observation replay and action responses.

See [Mock Robot Documentation](../client/robots/mock/README.md) for detailed configuration.

---

## 🔧 Step 5: Configure a Physical Robot (Robot Manufacturers)

**Physical robot logic is handled by the Client-side robot adapter; the Server performs inference only and does not call the robot SDK.**

1. Create a new directory and implementation file under `client/robots/`.
2. Inherit the `RobotBase` class from `client/robots/base_robot.py`.
3. Implement the `retrieve_observation()` and `execute_action()` methods.
4. Register the robot type and parameters in `conf/robots_conf.py`.
5. In the Client environment, install the vendor SDK and verify observation/action interfaces independently from the model.
6. Connect to the Server to confirm that inference results and action execution work correctly.

See the [Robot Adaptation Guide](guides/add-new-robot.md) for the complete interface specification.

---

## Next Steps

- [Project Architecture](../README.md#project-architecture): Understand the responsibilities of Client, Server, and the ZMQ communication layer.
- [Configuration Guide](configuration.md): Complete configuration options for Client, Server, robots, and recording.
- [Add New VLA Model Guide](guides/add-new-vla-model.md): Integrate new checkpoints/model implementations.
- [Robot Adaptation Guide](guides/add-new-robot.md): Integrate physical robots.
- [Troubleshooting](troubleshooting.md): Common runtime issues.
- [Mock Robot Documentation](../client/robots/mock/README.md): Configure offline dataset replay.
