# RoboCasa / PandaOmron

`robocasa_pandas` supports RoboCasa evaluation with single tasks, task suites, parallel environments, synchronous or asynchronous inference, action smoothing, video recording, and dataset export. Run the commands below from the project root and replace paths with your local installation paths.

## Environment Setup

This adapter uses **RoboCasa365**.

The model server and simulation client can use separate environments:

- Model environment: install the model and its dependencies, and prepare a checkpoint for RoboCasa.
- Simulation environment: install **RoboCasa365**, robosuite, MuJoCo, and the required assets. See the [RoboCasa installation guide](https://github.com/robocasa/robocasa#installation). This adapter uses RoboCasa365's Gymnasium task interface.

Install this project in the simulation environment:

```bash
uv pip install -e '.[sim]'
```

The `sim` extra provides simulation utilities used by this project; it does not include RoboCasa or the model. Robot defaults are defined in `get_robocasa_pandas_config()` in [conf/robots_conf.py](../../../conf/robots_conf.py).

## Start the Model Server

Start TAO in the model environment:

```bash
python run_server.py \
  --model_type tao \
  --model_path /path/to/checkpoint \
  --embodiment_tag robocasa_pandas_omron
```

The default server port is `5566`. The adapter derives camera mapping and action
order from the TAO embodiment configuration.

For GR00T N1.5:

```bash
python run_server.py \
  --model_type gr00t_n1_5 \
  --model_path /path/to/checkpoint \
  --embodiment_tag robocasa_pandas_omron
```

`--embodiment_tag robocasa_pandas_omron` selects the SDK tag `robocasa_panda_omron`
and GR00T's `panda_omron` data configuration through `conf/simulation.yml`.
The GR00T environment must register both identifiers.
DM05, SmolVLA, and GO1 accept the same shared tag with a compatible checkpoint.
The evaluator also accepts `--embodiment_tag robocasa_pandas_omron`.

## Web Evaluation

Start the Web client:

```bash
python run_web_client.py --port 9000
```

Open `http://localhost:9000/`:

1. In Configuration, select Robot Type `robocasa_pandas`, then set the simulation Python path, GPU, and model server address.
2. Configure action chunk length, execution mode, smoothing, and fusion. A blank action chunk length uses the RoboCasa default of 16.
3. In Simulation Evaluation, select tasks or a task suite, set episodes per task, parallel environments, and video/dataset saving options, then start evaluation.
4. View logs, statistics, and videos in the evaluation panel, or stop and resume existing jobs.

GPU, split, and seed are in Configuration. Camera dimensions, the optional Python path, and the episode step limit are under Advanced. A blank step limit uses the task registry default. Task selection, parallel environment count, and recording options are managed in Simulation Evaluation.

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
| Split | Environment data split: `target` or `pretrain`. |
| Seed | Starting random seed for episodes. |
| Camera Width / Height | Width and height of each camera image, in pixels. |
| Max Episode Steps | Maximum actions per episode; leave blank to use the task default. |

A blank action chunk length defaults to 16. Sampling ratios above 1 increase the number of executed samples. Video FPS does not determine simulation speed.

The trajectory viewer shows arm joints only, in radians. State is measured joint position. With the default OSC controller, Act Fit and Act Raw are joint-angle estimates from fitted and raw Cartesian commands, using damped differential IK from the same pre-step state. These estimates are for visualization, not controller joint targets or predicted motion; they do not change evaluation control. Select the three sources to compare them.

## CLI Evaluation

Run a single task in the simulation environment:

```bash
python scripts/robocasa_eval.py \
  --env_name PickPlaceCounterToCabinet \
  --n_episodes 10 --n_envs 1 \
  --run_id example-run
```

Choose a task supported by your RoboCasa installation. To run a suite, replace `--env_name` with `--task_suite target50`; these options are mutually exclusive.

| Feature | Options |
| --- | --- |
| Model connection | `--server_ip`, `--server_port`; default `127.0.0.1:5566` |
| Evaluation size | `--n_episodes`: total episodes per task; `--n_envs`: parallel environments |
| GPU assignment | `--gpu 0,2` assigns workers in round-robin order; omit to inherit the environment |
| Action chunk length | `--n_action_steps`; default 16 |
| Execution mode | `--mode sync/async`; default `sync` |
| Intra-chunk processing | `--intra_chunk_mode raw/interpolation/fitting`; default `raw` |
| Inter-chunk fusion | `--inter_chunk_mode sync/search_action/smooth_velocity/min_jerk`; default `sync` |
| Dataset saving | Enable with `--record`; set the directory with `--record_dir` |
| Video saving | Enabled by default; `--no_video` disables replay videos; `--video_layout grid/single` sets the layout |
| Rendering backend | `--mujoco_gl egl/osmesa/glfw`, depending on installed dependencies |

For example, `--gpu 0,2 --n_envs 4` assigns four workers to GPUs `0,2,0,2`. A single environment uses the first GPU in the list. Each worker configures its own CUDA and EGL devices.

Replay videos and dataset camera videos are controlled separately. See `python scripts/robocasa_eval.py --help` for additional options.

## Results and Resume

CLI results default to `data/robocasa_eval/`; override this with `--output_dir`. Single-task statistics are saved to `evals/<split>/<task>/stats.json`, and suite summaries to `evals/<split>/suites/<suite>/<run_id>/stats.json`. Set the dataset directory separately with `--record_dir`. Statistics include the actual dataset paths, with separate success and failure partitions.

To resume, keep the original output directory, `run_id`, and evaluation configuration. Use separate output directories for independent experiments to avoid reusing single-task statistics paths. Web jobs are stored under `data/simulation_web/jobs/`; resuming through the panel uses the job's saved configuration snapshot.
