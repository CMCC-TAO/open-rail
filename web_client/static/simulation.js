export async function initializeSimulation(root, prefix = "", getClientConfig = null) {
  const $ = (id) => root.querySelector("#" + prefix + id);
  const choices = {
    platform: [],
    instruction_type: ["seen", "unseen"],
    task_config: ["demo_clean", "demo_randomized"],
    video_layout: ["grid", "single"],
    render_observation_mode: ["chunk_boundary", "per_action"],
    split: ["target", "pretrain"],
    mode: ["sync", "async"],
    intra_chunk_mode: ["raw", "interpolation", "fitting"],
    inter_chunk_mode: ["sync", "search_action", "smooth_velocity", "min_jerk"],
  };
  const labels = {
    platform: "Simulation Platform",
    n_episodes: "Episodes per Task",
    mode: "Execution Mode",
    record: "Save LeRobot Dataset",
    video: "Save Evaluation Videos",
    video_fps: "Video FPS",
    video_layout: "Video Layout",
    n_envs: "Parallel Environments",
    gpu: "GPU Indices (Blank to Inherit)",
    n_action_steps: "Action Chunk Length",
    seed: "Random Seed",
    intra_chunk_mode: "Intra-chunk Smoothing",
    inter_chunk_mode: "Inter-chunk Fusion",
    intra_chunk_sample_ratio: "Output Sampling Ratio",
    async_replenish_threshold: "Async Replenishment Threshold (Blank for Default)",
    max_async_observation_lag_steps: "Maximum Observation Lag Steps (Blank for Default)",
    task_config: "RoboTwin Task Configuration",
    instruction_type: "Instruction Type",
    render_observation_mode: "Camera Rendering (Sync Mode)",
    split: "Task Split",
  };
  const basicFields = getClientConfig ? ["n_episodes", "n_envs", "record", "video"]
    : ["platform", "n_episodes", "mode", "record", "video"];
  const dashboardLabels = {
    n_episodes: "Episodes / Task",
    n_envs: "Parallel Envs",
    record: "Save Dataset",
    video: "Save Videos",
  };
  const advancedFields = getClientConfig ? ["video_fps", "video_layout"] : [
    "n_envs", "gpu", "n_action_steps", "seed", "intra_chunk_mode", "inter_chunk_mode",
    "intra_chunk_sample_ratio", "async_replenish_threshold", "max_async_observation_lag_steps",
    "task_config", "instruction_type", "render_observation_mode", "split",
    "video_fps", "video_layout",
  ];
  let benchmarkProfiles = [], defaults,
    selected = "",
    busy = false,
    ready = false,
    submitting = false,
    profileGeneration = 0,
    environmentPlatform = null,
    catalog = null,
    catalogPlatform = null,
    catalogGeneration = 0,
    chosenTasks = new Set(),
    lastError = "",
    lastErrorSource = "",
    artifactJob = "";
  const platformForConfig = (config) => benchmarkProfiles.find(spec => spec.robot_type === config.robots?.type)?.id;
  const currentBenchmark = () => benchmarkProfiles.find(spec => spec.id === currentPlatform());
  const currentPlatform = () => getClientConfig
    ? platformForConfig(getClientConfig()) : $("field-platform").value;
  function notifyRuntimeLock(active) {
    if (getClientConfig) document.dispatchEvent(new CustomEvent('simulation-evaluation-state', {
      detail: { active },
    }));
  }
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
  function error(e, source = "action") {
    $("error").textContent = e.message;
    if (prefix && lastError !== e.message && typeof window.toast === "function")
      window.toast(e.message, "error");
    lastError = e.message;
    lastErrorSource = source;
  }
  function clearPollingError() {
    if (lastErrorSource !== "poll") return;
    $("error").textContent = "";
    lastError = "";
    lastErrorSource = "";
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
  function table(stats, episodesPerTask) {
    $("results").replaceChildren();
    const tasks = stats.filter((s) => s.env_name && s.worker_index === undefined);
    const source = tasks.length ? tasks : stats.filter((s) => s.env_name);
    const table = document.createElement("table");
    for (const values of [
      ["Task", "Episodes", "Success Rate"],
      ...source.map((s) => [
        s.env_name,
        (s.num_episodes != null ? s.num_episodes : (s.episodes || []).length) + " / " + episodesPerTask,
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
      notifyRuntimeLock(submitting || jobs.some(job => ["running", "stopping"].includes(job.status)));
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
      $("start").disabled = !ready || submitting || jobs.some((j) =>
        ["running", "stopping"].includes(j.status)
      );
      if (!selected) {
        $("stop").disabled = true;
        $("resume").disabled = true;
        clearPollingError();
        return;
      }
      const [job, logs, files] = await Promise.all([
        api("/jobs/" + selected),
        api("/jobs/" + selected + "/logs"),
        api("/jobs/" + selected + "/files"),
      ]);
      const directory = job.directory || "data/simulation_web/jobs/" + job.id;
      $("status").textContent = "Status: " + job.status +
        (prefix ? "" : " | Output Directory: " + directory);
      $("status").title = "Output Directory: " + directory;
      $("stop").disabled = !["running", "interrupted"].includes(job.status);
      $("resume").disabled =
        !["cancelled", "failed", "interrupted"].includes(job.status) ||
        jobs.some((j) => ["running", "stopping"].includes(j.status));
      table(job.progress.concat(job.stats.filter((s) => s.task_suite)), job.config.n_episodes);
      $("logs").textContent = logs.text;
      const old = artifactJob === selected ? $("files").value : "";
      artifactJob = selected;
      $("files").replaceChildren(...files.map((f) => new Option(f, f)));
      if (files.includes(old)) $("files").value = old;
      fileChanged();
      clearPollingError();
    } catch (e) {
      error(e, "poll");
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
        if (action === "resume") notifyRuntimeLock(true);
        await api("/jobs/" + selected + "/" + action, "POST");
        if (prefix && typeof window.toast === "function")
          window.toast(action === "stop" ? "Evaluation stop requested." : "Evaluation resumed.", "ok");
      } catch (e) {
        error(e);
      } finally {
        await poll();
      }
    };
  $("config").onsubmit = async (event) => {
    event.preventDefault();
    $("error").textContent = "";
    try {
      if (!ready || submitting) return;
      submitting = true;
      notifyRuntimeLock(true);
      $("config").inert = true;
      $("start").disabled = true;
      const platform = currentPlatform();
      const snapshot = getClientConfig ? getClientConfig() : null;
      if (getClientConfig && !platformForConfig(snapshot))
        throw new Error("Select a simulation robot in Configuration.");
      const config = await api("/options?platform=" + platform);
      if (snapshot) config.client_config = snapshot;
      for (const key of [...basicFields, ...advancedFields]) {
        const input = $("field-" + key);
        const value = defaults[key];
        config[key] = typeof value === "boolean"
          ? input.checked
          : typeof value === "number" || value === null
          ? input.value === "" ? null : Number(input.value)
          : input.value;
      }
      if (snapshot) {
        const type = snapshot.robots.type;
        snapshot.robots[type] = {
          ...snapshot.robots[type], n_envs: config.n_envs,
          video_fps: config.video_fps, video_layout: config.video_layout,
        };
      }
      const suite = $("task-selection").value === "suite";
      const group = catalog?.suites.find(item => item.id === $("task-name").value);
      const tasks = suite ? group?.tasks.filter(task => chosenTasks.has(task)) || [] : [$("task-name").value];
      if (!tasks.length || !tasks[0]) throw new Error("Select at least one task.");
      config.env_name = tasks.length === 1 ? tasks[0] : "";
      config.task_suite = tasks.length === 1 ? "" : currentBenchmark()?.named_suites && tasks.length === group.tasks.length
        ? group.id : tasks.join(',');
      if (suite && group.split) {
        config.split = group.split;
        if (snapshot) snapshot.robots[snapshot.robots.type].split = group.split;
        if (!getClientConfig) $("field-split").value = group.split;
      }
      if (!getClientConfig && config.mode !== "async") {
        config.async_replenish_threshold = null;
        config.max_async_observation_lag_steps = null;
      }
      if (!getClientConfig && !currentBenchmark()?.resampling_modes.includes(config.intra_chunk_mode))
        config.intra_chunk_sample_ratio = 1;
      const job = await api("/jobs", "POST", config);
      selected = job.id;
      if (prefix && typeof window.toast === "function")
        window.toast("Evaluation started.", "ok");
      await poll();
    } catch (e) {
      error(e);
    } finally {
      submitting = false;
      $("config").inert = false;
      await poll();
    }
  };
  function updateControls() {
    const benchmark = currentBenchmark();
    for (const key of ["video_fps", "video_layout"])
      $("field-" + key).parentElement.hidden = !$("field-video").checked;
    if (getClientConfig) $("video-settings").hidden = !$("field-video").checked;
    if (!getClientConfig) {
      for (const key of ["task_config", "instruction_type", "render_observation_mode", "split"])
        $("field-" + key).parentElement.hidden = !benchmark?.form_fields.includes(key);
      $("field-render_observation_mode").disabled = $("field-mode").value === "async";
      $("field-render_observation_mode").title = "Async mode always renders every action.";
      $("field-gpu").parentElement.firstChild.textContent = "GPU Indices (e.g. 0 or 0,1; Blank to Inherit)";
      for (const key of ["async_replenish_threshold", "max_async_observation_lag_steps"])
        $("field-" + key).parentElement.hidden = $("field-mode").value !== "async";
      $("field-intra_chunk_sample_ratio").parentElement.hidden =
        !benchmark?.resampling_modes.includes($("field-intra_chunk_mode").value);
    }

  }

  function createField(key, value, group) {
    const label = document.createElement("label");
    label.textContent = getClientConfig ? dashboardLabels[key] || labels[key] : labels[key];
    if (getClientConfig) {
      label.className = "simulation-field";
      label.title = labels[key];
    }
    const input = document.createElement(choices[key] ? "select" : "input");
    input.id = prefix + "field-" + key;
    if (choices[key]) input.append(...choices[key].map((v) => new Option(
      key === "render_observation_mode" ? {chunk_boundary: "Chunk boundaries", per_action: "Every action"}[v] : v, v
    )));
    else input.type = typeof value === "boolean" ? "checkbox"
      : typeof value === "number" || value === null ? "number" : "text";
    if (key === "task_config" && value && !choices[key].includes(value)) {
      input.append(new Option(value, value));
    }
    if (input.type !== "checkbox") input.className = "input-text";
    if (typeof value === "boolean") input.checked = value;
    else input.value = value == null ? "" : value;
    if (input.type === "number") input.step = "any";
    if (key === "n_envs") {
      input.min = "1";
      input.step = "1";
      input.required = true;
    }
    if (key === "video_fps") {
      input.min = "1";
      input.step = "1";
      input.required = true;
    }
    label.append(input);
    $(group).append(label);
  }

  function taskSummary() {
    const suite = $("task-selection").value === "suite";
    const count = suite ? chosenTasks.size : Number(Boolean($("task-name").value));
    const episodes = Number($("field-n_episodes")?.value || defaults.n_episodes);
    $("task-summary").textContent = `${count} tasks × ${episodes} episodes = ${count * episodes} total`;
  }

  function renderTaskList() {
    const group = catalog?.suites.find(item => item.id === $("task-name").value);
    const query = $("task-search").value.trim().toLowerCase();
    const rows = (group?.tasks || []).filter(task => task.toLowerCase().includes(query)).map(task => {
      const row = document.createElement("label");
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.value = task;
      checkbox.checked = chosenTasks.has(task);
      checkbox.onchange = () => {
        if (checkbox.checked) chosenTasks.add(task);
        else chosenTasks.delete(task);
        taskSummary();
      };
      row.append(checkbox, document.createTextNode(task));
      return row;
    });
    $("task-list").replaceChildren(...rows);
    taskSummary();
  }

  function chooseTask() {
    const suite = $("task-selection").value === "suite";
    $("task-picker").hidden = !suite;
    chosenTasks = new Set(catalog?.suites.find(item => item.id === $("task-name").value)?.tasks || []);
    $("task-search").value = "";
    renderTaskList();
  }

  function populateTasks() {
    const suite = $("task-selection").value === "suite";
    const options = suite ? (catalog?.suites || []).map(item => new Option(item.id, item.id))
      : (catalog?.tasks || []).map(task => new Option(task, task));
    $("task-name").replaceChildren(...options);
    const preferred = suite ? defaults.task_suite || 'target50' : defaults.env_name;
    if (options.some(option => option.value === preferred)) $("task-name").value = preferred;
    updateControls();
    chooseTask();
  }

  async function loadTasks(platform) {
    const generation = ++catalogGeneration;
    catalog = null;
    catalogPlatform = null;
    $("task-name").replaceChildren(new Option("Loading tasks…", ""));
    $("task-name").disabled = true;
    $("task-picker").hidden = true;
    const data = await api("/task-catalog?platform=" + platform);
    if (generation !== catalogGeneration || currentPlatform() !== platform) return false;
    catalog = data;
    catalogPlatform = platform;
    $("task-name").disabled = false;
    populateTasks();
    return true;
  }

  function createTaskSelection() {
    for (const [id, text] of [["task-selection", "Task Selection"], ["task-name", "Task"]]) {
      const label = document.createElement("label");
      label.textContent = text;
      if (getClientConfig) label.className = "simulation-field";
      const input = document.createElement("select");
      input.id = prefix + id;
      input.className = "input-text";
      if (id === "task-selection") {
        input.append(new Option("Single Task", "single"), new Option("Task Set", "suite"));
        input.value = defaults.task_suite ? "suite" : "single";
      } else input.required = true;
      label.append(input);
      $("fields").append(label);
    }
    const picker = document.createElement("div");
    picker.id = prefix + "task-picker";
    picker.className = "simulation-task-picker";
    picker.hidden = true;
    const toolbar = document.createElement("div");
    toolbar.className = "simulation-task-toolbar";
    const search = document.createElement("input");
    search.id = prefix + "task-search";
    search.type = "search";
    search.className = "input-text";
    search.placeholder = "Search tasks…";
    search.setAttribute("aria-label", "Search tasks");
    search.oninput = renderTaskList;
    toolbar.append(search);
    for (const [id, text] of [["task-all", "All"], ["task-none", "None"]]) {
      const button = document.createElement("button");
      button.id = prefix + id;
      button.type = "button";
      button.className = "btn btn-xs";
      button.textContent = text;
      button.onclick = () => {
        if (id === 'task-none') chosenTasks.clear();
        else $("task-list").querySelectorAll("input").forEach(input => chosenTasks.add(input.value));
        renderTaskList();
      };
      toolbar.append(button);
    }
    const list = document.createElement("div");
    list.id = prefix + "task-list";
    list.className = "simulation-task-list";
    picker.append(toolbar, list);
    const summary = document.createElement("p");
    summary.id = prefix + "task-summary";
    summary.className = "simulation-hint";
    $("fields").append(picker, summary);
    $("task-selection").onchange = populateTasks;
    $("task-name").onchange = chooseTask;
    $("fields").addEventListener("input", event => {
      if (event.target.id === prefix + "field-n_episodes") taskSummary();
    });
  }

  async function syncClientConfiguration() {
    const config = getClientConfig();
    const platform = platformForConfig(config);
    const summary = $("configuration-summary");
    if (!platform) {
      ready = false;
      $("start").disabled = true;
      summary.textContent = "Select a simulation robot in Configuration.";
      return;
    }
    summary.textContent = "Configuration: " + config.robots.type + " · " + (config.rdm?.mode || "sync");
    if (defaults.platform !== platform) {
      ready = false;
      $("start").disabled = true;
      const generation = ++profileGeneration;
      try {
        const profile = await api("/options?platform=" + platform);
        if (generation !== profileGeneration || platform !== currentPlatform()) return;
        defaults = profile;
        $("task-name").value = "";
      } catch (e) {
        error(e);
        return;
      }
    }
    if (catalogPlatform !== platform) {
      ready = false;
      try {
        if (!await loadTasks(platform)) return;
      } catch (e) {
        error(e);
        return;
      }
    }
    if (environmentPlatform !== platform) {
      const robot = config.robots[config.robots.type] || {};
      for (const key of ["n_envs", "video_fps", "video_layout"])
        $("field-" + key).value = robot[key] ?? defaults[key];
      environmentPlatform = platform;
    }
    updateControls();
    ready = true;
    await poll();
  }

  async function initialize() {
    try {
      benchmarkProfiles = await api('/benchmarks');
      choices.platform = benchmarkProfiles.map(spec => spec.id);
      if (prefix && typeof window.registerSimulationBenchmarks === 'function')
        window.registerSimulationBenchmarks(benchmarkProfiles);
      defaults = await api("/options");
      if (getClientConfig) {
        const summary = document.createElement("p");
        summary.id = prefix + "configuration-summary";
        summary.className = "simulation-hint";
        $("fields").before(summary);
        createTaskSelection();
      }
      for (const key of basicFields) {
        createField(key, defaults[key], "fields");
        if (key === "platform") createTaskSelection();
      }
      for (const key of advancedFields) createField(key, defaults[key], "advanced-fields");
      $("field-video").onchange = updateControls;
      await poll();
      if (!getClientConfig) {
        $("field-platform").onchange = async () => {
          ready = false;
          const generation = ++profileGeneration;
          $("start").disabled = true;
          try {
            const profile = await api("/options?platform=" + $("field-platform").value);
            if (generation !== profileGeneration) return;
            defaults = profile;
            $("field-n_action_steps").value = defaults.n_action_steps;
            $("field-seed").value = defaults.seed;
            $("field-task_config").value = defaults.task_config;
            $("field-instruction_type").value = defaults.instruction_type;
            $("field-render_observation_mode").value = defaults.render_observation_mode;
            $("field-video_fps").value = defaults.video_fps;
            $("field-video_layout").value = defaults.video_layout;
            $("task-name").value = "";
            if (!await loadTasks(currentPlatform())) return;
            updateControls();
            ready = true;
            await poll();
          } catch (e) {
            error(e);
          }
        };
        $("field-intra_chunk_mode").onchange = updateControls;
        $("field-mode").onchange = updateControls;
        await loadTasks(currentPlatform());
        updateControls();
        ready = true;
        await poll();
      } else {
        document.addEventListener("app-config-updated", syncClientConfiguration);
        await syncClientConfiguration();
      }
      setInterval(() => {
        if (!document.hidden) poll();
      }, 3000);
    } catch (e) {
      error(e);
    }
  }
  await initialize();
}

if (document.getElementById("config") && document.getElementById("fields"))
  initializeSimulation(document);
