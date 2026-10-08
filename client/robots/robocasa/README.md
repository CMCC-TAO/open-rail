# RoboCasa evaluation

RoboCasa uses the standard `VLAClientAsync` observation, inference, action-chunk, ZMQ, recording, and visualization components. Benchmark mode executes every raw model action exactly once and waits for the post-step observation before requesting the next chunk.

Install the local RoboCasa checkout in the client environment, then start a compatible model server.

GR00T N1.5:

```bash
python run_server.py \
  --model_type gr00t_n1_5 \
  --model_path /path/to/checkpoint \
  --data_config_key panda_omron \
  --embodiment_tag robocasa_panda_omron
```

TAO:

```bash
python run_server.py \
  --model_type tao \
  --model_path /path/to/checkpoint \
  --embodiment_tag robocasa_panda_omron \
  --action_keys end_effector_position end_effector_rotation gripper_close base_motion control_mode
```

Run evaluation:

```bash
python scripts/robocasa_eval.py \
  --env_name PickPlaceCounterToCabinet \
  --split target \
  --n_episodes 50 \
  --n_envs 10 \
  --n_action_steps 16 \
  --output_dir data/robocasa_eval
```

Use `--mujoco_gl egl` on a compatible GPU node or `--mujoco_gl osmesa` when OSMesa is installed. Results are saved under `OUTPUT/evals/SPLIT/TASK/`.

`--n_envs` runs that many isolated RoboCasa clients concurrently against the same model server. Each worker owns its environment and seed range. With `--record`, the supervisor merges all workers for one task into one LeRobot recording root, then creates the global `success/` and `failure/` partitions.

Run all Target50 tasks sequentially:

```bash
python scripts/robocasa_eval.py \
  --task_suite target50 \
  --split target \
  --n_episodes 50 \
  --n_envs 10 \
  --n_action_steps 16 \
  --output_dir data/robocasa_eval
```

Per-task results use the same task directories. The suite summary is saved under
`OUTPUT/evals/target/suites/target50/RUN_ID/stats.json`.

The merged master uses `client/core/vla_client.py` for the Web and real-robot client. RoboCasa keeps its step-aware `VLAClientAsync` and transactional recorder under `client/simulation/`, sharing the current core action buffer, smoother, fuser, image utilities, and ZMQ transport. The former `client.core.vla_client.VLAClientAsync` import remains available.

Install auxiliary simulation dependencies with `pip install -e ".[sim]"`; the local RoboCasa checkout and assets are installed separately. The retained ZMQ configuration uses port `1117`, while this evaluation CLI defaults to `5566`; pass `--server_port 1117` when using the retained server configuration.
