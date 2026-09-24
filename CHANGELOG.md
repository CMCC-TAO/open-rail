# CHANGELOG

## [20260924]

- Fixed intermittent language instruction switching in the web client and inference requests.
- Added a top-bar keyboard shortcut popover for run controls and language instructions.
- Made Robot Control presets select `Default` in new tabs and restore selections by name after page reloads.
- Restored the TAO default embodiment and added an explicit override for other registered embodiments.
- Fixed network latency spikes after Reset and Resume.
- Restored inference after Reset and Resume when synchronous waiting or a transient inference error interrupts the worker.
- Prevented stale control commands and observations from crossing Reset and Resume.

## [20260923]

- Fixed robot control latency by moving continuous commands to an asynchronous thread in the robot subprocess.
- Renamed the `a2d` robot adapter to `agibot_g1`.
- Updated and tested the Zhejiang Humanoid (Navi WA2).
- Added `DM05` and `WALL-X` model integrations.
