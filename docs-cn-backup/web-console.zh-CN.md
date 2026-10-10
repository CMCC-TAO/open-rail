# Web 控制台

[English Version](../docs/web-console.md)

Web 控制台是由 `run_web_client.py` 启动的浏览器操作台（默认 `http://localhost:9000`）。页面上的所有内容都服务于五类工作：**运行控制**（启动、分段、暂停、复位循环）、**任务指令**（选择并下发机器人要做什么）、**数据录制与评估**（把运行过程沉淀为数据集与评分）、**机器人手动控制**，以及建立在实时相机与轨迹画面之上的**参数调优**。

控制台可独立于推理服务运行：按 [Getting Started](../docs/getting-started.md) 的 Step 2 启动后即可打开页面；连接服务端并配置机器人后，机器人状态、推理结果和相机画面才会出现。

## 页面布局

| 区域 | 面板 | 职责 |
| --- | --- | --- |
| 中栏 | **Runtime Monitor** | 主控：启动/停止、分段拉起循环、暂停、复位，并监控循环健康度 |
| 中栏 | **Language Command** | 选择、编辑并下发机器人正在执行的任务指令 |
| 左栏 | **Data Recording** | 把运行录制到磁盘并事后评分（EvalLog、LeRobot、ExpeData） |
| 左栏 | **Robot Control** | 向已连接机器人发送手动命令与预设 |
| 右栏 | **Camera Viewer** | 头部与腕部相机画面 |
| 中栏 | **Trajectory** | 所选关节状态/动作序列的实时曲线 |
| 左栏 | **Configuration** | 加载、调优并保存客户端参数 |
| 顶栏 | 状态徽标、Shortcuts、资源胶囊、服务指示灯 | 运行状态、快捷键帮助、CPU/GPU/MEM/NET、连接状态 |

下文按此顺序介绍——常用在前。

## Runtime Monitor

主控面板。一个总开关加三个阶段按钮驱动整个运行循环。

- **Start / Stop** 是同一个切换键。**Start** 创建客户端并一次性启动 Observe、Inference、Control 与可视化；启动前先自动应用待提交的配置修改。**Stop** 释放全部资源；下一次 Start 会按当前配置重建客户端。若 Data Recording 面板开启了 **Auto**，录制会在 Start 后自动开始。
- **Observe → Infer → Control** 在不想一次性全跑时分段拉起循环。顺序被强制两次：按钮在前置未就绪时禁用（Infer 需要 Observe，Control 需要 Infer），服务端还会对乱序请求给出明确报错。
- 把某一阶段**关掉**会级联停止其下游：关 Observe 会同时停 Inference 与 Control；关 Infer 停 Control。Control 自身可独立开关。
- **Pause** 停止全部三个线程，但记住各自此前是否在运行；**Resume** 恢复到完全相同的组合。Pause 与 Resume 同时会暂停/恢复进行中的录制。（`Space` 切换 Pause；`Ctrl+Space` 切换 Control。）
- **Reset**（也是 `Shift+R`）是一段受控流程，不是单次运动：客户端先暂停，机器人回到预设默认位（或 Robot Control 面板当前填入的位姿），客户端等待至少两倍 `1.5 × 平均推理时间` 让动作到位，然后清空内部缓冲。之后客户端**保持暂停**——按 Resume 继续。开启 **Auto** 录制时，录制会在复位后重新开始。
- **Key Statistics** 展示客户端侧循环健康度：Observe FPS、Infer Count、Img Proc Time、Avg Infer Time、Intra Chunk Time、Inter Chunk Time、Avg Net Latency。

## Language Command

选择机器人要做的事。**Task** 与 **Sub-Task** 选择器填充 **Instruction** 输入框；**Apply** 把选中的指令下发给 VLA 服务，并把任务进度重置到该步。**Upd / Add / Del** 维护指令文件；**Upd** 只修改当前指令的文本。

选择指令有守卫条件——录制中会被拒绝；**Auto Mode** 开启时会被拒绝（请先关闭 Auto Mode）；指令文件在加载后于磁盘上被改动时也会被拒绝（重新加载文件后再选）。

**Auto Mode** 依据任务进度输出自动推进到下一条指令，其中 **Start**（起始子任务）、**Thresh**（切换阈值）、**Win-Size**（进度平均窗口）对应 `language.*` 参数。**Progress** 条可视化当前任务进度值。

## Data Recording

把运行过程变成可复用的资产：执行数据落盘为 **EvalLog**（评估记录）、**LeRobot**（可直接训练的 episode）与 **ExpeData**（实验数据），每条记录可事后打分与备注，逐条回看执行质量。

- **Start / Stop** 配录制计时，另有 **Auto** 选项把录制与运行循环挂钩（见下方联动）。
- **Config**：`record.*` 参数的专用子树；录制参数在每次开始录制时读取。
- **Tasks**：选择本次录制使用的任务文件夹。
- **Evaluation Results**：每条记录一行（ID、子任务序号、时长、得分、备注）。评分按钮取自 `record.evaluation.scores`；修改得分按 Enter 即立即生效。
- **LeRobot Episodes**：按存储分块浏览已录 episode；每条可在列表中删除。

与本页其他面板的联动：

- **Auto** 会在 **Start** 后自动开始录制，并在 **Reset** 或 **Resume** 后重新开始录制。
- 录制跟随线程状态：Observe、Infer 或 Control 被关掉时录制自动暂停；重新打开后录制自动恢复。
- **Start** 作为停止键使用时，会先停掉进行中的录制，再停止客户端。
- 录制期间，在 Language 面板切换任务会被拒绝——先停止录制再换任务。

## Robot Control

对已连接机器人的直接手动控制——用于位姿摆置、预设调用与两次运行之间的恢复。分为 **Arm**、**Gripper/Hand**、**Body**（头部与腰部）、**Wheel/Leg** 几组；每组提供数值输入、预设下拉与预设编辑；**Send Cmd** 下发数值。

分组、数值范围与预设来自所选机器人的 `action_layout`（见[配置参考](../docs/configuration.md)）。缺少布局或预设的分组显示为禁用并在悬停时给出原因，让能力缺失可见，而不是静默失效。组内复选框先勾选启用，控件才可编辑。

- **Send Cmd** 立即把机器人驱动到给定数值。它需要机器人当前状态——**观测必须已启动**——否则请求被拒绝。
- **Reset** 见 Runtime Monitor；是同一个按钮、同一段受控流程。

## Camera Viewer

传输 **Head**、**Wrist-Left**、**Wrist-Right** 三路相机画面，每路有独立 **Close** 按钮，另有 **Close All**。出现哪些相机取决于所选机器人的 `camera.names` 映射与 `visualize.camera.open_*` 开关。画面在 Observe 启动时才连接，因此观测线程未运行时相机会一直是黑的。

## Trajectory

所选关节序列的实时曲线——状态与动作并排对照，用于在循环运行时检查跟踪质量。**Play / Clear** 控制视图，来源复选框选择序列（如 `State`、`ActionRaw`、`ActionFitted`），关节复选框选择维度。默认值取自 `visualize.trajectory.*`。状态序列画虚线、动作序列画实线；关节标签来自当前机器人的 `action_layout.arm`，因此轴名始终与所连机器人一致。

## Configuration

加载、调优并保存客户端参数。字段语义见[配置参考](../docs/configuration.md)；本节讲工作流与生效时机。

### Setup — 文件工作流

- **文件选择器 + Apply** 从 `conf/` 加载 YAML。这是**重载**，不是参数级热切换：运行中的客户端会被停止并按文件重建，正在进行的一切随之停止。想整体切换到另一份保存好的配置时用它。
- **Save As** 把当前内存中的配置另存为一个新文件（对话框默认填当前文件名加 `_1` 后缀）。存出一份满意的变体后，下次启动用 `--conf <file>` 加载，或之后经 Setup 加载。目标为 `.yaml`/`.yml` 时写成 YAML；其他扩展名写成 Python 字典文件。

### 编辑 — 暂存式修改

- **Main Parameters** 把最常用项固定在顶部：Robot Type、Mode、Wait Time [ms]、Control Period [ms]、Control Speed、Gripper Offset、Inter-Chunk Mode、Intra-Chunk Mode、Img Proc Method、Img Proc Width。固定哪些项本身也是可配置的，由 `visualize.main_parameters` 决定。
- 下方的**配置树**列出其余全部参数组，枚举值显示为下拉框（通过[新增平滑器](../docs/guides/add-new-inter-chunk-fuser.md)加入的自定义融合器也会出现在 Inter-Chunk Mode 下拉框中）。**Key filter** 按键名过滤配置树。
- 修改是**暂存**的，不会立即发送：出现 **● unsaved changes** 徽标，**Apply** 一次性发送全部暂存修改，随后自动保存回当前配置文件。若带着暂存修改点 **Start**，修改会先自动应用。`record.evaluation.scores` 是例外：按 Enter 即立即生效。

### 改动何时生效

补丁会立即更新内存中的配置——控制台与推理服务都**无需重启**。一个参数能否影响*运行中*的客户端，取决于它被消费的方式：

| 层级 | 范围 | 示例 |
| --- | --- | --- |
| 运行循环即时生效 | 每个控制周期都会重读的参数：`inter_chunk.*` 与 `intra_chunk.*` 全族（融合模式及各模式全部参数），以及 `controller.period`、`controller.speed` | 机器人运动中切换 Inter-Chunk Mode 或调 `smooth_velocity` 增益 |
| 经刷新生效 | 应用后推入运行中的客户端 | `vision.preprocess.*`（重建预处理）、`language.*`、`robots.mock.dataset_path`（客户端自动暂停，Mock 机器人重载数据集，再恢复） |
| 下次使用时读取 | 该功能下次启动时生效 | `record.*`（每次开始录制时读取） |
| 需重建客户端 | 客户端对象创建时即固定的值：`robots.type` 与 ZMQ 端点 | Stop → Start 会**复用同一个客户端对象**，这两类值不会自行重新绑定。切换请走 **Setup → Apply**（按文件重建客户端）或重启 `run_web_client.py`；运行中修改 `robots.type` 仅记录一条警告 |

这正是项目主页"40+ runtime parameters, no restart required"能力的机制：客户端运行中，平滑/融合全族与刷新类参数即时可调；客户端停止时调的任何参数则在下次 Start 生效。

## 操作 → 效果速查

| 操作 | 直接效果 | 联动行为 |
| --- | --- | --- |
| **Start** | 创建客户端，启动全部线程 | 先应用暂存配置；勾选 **Auto** 时自动开始录制 |
| **Stop** | 停止客户端，释放资源 | 先停掉进行中的录制；下次 Start 重建客户端 |
| **Pause / Resume** | 停止/恢复全部线程到此前精确状态 | 暂停/恢复进行中的录制；Resume 时勾选 **Auto** 会开始录制 |
| **关 Observe** | 停止观测 | 同时停 Inference 与 Control；录制自动暂停 |
| **关 Infer** | 停止推理 | 同时停 Control；录制自动暂停 |
| **Control 开关** | 仅启停机器人控制 | 按上述规则联动录制的暂停/恢复 |
| **Reset** | 客户端暂停，机器人回默认位，清空缓冲 | 之后客户端保持暂停；勾选 **Auto** 时录制可能重新开始 |
| **选择指令** | 设定当前指令，任务进度重置到该步 | 录制中或 Auto Mode 下被拒绝 |
| **Send Cmd** | 立即驱动机器人到给定数值 | 需要观测已启动 |
| **配置修改 + Apply** | 暂存项一次性下发；即时层参数作用于运行循环；文件自动保存 | `robots.type`/ZMQ 修改仅经 Setup Apply 或重启进程后生效 |
| **Setup Apply（加载 YAML）** | 停止客户端并按文件重建 | 进行中的一切停止 |
| **Save As** | 把当前配置另存为新文件 | 之后可用 `--conf` 或 Setup 加载 |

## 快捷键

| 按键 | 动作 |
| --- | --- |
| `Space` | 暂停 / 恢复 |
| `Ctrl` + `Space` | 启停控制 |
| `Shift` + `R` | 机器人复位 |
| 按住 `L` + `1–9` | 应用指令 1–9 |
| 按住 `L` + `0` | 应用指令 10 |
| 按住 `L` + `↑` / `↓` | 应用上一条 / 下一条指令 |
| `Ctrl` + `Enter` | 应用输入的指令 |

页面内 **⌨ Shortcuts** 弹层包含同一份列表。

## 相关页面

- [Getting Started](../docs/getting-started.md) — 启动控制台并连接服务端。
- [配置参考](../docs/configuration.md) — 这些面板中的全部参数。
- [Dataset Demo](../docs/demo-running-on-dataset.md) — 使用 Mock Robot 与数据集运行。
- [Troubleshooting](../docs/troubleshooting.md) — 面板行为异常时的排查。
