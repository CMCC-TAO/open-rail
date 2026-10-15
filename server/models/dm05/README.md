# DM0.5 (OpenDM) adapter

Open-RAIL runs `opendm.infer.policy.DM05Policy` in-process through
[`dm05.py`](dm05.py). It handles ZMQ transport and image decoding; no separate
OpenDM HTTP service is needed.

## Prerequisites

- An OpenDM source tree containing `opendm/infer/policy.py`, with compatible
  `DM05Policy.from_checkpoint()` / `predict()` APIs and `run_config.json` replay.
- A checkpoint trained for the target robot, including model weights,
  `config.json`, processor/tokenizer assets, `norm_stats.json` and preferably
  `run_config.json`. Keep its training joint order, camera order and units.
- One Python environment containing both OpenDM and Open-RAIL dependencies.
  Follow the selected OpenDM revision's PyTorch/CUDA installation instructions.

```bash
python -m pip install -e /path/to/dm_base
python -m pip install -e /path/to/open-rail
python -c "from opendm.infer.policy import DM05Policy; print('Policy import OK')"
```

For the `fast` backend, also install compatible TensorRT, Triton and ONNX
dependencies through OpenDM's `fast-infer` extra:

```bash
python -m pip install -e "/path/to/dm_base[fast-infer]"
```

Base pretrained weights do not replace a checkpoint trained for your robot.
LoRA exports additionally need their adapter assets and an accessible base model.

## Configuration

Edit `get_dm05_config()` in
[`conf/models_conf.py`](../../../conf/models_conf.py):

| Field | Meaning | Current default |
| --- | --- | --- |
| `model_path` | Checkpoint directory; overridden by `--model_path` | `/path/to/model` |
| `repo_path` | OpenDM source directory containing `opendm/` | `/path/to/repo` |
| `action_mode` | Legacy training-mode fallback: `absolute` or `relative` | `absolute` |
| `backend` | `default`, `fast` or `compile` | `fast` |
| `vision_trt_engine_path` | Vision engine location for `fast` | `/path/to/dm05_vision.engine` |
| `diffusion_steps` | Denoising iterations, not action count | `10` |
| `vision_attn_implementation` | Vision attention implementation | `flash_attention_2` |
| `execute_horizon` | Maximum action rows returned per request; must be positive | `16` |

Replace the placeholder paths. For the first integration check, use
`backend='default'` and `vision_trt_engine_path=None` to avoid TensorRT setup.
Vision-attention dependencies are still required. With `fast`, use a writable
engine path matching the checkpoint and deployment environment; first startup
may build the engine. `compile` uses `torch.compile` and warms prompt-length
buckets at startup, without a TensorRT engine.

### Checkpoint contract versus deployment settings

- `run_config.json` restores training-contract fields such as action mode,
  preprocessing settings and model chunk size. Recorded fields override caller
  settings; `action_mode` and `DM05_ACTION_MODE` only provide a fallback when
  that mode is not recorded.
- `norm_stats.json` supplies normalization and inferred state/action widths;
  `config.json` supplies chunk size when not superseded by the contract.
- Paths, backend, engine location, diffusion steps, vision attention and
  `execute_horizon` remain deployment settings in Open-RAIL.

Normally do not restate `action_dim`, `state_pad_to`, `chunk_size` or
`dataset_name`: the compatible backend reads the checkpoint. The adapter accepts
these optional fields for compatibility, but missing training settings are not
automatically reconstructed. Prefer a complete export with `run_config.json`.
An optional `robot_type` must use the OpenDM checkpoint/profile identifier,
which is not necessarily Open-RAIL's `agibot_g1` name.

For `compile`, optional `compile_warmup_prompts` supplies representative task
instructions. Alternatively use `language_cmd_path` with
`compile_warmup_language_key`; without usable prompts, OpenDM uses a synthetic
length sweep. Uncovered inputs can still trigger recompilation.

Shared settings in [`conf/server_conf.py`](../../../conf/server_conf.py):

- Set `max_infer_workers=1`: DM05 has no inference lock; the shared default is 3.
- `image_pad_and_resize=False` by default. If enabled, target height/width are
  configurable (default `640 × 640`); preprocessing must remain training-compatible.

The ZMQ port defaults to `5566` in
[`conf/zmq_conf.py`](../../../conf/zmq_conf.py). `conf/default_conf.yaml` configures
the Web client, not this server.

## Run

From the Open-RAIL root, in the prepared environment:

```bash
python run_server.py \
  --model_type dm05 \
  --model_path /path/to/agibot_g1/checkpoint \
  --debug
```

Wait for model loading and any engine build/compile warmup to finish. Check the
`backend=...` log and the first prediction's `action_shape` / `model_latency_ms`.
Only `--model_type`, `--model_path` and `--debug` are accepted; edit configuration
for other settings and restart the server. Run one server per port.

## Input and output

Send a `vla_obs` request with `ref_timestamp`, `loc_timestamp` and `obs`:

| Observation field | Requirement |
| --- | --- |
| `cam.head` | Encoded head image; first backend camera |
| `cam.hand_left` | Encoded left wrist image; second camera |
| `cam.hand_right` | Encoded right wrist image; third camera |
| `state` | Finite 1-D `float32` NumPy vector in training order and units |
| `language` | Nonempty string or list/tuple; only the first instruction is used |

All three cameras are required. Send JPEG/PNG bytes or encoded `uint8` arrays,
not raw pixel arrays. Images and state should describe the same observation.
Observation lists use only their first element, not batch/history inference.

An AgiBot G1 gripper checkpoint may use 20 state values and 16 action values:
left arm `[0:7]`, right arm `[7:14]`, grippers `[14:16]`, with head `[16:18]`
and waist `[18:20]` present only in state. These are example dimensions, not
adapter constants. Check the training export and robot configuration.
Zero-padding short states does not replace real observations needed by the model.

Successful responses contain `type='vla_action'`, `pred_action` as
`float32 (T, action_dim)`, unchanged timestamps and `ext={}`. For a positive
execution horizon, `T=min(predicted_chunk_length, execute_horizon)`; the default
returns at most 16 rows. This slices the output, not the model's trained horizon.

The backend normalizes state and denormalizes actions. For relative training,
it reconstructs absolute targets; absolute training already yields absolute
targets. Do not normalize twice or add state again. The server does not execute
actions or set control speed; client scheduling and fusion do that.

Use ZMQ **DEALER** with two payload frames: pickle observation + JSON metadata.
The server uses ROUTER and adds `avg_infer_time` to response metadata. Do not
use REQ or add an identity/delimiter frame. Pickle requires trusted peers.
See the [architecture guide](../../../docs/architecture.md) for shared transport
and the [Quick Start](../../../README.md#-quick-start) for client setup.

## Known limitations

- **Colors:** shared decoding converts BGR to RGB, but DM05's `_to_pil()` reverses
  channels again. Standard encoded images currently reach the policy with red/
  blue swapped; check against training preprocessing before hardware use.
- **Errors:** non-finite output returns `vla_status/not_ready`, not an action.
  The shared callback may then log a missing-`pred_action` error. Other inference
  failures do not guarantee an error response; set a timeout and inspect logs.
- **History/reset:** no `history_images` are forwarded and `reset()` is a no-op.
  An observation list does not enable DM05-MEM temporal inference.
- **Validation:** verify camera colors, joint order, units and action bounds.
  Finite output or dataset replay does not prove closed-loop task success.

Implementation: [adapter](dm05.py),
[shared server](../../core/vla_server.py),
[robot configuration](../../../conf/robots_conf.py). In OpenDM, see
`opendm/infer/policy.py` and `opendm/exp/run_config.py`. Model source and weights
remain subject to their own licenses.
