from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import numpy as np
import pytest

from client.core.inter_chunk_fuser import InterChunkFuser
from client.core.intra_chunk_smoother import IntraChunkSmoother
from client.core.realtime_data_manager import RealtimeDataManager
from client.core.task_language_manager import TaskLanguageManager
from client.robots.aloha_robotwin.body_robot import RobotBody
from client.simulation.vla_client import VLAClientAsync
from conf.client_conf import get_client_config
from scripts import aloha_robotwin_eval as twin
from scripts.robocasa_eval import _start_episode, _wait_for_episode
from test_robocasa_master_merge import FakeTransport as CasaTransport


class FakeTask:
    def __init__(self):
        self.take_action_cnt = 0
        self.step_lim = 8
        self.eval_success = False
        self.state = np.zeros(14)
        self.actions = []
        self.observations_taken = 0
        self.robot = SimpleNamespace(
            get_left_arm_jointState=lambda: self.state[:7].tolist(),
            get_right_arm_jointState=lambda: self.state[7:].tolist(),
        )

    def get_obs(self):
        self.observations_taken += 1
        return {
            "joint_action": {"vector": self.state.copy()},
            "observation": {
                key: {"rgb": np.zeros((16, 16, 3), np.uint8)}
                for key in ("head_camera", "left_camera", "right_camera")
            },
        }

    def take_action(self, action, action_type):
        assert action_type == "qpos"
        time.sleep(0.002)
        self.actions.append(action.copy())
        self.state = action.copy()
        self.take_action_cnt += 1
        self.eval_success = self.take_action_cnt >= self.step_lim

    def close_env(self):
        pass


class Transport(CasaTransport):
    def recvMessage(self, timeout_ms):
        time.sleep(0.003)
        action = np.linspace(0, 0.2, 8)[:, None] * np.ones((1, 14))
        action[:, 6] = np.arange(8) % 2
        action[:, 13] = 1 - np.arange(8) % 2
        return {
            "meta": self.meta,
            "data": {
                "type": "vla_action",
                "pred_action": action,
                "ref_timestamp": self.frame["ref_timestamp"],
                "loc_timestamp": self.frame["loc_timestamp"],
            },
        }


@pytest.mark.parametrize("boundary_only", [True, False])
def test_chunk_rendering_keeps_state_and_captures_terminal_frame(boundary_only):
    class RenderTask(FakeTask):
        def __init__(self):
            super().__init__()
            self.step_lim = 5
            self.captures = 0
            self.render_updates = 0
            self.render_freq = 0

        def _update_render(self):
            self.render_updates += 1

        def get_obs(self):
            self._update_render()
            self.captures += 1
            return super().get_obs()

        def take_action(self, action, action_type):
            for _ in range(3):
                self._update_render()
            super().take_action(action, action_type)
            if self.take_action_cnt == self.step_lim:
                self.eval_success = True
                self.get_obs()

    env = RenderTask()
    robot = RobotBody(get_client_config().robots.aloha_robotwin, env, "Stack bowls")
    robot.configure_chunk_rendering(boundary_only)
    try:
        results = []
        for step in range(1, 6):
            robot.set_action_chunk_boundary(step % 3 == 0)
            results.append(robot.control_robot(np.full(14, step / 10)))
            np.testing.assert_allclose(robot.current_state, step / 10)
        if boundary_only:
            assert [result.observation is not None for result in results] == [False, False, True, False, True]
            assert env.captures == 3 and env.render_updates == 3
        else:
            assert all(result.observation is not None for result in results)
            assert env.captures == 7
        assert results[-1].success and results[-1].observation_step == 5
        env.get_obs()
        assert env.captures == (4 if boundary_only else 8)
    finally:
        robot.close()


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("render_mode", ["chunk_boundary", "per_action"])
@pytest.mark.parametrize("intra", ["raw", "interpolation", "fitting"])
@pytest.mark.parametrize("inter", ["sync", "search_action", "smooth_velocity", "min_jerk"])
def test_threaded_pipeline(monkeypatch, tmp_path, mode, render_mode, intra, inter):
    monkeypatch.setenv('VLA_SIM_PREVIEW_PATH', str(tmp_path / 'preview.json'))
    config = get_client_config()
    config.robots.aloha_robotwin.render_observation_mode = render_mode
    args = twin.build_parser().parse_args(
        [
            "--task_name",
            "Task",
            "--mode",
            mode,
            "--intra_chunk_mode",
            intra,
            "--inter_chunk_mode",
            inter,
            "--n_action_steps",
            "8",
            "--intra_chunk_sample_ratio",
            "2" if intra == "interpolation" else "1",
        ]
    )
    twin.configure_pipeline(config, args)
    config.intra_chunk.preserve_input_timestamps = True
    config.inter_chunk.max_transition_steps = 5
    config.record.switch = False
    robot = RobotBody(config.robots.aloha_robotwin, FakeTask(), "Move the object")
    robot.task_env.step_lim = 12
    config.rdm.action_layout = robot.config.action_layout
    transport = Transport()
    monkeypatch.setattr(
        "client.simulation.vla_client.DataRecordManager",
        lambda **kwargs: SimpleNamespace(close=lambda: None),
    )
    client = VLAClientAsync(
        config,
        RealtimeDataManager(config.rdm, simulation_mode=True),
        InterChunkFuser(config.inter_chunk, simulation_mode=True),
        IntraChunkSmoother(config.intra_chunk, simulation_mode=True),
        TaskLanguageManager(config.language),
        transport,
        robot,
    )
    try:
        _start_episode(client, robot, False)
        assert _wait_for_episode(client, 0, 10, 5, 30)
        assert client.pipeline_error is None
        assert robot.get_episode_result()["steps"] == 12
        assert len(robot.task_env.actions) == 12
        boundary_only = mode == "sync" and render_mode == "chunk_boundary"
        expected_captures = (2 if intra == "interpolation" else 3) if boundary_only else 13
        assert robot.task_env.observations_taken == expected_captures
        assert all(a.shape == (14,) and np.isfinite(a).all() for a in robot.task_env.actions)
        samples = [s for s in client.camera_preview.trajectory_samples if 'action_fitted' in s]
        assert len(samples) == 12
        np.testing.assert_allclose([s['action_fitted'] for s in samples], robot.task_env.actions)
        np.testing.assert_allclose([s['state'] for s in samples], robot.task_env.actions)
        assert all(len(s['action_raw']) == 14 for s in samples)
        assert all(a['timestamp'] <= b['timestamp'] for a, b in zip(samples, samples[1:]))
    finally:
        client.close()
        robot.close()


@pytest.mark.parametrize("mode", ["raw", "interpolation", "fitting"])
def test_sampling_and_gripper_semantics(mode):
    config = get_client_config()
    config.intra_chunk.intra_chunk_mode = mode
    config.intra_chunk.output_sample_ratio = 1
    config.intra_chunk.preserve_input_timestamps = True
    smoother = IntraChunkSmoother(config.intra_chunk, simulation_mode=True)
    smoother.set_action_layout(config.robots.aloha_robotwin.action_layout)
    timestamps = np.array([0, 0.01, 0.03, 0.04, 0.07])
    actions = np.arange(70, dtype=float).reshape(14, 5) / 100
    actions[6] = [0, 0, 1, 1, 0]
    actions[13] = [1, 1, 0, 0, 1]
    output, velocity, acceleration, times, _ = smoother.process(
        timestamps, actions, joint_indices=robot_joints(), step_indices=[6, 13]
    )
    assert output.shape == actions.shape
    if mode != "interpolation":
        np.testing.assert_array_equal(times, timestamps)
        np.testing.assert_array_equal(output[[6, 13]], actions[[6, 13]])
    assert set(np.unique(output[[6, 13]])) <= {0, 1}
    assert not velocity[[6, 13]].any() and not acceleration[[6, 13]].any()
    one = smoother.process(np.array([0.0]), actions[:, :1], step_indices=[6, 13])
    np.testing.assert_array_equal(one[0], actions[:, :1])


def robot_joints():
    return list(range(6)) + list(range(7, 13))


@pytest.mark.parametrize("mode", ["sync", "search_action", "smooth_velocity", "min_jerk"])
def test_transition_limit(mode):
    config = get_client_config().inter_chunk
    config.inter_chunk_mode = mode
    config.max_transition_steps = 5
    fuser = InterChunkFuser(config, simulation_mode=True)
    actions = np.arange(140, dtype=float).reshape(14, 10) / 100
    zeros = np.zeros_like(actions)
    output, velocity, acceleration, index = fuser.process(
        actions,
        zeros,
        zeros,
        np.arange(10) * 0.01,
        0,
        np.zeros(14),
        np.zeros(14),
        np.zeros(14),
        list(range(14)),
        [6, 13],
    )
    np.testing.assert_array_equal(output[:, 5:], actions[:, 5:])
    np.testing.assert_array_equal(output[[6, 13]], actions[[6, 13]])
    assert 0 <= index < 5
    assert np.isfinite(velocity).all() and np.isfinite(acceleration).all()


def test_cli_validation_and_no_local():
    parser = twin.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--task_name", "Task", "--intra_chunk_mode", "local"])
    args = parser.parse_args(["--task_name", "Task", "--no_expert_check"])
    with pytest.raises(ValueError, match="instruction"):
        twin.validate_args(args)
    args = parser.parse_args(["--tasks", "Task,Other", "--n_envs", "2", "--no_process_isolation"])
    with pytest.raises(ValueError, match="Parallel"):
        twin.validate_args(args)


def make_fake_root(folder):
    folder.mkdir()
    (folder / "envs/utils").mkdir(parents=True)
    (folder / "task_config").mkdir()
    (folder / "description/utils").mkdir(parents=True)
    (folder / "embodiment").mkdir()
    (folder / "envs/__init__.py").write_text(
        "from pathlib import Path\nCONFIGS_PATH = str(Path(__file__).resolve().parents[1] / 'task_config')\n"
    )
    (folder / "envs/utils/__init__.py").write_text("")
    (folder / "envs/utils/create_actor.py").write_text("class UnStableError(Exception): pass\n")
    (folder / "description/utils/generate_episode_instructions.py").write_text(
        "def generate_episode_descriptions(*args): return [{'unseen': ['Move the object'], 'seen': ['Move the object']}]\n"
    )
    (folder / "task_config/demo_clean.yml").write_text(
        "embodiment: [aloha-agilex]\ncamera: {head_camera_type: test}\n"
    )
    (folder / "task_config/_embodiment_config.yml").write_text(
        "aloha-agilex: {file_path: embodiment}\n"
    )
    (folder / "task_config/_camera_config.yml").write_text("test: {h: 16, w: 16}\n")
    (folder / "embodiment/config.yml").write_text("{}\n")
    (folder / "envs/Task.py").write_text("""import numpy as np
from types import SimpleNamespace
class Task:
    def setup_demo(self, now_ep_num, seed, **kwargs):
        self.seed=seed
        self.take_action_cnt=0
        self.step_lim=4
        self.eval_success=False
        self.state=np.zeros(14)
        self.robot=SimpleNamespace(get_left_arm_jointState=lambda: self.state[:7].tolist(), get_right_arm_jointState=lambda: self.state[7:].tolist())
    def set_instruction(self, instruction): self.instruction=instruction
    def get_obs(self):
        return {'joint_action': {'vector': self.state}, 'observation': {k: {'rgb': np.zeros((16,16,3),np.uint8)} for k in ('head_camera','left_camera','right_camera')}}
    def take_action(self, action, action_type):
        self.state=action.copy()
        self.take_action_cnt+=1
        self.eval_success=self.take_action_cnt==4
    def play_once(self):
        self.plan_success = self.seed % 2 == 1
        return {'info': {}}
    def check_success(self): return self.plan_success
    def close_env(self): pass
""")


def test_isolated_parallel_cli_recording_and_resume(tmp_path):
    root = tmp_path / "RoboTwin"
    make_fake_root(root)
    project = Path(twin.PROJECT_ROOT)
    launcher = tmp_path / "launch.py"
    launcher.write_text(f"""import sys
sys.path.insert(0, {str(project)!r})
sys.path.insert(0, {str(project / "test")!r})
from scripts import aloha_robotwin_eval as twin
from test_robotwin_evaluation import Transport
if __name__ == '__main__':
    twin.casa.ZMQClient = lambda config: Transport()
    original = twin._worker_command
    def command(*args):
        value = original(*args)
        value[2] = __file__
        return value
    twin._worker_command = command
    twin.main()
""")
    import uuid

    record_dir = "data/robotwin_test_" + uuid.uuid4().hex
    command = [
        sys.executable,
        str(launcher),
        "--task_name",
        "Task",
        "--robotwin_root",
        str(root),
        "--output_dir",
        str(tmp_path / "output"),
        "--run_id",
        "20261009-test",
        "--n_episodes",
        "4",
        "--n_envs",
        "2",
        "--worker_episodes",
        "1",
        "--n_action_steps",
        "8",
        "--record",
        "--record_dir",
        record_dir,
        "--no_video",
        "--mode",
        "async",
    ]
    import shutil

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=90)
        assert result.returncode == 0, result.stdout + result.stderr
        path = tmp_path / "output/evals/unseen/Task/20261009-test/stats.json"
        stats = json.loads(path.read_text())
        assert len(stats["episodes"]) == 4
        assert [e["episode"] for e in stats["episodes"]] == list(range(4))
        assert len({e["seed"] for e in stats["episodes"]}) == 4
        assert all(e["seed"] % 2 == 1 for e in stats["episodes"])
        import pyarrow.parquet as pq

        success = Path(stats["lerobot_dataset_paths"]["success"])
        parquet = sorted(success.rglob("*.parquet"))
        assert len(parquet) == 4
        for file in parquet:
            table = pq.read_table(file).to_pydict()
            assert len(table["action"]) == 4
            np.testing.assert_allclose(table["action"], table["observation.state"])
        resumed = subprocess.run(command, capture_output=True, text=True, timeout=30)
        assert resumed.returncode == 0, resumed.stdout + resumed.stderr
        assert json.loads(path.read_text())["episodes"] == stats["episodes"]
        suite_command = [
            sys.executable,
            str(launcher),
            "--tasks",
            "Task,Missing",
            "--robotwin_root",
            str(root),
            "--output_dir",
            str(tmp_path / "output"),
            "--run_id",
            "20261009-suite",
            "--n_episodes",
            "1",
            "--no_video",
            "--no_expert_check",
            "--instruction",
            "Move the object",
        ]
        suite = subprocess.run(suite_command, capture_output=True, text=True, timeout=30)
        assert suite.returncode == 1
        summary = json.loads(
            (tmp_path / "output/evals/unseen/suites/robotwin/20261009-suite/stats.json").read_text()
        )
        assert summary["num_completed_tasks"] == 1 and summary["num_failed_tasks"] == 1
        changed = subprocess.run(
            command + ["--mode", "sync"], capture_output=True, text=True, timeout=30
        )
        assert changed.returncode != 0 and "configuration differs" in changed.stderr
    finally:
        shutil.rmtree(project / record_dir, ignore_errors=True)


def test_checkpoint_reuses_actual_seed_and_instruction(tmp_path, monkeypatch):
    import types
    from client.robots.aloha_robotwin.environment import select_episode

    actor = types.ModuleType("envs.utils.create_actor")
    actor.UnStableError = type("UnStableError", (Exception,), {})
    descriptions = types.ModuleType("generate_episode_instructions")
    descriptions.generate_episode_descriptions = lambda *args: [{"unseen": ["first", "second"]}]
    monkeypatch.setitem(sys.modules, actor.__name__, actor)
    monkeypatch.setitem(sys.modules, descriptions.__name__, descriptions)
    checked = []

    class Environment(FakeTask):
        def setup_demo(self, now_ep_num, seed, **kwargs):
            self.seed = seed

        def play_once(self):
            checked.append(self.seed)
            self.plan_success = self.seed % 2 == 1
            return {"info": {}}

        def check_success(self):
            return self.plan_success

        def set_instruction(self, instruction):
            self.instruction = instruction

    checkpoint = tmp_path / "episode.json"
    with ThreadPoolExecutor(max_workers=1) as executor:
        first = select_episode(
            executor, Environment, {}, "Task", 0, 0, "unseen", True, None, 5, 5, checkpoint
        )
        restored = select_episode(
            executor, Environment, {}, "Task", 0, 0, "unseen", True, None, 5, 5, checkpoint
        )
        assert first[1:] == restored[1:] and first[2] == 1
        assert checked == [0, 1]
        with pytest.raises(RuntimeError, match="No valid"):
            select_episode(executor, Environment, {}, "Task", 1, 0, "unseen", True, None, 1, 5)


@pytest.mark.parametrize("message", ["target_pose cannot be None for move action.", "unexpected assertion"])
def test_expert_missing_grasp_skips_seed_only_for_known_assertion(monkeypatch, message):
    import types
    from client.robots.aloha_robotwin.environment import select_episode

    actor = types.ModuleType("envs.utils.create_actor")
    actor.UnStableError = type("UnStableError", (Exception,), {})
    descriptions = types.ModuleType("generate_episode_instructions")
    descriptions.generate_episode_descriptions = lambda *args: [{"unseen": ["Stack bowls"]}]
    monkeypatch.setitem(sys.modules, actor.__name__, actor)
    monkeypatch.setitem(sys.modules, descriptions.__name__, descriptions)
    checked, closed = [], []

    class Environment(FakeTask):
        def setup_demo(self, now_ep_num, seed, **kwargs):
            self.seed = seed

        def play_once(self):
            checked.append(self.seed)
            if self.seed == 0:
                raise AssertionError(message)
            self.plan_success = True
            return {"info": {}}

        def check_success(self):
            return self.plan_success

        def set_instruction(self, instruction):
            self.instruction = instruction

        def close_env(self):
            closed.append(self.seed)

    with ThreadPoolExecutor(max_workers=1) as executor:
        args = (executor, Environment, {}, "Task", 0, 0, "unseen", True, "Stack bowls", 2, 5)
        if message == "unexpected assertion":
            with pytest.raises(AssertionError, match=message):
                select_episode(*args)
            assert checked == [0] and closed == [0]
        else:
            env, instruction, seed = select_episode(*args)
            assert seed == 1 and instruction == "Stack bowls"
            assert checked == [0, 1] and closed == [0, 1]
            env.close_env()


def test_isolation_deadline_kills_nested_session(tmp_path):
    import psutil
    from client.simulation.evaluation import run_isolated_worker

    phase = tmp_path / "phase.json"
    child_file = tmp_path / "child"
    script = tmp_path / "hang.py"
    script.write_text(f"""import json,pathlib,subprocess,sys,time
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
pathlib.Path({str(child_file)!r}).write_text(str(child.pid))
now=time.time()
pathlib.Path({str(phase)!r}).write_text(json.dumps({{'started':now,'deadline':now+.5,'stage':'seed selection'}}))
time.sleep(60)
""")
    assert run_isolated_worker([sys.executable, str(script)], phase) == 124
    child = (
        psutil.Process(int(child_file.read_text()))
        if psutil.pid_exists(int(child_file.read_text()))
        else None
    )
    assert child is None or child.status() == psutil.STATUS_ZOMBIE


def test_supervisor_recovers_native_crash(monkeypatch):
    args = twin.build_parser().parse_args(["--task_name", "Task", "--n_episodes", "2"])
    partial = {"num_episodes": 1}
    complete = {"num_episodes": 2}
    outputs = iter([partial, partial, partial, complete, complete])
    codes = iter([-11, 0])
    monkeypatch.setattr(twin, "_read_supervised_stats", lambda *args: next(outputs))
    monkeypatch.setattr(twin, "_worker_command", lambda *args: [])
    monkeypatch.setattr(twin, "_run_worker_process", lambda *args: next(codes))
    monkeypatch.setattr("client.simulation.evaluation.time.sleep", lambda *args: None)
    assert twin._run_supervised_task(args, "Task", "20261009-test") == complete


def test_server_robotwin_options_preserve_defaults(monkeypatch):
    import run_server
    from conf.server_conf import get_vla_server_config

    monkeypatch.setattr(sys, "argv", ["run_server.py"])
    default = get_vla_server_config()
    port = default.zmq.port
    result = run_server.override_config_with_args(default, run_server.parse_args())
    assert result.zmq.port == port
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_server.py",
            "--model_type",
            "tao",
            "--server_port",
            "5566",
            "--video_keys",
            "head_camera",
            "left_camera",
            "right_camera",
            "--action_keys",
            "left_arm",
            "left_gripper",
            "right_arm",
            "right_gripper",
        ],
    )
    result = run_server.override_config_with_args(get_vla_server_config(), run_server.parse_args())
    assert result.zmq.port == "5566"
    assert result.models.tao.video_keys == ["head_camera", "left_camera", "right_camera"]


def test_worker_gpu_assignment_and_suite_aliases(monkeypatch, tmp_path):
    monkeypatch.setattr(
        sys, "argv", ["aloha_robotwin_eval.py", "--tasks", "Task,Other", "--gpu", "0,2"]
    )
    args = twin.build_parser().parse_args(sys.argv[1:])
    args.output_dir = str(tmp_path)
    args._worker_index = 3
    args._episode_start, args._episode_end = 0, 1
    command = twin._worker_command(args, "Task", "20261009-test", "20261009")
    worker = twin.build_parser().parse_args(command[3:])
    assert worker.gpu == "2" and worker.task_suite == "Task,Other"
    assert worker._worker_env_name == "Task"


@pytest.mark.parametrize("mode", ["raw", "interpolation", "fitting"])
@pytest.mark.parametrize("ratio", [1, 2])
def test_robotwin_pipeline_scopes_resampling_to_interpolation(mode, ratio):
    args = twin.build_parser().parse_args(
        [
            "--task_name",
            "Task",
            "--intra_chunk_mode",
            mode,
            "--intra_chunk_sample_ratio",
            str(ratio),
        ]
    )
    config = twin.configure_pipeline(get_client_config(), args)
    assert config.intra_chunk.preserve_input_timestamps
    assert config.intra_chunk.output_sample_ratio == (ratio if mode == "interpolation" else 1)
    smoother = IntraChunkSmoother(config.intra_chunk, simulation_mode=True)
    smoother.set_action_layout(config.robots.aloha_robotwin.action_layout)
    action = np.zeros((14, 5))
    result = smoother.process(
        np.arange(5) * 0.01, action, joint_indices=robot_joints(), step_indices=[6, 13]
    )
    assert result[0].shape[1] == (5 * ratio if mode == "interpolation" else 5)
