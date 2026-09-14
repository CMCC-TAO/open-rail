---
title: Configuration
description: Configuration files and the chunk transition mode.
---

# Configuration

All framework configuration lives in the `conf/` directory. Each component has
its own file:

| File | Purpose |
|------|---------|
| `client_conf.py` | Client behavior (visualization, chunk transition) |
| `server_conf.py` | Server behavior |
| `models_conf.py` | Per-model settings |
| `robots_conf.py` | Per-robot settings |
| `zmq_conf.py` | ZMQ communication settings |

## Action chunk transition

For asynchronous inference, VLA-RAIL supports several strategies to smoothly
move from the n-th action chunk to the (n+1)-th:

```python
# in client_conf.py
config.chunk_trans_mode = 'search_action'  # 'search_action' | 'poly' | 'smooth_velocity'
```

- **`search_action`** — selects the candidate action with the smoothest velocity
  match; visible gaps may remain.
- **`poly`** — bridges chunks with a 5th-order polynomial; smooth but with larger
  derivative jumps.
- **`smooth_velocity`** — continuous velocity sequence via error/velocity
  feedback; smoothest, but slightly slower operation.

## Visualization

```python
# in client_conf.py
config.show_action_cams_qt = False  # use the web interface at localhost:8080
```
