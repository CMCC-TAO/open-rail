# WALL-X (Wall-OSS-0.5) adapter

This guide describes `run_server.py --model_type wallx`, using the `agibot_g1`
configuration with two 7-joint arms and two grippers as an example. open-rail
handles ZMQ transport and image decoding; the adapter calls the policy backend
in the sibling Wall-X source directory. The camera fields, state/action dimensions, and
client code below describe this example. For another configuration, align the
interface and checkpoint with its training layout.

**How to read this guide:** Steps 1–4 get one inference request answered on your
machine (prepare → configure → start → smoke-test). Step 5 is for wiring a real
robot or client to the running server. Pitfalls are collected under Notes.

## Step 1 — Prerequisites

- **Upstream source** — the Wall-X (Wall-OSS) project; its adapter entry is the module `wall_x.serving.a2d.A2DPolicy`. Locate the official repository on GitHub / Hugging Face and clone it as a sibling of this repository, or set `repo_path` to wherever you put it. The adapter inserts that path into `sys.path`; it is not vendored.
- **Checkpoint** — a directory fine-tuned for this state/action layout, containing:
  - `model.safetensors`
  - `config.yml` or `config.yaml`
  - `norm_stats.json`
  - the model and processor/tokenizer assets

  Optimizer state is not used. **Original Wall-OSS weights do not replace a checkpoint fine-tuned for this layout.**
- **Environment** — must contain both the Wall-X dependencies and the Open-RAIL server dependencies, including `ml_collections` and `rich`.

## Step 2 — Configuration

Fields of `get_wallx_config()` in [`conf/models_conf.py`](../../../conf/models_conf.py) that this adapter reads:

| Field | Required | Meaning | Default |
| --- | --- | --- | --- |
| `model_path` | yes | Checkpoint directory | `/path/to/model`; overridden by `--model_path` |
| `repo_path` | yes | Path to the `wall-x` source directory, inserted into `sys.path` | `<parent-of-open-rail>/wall-x` |
| `device` | no | Torch device for the policy | `cuda:0` |
| `flow_steps` | no | Flow-matching iterations. **Not** the returned chunk length | `10` |

Two shared server settings also apply; both are documented once in [`docs/configuration.md`](../../../docs/configuration.md):

- `zmq.port` ([`conf/zmq_conf.py`](../../../conf/zmq_conf.py), default `5566`) — the server binds `tcp://*:5566`. Run one server per port.
- `image_pad_and_resize` ([`conf/server_conf.py`](../../../conf/server_conf.py), default `False`) — Wall-X still applies its own training-config preprocessing.

`run_server.py` accepts only `--model_type`, `--model_path`, and `--debug`; there is no `--port` or `--device` — edit the configuration entries instead. Restart the server after changing adapter code.

## Step 3 — Run the server

```bash
# Run in the environment described under Step 1
python run_server.py \
  --model_type wallx \
  --model_path /path/to/agibot_g1/checkpoint \
  --debug
```

The client half runs on the robot side — see the root [Quick Start](../../../README.md#-quick-start).

## Step 4 — Smoke-test with one request

Before wiring a robot, verify the server answers a single inference request.
Save the following code as a Python script. Prepare `head.jpg`, `left.jpg`,
`right.jpg`, and `state.npy` from the same observation, and set an instruction
matching the scene. `state.npy` must contain the original `(16,)` state described
under Step 5; random state values are unsuitable for evaluating policy behavior.
Requires `numpy` and `pyzmq`.

```python
import json
import pickle
import time
from pathlib import Path

import numpy as np
import zmq

context = zmq.Context()
socket = context.socket(zmq.DEALER)
socket.setsockopt(zmq.LINGER, 0)
socket.connect("tcp://127.0.0.1:5566")  # Replace with the GPU server IP.

try:
    state = np.load("state.npy").astype(np.float32)
    assert state.shape == (16,) and np.isfinite(state).all()
    request = {
        "type": "vla_obs",
        "ref_timestamp": time.monotonic_ns(),
        "loc_timestamp": time.perf_counter(),
        "obs": {
            "cam.head": Path("head.jpg").read_bytes(),
            "cam.hand_left": Path("left.jpg").read_bytes(),
            "cam.hand_right": Path("right.jpg").read_bytes(),
            "state": state,
            "language": ["Pick up loose white garbage with left gripper"],
        },
    }
    socket.send_multipart([pickle.dumps(request), json.dumps({"request_id": 0}).encode("utf8")])
    deadline = time.monotonic() + 180
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not socket.poll(max(1, int(remaining * 1000))):
            raise TimeoutError("No action response; inspect server logs")
        payload, metadata = socket.recv_multipart()
        response, meta = pickle.loads(payload), json.loads(metadata)
        if response.get("type") == "heartbeat":
            continue
        if response.get("type") == "error":
            raise RuntimeError(response.get("error"))
        assert response["type"] == "vla_action"
        actions = np.asarray(response["pred_action"])
        assert actions.shape == (50, 16) and np.isfinite(actions).all()
        assert response["ref_timestamp"] == request["ref_timestamp"]
        assert response["loc_timestamp"] == request["loc_timestamp"]
        np.save("pred_action.npy", actions)
        print(actions.shape, meta)
        break
finally:
    socket.close()
    context.term()
```

The script prints `(50, 16)` plus the response metadata on success — the shape
is `(T, 16)` where `T` is the checkpoint's action horizon (50 in the checkpoint
used to verify this guide). A `TimeoutError` means the request never got an action response: re-check
Step 2 (`repo_path`, `model_path`) and inspect the server log. Adjust the
action-shape check when using a checkpoint with a different horizon.

## Step 5 — Connect your client or robot

Everything in Steps 1–4 applies unchanged here; this step defines what your
client must send and what the returned chunk means.

### Robot-side requirements

| Item | Expected | Where it is checked |
| --- | --- | --- |
| Camera keys | `cam.head`, `cam.hand_left`, `cam.hand_right` | must match `robots.agibot_g1.camera.names` ([`conf/robots_conf.py:34`](../../../conf/robots_conf.py)) |
| Image encoding | encoded JPEG/PNG **bytes**; BGR before `cv2.imencode` | the shared server calls `cv2.imdecode` ([`server/core/vla_server.py:121`](../../../core/vla_server.py)) |
| State layout | finite `float32 (16,)`: `[0:7]` left arm, `[7:14]` right arm, `[14]` left gripper, `[15]` right gripper | [`wallx.py:16`](wallx.py) → `A2DPolicy` |
| Action output | `float32 (T, 16)`; `T` = the checkpoint's `task.action_horizon_flow` (50 in the checkpoint used to verify this guide); first 14 dims are **absolute joint targets**, gripper values absolute | [`wallx.py:24`](wallx.py) → upstream `A2DPolicy.infer` |
| Control frequency | not part of this contract — the server returns an action chunk and does not control the robot | [`docs/architecture.md`](../../../docs/architecture.md) §2 |

Values must match the checkpoint's training joint order and original units. Do not substitute end-effector poses, and do not independently rescale angles or gripper values.

### Request and response

Send one observation dictionary per inference request:

```python
request = {
    "type": "vla_obs",
    "ref_timestamp": time.monotonic_ns(),
    "loc_timestamp": time.perf_counter(),
    "obs": {
        "cam.head": head_jpeg_bytes,
        "cam.hand_left": left_jpeg_bytes,
        "cam.hand_right": right_jpeg_bytes,
        "state": state,  # np.ndarray, float32, shape (16,)
        "language": ["Pick up loose white garbage with left gripper"],
    },
}
meta = {"request_id": 0}
```

| Field | Requirement |
| --- | --- |
| `type` | Must be `vla_obs` |
| `ref_timestamp` | Observation timestamp; the real client uses monotonic nanoseconds. Returned unchanged. |
| `loc_timestamp` | `time.perf_counter()` in seconds. Returned unchanged. Absolute monotonic timestamps cannot be compared across machines. |
| `cam.head` / `cam.hand_left` / `cam.hand_right` | JPEG/PNG-encoded image **bytes**, or a contiguous encoded `uint8` array. **Do not send raw `(H, W, 3)` pixel arrays** — the shared server calls `cv2.imdecode`. Convert `memoryview` to `bytes` before pickling, and convert RGB sources to BGR before encoding (`cv2.imencode(".jpg", bgr_image, [cv2.IMWRITE_JPEG_QUALITY, 80])`); the server decodes and converts back to RGB. Raw RGB arrays are supported only when calling the policy backend directly. |
| `state` | Finite one-dimensional values, preferably `float32 (16,)`. Extra dimensions are discarded after the first 16; do not add a batch dimension. |
| `language` | Nonempty string or a list/tuple containing one nonempty string. The real client sends a single-element list. |

Use images and state from the **same observation time**. The example LeRobot camera mapping:

| Dataset key | Request key |
| --- | --- |
| `observation.images.top_head` | `cam.head` |
| `observation.images.hand_left` | `cam.hand_left` |
| `observation.images.hand_right` | `cam.hand_right` |

The server also accepts observation lists, but the current policy uses only the
first element. A list is not a batch-inference or history-fusion interface; use
single-observation requests. Clients must not perform model normalization,
state discretization, 26-dimensional padding, or action-mask construction — the
backend applies them internally, and doing both would double-apply the transform.

The response:

```python
response = {
    "type": "vla_action",
    "pred_action": actions,  # np.ndarray, float32, shape (T, 16)
    "ref_timestamp": request["ref_timestamp"],
    "loc_timestamp": request["loc_timestamp"],
    "ext": {},
}
```

`T` comes from the checkpoint's `task.action_horizon_flow`; the example assumes
a 50-step checkpoint. The output has no batch dimension. The first 14 dimensions
are **absolute joint targets**, with the current joint state already added back
by the backend. Gripper values are also absolute targets. Do not add state again,
accumulate outputs as increments, or unnormalize them. Values use the original
training-data units. `ext` is empty and contains no task-completion probability;
the service returns an action chunk without an execution frequency and does not
control the robot.

### Wire protocol

The client uses **ZMQ DEALER** and the server uses ROUTER. Requests and responses
contain exactly two payload frames:

```python
socket.send_multipart([
    pickle.dumps(request),
    json.dumps(meta).encode("utf8"),
])
payload, metadata = socket.recv_multipart()
response = pickle.loads(payload)
meta = json.loads(metadata)
```

Do not add an identity frame or empty delimiter, and do not use a REQ socket.
`meta` must be a JSON-serializable dictionary; `{}` is valid. The response
preserves request metadata and adds `avg_infer_time`. The protocol uses pickle
and is intended for trusted clients and servers. The full framing and transport
design is documented in [`docs/architecture.md`](../../../docs/architecture.md) §3.3.

Heartbeat: send payload `{"type": "heartbeat", "timestamp": time.time()}` with
metadata `{"action": "ping"}`, using the same pickle + JSON framing. The response
payload has `type=heartbeat`, `status=pong`; metadata has `action=pong`.

## Notes and known issues

- **Heartbeat connectivity alone does not establish successful inference.** Long-running
  clients should send periodic heartbeats and distinguish heartbeat responses from
  `vla_action`; verify the returned action shape and finite values.
- **The output is already absolute** — see Step 5. Do not add state
  again, accumulate outputs as increments, or unnormalize them.
- **The backend pads internally** (16 external dims → 26, last 10 masked). Clients must
  not perform that padding, model normalization, state discretization, or action-mask
  construction.
- **Start with one outstanding observation request at a time.** The adapter serializes
  policy calls with a lock.
- **One process per port per model.** Two servers on the same port will not share a
  checkpoint; the second bind fails.
- **`avg_infer_time`** in the response metadata is the server's smoothed inference
  duration in seconds, not the full round-trip time ([`server/core/vla_server.py:221`](../../../core/vla_server.py)).
- **Dataset replay checks protocol behavior and action curves, not closed-loop robot
  task success.** Do not read a clean replay as proof the policy can do the task.
- The shared server currently prints a traceback on decoding or inference failure and
  does not guarantee an error response. Set a client timeout and inspect server logs.

## Upstream project

- Source: Wall-X (Wall-OSS), official repository on GitHub / Hugging Face (the stable contract is the module entry `wall_x.serving.a2d.A2DPolicy`, not a URL)
- License: the upstream Wall-X code and weights are covered by the upstream repository's own license, not this repository's Apache-2.0 — check the upstream license before use

Implementation references:

- [Model configuration](../../../conf/models_conf.py): `get_wallx_config()` — repo path, device, flow steps.
- [Adapter](wallx.py): policy invocation and serialized inference.
- [Shared server](../../../core/vla_server.py): image decoding, responses, exception handling.
- [ZMQ server](../../../core/zmq_server.py): framing and heartbeats.
- [Real client](../../../client/core/vla_client.py): `_process_data()` request format.
- Policy backend: `wall_x.serving/a2d.py` in the Wall-X source directory (sibling directory, outside this repository).
