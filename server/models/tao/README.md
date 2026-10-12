# TAO Inference Interface: a2d_gripper Example

This guide describes `run_server.py --model_type tao`, using the `a2d_gripper`
embodiment with two 7-joint arms and two grippers as an example. open-rail
handles ZMQ transport and image decoding; the adapter (`tao.py`) calls the TAO
policy backend through the sibling TAO source directory. The camera fields, state/action
dimensions, and client code below describe this example. For another
embodiment, align the interface and checkpoint with its training layout.

## Start the server

From the open-rail root, use an environment containing both TAO and open-rail
dependencies:

```bash
python run_server.py \
  --model_type tao \
  --model_path /path/to/tao_checkpoint \
  --debug
```

Replace the example path with a compatible fine-tuned checkpoint directory. It
must contain the model weights and a `processor/` subdirectory (the TAO
`PolicyTao` loads the processor via `TaoFlowMatchingProcessor.from_pretrained`).
Optimizer state is not used. Original TAO weights do not replace a checkpoint
fine-tuned for this state/action layout.

| Setting | Location | Default |
|---|---|---|
| `model_path` | `conf/models_conf.py:get_tao_config()` | `/path/to/model` |
| `embodiment_tag` | Same function | `a2d_gripper` |
| `port` | `conf/zmq_conf.py:get_vla_zmq_config()` | `5566`; server binds to `tcp://*:5566` |
| `image_pad_and_resize` | `conf/server_conf.py` | `False`; TAO still applies its training-config preprocessing |

`run_server.py` does not accept `--port` or `--device`; edit the corresponding
configuration entries. The environment needs TAO dependencies and open-rail
server dependencies, including `ml_collections` and `rich`.
Run one server per port. Restart the server after changing adapter code.

## Wire protocol

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
preserves request metadata and adds `avg_infer_time`.
The protocol uses pickle and is intended for trusted clients and servers.

## Observation request

For the `a2d_gripper` example, send one observation dictionary per inference
request:

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
|---|---|
| `type` | Must be `vla_obs` |
| `ref_timestamp` | Observation timestamp; the real client uses monotonic nanoseconds. Returned unchanged. |
| `loc_timestamp` | `time.perf_counter()` in seconds. Returned unchanged. Absolute monotonic timestamps cannot be compared across machines. |
| `cam.head` | JPEG/PNG-encoded head camera image |
| `cam.hand_left` | JPEG/PNG-encoded left wrist camera image |
| `cam.hand_right` | JPEG/PNG-encoded right wrist camera image |
| `state` | Finite one-dimensional values, preferably `float32 (16,)`. Extra dimensions are discarded after the first 16; do not add a batch dimension. |
| `language` | Nonempty string or a list/tuple containing one nonempty string. The real client sends a single-element list. |

The adapter maps the request keys to the TAO video names as:

| Dataset key | Request key |
|---|---|
| `base_image` | `cam.head` |
| `left_wrist_image` | `cam.hand_left` |
| `right_wrist_image` | `cam.hand_right` |

Send encoded image `bytes`, or a contiguous encoded `uint8` array.
**Do not send raw `(H, W, 3)` pixel arrays to the shared server**: it calls
`cv2.imdecode`. Convert `memoryview` to `bytes` before pickling.
OpenCV expects BGR input when encoding:

```python
ok, encoded = cv2.imencode(".jpg", bgr_image, [cv2.IMWRITE_JPEG_QUALITY, 80])
if not ok:
    raise ValueError("JPEG encoding failed")
image_bytes = encoded.tobytes()
```

Convert RGB source images to BGR before encoding. The shared server decodes them
and converts them to RGB for TAO. Clients must not perform model normalization,
state discretization, or action-mask construction.

The server also accepts observation lists, but the current policy uses only the
first element. A list is not a batch-inference or history-fusion interface; use
single-observation requests.

## State and action layout: a2d_gripper example

State is a 16-dimensional vector matching the checkpoint's training joint order
and original units:

| Slice | Meaning |
|---|---|
| `[0:7]` | Seven left-arm joints |
| `[7:14]` | Seven right-arm joints |
| `[14:15]` | Left gripper |
| `[15:16]` | Right gripper |

Do not substitute end-effector poses or independently rescale angles/gripper
values.

Action response:

```python
response = {
    "type": "vla_action",
    "pred_action": actions,  # np.ndarray, float32, shape (T, 16)
    "ref_timestamp": request["ref_timestamp"],
    "loc_timestamp": request["loc_timestamp"],
    "ext": {"prob_progress": progress},  # optional, np.ndarray float32 shape (T,)
}
```

The action uses the same 16-dimensional layout as state: 14 arm joints followed
by the left and right gripper. `T` comes from the embodiment's action horizon
(50 steps for `a2d_gripper`). The output has no batch dimension. The backend's
`decode_action` unnormalizes and converts relative deltas to **absolute joint
targets** in the original training-data units; do not add state again,
accumulate outputs as increments, or unnormalize them.

`ext["prob_progress"]` is present only when the checkpoint emits a task-progress
head; it is the per-step completion probability used for language subtask
advancement. The service returns an action chunk without an execution frequency
and does not control the robot.

## Minimal single-request example

Save the following code as a Python script. Prepare `head.jpg`, `left.jpg`,
`right.jpg`, and `state.npy` from the same observation, and set an instruction
matching the scene. `state.npy` must contain the original `(16,)` state described
above; random state values are unsuitable for evaluating policy behavior.
The client example requires `numpy` and `pyzmq`.

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

Adjust the action-shape check when using an embodiment with a different horizon.

## Heartbeats and error handling

- Send heartbeat payload `{"type": "heartbeat", "timestamp": time.time()}` with
  metadata `{"action": "ping"}`, using the same pickle + JSON framing.
  The response payload has `type=heartbeat`, `status=pong`; metadata has `action=pong`.
- Long-running clients should send periodic heartbeats and distinguish heartbeat
  responses from `vla_action`. Heartbeat connectivity alone does not establish
  successful inference; verify the returned action shape and finite values.
- Start with one outstanding observation request at a time. The adapter serializes
  policy calls with a lock.
- The shared open-rail server currently prints a traceback on decoding or inference
  failure and does not guarantee an error response. Set a client timeout and inspect
  server logs.
- `avg_infer_time` is the shared server's smoothed inference duration in seconds,
  not the full request round-trip time.
- Dataset replay checks protocol behavior and action curves, not closed-loop robot
  task success.

## Implementation references

- [Model configuration](../../../conf/models_conf.py): model path, embodiment tag.
- [Adapter](tao.py): policy invocation and action concatenation.
- [Shared server](../../core/vla_server.py): image decoding, responses, exception handling.
- [ZMQ server](../../core/zmq_server.py): framing and heartbeats.
- [Real client](../../../client/core/vla_client.py): `_process_data()` request format.
- [Policy backend](../../../../TAO/src/tao/serving/policy.py): `PolicyTao.get_action()` and absolute-action conversion.
- [Embodiment layout](../../../../TAO/src/tao/embodiments/a2d.py): `a2d_gripper` state/action indices.
