# Unitree G1 VLA 模型训练完整指南

> **目标**: 在集群上使用TAO框架训练Unitree G1机器人的视觉-语言-动作(VLA)模型  
> **预训练模型位置**: `/data/shared_checkpoints/tao/v0d5` (推荐使用)  
> **DINO特征提取器**: `/data/shared_checkpoints/dino/dinov2-large`

---

## 📋 目录

1. [前置准备](#1-前置准备)
2. [第一步: 创建Unitree G1 Embodiment配置](#2-第一步-创建unitree-g1-embodiment配置)
3. [第二步: 计算归一化统计信息](#3-第二步-计算归一化统计信息)
4. [第三步: 修改训练脚本](#4-第三步-修改训练脚本)
5. [第四步: 提交训练任务](#5-第四步-提交训练任务)
6. [第五步: 监控训练进度](#6-第五步-监控训练进度)
7. [第六步: 获取训练结果](#7-第六步-获取训练结果)
8. [常见问题](#8-常见问题)

---

## 1. 前置准备

### 1.1 确认环境

```bash
# 激活conda环境
conda activate lingtao

# 验证TAO是否安装
python -c "import tao; print('TAO imported successfully')"

# 检查GPU可用性
nvidia-smi
```

### 1.2 确认预训练模型存在

```bash
# TAO v0d5预训练模型（推荐）
ls -lah /data/shared_checkpoints/tao/v0d5/

# DINOv2特征提取器
ls -lah /data/shared_checkpoints/dino/dinov2-large/
```

**预期输出**:
- TAO v0d5: 包含 `model-00001-of-00003.safetensors`, `config.json`, `processor/`
- DINOv2: 包含 `model.safetensors`, `pytorch_model.bin`

### 1.3 准备Unitree G1数据集

确保你的lerobot数据集格式正确，例如：

```
/path/to/unitree_g1_dataset/
├── task_001/
│   ├── meta/
│   │   ├── info.json
│   │   └── episodes.jsonl
│   ├── data/
│   │   ├── chunk-000/
│   │   │   └── episode_000000.parquet
│   │   └── ...
│   └── videos/
│       └── observation.images.camera_name/
├── task_002/
└── ...
```

**关键要求**:
- 数据集必须包含 `observation.state` 和 `action` 字段
- 图像字段命名如 `observation.images.camera_name`
- 每个task是一个独立的lerobot数据集

---

## 2. 第一步: 创建Unitree G1 Embodiment配置

### 2.1 分析你的数据集结构

首先需要了解Unitree G1数据的字段名和维度：

```bash
# 查看一个episode的数据结构
python << 'EOF'
import pandas as pd
import os

# 替换为你的实际路径
dataset_path = "/path/to/your/unitree_g1_dataset/task_001"
parquet_file = os.path.join(dataset_path, "data/chunk-000/episode_000000.parquet")

if os.path.exists(parquet_file):
    df = pd.read_parquet(parquet_file)
    print("=== Columns ===")
    print(df.columns.tolist())
    print("\n=== First row sample ===")
    for col in df.columns[:5]:  # 显示前5列
        print(f"{col}: {df[col].iloc[0]}")
else:
    print(f"File not found: {parquet_file}")
EOF
```

### 2.2 创建配置文件

创建文件: `/home/ttt/Desktop/TAO/src/tao/embodiments/unitree_g1.py`

```python
from dataclasses import dataclass, field
from typing import Dict, List, Union, Any  
from tao.registry import EMBODIMENTS

# define format
ObservationsMapping = Dict[str, Union[str, List[str], Dict[str, str]]]  
SubComponentIndices = Dict[str, Dict[str, int]]  
ModalityIndexConfig = Dict[str, Union[SubComponentIndices, List[int]]]  
ModalityIndices = Dict[str, ModalityIndexConfig]  
SubComponentTransform = Dict[str, str]  
TransformationsConfig = Dict[str, Dict[str, SubComponentTransform]]  

@dataclass(frozen=True) 
@EMBODIMENTS.register("unitree_g1")
class UnitreeG1Config:
    """Configuration class for Unitree G1 robot"""
    
    # Mapping different observation keys to standard/common keys
    observations: ObservationsMapping = field(
        default_factory=lambda: {
            'video': {
                'base_image': 'observation.images.base_camera',  # 根据你的实际字段名修改
                # 如果有腕部相机，添加以下行
                # 'left_wrist_image': 'observation.images.left_wrist',
                # 'right_wrist_image': 'observation.images.right_wrist',
            },
            'state': ['observation.state'],  # Concatenated into single state vector
            'action': ['action'],            # Concatenated into single action vector
            'task_progress': 'none',         # none表示原始数据没有task progress，会自动推断
            'instruction': 'task_index'      # 或使用 'language_instruction'
        }
    )

    # Index mapping for state/action (extraction & delta indices)
    indices: ModalityIndices = field(
        default_factory=lambda: {
            # State vector indices (extraction mapping)
            'state': {
                'sub_components': {
                    # 根据你的Unitree G1实际维度修改
                    # 示例: 假设state是14维 (7关节 + 7关节)
                    "left_arm": {"start": 0, "end": 7},
                    "right_arm": {"start": 7, "end": 14},
                    # 如果有末端执行器(eef)，添加:
                    # "left_eef": {"start": 14, "end": 15},
                    # "right_eef": {"start": 15, "end": 16}
                },
                'delta_indices': [0]
            },
            # Action vector indices (extraction mapping)
            'action': {
                'sub_components': {
                    # 与state对应
                    "left_arm": {"start": 0, "end": 7},
                    "right_arm": {"start": 7, "end": 14},
                    # "left_eef": {"start": 14, "end": 15},
                    # "right_eef": {"start": 15, "end": 16}
                },
                'delta_indices': list(range(50)),  # action horizon=50
                'relative_mask': [7, 7]  # 根据子组件数量调整
            },
            'video': {
                'delta_indices': [0]
            },
            'task_progress': {
                'delta_indices': list(range(50))
            },
            'instruction': {
                'delta_indices': [0]
            }
        }
    )

    # Normalization/transformation rules for state/action sub-components
    transformations: TransformationsConfig = field(
        default_factory=lambda: {
            'state': {
                'sub_components': {
                    "left_arm": 'min_max',
                    "right_arm": 'min_max',
                    # "left_eef": 'min_max',
                    # "right_eef": 'min_max'
                }
            },
            'action': {
                'sub_components': {
                    "left_arm": 'min_max',
                    "right_arm": 'min_max',
                    # "left_eef": 'min_max',
                    # "right_eef": 'min_max'
                }
            }
        }
    )
```

**⚠️ 重要**: 你需要根据实际的Unitree G1数据修改以下内容：
1. 图像字段名 (`observation.images.xxx`)
2. State和action的维度 (通过上面的Python脚本查看)
3. 子组件划分 (left_arm, right_arm等)
4. `relative_mask` 的长度要与子组件数量一致

### 2.3 注册配置到模块

编辑 `/home/ttt/Desktop/TAO/src/tao/embodiments/__init__.py`，添加对 UnitreeG1Config 的导入：

```python
# 在现有导入后面添加
from .unitree_g1 import UnitreeG1Config

# 并在__all__列表中添加
__all__ = [
    # ... 现有项 ...
    "UnitreeG1Config"
]
```

**⚠️ 重要:** 必须更新 `__init__.py`，否则训练时 `EMBODIMENTS.get("unitree_g1")` 会报 "Key not found" 错误，因为 `@EMBODIMENTS.register("unitree_g1")` 装饰器只有在模块被导入时才会执行。

### 2.4 验证配置

```bash
cd /home/ttt/Desktop/TAO
python -c "from tao.embodiments.unitree_g1 import UnitreeG1Config; print('✅ Unitree G1 config loaded successfully')"
```

---

## 3. 第二步: 计算归一化统计信息

在训练之前，需要计算state和action的归一化统计信息(min/max或mean/std)。

### 3.1 修改统计脚本

编辑 `/home/ttt/Desktop/TAO/scripts/script_compute_norm_stats.sh`:

```bash
#!/bin/bash
set -euo pipefail

# ===================== 自定义配置区 =====================
EMBODIMENT_TAG_LIST=("unitree_g1")

# 定义Unitree G1数据集路径数组
unitree_g1=(
    "/path/to/your/unitree_g1_dataset/task_001"
    "/path/to/your/unitree_g1_dataset/task_002"
    "/path/to/your/unitree_g1_dataset/task_003"
    # 添加更多任务...
)

DATASET_PATHS=()
EMBODIMENT_TAGS=()

# 遍历所有EMBODIMENT_TAG
for tag in "${EMBODIMENT_TAG_LIST[@]}"; do
    eval "paths=(\${$tag[@]})"
    for path in "${paths[@]}"; do
        DATASET_PATHS+=("$path")
        EMBODIMENT_TAGS+=("$tag")
    done
done

# 验证结果
echo "===== DATASET_PATHS ====="
for idx in "${!DATASET_PATHS[@]}"; do
    echo "索引 $idx: ${DATASET_PATHS[$idx]}"
done

echo -e "\n===== EMBODIMENT_TAGS ====="
for idx in "${!EMBODIMENT_TAGS[@]}"; do
    echo "索引 $idx: ${EMBODIMENT_TAGS[$idx]}"
done

echo -e "\n===== 长度验证 ====="
echo "DATASET_PATHS 长度: ${#DATASET_PATHS[@]}"
echo "EMBODIMENT_TAGS 长度: ${#EMBODIMENT_TAGS[@]}"
if [ ${#DATASET_PATHS[@]} -eq ${#EMBODIMENT_TAGS[@]} ]; then
    echo -e "\033[0;32m✅ 两个数组长度一致\033[0m"
else
    echo -e "\033[0;31m❌ 两个数组长度不一致\033[0m"
fi

# 核心配置
CONDA_ENV_NAME="lingtao"
PYTHON_SCRIPT="compute_norm_stats.py"
OVERWRITE_EXISTING_RELATIVE="true"
OVERWRITE_EXISTING_ABSOLUTE="false"

# 激活conda环境
eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

# 构建执行命令
CMD="python \"$PYTHON_SCRIPT\""
CMD="$CMD --dataset-paths ${DATASET_PATHS[@]} --embodiment-tags ${EMBODIMENT_TAGS[@]}"

if [ "$OVERWRITE_EXISTING_RELATIVE" = "true" ]; then
    CMD="$CMD --overwrite-existing-relative"
fi
if [ "$OVERWRITE_EXISTING_ABSOLUTE" = "true" ]; then
    CMD="$CMD --overwrite-existing-absolute"
fi

echo "最终执行命令: $CMD"

# 执行命令
if eval "$CMD"; then
    echo -e "\033[0;32m===== 统计信息计算完成 =====\033[0m"
else
    echo -e "\033[0;31m===== 统计信息计算失败！=====\033[0m"
    exit 1
fi

conda deactivate
exit 0
```

### 3.2 运行统计脚本

```bash
cd /home/ttt/Desktop/TAO/scripts
chmod +x script_compute_norm_stats.sh
bash script_compute_norm_stats.sh
```

**预期输出**:
- 会在每个数据集目录下生成 `statistics.json` 文件
- 包含state和action的min/max或mean/std统计信息

---

## 4. 第三步: 修改训练脚本

### 4.1 使用推荐的v0d5配置

编辑 `/home/ttt/Desktop/TAO/scripts/script_slurm_v0d5.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=tao-unitree-g1
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:8
#SBATCH --output=slurm_logs/job_%j.out
#SBATCH --error=slurm_logs/job_%j.err

OUTPUT_DIR="/data/users/tiantaotao/checkpoints"

export MASTER_PORT=$(expr 20000 + $(echo -n $SLURM_JOBID | tail -c 4))
export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
echo "MASTER_ADDR: $MASTER_ADDR, MASTER_PORT: $MASTER_PORT"

eval "$(conda shell.bash hook)"
conda activate lingtao

export GPU_PER_NODE=$(echo "$CUDA_VISIBLE_DEVICES" | awk -F',' '{print NF}')

MODEL_CONFIG=TaoFlowMatchingModelConfig
DATA_CONFIG=DataConfigShardedMixtureDataset
BACKBONE_CONFIG=BackboneConfigEagleVL3
ACTION_HEAD_CONFIG=ActionHeadConfigAltDiT

# Unitree G1 embodiment tag
EMBODIMENT_TAG_LIST=("unitree_g1")

# 定义Unitree G1数据集路径数组
unitree_g1=(
    "/path/to/your/unitree_g1_dataset/task_001"
    "/path/to/your/unitree_g1_dataset/task_002"
    "/path/to/your/unitree_g1_dataset/task_003"
    # 添加更多任务...
)

DATASET_PATHS=()
EMBODIMENT_TAGS=()

# 遍历所有EMBODIMENT_TAG
for tag in "${EMBODIMENT_TAG_LIST[@]}"; do
    eval "paths=(\${$tag[@]})"
    for path in "${paths[@]}"; do
        DATASET_PATHS+=("$path")
        EMBODIMENT_TAGS+=("$tag")
    done
done

# 验证结果
echo "===== DATASET_PATHS ====="
for idx in "${!DATASET_PATHS[@]}"; do
    echo "索引 $idx: ${DATASET_PATHS[$idx]}"
done

echo -e "\n===== EMBODIMENT_TAGS ====="
for idx in "${!EMBODIMENT_TAGS[@]}"; do
    echo "索引 $idx: ${EMBODIMENT_TAGS[$idx]}"
done

echo -e "\n===== 长度验证 ====="
echo "DATASET_PATHS 长度: ${#DATASET_PATHS[@]}"
echo "EMBODIMENT_TAGS 长度: ${#EMBODIMENT_TAGS[@]}"
if [ ${#DATASET_PATHS[@]} -eq ${#EMBODIMENT_TAGS[@]} ]; then
    echo -e "\033[0;32m✅ 两个数组长度一致\033[0m"
else
    echo -e "\033[0;31m❌ 两个数组长度不一致\033[0m"
fi

DATASET_PATHS="[$(IFS=,; echo "${DATASET_PATHS[*]}")]"
EMBODIMENT_TAGS="[$(IFS=,; echo "${EMBODIMENT_TAGS[*]}")]"

# 训练参数
MAX_STEPS=10000
SAVE_STEPS=5000          # 每5000步保存一次
BATCH_SIZE=32            # 根据GPU显存调整
LEARNING_RATE=0.0001
USE_SWANLAB=false

MAX_ACTION_HORIZON=50
TUNE_TOP_LLM_LAYERS=4    # 微调顶层4层LLM
COLOR_JITTER_PARAMS='{"brightness":0.1,"contrast":0.1,"saturation":0.1,"hue":0.1}'

NUM_SHARDS_PER_EPOCH=100000
SHARD_SIZE=1024
EPISODE_SAMPLING_RATE=0.1
ADAM_BETA1=0.9
ADAM_BETA2=0.999

# 实验名称
EXP_DESC="tao_v0d5_unitree_g1"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
EXPERIMENT_NAME="${EXP_DESC}_${TIMESTAMP}_n${GPU_PER_NODE}_b${BATCH_SIZE}_s${MAX_STEPS}"
EXP_DIR="$OUTPUT_DIR/$EXPERIMENT_NAME"

# 预训练模型路径（使用v0d5）
BASE_DIR="/data/shared_checkpoints/tao/v0d5"

CMD="torchrun \
    --nnodes $SLURM_NNODES \
    --nproc_per_node $GPU_PER_NODE \
    --node_rank $SLURM_NODEID \
    --rdzv_id=$SLURM_JOB_ID \
    --rdzv-backend=c10d \
    --rdzv-endpoint=$MASTER_ADDR:$MASTER_PORT \
    train.py \
    --model $MODEL_CONFIG \
    --model.backbone_config $BACKBONE_CONFIG \
    --model.action_head_config $ACTION_HEAD_CONFIG \
    --model.backbone_config.tune_top_llm_layers $TUNE_TOP_LLM_LAYERS \
    --model.color_jitter_params $COLOR_JITTER_PARAMS \
    --model.action_head_config.max_action_horizon $MAX_ACTION_HORIZON \
    --data $DATA_CONFIG \
    --data.dataset_paths $DATASET_PATHS \
    --data.embodiment_tags $EMBODIMENT_TAGS \
    --training.max_steps $MAX_STEPS \
    --training.save_steps $SAVE_STEPS \
    --training.batch_size $BATCH_SIZE \
    --training.learning_rate $LEARNING_RATE \
    --training.adam_beta1 $ADAM_BETA1 \
    --training.adam_beta2 $ADAM_BETA2 \
    --training.output_dir $EXP_DIR \
    --training.base_dir $BASE_DIR \
    --training.num_gpus $GPU_PER_NODE \
    --training.use_swanlab $USE_SWANLAB \
    --data.num_shards_per_epoch $NUM_SHARDS_PER_EPOCH \
    --data.shard_size $SHARD_SIZE \
    --data.episode_sampling_rate $EPISODE_SAMPLING_RATE"

echo "Output dir: $EXP_DIR"

# 运行
srun --kill-on-bad-exit=1 $CMD
```

### 4.2 关键参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `MAX_STEPS` | 10000 | 总训练步数 |
| `SAVE_STEPS` | 5000 | 保存checkpoint的间隔 |
| `BATCH_SIZE` | 32 | 每个GPU的batch size |
| `LEARNING_RATE` | 0.0001 | 学习率 |
| `TUNE_TOP_LLM_LAYERS` | 4 | 微调顶层LLM层数（0=不微调） |
| `MAX_ACTION_HORIZON` | 50 | 动作预测时间步 |
| `EPISODE_SAMPLING_RATE` | 0.1 | 数据采样率（1.0=全部数据） |

---

## 5. 第四步: 提交训练任务

### 5.1 创建日志目录

```bash
mkdir -p /home/ttt/Desktop/TAO/slurm_logs
```

### 5.2 提交任务

```bash
cd /home/ttt/Desktop/TAO/scripts
sbatch script_slurm_v0d5.sh
```

**预期输出**:
```
Submitted batch job XXXXX
```

### 5.3 查看任务状态

```bash
# 查看所有任务
squeue -u tiantaotao

# 查看特定任务
squeue -j XXXXX
```

---

## 6. 第五步: 监控训练进度

### 6.1 实时查看日志

```bash
# 查看最新任务的日志
tail -f /home/ttt/Desktop/TAO/slurm_logs/job_XXXXX.out

# 或者使用less查看
less /home/ttt/Desktop/TAO/slurm_logs/job_XXXXX.out
```

### 6.2 关键日志指标

训练过程中会输出以下信息：

```
{'loss': 0.0064, 'grad_norm': 0.0237, 'learning_rate': 4.6e-09, 'epoch': 1.0}
{'loss': 0.0028, 'grad_norm': 0.0427, 'learning_rate': 2.7e-12, 'epoch': 1.0}
```

**监控要点**:
- **loss**: 应该逐渐下降并收敛
- **grad_norm**: 梯度范数，应该在合理范围内（<1.0）
- **learning_rate**: 学习率会逐渐衰减
- **epoch**: 当前训练轮次

### 6.3 检查checkpoint

```bash
# 查看输出目录
ls -lah /data/users/tiantaotao/checkpoints/tao_v0d5_unitree_g1_*/

# 查看checkpoint
ls -lah /data/users/tiantaotao/checkpoints/tao_v0d5_unitree_g1_*/checkpoint-*/
```

每个checkpoint包含：
- `model-*.safetensors`: 模型权重
- `config.json`: 模型配置
- `training_args.bin`: 训练参数
- `experiment_cfg/`: 实验配置
- `processor/`: 处理器配置

---

## 7. 第六步: 获取训练结果

### 7.1 训练完成后

训练完成后，你会在输出目录看到：

```
/data/users/tiantaotao/checkpoints/
└── tao_v0d5_unitree_g1_20260520_145000_n8_b32_s10000/
    ├── checkpoint-5000/
    │   ├── model-00001-of-00003.safetensors
    │   ├── model-00002-of-00003.safetensors
    │   ├── model-00003-of-00003.safetensors
    │   ├── config.json
    │   ├── training_args.bin
    │   └── ...
    ├── checkpoint-10000/  # 最终checkpoint
    │   ├── model-*.safetensors
    │   ├── config.json
    │   └── ...
    ├── config.json
    ├── experiment_cfg/
    └── processor/
```

### 7.2 使用训练好的模型

```python
from transformers import AutoModel

# 加载训练好的模型
model_path = "/data/users/tiantaotao/checkpoints/tao_v0d5_unitree_g1_20260520_145000_n8_b32_s10000/checkpoint-10000"
model = AutoModel.from_pretrained(model_path, trust_remote_code=True)

# 推理示例
# ... (根据你的具体应用场景)
```

### 7.3 备份模型

```bash
# 复制到你自己的目录
cp -r /data/users/tiantaotao/checkpoints/tao_v0d5_unitree_g1_* ~/my_models/

# 或者压缩保存
tar -czf unitree_g1_model.tar.gz /data/users/tiantaotao/checkpoints/tao_v0d5_unitree_g1_*/checkpoint-10000/
```

---

## 8. 常见问题

### Q1: Eagle模型找不到怎么办？

**A**: Eagle VL模型会在首次运行时自动从HuggingFace下载。如果网络不好，可以提前下载：

```bash
# 手动下载Eagle模型
python << 'EOF'
from transformers import AutoModel
model = AutoModel.from_pretrained("NVEagle/eagle_er-qwen3_1_7B-Siglip2_400M_stage1_5_128gpu_er_v7_1mlp_nops", trust_remote_code=True)
EOF
```

### Q2: 显存不足怎么办？

**A**: 减小batch size或启用梯度累积：

```bash
# 修改script_slurm_v0d5.sh
BATCH_SIZE=16  # 从32降到16

# 或者在train.py中添加梯度累积参数
--gradient_accumulation_steps 2
```

### Q3: Loss不下降怎么办？

**A**: 检查以下几点：
1. 数据集是否正确（字段名、维度匹配）
2. 归一化统计信息是否正确计算
3. 学习率是否合适（尝试调整为0.00005）
4. 增加训练步数

### Q4: 如何继续训练（从checkpoint恢复）？

**A**: 修改训练脚本，添加resume参数：

```bash
CMD="torchrun ... train.py \
    ... \
    --training.resume_from_checkpoint /data/users/tiantaotao/checkpoints/xxx/checkpoint-5000 \
    ..."
```

### Q5: 如何评估训练好的模型？

**A**: 使用TAO的评估工具：

```bash
cd /home/ttt/Desktop/TAO/tools
python evaluate_offline.py \
    --model_path /data/users/tiantaotao/checkpoints/xxx/checkpoint-10000 \
    --dataset_path /path/to/test/dataset \
    --embodiment_tag unitree_g1
```

---

## 📞 获取帮助

如果遇到问题：

1. 查看slurm错误日志: `cat slurm_logs/job_XXXXX.err`
2. 检查完整的训练日志: `less slurm_logs/job_XXXXX.out`
3. 联系集群管理员或参考TAO官方文档

---

**祝你训练顺利！🎉**
