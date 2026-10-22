# Simulation adapters

Keep benchmark-specific code in `client/robots/<robot_type>/`:

- Environment creation, reset, cleanup, and thread ownership.
- Action conversion, state extraction, camera lookup, and success detection.
- Benchmark-specific seed selection, expert checks, and rendering policy.

Reuse these modules when adding a benchmark:

| Module | Responsibility |
| --- | --- |
| `benchmarks.py` | Register robot types, evaluation entry points, dependencies, task catalogs, defaults, and capabilities |
| `robot_runtime.py` | Shared adapter and joint trajectory contract, differential IK estimates, observations, and episode state |
| `video_recorder.py` | Encode RGB display videos and render evaluation metadata |
| `profiling.py` | Aggregate step timings, optional MuJoCo hooks and render-device diagnostics |
| `evaluation.py` | CLI options, GPU assignment, episode lifecycle, statistics, resume and worker supervision |
| `recording_exports.py` | Partition and merge recorded datasets |
| `data_record_manager.py` | Record observations, actions, and LeRobot datasets |
| `preview.py` | Publish camera previews and trajectory history |
| `vla_client.py` | Coordinate observation, model inference, and action execution |
| `io_adapter.py` | Configure model layouts and convert observations/actions on the simulation client |

Pass target camera names and RGB arrays to `build_observation`. Pass source-keyed
RGB frames matching `config.camera.names.values()` to `VideoRecorder.write`.
Keep action indices and observation indices separate; a reset observation has
step zero and no applied action. `EpisodeState` preserves the adapter's supplied
success, termination, and truncation flags without interpreting reward.

Evaluation entry points should import shared helpers directly, without importing
another benchmark's script. The existing RoboCasa and RoboTwin entry points
retain their CLI names and benchmark defaults.

## Adding a Benchmark

1. Implement `SimulationRobot` in `client/robots/<robot_type>/body_robot.py` and add its robot configuration. Keep simulator creation, action mapping, reset, success detection, and cleanup in this adapter. `control_robot` returns `RobotStepResult`; observations use `build_observation`. Return the reset observation once from `retrieve_observation`.
2. Implement the evaluation entry point using `evaluation.build_parser`, `configure_pipeline`, `build_client`, and the existing episode/statistics helpers. Reuse `EvaluationRunner` for supervised and parallel workers. Environment setup, seed selection, and benchmark-specific resume identities remain in this entry point.
3. Register one `BenchmarkSpec` in `benchmarks.py`. Supply its robot type, script, dependencies, task catalog callback, CLI fields, and defaults. The catalog callback receives `(python, settings, project_root)` and returns `tasks` and `suites`; settings include `benchmark_options`. Discovery must not initialize simulators. Optional `validate` and `prepare` callbacks handle benchmark-specific checks.

## Model adaptation

Use `run_server.py` for all registered model types. Both the server and evaluators
accept `--embodiment_tag robotwin_aloha` or `--embodiment_tag robocasa_pandas_omron`.
`conf/simulation.yml` maps these names to IO profiles and model-specific settings.
`model_bridge.py` translates SDK camera/language keys, converts named TAO vectors,
and validates simulation state/action dimensions and finite values. GR00T N1.5
metadata aliases use a temporary checkpoint view; original checkpoints are untouched.
SmolVLA receives the current instruction. No IO descriptions, versions, hashes,
or negotiation fields are added to heartbeats, requests, or responses.

```bash
python run_server.py --model_type dm05 \
  --model_path /path/to/checkpoint --embodiment_tag robotwin_aloha \
  --server_port 5566 --debug

python scripts/aloha_robotwin_eval.py --task_name stack_bowls_three \
  --embodiment_tag robotwin_aloha --server_port 5566 --n_envs 1
```

The server and evaluator select the same layout when given the same tag.
They do not negotiate tags over ZMQ. TAO maps `robotwin_aloha` to its SDK tag
`aloha_robotwin`; `robocasa_pandas_omron` resolves to `robocasa_pandas`. Evaluators
also accept the existing names and aliases. Without a tag, configured defaults remain.

| Model adapter | RoboTwin | RoboCasa |
| --- | --- | --- |
| TAO | Registered SDK embodiment | Registered SDK embodiment |
| DM05, SmolVLA, GO1 | Compatible checkpoint required | Compatible checkpoint required |
| GR00T N1.5 | Explicit SDK data configuration required | Registered `panda_omron` configuration |
| Other registered models | Explicit adaptation required | Explicit adaptation required |

Unknown model/embodiment combinations fail before loading weights. Several existing
adapters use fixed A2D slices, action widths, or kinematics; accepting a shared flag
does not convert those adapters to a different robot. Add a compatible implementation
before registering it under `embodiments.<name>.models`. For OpenPI, register the
actual external training `config` name; do not infer it from the simulation name.
DM05 keeps its checkpoint's robot, dataset, normalization, and action-mode contract
unless explicit model settings are registered. Repository paths, dependencies,
backend settings, and execution horizons remain model-specific.

Adapted models use the same output layout for the selected benchmark.
`conf/simulation.yml` contains Web defaults (`defaults`, `platforms`) and named
model layouts (`io_profiles`). The `robotwin_aloha` profile defines RoboTwin's
14D joint action layout; `robocasa` defines RoboCasa's 12D action layout.
Input state retains the environment's native layout unless explicitly configured.
Robot configuration selects the default automatically; no
`--io_profile` argument is needed for these layouts. Model names do not select
action order. RDT still defaults to two observation frames; other models
use the evaluator's history setting.

Profiles describe the **final server output**. The model is expected to follow
the selected benchmark's layout and semantics; incompatible widths stop
evaluation. RoboCasa's model action order is base motion, control mode, end
effector position, end effector rotation, and gripper. The client reorders it
into the simulator's native action order before execution.

For a different layout, override the default on the evaluator:

```bash
python scripts/aloha_robotwin_eval.py --task_name <task> --io_profile /path/to/layout.yml
```

Use `--io_profile conf/simulation.yml#<name>` to select a named profile.
The `dual_arm_7dof_grippers` profile is a generic example, not a benchmark default.
Standalone layout YAML files remain supported. New benchmarks select their
default through the robot configuration's `io_profile`; explicit evaluator
profiles take precedence over the tag's layout on the evaluator. TAO uses SDK
slice order internally and converts named fields to the selected profile;
GR00T N1.5 uses its data configuration's action key order. Keep those settings consistent
with the common benchmark layout.
Web jobs use `vla_zmq.embodiment_tag` or the evaluation API's `embodiment_tag` field.
The selected tag must match the job platform. `vla_zmq.io_profile` and the API's
`io_profile` field remain available for explicit layout overrides.
The server accepts `--embodiment_tag` and `--server_port`; it does not accept
`--io_profile`. GR00T N1.5 resolves its data configuration through
`embodiments` settings for simulation tags. Other GR00T N1.5 SDK tags retain
`conf/embodiments_conf.py`'s `GR00T_DATA_CONFIG_BY_EMBODIMENT`: `a2d` selects `a2d_arms_only`;
unmapped SDK tags use the same identifier for embodiment and data configuration.

Benchmarks declare `state_layout` separately from `config.action_layout`, with
contiguous `start`/`end` slices. `SimulationRobot.describe_io()` reads these layouts;
`io_schema` can add units and semantics. RoboCasa discovers state widths from
observations. Single-value `left_hand`/`right_hand` fields are treated as grippers.

Profiles support `state`, `action`, `history_frames`, optional `action_dt` in
seconds, and `camera_mapping` from wire roles to environment roles. `state_mapping`
and `action_mapping` map target fields to `{source, scale, offset}` entries.
`environment` can override the benchmark layout. Field metadata `unit`, `kind`,
`frame`, and `rotation` must agree unless an explicit conversion handles them.
SDK camera names come from the server's embodiment/data configuration,
independently of client camera roles.

Nonlinear conversions use `register_io_converter(name, converter)` and the profile's
`converter` field. Stateless `encode(observation, context)` and
`decode(actions, context)` methods receive the native request state in
`context['state']`. Conversion runs before stale-action trimming and smoothing;
recordings retain native environment vectors. Invalid dimensions or nonfinite
values stop evaluation. Model `not_ready` responses retry without executing actions.

The web API and both evaluation pages discover registered benchmarks through
`/api/simulation/benchmarks`; their platform branches do not need editing.
Additional CLI fields can use `benchmark_options` and must be allowed by the
registration's `cli_fields`. Include them in `client_fields` to read their values
from the selected robot's configuration snapshot. Existing standard fields retain
their validation and cannot be overridden through `benchmark_options`.

For example, after implementing `newbench_catalog` and `scripts/newbench_eval.py`:

```python
register_benchmark(BenchmarkSpec(
    id='newbench', robot_type='new_robot', label='New benchmark',
    script='newbench_eval.py', dependencies=('numpy', 'newbench'),
    catalog=newbench_catalog,
    cli_fields=COMMON_CLI_FIELDS | {'scene_path'},
    client_fields=COMMON_CLIENT_FIELDS + ('scene_path',),
))
```

The common `build_client(config, robot, transport)` assembles action smoothing,
chunk fusion, inference, recording, previews, and execution for every adapter.
The caller owns the robot and transport and must close them after the client.

## Joint Trajectories

Adapters implement `joint_state()` to return labels and measured positions, and
`joint_action(action)` to return joint targets or visualization estimates. The
shared `get_joint_trajectory` builds State, Act Fit, and Act Raw with identical
joint dimensions and finite-value validation. Policy state and action dimensions
may differ from the number of displayed joints.

Declare `joint_action_semantics` as `joint_targets` for direct position targets
or `estimated_joint_angles` for estimates. RoboTwin uses its qpos targets;
RoboCasa uses a `DampedJointProjection` snapshot captured before the simulation
step. Fitted and raw commands must use the same snapshot. The projection never
writes controller goals or simulator state. Return `None` when a joint action
cannot be provided; never substitute measured positions for missing targets.

The camera preview and web viewer consume the same trajectory format for all
benchmarks. A joint layout change starts a new preview stream and clears old
samples. Simulator thread ownership and coordinate/action conversions remain
the adapter's responsibility.
