---
title: "Web Console"
description: "How to operate the Open-RAIL web console: run control, instructions, data recording, manual control, visualization, and configuration — with what each action actually does."
---

# Web Console

[中文版](../docs-cn-backup/web-console.zh-CN.md)

The web console is the browser dashboard started by `run_web_client.py` (default `http://localhost:9000`). Everything on the page serves one of five jobs: **run control** (start, stage, pause, reset the loop), **task instruction** (select and dispatch what the robot should do), **data recording and evaluation** (turn runs into datasets and scores), **manual robot control**, and **parameter tuning** on top of live camera and trajectory views.

The console runs independently of the inference server. You can open it right after Step 2 of [Getting Started](./getting-started.md); robot status, inference results, and camera streams appear once the server is connected and a robot is configured.

## Page layout

| Region | Panel | Job |
| --- | --- | --- |
| Center | **Runtime Monitor** | Main run control: start/stop, stage the loop, pause, reset, and watch loop health |
| Center | **Language Command** | Select, edit, and dispatch the task instruction the robot is executing |
| Left column | **Data Recording** | Record runs to disk and score them afterwards (EvalLog, LeRobot, ExpeData) |
| Left column | **Robot Control** | Send manual commands and presets to the connected robot |
| Right | **Camera Viewer** | Head and wrist camera streams |
| Center | **Trajectory** | Live plot of selected joint state/action series |
| Left column | **Configuration** | Load, tune, and save client parameters |
| Top bar | Status badge, Shortcuts, resource pills, server indicators | Run state, keyboard help, CPU/GPU/MEM/NET, connection status |

Panels are documented below in that order — most-used first.

## Runtime Monitor

The main control surface. One toggle plus three stage buttons drive the whole run loop.

- **Start / Stop** is a single toggle. **Start** creates the client and launches Observe, Inference, Control, and visualization together; pending configuration edits are applied first. **Stop** releases everything; the next Start recreates the client from the current configuration. If **Auto** recording is enabled in the Data Recording panel, recording starts automatically after Start.
- **Observe → Infer → Control** stage the loop when you do not want everything at once. The order is enforced twice: buttons stay disabled until their prerequisite runs (Infer needs Observe, Control needs Infer), and the server rejects out-of-order requests with an explicit message.
- Toggling a stage **off** stops everything downstream: Observe off stops Inference and Control; Infer off stops Control. Control toggles on/off by itself.
- **Pause** stops all three threads but remembers exactly which were running; **Resume** restores that exact combination. Pause and Resume also pause and resume an active recording. (`Space` toggles Pause; `Ctrl+Space` toggles Control.)
- **Reset** (also `Shift+R`) is a managed sequence, not a single move: the client pauses, the robot returns to preset defaults (or the pose currently filled in the Robot Control panel), the client waits at least twice `1.5 × average inference time` for the motion to settle, then clears its internal buffers. The client **stays paused** afterwards — press Resume to continue. With **Auto** recording, recording restarts after the reset.
- **Key Statistics** shows client-side loop health: Observe FPS, Infer Count, Img Proc Time, Avg Infer Time, Intra Chunk Time, Inter Chunk Time, and Avg Net Latency.

## Language Command

Selects what the robot is trying to do. The **Task** and **Sub-Task** selectors fill the **Instruction** box; **Apply** sends the selected instruction to the VLA server and resets task progress to that step. **Upd / Add / Del** maintain the instruction file; **Upd** changes only the text of the current instruction.

Selection is guarded — it is rejected while recording, while **Auto Mode** is on (turn Auto Mode off first), and when the instruction file changed on disk since it was loaded (reload the file, then select again).

**Auto Mode** advances to the next instruction from task-progress output, with **Start** (initial sub-task), **Thresh** (switch threshold), and **Win-Size** (progress averaging window) mapped to the `language.*` parameters. The **Progress** bar visualizes the current task-progress value.

## Data Recording

Turns runs into reusable assets: execution data is saved to disk as **EvalLog** (evaluation records), **LeRobot** (training-ready episodes), and **ExpeData** (experimental data), and each record can be scored and annotated afterwards so execution quality can be reviewed run by run.

- **Start / Stop** with a recording timer, plus an **Auto** option that ties recording to the run loop (see the interlocks below).
- **Config**: a dedicated subtree for the `record.*` parameters; recording settings are read when recording starts.
- **Tasks**: picks the task folder used for the current recording session.
- **Evaluation Results**: one row per record (ID, sub-task index, duration, score, note). The score buttons follow `record.evaluation.scores`; editing a score applies immediately on Enter.
- **LeRobot Episodes**: browse recorded episodes by storage chunk; each episode can be deleted from the list.

Interlocks with the rest of the page:

- **Auto** starts recording after **Start** and restarts it after **Reset** or **Resume**.
- Recording follows the thread state: Observe, Infer, or Control being toggled off pauses recording; toggling it back on resumes recording.
- Clicking **Start** while it acts as Stop first stops an active recording, then stops the client.
- While recording, switching the task in the Language panel is rejected — stop recording before changing tasks.

## Robot Control

Direct manual control of the connected robot — useful for pose setup, presets, and recovery between runs. It is organized into **Arm**, **Gripper/Hand**, **Body** (head and waist), and **Wheel/Leg** sections; each provides value inputs, a preset dropdown, and preset editing; **Send Cmd** dispatches the values.

Sections, value ranges, and presets come from the selected robot's `action_layout` (see the [Configuration Reference](./configuration.md)). A section whose layout or presets are missing shows as disabled with the reason on hover, so a missing capability is visible rather than silently dead. A group checkbox arms the section before its controls become editable.

- **Send Cmd** moves the robot to the given values immediately. It requires a current robot state — **Observe must be running** — otherwise the request is rejected.
- **Reset** is described under Runtime Monitor; it is the same button and the same managed sequence.

## Camera Viewer

Streams the **Head**, **Wrist-Left**, and **Wrist-Right** cameras, each with an individual **Close** button plus **Close All**. Which cameras appear follows the selected robot's `camera.names` mapping and the `visualize.camera.open_*` switches. The stream connects when Observe starts, so cameras stay black until the observation thread is running.

## Trajectory

A live chart of selected joint series — state versus action side by side — used to check tracking quality while the loop runs. **Play / Clear** control the view, the source checkboxes select series (such as `State`, `ActionRaw`, and `ActionFitted`), and the joint checkboxes select dimensions. Defaults follow `visualize.trajectory.*`. State series are drawn dashed and action series solid; joint labels are derived from the active robot's `action_layout.arm`, so axis names always match the connected robot.

## Configuration

Loads, tunes, and saves client parameters. Field semantics are documented in the [Configuration Reference](./configuration.md); this section is about the workflow and when changes take effect.

### Setup — file workflow

- **File selector + Apply** loads a YAML from `conf/`. This is a **reload**, not a parameter hot-swap: the running client is stopped and rebuilt from the file, and anything in progress stops with it. Use it when you want to switch to a different saved configuration wholesale.
- **Save As** writes the current in-memory configuration to a new file (the dialog defaults to the current file name with `_1` suffix). Save a variant you like, then load it at startup with `--conf <file>` or later via Setup. `.yaml`/`.yml` targets are written as YAML; any other extension as a Python dictionary file.

### Editing — staged changes

- **Main Parameters** pins the most-used entries at the top: Robot Type, Mode, Wait Time [ms], Control Period [ms], Control Speed, Gripper Offset, Inter-Chunk Mode, Intra-Chunk Mode, Img Proc Method, Img Proc Width. Which entries get pinned is itself configurable via `visualize.main_parameters`.
- The **configuration tree** below lists every remaining parameter group, with dropdowns for enum values (custom fusers added via [Add a Smoother](./guides/add-new-inter-chunk-fuser.md) appear in the Inter-Chunk Mode dropdown). The **Key filter** narrows the tree by key name.
- Edits are **staged**, not sent: a **● unsaved changes** badge appears, and **Apply** sends all staged changes at once and then auto-saves them back to the current config file. If you click **Start** with staged edits, they are applied automatically first. `record.evaluation.scores` applies immediately on Enter.

### When changes take effect

A patch updates the in-memory configuration immediately — no restart of the console or the inference server is ever needed. Which parameters affect a *running* client depends on how they are consumed:

| Tier | Scope | Examples |
| --- | --- | --- |
| Live on the running loop | Parameters re-read on every control cycle: the whole `inter_chunk.*` and `intra_chunk.*` families (fusing mode and every mode parameter), plus `controller.period`, `controller.speed` | Switch Inter-Chunk Mode or tune `smooth_velocity` gains while the robot is moving |
| Live via refresh | Applied and then pushed into the running client | `vision.preprocess.*` (preprocessing rebuilt), `language.*`, `robots.mock.dataset_path` (client auto-pauses, mock robot reloads the dataset, client resumes) |
| Read at next use | Picked up the next time that feature starts | `record.*` settings (read at each recording start) |
| Rebuild required | Values captured when the client object is created: `robots.type` and ZMQ endpoints | Stop → Start **reuses the same client object**, so these never rebind on their own. Switch via **Setup → Apply** (rebuilds the client from the file) or restart `run_web_client.py`; changing `robots.type` while running only logs a warning |

This is the mechanism behind the "40+ runtime parameters, no restart required" capability on the project homepage: while the client runs, the smoothing/fusion families and the refresh keys above tune on the fly, and any parameter tuned while the client is stopped takes effect at the next Start.

## Action → effect summary

| Action | Immediate effect | Linked behavior |
| --- | --- | --- |
| **Start** | Creates client, starts all threads | Applies staged config edits first; starts recording if **Auto** is on |
| **Stop** | Stops client, releases resources | Stops an active recording first; next Start recreates the client |
| **Pause / Resume** | Stops/restores all threads to their exact prior state | Pauses/resumes an active recording; Resume starts recording if **Auto** is on |
| **Observe off** | Stops observation | Also stops Inference and Control; pauses an active recording |
| **Infer off** | Stops inference | Also stops Control; pauses an active recording |
| **Control toggle** | Starts/stops robot control only | Toggles recording pause/resume as above |
| **Reset** | Pauses client, moves robot to defaults, clears buffers | Client stays paused afterwards; recording may restart if **Auto** is on |
| **Select instruction** | Sets current instruction, resets task progress to that step | Rejected while recording or in Auto Mode |
| **Send Cmd** | Moves robot to given values | Requires Observe running |
| **Config edit + Apply** | Staged keys sent at once; live-tier keys affect the running loop; file auto-saved | `robots.type`/ZMQ changes take effect only via Setup Apply or a process restart |
| **Setup Apply (load YAML)** | Stops the client and rebuilds it from the file | Anything in progress stops |
| **Save As** | Writes current config to a new file | Load it later via `--conf` or Setup |

## Keyboard shortcuts

| Keys | Action |
| --- | --- |
| `Space` | Pause / resume |
| `Ctrl` + `Space` | Start / stop control |
| `Shift` + `R` | Reset robot |
| Hold `L` + `1–9` | Apply instruction 1–9 |
| Hold `L` + `0` | Apply instruction 10 |
| Hold `L` + `↑` / `↓` | Apply previous / next instruction |
| `Ctrl` + `Enter` | Apply the typed instruction |

The same list is available in-page via **⌨ Shortcuts**.

## Related pages

- [Getting Started](./getting-started.md) — start the console and connect a server.
- [Configuration Reference](./configuration.md) — every parameter shown in these panels.
- [Dataset Demo](./demo-running-on-dataset.md) — run with the Mock Robot and a dataset.
- [Troubleshooting](./troubleshooting.md) — when a panel misbehaves.
