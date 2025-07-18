# 数据集可视视化工具

本工具用于check保存的lerobot数据集，并且能可视化预测动作数据与真实数据之间的差异

## 功能特点

- 支持lerobot格式的dataset，但无需依赖lerobot，且评估速度更快
- 可视化展示每个关节维度的预测值与真实值对比，以及当前帧的language
- 分区域显示不同的维度，可视化更舒适

## 前提条件

- 环境：python3.8+，conda环境
```bash
pip install opencv-python pandas pyarrow numpy matplotlib
```
- 数据结构：
```bash
.
├── data
│   └── chunk-000
│       ├── episode_000000.parquet
│       └── .........
├── meta
│   ├── episodes.jsonl
│   ├── info.json
│   └── tasks.jsonl
└── videos
    └── chunk-000
        ├── cam.hand_left
        │   ├── episode_000000.mp4
        │   └── .........
        ├── cam.hand_right
        │   ├── episode_000000.mp4
        │   └── .........
        └── cam.head
            ├── episode_000000.mp4
            └── .........
```
## 使用方法

```bash
python3 show_data.py \
--data-path /home/rm/wxz/EmbodiedAI/vla_infer_2/vla_infer/data/output/test \
--episode-id 2 \
--chunk-id 0
```

参数说明
```bash
python show_data.py -h
```

## 注意事项

暂无

## 输出示例

```
成功打开 /home/rm/wxz/EmbodiedAI/vla_infer_2/vla_infer/data/output/test/videos/chunk-000/cam.hand_left/episode_000002.mp4, 帧数: 1127
成功打开 /home/rm/wxz/EmbodiedAI/vla_infer_2/vla_infer/data/output/test/videos/chunk-000/cam.head/episode_000002.mp4, 帧数: 1127
成功打开 /home/rm/wxz/EmbodiedAI/vla_infer_2/vla_infer/data/output/test/videos/chunk-000/cam.hand_right/episode_000002.mp4, 帧数: 1127
min frame_count : 1127
20
task_index： 1
更新 0，耗时：149.24235800572205 ms
```

![example_1](./example_1.png)
![example_2](./example_2.png)
![example_3](./example_3.png)
```
Contributors: Xuanzhang Wen
```
