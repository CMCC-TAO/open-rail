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
cd /hy0505/XXX/Isaac-GR00T # Navigate to your gr00t project directory
pip install -e . --no-deps # Install only the local package without dependencies
```

#### Switching gr00t versions in the same conda environment
```bash
pip uninstall gr00t
PYTHONPATH=/hy0505/gaohan/Isaac-GR00T:$PYTHONPATH python run_server.py # Specify PYTHONPATH when running code
```

## GR00T N1.7

`server/models/gr00t/gr00t_n1_7.py` implements the GR00T N1.7 policy wrapper
(same `infer()` interface as `gr00t_n1_6.py`). It handles the N1.7 codebase
changes:

- `EmbodimentTag.A2D` no longer exists; a finetuned A2D checkpoint is registered
  under `EmbodimentTag.NEW_EMBODIMENT` (`'new_embodiment'`).
- Modality keys follow the A2D finetune config (`examples/a2d/agibot_a2d_config.py`):
  video `{top_head, hand_left, hand_right}`, state
  `{left_arm, right_arm, left_gripper, right_gripper}`.
- `denoising_steps` is no longer a `Gr00tPolicy` constructor argument; the action
  head reads `num_inference_timesteps` at sampling time.

### Code Repository
The vendored N1.7 gr00t package lives at `model/model_code/GR00T1.7/`
(and the working checkout at `model/model_code/isaac-gr00t-n1.7_wxz/`).

### Environment Setup
```bash
# One-time: creates the gr00t_1.7 conda env (python 3.12 + torch 2.9 cu128)
bash model/model_code/GR00T1.7/scripts/conda_setup_gr00t.sh

# Gated VLM backbone (nvidia/Cosmos-Reason2-2B) needs a HuggingFace login
conda activate gr00t_1.7
huggingface-cli login   # or: export HF_TOKEN=... (and HF_ENDPOINT=https://hf-mirror.com)
```

### Running the inference server
The wrapper uses the same caller interface as the other GR00T models: obs keys
`cam.head`, `cam.hand_left`, `cam.hand_right` (H, W, 3 uint8), a 16-dim `state`
(left_arm 7 + right_arm 7 + two grippers) and a `language` instruction string.

```bash
# PYTHONPATH must point at the N1.7 gr00t package so it shadows any other
# gr00t installed in the environment.
export PYTHONPATH=/home/rm/wxz/EmbodiedAI/vla_infer_web/vla_infer/model/model_code/isaac-gr00t-n1.7_wxz:$PYTHONPATH

python run_server.py \
    --model_type gr00t_n1_7 \
    --model_path /path/to/checkpoint-XXXXX
```

A ready-made launcher is provided at `gr00t_n1_7_test_server.sh` (repo root);
edit `CONDA_ENV`, `PYTHONPATH` and `--model_path` for your machine.

### Configuration
Registered as `config.models.gr00t1_7` in `conf/models_conf.py`:

| key | default | description |
| --- | --- | --- |
| `model_path` | `/path/to/model` | checkpoint directory |
| `embodiment_tag` | `new_embodiment` | embodiment tag name/value resolved via `EmbodimentTag.resolve` |
| `denoising_steps` | `4` | action-head denoising steps at sampling time |

### Usage in Python
```python
from server.models.gr00t.gr00t_n1_7 import ModelVLA

model = ModelVLA({
    'model_path': '/path/to/checkpoint-XXXXX',
    # 'embodiment_tag': 'new_embodiment',  # optional
    # 'denoising_steps': 4,                # optional
})
result = model.infer([{'obs': obs, 'ref_timestamp': ..., 'loc_timestamp': ...}])
pred_action = result['pred_action']  # (action_horizon, 16)
```

