# Troubleshooting

[中文版本](troubleshooting.zh-CN.md)

## Web client

### The web client does not start

- Make sure the terminal is in the project root containing `pyproject.toml`.
- Activate the intended Python/Conda environment and run `python -m pip install -e .`.
- The default command is:

	```bash
	python run_web_client.py
	```

- The default configuration is `conf/default_conf.yaml`. Put custom configuration files under `conf/` and select one with `--conf custom_conf.yaml`.

### The port is occupied or the browser cannot connect

- The default Web port is `9000`; use `--port 9001` to select another port.
- On Linux/macOS, the launcher attempts to release the main Web port. On Windows, close the process manually or use another port.
- For remote access, use `--host 0.0.0.0` and check firewall rules and network reachability.
- Ports `8080` and `8765` are used by the visualization services and should also be checked if visualization does not connect.

## Server and model

### The page opens but Server status is empty

The Client and Server are separate processes. Check:

- The Server is running without model dependency or checkpoint errors.
- The Client and Server use matching ZMQ addresses and ports.
- `--model_type` is one of the types supported by `run_server.py`.
- In a multi-machine deployment, the Server port is reachable from the Client.

### Model loading fails

- Confirm that `--model_path` points to the correct checkpoint directory.
- Install the model dependencies in the Server environment. GR00T, RDT, OpenPI, and TAO may require additional source code and CUDA/PyTorch dependencies.
- `--model_type mock` does not load a real checkpoint and only produces random actions. It validates the service and transport path, not model quality.

## Mock robot and dataset

### Mock playback cannot find Parquet or video files

- `robots.mock.dataset_path` must point to the dataset root, not its `data/` subdirectory or a single episode file.
- Confirm that `data/chunk-*/episode_*.parquet` exists.
- Confirm that every configured camera has a matching `videos/chunk-*/<video_key>/episode_*.mp4` file.
- Video directory names must match the values in `robots.mock.camera.names` from `conf/robots_conf.py`.
- Parquet and video files must use matching chunk and episode numbers.

### The Mock robot starts but produces no observations

- Confirm that the Parquet file can be read by `pandas.read_parquet()` and that `pyarrow` is installed.
- Confirm that OpenCV can open the videos and that the files are complete.
- `meta/info.json` is optional; without it, playback defaults to 30 FPS.
- Mock `execute_action()` does not move physical hardware. Returned actions only validate the control path.

## Robot integration

### Real robot control is unavailable

- Use a Mock dataset to validate the Client, Server, and transport path before checking vendor SDKs, ROS topics/nodes, camera streams, and robot networking.
- Confirm that the robot type, camera configuration, and `action_layout` are registered correctly in `conf/robots_conf.py`.
- A robot adapter should implement `retrieve_observation()` and `execute_action()`; the Server must not call robot SDKs directly.

## Data recording

### Data recording is enabled, but the recording shows zero

If **Runtime Monitor Control** is not selected while **Data Recording Lerobot** is enabled, recording may start but the recorded result can show zero. The **Control** option must be selected for LeRobot data to be recorded.