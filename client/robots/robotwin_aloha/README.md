# RoboTwin / Aloha

`robotwin_aloha` supports RoboTwin evaluation for the Aloha bimanual robot, including single tasks, task lists, parallel environments, synchronous or asynchronous inference, action smoothing, video recording, and dataset export. Run the commands below from the project root and replace paths with your local installation paths.

## Environment Setup

This adapter uses **RoboTwin 2.0**.

The model server and simulation client can use separate environments:

- Model environment: install TAO and its dependencies, and prepare a checkpoint for `aloha_robotwin`.
- Simulation environment: install **RoboTwin 2.0**, SAPIEN, PyTorch, cuRobo, and the required task assets. See the [RoboTwin installation guide](https://robotwin-platform.github.io/doc/usage/robotwin-install.html).

Install this project in the simulation environment:

```bash
uv pip install -e '.[sim]'
```

The `sim` extra provides simulation utilities used by this project; it does not include RoboTwin or the model. `--robotwin_root` points to the RoboTwin root directory. Task configurations are loaded from `task_config/<name>.yml`; the current adapter supports `embodiment: [aloha-agilex]`.

Robot defaults are defined in `get_robotwin_aloha_config()` in [conf/robots_conf.py](../../../conf/robots_conf.py).

## Start the Model Server

Start the server in the model environment:

```bash
python run_server.py \
  --model_type tao \
  --model_path /path/to/checkpoint \
  --embodiment_tag robotwin_aloha
```

The shared tag resolves to TAO's `aloha_robotwin` SDK name. DM05, SmolVLA, and
GO1 accept the same shared tag with a compatible checkpoint; model-specific
dependencies and paths must be configured separately. The evaluator also accepts
`--embodiment_tag robotwin_aloha` to select the matching IO profile.

The default server port is `5566`. Camera names come from the TAO embodiment
configuration, in head, left wrist, and right wrist order.

Actions contain 14 absolute qpos values in this order: six left-arm joints,
left gripper, six right-arm joints, and right gripper. The adapter derives
action field order from the embodiment's action slice indices.

## Web Evaluation

Start the Web client:

```bash
python run_web_client.py --port 9000
```

Open `http://localhost:9000/`:

1. In Configuration, select Robot Type `robotwin_aloha`, then set the simulation Python path, RoboTwin root directory, GPU, and model server address.
2. Configure the task configuration, instruction type, execution mode, and action processing. A blank action chunk length uses the RoboTwin default of 50.
3. In Simulation Evaluation, select tasks or a task suite, set episodes per task, parallel environments, and video/dataset saving options, then start evaluation.
4. View logs, statistics, and videos in the evaluation panel, or stop and resume existing jobs.

Evaluation captures the configuration at startup; later edits do not affect a running job. See the [Web simulation guide](../../../docs/simulation_evalution.md) for shared page controls and configuration files.

### Web Parameters

| Parameter | Description |
| --- | --- |
| Python | Simulation Python interpreter path; it can use a separate environment from the model server. |
| GPU | Simulation GPU indices, such as `0,1`; does not change the model server's GPU. |
| Model Server Address | IP and port of the running model server. |
| Task / Task Selection | Select a single task or tasks from a suite. |
| Episodes / Task | Total evaluation episodes per task. |
| Parallel Envs | Number of concurrent environments; episodes are distributed among them. |
| Action Chunk Length | Number of actions executed per chunk; shorter chunks request inference more often. |
| Execution Mode | `sync` requests inference after a chunk finishes; `async` requests the next chunk in advance. |
| Intra-chunk Smoothing | `raw` keeps original actions; `interpolation` interpolates; `fitting` fits a polynomial. |
| Output Sampling Ratio | Action output sampling multiplier; 1 preserves the action count. |
| Inter-chunk Fusion | How action chunks connect; `sync` joins directly, while other modes search or smooth the transition. |
| Async Replenishment Threshold | Number of remaining actions that triggers the next inference request in async mode. |
| Maximum Observation Lag Steps | Maximum allowed observation lag in async mode, measured in steps. |
| Save Dataset | Save a LeRobot dataset. |
| Save Videos | Save evaluation replay videos, independently of dataset saving. |
| Video FPS / Layout | Playback frame rate and layout; `grid` shows multiple views, while `single` shows one view. |
| RoboTwin Root | Root directory of the RoboTwin installation. |
| Task Configuration | Task configuration, such as `demo_clean` or `demo_randomized`. |
| Instruction Type | Language instruction split: `seen` or `unseen`. |
| Seed | Starting seed for episode candidates. |
| Camera Rendering | `chunk_boundary` captures images at action chunk boundaries; `per_action` captures after every action. Async mode always captures after every action. |

A blank action chunk length defaults to 50. Only interpolation mode allows sampling ratios above 1. Video FPS does not determine simulation speed.

## CLI Evaluation

Run a single task in the simulation environment:

```bash
python scripts/robotwin_eval.py \
  --robotwin_root /path/to/RoboTwin \
  --task_name stack_bowls_three --task_config demo_clean \
  --n_episodes 10 --n_envs 1 \
  --run_id example-run
```

Choose tasks and task configurations supported by your RoboTwin installation. Use `--tasks task_a,task_b` or `--tasks /path/to/tasks.yml` for a task list; this option is mutually exclusive with `--task_name`. YAML accepts a list of task names or `tasks: [...]`.

| Feature | Options |
| --- | --- |
| Model connection | `--server_ip`, `--server_port`; default `127.0.0.1:5566` |
| Evaluation size | `--n_episodes`: total episodes per task; `--n_envs`: parallel environments |
| GPU assignment | `--gpu 0` selects the simulation GPU; lists such as `--gpu 0,1` distribute workers across GPUs |
| Action chunk length | `--n_action_steps`; default 50 |
| Execution mode | `--mode sync/async`; default `sync` |
| Intra-chunk processing | `--intra_chunk_mode raw/interpolation/fitting`; default `raw` |
| Inter-chunk fusion | `--inter_chunk_mode sync/search_action/smooth_velocity/min_jerk`; default `sync` |
| Instruction type | `--instruction_type seen/unseen`; default `unseen` |
| Observation rendering | `--render_observation_mode chunk_boundary/per_action`; sync defaults to chunk boundaries, while async captures after every action |
| Dataset saving | Enable with `--record`; set the directory with `--record_dir` |
| Video saving | Enabled by default; `--no_video` disables replay videos; dataset camera videos are controlled by the dataset recording switch |

Expert checks and instruction generation are enabled by default. To use a fixed instruction, pass `--no_expert_check --instruction 'task instruction'`. See `python scripts/robotwin_eval.py --help` for additional options.

## Results and Resume

CLI results default to `data/aloha_robotwin_eval/evals/<seen-or-unseen>/<task>/<run_id>/`, including statistics, videos, and episode seed selections. Override the result root with `--output_dir`, and set the dataset directory separately with `--record_dir`. Statistics include the actual dataset paths, with separate success and failure partitions.

To resume, keep the original output directory, `run_id`, and evaluation configuration. Saved seeds, instructions, and episode progress are reused. Use a new `run_id` when changing the evaluation configuration. Web jobs are stored under `data/simulation_web/jobs/`; resuming through the panel uses the job's saved configuration snapshot.
