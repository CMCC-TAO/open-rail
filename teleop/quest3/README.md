# Quest3 Teleop and Human Intervention

Quest3 can override VLA policy actions while the runtime is active. A small
ROS2 bridge receives target-native joint commands from the Quest3 node, the VLA
client arbitrates between human and policy actions, and optional intervention
fields are stored with new LeRobot datasets.

Detailed documentation:

- [Human intervention runtime and interfaces](../docs/human-intervention.md)
- [Quest3 and client configuration reference](../docs/config-reference.md)
- [General client configuration](../../docs/configuration.md)
- [Web console guide](../../docs/web-console.md)

## Supported robots

| Web `robots.type` | Quest3 profile | Native action width |
| --- | --- | --- |
| `agibot_g1` | `teleop/quest3/config/a2d.yaml` | 16: 14 arm + 2 gripper |
| `ti5_t170c` | `teleop/quest3/config/ti5_t170c.yaml` | 16/21/26, selected by TI5 `hand_type` |

Quest3 teleop is hidden and forced off for all other robot types. Switching
`robots.type` automatically selects the profile above; the profile path is an
internal setting and cannot be patched through the Web API.

## Quick start: Web Client

1. Start the inference server and Web Client.
2. Select `agibot_g1` or `ti5_t170c` as **Robot Type**.
3. In **Configuration → teleop**, set:
   - `use_teleop: true`
   - `control_device: quest3`
4. Apply the configuration, then press **Start**. The client owns the Quest3
   subprocess and starts the bridge automatically.
5. Connect the Quest3 app and verify that the runtime badge changes to
   **TELEOP** while fresh human input is controlling the robot.

Do not also start a standalone Quest3 node while the Web Client manages it.

## Controls

The Unity app maps the physical buttons as follows:

- **Grip button**: arm teleoperation enable. Each side is independent.
- **Trigger**: hand/gripper control. Proportional mode follows its analog
  value, incremental mode closes/opens toward the configured limits, and
  discrete mode steps through configured native hand vectors.
- **Secondary button**: open the gripper in incremental mode, or move to the
  previous discrete hand value.
- **Primary button**: reset. The default `joint_command` mode interpolates to
  `robots.<type>.reset_robot_pos`, the same target used by the Web Reset button.

While an arm grip is held, controller motion is applied relative to the pose
captured at activation. Releasing it ends human control; the last human command
is held until a fresh policy chunk arrives, then policy control resumes
automatically. No resume command is required.

Web Reset is disabled while fresh Quest3 input is active. Teleop is stopped on
Pause/Stop and restarted on Resume/Start when `use_teleop` remains enabled.

## Recording interventions

Set `record.record_teleop_fields: true` before starting a new LeRobot dataset.
New datasets then contain:

- `teleop_action`, `teleop_action_mask`
- `rejected_action`, `rejected_action_mask`
- `is_teleop`

The existing `action` column always stores the action actually sent to the
robot. Existing datasets keep their current schema; the option does not migrate
them. See the [runtime and recording details](../docs/human-intervention.md#recording).

## Configuration locations

| Configuration | Location |
| --- | --- |
| Client teleop switch, topics, managed Quest3 process | `conf/client_conf.py` → `get_teleop_config()`; persisted by the Web Client YAML |
| Arm/hand timing, freshness, transition, outlier guard | `conf/client_conf.py` → `get_controller_config()` |
| Robot action layout, hand width, reset pose | `conf/robots_conf.py` |
| Quest3 controls, reset, hand mapping, IK, limits | `teleop/quest3/config/*.yaml` |
| Intervention recording columns | `conf/save_conf.py` → `record.record_teleop_fields` |

For every key, value ranges, topics, action-width rules, and examples, use the
[configuration reference](../docs/config-reference.md).

## Standalone bridge

Use these scripts for hardware debugging or when another process supplies the
joint-state feedback. Run from the repository root with ROS2 sourced.

```bash
teleop/quest3/quest3_a2d_node.sh
teleop/quest3/quest3_ti5_t170c_node.sh
```

Common overrides:

```bash
teleop/quest3/quest3_ti5_t170c_node.sh \
  --listen-port 8002 \
  --joint-command-topic /target_robot/joint_commands \
  --joint-states-topic /client_robot/joint_states \
  --reset-mode joint_command
```

The node reads newline-delimited JSON over TCP and publishes
`sensor_msgs/msg/JointState`. The VLA bridge validates exact joint names and
uses the optional per-joint mask in `JointState.effort` to identify entries that
are real human commands rather than feedback fallback.

## Simulation forwarders

Use a forwarder only when the downstream simulator/robot consumes ROS2
`FollowJointTrajectory` actions:

```bash
# A2D: arms, head, body, and interpolated reset
python3 -m teleop.quest3.joint_command_to_sim_a2d \
  --joint-command-topic /target_robot/joint_commands \
  --joint-states-topic /joint_states \
  --reset-topic /custom/custom_a

# TI5 T170C: both arms and reset
python3 -m teleop.quest3.joint_command_to_ti5_t170c \
  --joint-command-topic /target_robot/joint_commands \
  --reset-topic /custom/custom_a
```

Run each module with `--help` for action-server and timing overrides.

## Main-program adaptations

- `client/core/action_arbiter.py` selects fresh teleop first, then fresh policy,
  then holds the last safe action; it also provides transition blending,
  per-source timeouts, and action masks.
- `client/core/teleop_bridge.py` owns ROS2/ZMQ transport, launches the Quest3
  subprocess, publishes command-biased joint feedback, reads reset edges, and
  forwards validated native action vectors.
- `client/core/vla_client.py` performs outlier rejection, open-loop command
  dispatch, teleop-to-policy handoff, status reporting, and intervention-aware
  recording.
- The Web Client exposes teleop only for validated robots, shows connection and
  TELEOP state, protects the auto-selected config path, and locks Reset during
  active human control.
- `client/robots/base_robot.py` shares `reset_robot_pos` between the Web Reset
  button and Quest3 reset.
- `client/core/lerobot_dataset_recorder.py` writes optional intervention
  columns without changing the schema of existing datasets.
