# AgiBot G1 Robot

## Overview

The AgiBot G1 Robot is a humanoid robot implementation that provides real-time control and observation capabilities. This module continues to use the external `a2d_sdk` package to control the robot's arm movements, gripper operations, and multi-camera vision system.

## 1.Installation

### Preparation

Plug in the network cable of the PC into the DEBUG port of the AgiBot G1 robot, and configure the IPv4 network of the PC to `10.42.0.88` with a subnet mask of `255.255.255.0`. Note that you need to turn off the WIFI, as the `curl` command below may use the WIFI network, which may cause connection errors.

### Install AgiBot G1 SDK

After confirming network connection between PC and AgiBot G1 robot, execute the following command to deploy the GDK environment:

```bash
conda activate gr00t
curl -sSL http://10.42.0.101:8849/install.sh | bash
```
**Note：** If you encounter errors related to the `cosine` library not being compatible with the platform, please check if the python version is 3.10, as its wheel installation package is `cp310`. *This SDK can be used in a conda environment and does not require ROS*.

## 2. Setup SDK Environment

After SDK installation, execute the following commands:

```bash
conda activate gr00t
cd a2d_sdk
source env.sh
# Switch SDK working mode
# python robot_service.py -s -c ./conf/hybrid_deploy_depth53.pbtxt # old
python robot_service.py -s -c ./conf/copilot.pbtxt
```

## 3. Troubleshooting

- **SDK lack `robot_service.py` file**

  - Copy the `robot_service.py` file from other SDK to the current directory.

- **Prompt `lib/libstdc++.so.6: version GLIBCXX_3.4.30 not found` error**
    
    - Check if the system global library meets the requirements: `strings /usr/lib/x86_64-linux-gnu/libstdc++.so.6 | grep GLIBCXX_3.4.30`
    - If the requirements are met, you only need to re-soft link. `cd /home/zl/apps/miniconda3/envs/gr00t/lib`，clear `rm libstdc++.so.6`，then `ln -s /usr/lib/x86_64-linux-gnu/libstdc++.so.6 libstdc++.so.6`。

## 4. Configuration

The AgiBot G1 robot is configured through `get_agibot_g1_config()` in
`conf/robots_conf.py`, with overrides in the `robots.agibot_g1` section of
`conf/default_conf.yaml`. Select it with `robots.type: agibot_g1`.

The Web config loader accepts legacy `robots.type: a2d` and `robots.a2d`
settings and maps them to `agibot_g1`. Model-side A2D embodiment/dataset
identifiers and the external `a2d_sdk` import are unchanged.
