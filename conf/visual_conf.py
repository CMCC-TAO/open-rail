from ml_collections import ConfigDict


def get_visual_config():
    """Generate configuration for web visual panels."""
    config = ConfigDict()

    config.camera = ConfigDict()
    config.camera.open_head = True
    config.camera.open_wrist_left = True
    config.camera.open_wrist_right = True
    config.camera.update_interval_ms = 33

    config.trajectory = ConfigDict()
    config.trajectory.play = False
    config.trajectory.source = ['State']
    config.trajectory.selected_joints = [0, 1, 2, 3]
    config.trajectory.update_interval_ms = 50

    return config
