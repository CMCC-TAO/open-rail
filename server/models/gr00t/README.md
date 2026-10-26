# GR00T (Isaac-GR00T) adapter family

Open-RAIL runs NVIDIA Isaac-GR00T policies in-process through the adapters in
this directory. One adapter is provided per generation; all of them expose the
same `infer(sequence)` contract used by the shared ZMQ server.

| `--model_type` | Adapter | Config entry | Policy API |
| --- | --- | --- | --- |
| `gr00t_n1` | [`gr00t_n1.py`](gr00t_n1.py) | `config.models.gr00t` | `gr00t.model.policy.Gr00tPolicy` |
| `gr00t_n1_5` | [`gr00t_n1_5.py`](gr00t_n1_5.py) | `config.models.gr00t` | `gr00t.model.policy.Gr00tPolicy` |
| `gr00t_n1_6` | [`gr00t_n1_6.py`](gr00t_n1_6.py) | `config.models.gr00t` | `gr00t.policy.gr00t_policy.Gr00tPolicy` |
| `gr00t_n1_7` | [`gr00t_n1_7.py`](gr00t_n1_7.py) | `config.models.gr00t1_7` | `gr00t.policy.gr00t_policy.Gr00tPolicy` |
| `gr00t_n1_7_eef` | [`gr00t_n1_7_eef.py`](gr00t_n1_7_eef.py) | `config.models.gr00t_n1_7_eef` | `gr00t.policy.gr00t_policy.Gr00tPolicy` + Pink IK |

The first four adapters return model-space actions. `gr00t_n1_7_eef` converts
joint feedback to EEF state, calls the policy, and converts EEF actions back to
joint targets through the bundled IK solver.

## Prerequisites

- **Upstream source** — an Isaac-GR00T checkout matching the adapter. N1 and
  N1.5 import `gr00t.model.policy`, `gr00t.data.schema` and
  `gr00t.experiment.data_config`; N1.6, N1.7 and N1.7 EEF import
  `gr00t.policy.gr00t_policy` and `gr00t.data.embodiment_tags`. The adapter does
  not insert a source path, so install the checkout or put its root first on
  `PYTHONPATH`.
- **Checkpoint** — a fine-tuned checkpoint directory for the target robot,
  including `config.json`, every weight shard and index, processor assets, and
  statistics for the configured embodiment tag. N1.5 additionally reads
  `experiment_cfg/metadata.json`; N1.7 EEF reads processor statistics first and
  then `statistics.json` / `experiment_cfg/dataset_statistics.json`. Original
  upstream pretrained weights do not replace a checkpoint trained for your
  robot.
- **Environment** — one Python environment per generation. Open-RAIL server
  dependencies come from [pyproject.toml](../../../pyproject.toml). The EEF
  adapter also needs `pin-pink` (import `pink`), Pinocchio (import
  `pinocchio`), `qpsolvers` and `daqp`.

```bash
# N1 / N1.5 generation (example upstream checkout)
conda create -n gr00t_xx python=3.10
conda activate gr00t_xx
cd /path/to/Isaac-GR00T
pip install --upgrade setuptools
pip install -e .
pip install --no-build-isolation flash-attn==2.7.4.post1
pip install -e /path/to/open-rail
```

To reuse an existing environment, clone it and install the checkout without
dependencies: `conda create --name new_env --clone old_env`, then
`pip install -e . --no-deps` from the Isaac-GR00T root. When several GR00T
versions share one environment, uninstall `gr00t` and select the checkout per
run through `PYTHONPATH`.

## Configuration

Edit the matching factory in [conf/models_conf.py](../../../conf/models_conf.py).

`gr00t_n1`, `gr00t_n1_5`, `gr00t_n1_6` — `get_gr00t_config()`:

| Field | Meaning | Current default |
| --- | --- | --- |
| `model_path` | Checkpoint directory; overridden by `--model_path` | `/path/to/model` |
| `embodiment_tag` | Embodiment tag passed to the policy (N1.5) | `a2d` |
| `data_config_key` | Isaac-GR00T data config used for modalities (N1.5) | `a2d_arms_only` |

N1 hardcodes `EmbodimentTag.NEW_EMBODIMENT` and `DATA_CONFIG_MAP["a2d_arms_only"]`,
and N1.6 hardcodes `EmbodimentTag.A2D`; the factory fields apply to N1.5 only.

`gr00t_n1_7` — `get_gr00t_1_7_config()`:

| Field | Meaning | Current default |
| --- | --- | --- |
| `model_path` | Checkpoint directory; overridden by `--model_path` | `/path/to/model` |
| `embodiment_tag` | Tag resolved through `EmbodimentTag.resolve` | `new_embodiment` |
| `denoising_steps` | Value written to `policy.model.action_head.num_inference_timesteps` | `4` |

N1.7 removed the A2D tag; A2D fine-tunes register under `new_embodiment`.
`denoising_steps` is no longer a `Gr00tPolicy` constructor argument.

`gr00t_n1_7_eef` — `get_gr00t_n1_7_eef_config()`:

| Field | Meaning | Current default |
| --- | --- | --- |
| `model_path` | Checkpoint directory; overridden by `--model_path` | `/path/to/model` |
| `embodiment_tag` | Tag resolved through `EmbodimentTag.resolve` | `new_embodiment` |
| `joint_action_key` | EEF action slices passed to IK, despite the field name | Left pose `[0, 9]`, right pose `[9, 18]`, grippers `[18, 19]`, `[19, 20]` |
| `joint_state_key` | Input joint/gripper slices | Left arm `[0, 7]`, right arm `[7, 14]`, grippers `[14, 15]`, `[15, 16]` |
| `urdf_path` | Robot model used for FK and IK | Repository `server/utils/eef_utils/urdf/a2d_vla_zero_state.urdf` |
| `link_name` | Arm base and TCP frames | `base_link_l` → `gripper_center`; `base_link_r` → `right_gripper_center` |
| `q_left_init`, `q_right_init` | Fallback IK seeds | A2D seven-joint poses in `_get_a2d_eef_config()` |
| `reset_position` | Full URDF configuration; non-arm joints stay fixed here | A2D 34-value configuration |
| `ref_frame` | EEF frame: URDF world or arm base (`local`) | `world` |
| `rotation_type` | EEF orientation representation | `rot6d` |
| `rot6d_convention` | Rot6D construction; `rows` flattens the first two rotation-matrix rows | `rows` |

The EEF adapter falls back from `a2d` to `NEW_EMBODIMENT` when the upstream enum
cannot resolve it. To use a new robot, update `urdf_path`, `joint_state_key`,
`joint_action_key`, `link_name`, `q_left_init`, `q_right_init` and
`reset_position` to match its URDF and training layout.

Shared settings:

- The ZMQ port defaults to `5566` in [conf/zmq_conf.py](../../../conf/zmq_conf.py).
- `max_infer_workers` defaults to `3` in [conf/server_conf.py](../../../conf/server_conf.py).
  Only the EEF adapter serializes requests with an internal lock; set
  `max_infer_workers=1` for the other adapters unless the upstream policy is
  known to be thread-safe.
- `image_pad_and_resize` defaults to `False` with a `640 × 640` target. Selecting
  `gr00t_n1_7_eef` together with `--model_path` sets it to `True` in
  [run_server.py](../../../run_server.py). All other adapters use the flag value
  from `conf/server_conf.py`.

`run_server.py` accepts only `--model_type`, `--model_path` and `--debug`; edit
the configuration for other settings and restart the server.

## Run

From the Open-RAIL root, in the environment prepared for the selected
generation:

```bash
# N1 / N1.5 / N1.6 / N1.7
PYTHONPATH="/path/to/Isaac-GR00T:${PYTHONPATH}" python run_server.py \
  --model_type gr00t_n1_7 \
  --model_path /path/to/checkpoint \
  --debug

# N1.7 EEF
PYTHONPATH="/path/to/Isaac-GR00T:${PYTHONPATH}" python run_server.py \
  --model_type gr00t_n1_7_eef \
  --model_path /path/to/a2d/ckpt \
  --debug
```

Replace `gr00t_n1_7` with `gr00t_n1`, `gr00t_n1_5` or `gr00t_n1_6` as needed.
Wait for model loading to finish; for EEF also confirm that the checkpoint video
keys match the adapter's supported set. Run one server per port. The client
runs separately; see the root [Quick Start](../../../README.md#-quick-start).

## Input and output

Send a `vla_obs` request with `ref_timestamp`, `loc_timestamp` and `obs`:

| Observation field | Requirement |
| --- | --- |
| `cam.head` | Encoded head image |
| `cam.hand_left` | Encoded left wrist image |
| `cam.hand_right` | Encoded right wrist image |
| `state` | Finite 1-D NumPy vector in training joint order and units |
| `language` | Nonempty string, or a list/tuple containing one instruction |

Send JPEG/PNG bytes or encoded `uint8` arrays, not raw pixel arrays. Images and
state should describe the same observation. A list of observations uses only
its first element; it does not enable batch or history inference.

Camera and state mapping per adapter:

| Adapter | Head camera key | State layout |
| --- | --- | --- |
| `gr00t_n1` | `video.cam_right_high` | `[0:7]` left arm, `[7:14]` right arm, `[14]` left hand, `[15]` right hand |
| `gr00t_n1_5` | `video.cam_top_head` | Slices derived from `experiment_cfg/metadata.json` for `data_config_key` |
| `gr00t_n1_6` | `cam_top_head` | `[0:7]` left arm, `[7:14]` right arm, `[14]` left hand, `[15]` right hand |
| `gr00t_n1_7` | `top_head` | `[0:7]` left arm, `[7:14]` right arm, `[14:15]` left gripper, `[15:16]` right gripper |
| `gr00t_n1_7_eef` | Checkpoint-declared keys mapped to `cam.*` | Only the configured slices enter FK; extra dimensions are ignored |

`gr00t_n1_7_eef` accepts only checkpoints whose video keys are `cam_top_head`,
`cam_left_wrist` and `cam_right_wrist`, and requires joint feedback (not EEF
poses or normalized state). Its output is converted to absolute joint/gripper
targets; arm angles follow the URDF in radians and gripper values pass through
without unit conversion.

Language handling differs by generation: N1 and N1.5 pass
`annotation.human.task_description` at the top level; N1.6 and N1.7 nest it under
`language`; EEF uses the checkpoint's own `policy.language_key`.

Successful responses contain `type='vla_action'`, `pred_action`, unchanged
timestamps and `ext`. `pred_action` is a NumPy array of shape
`(T, action_dim)`, where `T` follows the checkpoint action horizon. N1 returns
no `ext` key. The other adapters return `ext={}` plus `prob_progress` when the
policy provides it; EEF returns it without indexing.

The server does not execute actions or set control speed; client scheduling and
fusion do that. Use ZMQ **DEALER** with two payload frames: pickle observation
plus JSON metadata. The server uses ROUTER and adds `avg_infer_time` to the
response metadata. Pickle requires trusted peers. See the
[architecture guide](../../../docs/architecture.md) for shared transport.

## Known limitations

- **Version coupling:** use the Isaac-GR00T checkout that matches the adapter.
  An older or newer `gr00t` package may expose a different `Gr00tPolicy` API.
- **Hardcoded tags:** N1 ignores `embodiment_tag` / `data_config_key` and uses
  `NEW_EMBODIMENT` with `a2d_arms_only`; N1.6 ignores `embodiment_tag` and uses
  `A2D`. Set the checkpoint's actual tag when running N1.5 or N1.7.
- **History:** every adapter uses only `sequence[0]` and one observation time
  step. Checkpoints requiring multiple video/state history steps are not
  supported.
- **IK verification:** for `gr00t_n1_7_eef`, verify IK convergence and URDF /
  fixed body pose correctness before using a real robot. A finite action array
  does not prove task success.
- **Concurrency:** except for EEF, the adapters have no inference lock; keep
  `max_infer_workers=1` unless the upstream policy is known to be thread-safe.
- **Validation:** verify camera color order, joint order, units and action
  bounds against the training pipeline before hardware use.

## Upstream project

- Source: NVIDIA Isaac-GR00T. Imported entry points are listed in the adapter
  table above.
- Code and weights remain subject to their own licenses; this repository's
  license does not replace their terms.

Implementation references:

- [Model configuration](../../../conf/models_conf.py): `get_gr00t_config()`,
  `get_gr00t_1_7_config()`, `get_gr00t_n1_7_eef_config()`.
- Adapters: [`gr00t_n1.py`](gr00t_n1.py), [`gr00t_n1_5.py`](gr00t_n1_5.py),
  [`gr00t_n1_6.py`](gr00t_n1_6.py), [`gr00t_n1_7.py`](gr00t_n1_7.py),
  [`gr00t_n1_7_eef.py`](gr00t_n1_7_eef.py).
- [FK/IK conversion](../../utils/eef_utils/action_to_joints.py): layouts,
  feedback seeds, output dtype.
- [Pink solver](../../utils/eef_utils/pink_single_arm_solver.py): convergence
  and failure behavior.
- [Shared server](../../core/vla_server.py): image decoding and responses.
- [ZMQ server](../../core/zmq_server.py): framing and heartbeats.
- [Real client](../../../client/core/vla_client.py): `_process_data()` request
  format.
