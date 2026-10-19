# RoboTwin / Aloha

`robotwin_aloha` 用于 RoboTwin 的 Aloha 双臂仿真测评，支持单任务、任务列表、并行环境、同步／异步推理、动作平滑、视频与数据集保存。以下命令均在本项目根目录执行，路径按实际安装位置替换。

## 环境配置

模型服务和仿真客户端可以使用独立环境：

- 模型环境：安装 TAO 及其依赖，准备 `aloha_robotwin` 对应的 checkpoint。
- 仿真环境：安装 RoboTwin、SAPIEN、PyTorch、cuRobo 和任务资源，安装方式见 [RoboTwin 安装说明](https://robotwin-platform.github.io/doc/usage/robotwin-install.html)。

在仿真环境中安装本项目：

```bash
uv pip install -e '.[sim]'
```

`sim` 扩展提供本项目使用的仿真辅助依赖，不包含 RoboTwin 和模型本身。`--robotwin_root` 指向 RoboTwin 根目录；任务配置从 `task_config/<配置名>.yml` 加载，当前支持 `embodiment: [aloha-agilex]`。

机器人默认配置位于 [conf/robots_conf.py](../../../conf/robots_conf.py) 的 `get_robotwin_aloha_config()`。

## 启动模型服务

在模型环境中启动：

```bash
python run_server.py \
  --model_type tao \
  --model_path /path/to/checkpoint \
  --embodiment_tag aloha_robotwin \
  --action_keys left_arm left_hand right_arm right_hand
```

默认服务端口为 `5566`。三路相机默认使用 `cam_top_head`、`cam_left_wrist`、`cam_right_wrist`，无需传入 `--video_keys`。

动作按左臂 6 维、左夹爪、右臂 6 维、右夹爪排列，共 14 维绝对 qpos。上述命令对应 `left_hand/right_hand` 动作字段；模型输出为 `left_gripper/right_gripper` 时，可省略 `--action_keys`，由适配器自动排序。

## Web 测评

启动 Web 客户端：

```bash
python run_web_client.py --port 9000
```

打开 `http://localhost:9000/`：

1. 在 Configuration 中选择 Robot Type `robotwin_aloha`，填写仿真环境的 Python 路径、RoboTwin 根目录、GPU 和模型服务地址。
2. 设置并行环境数、任务配置、指令类型、同步／异步模式和动作处理方式。动作块长度留空时使用 RoboTwin 默认值 50。
3. 在 Simulation Evaluation 中选择任务或任务集，设置每任务 episode 数、视频和数据集保存选项，启动测评。
4. 在测评面板查看日志、统计和视频，或停止、续跑已有任务。

测评使用启动时的配置快照，后续修改配置不会影响正在运行的任务。公共页面操作与配置文件说明见 [Web 仿真测评](../../../docs/robocasa_web.md)。

## CLI 测评

在仿真环境中运行单任务：

```bash
python scripts/aloha_robotwin_eval.py \
  --robotwin_root /path/to/RoboTwin \
  --task_name stack_bowls_three --task_config demo_clean \
  --n_episodes 10 --n_envs 1 \
  --run_id example-run
```

任务名与任务配置按所用 RoboTwin 环境选择。任务列表使用 `--tasks task_a,task_b` 或 `--tasks /path/to/tasks.yml`，与 `--task_name` 二选一。YAML 支持任务名列表或 `tasks: [...]`。

| 功能 | 参数 |
| --- | --- |
| 模型连接 | `--server_ip`、`--server_port`，默认 `127.0.0.1:5566` |
| 测评规模 | `--n_episodes` 为每任务总 episode 数；`--n_envs` 为并行环境数 |
| GPU 分配 | `--gpu 0` 指定仿真 GPU；多个编号如 `--gpu 0,1` 按 worker 分配 |
| 动作块长度 | `--n_action_steps`，默认 50 |
| 同步／异步 | `--mode sync/async`，默认 `sync` |
| 块内处理 | `--intra_chunk_mode raw/interpolation/fitting`，默认 `raw` |
| 块间衔接 | `--inter_chunk_mode sync/search_action/smooth_velocity/min_jerk`，默认 `sync` |
| 指令类型 | `--instruction_type seen/unseen`，默认 `unseen` |
| 观测渲染 | `--render_observation_mode chunk_boundary/per_action`，同步默认在动作块边界采集图像，异步逐动作采集 |
| 数据集保存 | `--record` 开启；`--record_dir` 设置目录 |
| 视频保存 | 默认开启；`--no_video` 关闭展示视频，数据集相机视频由录制开关控制 |

默认执行专家检查并生成指令。使用固定指令时，传入 `--no_expert_check --instruction '任务指令'`。其他参数见 `python scripts/aloha_robotwin_eval.py --help`。

## 结果与续跑

CLI 默认结果位于 `data/aloha_robotwin_eval/evals/<seen或unseen>/<task>/<run_id>/`，包含统计、视频和 episode 选种清单。`--output_dir` 修改结果根目录，`--record_dir` 单独指定数据集目录；统计文件记录实际数据集路径，并提供成功、失败分区。

续跑使用原输出目录、`run_id` 和测评配置，复用已保存的 seed、指令和 episode 进度。更改测评配置时使用新的 `run_id`。Web 任务统一保存在 `data/simulation_web/jobs/`，通过面板续跑时使用该任务的配置快照。
