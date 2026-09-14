# 基于RAIL，在AgiBotWorld 2026数据集上运行GR00T‑N1.5预训练模型

> 完整部署流程：源码下载、数据集准备、AV1视频转H.264、多处配置修改、服务端/客户端启动。
> 文档中 `Path/To/xxx` 均需要替换为本机真实**绝对路径**。

## 0. 下载RAIL源码至本地
RAIL源码本地路径：`Path/To/RAIL`

## 1. 下载AgiBotWorld 2026数据子集
下载压缩包：
https://huggingface.co/datasets/agibot-world/AgiBotWorld2026/blob/main/ImitationLearning/Home/task_4713/509995_510027.tar.gz

保存到本地路径：`Path/To/Dataset`

## 2. 数据集预处理：AV1编码MP4批量转H.264
解压 `509995_510027.tar.gz`。
原始视频为AV1编码，OpenCV/Git‑LFS无法正常读取，需要转码为H.264编码格式。

进入目录：`Path/To/Dataset/509995_510027/data/videos/chunk‑000`，新建脚本 `transcode_video.sh`：

```bash
#!/bin/bash
# Path/To/Dataset/509995_510027/data/videos/chunk-000路径下的相机目录列表
cam_dirs=(
"observation.images.hand_left"
"observation.images.hand_right"
"observation.images.head_back_fisheye"
"observation.images.head_left_fisheye"
"observation.images.head_right_fisheye"
"observation.images.top_head"
"observation.images.head_depth"
)
for cam in "${cam_dirs[@]}"; do
    if [ ! -d "$cam" ]; then
	echo "Skip $cam : directory not exist"
	continue
    fi
    echo "==== Process camera dir: $cam ===="
    # 递归找所有episode_*.mp4
    find "$cam" -type f -name "episode_*.mp4" | while read -r mp4file; do
	tmpfile="${mp4file}.tmp_transcode.mp4"
	echo "Transcode: $mp4file"
	ffmpeg -i "$mp4file" -c:v libx264 -crf 15 "$tmpfile" -y -hide_banner -loglevel error
	if [ $? -eq 0 ]; then
	    mv "$tmpfile" "$mp4file"
	    echo "OK replaced: $mp4file"
	else
	    echo "FAILED transcode $mp4file , keep original"
	    rm -f "$tmpfile"
	fi
    done
done
echo "All done"
```

执行转码脚本：
```bash
chmod +x transcode_video.sh
./transcode_video.sh
```

## 3.下载 GR00T N1.5 源码
分支：`n1.5‑release`

仓库地址：[https://github.com/NVIDIA/Isaac-GR00T/tree/n1.5-release](https://github.com/NVIDIA/Isaac-GR00T/tree/n1.5-release)

本地存放路径：`Path/To/Project/Isaac‑GR00T‑N1.5`

## 4. 下载 GR00T‑N1.5‑3B 预训练权重

权重仓库：[https://huggingface.co/nvidia/GR00T](https://huggingface.co/nvidia/GR00T)‑N1.5‑3B
本地存放路径：`Path/To/CheckPoint/GR00T‑N1.5‑3B`



## 5. 修改 RAIL 机器人配置
文件路径：`Path/To/RAIL/conf/robots_conf.py` (第704~706行)，修改 `get_mock_config()` 函数：

```
def get_mock_config():
    """Generate configuration for mock robot (simulation/testing).
    
    Returns:
        ConfigDict: Configuration dictionary containing camera mappings, data root path, and repository ID for mock robot.
    """
    config = ConfigDict()
    config.camera = ConfigDict()
    # config.hand_type = 'gripper' # 'gripper' or 'hand_as_gripper' or 'hand'
    config.camera.ref = 'head'
    config.camera.names = {'head': 'observation.images.head_rgb',
                'hand_left': 'observation.images.left_wrist_rgb',
                'hand_right': 'observation.images.right_wrist_rgb'}
    config.action_layout = _ordered_config({
        'arm': {
            'start': 0, 'end': 14, 'policy': 'gradual',
            'presets': {
                'left': {'Default': [0.0] * 7, 'Custom': [0.0] * 7},
                'right': {'Default': [0.0] * 7, 'Custom': [0.0] * 7},
            },
        },
        'gripper': {
            'start': 14, 'end': 16, 'policy': 'stepwise',
            'presets': {
                'left': {'Default': [0.0], 'Custom': [0.0]},
                'right': {'Default': [0.0], 'Custom': [0.0]},
            },
        },
        'head': {
            'start': 16, 'end': 18, 'policy': 'gradual',
            'presets': {
                    'left': {'Default': [0.0]*2, 'Custom': [0.0]*2},
                    'right': {'Default': [0.0]*2, 'Custom': [0.0]*2},
            },
        },
        'waist': {
            'start': 18, 'end': 20, 'policy': 'gradual',
            'presets': {
                    'left': {'Default': [0.0]*2, 'Custom': [0.0]*2},
                    'right': {'Default': [0.0]*2, 'Custom': [0.0]*2},
            },
        },
        'velocity': {
            'start': 20, 'end': 22, 'policy': 'gradual',
            'presets': {
                    'left': {'Default': [0.0]*2, 'Custom': [0.0]*2},
                    'right': {'Default': [0.0]*2, 'Custom': [0.0]*2},
            },
        },
    })
    config.manual_arm_interval = 0.01
    config.state_action_range = [[0, 16], [58, 70]]
    config.dataset_path = '/home/robot/Music/task_39_only1'
    # config.dataset_path = '/home/robot/Music'
    return config
```

## 6. 修改 RAIL 模型配置

文件路径：`Path/To/RAIL/conf/models_conf.py` (第36~37行)，修改 `get_gr00t_config()`，设置机器人标签与数据处理 key：

```
def get_gr00t_config():
    """Generate configuration for GR00T model.
    
    Returns:
        ConfigDict: Configuration dictionary containing model path for GR00T.
    """
    config = ConfigDict()
    config.model_path = '/path/to/model'
    config.embodiment_tag = 'agibot_genie1'
    config.data_config_key = 'agibot_genie1'
    return config
```

## 7. 修改 GR00T 源码数据配置

文件路径：`Path/To/Project/Isaac‑GR00T‑N1.5/gr00t/experiment/data_config.py`（704‑706 行），
修改 `AgibotGenie1DataConfig` 类的 `video_keys`：

```
class AgibotGenie1DataConfig(BaseDataConfig):
    video_keys = [
        "video.cam_top_head", "video.cam_left_wrist", "video.cam_right_wrist"
    ]
    ......
```

## 8. 修改权重内 metadata 配置

文件路径：`Path/To/CheckPoint/GR00T‑N1.5‑3B/experiment_cfg/metadata.json` （第1933~1959行），
找到 `agibot_genie1` → `modalities` → `video`，修改相机相关索引和参数：

```
"agibot_genie1": {
    ......,
    "modalities": {
        "video": {
            "cam_top_head": {
                "resolution": [
                    640,
                    640
                ],
                "channels": 3,
                "fps": 30.0
            },
            "cam_left_wrist": {
                "resolution": [
                    640,
                    640
                ],
                "channels": 3,
                "fps": 30.0
            },
            "cam_right_wrist": {
                "resolution": [
                    640,
                    640
                ],
                "channels": 3,
                "fps": 30.0
            }
        }
    }
}
```

## 9. 启动 RAIL 服务端

在一个终端内（默认已激活虚拟环境）启动RAIL服务端：

```
PYTHONPATH=Path/To/Project/Isaac-GR00T-N1.5:$PYTHONPATH python run_server.py --model_type gr00t_n1_5 --model_path Path/To/CheckPoint/GR00T‑N1.5‑3B
```

## 10. 启动 RAIL 客户端

新建一个终端（默认已激活虚拟环境）启动RAIL客户端：

```
python run_web_client.py
```

## 11. Web 页面配置数据集路径

浏览器访问：`http://localhost:9000`
点击 `Browse`，将左侧 `robots‑mock‑dataset_path` 修改为数据集实际路径：
`Path/To/Dataset/509995_510027/data`

![选择mock模式的数据集路径](../data/media/select_dataset_path.png)

## 12. 启动推理

点击页面顶层栏 `Start` 按钮，即可基于 AgiBotWorld2026 子集执行推理。

![mock模式demo](../data/media/mock_demo.png)

### 关键注意事项

1. 所有 `Path/To/xxx` 需要替换为你机器真实绝对路径；
2. 视频必须完成 AV1→H.264 转码，否则 OpenCV 读取报错；
3. `PYTHONPATH` 务必加入 GR00T‑N1.5 源码目录，否则 trust_remote_code 加载类失败；
4. metadata.json 是预训练权重内部文件，修改前建议备份原始文件。