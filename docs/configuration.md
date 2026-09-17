---
title: "Configuration Reference"
description: "Configuration sources, precedence, and reference tables for VLA-RAIL."
---

# Configuration Reference


## Configuration sources and precedence

| Entry point | Configuration load order |
| --- | --- |
| `run_web_client.py` | `conf/client_conf.py` defaults → `--conf` YAML file (default: `conf/default_conf.yaml`) → runtime load/patch requests |
| `run_server.py` | `conf/server_conf.py` defaults → command-line overrides |

Only existing leaf keys are updated when a Web-client YAML file is loaded; unknown keys are ignored. Keep `default_conf.yaml` synchronized with the fields below. `conf/user_conf_example.py` shows the nested dictionary format accepted by `--user_conf`.

All durations in the following tables are milliseconds unless another unit is shown explicitly.

## Client root dictionary

`get_client_config()` contains these top-level sections:

| Key | Description |
| --- | --- |
| `rdm` | Real-time observation buffering and inference-loop mode. |
| `intra_chunk` | Processing of actions within one model-generated action chunk. |
| `inter_chunk` | Fusion of the previous and next action chunks. |
| `controller` | Robot-command timing and execution speed. |
| `robots` | Selected robot adapter and adapter-specific settings. |
| `vla_zmq` | VLA inference-server connection and heartbeat settings. |
| `visualize` | WebSocket visualization server and display defaults. |
| `record` | Demonstration, evaluation, and LeRobot dataset recording. |
| `vision` | Observation-frame selection and preprocessing. |
| `language` | Language-task file and automatic subtask switching. |

### `rdm`: real-time data manager

| Key | Type / valid values | Meaning |
| --- | --- | --- |
| `mode` | `async` or `sync` | Inference/control loop mode. `async` avoids blocking on every inference result; `sync` waits for synchronized processing. |
| `max_len` | positive integer | Maximum number of observation frames retained in the buffer. |
| `observe_fps_window_size` | positive integer | Number of most recent captured frames used when estimating observation FPS. |

### `intra_chunk`: action processing inside a chunk

| Key | Type / valid values | Meaning |
| --- | --- | --- |
| `intra_chunk_mode` | `raw`, `interpolation`, or `fitting` | Action output mode: use raw actions, interpolate them, or use polynomial fitting. |
| `filter_window_size` | non-negative integer | Half-window used to filter gripper actions; the effective window is $2n+1$. |
| `min_gripper_action_threshold` | number | Gripper values below this threshold are treated as fully open (`0.0`). |
| `max_gripper_action_threshold` | number | Gripper values above this threshold are treated as fully closed (`1.0`). |
| `fitting_num_samples` | positive integer | Reserved trajectory-sampling setting; the current implementation uses the controller-period time grid instead. |
| `fitting_deg` | non-negative integer | Polynomial degree for fitted trajectories. |
| `max_joint_fitting_workers` | positive integer | Reserved worker setting; the current batch implementation does not create a joint-fitting executor. |
| `max_gripper_fitting_workers` | positive integer | Reserved worker setting; the current batch implementation does not create a gripper-fitting executor. |
| `max_head_fitting_workers` | positive integer | Reserved worker setting; the current batch implementation does not create a head-fitting executor. |
| `joint_dim` | non-negative integer | Number of dual-arm action dimensions processed by this stage. |
| `gripper_dim` | non-negative integer | Number of gripper action dimensions processed by this stage. |
| `head_dim` | non-negative integer | Number of head action dimensions processed by this stage. |

These dimensions must match the selected robot's action layout and the model output convention.

### `inter_chunk`: fusion between chunks

| Key | Type / valid values | Meaning |
| --- | --- | --- |
| `inter_chunk_mode` | `search_action`, `smooth_velocity`, `min_jerk`, or `sync` | Method used to join consecutive action chunks. |
| `search_action.search_length` | positive integer | Number of future actions inspected while choosing a smooth join. Increase it if the robot visibly pauses at chunk boundaries. |
| `smooth_velocity.max_vel` | positive number | Velocity limit for velocity-smoothing fusion. |
| `smooth_velocity.max_acc` | positive number | Acceleration limit for velocity-smoothing fusion. |
| `smooth_velocity.kp` | number | Proportional gain used by velocity smoothing. |
| `smooth_velocity.kd` | number | Derivative gain used by velocity smoothing. |
| `min_jerk.blend_threshold` | number | Threshold controlling when minimum-jerk blending is applied. |
| `min_jerk.adaptive_factor` | number | Adaptive scaling factor for minimum-jerk blending. A negative value keeps the implementation's automatic behavior. |
| `sync` | mapping | Reserved configuration section for `sync` mode; currently empty. |

### `controller`: robot command timing

| Key | Type / unit | Meaning |
| --- | --- | --- |
| `wait_time` | number, ms | Delay before the next inference/control iteration. Increase it when command generation causes visible hesitation. |
| `period` | number, ms | Robot command period used by the control timer and trajectory timing. |
| `speed` | positive number | Execution speed relative to teleoperation speed. |
| `raw_fps` | positive number, Hz | Dataset FPS used to train the VLA/WAM model; used as the timing baseline. |
| `gripper_offset` | integer, frames | Forward offset for stepwise gripper commands relative to arm commands. Increase a positive value if the gripper reacts too late. |

### `vision`: observation preprocessing

| Key | Type / valid values | Meaning |
| --- | --- | --- |
| `history_frame` | boolean | Include a historical observation frame in addition to the current frame when the model input supports it. |
| `preprocess.method` | string | Name of the preprocessing function resolved from `client.utils.misc`; `none` disables preprocessing. |
| `preprocess.keep_ratio` | boolean | Preserve aspect ratio while resizing. |
| `preprocess.height` | positive integer, pixels | Target image height for preprocessing. |
| `preprocess.width` | positive integer, pixels | Target image width for preprocessing. |

### `language`: task instruction selection

| Key | Type | Meaning |
| --- | --- | --- |
| `file_path` | path relative to `conf/` | JSON task-instruction file, normally `language_cmd.json`. |
| `task_id` | string | Task key in the language JSON file. If absent, the first available task is used. |
| `sub_task_id` | zero-based integer | Index of the active instruction in the selected task. Invalid indices fall back to `0`. |
| `auto_mode` | boolean | Automatically move to the next language instruction according to task-progress output. |
| `task_progress_threshold` | number | Mean progress probability required before automatic switching. |
| `task_progress_win_size` | positive integer | Sliding-window length used to average task progress. |

`language_cmd.json` is a mapping from task IDs to ordered arrays of instruction strings. Add a task by adding one such array; do not store configuration metadata in this file.

### `vla_zmq`: VLA server connection

| Key | Type / unit | Meaning |
| --- | --- | --- |
| `ip` | host name or IP address | VLA server address. |
| `port` | string or integer | VLA server TCP port; together with `ip` forms `tcp://ip:port`. |
| `infer_timeout` | positive integer, ms | Client receive timeout for one inference response. A timeout may drop a late response. |
| `heartbeat_interval` | positive integer, ms | Client heartbeat period. |
| `heartbeat_timeout` | positive integer, ms | Server-side inactivity time before a client is removed. |

### `visualize`: visualization service

| Key | Type / unit | Meaning |
| --- | --- | --- |
| `host` | host/IP | Interface on which the visualization WebSocket service listens. |
| `port` | integer | Visualization service port. |
| `max_size` | integer, bytes | Largest accepted WebSocket message. |
| `ping_interval` | number, seconds | WebSocket ping interval. |
| `ping_timeout` | number, seconds | Time allowed for a ping response. |
| `updata_fps` | positive number, Hz | Visualization update rate. The key name is retained for compatibility. |
| `camera.open_head` | boolean | Show the head camera. |
| `camera.open_wrist_left` | boolean | Show the left wrist camera. |
| `camera.open_wrist_right` | boolean | Show the right wrist camera. |
| `trajectory.play` | boolean | Start trajectory playback automatically in the UI. |
| `trajectory.source` | string array | Trajectory series displayed in the UI, such as `State`, `ActionRaw`, and `ActionFitted`. |
| `trajectory.selected_joints` | integer array | Initially selected action/state dimensions. |
| `trajectory.window_span_sec` | positive number, seconds | Time range displayed by the trajectory plot. |

### `record`: recording and LeRobot metadata

| Key | Type | Meaning |
| --- | --- | --- |
| `switch` | boolean | Master recording switch. It is read from the client configuration; the current `run_web_client.py` entry point has no `--record` option. |
| `auto` | boolean | Enable automatic recording behavior. |
| `save_dir` | project-relative path | Root directory for recorded data. |
| `is_record_episode` | runtime boolean | Whether episode recording is active. |
| `is_record_eval_log` | runtime boolean | Whether evaluation-log recording is active. |
| `is_record_expe_data` | runtime boolean | Whether experiment-data recording is active. |
| `save_raw` | boolean | Save source-resolution images rather than resized images. |
| `evaluation.scores` | numeric array | Score choices offered by the evaluation UI. |
| `lerobot.codebase_version` | string | Dataset/codebase version recorded in metadata. |
| `lerobot.robot_type` | string | Robot type recorded in metadata. |
| `lerobot.total_episodes`, `total_frames`, `total_tasks`, `total_videos`, `total_chunks` | non-negative integer | Dataset counters maintained in LeRobot metadata. |
| `lerobot.chunks_size` | positive integer | Number of episodes/frames represented by a storage chunk according to the recorder format. |
| `lerobot.fps` | positive number, Hz | Dataset frame rate. |
| `lerobot.state_shape`, `action_shape` | positive integer | Flattened state and action dimensions written to the dataset. |
| `lerobot.splits` | mapping | Dataset split definitions, for example `{valid: "0:100"}`. |
| `lerobot.data_path` | template string | Parquet path template relative to the recording root. |
| `lerobot.video_path` | template string | Video path template relative to the recording root. |
| `lerobot.cam.head`, `cam.hand_left`, `cam.hand_right` | mapping | Per-camera feature definition. Each has `shape.height`, `shape.width`, `shape.channel`, plus `encode.codec`, `encode.is_depth_map`, and `encode.has_audio`. |

Supported video codecs include `mp4v`, `avc1`, `XVID`, and `MJPG`. Camera shapes must describe the frames actually written by the selected robot pipeline.

## `robots`: robot adapters

`robots.type` selects `a2d`, `mock`, `ti5_t170c`, or `navi_wa2`. Configure only the subsection for the selected adapter unless preparing reusable profiles.

### Shared action-layout convention

An `action_layout` section divides a flat action vector into named segments. Every segment has `start` (inclusive), `end` (exclusive), and `policy`.

| Policy | Meaning |
| --- | --- |
| `gradual` | Continuous dimensions, normally arm joints; suitable for smoothing/fitting. |
| `stepwise` | Discrete or near-discrete dimensions, normally grippers/hands. |
| `manual` | Robot/Web-controlled dimensions that are not inferred by the model. Place these after model-controlled segments. |

Where available, `presets` provides UI reset/manual targets. `Default` and `Custom` are general presets; A2D grippers also provide `Open` and `Close`.

### `robots.a2d`

| Key | Meaning |
| --- | --- |
| `hand_type` | End-effector mode: `gripper`, `hand_as_gripper`, or `hand`. It selects camera names and proprioception layout. |
| `camera.ref` | Reference camera name. |
| `camera.names` | Mapping from canonical names (`head`, `hand_left`, `hand_right`) to robot camera identifiers. |
| `proprio_names` | Ordered proprioception groups used to assemble robot state. |
| `gripper_freq`, `head_freq` | Command frequencies for gripper and head control. |
| `manual_arm_interval` | Time interval in seconds between manually generated arm targets. |
| `action_layout` | A2D arm, gripper, head, waist, and wheel action ranges and UI presets. |

### `robots.mock`

| Key | Meaning |
| --- | --- |
| `camera.ref`, `camera.names` | Reference camera and mapping to dataset observation keys. |
| `action_layout` | Simulated arm and gripper action ranges and presets. |
| `manual_arm_interval` | Manual arm command interval in seconds. |
| `state_action_range` | Ranges used to select state/action fields from the mock dataset. |
| `dataset_path` | LeRobot-style dataset root. It must contain matching Parquet data and video directories. |

### `robots.ti5_t170c`

| Key | Meaning |
| --- | --- |
| `camera.*_camera_topic` | ROS image topics for the head and hand cameras. |
| `arms.*_joint_cmd_topic`, `arms.*_joint_states_topic` | ROS command/state topics for both arms. |
| `arms.*_arm_joint_names` | Ordered seven-joint names for each arm. |
| `hands.*_hand_joint_cmd_topic`, `hands.*_hand_joint_states_topic` | ROS command/state topics for both hands. |
| `hands.hand_joint_names` | Ordered six-joint hand names. |
| `waist.*`, `head.*` | ROS command/state topics and ordered joint names for waist and head. |
| `reset_robot_pos` | Full robot reset target vector; its ordering must match the bridge implementation. |
| `zero_pos` | Full robot zero/reference target vector; ordering must match the bridge implementation. |
| `action_layout` | Arm and multi-finger gripper action ranges. |

### `robots.navi_wa2`

| Key | Meaning |
| --- | --- |
| `tt` | Servo/control period in seconds. |
| `gain` | Servo gain. |
| `camera.topic_dict` | Compressed ROS image topics keyed by `head`, `hand_left`, and `hand_right`. |
| `action_layout` | Continuous arm and stepwise hand action ranges. |
| `reset_position` | Full reset pose vector; ordering must match the Navi WA2 driver. |

## Server and model dictionary

`get_vla_server_config()` provides `zmq`, `max_infer_workers`, `max_decode_workers`, and `models`.

| Key | Meaning |
| --- | --- |
| `zmq` | Same VLA network fields as `vla_zmq`; the server binds its ROUTER socket using the configured port. |
| `max_infer_workers` | Maximum concurrent inference workers. Set to `1` to disable concurrent inference. |
| `max_decode_workers` | Maximum image-decoding workers. |
| `models.type` | Selected model: `mock`, `act`, `gr00t_n1`, `gr00t_n1_5`, `gr00t_n1_6`, `rdt`, `smolvla`, `go1`, `pi0`, `pi05`, or `tao`. |

Model-specific keys are as follows:

| Model section | Keys | Meaning |
| --- | --- | --- |
| `models.mock` | `model_path` | Mock-model path placeholder. |
| `models.act` | `model_path` | ACT checkpoint path. |
| `models.gr00t` | `model_path`, `embodiment_tag`, `data_config_key` | GR00T checkpoint plus supported embodiment and data-configuration identifiers. |
| `models.rdt` | `model_path`, `config_path`, `vision_encoder_name_or_path`, `lang_embd_path` | RDT checkpoint, model configuration, vision encoder, and language embedding paths. |
| `models.smolvla` | `model_path`, `root_path` | SmolVLA checkpoint and associated data/root path. |
| `models.go1` | `model_path`, `exp_path`, `data_stats_path` | GO1 checkpoint, importable experiment path, and normalization statistics JSON. |
| `models.pi0`, `models.pi05` | `config`, `model_path`, `is_hand` | OpenPI model configuration/checkpoint; `is_hand` enables hand-action handling. |
| `models.tao` | `model_path`, `embodiment_tag` | TAO checkpoint and a TAO-registry embodiment identifier. |

Paths must be valid on the inference-server host. `embodiment_tag` and `data_config_key` are model-library identifiers, not arbitrary labels; use values registered by the matching model installation.

## Visualization ZMQ configuration

`get_vis_zmq_config()` is used by the standalone visualization ZMQ service.

| Key | Meaning |
| --- | --- |
| `client_ip`, `client_port` | Address used by a visualization client. |
| `server_ip`, `server_port` | Bind address used by the visualization server; `*` binds all interfaces. |

## Logging configuration

`conf/logging_conf.py` is programmatic logging configuration rather than a YAML parameter dictionary. It writes timestamped files below `logs/`, moves prior-day files into date directories, and removes date directories older than seven days. Console logging defaults to `INFO`; file logging defaults to `DEBUG`. Use `setup_logging(log_filename, logger_name)` when adding an entry point.
