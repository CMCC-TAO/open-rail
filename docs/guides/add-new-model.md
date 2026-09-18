---
title: "Add a New VLA/WAM Model"
description: "Step-by-step guide to integrate a new VLA/WAM model into the server."
---

# Quick‑Start for Adding New VLA/WAM Model


> Assume the target VLA/WAM model to be integrated is named `your_model`

## 1. Create Model Directory
Create a new model folder under path `server/models/`
```
server/models/your_model
```

## 2. Create Model Implementation File
Create file: `server/models/your_model/your_model.py`

Define the `ModelVLA` class inside `your_model.py`, which contains `__init__` and `infer` functions.

- `__init__`: Initialize configurations related to the VLA/WAM model, instantiate the model as `self.policy`
- `infer`: Execute model inference
  - Input: `sequence`, a list containing observation data and metadata
  - Fetch observation data from `sequence[0]`
  - Reformat observations into model‑expected input, run inference to obtain `predicted_action`
    (`T×D` numpy array, where `T` denotes action time steps and `D` denotes robot joint dimensions)
  - Return a dictionary with specified format

```python
# Core logic skeleton for your_model.py
class ModelVLA:
    def __init__(self, cfg):
        # Initialize configurations for the target VLA/WAM model
        # Instantiate the target VLA/WAM model
        self.policy = None

    def infer(self, sequence):
        # data = {
        #     'type': 'vla_obs',  # data type identifier
        #     'ref_timestamp': frame['ref_timestamp'],  # reference timestamp of multi‑sensor observations inside robot
        #     'loc_timestamp': loc_timestamp,  # timestamp when client receives observations from robot
        #     'obs': {   # observation content
        #         'camera': ...,
        #         'state': ...,
        #         'language': ...,
        #     },
        # }
        data = sequence[0]

        # Extract observation content. obs is a dict with keys: "camera", "state", "language"
        # "camera" strongly depends on robot setup. Example multi‑view keys: 'cam.head', 'cam.hand_left', 'cam.hand_right'
        obs = data['obs']

        # Re‑format obs into input format expected by your_model
        obs_input = xxx # re‑format operations

        # Run model inference
        predicted_action = self.policy.predict(obs_input) # TxD numpy.array

        ext_result = {}
        return {
            "type": "vla_action",  # data type identifier
            "pred_action": predicted_action, # model predicted action, TxD numpy.array
            "ref_timestamp": data["ref_timestamp"],  # reference timestamp of multi‑sensor observations inside robot
            'loc_timestamp': data['loc_timestamp'],  # timestamp when client receives observations from robot
            'ext': ext_result  # optional extra outputs from model, defaults to empty dict
        }
```

## 3. Add Module Export File
Create `server/models/your_model/__init__.py`
```python
from .your_model import ModelVLA
```

## 4. Modify the `models_conf.py` Configuration File under the `conf` Directory

### 4.1 Add new model entry in ModelType Enum
```python
class ModelType(str, Enum):
    GR00T_N1_5 = 'gr00t_n1_5'
    .....
    YOUR_MODEL = 'your_model'   # Add your new model here
```

### 4.2 Implement model config constructor function
```python
def get_your_model_config():
    """Generate configuration for your_model.
    
    Returns:
        ConfigDict: Configuration dictionary containing model path for your_model.
    """
    config = ConfigDict()
    config.config = 'xxxxxxx'
    config.model_path = 'xxxxxxxx'
    return config
```

### 4.3 Register model config into global configuration interface
```python
def get_models_config():
    """Generate configuration for all available VLA/WAM models.
    
    This function creates a comprehensive configuration dictionary that includes
    settings for all supported VLA/WAM models (GR00T, ...) and specifies
    which model type to use by default.
    
    Returns:
        ConfigDict: Configuration dictionary containing:
            - type: Default model type to use
            - gr00t: GR00T model configuration
            ......
            - your_model: YOUR_MODEL configuration
    """
    config = ConfigDict()
    config.gr00t = get_gr00t_config()
    .......
    config.your_model = get_your_model_config()
    return config
```

## 5. Modify run_server.py

### 5.1 get_model: Add branch for new model instantiation
```python
def get_model(config):
    """Create and return a VLA/WAM model instance based on configuration
    
    Args:
        config: Configuration object containing model type and settings
        
    Returns:
        ModelVLA: VLA/WAM model instance for the specified type
        
    Raises:
        ValueError: If model type is not supported
    """
    if config.type == ModelType.GR00T_N1_5:
        from server.models.gr00t.gr00t_n1_5 import ModelVLA as GR00T_N1_5
        return GR00T_N1_5(config.gr00t)
    ......
    elif config.type == ModelType.YOUR_MODEL:
        from server.models.your_model.your_model import ModelVLA as YOUR_MODEL
        return YOUR_MODEL(config.your_model)
    else:
        raise ValueError("Invalid model type")
```

### 5.2 parse_args: Append your_model to CLI argument choices
```python
def parse_args():
    """Parse command line arguments for VLA Server
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='VLA Server')
    
    # Keep only the most commonly used parameters
    parser.add_argument('--model_type', type=str, choices=['gr00t_n1_5',..., 'your_model'], help='Model type to use for inference')
    ......
    return parser.parse_args()
```

### 5.3 override_config_with_args: Support overriding model_path via CLI
```python
def override_config_with_args(config, args):
    """Override configuration with command line arguments
    
    Args:
        config: Original configuration object
        args: Command line arguments
    
    Returns:
        config: Updated configuration object
    """
    # Override model type
    if args.model_type:
        config.models.type = ModelType(args.model_type)
    
    # Override model path
    if args.model_path:
        if config.models.type == ModelType.GR00T_N1_5:
            config.models.gr00t.model_path = args.model_path
        ......
        elif config.models.type == ModelType.YOUR_MODEL:
            config.models.your_model.model_path = args.model_path
    return config
```

## 6. Launch Model Service
Run the following command inside your virtual environment:
```bash
python run_server.py --model_type your_model --model_path /path/to/your_model
```
