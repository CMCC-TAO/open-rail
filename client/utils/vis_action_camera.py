import sys
import os
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QComboBox, QGraphicsProxyWidget, QWidget, QHBoxLayout
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from PyQt5.QtCore import Qt

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

pg.setConfigOptions(useOpenGL=False)

def raw_filter(x, y):
    """Remove consecutive duplicate values"""
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    mask = np.ones(len(y), dtype=bool)
    mask[1:] = y[1:] != y[:-1]
    return x[mask], y[mask]

def main():
    app = QApplication([])
    win = pg.GraphicsLayoutWidget(show=True, title="Real-Time VLA action-camera Visualization")
    win.resize(1200, 800)

    # ---------------- Server initialization ----------------
    import cv2
    from conf.server_conf import get_vis_server_config
    from server.core.vis_server import VISServer
    from server.core.zmq_server import ZMQServer

    config = get_vis_server_config()
    zmq_server = ZMQServer(config.zmq)
    vis_server = VISServer(config, zmq_server)
    vis_server.run()
    print("VISServer started.")

    # ---------------- Adaptive row/column layout ----------------
    win.ci.layout.setColumnStretchFactor(0, 4)
    win.ci.layout.setColumnStretchFactor(1, 7)
    win.ci.layout.setRowStretchFactor(0, 3)
    win.ci.layout.setRowStretchFactor(1, 2)

    # ---------------- Image areas with top-centered labels ----------------
    img_plots = []
    img_items = []
    img_labels = ["Top Head Camera", "Left Wrist Camera", "Right Wrist Camera"]
    top_margin = 10  # pixels from top

    for i, (r, c) in enumerate([(0,0), (1,0), (1,1)]):
        p_img = win.addPlot(row=r, col=c)
        p_img.hideAxis('bottom')
        p_img.hideAxis('left')
        p_img.setMouseEnabled(x=False, y=False)
        p_img.setMenuEnabled(False)
        p_img.setAspectLocked(False)

        img_item = pg.ImageItem()
        p_img.addItem(img_item)

        # Add top-centered label
        label = pg.TextItem(text=img_labels[i], color='w', anchor=(0.5,0))
        label.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        p_img.addItem(label)

        # Update label position on resize
        def update_label(vb, item=img_item, lbl=label):
            rect = vb.viewRect()
            lbl.setPos(rect.center().x(), rect.top() + top_margin)

        p_img.getViewBox().sigResized.connect(update_label)

        img_plots.append(p_img)
        img_items.append(img_item)

    # ---------------- Action curve area ----------------
    curve_raws, curve_fits = [], []
    p = win.addPlot(row=0, col=1, title="Action Trajectory")
    p.showGrid(x=True, y=True, alpha=0.3)

    legend = pg.LegendItem(offset=(-10, -10))
    legend.setParentItem(p.graphicsItem())
    legend.setColumnCount(2)

    cr1 = p.plot(pen=pg.mkPen('r', width=2))
    cf1 = p.plot(pen=pg.mkPen('g', width=3))
    cr2 = p.plot(pen=pg.mkPen('b', width=2))
    cf2 = p.plot(pen=pg.mkPen('y', width=3))

    curve_raws.extend([cr1, cr2])
    curve_fits.extend([cf1, cf2])

    # ---------------- Single action selection widget (7 joint pairs + grippers) ----------------
    joint_pairs = [
        (0, 7),
        (1, 8),
        (2, 9),
        (3, 10),
        (4, 11),
        (5, 12),
        (6, 13),
        (14, 15)  # Grippers
    ]
    combo = QComboBox()
    for i in range(len(joint_pairs)):
        if i < 7:
            combo.addItem(f"Joint Pair:(L{i}, R{i+7})")
        else:
            combo.addItem("Grippers:(L14, R15)")
    combo.setCurrentIndex(6)
    combo.setFixedWidth(200)
    combo.setMaxVisibleItems(8)
    combo.setView(QtWidgets.QListView())

    container = QWidget()
    h_layout = QHBoxLayout()
    h_layout.setContentsMargins(40, 0, 0, 0)  # Left margin 40px
    h_layout.setSpacing(15)
    h_layout.addStretch(1)
    h_layout.addWidget(combo)
    h_layout.addStretch(1)
    container.setLayout(h_layout)
    container.setAttribute(Qt.WA_TranslucentBackground)

    proxy = QGraphicsProxyWidget()
    proxy.setWidget(container)
    p.layout.addItem(proxy, 1, 0, 1, p.layout.columnCount())

    current_indices = [0, 0]  # Store current left and right arm indices

    # ---------------- Periodic update ----------------
    def update_ui():
        imgs, action_fitted, action_raw = vis_server.get_latest_data()
        if imgs is None:
            return

        # Update images
        for i, (p_img, img_item) in enumerate(zip(img_plots, img_items)):
            if i >= len(imgs):
                continue
            img = list(imgs.values())[i]
            if img is not None and img.ndim == 3:
                img = img[120:-120, :, :]
                img = np.transpose(np.flipud(img), (1, 0, 2))  # Keep flip and transpose (optional)
                img_item.setImage(img)
                rect = p_img.getViewBox().viewRect()

                # Update image position & size
                img_item.setRect(rect)

                # Update label position
                for item in p_img.items:
                    if isinstance(item, pg.TextItem):
                        item.setPos(rect.center().x(), rect.top() + top_margin)


        # Update action curves
        if action_raw is not None and len(action_raw) > 0:
            raw_arr = np.array(action_raw)
            fit_arr = np.array(action_fitted)
            min_len = min(len(raw_arr), len(fit_arr))
            x = np.arange(min_len)

            # Get left/right indices from single combo widget
            pair_idx = combo.currentIndex()
            idx1, idx2 = joint_pairs[pair_idx]

            # Update legend if selection changed
            if current_indices[0] != idx1 or current_indices[1] != idx2:
                current_indices[0] = idx1
                current_indices[1] = idx2
                legend.clear()
                legend.addItem(curve_raws[0], f"L{idx1:02d} (VLA Raw Ouput)")
                legend.addItem(curve_fits[0], f"L{idx1:02d} (Optimized)")
                legend.addItem(curve_raws[1], f"R{idx2:02d} (VLA Raw Ouput)")
                legend.addItem(curve_fits[1], f"R{idx2:02d} (Optimized)")

            if min_len > 0:
                x1, y1 = raw_filter(x, raw_arr[:min_len, idx1])
                curve_raws[0].setData(x1, y1)
                curve_fits[0].setData(x, fit_arr[:min_len, idx1])

                x2, y2 = raw_filter(x, raw_arr[:min_len, idx2])

                # Set direction for grippers or regular joints
                if pair_idx == 7:
                    # Grippers move in same direction
                    curve_raws[1].setData(x2, 0.001+y2)
                    curve_fits[1].setData(x, 0.001+-fit_arr[:min_len, idx2])
                else:
                    # Regular left/right joints move in opposite directions
                    curve_raws[1].setData(x2, -1*y2)
                    curve_fits[1].setData(x, -1*fit_arr[:min_len, idx2])

    timer = QTimer()
    timer.timeout.connect(update_ui)
    timer.start(30)

    # Force autoRange for all image areas initially
    QtCore.QTimer.singleShot(100, lambda: [p.getViewBox().autoRange() for p in img_plots])

    try:
        sys.exit(app.exec_())
    finally:
        vis_server.close()
        print("Real-Time VLA action-camera visualization service shutdown.")

if __name__ == "__main__":
    main()
