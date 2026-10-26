import json
from types import SimpleNamespace

import numpy as np

from teleop.action_mapping import action_layout_for_robot
from teleop.quest3 import quest3


def test_teleop_status_file_is_written_atomically(tmp_path):
    status_path = tmp_path / "quest3_status.json"

    quest3._write_teleop_status(
        status_path,
        state="connected",
        connected=True,
        port=8002,
        remote="127.0.0.1:54321",
    )

    payload = json.loads(status_path.read_text(encoding="utf-8"))
    assert payload["state"] == "connected"
    assert payload["connected"] is True
    assert payload["port"] == 8002
    assert payload["remote"] == "127.0.0.1:54321"
    assert list(tmp_path.glob(".*.tmp")) == []


class _Logger:
    def __init__(self):
        self.info_messages = []
        self.warning_messages = []

    def info(self, message):
        self.info_messages.append(message)

    def warning(self, message):
        self.warning_messages.append(message)


def _make_node():
    node = object.__new__(quest3.VRWholeBodyBridgeNode)
    node.node = SimpleNamespace(get_logger=lambda: node.logger)
    node.state = quest3.BridgeState()
    node.robot_action_layout = action_layout_for_robot("ti5_t170c")
    node.joint_names = list(node.robot_action_layout.action_names[:16])
    node.left_hand_feedback_names = list(node.robot_action_layout.left_hand_names)
    node.right_hand_feedback_names = list(node.robot_action_layout.right_hand_names)
    node.joint_state_optional_names = set(
        node.left_hand_feedback_names + node.right_hand_feedback_names
    )
    node.left_gripper_control_mode = "incremental"
    node.right_gripper_control_mode = "incremental"
    node.left_hand_range = ([1000.0] * 6, [0.0, 0.0, 0.0, 0.0, 0.0, 1000.0])
    node.right_hand_range = node.left_hand_range
    node.left_discrete_values = []
    node.right_discrete_values = []
    node.left_hand_slice = slice(14, 15)
    node.right_hand_slice = slice(15, 16)
    node.reset_action = np.array([0.25] * 14 + [1.0, 1.0])
    node._reported_missing_hand_feedback = False
    node._last_invalid_joint_state_warn_s = 0.0
    node.logger = _Logger()
    return node


def test_missing_optional_hand_joints_do_not_drop_arm_feedback():
    node = _make_node()
    arm_names = node.joint_names[:14]
    msg = SimpleNamespace(
        name=arm_names,
        position=[float(index) for index in range(14)],
    )

    node._joint_state_cb(msg)

    assert node.state.joint_state_ready is True
    np.testing.assert_allclose(node.state.reference_action[:14], np.arange(14))
    np.testing.assert_allclose(node.state.reference_action[14:], [1.0, 1.0])
    assert node.logger.warning_messages == []
    assert len(node.logger.info_messages) == 1


def test_missing_required_arm_joint_still_drops_feedback():
    node = _make_node()
    msg = SimpleNamespace(
        name=node.joint_names[1:14],
        position=[float(index) for index in range(13)],
    )

    node._joint_state_cb(msg)

    assert node.state.joint_state_ready is False
    assert node.logger.warning_messages
    assert "missing joints" in node.logger.warning_messages[0]


def test_named_native_feedback_feeds_reference_action():
    node = _make_node()
    left_hand = [500.0] * 5 + [1000.0]
    right_hand = [500.0] * 5 + [1000.0]
    msg = SimpleNamespace(
        name=list(node.robot_action_layout.action_names),
        position=[float(index) for index in range(14)] + left_hand + right_hand,
    )

    node._joint_state_cb(msg)

    assert node.state.joint_state_ready is True
    np.testing.assert_allclose(node.state.reference_action[:14], np.arange(14))
    np.testing.assert_allclose(node.state.reference_action[14:], [0.5, 0.5])
    assert node.logger.warning_messages == []


def test_arm_teleop_without_hand_input_holds_reference_hand():
    node = object.__new__(quest3.VRWholeBodyBridgeNode)
    node.state = quest3.BridgeState()
    node.state.joint_state_ready = True
    node.state.left.pose_valid = True
    node.state.left.trigger = 1.0
    node.state.reference_action[14:] = [0.0, 0.0]
    node.state.action[14:] = [1.0, 1.0]
    node.trigger_threshold = 0.9
    node.left_gripper_control_mode = "incremental"
    node.right_gripper_control_mode = "incremental"
    node.left_discrete_values = []
    node.right_discrete_values = []
    node.left_hand_slice = slice(14, 15)
    node.right_hand_slice = slice(15, 16)
    node.min_action = np.full(16, -np.inf)
    node.max_action = np.full(16, np.inf)
    node._update_reset_edge_locked = lambda: None
    node._next_reset_action_locked = lambda: None
    node._update_arm_locked = lambda side, arm_slice: None
    node._update_gripper_locked = lambda side, index: None
    node._is_gripper_control_requested = lambda side: False
    published = []
    node._publish_joint_command = lambda action: published.append(np.asarray(action).copy())

    node._tick()

    assert len(published) == 1
    np.testing.assert_allclose(published[0][14:], [0.0, 0.0])


def test_releasing_hand_control_holds_last_hand_command():
    node = object.__new__(quest3.VRWholeBodyBridgeNode)
    node.state = quest3.BridgeState()
    node.state.joint_state_ready = True
    node.state.left.pose_valid = True
    node.state.left.trigger = 1.0
    node.state.left.gripper_command_initialized = True
    node.state.right.gripper_command_initialized = True
    node.state.reference_action[14:] = [0.0, 0.0]
    node.state.action[14:] = [1.0, 0.25]
    node.trigger_threshold = 0.9
    node.left_gripper_control_mode = "incremental"
    node.right_gripper_control_mode = "incremental"
    node.left_discrete_values = []
    node.right_discrete_values = []
    node.left_hand_slice = slice(14, 15)
    node.right_hand_slice = slice(15, 16)
    node.min_action = np.full(16, -np.inf)
    node.max_action = np.full(16, np.inf)
    node._update_reset_edge_locked = lambda: None
    node._next_reset_action_locked = lambda: None
    node._update_arm_locked = lambda side, arm_slice: None
    node._update_gripper_locked = lambda side, index: None
    node._is_gripper_control_requested = lambda side: False
    published = []
    node._publish_joint_command = lambda action: published.append(np.asarray(action).copy())

    node._tick()

    assert len(published) == 1
    np.testing.assert_allclose(published[0][14:], [1.0, 0.25])


def test_discrete_hand_control_uses_trigger_and_secondary_rising_edges():
    node = object.__new__(quest3.VRWholeBodyBridgeNode)
    node.state = quest3.BridgeState()
    node.state.action = np.zeros(26)
    node.state.reference_action = np.zeros(26)
    node.grip_threshold = 0.9
    node.left_hand_slice = slice(14, 20)
    side = node.state.left
    values = [
        [1000.0] * 6,
        [500.0, 500.0, 500.0, 500.0, 500.0, 1000.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 1000.0],
    ]

    assert node._update_discrete_gripper_locked(side, node.left_hand_slice, values) is False

    side.grip = 1.0
    assert node._update_discrete_gripper_locked(side, node.left_hand_slice, values) is True
    assert side.discrete_index == 0
    np.testing.assert_allclose(node.state.action[14:20], [1000.0] * 6)
    node.state.reference_action[14:20] = [1000.0] * 6

    assert node._update_discrete_gripper_locked(side, node.left_hand_slice, values) is False
    side.grip = 0.0
    assert node._update_discrete_gripper_locked(side, node.left_hand_slice, values) is False
    side.grip = 1.0
    assert node._update_discrete_gripper_locked(side, node.left_hand_slice, values) is True
    assert side.discrete_index == 1
    np.testing.assert_allclose(node.state.action[14:20], [500.0, 500.0, 500.0, 500.0, 500.0, 1000.0])
    node.state.reference_action[14:20] = [500.0, 500.0, 500.0, 500.0, 500.0, 1000.0]

    side.grip = 0.0
    node._update_discrete_gripper_locked(side, node.left_hand_slice, values)
    side.grip = 1.0
    node._update_discrete_gripper_locked(side, node.left_hand_slice, values)
    assert side.discrete_index == 2
    node.state.reference_action[14:20] = [0.0, 0.0, 0.0, 0.0, 0.0, 1000.0]
    side.grip = 0.0
    node._update_discrete_gripper_locked(side, node.left_hand_slice, values)
    side.grip = 1.0
    node._update_discrete_gripper_locked(side, node.left_hand_slice, values)
    assert side.discrete_index == 0
    node.state.reference_action[14:20] = [1000.0] * 6

    side.grip = 0.0
    node._update_discrete_gripper_locked(side, node.left_hand_slice, values)
    side.secondary_button = True
    assert node._update_discrete_gripper_locked(side, node.left_hand_slice, values) is True
    assert side.discrete_index == 2
    np.testing.assert_allclose(node.state.action[14:20], [0.0, 0.0, 0.0, 0.0, 0.0, 1000.0])


def test_discrete_feedback_selects_nearest_full_hand_vector():
    values = [
        [1000.0] * 6,
        [500.0, 500.0, 500.0, 500.0, 500.0, 1000.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 1000.0],
    ]

    assert quest3.VRWholeBodyBridgeNode._nearest_discrete_index(values, [900.0] * 5 + [1000.0]) == 0
    assert quest3.VRWholeBodyBridgeNode._nearest_discrete_index(values, [480.0] * 5 + [1000.0]) == 1
    assert quest3.VRWholeBodyBridgeNode._nearest_discrete_index(values, [20.0] * 5 + [1000.0]) == 2


def test_discrete_feedback_sets_current_action_to_nearest_vectors():
    node = object.__new__(quest3.VRWholeBodyBridgeNode)
    node.node = SimpleNamespace(get_logger=lambda: node.logger)
    node.state = quest3.BridgeState()
    node.robot_action_layout = action_layout_for_robot("ti5_t170c")
    node.state.action = np.zeros(26)
    node.state.reference_action = np.zeros(26)
    node.left_gripper_control_mode = "discrete"
    node.right_gripper_control_mode = "discrete"
    node.left_hand_range = None
    node.right_hand_range = None
    node.left_hand_feedback_names = [f"left_hand_joint{i}" for i in range(1, 7)]
    node.right_hand_feedback_names = [f"right_hand_joint{i}" for i in range(1, 7)]
    node.left_hand_slice = slice(14, 20)
    node.right_hand_slice = slice(20, 26)
    node.joint_names = list(node.robot_action_layout.action_names)
    node.joint_state_optional_names = set(
        node.left_hand_feedback_names + node.right_hand_feedback_names
    )
    node._reported_missing_hand_feedback = False
    node._last_invalid_joint_state_warn_s = 0.0
    node.logger = _Logger()
    node.reset_action = np.zeros(26)
    node.left_discrete_values = [
        [1000.0] * 6,
        [500.0, 500.0, 500.0, 500.0, 500.0, 1000.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 1000.0],
    ]
    node.right_discrete_values = node.left_discrete_values
    positions = [0.0] * 26
    positions[14:20] = [480.0, 480.0, 480.0, 480.0, 480.0, 1000.0]
    positions[20:26] = [20.0, 20.0, 20.0, 20.0, 20.0, 1000.0]
    msg = SimpleNamespace(
        name=list(node.robot_action_layout.action_names),
        position=positions,
    )

    node._joint_state_cb(msg)

    assert node.state.left.discrete_index == 1
    assert node.state.right.discrete_index == 2
    np.testing.assert_allclose(node.state.action[14:20], node.left_discrete_values[1])
    np.testing.assert_allclose(node.state.action[20:26], node.right_discrete_values[2])


def test_proportional_hand_control_uses_hysteresis_and_holds_on_release():
    node = object.__new__(quest3.VRWholeBodyBridgeNode)
    node.state = quest3.BridgeState()
    node.left_gripper_control_mode = "proportional"
    node.right_gripper_control_mode = "proportional"
    node.gripper_input_min = 0.0
    node.gripper_input_max = 1.0
    node.proportional_activation_threshold = 0.05
    node.proportional_release_threshold = 0.02
    node.proportional_latch_on_release = True
    node.gripper_command_min = 0.0
    node.gripper_command_max = 1.0
    side = node.state.left

    side.grip = 0.03
    assert node._is_gripper_control_requested(side) is False
    side.grip = 0.06
    assert node._is_gripper_control_requested(side) is True

    side.gripper_control_active = True
    side.gripper_command_initialized = True
    side.grip = 0.03
    assert node._is_gripper_control_requested(side) is True

    node.state.action[14] = 0.4
    side.grip = 0.01
    node._update_gripper_locked(side, 14)
    assert node._is_gripper_control_requested(side) is False
    assert side.gripper_control_active is False
    assert node.state.action[14] == 0.4


def test_proportional_hand_release_latches_reached_action():
    node = object.__new__(quest3.VRWholeBodyBridgeNode)
    node.state = quest3.BridgeState()
    node.left_gripper_control_mode = "proportional"
    node.right_gripper_control_mode = "proportional"
    node.gripper_input_min = 0.0
    node.gripper_input_max = 1.0
    node.proportional_activation_threshold = 0.05
    node.proportional_release_threshold = 0.02
    node.proportional_latch_on_release = True
    node.gripper_command_min = 0.0
    node.gripper_command_max = 1.0
    side = node.state.left

    side.grip = 1.0
    node._update_gripper_locked(side, 14)
    assert side.gripper_control_active is True
    assert side.proportional_hold_action == 1.0
    assert node.state.action[14] == 1.0

    side.grip = 0.01
    node._update_gripper_locked(side, 14)

    assert side.gripper_control_active is False
    assert node.state.action[14] == 1.0
    assert side.proportional_hold_action is None


def test_arm_exit_cleanup_does_not_reset_hand_hold_state():
    side = quest3.ControllerSide()
    side.control_state = quest3.ARM_CONTROL_TRANSITION_EXIT
    side.gripper_control_active = False
    side.gripper_command_initialized = True
    side.discrete_index = 2

    quest3.VRWholeBodyBridgeNode._clear_arm_control_refs_locked(side)

    assert side.control_state == quest3.ARM_CONTROL_AUTO
    assert side.gripper_command_initialized is True
    assert side.discrete_index == 2

    quest3.VRWholeBodyBridgeNode._clear_hand_control_state_locked(side)

    assert side.gripper_command_initialized is False
    assert side.discrete_index == -1


def test_exit_finish_updates_inactive_arm_reference_to_final_command():
    node = object.__new__(quest3.VRWholeBodyBridgeNode)
    node.state = quest3.BridgeState()
    node.state.reference_action = np.zeros(14)
    final_command = np.arange(7, 14, dtype=float) + 20.0
    node.state.action = np.concatenate([np.zeros(7), final_command])
    node.trigger_release_threshold = 0.75
    node.controller_transforms = {"right": object(), "base": object()}
    node.ik = SimpleNamespace(solve=lambda *args: final_command.copy())
    node._advance_arm_transition_locked = lambda side: True

    side = node.state.right
    side.control_state = quest3.ARM_CONTROL_TRANSITION_EXIT
    side.pose_valid = True
    side.pose_pos = np.zeros(3)
    side.pose_quat = np.array([0.0, 0.0, 0.0, 1.0])
    side.trigger = 0.0
    side.trigger_ref_pos = np.zeros(3)
    side.trigger_ref_quat = np.array([0.0, 0.0, 0.0, 1.0])
    side.trigger_ref_action = np.zeros(7)
    side.trigger_ref_ee_pose = np.zeros(7)

    node._update_arm_locked(side, slice(7, 14))

    assert side.control_state == quest3.ARM_CONTROL_AUTO
    np.testing.assert_allclose(node.state.reference_action[7:14], final_command)


def test_retrigger_during_exit_preserves_current_arm_command():
    node = object.__new__(quest3.VRWholeBodyBridgeNode)
    node.state = quest3.BridgeState()
    node.state.reference_action = np.zeros(14)
    current_command = np.arange(7, 14, dtype=float) + 10.0
    node.state.action = np.concatenate([np.zeros(7), current_command])
    side = node.state.right
    side.control_state = quest3.ARM_CONTROL_TRANSITION_EXIT
    side.pose_valid = True
    side.pose_pos = np.array([0.1, 0.2, 0.3])
    side.pose_quat = np.array([0.0, 0.0, 0.0, 1.0])

    node._start_arm_intervention_locked(
        "right",
        side,
        slice(7, 14),
        reference_pose=np.zeros(7),
    )

    assert side.control_state == quest3.ARM_CONTROL_MANUAL
    np.testing.assert_allclose(node.state.action[7:14], current_command)
    np.testing.assert_allclose(side.trigger_ref_action, current_command)


def test_inactive_arm_uses_released_reference_while_other_arm_stays_active():
    node = object.__new__(quest3.VRWholeBodyBridgeNode)
    node.state = quest3.BridgeState()
    node.state.joint_state_ready = True
    node.state.left.pose_valid = True
    node.state.left.trigger = 1.0
    released_right = np.arange(7, 14, dtype=float) + 30.0
    node.state.reference_action[7:14] = released_right
    node.state.action[7:14] = np.zeros(7)
    node.trigger_threshold = 0.9
    node.left_gripper_control_mode = "incremental"
    node.right_gripper_control_mode = "incremental"
    node.left_discrete_values = []
    node.right_discrete_values = []
    node.left_hand_slice = slice(14, 15)
    node.right_hand_slice = slice(15, 16)
    node.min_action = np.full(16, -np.inf)
    node.max_action = np.full(16, np.inf)
    node._update_reset_edge_locked = lambda: None
    node._next_reset_action_locked = lambda: None
    node._update_arm_locked = lambda side, arm_slice: None
    node._update_gripper_locked = lambda side, index: None
    node._is_gripper_control_requested = lambda side: False
    published = []
    node._publish_joint_command = lambda action: published.append(np.asarray(action).copy())

    node._tick()

    assert len(published) == 1
    np.testing.assert_allclose(published[0][7:14], released_right)
