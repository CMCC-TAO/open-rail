## GR00T N1 & N1.5
### 代码仓
- GR00T N1: http://36.140.17.36:10000/git/embodiedai/Isaac-GR00T/-/tree/GR00T_N1?ref_type=heads
- GR00T N1.5: http://36.140.17.36:10000/git/embodiedai/Isaac-GR00T/-/tree/GR00T_N1.5?ref_type=heads

### 环境配置

#### 从零开始配置conda环境
```bash
conda create -n gr00t_xx python=3.10
conda activate gr00t_xx
pip install --upgrade setuptools
pip install -e .
pip install --no-build-isolation flash-attn==2.7.4.post1
```

#### 从已有的conda环境复制

```bash
conda env list #查看现有conda环境
conda create --name new_env_name --clone old_env_name
cd /hy0505/XXX/Isaac-GR00T #到自己gr00t project下
pip install -e . --no-deps #只装本地包本身，不装依赖
```

#### 同一个conda环境下切换gr00t版本
```bash
pip uninstall gr00t
PYTHONPATH=/hy0505/gaohan/Isaac-GR00T:$PYTHONPATH python run_server.py #运行代码时指定PYTHONPATH
```
