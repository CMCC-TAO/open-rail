# CHANGELOG

## [20260923]

- Fixed robot control latency by moving continuous commands to an asynchronous thread in the robot subprocess.
- Renamed the `a2d` robot adapter to `agibot_g1`.
- Updated and tested the Zhejiang Humanoid (Navi WA2).
- Added `M05` and `WALL-X` model integrations.
