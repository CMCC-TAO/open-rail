import sys
import time
import numpy as np
import cv2
import pyarrow.parquet as pq
import json
import os
import logging
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QSlider, QPushButton, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QGridLayout  # 确保导入

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Qt5Agg')

    
class LoadLerobotDataset:
    """Class for loading and processing the LeRobot dataset.

    Attributes:
        root_path (str): Root path of the dataset.
        info_config (dict): Configuration info loaded from tasks.jsonl and info.json.
        video_paths (list): List to store video paths.
    """

    def __init__(self, root_path: str, logger: logging.Logger = None):
        """Initialize the LoadLerobotDataset with the root path."""
        self.root_path = root_path
        self.info_config = self.load_lerobot_dataset_info(root_path)
        self.logger = logger or logging.getLogger(__name__)
        self.chunk_size = self.info_config["chunks_size"]
        self.total_episodes = self.info_config["total_episodes"]
        self.data_format = self.info_config["data_path"]
        self.video_format = self.info_config["video_path"]
    def get_data_path_from_index(self, index: int):
        if index>= self.total_episodes:
            self.logger.error(
                f"Index out of range. Please input a valid index from 0 to {self.total_episodes - 1}"
            )           
            return None,None
        episode_chunk = index // self.chunk_size
        parquet_path  = self.generate_parquet_file_path(episode_chunk,index)
        # parquet_content=pd.read_parquet(parquet_file_path)
        # videos_content = []
        video_paths = []
        for key in self.info_config["video_key"]:
            video_path = self.generate_video_file_path(episode_chunk,key,index)
            # cap = cv2.VideoCapture(video_path)
            video_paths.append(video_path)
        return parquet_path,video_paths
    def load_lerobot_dataset_info(self, root_path: str) -> dict:
        """Load dataset info from tasks.jsonl and info.json files.

        Args:
            root_path: Root path of the dataset.

        Returns:
            dict: Dataset configuration info with video keys.

        Raises:
            FileNotFoundError: If info.json does not exist.
        """
        task_file_path = os.path.join(root_path, "meta", "tasks.jsonl")
        info_file_path = os.path.join(root_path, "meta", "info.json")

        if not os.path.exists(info_file_path):
            raise FileNotFoundError(f"info.json file {info_file_path} does not exist")

        with open(info_file_path, "r") as file:
            info_config = json.load(file)

        video_keys = []
        print(info_config.keys())
        for feature_key in info_config["features"].keys():
            # print(feature)
            feature = info_config["features"][feature_key]
            if not isinstance(feature, dict):
                continue
            if feature["dtype"] == "video":
                # print(feature)
                video_keys.append(feature_key)

        info_config["video_key"] = video_keys
        return info_config

    def generate_parquet_file_path(
        self, episode_chunk: int, episode_index: int
    ) -> str:
        """Generate path for the parquet file.

        Args:
            episode_chunk: Index of the chunk.
            episode_index: Index of the episode.

        Returns:
            str: Path to the parquet file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        parquet_file_path = os.path.join(
            self.root_path, self.data_format.format(episode_chunk=episode_chunk,
                                                    episode_index=episode_index)
        )

        if not os.path.exists(parquet_file_path):
            raise FileNotFoundError(f"Parquet file {parquet_file_path} does not exist")

        return parquet_file_path

    def generate_video_file_path(
        self,
        episode_chunk: int,
        video_key: str,
        episode_index: int,
    ) -> str:
        """Generate path for the video file.

        Args:
            root_path: Root path of the dataset.
            video_path_format: Format string for the video file path.
            episode_chunk: Index of the chunk.
            video_key: Key of the video stream.
            episode_index: Index of the episode.

        Returns:
            str: Path to the video file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        video_file_path = os.path.join(
            self.root_path, self.video_format.format(episode_chunk=episode_chunk,
                                                     video_key=video_key,
                                                    episode_index=episode_index)
        )

        if not os.path.exists(video_file_path):
            raise FileNotFoundError(f"Video file {video_file_path} does not exist")

        return video_file_path

class DatasetVisualizer(QWidget):
    def __init__(self, video_paths, parquet_path, task_language_dict,show_text=False,show_task_progress=False):
        super().__init__()
        self.video_paths = video_paths
        self.parquet_path = parquet_path
        self.task_language_dict = task_language_dict
        self.show_text = show_text
        # 初始化视频捕获
        self.video_caps = [cv2.VideoCapture(path) for path in video_paths]
        self.frame_count = int(min([cap.get(cv2.CAP_PROP_FRAME_COUNT) for cap in self.video_caps]))
        self.current_frame = 0

        self.parquet_data = pq.read_table(parquet_path).to_pandas()

        self.state_dim = min(30, self.parquet_data.iloc[0]['observation.state'].shape[0])
        self.action_dim = min(30, self.parquet_data.iloc[0]['action'].shape[0])
        self.state_dim = min(self.state_dim, self.action_dim)
        self.show_task_progress = show_task_progress
        self.chart_configs = [
            {'name': 'Left Arm', 'range': (0, 6)},
            {'name': 'Right Arm', 'range': (7, 13)},
            {'name': 'Actuator', 'range': (14, 15)},
            {'name': 'Remaining', 'range': (16, None)}
        ]
        if self.show_task_progress:
            self.chart_configs = [
                {'name': 'Left Arm', 'range': (0, 6)},
                {'name': 'Right Arm', 'range': (7, 13)},
                {'name': 'Actuator', 'range': (14, 15)},
                {'name': 'task_progress', 'range': (16,16)}
            ]

        self.vlines = []
        self.line_figs = []
        self.line_axes = []

        self.init_ui()
        self.init_plots()
        self.update_frame(0)

    def init_ui(self):
        layout = QVBoxLayout()

        # 第一部分：视频 + frame + task_content
        self.video_label = QLabel("Video Display")
        self.video_label.setAlignment(Qt.AlignCenter)

        self.info_label = QLabel("Frame: 0 | Task: None")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        layout.addWidget(self.info_label)
        layout.addWidget(self.video_label)

        # 第二部分：折线图区域（4 个独立 Figure）
        charts_layout = QGridLayout()



        self.charts = []
        self.canvases = []
        self.axes = []
        self.backgrounds = []
        self.vlines = []

        for i in range(4):
            fig = Figure(figsize=(4, 4))
            ax = fig.add_subplot(111)
            canvas = FigureCanvas(fig)
            self.backgrounds.append(None)  # 占位
            self.charts.append(fig)
            self.canvases.append(canvas)
            self.axes.append(ax)

            # 按照 2x2 排列
            row = i // 2
            col = i % 2
            charts_layout.addWidget(canvas, row, col)  # 添加到对应位置

        layout.addLayout(charts_layout)

        # 控制区域
        control_layout = QHBoxLayout()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, self.frame_count - 1)
        self.slider.valueChanged.connect(self.update_frame)
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_play)
        control_layout.addWidget(self.slider)
        control_layout.addWidget(self.play_button)
        layout.addLayout(control_layout)

        self.setLayout(layout)

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.play_next_frame)
        self.playing = False

    def generate_text_content(self, states, action):
        task_content = ""
        for i , state in enumerate(states):
            # task_content = f"State {i}: {state:.3f} \nAction {i}: {action[i]:.3f} \n"
            task_content += f"State {i}: {state:.3f} \nAction {i}: {action[i]:.3f} \n"

        return task_content

    def init_plots(self):
        self.states_all = self.parquet_data['observation.state'].values
        self.actions_all = self.parquet_data['action'].values

        self.vlines = []

        self.text_axes = []
        for i, config in enumerate(self.chart_configs):
            start_dim, end_dim = config['range']
            name = config['name']
            

            if end_dim is None:
                if start_dim < self.state_dim:
                    dims = range(start_dim, self.state_dim)
                else:
                    dims = range(0)
            else:
                dims = range(start_dim, min(end_dim + 1, self.state_dim))

            if not len(dims):
                continue

            ax = self.axes[i]
            ax.set_title(f'{name} ')
            ax.set_xlabel('Frame')
            # ax.set_ylabel('Value')
            ax.grid(True)



            for idx, dim in enumerate(dims):
                states = [row[dim] for row in self.states_all]
                states = np.array(states)
                if name == 'Actuator':
                    states = (states - 35)/(120 -35)
                actions = [row[dim] for row in self.actions_all]
                if self.show_task_progress and dim == 16:
                    ax.plot(actions, label=f'Action {dim}', linestyle='--', linewidth=1.5)
                else:
                    ax.plot(states, label=f'State {dim}', linestyle='-', linewidth=1.5)
                    ax.plot(actions, label=f'Action {dim}', linestyle='--', linewidth=1.5)


            ax.legend(loc='upper right', bbox_to_anchor=(1.10, 1), ncol=1,fontsize=8)

            # 保存背景
            self.canvases[i].draw()
            self.backgrounds[i] = self.canvases[i].copy_from_bbox(ax.bbox)

            # 添加垂直线
            vline = ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Current Frame')
            self.vlines.append(vline)
            # 添加值
            # text_content = self.generate_text_content(states, actions)
            if self.show_text:
                text_ax = ax.text(0.0, 0.95, '',transform=ax.transAxes, fontsize=8, verticalalignment='top')
                self.text_axes.append(text_ax)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_backgrounds()

    def _update_backgrounds(self):
        # self.init_plots()
        for i in range(len(self.chart_configs)):
            ax = self.axes[i]
            vline = self.vlines[i]
            vline.remove()
            if self.show_text:
                text_ax = self.text_axes[i]
                text_ax.remove()
            canvas = self.canvases[i]
            canvas.draw()
            self.backgrounds[i] = canvas.copy_from_bbox(ax.bbox)
            vline = ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Current Frame')
            self.vlines[i] = vline
            if self.show_text:
                text_ax = ax.text(0.0, 0.95, '',transform=ax.transAxes, fontsize=8, verticalalignment='top')
                self.text_axes[i] = text_ax
    def update_frame(self, value):
        start_time= time.perf_counter()
        self.current_frame = value
        frame_data = self.parquet_data.iloc[self.current_frame]
        task_index = frame_data['task_index']
        print(f"task_index： {task_index}")
        task_content = self.task_language_dict[task_index]
        self.info_label.setText(f"Frame: {self.current_frame} | Task: {task_content}")
        label_time = time.perf_counter()
        print(f"lable took {time.perf_counter() - start_time:.3f}s")
        self.show_video_frame()
        video_time = time.perf_counter()
        print(f"video took {time.perf_counter() - label_time:.3f}s")
        
        self.update_lines(frame_data)
        print(f"update_lines took {time.perf_counter() - video_time:.3f}s")
        print(f"one Frame {self.current_frame} took {time.perf_counter() - start_time:.3f}s")

    def show_video_frame(self):
        if not hasattr(self, 'video_pixmap'):
            self.video_pixmap = None

        frames = []
        for cap in self.video_caps:
            cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame, (640, 480))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # ✅ 转换为 RGB
                frames.append(frame)

        if frames:
            combined = np.hstack(frames)
            height, width, channel = combined.shape
            bytes_per_line = 3 * width
            qimg = QImage(combined.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()

            if self.video_pixmap is None:
                self.video_pixmap = QPixmap.fromImage(qimg)
                self.video_label.setPixmap(self.video_pixmap)
            else:
                self.video_pixmap.convertFromImage(qimg)
                self.video_label.setPixmap(self.video_pixmap)

    def update_lines(self,frame_data):
        for i, config in enumerate(self.chart_configs):
            ax = self.axes[i]
            vline = self.vlines[i]
            canvas = self.canvases[i]
            background = self.backgrounds[i]
            canvas.restore_region(background)
            
            vline.set_xdata([self.current_frame, self.current_frame])
            ax.draw_artist(vline)

            if self.show_text:
                text_ax = self.text_axes[i]
                start_dim, end_dim = config['range']
                name = config['name']

                # 计算维度范围
                if end_dim is None:
                    if start_dim < self.state_dim:
                        dims = range(start_dim, self.state_dim)
                    else:
                        dims = range(0)  # 空范围
                else:
                    dims = range(start_dim, min(end_dim + 1, self.state_dim))
                
                # 获取state和action数据
                states = frame_data['observation.state'][dims]
                if name == 'Actuator':
                    states = np.array(states)
                    states = (states - 35)/(120 -35)
                actions = frame_data['action'][dims]
                text_content = self.generate_text_content(states, actions)
                # print(f"text_content: {text_content}")
                if self.show_task_progress and name == "task_progress":
                    text_content = f"task_progress : {actions[0]:.3f}\n"
                text_ax.set_text(text_content)
                ax.draw_artist(text_ax)

            
            canvas.blit(ax.bbox)
    

    def toggle_play(self):
        self.playing = not self.playing
        self.play_button.setText("Pause" if self.playing else "Play")
        if self.playing:
            self.timer.start(33)  # 30fps
        else:
            self.timer.stop()
        
    def play_next_frame(self):
        if self.current_frame < self.frame_count - 1:
            self.current_frame += 1
            self.slider.setValue(self.current_frame)
        else:
            self.toggle_play()
        if hasattr(self, '_last_auto_play_time'):
            elapsed = time.perf_counter() - self._last_auto_play_time
            print(f"[AutoPlay] Frame {self.current_frame} interval: {elapsed:.3f}s")
        self._last_auto_play_time = time.perf_counter()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dataset Visualizer")

        # 加载数据
        args = self.parse_args()
        lerobot_data = LoadLerobotDataset(args.data_path)
        parquet_path, video_paths = lerobot_data.get_data_path_from_index(args.episode_id)

        task_file_path = os.path.join(args.data_path, 'meta', 'tasks.jsonl')
        task_language_dict = {}
        with open(task_file_path, 'r') as file:
            for line in file:
                data = json.loads(line)
                task_language_dict[data['task_index']] = data['task']

        self.visualizer = DatasetVisualizer(video_paths, parquet_path, task_language_dict, args.using_text,show_task_progress=True)
        self.setCentralWidget(self.visualizer)  # ✅ 确保设置为中心部件

    def parse_args(self):
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("-p","--data-path", type=str, default="/home/rm/wxz/EmbodiedAI/dataset/task_all/task_776_first_10_episodes")
        parser.add_argument("-id","--episode-id", type=int, default=2)
        parser.add_argument("-text","--using_text", type=int, default=True)
        parser.add_argument("-mode","--using_model", type=int, default=1)
        return parser.parse_args()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()  # ✅ 最大化显示
    # window.show()
    sys.exit(app.exec_())