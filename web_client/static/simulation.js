export async function initializeSimulation(root, prefix = "", getClientConfig = null) {
  const $ = (id) => root.querySelector("#" + prefix + id);
  const choices = {
    platform: ["robocasa", "robotwin"],
    instruction_type: ["seen", "unseen"],
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
  const advancedFields = getClientConfig ? [] : [
    "n_envs", "gpu", "n_action_steps", "seed", "intra_chunk_mode", "inter_chunk_mode",
    "intra_chunk_sample_ratio", "async_replenish_threshold", "max_async_observation_lag_steps",
    "task_config", "instruction_type", "split",
  ];
  let defaults,
    selected = "",
    busy = false,
    ready = false,
    submitting = false,
    profileGeneration = 0,
    environmentPlatform = null,
    lastError = "",
    artifactJob = "";
  const platformForConfig = (config) => ({robocasa: "robocasa", aloha_robotwin: "robotwin"})[config.robots?.type];
  const currentPlatform = () => getClientConfig
    ? platformForConfig(getClientConfig()) : $("field-platform").value;
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
    if (prefix && lastError !== e.message && typeof window.toast === "function")
      window.toast(e.message, "error");
    lastError = e.message;
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
        return;
      }
      const [job, logs, files] = await Promise.all([
        api("/jobs/" + selected),
        api("/jobs/" + selected + "/logs"),
        api("/jobs/" + selected + "/files"),
      ]);
      const directory = "data/robocasa_web/jobs/" + job.id;
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
        if (prefix && typeof window.toast === "function")
          window.toast(action === "stop" ? "Evaluation stop requested." : "Evaluation resumed.", "ok");
        await poll();
      } catch (e) {
        error(e);
      }
    };
  $("config").onsubmit = async (event) => {
    event.preventDefault();
    $("error").textContent = "";
    try {
      if (!ready || submitting) return;
      submitting = true;
      $("config").inert = true;
      $("start").disabled = true;
      const platform = currentPlatform();
      const snapshot = getClientConfig ? getClientConfig() : null;
      if (getClientConfig && !platformForConfig(snapshot))
        throw new Error("Select robocasa or aloha_robotwin in Configuration.");
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
        snapshot.robots[type] = { ...snapshot.robots[type], n_envs: config.n_envs };
      }
      const suite = $("task-selection").value === "suite";
      config.env_name = suite ? "" : $("task-name").value.trim();
      config.task_suite = suite ? $("task-name").value.trim() : "";
      if (!getClientConfig && config.mode !== "async") {
        config.async_replenish_threshold = null;
        config.max_async_observation_lag_steps = null;
      }
      if (!getClientConfig && platform === "robotwin" && config.intra_chunk_mode !== "interpolation")
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
    const robotwin = currentPlatform() === "robotwin";
    if (!getClientConfig) {
      for (const key of ["task_config", "instruction_type"])
        $("field-" + key).parentElement.hidden = !robotwin;
      $("field-split").parentElement.hidden = robotwin;
      $("field-gpu").parentElement.firstChild.textContent = robotwin
        ? "GPU Indices (e.g. 0 or 0,1; Blank to Inherit)"
        : "Simulation GPU Index (e.g. 2; Blank to Inherit)";
      for (const key of ["async_replenish_threshold", "max_async_observation_lag_steps"])
        $("field-" + key).parentElement.hidden = $("field-mode").value !== "async";
      $("field-intra_chunk_sample_ratio").parentElement.hidden =
        robotwin && $("field-intra_chunk_mode").value !== "interpolation";
    }
    const suite = $("task-selection").value === "suite";
    $("task-name").parentElement.firstChild.textContent = suite
      ? robotwin ? "Task List" : "Task Suite"
      : "Task";
    $("task-name").placeholder = suite
      ? robotwin ? "task_a,task_b or task-list YAML path" : "target50"
      : robotwin ? "Task name" : "PickPlaceCounterToCabinet";
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
    if (choices[key]) input.append(...choices[key].map((v) => new Option(v, v)));
    else input.type = typeof value === "boolean" ? "checkbox"
      : typeof value === "number" || value === null ? "number" : "text";
    if (input.type !== "checkbox") input.className = "input-text";
    if (typeof value === "boolean") input.checked = value;
    else input.value = value == null ? "" : value;
    if (input.type === "number") input.step = "any";
    if (key === "n_envs") {
      input.min = "1";
      input.step = "1";
      input.required = true;
    }
    label.append(input);
    $(group).append(label);
  }

  function createTaskSelection() {
    for (const [id, text] of [["task-selection", "Task Selection"], ["task-name", "Task"]]) {
      const label = document.createElement("label");
      label.textContent = text;
      if (getClientConfig) label.className = "simulation-field";
      const input = document.createElement(id === "task-selection" ? "select" : "input");
      input.id = prefix + id;
      input.className = "input-text";
      if (id === "task-selection") {
        input.append(new Option("Single Task", "single"), new Option("Task Suite / List", "suite"));
        input.value = defaults.task_suite ? "suite" : "single";
      } else {
        input.type = "text";
        input.required = true;
        input.value = defaults.env_name || defaults.task_suite;
      }
      label.append(input);
      $("fields").append(label);
    }
    $("task-selection").onchange = () => {
      $("task-name").value = "";
      updateControls();
    };
  }

  async function syncClientConfiguration() {
    const config = getClientConfig();
    const platform = platformForConfig(config);
    const summary = $("configuration-summary");
    if (!platform) {
      ready = false;
      $("start").disabled = true;
      summary.textContent = "Select robocasa or aloha_robotwin in Configuration.";
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
    if (environmentPlatform !== platform) {
      $("field-n_envs").value = config.robots[config.robots.type]?.n_envs ?? defaults.n_envs;
      environmentPlatform = platform;
    }
    updateControls();
    ready = true;
    await poll();
  }

  async function initialize() {
    try {
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
            $("task-name").value = "";
            updateControls();
            ready = true;
            await poll();
          } catch (e) {
            error(e);
          }
        };
        $("field-intra_chunk_mode").onchange = updateControls;
        $("field-mode").onchange = updateControls;
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
