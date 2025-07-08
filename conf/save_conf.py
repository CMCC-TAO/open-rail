from ml_collections import ConfigDict
def get_record_data_config():
    """Generate config for recording data, compatible with save_config.json structure.

    Returns:
        ConfigDict: Configuration for recording data.
    """
    config = ConfigDict(allow_dotted_keys=True)

    # 基础路径和版本信息
    config.enable = True ## True to record data, False to not record data
    config.save_path = "./output/test" ## 保存路径 如果保存路径为空，则不保存数据
    config.info = ConfigDict(allow_dotted_keys=True)
    config.info.codebase_version = "v2.0" ## lerobot数据集版本
    config.info.robot_type = "a2d" ## 输入机器人类型

    # 数据统计信息（初始为0）
    config.info.total_episodes = 0
    config.info.total_frames = 0
    config.info.total_tasks = 0
    config.info.total_videos = 0
    config.info.total_chunks = 1
    config.info.chunks_size = 1000
    config.info.fps = 30

    # 数据划分
    config.info.splits = {'valid': '0:100'}

    # 路径模板
    config.info.data_path = "data/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.parquet"
    config.info.video_path = "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4"

    # Features 定义
    config.info.features = ConfigDict(allow_dotted_keys=True)


    config.info.features['cam.head'] = generate_image_feature_config()()
    config.info.features['cam.hand_left'] = generate_image_feature_config(width=848,height=480)()
    config.info.features['cam.hand_right'] = generate_image_feature_config(width=848,height=480)()

    # 非视频特征
    config.info.features['observation.state'] = ConfigDict({
        "dtype": "float32",
        "shape": [20]
    })
    config.info.features['action'] = ConfigDict({
        "dtype": "float32",
        "shape": [22]
    })
    config.info.features['episode_index'] = ConfigDict({
        "dtype": "int64",
        "shape": [1],
        "names": None
    })
    config.info.features['frame_index'] = ConfigDict({
        "dtype": "int64",
        "shape": [1],
        "names": None
    })
    config.info.features['index'] = ConfigDict({
        "dtype": "int64",
        "shape": [1],
        "names": None
    })
    config.info.features['task_index'] = ConfigDict({
        "dtype": "int64",
        "shape": [1],
        "names": None
    })
    config.info.features['timestamp'] = ConfigDict({
        "dtype": "float32",
        "shape": [1],
        "names": None
    })

    return config

def generate_image_feature_config(width=1280,height=720,fps=30.0):
    # 视频相关参数统一定义
    video_info_common = {
        "video.fps": fps,
        "video.codec": "av1",
        "video.pix_fmt": "yuv420p",
        "video.is_depth_map": False,
        "has_audio": False
    }

    info_common = {
        "video.fps": fps,
        "video.height": height,
        "video.width": width,
        "video.channels": 3,
        "video.codec": "mpeg4",
        "video.pix_fmt": "yuv420p",
        "video.is_depth_map": False,
        "has_audio": False
    }

    image_feature = lambda: ConfigDict({
        "dtype": "video",
        "shape": [height, width, 3],
        "names": ["height", "width", "channel"],
        "video_info": ConfigDict(video_info_common,allow_dotted_keys=True),
        "info": ConfigDict(info_common,allow_dotted_keys=True)
    })
    return image_feature
