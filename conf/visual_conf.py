from ml_collections import ConfigDict


def get_visual_config():
    """Generate configuration for web visual panels."""
    config = ConfigDict()

    config.camera = ConfigDict()
    config.camera.connect_when_running = True
    config.camera.default_open = [False, False, False]
    config.camera.update_interval_ms = 33

    config.trajectory = ConfigDict()
    config.trajectory.default_paused = True
    config.trajectory.default_source = ['state']
    config.trajectory.default_selected_joints = [0, 1, 2, 3]
    config.trajectory.update_interval_ms = 50

    return config
