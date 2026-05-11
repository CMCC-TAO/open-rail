# Ti5_t170c 机器人适配器（vla_infer-master/client/robots）

这是 `vla_infer-master` 里的 **Ti5_t170c** 机器人适配实现，用于让 `VLAClient` 能像使用 A2D 一样完成：

- 读取观测：返回 `ref_timestamp`、`cam.*`（相机占位先不接入）、`obs.state`
- 下发控制：接收 VLA 动作并通过 ROS2 topic 下达到 Ti5 的驱动节点

## 适配位置与实现状态

- 适配器代码：`client/robots/ti5_t170c/body_robot.py`
- 目前实现范围（Phase-1）：
  - 已支持 **双臂 14 维控制**（left 7 + right 7）
  - 目前 **未接入真实夹爪/灵巧手**：VLA 动作的后 2 维（通常对应 gripper）先被忽略
  - 相机：`cam.head` 使用**黑图占位**，保证 `VLAClient._process_data()` 能编码并把数据发给 server

## VLAClient 需要的观测/控制契约

### 1) `retrieve_observation()` 返回值（dict）
返回至少包含以下 key（来自 `client/core/vla_client.py` 的使用方式）：

- `ref_timestamp`: 标量（这里用 ROS2 `JointState.header.stamp` 转纳秒的近似时间戳）
- `cam.head`: 一个 `numpy.ndarray` 图像（占位黑图，形状 `H x W x 3`、dtype `uint8`）
- `obs.state`: `np.ndarray`，1D（当前 Phase-1 按 A2D 维度预留为 20 维）
  - `obs.state[0:7]`：left arm 7 维
  - `obs.state[7:14]`：right arm 7 维
  - 其余（gripper/head/waist）当前填 0

`retrieve_observation()` 具有“新帧门控”：

- 当 ROS2 反馈时间戳没有更新时会返回 `None`（`VLAClient` 会跳过本次发送）

### 2) `control_robot(action)` 输入

- `action` 是 `np.ndarray`，维度至少 14
- 目前支持：
  - `action[:7]` → left arm
  - `action[7:14]` → right arm
- `action[14:16]`（通常 gripper）当前不处理

## ROS2 topic 映射（对接 `ti5_t170c_driver`）

根据 `ti5_t170c_driver/数采接口(1).md` 与 `tj_arm_controller` 源码，Ti5 双臂对外接口为：

- 读取（反馈）：
  - `/left_arm/joint_states`  （`sensor_msgs/msg/JointState`）
  - `/right_arm/joint_states` （`sensor_msgs/msg/JointState`）
- 写入（控制）：
  - `/left_arm/joint_cmd`  （`sensor_msgs/msg/JointState`）
  - `/right_arm/joint_cmd` （`sensor_msgs/msg/JointState`）

关节名顺序（由 `tj_arm_controller` 的 joint_names 定义决定）：

- left arm 7 维：
  - `L_SHOULDER_P_JOINT`
  - `L_SHOULDER_R_JOINT`
  - `L_SHOULDER_Y_JOINT`
  - `L_ELBOW_JOINT`
  - `L_WRIST_Y_JOINT`
  - `L_WRIST_R_JOINT`
  - `L_WRIST_P_JOINT`
- right arm 7 维：
  - `R_SHOULDER_P_JOINT`
  - `R_SHOULDER_R_JOINT`
  - `R_SHOULDER_Y_JOINT`
  - `R_ELBOW_JOINT`
  - `R_WRIST_Y_JOINT`
  - `R_WRIST_R_JOINT`
  - `R_WRIST_P_JOINT`

## 在 `vla_infer-master` 中的配置接入

已完成的接入点：

- `conf/robots_conf.py`
  - 新增 `RobotType.TI5_T170C = 'ti5_t170c'`
  - 新增 `get_ti5_t170c_config()`：配置 topic 名与关节名顺序
- `run_client.py`
  - `--robots_type` 增加 `ti5_t170c`
  - `get_robot()` 增加分支：`client/robots/ti5_t170c/body_robot.py`

## 启动与运行（Phase-1：只跑双臂）

### 0) 前置条件

1. 已安装 ROS2 Humble，并能使用 `ros2` 命令
2. `ti5_t170c_driver` 工作空间已 build 且 source（提供 topics/services）
3. `vla_infer-master` 的运行 Python 环境需要包含依赖：
   - `rclpy`、`sensor_msgs`
   - `opencv-python`（`vla_infer-master/client/robots/base_robot.py` 会在 import 时用到 `cv2`）

### 1) 启动 Ti5 双臂控制器

```bash
cd ti5_t170c_driver
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash

# 先单独确认机械臂反馈话题可用
ros2 launch tj_arm_controller tj_arm_controller.launch.py
```

用下面命令验证反馈是否在更新（任选一个）：

```bash
ros2 topic echo /left_arm/joint_states
# 或
ros2 topic echo /right_arm/joint_states
```

### 2) 启动 vla server（如果你需要推理链路）

```bash
cd vla_infer-master
python run_server.py
```

### 3) 启动 vla client（Ti5）

```bash
cd vla_infer-master
source /opt/ros/humble/setup.bash
source ../ti5_t170c_driver/install/setup.bash

python run_client.py --robots_type ti5_t170c
```

## 故障排查

### 1) `ModuleNotFoundError: No module named 'cv2'`

原因：`vla_infer-master` 的 Python 环境缺少 `opencv-python`。

解决：在你运行 `run_client.py` 的 Python 环境里安装 `opencv-python` 后重试。

### 2) rclpy 导入失败 / topics 无数据

- 确认已 `source /opt/ros/humble/setup.bash`
- 确认已 `source ti5_t170c_driver/install/setup.bash`
- 确认 `tj_arm_controller` 已启动并能看到 `/left_arm/joint_states` 或 `/right_arm/joint_states` 在更新

## 下一步建议（把方案补齐到完整 A2D 契约）

1. 接入真实相机（替换 `cam.head` 占位图）
2. 接入夹爪/灵巧手，并实现 `action[14:16]` → 夹爪控制 topic，同时在 `obs.state` 里填入对应状态维度
3. 可选：扩展 head/waist/wheel 的控制与观测，使 `obs.state` 更完整对齐 A2D

