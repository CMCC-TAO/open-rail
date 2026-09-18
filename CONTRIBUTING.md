# Contributing Guide

Thank you for contributing code, model adapters, robot adapters, smoothing strategies, tests, or documentation to Open-RAIL.

## Before you start

Please read the following first:

- [Project README](README.md)
- [Architecture guide](docs/architecture.md)
- [Configuration guide](docs/configuration.md)
- [Robot integration guide](docs/guides/add-new-robot.md)
- [VLA/WAM model integration guide](docs/guides/add-new-model.md)

For new robots or model adapters, it is recommended to open an issue first and describe the use case, dependencies, input/output contract, and validation method.

## Development environment

The project requires Python 3.10 or newer. It is recommended to use an isolated Conda or virtual environment:

```bash
conda create -n open-rail-dev python=3.10 -y
conda activate open-rail-dev
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

`pyproject.toml` defines Open-RAIL’s own dependencies and CLI entry points. Launching a Open-RAIL server also requires the dependencies of the model it serves, which should be installed in the server-side environment. Running a Open-RAIL client requires the relevant robot SDK or ROS dependencies, which should be installed in the client-side environment. Keeping these dependencies separate avoids unnecessarily coupling and dependency conflicts.

## How to contribute

- Fork the repository and create a feature branch from the latest main branch instead of committing directly to main.
- Keep each commit focused on one clear issue and avoid mixing unrelated formatting or generated-file changes.
- Use concise commit messages that explain the purpose of the change, for example `docs: update architecture guide` or `feat: add robot adapter`.
- Do not commit model checkpoints, raw recorded videos, runtime logs, cache directories, or local configuration secrets.
- Before committing, check `git diff` and verify that no personal paths, device addresses, access tokens, or other sensitive information are included.
- Submit a Pull Request to this repository and describe the change scope, motivation, and any relevant validation results. If the change is large or complex, consider opening an issue first to discuss the design.

## Module boundaries

Please keep the dependency direction as follows:

```text
Robot adapter -> Client control loop -> Message contract -> Server inference -> Model adapter
```

- Robot adapters and related integration code, such as hardware access and SDK calls, live in `client/robots/`.
- Observation processing, local state management, action scheduling, smoothing, and command dispatch belong in `client/core`.
- Model loading and `infer()` implementations resides in `server/models/`.
- `server/core/vla_server.py` handles the inference workflow and must not call the robot SDK or execute hardware actions.
- `client/core/zmq_client.py` and `server/core/zmq_server.py` handle communication between the client and server, including sending and receiving messages and monitoring connection status. Model inference and robot control logic should remain outside these modules.
- Data recording, evaluation, and visualization should be integrated through separate interfaces or queues so they do not block the real-time inference and control path.

When adding new modules, reuse existing configuration, adapters, and queues where possible.

## Adding a robot adapter

Create a robot directory under `client/robots/` and inherit from `RobotBase`; at minimum, implement:

- `retrieve_observation()`: return camera data, robot state, and required timestamps.
- `execute_action()`: convert client actions into robot commands.

Also complete the following:

- Register the robot type and configuration in `conf/robots_conf.py`.
- Define the camera names, action dimensions, and `action_layout` clearly.
- Keep vendor SDK, ROS topic, and device communication code inside the robot adapter.
- Validate observation reading and action conversion before connecting to a model server.
- Document the physical device, SDK, ROS version, and safety assumptions.

See the [robot integration guide](docs/guides/add-new-robot.md) for the detailed interface requirements.

## Adding a VLA/WAM model adapter

Create a model directory under `server/models/` and implement `ModelVLA` with initialization and `infer(sequence)` interfaces:

- Read observations and metadata from the incoming sequence.
- Convert camera, state, and language inputs into the format expected by the model.
- Return `pred_action` and required metadata using the current client protocol.
- Register the model type in `run_server.py:get_model()` and `conf/models_conf.py`.
- Record the checkpoint, upstream source, and model-specific dependency requirements in the model environment.

Model code should not directly operate the ZMQ socket, robot SDK, or client API. See the [VLA/WAM model integration guide](docs/guides/add-new-model.md) for the detailed contract.

## Testing and style checks

The repository does not yet have a dedicated test suite. Formatting and linting checks are, however, configured in `.pre-commit-config.yaml`.

For document modifications, also check Markdown fences, relative links, and `git diff --check`:

For all code changes, include enough information in your pull request for reviewers to run and verify your changes, as applicable:
- Python environment setup and key dependency versions
- Any GPU, CUDA, ROS, or vendor SDK requirements
- The model checkpoint, dataset, or simulation input used and how to obtain it
- Commands to run the code, expected behavior, and your validation results

## Pull request checklist

Before submitting a Pull Request, confirm that:

- [ ] The change scope and motivation are explained.
- [ ] New or modified modules respect the Client, Server, and communication boundaries.
- [ ] Relevant tests or checks have been run and reproducible.
- [ ] No checkpoints, recorded data, logs, personal configuration, or sensitive information are included.
- [ ] Links in the documents are consistent with the page's language.
- [ ] For robot control changes, state whether they were tested on real hardware and describe any safety checks performed.

## License

This project is licensed under Apache License 2.0. By submitting code or documentation, you confirm that you have the right to contribute the relevant content under that license and agree to have it published under the project license.
