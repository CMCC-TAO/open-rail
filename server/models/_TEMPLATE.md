> **Template** — copy this entire file to `server/models/<your_model>/README.md`, replace every `{{PLACEHOLDER}}` (search for `{{` afterwards: it should return zero matches), then delete this line. A completed example: [`wallx/README.md`](wallx/README.md).

# {{MODEL_NAME}} Adapter

This guide describes `run_server.py --model_type {{MODEL_TYPE}}`, using the
`{{VALIDATED_ROBOT_CONFIG}}` configuration as the worked example. The camera
fields, state/action dimensions, and client code below describe this example.
For another configuration, align the interface and checkpoint with its
training layout.

**How to read this guide:** Steps 1–4 get one inference request answered on your
machine (prepare → configure → start → smoke-test). Step 5 is for wiring a real
robot or client to the running server. Pitfalls are collected under Notes.

## Step 1 — Prerequisites

- **Upstream source** — {{UPSTREAM_PROJECT_NAME}}; its adapter entry is the module `{{ENTRY_MODULE}}`. Depending on the model, the upstream is either a checkout to clone (as a sibling of this repository, or wherever `repo_path` points — the adapter inserts that path into `sys.path`; it is not vendored), a pip-installed package, or code that lives inside this repository — describe whichever applies.
- **Checkpoint** — a directory fine-tuned for this state/action layout, containing:
  - {{CHECKPOINT_FILE_1}}
  - {{CHECKPOINT_FILE_2}}
  - {{CHECKPOINT_FILE_3}}

  {{WHAT_IS_NOT_USED_AND_WHY}} **Original upstream weights do not replace a checkpoint fine-tuned for this layout.**
- **Environment** — must contain both the model's own dependencies and the Open-RAIL server dependencies, including `{{MODEL_SPECIFIC_DEP}}`.

## Step 2 — Configuration

Fields of `get_{{MODEL_TYPE}}_config()` in [`conf/models_conf.py`](../../../conf/models_conf.py) that this adapter reads:

| Field | Required | Meaning | Default |
| --- | --- | --- | --- |
| `model_path` | yes | Checkpoint directory | `/path/to/model`; overridden by `--model_path` |
| {{FIELD}} | {{yes/no}} | {{WHAT_IT_CONTROLS}} | {{DEFAULT_VALUE}} |

Shared server settings that also apply (documented once in [`docs/configuration.md`](../../../docs/configuration.md)):

- {{SHARED_SETTING_1}}
- {{SHARED_SETTING_2}}

`run_server.py` accepts only `--model_type`, `--model_path`, and `--debug`; there is no `--port` or `--device` — edit the configuration entries instead. Restart the server after changing adapter code.

## Step 3 — Run the server

```bash
# Run in the environment described under Step 1
python run_server.py \
  --model_type {{MODEL_TYPE}} \
  --model_path /path/to/{{ROBOT_CONFIG}}/checkpoint \
  --debug
```

The client half runs on the robot side — see the root [Quick Start](../../../README.md#-quick-start).

## Step 4 — Smoke-test with one request

Before wiring a robot, verify the server answers a single inference request.
Save the following code as a Python script. Prepare {{INPUT_FILES_FROM_SAME_OBSERVATION}}
and set an instruction matching the scene. {{STATE_SOURCE_REQUIREMENT}}.
Requires `numpy` and `pyzmq`.

```python
{{MINIMAL_SINGLE_REQUEST_SCRIPT}}
```

The script prints {{EXPECTED_SHAPE}} plus the response metadata on success.
A `TimeoutError` means the request never got an action response: re-check Step 2
(`repo_path`, `model_path`) and inspect the server log. Adjust the action-shape
check when using a checkpoint with a different horizon.

## Step 5 — Connect your client or robot

Everything in Steps 1–4 applies unchanged here; this step defines what your
client must send and what the returned chunk means.

### Robot-side requirements

| Item | Expected | Where it is checked |
| --- | --- | --- |
| Camera keys | `{{CAM_KEY_1}}`, `{{CAM_KEY_2}}` | must match `robots.{{ROBOT_TYPE}}.camera.names` ([`conf/robots_conf.py`](../../../conf/robots_conf.py)) |
| Image encoding | encoded JPEG/PNG **bytes**; BGR before `cv2.imencode` | the shared server calls `cv2.imdecode` ([`server/core/vla_server.py`](../../../core/vla_server.py)) |
| State layout | {{DIMENSIONS_AND_JOINT_ORDER}} | [`{{FILE}}:{{LINE}}`]({{FILE}}) |
| Action output | `float32 (T, {{ACTION_DIM}})`; {{ABSOLUTE_OR_INCREMENTAL}}; {{SEMANTICS_OF_EACH_DIM}} | [`{{FILE}}:{{LINE}}`]({{FILE}}) |
| Control frequency | {{WHETHER_PART_OF_THIS_CONTRACT}} | [`docs/architecture.md`](../../../docs/architecture.md) §2 |

Values must match the checkpoint's training joint order and original units. Do not substitute end-effector poses, and do not independently rescale angles or gripper values.

### Request and response

Send one observation dictionary per inference request:

```python
{{REQUEST_DICT_EXAMPLE}}
```

| Field | Requirement |
| --- | --- |
| `type` | Must be `vla_obs` |
| `ref_timestamp` | Observation timestamp; the real client uses monotonic nanoseconds. Returned unchanged. |
| `loc_timestamp` | `time.perf_counter()` in seconds. Returned unchanged. Absolute monotonic timestamps cannot be compared across machines. |
| `{{CAM_KEY_1}}` / `{{CAM_KEY_2}}` / {{OTHER_CAM_KEYS}} | JPEG/PNG-encoded image **bytes**, or a contiguous encoded `uint8` array. **Do not send raw `(H, W, 3)` pixel arrays** — the shared server calls `cv2.imdecode`. Convert `memoryview` to `bytes` before pickling, and convert RGB sources to BGR before encoding; the server decodes and converts back to RGB. |
| `state` | {{STATE_REQUIREMENT}} (truncated, padded, or exact — per your adapter) |
| `language` | {{LIST_OR_STRING}}; {{WHICH_ITEM_IS_USED}} |

Use images and state from the **same observation time**. {{DATASET_CAMERA_MAPPING_IF_ANY}}

The server also accepts observation lists, but {{WHAT_THE_ADAPTER_ACTUALLY_USES}}.
Clients must not perform model normalization, state discretization, internal
padding, or action-mask construction — the backend applies them internally,
and doing both would double-apply the transform.

The response:

```python
{{RESPONSE_DICT_EXAMPLE}}
```

{{RESPONSE_SEMANTICS_CHUNK_LENGTH_ABSOLUTE_VS_INCREMENTAL_UNITS_AND_EXT}}

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

- {{HARD_CODED_VALUE_AND_FILE_LINE}}
- {{WHAT_BREAKS_IF_CAMERA_SET_DIFFERS}}
- {{CONCURRENCY_BEHAVIOR}}
- **Dataset replay checks protocol behavior and action curves, not closed-loop robot
  task success.** Do not read a clean replay as proof the policy can do the task.
- {{OTHER_PITFALLS_YOU_HIT}}

## Upstream project

- Source: {{UPSTREAM_PROJECT_NAME}} (official repository on GitHub / Hugging Face; the stable contract is the module entry `{{ENTRY_MODULE}}`, not a URL)
- License: the upstream model code and weights are covered by the upstream repository's own license, not this repository's Apache-2.0 — check the upstream license before use

Implementation references:

- [Model configuration](../../../conf/models_conf.py): `get_{{MODEL_TYPE}}_config()`.
- [Adapter]({{MODEL_TYPE}}.py): policy invocation and serialized inference.
- [Shared server](../../core/vla_server.py): image decoding, responses, exception handling.
- [ZMQ server](../../core/zmq_server.py): framing and heartbeats.
- [Real client](../../../client/core/vla_client.py): `_process_data()` request format.
