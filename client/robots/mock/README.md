# Mock Robot

## Overview

The Mock Robot is a simulation implementation that uses LeRobot datasets to provide realistic robot observation data without requiring actual hardware. This is particularly useful for development, testing, and demonstration purposes.

## Usage

Start the Server：

```bash
conda activate gr00t
python run_server.py --model_type gr00t_n1_5 --model_path /mnt/models/pnp_bottle/checkpoint-60000
```

Start the Client：

```bash
conda activate gr00t
python run_client.py --robots_type mock
```

**Note：** If LeRobot is not installed, the library will generate fake random observation data and send it to the server for inference.

### Configuration

The mock robot is configured through the `conf/robots_conf.yaml` file.
