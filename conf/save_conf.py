from ml_collections import ConfigDict
def get_record_data_config() -> ConfigDict:
    """Generate configuration for data recording system.
    
    This function creates a comprehensive configuration dictionary for recording
    robot demonstration data, compatible with LeRobot dataset format. It includes
    settings for data paths, video encoding, feature definitions, and metadata.

    Returns:
        ConfigDict: Configuration dictionary for data recording containing:
            - switch: Enable/disable data recording
            - save_dir: Relative directory under project root for saved data
            - info: Metadata including dataset version, robot type, statistics
            - features: Data feature definitions for cameras, actions, states
    """
    config = ConfigDict(allow_dotted_keys=True)

    # Record Common
    config.switch = False  # Enable/disable data recording
    config.save_dir = "data/recording"  # Relative to project root
    
    # Evaluation
    config.eval_log_format = "json"  # Evaluation log save format: json | csv | both
    config.eval_scores = [0, 0.5, 1]  # Score options for evaluation log scoring buttons

    # Episode
    config.is_record_episode = False  # Runtime flag: whether episode recording is active
    config.is_record_eval_log = False  # Runtime flag: whether eval log recording is active
    config.save_raw = True  # Save raw image without resizing or not.

    # Episode info (metadata)
    config.info = ConfigDict(allow_dotted_keys=True)
    config.info.codebase_version = "v2.0"  # Dataset version (e.g., lerobot)
    config.info.robot_type = "a2d"  # Type of robot used

    # Data statistics (initialized to 0)
    config.info.total_episodes = 0
    config.info.total_frames = 0
    config.info.total_tasks = 0
    config.info.total_videos = 0
    config.info.total_chunks = 1
    config.info.chunks_size = 1000
    config.info.fps = 30
    config.info.state_shape = 20
    config.info.action_shape = 22

    # Dataset splits
    config.info.splits = {'valid': '0:100'}

    # Path templates
    config.info.data_path = "data/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.parquet"
    config.info.video_path = "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4"

    # Image feature definitions
    # config.info.features = ConfigDict(allow_dotted_keys=True)

    # Image config dict from cameras
    config.info['cam.head'] = generate_image_feature_config()
    config.info['cam.hand_left'] = generate_image_feature_config(width=848,height=480)
    config.info['cam.hand_right'] = generate_image_feature_config(width=848,height=480)

    # Other features
    # config.info.features['observation.state'] = ConfigDict({
    #     "dtype": "float32",
    #     "shape": [20]
    # })
    # config.info.features['action'] = ConfigDict({
    #     "dtype": "float32",
    #     "shape": [22]
    # })
    # config.info.features['episode_index'] = ConfigDict({
    #     "dtype": "int64",
    #     "shape": [1],
    #     "names": None
    # })
    # config.info.features['frame_index'] = ConfigDict({
    #     "dtype": "int64",
    #     "shape": [1],
    #     "names": None
    # })
    # config.info.features['index'] = ConfigDict({
    #     "dtype": "int64",
    #     "shape": [1],
    #     "names": None
    # })
    # config.info.features['task_index'] = ConfigDict({
    #     "dtype": "int64",
    #     "shape": [1],
    #     "names": None
    # })
    # config.info.features['timestamp'] = ConfigDict({
    #     "dtype": "float32",
    #     "shape": [1],
    #     "names": None
    # })

    # print(f"Generated record data config: {config}")

    return config

def generate_image_feature_config(width: int = 1280, height: int = 720, fps: int = 30) -> ConfigDict:
    """
    Generates a ConfigDict object representing image/video feature specifications.

    Args:
        width (int): Width of the video frame. Default is 1280.
        height (int): Height of the video frame. Default is 720.
        fps (int): Frames per second of the video. Default is 30.

    Returns:
        ConfigDict: A configuration dictionary containing:
            - dtype: Data type (e.g., 'video')
            - shape: Shape of the frame [height, width, channels]
            - names: Dimension names ['height', 'width', 'channel']
            - video_info: ConfigDict containing video encoding parameters
            - info: ConfigDict with additional metadata such as resolution and codec
    """
    # Common video metadata definitions
    encode = {
        # "video.fps": fps,
        "codec": "mp4v", # ('mp4v', 'avc1', 'XVID', 'MJPG')
        "is_depth_map": False, # Depth image for True and False for RGB image
        "has_audio": False
    }

    shape = {
        # "video.fps": fps,
        "height": height,
        "width": width,
        "channel": 3,
    }

    # Construct and return ConfigDict object
    return ConfigDict({
        # "dtype": "video",
        "shape": ConfigDict(shape, allow_dotted_keys=False),
        # "names": ["height", "width", "channel"],
        "encode": ConfigDict(encode, allow_dotted_keys=False),
        # "info": ConfigDict(info_common, allow_dotted_keys=True)
    })
