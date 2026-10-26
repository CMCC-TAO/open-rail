from conf.robots_conf import get_agibot_g1_config, get_ti5_t170c_config
from teleop.action_mapping import (
    action_layout_from_action_names,
    action_layout_from_robot_config,
)


def test_action_layout_follows_robot_end_effector_profile():
    a2d = action_layout_from_robot_config(get_agibot_g1_config())
    hand = action_layout_from_robot_config(get_ti5_t170c_config("hand"))
    mixed = action_layout_from_robot_config(get_ti5_t170c_config("lhand_rgripper"))

    assert (a2d.action_dim, a2d.hand_widths) == (16, (1, 1))
    assert (hand.action_dim, hand.hand_widths) == (26, (6, 6))
    assert (mixed.action_dim, mixed.hand_widths) == (21, (6, 1))
    assert mixed.action_names[14:] == tuple(
        [f"left_hand_joint{i}" for i in range(1, 7)] + ["right_hand_joint1"]
    )


def test_action_layout_can_be_reconstructed_from_bridge_action_names():
    layout = action_layout_from_robot_config(get_ti5_t170c_config("lgripper_rhand"))
    restored = action_layout_from_action_names(layout.action_names)

    assert restored.action_names == layout.action_names
    assert restored.hand_widths == (1, 6)
