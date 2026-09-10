import json
import os
import sys
import time

import numpy as np
from PIL import Image


def _ensure_repo_on_path(repo_path: str) -> None:
    if repo_path not in sys.path:
        sys.path.insert(0, repo_path)


def _load_compile_warmup_prompts(cfg: dict):
    """A representative spread of prompt lengths to pre-warm compiled buckets.
    """
    explicit = cfg.get("compile_warmup_prompts")
    if explicit:
        return list(explicit)

    dataset_name = str(cfg.get("dataset_name", ""))
    language_key = cfg.get(
        "compile_warmup_language_key",
        dataset_name[: -len("_generalist")]
        if dataset_name.endswith("_generalist")
        else dataset_name,
    )
    language_cmd_path = cfg.get("language_cmd_path")
    if not language_cmd_path:
        print(
            "[ZLA][dm05] compile warmup: no language_cmd_path or "
            "compile_warmup_prompts in config; using the synthetic sweep.",
            flush=True,
        )
        return None
    try:
        with open(language_cmd_path, encoding="utf-8") as f:
            prompts = json.load(f).get(language_key)
        if prompts:
            return list(prompts)
        print(
            f"[ZLA][dm05] compile warmup: no entry {language_key!r} in "
            f"{language_cmd_path}; using the synthetic sweep.",
            flush=True,
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"[ZLA][dm05] compile warmup: could not read {language_cmd_path} "
            f"({exc!r}); using the synthetic sweep.",
            flush=True,
        )
    return None


def _to_pil(image) -> Image.Image:
    """Convert one observation camera frame to a PIL RGB image."""
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

    CAMERA_KEYS = ("cam.head", "cam.hand_left", "cam.hand_right")

    def __init__(self, config):
        self.cfg = config
        _ensure_repo_on_path(str(self.cfg["repo_path"]))

        from opendm.infer.policy import DM05Policy

        # How many of the predicted steps the caller executes per cycle.
        self.execute_horizon = int(self.cfg.get("execute_horizon", 16))
        self._logged_action_shape = False

        self.policy = DM05Policy.from_checkpoint(
            str(self.cfg["model_path"]),
            backend=str(self.cfg.get("backend", "fast")),
            diffusion_steps=int(self.cfg.get("diffusion_steps", 10)),
            # Left as None these come from the checkpoint's norm_stats.json
            # instead of being restated in the deploy config.
            output_action_dim=self.cfg.get("action_dim"),
            state_pad_to=self.cfg.get("state_pad_to"),
            vision_trt_engine_path=self.cfg.get("vision_trt_engine_path"),
            vision_attn_implementation=str(
                self.cfg.get("vision_attn_implementation", "flash_attention_2")
            ),
            # None means "use the checkpoint's own config.json".
            chunk_size=self.cfg.get("chunk_size"),
            dataset_name=self.cfg.get("dataset_name"),
            robot_type=self.cfg.get("robot_type"),
            # Ignored once the checkpoint carries a contract; still the only
            # way to serve a checkpoint written before run_config.json existed.
            action_mode=os.environ.get("DM05_ACTION_MODE") or self.cfg.get("action_mode"),
            compile_warmup_prompts=_load_compile_warmup_prompts(self.cfg),
        )
        print(f"[ZLA][dm05] backend={self.policy.backend_label}", flush=True)

    def infer(self, sequence, verbose: bool = False):
        data = sequence[0]
        obs = data["obs"]

        images = [_to_pil(obs[key]) for key in self.CAMERA_KEYS]
        state = np.asarray(obs["state"], dtype=np.float32).tolist()
        language = obs["language"]
        prompt = language[0] if isinstance(language, (list, tuple)) else language

        if verbose:
            for name, image in zip(self.CAMERA_KEYS, images):
                print(name, image.size)
            print("state", len(state), "prompt", prompt)

        time0 = time.time()
        actions = self.policy.predict(images=images, state=state, prompt=prompt)
        if not np.all(np.isfinite(actions)):
            return {
                "type": "vla_status",
                "status": "not_ready",
                "reason": "DM05 produced non-finite actions",
            }

        if not self._logged_action_shape:
            print(
                f"[ZLA][dm05] backend={self.policy.backend_label} "
                f"action_shape={actions.shape} "
                f"model_latency_ms={self.policy.last_latency_sec * 1000:.1f}",
                flush=True,
            )
            self._logged_action_shape = True
        print(time.time() - time0, "action shape:", actions.shape)

        return {
            "type": "vla_action",
            "pred_action": actions[: self.execute_horizon],
            "ref_timestamp": data["ref_timestamp"],
            "loc_timestamp": data["loc_timestamp"],
            "ext": {},
        }

    def reset(self):
        return None
