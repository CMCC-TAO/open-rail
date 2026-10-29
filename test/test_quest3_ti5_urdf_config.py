import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import yaml

from teleop.quest3 import joint_command_to_ti5_t170c as ti5_command
from teleop.action_mapping import action_layout_for_robot

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "teleop" / "quest3" / "config" / "ti5_t170c.yaml"
URDF_PATH = REPO_ROOT / "teleop" / "quest3" / "urdf" / "ti5_robot_tjv2.urdf"


def _load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _load_urdf():
    return ET.parse(URDF_PATH).getroot()


def _movable_joint_chain(urdf_root, base_link: str, tip_link: str) -> list[str]:
    links = {link.attrib["name"] for link in urdf_root.findall("link")}
    joints_by_child = {
        joint.find("child").attrib["link"]: joint
        for joint in urdf_root.findall("joint")
    }
    assert base_link in links
    assert tip_link in links

    chain = []
    link = tip_link
    while link != base_link:
        joint = joints_by_child[link]
        if joint.attrib["type"] != "fixed":
            chain.append(joint.attrib["name"])
        link = joint.find("parent").attrib["link"]
    return list(reversed(chain))


def test_ti5_quest3_config_uses_tjv2_arm_chains_and_ros_joint_names():
    config = _load_config()
    ik = config["ik"]
    urdf_root = _load_urdf()

    assert urdf_root.attrib["name"] == "ti5_robot"
    assert (CONFIG_PATH.parent / ik["urdf_path"]).resolve() == URDF_PATH

    left_chain = _movable_joint_chain(
        urdf_root, ik["left"]["base_link"], ik["left"]["tip_link"]
    )
    right_chain = _movable_joint_chain(
        urdf_root, ik["right"]["base_link"], ik["right"]["tip_link"]
    )
    assert left_chain == [f"Joint{i}_L" for i in range(1, 8)]
    assert right_chain == [f"Joint{i}_R" for i in range(1, 8)]
    layout = action_layout_for_robot("ti5_t170c")
    assert layout.hand_widths == (6, 6)
    assert layout.action_names[14:20] == tuple(f"left_hand_joint{i}" for i in range(1, 7))
    assert layout.action_names[20:26] == tuple(f"right_hand_joint{i}" for i in range(1, 7))
    assert "joint_state_names" not in config
    assert "joint_state_names_discrete" not in config
    assert "joint_state_position_names" not in config
    assert "left_hand_continuous_range" in config
    assert "right_hand_continuous_range" in config
    assert "left_hand_range" not in config
    assert "right_hand_range" not in config
    assert ti5_command.TI5_LEFT_ARM_JOINTS == left_chain
    assert ti5_command.TI5_RIGHT_ARM_JOINTS == right_chain


def test_ti5_quest3_arm_limits_match_tjv2_urdf():
    config = _load_config()
    urdf_root = _load_urdf()
    joint_limits = {
        joint.attrib["name"]: joint.find("limit").attrib
        for joint in urdf_root.findall("joint")
        if joint.find("limit") is not None
    }
    arm_joint_names = ti5_command.TI5_LEFT_ARM_JOINTS + ti5_command.TI5_RIGHT_ARM_JOINTS

    expected_min = [float(joint_limits[name]["lower"]) for name in arm_joint_names]
    expected_max = [float(joint_limits[name]["upper"]) for name in arm_joint_names]
    assert config["min_action"][:14] == expected_min
    assert config["max_action"][:14] == expected_max
    assert all(
        lower <= value <= upper
        for value, lower, upper in zip(
            ti5_command.LEFT_ARM_RESET_POS + ti5_command.RIGHT_ARM_RESET_POS,
            expected_min,
            expected_max,
        )
    )


def test_ti5_quest3_vr_transforms_match_tjv2_frame_conventions():
    config = _load_config()
    expected_arm_rotation = np.array(
        [
            [0.0, 0.0, 1.0],
            [0.0, -1.0, 0.0],
            [1.0, 0.0, 0.0],
        ]
    )
    left = np.asarray(config["rot_left_arm_from_vr_to_urdf"]["rotation_mat"])
    right = np.asarray(config["rot_right_arm_from_vr_to_urdf"]["rotation_mat"])
    base = np.asarray(config["rot_base_from_vr_to_urdf"]["rotation_mat"])

    # tjv2 L/R flange frames share one local-axis convention, unlike the retired
    # WRIST_P frames. The robot BASE_LINK orientation itself is unchanged.
    np.testing.assert_allclose(left, expected_arm_rotation)
    np.testing.assert_allclose(right, expected_arm_rotation)
    np.testing.assert_allclose(
        base,
        [
            [0.0, 1.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
    )
    for rotation in (left, right, base):
        np.testing.assert_allclose(rotation @ rotation.T, np.eye(3), atol=1e-12)
        np.testing.assert_allclose(np.linalg.det(rotation), 1.0, atol=1e-12)
