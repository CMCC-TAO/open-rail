# New Robot Integration Guide

[中文版本](add-new-robot.zh-CN.md)

## Quick Start

The example robot `my_robot` has two 7-DoF arms, two gripper dimensions, and a 2-DoF head used only by manual control.

### 1. Create the adapter

```text
client/robots/my_robot/
├── __init__.py
└── body_robot.py
```

Minimal `body_robot.py`:

```python
import numpy as np

from ..base_robot import RobotBase
from .driver import MyRobotDriver, MyCameraDriver


class RobotBody(RobotBase):
    def __init__(self, config):
        super().__init__(config)  # Required: parses action layout and indices.
        self.cfg = config  # Current Web manual control reads parameters from self.cfg.
        self.robot = MyRobotDriver(config)
        self.camera = MyCameraDriver(config.camera)
        self.current_timestamp = None

    def control_robot(self, action):
        """Execute model output, which contains gradual/stepwise segments only."""
        action = np.asarray(action, dtype=float).reshape(-1)
        if action.size != self.action_dim:
            raise ValueError(f"action dim={action.size}, expected={self.action_dim}")

        for name, layout in self.action_layout.items():
            if layout["policy"] == "manual":
                continue
            start, end = int(layout["start"]), int(layout["end"])
            self.execute_action({name: action[start:end].tolist()})

    def execute_action(self, data):
        """Execute an already segmented low-level command."""
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

When `action_layout` contains `presets.Default`, the adapter can normally inherit `reset_robot()` and Web `_control_robot()` directly from `RobotBase`.

### 2. Add configuration

Edit [`conf/robots_conf.py`](../../conf/robots_conf.py):

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
        # Manual segments must follow every model-action segment.
        "head": {
            "start": 16, "end": 18, "policy": "manual",
            "presets": {"Default": [0.0, 0.0]},
        },
    })
    return config


def get_robots_config():
    config = ConfigDict()
    config.type = RobotType.MY_ROBOT
    # Keep existing configurations...
    config.my_robot = get_my_robot_config()
    return config
```

### 3. Register both factories

CLI factory: add to `get_robot()` in [`run_client.py`](../../run_client.py):

```python
elif robot_type == RobotType.MY_ROBOT:
    from client.robots.my_robot.body_robot import RobotBody
    return RobotBody(robot_config)
```

Web factory: add a creation branch to `_get_robot()` in [`web_client/server.py`](../../web_client/server.py):

```python
elif robot_type == RobotType.MY_ROBOT:
    from client.robots.my_robot.body_robot import RobotBody
    robot_instance = RobotBody(robot_config)
```

To reuse the same SDK object after Web stop/start, also add a type/module match to the reuse section at the beginning of `_get_robot()`. Otherwise, the Web factory closes and recreates it.

`RobotBody` receives the `config.robots.my_robot` subsection, not the complete Client configuration. The base constructor stores it as `self.config`, while current Web manual control reads `self.cfg`, so the adapter should set the alias shown in the template.

### 4. Run

Disconnect actuators or reduce speed first, then verify dimensions, direction, units, and limits:

```bash
python run_client.py --robots_type my_robot
python run_web_client.py
```

## Current Branch Data Rules

### `action_layout`

Every segment requires `start`, `end`, and `policy`; `presets` is optional.

| policy | Purpose | Included in model action |
|---|---|---|
| `gradual` | Continuous joints such as arms | Yes |
| `stepwise` | Grippers or fast/discrete dimensions | Yes |
| `manual` | Web-only head, waist, or wheels | No |

Constraints:

- Ranges use `[start, end)` and must not overlap.
- Every `manual` segment must follow all `gradual/stepwise` segments; otherwise `parse_action_layout()` raises an error.
- `self.action_dim` covers model segments only; `self.state_dim` is the largest `end` across all segments.
- `self.joint_indices` contains `gradual` indices; `self.step_indices` contains `stepwise` indices for trajectory processing.
- Model, driver, and `obs.state` ordering must match the layout.

### Web manual control

The base `_control_robot()` supports:

- `l_arm/r_arm`, `l_gripper/r_gripper`, and `l_hand/r_hand`.
- `head`, `waist`, `body`, `wheel`, and `leg`.
- `-1000` to keep the current value of an individual dimension.
- Ruckig arm interpolation using `manual_arm_interval`.

The combined left/right dimension must be positive and even. Before using base manual control, `retrieve_observation()` must update `current_state`, and `execute_action()` must handle the corresponding key.

### Reset presets

The base `reset_robot()` builds manual commands from each segment's `presets.Default`. Use this form for bilateral actions:

```python
"presets": {
    "left": {"Default": [...]},
    "right": {"Default": [...]},
}
```

Use this form for non-bilateral actions:

```python
"presets": {"Default": [...]}
```

A complete `target_pose` may also be supplied and is sliced by `action_layout`. Override `reset_robot()` only when hardware requires a special reset order.

### Observation

Minimal format:

```python
{
    "ref_timestamp": timestamp,
    "cam.head": image,
    "obs.state": state,
}
```

- Return `None` when the reference frame is unchanged; do not submit duplicates.
- Use C-contiguous `uint8 H×W×3` images in OpenCV BGR convention.
- Select nearest multi-camera frames using the reference timestamp.
- `obs.state` should cover the complete layout, including `manual` segments, and must update `current_state`.
- Do not reconnect devices, write synchronously to disk, or wait for motion completion inside `retrieve_observation()`.

## Recording Requirements

Keep observation keys, dtypes, and shapes stable; keep `obs.state` order fixed; ensure model action dimension equals `self.action_dim`; and include camera names in both observations and recording configuration. This branch records control-thread `action_fitted`, so driver-side mapping is not automatically reflected in recorded actions.

## Validation Checklist

- [ ] `RobotBody(config)` constructs and calls `super().__init__(config)`.
- [ ] `action_dim`, `state_dim`, and joint/step indices are correct.
- [ ] Every model-action segment reaches the intended driver.
- [ ] Web left/right control and `-1000` hold work correctly.
- [ ] Default presets reset every configured segment safely.
- [ ] Images, timestamps, `obs.state`, and `current_state` are correct and synchronized.
- [ ] Joint order, units, signs, and limits are correct.
- [ ] Both `run_client.py` and `run_web_client.py` can construct the robot.
- [ ] Network/device loss and shutdown enter a safe state; `close()` is repeatable.
