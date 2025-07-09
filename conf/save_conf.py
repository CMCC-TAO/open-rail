from ml_collections import ConfigDict
def get_record_data_config()-> ConfigDict:
    """Generate config for recording data, compatible with save_config.json structure.

    Returns:
        ConfigDict: Configuration for recording data.
    """
    config = ConfigDict(allow_dotted_keys=True)

    # Base path and version info
    config.enable = True ## True to record data, False to not record data
    config.save_path = "./data/output/test" # Save root directory.
    config.info = ConfigDict(allow_dotted_keys=True)
    config.info.codebase_version = "v2.0" #  # Version of the dataset (e.g., lerobot)
    config.info.robot_type = "a2d"  # Type of robot used

    # Data statistics (initialized to 0)）
    config.info.total_episodes = 0
    config.info.total_frames = 0
    config.info.total_tasks = 0
    config.info.total_videos = 0
    config.info.total_chunks = 1
    config.info.chunks_size = 1000
    config.info.fps = 30

    # Dataset splits
    config.info.splits = {'valid': '0:100'}

    # Path templates
    config.info.data_path = "data/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.parquet"
    config.info.video_path = "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4"

    # Image feature definitions
    config.info.features = ConfigDict(allow_dotted_keys=True)

    # Image features from cameras
    config.info.features['cam.head'] = generate_image_feature_config()
    config.info.features['cam.hand_left'] = generate_image_feature_config(width=848,height=480)
    config.info.features['cam.hand_right'] = generate_image_feature_config(width=848,height=480)

    # Other features
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

def generate_image_feature_config(width: int = 1280, height: int = 720, fps: float = 30.0) -> ConfigDict:
    """
    Generates a ConfigDict object representing image/video feature specifications.

    Args:
        width (int): Width of the video frame. Default is 1280.
        height (int): Height of the video frame. Default is 720.
        fps (float): Frames per second of the video. Default is 30.0.

    Returns:
        ConfigDict: A configuration dictionary containing:
            - dtype: Data type (e.g., 'video')
            - shape: Shape of the frame [height, width, channels]
            - names: Dimension names ['height', 'width', 'channel']
            - video_info: ConfigDict containing video encoding parameters
            - info: ConfigDict with additional metadata such as resolution and codec
    """
    # Common video metadata definitions
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

    # 直接构造并返回 ConfigDict 对象
    return ConfigDict({
        "dtype": "video",
        "shape": [height, width, 3],
        "names": ["height", "width", "channel"],
        "video_info": ConfigDict(video_info_common, allow_dotted_keys=True),
        "info": ConfigDict(info_common, allow_dotted_keys=True)
    })
