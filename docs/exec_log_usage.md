# 实验执行记录（Execution Log）使用说明

## 概述

执行记录面板用于在 VLA 推理过程中自动/手动记录每条语言指令的执行情况，包括任务名、指令内容、起止时间、耗时、评分和备注。记录持久化在浏览器 `localStorage` 中，可导出 CSV 或保存到服务端 `logs/` 目录。

## 面板入口

执行记录面板位于 **Data Recording** 面板内。在 Recording 控制区勾选 **ExecLog** 复选框即可展开/收起执行记录面板。

## 记录的生命周期

### 自动触发

| 事件 | 行为 |
|---|---|
| **系统 Start** | 自动创建一条 `running` 记录，使用当前选中的任务和指令 |
| **系统 Stop** | 当前 `running` 记录标记为 `interrupted`，保留已运行时长 |
| **系统 Pause** | 计时器冻结，不计入时长 |
| **系统 Resume** | 计时器恢复 |
| **Auto Mode 切换下一条指令** | 旧记录标记为 `switched`，新记录以新指令开始 |
| **Auto Mode 全流程结束** | 当前记录标记为 `interrupted`，系统自动 Pause |
| **后端断连（程序 Kill）** | 当前记录标记为 `interrupted` |
| **页面关闭/刷新** | 通过 `beforeunload` 将 `running` 记录标记为 `interrupted` 并保存 |

### 手动触发

点击面板工具栏 **● Rec** 按钮可手动切换记录状态：

- **未录制状态** → 点击开始新记录（需系统处于 Running 状态）
- **录制中状态** → 点击结束当前记录，标记为 `interrupted`

按钮在录制中会显示红色脉冲动画。

## 记录状态说明

| 状态 | 含义 | 显示样式 |
|---|---|---|
| `running` | 正在执行中 | 正常显示，实时计时 |
| `switched` | 因切换到下一条指令而结束 | 半透明 |
| `interrupted` | 因停止/中断而结束 | 橙色背景 + 半透明 |
| `scored` | 已评分 | 评分颜色高亮 |

## 评分

### 工具栏快捷评分

面板工具栏有 **0 / 0.5 / 1** 三个按钮，点击后对当前 `running` 记录打分。
### 表格内修改评分

每条记录的 **Sco** 列是一个下拉框，可随时修改分值：

- `--`：未评分
- `0`：失败（红色）
- `0.5`：部分成功（橙色）
- `1`：成功（绿色）

修改分值后自动保存。已结束的记录评分后会自动将状态更新为 `scored`。

## 数据导出与保存

| 按钮 | 功能 |
|---|---|
| **CSV** | 导出所有记录为 CSV 文件下载 |
| **Save** | 将所有记录 POST 到服务器，保存为 JSON 文件 |
| **Clear All** | 清空所有记录并重置 ID 计数器（需确认） |

## 表格列说明

| 列 | 内容 |
|---|---|
| **Task#** | 记录序号 + 任务名（截断）+ 子任务编号，hover 显示完整信息 |
| **Inst** | 指令文本（截断），hover 显示全文 |
| **Start** | 开始时间（HH:MM:SS） |
| **Dur** | 执行时长，`running` 状态时实时更新 |
| **Sco** | 评分下拉框 |
| **Note** | 备注输入框，失焦自动保存 |
| **✕** | 删除该条记录 |

## ID 编号

每条记录有全局自增的数字 ID，在 Task# 列灰色小字显示。Clear All 后 ID 从 `1` 重新开始。

## 数据持久化

- **自动保存**：每次记录变更（新建/结束/评分/备注/删除）都会自动写入 `localStorage`
- **页面加载**：从 `localStorage` 恢复记录，自动丢弃上次残留的 `running` 记录
- **手动保存到服务器**：点击 Save 按钮，记录保存到服务端 `logs/` 目录

## 相关代码位置

- 主逻辑：`web_client/static/modules/recording.js`
- 样式：`web_client/static/styles/modules/recording.css`
- 面板结构：`web_client/static/index.html`
- 语言指令触发：`web_client/static/modules/language.js`（调用 `startExecRecord` / `autoStartExecRecord`）
