import os
import sys
import time

import numpy as np
from PIL import Image


def _ensure_repo_on_path(repo_path: str) -> None:
    if repo_path not in sys.path:
        sys.path.insert(0, repo_path)


def _to_pil(image) -> Image.Image:
    """Convert one observation camera frame to a PIL RGB image.
    """
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    array = np.asarray(image)
    if array.dtype != np.uint8:
        array = np.clip(array * 255.0 if array.max() <= 1.0 else array, 0, 255).astype(np.uint8)
    if array.ndim == 3 and array.shape[-1] == 3:
        array = array[:, :, ::-1]
    return Image.fromarray(array).convert("RGB")


class ModelVLA:
    """DM0.5 policy: three RGB cameras + language + state -> action chunk."""

    def __init__(self, config):
        self.cfg = config
        _ensure_repo_on_path(str(self.cfg["repo_path"]))

        from opendm.constants.robot import ActionMode
        from opendm.exp.dm05_exp import (
            DM05DataConfig,
            DM05Exp,
            DM05InferenceConfig,
            DM05ModelConfig,
        )

        model_config = DM05ModelConfig(
            model_name_or_path=str(self.cfg["model_path"]),
            chunk_size=int(self.cfg.get("chunk_size", 50)),
            vision_attn_implementation=str(
                self.cfg.get("vision_attn_implementation", "flash_attention_2")
            ),
        )
        action_mode_str = os.environ.get(
            "DM05_ACTION_MODE", str(self.cfg.get("action_mode", "relative"))
        ).lower()
        action_mode = (
            ActionMode.ABSOLUTE if action_mode_str == "absolute" else ActionMode.RELATIVE
        )
        data_config = DM05DataConfig(
            dataset_name=str(self.cfg.get("dataset_name", "a2d_tidyup_generalist")),
            action_mode=action_mode,
        )
        inference_config = DM05InferenceConfig(
            backend=str(self.cfg.get("backend", "fast")),
            output_action_dim=int(self.cfg["action_dim"]),
            image_prompts=["Head", "Left wrist", "Right wrist"],
            vision_trt_engine_path=self.cfg.get("vision_trt_engine_path") or None,
            diffusion_steps=int(self.cfg.get("diffusion_steps", 10)),
        )
        self.exp = DM05Exp(
            task="inference",
            model_config=model_config,
            data_config=data_config,
            inference_config=inference_config,
        )
        self.exp._initialize_inference_runtime()

        self.robot_type = self.cfg.get("robot_type") or None
        self.state_pad_to = int(self.cfg.get("state_pad_to", 0)) or None
        self._logged_action_shape = False

    def _pad_state(self, state: list[float]) -> list[float]:
        if self.state_pad_to is None:
            return state
        pad_width = self.state_pad_to - len(state)
        if pad_width < 0:
            raise ValueError(
                f"state length {len(state)} exceeds configured state_pad_to={self.state_pad_to}"
            )
        return state + [0.0] * pad_width

    def infer(self, sequence, verbose: bool = False):
        data = sequence[0]
        obs = data["obs"]

        images = [
            _to_pil(obs["cam.head"]),
            _to_pil(obs["cam.hand_left"]),
            _to_pil(obs["cam.hand_right"]),
        ]
        state = np.asarray(obs["state"], dtype=np.float32).tolist()
        state = self._pad_state(state)
        language = obs["language"]
        prompt = language[0] if isinstance(language, (list, tuple)) else language

        if verbose:
            for name, image in zip(["head", "hand_left", "hand_right"], images):
                print(name, image.size)
            print("state", len(state), "prompt", prompt)

        time0 = time.time()
        model_input = self.exp.inference_config._prepare_model_input(
            text=prompt,
            images=images,
            states=state,
            robot_type=self.robot_type,
        )
        actions = self.exp.inference_config._predict(model_input)
        if not np.all(np.isfinite(actions)):
            return {
                "type": "vla_status",
                "status": "not_ready",
                "reason": "DM05 produced non-finite actions",
            }

        if not self._logged_action_shape:
            print(
                f"[ZLA][dm05] backend={self.exp.inference_config.backend} "
                f"action_shape={actions.shape} "
                f"model_latency_ms={self.exp.inference_config.last_model_latency_sec * 1000:.1f}",
                flush=True,
            )
            self._logged_action_shape = True
        print(time.time() - time0, "action shape:", actions.shape)

        return {
            "type": "vla_action",
            "pred_action": actions,
            "ref_timestamp": data["ref_timestamp"],
            "loc_timestamp": data["loc_timestamp"],
            "ext": {},
        }

    def reset(self):
        return None
