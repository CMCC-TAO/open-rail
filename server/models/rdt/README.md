本文档说明如何在将RDT模型集成到推理框架中使用。

1.克隆RDT的工程代码到推理框架工程的server路径下，并配置RDT需要的conda环境：

```bash
    # Clone this repo
    git clone git@github.com:thu-ml/RoboticsDiffusionTransformer.git
    cd RoboticsDiffusionTransformer
    
    # Create a Conda environment
    conda create -n rdt python=3.10.0
    conda activate rdt
    
    # Install pytorch
    # Look up https://pytorch.org/get-started/previous-versions/ with your cuda version for a correct command
    pip install torch==2.1.0 torchvision==0.16.0  --index-url https://download.pytorch.org/whl/cu121
    
    # Install packaging
    pip install packaging==24.0
    
    # Install flash-attn
    pip install flash-attn --no-build-isolation
    
    # Install other prequisites
    pip install -r requirements.txt
```

2.修改RDT模型接口python文件中的模型和语言指令路径，语言指令生成的方式可以参考[RDT的官方文档](https://github.com/thu-ml/RoboticsDiffusionTransformer/blob/main/scripts/encode_lang_batch.py)，需要制定的路径包括：

- RDT工程代码的根目录；
- RDT模型文件的目录，通常是RDT官方工程训练时保存的checkpoint路径，需包含config.json和pytorch_model.bin两个文件；
- SigLip视觉编码器的目录，参考[RDT的官方文档](https://github.com/thu-ml/RoboticsDiffusionTransformer/blob/main/scripts/encode_lang_batch.py)；
- 语言指令特征文件的路径，格式为.pt文件；

rdt.py中修改模型和语言指令的代码如下：

```python
# ...

import sys
sys.path.append('path/to/your/rdt/root')

class ModelVLA:
    def __init__(self):

        with open("path/to/your/rdt/root/configs/base.yaml", "r") as f:
            config = yaml.safe_load(f)

        model_path = 'path/to/rdt-ckpt/'
        vision_encoder_name_or_path = 'path/to/siglip-so400m-patch14-384'
        self.lang_embd_path = 'path/to/language/embedding/file'

# ...
```

3.完成以上修改，即可使用RDT模型进行真机推理。
