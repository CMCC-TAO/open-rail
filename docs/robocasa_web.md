# Web Simulation Evaluation

Start `python run_web_client.py --port 9000` and open `http://localhost:9000/`.
In **Configuration**, select Robot Type `robocasa` or `aloha_robotwin`.
Configure mode, action chunk length, smoothing, fusion, image preprocessing, and the model
connection there. Robot-specific settings include Python, GPU, parallel environments,
seed, and RoboTwin root/task settings. Blank environment paths use the backend presets.
Blank action chunk length uses the platform default: 16 for RoboCasa, 50 for RoboTwin.

Expand **Simulation Evaluation**. **Task Selection** switches between single tasks and task sets;
**Task** lists the configured platform's tasks or sets such as RoboCasa `target50` and
RoboTwin `all_tasks`. Sets default to all tasks selected; search and check the tasks to run
in the scrollable list below. The summary shows task count and total episodes.
Choose episodes per task, parallel environments, and dataset/video saving, then select
**Run Evaluation**. Robot selection alone starts no process.
The evaluation captures the current Configuration, including pending edits; **Apply**
is only needed to persist those edits to the main client configuration. Runtime Monitor's
client launch buttons do not launch a simulator in this mode.
Parallel environments initially uses the selected robot's Configuration value; the evaluation panel value applies to the new job and its saved snapshot.

Jobs save their complete resolved configuration, `client_config.json`, `client_config.py`,
logs, statistics, videos, and optional LeRobot datasets under
`data/simulation_web/jobs/<job ID>/` for both platforms. Existing jobs under
`data/robocasa_web/jobs/` remain accessible and resume in their original directories.
The worker loads the snapshot through the existing
`--user_conf` mechanism. Later Configuration edits do not alter the running job;
Resume uses its saved configuration. One evaluation runs at a time and may use parallel
environments. Start the model inference service separately.

Environment paths and hidden defaults come from `conf/web_simulation.yaml`.
This local file is ignored by Git. For another installation, copy
`conf/web_simulation.example.yml` and set the installed RoboTwin path.
The `defaults` mapping applies to both platforms; `platforms.robocasa` and
`platforms.robotwin` override individual values using `EvaluationConfig` field names.
An empty `python` uses the Web service's interpreter. Configuration overrides the presets
for shared settings. Simulation task selection and saving switches belong to the
Evaluation panel; hardware-specific controller settings may be normalized by the existing
evaluation pipeline.

The standalone `/simulation` page retains its independent configuration form.
Shared cameras and trajectories display the running simulation or robot client.
Robot Control and Data Recording continue to control the robot client. Results, saved
videos, and logs are available inside the evaluation panel. Tests use simulated processes
and browser API responses; real rendering and inference require the configured simulators.
