import os

os.environ["TI5_SDK_SIM"] = "1"

import numpy as np
import pandas as pd
import pytest

from client.robots.ti5_t170c.body_robot import RobotBody
from conf.robots_conf import get_ti5_t170c_config
from ti5_t170c_sdk._dds_bridge import shutdown_bridge


def _body(hand_type="hand"):
    shutdown_bridge()
    config = get_ti5_t170c_config(hand_type)
    config.camera.backend = "mock"
    return RobotBody(config)


def _write_actions(tmp_path, rows):
    path = tmp_path / "actions.parquet"
    pd.DataFrame({"action": rows}).to_parquet(path)
    return path


def test_hand_profile_rejects_short_model_action():
    robot = _body("hand")
    assert robot.action_dim == 26
    assert robot._profile.hand_dof == 12
    robot.control_robot([0] * 26)
    with pytest.raises(ValueError, match="hand") as exc:
        robot.control_robot([0] * 21)
    message = str(exc.value)
    assert "26" in message and "21" in message


def test_mixed_profile_does_not_drive_gripper_from_a_finger():
    robot = _body("lhand_rgripper")
    assert robot.action_dim == 21
    with pytest.raises(ValueError, match="21"):
        robot.control_robot([0] * 26)
    assert robot.robot._endpoints._sim.published == []


def test_legacy_16d_action_is_rejected_by_native_body():
    robot = _body("hand")
    with pytest.raises(ValueError, match=r"26.*16"):
        robot.control_robot(np.zeros(16, dtype=np.float32))


def test_layout_wider_than_profile_is_rejected():
    shutdown_bridge()
    config = get_ti5_t170c_config("lhand_rgripper")
    config.camera.backend = "mock"
    config.action_layout["hand"]["end"] = 26
    with pytest.raises(ValueError, match=r"6\+1"):
        RobotBody(config)


def test_manual_split_keeps_the_unspecified_side():
    robot = _body("lhand_rgripper")
    robot.robot.move_hand([1, 2, 3, 4, 5, 6, 9])
    robot.robot._endpoints._sim.published.clear()
    robot._control_robot({"source": "manual", "l_hand": [1000] * 6})
    hand_cmds = [item for item in robot.robot._endpoints._sim.published if "gripper" in item[0] or "hand" in item[0]]
    assert hand_cmds[-1][0] == "right_gripper_cmd"
    assert hand_cmds[-1][1] == [9.0]
    left = [item[1] for item in hand_cmds if item[0] == "left_hand_angle_cmd"][-1]
    assert left == [1000.0] * 6


def test_replay_lengths(tmp_path):
    robot = _body("hand")
    arm_only = _write_actions(tmp_path, [np.arange(14, dtype=np.float32)])
    loaded = robot.load_action_data(arm_only)
    assert loaded[0].shape == (26,)
    assert np.allclose(loaded[0][:14], np.arange(14))
    assert np.allclose(loaded[0][14:], 1000.0)

    expanded = tmp_path / "expanded.parquet"
    pd.DataFrame({"action": [np.zeros(16, dtype=np.float32)]}).to_parquet(expanded)
    with pytest.raises(ValueError, match=r"6\+6"):
        robot.load_action_data(expanded)

    with_head = tmp_path / "head.parquet"
    frame = np.arange(29, dtype=np.float32)
    pd.DataFrame({"action": [frame]}).to_parquet(with_head)
    kept = robot.load_action_data(with_head)[0]
    assert kept.shape == (29,)
    assert np.allclose(kept[26:], frame[26:])


class _ReplayProbe(RobotBody):
    def __init__(self, hand_type, frame):
        super().__init__(_mock_config(hand_type))
        self._frame = np.asarray(frame, dtype=np.float32)
        self.sent = []

    def load_action_data(self, parquet_path, key="action"):
        return [self._frame]

    def execute_action(self, data):
        self.sent.append(dict(data))


def _mock_config(hand_type):
    shutdown_bridge()
    config = get_ti5_t170c_config(hand_type)
    config.camera.backend = "mock"
    return config


def test_hand_replay_still_sends_head_and_mixed_replay_does_not():
    dexterous = _ReplayProbe("hand", np.arange(29, dtype=np.float32))
    dexterous.replay_trajectories("ignored.parquet", accelerate=False)
    assert any("head" in item for item in dexterous.sent)

    mixed = _ReplayProbe("lhand_rgripper", np.zeros(21, dtype=np.float32))
    mixed.replay_trajectories("ignored.parquet", accelerate=False)
    assert mixed.sent
    assert all(set(item) <= {"arm", "hand"} for item in mixed.sent)
    assert any("hand" in item for item in mixed.sent)
