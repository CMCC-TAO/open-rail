import logging
import time
from typing import Callable, Optional, Sequence

import numpy as np
import pandas as pd
from ti5_t170c_sdk import Ti5Robot, create_camera
from ti5_t170c_sdk._constants import end_effector_profile

from ..base_robot import RobotBase


class RobotBody(RobotBase):
    """TI5 T170c VLA adapter. Model width follows the end-effector profile."""

    def __init__(self, config):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.cfg = config
        self._bind_end_effector_profile()

        cam_cfg = self.cfg.get("camera", {})
        # Initialize DDS before ZMQ camera traffic so joint discovery is not starved.
        self.robot = Ti5Robot(self.cfg, hand_type=self._profile.name)
        self._wait_for_joint_state(timeout_s=float(cam_cfg.get("joint_warmup_s", 5.0)))
        self.camera = create_camera(cam_cfg)

        self.current_state = np.zeros(self.state_dim or self.action_dim, dtype=np.float32)
        state, _ = self.robot.full_joint_states()
        self.current_state = self._trim_state(state)
        self.current_timestamp = 0
        self.hand_count = 0

    def control_robot(self, action):
        """Apply VLA action chunk to the robot.

        Only gradual/stepwise segments inside the model action vector are driven
        here (arm + hand, dim=26). Segments with policy='manual' (e.g. head) are
        Web Robot Control only via execute_action / _control_robot.
        """
        action = np.asarray(action, dtype=np.float32).reshape(-1)
        if action.size != self.action_dim:
            raise ValueError(
                f"hand_type {self._profile.name!r} expects action_dim {self.action_dim} "
                f"({self._profile.left.dof}+{self._profile.right.dof} end effector), "
                f"got {action.size}"
            )
        segments = {
            name: action[v["start"] : v["end"]]
            for name, v in self.action_layout.items()
            if v.get("policy") != "manual"
        }

        if "arm" in segments:
            self.execute_action({"arm": segments["arm"].tolist()})

        hand_freq = int(self.cfg.get("hand_freq", 1))
        if "hand" in segments and self.hand_count % hand_freq == 0:
            self.hand_count = 0
            # Hand uses Inspire hardware units [0, 1000] (matches TAO / training).
            hand_cmd = np.clip(segments["hand"], 0.0, 1000.0)
            self.execute_action({"hand": hand_cmd.tolist()})
        self.hand_count += 1

        if "waist" in segments:
            self.execute_action({"waist": segments["waist"].tolist()})

    def execute_action(self, data: dict) -> None:
        if "arm" in data:
            self.logger.debug("execute_action arm=%s", data["arm"])
            self.robot.move_arm(data["arm"])
        if "hand" in data:
            self.logger.info("execute_action hand=%s", data["hand"])
            self.robot.move_hand(data["hand"])
        if "head" in data:
            self.logger.info("execute_action head=%s", data["head"])
            self.robot.move_head(data["head"])
        if "waist" in data:
            self.robot.move_waist(data["waist"])

    def reset_robot(self, target_pose=None, mode="default"):
        if target_pose is None:
            if mode == "default":
                target_pose = np.array(self.cfg["reset_robot_pos"], dtype=np.float32)
            elif mode == "zero":
                target_pose = np.zeros(self.action_dim, dtype=np.float32)
            else:
                self.logger.warning("reset_robot skipped: unknown mode=%s", mode)
                return
        else:
            target_pose = np.asarray(target_pose, dtype=np.float32)

        # reset_robot_pos is arm+hand (26); skip slices that do not fit the pose.
        segments = {
            name: target_pose[v["start"] : v["end"]]
            for name, v in self.action_layout.items()
            if v["end"] <= target_pose.size
        }

        current_obs = self.retrieve_observation()
        if current_obs is None:
            current_positions = self.current_state[:14]
        else:
            current_positions = np.asarray(current_obs["obs.state"][:14], dtype=np.float32)

        target_positions = np.asarray(segments.get("arm", target_pose[:14]), dtype=np.float32)
        dis = np.abs(current_positions - target_positions)
        mask = dis > np.deg2rad(0.01)

        if not np.any(mask):
            if "arm" in segments:
                self.execute_action({"arm": target_positions.tolist()})
        else:
            trajs = self.ruckig_planning(current_positions, target_positions)
            for i, traj in enumerate(trajs):
                print(f"\r{i}", end="")
                self.execute_action({"arm": traj})
                time.sleep(0.01)

        if "hand" in segments:
            self.execute_action({"hand": segments["hand"].tolist()})
        if "head" in segments and segments["head"].size > 0:
            self.execute_action({"head": segments["head"].tolist()})
        if "waist" in segments and segments["waist"].size > 0:
            self.execute_action({"waist": segments["waist"].tolist()})

    def _safe_image_nearest(self, stream: str, ref_timestamp: int):
        try:
            return self.camera.get_image_nearest(stream, ref_timestamp)
        except (RuntimeError, KeyError):
            return None, None

    def _wait_for_joint_state(self, timeout_s: float = 3.0) -> None:
        if self._wait_for_arm_samples(timeout_s):
            return

        self.logger.warning(
            "Arm joint state not received within %.1fs; resetting DDS bridge once.",
            timeout_s,
        )
        from ti5_t170c_sdk._dds_bridge import shutdown_bridge
        from ti5_t170c_sdk._network import ensure_cyclonedds_uri, parse_host_from_uri

        peer_ip = parse_host_from_uri(self.cfg.get("camera", {}).get("forwarder_uri"))
        ensure_cyclonedds_uri(peer_ip=peer_ip, force=True)
        shutdown_bridge()
        self.robot = Ti5Robot(self.cfg, hand_type=self._profile.name)
        if not self._wait_for_arm_samples(min(timeout_s, 2.0)):
            self.logger.warning(
                "Arm joint state still unavailable after DDS bridge reset."
            )

    def _wait_for_arm_samples(self, timeout_s: float) -> bool:
        deadline = time.monotonic() + max(0.0, timeout_s)
        while time.monotonic() < deadline:
            _, ts = self.robot.arm_joint_states()
            if ts > 0:
                return True
            time.sleep(0.05)
        return False

    def retrieve_observation(self):
        try:
            cam_names = dict(self.cfg["camera"]["names"])
            cam_ref = self.cfg["camera"]["ref"]
            ref_stream = cam_names[cam_ref]

            state, _ = self.robot.full_joint_states()
            self.current_state = self._trim_state(state)

            image, ref_timestamp = self.camera.get_latest_image(ref_stream)
            if self.current_timestamp == ref_timestamp:
                return None
            self.current_timestamp = ref_timestamp

            result = {"ref_timestamp": ref_timestamp}
            result[f"cam.{cam_ref}"] = image[:, :, ::-1] if image.ndim == 3 else image

            for key, stream in cam_names.items():
                if key == cam_ref:
                    continue
                image, _ = self._safe_image_nearest(stream, ref_timestamp)
                if image is None:
                    self.logger.warning("missing camera stream: %s", stream)
                    continue
                result[f"cam.{key}"] = image[:, :, ::-1] if image.ndim == 3 else image

            result["obs.state"] = self.current_state[: self.action_dim].copy()
            return result
        except Exception as exc:
            self.logger.exception("retrieve_observation failed: %s", exc)
            return None

    def close(self):
        self.camera.close()
        self.robot.shutdown()
        self.logger.info("TI5 T170c robot closed")

    def load_action_data(self, parquet_path, key="action"):
        """Load replay frames whose length is 14, action_dim, or head.end.

        Arm-only frames keep the open end effector from reset_robot_pos.
        Any other length is rejected so a short gripper trace cannot be
        copied onto a dexterous hand.
        """
        df = pd.read_parquet(parquet_path)
        raw = df[key].tolist()
        default = np.asarray(
            self.cfg.get("reset_robot_pos", [0.0] * self.action_dim),
            dtype=np.float32,
        )
        if default.shape[0] < self.action_dim:
            default = np.resize(default, self.action_dim)
        else:
            default = default[: self.action_dim].copy()

        arm_s = self.action_layout["arm"]["start"]
        arm_e = self.action_layout["arm"]["end"]
        hand_s = self.action_layout["hand"]["start"]
        hand_e = self.action_layout["hand"]["end"]
        head = self.action_layout.get("head")

        accepted = {arm_e, self.action_dim}
        if head is not None:
            accepted.add(head["end"])

        processed_data = []
        for ele in raw:
            src = np.asarray(ele, dtype=np.float32).reshape(-1)
            if src.shape[0] not in accepted:
                raise ValueError(
                    f"hand_type {self._profile.name!r} expects replay length "
                    f"{sorted(accepted)} ({self._profile.left.dof}+{self._profile.right.dof}), "
                    f"got {src.shape[0]}"
                )
            if src.shape[0] == arm_e:
                # Arm-only frames keep the open end effector from reset_robot_pos.
                out = default.copy()
                out[arm_s:arm_e] = src[arm_s:arm_e]
            else:
                out = src.copy()
                out[hand_s:hand_e] = np.clip(src[hand_s:hand_e], 0.0, 1000.0)
            processed_data.append(out)
        return processed_data

    def default_replay_trajectories(
        self,
        parquet_path,
        accelerate: bool = True,
        accelerate_times: int = 2,
        sleep_s: float = 0.05,
    ) -> None:
        """Replay arm + hand only (default fast path)."""
        trajs = self.load_action_data(parquet_path=parquet_path)
        if not accelerate:
            accelerate_times = 1

        arm_e = self.action_layout["arm"]["end"]
        hand_s = self.action_layout["hand"]["start"]
        hand_e = self.action_layout["hand"]["end"]

        for idx, traj in enumerate(trajs):
            if idx % accelerate_times != 0:
                continue
            frame = np.asarray(traj, dtype=np.float32)
            self.execute_action({"arm": frame[:arm_e].tolist()})
            self.execute_action(
                {"hand": np.clip(frame[hand_s:hand_e], 0.0, 1000.0).tolist()}
            )
            time.sleep(sleep_s)

    def replay_trajectories(
        self,
        parquet_path,
        use_default: bool = True,
        accelerate: bool = True,
        accelerate_times: int = 2,
        exclude_path: Sequence[str] = ("place",),
        progress_fn: Optional[Callable] = None,
        sleep_s: float = 0.05,
    ) -> None:
        """Replay teleoperation trajectory on real hardware."""
        try:
            if self.cfg.get("hand_type") == "hand":
                use_default = False

            if use_default:
                self.default_replay_trajectories(
                    parquet_path=parquet_path,
                    accelerate=accelerate,
                    accelerate_times=accelerate_times,
                    sleep_s=sleep_s,
                )
                return

            trajs = self.load_action_data(parquet_path=parquet_path)
            path_str = str(parquet_path)
            for token in exclude_path:
                if token in path_str:
                    accelerate = False
                    break

            if not accelerate:
                accelerate_times = 1

            for idx, traj in enumerate(trajs):
                if progress_fn is not None:
                    progress_fn(idx, len(trajs), traj)
                if idx % accelerate_times != 0:
                    continue
                self._execute_replay_frame(traj)
                time.sleep(sleep_s)
        except Exception as exc:
            self.logger.exception("Replay %s failed: %s", parquet_path, exc)

    def _execute_replay_frame(self, traj) -> None:
        """Dispatch one normalized frame for segments present in action_layout."""
        frame = np.asarray(traj, dtype=np.float32).reshape(-1)
        arm_e = self.action_layout["arm"]["end"]
        hand_s = self.action_layout["hand"]["start"]
        hand_e = self.action_layout["hand"]["end"]
        head = self.action_layout.get("head")
        waist = self.action_layout.get("waist")

        self.execute_action({"arm": frame[:arm_e].tolist()})
        if frame.shape[0] >= hand_e:
            self.execute_action(
                {"hand": np.clip(frame[hand_s:hand_e], 0.0, 1000.0).tolist()}
            )
        if head is not None and frame.shape[0] >= head["end"]:
            self.execute_action(
                {"head": frame[head["start"] : head["end"]].tolist()}
            )
        if waist is not None and frame.shape[0] >= waist["end"]:
            self.execute_action(
                {"waist": frame[waist["start"] : waist["end"]].tolist()}
            )

    def _trim_state(self, state) -> np.ndarray:
        """Trim SDK full_joint_states to state_dim (arm+hand[+manual head])."""
        n = self.state_dim or self.action_dim
        return np.asarray(state, dtype=np.float32)[:n].copy()

    def _bind_end_effector_profile(self) -> None:
        """Check the yaml hand segment against the SDK profile before opening DDS."""
        hand_type = self.cfg.get("hand_type") or "hand"
        self._profile = end_effector_profile(hand_type)
        hand = self.action_layout["hand"]
        width = hand["end"] - hand["start"]
        if width != self._profile.hand_dof:
            raise ValueError(
                f"hand_type {self._profile.name!r} is "
                f"{self._profile.left.dof}+{self._profile.right.dof}, "
                f"but action_layout.hand width is {width}"
            )
        head = self.action_layout.get("head")
        if head is not None and head["start"] != hand["end"]:
            raise ValueError(
                f"head.start must equal hand.end ({hand['end']}), got {head['start']}"
            )

    def _control_robot(self, data):
        """Split TI5 l_hand/r_hand by profile width, then keep the base path."""
        payload = dict(data)
        left = payload.pop("l_hand", None)
        right = payload.pop("r_hand", None)
        if left is not None or right is not None:
            left_dof = self._profile.left.dof
            right_dof = self._profile.right.dof
            if left is None:
                left = [-1000] * left_dof
            if right is None:
                right = [-1000] * right_dof
            if len(left) != left_dof or len(right) != right_dof:
                raise ValueError(
                    f"hand_type {self._profile.name!r} expects l_hand {left_dof} and "
                    f"r_hand {right_dof}, got {len(left)} and {len(right)}"
                )
            current = self._current_pose("hand")
            target = self._target_pose(current, list(left) + list(right))
            self.execute_action({"hand": target.tolist()})
        super()._control_robot(payload)
