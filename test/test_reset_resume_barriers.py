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
    client.visualize_server = SimpleNamespace(vis_global_step=1, update_chart_data=lambda **_: None)
    client.show_thread_lock = threading.Lock()
    client._last_executed_action = None
    client._last_executed_action_lock = threading.Lock()
    client.teleop_bridge = None

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


def test_teleop_enabled_reset_does_not_hold_pre_reset_action():
    import logging
    import threading
    from queue import Queue
    from types import SimpleNamespace

    from client.core.action_arbiter import ActionArbiter, ActionSource, ActionTransitionFilter
    from client.core.vla_client import VLAClient

    sent = []
    policy = {'action': None}

    class FakeDataManager:
        def get_action_fitted(self):
            return policy['action'], None, None, None

        def get_prob_progress(self):
            return None

        def clear(self):
            policy['action'] = None

    class FakeRobot:
        def control_robot(self, action):
            sent.append(np.asarray(action, dtype=float).copy())

    client = VLAClient.__new__(VLAClient)
    client.logger = logging.getLogger(__name__)
    client._control_execution_lock = threading.Lock()
    client._inference_execution_lock = threading.Lock()
    client.is_control_thread_running = True
    client.realtime_data_manager = FakeDataManager()
    client.robot = FakeRobot()
    client.config = SimpleNamespace(
        record=SimpleNamespace(switch=False),
        language=SimpleNamespace(auto_mode=False),
        controller=SimpleNamespace(period=3.75),
        teleop=SimpleNamespace(use_teleop=True),
    )
    client.visualize_server = SimpleNamespace(vis_global_step=1, update_chart_data=lambda **_: None)
    client.show_thread_lock = threading.Lock()
    client.observe_period = 1.0
    client._raw_observe_queue = Queue(maxsize=2)
    client._raw_observe_shm_cache = {}
    client.image_process_time = 0.0
    client._last_executed_action = None
    client._last_executed_action_lock = threading.Lock()
    client.teleop_bridge = None
    # A zero timeout makes every policy record stale by the next tick, matching
    # the real reset wait, so the pre-fix code falls into the HOLD path.
    client.action_arbiter = ActionArbiter(policy_timeout_s=0.0)
    client.action_transition_filter = ActionTransitionFilter(transition_steps=4)
    client._action_select_last_debug_s = 0.0
    client._teleop_policy_handoff_active = False
    client._teleop_policy_handoff_hold_action = None
    client._teleop_policy_handoff_started_s = None
    client._teleop_outlier_reject_count = 3
    client._policy_generation = 0
    client._policy_generation_lock = threading.Lock()

    pre_reset = np.array([5.0, 5.0])
    policy['action'] = pre_reset
    client._control_thread_fun()
    assert len(sent) == 1 and np.allclose(sent[0], pre_reset)

    client.reset()
    assert client._teleop()._get_last_executed_action() is None
    assert client.action_arbiter.latest_action(ActionSource.POLICY) is None
    assert client._teleop_outlier_reject_count == 0
    assert client._policy_generation == 1

    # Before the first post-reset chunk arrives nothing may be sent: a HOLD of
    # the pre-reset action would drag the arm away from the reset pose.
    client._control_thread_fun()
    assert len(sent) == 1

    # The first fresh chunk is executed as-is, not blended from the old pose.
    fresh = np.array([0.0, 0.0])
    policy['action'] = fresh
    client._control_thread_fun()
    assert len(sent) == 2 and np.allclose(sent[1], fresh)
