import dataclasses
import enum
import logging
import socket

import tyro

from openpi.policies import policy as _policy
from openpi.policies import policy_config as _policy_config
from openpi.serving import websocket_policy_server
from openpi.training import config as _config
import numpy as np
import time


class EnvMode(enum.Enum):
    """Supported environments."""

    ALOHA = "aloha"
    ALOHA_SIM = "aloha_sim"
    DROID = "droid"
    LIBERO = "libero"
    A2D = 'a2d'


@dataclasses.dataclass
class Checkpoint:
    """Load a policy from a trained checkpoint."""

    # Training config name (e.g., "pi0_aloha_sim").
    config: str
    # Checkpoint directory (e.g., "checkpoints/pi0_aloha_sim/exp/10000").
    dir: str


@dataclasses.dataclass
class Default:
    """Use the default policy for the given environment."""


@dataclasses.dataclass
class Args:
    """Arguments for the serve_policy script."""

    # Environment to serve the policy for. This is only used when serving default policies.
    env: EnvMode = EnvMode.ALOHA_SIM

    # If provided, will be used in case the "prompt" key is not present in the data, or if the model doesn't have a default
    # prompt.
    default_prompt: str | None = None

    # Port to serve the policy on.
    port: int = 8000
    # Record the policy's behavior for debugging.
    record: bool = False

    # Specifies how to load the policy. If not provided, the default policy for the environment will be used.
    policy: Checkpoint | Default = dataclasses.field(default_factory=Default)


# Default checkpoints that should be used for each environment.
DEFAULT_CHECKPOINT: dict[EnvMode, Checkpoint] = {
    EnvMode.ALOHA: Checkpoint(
        config="pi05_aloha",
        dir="gs://openpi-assets/checkpoints/pi05_base",
    ),
    EnvMode.ALOHA_SIM: Checkpoint(
        config="pi0_aloha_sim",
        dir="gs://openpi-assets/checkpoints/pi0_aloha_sim",
    ),
    EnvMode.DROID: Checkpoint(
        config="pi05_droid",
        dir="gs://openpi-assets/checkpoints/pi05_droid",
    ),
    EnvMode.LIBERO: Checkpoint(
        config="pi05_libero",
        dir="gs://openpi-assets/checkpoints/pi05_libero",
    ),
    EnvMode.A2D: Checkpoint(
        config="pi0_a2d",
        dir="/path/to/pi0_model",
    ),
    EnvMode.A2D: Checkpoint(
        config="pi05_a2d",
        dir="/path/to/pi05_model",
    )
}


def create_default_policy(env: EnvMode, *, default_prompt: str | None = None) -> _policy.Policy:
    """Create a default policy for the given environment."""
    if checkpoint := DEFAULT_CHECKPOINT.get(env):
        return _policy_config.create_trained_policy(
            _config.get_config(checkpoint.config), checkpoint.dir, default_prompt=default_prompt
        )
    raise ValueError(f"Unsupported environment mode: {env}")


def create_policy(args: Args) -> _policy.Policy:
    """Create a policy from the given arguments."""
    match args.policy:
        case Checkpoint():
            return _policy_config.create_trained_policy(
                _config.get_config(args.policy.config), args.policy.dir, default_prompt=args.default_prompt
            )
        case Default():
            return create_default_policy(args.env, default_prompt=args.default_prompt)


class ModelVLA:
    def __init__(self, config):
        """Initialize the pi0 VLA model with configuration
        
        Args:
            config: Dictionary containing model configuration parameters
        """
        self.cfg = config
        self.overwrite_args()
        print(self.cfg)
        print(self.args)

        # intialize policy
        self.policy         = create_policy(self.args)
        self.policy_metadata = self.policy.metadata
    

    def overwrite_args(self):
        self.args = Args()
        self.args.env = EnvMode.A2D
        self.args.policy = Checkpoint(config=self.cfg.config, dir=self.cfg.model_path)
        

    def reshape_action(self, predicted_action: np.ndarray) -> np.ndarray:
        """
        将(bs,26)的action数组转换为(bs,16)，按指定规则计算均值维度
        
        Args:
            predicted_action: 输入数组，形状(bs, 26)
            
        Returns:
            输出数组，形状(bs, 16)
        """
        # 1. 校验输入形状（避免维度错误）
        if predicted_action.ndim != 2 or predicted_action.shape[1] != 26:
            raise ValueError(f"输入数组形状必须为(bs,26)，当前为{predicted_action.shape}")
        
        bs = predicted_action.shape[0]
        
        # 2. 提取前14列（0~13）
        action_14 = predicted_action[:, :14]  # shape: (bs,14)
        
        # 3. 计算15~19列的行均值（目标第14列）
        mean_15_19 = predicted_action[:, 15:20].mean(axis=1, keepdims=True)  # shape: (bs,1)
        
        # 4. 计算21~25列的行均值（目标第15列）
        mean_21_25 = predicted_action[:, 21:26].mean(axis=1, keepdims=True)  # shape: (bs,1)
        
        # 5. 拼接所有部分得到(bs,16)
        new_action = np.concatenate([
            action_14,    # 0~13列
            mean_15_19,   # 14列
            mean_21_25    # 15列
        ], axis=1)
        
        return new_action


    def infer(self, sequence):
        """Perform inference on input sequence data
        
        Args:
            sequence: List containing observation data and metadata
            
        Returns:
            dict: Inference result containing predicted actions and timestamps
        """
        # get observation
        data = sequence[0]
        obs = data['obs'].copy()
        inp_obs = {
            "top_head": obs['cam.head'],
            "hand_left": obs['cam.hand_left'],
            "hand_right": obs['cam.hand_right'],
            'state': obs['state'],
            "prompt": obs['language'][0]
        }
        # get action
        ext_result = {}
        output = self.policy.infer(inp_obs)
        print(f"type pi output: {type(output)}")
        print(f"key output: {output.keys()}")
        predicted_action = output['actions']
        print(output['policy_timing'], 'action shape: ', predicted_action.shape)
        if self.cfg.is_hand:
            predicted_action = self.reshape_action(predicted_action)
        print("reshape action shape: ", predicted_action.shape)

        return {"type": "vla_action", "pred_action": predicted_action, "ref_timestamp": data["ref_timestamp"], 'loc_timestamp': data['loc_timestamp'], 'ext': ext_result}
    