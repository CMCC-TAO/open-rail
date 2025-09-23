## GR00T N1 & N1.5
### Code Repositories
- GR00T N1: http://36.140.17.36:10000/git/embodiedai/Isaac-GR00T/-/tree/GR00T_N1?ref_type=heads
- GR00T N1.5: http://36.140.17.36:10000/git/embodiedai/Isaac-GR00T/-/tree/GR00T_N1.5?ref_type=heads

### Environment Setup

#### Setting up conda environment from scratch
```bash
conda create -n gr00t_xx python=3.10
conda activate gr00t_xx
pip install --upgrade setuptools
pip install -e .
pip install --no-build-isolation flash-attn==2.7.4.post1
```

#### Cloning from existing conda environment

```bash
conda env list # List existing conda environments
conda create --name new_env_name --clone old_env_name
cd /hy0505/XXX/Isaac-GR00T # Navigate to your gr00t project directory
pip install -e . --no-deps # Install only the local package without dependencies
```

#### Switching gr00t versions in the same conda environment
```bash
pip uninstall gr00t
PYTHONPATH=/hy0505/gaohan/Isaac-GR00T:$PYTHONPATH python run_server.py # Specify PYTHONPATH when running code
```
