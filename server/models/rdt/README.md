# RDT (Robotics Diffusion Transformer) Adapter

This guide describes `run_server.py --model_type rdt`, using the dual-arm
gripper layout — model-side identifier `a2d`, served by the `agibot_g1` robot
adapter (two 7-joint arms and two grippers) — as the worked example. The
camera fields, state/action dimensions, and client code below describe this
example. For another configuration, align the interface and checkpoint with its
training layout.

**How to read this guide:** Steps 1–4 get one inference request answered on your
machine (prepare → configure → start → smoke-test). Step 5 is for wiring a real
robot or client to the running server. Pitfalls are collected under Notes.

## Step 1 — Prerequisites

- **Upstream source** — RDT ([thu-ml/RoboticsDiffusionTransformer](https://github.com/thu-ml/RoboticsDiffusionTransformer)); the adapter entry is `create_model` from the upstream module `scripts.agilex_model`. Clone the upstream RDT source code **inside the adapter directory** (for example `server/models/rdt/rdt_train_a2d/`) — the adapter inserts its path into `sys.path`; it is not vendored. ⚠️ The `sys.path` entry at [`rdt.py:3`](rdt.py) is a placeholder (`/path/to/rdt_train_a2d`) — set it to the RDT source directory you cloned before starting the server. This is the only code change this adapter requires; everything else is configuration.
- **Checkpoint** — a directory saved by RDT training, fine-tuned for this state/action layout, containing:
  - `config.json`
  - `pytorch_model.bin`

  Optimizer state is not used. Original RDT weights do not replace a checkpoint fine-tuned for this layout.
- **Vision encoder** — SigLIP `siglip-so400m-patch14-384` (a local directory or a Hugging Face cache path).
- **Language embeddings** — a pre-generated `.pt` file loaded via `torch.load(...)["embeddings"]`. RDT does **not** encode language at inference time: the text your robot executes comes from this file, not from the request. Generate it with the upstream [`scripts/encode_lang_batch.py`](https://github.com/thu-ml/RoboticsDiffusionTransformer/blob/main/scripts/encode_lang_batch.py); regenerate and update `lang_embd_path` whenever the task instruction changes.
- **Environment** — must contain both RDT's own dependencies and the Open-RAIL server dependencies:

  ```bash
  conda create -n rdt python=3.10.0
  conda activate rdt
  # Install PyTorch matching your CUDA version — see https://pytorch.org/get-started/previous-versions/
  pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121
  pip install packaging==24.0
  pip install flash-attn --no-build-isolation
  pip install -r requirements.txt   # from the cloned RDT source directory

  # From the open-rail root: installs the shared runtime dependencies,
  # including pyzmq, numpy, opencv-python, ml-collections, and rich —
  # the shared server imports them at startup
  pip install -e .
  ```

## Step 2 — Configuration

Fields of `get_rdt_config()` in [`conf/models_conf.py`](../../../conf/models_conf.py) that this adapter reads:

| Field | Required | Meaning | Default |
| --- | --- | --- | --- |
| `model_path` | yes | Checkpoint directory (`config.json` + `pytorch_model.bin`) | `/path/to/model`; overridden by `--model_path` |
| `config_path` | yes | The upstream RDT model config YAML (e.g. `configs/base.yaml` from the cloned source directory); defines the chunk size and architecture | `/path/to/config` |
| `vision_encoder_name_or_path` | yes | SigLIP vision encoder directory | `/path/to/vision_encoder` |
| `lang_embd_path` | yes | Pre-generated language-embedding `.pt` file | `/path/to/lang_embds/place_bottle.pt` |

Shared server settings that also apply (documented once in [`docs/configuration.md`](../../../docs/configuration.md)):

- `zmq.port` (`conf/zmq_conf.py`, default `5566`) — the server binds `tcp://*:5566`; run one server per port.
- `image_pad_and_resize` (`conf/server_conf.py`, default `False`) — RDT still applies its training-config preprocessing.

`run_server.py` accepts only `--model_type`, `--model_path`, and `--debug`; there is no `--port` or `--device` — edit the configuration entries instead. Restart the server after changing adapter code.

## Step 3 — Run the server

```bash
# Run in the environment described under Step 1
python run_server.py \
  --model_type rdt \
  --model_path /path/to/a2d/checkpoint \
  --debug
```

The client half runs on the robot side — see the root [Quick Start](../../../README.md#-quick-start).

## Step 4 — Smoke-test with one request

Before wiring a robot, verify the server answers a single inference request.
**This adapter requires a two-frame request** — a JSON list holding the
*current* and the *previous* observation (see Step 5 for why). Prepare
`head.jpg`, `hand_left.jpg`, `hand_right.jpg`, and `state.npy` from real
observations; random state values are unsuitable for evaluating policy
behavior. All three camera keys are required: a `None` value fails in the
shared server's decoder, and an omitted key raises `KeyError` in this adapter.
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

def observation(head_jpeg: bytes, state: np.ndarray):
    return {
        "type": "vla_obs",
        "ref_timestamp": time.monotonic_ns(),
        "loc_timestamp": time.perf_counter(),
        "obs": {
            "cam.head": head_jpeg,
            "cam.hand_left": Path("hand_left.jpg").read_bytes(),
            "cam.hand_right": Path("hand_right.jpg").read_bytes(),
            "state": state,
            "language": ["put the bottle into the box"],  # ignored by this adapter
        },
    }

try:
    state = np.load("state.npy").astype(np.float32)
    assert state.shape >= (16,) and np.isfinite(state).all()
    curr = observation(Path("head.jpg").read_bytes(), state)
    prev = observation(Path("head.jpg").read_bytes(), state)  # use an earlier frame in practice
    request = [curr, prev]  # two-frame list: [current, previous]
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
        assert response["type"] == "vla_action"
        actions = np.asarray(response["pred_action"])
        assert actions.ndim == 2 and actions.shape[1] == 16 and np.isfinite(actions).all()
        assert response["ref_timestamp"] == curr["ref_timestamp"]
        assert response["loc_timestamp"] == curr["loc_timestamp"]
        np.save("pred_action.npy", actions)
        print(actions.shape, meta)
        break
finally:
    socket.close()
    context.term()
```

The script prints the action shape plus the response metadata on success. The
shape is `(T, 16)` where `T` is the chunk size defined by the checkpoint's
`config_path` YAML. A `TimeoutError` usually means the adapter failed during
loading — re-check Step 1 (`sys.path` in `rdt.py:3`), Step 2 (`config_path`,
`vision_encoder_name_or_path`, `lang_embd_path`), and inspect the server log:
a bad path raises there and no error response is guaranteed.

## Step 5 — Connect your client or robot

Everything in Steps 1–4 applies unchanged here; this step defines what your
client must send and what the returned chunk means.

### Robot-side requirements

| Item | Expected | Where it is checked |
| --- | --- | --- |
| Camera keys | `cam.head`, `cam.hand_left`, `cam.hand_right` | must match `robots.agibot_g1.camera.names` ([`conf/robots_conf.py:34-36`](../../../conf/robots_conf.py)); legacy `robots.a2d.*` keys are migrated automatically on load |
| Image encoding | encoded JPEG/PNG **bytes**; BGR before `cv2.imencode` | the shared server calls `cv2.imdecode` and hands the adapter RGB arrays ([`server/core/vla_server.py:121-128`](../../core/vla_server.py)) |
| Request body | a **list of two observations** `[current, previous]`, not a single dictionary | [`rdt.py:32-33`](rdt.py) reads `sequence[0]` / `sequence[1]` |
| State layout | `float32`, 16 meaningful dims: `[0:7]` left arm, `[7:14]` right arm, `[14:15]` left gripper, `[15:16]` right gripper; dims beyond 16 are ignored | [`rdt.py:50-56`](rdt.py) |
| Action output | `float32 (T, 16)` in the same joint order as state; `T` = chunk size from the checkpoint's config; no batch dimension | [`rdt.py:70-76`](rdt.py) |
| Control frequency | not part of this contract — the server returns a chunk and does not control the robot. The adapter constructs the policy with `control_frequency=30` ([`rdt.py:27`](rdt.py)) | — |

Values must match the checkpoint's training joint order and original units. Do
not substitute end-effector poses, and do not independently rescale angles or
gripper values.

### Request and response

Send **one list of two observation dictionaries** per inference request:

```python
request = [
    {  # current observation — its timestamps are echoed back
        "type": "vla_obs",
        "ref_timestamp": time.monotonic_ns(),
        "loc_timestamp": time.perf_counter(),
        "obs": {
            "cam.head": head_jpeg_bytes,
            "cam.hand_left": left_jpeg_bytes,    # all three are required
            "cam.hand_right": right_jpeg_bytes,
            "state": state,        # np.ndarray, float32, 16 meaningful dims
            "language": ["..."],   # ignored by this adapter
        },
    },
    {  # previous observation — same structure, earlier images and state
        "type": "vla_obs",
        "ref_timestamp": time.monotonic_ns(),
        "loc_timestamp": time.perf_counter(),
        "obs": {"cam.head": prev_head, "cam.hand_left": prev_left,
                "cam.hand_right": prev_right, "state": prev_state,
                "language": ["..."]},
    },
]
meta = {"request_id": 0}
```

| Field | Requirement |
| --- | --- |
| `type` | Must be `vla_obs` in each frame |
| `ref_timestamp` / `loc_timestamp` | The **current** frame's values are returned unchanged ([`rdt.py:79`](rdt.py)); `ref_timestamp` should be your observation timestamp, `loc_timestamp` the send-time clock — the real client uses `time.perf_counter()` ([`client/core/vla_client.py:908`](../../../client/core/vla_client.py)) |
| `cam.*` | JPEG/PNG-encoded image **bytes**, or a contiguous encoded `uint8` array. **Do not send raw `(H, W, 3)` pixel arrays** — the shared server calls `cv2.imdecode`. Convert `memoryview` to `bytes` before pickling, and convert RGB sources to BGR before encoding; the server decodes and converts back to RGB ([`server/core/vla_server.py:121-128`](../../core/vla_server.py)). All three camera keys must be present with valid image data — `None` fails in the server decoder, an omitted key raises `KeyError` in this adapter ([`rdt.py:39-45`](rdt.py)). |
| `state` | Finite one-dimensional values, preferably `float32 (16,)`. The 16 dims are consumed in the layout above; extra dimensions are ignored. Do not add a batch dimension. |
| `language` | **Ignored by this adapter** — semantics come from the `lang_embd_path` file. The shared server only surfaces it in heartbeat status info. Send it or not; it changes nothing. |

Use images and state from the **same observation time** within each frame; the
two frames must be consecutive observations (current + previous). The adapter
reorders state and action internally between the request layout above and the
checkpoint's internal `7+1+7+1` training order — clients only ever see the
layout above. Clients must not perform model normalization, state
discretization, internal padding, or action-mask construction — the backend
applies them internally, and doing both would double-apply the transform.

The response:

```python
response = {
    "type": "vla_action",
    "pred_action": actions,  # np.ndarray, float32, shape (T, 16)
    "ref_timestamp": request[0]["ref_timestamp"],
    "loc_timestamp": request[0]["loc_timestamp"],
}
```

The action values are in the units and convention of the checkpoint's training
data; the adapter only reorders dimensions and does not convert between
absolute and incremental representations. The service returns an action chunk
without an execution frequency and does not control the robot.

### Wire protocol

The client uses **ZMQ DEALER** and the server uses ROUTER. Requests and responses
contain exactly two payload frames (pickle payload + JSON metadata); do not add
an identity frame or empty delimiter, and do not use a REQ socket. The response
preserves request metadata and adds `avg_infer_time`. The protocol uses pickle
and is intended for trusted clients and servers. The full framing and transport
design is documented in [`docs/architecture.md`](../../../docs/architecture.md) §3.3.

Heartbeat: send payload `{"type": "heartbeat", "timestamp": time.time()}` with
metadata `{"action": "ping"}`, using the same pickle + JSON framing. The response
payload has `type=heartbeat`, `status=pong`; metadata has `action=pong`.

## Notes and known issues

- **A single-observation request crashes the adapter** with an `IndexError` (`sequence[1]` does not exist) — always send the two-frame list.
- **Language is not a runtime input.** Changing the task instruction requires regenerating the embeddings file (upstream `encode_lang_batch.py`) and updating `lang_embd_path` — a request's `language` field is ignored.
- The server runs up to `max_infer_workers = 3` inference requests concurrently
  ([`conf/server_conf.py:23`](../../../conf/server_conf.py)); the RDT adapter has
  no internal lock and the upstream `policy.step` is not guaranteed thread-safe.
  Start with one outstanding request at a time, or set `max_infer_workers = 1`.
- A bad `config_path`, `vision_encoder_name_or_path`, or `lang_embd_path` raises in the **server** log; the shared server prints a traceback and does not guarantee an error response. Set a client timeout and inspect server logs.
- `avg_infer_time` is the shared server's smoothed inference duration in seconds, not the full request round-trip time.
- **Dataset replay checks protocol behavior and action curves, not closed-loop robot task success.** Do not read a clean replay as proof the policy can do the task.

## Upstream project

- Source: RDT — Robotics Diffusion Transformer, official repository [thu-ml/RoboticsDiffusionTransformer](https://github.com/thu-ml/RoboticsDiffusionTransformer) (the stable contract is the module entry `scripts.agilex_model.create_model`, not a URL)
- License: the upstream model code and weights are covered by the upstream repository's own license, not this repository's Apache-2.0 — check the upstream license before use

Implementation references:

- [Model configuration](../../../conf/models_conf.py): `get_rdt_config()`.
- [Adapter](rdt.py): state/action reordering and policy invocation.
- [Shared server](../../core/vla_server.py): image decoding, responses, exception handling.
- [ZMQ server](../../core/zmq_server.py): framing and heartbeats.
- [Real client](../../../client/core/vla_client.py): `_process_data()` request format.
