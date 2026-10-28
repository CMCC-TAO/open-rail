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

## Fresh-machine installation

This section installs the host-side Quest3 bridge and its runtime dependencies.
The Unity app that runs on the headset is distributed separately and is not
built by this repository.

### Requirements

| Item | Requirement |
| --- | --- |
| Host OS | Ubuntu 22.04 x86_64 is the validated platform |
| ROS 2 | Humble with `rclpy`, `sensor_msgs`, `std_msgs`, and `xacro` |
| Python | Python 3.10, matching ROS 2 Humble's Python ABI |
| Headset | Meta Quest 3 with developer mode and USB debugging enabled |
| Connection | USB data cable; Wi-Fi/LAN is optional for direct TCP mode |
| Robot | A supported robot adapter and its vendor SDK/driver installed separately |

Do not install ROS 2 from PyPI. Use the Ubuntu ROS 2 Humble installation and
then source `/opt/ros/humble/setup.bash` in every terminal that starts the
client or the Quest3 node.

### 1. Install host packages

```bash
# Install ROS 2 Humble first if /opt/ros/humble does not exist:
# https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html
sudo apt update
sudo apt install -y \
  adb android-sdk-platform-tools-common \
  build-essential cmake libeigen3-dev pybind11-dev python3-venv \
  ros-humble-ros-base ros-humble-rclpy ros-humble-sensor-msgs \
  ros-humble-std-msgs ros-humble-xacro
source /opt/ros/humble/setup.bash
```

### 2. Install Open-RAIL in a Python 3.10 environment

```bash
git clone https://github.com/CMCC-TAO/open-rail.git
cd open-rail
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

Source ROS 2 before activating the environment in each new shell so that
`rclpy` and the ROS message packages remain visible to the client process:

```bash
source /opt/ros/humble/setup.bash
source .venv/bin/activate
```

### 3. Install the IK solver (`kine_opt`)

Source code, native dependency details, and optional wheel-build instructions
are maintained in the [kine_opt GitLab repository](http://36.140.17.36:10000/git/DengJiayin/kine_opt).

The Quest3 node uses native IK bindings that are not vendored in this
repository. Both backends are needed to support both robot profiles:

- `kine_solver_py.SingleArmKineSolver` for `ti5_t170c`;
- `casadi_ik_cpp.PinocchioCasadiChunkKineSolver` for `agibot_g1`.

Install `kine_opt` into the same environment as Open-RAIL. Its Python wheel
does not bundle Pinocchio, CasADi, Eigen, Boost, or urdfdom, so the native
dependencies must be installed first:

```bash
python -m pip install 'pin==2.7.0' 'casadi==3.8.1' cmake pybind11
```

Build `kine_opt` from the repository in editable mode:

```bash
git clone http://36.140.17.36:10000/git/DengJiayin/kine_opt.git ../kine_opt

SITE_PACKAGES="$(python -c 'import site; print(site.getsitepackages()[0])')"
export PYTHONNOUSERSITE=1
export CMAKE_PREFIX_PATH="${SITE_PACKAGES}/cmeel.prefix:${SITE_PACKAGES}/casadi:${CMAKE_PREFIX_PATH:-}"
export BOOST_ROOT="${SITE_PACKAGES}/cmeel.prefix"
python -m pip install -e ../kine_opt --no-build-isolation
```

Rebuild the native extensions after changing `kine_opt` C++ sources or CMake
configuration:

```bash
python -m pip install -e ../kine_opt --no-build-isolation --force-reinstall
```

The upstream guide also supports a conda-forge environment. If Open-RAIL
itself runs in conda, install the validated native stack into that same
environment:

```bash
conda install -c conda-forge --strict-channel-priority \
  eigen=3.4.0 pinocchio=3.1.0 eigenpy casadi boost-cpp pybind11 cmake
export CMAKE_PREFIX_PATH="$CONDA_PREFIX:$CMAKE_PREFIX_PATH"
export BOOST_ROOT="$CONDA_PREFIX"
python -m pip install -e ../kine_opt --no-build-isolation
```

Do not mix conda-provided and pip/system native libraries in one Python
environment. The native extensions must be built against the installed
Pinocchio/CasADi headers and ABI.

### 4. Enable USB transport on the headset

1. Enable developer mode for the Quest 3 in the Meta Horizon phone app.
2. Connect the headset with a USB data cable and accept the USB debugging
   authorization prompt inside the headset.
3. Verify that the host sees an authorized device:

   ```bash
   adb devices
   # Expected: <serial>    device
   ```

4. Install and launch the Quest3 teleop app. Its TCP destination should be
   `127.0.0.1:8002` when using the default USB transport.

The Quest3 node runs `adb reverse tcp:8002 tcp:8002` automatically and
periodically reasserts it while the headset is disconnected. To diagnose the
mapping manually:

```bash
adb reverse tcp:8002 tcp:8002
adb reverse --list
```

For direct Wi-Fi/LAN mode, set `teleop.devices.quest3.no_adb_reverse: true`,
point the headset app at the host's LAN IP and port `8002`, and allow TCP
`8002` through the host firewall. The node listens on `0.0.0.0:8002`, so no
profile change is needed unless the port is overridden.

### 5. Verify the installation

Run this check from the repository root in the ROS-sourced virtual
environment:

```bash
source /opt/ros/humble/setup.bash
source .venv/bin/activate

python - <<'PY'
import rclpy
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64
from kine_solver_py import SingleArmKineSolver
from casadi_ik_cpp import PinocchioCasadiChunkKineSolver
print("Quest3 teleop Python dependencies: OK")
PY

adb devices
teleop/quest3/quest3_a2d_node.sh --help
teleop/quest3/quest3_ti5_t170c_node.sh --help
```

Then follow the [Web Client quick start](#quick-start-web-client) or run one
of the standalone scripts below. For a hardware test, first put the robot in a
safe state, clear the workspace, and verify the configured reset pose.

### Robot-specific prerequisites

- **TI5 T170C:** install the laptop SDK from `ti5_t170c_robot/` with
  `bash install1.sh`, and use the same `ROS_DOMAIN_ID`/`RMW_IMPLEMENTATION` as
  the robot driver. The Orin-side driver and camera forwarder must already be
  running; see the [TI5 SDK README](../../ti5_t170c_robot/README.md).
- **AgiBot G1:** install the vendor `a2d_sdk` and start its robot service as
  described in the [AgiBot G1 adapter README](../../client/robots/agibot_g1/README.md).

Quest3 teleop installs only the host-side bridge. It does not install robot
drivers, start the robot's controller, or deploy the headset application.

### Troubleshooting

| Symptom | Check |
| --- | --- |
| `No module named rclpy` | Source `/opt/ros/humble/setup.bash`, then activate the Python 3.10 environment that launches the Web Client. |
| `Cannot import kine_solver_py` or `casadi_ik_cpp` | Install/rebuild `kine_opt` with the exact `python` executable used by the client; a wheel or native build for another Python version will not load. |
| `adb devices` shows no device or `unauthorized` | Use a data cable, enable developer mode/USB debugging, accept the prompt in the headset, run `adb kill-server && adb devices`, and check the Android udev rules package. |
| Web status stays at `listening` | The bridge is running but no headset connected. Check the app's `127.0.0.1:8002` destination, `adb reverse --list`, and `logs/quest3_teleop.log`. |
| `Address already in use` on port `8002` | Stop the other process or set `teleop.devices.quest3.listen_port` to the same unused port used by the headset app. |
| IK extension fails with an undefined symbol | The native Pinocchio/CasADi libraries do not match the `kine_opt` build; recreate the environment and rebuild `kine_opt` without mixing conda and system libraries. |

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
| Client teleop switch, topics, managed Quest3 process, timing, transition, outlier guard, and robot-profile mapping | `conf/client_conf.py` → `get_teleop_config()`; persisted by the Web Client YAML |
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

The TCP server enables keepalive and expires a connection after
`tcp_client_timeout_sec` without packets. While disconnected, it periodically
reasserts the USB `adb reverse` mapping so headset sleep, USB re-enumeration, or
an adb restart does not require restarting the entire client.

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
