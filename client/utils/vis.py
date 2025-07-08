# 本可视化程序既是独立程序（作为绘图server），也是一个模块（作为绘图client）
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import threading
import random
import time
import zmq
import json
import argparse
from matplotlib.ticker import MaxNLocator
from matplotlib import cm
from typing import List, Tuple, Optional, Union, Dict, Any

# plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'SimHei']  # 设置默认字体为黑体
# plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示异常

class PlotConfig:
    server_address: str = "tcp://*:58585"  # ZMQ绑定地址
    client_address: str = "tcp://localhost:58585"  # ZMQ绑定地址
    
    # 图表基本配置
    max_points: int = 1000  # 图表显示的最大数据点数
    auto_scroll: bool = True  # 自动滚动显示
    scroll_window: int = 300  # 滚动窗口大小（显示的数据点数）
    title: str = "RT Data"  # 图表标题
    y_label: str = "y"  # Y轴标签
    x_label: str = "x"  # X轴标签
    num_subplots: int = 2  # 子图数量
    num_cols: int = 2 # 列数
    subplot_titles: Optional[List[str]] = None  # 子图标题列表，如果不提供则使用默认标题
    
    # 线条和标记配置
    show_markers: bool = True  # 是否显示数据点标记
    marker_style: str = 'o'  # 数据点标记样式
    marker_size: int = 1  # 数据点标记大小
    line_styles: Optional[List[str]] = None  # 线条样式列表，可选值包括 "-"(实线), "--"(虚线), "-."(点划线), ":"(点线) 等
    line_width: float = 1.0  # 线条宽度
    line_labels: Optional[List[str]] = None  # 线条标签列表，如果不提供则使用默认标签
    show_lines: bool = False  # 是否显示线条，设为False则只显示标记点
    line_alpha: float = 1.0  # 线条透明度
    
    # 颜色和样式配置
    color_theme: str = 'rainbow'  # 颜色主题 (可选: default, viridis, plasma, inferno, magma, cividis, rainbow)
    grid_style: str = 'solid'  # 网格线样式 (可选: solid, dashed, dotted, dashdot)
    grid_alpha: float = 0.3  # 网格线透明度 (0-1之间的浮点数)
    background_color: Optional[str] = None  # 图表背景颜色 (例如: "#f0f0f0", "lightgray")
    legend_loc: str = 'upper right'  # 图例位置 (可选: upper left, upper right, lower left, lower right, center, best)
    custom_colors: Optional[List[str]] = None  # 自定义颜色列表
    
    # 显示和交互配置
    show_stats: bool = True  # 是否显示数据统计信息
    figure_size: Optional[Tuple[float, float]] = None  # 图表尺寸 (宽度, 高度)，单位为英寸
    dpi: int = 100  # 图表DPI
    font_size: int = 10  # 字体大小
    auto_adjust_ylim: bool = True  # 自动调整Y轴范围以适应数据
    auto_ylim_mode: str = 'vis' # vis: 依据可见范围内的最大最小值，all: 依据所有数据的最大最小值
    y_lim: Tuple[float, float] = (-0.6, 1.3)  # Y轴范围，如果auto_adjust_ylim为False，则使用此值
    dark_mode: bool = False  # 启用暗黑模式
    show_toolbar: bool = True  # 显示matplotlib工具栏
    antialiased: bool = True  # 启用抗锯齿
    
    # 性能优化配置
    update_interval: int = 10  # 图表更新间隔（毫秒）
    use_blit: bool = False  # 使用blitting优化性能，ZL：当为True，x/y轴刻度等不会更新（窗口变化时更新）
    downsample_threshold: int = 10000  # 数据点超过此阈值时启用降采样
    downsample_method: str = 'peak'  # 降采样方法 (可选: peak, mean, min_max)
    
    # 数据导出配置
    export_data: bool = False  # 启用数据导出功能
    export_path: str = './data_export'  # 数据导出路径

class RealtimePlot:
    def __init__(self, config: PlotConfig):
        self.cfg = config
        
        # 初始化图表数据存储
        self.data = {}
        self.lines = {}
        self.axes = {}
        self.fig = None
        self.ani = None
        self.visible_subplot = None  # 当前可见的子图索引，None表示显示所有子图
        self.running = False
        self.lock = threading.Lock()  # 用于线程安全的数据访问
        
        # 初始化颜色映射
        self._init_colors()
    
    def _init_colors(self):
        """初始化颜色映射"""
        if self.cfg.custom_colors:
            self.colors = self.cfg.custom_colors
        else:
            # 根据颜色主题创建颜色映射
            if self.cfg.color_theme == 'default':
                self.colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
            else:
                # 使用matplotlib的颜色映射
                cmap = getattr(cm, self.cfg.color_theme, cm.rainbow)
                self.colors = [cmap(i) for i in np.linspace(0, 1, 10)]
    
    def _init_figure(self):
        """初始化matplotlib图表"""
        # 设置图表样式
        if self.cfg.dark_mode:
            plt.style.use('dark_background')
        
        # 创建图表和子图
        fig_size = self.cfg.figure_size or (12, 8)
        self.fig, axes = plt.subplots(
            nrows=(self.cfg.num_subplots + self.cfg.num_cols - 1) // self.cfg.num_cols,
            ncols=self.cfg.num_cols,
            figsize=fig_size,
            dpi=self.cfg.dpi,
            squeeze=False  # 确保axes始终是二维数组
        )
        
        # 设置图表标题和样式
        self.fig.suptitle(self.cfg.title, fontsize=self.cfg.font_size + 4)
        self.fig.tight_layout(rect=[0, 0, 1, 0.96])  # 为标题留出空间
        
        # 设置背景颜色
        if self.cfg.background_color:
            self.fig.patch.set_facecolor(self.cfg.background_color)
        
        # 初始化每个子图
        for i in range(self.cfg.num_subplots):
            row, col = divmod(i, self.cfg.num_cols)
            ax = axes[row, col]
            
            # 设置子图标题
            if self.cfg.subplot_titles and i < len(self.cfg.subplot_titles):
                title = self.cfg.subplot_titles[i]
            else:
                title = f"plot {i+1}"
            ax.set_title(title, fontsize=self.cfg.font_size + 2)
            
            # 设置轴标签
            ax.set_xlabel(self.cfg.x_label, fontsize=self.cfg.font_size)
            ax.set_ylabel(self.cfg.y_label, fontsize=self.cfg.font_size)
            
            # 设置网格
            ax.grid(True, linestyle=self.cfg.grid_style, alpha=self.cfg.grid_alpha)
            
            # 设置Y轴范围
            if not self.cfg.auto_adjust_ylim:
                ax.set_ylim(self.cfg.y_lim)
            
            # 设置整数刻度
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            
            # 存储轴对象
            self.axes[i] = ax
            
            # 初始化该子图的数据存储
            self.data[i] = {}
            self.lines[i] = {}
        
        # 隐藏多余的子图
        total_subplots = axes.shape[0] * axes.shape[1]
        for i in range(self.cfg.num_subplots, total_subplots):
            row, col = divmod(i, self.cfg.num_cols)
            axes[row, col].set_visible(False)
        
        # 添加图例
        for i in range(self.cfg.num_subplots):
            self.axes[i].legend(loc=self.cfg.legend_loc, fontsize=self.cfg.font_size - 2)
        
        # 启用工具栏
        if not self.cfg.show_toolbar:
            plt.rcParams['toolbar'] = 'None'
        
        # 启用抗锯齿
        if self.cfg.antialiased:
            plt.rcParams['lines.antialiased'] = True
        
        return self.fig
    
    def add_line_data(self, y_values: List[float], x_values: Optional[List[float]] = None, subplot_idx: int = 0, line_idx: int = 0, line_props: Optional[Dict[str, Any]] = None):
        """添加线条数据
        
        Args:
            y_values: Y轴数据点列表
            x_values: X轴数据点列表，如果为None则使用递增的索引
            subplot_idx: 子图索引
            line_idx: 线条索引
            line_props: 线条属性字典，可以包含 'show_line', 'color', 'linestyle', 'linewidth', 'marker', 'markersize', 'alpha' 等
        """
        with self.lock:
            # 确保子图索引有效
            if subplot_idx >= self.cfg.num_subplots:
                print(f"警告: 子图索引 {subplot_idx} 超出范围，最大值为 {self.cfg.num_subplots-1}，不绘制此子图")
                # subplot_idx = subplot_idx % self.cfg.num_subplots
                return
            
            # 确保该子图的数据字典已初始化
            if subplot_idx not in self.data:
                self.data[subplot_idx] = {}
            
            # 确保该线条的数据列表已初始化
            if line_idx not in self.data[subplot_idx]:
                self.data[subplot_idx][line_idx] = {'x': [], 'y': [], 'props': {}}
            
            # 如果提供了线条属性，更新它
            if line_props:
                self.data[subplot_idx][line_idx]['props'].update(line_props)
            
            # 添加Y值数据
            if not isinstance(y_values, list):
                y_values = [y_values]
            
            # 处理X值
            if x_values is None:
                # 如果没有提供X值，使用当前数据长度作为X值
                current_len = len(self.data[subplot_idx][line_idx]['x'])
                x_values = [current_len + i for i in range(len(y_values))]
            elif not isinstance(x_values, list):
                x_values = [x_values]
            
            # 确保x和y的长度一致
            min_len = min(len(x_values), len(y_values))
            x_values = x_values[:min_len]
            y_values = y_values[:min_len]
            
            # 添加数据点
            self.data[subplot_idx][line_idx]['x'].extend(x_values)
            self.data[subplot_idx][line_idx]['y'].extend(y_values)
            
            # 限制数据点数量，保持性能
            if len(self.data[subplot_idx][line_idx]['x']) > self.cfg.max_points:
                excess = len(self.data[subplot_idx][line_idx]['x']) - self.cfg.max_points
                self.data[subplot_idx][line_idx]['x'] = self.data[subplot_idx][line_idx]['x'][excess:]
                self.data[subplot_idx][line_idx]['y'] = self.data[subplot_idx][line_idx]['y'][excess:]
    
    def _downsample_data(self, x_data, y_data, target_points=100):
        """对数据进行降采样，减少绘图点数，提高性能
        
        Args:
            x_data: X轴数据
            y_data: Y轴数据
            target_points: 目标点数
            
        Returns:
            降采样后的(x_data, y_data)元组
        """
        if len(x_data) <= target_points:
            return x_data, y_data
        
        # 计算降采样因子
        factor = max(1, len(x_data) // target_points)
        
        if self.cfg.downsample_method == 'mean':
            # 使用平均值降采样
            x_downsampled = []
            y_downsampled = []
            for i in range(0, len(x_data), factor):
                end = min(i + factor, len(x_data))
                if i < end:
                    x_downsampled.append(np.mean(x_data[i:end]))
                    y_downsampled.append(np.mean(y_data[i:end]))
            return x_downsampled, y_downsampled
            
        elif self.cfg.downsample_method == 'min_max':
            # 使用最小值和最大值降采样，保留数据范围
            x_downsampled = []
            y_downsampled = []
            for i in range(0, len(x_data), factor):
                end = min(i + factor, len(x_data))
                if i < end:
                    chunk_x = x_data[i:end]
                    chunk_y = y_data[i:end]
                    
                    # 添加区间的第一个点
                    x_downsampled.append(chunk_x[0])
                    y_downsampled.append(chunk_y[0])
                    
                    if len(chunk_y) > 1:
                        # 找出Y值最小和最大的点
                        min_idx = np.argmin(chunk_y)
                        max_idx = np.argmax(chunk_y)
                        
                        # 确保不重复添加第一个点
                        if min_idx != 0:
                            x_downsampled.append(chunk_x[min_idx])
                            y_downsampled.append(chunk_y[min_idx])
                        
                        if max_idx != 0 and max_idx != min_idx:
                            x_downsampled.append(chunk_x[max_idx])
                            y_downsampled.append(chunk_y[max_idx])
                        
                        # 添加区间的最后一个点
                        if len(chunk_y) > 1 and len(chunk_y) - 1 not in (0, min_idx, max_idx):
                            x_downsampled.append(chunk_x[-1])
                            y_downsampled.append(chunk_y[-1])
            return x_downsampled, y_downsampled
        
        else:  # 默认使用'peak'方法
            # 使用峰值检测降采样，保留数据特征
            x_downsampled = []
            y_downsampled = []
            for i in range(0, len(x_data), factor):
                end = min(i + factor, len(x_data))
                if i < end:
                    chunk_x = x_data[i:end]
                    chunk_y = y_data[i:end]
                    
                    # 始终保留第一个点
                    x_downsampled.append(chunk_x[0])
                    y_downsampled.append(chunk_y[0])
                    
                    # 如果区间内有多个点，检测峰值
                    if len(chunk_y) > 2:
                        # 简单的峰值检测：与相邻点比较
                        for j in range(1, len(chunk_y) - 1):
                            if (chunk_y[j] > chunk_y[j-1] and chunk_y[j] > chunk_y[j+1]) or \
                               (chunk_y[j] < chunk_y[j-1] and chunk_y[j] < chunk_y[j+1]):
                                x_downsampled.append(chunk_x[j])
                                y_downsampled.append(chunk_y[j])
                    
                    # 始终保留最后一个点
                    if len(chunk_y) > 1:
                        x_downsampled.append(chunk_x[-1])
                        y_downsampled.append(chunk_y[-1])
            return x_downsampled, y_downsampled
    
    def _update_plot(self, frame):
        """更新图表，由animation调用"""
        with self.lock:
            # 如果指定了可见子图，只更新该子图
            subplots_to_update = [self.visible_subplot] if self.visible_subplot is not None else self.data.keys()
            
            for subplot_idx in subplots_to_update:
                if subplot_idx not in self.data:
                    continue
                
                ax = self.axes[subplot_idx]
                
                # 找出该子图中所有线条的最大X值，用于确定是否需要滚动
                max_x_values = []
                for line_idx, line_data in self.data[subplot_idx].items():
                    if line_data['x'] and len(line_data['x']) > 0:
                        max_x_values.append(max(line_data['x']))
                
                # 如果有数据，确定X轴范围
                if max_x_values and self.cfg.auto_scroll:
                    max_x = max(max_x_values)
                    # 设置X轴范围，实现滚动效果
                    if self.cfg.scroll_window > 0:
                        new_min = max(0, max_x - self.cfg.scroll_window)
                        ax.set_xlim(new_min, max_x)
                    else:
                        new_min = max(0, max_x - self.cfg.max_points)
                        ax.set_xlim(new_min, max_x)
                    
                # 更新或创建每条线
                for line_idx, line_data in self.data[subplot_idx].items():
                    if not line_data['x'] or len(line_data['x']) == 0:
                        continue
                    
                    # 获取线条数据
                    x_data = line_data['x']
                    y_data = line_data['y']
                    
                    # 获取线条属性
                    line_props = line_data.get('props', {})
                    
                    # 如果数据点过多，进行降采样以提高性能
                    if len(x_data) > self.cfg.downsample_threshold:
                        x_display, y_display = self._downsample_data(x_data, y_data, self.cfg.max_points)
                    else:
                        x_display, y_display = x_data, y_data
                    
                    # 如果线条已存在，更新数据
                    if line_idx in self.lines[subplot_idx]:
                        line = self.lines[subplot_idx][line_idx]
                        line.set_data(x_display, y_display)
                        
                        # 更新线条属性（如果有变化）
                        if 'color' in line_props:
                            line.set_color(line_props['color'])
                        if 'linestyle' in line_props:
                            line.set_linestyle(line_props['linestyle'])
                        if 'linewidth' in line_props:
                            line.set_linewidth(line_props['linewidth'])
                        if 'marker' in line_props:
                            line.set_marker(line_props['marker'])
                        if 'markersize' in line_props:
                            line.set_markersize(line_props['markersize'])
                        if 'alpha' in line_props:
                            line.set_alpha(line_props['alpha'])
                        
                        # 处理是否显示线条
                        show_line = line_props.get('show_line', self.cfg.show_lines)
                        if not show_line and line.get_linestyle() != '':
                            line.set_linestyle('')
                        elif show_line and line.get_linestyle() == '' and 'linestyle' not in line_props:
                            line.set_linestyle('-')  # 默认实线
                    else:
                        # 创建新线条
                        color_idx = line_idx % len(self.colors)
                        color = line_props.get('color', self.colors[color_idx])
                        
                        # 设置线条样式
                        line_style = '-'
                        if 'linestyle' in line_props:
                            line_style = line_props['linestyle']
                        elif self.cfg.line_styles and line_idx < len(self.cfg.line_styles):
                            line_style = self.cfg.line_styles[line_idx]
                        
                        # 处理是否显示线条
                        show_line = line_props.get('show_line', self.cfg.show_lines)
                        if not show_line:
                            line_style = ''
                        
                        # 设置线条标签
                        line_label = f"line {line_idx+1}"
                        if 'label' in line_props:
                            line_label = line_props['label']
                        elif self.cfg.line_labels and line_idx < len(self.cfg.line_labels):
                            line_label = self.cfg.line_labels[line_idx]
                        
                        # 创建线条
                        line, = ax.plot(
                            x_display, y_display,
                            color=color,
                            linestyle=line_style,
                            linewidth=line_props.get('linewidth', self.cfg.line_width),
                            label=line_label,
                            marker=line_props.get('marker', self.cfg.marker_style if self.cfg.show_markers else None),
                            markersize=line_props.get('markersize', self.cfg.marker_size),
                            alpha=line_props.get('alpha', self.cfg.line_alpha)
                        )
                        
                        # 存储线条对象
                        self.lines[subplot_idx][line_idx] = line
                
                # 自动调整Y轴范围
                if self.cfg.auto_adjust_ylim:
                    all_y_values = []
                    for line_data in self.data[subplot_idx].values():
                        if line_data['y']:
                            # 如果是vis模式或数据量很大，只使用可见范围内的数据来调整Y轴
                            if (self.cfg.auto_ylim_mode == 'vis' or len(line_data['y']) > self.cfg.max_points) and len(line_data['x']) > 0:
                                # 获取当前X轴范围
                                x_min, x_max = ax.get_xlim()
                                # 找出在可见范围内的数据点
                                visible_indices = [i for i, x in enumerate(line_data['x']) if x_min <= x <= x_max]
                                if visible_indices:
                                    visible_y = [line_data['y'][i] for i in visible_indices]
                                    all_y_values.extend(visible_y)
                            else:
                                all_y_values.extend(line_data['y'])
                    
                    if all_y_values:
                        min_y = min(all_y_values)
                        max_y = max(all_y_values)
                        # 添加一些边距
                        padding = (max_y - min_y) * 0.1 if max_y > min_y else 0.1
                        ax.set_ylim(min_y - padding, max_y + padding)
                
                # 更新图例
                if self.lines[subplot_idx]:
                    ax.legend(loc=self.cfg.legend_loc, fontsize=self.cfg.font_size - 2)
                    
                # 显示统计信息
                if self.cfg.show_stats:
                    stats_text = ""
                    for line_idx, line_data in self.data[subplot_idx].items():
                        if line_data['y'] and len(line_data['y']) > 0:
                            y_values = line_data['y']
                            line_label = f"line {line_idx+1}"
                            if 'label' in line_data.get('props', {}):
                                line_label = line_data['props']['label']
                            elif self.cfg.line_labels and line_idx < len(self.cfg.line_labels):
                                line_label = self.cfg.line_labels[line_idx]
                            stats_text += f"{line_label}: avg={np.mean(y_values):.2f}, max={max(y_values):.2f}, min={min(y_values):.2f}\n"
                    stats_text = stats_text.strip()
                    # 更新或创建统计信息文本
                    if hasattr(ax, '_stats_text'):
                        ax._stats_text.set_text(stats_text)
                    else:
                        ax._stats_text = ax.text(
                            0.02, 0.98, stats_text,
                            transform=ax.transAxes,
                            verticalalignment='top',
                            fontsize=self.cfg.font_size - 2,
                            bbox=dict(boxstyle='round', facecolor='white', alpha=0.7)
                        )
        
        # 返回所有线条对象，用于animation
        all_lines = []
        for subplot_lines in self.lines.values():
            all_lines.extend(subplot_lines.values())
        return all_lines
    
    def set_visible_subplot(self, subplot_idx: Optional[int] = None):
        """设置可见的子图，如果为None则显示所有子图"""
        with self.lock:
            self.visible_subplot = subplot_idx
            
            # 更新子图可见性
            if self.fig is not None:
                for idx, ax in self.axes.items():
                    if subplot_idx is None or idx == subplot_idx:
                        ax.set_visible(True)
                    else:
                        ax.set_visible(False)
                
                # 重新布局图表
                self.fig.tight_layout(rect=[0, 0, 1, 0.96])
    
    def start(self):
        """启动实时绘图"""
        if self.running:
            return
        
        self.running = True
        
        # 初始化图表
        self._init_figure()
        
        self.ani = animation.FuncAnimation(
            self.fig,
            self._update_plot,
            interval=self.cfg.update_interval,  # 更新间隔（毫秒）
            blit=self.cfg.use_blit,
            cache_frame_data=False  # 不缓存帧数据，减少内存使用
        )
        
        # 如果启用数据导出，创建导出目录
        if self.cfg.export_data:
            import os
            os.makedirs(self.cfg.export_path, exist_ok=True)
            print(f"数据将导出到: {self.cfg.export_path}")
        
        # 设置紧凑布局，确保所有元素都能正确显示
        self.fig.tight_layout(rect=[0, 0, 1, 0.96])  # 为标题留出空间
        
        # 显示图表
        plt.show(block=True)
    
    def export_data_to_file(self):
        """将当前数据导出到文件"""
        if not self.cfg.export_data:
            print("数据导出功能未启用，请设置 PlotConfig.export_data = True")
            return
        
        import os
        import csv
        import datetime
        
        # 创建导出目录
        os.makedirs(self.cfg.export_path, exist_ok=True)
        
        # 生成时间戳文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 为每个子图导出数据
        for subplot_idx, subplot_data in self.data.items():
            if not subplot_data:  # 跳过空子图
                continue
                
            # 创建子图目录
            subplot_dir = os.path.join(self.cfg.export_path, f"subplot_{subplot_idx}")
            os.makedirs(subplot_dir, exist_ok=True)
            
            # 为每条线导出数据
            for line_idx, line_data in subplot_data.items():
                if not line_data['x'] or not line_data['y']:  # 跳过空线条
                    continue
                    
                # 获取线条标签
                line_label = f"line_{line_idx}"
                if self.cfg.line_labels and line_idx < len(self.cfg.line_labels):
                    line_label = self.cfg.line_labels[line_idx].replace(" ", "_")
                
                # 创建CSV文件
                filename = os.path.join(subplot_dir, f"{line_label}_{timestamp}.csv")
                
                # 写入数据
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['x', 'y'])  # 写入表头
                    
                    # 写入数据行
                    for i in range(len(line_data['x'])):
                        writer.writerow([line_data['x'][i], line_data['y'][i]])
                
                print(f"已导出数据到: {filename}")
    
    def stop(self):
        """停止实时绘图"""
        self.running = False
        
        # 如果启用了数据导出，在停止前导出数据
        if self.cfg.export_data:
            self.export_data_to_file()
        
        # 停止动画
        if self.ani is not None:
            # self.ani.event_source.stop()
            self.ani = None
        
        # 关闭图表
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None

class ZmqPlotServer:
    def __init__(self, config: PlotConfig):
        self.address = config.server_address
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind(self.address)
        self.socket.setsockopt(zmq.SNDHWM, 2) # 设置缓冲区为N条消息
        self.socket.setsockopt(zmq.RCVHWM, 2)
        self.socket.setsockopt(zmq.LINGER, 0) # 关闭时立即丢弃未发送的消息
        self.running = True
        
        # 创建绘图对象，传递相同的配置对象
        self.plot = RealtimePlot(config=config)
        
        # 初始化接收线程
        self.recv_thread = None
    
    def _receive_data(self):
        """在单独线程中接收ZMQ数据"""
        self.socket.setsockopt(zmq.RCVTIMEO, 1000)  # 设置接收超时为1秒
        
        while self.running:
            try:
                # 接收数据
                message = self.socket.recv_string()
                
                # 解析JSON数据
                try:
                    data = json.loads(message)
                    # 处理线条数据
                    # 提取y值、可选的x值、子图索引
                    y_values = data.get('y', [])
                    x_value = data.get('x', None)
                    subplot_idx = data.get('subplot', 0)  # 默认使用第一个子图
                    line_props = data.get('line_props', None)  # 获取线条属性
                    
                    # 如果数据是多子图格式
                    if 'line_data' in data:
                        # 多子图数据格式: {'line_data': [{subplot_idx: 0, y: [...], x: value, line_idx: 0, line_props: {...}}, ...]}
                        for subplot_data in data['line_data']:
                            subplot_idx = subplot_data.get('subplot', 0)
                            y_values = subplot_data.get('y', [])
                            x_value = subplot_data.get('x', None)
                            line_idx = subplot_data.get('line_idx', 0)
                            line_props = subplot_data.get('line_props', None)
                            self.plot.add_line_data(y_values, x_value, subplot_idx, line_idx, line_props)
                    else:
                        # 单子图数据格式: {y: [...], x: value, subplot: 0, line_idx: 0, line_props: {...}}
                        line_idx = data.get('line_idx', 0)
                        self.plot.add_line_data(y_values, x_value, subplot_idx, line_idx, line_props)
                    
                except json.JSONDecodeError:
                    print(f"接收到无效JSON数据: {message}")
                except Exception as e:
                    print(f"处理数据时出错: {e}")
                    import traceback
                    traceback.print_exc()
                
            except zmq.Again:
                # 超时但没有数据，继续循环
                continue
            except Exception as e:
                print(f"接收数据时出错: {e}")
                if not self.running:
                    break
    
    def start(self):
        # 启动数据接收
        self.running = True
        self.recv_thread = threading.Thread(target=self._receive_data)
        self.recv_thread.daemon = True
        self.recv_thread.start()
        
        print(f"ZMQ绘图服务器已启动，监听地址: {self.address}")
        # 启动绘图，ZL:需放在最后，在此阻塞
        self.plot.start()
        return True
    
    def stop(self):
        """停止ZMQ服务器和绘图"""
        self.running = False
        
        # 等待接收线程结束
        if self.recv_thread and self.recv_thread.is_alive():
            self.recv_thread.join(timeout=1.0)
        
        # 关闭ZMQ套接字
        self.socket.close()
        self.context.term()
        
        # 停止绘图
        self.plot.stop()
        
        print("ZMQ绘图服务器已停止")
        return True

    def __del__(self):
        self.stop()

# 绘图客户端，在其它地方导入使用
class ZmqPlotClient:
    def __init__(self):
        self.cfg = PlotConfig()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.connect(self.cfg.client_address)
        self.socket.setsockopt(zmq.LINGER, 0) # 关闭时立即丢弃未发送的消息

    def send(self, data):
        try:
            self.socket.send_string(json.dumps(data), flags=zmq.NOBLOCK)
        except Exception as e:
            print(f"vis.py处理发送时出错: {e}")

    def stop(self):
        try:
            if hasattr(self, 'socket'):
                try:
                    self.socket.close(linger=0)
                except:
                    pass
            if hasattr(self, 'context'):
                try:
                    self.context.term()
                except:
                    pass
        except Exception as e:
            print(f"关闭可视化客户端时出错: {e}")
        finally:
            print("可视化程序结束")
    
    def __del__(self):
        self.stop()

def start_server():
    server = ZmqPlotServer(config=PlotConfig())
    server.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止")
    finally:
        server.stop()
        print("程序结束")

def test_client():
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.connect('tcp://localhost:58585')
    socket.setsockopt(zmq.SNDHWM, 2) # 设置缓冲区为N条消息
    socket.setsockopt(zmq.RCVHWM, 2)
    socket.setsockopt(zmq.LINGER, 0) # 关闭时立即丢弃未发送的消息
    print("开始发送数据...")
    
    try:
        # 生成正弦波和余弦波数据
        t = 0
        while True:
            # 多子图数据格式示例 - 线条数据
            multi_data = {
                'line_data': [
                    {
                        'subplot': 0,
                        'y': [np.sin(t), np.cos(t)],
                        'x': [t, t + 10],
                        'line_idx': 0,
                        "line_props": {
                            "show_line": True,  # 不显示线条，只显示点
                            "color": "red",
                            "marker": "o",
                            "markersize": 5,
                            "label": "rt"
                        }
                    },
                    {
                        'subplot': 1,
                        'y': [np.sin(t)],
                        'x': [t],
                        'line_idx': 3
                    },
                    {
                        'subplot': 1,
                        'y': [20 * np.sin(t*2)],
                        'x': [t + 20],
                        'line_idx': 1
                    },
                    {
                        'subplot': 1,
                        'y': [20 * np.cos(t*2)],
                        'x': [t + 20],
                        'line_idx': 2
                    },
                    {
                        'subplot': 3,
                        'y': [np.sin(t), np.cos(t)],
                        'x': [t, t + 10],
                        'line_idx': 0,
                        "line_props": {
                            "show_line": False,  # 不显示线条，只显示点
                            "color": "blue",
                            "marker": ">",
                            "markersize": 5,
                            "label": "abc"
                        }
                    },
                ]
            }
            socket.send_string(json.dumps(multi_data))
            print(f"已发送, {time.time()}")
            
            t += 0.1
            time.sleep(0.00001)
            
    except KeyboardInterrupt:
        print("\n停止")
    finally:
        socket.close()
        context.term()
        print("程序结束")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="测试")
    args = parser.parse_args()
    if args.test:
        test_client()
    else:
        start_server()
