"""pi0.5 adapter with low-memory loading and optional torch.compile."""

from dataclasses import asdict, replace
from importlib.util import find_spec
import os
from pathlib import Path
import sys
import time

import numpy as np


def _ensure_openpi_client_on_path():
    """Find the bundled client beside the OpenPI source selected by PYTHONPATH."""
    if find_spec("openpi_client") is not None:
        return
    import openpi

    for package_path in openpi.__path__:
        client_src = Path(package_path).resolve().parents[1] / "packages/openpi-client/src"
        if (client_src / "openpi_client").is_dir():
            sys.path.insert(0, str(client_src))
            return


def _stream_checkpoint(model, weight_path, device):
    """Read one tensor at a time, then assign weights without copying the model."""
    from safetensors import safe_open

    expected = model.state_dict()
    with safe_open(str(weight_path), framework="pt", device="cpu") as checkpoint:
        keys = set(checkpoint.keys())
        aliases = {k: v for k, v in (checkpoint.metadata() or {}).items() if k in expected}
    if keys | aliases.keys() != expected.keys() or not set(aliases.values()) <= keys:
        raise ValueError("Checkpoint keys do not match the model")

    weights = {}
    for index, name in enumerate(sorted(keys), 1):
        # Close each mapping after the synchronous copy to keep CPU RSS low.
        with safe_open(str(weight_path), framework="pt", device="cpu") as checkpoint:
            weights[name] = checkpoint.get_tensor(name).to(device=device, dtype=expected[name].dtype, copy=True)
        if index % 128 == 0 or index == len(keys):
            print(f"[pi05_pytorch] loaded tensors: {index}/{len(keys)}", flush=True)
    weights.update({alias: weights[source] for alias, source in aliases.items()})
    model.load_state_dict(weights, assign=True)
    for alias, source in aliases.items():
        parent, _, leaf = alias.rpartition(".")
        source_parent, _, source_leaf = source.rpartition(".")
        setattr(model.get_submodule(parent), leaf, getattr(model.get_submodule(source_parent), source_leaf))
    model.requires_grad_(False).to(device)
    for module in model.modules():
        if hasattr(module, "original_inv_freq"):
            module.original_inv_freq = module.inv_freq
    return model


def _load_pytorch_model(model_config, weight_path, device):
    from accelerate import init_empty_weights
    from openpi.models_pytorch.pi0_pytorch import PI0Pytorch

    print(
        f"[pi05_pytorch] creating meta model; "
        f"compile={model_config.pytorch_compile_mode or 'off'}, device={device}",
        flush=True,
    )
    with init_empty_weights(include_buffers=False):
        model = PI0Pytorch(model_config)
    # Match OpenPI's final mixed precision before allocating real weights.
    model.paligemma_with_expert.to_bfloat16_for_selected_params("bfloat16")
    return _stream_checkpoint(model, weight_path, device)


def _create_streaming_policy(train_config, model_path, device, compile_mode="max-autotune"):
    # Bound compiler workers on deployment hosts; callers may override this.
    if compile_mode is not None:
        os.environ.setdefault("TORCHINDUCTOR_COMPILE_THREADS", "2")
    import torch
    from openpi.policies import policy_config

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    for tokenizer_path in (
        Path(model_path) / "assets/paligemma_tokenizer.model",
        Path.home() / ".cache/openpi/paligemma_tokenizer.model",
    ):
        if tokenizer_path.is_file():
            os.environ.setdefault("PALIGEMMA_TOKENIZER", str(tokenizer_path.resolve()))
            break

    # Reuse OpenPI's policy/transforms, overriding only this model's loader.
    class StreamingConfig(type(train_config.model)):
        def load_pytorch(self, train_config, weight_path):
            return _load_pytorch_model(self, weight_path, device)

    model_args = asdict(train_config.model)
    model_args["pytorch_compile_mode"] = compile_mode
    return policy_config.create_trained_policy(
        replace(train_config, model=StreamingConfig(**model_args)), model_path, pytorch_device=device
    )


class ModelVLA:
    CAMERAS = {
        "top_head": "cam.head",
        "hand_left": "cam.hand_left",
        "hand_right": "cam.hand_right",
    }
    ACTION_DIM = 16

    def __init__(self, config):
        self.cfg = config
        self.execute_horizon = int(self.cfg.get("execute_horizon", 50))
        if self.execute_horizon <= 0:
            raise ValueError("execute_horizon must be positive")

        _ensure_openpi_client_on_path()
        from openpi.training import config as training_config

        model_path = str(self.cfg["model_path"])
        config_name = str(self.cfg.get("config", "pi05_a2d"))
        train_config = training_config.get_config(config_name)
        self.policy = _create_streaming_policy(
            train_config,
            model_path,
            device=self.cfg.get("device") or None,
            compile_mode=self.cfg.get("compile_mode", "max-autotune"),
        )
        self.policy_metadata = self.policy.metadata
        print(
            f"[pi05_pytorch] ready: config={config_name} ckpt={model_path} "
            f"execute_horizon={self.execute_horizon}",
            flush=True,
        )

    def get_action(self, obs):
        """Map a decoded server observation to the training policy's input."""
        images = {}
        for name, key in self.CAMERAS.items():
            # VLAServer supplies HWC RGB; OpenPI accepts CHW RGB.
            image = np.asarray(obs[key])
            if image.ndim != 3 or image.shape[-1] != 3 or image.dtype != np.uint8:
                raise ValueError(f"{key} must be HWC RGB uint8, got {image.shape} {image.dtype}")
            images[name] = np.ascontiguousarray(image.transpose(2, 0, 1))

        state = np.asarray(obs["state"], dtype=np.float32)
        if state.ndim != 1 or state.size < self.ACTION_DIM or not np.all(np.isfinite(state[: self.ACTION_DIM])):
            raise ValueError("A2D state must be a vector with at least 16 finite entries")

        language = obs["language"]
        prompt = language[0] if isinstance(language, (list, tuple)) and language else language
        if not isinstance(prompt, str):
            raise ValueError("language must be a string or a non-empty list/tuple of strings")

        # OpenPI handles normalization and converts delta predictions to absolute actions.
        output = self.policy.infer({"images": images, "state": state[: self.ACTION_DIM].copy(), "prompt": prompt})
        actions = np.asarray(output["actions"], dtype=np.float32)
        if actions.ndim != 2 or actions.shape[0] == 0 or actions.shape[1] != self.ACTION_DIM:
            raise ValueError(f"Expected A2D actions with shape (horizon, 16), got {actions.shape}")
        if not np.all(np.isfinite(actions)):
            raise ValueError("pi05 produced non-finite actions")
        return actions[: self.execute_horizon].copy()

    def infer(self, sequence, verbose=False):
        """Return the action message consumed by VLAServer and the A2D client."""
        data = sequence[0]
        started_at = time.perf_counter()
        predicted_action = self.get_action(data["obs"])
        if verbose:
            print(time.perf_counter() - started_at, "action shape:", predicted_action.shape)
        return {
            "type": "vla_action",
            "pred_action": predicted_action,
            "ref_timestamp": data["ref_timestamp"],
            "loc_timestamp": data["loc_timestamp"],
            "ext": {},
        }

    def reset(self):
        """The OpenPI policy is stateless between requests."""
        return None
