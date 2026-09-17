# 新机器人接入指南

[English Version](add-new-robot.md)

## 快速开始

下面以双臂机器人 `my_robot` 为例：双臂 14 维、双夹爪 2 维，头部 2 维只供手动控制。

### 1. 创建机器人适配器

```text
client/robots/my_robot/
├── __init__.py
└── body_robot.py
```

`body_robot.py` 最小模板：

```python
import numpy as np

from ..base_robot import RobotBase
from .driver import MyRobotDriver, MyCameraDriver


class RobotBody(RobotBase):
    def __init__(self, config):
        super().__init__(config)  # 必须调用：解析 action_layout 和动作索引
        self.cfg = config  # 当前基类的 Web 手动控制从 self.cfg 读取参数
        self.robot = MyRobotDriver(config)
        self.camera = MyCameraDriver(config.camera)
        self.current_timestamp = None

    def control_robot(self, action):
        """执行模型输出；action 只包含 gradual/stepwise 段。"""
        action = np.asarray(action, dtype=float).reshape(-1)
        if action.size != self.action_dim:
            raise ValueError(f"action dim={action.size}, expected={self.action_dim}")

        for name, layout in self.action_layout.items():
            if layout["policy"] == "manual":
                continue
            start, end = int(layout["start"]), int(layout["end"])
            self.execute_action({name: action[start:end].tolist()})

    def execute_action(self, data):
        """执行已经分段的底层命令。"""
        if "arm" in data:
            self.robot.move_arm(data["arm"])
        if "gripper" in data:
            self.robot.move_gripper(data["gripper"])
        if "head" in data:
            self.robot.move_head(data["head"])

    def retrieve_observation(self):
        image, timestamp_ns = self.camera.get_latest_image()
        if timestamp_ns == self.current_timestamp:
            return None
        self.current_timestamp = timestamp_ns

        state = np.asarray(self.robot.get_state(), dtype=float).reshape(-1)
        if state.size != self.state_dim:
            raise ValueError(f"state dim={state.size}, expected={self.state_dim}")
        self.current_state = state.copy()

        return {
            "ref_timestamp": int(timestamp_ns),
            "cam.head": np.ascontiguousarray(image, dtype=np.uint8),
            "obs.state": state,
        }

    def close(self):
        self.camera.close()
        self.robot.close()
```

如果 `action_layout` 已配置 `presets.Default`，通常可直接继承基类的 `reset_robot()` 和 Web 手动控制 `_control_robot()`，无需重复实现。

### 2. 添加配置

修改 [`conf/robots_conf.py`](../../conf/robots_conf.py)：

```python
class RobotType(str, Enum):
    A2D = "a2d"
    MOCK = "mock"
    TI5_T170C = "ti5_t170c"
    NAVI_WA2 = "navi_wa2"
    MY_ROBOT = "my_robot"


def get_my_robot_config():
    config = ConfigDict()
    config.manual_arm_interval = 0.01
    config.camera = ConfigDict({"ref": "head", "names": {"head": "head"}})
    config.action_layout = _ordered_config({
        "arm": {
            "start": 0, "end": 14, "policy": "gradual",
            "presets": {
                "left": {"Default": [0.0] * 7},
                "right": {"Default": [0.0] * 7},
            },
        },
        "gripper": {
            "start": 14, "end": 16, "policy": "stepwise",
            "presets": {
                "left": {"Default": [0.0], "Open": [0.0], "Close": [1.0]},
                "right": {"Default": [0.0], "Open": [0.0], "Close": [1.0]},
            },
        },
        # manual 段必须位于所有模型动作段之后。
        "head": {
            "start": 16, "end": 18, "policy": "manual",
            "presets": {"Default": [0.0, 0.0]},
        },
    })
    return config


def get_robots_config():
    config = ConfigDict()
    config.type = RobotType.MY_ROBOT
    # 保留已有配置……
    config.my_robot = get_my_robot_config()
    return config
```

### 3. 注册两个构造入口

命令行入口：在 [`run_client.py`](../../run_client.py) 的 `get_robot()` 中增加：

```python
elif robot_type == RobotType.MY_ROBOT:
    from client.robots.my_robot.body_robot import RobotBody
    return RobotBody(robot_config)
```

Web 入口：在 [`web_client/server.py`](../../web_client/server.py) 的 `_get_robot()` 中增加创建分支：

```python
elif robot_type == RobotType.MY_ROBOT:
    from client.robots.my_robot.body_robot import RobotBody
    robot_instance = RobotBody(robot_config)
```

如需 Web 停止后复用同一个 SDK 实例，还要在 `_get_robot()` 前部增加对应的类型/模块匹配分支；否则切换或重启时会先关闭再重建。

`RobotBody` 接收的是 `config.robots.my_robot` 子配置，不是完整 Client 配置。当前基类构造函数保存为 `self.config`，但 Web 手动控制读取 `self.cfg`，因此新适配器需要像模板一样设置别名。

### 4. 运行

先断开执行器或降低速度，验证维度、方向、单位和限位，然后运行：

```bash
python run_client.py --robots_type my_robot
python run_web_client.py
```

## 当前分支的数据规则

### `action_layout`

每段必须包含 `start`、`end`、`policy`，可选 `presets`。

| policy | 用途 | 是否进入模型 action |
|---|---|---|
| `gradual` | 连续关节，如机械臂 | 是 |
| `stepwise` | 夹爪、离散/快速变化维度 | 是 |
| `manual` | 头、腰、轮子等 Web-only 维度 | 否 |

关键约束：

- 区间使用 `[start, end)`，不能重叠。
- 所有 `manual` 段必须放在 `gradual/stepwise` 段之后，否则 `parse_action_layout()` 会报错。
- `self.action_dim` 只计算模型动作段；`self.state_dim` 是所有段最大 `end`。
- `self.joint_indices` 来自 `gradual`；`self.step_indices` 来自 `stepwise`，供轨迹平滑使用。
- 模型、驱动和 `obs.state` 的维度顺序必须与布局一致。

### Web 手动控制

基类 `_control_robot()` 已支持：

- `l_arm/r_arm`、`l_gripper/r_gripper`、`l_hand/r_hand`。
- `head`、`waist`、`body`、`wheel`、`leg`。
- 数值 `-1000` 表示保持该维当前位置。
- 机械臂通过 Ruckig 插值，周期由 `manual_arm_interval` 控制。

左右控制的 action 总维度必须是正偶数。使用基类手动控制前，`retrieve_observation()` 必须正确更新 `current_state`，且 `execute_action()` 必须支持相应 key。

### Reset presets

基类 `reset_robot()` 从每段的 `presets.Default` 生成手动控制命令。双侧动作使用：

```python
"presets": {
    "left": {"Default": [...]},
    "right": {"Default": [...]},
}
```

非双侧动作使用：

```python
"presets": {"Default": [...]}
```

也可传入完整 `target_pose`；基类会按 `action_layout` 切片。只有硬件需要特殊复位顺序时才覆盖 `reset_robot()`。

### Observation

最小格式：

```python
{
    "ref_timestamp": timestamp,
    "cam.head": image,
    "obs.state": state,
}
```

- 无新参考帧时返回 `None`，不要重复提交同一帧。
- 普通图像使用 C-contiguous `uint8 H×W×3`，按 OpenCV BGR 约定。
- 多相机按参考时间戳取最近帧。
- `obs.state` 建议覆盖全部布局（包括 `manual` 段），并同步写入 `current_state`。
- 不要在 `retrieve_observation()` 内重连设备、同步写盘或等待机器人动作完成。

## 录制要求

观测的 key、dtype 和 shape 必须稳定，`obs.state` 顺序固定，模型 action 维度等于 `self.action_dim`，相机名称同时存在于观测和录制配置。当前分支记录控制线程的 `action_fitted`，驱动侧额外映射不会自动反映到 action 文件中。

## 验证清单

- [ ] `RobotBody(config)` 能创建，且 `super().__init__(config)` 已调用。
- [ ] `action_dim`、`state_dim`、joint/step indices 符合预期。
- [ ] 模型 action 各段能路由到正确驱动。
- [ ] Web 左右控制及 `-1000` 保持位置有效。
- [ ] Default presets 能安全复位所有配置段。
- [ ] 图像、时间戳、`obs.state` 与 `current_state` 正确且同步。
- [ ] 关节顺序、单位、正负方向和限位正确。
- [ ] `run_client.py` 和 `run_web_client.py` 均能创建该机器人。
- [ ] 断网、设备掉线及退出时进入安全状态，并能重复调用 `close()`。
