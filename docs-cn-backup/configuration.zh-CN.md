# 配置参数字典

[English Version](configuration.md)

## 配置来源与优先级

| 启动入口 | 配置加载顺序 |
| --- | --- |
| `run_web_client.py` | `conf/client_conf.py` 默认值 → `--conf` 指定的 YAML（默认 `conf/default_conf.yaml`）→ 运行时 load/patch 请求 |
| `run_server.py` | `conf/server_conf.py` 默认值 → 命令行参数覆盖 |

Web 客户端加载 YAML 时仅会更新已存在的叶子参数，未知字段会被忽略。因此应按本文字段维护 `default_conf.yaml`。`conf/user_conf_example.py` 展示了 `--user_conf` 可使用的嵌套字典格式。

除非表格中特别注明，本文的时间单位均为毫秒。

## 客户端根参数字典

`get_client_config()` 包含以下一级分组：

| 字段 | 说明 |
| --- | --- |
| `rdm` | 实时观测缓存与推理循环模式。 |
| `intra_chunk` | 单个模型动作块内部的处理。 |
| `inter_chunk` | 相邻两个动作块之间的衔接。 |
| `controller` | 机器人命令时序与执行速度。 |
| `robots` | 机器人适配器选择及其专有参数。 |
| `vla_zmq` | VLA 推理服务连接与心跳。 |
| `visualize` | 可视化 WebSocket 服务及显示初始状态。 |
| `record` | 示教、评估与 LeRobot 数据集记录。 |
| `vision` | 观测帧选择和图像预处理。 |
| `language` | 语言任务文件及自动子任务切换。 |

### `rdm`：实时数据管理器

| 字段 | 类型 / 可选值 | 含义 |
| --- | --- | --- |
| `mode` | `async` 或 `sync` | 推理与控制循环模式。`async` 不会为每次推理结果阻塞；`sync` 使用同步处理。 |
| `max_len` | 正整数 | 观测缓存可保留的最大帧数。 |
| `observe_fps_window_size` | 正整数 | 用于估算观测 FPS 的最近采集帧数量。 |

### `intra_chunk`：块内动作处理

| 字段 | 类型 / 可选值 | 含义 |
| --- | --- | --- |
| `intra_chunk_mode` | `raw`、`interpolation` 或 `fitting` | 动作输出方式：直接使用原始动作、插值或多项式拟合。 |
| `filter_window_size` | 非负整数 | 夹爪动作滤波半窗口，实际窗口长度为 $2n+1$。 |
| `min_gripper_action_threshold` | 数值 | 小于此阈值的夹爪动作视为完全打开（`0.0`）。 |
| `max_gripper_action_threshold` | 数值 | 大于此阈值的夹爪动作视为完全闭合（`1.0`）。 |
| `fitting_num_samples` | 正整数 | 预留的轨迹采样参数；当前实现实际使用由控制周期生成的时间网格。 |
| `fitting_deg` | 非负整数 | 轨迹拟合的多项式阶数。 |
| `max_joint_fitting_workers` | 正整数 | 预留的工作线程参数；当前批量实现不会创建关节拟合执行器。 |
| `max_gripper_fitting_workers` | 正整数 | 预留的工作线程参数；当前批量实现不会创建夹爪拟合执行器。 |
| `max_head_fitting_workers` | 正整数 | 预留的工作线程参数；当前批量实现不会创建头部拟合执行器。 |
| `joint_dim` | 非负整数 | 本阶段处理的双臂动作维度数。 |
| `gripper_dim` | 非负整数 | 本阶段处理的夹爪动作维度数。 |
| `head_dim` | 非负整数 | 本阶段处理的头部动作维度数。 |

上述维度必须与所选机器人动作布局及模型输出约定一致。

### `inter_chunk`：块间融合

| 字段 | 类型 / 可选值 | 含义 |
| --- | --- | --- |
| `inter_chunk_mode` | `search_action`、`smooth_velocity`、`min_jerk` 或 `sync` | 连接相邻动作块的方法。 |
| `search_action.search_length` | 正整数 | 为选取平滑衔接点向后搜索的动作数量。机器人在块边界停顿时可适当增大。 |
| `smooth_velocity.max_vel` | 正数 | 速度平滑模式的速度上限。 |
| `smooth_velocity.max_acc` | 正数 | 速度平滑模式的加速度上限。 |
| `smooth_velocity.kp` | 数值 | 速度平滑使用的比例增益。 |
| `smooth_velocity.kd` | 数值 | 速度平滑使用的微分增益。 |
| `min_jerk.blend_threshold` | 数值 | 控制何时启用最小加加速度融合的阈值。 |
| `min_jerk.adaptive_factor` | 数值 | 最小加加速度融合的自适应缩放系数；负值保留实现中的自动行为。 |
| `sync` | 映射 | `sync` 模式预留配置，目前为空。 |

### `controller`：机器人命令时序

| 字段 | 类型 / 单位 | 含义 |
| --- | --- | --- |
| `wait_time` | 数值，ms | 下一次推理/控制迭代前的等待时间。命令生成导致明显迟滞时可增大。 |
| `period` | 数值，ms | 控制定时器和轨迹时间轴使用的机器人命令周期。 |
| `speed` | 正数 | 相对于遥操作速度的执行速度。 |
| `raw_fps` | 正数，Hz | VLA/WAM 训练数据集 FPS，作为时序基准。 |
| `gripper_offset` | 整数，帧 | 对步进式夹爪命令施加的前移偏移。夹爪反应偏慢时可增大正值。 |

### `vision`：观测预处理

| 字段 | 类型 / 可选值 | 含义 |
| --- | --- | --- |
| `history_frame` | 布尔值 | 模型输入支持时，除当前帧外再使用一帧历史观测。 |
| `preprocess.method` | 字符串 | 从 `client.utils.misc` 动态解析的预处理函数名；`none` 表示关闭预处理。 |
| `preprocess.keep_ratio` | 布尔值 | 缩放时是否保持原始宽高比。 |
| `preprocess.height` | 正整数，像素 | 预处理后的目标图像高度。 |
| `preprocess.width` | 正整数，像素 | 预处理后的目标图像宽度。 |

### `language`：语言任务选择

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `file_path` | 相对 `conf/` 的路径 | JSON 任务指令文件，通常为 `language_cmd.json`。 |
| `task_id` | 字符串 | 语言 JSON 中的任务键。不存在时会回退到第一个可用任务。 |
| `sub_task_id` | 从零开始的整数 | 所选任务中当前指令的索引。索引无效时回退为 `0`。 |
| `auto_mode` | 布尔值 | 是否根据任务进度输出自动切换到下一条语言指令。 |
| `task_progress_threshold` | 数值 | 自动切换所需的平均任务进度概率阈值。 |
| `task_progress_win_size` | 正整数 | 计算平均任务进度的滑动窗口长度。 |

`language_cmd.json` 是 `任务 ID → 有序指令字符串数组` 的映射。添加任务时应添加一组指令数组，不应在此文件中混入其他配置元数据。

### `vla_zmq`：VLA 服务连接

| 字段 | 类型 / 单位 | 含义 |
| --- | --- | --- |
| `ip` | 主机名或 IP 地址 | VLA 推理服务地址。 |
| `port` | 字符串或整数 | VLA 服务 TCP 端口，与 `ip` 共同组成 `tcp://ip:port`。 |
| `infer_timeout` | 正整数，ms | 等待一次推理响应的客户端接收超时；超时后迟到响应可能被丢弃。 |
| `heartbeat_interval` | 正整数，ms | 客户端心跳发送周期。 |
| `heartbeat_timeout` | 正整数，ms | 服务端将客户端判定为失联并清理前的无活动时长。 |

### `visualize`：可视化服务

| 字段 | 类型 / 单位 | 含义 |
| --- | --- | --- |
| `host` | 主机/IP | 可视化 WebSocket 服务的监听地址。 |
| `port` | 整数 | 可视化服务端口。 |
| `max_size` | 整数，字节 | 可接收的最大 WebSocket 消息大小。 |
| `ping_interval` | 数值，秒 | WebSocket Ping 间隔。 |
| `ping_timeout` | 数值，秒 | 等待 Ping 响应的最长时间。 |
| `updata_fps` | 正数，Hz | 可视化更新频率；字段拼写为兼容性原因保留。 |
| `camera.open_head` | 布尔值 | 是否显示头部相机。 |
| `camera.open_wrist_left` | 布尔值 | 是否显示左腕相机。 |
| `camera.open_wrist_right` | 布尔值 | 是否显示右腕相机。 |
| `trajectory.play` | 布尔值 | UI 是否自动开始播放轨迹。 |
| `trajectory.source` | 字符串数组 | UI 显示的轨迹序列，例如 `State`、`ActionRaw`、`ActionFitted`。 |
| `trajectory.selected_joints` | 整数数组 | 初始选中的状态/动作维度。 |
| `trajectory.window_span_sec` | 正数，秒 | 轨迹图显示的时间范围。 |

### `record`：记录与 LeRobot 元数据

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `switch` | 布尔值 | 记录总开关，从客户端配置读取；当前 `run_web_client.py` 入口没有 `--record` 参数。 |
| `auto` | 布尔值 | 是否启用自动记录行为。 |
| `save_dir` | 相对项目根目录的路径 | 记录数据的根目录。 |
| `is_record_episode` | 运行时布尔值 | 是否正在记录 episode。 |
| `is_record_eval_log` | 运行时布尔值 | 是否正在记录评估日志。 |
| `is_record_expe_data` | 运行时布尔值 | 是否正在记录实验数据。 |
| `save_raw` | 布尔值 | 是否保存源分辨率图像而非缩放图像。 |
| `evaluation.scores` | 数值数组 | 评估 UI 提供的评分选项。 |
| `lerobot.codebase_version` | 字符串 | 写入元数据的数据集/代码版本。 |
| `lerobot.robot_type` | 字符串 | 写入元数据的机器人类型。 |
| `lerobot.total_episodes`、`total_frames`、`total_tasks`、`total_videos`、`total_chunks` | 非负整数 | LeRobot 元数据维护的数据集计数。 |
| `lerobot.chunks_size` | 正整数 | 记录器格式中一个存储块包含的 episode/帧数量。 |
| `lerobot.fps` | 正数，Hz | 数据集帧率。 |
| `lerobot.state_shape`、`action_shape` | 正整数 | 写入数据集的扁平状态、动作维度。 |
| `lerobot.splits` | 映射 | 数据集划分定义，例如 `{valid: "0:100"}`。 |
| `lerobot.data_path` | 模板字符串 | 相对于记录根目录的 Parquet 路径模板。 |
| `lerobot.video_path` | 模板字符串 | 相对于记录根目录的视频路径模板。 |
| `lerobot.cam.head`、`cam.hand_left`、`cam.hand_right` | 映射 | 单个相机特征定义：包含 `shape.height`、`shape.width`、`shape.channel` 和 `encode.codec`、`encode.is_depth_map`、`encode.has_audio`。 |

支持的视频编码器包括 `mp4v`、`avc1`、`XVID` 和 `MJPG`。相机尺寸必须与所选机器人管线实际写出的帧一致。

## `robots`：机器人适配器

`robots.type` 可选择 `a2d`、`mock`、`ti5_t170c` 或 `navi_wa2`。运行时通常只需要配置当前选用适配器的子段。

### 通用动作布局约定

`action_layout` 将扁平动作向量切分为命名区间。每个区间包含 `start`（含）、`end`（不含）和 `policy`。

| `policy` | 含义 |
| --- | --- |
| `gradual` | 连续维度，通常为手臂关节，适合平滑或拟合。 |
| `stepwise` | 离散或近似离散维度，通常为夹爪/灵巧手。 |
| `manual` | 不由模型推理、由机器人或 Web 端控制的维度；应排在模型控制区间之后。 |

存在 `presets` 时，它提供 UI 复位和手动控制目标。`Default` 与 `Custom` 是通用预设；A2D 夹爪还包括 `Open` 与 `Close`。

### `robots.a2d`

| 字段 | 含义 |
| --- | --- |
| `hand_type` | 末端类型：`gripper`、`hand_as_gripper` 或 `hand`，会影响相机名称和本体状态布局。 |
| `camera.ref` | 参考相机名称。 |
| `camera.names` | 规范名称（`head`、`hand_left`、`hand_right`）到机器人相机标识的映射。 |
| `proprio_names` | 拼接机器人状态时使用的有序本体状态组。 |
| `gripper_freq`、`head_freq` | 夹爪、头部控制命令频率。 |
| `manual_arm_interval` | 手动生成手臂目标之间的时间间隔，单位为秒。 |
| `action_layout` | A2D 手臂、夹爪、头部、腰部和底盘动作范围及 UI 预设。 |

### `robots.mock`

| 字段 | 含义 |
| --- | --- |
| `camera.ref`、`camera.names` | 参考相机及到数据集观测键的映射。 |
| `action_layout` | 仿真手臂、夹爪的动作范围和预设。 |
| `manual_arm_interval` | 手动手臂命令间隔，单位为秒。 |
| `state_action_range` | 从 mock 数据集提取状态/动作字段时使用的区间。 |
| `dataset_path` | LeRobot 风格数据集根目录，必须包含可匹配的 Parquet 数据和视频目录。 |

### `robots.ti5_t170c`

| 字段 | 含义 |
| --- | --- |
| `camera.*_camera_topic` | 头部和手部相机的 ROS 图像话题。 |
| `arms.*_joint_cmd_topic`、`arms.*_joint_states_topic` | 双臂 ROS 命令/状态话题。 |
| `arms.*_arm_joint_names` | 双臂各七个关节的有序名称。 |
| `hands.*_hand_joint_cmd_topic`、`hands.*_hand_joint_states_topic` | 双手 ROS 命令/状态话题。 |
| `hands.hand_joint_names` | 六个手部关节的有序名称。 |
| `waist.*`、`head.*` | 腰部和头部的 ROS 命令/状态话题及有序关节名称。 |
| `reset_robot_pos` | 机器人完整复位目标向量，顺序必须与桥接实现一致。 |
| `zero_pos` | 机器人完整零位/参考目标向量，顺序必须与桥接实现一致。 |
| `action_layout` | 手臂与多指夹爪的动作范围。 |

### `robots.navi_wa2`

| 字段 | 含义 |
| --- | --- |
| `tt` | 舵机/控制周期，单位为秒。 |
| `gain` | 舵机增益。 |
| `camera.topic_dict` | 以 `head`、`hand_left`、`hand_right` 为键的压缩 ROS 图像话题。 |
| `action_layout` | 连续手臂与步进式手部动作范围。 |
| `reset_position` | 完整复位姿态向量，顺序必须与 NAVIAI-WA2 驱动一致。 |

## 服务端与模型参数字典

`get_vla_server_config()` 提供 `zmq`、`max_infer_workers`、`max_decode_workers` 和 `models`。

| 字段 | 含义 |
| --- | --- |
| `zmq` | 与 `vla_zmq` 相同的 VLA 网络字段；服务端使用其中端口绑定 ROUTER socket。 |
| `max_infer_workers` | 最大并发推理工作线程数。设为 `1` 可禁用并发推理。 |
| `max_decode_workers` | 最大图像解码工作线程数。 |
| `models.type` | 选用模型：`mock`、`act`、`gr00t_n1`、`gr00t_n1_5`、`gr00t_n1_6`、`rdt`、`smolvla`、`go1`、`pi0`、`pi05` 或 `tao`。 |

各模型子段参数如下：

| 模型子段 | 字段 | 含义 |
| --- | --- | --- |
| `models.mock` | `model_path` | Mock 模型路径占位参数。 |
| `models.act` | `model_path` | ACT 权重路径。 |
| `models.gr00t` | `model_path`、`embodiment_tag`、`data_config_key` | GR00T 权重及受支持的具身类型、数据配置标识。 |
| `models.rdt` | `model_path`、`config_path`、`vision_encoder_name_or_path`、`lang_embd_path` | RDT 权重、模型配置、视觉编码器和语言嵌入路径。 |
| `models.smolvla` | `model_path`、`root_path` | SmolVLA 权重及关联数据/根路径。 |
| `models.go1` | `model_path`、`exp_path`、`data_stats_path` | GO1 权重、可导入的实验路径和归一化统计 JSON。 |
| `models.pi0`、`models.pi05` | `config`、`model_path`、`is_hand` | OpenPI 模型配置与权重；`is_hand` 启用灵巧手动作处理。 |
| `models.tao` | `model_path`、`embodiment_tag` | TAO 权重与 TAO 注册表中的具身类型标识。 |

所有路径必须在推理服务所在主机有效。`embodiment_tag` 与 `data_config_key` 是模型库注册标识，不可随意填写，应使用对应模型安装环境已注册的值。

## 可视化 ZMQ 参数

`get_vis_zmq_config()` 用于独立的可视化 ZMQ 服务。

| 字段 | 含义 |
| --- | --- |
| `client_ip`、`client_port` | 可视化客户端使用的连接地址。 |
| `server_ip`、`server_port` | 可视化服务端的绑定地址；`*` 表示绑定全部网络接口。 |

## 日志配置

`conf/logging_conf.py` 是程序化日志配置，而非 YAML 参数字典。它会将带时间戳的日志写入 `logs/`，把前一天及更早的日志归档到日期目录，并删除七天前的日期目录。控制台日志默认级别为 `INFO`，文件日志默认级别为 `DEBUG`。新增启动入口时应调用 `setup_logging(log_filename, logger_name)`。
