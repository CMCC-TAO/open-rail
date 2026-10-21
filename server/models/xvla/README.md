# X-VLA EEF adapter

This guide describes `run_server.py --model_type xvla_eef` with the A2D
configuration: two seven-joint arms, two grippers, and three cameras.
Open-RAIL handles ZMQ transport and image decoding; the adapter converts joint
feedback to EEF state, calls X-VLA, and converts predicted EEF poses back to
joint targets through Pink IK. Align the URDF, frames, layouts, and checkpoint
with the training data before using another robot configuration.

**How to read this guide:** Steps 1–4 prepare, configure, start, and smoke-test
the server. Step 5 defines the client interface. Implementation limits are
collected under Notes.

## Step 1 — Prerequisites

- **Upstream source** — X-VLA, providing
  `models.modeling_xvla.XVLA` and `models.processing_xvla.XVLAProcessor`.
  The source is not vendored. Add its repository root to `PYTHONPATH`;
  this adapter does not insert a source path or expose `repo_path`.
- **Checkpoint** — an A2D EEF fine-tuned directory containing `config.json`,
  model weights (for example `model.safetensors`), image-processor assets
  (`preprocessor_config.json`), and tokenizer assets. Both `from_pretrained`
  calls use this directory. The checkpoint must use `action_mode="ee6d"`
  and 20-dimensional EEF actions. Training/optimizer state is not loaded.
  Original upstream weights do not replace a checkpoint trained for this layout.
- **Environment** — install the dependencies required by your X-VLA checkout,
  the Open-RAIL server dependencies in [pyproject.toml](../../../pyproject.toml),
  and the IK dependencies: `pin-pink` (import `pink`), Pinocchio
  (import `pinocchio`), `qpsolvers`, and `daqp`.
  The adapter selects CUDA when available, otherwise CPU, and casts the model
  to `torch.bfloat16` on either device; the selected device must support its
  operators. A CPU fallback is not a validated inference guarantee.

## Step 2 — Configuration

Fields of `get_xvla_eef_config()` in
[conf/models_conf.py](../../../conf/models_conf.py):

| Field | Required | Meaning | Default |
| --- | --- | --- | --- |
| `model_path` | yes | Local checkpoint directory | `/path/to/model`; overridden by `--model_path` |
| `domain_id` | yes | Training domain index; must be below checkpoint `num_domains` | `20`, annotated for `task_261` |
| `denoising_steps` | yes | Steps passed to `generate_actions`; independent of chunk length | `10` |
| `eef_action_key` | yes | EEF slices after conversion to IK order | Left pose `[0, 9]`, right pose `[9, 18]`, grippers `[18, 19]` and `[19, 20]` |
| `urdf_path` | yes | Robot model used for FK and IK | Repository `server/utils/eef_utils/urdf/a2d_vla_zero_state.urdf` |
| `reset_position` | yes | Full URDF configuration; non-arm joints are fixed at these values in the reduced models | A2D 34-value configuration in `_get_a2d_eef_config()` |
| `joint_state_key` | yes | Input joint/gripper slices | Left arm `[0, 7]`, right arm `[7, 14]`, grippers `[14, 15]` and `[15, 16]` |
| `link_name` | yes | Arm base and TCP frames | `base_link_l` → `gripper_center`; `base_link_r` → `right_gripper_center` |
| `q_left_init`, `q_right_init` | yes | Fallback IK seeds; normal inference seeds each chunk from received joint feedback | A2D seven-joint poses in the config factory |
| `ref_frame` | yes | EEF frame: URDF world or the configured arm base (`local`) | `world` |
| `rotation_type` | yes | EEF orientation representation | `rot6d` |
| `rot6d_convention` | yes | Rot6D construction; `rows` flattens the first two rotation-matrix rows | `rows` |
| `ik` | yes | Keyword arguments forwarded to `ActionIKSolver`; an empty dict uses solver defaults | `max_iterations=100`, `stagnation_iterations=8` |
| `processor_path` | unused | Present in the config factory but not read by this adapter | `None`; processor always loads from `model_path` |

X-VLA explicitly rejects `rotation_type` values other than `rot6d`.
The IK mapping is also exposed as `joint_action_key` by the shared A2D config. X-VLA reads `eef_action_key`.

If you want change robot, please modify the `urdf_path`, `joint_action_key`, `eef_action_key`, `link_name`, `q_left_init`, `q_right_init`, `reset_position`.

Shared settings are described in [configuration](../../../docs/configuration.md):

- `zmq.port` in [conf/zmq_conf.py](../../../conf/zmq_conf.py) defaults to
  `5566`; the server binds `tcp://*:5566`.
- `image_pad_and_resize` in [conf/server_conf.py](../../../conf/server_conf.py)
  defaults to `False`. X-VLA does not override it; its checkpoint processor
  still performs image preprocessing.
- IK defaults to `dt=0.033` and `qp_solver="daqp"`. The time step constrains
  IK output changes; it does not schedule robot execution. Additional supported
  IK settings can be supplied through `config.ik`.

`run_server.py` accepts only `--model_type`, `--model_path`, and `--debug`.
There are no `--domain_id`, `--port`, `--device`, or `--urdf_path` flags.
Edit the configuration entries and restart the server.

## Step 3 — Run the server

Run from the Open-RAIL repository root in the environment prepared above:

```bash
PYTHONPATH="/path/to/X-VLA:${PYTHONPATH}" python run_server.py \
  --model_type xvla_eef \
  --model_path /path/to/a2d/ckpt \
  --debug
```

The client runs separately; see the root [Quick Start](../../../README.md#-quick-start).

## Step 4 — Smoke-test with one request

Prepare `head.jpg`, `left.jpg`, `right.jpg`, and `state.npy` from the same
observation in one directory. Use the original `(16,)` joint/gripper values
described in Step 5 and an instruction matching the scene.

Save the following standalone script as `smoke_test.py` in that directory.
With the Step 3 server running, execute `python smoke_test.py` from the same
directory in an environment containing `numpy` and `pyzmq`.

```python
import json
import pickle
import time
import uuid
from pathlib import Path

import numpy as np
import zmq

ENDPOINT = "tcp://127.0.0.1:5566"  # Replace with the GPU server IP.
EXPECTED_HORIZON = 30
TIMEOUT_SECONDS = 180
OUTPUT_DIR = Path("xvla_smoke_result")

state = np.load("state.npy", allow_pickle=False)
if state.shape != (16,) or not np.isfinite(state).all():
    raise ValueError("state.npy must contain a finite vector of shape (16,)")

request_id = uuid.uuid4().hex
request = {
    "type": "vla_obs",
    "ref_timestamp": time.monotonic_ns(),
    "loc_timestamp": time.perf_counter(),
    "obs": {
        "cam.head": Path("head.jpg").read_bytes(),
        "cam.hand_left": Path("left.jpg").read_bytes(),
        "cam.hand_right": Path("right.jpg").read_bytes(),
        "state": state,
        "language": ["pick the bottle into the basket"],
    },
}
OUTPUT_DIR.mkdir(exist_ok=False)
context = zmq.Context()
socket = context.socket(zmq.DEALER)
socket.setsockopt(zmq.LINGER, 0)

try:
    socket.connect(ENDPOINT)
    started = time.perf_counter()
    socket.send_multipart([
        pickle.dumps(request),
        json.dumps({"request_id": request_id}).encode("utf8"),
    ])
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not socket.poll(max(1, int(remaining * 1000))):
            raise TimeoutError("No action response; inspect the server log")
        payload, metadata = socket.recv_multipart()
        response, meta = pickle.loads(payload), json.loads(metadata)
        if response.get("type") == "heartbeat":
            continue
        if response.get("type") == "error":
            raise RuntimeError(response.get("error"))
        if response.get("type") != "vla_action":
            raise ValueError(f"Unexpected response type: {response.get('type')}")
        elapsed = time.perf_counter() - started
        actions = np.asarray(response["pred_action"])
        if actions.shape != (EXPECTED_HORIZON, 16) or not np.isfinite(actions).all():
            raise ValueError(f"Invalid action shape or values: {actions.shape}")
        for key in ("ref_timestamp", "loc_timestamp"):
            if response.get(key) != request[key]:
                raise ValueError(f"Response {key} does not match the request")
        if meta.get("request_id") != request_id:
            raise ValueError("Response request_id does not match the request")
        infer_time = meta.get("avg_infer_time")
        if not isinstance(infer_time, (int, float)) or not np.isfinite(infer_time) or infer_time < 0:
            raise ValueError(f"Invalid avg_infer_time: {infer_time!r}")
        result = {
            "action_shape": list(actions.shape),
            "action_dtype": str(actions.dtype),
            "round_trip_seconds": elapsed,
            "metadata": meta,
        }
        np.save(OUTPUT_DIR / "pred_action.npy", actions)
        (OUTPUT_DIR / "response.pkl").write_bytes(pickle.dumps(response))
        (OUTPUT_DIR / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        break
finally:
    socket.close()
    context.term()
```

The script sends one observation and checks a finite `(30, 16)` action
array, echoed timestamps, request ID, and inference-time metadata. It saves
`pred_action.npy`, `response.pkl`, and `result.json` in `xvla_smoke_result`;
it does not send robot motion commands. Use a new `OUTPUT_DIR` for each run.

The default `EXPECTED_HORIZON=30` comes from the inspected checkpoint's `num_actions`.
Change it for another checkpoint, and adjust `ENDPOINT`, `TIMEOUT_SECONDS`,
and the language instruction as needed. On timeout, inspect the server log
and check dependencies, checkpoint assets, and configuration. A passing
response check does not establish IK convergence; success flags are not
included in the wire response.

## Step 5 — Connect your client or robot

### Robot-side requirements

| Item | Expected | Implementation |
| --- | --- | --- |
| Camera keys | `cam.head`, `cam.hand_left`, `cam.hand_right`, in that processor order; all three required | [Adapter](xvla_eef.py), `_CAMERA_KEYS` |
| Image encoding | JPEG/PNG bytes; BGR before OpenCV encoding, RGB after server decoding | [Shared server](../../core/vla_server.py) |
| State layout | `[0:7]` left arm, `[7:14]` right arm, `[14]` left gripper, `[15]` right gripper | [FK/IK conversion](../../utils/eef_utils/action_to_joints.py) |
| Action output | Finite `float64 (T, 16)`, same joint/gripper order; absolute targets | [FK/IK conversion](../../utils/eef_utils/action_to_joints.py) |
| Control frequency | Supplied by the client/controller, not the response | [Architecture](../../../docs/architecture.md) §2 |

Arm angles follow the URDF in radians; EEF translations use its length scale
(metres for the supplied A2D model). Gripper values must match training units.
The adapter does not rescale observed grippers or convert output values to
hardware units.

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
        "state": state,  # np.ndarray, shape (16,)
        "language": ["Pick up the cup with the left gripper"],
    },
}
meta = {"request_id": 0}
```

| Field | Requirement |
| --- | --- |
| `type` | Must be `vla_obs`. |
| `ref_timestamp` | Observation timestamp; the real client uses monotonic nanoseconds. Returned unchanged. |
| `loc_timestamp` | `time.perf_counter()` in seconds. Returned unchanged; absolute monotonic timestamps cannot be compared across machines. |
| Camera fields | JPEG/PNG-encoded bytes or a contiguous encoded `uint8` array. Do not send raw `(H, W, 3)` pixels over ZMQ. Convert RGB sources to BGR before `cv2.imencode`; the server decodes back to RGB. Convert `memoryview` to `bytes` before pickling. |
| `state` | Finite one-dimensional vector with at least 16 values under the default mapping. Only the configured slices enter FK/IK; extra dimensions are not model state. Do not add a batch dimension. |
| `language` | String, or a list/tuple/NumPy array containing exactly one string. Use a nonempty instruction matching the scene. |

Use images and joint feedback from the same observation time. The shared server
also accepts observation lists, but this adapter uses only `sequence[0]`.
A list does not enable batch inference or observation history.

Internally, the adapter changes layouts as follows:

| Stage | 20-dimensional EEF layout |
| --- | --- |
| FK output / IK input | Left pose `[0:9]`, right pose `[9:18]`, left/right grippers `[18:20]` |
| X-VLA proprioception / action | Left pose `[0:9]`, left gripper `[9]`, right pose `[10:19]`, right gripper `[19]` |

Each pose contains XYZ followed by six rotation values. Clients send joint
feedback, not either EEF layout. The adapter owns FK, layout conversion, and IK;
the X-VLA processor and action space own image/text processing and gripper
postprocessing. Do not pre-normalize or manually reorder client state.

```python
response = {
    "type": "vla_action",
    "pred_action": actions,  # np.ndarray, float64, shape (T, 16)
    "ref_timestamp": request["ref_timestamp"],
    "loc_timestamp": request["loc_timestamp"],
    "ext": {},
}
```

`T` is checkpoint `num_actions`. The output contains absolute joint targets
and gripper targets with no batch dimension. Do not add current state or
accumulate the chunk as increments. `ext` contains neither progress
probability nor IK success flags.



## Notes and known issues

- `domain_id` must match the training domain, not just pass the range check.
- **Before use in real robot, please checkout if IK work correctly**.
- **The URDF and fixed body pose must match the observation.** Extra head/waist state entries do not update the reduced FK model; its non-arm joints remain fixed at `reset_position`.
## Upstream project

- Source: X-VLA; the imported entries are `models.modeling_xvla.XVLA` and
  `models.processing_xvla.XVLAProcessor` in the external source checkout.
- License: upstream code and weights retain their respective licenses; this
  repository's license does not replace their terms.

Implementation references:

- [Model configuration](../../../conf/models_conf.py): `get_xvla_eef_config()`.
- [Adapter](xvla_eef.py): policy invocation and serialized inference.
- [FK/IK conversion](../../utils/eef_utils/action_to_joints.py): layouts, feedback seeds, output dtype.
- [Pink solver](../../utils/eef_utils/pink_single_arm_solver.py): convergence and failure behavior.
- [Shared server](../../core/vla_server.py): image decoding and responses.
- [ZMQ server](../../core/zmq_server.py): framing and heartbeats.
- [Real client](../../../client/core/vla_client.py): `_process_data()` request format.

