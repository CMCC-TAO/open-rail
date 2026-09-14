---
title: Introduction
description: What VLA-RAIL is and how it is structured.
---

# Introduction

**VLA-RAIL** is a real-time asynchronous inference linker for Vision-Language-Action
(VLA) models and robots. It provides a client-server architecture that enables
real-time robot control using models such as ACT, GR00T, RDT, SmolVLA, and GO1.

## Architecture

The framework uses a client-server architecture with **ZMQ** for communication:

- The **client** obtains observation data and robot state, sends it to the server,
  receives inference results, and sends control commands to the robot.
- The **server** runs VLA model inference and returns actions to clients.

## Repository layout

```
.
├── client/        # Client-side components (core, robots, utils)
├── conf/          # Configuration files
├── server/        # Server-side components (core, models)
├── scripts/       # Utility scripts
├── run_client.py  # Client entry point
└── run_server.py  # Server entry point
```

## Next

- [Installation](/docs/installation/)
- [Configuration](/docs/configuration/)
- [Models & Robots](/docs/models-robots/)
