import json
import logging
from pathlib import Path
import threading
import time
from types import SimpleNamespace

import numpy as np
from ml_collections import ConfigDict

from client.core.teleop_bridge import RosTeleopBridge, TeleopDeviceProcess
from client.core.action_arbiter import ActionArbiter, ActionSource
from client.core.vla_client import VLAClient
from client.robots.base_robot import RobotBase
from conf.client_conf import (
    TELEOP_CONFIG_PATH_BY_ROBOT,
    apply_teleop_robot_mapping,
    get_client_config,
    get_teleop_config_path,
)
from conf.robots_conf import RobotType, get_ti5_t170c_config
from teleop.action_mapping import action_layout_for_robot
from teleop.quest3.quest3 import BridgeState, QuestTcpServer
from teleop.status import teleop_enabled, teleop_status_snapshot


def test_quest3_process_receives_shared_native_reset_action():
    native_reset_action = [float(index) for index in range(26)]
    action_names = list(action_layout_for_robot("ti5_t170c").action_names)
    process = TeleopDeviceProcess(
        device="quest3",
        config=ConfigDict({"devices": {"quest3": {}}}),
        command_topic="/target_robot/joint_commands",
        joint_state_topic="/client_robot/joint_states",
        reset_topic="/custom/custom_a",
        action_names=action_names,
        native_reset_action=native_reset_action,
    )

    command, _, _ = process._build_command()
    assert "--reset-action" not in command
    names_index = command.index("--action-names")
    assert json.loads(command[names_index + 1]) == action_names
    native_index = command.index("--native-reset-action")
    assert json.loads(command[native_index + 1]) == native_reset_action


def test_quest3_process_reports_connected_from_status_file(tmp_path):
    process = TeleopDeviceProcess(
        device="quest3",
        config=ConfigDict({"devices": {"quest3": {}}}),
        command_topic="/target_robot/joint_commands",
        joint_state_topic="/client_robot/joint_states",
        reset_topic="/custom/custom_a",
    )
    process.process = SimpleNamespace(pid=1234, poll=lambda: None)
    process.status_file = tmp_path / "quest3_status.json"
    process.status_file.write_text(json.dumps({
        "state": "connected",
        "connected": True,
        "remote": "127.0.0.1:54321",
        "total_packets": 12,
    }), encoding="utf-8")

    status = process.status()

    assert status["process_running"] is True
    assert status["device_connected"] is True
    assert status["state"] == "connected"
    assert status["total_packets"] == 12


def test_quest3_process_command_includes_status_file(tmp_path):
    process = TeleopDeviceProcess(
        device="quest3",
        config=ConfigDict({"devices": {"quest3": {}}}),
        command_topic="/target_robot/joint_commands",
        joint_state_topic="/client_robot/joint_states",
        reset_topic="/custom/custom_a",
    )
    process.status_file = Path(tmp_path) / "quest3_status.json"

    command, _, _ = process._build_command()

    status_index = command.index("--status-file")
    assert command[status_index + 1] == str(process.status_file)


def test_ros_teleop_bridge_uses_target_action_width():
    action_names = action_layout_for_robot("ti5_t170c").action_names
    bridge = RosTeleopBridge(
        submit_action=lambda action, timestamp: None,
        action_names=action_names,
    )

    assert bridge.action_dim == 26


def test_ros_teleop_bridge_passes_ordered_native_action_through():
    action_names = action_layout_for_robot('ti5_t170c').action_names
    submitted = []
    bridge = RosTeleopBridge(
        submit_action=lambda action, timestamp: submitted.append(action),
        action_names=action_names,
    )
    positions = [float(index) for index in range(len(action_names))]

    bridge._command_cb(SimpleNamespace(name=list(action_names), position=positions))

    assert len(submitted) == 1
    np.testing.assert_allclose(submitted[0], positions)


def test_teleop_robot_mapping_switches_profiles_and_disables_unsupported():
    config = get_client_config()
    config.teleop.use_teleop = True

    assert apply_teleop_robot_mapping(config, 'agibot_g1') is True
    assert config.teleop.devices.quest3.config_path == 'teleop/quest3/config/a2d.yaml'
    assert config.teleop.use_teleop is True

    assert apply_teleop_robot_mapping(config, 'ti5_t170c') is True
    assert config.teleop.devices.quest3.config_path == 'teleop/quest3/config/ti5_t170c.yaml'

    assert apply_teleop_robot_mapping(config, 'unitree_g1') is False
    assert config.teleop.use_teleop is False
    assert config.teleop.devices.quest3.config_path == ''


def test_teleop_support_is_limited_to_validated_robot_bodies():
    assert TELEOP_CONFIG_PATH_BY_ROBOT == {
        'agibot_g1': 'teleop/quest3/config/a2d.yaml',
        'ti5_t170c': 'teleop/quest3/config/ti5_t170c.yaml',
    }
    assert get_teleop_config_path('a2d') == 'teleop/quest3/config/a2d.yaml'
    assert get_teleop_config_path(RobotType.TI5_T170C) == 'teleop/quest3/config/ti5_t170c.yaml'
    assert get_teleop_config_path('RobotType.TI5_T170C') == 'teleop/quest3/config/ti5_t170c.yaml'
    assert get_teleop_config_path('mock') is None
    assert get_teleop_config_path('navi_wa2') is None


def test_teleop_status_is_derived_from_one_shared_snapshot():
    config = get_client_config()
    config.teleop.use_teleop = True
    config.robots.type = RobotType.TI5_T170C
    apply_teleop_robot_mapping(config, 'ti5_t170c')

    status = teleop_status_snapshot(config)

    assert teleop_enabled(config) is True
    assert status['enabled'] is True
    assert status['supported'] is True
    assert status['config_path'] == 'teleop/quest3/config/ti5_t170c.yaml'
    assert status['bridge_running'] is False

    config.robots.type = RobotType.UNITREE_G1
    apply_teleop_robot_mapping(config, 'unitree_g1')
    unsupported = teleop_status_snapshot(config)
    assert teleop_enabled(config) is False
    assert unsupported['supported'] is False
    assert unsupported['state'] == 'unsupported'


def test_ti5_native_teleop_action_is_not_remapped_or_rescaled():
    client = object.__new__(VLAClient)
    ti5_config = get_ti5_t170c_config()
    client.config = ConfigDict({
        'robots': {
            'type': 'ti5_t170c',
            'ti5_t170c': ti5_config,
        },
        'controller': {
            'teleop_outlier_guard_enabled': True,
            'teleop_outlier_max_arm_joint_delta': 0.5,
            'teleop_outlier_max_arm_norm_delta': 1.2,
            'teleop_outlier_max_gripper_delta': 1.0,
            'teleop_outlier_log_interval_s': 1.0,
        },
    })
    client.robot = SimpleNamespace(current_state=[0.0] * 14 + [1000.0] * 12 + [0.0] * 3)
    client.logger = logging.getLogger(__name__)
    client.action_arbiter = ActionArbiter()
    client._last_executed_action = None
    client._last_executed_action_lock = threading.Lock()
    client._teleop_outlier_reject_count = 0
    client._teleop_outlier_last_log_s = 0.0

    native_action = [0.0] * 14 + [0.0, 0.0, 0.0, 0.0, 0.0, 1000.0] * 2
    action = client._validate_teleop_bridge_action(native_action)

    np.testing.assert_allclose(action[:14], np.zeros(14))
    np.testing.assert_allclose(action, native_action)


def test_ti5_bridge_rejects_legacy_scalar_width_instead_of_remapping_it():
    client = object.__new__(VLAClient)
    client.config = ConfigDict({
        'robots': {
            'type': 'ti5_t170c',
            'ti5_t170c': get_ti5_t170c_config(),
        },
        'controller': {'teleop_outlier_guard_enabled': False},
    })
    client.logger = logging.getLogger(__name__)
    client._teleop_outlier_last_log_s = 0.0

    assert client._validate_teleop_bridge_action([0.0] * 16) is None


def test_web_reset_reads_reset_robot_pos():
    class CaptureRobot(RobotBase):
        def __init__(self, config):
            super().__init__(config)
            self.control_data = None

        def _control_robot(self, data):
            self.control_data = data

    config = ConfigDict({
        "action_layout": {
            "arm": {"start": 0, "end": 2, "policy": "gradual"},
            "gripper": {"start": 2, "end": 4, "policy": "stepwise"},
        },
        "reset_robot_pos": [1.0, 2.0, 3.0, 4.0],
    })
    robot = CaptureRobot(config)

    robot.reset_robot(mode="default")

    assert robot.control_data == {
        "source": "manual",
        "l_arm": [1.0],
        "r_arm": [2.0],
        "l_gripper": [3.0],
        "r_gripper": [4.0],
    }


def test_stale_teleop_action_is_not_used_as_outlier_baseline():
    client = object.__new__(VLAClient)
    client.logger = logging.getLogger(__name__)
    client.config = ConfigDict({
        'robots': {'type': 'ti5_t170c', 'ti5_t170c': get_ti5_t170c_config()},
        'controller': {
            'teleop_timeout_s': 0.15,
            'teleop_outlier_guard_enabled': True,
            'teleop_outlier_max_arm_joint_delta': 0.5,
            'teleop_outlier_max_arm_norm_delta': 1.2,
            'teleop_outlier_max_gripper_delta': 1.0,
            'teleop_outlier_log_interval_s': 1.0,
        },
    })
    client.robot = SimpleNamespace(current_state=np.zeros(26))
    client.action_arbiter = ActionArbiter(action_timeout_s=0.15)
    client._last_executed_action = np.zeros(26)
    client._last_executed_action_lock = threading.Lock()
    client._teleop_outlier_reject_count = 0
    client._teleop_outlier_last_log_s = 0.0

    stale = np.zeros(26)
    stale[0] = 2.0
    client.action_arbiter.submit(ActionSource.TELEOP, stale, timestamp=time.perf_counter() - 1.0)
    new_action = np.zeros(26)
    new_action[0] = 0.1

    accepted = client._validate_teleop_bridge_action(new_action, timestamp=time.perf_counter())
    np.testing.assert_allclose(accepted, new_action)


def test_rejected_teleop_stream_releases_ownership_after_threshold():
    client = object.__new__(VLAClient)
    client.logger = logging.getLogger(__name__)
    client.config = ConfigDict({'controller': {
        'teleop_timeout_s': 0.15,
        'teleop_outlier_reanchor_after_rejects': 5,
    }})
    client.action_arbiter = ActionArbiter(action_timeout_s=0.15)
    client._teleop_outlier_reject_count = 5

    client._hold_teleop_after_rejected_action(time.perf_counter())

    assert client.action_arbiter.last_submitted_at(ActionSource.TELEOP) is None


def test_live_teleop_session_holds_only_its_own_last_safe_action():
    client = object.__new__(VLAClient)
    client.logger = logging.getLogger(__name__)
    client.config = ConfigDict({'controller': {
        'teleop_timeout_s': 0.15,
        'teleop_outlier_reanchor_after_rejects': 5,
    }})
    client.action_arbiter = ActionArbiter(action_timeout_s=0.15)
    client._teleop_outlier_reject_count = 1
    safe = np.arange(26, dtype=float)
    timestamp = time.perf_counter()
    client.action_arbiter.submit(ActionSource.TELEOP, safe, timestamp=timestamp)

    client._hold_teleop_after_rejected_action(timestamp + 0.01)

    np.testing.assert_allclose(client.action_arbiter.latest_action(ActionSource.TELEOP), safe)


def test_starting_control_starts_configured_teleop_bridge():
    client = object.__new__(VLAClient)
    client._control_execution_lock = threading.RLock()
    client.robot = SimpleNamespace()
    client.is_running = False
    client.is_control_thread_running = False
    client.control_thread_timer = SimpleNamespace(
        is_alive=lambda: False,
        start=lambda: None,
    )
    client.task_language_manager = SimpleNamespace(new_task=lambda: None)
    calls = []
    client._use_teleop_enabled = lambda: True
    client.start_teleop_bridge = lambda: calls.append('start')

    client.start_control()

    assert calls == ['start']
    assert client.is_control_thread_running is True


def test_quest3_tcp_watchdog_expires_silent_connection():
    server = object.__new__(QuestTcpServer)
    server.client_timeout_s = 2.0
    server.last_packet_monotonic = 10.0
    assert not server._client_timed_out(11.99)
    assert server._client_timed_out(12.01)
    server.client_timeout_s = 0.0
    assert not server._client_timed_out(100.0)


def test_quest3_tcp_status_refreshes_packet_heartbeat(tmp_path):
    server = QuestTcpServer(
        node=SimpleNamespace(get_logger=lambda: SimpleNamespace(info=lambda *args: None)),
        state=BridgeState(),
        port=8002,
        controller_y_rotation_rad=0.0,
        invalid_origin_epsilon_m=0.0,
        status_file=str(tmp_path / "quest3_status.json"),
        status_publish_interval_s=1.0,
    )
    server.last_packet_monotonic = time.monotonic()
    server.last_packet_wall_time = time.time()
    server._last_status_publish_monotonic = 0.0
    server.state.left.pose_valid = True
    server.state.right.pose_valid = False
    server._publish_periodic_status("connected", connected=True)
    payload = json.loads((tmp_path / "quest3_status.json").read_text(encoding="utf-8"))
    assert payload["state"] == "connected"
    assert payload["connected"] is True
    assert payload["last_packet_at"] is not None
    assert payload["last_packet_age_s"] >= 0.0
    assert payload["left_tracking_valid"] is True
    assert payload["right_tracking_valid"] is False
