# VLA模型快速接入指南

[English Version](add-new-vla-model.md)

> 假设待接入VLA模型命名为`your_model`

## 1. 创建模型目录
在`server/models/`路径下新建模型文件夹
```
server/models/your_model
```

## 2. 新建模型实现文件
新建文件：`server/models/your_model/your_model.py`

在`your_model.py`内定义`ModelVLA`类，包含`__init__`函数和`infer`函数。

- `__init__`：初始化VLA模型相关配置，实例化模型为`self.policy`
- `infer`：执行模型推理
  - 输入`sequence`列表，包含观测数据与元数据的列表
  - 从`sequence[0]`取出观测数据
  - 组织观测为模型输入格式，推理得到`predicted_action`（`T×D`的numpy数组，`T`动作时间步，`D`机器人关节维度）
  - 返回指定格式字典

```python
# your_model.py 核心逻辑示意
class ModelVLA:
    def __init__(self, cfg):
        # 初始化待接入VLA模型相关配置
        # 实例化待接入VLA模型
        self.policy = None

    def infer(self, sequence):
        # data = {
        #     'type': 'vla_obs',  # 定义数据类型
        #     'ref_timestamp': frame['ref_timestamp'],  # 机器人内部多传感器观测的参考时间戳
        #     'loc_timestamp': loc_timestamp,  # client侧从机器人获得观测的时间戳
        #     'obs': {   #详细观测数据内容
        #         **encoded_imgs,
        #         'state': frame['obs.state'],
        #         'language': [self.task_language_manager.get_current_language()],
        #     },
        # }
        data = sequence[0]

        # 取出观测内容，obs为字典格式，key包含 "camera", "state", "language"
        # "camera"与机器人配置强相关，示例多视角：'cam.head'、'cam.hand_left'、'cam.hand_right'
        obs = data['obs']

        # 将obs组织成your_model推理的输入格式
        obs_input = xxx # 重构 obs 格式 

        # 调用推理
        predicted_action = self.policy.predict(obs_input) # TxD numpy.array

        ext_result = {}
        return {
            "type": "vla_action",  # 定义数据类型
            "pred_action": predicted_action, # 模型预测的动作TxD numpy.array
            "ref_timestamp": data["ref_timestamp"],  # 机器人内部多传感器观测的参考时间戳
            'loc_timestamp': data['loc_timestamp'],  # client侧从机器人获得观测的时间戳
            'ext': ext_result  # 其他模型可能包含的输出，默认为空字典
        }
```

## 3. 添加模块导出文件
新建 `server/models/your_model/__init__.py`
```python
from .your_model import ModelVLA
```

## 4. 修改conf路径下的models_conf.py配置文件

### 4.1 在ModelType枚举新增模型
```python
class ModelType(str, Enum):
    GR00T_N1_5 = 'gr00t_n1_5'
    .....
    YOUR_MODEL = 'your_model'   #新增你的模型
```

### 4.2 编写模型config构造函数
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

### 4.3 将模型配置加入全局配置接口
```python
def get_models_config():
    """Generate configuration for all available VLA models.
    
    This function creates a comprehensive configuration dictionary that includes
    settings for all supported VLA models (GR00T, ...) and specifies
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

## 5. 修改run_server.py

### 5.1 get_model：新增模型实例化分支
```python
def get_model(config):
    """Create and return a VLA model instance based on configuration
    
    Args:
        config: Configuration object containing model type and settings
        
    Returns:
        ModelVLA: VLA model instance for the specified type
        
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

### 5.2 parse_args：命令行参数choices增加your_model
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

### 5.3 override_config_with_args：支持命令行覆写model_path
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

## 6. 启动模型服务
your_model对应的虚拟环境下执行启动命令：
```bash
python run_server.py --model_type your_model --model_path /path/to/your_model
```

