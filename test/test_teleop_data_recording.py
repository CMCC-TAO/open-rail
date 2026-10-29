import json
from collections import deque
from queue import Queue
from types import SimpleNamespace

import numpy as np
import pyarrow.parquet as pq

from client.core.action_arbiter import ActionArbiter, ActionSource
from client.core.data_record_manager import DataRecordManager
from client.core.lerobot_dataset_recorder import TELEOP_FEATURE_KEYS, LeRobotDatasetRecorder
from client.core.teleop_bridge import RosTeleopBridge, TeleopRuntime
from conf.save_conf import get_record_data_config
from teleop.action_mapping import action_layout_for_robot
from teleop.quest3 import quest3


def test_arbiter_carries_teleop_mask_and_hold_keeps_none():
    arbiter = ActionArbiter(action_timeout_s=1.0)
    mask = [True, False, True]
    arbiter.submit(ActionSource.TELEOP, [1.0, 2.0, 3.0], timestamp=0.0, mask=mask)

    selected = arbiter.select(now=0.1)

    assert selected.source == ActionSource.TELEOP
    np.testing.assert_array_equal(selected.mask, mask)
    np.testing.assert_array_equal(arbiter.latest_mask(ActionSource.TELEOP), mask)
    assert arbiter.select(now=5.0).mask is None


def _tick_node():
    node = object.__new__(quest3.VRWholeBodyBridgeNode)
    node.state = quest3.BridgeState()
    node.state.joint_state_ready = True
    node.state.left.pose_valid = True
    node.state.left.trigger = 1.0
    node.trigger_threshold = 0.9
    node.left_gripper_control_mode = "incremental"
    node.right_gripper_control_mode = "incremental"
    node.left_discrete_values = []
    node.right_discrete_values = []
    node.left_hand_slice = slice(14, 15)
    node.right_hand_slice = slice(15, 16)
    node.min_action = np.full(16, -np.inf)
    node.max_action = np.full(16, np.inf)
    node.robot_action_layout = action_layout_for_robot("ti5_t170c")
    node._update_reset_edge_locked = lambda: None
    node._next_reset_action_locked = lambda: None
    node._update_arm_locked = lambda side, arm_slice: None
    node._update_gripper_locked = lambda side, index: None
    node._is_gripper_control_requested = lambda side: False
    return node


def test_quest3_tick_marks_only_human_controlled_joints():
    node = _tick_node()
    published = []
    node._publish_joint_command = lambda action, mask=None: published.append(mask)

    node._tick()

    mask = published[0]
    assert mask[0:7].all()
    assert not mask[7:14].any()
    assert not mask[14:16].any()
    native_mask = node._expand_hand_mask(mask)
    assert native_mask.shape == (26,)
    assert not native_mask[14:].any()


def test_quest3_publishes_mask_in_effort_and_bridge_reads_it():
    node = _tick_node()
    node.right_hand_range = None
    node.left_hand_range = None
    node.command_joint_names = list(node.robot_action_layout.action_names)
    node.JointState = lambda: SimpleNamespace(header=SimpleNamespace(stamp=None))
    node.node = SimpleNamespace(get_clock=lambda: SimpleNamespace(now=lambda: SimpleNamespace(to_msg=lambda: None)))
    node._expand_hand_command = lambda action: np.concatenate([action[:14], [action[14]] * 6, [action[15]] * 6])
    messages = []
    node.pub = SimpleNamespace(publish=messages.append)

    mask = np.array([True] * 7 + [False] * 7 + [True, False])
    node._publish_joint_command(np.zeros(16), mask=mask)

    msg = messages[0]
    assert msg.effort == [1.0] * 7 + [0.0] * 7 + [1.0] * 6 + [0.0] * 6

    submitted = []
    bridge = RosTeleopBridge(
        submit_action=lambda action, timestamp, mask=None: submitted.append(mask),
        action_names=node.command_joint_names,
    )
    bridge._command_cb(msg)
    np.testing.assert_array_equal(submitted[0], np.asarray(msg.effort) > 0.5)


def test_bridge_without_effort_keeps_legacy_callback_signature():
    action_names = action_layout_for_robot("ti5_t170c").action_names
    submitted = []
    bridge = RosTeleopBridge(
        submit_action=lambda action, timestamp: submitted.append(action),
        action_names=action_names,
    )

    bridge._command_cb(SimpleNamespace(name=list(action_names), position=[0.0] * len(action_names), effort=[]))

    assert len(submitted) == 1


def test_record_fields_for_teleop_override():
    executed = np.arange(4, dtype=float)
    policy = np.full(4, 9.0)
    mask = np.array([True, True, False, False])

    fields = TeleopRuntime._teleop_record_fields(executed, ActionSource.TELEOP, teleop_mask=mask, policy_action=policy)

    assert fields['is_teleop'] is True
    np.testing.assert_allclose(fields['teleop_action'], executed)
    np.testing.assert_array_equal(fields['teleop_action_mask'], mask)
    np.testing.assert_allclose(fields['rejected_action'], policy)
    np.testing.assert_array_equal(fields['rejected_action_mask'], mask)


def test_record_fields_for_policy_and_teleop_without_policy():
    executed = np.ones(3)

    policy_fields = TeleopRuntime._teleop_record_fields(executed, ActionSource.POLICY, policy_action=executed)
    assert policy_fields['is_teleop'] is False
    assert not policy_fields['teleop_action'].any()
    assert not policy_fields['teleop_action_mask'].any()
    assert not policy_fields['rejected_action_mask'].any()

    teleop_fields = TeleopRuntime._teleop_record_fields(executed, ActionSource.TELEOP)
    assert teleop_fields['teleop_action_mask'].all()
    assert not teleop_fields['rejected_action'].any()
    assert not teleop_fields['rejected_action_mask'].any()

    hold_fields = TeleopRuntime._teleop_record_fields(executed, ActionSource.HOLD)
    assert hold_fields['is_teleop'] is False


def test_data_record_manager_pairs_teleop_fields_with_observation():
    manager = object.__new__(DataRecordManager)
    manager.logger = SimpleNamespace(warning=lambda *args, **kwargs: None)
    manager.shared_data = SimpleNamespace(running=SimpleNamespace(is_set=lambda: True))
    manager._get_recording_session_id = lambda: 1
    manager.action_frame_queue = deque(maxlen=10)
    manager.record_queue = Queue()
    teleop_record = {'is_teleop': True}

    manager._add_action_fun(np.ones(2), 0.0, 1, teleop_record)
    manager._add_observation_fun({'obs': {}}, {}, 0.0, 1)

    _, action, _, step_teleop = manager.record_queue.get_nowait()
    np.testing.assert_allclose(action, np.ones(2))
    assert step_teleop is teleop_record

    manager._add_action_fun(np.zeros(2), 0.0, 1)
    manager._add_observation_fun({'obs': {}}, {}, 0.0, 1)
    assert manager.record_queue.get_nowait()[3] is None


def _record_episode(recorder, save_path, frames, record_teleop_fields=True):
    recorder.set_task(save_path=str(save_path), record_teleop_fields=record_teleop_fields)
    recorder.update_camera_shape_dict({name: (8, 8, 3) for name in recorder.camera_name_list})
    recorder.begin_recording(
        episode_chunk=0,
        episode_index=recorder.config['episode_index'],
        total_frames=recorder.config['total_frames'],
        total_videos=recorder.config['total_videos'],
        total_episodes=recorder.config['total_episodes'],
        save_raw=True,
    )
    for action, step_teleop in frames:
        step_state = {
            'obs': {
                'state': np.zeros(recorder.state_shape, dtype=np.float32),
                **{name: np.zeros((8, 8, 3), dtype=np.uint8) for name in recorder.camera_name_list},
            }
        }
        recorder.add_frame_async(step_state, np.asarray(action, dtype=np.float32), {}, step_teleop)
    recorder.end_recording()
    episode_index = recorder.episode_index - 1
    return pq.read_table(save_path / f"data/chunk-000/episode_{episode_index:06d}.parquet")


def test_new_dataset_records_teleop_columns(tmp_path):
    recorder = LeRobotDatasetRecorder(get_record_data_config().lerobot)
    teleop = TeleopRuntime._teleop_record_fields(
        np.full(4, 2.0),
        ActionSource.TELEOP,
        teleop_mask=[True, False, True, False],
        policy_action=np.full(4, 5.0),
    )

    table = _record_episode(recorder, tmp_path, [(np.ones(4), None), (np.full(4, 2.0), teleop)])

    rows = table.to_pylist()
    assert table.column_names[:7] == [
        'observation.state', 'action', 'episode_index', 'frame_index', 'index', 'task_index', 'timestamp'
    ]
    assert set(TELEOP_FEATURE_KEYS) <= set(table.column_names)
    assert rows[0]['is_teleop'] is False
    assert rows[0]['teleop_action_mask'] == [False] * 22
    assert rows[1]['is_teleop'] is True
    assert rows[1]['action'][:4] == [2.0] * 4
    assert rows[1]['teleop_action'][:4] == [2.0] * 4
    assert rows[1]['teleop_action_mask'][:4] == [True, False, True, False]
    assert rows[1]['rejected_action'][:4] == [5.0] * 4
    assert rows[1]['rejected_action_mask'][:4] == [True, False, True, False]
    assert len(rows[1]['rejected_action']) == 22

    info = json.loads((tmp_path / 'meta' / 'info.json').read_text())
    assert info['features']['teleop_action_mask'] == {'dtype': 'bool', 'shape': [22]}
    assert info['features']['is_teleop']['dtype'] == 'bool'


def test_legacy_dataset_keeps_legacy_parquet_schema(tmp_path):
    legacy_recorder = LeRobotDatasetRecorder(get_record_data_config().lerobot)
    legacy_table = _record_episode(legacy_recorder, tmp_path, [(np.ones(4), None)], record_teleop_fields=False)
    assert not set(TELEOP_FEATURE_KEYS) & set(legacy_table.column_names)

    # A fresh process appending to the same legacy dataset must not mix schemas.
    recorder = LeRobotDatasetRecorder(get_record_data_config().lerobot)
    teleop = TeleopRuntime._teleop_record_fields(np.ones(4), ActionSource.TELEOP)
    table = _record_episode(recorder, tmp_path, [(np.ones(4), teleop)])

    assert table.column_names == legacy_table.column_names
    info = json.loads((tmp_path / 'meta' / 'info.json').read_text())
    assert not set(TELEOP_FEATURE_KEYS) & set(info['features'])
