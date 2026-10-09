const $ = (id) => document.getElementById(id);
const choices = {
  split: ["target", "pretrain"],
  mode: ["sync", "async"],
  intra_chunk_mode: ["raw", "interpolation", "fitting"],
  inter_chunk_mode: ["sync", "search_action", "smooth_velocity", "min_jerk"],
  mujoco_gl: ["egl", "osmesa", "glfw"],
  preprocess: ["none", "resize"],
  video_layout: ["grid", "single"],
};
const labels = {
  python: "Python 可执行文件",
  env_name: "单个任务（与任务集二选一）",
  task_suite: "任务集（如 target50）",
  split: "任务划分",
  n_episodes: "每任务 episode 数",
  n_envs: "并行环境数",
  n_action_steps: "动作块长度",
  seed: "随机种子",
  mode: "同步 / 异步",
  intra_chunk_mode: "块内平滑算法",
  intra_chunk_sample_ratio: "平滑采样倍率",
  inter_chunk_mode: "块间融合算法",
  async_replenish_threshold: "异步补充阈值（空为默认）",
  max_async_observation_lag_steps: "最大观测滞后步数（空为默认）",
  max_episode_steps: "最大 episode 步数（空为默认）",
  episode_timeout: "Episode 超时（秒）",
  stall_timeout: "无进展超时（秒）",
  server_ip: "模型服务地址",
  server_port: "模型服务端口",
  mujoco_gl: "渲染后端",
  preprocess: "图像预处理",
  record: "保存 LeRobot 数据集",
  video: "保存测评视频",
  record_fps: "数据集帧率",
  video_fps: "视频帧率",
  video_layout: "视频布局",
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
    ["任务", "已保存 episodes", "成功率"],
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
      ...jobs.map((j) => new Option(j.id + " · " + j.status, j.id))
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
    if (!selected) return;
    const [job, logs, files] = await Promise.all([
      api("/jobs/" + selected),
      api("/jobs/" + selected + "/logs"),
      api("/jobs/" + selected + "/files"),
    ]);
    $("status").textContent =
      "状态：" + job.status + " ｜ 保存目录：data/robocasa_web/jobs/" + job.id;
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
    await poll();
    setInterval(() => {
      if (!document.hidden) poll();
    }, 3000);
  } catch (e) {
    error(e);
  }
}
initialize();
