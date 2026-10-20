# 新机器人接入指南

[English Version](../docs/guides/add-new-robot.md)

## 快速开始

示例机器人 `my_robot` 有两条 7 自由度手臂、两维夹爪，以及一个仅用于手动控制的 2 自由度头部。

### 1. 创建适配器

```text
client/robots/my_robot/
├── __init__.py
└── body_robot.py
```

最小化的 `body_robot.py`：

```python
import numpy as np

from ..base_robot import RobotBase
from .driver import MyRobotDriver, MyCameraDriver


class RobotBody(RobotBase):
    def __init__(self, config):
        super().__init__(config)  # 必需：解析动作布局与索引。
        self.cfg = config  # 当前 Web 手动控制从 self.cfg 读取参数。
        self.robot = MyRobotDriver(config)
        self.camera = MyCameraDriver(config.camera)
        self.current_timestamp = None

    def control_robot(self, action):
        """执行模型输出，其中只包含 gradual/stepwise 区间。"""
        action = np.asarray(action, dtype=float).reshape(-1)
        if action.size != self.action_dim:
            raise ValueError(f"action dim={action.size}, expected={self.action_dim}")

        for name, layout in self.action_layout.items():
            if layout["policy"] == "manual":
                continue
            start, end = int(layout["start"]), int(layout["end"])
            self.execute_action({name: action[start:end].tolist()})

    def execute_action(self, data):
        """执行已切分好的底层命令。"""
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

当 `action_layout` 含有 `presets.Default` 时，适配器通常可以直接继承 `RobotBase` 的 `reset_robot()` 与 Web 端 `_control_robot()`。

### 2. 添加配置

编辑 [`conf/robots_conf.py`](../../conf/robots_conf.py)：

```python
class RobotType(str, Enum):
    AGIBOT_G1 = "agibot_g1"
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
        # manual 区间必须排在所有模型动作区间之后。
        "head": {
            "start": 16, "end": 18, "policy": "manual",
            "presets": {"Default": [0.0, 0.0]},
        },
    })
    return config


def get_robots_config():
    config = ConfigDict()
    config.type = RobotType.MY_ROBOT
    # 保留既有配置……
    config.my_robot = get_my_robot_config()
    return config
```

### 3. 注册 Web 工厂

新机器人类型通过在 [`client/robots/robot_proxy.py`](../../client/robots/robot_proxy.py) 的 `_ROBOT_MODULES` 映射中添加一条记录完成注册，该映射把每个 `RobotType` 取值对应到定义其 `RobotBody` 的模块：

```python
_ROBOT_MODULES: Dict[str, str] = {
    'agibot_g1': 'client.robots.agibot_g1.body_robot',
    'mock': 'client.robots.mock.body_robot',
    'ti5_t170c': 'client.robots.ti5_t170c.body_robot',
    'navi_wa2': 'client.robots.navi_wa2.body_robot',
    'my_robot': 'client.robots.my_robot.body_robot',
}
```

[`web_client/server.py`](../../web_client/server.py) 无需改动：`_create_robot()`（`web_client/server.py:1332`）只是把注册的类型包进 `RobotProxy`，具体的 `RobotBody` 在机器人工作子进程中从 `_ROBOT_MODULES` 导入。未在 `_ROBOT_MODULES` 中注册的类型会报 `Unsupported robot type`。

每次客户端启动都会新建一个 `RobotProxy`，因此不存在需要更新的 SDK 实例复用钩子。

`RobotBody` 接收的是 `config.robots.my_robot` 子段，而不是完整的客户端配置。基类构造函数把它存为 `self.config`，而当前 Web 手动控制读取的是 `self.cfg`，因此适配器应按模板所示建立这个别名。

### 4. 运行

先断开执行器动力或降低速度，再核对维度、方向、单位与限位。机器人类型从配置中的 `robots.type` 读取（见第 2 步），因此在 Web 配置面板中选择即可，无需命令行参数：

```bash
python run_web_client.py
```

## 当前分支的数据规则

### `action_layout`

每个区间必须有 `start`、`end` 和 `policy`；`presets` 可选。

| policy | 用途 | 是否计入模型动作 |
|---|---|---|
| `gradual` | 手臂等连续关节 | 是 |
| `stepwise` | 夹爪等快速/离散维度 | 是 |
| `manual` | 仅 Web 端控制的头部、腰部或底盘 | 否 |

约束：

- 区间为 `[start, end)`，彼此不得重叠。
- 所有 `manual` 区间必须排在全部 `gradual/stepwise` 区间之后，否则 `parse_action_layout()` 会报错。
- `self.action_dim` 只覆盖模型区间；`self.state_dim` 取所有区间中最大的 `end`。
- `self.joint_indices` 包含 `gradual` 索引；`self.step_indices` 包含用于轨迹处理的 `stepwise` 索引。
- 模型、驱动与 `obs.state` 的顺序必须与布局一致。

### Web 手动控制

基类 `_control_robot()` 支持：

- `l_arm/r_arm`、`l_gripper/r_gripper` 和 `l_hand/r_hand`。
- `head`、`waist`、`body`、`wheel` 和 `leg`。
- 用 `-1000` 表示保持某一维度的当前值。
- 使用 `manual_arm_interval` 做 Ruckig 手臂插值。

左右合并后的维度必须为正偶数。使用基类手动控制前，`retrieve_observation()` 必须更新 `current_state`，且 `execute_action()` 必须能处理对应的键。

### 复位预设

基类 `reset_robot()` 依据各区间的 `presets.Default` 构造手动命令。双侧动作使用这种形式：

```python
"presets": {
    "left": {"Default": [...]},
    "right": {"Default": [...]},
}
```

非双侧动作使用这种形式：

```python
"presets": {"Default": [...]}
```

也可以提供完整的 `target_pose`，它会按 `action_layout` 切分。只有当硬件要求特殊复位顺序时才需要重写 `reset_robot()`。

### 观测

最小格式：

```python
{
    "ref_timestamp": timestamp,
    "cam.head": image,
    "obs.state": state,
}
```

- 参考帧未变化时返回 `None`，不要重复提交。
- 图像使用 C 连续的 `uint8 H×W×3`，OpenCV BGR 顺序。
- 以参考时间戳选取多相机中最近的帧。
- `obs.state` 应覆盖完整布局（含 `manual` 区间），并且必须更新 `current_state`。
- 不要在 `retrieve_observation()` 里重连设备、同步写盘或等待运动完成。

## 记录要求

保持观测键、数据类型和形状稳定；保持 `obs.state` 顺序固定；确保模型动作维度等于 `self.action_dim`；相机名称要同时出现在观测与记录配置中。本分支记录的是控制线程的 `action_fitted`，因此驱动侧的映射不会自动体现在记录的动作里。

## 验收清单

- [ ] `RobotBody(config)` 可构造，并调用了 `super().__init__(config)`。
- [ ] `action_dim`、`state_dim` 与关节/步进索引正确。
- [ ] 每个模型动作区间都能到达预期驱动。
- [ ] Web 左右控制与 `-1000` 保持值工作正常。
- [ ] Default 预设能安全复位所有已配置区间。
- [ ] 图像、时间戳、`obs.state` 与 `current_state` 正确且同步。
- [ ] 关节顺序、单位、符号与限位正确。
- [ ] `python run_web_client.py` 能启动并构造机器人。
- [ ] 网络/设备掉线与关机进入安全状态；`close()` 可重复调用。
