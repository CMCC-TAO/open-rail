# Quest3 and Client Configuration Reference

This reference covers the teleop configuration added to the client. For the
broader client configuration model, see
[`docs/configuration.md`](../../docs/configuration.md).

## Configuration sources

| Source | Purpose |
| --- | --- |
| `conf/client_conf.py` | Built-in defaults for `teleop`, `controller`, and `record`. |
| Web Client YAML (`--conf`, default `conf/default_conf.yaml`) | Persisted runtime overrides. The file is created on first Web save and is git-ignored. |
| Web Configuration panel | Staged edits; Apply patches the running config. |
| Quest3 YAML profiles | Robot-specific button mapping, reset, hand mapping, IK, and limits. |
| CLI flags | Per-process overrides for standalone Quest3 nodes and forwarders. |

Quest3 profile selection is automatic:

| Robot type | Profile |
| --- | --- |
| `agibot_g1` (legacy alias `a2d`) | `teleop/quest3/config/a2d.yaml` |
| `ti5_t170c` | `teleop/quest3/config/ti5_t170c.yaml` |

`teleop.devices.quest3.config_path`, `auto_config_path`, and
`config_path_by_robot` are internal/protected fields. The Web API rejects
attempts to patch them directly. Changing `robots.type` updates the mapping and
forces teleop off for unsupported robots.

## Web/client teleop group

Defaults are defined in `get_teleop_config()` in `conf/client_conf.py`.

| Key | Default | Meaning |
| --- | --- | --- |
| `teleop.use_teleop` | `false` | Master switch. When true and the client is running, the bridge and managed Quest3 process start. |
| `teleop.control_device` | `quest3` | Managed device type. The Web UI exposes only `quest3`. |
| `teleop.ros2.topic` | `/target_robot/joint_commands` | Joint command topic consumed by the bridge. |
| `teleop.ros2.reset_topic` | `/custom/custom_a` | Float64 reset topic for `reset_mode: topic`. |
| `teleop.ros2.joint_state_topic` | `/client_robot/joint_states` | Command-biased state published for Quest3 IK/fallback. |
| `teleop.ros2.joint_state_publish_rate` | `30.0` | State heartbeat rate in Hz; `0` disables the timer. |
| `teleop.ros2.reset_threshold` | `0.5` | Rising-edge threshold for topic-based reset. |
| `teleop.ros2.node_name` | `vla_infer_teleop_bridge` | ROS2 bridge node name. |
| `teleop.devices.quest3.no_adb_reverse` | `false` | Skip managed `adb reverse tcp:<port>` setup. |
| `teleop.devices.quest3.python` | current interpreter | Optional Python executable override for the managed node. |
| `teleop.devices.quest3.listen_port` | profile value | Optional TCP listen-port override. |
| `teleop.devices.quest3.command` | unset | Optional full command override for a custom producer. |
| `teleop.devices.quest3.log_path` | `logs/quest3_teleop.log` | Captured stdout/stderr from the managed Quest3 process. |

Apply behavior:

- Enabling/disabling teleop on a running client starts/stops the bridge.
- Applying device/topic changes while enabled recreates the bridge.
- Pause/Stop stops the bridge; Resume/Start restarts it when enabled.
- Start the runtime after enabling teleop if the device-connect check reports it
  unavailable.

`bridge_type` and `teleop.zmq.*` are supported by the programmatic bridge factory
(`ros2` by default, or `zmq`) but are not part of the Web default config.

## Client controller timing and safety

These fields live under `controller` in `conf/client_conf.py`.

| Key | Default | Meaning |
| --- | --- | --- |
| `teleop_timeout_s` | `0.15` | Teleop remains authoritative only while newer input arrives inside this window. |
| `policy_timeout_s` | `0.5` | Freshness window for policy actions. |
| `action_transition_steps` | `64` | Blend length when policy/hold source changes. Teleop is passed through directly. |
| `action_transition_max_delta_per_step` | `None` | Optional absolute per-tick output clamp for blended actions. |
| `teleop_outlier_guard_enabled` | `true` | Enable teleop jump validation. |
| `teleop_outlier_max_arm_joint_delta` | `0.5` | Max absolute change for any one arm joint per packet. |
| `teleop_outlier_max_arm_norm_delta` | `1.2` | Max L2 change across 14 arm joints per packet. |
| `teleop_outlier_max_gripper_delta` | `1.0` | Max hand change, scaled by the native hand preset scale. |
| `teleop_outlier_reanchor_after_rejects` | `5` | Release teleop ownership after this many consecutive rejected packets. |
| `teleop_outlier_log_interval_s` | `1.0` | Warning-log rate limit. |

## Recording configuration

Defined in `get_record_data_config()` in `conf/save_conf.py`.

| Key | Default | Meaning |
| --- | --- | --- |
| `record.record_teleop_fields` | `true` | Add intervention columns to new datasets. The Web panel applies this immediately; it takes effect on the next recording. |

The added columns are `teleop_action`, `teleop_action_mask`,
`rejected_action`, `rejected_action_mask`, and `is_teleop`. Existing datasets
retain their schema and cannot be migrated by toggling this option.

## Robot-side configuration

`conf/robots_conf.py` supplies the teleop action contract and reset pose:

- `action_layout.arm` must cover indices `0:14`.
- `action_layout.hand` or `action_layout.gripper` determines hand width from the
  left/right `Default` presets.
- `reset_robot_pos` is shared by Quest3 reset and the Web Reset button.
- TI5 `hand_type` profiles are `hand` (6+6), `gripper` (1+1),
  `lhand_rgripper` (6+1), and `lgripper_rhand` (1+6).

The Quest3 node can also receive `action_names` and `native_reset_action` from
the VLA bridge. These are generated from the active robot config; users do not
normally set them.

## Quest3 profile YAML

Profiles live in `teleop/quest3/config/`. Relative IK paths are resolved from
the YAML file's directory.

### Process, topics, and reset

| Key | Meaning |
| --- | --- |
| `robot` | Robot identifier used in the Quest3 ROS node name and default profile lookup. |
| `listen_port` | TCP port for newline-delimited JSON from the Unity app. |
| `tcp_client_timeout_sec` | Close an idle/half-open Quest3 connection after this many seconds without packets; `0` disables the watchdog. |
| `tcp_status_publish_interval_sec` | Refresh the parent-process status heartbeat while listening or connected. |
| `adb_reverse_reassert_sec` | While disconnected, periodically recreate the USB `adb reverse` mapping; `0` disables it. |
| `control_frequency` | Quest3 control/IK loop rate in Hz. |
| `joint_command_topic` | Published `JointState` command topic. |
| `joint_states_topic` | State feedback consumed for activation anchors and inactive-side fallback. |
| `reset_mode` | `joint_command`, `topic`, or `none`; aliases include `joint`, `command`, `off`, and `disabled`. |
| `reset_topic` | Float64 topic used only by `reset_mode: topic`. |
| `reset_press_value`, `reset_release_value` | Topic-mode reset edge values. |
| `reset_pulse_on_press` | Publish press then release immediately. |
| `reset_interp_duration_sec` | Joint-command reset interpolation duration. |
| `reset_start_hold_sec` | Hold current command briefly before reset interpolation. |

### Arm control

| Key | Meaning |
| --- | --- |
| `trigger_threshold` | Grip-button threshold that activates arm control. |
| `trigger_release_threshold` | Lower hysteresis threshold that ends arm control. |
| `teleop_transition_duration_sec` | Smooth enter/exit duration for dynamic anchoring. |
| `position_scale`, `orientation_scale` | Multipliers for controller relative motion. |
| `controller_y_rotation_deg` | Fixed controller-local Y rotation before relative motion. |
| `rot_*_from_vr_to_urdf` | Coordinate-transform matrices from VR to URDF frames. |

Left and right arm activation is independent. Activation captures a fresh
controller/robot/FK anchor; manual arm output then runs open-loop.

### Hand/gripper control

| Key | Meaning |
| --- | --- |
| `hand_control_mode` | Shared default: `incremental`, `proportional`, or `discrete`. |
| `left_hand_control_mode`, `right_hand_control_mode` | Optional per-side override. |
| `left_hand_discrete_values`, `right_hand_discrete_values` | Full native hand vectors for discrete stepping. |
| `left_hand_continuous_range`, `right_hand_continuous_range` | Native values at scalar `0.0` and `1.0`; required for multi-coordinate continuous hands. |
| `gripper_input_min`, `gripper_input_max` | Analog input range for proportional mode. |
| `proportional_activation_threshold`, `proportional_release_threshold` | Hysteresis for proportional control. |
| `proportional_latch_on_release` | Keep the highest proportional target reached in a session. |
| `gripper_command_min`, `gripper_command_max` | Command range. |
| `grip_threshold` | Input threshold for incremental closing/opening. |
| `gripper_speed` | Incremental command speed in normalized units per second. |

`hand_control_mode: incremental` and `proportional` use one scalar internally and
expand it through the continuous range. `discrete` values must already match the
native hand width. Mixed profiles can use different modes per side; a continuous
multi-coordinate hand without a range is rejected.

### IK and limits

| Key | Meaning |
| --- | --- |
| `ik.enabled` | Enable controller-driven arm IK. |
| `ik.solver_backend` | `cpp` (`kine_solver_py`) or `casadi` (`casadi_ik_cpp`). |
| `ik.urdf_path` | Plain URDF, resolved relative to the profile. |
| `ik.ref_frame`, `ik.rotation_type` | Solver reference frame and orientation representation. |
| `ik.left` / `ik.right` | `base_link` and `tip_link` for each IK chain. |
| `ik.pos_weight`, `ori_weight`, `smooth_weight`, `rest_weight` | CasADi IK optimization weights. |
| `min_action`, `max_action` | Internal command clamps before hand expansion. |

A2D uses the CasADi backend and the shared arm-frame transform. TI5 uses the
`cpp` backend and `ti5_robot_tjv2.urdf`; the retired T170C xacro is not used.

## Example: Web configuration

Use the Web panel when possible:

```text
Robot Type: ti5_t170c
teleop.use_teleop: true
teleop.control_device: quest3
record.record_teleop_fields: true
```

The persisted YAML equivalent is:

```yaml
teleop:
  use_teleop: true
  control_device: quest3

record:
  record_teleop_fields: true
```

Do not add a manual `config_path`; the active robot type supplies it.

## Example: standalone Quest3 node

```bash
source /opt/ros/humble/setup.bash

teleop/quest3/quest3_ti5_t170c_node.sh \
  --listen-port 8002 \
  --joint-command-topic /target_robot/joint_commands \
  --joint-states-topic /client_robot/joint_states \
  --reset-mode joint_command
```

Useful CLI overrides include `--reset-topic`, `--reset-action`,
`--action-names`, `--native-reset-action`, `--status-file`, and
`--no-adb-reverse`. The VLA client normally supplies the action names, native
reset vector, and status file automatically.

## Example: trajectory forwarder

A2D:

```bash
python3 -m teleop.quest3.joint_command_to_sim_a2d \
  --joint-command-topic /target_robot/joint_commands \
  --joint-states-topic /joint_states \
  --reset-topic /custom/custom_a
```

TI5 T170C:

```bash
python3 -m teleop.quest3.joint_command_to_ti5_t170c \
  --joint-command-topic /target_robot/joint_commands \
  --reset-topic /custom/custom_a
```

Use `--left-arm-action`, `--right-arm-action`, and the module's other
`--help` options to match the downstream action servers.

## Validation checklist

1. The selected robot is `agibot_g1` or `ti5_t170c`.
2. `teleop.use_teleop` is true and the runtime is running.
3. Quest3 status reaches `connected`; `listening` means no headset connected.
4. Command joint names exactly match the active action layout.
5. The action width matches the robot hand profile.
6. `ik.urdf_path` and the required ROS Python IK backend are available.
7. For recording, the dataset is new or already has the intervention columns.
