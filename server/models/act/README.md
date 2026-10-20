# ACT Adapter

This guide describes `run_server.py --model_type act`, using the validated
`agibot_g1` configuration as the worked example. The camera fields, state and
action dimensions, and client code below are specific to the bundled ACT
adapter and its 20-dimensional AgiBot G1 training layout.

**How to read this guide:** Steps 1–4 get one inference request answered on your
machine (prepare → configure → start → smoke-test). Step 5 defines the real
robot/client contract. Known constraints are collected under Notes.

## Step 1 — Prerequisites

- **Model implementation** — the ACT policy and its DETR implementation live in
  this directory; no separate ACT source checkout is loaded at runtime. The
  adapter entry is `server.models.act.ModelVLA`.
- **Checkpoint** — `model_path` must point to a PyTorch state-dict checkpoint
  file, not a directory. Its parent directory must also contain
  `dataset_stats.pkl`:

  ```text
  /path/to/checkpoint/
  ├── <checkpoint-file>
  └── dataset_stats.pkl
  ```

  `dataset_stats.pkl` must contain the min/max statistics expected by the
  adapter for `observation.state` (20 values) and `action` (22 values). The
  loaded values must support the tensor operations used by the bundled
  normalizer. Optimizer state and a separate model configuration file are not
  read. A checkpoint trained for a different architecture, camera set, state
  layout, or action layout is not interchangeable with this adapter.
- **Environment** — use a CUDA-enabled environment containing the Open-RAIL
  server dependencies and the ACT imports used in this directory, including
  PyTorch, torchvision, einops, OmegaConf, matplotlib, OpenCV, NumPy, and
  IPython. The repository does not pin a verified ACT-specific PyTorch/CUDA
  version; use the versions with which the checkpoint was produced and verify
  them with the smoke test below.

## Step 2 — Configuration

The only field in `get_act_config()` in
[`conf/models_conf.py`](../../../conf/models_conf.py) is:

| Field | Required | Meaning | Default |
| --- | --- | --- | --- |
| `model_path` | yes | Path to the PyTorch checkpoint file; overridden by `--model_path` | `/path/to/model` |

Shared server settings also apply (see
[`docs/configuration.md`](../../../docs/configuration.md)):

- `zmq.port` in [`conf/zmq_conf.py`](../../../conf/zmq_conf.py), default `5566`.
- `image_pad_and_resize` in
  [`conf/server_conf.py`](../../../conf/server_conf.py), default `False`. All
  three decoded ACT images must have the same height and width before the
  adapter stacks them. Enable shared padding/resizing or make the client
  provide equal-sized images when the cameras have different native
  resolutions.
- ACT always uses the default CUDA device through `.cuda()`; the current model
  configuration has no `device` field.

`run_server.py` accepts only `--model_type`, `--model_path`, and `--debug`;
there is no `--port` or `--device`. Edit the corresponding configuration entry
instead. Restart the server after changing adapter code or configuration.

## Step 3 — Run the server

Run from the repository root in the environment described above:

```bash
python run_server.py \
  --model_type act \
  --model_path /path/to/checkpoint/<checkpoint-file> \
  --debug
```

The client half runs on the robot side; see the root
[Quick Start](../../../README.md#-quick-start).

## Step 4 — Smoke-test with one request

Before connecting a robot, verify that the server answers one request. Prepare
`head.jpg`, `left.jpg`, `right.jpg`, and `state.npy` from the same observation.
The three images must have the same decoded height and width unless shared
padding/resizing is enabled. `state.npy` must be finite `float32` data with
shape `(20,)` in the layout documented in Step 5; random state values are not
suitable for evaluating policy behavior. Requires `numpy` and `pyzmq`.

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
    assert state.shape == (20,) and np.isfinite(state).all()
    request = {
        "type": "vla_obs",
        "ref_timestamp": time.monotonic_ns(),
        "loc_timestamp": time.perf_counter(),
        "obs": {
            "cam.head": Path("head.jpg").read_bytes(),
            "cam.hand_left": Path("left.jpg").read_bytes(),
            "cam.hand_right": Path("right.jpg").read_bytes(),
            "state": state,
            "language": [""],  # Present for protocol compatibility; ACT ignores it.
        },
    }
    meta = {"request_id": 0}
    socket.send_multipart([
        pickle.dumps(request),
        json.dumps(meta).encode("utf8"),
    ])

    deadline = time.monotonic() + 180
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not socket.poll(max(1, int(remaining * 1000))):
            raise TimeoutError("No action response; inspect server logs")
        payload, metadata = socket.recv_multipart()
        response, response_meta = pickle.loads(payload), json.loads(metadata)
        if response.get("type") == "heartbeat":
            continue
        assert response["type"] == "vla_action"
        actions = np.asarray(response["pred_action"])
        assert actions.shape == (64, 16) and np.isfinite(actions).all()
        assert response["ref_timestamp"] == request["ref_timestamp"]
        assert response["loc_timestamp"] == request["loc_timestamp"]
        np.save("pred_action.npy", actions)
        print(actions.shape, response_meta)
        break
finally:
    socket.close()
    context.term()
```

The expected shape is `(64, 16)`: the action horizon is hard-coded to 64 and
the adapter returns the first 16 dimensions of the 22-dimensional model
output. This script is derived from the current implementation; this repository
does not contain a checkpoint with which to run it. A timeout can also mean
that decoding or inference raised an exception, because the shared server logs
such failures but does not guarantee an error response.

## Step 5 — Connect your client or robot

Everything in Steps 1–4 applies unchanged here. This section defines the
values a client must send and how to interpret the returned action chunk.

### Robot-side requirements

| Item | Expected | Where it is checked |
| --- | --- | --- |
| Camera keys | `cam.head`, `cam.hand_left`, `cam.hand_right` | hard-coded in [`act.py`](act.py); names match `robots.agibot_g1.camera.names` in [`conf/robots_conf.py`](../../../conf/robots_conf.py) |
| Image encoding | encoded JPEG/PNG bytes; BGR before `cv2.imencode` | shared decoding in [`server/core/vla_server.py`](../../../core/vla_server.py) |
| State layout | finite `float32 (20,)`: `[0:7]` left arm, `[7:14]` right arm, `[14]` left gripper, `[15]` right gripper, `[16:18]` head, `[18:20]` waist | 20-value normalizer in [`act.py`](act.py); layout confirmed for the validated checkpoint |
| Action output | `float32 (64, 16)`: `[0:7]` left arm, `[7:14]` right arm, `[14]` left gripper, `[15]` right gripper; absolute joint targets | horizon and output slice in [`act.py`](act.py) |
| Control frequency | not part of the model-server contract; the client schedules the returned chunk | [`docs/architecture.md`](../../../docs/architecture.md) §2 |

State and action values must use the checkpoint training data's original joint
order and units. This repository does not independently document those units.
Do not substitute end-effector poses or rescale values on the client. The
adapter normalizes the 20-dimensional state and unnormalizes the
22-dimensional model output using `dataset_stats.pkl`, then returns dimensions
`0:16` as absolute targets.

Although 20 state values are sent, the current `arms_only` model path removes
the final four head/waist values before projecting proprioception. They must
still be present because state normalization is configured for exactly 20
values.

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
        "state": state,       # np.ndarray, float32, shape (20,)
        "language": [""],    # Ignored by ACT.
    },
}
meta = {"request_id": 0}
```

| Field | Requirement |
| --- | --- |
| `type` | Must be `vla_obs`. |
| `ref_timestamp` | Observation timestamp; the real client uses monotonic nanoseconds. Returned unchanged. |
| `loc_timestamp` | `time.perf_counter()` in seconds. Returned unchanged. Absolute monotonic timestamps cannot be compared across machines. |
| `cam.head` / `cam.hand_left` / `cam.hand_right` | JPEG/PNG-encoded bytes, or a contiguous encoded `uint8` array. Do not send raw `(H, W, 3)` pixel arrays: the shared server calls `cv2.imdecode`. Convert `memoryview` to `bytes` before pickling if the serializer cannot handle it. Convert RGB sources to BGR before `cv2.imencode`; the server decodes to BGR and passes RGB arrays to ACT. All three decoded images must have equal spatial dimensions before stacking. |
| `state` | Exact finite one-dimensional 20-value state in the layout above. Do not add a batch dimension. |
| `language` | Ignored by the current ACT checkpoint and adapter because `use_language=False` is hard-coded. The real client still sends a one-element list. |

Use the images and state from the same observation time. For the validated
`agibot_g1` integration, the request keys directly identify the head, left
wrist, and right wrist cameras. Preserve the same view order used for training.

The shared server accepts observation lists, but this adapter uses only
`sequence[0]`; a list is not a batch-inference or history-fusion interface.
Clients must not apply state/action min-max transforms: the adapter uses
`dataset_stats.pkl` internally, and preprocessing twice changes the policy
contract.

The response is:

```python
response = {
    "type": "vla_action",
    "pred_action": actions,       # np.ndarray, float32, shape (64, 16)
    "obs_state": state[None, :],  # echoed batched input state
    "ref_timestamp": request["ref_timestamp"],
    "loc_timestamp": request["loc_timestamp"],
}
```

The output has no batch dimension. It contains 64 absolute targets in the
original training-data units. Do not accumulate them as increments, add the
current state again, or unnormalize them. The model also predicts dimensions
16–21 and an internal task-completion value, but the current adapter does not
return either one and does not include an `ext` field.

### Wire protocol

The client uses ZMQ DEALER and the server uses ROUTER. Requests and responses
contain exactly two client-visible frames: a pickle payload and JSON metadata.

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
Metadata must be a JSON-serializable dictionary. The response preserves it and
adds `avg_infer_time`. Pickle is intended only for trusted clients and servers.
See [`docs/architecture.md`](../../../docs/architecture.md) §3.3 for the full
transport design.

For a heartbeat, send payload
`{"type": "heartbeat", "timestamp": time.time()}` with metadata
`{"action": "ping"}` using the same framing. The response payload has
`type=heartbeat` and `status=pong`; response metadata has `action=pong`.

## Notes and known issues

- The architecture, 64-step horizon, 20-dimensional input normalization,
  22-dimensional model output, three-camera order, CUDA device, and returned
  `0:16` slice are hard-coded in [`act.py`](act.py) and
  [`detr/models/detr_vae.py`](detr/models/detr_vae.py). A differently trained
  checkpoint requires code changes, not only a different `model_path`.
- All three images are stacked with `np.stack`. Different decoded resolutions
  fail unless the client or shared server first makes them equal-sized.
- `dataset_stats.pkl` is mandatory. Missing, incorrectly shaped, or incompatible
  statistics prevent startup or inference; clients must not repeat the same
  normalization.
- Language input is ignored. Changing the instruction does not change this
  checkpoint's ACT inference path.
- Start with one outstanding inference request at a time. The shared server can
  schedule multiple workers, but the ACT adapter has no model-level lock and
  concurrent inference on the same policy instance is not established by the
  repository.
- The shared server logs decoding and inference exceptions but does not
  guarantee an error response. Set a client timeout and inspect server logs.
- `avg_infer_time` is the server's smoothed decode-plus-inference duration, not
  full network round-trip latency.
- Dataset replay checks protocol behavior and action curves, not closed-loop
  robot task success.

## Source and license

- The ACT adapter and policy integration used at runtime are bundled under
  `server/models/act/`; no private source URL is required.
- The DETR-derived portion carries its own
  [`detr/LICENSE`](detr/LICENSE). Model checkpoints remain subject to the terms
  under which they were produced or distributed; verify checkpoint provenance
  before use.

Implementation references:

- [Model configuration](../../../conf/models_conf.py): `get_act_config()`.
- [Adapter](act.py): checkpoint/statistics loading, preprocessing, inference,
  and serialized response.
- [Policy wrapper](policy.py): ACT invocation and image normalization.
- [DETR model](detr/models/detr_vae.py): model dimensions and action head.
- [Shared server](../../core/vla_server.py): image decoding, worker scheduling,
  responses, and exception handling.
- [ZMQ server](../../core/zmq_server.py): framing and heartbeats.
- [Real client](../../../client/core/vla_client.py): `_process_data()` request
  format and action-chunk handling.
