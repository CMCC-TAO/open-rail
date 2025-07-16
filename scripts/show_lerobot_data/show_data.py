import os
import cv2
import pandas as pd
import pyarrow.parquet as pq
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # 必须放在导入 pyplot 之前
import matplotlib.pyplot as plt
from matplotlib import pyplot as plt
from matplotlib.widgets import Slider, Button
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import json
import string
import math
import argparse
class DatasetVisualizer:
    """
    A class to visualize dataset including video frames and corresponding state/action data.
    
    Attributes:
        video_paths (list): List of paths to video files.
        parquet_path (str): Path to the Parquet file containing state and action data.
        task_language_dict (dict): Dictionary mapping task indices to their descriptions.
        ...
    """
    def __init__(self, video_paths, parquet_path,task_language_dict):
        """
        Initializes the DatasetVisualizer with video paths, Parquet data, and task descriptions.

        Args:
            video_paths (list): List of paths to video files.
            parquet_path (str): Path to the Parquet file containing state and action data.
            task_language_dict (dict): Dictionary mapping task indices to their descriptions.
        """
        self.task_language_dict = task_language_dict
        print(task_language_dict)
        self.video_paths = video_paths
        self.parquet_path = parquet_path
        self.video_caps = [cv2.VideoCapture(path) for path in video_paths]
        for path in video_paths:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                print(f"无法打开视频文件: {path}")
            else:
                print(f"成功打开 {path}, 帧数: {int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}")
                cap.release()
        self.video_names = [path.split('/')[-2].split('.')[-1] for path in video_paths]
        self.parquet_data = pq.read_table(parquet_path).to_pandas()
        
        # 获取视频帧数和帧率
        self.frame_count = int(min([cap.get(cv2.CAP_PROP_FRAME_COUNT) for cap in self.video_caps]))
        print('min frame_count :',self.frame_count)
        self.fps = int(self.video_caps[0].get(cv2.CAP_PROP_FPS))
        print(self.parquet_data.iloc[0]['observation.state'].shape[0])
        # 设置要显示的维度（最大20）
        self.state_dim = min(22, self.parquet_data.iloc[0]['observation.state'].shape[0])
        self.action_dim = min(22, self.parquet_data.iloc[0]['action'].shape[0])
        self.state_dim = min (self.state_dim,self.action_dim)
        # 修改图形界面布局 - 创建2x2图表布局
        self.fig = plt.figure(figsize=(15, 12))
        self.gs = self.fig.add_gridspec(3, 2)  # 3行2列的网格布局

        # 视频显示在顶部
        self.ax_video = self.fig.add_subplot(self.gs[0, :])  # 跨越所有列

        # 四个图表分别放在下面两行
        self.ax_chart1 = self.fig.add_subplot(self.gs[1, 0])  # 左上
        self.ax_chart2 = self.fig.add_subplot(self.gs[1, 1])  # 右上
        self.ax_chart3 = self.fig.add_subplot(self.gs[2, 0])  # 左下
        self.ax_chart4 = self.fig.add_subplot(self.gs[2, 1])  # 右下
        self.state_bars_list = []
        self.action_bars_list = []
        self.state_texts_list=[]
        self.action_texts_list=[]
        # # 添加滑动条和按钮的位置需要相应调整
        # plt.subplots_adjust(bottom=0.2, hspace=0.4, wspace=0.3)
        
        # 添加滑动条
        ax_slider = plt.axes([0.2, 0.05, 0.6, 0.03])
        self.slider = Slider(ax_slider, 'Frame', 0, self.frame_count-1, valinit=0, valstep=1)
        self.slider.on_changed(self.update)

        self.chart_configs = [
            {'name': 'Left Arm', 'range': (0, 6)},
            {'name': 'Right Arm', 'range': (7, 13)},
            {'name': 'Actuator', 'range': (14, 15)},
            {'name': 'Remaining', 'range': (16, None)}
        ]
        # 添加播放/暂停按钮
        ax_button = plt.axes([0.85, 0.05, 0.1, 0.04])
        self.button = Button(ax_button, 'Play')
        self.button.on_clicked(self.toggle_play)

        # 控制播放状态
        self.playing = False
        self.play_thread = None

        # 初始化显示
        self.current_frame = 0
        self.executor = ThreadPoolExecutor(max_workers=len(self.video_caps))  # 线程池
        self.future_to_cap_index = {}
        self.lock = threading.Lock()  # 用于同步访问 frames 和 UI 更新
        
        self.update(0)
        self.initialize_static_line_plots()
    def load_frame_async(self, cap_index, frame_idx):
        """
        Asynchronously loads a single video frame from the specified video capture.

        Args:
            cap_index (int): Index of the video capture object.
            frame_idx (int): Frame index to be loaded.

        Returns:
            tuple: A tuple containing the capture index, the loaded frame, and a boolean indicating success.
        """
        cap = self.video_caps[cap_index]
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, (640, 480))
        return cap_index, frame, ret
    def update(self, val):
        """
        Updates the visualization based on the current frame selected by the slider.

        Args:
            val (float): Current value of the slider indicating the frame number.
        """
        self.current_frame = int(val)
        frame_data = self.parquet_data.iloc[self.current_frame]
        task_index = frame_data['task_index']
        print(f"task_index： {task_index}")
        task_content = self.task_language_dict[task_index]
        # 清空视频子图（必须）
        self.ax_video.clear()

        # 拼接并显示所有视频画面（第一行）
        frames = []
        start_time = time.perf_counter()
        # 异步加载帧
        futures = []
        for i in range(len(self.video_caps)):
            future = self.executor.submit(self.load_frame_async, i, self.current_frame)
            self.future_to_cap_index[future] = i
            futures.append(future)

        # 等待所有帧加载完成
        frames = [None] * len(self.video_caps)
        for future in futures:
            cap_index, frame, ret = future.result()
            if ret:
                frames[cap_index] = frame
        for i, name in enumerate(self.video_names):
            if frames[i] is not None:
                self.ax_video.text(
                    i * (1 / len(frames)) + (0.5 / len(frames)),
                    0.95,
                    name,
                    transform=self.ax_video.transAxes,
                    fontsize=12,
                    color='red',
                    ha='center',
                    va='center'
                )
        if frames:
            combined_frame = np.hstack(frames)
            self.ax_video.imshow(combined_frame)
            self.ax_video.axis('off')
            self.ax_video.set_title(f'Videos - Frame {self.current_frame} language: {task_content}')
        video_time = time.perf_counter()
        # print(f"更新视频帧 {self.current_frame}，耗时：{(video_time - load_video_time)*1000} ms")
        # === State 数据更新 ===
        for i, config in enumerate(self.chart_configs):
            start_dim, end_dim = config['range']
            name = config['name']
            ax = getattr(self, f'ax_chart{i+1}')

            # 计算维度范围
            if end_dim is None:
                if start_dim < self.state_dim:
                    dims = range(start_dim, self.state_dim)
                else:
                    dims = range(0)  # 空范围
            else:
                dims = range(start_dim, min(end_dim + 1, self.state_dim))
            
            # 获取state和action数据
            state = frame_data['observation.state'][dims]
            if name == 'Actuator':
                state = (state - 35)/(120 -35)
            action = frame_data['action'][dims]
        # state = frame_data['observation.state'][:self.state_dim]
            x_pos = np.array(dims)

            if i>=len(self.state_bars_list):
                  # 第一次创建柱状图和标签
                bar_width = 0.4
                x_pos_state = x_pos - bar_width / 2
                x_pos_action = x_pos + bar_width / 2

                state_bars = ax.bar(x_pos_state, state, width=bar_width, color='skyblue', label='State')
                action_bars = ax.bar(x_pos_action, action, width=bar_width, color='orange', alpha=0.8, label='Action')

                ax.set_xticks(x_pos)
                ax.set_xticklabels([f'{i}' for i in dims])
                ax.set_ylabel(name + ' Value')
                ax.set_title(f'{name} State & Action')
                ax.grid(axis='y')
                
                # 创建数值标签
                state_texts = [
                    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                            f'{value:.3f}', ha='center', va='bottom', fontsize=8)
                    for bar, value in zip(state_bars, state)
                ]
                action_texts = [
                    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                            f'{value:.3f}', ha='center', va='bottom', fontsize=8)
                    for bar, value in zip(action_bars, action)
                ]

                self.state_bars_list.append(state_bars)
                self.action_bars_list.append(action_bars)
                self.state_texts_list.append(state_texts)
                self.action_texts_list.append(action_texts)
            else:
                
                state_bars = self.state_bars_list[i]
                action_bars = self.action_bars_list[i]
                state_texts = self.state_texts_list[i]
                action_texts = self.action_texts_list[i]
                # 后续仅更新高度和文本
                for bar, value, text in zip(state_bars, state, state_texts):
                    bar.set_height(value)
                    text.set_y(value + 0.01)
                    text.set_text(f'{value:.3f}')
                for bar, value, text in zip(action_bars, action, action_texts):
                    bar.set_height(value)
                    text.set_y(value + 0.01)
                    text.set_text(f'{value:.3f}')
                # 更新 state 图表 Y 轴范围
                ax.set_ylim(min(np.min(state),np.min(action)) - 0.1, max(np.max(state),np.max(action))+ 0.1)
        # print(f"更新state {self.current_frame}，耗时：{(time.perf_counter() - video_time)*1000} ms")
        print(f"更新 {self.current_frame}，耗时：{(time.perf_counter() - start_time)*1000} ms")
        self.fig.canvas.draw_idle()
    
    def show(self):
        """Displays the visualization window."""
        plt.show()
        
    def __del__(self):
        """Releases all video capture resources when the visualizer is destroyed."""
        for cap in self.video_caps:
            cap.release()

    def toggle_play(self, event):
        """
        Toggles play/pause state of the automatic playback.

        Args:
            event (matplotlib.backend_bases.Event): Event triggering this method.
        """
        self.playing = not self.playing
        self.button.label.set_text('Pause' if self.playing else 'Play')
        if self.playing:
            self.fig.canvas.manager.window.after(10, self.auto_play)  # 启动播放循环

    def auto_play(self):
        """Automatically advances the slider to play frames continuously."""
        start = time.time()
        fps = 30  # 播放速度
        interval_ms = int(1000 / fps)

        if self.playing and self.current_frame < self.frame_count - 1:
            self.current_frame += 1
            self.slider.set_val(self.current_frame)
        
        if self.playing:
            self.fig.canvas.manager.window.after(interval_ms, self.auto_play)

        print(f"Frame {self.current_frame} took {time.time() - start:.3f}s")

    def a2d_end_actuator_nomarlize(self, datas):
        """
        Normalizes actuator values for visualization purposes.

        Args:
            datas (list): List of raw actuator data values.

        Returns:
            list: Normalized values between 0 and 1.
        """
        states = []
        for data in datas:
            data_new = (data-35)/(120-35)
            states.append(data_new)
        return states
    def initialize_static_line_plots(self):
        """Initializes static line plots showing complete trajectories of state and action data."""
        for i, config in enumerate(self.chart_configs):
            start_dim, end_dim = config['range']
            name = config['name']
            # 确定实际的维度范围
            if end_dim is None:
                if start_dim < self.state_dim:
                    dims = range(start_dim, self.state_dim)
                else:
                    dims = range(0)
            else:
                dims = range(start_dim, min(end_dim + 1, self.state_dim))
            plot_num = len(dims)
            if plot_num ==0:
                plt.show()
                continue
            # rows = math.ceil(plot_num / 2)
            line_fig, line_axes = plt.subplots(plot_num, 1, figsize=(40,plot_num*2 ))

            # 设置窗口标题（避免显示为 Figure）
            line_fig.canvas.manager.set_window_title(f'Trajectory Plot - {name}')

            # 最大化窗口（适用于TkAgg、GTKAgg等后端）
            # 获取窗口并最大化（兼容 TkAgg）
            if hasattr(line_fig.canvas.manager, 'window'):
                try:
                    # 使用 Tkinter 的方式最大化窗口
                    line_fig.canvas.manager.window.attributes('-zoomed', True)
                except Exception as e:
                    print(f"无法最大化窗口 (TkAgg): {e}")
            # 将 axes 转换为一维数组以便遍历
            line_axes = line_axes.flatten()

            # 遍历每个维度并绘制折线图
            for idx, dim in enumerate(dims):
                ax = line_axes[idx]
                # 获取当前维度下所有帧的 state 和 action 值
                states = [row[dim] for row in self.parquet_data['observation.state']]
                if name == 'Actuator':
                    states = self.a2d_end_actuator_nomarlize(states)
                actions = [row[dim] for row in self.parquet_data['action']]
                # print(f'states shape {state}')
                # print(f'actions shape {actions.shape}')
                # 绘制 state 和 action 的折线图
                ax.plot(range(self.frame_count), states, label='State', color='skyblue')
                ax.plot(range(self.frame_count), actions, label='Action', color='orange', alpha=0.8)

                # 设置标题和标签
                ax.set_title(f'{name} - Dimension {dim}')
                ax.set_xlabel('Frame')
                ax.set_ylabel('Value')
                ax.legend()
                ax.grid(True)

            # 自动调整布局
            plt.tight_layout()
            if i==len(self.chart_configs)-1:
                plt.show()
            # plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="可视化数据集，支持指定路径和 episode ID")
    parser.add_argument("--data-path", type=str, default="/home/rm/wxz/EmbodiedAI/vla_infer_2/vla_infer/data/output/test",
                        help="数据根目录路径")
    parser.add_argument("--episode-id", type=int, default=2,
                        help="要显示的 episode ID")
    parser.add_argument("--chunk-id", type=int, default=0,
                        help="要显示的 chunk ID")

    args = parser.parse_args()

    data_path = args.data_path
    episode_id = args.episode_id
    chunk_id = args.chunk_id

    video_files = [ 
        os.path.join(data_path, 'videos', f'chunk-{chunk_id:03d}', "cam.hand_left", f'episode_{episode_id:06d}.mp4'),
        os.path.join(data_path, 'videos', f'chunk-{chunk_id:03d}', "cam.head", f'episode_{episode_id:06d}.mp4'),
        os.path.join(data_path, 'videos', f'chunk-{chunk_id:03d}', "cam.hand_right", f'episode_{episode_id:06d}.mp4')
    ]
    parquet_file = os.path.join(data_path, 'data', f'chunk-{chunk_id:03d}', f'episode_{episode_id:06d}.parquet')
    task_file_path = os.path.join(data_path, 'meta','tasks.jsonl')
    task_language_dict = {}

    # 检查文件是否存在
    for file in video_files + [parquet_file]+ [task_file_path]:
        if not os.path.exists(file):
            raise FileNotFoundError(f"文件 {file} 不存在")
    with open(task_file_path, 'r') as file:
        for line in file:
            data = json.loads(line)
            task_index = data['task_index']
            task_name = data['tasks']  
            if task_name not in task_language_dict:
                task_language_dict[task_index] = task_name
    visualizer = DatasetVisualizer(video_files, parquet_file,task_language_dict)
    visualizer.show()