# CHANGELOG

## [20261019]

- Added a PyTorch pi0.5 (`pi05_pytorch`) adapter with CLI/configuration support, configurable execution horizons, and optional `torch.compile`.
- Added low-memory checkpoint loading that preserves mixed precision and shared weights.

## [20261015]

- Added image overlays to the Camera Viewer, with multi-camera reference capture, indexed image selection, configurable storage paths, and adjustable opacity.
- Allowed EvalLog, LeRobot, and ExpeData to all be unchecked; require at least one selection only when starting manual or automatic recording, with validation on both the frontend and backend.

## [20261013]

- Fixed web-client configuration switching and robot-type changes while observation is active; validate configurations before releasing the current runtime and require observation to be restarted after switching.
- Kept the active YAML configuration selection synchronized across loading, Apply, Save As, and page refreshes.
- Removed implicit selection of the first YAML file when `default_conf.yaml` is missing, and kept repeated Apply operations on the selected file.
- Made Stop and Pause suspend observation reads in the robot subprocess, preventing Mock episode playback from continuing in the background and rejecting stale frames on resume.
- Made automatic recording wait for successful client startup, cleared startup state on failure, and moved recording initialization off the web server's event loop.
- Fixed shutdown semaphore leaks by releasing the shared control lock and finalizing IPC resources before forced process exit.

## [20260924]

- Fixed intermittent language instruction switching in the web client and inference requests.
- Added a top-bar keyboard shortcut popover for run controls and language instructions.
- Made Robot Control presets select `Default` in new tabs and restore selections by name after page reloads.
- Restored the TAO default embodiment and added an explicit override for other registered embodiments.
- Fixed network latency spikes after Reset and Resume.
- Restored inference after Reset and Resume when synchronous waiting or a transient inference error interrupts the worker.
- Prevented stale control commands and observations from crossing Reset and Resume.
- Added the smooth_velocity_2 action chunk fuser.

## [20260923]

- Fixed robot control latency by moving continuous commands to an asynchronous thread in the robot subprocess.
- Renamed the `a2d` robot adapter to `agibot_g1`.
- Updated and tested the Zhejiang Humanoid (Navi WA2).
- Added `DM05` and `WALL-X` model integrations.
