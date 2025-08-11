import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import CubicSpline
from scipy.signal import savgol_filter
import time
import yaml
import re
from pathlib import Path

def crop_and_resize(img, target_height=480, target_width=640):
    h, w = img.shape[:2]
    target_ratio = target_width / target_height
    current_ratio = w / h

    # 计算需要裁剪的边
    if current_ratio > target_ratio:
        # 裁剪宽度（长边是宽度）
        new_width = int(h * target_ratio)  # 按目标比例计算新宽度
        delta = w - new_width
        left = delta // 2
        right = delta - left
        cropped = img[:, left:w - right]  # 高度不变，裁剪左右
    else:
        # 裁剪高度（长边是高度）
        new_height = int(w / target_ratio)  # 按目标比例计算新高度
        delta = h - new_height
        top = delta // 2
        bottom = delta - top
        cropped = img[top:h - bottom, :]  # 宽度不变，裁剪上下

    # 缩放至目标尺寸（使用INTER_AREA插值适用于缩小图像）
    resized = cv2.resize(cropped, (target_width, target_height), interpolation=cv2.INTER_AREA)
    return resized

def pad_and_resize(img, target_height=640, target_width=640, pad_color=(0, 0, 0)):
    h, w = img.shape[:2]
    target_ratio = target_width / target_height
    current_ratio = w / h

    # 计算需要填充的边
    if current_ratio > target_ratio:
        # 填充高度（长边是宽度）
        new_height = int(w / target_ratio)  # 按目标比例计算新高度
        delta = new_height - h
        top = delta // 2
        bottom = delta - top
        padded = cv2.copyMakeBorder(img, top, bottom, 0, 0, cv2.BORDER_CONSTANT, value=pad_color)  # 宽度不变，填充上下
    else:
        # 填充宽度（长边是高度）
        new_width = int(h * target_ratio)  # 按目标比例计算新宽度
        delta = new_width - w
        left = delta // 2
        right = delta - left
        padded = cv2.copyMakeBorder(img, 0, 0, left, right, cv2.BORDER_CONSTANT, value=pad_color)  # 高度不变，填充左右

    # 缩放至目标尺寸（使用INTER_AREA插值适用于缩小图像）
    resized = cv2.resize(padded, (target_width, target_height), interpolation=cv2.INTER_AREA)
    return resized

def resize(img, target_height=480, target_width=640):
    return cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_AREA)

def preprocess_yaml(file_path, base_dir=None):
    """解析包含!include的YAML文件"""
    if base_dir is None:
        base_dir = Path(file_path).parent
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 查找所有!include指令
    includes = re.findall(r"!include\s+['\"](.+?)['\"]", content)
    
    # 递归处理包含文件
    parsed_includes = {}
    for inc in set(includes):
        inc_path = base_dir / inc
        parsed_includes[inc] = preprocess_yaml(inc_path, base_dir)
    
    # 替换为YAML安全表示
    for path, data in parsed_includes.items():
        include_tag = f"!include '{path}'"
        yaml_data = yaml.dump(data, default_flow_style=False)
        content = content.replace(include_tag, yaml_data)
    
    return yaml.safe_load(content)

class RobotSmoother:
    def __init__(self, robot_interface):
        self.robot = robot_interface
        self.trajectory_queue = []
        
        # 运动约束参数
        self.max_velocity = 0.15    # 降低最大速度
        self.max_acceleration = 0.1 # 降低加速度
        
    def cubic_spline_interpolation(self, waypoints, density=5):
        """三次样条插值生成平滑轨迹"""
        n_points = len(waypoints)
        t = np.linspace(0, 1, n_points)
        
        # 转置为(6, n)维度数组（假设6自由度）
        wp_array = np.array(waypoints).T
        
        # 为每个关节创建样条曲线
        cs = [CubicSpline(t, wp) for wp in wp_array]
        
        # 生成插值时间点
        t_new = np.linspace(0, 1, n_points*density)
        return np.array([c(t_new) for c in cs]).T.tolist()

    def add_actions(self, chunk):
        """添加新动作块并进行平滑处理"""
        # 轨迹插值（每个原始点间插入4个新点）
        smoothed = self.cubic_spline_interpolation(chunk, density=5)
        self.trajectory_queue.extend(smoothed)
        
    def get_trajectory_queue(self):
        return self.trajectory_queue
        """执行缓存的轨迹点"""
        self.robot.set_velocity(self.max_velocity)
        self.robot.set_acceleration(self.max_acceleration)
        
        for wp in self.trajectory_queue:
            # 添加最小执行时间保证
            start_time = time.time()
            
            self.robot.move_to(wp)  # 假设这是底层控制接口
            
            # 计算实际运动时间，防止超速
            elapsed = time.time() - start_time
            min_duration = 0.1  # 每个点的最小执行时间
            if elapsed < min_duration:
                time.sleep(min_duration - elapsed)
        
        self.trajectory_queue.clear()

def smooth_with_gaussian(actions, sigma=1.5):
    """使用高斯滤波器平滑动作序列的每一维。"""
    smoothed_actions = np.zeros_like(actions)
    for i in range(actions.shape[1]): # 对每一维（每个关节/坐标）独立滤波
        smoothed_actions[:, i] = gaussian_filter1d(actions[:, i], sigma=sigma, mode='nearest')
        # mode='nearest' 处理边界，避免边缘效应过大
    return smoothed_actions

def filter_trajectory(points, window=5):
    """应用Savitzky-Golay滤波器"""
    return savgol_filter(points, window, 3, axis=0)
