# Contributing Guide

Thank you for contributing code, model adapters, robot adapters, smoothing strategies, tests, or documentation to OPEN-RAIL.

## Before you start

Please read the following first:

- [Project README](README.md)
- [Architecture guide](docs/architecture.md)
- [Configuration guide](docs/configuration.md)
- [Robot integration guide](docs/guides/add-new-robot.md)
- [VLA model integration guide](docs/guides/add-new-vla-model.md)

For new robots or model adapters, it is recommended to open an issue first and describe the use case, dependencies, input/output contract, and validation method.

## Development environment

The project requires Python 3.10 or newer. It is recommended to use an isolated Conda or virtual environment:

```bash
conda create -n open-rail-dev python=3.10 -y
conda activate open-rail-dev
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

`pyproject.toml` is the authoritative source for dependencies and CLI entry points. Model-specific dependencies should be installed in the server-side model environment, while robot SDK or ROS dependencies should be installed in the client-side environment to avoid binding the two environments together unnecessarily.

## Branches and commits

- Create a feature branch from the latest main branch instead of committing directly to main.
- Keep each commit focused on one clear issue and avoid mixing unrelated formatting or generated-file changes.
- Use concise commit messages that explain the purpose of the change, for example `docs: update architecture guide` or `feat: add robot adapter`.
- Do not commit model checkpoints, raw recorded videos, runtime logs, cache directories, or local configuration secrets.
- Before committing, check `git diff` and verify that no personal paths, device addresses, access tokens, or other sensitive information are included.

## Module boundaries

Please keep the dependency direction as follows:

```text
Robot adapter -> Client control loop -> message contract -> Server inference -> model adapter
```

- Robot hardware and SDK calls belong in `client/robots/`.
- Observation collection, local state management, action scheduling, smoothing, and command dispatch belong on the client side.
- Model loading and `infer()` implementations belong in `server/models/`.
- `server/core/vla_server.py` handles the inference workflow and must not call the robot SDK or execute hardware actions.
- `client/core/zmq_client.py` and `server/core/zmq_server.py` are responsible only for transport, routing, heartbeat, and request correlation; they should not carry business logic.
- Data recording, evaluation, and visualization should be integrated through separate interfaces or queues so they do not block the real-time inference and control path.

When adding new modules, prefer reusing existing configuration, adapters, and queue interfaces instead of copying the same business logic across boundaries.

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

## Adding a VLA model adapter

Create a model directory under `server/models/` and implement `ModelVLA` with initialization and `infer(sequence)` interfaces:

- Read observations and metadata from the incoming sequence.
- Convert camera, state, and language inputs into the format expected by the model.
- Return `pred_action` and required metadata using the current client protocol.
- Register the model type in `run_server.py:get_model()` and `conf/models_conf.py`.
- Record the checkpoint, upstream source, and model-specific dependency requirements in the model environment.

Model code should not directly operate the ZMQ socket, robot SDK, or client API. See the [VLA model integration guide](docs/guides/add-new-vla-model.md) for the detailed contract.

## Testing and checks

The repository currently does not include a separate automated test suite, but `.pre-commit-config.yaml` is already configured for code formatting and linting. Before submitting, complete at least the checks relevant to your change scope:

```bash
python -m pytest
python -m compileall client server conf
```

If you only modify documentation, also check Markdown fences, relative links, and `git diff --check`:

```bash
git diff --check
```

When modifying the model, robot, or communication layers, record:

- the Python environment and key dependency versions
- whether GPU, CUDA, ROS, or vendor SDK support is required
- the model checkpoint, dataset, or simulation input used
- startup commands, expected results, and actual validation results

## Documentation requirements

- Use the Chinese version for Chinese docs and the English version for English docs.
- New commands must match the actual entry-point arguments and paths; do not invent nonexistent parameters or locations.
- Describe default values, config file locations, and runtime environment assumptions, especially cross-platform differences.
- If a behavior has not been validated, write “requires verification” or “depends on the specific model/hardware,” and do not present speculation as a guarantee.
- When changing directory structure, entry commands, or configuration fields, also check the related instructions in README and `docs/`.

## Pull request checklist

Before submitting a Pull Request, confirm that:

- [ ] The change scope and motivation are explained.
- [ ] New or modified modules respect the Client, Server, and communication boundaries.
- [ ] Relevant tests or checks have been run and any non-running items are recorded.
- [ ] No checkpoints, recorded data, logs, personal configuration, or sensitive information are included.
- [ ] Related Chinese/English documents and links are synchronized.
- [ ] Hardware safety verification is stated when robot control is involved.

## License

This project is licensed under Apache License 2.0. By submitting code or documentation, you confirm that you have the right to contribute the relevant content under that license and agree to have it published under the project license.
