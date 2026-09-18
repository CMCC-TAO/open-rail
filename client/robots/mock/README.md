# Mock Robot

## Overview

The Mock Robot is a simulation implementation that uses LeRobot datasets to provide realistic robot observation data without requiring actual hardware. This is particularly useful for development, testing, and demonstration purposes.

## Usage

Start the Server：

```bash
conda activate gr00t
python run_server.py --model_type gr00t_n1_5 --model_path /mnt/models/pnp_bottle/checkpoint-60000
```

Start the Client：

```bash
conda activate gr00t
python run_client.py --robots_type mock
```

**Note：** If LeRobot is not installed, the library will generate fake random observation data and send it to the server for inference.

### Configuration

The mock robot is configured through the `conf/robots_conf.yaml` file.
# Mock Robot

The Mock Robot replays camera frames and robot state from an existing LeRobot-format dataset. It does not require physical robot hardware, but it does require a valid local dataset. It is intended for client, transport, and integration testing.

## Dataset layout

Set `robots.mock.dataset_path` to the dataset root. The implementation searches for Parquet files and then opens the configured camera videos for the same chunk and episode:

```text
<dataset_root>/
├── data/chunk-000/episode_000000.parquet
├── videos/chunk-000/observation.images.head_rgb/episode_000000.mp4
├── videos/chunk-000/observation.images.left_wrist_rgb/episode_000000.mp4
├── videos/chunk-000/observation.images.right_wrist_rgb/episode_000000.mp4
└── meta/info.json                 # optional; provides playback fps
```

The video directory names must match the values in `robots.mock.camera.names` in `conf/robots_conf.py`. The Parquet file and all configured videos must use the same chunk and episode numbers.

## Configuration

The default Mock configuration is defined by `get_mock_config()` in `conf/robots_conf.py`. Set the dataset path in the client configuration used by the Web client:

```yaml
robots:
	mock:
		dataset_path: /path/to/your/dataset
```

On Windows, use a YAML path such as `D:/data/my_dataset` or quote a path containing backslashes. A missing or empty path raises `mock.dataset_path is empty`; a missing Parquet file or video produces a corresponding file-not-found error.

## Run

1. Start a Server. `--model_type mock` is enough to test the transport and returns random actions; a real model requires its own checkpoint and model environment.
2. Start the Web client with the configuration containing the Mock dataset:

	 ```bash
	 python run_web_client.py --conf default_conf.yaml
	 ```

3. Select the Mock robot in the client configuration and start a task.

The Mock robot reads video frames sequentially, returns the state/action columns selected by `state_action_range`, and loops to the next episode when the current episode ends. `execute_action()` does not move physical hardware.
