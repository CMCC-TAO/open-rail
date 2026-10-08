---
title: "Add a New Inter-Chunk Fuser"
description: "Step-by-step guide to add a custom inter-chunk smoothing policy to the shared runtime."
---

# Open-RAIL Add New inter_chunk_fuser Policy Development Document

[中文版](../../docs-cn-backup/add-new-inter-chunk-fuser.zh-CN.md)
## inter_chunk_fuser Overview
Let the observation at time $t_1$ be $O_{t_1}$. The VLA model predicts an $n$-step action chunk $[a_0, a_1, \dots, a_n]_{t_1}$ conditioned on language instruction and observation.

Open-RAIL adopts an asynchronous architecture: once $\text{chunk}_{t_1}: [a_0, a_1, \dots, a_n]_{t_1}$ is available, the robot starts executing this chunk immediately. Meanwhile, the VLA model predicts the next action chunk $[a_0, a_1, \dots, a_n]_{t_2}$ based on the observation $O_{t_2}$ at time $t_2$.

Define the VLA model inference latency as $\Delta_t$. In general, $t_2 \ge t_1 + \Delta_t$.

In practice, the new action chunk arrives before the old chunk finishes execution. Suppose the robot is executing the $i$-th action of $\text{chunk}_{t_1}$ when $\text{chunk}_{t_2}$ arrives. The **inter_chunk_fuser** is designed to smoothly transition from the $i$-th action of $\text{chunk}_{t_1}$ to a designated action in $\text{chunk}_{t_2}$, mitigating abrupt jumps in action magnitude.

### Input Arguments for Fuser Policy
| Parameter | Description |
| ---- | ---- |
| next_action_chunk | New action sequence with dimension $d \times n$, where $d$ = number of robot joints, $n$ = number of action steps |
| next_vel_chunk | Velocity sequence corresponding to next_action_chunk |
| next_acc_chunk | Acceleration sequence corresponding to next_action_chunk |
| currt_action | Current action being executed from the old action chunk |
| currt_vel | Velocity while executing currt_action |
| currt_acc | Acceleration while executing currt_action |
| target_chunk_index | Index of the target action to connect within next_action_chunk |

> Open-RAIL has implemented three built-in inter-chunk-fuser policies: `search_action`, `min_jerk`, `smooth_velocity`

---
## Development Steps for Custom inter_chunk_fuser Policy (`your_fuser_method`)
Policy shorthand name: `your_fuser`

### 1. Add policy entry in inter_chunk_fuser.py
File path: `./client/core/inter_chunk_fuser.py`
Add a conditional branch for `your_fuser` inside the `process` function of class `InterChunkFuser`.

### 2. Implement policy logic in inter_chunk_fuser.py
File path: `./client/core/inter_chunk_fuser.py`
Add a member function `your_fuser_method` inside class `InterChunkFuser` to implement your smooth transition algorithm.

### 3. Add policy configuration in client_conf.py
File path: `./conf/client_conf.py`
1. Create a new function `your_fuser_method_config` to define hyperparameters for this policy;
2. Instantiate `your_fuser_method_config` inside the `get_inter_chunk_config` function.

### 4. Add frontend configuration option
File path: `./web_client/static/modules/config.js`
Add the option `"your_fuser"` to the `inter_chunk_mode` list under `CONFIG_SELECT_OPTIONS`.

### 5. Verification
Start server and web_client, then visit `localhost:9000`. You can select the `your_fuser` policy from the dropdown menu at **Main Parameters** → **Inter-Chunk Mode** on the web page.
