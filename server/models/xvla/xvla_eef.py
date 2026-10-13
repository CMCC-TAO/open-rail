import os
import threading
import time
from collections import Counter

import numpy as np
import torch

from ...utils.eef_utils.action_to_joints import ActionIKSolver
from models.modeling_xvla import XVLA
from models.processing_xvla import XVLAProcessor


class ModelVLA:
    _CAMERA_KEYS = ("cam.head", "cam.hand_left", "cam.hand_right")
    _ACTION_DIM = 20

    def __init__(self, config):
        self.cfg = config
        self._infer_lock = threading.Lock()

        model_path = os.path.expanduser(config.model_path)

        if not os.path.isdir(model_path):
            raise FileNotFoundError(f"X-VLA checkpoint not found: {model_path}")
        if config.rotation_type != "rot6d":
            raise ValueError(
                f"X-VLA EEF rotation_type must be 'rot6d', got {config.rotation_type!r}"
            )

        self.ik_solver = ActionIKSolver(
            urdf_path=config.urdf_path,
            reset_position=np.asarray(config.reset_position),
            link_name=config.link_name,
            eef_action_key=config.eef_action_key,
            joint_state_key=config.joint_state_key,
            rotation_type=config.rotation_type,
            ref_frame=config.ref_frame,
            rot6d_convention=config.rot6d_convention,
            **config.ik.to_dict(),
        )
        self.ik_solver.q_left_init = np.asarray(config.q_left_init)
        self.ik_solver.q_right_init = np.asarray(config.q_right_init)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = XVLAProcessor.from_pretrained(model_path)
        self.model = XVLA.from_pretrained(
            model_path,
            torch_dtype=torch.float32,
        ).to(self.device, dtype=torch.bfloat16)
        # self.model = XVLA.from_pretrained(
        #             model_path,
        #             torch_dtype=torch.float32,
        #         ).to(self.device)
        self.model.eval()

        if self.model.action_mode != "ee6d":
            raise ValueError(
                f"X-VLA checkpoint action_mode must be 'ee6d', got {self.model.action_mode!r}"
            )
        if self.model.action_space.dim_action != self._ACTION_DIM:
            raise ValueError(
                f"X-VLA action dimension must be {self._ACTION_DIM}, "
                f"got {self.model.action_space.dim_action}"
            )
        if not 0 <= config.domain_id < self.model.config.num_domains:
            raise ValueError(
                f"domain_id must be in [0, {self.model.config.num_domains}), got {config.domain_id}"
            )

        print(f"Loaded X-VLA EEF policy from {model_path} on {self.device}")

    @staticmethod
    def _normalize_language(language):
        if isinstance(language, np.ndarray):
            language = language.reshape(-1).tolist()
        if isinstance(language, (list, tuple)):
            if len(language) != 1:
                raise ValueError(f"Expected one language instruction, got {len(language)}")
            language = language[0]
        if not isinstance(language, str):
            raise TypeError(f"Language instruction must be a string, got {type(language)}")
        return language

    @classmethod
    def _to_xvla_layout(cls, eef):
        eef = np.asarray(eef, dtype=np.float32)
        if eef.shape[-1] != cls._ACTION_DIM:
            raise ValueError(
                f"EEF vector must have {cls._ACTION_DIM} dimensions, got {eef.shape[-1]}"
            )
        return np.concatenate(
            [eef[..., :9], eef[..., 18:19], eef[..., 9:18], eef[..., 19:20]],
            axis=-1,
        )

    @classmethod
    def _to_ik_layout(cls, action):
        action = np.asarray(action, dtype=np.float32)
        if action.shape[-1] != cls._ACTION_DIM:
            raise ValueError(
                f"X-VLA action must have {cls._ACTION_DIM} dimensions, got {action.shape[-1]}"
            )
        return np.concatenate(
            [action[..., :9], action[..., 10:19], action[..., 9:10], action[..., 19:20]],
            axis=-1,
        )

    def infer(self, sequence):
        with self._infer_lock:
            return self._infer(sequence)

    def _infer(self, sequence):
        data = sequence[0]
        obs = data["obs"].copy()
        action = self.predict_eef(obs)

        start_time = time.perf_counter()
        predicted_action = self.ik_solver.process_chunk_batch(
            action,
            state=np.asarray(obs["state"]),
        )
        if predicted_action is None:
            raise RuntimeError("X-VLA action could not be converted by the IK solver")

        solvers = (self.ik_solver.left_solver, self.ik_solver.right_solver)
        stop_reasons = Counter(reason for solver in solvers for reason in solver.last_stop_reasons)
        print(
            time.perf_counter() - start_time, "IK action shape:", predicted_action.shape,
            "successes:", self.ik_solver.last_successes.sum(axis=0).tolist(),
            "QP iterations:", sum(int(solver.last_iterations.sum()) for solver in solvers),
            "stops:", dict(stop_reasons),
        )
        return {
            "type": "vla_action",
            "pred_action": predicted_action,
            "ref_timestamp": data["ref_timestamp"],
            "loc_timestamp": data["loc_timestamp"],
            "ext": {},
        }

    def predict_eef(self, obs):
        obs = obs.copy()
        missing_keys = [key for key in self._CAMERA_KEYS if key not in obs]
        if missing_keys:
            raise KeyError(f"Missing X-VLA camera observations: {missing_keys}")

        language = self._normalize_language(obs["language"])
        eef_state = self.ik_solver.process_joint_state(np.asarray(obs["state"]))
        proprio = self._to_xvla_layout(eef_state)
        images = [np.asarray(obs[key], dtype=np.uint8) for key in self._CAMERA_KEYS]
        inputs = self.processor(images=images, language_instruction=language)

        model_dtype = next(self.model.parameters()).dtype
        model_inputs = {}
        for key, value in inputs.items():
            if value.is_floating_point():
                model_inputs[key] = value.to(self.device, dtype=model_dtype)
            else:
                model_inputs[key] = value.to(self.device)
        model_inputs["proprio"] = torch.from_numpy(proprio).unsqueeze(0).to(
            self.device, dtype=model_dtype
        )
        model_inputs["domain_id"] = torch.tensor(
            [self.cfg.domain_id], device=self.device, dtype=torch.long
        )

        start_time = time.time()
        with torch.inference_mode():
            action = self.model.generate_actions(
                **model_inputs,
                steps=self.cfg.denoising_steps,
            )
        action = action.squeeze(0).float().cpu().numpy()
        action = self._to_ik_layout(action)
        print(time.time() - start_time, "EEF action shape:", action.shape)
        return action
