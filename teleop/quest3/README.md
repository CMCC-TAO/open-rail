# Quest3 Teleop Bridge

Python ROS2 bridge for controlling A2D or TI5-style robot arms from Quest3 controller packets.

The bridge receives newline-delimited JSON over TCP from the Quest3 Unity client and publishes the VLA teleop command interface directly:

- `sensor_msgs/msg/JointState` on `/target_robot/joint_commands`
- optionally, `std_msgs/msg/Float64` reset edges on `/custom/custom_a` when `reset_mode: topic`

The old `joint_ros_to_tcp_node` and `tcp_to_ros_joint_node` path is not used here because the VLA client consumes ROS topics directly.

## Run

Start A2D:

```bash
teleop/quest3/quest3_a2d_node.sh
```

Start TI5 T170C:

```bash
teleop/quest3/quest3_ti5_t170c_node.sh
```

Useful runtime overrides:

```bash
teleop/quest3/quest3_a2d_node.sh \
  --listen-port 8002 \
  --joint-command-topic /target_robot/joint_commands \
  --joint-states-topic /joint_states \
  --reset-mode joint-command
```

The launch scripts change into the repository root before running `python3 -m teleop.quest3.quest3`.

## Controls

Arm teleop is enabled per side by pressing that controller's trigger past `trigger_threshold`.

When a trigger first becomes active, the bridge captures:

- the controller pose at press time
- the robot joint state at press time
- the FK end-effector pose at press time

While the trigger stays held, controller motion is applied as a delta from that fixed reference. Releasing the trigger clears the reference, so the next press starts from a fresh robot state. Left and right triggers are independent.

The gripper command uses the controller grip input:

- grip past `grip_threshold` closes toward `1.0`
- secondary button opens toward `0.0`
- `gripper_speed` controls the normalized command rate in units per second

## State Source

The bridge waits for `/joint_states` before publishing teleop or reset joint commands. After reset completes, it waits for fresh joint feedback again before accepting new trigger-relative teleop commands.

Command vector order is fixed:

```text
left_arm_joint1..7, right_arm_joint1..7, left_hand_joint1, right_hand_joint1
```

`min_action` and `max_action` clamp the final 16-element command vector before publishing.

## Reset

Quest primary button behavior is selected by `reset_mode`, which defaults to `joint_command`:

- `joint_command` interpolates from the latest received joint state to `reset_action` and publishes each step as a `JointState` on `joint_command_topic`
- `topic` publishes reset edges to `reset_topic`
- `none` clears teleop trigger references without commanding a reset

In `topic` mode, primary button edges publish to the reset topic:

- press publishes `reset_press_value`
- release publishes `reset_release_value`
- if `reset_pulse_on_press` is true, press publishes press then release immediately

In `joint_command` mode, the 16-element `reset_action` uses the fixed command vector order and is clamped by `min_action` / `max_action`. The interpolation duration is controlled by `reset_interp_duration_sec`; `reset_start_hold_sec` optionally repeats the current command briefly before moving.

## IK

A2D uses the CasADi backend:

```yaml
ik:
  solver_backend: casadi
  urdf_path: ../urdf/a2d_vla_zero_state.urdf
```

Relative URDF paths are resolved from the YAML file's directory. A2D keeps its URDF at:

```text
teleop/quest3/urdf/a2d_vla_zero_state.urdf
```

TI5 may keep `urdf_path` pointed at a `.xacro`. If a xacro uses ROS package lookup, add the required install prefixes to `ik.xacro_ament_prefix_paths`.

The active ROS Python environment must provide the configured backend:

- `casadi_ik_cpp.PinocchioCasadiChunkKineSolver` for `solver_backend: casadi`
- `kine_solver_py.SingleArmKineSolver` for `solver_backend: cpp`

## Coordinate Transforms

The Quest packet pose is first converted from Unity coordinates into the VR base convention used by the original bridge. Controller orientation is then adjusted by `controller_y_rotation_deg`.

Relative controller positions can be converted with `rot_base_from_vr_to_urdf`:

```text
p_urdf = base_rotation_mat @ p_vr
```

Relative controller rotations are converted to the URDF end-effector convention with the per-arm matrix:

```text
R_urdf = rotation_mat @ R_vr @ rotation_mat.T
```

A2D uses one shared `rot_arm_from_vr_to_urdf` matrix for both arms because the arm end-effector frames share the same axis convention. Per-side keys are still supported for robot configs that need them.

## A2D Simulation Forwarder

To forward `/target_robot/joint_commands` to A2D trajectory action controllers, run:

```bash
python3 -m teleop.quest3.joint_command_to_sim_a2d \
  --joint-command-topic /target_robot/joint_commands \
  --joint-states-topic /joint_states \
  --reset-topic /custom/custom_a \
  --left-arm-action /left_arm_controller/follow_joint_trajectory \
  --right-arm-action /right_arm_controller/follow_joint_trajectory \
  --head-action /head_controller/follow_joint_trajectory \
  --body-action /body_controller/follow_joint_trajectory
```

The forwarder also listens for reset edges and can interpolate the latest known arm and hand state toward its built-in A2D reset target.
