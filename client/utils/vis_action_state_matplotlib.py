# This visualization program can be used both as a standalone program (as a plotting server) and as a module (as a plotting client)
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

class PlotConfig:
    server_address: str = "tcp://*:58585"  # ZMQ binding address
    client_address: str = "tcp://localhost:58585"  # ZMQ binding address
    
    # Basic chart configuration
    max_points: int = 2000  # Maximum number of data points to display in chart
    auto_scroll: bool = True  # Enable auto-scrolling display
    scroll_window: int = 300  # Scroll window size (number of data points to display)
    title: str = "RT Data"  # Chart title
    y_label: str = "y"  # Y-axis label
    x_label: str = "x"  # X-axis label
    num_subplots: int = 4  # Number of subplots
    num_cols: int = 2 # Number of columns
    subplot_titles: Optional[List[str]] = None  # List of subplot titles, use default titles if not provided
    
    # Line and marker configuration
    show_markers: bool = True  # Whether to show data point markers
    marker_style: str = 'o'  # Data point marker style
    marker_size: int = 1  # Data point marker size
    line_styles: Optional[List[str]] = None  # List of line styles, options include "-"(solid), "--"(dashed), "-."(dashdot), ":"(dotted), etc.
    line_width: float = 1.0  # Line width
    line_labels: Optional[List[str]] = None  # List of line labels, use default labels if not provided
    show_lines: bool = False  # Whether to show lines, set to False to show only marker points
    line_alpha: float = 1.0  # Line transparency
    
    # Color and style configuration
    color_theme: str = 'rainbow'  # Color theme (options: default, viridis, plasma, inferno, magma, cividis, rainbow)
    grid_style: str = 'solid'  # Grid line style (options: solid, dashed, dotted, dashdot)
    grid_alpha: float = 0.3  # Grid line transparency (float between 0-1)
    background_color: Optional[str] = None  # Chart background color (e.g.: "#f0f0f0", "lightgray")
    legend_loc: str = 'upper right'  # Legend position (options: upper left, upper right, lower left, lower right, center, best)
    custom_colors: Optional[List[str]] = None  # Custom color list
    
    # Display and interaction configuration
    show_stats: bool = True  # Whether to show data statistics
    figure_size: Optional[Tuple[float, float]] = None  # Chart size (width, height) in inches
    dpi: int = 100  # Chart DPI
    font_size: int = 10  # Font size
    auto_adjust_ylim: bool = True  # Automatically adjust Y-axis range to fit data
    auto_ylim_mode: str = 'vis' # vis: based on min/max values in visible range, all: based on min/max values of all data
    y_lim: Tuple[float, float] = (-0.6, 1.3)  # Y-axis range, used when auto_adjust_ylim is False
    dark_mode: bool = False  # Enable dark mode
    show_toolbar: bool = True  # Show matplotlib toolbar
    antialiased: bool = True  # Enable antialiasing
    
    # Performance optimization configuration
    update_interval: int = 10  # Chart update interval (milliseconds)
    use_blit: bool = False  # Use blitting to optimize performance, ZL: when True, x/y axis scales won't update (updates when window changes)
    downsample_threshold: int = 10000  # Enable downsampling when data points exceed this threshold
    downsample_method: str = 'peak'  # Downsampling method (options: peak, mean, min_max)
    
    # Data export configuration
    export_data: bool = False  # Enable data export functionality
    export_path: str = './data_export'  # Data export path
    
    def update_from_args(self, args):
        """Update configuration from argparse arguments.
        
        Args:
            args: argparse.Namespace object containing parsed arguments
        """
        if hasattr(args, 'num_subplots') and args.num_subplots is not None:
            self.num_subplots = args.num_subplots
        if hasattr(args, 'num_cols') and args.num_cols is not None:
            self.num_cols = args.num_cols
        if hasattr(args, 'auto_adjust_ylim') and args.auto_adjust_ylim is not None:
            self.auto_adjust_ylim = args.auto_adjust_ylim
        if hasattr(args, 'y_lim') and args.y_lim is not None:
            self.y_lim = tuple(args.y_lim)
        if hasattr(args, 'scroll_window') and args.scroll_window is not None:
            self.scroll_window = args.scroll_window

class RealtimePlot:
    def __init__(self, config: PlotConfig):
        """Initialize RealtimePlot with configuration.
        
        Args:
            config: PlotConfig object containing all plotting parameters
        """
        self.cfg = config
        
        # Initialize chart data storage
        self.data = {}
        self.lines = {}
        self.axes = {}
        self.fig = None
        self.ani = None
        self.visible_subplot = None  # Current visible subplot index, None means show all subplots
        self.running = False
        self.lock = threading.Lock()  # For thread-safe data access
        
        # Initialize color mapping
        self._init_colors()
    
    def _init_colors(self):
        """Initialize color mapping."""
        if self.cfg.custom_colors:
            self.colors = self.cfg.custom_colors
        else:
            # Create color mapping based on color theme
            if self.cfg.color_theme == 'default':
                self.colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
            else:
                # Use matplotlib's color mapping
                cmap = getattr(cm, self.cfg.color_theme, cm.rainbow)
                self.colors = [cmap(i) for i in np.linspace(0, 1, 10)]
    
    def _init_figure(self):
        """Initialize matplotlib figure."""
        # Set chart style
        if self.cfg.dark_mode:
            plt.style.use('dark_background')
        
        # Create figure and subplots
        fig_size = self.cfg.figure_size or (12, 8)
        self.fig, axes = plt.subplots(
            nrows=(self.cfg.num_subplots + self.cfg.num_cols - 1) // self.cfg.num_cols,
            ncols=self.cfg.num_cols,
            figsize=fig_size,
            dpi=self.cfg.dpi,
            squeeze=False  # Ensure axes is always a 2D array
        )
        
        # Set chart title and style
        self.fig.suptitle(self.cfg.title, fontsize=self.cfg.font_size + 4)
        self.fig.tight_layout(rect=[0, 0, 1, 0.96])  # Leave space for title
        
        # Set background color
        if self.cfg.background_color:
            self.fig.patch.set_facecolor(self.cfg.background_color)
        
        # Initialize each subplot
        for i in range(self.cfg.num_subplots):
            row, col = divmod(i, self.cfg.num_cols)
            ax = axes[row, col]
            
            # Set subplot title
            if self.cfg.subplot_titles and i < len(self.cfg.subplot_titles):
                title = self.cfg.subplot_titles[i]
            else:
                title = f"joint {i}"
            ax.set_title(title, fontsize=self.cfg.font_size + 2)
            
            # Set axis labels
            ax.set_xlabel(self.cfg.x_label, fontsize=self.cfg.font_size)
            ax.set_ylabel(self.cfg.y_label, fontsize=self.cfg.font_size)
            
            # Set grid
            ax.grid(True, linestyle=self.cfg.grid_style, alpha=self.cfg.grid_alpha)
            
            # Set Y-axis range
            if not self.cfg.auto_adjust_ylim:
                ax.set_ylim(self.cfg.y_lim)
            
            # Set integer ticks
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            
            # Store axis object
            self.axes[i] = ax
            
            # Initialize data storage for this subplot
            self.data[i] = {}
            self.lines[i] = {}
        
        # Hide excess subplots
        total_subplots = axes.shape[0] * axes.shape[1]
        for i in range(self.cfg.num_subplots, total_subplots):
            row, col = divmod(i, self.cfg.num_cols)
            axes[row, col].set_visible(False)
        
        # Add legend
        for i in range(self.cfg.num_subplots):
            self.axes[i].legend(loc=self.cfg.legend_loc, fontsize=self.cfg.font_size - 2)
        
        # Enable toolbar
        if not self.cfg.show_toolbar:
            plt.rcParams['toolbar'] = 'None'
        
        # Enable antialiasing
        if self.cfg.antialiased:
            plt.rcParams['lines.antialiased'] = True
        
        return self.fig
    
    def add_line_data(self, y_values: List[float], x_values: Optional[List[float]] = None, subplot_idx: int = 0, line_idx: int = 0, line_props: Optional[Dict[str, Any]] = None):
        """Add line data to the plot.
        
        Args:
            y_values: List of Y-axis data points
            x_values: List of X-axis data points, if None uses incremental indices
            subplot_idx: Subplot index
            line_idx: Line index
            line_props: Line properties dictionary, can contain 'show_line', 'color', 'linestyle', 'linewidth', 'marker', 'markersize', 'alpha', etc.
        """
        with self.lock:
            # Ensure subplot index is valid
            if subplot_idx >= self.cfg.num_subplots:
                print(f"Warning: subplot index {subplot_idx} out of range, maximum value is {self.cfg.num_subplots-1}, not plotting this subplot")
                # subplot_idx = subplot_idx % self.cfg.num_subplots
                return
            
            # Ensure the subplot's data dictionary is initialized
            if subplot_idx not in self.data:
                self.data[subplot_idx] = {}
            
            # Ensure the line's data list is initialized
            if line_idx not in self.data[subplot_idx]:
                self.data[subplot_idx][line_idx] = {'x': [], 'y': [], 'props': {}}
            
            # If line properties are provided, update them
            if line_props:
                self.data[subplot_idx][line_idx]['props'].update(line_props)
            
            # Add Y value data
            if not isinstance(y_values, list):
                y_values = [y_values]
            
            # Process X values
            if x_values is None:
                # If no X values provided, use current data length as X values
                current_len = len(self.data[subplot_idx][line_idx]['x'])
                x_values = [current_len + i for i in range(len(y_values))]
            elif not isinstance(x_values, list):
                x_values = [x_values]
            
            # Ensure x and y have the same length
            min_len = min(len(x_values), len(y_values))
            x_values = x_values[:min_len]
            y_values = y_values[:min_len]
            
            # Add data points
            self.data[subplot_idx][line_idx]['x'].extend(x_values)
            self.data[subplot_idx][line_idx]['y'].extend(y_values)
            
            # Limit number of data points to maintain performance
            if len(self.data[subplot_idx][line_idx]['x']) > self.cfg.max_points:
                excess = len(self.data[subplot_idx][line_idx]['x']) - self.cfg.max_points
                self.data[subplot_idx][line_idx]['x'] = self.data[subplot_idx][line_idx]['x'][excess:]
                self.data[subplot_idx][line_idx]['y'] = self.data[subplot_idx][line_idx]['y'][excess:]
    
    def _downsample_data(self, x_data, y_data, target_points=100):
        """Downsample data to reduce number of plot points and improve performance.
        
        Args:
            x_data: X-axis data
            y_data: Y-axis data
            target_points: Target number of points
            
        Returns:
            Tuple of downsampled (x_data, y_data)
        """
        if len(x_data) <= target_points:
            return x_data, y_data
        
        # Calculate downsampling factor
        factor = max(1, len(x_data) // target_points)
        
        if self.cfg.downsample_method == 'mean':
            # Use mean downsampling
            x_downsampled = []
            y_downsampled = []
            for i in range(0, len(x_data), factor):
                end = min(i + factor, len(x_data))
                if i < end:
                    x_downsampled.append(np.mean(x_data[i:end]))
                    y_downsampled.append(np.mean(y_data[i:end]))
            return x_downsampled, y_downsampled
            
        elif self.cfg.downsample_method == 'min_max':
            # Use min and max downsampling to preserve data range
            x_downsampled = []
            y_downsampled = []
            for i in range(0, len(x_data), factor):
                end = min(i + factor, len(x_data))
                if i < end:
                    chunk_x = x_data[i:end]
                    chunk_y = y_data[i:end]
                    
                    # Add the first point of the interval
                    x_downsampled.append(chunk_x[0])
                    y_downsampled.append(chunk_y[0])
                    
                    if len(chunk_y) > 1:
                        # Find points with minimum and maximum Y values
                        min_idx = np.argmin(chunk_y)
                        max_idx = np.argmax(chunk_y)
                        
                        # Ensure not to add the first point repeatedly
                        if min_idx != 0:
                            x_downsampled.append(chunk_x[min_idx])
                            y_downsampled.append(chunk_y[min_idx])
                        
                        if max_idx != 0 and max_idx != min_idx:
                            x_downsampled.append(chunk_x[max_idx])
                            y_downsampled.append(chunk_y[max_idx])
                        
                        # Add the last point of the interval
                        if len(chunk_y) > 1 and len(chunk_y) - 1 not in (0, min_idx, max_idx):
                            x_downsampled.append(chunk_x[-1])
                            y_downsampled.append(chunk_y[-1])
            return x_downsampled, y_downsampled
        
        else:  # Default to 'peak' method
            # Use peak detection downsampling to preserve data features
            x_downsampled = []
            y_downsampled = []
            for i in range(0, len(x_data), factor):
                end = min(i + factor, len(x_data))
                if i < end:
                    chunk_x = x_data[i:end]
                    chunk_y = y_data[i:end]
                    
                    # Always keep the first point
                    x_downsampled.append(chunk_x[0])
                    y_downsampled.append(chunk_y[0])
                    
                    # If there are multiple points in the interval, detect peaks
                    if len(chunk_y) > 2:
                        # Simple peak detection: compare with adjacent points
                        for j in range(1, len(chunk_y) - 1):
                            if (chunk_y[j] > chunk_y[j-1] and chunk_y[j] > chunk_y[j+1]) or \
                               (chunk_y[j] < chunk_y[j-1] and chunk_y[j] < chunk_y[j+1]):
                                x_downsampled.append(chunk_x[j])
                                y_downsampled.append(chunk_y[j])
                    
                    # Always keep the last point
                    if len(chunk_y) > 1:
                        x_downsampled.append(chunk_x[-1])
                        y_downsampled.append(chunk_y[-1])
            return x_downsampled, y_downsampled
    
    def _update_plot(self, frame):
        """Update plot, called by animation."""
        with self.lock:
            # If visible subplot is specified, only update that subplot
            subplots_to_update = [self.visible_subplot] if self.visible_subplot is not None else self.data.keys()
            
            for subplot_idx in subplots_to_update:
                if subplot_idx not in self.data:
                    continue
                
                ax = self.axes[subplot_idx]
                
                # Find maximum X value among all lines in this subplot to determine if scrolling is needed
                max_x_values = []
                for line_idx, line_data in self.data[subplot_idx].items():
                    if line_data['x'] and len(line_data['x']) > 0:
                        max_x_values.append(max(line_data['x']))
                
                # If there is data, determine X-axis range
                if max_x_values and self.cfg.auto_scroll:
                    max_x = max(max_x_values)
                    # Set X-axis range to achieve scrolling effect
                    if self.cfg.scroll_window > 0:
                        new_min = max(0, max_x - self.cfg.scroll_window)
                        ax.set_xlim(new_min, max_x)
                    else:
                        new_min = max(0, max_x - self.cfg.max_points)
                        ax.set_xlim(new_min, max_x)
                    
                # Update or create each line
                for line_idx, line_data in self.data[subplot_idx].items():
                    if not line_data['x'] or len(line_data['x']) == 0:
                        continue
                    
                    # Get line data
                    x_data = line_data['x']
                    y_data = line_data['y']
                    
                    # Get line properties
                    line_props = line_data.get('props', {})
                    
                    # If too many data points, downsample to improve performance
                    if len(x_data) > self.cfg.downsample_threshold:
                        x_display, y_display = self._downsample_data(x_data, y_data, self.cfg.max_points)
                    else:
                        x_display, y_display = x_data, y_data
                    
                    # If line already exists, update data
                    if line_idx in self.lines[subplot_idx]:
                        line = self.lines[subplot_idx][line_idx]
                        line.set_data(x_display, y_display)
                        
                        # Update line properties (if changed)
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
                        
                        # Handle whether to show line
                        show_line = line_props.get('show_line', self.cfg.show_lines)
                        if not show_line and line.get_linestyle() != '':
                            line.set_linestyle('')
                        elif show_line and line.get_linestyle() == '' and 'linestyle' not in line_props:
                            line.set_linestyle('-')  # 默认实线
                    else:
                        # Create new line
                        color_idx = line_idx % len(self.colors)
                        color = line_props.get('color', self.colors[color_idx])
                        
                        # Set line style
                        line_style = '-'
                        if 'linestyle' in line_props:
                            line_style = line_props['linestyle']
                        elif self.cfg.line_styles and line_idx < len(self.cfg.line_styles):
                            line_style = self.cfg.line_styles[line_idx]
                        
                        # Handle whether to show line
                        show_line = line_props.get('show_line', self.cfg.show_lines)
                        if not show_line:
                            line_style = ''
                        
                        # Set line label
                        line_label = f"line {line_idx+1}"
                        if 'label' in line_props:
                            line_label = line_props['label']
                        elif self.cfg.line_labels and line_idx < len(self.cfg.line_labels):
                            line_label = self.cfg.line_labels[line_idx]
                        
                        # Create line
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
                        
                        # Store line object
                        self.lines[subplot_idx][line_idx] = line
                
                # Automatically adjust Y-axis range
                if self.cfg.auto_adjust_ylim:
                    all_y_values = []
                    for line_data in self.data[subplot_idx].values():
                        if line_data['y']:
                            # If in vis mode or large data volume, only use data within visible range to adjust Y-axis
                            if (self.cfg.auto_ylim_mode == 'vis' or len(line_data['y']) > self.cfg.max_points) and len(line_data['x']) > 0:
                                # Get current X-axis range
                                x_min, x_max = ax.get_xlim()
                                # Find data points within visible range
                                visible_indices = [i for i, x in enumerate(line_data['x']) if x_min <= x <= x_max]
                                if visible_indices:
                                    visible_y = [line_data['y'][i] for i in visible_indices]
                                    all_y_values.extend(visible_y)
                            else:
                                all_y_values.extend(line_data['y'])
                    
                    if all_y_values:
                        min_y = min(all_y_values)
                        max_y = max(all_y_values)
                        # Add some padding
                        padding = (max_y - min_y) * 0.1 if max_y > min_y else 0.1
                        ax.set_ylim(min_y - padding, max_y + padding)
                
                # Update legend
                if self.lines[subplot_idx]:
                    ax.legend(loc=self.cfg.legend_loc, fontsize=self.cfg.font_size - 2)
                    
                # Show statistics
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
                    # Update or create statistics text
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
        
        # Return all line objects for animation
        all_lines = []
        for subplot_lines in self.lines.values():
            all_lines.extend(subplot_lines.values())
        return all_lines
    
    def set_visible_subplot(self, subplot_idx: Optional[int] = None):
        """Set visible subplot, if None then show all subplots.
        
        Args:
            subplot_idx: Index of subplot to show, None to show all
        """
        with self.lock:
            self.visible_subplot = subplot_idx
            
            # Update subplot visibility
            if self.fig is not None:
                for idx, ax in self.axes.items():
                    if subplot_idx is None or idx == subplot_idx:
                        ax.set_visible(True)
                    else:
                        ax.set_visible(False)
                
                # Re-layout the chart
                self.fig.tight_layout(rect=[0, 0, 1, 0.96])
    
    def start(self):
        """Start real-time plotting."""
        if self.running:
            return
        
        self.running = True
        
        # Initialize chart
        self._init_figure()
        
        self.ani = animation.FuncAnimation(
            self.fig,
            self._update_plot,
            interval=self.cfg.update_interval,  # 更新间隔（毫秒）
            blit=self.cfg.use_blit,
            cache_frame_data=False  # Don't cache frame data to reduce memory usage
        )
        
        # If data export is enabled, create export directory
        if self.cfg.export_data:
            import os
            os.makedirs(self.cfg.export_path, exist_ok=True)
            print(f"Data will be exported to: {self.cfg.export_path}")
        
        # Set tight layout to ensure all elements are displayed correctly
        self.fig.tight_layout(rect=[0, 0, 1, 0.96])  # Leave space for title
        
        # Show chart
        plt.show(block=True)
    
    def export_data_to_file(self):
        """Export current data to file."""
        if not self.cfg.export_data:
            print("Data export feature not enabled, please set PlotConfig.export_data = True")
            return
        
        import os
        import csv
        import datetime
        
        # Create export directory
        os.makedirs(self.cfg.export_path, exist_ok=True)
        
        # Generate timestamp filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export data for each subplot
        for subplot_idx, subplot_data in self.data.items():
            if not subplot_data:  # Skip empty subplots
                continue
                
            # Create subplot directory
            subplot_dir = os.path.join(self.cfg.export_path, f"subplot_{subplot_idx}")
            os.makedirs(subplot_dir, exist_ok=True)
            
            # Export data for each line
            for line_idx, line_data in subplot_data.items():
                if not line_data['x'] or not line_data['y']:  # Skip empty lines
                    continue
                    
                # Get line label
                line_label = f"line_{line_idx}"
                if self.cfg.line_labels and line_idx < len(self.cfg.line_labels):
                    line_label = self.cfg.line_labels[line_idx].replace(" ", "_")
                
                # Create CSV file
                filename = os.path.join(subplot_dir, f"{line_label}_{timestamp}.csv")
                
                # Write data
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['x', 'y'])  # Write header
                    
                    # Write data rows
                    for i in range(len(line_data['x'])):
                        writer.writerow([line_data['x'][i], line_data['y'][i]])
                
                print(f"Data exported to: {filename}")
    
    def stop(self):
        """Stop and close the client connection."""
        """Stop real-time plotting."""
        self.running = False
        
        # If data export is enabled, export data before stopping
        if self.cfg.export_data:
            self.export_data_to_file()
        
        # Stop animation
        if self.ani is not None:
            # self.ani.event_source.stop()
            self.ani = None
        
        # Close chart
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None

class ZmqPlotServer:
    """Plot server that receives ZMQ data and plots in real-time.
    
    This class creates a ZMQ subscriber that receives plotting data
    and displays it using RealtimePlot.
    """
    def __init__(self, config: PlotConfig):
        """Initialize plot server.
        
        Args:
            config: Plot configuration
        """
        self.address = config.server_address
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind(self.address)
        self.socket.setsockopt(zmq.SNDHWM, 2) # Set buffer to N messages
        self.socket.setsockopt(zmq.RCVHWM, 2)
        self.socket.setsockopt(zmq.LINGER, 0) # Immediately discard unsent messages on close
        self.running = True
        
        # Create plot object, pass the same configuration object
        self.plot = RealtimePlot(config=config)
        
        # Initialize receive thread
        self.recv_thread = None
    
    def _receive_data(self):
        """Receive ZMQ data in separate thread.
        
        This method runs in a background thread and continuously
        receives data from ZMQ socket.
        """
        self.socket.setsockopt(zmq.RCVTIMEO, 1000)  # Set receive timeout to 1 second
        
        while self.running:
            try:
                # Receive data
                message = self.socket.recv_string()
                
                # Parse JSON data
                try:
                    data = json.loads(message)
                    # Process line data
                    # Extract y values, optional x values, subplot index
                    y_values = data.get('y', [])
                    x_value = data.get('x', None)
                    subplot_idx = data.get('subplot', 0)  # 默认使用第一个子图
                    line_props = data.get('line_props', None)  # 获取线条属性
                    
                    # If data is in multi-subplot format
                    if 'line_data' in data:
                        # Multi-subplot data format: {'line_data': [{subplot_idx: 0, y: [...], x: value, line_idx: 0, line_props: {...}}, ...]}
                        for subplot_data in data['line_data']:
                            subplot_idx = subplot_data.get('subplot', 0)
                            y_values = subplot_data.get('y', [])
                            x_value = subplot_data.get('x', None)
                            line_idx = subplot_data.get('line_idx', 0)
                            line_props = subplot_data.get('line_props', None)
                            self.plot.add_line_data(y_values, x_value, subplot_idx, line_idx, line_props)
                    else:
                        # Single subplot data format: {y: [...], x: value, subplot: 0, line_idx: 0, line_props: {...}}
                        line_idx = data.get('line_idx', 0)
                        self.plot.add_line_data(y_values, x_value, subplot_idx, line_idx, line_props)
                    
                except json.JSONDecodeError:
                    print(f"Received invalid JSON data: {message}")
                except Exception as e:
                    print(f"Error processing data: {e}")
                    import traceback
                    traceback.print_exc()
                
            except zmq.Again:
                # Timeout but no data, continue loop
                continue
            except Exception as e:
                print(f"Error receiving data: {e}")
                if not self.running:
                    break
    
    def start(self):
        # Start data reception
        self.running = True
        self.recv_thread = threading.Thread(target=self._receive_data)
        self.recv_thread.daemon = True
        self.recv_thread.start()
        
        print(f"ZMQ plot server started, listening address: {self.address}")
        # Start plotting, ZL: must be placed last, blocks here
        self.plot.start()
        return True
    
    def stop(self):
        """Stop ZMQ server and plotting."""
        self.running = False
        
        # Wait for receive thread to end
        if self.recv_thread and self.recv_thread.is_alive():
            self.recv_thread.join(timeout=1.0)
        
        # Close ZMQ socket
        self.socket.close()
        self.context.term()
        
        # Stop plotting
        self.plot.stop()
        
        print("ZMQ plot server stopped")
        return True

    def __del__(self):
        self.stop()

# Plot client for use in other modules
class ZmqPlotClient:
    def __init__(self):
        """Initialize plot client."""
        self.cfg = PlotConfig()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.connect(self.cfg.client_address)
        self.socket.setsockopt(zmq.LINGER, 0) # Immediately discard unsent messages on close

    def send(self, data):
        """Send data to plot server.
        
        Args:
            data: Data dictionary to send to the plot server
        """
        try:
            self.socket.send_string(json.dumps(data), flags=zmq.NOBLOCK)
        except Exception as e:
            print(f"Error sending data in vis.py: {e}")

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
            print(f"Error closing visualization client: {e}")
        finally:
            print("Visualization program ended")
    
    def __del__(self):
        self.stop()

def start_server(config=None):
    """Start ZMQ plot server with configuration.
    
    Args:
        config: PlotConfig instance, if None creates default configuration
    
    This function creates and starts a ZmqPlotServer instance
    that listens for incoming plot data via ZMQ.
    """
    if config is None:
        config = PlotConfig()
    server = ZmqPlotServer(config=config)
    server.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping")
    finally:
        server.stop()
        print("Program ended")

def test_client():
    """Test client function for sending sample data to the plot server.
    
    Generates sine and cosine wave data and sends it to the visualization server
    for testing purposes.
    """
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.connect('tcp://localhost:58585')
    socket.setsockopt(zmq.SNDHWM, 2) # Set buffer to N messages
    socket.setsockopt(zmq.RCVHWM, 2)
    socket.setsockopt(zmq.LINGER, 0) # Immediately discard unsent messages on close
    print("Starting to send data...")
    
    try:
        # Generate sine and cosine wave data
        t = 0
        while True:
            # Multi-subplot data format example - line data
            multi_data = {
                'line_data': [
                    {
                        'subplot': 0,
                        'y': [np.sin(t), np.cos(t)],
                        'x': [t, t + 10],
                        'line_idx': 0,
                        "line_props": {
                            "show_line": True,  # Show lines, set to False to show only points
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
            print(f"Sent, {time.time()}")
            
            t += 0.1
            time.sleep(0.00001)
            
    except KeyboardInterrupt:
        print("\nStopping")
    finally:
        socket.close()
        context.term()
        print("Program ended")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Real-time plotting visualization tool")
    parser.add_argument("--test", action="store_true", help="Test mode")
    
    # Plot configuration arguments
    parser.add_argument("--num_subplots", type=int, help="Number of subplots (default: 2)")
    parser.add_argument("--num_cols", type=int, help="Number of columns (default: 2)")
    parser.add_argument("--auto_adjust_ylim", action="store_true", help="Enable auto adjust Y-axis limits")
    parser.add_argument("--no_auto_adjust_ylim", action="store_true", help="Disable auto adjust Y-axis limits")
    parser.add_argument("--y_lim", type=float, nargs=2, metavar=('MIN', 'MAX'), help="Y-axis limits (min max), e.g., --y_lim -1.0 1.0")
    parser.add_argument("--scroll_window", type=int, help="Scroll window size (number of data points to display, default: 300)")
    
    args = parser.parse_args()
    
    if args.test:
        test_client()
    else:
        # Create configuration and update from arguments
        config = PlotConfig()
        
        # Handle auto_adjust_ylim boolean flags
        if args.auto_adjust_ylim:
            args.auto_adjust_ylim = True
        elif args.no_auto_adjust_ylim:
            args.auto_adjust_ylim = False
        else:
            args.auto_adjust_ylim = None
        
        config.update_from_args(args)
        start_server(config)
