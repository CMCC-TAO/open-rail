from types import SimpleNamespace

import numpy as np
import pytest

from teleop import hand_mapping
from teleop.action_mapping import action_layout_for_robot, action_layout_from_robot_config
from conf.robots_conf import get_ti5_t170c_config
from teleop.quest3 import quest3


PARTIAL_RANGE = [
    [0.0, 0.0, 1000.0, 1000.0, 0.0, 0.0],
    [1000.0, 0.0, 1000.0, 1000.0, 0.0, 1000.0],
]
RIGHT_GRIPPER_RANGE = [[1000.0], [0.0]]


def test_partial_hand_range_only_moves_changing_joints():
    hand_range = hand_mapping.normalize_hand_range(PARTIAL_RANGE, name="left_hand_range")

    assert hand_mapping.expand_hand_scalar(0.0, hand_range) == PARTIAL_RANGE[0]
    assert hand_mapping.expand_hand_scalar(1.0, hand_range) == PARTIAL_RANGE[1]
    assert hand_mapping.expand_hand_scalar(0.25, hand_range) == [250.0, 0.0, 1000.0, 1000.0, 0.0, 250.0]
    assert hand_mapping.expand_hand_scalar(2.0, hand_range) == PARTIAL_RANGE[1]


def test_hand_range_projection_inverts_expansion():
    hand_range = hand_mapping.normalize_hand_range(PARTIAL_RANGE, name="left_hand_range")

    for alpha in (0.0, 0.3, 1.0):
        native = hand_mapping.expand_hand_scalar(alpha, hand_range)
        assert hand_mapping.project_hand_vector(native, hand_range) == pytest.approx(alpha)
    # Fixed coordinates do not affect the projection.
    assert hand_mapping.project_hand_vector([500.0, 9.0, 0.0, 0.0, 9.0, 500.0], hand_range) == pytest.approx(0.5)


def test_hand_range_validation():
    with pytest.raises(ValueError, match="two native hand vectors"):
        hand_mapping.normalize_hand_range([[0.0] * 6], name="left_hand_range")
    with pytest.raises(ValueError, match="same width"):
        hand_mapping.normalize_hand_range([[0.0] * 6, [1.0] * 5], name="left_hand_range")
    with pytest.raises(ValueError, match="identical"):
        hand_mapping.normalize_hand_range([[1.0] * 6, [1.0] * 6], name="left_hand_range")


def _range_node():
    node = object.__new__(quest3.VRWholeBodyBridgeNode)
    node.state = quest3.BridgeState()
    node.left_gripper_control_mode = "proportional"
    node.right_gripper_control_mode = "incremental"
    node.robot_action_layout = action_layout_for_robot("ti5_t170c")
    node.left_hand_slice = slice(14, 15)
    node.right_hand_slice = slice(15, 16)
    node.left_hand_range = hand_mapping.normalize_hand_range(PARTIAL_RANGE, name="left_hand_range")
    node.right_hand_range = hand_mapping.normalize_hand_range(
        [[1000.0] * 6, [0.0, 0.0, 0.0, 0.0, 0.0, 1000.0]], name="right_hand_range"
    )
    node.left_hand_feedback_names = [f"left_hand_joint{i}" for i in range(1, 7)]
    node.right_hand_feedback_names = [f"right_hand_joint{i}" for i in range(1, 7)]
    node.command_joint_names = list(node.robot_action_layout.action_names)
    return node


def test_range_mode_publishes_native_hand_width():
    node = _range_node()
    published = []
    node.JointState = lambda: SimpleNamespace(header=SimpleNamespace(stamp=None))
    node.node = SimpleNamespace(get_clock=lambda: SimpleNamespace(now=lambda: SimpleNamespace(to_msg=lambda: None)))
    node.pub = SimpleNamespace(publish=published.append)

    node._publish_joint_command(np.asarray([0.1] * 14 + [0.5, 1.0]))

    msg = published[0]
    assert msg.name == list(node.robot_action_layout.action_names)
    np.testing.assert_allclose(msg.position[:14], [0.1] * 14)
    np.testing.assert_allclose(msg.position[14:20], [500.0, 0.0, 1000.0, 1000.0, 0.0, 500.0])
    np.testing.assert_allclose(msg.position[20:26], [0.0, 0.0, 0.0, 0.0, 0.0, 1000.0])


def test_range_mode_projects_native_feedback_to_scalar():
    node = _range_node()
    left = hand_mapping.hand_feedback_to_control(
        [750.0, 0.0, 1000.0, 1000.0, 0.0, 750.0],
        mode=node.left_gripper_control_mode,
        hand_range=node.left_hand_range,
        robot_width=6,
    )
    right = hand_mapping.hand_feedback_to_control(
        [1000.0] * 6,
        mode=node.right_gripper_control_mode,
        hand_range=node.right_hand_range,
        robot_width=6,
    )

    assert left == [pytest.approx(0.75)]
    assert right == [pytest.approx(0.0)]


class _QuietLogger:
    def warning(self, message):
        pass


def _layout_node(config):
    node = object.__new__(quest3.VRWholeBodyBridgeNode)
    node.node = SimpleNamespace(get_logger=_QuietLogger)
    node.state = quest3.BridgeState()
    full_config = {"robot": "ti5_t170c", **config}
    node._configure_hand_layout(full_config)
    node.min_action, node.max_action = node._load_action_limits(config)
    return node


DISCRETE_VALUES = [
    [1000.0] * 6,
    [0.0, 0.0, 0.0, 0.0, 0.0, 1000.0],
]


def test_per_side_modes_fall_back_to_shared_mode():
    node = _layout_node({
        "gripper_control_mode": "proportional",
        "right_gripper_control_mode": "incremental",
        "left_hand_range": PARTIAL_RANGE,
        "right_hand_range": PARTIAL_RANGE,
    })

    assert node.left_gripper_control_mode == "proportional"
    assert node.right_gripper_control_mode == "incremental"
    assert node.joint_names == quest3.SCALAR_ACTION_NAMES
    assert node._hand_mode(node.state.left) == "proportional"
    assert node._hand_mode(node.state.right) == "incremental"


def test_mixed_discrete_and_ranged_hands_share_native_command_layout():
    mixed_layout = action_layout_from_robot_config(get_ti5_t170c_config("lhand_rgripper"))
    node = _layout_node({
        "action_names": list(mixed_layout.action_names),
        "left_gripper_control_mode": "discrete",
        "right_gripper_control_mode": "proportional",
        "left_hand_discrete_values": DISCRETE_VALUES,
        "right_hand_range": RIGHT_GRIPPER_RANGE,
        "min_action": [-1.0] * 14 + [0.0, 0.0],
        "max_action": [1.0] * 14 + [1.0, 1.0],
    })

    assert node.left_hand_slice == slice(14, 20)
    assert node.right_hand_slice == slice(20, 21)
    assert len(node.joint_names) == 21
    assert node.joint_names[14:20] == [f"left_hand_joint{i}" for i in range(1, 7)]
    assert node.joint_names[20] == "right_hand_joint1"
    np.testing.assert_allclose(node.min_action[14:], [0.0] * 6 + [0.0])
    np.testing.assert_allclose(node.max_action[14:], [1000.0] * 6 + [1.0])
    assert node.command_joint_names == list(mixed_layout.action_names)

    action = np.asarray([0.1] * 14 + [500.0] * 6 + [0.5])
    expanded = node._expand_hand_command(action)
    np.testing.assert_allclose(expanded[14:20], [500.0] * 6)
    np.testing.assert_allclose(expanded[20:21], [500.0])

    left_control = hand_mapping.hand_feedback_to_control(
        [0.0] * 6,
        mode=node.left_gripper_control_mode,
        hand_range=node.left_hand_range,
        robot_width=6,
    )
    right_control = hand_mapping.hand_feedback_to_control(
        [250.0],
        mode=node.right_gripper_control_mode,
        hand_range=node.right_hand_range,
        robot_width=1,
    )
    assert left_control == [0.0] * 6
    assert right_control == [pytest.approx(0.75)]

    native_reset = [0.0] * 14 + [1000.0] * 6 + [250.0]
    reset = node._compose_reset_action([0.0] * 16, native_reset)
    assert reset[14:20] == [1000.0] * 6
    assert reset[20] == pytest.approx(0.75)


def test_native_output_requires_range_for_continuous_hand():
    with pytest.raises(ValueError, match="continuous range"):
        _layout_node({
            "left_gripper_control_mode": "discrete",
            "right_gripper_control_mode": "incremental",
            "left_hand_discrete_values": DISCRETE_VALUES,
        })


def test_per_side_tick_runs_each_hand_with_its_own_mode():
    mixed_layout = action_layout_from_robot_config(get_ti5_t170c_config("lhand_rgripper"))
    node = _layout_node({
        "action_names": list(mixed_layout.action_names),
        "left_gripper_control_mode": "discrete",
        "right_gripper_control_mode": "proportional",
        "left_hand_discrete_values": DISCRETE_VALUES,
        "right_hand_range": RIGHT_GRIPPER_RANGE,
    })
    for key, value in dict(
        grip_threshold=0.9, trigger_threshold=0.9, gripper_input_min=0.0, gripper_input_max=1.0,
        proportional_activation_threshold=0.05, proportional_release_threshold=0.02,
        proportional_latch_on_release=True, gripper_command_min=0.0, gripper_command_max=1.0,
    ).items():
        setattr(node, key, value)
    node.state.action = np.zeros(21)
    node.state.reference_action = np.asarray([0.0] * 14 + [1000.0] * 6 + [0.0])
    node.state.joint_state_ready = True
    node._update_reset_edge_locked = lambda: None
    node._next_reset_action_locked = lambda: None
    node._update_arm_locked = lambda side, arm_slice: None
    published = []
    node._publish_joint_command = lambda action: published.append(np.asarray(action).copy())

    node.state.left.grip = 1.0
    node.state.right.grip = 0.5
    node._tick()

    np.testing.assert_allclose(published[-1][14:20], DISCRETE_VALUES[1])
    assert published[-1][20] == pytest.approx(0.5)
