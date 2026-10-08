import time

import numpy as np
from ml_collections import ConfigDict

from client.robots.robot_proxy import RobotProxy


def _config():
    return ConfigDict({
        'action_layout': {
            'arm': {'start': 0, 'end': 2, 'policy': 'gradual'},
        },
    })


def test_control_robot_is_non_blocking_and_keeps_latest_action():
    proxy = RobotProxy(
        'mock',
        _config(),
        robot_module='test_proxy_robot',
        startup_timeout=5.0,
    )
    try:
        started = time.perf_counter()
        for value in range(30):
            proxy.control_robot(np.array([value, value], dtype=np.float32))
        elapsed = time.perf_counter() - started

        # The fake observation blocks for 20 ms. The old synchronous RPC path
        # needed roughly 600 ms for this loop; submission must now stay local.
        assert elapsed < 0.1

        deadline = time.monotonic() + 2.0
        actions = []
        while time.monotonic() < deadline:
            actions = proxy.get_control_actions()
            if actions and actions[-1] == [29.0, 29.0]:
                break
            time.sleep(0.01)
        assert actions[-1] == [29.0, 29.0]

        # Explicit/manual commands retain their synchronous return semantics.
        assert proxy.execute_action({'arm': [1.0, 2.0]}) == 'exec-ok'
    finally:
        proxy.close()


def test_async_control_error_is_reported_on_next_submission():
    proxy = RobotProxy(
        'mock',
        _config(),
        robot_module='test_proxy_robot',
        startup_timeout=5.0,
    )
    try:
        proxy.control_robot(np.array([-999.0, 0.0], dtype=np.float32))
        # Let the dedicated control worker execute the injected failing action;
        # immediately submitting a replacement is allowed to coalesce it away.
        time.sleep(0.1)
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            try:
                proxy.control_robot(np.zeros(2, dtype=np.float32))
            except RuntimeError as exc:
                assert 'injected control failure' in str(exc)
                break
            time.sleep(0.01)
        else:
            raise AssertionError('asynchronous control failure was not reported')
    finally:
        proxy.close()
