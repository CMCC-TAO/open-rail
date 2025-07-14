# A2D Robot

## Overview

The A2D Robot is a humanoid robot implementation that provides real-time control and observation capabilities. This module interfaces with the A2D SDK to control the robot's arm movements, gripper operations, and multi-camera vision system.

## Installation

### 1. Install A2D SDK

After confirming network connection between PC and A2D robot, execute the following command to deploy the GDK environment:

```bash
curl -sSL http://10.42.0.101:8849/install.sh | bash
```

### 2. Setup SDK Environment

After SDK installation, execute the following commands:

```bash
cd a2d_sdk
source env.sh
# Switch SDK working mode
# python3 robot_service.py -s -c ./conf/hybrid_deploy_depth53.pbtxt # old
python3 robot_service.py -s -c ./conf/copilot.pbtxt
```

## Configuration

The A2D robot is configured through the `robots_conf.yaml` file.
