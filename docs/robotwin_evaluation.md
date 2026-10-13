# RoboTwin 仿真测评

RoboTwin/Aloha 接入 `client/simulation`，与 RoboCasa 共用同步／异步客户端、录制管理器、worker 调度和数据集导出。支持 `raw`、`interpolation`、`fitting`；不接入 `local`。

## 环境与模型

在 RoboTwin 已安装的 Python 环境中安装本项目及视频依赖：

```bash
uv pip install -e '.[sim]'
```

RoboTwin、SAPIEN、cuRobo、机器人资源和任务资源按 RoboTwin 自身的安装说明准备。本项目不自动安装或修改它们。

模型推理服务单独启动。模型应输出 14 维绝对 qpos，顺序为左臂 6 维、左夹爪、右臂 6 维、右夹爪。使用与 checkpoint 一致的相机、状态和动作字段。TAO 支持通过 `video_keys` 配置三路相机名称；当输出字段为 `left_arm`、`left_gripper`、`right_arm`、`right_gripper` 时，会自动按该顺序拼接动作。其他字段名可通过 `--action_keys` 显式指定顺序。

TAO 服务可以显式设置相机名称；下面的字段名须替换为 checkpoint 的实际名称：

```bash
python run_server.py --model_type tao --model_path /path/to/checkpoint \
  --embodiment_tag YOUR_TAG --server_port 5566 \
  --video_keys head_camera left_camera right_camera
```

## CLI

```bash
python scripts/aloha_robotwin_eval.py \
  --robotwin_root /data/users/huangkai/project/rail_robotwin/RoboTwin \
  --task_name stack_bowls_three --task_config demo_clean \
  --server_ip 127.0.0.1 --server_port 5566 \
  --n_episodes 50 --n_envs 1 --n_action_steps 50 \
  --mode sync --intra_chunk_mode raw --inter_chunk_mode sync \
  --record --record_dir data/aloha_robotwin_eval/lerobot \
  --run_id 20261009-run1
```

`--gpu 0` 设置仿真 worker 的可见 GPU；并行时 `--gpu 0,1` 按 worker 编号轮流分配 GPU。模型服务的 GPU 由其自身环境决定。异步模式使用 `--mode async`，可设置 `--async_replenish_threshold` 和 `--max_async_observation_lag_steps`。`--max_transition_steps` 限制块间处理范围，默认 5。

`fitting` 保留输入动作数量和时间戳；`interpolation` 使用 `--intra_chunk_sample_ratio` 调整动作数量，兼容 `--interpolation_sample_ratio`。夹爪维度不参与连续平滑。改变采样倍率会改变动作执行次数，比较成功率时需保持实验参数一致。

同步模式默认使用 `--render_observation_mode chunk_boundary`：三种平滑方式均只在初始观测、处理后的 action chunk 结束和 episode 提前结束时采集相机图像。中间动作保留物理步进、关节状态和成功判定，并跳过动作内部的渲染更新。前一块的结束观测作为下一块的初始观测。视频和数据集相机观测也只在这些边界更新。需要中间画面时选择 `per_action`；异步模式始终逐动作采集。Web 首页对应 `robots.aloha_robotwin.render_observation_mode`，独立测评页在 Advanced Settings 中提供相同选项。

任务列表使用 `--tasks task_a,task_b`，也可提供 YAML 文件，内容为列表或 `tasks: [...]`。它与 `--task_name` 二选一。`--env_name` 和 `--task_suite` 为兼容别名。

默认专家检查生成 `seen/unseen` 指令。跳过专家检查时必须提供固定指令：

```bash
python scripts/aloha_robotwin_eval.py \
  --robotwin_root /path/to/RoboTwin --task_name stack_bowls_three \
  --no_expert_check --instruction 'Stack the three bowls' \
  --server_port 5566 --run_id manual-run
```

## 保存与续测

统计、视频及 episode 选种清单位于：

```text
data/aloha_robotwin_eval/evals/<seen或unseen>/<task>/<run_id>/
```

每个 episode 的种子搜索从 `seed + episode × seed_stride` 开始，默认间隔 100；最大尝试次数不能超过间隔。这样并行环境不会因跳过无效 seed 而使用重叠的种子范围。实际 seed 和指令在执行前保存，中断后复用该清单。这与源脚本连续递增 seed 的序列不同，比较旧实验时需核对实际 seed。

默认使用独立 worker；`--worker_episodes` 控制每次 worker 完成的 episode 数量。重复使用原命令及相同 `run_id` 会恢复已保存进度。影响测评的配置发生变化会拒绝续测，应使用新 `run_id`。

`--record` 输出 LeRobot 数据集，结束时导出 `success`、`failure` 分区；并行 worker 的数据集按全局 episode 编号合并。数据集路径写入统计文件。测评视频与数据集相机视频分别保存，`--no_video` 只关闭测评展示视频。

专家选种有尝试次数和时间限制；隔离 worker 的监督进程可以终止卡住的环境准备或 episode。`--no_process_isolation` 下无法强制终止卡住的原生环境调用，也不支持并行环境。断连等待上限由 `--server_reconnect_timeout` 控制，0 表示持续重试。

## Web

```bash
python run_web_client.py --port 9000
```

访问 `/simulation`，选择 `robotwin`，填写安装了 RoboTwin 的 Python 可执行文件、RoboTwin 根目录、任务与模型服务地址。页面支持启动、停止、续跑、日志、统计和保存视频回放。历史目录沿用 `data/robocasa_web/jobs/`，原 RoboCasa 任务继续可用。

自动化验证使用模拟 RoboTwin 环境与模型传输，并实际写入 Parquet 和视频；真实 SAPIEN 渲染、GPU 并行资源需求及 checkpoint 成功率需要在对应环境中验证。
