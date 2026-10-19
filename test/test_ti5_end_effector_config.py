import subprocess
import sys
from pathlib import Path

import yaml

from conf.robots_conf import (
    get_agibot_g1_config,
    get_navi_wa2_config,
    get_ti5_t170c_config,
    get_unitree_g1_config,
)


def test_robots_conf_does_not_import_the_ti5_sdk():
    # A fresh interpreter: this file's neighbors import the SDK on purpose.
    root = Path(__file__).resolve().parents[1]
    script = (
        "import sys\n"
        "from conf.robots_conf import get_robots_config\n"
        "get_robots_config()\n"
        "assert not any(name == 'ti5_t170c_sdk' or name.startswith('ti5_t170c_sdk.') "
        "for name in sys.modules)\n"
    )
    subprocess.run([sys.executable, "-c", script], cwd=root, check=True)


def test_default_ti5_layout_stays_26():
    config = get_ti5_t170c_config()
    assert config.hand_type == "hand"
    hand = config.action_layout["hand"]
    head = config.action_layout["head"]
    assert (hand["start"], hand["end"], hand["policy"]) == (14, 26, "gradual")
    assert (head["start"], head["end"], head["policy"]) == (26, 29, "manual")
    assert len(config.reset_robot_pos) == 26
    assert list(config.reset_robot_pos[14:]) == [1000.0] * 12
    assert len(hand["presets"]["left"]["Default"]) == 6
    assert len(hand["presets"]["right"]["Default"]) == 6


def test_mixed_profile_is_6_plus_1_not_a_half_split():
    config = get_ti5_t170c_config("lhand_rgripper")
    hand = config.action_layout["hand"]
    assert (hand["start"], hand["end"]) == (14, 21)
    assert len(hand["presets"]["left"]["Default"]) == 6
    assert len(hand["presets"]["right"]["Default"]) == 1
    assert config.action_layout["head"]["start"] == 21
    assert config.action_layout["head"]["end"] == 24
    assert len(config.reset_robot_pos) == 21


def test_other_robots_keep_their_end_effector_layout():
    agibot = get_agibot_g1_config()
    assert agibot.hand_type == "gripper"
    assert (agibot.action_layout["gripper"]["start"], agibot.action_layout["gripper"]["end"]) == (14, 16)
    assert "hand" not in agibot.action_layout
    navi = get_navi_wa2_config()
    assert navi.hand_type == "hand"
    assert (navi.action_layout["hand"]["start"], navi.action_layout["hand"]["end"]) == (16, 28)
    assert navi.action_layout["hand"]["policy"] == "stepwise"
    unitree = get_unitree_g1_config()
    assert unitree.hand_type == "hand"
    assert (unitree.action_layout["hand"]["start"], unitree.action_layout["hand"]["end"]) == (14, 26)
    assert unitree.action_layout["hand"]["policy"] == "stepwise"


def test_default_yaml_matches_active_ti5_profile():
    yaml_path = Path(__file__).resolve().parents[1] / "conf" / "default_conf.yaml"
    with open(yaml_path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    ti5 = data["robots"]["ti5_t170c"]
    generated = get_ti5_t170c_config(ti5["hand_type"])
    assert (ti5["action_layout"]["hand"]["start"], ti5["action_layout"]["hand"]["end"]) == (
        generated.action_layout["hand"]["start"],
        generated.action_layout["hand"]["end"],
    )
    assert ti5["action_layout"]["head"]["start"] == generated.action_layout["head"]["start"]
    assert len(ti5["reset_robot_pos"]) == generated.action_layout["hand"]["end"]
    assert len(ti5["action_layout"]["hand"]["presets"]["right"]["Default"]) == len(
        generated.action_layout["hand"]["presets"]["right"]["Default"]
    )
