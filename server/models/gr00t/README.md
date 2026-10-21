


## GR00T N1 & N1.5
### Code Repositories
- GR00T N1: http://36.140.17.36:10000/git/embodiedai/Isaac-GR00T/-/tree/GR00T_N1?ref_type=heads
- GR00T N1.5: http://36.140.17.36:10000/git/embodiedai/Isaac-GR00T/-/tree/GR00T_N1.5?ref_type=heads

### Environment Setup

#### Setting up conda environment from scratch
```bash
conda create -n gr00t_xx python=3.10
conda activate gr00t_xx
pip install --upgrade setuptools
pip install -e .
pip install --no-build-isolation flash-attn==2.7.4.post1
```

#### Cloning from existing conda environment

```bash
conda env list # List existing conda environments
conda create --name new_env_name --clone old_env_name
cd /path/to/Isaac-GR00T # Navigate to your gr00t project directory
pip install -e . --no-deps # Install only the local package without dependencies
```

#### Switching gr00t versions in the same conda environment
```bash
pip uninstall gr00t
PYTHONPATH=/path/to/Isaac-GR00T:$PYTHONPATH python run_server.py # Specify PYTHONPATH when running code
```

# GR00T N1.7 EEF adapter

This guide describes `run_server.py --model_type gr00t_n1_7_eef` with the A2D
configuration: two seven-joint arms, two grippers, and three cameras.
The adapter converts joint feedback to EEF state, calls `Gr00tPolicy`, and
converts EEF actions back to joint targets through Pink IK. Its configuration
is independent of the older `config.models.gr00t` entry.

**How to read this guide:** Steps 1–4 prepare, configure, start, and smoke-test
the server. Step 5 defines the client interface. Implementation limits are
collected under Notes.

## Step 1 — Prerequisites

- **Upstream source** — an Isaac-GR00T checkout providing
  `gr00t.policy.gr00t_policy.Gr00tPolicy` and
  `gr00t.data.embodiment_tags.EmbodimentTag.resolve`.
  Install that checkout in the active environment or add its root to
  `PYTHONPATH`. The adapter does not insert a source path; an older
  `gr00t` package may expose a different API.
- **Checkpoint** — an A2D EEF fine-tuned directory with `config.json`, model
  weights (including every shard and index for sharded checkpoints),
  `processor_config.json`, and statistics for `new_embodiment`.
  The local example contains `statistics.json` and
  `experiment_cfg/dataset_statistics.json`; the adapter uses processor-loaded
  statistics first, then these two paths in order. Keep all processor and
  backbone assets required by the chosen upstream checkout.
  Optimizer/trainer state is not used. Original upstream weights do not
  replace a checkpoint fine-tuned for this EEF layout.
- **Environment** — use the dependencies required by the N1.7 checkout,
  the Open-RAIL server dependencies in [pyproject.toml](../../../pyproject.toml),
  and `pin-pink` (import `pink`), Pinocchio (import `pinocchio`),
  `qpsolvers`, and `daqp`. The adapter selects CUDA when available,
  otherwise CPU; that selection alone does not establish CPU compatibility
  or acceptable inference latency.

## Step 2 — Configuration

Fields of `get_gr00t_n1_7_eef_config()` in
[conf/models_conf.py](../../../conf/models_conf.py):

| Field | Required | Meaning | Default |
| --- | --- | --- | --- |
| `model_path` | yes | Fine-tuned checkpoint directory | `/path/to/model`; overridden by `--model_path` |
| `embodiment_tag` | yes | Processor modality/statistics selection | `new_embodiment` |
| `joint_action_key` | yes | EEF action slices passed to IK, despite the field name | Left pose `[0, 9]`, right pose `[9, 18]`, grippers `[18, 19]` and `[19, 20]` |
| `urdf_path` | yes | Robot model used for FK and IK | Repository `server/utils/eef_utils/urdf/a2d_vla_zero_state.urdf` |
| `reset_position` | yes | Full URDF configuration; non-arm joints are fixed at these values in the reduced models | A2D 34-value configuration in `_get_a2d_eef_config()` |
| `joint_state_key` | yes | Input joint/gripper slices | Left arm `[0, 7]`, right arm `[7, 14]`, grippers `[14, 15]` and `[15, 16]` |
| `link_name` | yes | Arm base and TCP frames | `base_link_l` → `gripper_center`; `base_link_r` → `right_gripper_center` |
| `q_left_init`, `q_right_init` | yes | Fallback IK seeds; normal inference seeds each chunk from received joint feedback | A2D seven-joint poses in the config factory |
| `ref_frame` | yes | EEF frame: URDF world or the configured arm base (`local`) | `world` |
| `rotation_type` | yes | EEF orientation representation | `rot6d` |
| `rot6d_convention` | yes | Rot6D construction; `rows` flattens the first two rotation-matrix rows | `rows` |

The configured tag is resolved by the upstream enum. If resolving `a2d`
raises `ValueError`, the adapter falls back to `NEW_EMBODIMENT`.
The supplied checkpoint must support the resolved tag.

To use a new robot, update `urdf_path`, `joint_state_key`, `joint_action_key`,
`link_name`, `q_left_init`, `q_right_init`, and `reset_position` to match its
URDF and training layout.

Shared settings are described in [configuration](../../../docs/configuration.md):

- `zmq.port` in [conf/zmq_conf.py](../../../conf/zmq_conf.py) defaults to
  `5566`; the server binds `tcp://*:5566`.
- `image_pad_and_resize` in [conf/server_conf.py](../../../conf/server_conf.py)
  defaults to `False`, with a `640 × 640` target. In the current
  [startup code](../../../run_server.py), selecting `gr00t_n1_7_eef` **and
  supplying `--model_path`** sets it to `True`. Selecting the model alone
  does not enable it. The Step 3 command therefore pads/resizes images before
  the policy's own preprocessing. This is a server setting; adding it to
  `conf/a2d_conf.yaml` does not configure the server.
- The adapter uses `ActionIKSolver` defaults: `dt=0.033`,
  `qp_solver="daqp"`, `max_iterations=100`, and
  `stagnation_iterations=0`. It does not forward an `ik` configuration
  dictionary. The time step constrains IK changes, not robot scheduling.

`run_server.py` accepts only `--model_type`, `--model_path`, and `--debug`.
Set the URDF, embodiment, and orientation options in the config factory;
there are no `--urdf_path`, `--rotation_type`, `--port`, or `--device`
flags. Restart the server after changes.

## Step 3 — Run the server

Run from the Open-RAIL repository root in the prepared N1.7 environment:

```bash
PYTHONPATH="/path/to/Isaac-GR00T:${PYTHONPATH}" python run_server.py \
  --model_type gr00t_n1_7_eef \
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
EXPECTED_HORIZON = 40
TIMEOUT_SECONDS = 180
OUTPUT_DIR = Path("gr00t_smoke_result")

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

The script sends one observation and checks a finite `(40, 16)` action
array, echoed timestamps, request ID, and inference-time metadata. It saves
`pred_action.npy`, `response.pkl`, and `result.json` in `gr00t_smoke_result`;
it does not send robot motion commands. Use a new `OUTPUT_DIR` for each run.

The default `EXPECTED_HORIZON=40` comes from the inspected checkpoint processor's action indices.
Change it for another checkpoint, and adjust `ENDPOINT`, `TIMEOUT_SECONDS`,
and the language instruction as needed. On timeout, inspect the server log
and check dependencies, checkpoint assets, and configuration. A passing
response check does not establish IK convergence; success flags are not
included in the wire response.

## Step 5 — Connect your client or robot

### Robot-side requirements

| Item | Expected | Implementation |
| --- | --- | --- |
| Camera keys | `cam.head`, `cam.hand_left`, `cam.hand_right` for the example checkpoint | [Adapter](gr00t_n1_7_eef.py), `_CAMERA_KEYS` |
| Image encoding | JPEG/PNG bytes; BGR before OpenCV encoding, RGB after server decoding | [Shared server](../../core/vla_server.py) |
| State layout | `[0:7]` left arm, `[7:14]` right arm, `[14]` left gripper, `[15]` right gripper | [FK/IK conversion](../../utils/eef_utils/action_to_joints.py) |
| Action output | Finite `float64 (T, 16)`, same joint/gripper order; absolute targets | [FK/IK conversion](../../utils/eef_utils/action_to_joints.py) |
| Control frequency | Supplied by the client/controller, not the response | [Architecture](../../../docs/architecture.md) §2 |

Arm angles follow the URDF in radians; EEF translations use its length scale
(metres for the supplied A2D model). Gripper values pass through FK/IK without
unit conversion and must match the training data.

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
        "language": ["pick the bottle into the basket"],
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

The adapter maps checkpoint video keys to decoded observations:

| Checkpoint video key | Request key |
| --- | --- |
| `cam_top_head` | `cam.head` |
| `cam_left_wrist` | `cam.hand_left` |
| `cam_right_wrist` | `cam.hand_right` |

Unsupported checkpoint video keys cause a startup error. The adapter reads
only the cameras declared by the checkpoint.

The default FK result is 20-dimensional:
`[left XYZ+Rot6D (9), right XYZ+Rot6D (9), left gripper, right gripper]`.
The inspected checkpoint uses `left_arm`, `right_arm`, `left_hand`,
`right_hand` in that order for both state and action. The adapter derives
state slices from the checkpoint's ordered state keys and statistics widths,
and concatenates action outputs in its ordered action keys. Matching total
dimension alone is insufficient: these orders must agree with the configured
FK/IK layout.

The adapter supplies one observation time step (`B=1, T_obs=1`). Checkpoints
requiring multiple video/state history steps are not supported by this path.
Clients must send joint feedback, not EEF poses, normalized model state, or
relative action offsets. `Gr00tPolicy` owns checkpoint preprocessing and
action decoding; IK consumes its decoded pose targets.

```python
response = {
    "type": "vla_action",
    "pred_action": actions,  # np.ndarray, float64, shape (T, 16)
    "ref_timestamp": request["ref_timestamp"],
    "loc_timestamp": request["loc_timestamp"],
    "ext": {},  # May contain prob_progress when returned by the policy.
}
```

`T` follows the checkpoint action horizon. The output contains absolute joint
and gripper targets, without a batch dimension. Do not add current state or
accumulate outputs as increments. `prob_progress` is optional: the adapter
forwards it from policy info or a NumPy-valued action field when present;
it does not compute task progress itself.

## Notes and known issues

- `embodiment_tag` and the state/action modality order must match the checkpoint.
- **Verify that IK works correctly before using a real robot.**
- **The URDF and fixed body pose must match the observation.** Extra head/waist
  state entries do not update the reduced FK model; its non-arm joints remain
  fixed at `reset_position`.

## Upstream project

- Source: Isaac-GR00T; the imported policy entry is
  `gr00t.policy.gr00t_policy.Gr00tPolicy`.
- License: upstream code and weights retain their respective licenses; this
  repository's license does not replace their terms.

Implementation references:

- [Model configuration](../../../conf/models_conf.py): `get_gr00t_n1_7_eef_config()`.
- [Adapter](gr00t_n1_7_eef.py): policy invocation and serialized inference.
- [FK/IK conversion](../../utils/eef_utils/action_to_joints.py): layouts, feedback seeds, output dtype.
- [Pink solver](../../utils/eef_utils/pink_single_arm_solver.py): convergence and failure behavior.
- [Shared server](../../core/vla_server.py): image decoding and responses.
- [ZMQ server](../../core/zmq_server.py): framing and heartbeats.
- [Real client](../../../client/core/vla_client.py): `_process_data()` request format.
