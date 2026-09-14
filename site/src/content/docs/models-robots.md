---
title: Models & Robots
description: Supported VLA models and robots.
---

# Supported Models & Robots

## VLA Models

| Model | Notes |
|-------|-------|
| ACT | Action Chunking Transformer |
| GR00T N1 | NVIDIA generalist robot model |
| GR00T N1.5 | Improved GR00T release |
| RDT | Robotics Diffusion Transformer |
| SmolVLA | Compact vision-language-action model |
| GO1 | Open VLA baseline |
| DualArmVLA | Bimanual manipulation model |

Run a model with:

```bash
python run_server.py --model_type gr00t_n1 --model_path /path/to/checkpoint
```

## Robots

| Robot | Notes |
|-------|-------|
| A2D-Gripper Robot | A2D humanoid |
| A2D-Hand Robot | A2D humanoid |
| Ti5-DualArm Robot | A2D humanoid |
| Mock Robot | Simulation for testing |

## Client

```bash
python run_client.py          # start the client
python run_client.py --help    # show options
```
