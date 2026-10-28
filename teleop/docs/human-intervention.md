# Quest3 Human Intervention: Runtime and Interfaces

This document describes how Quest3 actions enter the VLA client, override policy
actions, hand control back to the policy, and optionally appear in recorded
datasets. For configuration keys, see the
[configuration reference](config-reference.md).

## Data flow

```text
Quest3 Unity app
  -> TCP JSON :8002
  -> teleop/quest3/quest3.py (packet watchdog + status heartbeat)
       controller pose -> IK -> target-native JointState
  -> /target_robot/joint_commands
  -> client/core/teleop_bridge.py
  -> client/core/action_arbiter.py
       fresh TELEOP > fresh POLICY > HOLD
  -> client/core/vla_client.py control tick
  -> robot command + optional LeRobot intervention columns
```

The Quest3 node is normally launched as a child process by the VLA client. It
can also run standalone through `teleop/quest3/quest3_*_node.sh`.

## Supported action contracts

The first 14 dimensions are always two 7-DoF arms. Hand/gripper width comes from
the selected robot configuration:

| Robot/profile | Widths (left + right) | Total |
| --- | --- | --- |
| `agibot_g1` | 1 + 1 gripper | 16 |
| TI5 `hand` | 6 + 6 | 26 |
| TI5 `gripper` | 1 + 1 | 16 |
| TI5 `lhand_rgripper` | 6 + 1 | 21 |
| TI5 `lgripper_rhand` | 1 + 6 | 21 |

Joint names are canonical and ordered as
`left_arm_joint1..7`, `right_arm_joint1..7`, then the left and right hand joints.
The teleop producer must publish values in the robot's native units. For example,
TI5 hands use configured hardware coordinates such as `0..1000`, not normalized
intervention scalars.

The client derives this contract from `robots.<type>.action_layout` through
`teleop/action_mapping.py`. The arm segment must be exactly action indices
`0:14`. A width mismatch is rejected before arbitration.

## ROS2 interface

### Commands: `/target_robot/joint_commands`

The bridge subscribes to `sensor_msgs/msg/JointState` and requires:

- `name` to exactly match the active action layout;
- `position` to have the same length as `name`;
- values to be finite and match the expected action width.

Optional `effort` carries a per-joint human-control mask. This field is a mask,
not torque:

- `1.0`: the corresponding position came from real human input;
- `0.0`: the position was filled from robot feedback or another fallback;
- empty `effort`: legacy producer; the whole action is treated as human input.

The mask is propagated through arbitration and recording. Reset interpolation
publishes no mask.

### Feedback: `/client_robot/joint_states`

The VLA bridge publishes a `JointState` at
`teleop.ros2.joint_state_publish_rate` and immediately after successful robot
commands when human input is not active. Positions are command-biased: the last
robot state is overlaid with the last executed command where possible. Quest3
uses this stream to anchor IK and to fill inactive arms/hands.

### Reset topic: `/custom/custom_a`

Used only when `reset_mode: topic`. A `std_msgs/msg/Float64` rising edge above
`teleop.ros2.reset_threshold` calls the client reset path once. `joint_command`
mode performs reset inside the Quest3 node instead; `none` clears references
without moving the robot.

## Optional ZMQ interface

`ZmqTeleopBridge` is available for producers that send action arrays directly.
It connects a DEALER socket to `teleop.zmq.endpoint` (default
`tcp://127.0.0.1:5570`) and accepts JSON payloads in these forms:

```json
{"action": [0.0, 0.1]}
{"positions": [0.0, 0.1]}
{"action": {"data": [0.0, 0.1], "dtype": "float64", "shape": [2]}}
```

The bridge sends a periodic
`{"type": "teleop_bridge_ready", "identity": ...}` heartbeat. ZMQ actions are
padded to the configured action width if shorter and rejected if larger. ZMQ
messages do not carry a mask, so the entire action is treated as human input.

## Arbitration and safety

`ActionArbiter` is thread-safe and applies this priority every control tick:

1. fresh `TELEOP`;
2. otherwise fresh `POLICY`;
3. otherwise `HOLD` the last selected action.

Default freshness windows are `controller.teleop_timeout_s = 0.15` and
`controller.policy_timeout_s = 0.5`. A synthetic `HOLD` is not accepted as an
input source.

Policy transitions use `controller.action_transition_steps` (default 64) to
blend discontinuities. Teleop commands bypass that blend and set the filter
anchor directly, so human motion remains open-loop and responsive.

Before submission, `VLAClient._validate_teleop_bridge_action()` enforces action
width and finiteness and applies the outlier guard:

- max single-arm-joint delta (`teleop_outlier_max_arm_joint_delta`);
- max arm-vector L2 delta (`teleop_outlier_max_arm_norm_delta`);
- max hand delta (`teleop_outlier_max_gripper_delta`, scaled to native units).

Malformed or implausible packets are dropped. A teleop baseline is only used
while it is fresh; after a session timeout the last executed command or measured
state is used instead. While a live session has a fresh safe action, that action
is held through an isolated bad packet. After
`teleop_outlier_reanchor_after_rejects` consecutive rejects, teleop ownership is
released so policy or a later intervention can recover. Set
`teleop_outlier_guard_enabled: false` only for a trusted producer.

## Human-control session

The Quest3 node publishes commands only while an arm, hand, or reset output is
requested.

- Left/right arm control is activated independently by holding that side's grip
  button above `trigger_threshold`.
- Activation captures the controller pose, robot joint state, and FK
  end-effector pose. Subsequent motion is relative to that anchor.
- Releasing below `trigger_release_threshold` ends the session.
- Continuous hand modes accept the analog trigger; discrete mode advances on
  rising edges using full native hand vectors.
- `proportional_latch_on_release` keeps the highest reached proportional target
  when the hand session ends.

Arm control remains open-loop: robot control uses a latest-wins non-blocking
queue and is not throttled by observation polling.

## Policy handoff

When fresh teleop stops, the client does not jump immediately to an old policy
chunk:

1. The last executed human action becomes the handoff hold action.
2. The policy generation is invalidated and queued policy chunks are cleared.
3. The robot holds the human action while the client waits for a fresh
   inference result.
4. The new policy chunk is fused from the human hold action.
5. After the first fused policy action is published, teleop handoff ends and
   normal policy control resumes.

Fresh teleop input during the wait cancels the handoff and returns control to the
human. The status field `teleop_policy_handoff_active` reports this state.

## Reset behavior

- `joint_command`: interpolate from the latest command/state to
  `robots.<type>.reset_robot_pos`, publish each step on the joint command topic,
  then wait for fresh joint feedback.
- `topic`: publish Float64 reset edges; the VLA bridge converts the rising edge
  into one reset callback.
- `none`: clear teleop references only.

The Web Reset button and Quest3 reset share `reset_robot_pos`. The Web/API Reset
path returns HTTP 409 while fresh Quest3 input is active.

## Status and Web behavior

The Web Client consumes runtime fields including:

- `teleop_enabled`, `teleop_supported`
- `teleop_bridge_running`, `teleop_device_connected`
- `teleop_device_state`, `teleop_device_message`
- `teleop_human_active`, `teleop_policy_handoff_active`

`GET /api/client/teleop/status` returns the same device/bridge snapshot even
before a runtime client exists. Managed Quest3 states include `starting`,
`listening`, `connected`, `stopped`, and `error`; the client snapshot can also
report `disabled`, `unavailable`, or `unsupported`. A connection that stops
sending packets is closed after `tcp_client_timeout_sec`, and the server then
accepts the headset's next connection. The API exposes `last_packet_age_s`,
`total_packets`, `status_age_s`, `left_tracking_valid`, and
`right_tracking_valid` for connection and tracking diagnosis.

The UI changes the runtime badge from **RUNNING** to **TELEOP** while human input
is fresh, disables Reset, and reports whether the Quest3 TCP device connected.
Pause/Stop tears down the bridge; Resume/Start recreates it when enabled.

## Recording

Set `record.record_teleop_fields: true` before starting a new dataset. The
recorder then adds these per-frame columns:

| Column | Meaning |
| --- | --- |
| `action` | Action actually sent to the robot, regardless of source. |
| `teleop_action` | Executed action while `TELEOP` is selected; zeros otherwise. |
| `teleop_action_mask` | Entries of `teleop_action` carrying real human data; all true if the producer supplied no mask. |
| `rejected_action` | Policy action that would have run during a teleop override; zeros when unavailable. |
| `rejected_action_mask` | Entries replaced by human control. |
| `is_teleop` | True only when fresh human input selected the executed action. |

During teleop-to-policy handoff, the executed action is held but `is_teleop` is
false. Existing LeRobot datasets keep their original schema, and appending to a
legacy dataset does not mix new columns into it. The setting takes effect on the
next recording.

See `test/test_teleop_data_recording.py` for schema and mask examples.
