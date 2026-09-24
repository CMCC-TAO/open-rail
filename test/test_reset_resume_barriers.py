import time

import numpy as np
from ml_collections import ConfigDict

from client.core.realtime_data_manager import RealtimeDataManager
from client.robots.robot_proxy import RobotProxy


def test_reset_rejects_observations_published_before_barrier():
    manager = RealtimeDataManager(ConfigDict({
        'max_len': 10,
        'observe_fps_window_size': 2,
    }))
    old_publish_time = time.perf_counter()
    manager.clear()

    assert not manager.add_observe_data({'frame': 'old'}, source_time=old_publish_time)
    assert manager.frame_count == 0
    for index in range(5):
        assert manager.add_observe_data({'frame': index}, source_time=time.perf_counter())
        assert manager.pop_observe_data() is None
    assert manager.add_observe_data({'frame': 'new'}, source_time=time.perf_counter())
    assert manager.pop_observe_data() == {'frame': 'new'}


def test_worker_rejects_action_from_before_reset_even_if_queued_later():
    proxy = RobotProxy(
        'mock',
        ConfigDict({'action_layout': {'arm': {'start': 0, 'end': 2, 'policy': 'gradual'}}}),
        robot_module='test_proxy_robot',
        startup_timeout=5.0,
    )
    try:
        old_epoch = proxy._control_epoch.value
        proxy.pause_controls()
        assert proxy.reset_robot() == 'reset:default'
        proxy.resume_controls()

        # Simulate multiprocessing.Queue's feeder publishing a pre-reset item
        # only after clear_control_actions() and the physical reset return.
        proxy._control_queue.put((old_epoch, np.array([99, 99], dtype=np.float32)))
        time.sleep(0.1)
        assert [99.0, 99.0] not in proxy.get_control_actions()

        proxy.control_robot(np.array([1, 1], dtype=np.float32))
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            if [1.0, 1.0] in proxy.get_control_actions():
                break
            time.sleep(0.01)
        assert [1.0, 1.0] in proxy.get_control_actions()
        assert [99.0, 99.0] not in proxy.get_control_actions()

        fresh_epoch = proxy._control_epoch.value
        proxy._control_queue.put((fresh_epoch, np.array([2, 2], dtype=np.float32)))
        proxy._control_queue.put((old_epoch, np.array([98, 98], dtype=np.float32)))
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            if [2.0, 2.0] in proxy.get_control_actions():
                break
            time.sleep(0.01)
        assert [2.0, 2.0] in proxy.get_control_actions()
        assert [98.0, 98.0] not in proxy.get_control_actions()
    finally:
        proxy.close()


def test_control_timer_cannot_submit_an_old_action_after_pause():
    import logging
    import threading
    from types import SimpleNamespace

    from client.core.vla_client import VLAClient

    entered = threading.Event()
    release = threading.Event()
    events = []

    class BlockingDataManager:
        def get_action_fitted(self):
            entered.set()
            assert release.wait(timeout=2)
            return np.array([7.0]), None, None, None

        def get_prob_progress(self):
            return None

        def interrupt_wait_for_next(self):
            pass

    class FakeRobot:
        def control_robot(self, action):
            events.append(('action', float(action[0])))

        def pause_controls(self):
            events.append(('paused', None))

    client = VLAClient.__new__(VLAClient)
    client.logger = logging.getLogger(__name__)
    client._control_execution_lock = threading.Lock()
    client.is_control_thread_running = True
    client.is_observe_thread_running = False
    client.is_inference_thread_running = False
    client.realtime_data_manager = BlockingDataManager()
    client.robot = FakeRobot()
    client.config = SimpleNamespace(
        record=SimpleNamespace(switch=False),
        language=SimpleNamespace(auto_mode=False),
        controller=SimpleNamespace(period=3.75),
    )
    client.visualize_server = SimpleNamespace(vis_global_step=1)
    client.show_thread_lock = threading.Lock()

    tick = threading.Thread(target=client._control_thread_fun)
    tick.start()
    assert entered.wait(timeout=1)
    pause = threading.Thread(target=client.stop_control)
    pause.start()
    release.set()
    tick.join(timeout=2)
    pause.join(timeout=2)
    assert not tick.is_alive() and not pause.is_alive()
    assert events == [('action', 7.0), ('paused', None)]
