import json
import os
import threading
import time

import numpy as np
import torch

from gr00t.data.embodiment_tags import EmbodimentTag
from gr00t.policy.gr00t_policy import Gr00tPolicy

from ...utils.eef_utils.action_to_joints import ActionIKSolver


class ModelVLA:
    """GR00T N1.7 EEF Vision-Language-Action adapter.

    This wrapper is designed for GR00T N1.7 checkpoints that are loaded via the
    GR00T policy API and then converted into robot joint commands through an IK
    solver. It keeps the same interface as the other VLA adapters in this repo.
    """

    _CAMERA_KEYS = {
        "cam_top_head": "cam.head",
        "cam_left_wrist": "cam.hand_left",
        "cam_right_wrist": "cam.hand_right",
    }

    def _resolve_embodiment_tag(self):
        configured_tag = self.cfg.get("embodiment_tag", "new_embodiment")
        try:
            return EmbodimentTag.resolve(configured_tag)
        except ValueError:
            if str(configured_tag).lower() == "a2d":
                return EmbodimentTag.NEW_EMBODIMENT
            raise

    def _configure_state_indices(self, model_path, embodiment_tag):
        statistics = getattr(self.policy.processor, "statistics", None)
        if not statistics:
            for relative_path in (
                "statistics.json",
                os.path.join("experiment_cfg", "dataset_statistics.json"),
            ):
                statistics_path = os.path.join(model_path, relative_path)
                if os.path.exists(statistics_path):
                    with open(statistics_path, "r", encoding="utf-8") as file:
                        statistics = json.load(file)
                    break

        tag_statistics = (statistics or {}).get(embodiment_tag.value, {}).get("state", {})
        state_keys = self.policy.modality_configs["state"].modality_keys
        missing_keys = [key for key in state_keys if key not in tag_statistics]
        if missing_keys:
            raise ValueError(
                f"Missing state statistics for {embodiment_tag.value}: {missing_keys}"
            )

        self.state_indices = {}
        start_index = 0
        for key in state_keys:
            key_statistics = tag_statistics[key]
            dimension_source = next(
                (key_statistics[name] for name in ("mean", "min", "q01") if name in key_statistics),
                None,
            )
            if dimension_source is None:
                raise ValueError(f"Cannot determine state dimension for {key}")
            end_index = start_index + int(np.asarray(dimension_source).size)
            self.state_indices[key] = slice(start_index, end_index)
            start_index = end_index

        self.state_dimension = start_index

    def __init__(self, config):
        self.cfg = config
        self._infer_lock = threading.Lock()
        model_path = self.cfg["model_path"]

        self.ik_solver = ActionIKSolver(
            urdf_path=self.cfg["urdf_path"],
            reset_position=np.array(self.cfg["reset_position"]),
            link_name=self.cfg["link_name"],
            eef_action_key=self.cfg["joint_action_key"],
            joint_state_key=self.cfg["joint_state_key"],
            rotation_type=self.cfg["rotation_type"],
            ref_frame=self.cfg["ref_frame"],
            rot6d_convention=self.cfg["rot6d_convention"],
        )
        self.ik_solver.q_left_init = np.array(self.cfg["q_left_init"])
        self.ik_solver.q_right_init = np.array(self.cfg["q_right_init"])

        device = "cuda" if torch.cuda.is_available() else "cpu"
        embodiment_tag = self._resolve_embodiment_tag()
        self.policy = Gr00tPolicy(
            model_path=model_path,
            embodiment_tag=embodiment_tag,
            device=device,
        )
        self._configure_state_indices(model_path, embodiment_tag)

        video_keys = self.policy.modality_configs["video"].modality_keys
        unsupported_video_keys = [key for key in video_keys if key not in self._CAMERA_KEYS]
        if unsupported_video_keys:
            raise ValueError(f"Unsupported checkpoint video keys: {unsupported_video_keys}")

        print("Loaded GR00T N1.7 EEF policy")
        print(getattr(self.policy, "model", None))

    def infer(self, sequence):
        with self._infer_lock:
            return self._infer(sequence)

    def _infer(self, sequence):
        data = sequence[0]
        obs = data["obs"].copy()
        model_state = self.ik_solver.process_joint_state(np.asarray(obs["state"]))
        model_state = np.asarray(model_state, dtype=np.float32)
        if model_state.size != self.state_dimension:
            raise ValueError(
                f"Processed state dimension must be {self.state_dimension}, got {model_state.size}"
            )
        model_state = model_state[None, None]

        language = obs["language"]
        if isinstance(language, np.ndarray):
            language = language.reshape(-1).tolist()
        if isinstance(language, (list, tuple)):
            if len(language) != 1:
                raise ValueError(f"Expected one language instruction, got {len(language)}")
            language = language[0]
        if not isinstance(language, str):
            raise TypeError(f"Language instruction must be a string, got {type(language)}")

        video_keys = self.policy.modality_configs["video"].modality_keys
        inp_obs = {
            "video": {
                key: np.asarray(obs[self._CAMERA_KEYS[key]], dtype=np.uint8)[None, None]
                for key in video_keys
            },
            "state": {
                key: model_state[..., state_slice]
                for key, state_slice in self.state_indices.items()
            },
            "language": {self.policy.language_key: [[language]]},
        }

        start_time = time.time()
        ext_result = {}
        result = self.policy.get_action(inp_obs)

        if isinstance(result, tuple):
            predicted_action, info = result
        else:
            predicted_action, info = result, {}

        if isinstance(info, dict) and "prob_progress" in info:
            ext_result["prob_progress"] = info["prob_progress"]

        if isinstance(predicted_action, dict):
            if isinstance(predicted_action.get("prob_progress"), np.ndarray):
                ext_result["prob_progress"] = predicted_action["prob_progress"]

            action_parts = []
            action_keys = self.policy.modality_configs["action"].modality_keys
            for key in action_keys:
                value = np.asarray(predicted_action[key])
                if value.ndim == 3:
                    value = value[0]
                elif value.ndim == 1:
                    value = value[:, None]
                if value.ndim != 2:
                    raise ValueError(f"Unexpected action shape for {key}: {value.shape}")
                action_parts.append(value)
            predicted_action = np.concatenate(action_parts, axis=1)

        predicted_action = self.ik_solver.process_chunk(
            predicted_action,
            state=np.asarray(obs["state"]),
        )
        print(time.time() - start_time, "action shape:", predicted_action.shape)
        return {
            "type": "vla_action",
            "pred_action": predicted_action,
            "ref_timestamp": data["ref_timestamp"],
            "loc_timestamp": data["loc_timestamp"],
            "ext": ext_result,
        }
