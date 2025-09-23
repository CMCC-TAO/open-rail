# VLA Model Offline Evaluation Tool

This tool is used for offline evaluation of VLA models, helping analyze model prediction accuracy by visualizing comparisons between model-predicted action data and ground truth data.

## Features

- Supports lerobot format ground truth data (parquet, etc.), but does not require lerobot dependency, with faster evaluation speed
- Visualizes comparison between predicted and actual values for each joint dimension, along with their MSE
- Marks red dots at each lookahead_idx, which can be set to chunk_size

## Prerequisites

- This visualization tool depends on: `vla_infer/server/models/<model_name>/vla_model.py`, different models need to implement this file for evaluation.
- Different models may have inconsistent inputs, requiring modification of obs mapping at TODO locations in vis_eval.py.

## Usage

```bash
# Different models need to modify obs mapping at TODO locations in the code
python vis_eval.py \
--model_path /hy0505/checkpoints/gr00t_finetune/pickbottle_499_chunk64_20250507_192258_b24/checkpoint-60000 \
--gt_root /hy0505/dataset/A2d_zyhy_data/gr00t/task_158284_depth_test/task_158284_test \
--lookahead_idx 64 \
--episode_id 0 \
--chunk_id 0 \
--joint_dim 16 \
--dt_length -1 \
--split_ids 0-7,7-14,14-15 \
--language 'pick bottle into the box' \
--note ''
```

Parameter description
```bash
python vis_eval.py -h
```

## Notes

None

## Output Example

```
0.05212831497192383 action shape: (64, 16)
Using trajectory 0 length: 429, average MSE: 0.00017928320901957972
EVAL chart saved to: ./img_vis_eval.png
```

![example_output](./example_output.jpg)

```
Contributors: Zhao Lei
```
