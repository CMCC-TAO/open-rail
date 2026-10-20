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
