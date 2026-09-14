---
title: Installation
description: Install VLA-RAIL and its dependencies.
---

# Installation

VLA-RAIL requires **Python >= 3.10**. All core dependencies are listed in `requirements.txt`.

## 1. Clone the repository

```bash
git clone https://github.com/zhaoyongsheng/vla_infer.git
cd vla_infer
```

## 2. Create an environment

```bash
conda create -n vla-rail python=3.10
conda activate vla-rail
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

Core dependencies include `torch`, `diffusers`, `lerobot`, `opencv-python`,
`pyzmq`, `PyQt5`, `pyqtgraph`, and `ruckig`. See `requirements.txt` for exact
versions.

## 4. Next steps

- Configure the framework in [`conf/`](../configuration/).
- Pick a [model and robot](../models-robots/).
- Launch the server and client from the [Quickstart](../) on the landing page.
