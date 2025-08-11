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
    """Crop and resize image to target dimensions while maintaining aspect ratio.
    
    Args:
        img: Input image array
        target_height (int): Target height in pixels
        target_width (int): Target width in pixels
        
    Returns:
        numpy.ndarray: Cropped and resized image
    """
    h, w = img.shape[:2]
    target_ratio = target_width / target_height
    current_ratio = w / h

    # Calculate edges to crop
    if current_ratio > target_ratio:
        # Crop width (width is the longer side)
        new_width = int(h * target_ratio)  # Calculate new width based on target ratio
        delta = w - new_width
        left = delta // 2
        right = delta - left
        cropped = img[:, left:w - right]  # Keep height unchanged, crop left and right
    else:
        # Crop height (height is the longer side)
        new_height = int(w / target_ratio)  # Calculate new height based on target ratio
        delta = h - new_height
        top = delta // 2
        bottom = delta - top
        cropped = img[top:h - bottom, :]  # Keep width unchanged, crop top and bottom

    # Resize to target dimensions (using INTER_AREA interpolation suitable for downscaling)
    resized = cv2.resize(cropped, (target_width, target_height), interpolation=cv2.INTER_AREA)
    return resized

def pad_and_resize(img, target_height=480, target_width=640, pad_color=(0, 0, 0)):
    """Pad and resize image to target dimensions while maintaining aspect ratio.
    
    Args:
        img: Input image array
        target_height (int): Target height in pixels
        target_width (int): Target width in pixels
        pad_color (tuple): RGB color for padding (default: black)
        
    Returns:
        numpy.ndarray: Padded and resized image
    """
    h, w = img.shape[:2]
    target_ratio = target_width / target_height
    current_ratio = w / h

    # Calculate edges to pad
    if current_ratio > target_ratio:
        # Pad height (width is the longer side)
        new_height = int(w / target_ratio)  # Calculate new height based on target ratio
        delta = new_height - h
        top = delta // 2
        bottom = delta - top
        padded = cv2.copyMakeBorder(img, top, bottom, 0, 0, cv2.BORDER_CONSTANT, value=pad_color)  # Keep width unchanged, pad top and bottom
    else:
        # Pad width (height is the longer side)
        new_width = int(h * target_ratio)  # Calculate new width based on target ratio
        delta = new_width - w
        left = delta // 2
        right = delta - left
        padded = cv2.copyMakeBorder(img, 0, 0, left, right, cv2.BORDER_CONSTANT, value=pad_color)  # Keep height unchanged, pad left and right

    # Resize to target dimensions (using INTER_AREA interpolation suitable for downscaling)
    resized = cv2.resize(padded, (target_width, target_height), interpolation=cv2.INTER_AREA)
    return resized

def resize(img, target_height=480, target_width=640):
    """Resize image to target dimensions.
    
    Args:
        img: Input image array
        target_height (int): Target height in pixels
        target_width (int): Target width in pixels
        
    Returns:
        numpy.ndarray: Resized image
    """
    return cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_AREA)

def preprocess_yaml(file_path, base_dir=None):
    """Parse YAML files containing !include directives"""
    if base_dir is None:
        base_dir = Path(file_path).parent
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find all !include directives
    includes = re.findall(r"!include\s+['\"](.+?)['\"]")
    
    # Recursively process included files
    parsed_includes = {}
    for inc in set(includes):
        inc_path = base_dir / inc
        parsed_includes[inc] = preprocess_yaml(inc_path, base_dir)
    
    # Replace with YAML safe representation
    for path, data in parsed_includes.items():
        include_tag = f"!include '{path}'"
        yaml_data = yaml.dump(data, default_flow_style=False)
        content = content.replace(include_tag, yaml_data)
    
    return yaml.safe_load(content)

class RobotSmoother:
    """Robot trajectory smoother for generating smooth motion paths.
    
    This class provides trajectory smoothing capabilities using cubic spline
    interpolation and motion constraint parameters.
    """
    
    def __init__(self, robot_interface):
        """Initialize the robot smoother.
        
        Args:
            robot_interface: Robot control interface object
        """
        self.robot = robot_interface
        self.trajectory_queue = []
        
        # Motion constraint parameters
        self.max_velocity = 0.15    # Reduced maximum velocity
        self.max_acceleration = 0.1 # Reduced acceleration
        
    def cubic_spline_interpolation(self, waypoints, density=5):
        """Generate smooth trajectory using cubic spline interpolation.
        
        Args:
            waypoints (list): List of waypoint positions
            density (int): Interpolation density (points per original waypoint)
            
        Returns:
            list: Interpolated smooth trajectory points
        """
        n_points = len(waypoints)
        t = np.linspace(0, 1, n_points)
        
        # Transpose to (6, n) dimension array (assuming 6 DOF)
        wp_array = np.array(waypoints).T
        
        # Create spline curves for each joint
        cs = [CubicSpline(t, wp) for wp in wp_array]
        
        # Generate interpolated time points
        t_new = np.linspace(0, 1, n_points*density)
        return np.array([c(t_new) for c in cs]).T.tolist()

    def add_actions(self, chunk):
        """Add new action chunk and perform smoothing.
        
        Args:
            chunk (list): List of action waypoints to be smoothed
        """
        # Trajectory interpolation (insert 4 new points between each original point)
        smoothed = self.cubic_spline_interpolation(chunk, density=5)
        self.trajectory_queue.extend(smoothed)
        
    def get_trajectory_queue(self):
        """Get the current trajectory queue.
        
        Returns:
            list: Current trajectory queue
        """
        return self.trajectory_queue
        
    def execute_trajectory(self):
        """Execute cached trajectory points.
        
        This method executes all waypoints in the trajectory queue with
        velocity and acceleration constraints.
        """
        self.robot.set_velocity(self.max_velocity)
        self.robot.set_acceleration(self.max_acceleration)
        
        for wp in self.trajectory_queue:
            # Add minimum execution time guarantee
            start_time = time.time()
            
            self.robot.move_to(wp)  # Assuming this is the low-level control interface
            
            # Calculate actual motion time to prevent overspeed
            elapsed = time.time() - start_time
            min_duration = 0.1  # Minimum execution time per point
            if elapsed < min_duration:
                time.sleep(min_duration - elapsed)
        
        self.trajectory_queue.clear()

def smooth_with_gaussian(actions, sigma=1.5):
    """Smooth action sequences using Gaussian filter for each dimension.
    
    Args:
        actions (numpy.ndarray): Action sequence array
        sigma (float): Standard deviation for Gaussian kernel
        
    Returns:
        numpy.ndarray: Smoothed action sequence
    """
    smoothed_actions = np.zeros_like(actions)
    for i in range(actions.shape[1]): # Apply filter independently for each dimension (each joint/coordinate)
        smoothed_actions[:, i] = gaussian_filter1d(actions[:, i], sigma=sigma, mode='nearest')
        # mode='nearest' handles boundaries to avoid excessive edge effects
    return smoothed_actions

def filter_trajectory(points, window=5):
    """Apply Savitzky-Golay filter to trajectory points.
    
    Args:
        points (numpy.ndarray): Trajectory points array
        window (int): Window size for the filter
        
    Returns:
        numpy.ndarray: Filtered trajectory points
    """
    return savgol_filter(points, window, 3, axis=0)
