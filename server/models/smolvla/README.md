# SmolVLA adapter

Open-RAIL runs a LeRobot SmolVLA policy in-process through
[`smolvla.py`](smolvla.py). The adapter builds the policy with LeRobot's
`TrainPipelineConfig` / `make_policy()` and calls
`policy.predict_action_chunk()`; it handles ZMQ transport and image decoding
through the shared server.

## Prerequisites

- A **LeRobot** environment that provides `lerobot.policies.smolvla`,
  `lerobot.configs`, `lerobot.datasets` and `make_policy()`. Use a LeRobot
  revision whose `TrainPipelineConfig`, `LeRobotDatasetMetadata` and
  `make_policy()` signatures match the adapter.
- A **SmolVLA training output** containing the policy configuration and
  weights, passed as `model_path`.
- A **LeRobot dataset root** containing the dataset `meta/` used to build
  `LeRobotDatasetMetadata` (repo id hardcoded as `data`, codebase version
  `1.2`). The metadata must declare the three camera keys and the state/action
  widths used during training.
- One Python environment containing LeRobot, PyTorch, `opencv-python`, Pillow,
  pandas, and the Open-RAIL dependencies from
  [pyproject.toml](../../../pyproject.toml). The policy runs on the device
  selected by `cfg.policy.device`; a CUDA build is expected for practical
  latency.

```bash
python -m pip install -e /path/to/lerobot
python -m pip install -e /path/to/open-rail
```

Base pretrained weights do not replace a checkpoint fine-tuned for your robot.

## Configuration

Edit `get_smolvla_config()` in
[conf/models_conf.py](../../../conf/models_conf.py):

| Field | Meaning | Current default |
| --- | --- | --- |
| `model_path` | LeRobot training output passed to `TrainPipelineConfig.validate()`; overridden by `--model_path` | `/path/to/model` |
| `root_path` | Dataset root used by `LeRobotDatasetMetadata` | `/path/to/root` |

`root_path` has no command-line override; set it in the config factory and
restart the server. The adapter registers the metadata with
`repo_id="data"` and version `"1.2"`, so `root_path` is the directory
containing `meta/`, `data/` and `videos/` for that dataset.

Shared settings:

- The ZMQ port defaults to `5566` in [conf/zmq_conf.py](../../../conf/zmq_conf.py).
- Set `max_infer_workers=1` in [conf/server_conf.py](../../../conf/server_conf.py):
  the adapter has no inference lock, while the shared default is `3`.
- `image_pad_and_resize=False` by default. If enabled, target height/width are
  configurable (default `640 × 640`); resizing must remain compatible with the
  policy's own preprocessing.

`run_server.py` accepts only `--model_type`, `--model_path` and `--debug`; edit
the configuration for other settings and restart the server.

## Run

From the Open-RAIL root, in the prepared LeRobot environment:

```bash
python run_server.py \
  --model_type smolvla \
  --model_path /path/to/lerobot/output \
  --debug
```

Wait for the policy and dataset metadata to load. Only `--model_type`,
`--model_path` and `--debug` are accepted. Run one server per port. The client
runs separately; see the root [Quick Start](../../../README.md#-quick-start).

## Input and output

Send a `vla_obs` request with `ref_timestamp`, `loc_timestamp` and `obs`:

| Observation field | Requirement |
| --- | --- |
| `cam.head` | Encoded head image; mapped to `observation.images.top_head` |
| `cam.hand_left` | Encoded left wrist image; mapped to `observation.images.hand_left` |
| `cam.hand_right` | Encoded right wrist image; mapped to `observation.images.hand_right` |
| `state` | Finite 1-D NumPy vector forwarded unchanged as `observation.state` |
| `language` | Accepted but ignored; the adapter always uses a fixed task string |

Send JPEG/PNG bytes or encoded `uint8` arrays, not raw pixel arrays. Images are
decoded to RGB by the shared server and converted to `float32 (1, 3, H, W)` in
`[0, 1]` by the adapter. The state is not sliced, padded or normalized, so its
length and order must match the training dataset. Do not add a batch
dimension. A list of observations uses only its first element; it does not
enable batch or history inference.

Successful responses contain `type='vla_action'`, `pred_action`, unchanged
timestamps and `ext={}`. `pred_action` is a NumPy array of shape
`(T, action_dim)`, with the batch dimension squeezed out; `T` is the policy's
action chunk length and `action_dim` comes from the checkpoint. The adapter
neither normalizes nor un-normalizes actions:

- `predict_action_chunk()` performs the policy's own preprocessing and action
  decoding.
- The output is treated as absolute targets; no state is added and no
  increments are accumulated.

The server does not execute actions or set control speed; client scheduling and
fusion do that. Use ZMQ **DEALER** with two payload frames: pickle observation
plus JSON metadata. The server uses ROUTER and adds `avg_infer_time` to the
response metadata. Pickle requires trusted peers. See the
[architecture guide](../../../docs/architecture.md) for shared transport.

## Known limitations

- **Language prompt:** `obs['language']` is ignored; the task string is
  hardcoded as `pick bottle into the box`. Change it in
  [`smolvla.py`](smolvla.py) for a different task.
- **Dataset dependency:** `root_path` must contain LeRobot metadata compatible
  with the checkpoint. There is no fallback when the metadata is missing or
  declares different camera/state keys.
- **State handling:** the full state vector is passed through. Unlike the GR00T
  adapters, there is no slicing, padding or metadata-driven layout.
- **Single observation:** only `sequence[0]` is used; observation history and
  batch inference are not supported.
- **Concurrency:** no inference lock is held. Keep `max_infer_workers=1`
  unless the policy is known to be thread-safe.
- **Validation:** verify camera color order, joint order, units and action
  bounds against the training pipeline before hardware use.

Implementation references:

- [Model configuration](../../../conf/models_conf.py): `get_smolvla_config()`.
- [Adapter](smolvla.py): policy construction and serialized inference.
- [Shared server](../../core/vla_server.py): image decoding and responses.
- [ZMQ server](../../core/zmq_server.py): framing and heartbeats.
- [Real client](../../../client/core/vla_client.py): `_process_data()` request
  format.

Upstream SmolVLA and LeRobot code and weights remain subject to their own
licenses; this repository's license does not replace their terms.
