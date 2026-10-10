# Open-RAIL 新增 inter_chunk_fuser 策略开发文档

[English Version](../docs/guides/add-new-inter-chunk-fuser.md)

## inter_chunk_fuser 作用说明
假设 $t_1$ 时刻观测为 $O_{t_1}$，VLA 模型根据语言指令与观测预测一个 $n$ 步动作块：$[a_0, a_1, \dots, a_n]_{t_1}$。

Open-RAIL 采用异步架构：得到 $\text{chunk}_{t_1}: [a_0, a_1, \dots, a_n]_{t_1}$ 后，机器人立刻执行该动作块；与此同时 VLA 模型基于 $t_2$ 时刻观测 $O_{t_2}$ 预测下一个动作块 $[a_0, a_1, \dots, a_n]_{t_2}$。

定义 VLA 模型推理时延为 $\Delta_t$，通常满足 $t_2 \ge t_1 + \Delta_t$。

实际场景中，旧动作块尚未执行完毕，新动作块就已经生成。若机器人执行到 $\text{chunk}_{t_1}$ 的第 $i$ 个动作时，$\text{chunk}_{t_2}$ 到达，则 **inter_chunk_fuser** 的目标是从 $\text{chunk}_{t_1}$ 的第 $i$ 个动作平滑衔接到 $\text{chunk}_{t_2}$ 的指定动作，抑制动作幅值跳变。

### 策略输入参数
| 参数 | 说明 |
| ---- | ---- |
| next_action_chunk | 新动作序列，维度 $d \times n$；$d$ 为机器人关节数，$n$ 为动作步数 |
| next_vel_chunk | 与 next_action_chunk 对应的速度序列 |
| next_acc_chunk | 与 next_action_chunk 对应的加速度序列 |
| currt_action | 当前正在执行的旧动作块内动作 |
| currt_vel | 执行 currt_action 对应的速度 |
| currt_acc | 执行 currt_action 对应的加速度 |
| target_chunk_index | next_action_chunk 中待衔接动作的索引 |

> Open-RAIL 内部已实现3种inter-chunk-fuser策略：`search_action`、`min_jerk`、`smooth_velocity`

---

## 新增自定义 inter_chunk_fuser 策略（`your_fuser_method`）开发步骤
策略简称：`your_fuser`

### 1. inter_chunk_fuser.py 增加策略入口
文件路径：`./client/core/inter_chunk_fuser.py`
在 `InterChunkFuser` 类的 `process` 函数中，增加 `your_fuser` 判断分支入口。

### 2. inter_chunk_fuser.py 实现策略逻辑
文件路径：`./client/core/inter_chunk_fuser.py`
在 `InterChunkFuser` 类内部，新增成员函数 `your_fuser_method`，实现你的平滑衔接算法。

### 3. client_conf.py 增加策略配置
文件路径：`./conf/client_conf.py`
1. 新建 `your_fuser_method_config` 函数，定义该策略所需超参数；
2. 在 `get_inter_chunk_config` 函数中实例化 `your_fuser_method_config`。

### 4. web前端配置项添加
文件路径：`./web_client/static/modules/config.js`
在 `CONFIG_SELECT_OPTIONS` 下的 `inter_chunk_mode` 列表中，新增 `"your_fuser"` 选项。

### 5. 验证
启动 server 和 web_client，访问 `localhost:9000`，在网页左侧 **Main Parameters** → **Inter-Chunk Mode** 下拉框即可选择 `your_fuser` 策略。
