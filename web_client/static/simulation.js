const $ = (id) => document.getElementById(id);
const choices = {
  platform: ["robocasa", "robotwin"],
  instruction_type: ["seen", "unseen"],
  split: ["target", "pretrain"],
  mode: ["sync", "async"],
  intra_chunk_mode: ["raw", "interpolation", "fitting"],
  inter_chunk_mode: ["sync", "search_action", "smooth_velocity", "min_jerk"],
  mujoco_gl: ["egl", "osmesa", "glfw"],
  preprocess: ["none", "resize"],
  video_layout: ["grid", "single"],
};
const labels = {
  platform: "Simulation Platform",
  robotwin_root: "RoboTwin Root Directory",
  task_config: "RoboTwin Task Configuration",
  instruction_type: "Instruction Type",
  instruction: "Fixed Instruction (Optional)",
  no_expert_check: "Skip Expert Check (Instruction Required)",
  gpu: "GPU Indices (Blank to Inherit)",
  max_transition_steps: "Maximum Chunk Transition Steps",
  max_seed_attempts: "Maximum Seed Attempts per Episode",
  seed_stride: "Episode Seed Stride",
  seed_selection_timeout: "Environment Setup and Seed Selection Timeout (Seconds)",
  worker_episodes: "Episodes per Worker",
  max_native_restarts: "Crash Retries at the Same Checkpoint",
  server_reconnect_interval: "Reconnect Interval (Seconds)",
  server_reconnect_timeout: "Reconnect Timeout (Seconds; 0 for Unlimited)",
  python: "Python Executable",
  env_name: "Single Task (Choose Task or Suite)",
  task_suite: "Task Suite (e.g. target50)",
  split: "Task Split",
  n_episodes: "Episodes per Task",
  n_envs: "Parallel Environments",
  n_action_steps: "Action Chunk Length",
  seed: "Random Seed",
  mode: "Execution Mode",
  intra_chunk_mode: "Intra-chunk Smoothing",
  intra_chunk_sample_ratio: "Output Sampling Ratio",
  inter_chunk_mode: "Inter-chunk Fusion",
  async_replenish_threshold: "Async Replenishment Threshold (Blank for Default)",
  max_async_observation_lag_steps: "Maximum Observation Lag Steps (Blank for Default)",
  max_episode_steps: "Maximum Episode Steps (Blank for Default)",
  episode_timeout: "Episode Timeout (Seconds)",
  stall_timeout: "Stall Timeout (Seconds)",
  server_ip: "Model Server Address",
  server_port: "Model Server Port",
  mujoco_gl: "Rendering Backend",
  preprocess: "Image Preprocessing",
  record: "Save LeRobot Dataset",
  video: "Save Evaluation Videos",
  record_fps: "Dataset Frame Rate",
  video_fps: "Video Frame Rate",
  video_layout: "Video Layout",
};
let defaults,
  selected = "",
  busy = false;
async function api(path, method = "GET", body) {
  const response = await fetch("/api/simulation" + path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail)
    );
  return data;
}
function error(e) {
  $("error").textContent = e.message;
}
function fileChanged() {
  const name = $("files").value;
  const url =
    "/api/simulation/jobs/" +
    encodeURIComponent(selected) +
    "/artifact/" +
    name.split("/").map(encodeURIComponent).join("/");
  $("download").hidden = !name;
  $("download").href = url;
  $("video").hidden = !name.endsWith(".mp4");
  if (name.endsWith(".mp4")) {
    if ($("video").getAttribute("src") !== url) $("video").src = url;
  } else {
    $("video").removeAttribute("src");
    $("video").load();
  }
}
function table(stats) {
  $("results").replaceChildren();
  const tasks = stats.filter((s) => s.env_name && s.worker_index === undefined);
  const source = tasks.length ? tasks : stats.filter((s) => s.env_name);
  const table = document.createElement("table");
  for (const values of [
    ["Task", "Saved Episodes", "Success Rate"],
    ...source.map((s) => [
      s.env_name,
      s.num_episodes != null ? s.num_episodes : (s.episodes || []).length,
      ((s.success_rate || 0) * 100).toFixed(1) + "%",
    ]),
  ]) {
    const tr = document.createElement("tr");
    for (const value of values) {
      const td = document.createElement("td");
      td.textContent = value;
      tr.append(td);
    }
    table.append(tr);
  }
  $("results").append(table);
  for (const s of stats.filter((s) => s.task_suite)) {
    const p = document.createElement("p");
    p.textContent = JSON.stringify({
      task_suite: s.task_suite,
      completed: s.num_completed_tasks,
      failed: s.num_failed_tasks,
      success_rate:
        s.success_rate != null ? s.success_rate : s.overall_success_rate,
    });
    $("results").append(p);
  }
}
async function poll() {
  if (busy) return;
  busy = true;
  try {
    const jobs = await api("/jobs");
    const previous = selected;
    $("jobs").replaceChildren(
      ...jobs.map(
        (j) =>
          new Option(
            j.id + " · " + (j.config.platform || "robocasa") + " · " + j.status,
            j.id
          )
      )
    );
    selected = jobs.some((j) => j.id === previous)
      ? previous
      : jobs.length
      ? jobs[0].id
      : "";
    $("jobs").value = selected;
    $("start").disabled = jobs.some((j) =>
      ["running", "stopping"].includes(j.status)
    );
    if (!selected) {
      $("stop").disabled = true;
      $("resume").disabled = true;
      return;
    }
    const [job, logs, files] = await Promise.all([
      api("/jobs/" + selected),
      api("/jobs/" + selected + "/logs"),
      api("/jobs/" + selected + "/files"),
    ]);
    $("status").textContent =
      "Status: " + job.status + " | Output Directory: data/robocasa_web/jobs/" + job.id;
    $("stop").disabled = !["running", "interrupted"].includes(job.status);
    $("resume").disabled =
      !["cancelled", "failed", "interrupted"].includes(job.status) ||
      $("start").disabled;
    table(job.progress.concat(job.stats.filter((s) => s.task_suite)));
    $("logs").textContent = logs.text;
    const old = $("files").value;
    $("files").replaceChildren(...files.map((f) => new Option(f, f)));
    if (files.includes(old)) $("files").value = old;
    fileChanged();
  } catch (e) {
    error(e);
  } finally {
    busy = false;
  }
}
$("jobs").onchange = () => {
  selected = $("jobs").value;
  poll();
};
$("files").onchange = fileChanged;
for (const action of ["stop", "resume"])
  $(action).onclick = async () => {
    try {
      $(action).disabled = true;
      await api("/jobs/" + selected + "/" + action, "POST");
      await poll();
    } catch (e) {
      error(e);
    }
  };
$("config").onsubmit = async (event) => {
  event.preventDefault();
  $("error").textContent = "";
  const config = {};
  for (const [key, value] of Object.entries(defaults)) {
    const input = $("field-" + key);
    config[key] =
      typeof value === "boolean"
        ? input.checked
        : typeof value === "number" || value === null
        ? input.value === ""
          ? null
          : Number(input.value)
        : input.value;
  }
  try {
    $("start").disabled = true;
    const job = await api("/jobs", "POST", config);
    selected = job.id;
    await poll();
  } catch (e) {
    error(e);
    $("start").disabled = false;
  }
};
function updatePlatform() {
  const robotwin = $("field-platform").value === "robotwin";
  $("field-intra_chunk_sample_ratio").disabled =
    robotwin && $("field-intra_chunk_mode").value !== "interpolation";
  const onlyRobotwin = [
    "robotwin_root",
    "task_config",
    "instruction_type",
    "instruction",
    "no_expert_check",
    "max_transition_steps",
    "max_seed_attempts",
    "seed_stride",
    "seed_selection_timeout",
  ];
  for (const key of onlyRobotwin)
    $("field-" + key).parentElement.hidden = !robotwin;
  $("field-gpu").parentElement.firstChild.textContent = robotwin
    ? "GPU Indices (e.g. 0 or 0,1; Blank to Inherit)"
    : "Simulation GPU Index (e.g. 2; Blank to Inherit)";
  for (const key of ["split", "mujoco_gl"])
    $("field-" + key).parentElement.hidden = robotwin;
  $("field-task_suite").parentElement.firstChild.textContent = robotwin
    ? "Task List (Comma-separated or YAML File)"
    : labels.task_suite;
  $("field-task_suite").placeholder = robotwin
    ? "task_a,task_b or path to a task-list YAML file"
    : "target50";
}

async function initialize() {
  try {
    defaults = await api("/options");
    for (const [key, value] of Object.entries(defaults)) {
      const label = document.createElement("label");
      label.textContent = labels[key] || key;
      const input = document.createElement(choices[key] ? "select" : "input");
      input.id = "field-" + key;
      if (choices[key])
        input.append(...choices[key].map((v) => new Option(v, v)));
      else
        input.type =
          typeof value === "boolean"
            ? "checkbox"
            : typeof value === "number" || value === null
            ? "number"
            : "text";
      if (typeof value === "boolean") input.checked = value;
      else input.value = value == null ? "" : value;
      if (input.type === "number") input.step = "any";
      label.append(input);
      $("fields").append(label);
    }
    $("field-platform").onchange = () => {
      const robotwin = $("field-platform").value === "robotwin";
      $("field-env_name").value = "";
      $("field-task_suite").value = "";
      $("field-n_action_steps").value = robotwin ? 50 : 16;
      $("field-seed").value = robotwin ? 0 : 42;
      updatePlatform();
    };
    $("field-intra_chunk_mode").onchange = updatePlatform;
    updatePlatform();
    await poll();
    setInterval(() => {
      if (!document.hidden) poll();
    }, 3000);
  } catch (e) {
    error(e);
  }
}
initialize();
