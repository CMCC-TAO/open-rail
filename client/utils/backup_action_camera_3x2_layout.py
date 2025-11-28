import os
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import pyqtgraph as pg

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Disable OpenGL for better compatibility
pg.setConfigOptions(useOpenGL=False)

def raw_filter(x, y):
    """
    Filter data to keep only changing data points
    Args:
        x: x-axis data
        y: y-axis data
    Returns:
        Filtered x and y data
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    # Create mask to mark changing data points
    mask = np.ones(len(y), dtype=bool)
    mask[1:] = y[1:] != y[:-1]  # Compare current value with previous value
    return x[mask], y[mask]

def main():
    # Create Qt application instance
    app = QApplication([])
    # Create graphics layout window for VLA visualization interface
    window = pg.GraphicsLayoutWidget(show=True, title="VLA Visualization")
    # Set window size to 1200x800 pixels
    window.resize(1200, 800)

    # Import required modules and classes
    import cv2
    from conf.server_conf import get_vis_server_config
    from server.core.vis_server import VISServer
    from server.core.zmq_server import ZMQServer
    
    # Get visualization server configuration
    config = get_vis_server_config()
    # Create ZMQ server instance
    zmq_server = ZMQServer(config.zmq)
    # Create visualization server instance
    vis_server = VISServer(config, zmq_server)
    # Start visualization server
    vis_server.run()
    print("VISServer started.")

    # ---------------- Set column width ratios ----------------
    # Set left image column width to 1, right curve column width to 2
    window.ci.layout.setColumnStretchFactor(0, 1)
    window.ci.layout.setColumnStretchFactor(1, 2)

    # ---------------- Left 3 images ----------------
    # Create list for image display items
    image_items = []
    # Create 3 view boxes for image display
    for i in range(3):
        view_box = window.addViewBox(row=i, col=0)
        # Lock aspect ratio to prevent image distortion
        view_box.setAspectLocked(True)
        # Create image item and add to view box
        image_item = pg.ImageItem()
        view_box.addItem(image_item)
        image_items.append(image_item)

    # ---------------- Right 3 action curves ----------------
    # Create lists for raw and fitted curves
    raw_curves, fitted_curves = [], []
    # Create 3 plots for action curve display
    for i in range(3):
        # Add plot to specified position
        plot = window.addPlot(row=i, col=1, title=f"Action {i}")
        # Show grid lines
        plot.showGrid(x=True, y=True, alpha=0.3)
        # Create red raw curve (width 2)
        raw_curve = plot.plot(pen=pg.mkPen('r', width=2))
        # Create green fitted curve (width 3)
        fitted_curve = plot.plot(pen=pg.mkPen('g', width=3))
        raw_curves.append(raw_curve)
        fitted_curves.append(fitted_curve)

    # ---------------- Timer update function ----------------
    def update_ui():
        """
        Timer function to update user interface
        """
        # Get latest data from visualization server
        images, action_fitted, action_raw = vis_server.get_latest_data()
        if images is None:
            return

        # Update image display
        for i, (key, img) in enumerate(list(images.items())[:3]):
            # Check if image data is valid
            if img is not None and img.ndim == 3:
                # Transpose and flip image for correct display
                image_items[i].setImage(np.transpose(np.flipud(img), (1,0,2)))

        # Update action curves, select one joint from each arm and one gripper
        if action_raw is not None and len(action_raw) > 0:
            # Convert action data to numpy arrays
            raw_array = np.array(action_raw)
            fitted_array = np.array(action_fitted)
            # Get minimum length of data
            min_length = min(len(raw_array), len(fitted_array))
            x_axis = np.arange(min_length)

            # Update first action curve (index 14)
            x_filtered, y_filtered = raw_filter(x_axis, raw_array[:min_length, 14])
            raw_curves[0].setData(x_filtered, y_filtered)
            fitted_curves[0].setData(x_axis, fitted_array[:min_length, 14])
            
            # Update second action curve (index 6)
            x_filtered, y_filtered = raw_filter(x_axis, raw_array[:min_length, 6])
            raw_curves[1].setData(x_filtered, y_filtered)
            fitted_curves[1].setData(x_axis, fitted_array[:min_length, 6])

            # Update third action curve (index 13)
            x_filtered, y_filtered = raw_filter(x_axis, raw_array[:min_length, 13])
            raw_curves[2].setData(x_filtered, y_filtered)
            fitted_curves[2].setData(x_axis, fitted_array[:min_length, 13])

    # Create timer to update interface every 30 milliseconds
    timer = QTimer()
    timer.timeout.connect(update_ui)
    timer.start(30)

    try:
        # Start application event loop
        sys.exit(app.exec_())
    finally:
        # Close visualization server on program exit
        vis_server.close()
        print("VISServer shutdown.")

# Program entry point
if __name__ == "__main__":
    main()
    