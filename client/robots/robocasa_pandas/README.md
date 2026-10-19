# RoboCasa / PandaOmron

`robocasa_pandas` 用于 RoboCasa 仿真测评，支持单任务、任务集、并行环境、同步／异步推理、动作平滑、视频与数据集保存。以下命令均在本项目根目录执行，路径按实际安装位置替换。

## 环境配置

模型服务和仿真客户端可以使用独立环境：

- 模型环境：安装所用模型及其依赖，准备 RoboCasa 对应的 checkpoint。
- 仿真环境：安装 RoboCasa、robosuite、MuJoCo 和所需资源，安装方式见 [RoboCasa 安装说明](https://github.com/robocasa/robocasa#installation)。当前适配器使用 RoboCasa 的 Gymnasium 任务接口。

在仿真环境中安装本项目：

```bash
uv pip install -e '.[sim]'
```

`sim` 扩展提供本项目使用的仿真辅助依赖，不包含 RoboCasa 和模型本身。机器人默认配置位于 [conf/robots_conf.py](../../../conf/robots_conf.py) 的 `get_robocasa_pandas_config()`。

## 启动模型服务

在模型环境中启动 TAO：

```bash
python run_server.py \
  --model_type tao \
  --model_path /path/to/checkpoint \
  --embodiment_tag robocasa_panda_omron
```

默认服务端口为 `5566`。相机映射和动作顺序由适配器处理，无需传入 `--video_keys` 和 `--action_keys`。

使用 GR00T N1.5 时：

```bash
python run_server.py \
  --model_type gr00t_n1_5 \
  --model_path /path/to/checkpoint \
  --data_config_key panda_omron \
  --embodiment_tag robocasa_panda_omron
```

GR00T 环境需包含对应的 `panda_omron` 数据配置。

## Web 测评

启动 Web 客户端：

```bash
python run_web_client.py --port 9000
```

打开 `http://localhost:9000/`：

1. 在 Configuration 中选择 Robot Type `robocasa_pandas`，设置仿真环境的 Python 路径、GPU、并行环境数和模型服务地址。
2. 设置动作块长度、同步／异步模式、块内平滑和块间衔接方式。动作块长度留空时使用 RoboCasa 默认值 16。
3. 在 Simulation Evaluation 中选择任务或任务集，设置每任务 episode 数、视频和数据集保存选项，启动测评。
4. 在测评面板查看日志、统计和视频，或停止、续跑已有任务。

测评使用启动时的配置快照，后续修改配置不会影响正在运行的任务。公共页面操作与配置文件说明见 [Web 仿真测评](../../../docs/robocasa_web.md)。

## CLI 测评

在仿真环境中运行单任务：

```bash
python scripts/robocasa_eval.py \
  --env_name PickPlaceCounterToCabinet \
  --n_episodes 10 --n_envs 1 \
  --run_id example-run
```

任务名按所用 RoboCasa 环境选择。运行任务集时，将 `--env_name` 替换为 `--task_suite target50`，两者二选一。

| 功能 | 参数 |
| --- | --- |
| 模型连接 | `--server_ip`、`--server_port`，默认 `127.0.0.1:5566` |
| 测评规模 | `--n_episodes` 为每任务总 episode 数；`--n_envs` 为并行环境数 |
| 动作块长度 | `--n_action_steps`，默认 16 |
| 同步／异步 | `--mode sync/async`，默认 `sync` |
| 块内处理 | `--intra_chunk_mode raw/interpolation/fitting`，默认 `raw` |
| 块间衔接 | `--inter_chunk_mode sync/search_action/smooth_velocity/min_jerk`，默认 `sync` |
| 数据集保存 | `--record` 开启；`--record_dir` 设置目录 |
| 视频保存 | 默认开启；`--no_video` 关闭展示视频，`--video_layout grid/single` 设置布局 |
| 渲染后端 | `--mujoco_gl egl/osmesa/glfw`，按已安装环境选择 |

展示视频与数据集相机视频分别控制。其他参数见 `python scripts/robocasa_eval.py --help`。

## 结果与续跑

CLI 默认结果目录为 `data/robocasa_eval/`，可用 `--output_dir` 修改；单任务统计位于 `evals/<split>/<task>/stats.json`，任务集汇总位于 `evals/<split>/suites/<suite>/<run_id>/stats.json`。数据集保存位置由 `--record_dir` 单独指定，统计文件中记录实际路径，并提供成功、失败分区。

续跑保留原输出目录、`run_id` 和测评配置。独立实验使用不同输出目录，避免复用单任务统计路径。Web 任务统一保存在 `data/simulation_web/jobs/`，通过面板续跑时使用该任务的配置快照。
