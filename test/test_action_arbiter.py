import numpy as np

from client.core.action_arbiter import ActionArbiter, ActionSource


def test_arbiter_exposes_latest_teleop_record_without_duplicate_client_state():
    arbiter = ActionArbiter(action_timeout_s=1.0)
    action = np.asarray([1.0, 2.0])

    arbiter.submit(ActionSource.TELEOP, action, timestamp=12.5)

    assert arbiter.last_submitted_at(ActionSource.TELEOP) == 12.5
    np.testing.assert_allclose(arbiter.latest_action(ActionSource.TELEOP), action)
    arbiter.clear_source(ActionSource.TELEOP)
    assert arbiter.last_submitted_at(ActionSource.TELEOP) is None
    assert arbiter.latest_action(ActionSource.TELEOP) is None
