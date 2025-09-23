This document explains how to integrate the RDT model into the inference framework.

1. Clone the RDT project code to the server path of the inference framework project and configure the conda environment required by RDT:

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

2. Modify the model and language instruction paths in the RDT model interface Python file. The language instruction generation method can refer to [RDT's official documentation](https://github.com/thu-ml/RoboticsDiffusionTransformer/blob/main/scripts/encode_lang_batch.py). The paths that need to be specified include:

- Root directory of the RDT project code;
- Directory of the RDT model files, usually the checkpoint path saved during training in the RDT official project, which should contain config.json and pytorch_model.bin files;
- Directory of the SigLip vision encoder, refer to [RDT's official documentation](https://github.com/thu-ml/RoboticsDiffusionTransformer/blob/main/scripts/encode_lang_batch.py);
- Path to the language instruction feature file, in .pt format;

The code to modify the model and language instructions in rdt.py is as follows:

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
