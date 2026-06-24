# Unitree G1 Robot (Template)

## Overview

This folder is a template adapter for integrating a Unitree G1 robot into this VLA framework.
It follows the same style as existing adapters under `client/robots/a2d` and `client/robots/mock`.

## Files

- `body_robot.py`
  - Robot adapter class `RobotBody`.
  - Keeps the same core interface required by the framework.
  - Includes TODO markers where you should connect your real G1 SDK.

## Required Methods

You should complete these methods in `RobotBody`:

- `retrieve_observation()`
- `control_robot(action)`
- `execute_action(data)`
- `reset_robot(target_pose=None, mode='default')`
- `close()`

## Observation Contract

`retrieve_observation()` should return a dict compatible with the framework:

- `ref_timestamp`
- `cam.<camera_name>` image arrays
- `obs.state` numpy array

## Next Step

After you finish SDK integration, update `conf/robots_conf.py` and `run_client.py` to register `unitree_g1` as a selectable robot type.
