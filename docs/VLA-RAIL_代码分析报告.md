# VLA-RAIL（open-rail）代码分析报告

- 分析对象：`/home/bruce/Projects/18.VLA/open-rail`，当前分支 `lw_ti5_adapt`（已合并 master，HEAD `42eff01`）
- 分析日期：2026-09-16
- 范围：Python 主体约 1.87 万行（client / server / conf / web_client / extra / robots / models）。前端 JS/CSS 和 ACT 的 DETR 第三方代码只做了浏览，没有逐行审查。
- 标注说明：**【已验证】** 表示在沙箱里跑过最小复现；**【需确认】** 表示依赖训练数据或 SDK 行为，需要结合实际环境判断。其余结论均来自代码阅读，并附了文件和行号。

---

## 1. 项目定位

VLA-RAIL 是 VLA（视觉-语言-动作）模型与真实机器人之间的**实时异步推理链路**，对应论文 arXiv:2512.24673。

它不训练模型，核心解决三件事：

1. **异步推理**：机器人按 30Hz 观测、按约 266Hz 控制；模型推理慢（100ms 量级），推理结果以动作块（action chunk）形式返回。
2. **块内平滑**（Intra-chunk）：把 30Hz 的稀疏动作拟合、插值成 3.75ms 步长的稠密轨迹。
3. **块间衔接**（Inter-chunk）：新块到达时，从机器人当前状态平滑过渡到新块，并补偿推理延迟。

已支持的机器人：A2D（夹爪/灵巧手）、Ti5 T170C（26 自由度，当前分支的适配目标）、Navi WA2、Mock。
已支持的模型：ACT、GR00T N1/N1.5/N1.6、RDT、SmolVLA、GO1、π0/π0.5、TAO、Mock。

---

## 2. 架构与数据流

### 2.1 进程与线程

```
┌──────────────── 客户端进程（run_client.py 或 run_web_client.py）────────────────┐
│                                                                                  │
│  observe 线程 ──► 本地 SHM 环形缓冲(30) ──► process_observe 线程                  │
│    │ RobotProxy.retrieve_observation()          │ JPEG 编码(3线程) + 组包         │
│    │                                            ├─► RealtimeDataManager.observe_buffer
│    │                                            ├─► VisualizeServer (WS :8765)   │
│    │                                            └─► DataRecordManager ──► 写盘子进程(fork)
│    │                                                                             │
│  inference 线程: pop 最新观测 → ZMQ DEALER → 等待响应(500ms)                      │
│     → IntraChunkSmoother(拟合/插值) → InterChunkFuser(min_jerk 等)               │
│     → RDM.update_action_chunk_fitted()                                           │
│                                                                                  │
│  control 定时线程(3.75ms): RDM.get_action_fitted() 索引+1 → RobotProxy.control_robot()
│                                                                                  │
│  Web 端(FastAPI :9000, 仅 web 模式): REST + /ws，启停、手动控制、录制、配置        │
└────────┬─────────────────────────────────────────────────────────────────────────┘
         │ mp.Queue(命令/状态) + SharedMemory(图像, ring=4)
┌────────▼────────── 机器人 worker 子进程(spawn) ──────────┐
│ 循环: drain 命令队列 → RobotBody.retrieve_observation()  │
│       → 写 SHM → 推送 obs 队列(maxsize=2)                │
│ RobotBody = a2d / ti5_t170c / navi_wa2 / mock + 厂商 SDK │
└──────────────────────────────────────────────────────────┘
         ▲ ZMQ ROUTER :5566（pickle + JSON 元数据，外加独立心跳 DEALER）
┌────────┴──────────────── 服务端进程（run_server.py）─────────────────────────────┐
│ recv 线程 → 图像解码池(9) → pad 到 640×640 → 推理池(3) → model.infer()          │
│ → sender 线程 → ROUTER.send                                                      │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 一次推理的数据流与时间戳

1. 机器人给出 `ref_timestamp`（相机时间）和 `obs.state`；客户端在组包时打上 `loc_timestamp = perf_counter()`。
2. 服务端原样回传 `ref_timestamp` 和 `loc_timestamp`，`pred_action` 形状为 `(T, D)`，可选 `ext.prob_progress`。
3. 客户端生成时间轴 `t_i = i × observe_period`（`observe_period = 1/speed/raw_fps`），并把第 0 帧置为 0（`realtime_data_manager.py:217`）。
4. 块内平滑：`gradual` 段做 4 阶多项式最小二乘拟合，`stepwise` 段（夹爪）做滑窗均值加阈值吸附，重采样到 3.75ms 网格。
5. 延迟补偿：`time_offset = now − loc_timestamp`，然后跳到新块中第一个晚于该偏移的采样点（`get_start_chunk_index`）。
6. 块间融合：默认 `min_jerk`，用五次多项式从当前 (x, v, a) 过渡到新块，尾段再与原轨迹线性混合。
7. 控制线程每个 tick 让 `action_chunk_index + 1`，并下发该列动作。

### 2.3 关键设计亮点

- **机器人 SDK 放进独立子进程**（`robot_proxy.py`）：避开 GIL 争用。信号处理、SHM 泄漏兜底、队列信号量释放都考虑得很细。
- **RDM 锁模型已收敛为单一 `action_lock`**：注释清楚记录了之前双锁无互斥的历史问题，属于正确的修复。
- **计算已向量化**：块内拟合用 Vandermonde 矩阵批量 lstsq，min-jerk 也有 NumPy 版本。
- **`action_layout` 统一描述动作维度**：`gradual`、`stepwise`、`manual` 三种策略让多机器人适配比较干净。
- **ZMQ 设计**：心跳与业务用两个独立 DEALER，请求带 `request_id` 并丢弃过期响应。

---

## 3. 模块要点

| 模块 | 职责 | 备注 |
|---|---|---|
| `conf/*.py` + `default_conf.yaml` | ml_collections ConfigDict；web 模式从 yaml 加载/保存 | CLI 版与 web 版两套配置来源，容易不一致（见 M2、L8） |
| `client/core/vla_client.py` | 线程编排：观测、推理、控制、可视化、录制 | 958 行，职责偏多 |
| `client/core/realtime_data_manager.py` | 观测缓冲、原始块和拟合块、索引推进、耗时统计、sync 等待 | 核心状态机 |
| `client/core/intra_chunk_smoother.py` | raw / interpolation(CubicSpline) / fitting(多项式) | 见 H2 |
| `client/core/inter_chunk_fuser.py` | search_action / smooth_velocity / min_jerk / sync | smooth_velocity 实为纯 Python 双重循环，文档写的是 Numba |
| `client/core/shared_memory_manager.py` | 预分配环形 SHM 槽和描述符 | 读端没有序号校验（见 M8） |
| `client/core/task_language_manager.py` | 子任务语言指令，按 prob_progress 自动切换 | 见 M6 |
| `client/core/data_record_manager.py` + `lerobot_dataset_recorder.py` | LeRobot v2.0 格式录制与评测记录 | 1400+ 行 |
| `client/robots/robot_proxy.py` | 子进程代理、同步 RPC | 见 H1 |
| `client/robots/{a2d,ti5_t170c,...}` | SDK 适配 | Ti5 为本分支新增 |
| `server/core/*` | ZMQ ROUTER、解码、推理线程池 | 见 H3、M5 |
| `server/models/*` | 各模型的 `infer(sequence) → {type, pred_action, ref_timestamp, loc_timestamp, ext}` | 接口一致，但大量 `print` |
| `web_client/server.py` | FastAPI 控制台 | 1981 行，见 H4、M7 |
| `extra/dispatch` | 多机调度（外部任务服务器 ZMQ） | 服务器 IP 硬编码为 192.168.0.188 |

---

## 4. 问题清单

### 🔴 高优先级

#### H1. 控制频率远达不到 266Hz，且轨迹按 tick 推进，导致执行速度随负载漂移 【已验证】

**原因链：**

1. `RobotProxy.control_robot()` 是同步 RPC（`robot_proxy.py:482-511`），命令只在 worker 主循环里被处理。
2. worker 循环是"处理命令 → `retrieve_observation()`"串行执行（`robot_proxy.py:182-195`）。A2D 在没有新帧时会 `time.sleep(0.01)`（`a2d/body_robot.py:143-146`）；有新帧时还要同步等待非参考相机和本体状态。
3. 结果是每次 `control_robot` 至少被阻塞一个观测周期。`MultiThreadTimer` 不追帧（`multi_thread_timer.py:37-40`）。
4. `get_action_fitted()` 每个 tick 固定让索引 +1（`realtime_data_manager.py:364`），而轨迹按 3.75ms 网格生成。

**实测：** 用一个模拟 A2D 行为的假机器人（33ms 出一帧，无帧时 sleep 10ms）跑真实的 `RobotProxy` 和 `MultiThreadTimer`：

- `control_robot` RPC 延迟：中位数 **10.86ms**，p90 11.10ms
- 目标 266.7Hz，实际只有 **99.7Hz**

**后果：**

- 实际执行速度约为设计速度的 **1/2.7**。README 提到的"smooth_velocity 模式偏慢"很可能部分源于此。
- 延迟补偿按"墙钟时间"算出起始索引，播放却按"tick 数"推进，两者单位不一致，补偿会持续偏差。
- 控制节拍随相机帧率、SDK 耗时、日志量抖动，动作平滑性无法保证。

**建议：**

- worker 中把控制和观测拆开：控制命令走独立线程或共享内存"最新目标值"，不做逐条 RPC 应答；或者在 `retrieve_observation` 前后都 drain 命令，并去掉 A2D 的 sleep。
- 让 `get_action_fitted` 按 `perf_counter()` 相对块起点的时间查索引，而不是 `+1`。这样即使控制频率下降，轨迹时间轴也保持正确。

#### H2. `intra_chunk_mode='raw'` 时动作以约 8.9 倍速执行

`_traj_raw` 直接返回 30Hz 的原始动作和稀疏时间戳（`intra_chunk_smoother.py:425-429`），控制线程仍然每 3.75ms 前进一列。于是 33.3ms 一帧的动作被 3.75ms 消费一次，理论上是 **8.9 倍速**。按 H1 的实测 100Hz 算，也有约 3.3 倍速。另外 `next_timestamps[1]-[0]` 与 `get_start_chunk_index` 的语义也会随之错位。

**建议：** raw 模式做零阶保持重采样到 `time_step` 网格，或者禁止在该模式下启动控制。

#### H3. ZMQ socket 跨线程使用（线程不安全）

- 服务端：同一个 ROUTER socket 在 `recvThreadFun` 中 `recv_multipart`（`zmq_server.py:132`），又在 `_sender_worker` 线程中 `send_multipart`（`zmq_server.py:101`）。ZMQ socket 不是线程安全的，并发收发可能导致断言崩溃或消息损坏。
- 客户端：心跳线程失败时在 `_attempt_reconnect` 里关闭并重建 `self.dealer`（`zmq_client.py:125-141`），推理线程可能正在同一个 dealer 上 `poll`/`recv`/`send`。`_reconnect_lock` 并没有保护业务收发。

**建议：** 服务端改成单线程 `zmq.Poller` 同时处理收发（发送队列用 inproc PAIR 或 poller 中检查队列）；客户端重连时加锁互斥业务收发，或者把重连动作交给推理线程执行。

#### H4. Web 控制台无鉴权，默认监听 0.0.0.0，可远程驱动机器人并写文件

- `run_web_client.py:31` 和 `web_client/server.py:1976` 默认 `0.0.0.0`，所有 REST/WS 接口都没有认证。同网段任何人都能 reset、手动控制机械臂、启停推理。
- `/api/client/language/save`（`server.py:811-829`）只校验"在项目根目录内"，可以把任意 JSON 写到 ROOT 下任意路径，包括覆盖 `.py` 源码。
- `/api/client/config/save` 可以把生成的 Python 或 YAML 写到 ROOT 下任意路径。`/api/client/config/path`（`server.py:586-590`）完全不校验。

**建议：** 默认绑定 `127.0.0.1`；加简单 token 认证；写文件限定在 `conf/` 目录并使用扩展名白名单。

#### H5. 非 Ti5 环境下 `run_web_client.py` 无法启动

`_ensure_dds_env` 的 `import ti5_t170c_sdk` 在 try 内，但 `ensure_cyclonedds_uri(peer_ip=peer_ip)` 在 try 外（`run_web_client.py:48,59`）。没安装 Ti5 SDK 的 A2D 或 Mock 机器会抛 `NameError`，web 客户端直接退出。这是合并 Ti5 分支时引入的回归问题。

**建议：** 整体放进 try，或者只在 `robots.type == ti5_t170c` 时调用。

### 🟠 中优先级

#### M1. 图像通道顺序：模型实际收到 BGR；录制视频也是颜色互换的 【已验证链路】【需确认影响】

- 机器人适配层把 SDK 图像翻转成 RGB（`a2d/body_robot.py:152`，其 `__main__` 用 `RGB2BGR` 显示，说明输出确实是 RGB）。
- 客户端：RGB → BGR → `imencode`，这一步正确（`vla_client.py:785-788`）。
- 服务端：`imdecode` 得到 BGR，`[:, :, ::-1]` 翻一次，return 时又 `[:, :, ::-1]` 翻回去（`vla_server.py:121-125`），**模型最终拿到 BGR**。复现结果：纯红 RGB 像素 `[255,0,0]` 到模型输入变成 `[0,0,254]`。
- 录制：`_prepare_video_frame` 把 RGB 数组直接交给 `cv2.VideoWriter`（期望 BGR）而没有转换（`lerobot_dataset_recorder.py:1116-1142`），所以 mp4 文件红蓝互换。

两处"错误"对自采数据恰好互相抵消，所以用本框架录制并训练的模型可能表现正常。但加载标准 LeRobot 数据或官方预训练权重（π0、GR00T 等）时，推理输入颜色是反的。

**建议：** 服务端只翻转一次，录制端写入前 `RGB2BGR`，并评估已有自采数据集是否需要重新转码。

#### M2. `run_client.py` 的多个 CLI 参数一用就崩 【已验证】

`override_config_with_args`（`run_client.py:98-121`）：

- `--fps`：`config.observer` 不存在（`get_observer_config` 从未挂载），抛 `AttributeError`。
- `--language`：用 list 覆盖 ConfigDict 字段，抛 `TypeError`。
- `--preprocess`：用 str 覆盖 ConfigDict 字段，抛 `TypeError`；`--preprocess_size` 写入的字段也不会被读取。

`conf/user_conf_example.py` 中的 `language` 列表覆盖会因同样原因失败，但被 `apply_user_config` 捕获后只打印一条警告，**静默失效**。

#### M3. `rdm.mode='sync'` 下，`clear()` 后推理线程永久阻塞

`wait_for_next(mode='sync')` 使用无超时的 `wait_for`，谓词要求 `action_chunk_index is not None`（`realtime_data_manager.py:494-498`）。`clear()` 会把它置为 None 并 notify（`:449-453`），但被唤醒后谓词仍为假。而唯一能发布新块的正是这个被阻塞的推理线程，形成**自锁**，之后的 resume 也无效。默认 async 模式不受影响。

**建议：** `wait_for` 加超时，或者在谓词中把"已被清空"视为可退出条件。

#### M4. 延迟补偿的边界处理错误

- `get_start_chunk_index`：当推理延迟超过整个块时长时，循环找不到点，返回 **0**（`realtime_data_manager.py:317-326`），也就是回放最旧的动作。应返回最后一个索引，或丢弃这个块。
- `_search_smooth_action`：没有运动关节时 `return next_action_chunk, 0`（`inter_chunk_fuser.py:580-582`），丢掉了 `target_chunk_index` 的延迟补偿，应返回 `target_chunk_index`。

#### M5. 服务端并发调用同一模型

`max_infer_workers=3`（`server_conf.py`），`executor.submit(self.model.infer, ...)` 可能并发执行（`vla_server.py:46,185`）。客户端 500ms 超时后会发下一个请求，旧请求仍在推理，于是出现并发。大多数策略实现（torch 模型、带内部状态的 ACT 时间集成、openpi policy）并非线程安全，而且并发会让 GPU 延迟雪崩。

**建议：** 默认 1 个 worker；客户端超时后在服务端丢弃积压请求（只保留最新的一个）。

#### M6. auto_mode 下任务进度队列无界增长，控制线程开销随运行时间线性上升

`task_progress_queue = deque()` 没有 maxlen（`task_language_manager.py:29`），控制线程每 tick 追加一次（约 100-266 次/秒），只有子任务切换成功时才清空。`_average_task_progress` 每个 tick 执行一次 `list(self.task_progress_queue)`，是全量复制（`:285`）。长时间卡在同一子任务时，内存和 CPU 持续增长。

另外 `get_prob_progress()` 在没有进度时返回 `0` 而不是 `None`（`realtime_data_manager.py:398`），导致 `vla_client.py:533` 的 `is not None` 判断永远为真，窗口会被 0 填充。窗口大小 10 在 266Hz 下只有约 37ms，可能不符合设计本意。

**建议：** `deque(maxlen=win_size)`，改为按推理次数而不是控制 tick 累积。

#### M7. Web reset 接口阻塞整个事件循环

`client_control_reset` 是 `async def`，但直接同步调用 `robot.reset_robot()`（`web_client/server.py:1758`）。这是一次 RPC，内部有 Ruckig 规划和逐点 sleep，可能持续数秒到 30s 超时，期间整个 FastAPI 和 WebSocket 都卡住。其他控制接口都用了 `asyncio.to_thread`，唯独这里没有。`_stop_client` 中的 `vla_client.stop()` 也会同步 sleep。

#### M8. 录制读取共享内存时没有帧序号校验

观测线程写入进程内 SHM 环形缓冲（`ring_size=30`，`vla_client.py:104`），录制子进程之后按描述符去读（`data_record_manager.py:528`），不检查 `slot_index` 和 `timestamp_ns` 是否已被覆盖。写盘落后超过约 1 秒（30 帧）时，会**静默录入更新的帧**，视频与状态、动作错位。worker 与主进程之间的 ring=4 也存在同类窗口，概率较低。

此外录制进程使用默认的 fork 启动方式，fork 时父进程已有 ZMQ、线程池等多线程，存在死锁风险。

**建议：** 读取时校验时间戳，不一致就丢帧并计数；录制进程改用 spawn。

#### M9. Ti5 每个控制周期都打印 INFO 日志

`execute_action` 中 `self.logger.info("execute_action hand=%s", ...)`（`ti5_t170c/body_robot.py:69`），而 `hand_freq=1`，即每个 tick 都下发手部指令。worker 子进程的 basicConfig 是 INFO 级别输出到终端，每秒上百行同步 I/O，直接叠加在 H1 的控制延迟上。

**建议：** 改为 debug 级别或节流输出。

### 🟡 低优先级 / 代码质量

| # | 位置 | 问题 |
|---|---|---|
| L1 | `realtime_data_manager.py:166` | `compute_avg_inter_traj_time` 用了 `self.avg_intra_traj_time * 0.8`（复制粘贴错误），统计值失真 |
| L2 | `vla_client.py:507,550` | `observe_period` 已经是秒，又 `/1000`，导致可视化中原始动作的速度放大 1000 倍、加速度放大 10⁶ 倍 |
| L3 | `zmq_server.py:38,117` | `heartbeat_timeout` 配置单位是 ms（30000），服务端按秒比较，客户端永远不会被清理 |
| L4 | `zmq_server.py:138-141` | 判断 `len(parts) >= 2` 却访问 `parts[2]` |
| L5 | `conf/models_conf.py:79` / `:71` | GO1 的 `data_stats_path` 在配置时用占位路径拼好，`--model_path` 覆盖后不更新；SmolVLA `root_path` 硬编码个人目录 |
| L6 | `server/models/openpi/pi05.py:79-86` | `DEFAULT_CHECKPOINT` 字典中 `EnvMode.A2D` 键重复，pi0 条目被覆盖 |
| L7 | `pi0.py`/`pi05.py` `reshape_action` | 左手取 15:20、右手取 21:26，跳过了第 14、20 列（26 = 14 臂 + 6 + 6 手），疑似差一错误 【需确认】 |
| L8 | `conf/robots_conf.py:135-140`、`default_conf.yaml:347-381,451-477` | Ti5 `_arm_reset` 左臂第 6 关节是 `-0.21850174207321`，右臂是 `-0.2251850174207321`，疑似笔误；yaml 中 `left.Custom` 填的是右臂数值；yaml 与 py 的 `reset_robot_pos` 完全不同，CLI 和 web 两种启动会复位到不同姿态 |
| L9 | `a2d/body_robot.py:223-228` | `load_action_data` 左手取 `[15:19]`（4 维）、右手取 `[20:23]`（3 维），阈值逻辑左右相反（左 >0.1 置 1，右 <0.1 置 0） |
| L10 | `run_client.py:176-218` | 交互菜单硬编码 `"make_coffee"`；`s`/`d` 的实现被注释掉却提示"已保存/已删除"；引用了不存在的 `vla_client.language` |
| L11 | `task_language_manager.py:191` | 语言表为空时 `return ""`，调用方按两个值解包，抛 `ValueError` |
| L12 | `vla_client.py:263` | `start_recording` 在没有相机时 `while camera_shape_dict is None` 死等 |
| L13 | `vla_client.py:394-395` | 观测线程 `sleep(0.01/n)` 且 n 无上限，没有新帧时退化为忙等 |
| L14 | `web_client/server.py` `_cleanup` | 获取锁超时时，`finally: del vla_client` 会抛 `UnboundLocalError`，掩盖原始异常 |
| L15 | `visualize_server.py:46`、`run_web_client.py:37` | `os.system('kill -9 $(lsof ...)')`，端口为空时报错，也可能误杀其他进程 |
| L16 | `a2d/body_robot.py` `control_robot` | 不过滤 `policy='manual'` 的段（Ti5 版本过滤了）；若模型输出维度 ≥22，会驱动头、腰、底盘 |
| L17 | `base_robot.py:72` | `_control_robot` 读取 `self.cfg`，A2D 没有定义 `cfg`，`manual_arm_interval` 和 `hand_type` 配置不生效（回退到默认值） |

### 工程与文档

- **README 与代码不一致**：`config.chunk_trans_mode` 实际叫 `inter_chunk_mode`；README 写的 `poly` 模式不存在（代码是 `min_jerk`）；`show_action_cams_qt`/`show_action_cams` 在代码中不存在；`scripts/reset_robot/` 不存在；可视化端口写 8080，实际是 8765（WS）和 9000（web）。
- **`temp.md` 是通用 README 模板残留**，内容与项目无关。
- **依赖冲突**：`requirements.txt` 注明是"web_client 最小依赖"，锁定 `numpy==1.26.4`，而 README 要求 `numpy>=2.4.4`、`pandas>=3.0.2`。服务端和模型依赖没有独立清单。
- **测试缺失**：`test/` 下只有临时验证脚本（`test_proxy_robot.py` 注释写着"验证后删除"）；平滑、融合、时间戳这类纯函数最适合单测，却完全没有覆盖。
- **仓库卫生**：`.gitignore` 忽略了 `data/`，但 README 引用 `data/media/*`；存在 `detr_vae.py.bak`；大量注释掉的旧代码；各模型 `infer()` 每次调用都 `print`。

---

## 5. 修复路线建议

| 阶段 | 内容 | 预期收益 |
|---|---|---|
| **P0 立即** | H5（web 启动回归）、M2（CLI 崩溃）、M9（Ti5 日志）、L1/L2/L3 小修 | 改动小，恢复可用性，统计和可视化可信 |
| **P1 本周** | H1：worker 控制与观测解耦，索引改为按时间推进；H2 raw 模式重采样；M4 延迟补偿边界 | 直接决定真机动作速度与平滑性，最高价值 |
| **P1 本周** | H3：ZMQ 单线程收发；M5：服务端单 worker 并丢弃积压 | 消除偶发崩溃和延迟雪崩 |
| **P2** | M1 色彩通道（先确认训练数据来源）、M8 录制帧校验、M3 sync 超时、M6 进度队列 | 数据质量与长时稳定性 |
| **P2** | H4 Web 安全（绑定本机 + token + 写路径白名单）、M7 | 实验室网络安全 |
| **P3** | 为 smoother / fuser / RDM 时间轴补单测；清理 README、temp.md、依赖清单；拆分 `vla_client.py` 和 `web_client/server.py` | 可维护性 |

---

## 附：验证记录

1. **CLI 覆盖**：用 ml_collections 加载 `get_client_config()` 后执行三种覆盖，依次得到 `AttributeError 'observer'`、`TypeError(list→ConfigDict)`、`TypeError(str→ConfigDict)`。
2. **代理控制延迟**：真实的 `RobotProxy` + `MultiThreadTimer(3.75ms)`，配合模拟 A2D 取帧行为的假机器人，得到 RPC 延迟中位数 10.86ms，实际控制频率 99.7Hz。
3. **颜色链路**：按客户端编码和服务端解码的原代码逻辑复现，RGB 红色像素到模型输入变为 `[0,0,254]`（BGR）。
