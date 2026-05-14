/**
 * VLA Web Client — Frontend Logic
 *
 * WebSocket: ws://localhost:9000/ws
 *   Receives: { type: 'stats'|'status'|'error', data: {...} }
 *
 * REST endpoints:
 *   GET  /api/config
 *   POST /api/config/patch       { patch: { "key.path": value, ... } }
 *   POST /api/config/load_file   { path: "..." }
 *   POST /api/config/save_file   { path: "..." }
 *   GET  /api/client/status
 *   POST /api/client/start
 *   POST /api/client/stop
 *   POST /api/client/pause
 *   POST /api/client/resume
 *   POST /api/client/command     { command, params }
 */

'use strict';

// ═══════════════════════════════════════════════════════
//  Constants
// ═══════════════════════════════════════════════════════
const WS_URL    = `ws://${location.host}/ws`;
const RECONNECT = 3000;

// Visual WebSocket — connects to VLAWebSocketServer (port 8765) for camera frames
const CAM_WS_URL       = `ws://${location.hostname}:8765`;
const CAM_WS_RECONNECT = 3000;

// Trajectory x-axis window span (seconds).
// Historical mapping: old point-count window used 600 points with fitting_time_step=3.75ms => 2.25s.
const TRAJ_WINDOW_SPAN_SEC = 10.0;
// Maximum supported trajectory window span (seconds).
const TRAJ_WINDOW_SPAN_SEC_MAX = 15.0;
// Hard cap for safety under very high-frequency streams.
const TRAJ_BUFFER_HARD_MAX_POINTS = 20000;
// Default trajectory chart update interval in ms (20 FPS)
const DEFAULT_TRAJ_UPDATE_MS = 50;

// Per-joint colour palette (14 colours, one per joint L0-L6 R0-R6)
const JOINT_COLORS = [
  // L0-L6: High contrast bright colors
  'rgb(220, 20, 60)',   // L0 - Crimson red
  'rgb(255, 140, 0)',   // L1 - Dark orange
  'rgb(255, 0, 255)',   // L2 - Magenta (changed from purple for better contrast)
  'rgb(0, 150, 0)',     // L3 - Forest green (changed from green for better contrast)
  'rgb(0, 70, 255)',    // L4 - Strong blue (changed from blue for better contrast)
  'rgb(75, 0, 130)',    // L5 - Indigo
  'rgb(186, 85, 211)',  // L6 - Medium purple (changed from violet for better contrast)
  
  // R0-R6: Contrasting colors from the first set
  'rgb(0, 191, 255)',   // R0 - Deep sky blue (changed from magenta to avoid repetition)
  'rgb(255, 20, 147)',  // R1 - Deep pink
  'rgb(139, 69, 19)',   // R2 - Saddle brown (changed from brown for better contrast)
  'rgb(184, 134, 11)',  // R3 - Dark goldenrod (changed from olive for better contrast)
  'rgb(0, 128, 128)',   // R4 - Teal
  'rgb(160, 32, 240)',  // R5 - Purple (changed from sienna for better contrast)
  'rgb(255, 105, 180)', // R6 - Hot pink (changed from crimson to ensure uniqueness)
];

// ═══════════════════════════════════════════════════════
//  State
// ═══════════════════════════════════════════════════════
let _visualPersistTimer = null;
let _visualPersistInFlight = false;

const App = {
  ws: null,
  wsAlive: false,
  reconnectTimer: null,
  isRunning: null,   // null = uninitialised; set on first stats push
  isPaused: false,   // true when client is paused (inference/commands paused but resources alive)

  // Camera WebSocket (port 8765 — VLAWebSocketServer)
  camWs: null,
  camWsAlive: false,
  camWsReconnectTimer: null,

  config: {},
  pendingPatch: {},
  langPresets: [],

  // Camera open/close state — default all closed
  camOpen: [false, false, false],

  // Language auto mode state
  langAuto: {
    lastProgress: null,
  },

  // ── Trajectory chart state ──
  traj: {
    // Set<'state'|'action_fitted'|'action_raw'> — which sources to display (can be combined)
    source: new Set(['state']),
    // Default manual mode: do not play until user clicks Play
    paused: true,
    // Number of joints (determined from first data push)
    numJoints: 0,
    // Which joints to display  Set<number>
    selectedJoints: new Set(),
    // Data buffer: { state: [...], action_fitted: [...], action_raw: [...] }
    buffer: { state: [], action_fitted: [], action_raw: [] },
    // Time axis baseline and monotonic guard (x-axis in seconds)
    startTimeSec: null,
    lastX: 0,
    // x window bounds
    xLeft: 0, xRight: 0,
    // fixed x-axis sliding window span in seconds
    windowSpanSec: normalizeTrajWindowSpanSec(TRAJ_WINDOW_SPAN_SEC),
    // Single unified Chart.js instance
    chart: null,
    // Dirty flag → batch updates at configured interval
    dirty: false,
    updateIntervalMs: DEFAULT_TRAJ_UPDATE_MS,
    updateTimer: null,
    lastUpdateAt: 0,
  },

  recordingListTimer: null,
};

// ═══════════════════════════════════════════════════════
//  DOM helpers
// ═══════════════════════════════════════════════════════
const $ = id => document.getElementById(id);

function toast(msg, type = 'info', duration = 3500) {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  $('toast-container').appendChild(el);
  setTimeout(() => {
    el.style.animation = 'fadeOut .3s forwards';
    el.addEventListener('animationend', () => el.remove());
  }, duration);
}

async function apiFetch(url, opts = {}) {
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' }, ...opts,
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || JSON.stringify(json));
    return json;
  } catch (e) {
    toast(e.message, 'error');
    throw e;
  }
}

// ═══════════════════════════════════════════════════════
//  WebSocket
// ═══════════════════════════════════════════════════════
function connectWS() {
  if (App.ws && App.ws.readyState <= 1) return;
  App.ws = new WebSocket(WS_URL);

  App.ws.onopen = () => {
    App.wsAlive = true;
    updateWSIndicator(true);
    clearTimeout(App.reconnectTimer);
    App._pingTimer = setInterval(() => {
      if (App.ws.readyState === 1) App.ws.send(JSON.stringify({ type: 'ping' }));
    }, 15000);
  };

  App.ws.onmessage = (ev) => {
    try { handleWSMessage(JSON.parse(ev.data)); } catch (e) { /* ignore */ }
  };

  App.ws.onclose = () => {
    App.wsAlive = false;
    updateWSIndicator(false);
    clearInterval(App._pingTimer);
    App.reconnectTimer = setTimeout(connectWS, RECONNECT);
  };

  App.ws.onerror = () => App.ws.close();
}

// ═══════════════════════════════════════════════════════
//  Camera WebSocket (VLAWebSocketServer — port 8765)
// ═══════════════════════════════════════════════════════
function connectCamWS() {
  if (App.camWs && App.camWs.readyState <= 1) return;
  App.camWs = new WebSocket(CAM_WS_URL);
  App.camWs.binaryType = 'arraybuffer';

  App.camWs.onopen = () => {
    App.camWsAlive = true;
    clearTimeout(App.camWsReconnectTimer);
  };

  App.camWs.onmessage = (ev) => {
    if (ev.data instanceof ArrayBuffer || ev.data instanceof Blob) {
      decodeCameraBinaryFrame(ev.data);
      return;
    }

    if (typeof ev.data === 'string') {
      try {
        handleCamWSMessage(JSON.parse(ev.data));
      } catch (e) { /* ignore malformed text frame */ }
    }
  };

  App.camWs.onclose = () => {
    App.camWsAlive = false;
    if (App.isRunning) {
      App.camWsReconnectTimer = setTimeout(connectCamWS, CAM_WS_RECONNECT);
    }
  };

  App.camWs.onerror = () => {
    if (App.camWs) App.camWs.close();
  };
}

function disconnectCamWS() {
  clearTimeout(App.camWsReconnectTimer);
  if (App.camWs) {
    App.camWs.onclose = null; // prevent auto-reconnect after manual close
    App.camWs.close();
    App.camWs = null;
  }
  App.camWsAlive = false;
}

function handleWSMessage(msg) {
  switch (msg.type) {
    case 'stats':  renderStats(msg.data); break;
    case 'status': toast(msg.data.message, msg.data.running || msg.data.paused ? 'ok' : 'warn'); setRunningUI(msg.data.running, msg.data.paused ?? false); break;
    case 'error':  toast(msg.data.message, 'error'); setRunningUI(false, false); break;
    case 'pong':   break;
  }
}

/**
 * Decode binary camera frame — mirrors visual/app.js protocol:
 *   [4 bytes: uint32 headerLen][headerLen bytes: JSON][rest: JPEG bytes]
 * header JSON: { type: 'camera_data_binary', camera_id: 0|1|2, ... }
 */
async function decodeCameraBinaryFrame(raw) {
  try {
    // Mirror visual/app.js::handleBinaryMessage protocol
    const arrayBuffer = raw instanceof Blob ? await raw.arrayBuffer() : raw;
    if (!(arrayBuffer instanceof ArrayBuffer) || arrayBuffer.byteLength < 4) return;

    const dataView = new DataView(arrayBuffer);

    // Header length (first 4 bytes, big-endian)
    const headerLength = dataView.getUint32(0, false);
    if (headerLength <= 0 || (4 + headerLength) > arrayBuffer.byteLength) return;

    // Header JSON
    const headerBytes = new Uint8Array(arrayBuffer, 4, headerLength);
    const headerText = new TextDecoder().decode(headerBytes);
    const header = JSON.parse(headerText);

    // Payload (image bytes)
    const payloadStart = 4 + headerLength;
    const declaredSize = Number(header.data_size);
    const payloadEnd = Number.isFinite(declaredSize) && declaredSize > 0
      ? Math.min(arrayBuffer.byteLength, payloadStart + declaredSize)
      : arrayBuffer.byteLength;
    if (payloadEnd <= payloadStart) return;

    // Copy payload to independent buffer to avoid byteOffset-related corruption
    const imageData = new Uint8Array(arrayBuffer.slice(payloadStart, payloadEnd));

    if (header.type === 'camera_data_binary') {
      const cameraId = header.camera_id;
      if (cameraId === undefined || cameraId === null) return;
      handleCameraFrame(Number(cameraId), imageData);
    }
  } catch (e) { /* malformed frame, ignore */ }
}

function handleCamWSMessage(msg) {
  if (!msg || msg.type !== 'joint_data' || !msg.data) return;

  const { tab, type, joints_y, timestamp } = msg.data;
  if (tab !== 'position' || !Array.isArray(joints_y) || joints_y.length === 0) return;

  if (type === 'state') {
    ingestTrajData(joints_y, [], [], timestamp);
  } else if (type === 'action_fitted' || type === 'action') {
    ingestTrajData([], joints_y, [], timestamp);
  } else if (type === 'action_raw' || type === 'origin') {
    ingestTrajData([], [], joints_y, timestamp);
  }
}

function updateWSIndicator(connected) {
  $('ws-indicator').className = `ws-dot ${connected ? 'connected' : 'disconnected'}`;
}

// ═══════════════════════════════════════════════════════
//  Default demo values for State & Action (shown when client is not running)
//  Layout: J0-6 = Arm-Left (7), J7-13 = Arm-Right (7), J14-15 = Gripper (2)
// ═══════════════════════════════════════════════════════
const DEFAULT_JOINTS = Object.freeze([
  // Arm-Left  J0-J6  (values in 100-180 range for label width validation)
  0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000,
  // Arm-Right J7-J13
  0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000,
  // Gripper   J14-J15
  0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000
]);

/** Add small Gaussian-like noise to DEFAULT_JOINTS for a lifelike idle display. */
function _makeDefaultJointValues(noiseScale = 0.03) {
  return DEFAULT_JOINTS.map(v => {
    const noise = (Math.random() + Math.random() + Math.random() - 1.5) * noiseScale;
    return Math.round((v + noise) * 100) / 100;
  });
}

// Cache default values so they don't flicker on every render cycle
let _defaultStateCache  = null;
let _defaultActionCache = null;

function getDefaultState()  { if (!_defaultStateCache)  _defaultStateCache  = _makeDefaultJointValues(0.00); return _defaultStateCache; }
function getDefaultAction() { if (!_defaultActionCache) _defaultActionCache = _makeDefaultJointValues(0.00); return _defaultActionCache; }

// ═══════════════════════════════════════════════════════
//  Stats rendering
// ═══════════════════════════════════════════════════════
function renderStats(data) {
  setRunningUI(data.running, data.paused ?? false);

  $('val-infer-count').textContent = data.infer_count ?? '–';
  $('val-infer-time').textContent  = data.avg_infer_time != null
    ? (data.avg_infer_time * 1000).toFixed(1) + ' ms' : '–';
  $('val-traj-time').textContent   = data.avg_traj_time != null
    ? (data.avg_traj_time * 1000).toFixed(1) + ' ms' : '–';

  updateTaskProgress(data?.current_prob_progress ?? data?.info_act?.current_prob_progress);

  const cpuVal = Number(data.cpu_usage);
  const gpuVal = Number(data.gpu_usage);
  const memVal = Number(data.mem_usage);
  const bwVal = Number(data.bandwidth_m);
  const cpuEl = $('val-cpu-usage');
  const gpuEl = $('val-gpu-usage');
  const memEl = $('val-mem-usage');
  const bwEl = $('val-bw-usage');

  const setResourceValue = (el, value, label) => {
    if (!el) return;
    const valueEl = el.querySelector('.resource-value');
    if (valueEl) {
      valueEl.textContent = value;
    } else {
      el.textContent = `${label} ${value}`;
    }
  };

  setResourceValue(cpuEl, Number.isFinite(cpuVal) ? cpuVal.toFixed(1) + '%' : '--', 'CPU');
  setResourceValue(gpuEl, Number.isFinite(gpuVal) ? gpuVal.toFixed(1) + '%' : '--', 'GPU');
  setResourceValue(memEl, Number.isFinite(memVal) ? memVal.toFixed(1) + '%' : '--', 'MEM');
  setResourceValue(bwEl, Number.isFinite(bwVal) ? bwVal.toFixed(2) + 'M' : '--', 'BW');

  // Use default joint values when client is not running and no real data available
  const stateVals  = (data.current_state  && data.current_state.length)  ? data.current_state  : getDefaultState();
  const actionVals = (data.current_action && data.current_action.length) ? data.current_action : getDefaultAction();
  renderJointsGrouped('state',  stateVals);
  renderJointsGrouped('action', actionVals);

  $('debug-info').textContent = data.debug_info || '';

  // Feed trajectory chart from stats only when visual WS stream is unavailable.
  // Avoid mixing two data sources (different timestamps/rates), which causes jitter.
  if (!App.camWsAlive) {
    ingestTrajData(data.current_state || [], data.current_action || [], []);
  }
}

function renderKV(containerId, obj) {
  const el = $(containerId);
  if (!el) return;
  el.innerHTML = '';
  for (const [k, v] of Object.entries(obj)) {
    const kEl = document.createElement('div'); kEl.className = 'kv-key'; kEl.textContent = k;
    const vEl = document.createElement('div'); vEl.className = 'kv-val'; vEl.textContent = v;
    el.appendChild(kEl); el.appendChild(vEl);
  }
}

function renderJoints(containerId, values) {
  const el = $(containerId);
  if (!el) return;
  el.innerHTML = '';
  values.forEach((v, i) => {
    const chip = document.createElement('div');
    chip.className = 'joint-chip';
    chip.textContent = `J${i}: ${typeof v === 'number' ? v.toFixed(3) : v}`;
    el.appendChild(chip);
  });
}

function updateTaskProgress(rawProgress) {
  const fillEl = $('task-progress-fill');
  const valueEl = $('task-progress-value');
  if (!fillEl || !valueEl) return;

  const parsed = Number(rawProgress);
  if (!Number.isFinite(parsed)) {
    fillEl.style.width = '0%';
    valueEl.textContent = '--';
    App.langAuto.lastProgress = null;
    return;
  }

  const clamped = Math.max(0, Math.min(1, parsed));
  fillEl.style.width = `${(clamped * 100).toFixed(1)}%`;
  valueEl.textContent = `${(clamped * 100).toFixed(1)}%`;
  maybeAutoSwitchLanguageByProgress(clamped);
}

function maybeAutoSwitchLanguageByProgress(progress01) {
  const autoChk = $('chk-lang-auto-mode');
  if (!autoChk || !autoChk.checked) {
    App.langAuto.lastProgress = progress01;
    return;
  }

  const taskSel = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  const textEl = $('lang-cmd-text');
  if (!taskSel || !subtaskSel || !textEl) return;

  const taskName = taskSel.value;
  const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
  const n = subtasks.length;
  if (n <= 1) {
    App.langAuto.lastProgress = progress01;
    return;
  }

  const prev = App.langAuto.lastProgress;
  App.langAuto.lastProgress = progress01;
  if (!Number.isFinite(prev)) return;

  let curIdx = parseInt(subtaskSel.value, 10);
  if (!Number.isFinite(curIdx) || curIdx < 0) curIdx = 0;

  let nextIdx = curIdx;
  while (nextIdx < n - 1) {
    const threshold = (nextIdx + 1) / n;
    if (prev < threshold && progress01 >= threshold) nextIdx += 1;
    else break;
  }

  if (nextIdx === curIdx) return;

  subtaskSel.value = String(nextIdx);
  subtaskSel.dispatchEvent(new Event('change'));

  const lang = subtasks[nextIdx];
  if (typeof lang === 'string' && lang.trim()) {
    textEl.value = lang;
    sendCommand('set_language', { language: lang });
  }
}

// Joint layout: J0-6 = Arm Left (7), J7-13 = Arm Right (7), J14+ = Gripper/Hand
const JOINT_ARM_L_COUNT   = 7;
const JOINT_ARM_R_COUNT   = 7;
// J0..6 → Arm-L, J7..13 → Arm-R, J14+ → Gripper/Hand

function renderJointsGrouped(side, values) {
  // side: 'state' | 'action'
  const elArmL    = $(`joint-${side}-arm-l`);
  const elArmR    = $(`joint-${side}-arm-r`);
  const elGripper = $(`joint-${side}-gripper`);
  if (!elArmL) return;

  elArmL.innerHTML = '';
  elArmR.innerHTML = '';
  elGripper.innerHTML = '';

  values.forEach((v, i) => {
    const chip = document.createElement('div');
    chip.className = 'joint-chip';
    const val = typeof v === 'number' ? v.toFixed(4) : v;
    if (i < JOINT_ARM_L_COUNT) {
      // chip.textContent = `L${i}: ${val}`;
      chip.textContent = `${i}｜${val}`;
      elArmL.appendChild(chip);
    } else if (i < JOINT_ARM_L_COUNT + JOINT_ARM_R_COUNT) {
      // chip.textContent = `R${i - JOINT_ARM_L_COUNT}: ${val}`;
      chip.textContent = `${i - JOINT_ARM_L_COUNT}｜${val}`;
      elArmR.appendChild(chip);
    } else {
      // chip.textContent = `G${i - JOINT_ARM_L_COUNT - JOINT_ARM_R_COUNT}: ${val}`;
      chip.textContent = `${i - JOINT_ARM_L_COUNT - JOINT_ARM_R_COUNT}｜${val}`;
      elGripper.appendChild(chip);
    }
  });
}

// ═══════════════════════════════════════════════════════
//  Running state UI
// ═══════════════════════════════════════════════════════
/**
 * Update button states and status badge.
 * @param {boolean} running  - Whether the vla_client process is alive.
 * @param {boolean} paused   - Whether inference/robot commands are stopped (is_running_action=False).
 *
 * Button availability matrix:
 *   State            | Start/Stop | Pause/Resume | Reset
 *   -----------------+------------+--------------+------
 *   Not running      |  Start     |  ✗           |  ✗
 *   Running (active) |  Stop      |  Pause       |  ✓
 *   Running (paused) |  Stop      |  Resume      |  ✓
 */
async function syncRuntimeCameraConfig() {
  if (!App.isRunning) return;
  try {
    await apiFetch('/api/visual/camera_cfg', {
      method: 'POST',
      body: JSON.stringify({
        open_head: !!App.camOpen[0],
        open_wrist_left: !!App.camOpen[1],
        open_wrist_right: !!App.camOpen[2],
      }),
    });
  } catch (_) {
    // no-op
  }
}

function setRunningUI(running, paused = false) {
  if (App.isRunning === running && App.isPaused === paused) return;
  const wasRunning = App.isRunning === true;
  App.isRunning = running;
  App.isPaused  = paused;

  // Camera Visual: connect dedicated WS server when running
  if (running) {
    connectCamWS();
    syncRuntimeCameraConfig();
  } else {
    disconnectCamWS();
  }

  // Status badge
  let badgeText, badgeClass;
  if (!running) {
    badgeText  = 'STOPPED';
    badgeClass = 'stopped';
  } else if (paused) {
    badgeText  = 'PAUSED';
    badgeClass = 'paused';
  } else {
    badgeText  = 'RUNNING';
    badgeClass = 'running';
  }
  $('status-badge').textContent = badgeText;
  $('status-badge').className   = `status-badge ${badgeClass}`;

  // btn-start toggles Start/Stop
  const btnStart = $('btn-start');
  if (running) {
    btnStart.textContent = '■ Stop';
    btnStart.className = 'btn btn-danger btn-sm';
  } else {
    btnStart.textContent = '▶ Start';
    btnStart.className = 'btn btn-success btn-sm';
  }
  btnStart.disabled = false;

  // Pause button toggles Pause/Resume while running
  const btnPause = $('btn-pause');
  btnPause.disabled = !running;
  if (!running) {
    btnPause.textContent = '⏸ Pause';
    btnPause.className = 'btn btn-danger  btn-sm';
  } else if (paused) {
    btnPause.textContent = '▶ Resume';
    btnPause.className = 'btn btn-success btn-sm';
  } else {
    btnPause.textContent = '⏸ Pause';
    btnPause.className = 'btn btn-danger  btn-sm';
  }

  $('btn-reset').disabled = !running;             // available in both running states

  // Persist visual state only when transitioning from running -> stopped.
  // Avoid startup/status-sync overwriting config before user interaction.
  if (!running && wasRunning) {
    schedulePersistVisualState(0);
  }
}

// ═══════════════════════════════════════════════════════
//  Config rendering — BASIC group split into sub-groups
// ═══════════════════════════════════════════════════════

// Keys to exclude from the config tree (handled separately or rendered via createLangLinkRow)
const CONFIG_EXCLUDED_KEYS = new Set(['language']);

// Sub-group definitions for root-level leaf keys in the BASIC section
const BASIC_SUBGROUPS = {
  intra_chunk: ['intra_chunk_mode', 'fitting_deg', 'fitting_num_samples', 'fitting_time_step'],
  inter_chunk: ['inter_chunk_mode', 'search_length', 'smooth_action', 'smooth_base', 'smooth_length', 'smooth_ratio'],
};

// Select options for specific keys
const CONFIG_SELECT_OPTIONS = {
  inter_chunk_mode: ['search_action', 'poly', 'smooth_velocity', 'min_jerk', 'bspline', 'sync'],
  intra_chunk_mode: ['raw', 'raw_ipt', 'fit'],
  fitting_deg: [3, 4, 5, 6],
  preprocess: ['crop_and_resize', 'pad_and_resize', 'resize', 'none'],
  type: ['a2d', 'mock']
};

// Keys that must be treated as integers (rendered as number input, parsed with parseInt)
const CONFIG_INT_KEYS = new Set([
  'fitting_num_samples', 'search_length', 'smooth_length', 'gripper_offset',
  'fps', 'height', 'width', 'update_interval_ms',
]);

const CONFIG_HIDDEN_DOT_KEYS = new Set([
  'language.task_id',
  'language.sub_task_id',
  'language.auto_mode',
  'language.task_progress_threshold',
  'visual.camera.connect_when_running',
  'visual.camera.open_head',
  'visual.camera.open_wrist_left',
  'visual.camera.open_wrist_right',
  'visual.trajectory.selected_joints',
  'visual.trajectory.source',
  'visual.trajectory.window_span_sec',
]);

function getCfgMultiSelectOptions(dotKey) {
  if (dotKey === 'visual.trajectory.source') {
    return [
      { value: 'State', label: 'State' },
      { value: 'ActionFitted', label: 'ActionFitted' },
      { value: 'ActionRaw', label: 'ActionRaw' },
    ];
  }

  if (dotKey === 'visual.trajectory.selected_joints') {
    return TRAJ_JOINT_LABELS.map((name, idx) => ({ value: String(idx), label: `${name} (${idx})` }));
  }

  return null;
}

function renderConfigTree(cfg) {
  const root = $('config-tree');
  root.innerHTML = '';
  buildTree(cfg, '', root);
}

function buildTree_old(obj, prefix, parentEl) {
  const basicEntries    = [];
  const subGroupEntries = [];

  for (const [key, val] of Object.entries(obj)) {
    // Skip excluded keys at root level
    if (!prefix && CONFIG_EXCLUDED_KEYS.has(key)) continue;

    const isGroup = val !== null && typeof val === 'object' && !Array.isArray(val);
    if (isGroup) {
      subGroupEntries.push([key, val]);
    } else if (!prefix) {
      basicEntries.push([key, val]);
    } else {
      const dotKey = `${prefix}.${key}`;
      if (CONFIG_HIDDEN_DOT_KEYS.has(dotKey)) continue;
      parentEl.appendChild(createCfgRow(dotKey, key, val));
    }
  }

  // BASIC group for root-level leaves — split into sub-groups
  if (basicEntries.length > 0) {
    // Assign each basic entry to its sub-group or "others"
    const sgMap = {};
    for (const sgName of Object.keys(BASIC_SUBGROUPS)) sgMap[sgName] = [];
    sgMap['others'] = [];

    for (const [k, v] of basicEntries) {
      let placed = false;
      for (const [sgName, keys] of Object.entries(BASIC_SUBGROUPS)) {
        if (keys.includes(k)) { sgMap[sgName].push([k, v]); placed = true; break; }
      }
      if (!placed) sgMap['others'].push([k, v]);
    }

    // Build the outer BASIC group
    const basicBody = document.createElement('div');
    basicBody.className = 'cfg-group-body';

    for (const [sgName, entries] of Object.entries(sgMap)) {
      if (entries.length === 0) continue;
      const rows = entries.map(([k, v]) => createCfgRow(k, k, v));
      basicBody.appendChild(buildGroup(sgName.toUpperCase().replace('_', '-'), rows));
    }

    parentEl.appendChild(buildGroupFromEl('BASIC', basicBody));
  }

  // Sub-groups
  for (const [key, val] of subGroupEntries) {
    const dotKey  = prefix ? `${prefix}.${key}` : key;
    const body    = document.createElement('div');
    body.className = 'cfg-group-body';
    buildTree(val, dotKey, body);
    parentEl.appendChild(buildGroupFromEl(key.toUpperCase(), body));
  }
}
function buildTree(obj, prefix, parentEl) {
  const basicEntries    = [];
  const subGroupEntries = [];

  for (const [key, val] of Object.entries(obj)) {
    // Skip excluded keys at root level
    if (!prefix && CONFIG_EXCLUDED_KEYS.has(key)) continue;

    const isGroup = val !== null && typeof val === 'object' && !Array.isArray(val);
    if (isGroup) {
      subGroupEntries.push([key, val]);
    } else if (!prefix) {
      basicEntries.push([key, val]);
    } else {
      const dotKey = `${prefix}.${key}`;
      if (CONFIG_HIDDEN_DOT_KEYS.has(dotKey)) continue;
      parentEl.appendChild(createCfgRow(dotKey, key, val));
    }
  }

  // 1. Render BASIC group first (if there are root-level leaves)
  if (basicEntries.length > 0) {
    // Assign each basic entry to its sub-group or "others"
    const sgMap = {};
    for (const sgName of Object.keys(BASIC_SUBGROUPS)) sgMap[sgName] = [];
    sgMap['others'] = [];

    for (const [k, v] of basicEntries) {
      let placed = false;
      for (const [sgName, keys] of Object.entries(BASIC_SUBGROUPS)) {
        if (keys.includes(k)) { sgMap[sgName].push([k, v]); placed = true; break; }
      }
      if (!placed) sgMap['others'].push([k, v]);
    }

    // Build the outer BASIC group
    const basicBody = document.createElement('div');
    basicBody.className = 'cfg-group-body';

    for (const [sgName, entries] of Object.entries(sgMap)) {
      if (entries.length === 0) continue;
      const rows = entries.map(([k, v]) => createCfgRow(k, k, v));
      basicBody.appendChild(buildGroup(sgName.toUpperCase().replace('_', '-'), rows));
    }

    parentEl.appendChild(buildGroupFromEl('BASIC', basicBody));
  }

  // 2. Define custom order for sub-groups
  // List the keys in the order you want them to appear.
  // Keys not listed here will appear at the end in their original order.
  const CUSTOM_GROUP_ORDER = [
    'robots',
    'visual',
    // Add other keys here if you want to reorder them too, e.g., 'record', 'traj'
  ];

  // 3. Sort subGroupEntries based on CUSTOM_GROUP_ORDER
  subGroupEntries.sort((a, b) => {
    const keyA = a[0].toLowerCase();
    const keyB = b[0].toLowerCase();
    
    const indexA = CUSTOM_GROUP_ORDER.indexOf(keyA);
    const indexB = CUSTOM_GROUP_ORDER.indexOf(keyB);
    
    // If both are in the custom list, sort by their index
    if (indexA !== -1 && indexB !== -1) {
      return indexA - indexB;
    }
    // If only A is in the list, A comes first
    if (indexA !== -1) return -1;
    // If only B is in the list, B comes first
    if (indexB !== -1) return 1;
    // If neither is in the list, maintain original relative order (stable sort)
    return 0;
  });

  // 4. Render sorted sub-groups
  for (const [key, val] of subGroupEntries) {
    const dotKey  = prefix ? `${prefix}.${key}` : key;
    const body    = document.createElement('div');
    body.className = 'cfg-group-body';
    // ROBOTS group: custom rendering with type-driven sub-group visibility
    if (!prefix && key === 'robots') {
      _buildRobotsGroup(val, body);
    } else {
      buildTree(val, dotKey, body);
    }
    parentEl.appendChild(buildGroupFromEl(key.toUpperCase(), body));
  }
}
// ═══════════════════════════════════════════════════════
//  Robots group — dynamic sub-group visibility by type
// ═══════════════════════════════════════════════════════

/**
 * Renders the robots config group with dynamic sub-group visibility.
 * The robots.type select controls which sub-group (a2d / mock / …) is shown.
 *
 * robots object structure (example):
 *   { type: 'a2d', a2d: {...}, mock: {...} }
 *
 * Layout inside parentEl:
 *   ┌── type row (select)
 *   ├── [sub-group: a2d]   ← shown only when type === 'a2d'
 *   └── [sub-group: mock]  ← shown only when type === 'mock'
 */
function _buildRobotsGroup(obj, parentEl) {
  const TYPE_KEY = 'type';
  const currentType = String(obj[TYPE_KEY] ?? '');

  // Separate leaf keys from sub-group keys
  const leaves = [];        // [ [key, val], ... ]  — non-object entries (incl. type)
  const subGroups = [];     // [ [key, val], ... ]  — object entries (the robot types)

  for (const [k, v] of Object.entries(obj)) {
    const isGroup = v !== null && typeof v === 'object' && !Array.isArray(v);
    if (isGroup) {
      subGroups.push([k, v]);
    } else {
      leaves.push([k, v]);
    }
  }

  // ── 1. Render leaf rows (type + any other flat keys) ──────────────────
  // Put 'type' first
  const typeEntry = leaves.find(([k]) => k === TYPE_KEY);
  const otherLeaves = leaves.filter(([k]) => k !== TYPE_KEY);
  const orderedLeaves = typeEntry ? [typeEntry, ...otherLeaves] : otherLeaves;

  // Build a dedicated select for robots.type that drives visibility
  const knownTypes = subGroups.map(([k]) => k);

  let typeInput = null;
  for (const [k, v] of orderedLeaves) {
    const dotKey = `robots.${k}`;
    const row = document.createElement('div');
    row.className = 'cfg-row';
    row.dataset.key = dotKey;

    const keyEl = document.createElement('div');
    keyEl.className = 'cfg-key'; keyEl.title = dotKey; keyEl.textContent = k;

    const valEl = document.createElement('div');
    valEl.className = 'cfg-value';

    let input;
    if (k === TYPE_KEY && knownTypes.length > 0) {
      // Build select from known sub-group names
      input = document.createElement('select');
      knownTypes.forEach(opt => {
        const o = document.createElement('option');
        o.value = opt; o.textContent = opt;
        if (opt === currentType) o.selected = true;
        input.appendChild(o);
      });
      typeInput = input;
    } else {
      input = document.createElement('input');
      input.type = 'text'; input.value = v === null ? '' : String(v);
    }
    input.className = 'input-text';
    input.addEventListener('input',  () => onCfgChange(dotKey, input, v));
    input.addEventListener('change', () => onCfgChange(dotKey, input, v));
    valEl.appendChild(input);
    row.appendChild(keyEl); row.appendChild(valEl);
    parentEl.appendChild(row);
  }

  // ── 2. Render sub-groups with initial visibility ──────────────────────
  const subGroupEls = {};  // { typeName: groupEl }

  for (const [k, v] of subGroups) {
    const dotKey = `robots.${k}`;
    const body = document.createElement('div');
    body.className = 'cfg-group-body';
    buildTree(v, dotKey, body);
    const groupEl = buildGroupFromEl(k.toUpperCase(), body);
    groupEl.dataset.robotType = k;
    // Show only the group matching current type
    groupEl.style.display = (k === currentType) ? '' : 'none';
    subGroupEls[k] = groupEl;
    parentEl.appendChild(groupEl);
  }

  // ── 3. Wire type select → sub-group visibility ────────────────────────
  if (typeInput) {
    typeInput.addEventListener('change', () => {
      const selected = typeInput.value;
      for (const [k, el] of Object.entries(subGroupEls)) {
        el.style.display = (k === selected) ? '' : 'none';
      }
    });
  }
}

function buildGroup(label, rowEls) {
  const group  = document.createElement('div');
  group.className = 'cfg-group';
  const header = document.createElement('div');
  header.className = 'cfg-group-header';
  header.innerHTML = `<span class="cfg-group-toggle">▶</span><span>${label}</span>`;
  const body = document.createElement('div');
  body.className = 'cfg-group-body';
  body.style.display = 'none';
  rowEls.forEach(r => body.appendChild(r));
  header.addEventListener('click', () => {
    const open = header.classList.toggle('open');
    body.style.display = open ? '' : 'none';
  });
  group.appendChild(header);
  group.appendChild(body);
  return group;
}

function buildGroupFromEl(label, bodyEl) {
  const group  = document.createElement('div');
  group.className = 'cfg-group';
  const header = document.createElement('div');
  header.className = 'cfg-group-header';
  header.innerHTML = `<span class="cfg-group-toggle">▶</span><span>${label}</span>`;
  bodyEl.style.display = 'none';
  header.addEventListener('click', () => {
    const open = header.classList.toggle('open');
    bodyEl.style.display = open ? '' : 'none';
  });
  group.appendChild(header);
  group.appendChild(bodyEl);
  return group;
}

function createCfgRow(dotKey, label, value) {
  const row = document.createElement('div');
  row.className = 'cfg-row';
  row.dataset.key = dotKey;

  const keyEl = document.createElement('div');
  keyEl.className = 'cfg-key'; keyEl.title = dotKey; keyEl.textContent = label;

  const valEl = document.createElement('div');
  valEl.className = 'cfg-value';

  // Extract the bare key name (last segment) for option lookup
  const bareKey = dotKey.includes('.') ? dotKey.split('.').pop() : dotKey;

  let input;
  const multiSelectOptions = getCfgMultiSelectOptions(dotKey);
  if (multiSelectOptions) {
    input = document.createElement('select');
    input.multiple = true;
    input.size = Math.min(8, Math.max(2, multiSelectOptions.length));

    const selectedRaw = Array.isArray(value)
      ? value
      : (value == null ? [] : String(value).split(',').map(v => v.trim()).filter(Boolean));

    const selectedSet = new Set(
      selectedRaw.map(v => {
        if (dotKey === 'visual.trajectory.source') return String(v).trim().toLowerCase();
        return String(parseInt(v, 10));
      })
    );

    multiSelectOptions.forEach(opt => {
      const o = document.createElement('option');
      o.value = opt.value;
      o.textContent = opt.label;
      const key = dotKey === 'visual.trajectory.source'
        ? String(opt.value).toLowerCase()
        : String(parseInt(opt.value, 10));
      if (selectedSet.has(key)) o.selected = true;
      input.appendChild(o);
    });
  } else if (CONFIG_SELECT_OPTIONS[bareKey]) {
    // Predefined select options
    input = document.createElement('select');
    CONFIG_SELECT_OPTIONS[bareKey].forEach(opt => {
      const o = document.createElement('option');
      o.value = opt; o.textContent = opt;
      if (String(value) === String(opt)) o.selected = true;
      input.appendChild(o);
    });
  } else if (typeof value === 'boolean') {
    input = document.createElement('select');
    ['true', 'false'].forEach(opt => {
      const o = document.createElement('option');
      o.value = opt; o.textContent = opt;
      if (String(value) === opt) o.selected = true;
      input.appendChild(o);
    });
  } else if (Array.isArray(value)) {
    input = document.createElement('input');
    input.type = 'text'; input.value = JSON.stringify(value); input.title = 'JSON array';
  } else if (CONFIG_INT_KEYS.has(bareKey)) {
    input = document.createElement('input');
    input.type = 'number'; input.step = '1'; input.value = value === null ? '' : String(Math.round(Number(value)));
  } else {
    input = document.createElement('input');
    input.type = 'text'; input.value = value === null ? '' : String(value);
  }

  input.className = 'input-text';
  input.addEventListener('input',  () => onCfgChange(dotKey, input, value));
  input.addEventListener('change', () => onCfgChange(dotKey, input, value));
  valEl.appendChild(input);
  row.appendChild(keyEl);
  row.appendChild(valEl);
  return row;
}

function onCfgChange(dotKey, input, originalValue) {
  const bareKey = dotKey.includes('.') ? dotKey.split('.').pop() : dotKey;

  if (input.tagName === 'SELECT' && input.multiple) {
    const selected = Array.from(input.selectedOptions).map(o => o.value);
    let parsed = selected;

    if (dotKey === 'visual.trajectory.selected_joints') {
      parsed = selected.map(v => parseInt(v, 10)).filter(Number.isFinite);
    } else if (dotKey === 'visual.trajectory.source') {
      parsed = selected
        .map(v => String(v).trim().toLowerCase())
        .map(v => {
          if (v === 'state') return 'State';
          if (v === 'action' || v === 'actionfitted' || v === 'action_fitted') return 'ActionFitted';
          if (v === 'origin' || v === 'actionraw' || v === 'action_raw') return 'ActionRaw';
          return null;
        })
        .filter(Boolean);
    }

    input.style.borderColor = '';
    App.pendingPatch[dotKey] = parsed;
    markPending();
    return;
  }

  const raw = input.tagName === 'SELECT' ? input.value : input.value.trim();
  let parsed;
  if (typeof originalValue === 'boolean') {
    parsed = raw === 'true';
  } else if (CONFIG_INT_KEYS.has(bareKey)) {
    parsed = parseInt(raw, 10);
    if (isNaN(parsed)) { input.style.borderColor = 'var(--danger)'; return; }
  } else if (typeof originalValue === 'number') {
    parsed = Number(raw);
    if (isNaN(parsed)) { input.style.borderColor = 'var(--danger)'; return; }
  } else if (Array.isArray(originalValue)) {
    try { parsed = JSON.parse(raw); } catch { input.style.borderColor = 'var(--danger)'; return; }
  } else if (CONFIG_SELECT_OPTIONS[bareKey] && typeof CONFIG_SELECT_OPTIONS[bareKey][0] === 'number') {
    parsed = parseInt(raw, 10);
    if (isNaN(parsed)) { input.style.borderColor = 'var(--danger)'; return; }
  } else {
    parsed = raw;
  }
  input.style.borderColor = '';
  App.pendingPatch[dotKey] = parsed;
  markPending();
}

/** Mark pending changes: show badge + highlight Apply button */
function markPending() {
  $('pending-badge').classList.remove('hidden');
  const btn = $('btn-apply-config');
  if (btn) btn.classList.add('btn-primary');
}

/** Clear pending state: hide badge + restore Apply button to normal */
function clearPending() {
  $('pending-badge').classList.add('hidden');
  const btn = $('btn-apply-config');
  if (btn) btn.classList.remove('btn-primary');
}

/**
 * Create a real cfg-row for task_id or sub_task_id.
 * Both are real config fields that write to App.pendingPatch when changed.
 *   task_id  → string key into LangCmd.tasks (Task <select>)
 *   sub_task_id → integer index into the selected task's subtask array
 */
function createLangLinkRow(dotKey, label) {
  const row = document.createElement('div');
  row.className = 'cfg-row';
  row.dataset.key = dotKey;

  const keyEl = document.createElement('div');
  keyEl.className = 'cfg-key'; keyEl.title = dotKey; keyEl.textContent = label;

  const valEl = document.createElement('div');
  valEl.className = 'cfg-value';

  const sel = document.createElement('select');
  sel.className = 'input-text';
  // IDs: cfg-language-task / cfg-language-index
  sel.id = dotKey === 'language.task_id' ? 'cfg-language-task' : 'cfg-language-index';

  valEl.appendChild(sel);
  row.appendChild(keyEl);
  row.appendChild(valEl);

  if (dotKey === 'language.task_id') {
    sel.addEventListener('change', () => {
      const task = sel.value;
      // Rebuild sub_task_id options (display sync only, pendingPatch written on Apply)
      syncLangIndexOptions(task, 0);
      // Sync → Language Command panel Task select
      const taskSel = $('lang-task-select');
      if (taskSel && taskSel.value !== task) {
        taskSel.value = task;
        taskSel.dispatchEvent(new Event('change'));
      }
    });
  } else {
    // sub_task_id
    sel.addEventListener('change', () => {
      // Sync → Language Command panel Sub-task select (display sync only)
      const subtaskSel = $('lang-subtask-select');
      if (subtaskSel && subtaskSel.value !== sel.value) {
        subtaskSel.value = sel.value;
        subtaskSel.dispatchEvent(new Event('change'));
      }
    });
  }

  return row;
}

/** Populate the cfg-language-task select from current LangCmd.tasks.
 *  @param {string} [currentTask]  - task to pre-select (from App.config)
 *  @param {number} [currentIndex] - index to pre-select in sub_task_id (from App.config)
 */
function syncLangTaskOptions(currentTask, currentIndex) {
  const sel = $('cfg-language-task');
  if (!sel) return;
  const prev = currentTask !== undefined ? currentTask : sel.value;
  sel.innerHTML = '';
  Object.keys(LangCmd.tasks).forEach(name => {
    const o = document.createElement('option');
    o.value = name; o.textContent = name;
    sel.appendChild(o);
  });
  if (prev && LangCmd.tasks[prev]) sel.value = prev;
  else if (sel.options.length > 0) sel.selectedIndex = 0;
  syncLangIndexOptions(sel.value, currentIndex);
}

/** Populate the cfg-language-index select from the given task's sub-tasks.
 *  @param {string} taskName
 *  @param {number} [currentIndex] - index to pre-select
 */
function syncLangIndexOptions(taskName, currentIndex) {
  const sel = $('cfg-language-index');
  if (!sel) return;
  const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
  sel.innerHTML = '';
  subtasks.forEach((text, i) => {
    const o = document.createElement('option');
    o.value = i;
    o.textContent = `${i + 1}. ${text.substring(0, 60)}${text.length > 60 ? '…' : ''}`;
    o.title = text;
    sel.appendChild(o);
  });
  // Pre-select given index, or restore previous
  if (currentIndex !== undefined && !isNaN(currentIndex)) {
    sel.value = currentIndex;
  }
  if (!sel.value && sel.options.length > 0) sel.selectedIndex = 0;
}

function filterConfigTree(query) {
  const q = query.toLowerCase().trim();
  $('config-tree').querySelectorAll('.cfg-row').forEach(row => {
    row.style.display = (!q || row.dataset.key.toLowerCase().includes(q)) ? '' : 'none';
  });
  $('config-tree').querySelectorAll('.cfg-group').forEach(g => {
    // Robot type sub-groups (data-robot-type) are controlled exclusively by the
    // type select in _buildRobotsGroup; never let the filter override their visibility.
    if (g.dataset.robotType) return;
    if (!q) { g.style.display = ''; return; }
    const body = g.querySelector('.cfg-group-body');
    if (!body) return;
    g.style.display = [...body.querySelectorAll('.cfg-row')].some(r => r.style.display !== 'none') ? '' : 'none';
  });
}

// ═══════════════════════════════════════════════════════
//  Language Command Panel
//  Two-level hierarchy loaded from a JSON file via file picker.
//  JSON format: { "TaskA": ["sub1","sub2",...], "TaskB": [...] }
//  Tasks → <select> level-1; Sub-tasks → <select> level-2 (ordered Array)
// ═══════════════════════════════════════════════════════
const LangCmd = {
  tasks: {},        // { taskName: [instruction0, instruction1, ...] }  — ordered array
};

function buildLangTasksFromData(data) {
  LangCmd.tasks = {};
  if (!data || typeof data !== 'object') return;

  if (Array.isArray(data)) {
    // Flat array → single "Default" task
    LangCmd.tasks['Default'] = data.filter(x => typeof x === 'string');
  } else {
    for (const [taskName, subtasks] of Object.entries(data)) {
      if (Array.isArray(subtasks)) {
        LangCmd.tasks[taskName] = subtasks.filter(x => typeof x === 'string');
      }
    }
  }
}

function renderLangTaskSelect() {
  const taskSel    = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  if (!taskSel) return;

  const prevTask = taskSel.value;
  taskSel.innerHTML = '';

  Object.keys(LangCmd.tasks).forEach(taskName => {
    const opt = document.createElement('option');
    opt.value = taskName;
    opt.textContent = taskName;
    taskSel.appendChild(opt);
  });

  // Restore or select first
  if (prevTask && LangCmd.tasks[prevTask]) taskSel.value = prevTask;
  if (!taskSel.value && taskSel.options.length > 0) taskSel.selectedIndex = 0;

  renderLangSubtaskSelect();
  // Sync Config panel: use App.config values if available, otherwise current selection
  const cfgTask  = (App.config && App.config.language && App.config.language.task_id) || taskSel.value;
  const cfgIndex = (App.config && App.config.language && App.config.language.sub_task_id != null) ? App.config.language.sub_task_id : undefined;
  syncLangTaskOptions(cfgTask, cfgIndex);
}

function renderLangSubtaskSelect() {
  const taskSel    = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  if (!subtaskSel) return;

  subtaskSel.innerHTML = '';
  const taskName = taskSel ? taskSel.value : null;
  const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];

  subtasks.forEach((text, i) => {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = `${i + 1}. ${text.substring(0, 50)}${text.length > 50 ? '…' : ''}`;
    opt.title = text;
    subtaskSel.appendChild(opt);
  });
  // Sync Config panel sub_task_id options (preserve current selection)
  syncLangIndexOptions(taskName);
}

// Keep old renderLangPresets as compatibility alias (called on config load)
function renderLangPresets(presets) {
  App.langPresets = presets || [];
  // config.language (flat array) → put into LangCmd only if no JSON loaded yet
  if (Object.keys(LangCmd.tasks).length === 0) {
    buildLangTasksFromData(presets);
    renderLangTaskSelect();
  }
}

function setupLangPanel() {
  const taskSel = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  const autoChk = $('chk-lang-auto-mode');
  const thresholdInput = $('inp-lang-threshold');
  let thresholdSaveTimer = null;

  const setThresholdEditable = (enabled) => {
    if (!thresholdInput) return;
    thresholdInput.disabled = !enabled;
  };

  const getConfigSavePath = () => {
    const display = $('conf-path-display');
    return (display && display.dataset.fullPath) || (display && display.textContent.trim()) || '';
  };

  const persistLanguagePatch = async (patch) => {
    if (!App.config || typeof App.config !== 'object') App.config = {};
    if (!App.config.language || typeof App.config.language !== 'object') App.config.language = {};

    Object.entries(patch).forEach(([dotKey, value]) => {
      App.pendingPatch[dotKey] = value;
      if (dotKey.startsWith('language.')) {
        const key = dotKey.slice('language.'.length);
        App.config.language[key] = value;
      }
    });
    markPending();

    try {
      const res = await apiFetch('/api/config/patch', {
        method: 'POST',
        body: JSON.stringify({ patch }),
      });
      App.config = res.config || App.config;

      Object.keys(patch).forEach((dotKey) => delete App.pendingPatch[dotKey]);
      if (!Object.keys(App.pendingPatch).length) clearPending();

      const path = getConfigSavePath();
      if (path) {
        await apiFetch('/api/config/save_file', {
          method: 'POST',
          body: JSON.stringify({ path }),
        });
      }
      return true;
    } catch (_) {
      Object.entries(patch).forEach(([dotKey, value]) => {
        App.pendingPatch[dotKey] = value;
      });
      markPending();
      return false;
    }
  };

  const commitThreshold = async () => {
    if (!thresholdInput || thresholdInput.disabled) return;
    const raw = thresholdInput.value.trim();
    const value = Number(raw);
    if (!Number.isFinite(value)) {
      thresholdInput.style.borderColor = 'var(--danger)';
      return;
    }
    thresholdInput.style.borderColor = '';
    await persistLanguagePatch({ 'language.task_progress_threshold': value });
  };

  // Task select → rebuild subtask list + sync Config panel selects only (no pendingPatch yet)
  if (taskSel) {
    taskSel.addEventListener('change', () => {
      renderLangSubtaskSelect();
      App.langAuto.lastProgress = null;
      const cfgTaskSel = $('cfg-language-task');
      if (cfgTaskSel && cfgTaskSel.value !== taskSel.value) {
        cfgTaskSel.value = taskSel.value;
        syncLangIndexOptions(taskSel.value, 0);
      }
    });
  }

  // Subtask select → fill textarea + sync Config panel selects only (no pendingPatch yet)
  if (subtaskSel) {
    subtaskSel.addEventListener('change', () => {
      const taskName = taskSel ? taskSel.value : null;
      const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
      const idx = parseInt(subtaskSel.value, 10);
      if (!isNaN(idx) && subtasks[idx] !== undefined) {
        $('lang-cmd-text').value = subtasks[idx];
      }
      const cfgIdxSel = $('cfg-language-index');
      if (cfgIdxSel && cfgIdxSel.value !== subtaskSel.value) {
        cfgIdxSel.value = subtaskSel.value;
      }
    });
  }

  if (autoChk) {
    autoChk.addEventListener('change', async () => {
      App.langAuto.lastProgress = null;
      const enabled = !!autoChk.checked;
      setThresholdEditable(enabled);
      await persistLanguagePatch({ 'language.auto_mode': enabled });
    });
  }

  if (thresholdInput) {
    thresholdInput.addEventListener('input', () => {
      const value = Number(thresholdInput.value.trim());
      thresholdInput.style.borderColor = Number.isFinite(value) ? '' : 'var(--danger)';
      if (thresholdInput.disabled || !Number.isFinite(value)) return;
      if (thresholdSaveTimer) clearTimeout(thresholdSaveTimer);
      thresholdSaveTimer = setTimeout(() => {
        thresholdSaveTimer = null;
        commitThreshold();
      }, 300);
    });

    thresholdInput.addEventListener('change', async () => {
      if (thresholdSaveTimer) {
        clearTimeout(thresholdSaveTimer);
        thresholdSaveTimer = null;
      }
      await commitThreshold();
    });

    thresholdInput.addEventListener('keydown', async (e) => {
      if (e.key !== 'Enter') return;
      if (thresholdSaveTimer) {
        clearTimeout(thresholdSaveTimer);
        thresholdSaveTimer = null;
      }
      await commitThreshold();
    });
  }

  setThresholdEditable(!!(autoChk && autoChk.checked));
}

// ═══════════════════════════════════════════════════════
//  Config load
// ═══════════════════════════════════════════════════════

// Conf directory path (absolute), fetched once from server
let CONF_DIR = 'conf';

async function initConfDir() {
  try {
    const res = await apiFetch('/api/conf_dir');
    if (res.path) CONF_DIR = res.path;
  } catch (_) { /* fallback to 'conf' */ }
}

function _toBool(v, fallback) {
  return typeof v === 'boolean' ? v : fallback;
}

function _toInt(v, fallback, min = null) {
  const n = parseInt(v, 10);
  if (!Number.isFinite(n)) return fallback;
  if (min != null && n < min) return min;
  return n;
}

function normalizeTrajWindowSpanSec(rawSpanSec, fallback = TRAJ_WINDOW_SPAN_SEC) {
  const fallbackVal = Number(fallback);
  const fallbackSafe = Number.isFinite(fallbackVal) && fallbackVal > 0
    ? Math.min(fallbackVal, TRAJ_WINDOW_SPAN_SEC_MAX)
    : 2.25;
  const span = Number(rawSpanSec);
  if (!Number.isFinite(span) || span <= 0) return fallbackSafe;
  return Math.min(span, TRAJ_WINDOW_SPAN_SEC_MAX);
}

function trimTrajBufferToMaxWindow(bufferKey, latestX) {
  const t = App.traj;
  const buf = t.buffer[bufferKey];
  if (!buf || buf.length === 0 || !Number.isFinite(latestX)) return;

  const cutoff = latestX - TRAJ_WINDOW_SPAN_SEC_MAX;
  while (buf.length > 0 && Number.isFinite(buf[0].x) && buf[0].x < cutoff) {
    buf.shift();
  }
  if (buf.length > TRAJ_BUFFER_HARD_MAX_POINTS) {
    buf.splice(0, buf.length - TRAJ_BUFFER_HARD_MAX_POINTS);
  }
}

function syncTrajWindowSpanUI() {
  const span = normalizeTrajWindowSpanSec(App.traj.windowSpanSec, TRAJ_WINDOW_SPAN_SEC);
  const uiValue = Math.round(span);
  const slider = $('traj-window-span-slider');
  const value = $('traj-window-span-value');
  if (slider) {
    slider.min = '1';
    slider.max = String(TRAJ_WINDOW_SPAN_SEC_MAX);
    slider.step = '1';
    slider.value = String(uiValue);
  }
  if (value) value.textContent = `${uiValue}s`;
}

function applyVisualConfig(cfg = App.config) {
  const visualCfg = (cfg && typeof cfg === 'object') ? (cfg.visual || {}) : {};

  const camCfg = (visualCfg.camera && typeof visualCfg.camera === 'object') ? visualCfg.camera : {};
  const trajCfg = (visualCfg.trajectory && typeof visualCfg.trajectory === 'object') ? visualCfg.trajectory : {};

  camState.updateInterval = _toInt(camCfg.update_interval_ms, camState.updateInterval || 33, 16);
  restartCameraUpdateTimer();

  const hasNamedCamOpen = ['open_head', 'open_wrist_left', 'open_wrist_right'].some(k => k in camCfg);
  const camOpenCfg = hasNamedCamOpen
    ? [camCfg.open_head, camCfg.open_wrist_left, camCfg.open_wrist_right]
    : (Array.isArray(camCfg.default_open) ? camCfg.default_open : App.camOpen);
  const nextCamOpen = [0, 1, 2].map(i => !!camOpenCfg[i]);
  for (let i = 0; i < 3; i++) {
    if (App.camOpen[i] !== nextCamOpen[i]) toggleCamera(i);
  }
  const camAllBtn = $('btn-cam-all-toggle');
  if (camAllBtn) {
    const allOn = App.camOpen.every(v => v);
    camAllBtn.textContent = allOn ? '⏸ Close All' : '▶ Open All';
    camAllBtn.className = allOn ? 'btn btn-xs btn-danger' : 'btn btn-xs btn-success';
  }

  if (typeof trajCfg.play === 'boolean') {
    App.traj.paused = !trajCfg.play;
  } else {
    App.traj.paused = _toBool(trajCfg.default_paused, App.traj.paused);
  }
  App.traj.updateIntervalMs = _toInt(trajCfg.update_interval_ms, App.traj.updateIntervalMs || DEFAULT_TRAJ_UPDATE_MS, 16);
  const cfgWindowSpanSec = Number(trajCfg.window_span_sec ?? trajCfg.window_sec ?? trajCfg.window_seconds);
  App.traj.windowSpanSec = normalizeTrajWindowSpanSec(cfgWindowSpanSec, App.traj.windowSpanSec);
  syncTrajWindowSpanUI();

  const sourceCfgRaw = Array.isArray(trajCfg.source)
    ? trajCfg.source
    : (Array.isArray(trajCfg.default_source) ? trajCfg.default_source : null);
  if (Array.isArray(sourceCfgRaw)) {
    const source = new Set();
    sourceCfgRaw.forEach(k => {
      const key = String(k).trim().toLowerCase();
      if (key === 'state') source.add('state');
      else if (key === 'action' || key === 'actionfitted' || key === 'action_fitted') source.add('action_fitted');
      else if (key === 'origin' || key === 'actionraw' || key === 'action_raw') source.add('action_raw');
    });
    App.traj.source = source;
  }

  const selectedJointsRaw = trajCfg.selected_joints ?? trajCfg.default_selected_joints;
  let jointTokens = [];
  if (Array.isArray(selectedJointsRaw)) {
    jointTokens = selectedJointsRaw;
  } else if (typeof selectedJointsRaw === 'string') {
    jointTokens = selectedJointsRaw.split(',').map(v => v.trim()).filter(Boolean);
  }
  if (jointTokens.length > 0) {
    const joints = jointTokens
      .map(v => {
        if (typeof v === 'number') return v;
        const s = String(v).trim();
        if (/^[LR]\d+$/i.test(s)) return parseInt(s.slice(1), 10) + (s[0].toUpperCase() === 'R' ? 7 : 0);
        return parseInt(s, 10);
      })
      .filter(v => Number.isFinite(v) && v >= 0 && v < TRAJ_JOINT_COUNT);
    if (joints.length > 0) App.traj.selectedJoints = new Set(joints);
  }

  document.querySelectorAll('.joint-sel-chip').forEach(chip => {
    const idx = parseInt(chip.dataset.idx, 10);
    const active = App.traj.selectedJoints.has(idx);
    chip.classList.toggle('active', active);
    _applyChipColor(chip, active, JOINT_COLORS[idx]);
  });

  const chkState = $('chk-traj-state');
  const chkActionFitted = $('chk-traj-action-fitted');
  const chkActionRaw = $('chk-traj-action-raw');
  const btnAllSource = $('btn-traj-all');
  const btnPlay = $('btn-traj-pause');
  if (chkState) chkState.checked = App.traj.source.has('state');
  if (chkActionFitted) chkActionFitted.checked = App.traj.source.has('action_fitted');
  if (chkActionRaw) chkActionRaw.checked = App.traj.source.has('action_raw');
  if (btnAllSource) {
    const allSelected = App.traj.source.has('state') && App.traj.source.has('action_fitted') && App.traj.source.has('action_raw');
    btnAllSource.className = 'btn btn-xs' + (allSelected ? ' btn-active' : '');
    btnAllSource.textContent = allSelected ? 'None' : 'All';
  }
  if (btnPlay) {
    btnPlay.innerHTML = App.traj.paused
      ? '<span class="btn-icon">▶</span> Play'
      : '<span class="btn-icon">⏸</span> Pause';
    btnPlay.className = 'btn btn-xs' + (App.traj.paused ? ' btn-active' : '');
  }

  startTrajUpdateTimer();
  App.traj.dirty = true;
  refreshUnifiedChart();

  if (App.isRunning) {
    connectCamWS();
    syncRuntimeCameraConfig();
  }
}

function getVisualStatePatch() {
  return {
    'visual.camera.open_head': !!App.camOpen[0],
    'visual.camera.open_wrist_left': !!App.camOpen[1],
    'visual.camera.open_wrist_right': !!App.camOpen[2],
    'visual.trajectory.play': !App.traj.paused,
    'visual.trajectory.source': [...App.traj.source].map(s => {
      if (s === 'action_fitted') return 'ActionFitted';
      if (s === 'action_raw') return 'ActionRaw';
      return 'State';
    }),
    'visual.trajectory.selected_joints': [...App.traj.selectedJoints].sort((a, b) => a - b),
    'visual.trajectory.window_span_sec': normalizeTrajWindowSpanSec(App.traj.windowSpanSec, TRAJ_WINDOW_SPAN_SEC),
  };
}

function syncVisualStateToLocalConfig(patch) {
  if (!App.config || typeof App.config !== 'object') App.config = {};
  if (!App.config.visual || typeof App.config.visual !== 'object') App.config.visual = {};
  if (!App.config.visual.camera || typeof App.config.visual.camera !== 'object') App.config.visual.camera = {};
  if (!App.config.visual.trajectory || typeof App.config.visual.trajectory !== 'object') App.config.visual.trajectory = {};

  App.config.visual.camera.open_head = patch['visual.camera.open_head'];
  App.config.visual.camera.open_wrist_left = patch['visual.camera.open_wrist_left'];
  App.config.visual.camera.open_wrist_right = patch['visual.camera.open_wrist_right'];
  App.config.visual.trajectory.play = patch['visual.trajectory.play'];
  delete App.config.visual.trajectory.default_paused;
  App.config.visual.trajectory.source = patch['visual.trajectory.source'];
  App.config.visual.trajectory.selected_joints = patch['visual.trajectory.selected_joints'];
  App.config.visual.trajectory.window_span_sec = patch['visual.trajectory.window_span_sec'];
}

function syncVisualStateToConfigInputs(patch) {
  const setVal = (dotKey, value) => {
    const row = document.querySelector(`.cfg-row[data-key="${dotKey}"]`);
    if (!row) return;
    const input = row.querySelector('input, select');
    if (!input) return;

    if (input.tagName === 'SELECT' && input.multiple) {
      const selectedSet = new Set((Array.isArray(value) ? value : [value]).map(v => String(v)));
      Array.from(input.options).forEach(opt => {
        const k = dotKey === 'visual.trajectory.source'
          ? String(opt.value).toLowerCase()
          : String(opt.value);
        const vv = dotKey === 'visual.trajectory.source'
          ? new Set([...selectedSet].map(x => x.toLowerCase()))
          : selectedSet;
        opt.selected = vv.has(k);
      });
      return;
    }

    if (input.tagName === 'SELECT') {
      input.value = String(value);
      return;
    }

    if (Array.isArray(value)) input.value = JSON.stringify(value);
    else input.value = value == null ? '' : String(value);
  };

  Object.entries(patch).forEach(([k, v]) => setVal(k, v));
}

async function persistVisualStateNow() {
  const patch = getVisualStatePatch();
  syncVisualStateToLocalConfig(patch);
  syncVisualStateToConfigInputs(patch);

  // Visual panel changes are auto-applied; never show "unsaved changes" for them.
  Object.keys(App.pendingPatch)
    .filter(k => k.startsWith('visual.camera.') || k.startsWith('visual.trajectory.'))
    .forEach(k => delete App.pendingPatch[k]);
  if (!Object.keys(App.pendingPatch).length) clearPending();

  if (App.isRunning) {
    try {
      await apiFetch('/api/visual/camera_cfg', {
        method: 'POST',
        body: JSON.stringify({
          open_head: patch['visual.camera.open_head'],
          open_wrist_left: patch['visual.camera.open_wrist_left'],
          open_wrist_right: patch['visual.camera.open_wrist_right'],
        }),
      });
    } catch (_) {
      // no-op: keep local UI effective
    }
    return;
  }

  if (_visualPersistInFlight) return;

  _visualPersistInFlight = true;
  try {
    const res = await apiFetch('/api/config/patch', {
      method: 'POST',
      body: JSON.stringify({ patch }),
    });
    App.config = res.config || App.config;

    const display = $('conf-path-display');
    const path = (display && display.dataset.fullPath) || (display && display.textContent.trim()) || '';
    if (path) {
      await apiFetch('/api/config/save_file', { method: 'POST', body: JSON.stringify({ path }) });
    }
  } catch (_) {
    // no-op: visual state already effective in UI
  } finally {
    _visualPersistInFlight = false;
  }
}

function schedulePersistVisualState(delay = 120) {
  if (_visualPersistTimer) clearTimeout(_visualPersistTimer);
  _visualPersistTimer = setTimeout(() => {
    _visualPersistTimer = null;
    persistVisualStateNow();
  }, delay);
}

async function loadConfigFromServer() {
  try {
    const res = await apiFetch('/api/config');
    App.config = res.config || {};
    App.pendingPatch = {};
    clearPending();
    renderConfigTree(App.config);
    applyVisualConfig(App.config);
    // Apply language-related UI state from config (task/sub-task/auto/threshold)
    applyLangConfigSelection();
    // Set default path display on startup
    const display = $('conf-path-display');
    if (display && !display.dataset.fullPath) {
      const defaultRel = 'conf/default_conf.yaml';
      const defaultFull = CONF_DIR.replace(/\/conf$/, '') + '/' + defaultRel;
      display.textContent = defaultRel;
      display.title = defaultFull;
      display.dataset.fullPath = defaultFull;
    }
    toast('Config loaded.', 'ok', 2000);
  } catch (e) { /* already toasted */ }
}

/** Load language command JSON from App.config.language.file_path (fallback to default endpoint). */
async function loadDefaultLangFile() {
  try {
    const langPath = App.config && App.config.language && App.config.language.file_path;
    let res;
    if (langPath) {
      res = await apiFetch('/api/lang_file/load', { method: 'POST', body: JSON.stringify({ path: langPath }) });
    } else {
      res = await apiFetch('/api/default_lang_file');
      if (!App.config || typeof App.config !== 'object') App.config = {};
      if (!App.config.language || typeof App.config.language !== 'object') App.config.language = {};
      if (res.path) App.config.language.file_path = res.path;
    }

    if (res.data) {
      buildLangTasksFromData(res.data);
      renderLangTaskSelect();
      // Apply task_id / sub_task_id from current config
      applyLangConfigSelection();
    }
  } catch (_) { /* non-fatal: lang panel stays empty */ }
}

/**
 * After lang data is loaded (or config reloaded), synchronize the Language Command panel
 * and Config panel selects to reflect App.config.task_id / sub_task_id.
 * Also fills lang-cmd-text with the corresponding instruction.
 */
function applyLangConfigSelection() {
  const task = App.config && App.config.language && App.config.language.task_id;
  const index = (App.config && App.config.language && App.config.language.sub_task_id != null) ? App.config.language.sub_task_id : 0;
  const autoModeRaw = App.config && App.config.language && App.config.language.auto_mode;
  const autoMode = (autoModeRaw === true || autoModeRaw === 'true' || autoModeRaw === 1 || autoModeRaw === '1');
  const thresholdRaw = App.config && App.config.language && App.config.language.task_progress_threshold;
  const threshold = Number(thresholdRaw);

  const autoChk = $('chk-lang-auto-mode');
  if (autoChk) autoChk.checked = autoMode;

  const thresholdInput = $('inp-lang-threshold');
  if (thresholdInput) {
    const fallback = Number(thresholdInput.value);
    const displayThreshold = Number.isFinite(threshold)
      ? threshold
      : (Number.isFinite(fallback) ? fallback : 0.95);
    thresholdInput.value = String(displayThreshold);
    thresholdInput.disabled = !(autoChk ? !!autoChk.checked : autoMode);
    thresholdInput.style.borderColor = '';
  }

  // Sync Lang Panel Task select
  const taskSel = $('lang-task-select');
  if (taskSel && task && LangCmd.tasks[task]) {
    taskSel.value = task;
  }

  // Rebuild subtask list for the selected task
  renderLangSubtaskSelect();

  // Sync Lang Panel Sub-task select
  const subtaskSel = $('lang-subtask-select');
  if (subtaskSel) {
    subtaskSel.value = index;
    const taskName = taskSel ? taskSel.value : null;
    const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
    if (subtasks[index] !== undefined) {
      $('lang-cmd-text').value = subtasks[index];
    }
  }

  // Sync Config panel selects
  syncLangTaskOptions(task, index);
}

// ═══════════════════════════════════════════════════════
//  Camera Visual
//  Mirrors visual/app.js:
//    - Receives binary WebSocket frames: camera_data_binary
//    - Decodes JPEG via Blob + createObjectURL (no canvas needed)
//    - 33ms update timer (30FPS throttle)
//    - Falls back to MJPEG img.src if no WS binary frames arrive
// ═══════════════════════════════════════════════════════

// Camera metadata: index → display name
const CAM_NAMES = ['Head', 'Wrist-Left', 'Wrist-Right'];

// Per-camera runtime state (mirrors visual/ latestCameraData pattern)
const camState = {
  // latest pending binary frame per camera index
  pendingData: {},      // { 0: Uint8Array, 1: Uint8Array, 2: Uint8Array }
  pendingUpdate: false,
  lastUpdateTime: 0,
  updateInterval: 33,
  updateTimer: null,
};

function restartCameraUpdateTimer() {
  if (camState.updateTimer) clearInterval(camState.updateTimer);
  camState.updateTimer = setInterval(() => {
    if (!camState.pendingUpdate) return;
    const now = Date.now();
    if (now - camState.lastUpdateTime < camState.updateInterval) return;

    Object.keys(camState.pendingData).forEach(idx => {
      const i = Number(idx);
      if (!App.camOpen[i]) return;
      updateCameraDisplay(i, camState.pendingData[i]);
    });

    camState.pendingUpdate = false;
    camState.lastUpdateTime = now;
  }, camState.updateInterval);
}

/** Recalculate and apply grid-template-columns based on current collapsed state. */
function updateLayoutColumns() {
  const leftCollapsed = $('left-col').classList.contains('collapsed');
  const visualCollapsed = $('panel-visual').classList.contains('collapsed');
  const left  = leftCollapsed ? '0px'   : '280px';
  const right = visualCollapsed ? '0px' : '300px';
  // When a column is 0, also suppress the gap on that side by adjusting padding
  const layout = document.querySelector('.layout');
  layout.style.gridTemplateColumns = `${left} 1fr ${right}`;
  // Suppress padding on collapsed sides so no whitespace strip remains
  const gap = getComputedStyle(document.documentElement).getPropertyValue('--panel-gap').trim();
  layout.style.paddingLeft   = leftCollapsed ? '0' : gap;
  layout.style.paddingRight  = visualCollapsed ? '0' : gap;
}

function setupCameraPanel() {
  // Collapse / expand the whole camera panel
  $('btn-visual-collapse').addEventListener('click', () => {
    const panel = $('panel-visual');
    const collapsed = panel.classList.toggle('collapsed');
    $('btn-visual-reveal').classList.toggle('hidden', !collapsed);
    updateLayoutColumns();
  });
  $('btn-visual-reveal').addEventListener('click', () => {
    $('panel-visual').classList.remove('collapsed');
    $('btn-visual-reveal').classList.add('hidden');
    updateLayoutColumns();
  });

  // Individual open/close buttons
  for (let i = 0; i < 3; i++) {
    $(`btn-cam-${i}`).addEventListener('click', () => {
      toggleCamera(i);
      updateAllToggleBtn();
      schedulePersistVisualState();
    });
  }

  // All toggle: Open All (all closed) ↔ Close All (all open)
  function updateAllToggleBtn() {
    const allOn = App.camOpen.every(v => v);
    const btn = $('btn-cam-all-toggle');
    if (allOn) {
      btn.textContent = '⏸ Close All';
      btn.className = 'btn btn-xs btn-danger';
    } else {
      btn.textContent = '▶ Open All';
      btn.className = 'btn btn-xs btn-success';
    }
  }
  $('btn-cam-all-toggle').addEventListener('click', () => {
    const allOn = App.camOpen.every(v => v);
    for (let i = 0; i < 3; i++) {
      if (allOn && App.camOpen[i]) toggleCamera(i);
      else if (!allOn && !App.camOpen[i]) toggleCamera(i);
    }
    updateAllToggleBtn();
    schedulePersistVisualState();
  });

  restartCameraUpdateTimer();

  // Apply initial closed state to all cameras
  for (let i = 0; i < 3; i++) _applyCameraClosedState(i);

  // Sync initial state of All toggle button
  updateAllToggleBtn();
}

/* Called from handleWSMessage when a binary camera frame arrives */
function handleCameraFrame(cameraId, imageBytes) {
  // imageBytes: Uint8Array JPEG data
  camState.pendingData[cameraId] = imageBytes;
  camState.pendingUpdate = true;
}

/* Render JPEG bytes to <img> via Blob URL — mirrors visual/app.js updateCameraDisplay */
function updateCameraDisplay(idx, imageBytes) {
  const imgEl = $(`cam-img-${idx}`);
  const phEl  = $(`cam-placeholder-${idx}`);
  if (!imgEl) return;

  const blob    = new Blob([imageBytes], { type: 'image/jpeg' });
  const blobUrl = URL.createObjectURL(blob);

  const tmp = new Image();
  tmp.onload = () => {
    // Release previous blob URL
    if (imgEl.src && imgEl.src.startsWith('blob:')) URL.revokeObjectURL(imgEl.src);
    imgEl.src = blobUrl;
    imgEl.classList.add('loaded');
    if (phEl) phEl.style.display = 'none';
    // Mark status ON
    const statusEl = $(`cam-status-${idx}`);
    if (statusEl) {
      statusEl.textContent = 'ON';
      statusEl.classList.add('active');
      statusEl.classList.remove('error');
    }
  };
  tmp.onerror = () => URL.revokeObjectURL(blobUrl);
  tmp.src = blobUrl;
}

/** Apply the visual closed state for camera idx (no toggle, just sets DOM to closed). */
function _applyCameraClosedState(idx) {
  const preview  = $(`cam-preview-${idx}`);
  const statusEl = $(`cam-status-${idx}`);
  const btnEl    = $(`btn-cam-${idx}`);
  const phEl     = $(`cam-placeholder-${idx}`);
  if (preview)  preview.classList.add('closed');
  if (statusEl) { statusEl.textContent = 'OFF'; statusEl.classList.remove('active', 'error'); }
  if (btnEl)    btnEl.textContent = 'Open';
  if (phEl)     phEl.style.display = 'none';
  // cam-row (title + button) always visible
}

function toggleCamera(idx) {
  App.camOpen[idx] = !App.camOpen[idx];
  const preview  = $(`cam-preview-${idx}`);
  const statusEl = $(`cam-status-${idx}`);
  const btnEl    = $(`btn-cam-${idx}`);
  const imgEl    = $(`cam-img-${idx}`);
  const phEl     = $(`cam-placeholder-${idx}`);

  if (App.camOpen[idx]) {
    // Open: remove dim overlay, resume receiving frames
    preview.classList.remove('closed');
    statusEl.textContent = 'ON';
    statusEl.classList.add('active');
    statusEl.classList.remove('error');
    btnEl.textContent = 'Close';
    // Show placeholder only if no stream yet
    const hasStream = imgEl && imgEl.classList.contains('loaded');
    if (!hasStream) {
      if (phEl) { phEl.style.display = ''; phEl.textContent = 'Waiting for stream…'; }
    }
    // Render immediately if frame is cached
    if (camState.pendingData[idx]) {
      updateCameraDisplay(idx, camState.pendingData[idx]);
    }
  } else {
    // Close: add dim overlay, stop rendering — but keep preview box visible
    preview.classList.add('closed');
    statusEl.textContent = 'OFF';
    statusEl.classList.remove('active', 'error');
    btnEl.textContent = 'Open';
    // Hide the "Waiting" placeholder (the CLOSED overlay takes over)
    if (phEl) phEl.style.display = 'none';
    // cam-row (title + button) always visible
  }
}

function getRecordingSaveItems() {
  const items = [];
  if ($('chk-record-episode')?.checked) items.push('Episode');
  if ($('chk-record-expdata')?.checked) items.push('ExpData');
  return items;
}

function renderRecordingFileList(data) {
  const listEl = $('recording-file-list');
  const baseEl = $('recording-base-dir');
  if (!listEl) return;

  const files = Array.isArray(data?.files) ? data.files : [];
  if (baseEl) baseEl.textContent = data?.base_dir || '';

  if (!files.length) {
    listEl.innerHTML = '<div class="recording-file-item empty">(empty)</div>';
    return;
  }

  const top = files.slice(0, 200);
  listEl.innerHTML = top
    .map(item => {
      const name = typeof item === 'string' ? item : (item.path || item.name || '');
      const safe = String(name)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;');
      return `<div class="recording-file-item" title="${safe}">${safe}</div>`;
    })
    .join('');
}

async function refreshRecordingFileList() {
  try {
    const res = await apiFetch('/api/recording/files');
    renderRecordingFileList(res);
  } catch (_) { /* toasted */ }
}

function setupRecordingPanel() {
  const body = $('recording-body');
  const btn = $('btn-recording-collapse');
  if (body && btn) {
    btn.textContent = body.classList.contains('collapsed') ? '▲' : '▼';
    btn.addEventListener('click', () => {
      const collapsed = body.classList.toggle('collapsed');
      btn.textContent = collapsed ? '▲' : '▼';
      if (!collapsed) refreshRecordingFileList();
    });
  }

  $('btn-recording-start')?.addEventListener('click', async () => {
    const saveItems = getRecordingSaveItems();
    await sendCommand('record', { enable: true, save_items: saveItems });
    toast('Recording started.', 'ok');
  });

  $('btn-recording-stop')?.addEventListener('click', async () => {
    const saveItems = getRecordingSaveItems();
    await sendCommand('record', { enable: false, save_items: saveItems });
    toast('Recording stopped.', 'warn');
    await refreshRecordingFileList();
  });

  refreshRecordingFileList();
  if (App.recordingListTimer) clearInterval(App.recordingListTimer);
  App.recordingListTimer = setInterval(refreshRecordingFileList, 5000);
}

// ═══════════════════════════════════════════════════════
//  Joint Trajectory — Chart.js implementation
//  Single unified chart: all selected joints on one canvas.
//  State series = dashed line; Action series = solid line.
//  Each joint has its own colour from JOINT_COLORS palette.
//  Zoom/pan via chartjs-plugin-zoom.
// ═══════════════════════════════════════════════════════

// Fixed joint labels for trajectory selector: L0-L6 (idx 0-6), R0-R6 (idx 7-13)
const TRAJ_JOINT_LABELS = [
  'L0','L1','L2','L3','L4','L5','L6',
  'R0','R1','R2','R3','R4','R5','R6',
];
const TRAJ_JOINT_COUNT = TRAJ_JOINT_LABELS.length;  // 14

/* ── Create the single unified Chart.js instance ── */
function createUnifiedChart() {
  const t = App.traj;
  if (t.chart) return;
  const canvas = $('traj-canvas');
  if (!canvas) return;
  t.chart = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: { datasets: [] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      parsing: false,
      scales: {
        x: {
          type: 'linear',
          title: { display: false },
          ticks: { maxTicksLimit: 8, color: '#656d76', font: { size: 9 } },
          grid: { color: 'rgba(208,215,222,.5)' },
        },
        y: {
          title: { display: true, text: 'rad', color: '#656d76', font: { size: 9 } },
          ticks: { maxTicksLimit: 6, color: '#656d76', font: { size: 9 } },
          grid: { color: 'rgba(208,215,222,.5)' },
        },
      },
      plugins: {
        legend: {
          display: true,
          position: 'right',
          labels: {
            usePointStyle: true,
            pointStyle: 'line',
            padding: 8,
            font: { size: 9 },
            color: '#1f2328',
            boxWidth: 20,
            generateLabels(chart) {
              const labels = Chart.defaults.plugins.legend.labels.generateLabels(chart);
              return labels.map(item => {
                const ds = chart.data.datasets[item.datasetIndex] || {};
                item.pointStyle = 'line';
                item.lineWidth = Number(ds.borderWidth) || 1.5;
                item.lineDash = Array.isArray(ds.borderDash) ? ds.borderDash : [];
                item.lineDashOffset = Number(ds.borderDashOffset) || 0;
                return item;
              });
            },
          },
        },
        tooltip: {
          mode: 'index', intersect: false,
          backgroundColor: 'rgba(31,35,40,.9)',
          titleColor: '#fff', bodyColor: '#fff',
          borderColor: '#0969da', borderWidth: 1,
        },
        zoom: {
          pan:  { enabled: true, mode: 'xy', modifierKey: 'shift' },
          zoom: {
            wheel:  { enabled: true, modifierKey: 'ctrl' },
            pinch:  { enabled: true },
            drag:   {
              enabled: true,
              backgroundColor: 'rgba(9,105,218,.15)',
              borderColor: 'rgba(9,105,218,.6)', borderWidth: 1,
            },
            mode: 'xy',
          },
        },
      },
      interaction: { intersect: false, mode: 'index' },
    },
  });
}

/* ── Build joint selector chips — two rows: L0-L6 (row-l), R0-R6 (row-r) ── */
function buildJointSelector(numJoints) {
  const t = App.traj;
  // Only build once; ignore subsequent calls
  if (t.numJoints === TRAJ_JOINT_COUNT) return;
  t.numJoints = TRAJ_JOINT_COUNT;

  // Default: first 4 joints selected
  t.selectedJoints = new Set([0, 1, 2, 3]);

  // Rows are already in HTML; insert chips BEFORE the All/None buttons
  const rowL = $('joint-row-l');  // L0-L6 + All
  const rowR = $('joint-row-r');  // R0-R6 + None
  const btnAll  = $('btn-joints-all');
  const btnNone = $('btn-joints-none');

  for (let i = 0; i < TRAJ_JOINT_COUNT; i++) {
    const chip = document.createElement('span');
    const color = JOINT_COLORS[i];
    chip.className = 'joint-sel-chip' + (t.selectedJoints.has(i) ? ' active' : '');
    chip.textContent = TRAJ_JOINT_LABELS[i];
    chip.dataset.idx = i;
    _applyChipColor(chip, t.selectedJoints.has(i), color);
    chip.addEventListener('click', () => {
      if (t.selectedJoints.has(i)) {
        t.selectedJoints.delete(i);
        chip.classList.remove('active');
        _applyChipColor(chip, false, color);
      } else {
        t.selectedJoints.add(i);
        chip.classList.add('active');
        _applyChipColor(chip, true, color);
      }
      refreshUnifiedChart();
      schedulePersistVisualState();
    });
    if (i < 7) {
      rowL.insertBefore(chip, btnAll);   // insert before All
    } else {
      rowR.insertBefore(chip, btnNone);  // insert before None
    }
  }

  refreshUnifiedChart();
}

/** Apply colour styling to a chip based on active state */
function _applyChipColor(chip, active, color) {
  if (active) {
    chip.style.borderColor = color;
    chip.style.color       = color;
    chip.style.background  = color.replace('rgb(', 'rgba(').replace(')', ', 0.12)');
  } else {
    chip.style.borderColor = '';
    chip.style.color       = '';
    chip.style.background  = '';
  }
}

function recomputeTrajXWindow() {
  const t = App.traj;
  const keys = ['state', 'action_fitted', 'action_raw'];
  const activeKeys = keys.filter(k => t.source.has(k));
  const targetKeys = activeKeys.length ? activeKeys : keys;

  const rightCandidates = [];
  targetKeys.forEach(k => {
    const buf = t.buffer[k];
    if (!buf || buf.length === 0) return;
    rightCandidates.push(buf[buf.length - 1].x);
  });
  if (!rightCandidates.length) return;

  const right = Math.max(...rightCandidates);
  if (!Number.isFinite(right)) return;

  const span = normalizeTrajWindowSpanSec(t.windowSpanSec, TRAJ_WINDOW_SPAN_SEC);
  t.windowSpanSec = span;
  t.xRight = right;
  t.xLeft = Math.max(0, right - span);
}

/* ── Ingest new data point ── */
function ingestTrajData(stateArr, actionFittedArr, actionRawArr = [], timestampSec = null) {
  const n = Math.max(stateArr.length, actionFittedArr.length, actionRawArr.length);
  if (n === 0) return;

  // Build selector if numJoints changed
  buildJointSelector(n);

  const t = App.traj;
  const nowSec = Number.isFinite(Number(timestampSec)) ? Number(timestampSec) : (Date.now() / 1000);
  if (t.startTimeSec == null) t.startTimeSec = nowSec;

  let x = nowSec - t.startTimeSec;
  if (!Number.isFinite(x) || x < 0) x = t.lastX;
  if (x < t.lastX) x = t.lastX;
  t.lastX = x;

  if (stateArr.length > 0) {
    t.buffer.state.push({ x, joints_y: stateArr.slice() });
    trimTrajBufferToMaxWindow('state', x);
  }
  if (actionFittedArr.length > 0) {
    t.buffer.action_fitted.push({ x, joints_y: actionFittedArr.slice() });
    trimTrajBufferToMaxWindow('action_fitted', x);
  }
  if (actionRawArr.length > 0) {
    t.buffer.action_raw.push({ x, joints_y: actionRawArr.slice() });
    trimTrajBufferToMaxWindow('action_raw', x);
  }

  // If Source is None (all unchecked), keep axis frozen and skip redraw trigger.
  if (t.source.size === 0) return;

  recomputeTrajXWindow();
  t.dirty = true;
}

/* ── Extract series data for one joint from one buffer ── */
function getJointSeriesData(bufferKey, jointIdx) {
  const buf = App.traj.buffer[bufferKey];
  if (!buf || buf.length === 0) return [];
  // Do not filter by x-window here; Chart.js x.min/x.max handles clipping.
  // This avoids per-refresh full-buffer filtering overhead and improves smoothness.
  return buf.map(p => ({ x: p.x, y: p.joints_y[jointIdx] }));
}

/* ── Rebuild all datasets in the unified chart ── */
function refreshUnifiedChart() {
  const t = App.traj;
  if (!t.chart) return;

  const src = t.source;   // Set<'state'|'action_fitted'|'action_raw'>
  const datasets = [];
  let allY = [];

  const sorted = [...t.selectedJoints].sort((a, b) => a - b);
  const enabledSources = ['state', 'action_fitted', 'action_raw'].filter(k => src.has(k));
  const showSuffix = enabledSources.length > 1;


  for (const jointIdx of sorted) {
    const color  = JOINT_COLORS[jointIdx] || 'rgb(100,100,100)';
    const label  = TRAJ_JOINT_LABELS[jointIdx] ?? `J${jointIdx}`;
    const alpha  = color.replace('rgb(', 'rgba(').replace(')', ', 0.08)');

    if (src.has('state')) {
      const data = getJointSeriesData('state', jointIdx);
      datasets.push({
        label: label + (showSuffix ? ' (S)' : ''),
        data,
        borderColor: color,
        backgroundColor: alpha,
        borderWidth: 1.5,
        borderDash: [1, 3],
        pointRadius: 0, pointHoverRadius: 3,
        tension: 0.1, fill: false,
      });
      allY = allY.concat(data.map(p => p.y).filter(Number.isFinite));
    }

    if (src.has('action_fitted')) {
      const data = getJointSeriesData('action_fitted', jointIdx);
      datasets.push({
        label: label + (showSuffix ? ' (AF)' : ''),
        data,
        borderColor: color,
        backgroundColor: alpha,
        borderWidth: 1.5,
        borderDash: [],
        pointRadius: 0, pointHoverRadius: 3,
        tension: 0.1, fill: false,
      });
      allY = allY.concat(data.map(p => p.y).filter(Number.isFinite));
    }

    if (src.has('action_raw')) {
      const data = getJointSeriesData('action_raw', jointIdx);
      datasets.push({
        label: label + (showSuffix ? ' (AR)' : ''),
        data,
        borderColor: color,
        backgroundColor: alpha,
        borderWidth: 1.5,
        borderDash: [4, 3],
        pointRadius: 0, pointHoverRadius: 3,
        tension: 0.1, fill: false,
      });
      allY = allY.concat(data.map(p => p.y).filter(Number.isFinite));
    }
  }

  t.chart.data.datasets = datasets;

  // Dynamic Y range with 10% padding
  if (allY.length > 0) {
    const yMin = Math.min(...allY);
    const yMax = Math.max(...allY);
    const pad  = (yMax - yMin) * 0.1 || 0.1;
    t.chart.options.scales.y.min = yMin - pad;
    t.chart.options.scales.y.max = yMax + pad;
  } else {
    t.chart.options.scales.y.min = undefined;
    t.chart.options.scales.y.max = undefined;
  }

  // Sync X window
  const { xLeft, xRight } = t;
  if (Number.isFinite(xLeft) && Number.isFinite(xRight) && xRight > xLeft) {
    t.chart.options.scales.x.min = xLeft;
    t.chart.options.scales.x.max = xRight;
  } else {
    t.chart.options.scales.x.min = undefined;
    t.chart.options.scales.x.max = undefined;
  }

  t.chart.update('none');
}

/* ── Batch update timer (50 ms, 20 FPS) ── */
function startTrajUpdateTimer() {
  if (App.traj.updateTimer) clearInterval(App.traj.updateTimer);
  const intervalMs = Number.isFinite(Number(App.traj.updateIntervalMs))
    ? Math.max(16, Number(App.traj.updateIntervalMs))
    : DEFAULT_TRAJ_UPDATE_MS;

  App.traj.updateTimer = setInterval(() => {
    if (!App.traj.dirty || App.traj.paused) return;
    const now = Date.now();
    if (now - App.traj.lastUpdateAt < intervalMs) return;
    refreshUnifiedChart();
    App.traj.dirty = false;
    App.traj.lastUpdateAt = now;
  }, intervalMs);
}

/* ── Wire trajectory controls ── */
function setupTrajPanel() {
  // Source checkboxes: toggle independently; all can be deselected
  const srcChecks = {
    state: $('chk-traj-state'),
    action_fitted: $('chk-traj-action-fitted'),
    action_raw: $('chk-traj-action-raw'),
  };
  const btnAllSource = $('btn-traj-all');

  function syncSrcButtons() {
    Object.entries(srcChecks).forEach(([k, chk]) => {
      if (!chk) return;
      chk.checked = App.traj.source.has(k);
    });
    if (btnAllSource) {
      const s = App.traj.source;
      const allSelected = s.has('state') && s.has('action_fitted') && s.has('action_raw');
      btnAllSource.className = 'btn btn-xs' + (allSelected ? ' btn-active' : '');
      btnAllSource.textContent = allSelected ? 'None' : 'All';
    }
  }
  function setSource(src, enabled) {
    const s = App.traj.source;
    if (enabled) s.add(src);
    else s.delete(src);
    if (s.size > 0) recomputeTrajXWindow();
    App.traj.dirty = true;
    syncSrcButtons();
    refreshUnifiedChart();
    schedulePersistVisualState();
  }
  srcChecks.state?.addEventListener('change', e => setSource('state', !!e.target.checked));
  srcChecks.action_fitted?.addEventListener('change', e => setSource('action_fitted', !!e.target.checked));
  srcChecks.action_raw?.addEventListener('change', e => setSource('action_raw', !!e.target.checked));
  if (btnAllSource) {
    btnAllSource.addEventListener('click', () => {
      const s = App.traj.source;
      const allSelected = s.has('state') && s.has('action_fitted') && s.has('action_raw');
      App.traj.source = allSelected
        ? new Set()
        : new Set(['state', 'action_fitted', 'action_raw']);
      if (App.traj.source.size > 0) recomputeTrajXWindow();
      App.traj.dirty = true;
      syncSrcButtons();
      refreshUnifiedChart();
      schedulePersistVisualState();
    });
  }
  syncSrcButtons();

  const windowSlider = $('traj-window-span-slider');
  const applyWindowSpan = (raw) => {
    const next = normalizeTrajWindowSpanSec(Number(raw), App.traj.windowSpanSec);
    App.traj.windowSpanSec = next;
    syncTrajWindowSpanUI();
    if (App.traj.source.size > 0) recomputeTrajXWindow();
    App.traj.dirty = true;
    refreshUnifiedChart();
    schedulePersistVisualState();
  };
  if (windowSlider) {
    windowSlider.addEventListener('input', e => applyWindowSpan(e.target.value));
    windowSlider.addEventListener('change', e => applyWindowSpan(e.target.value));
  }
  syncTrajWindowSpanUI();

  // Play/Pause
  function syncTrajPlayButton() {
    const btn = $('btn-traj-pause');
    if (!btn) return;
    btn.innerHTML = App.traj.paused
      ? '<span class="btn-icon">▶</span> Play'
      : '<span class="btn-icon">⏸</span> Pause';
    btn.className = 'btn btn-xs' + (App.traj.paused ? ' btn-active' : '');
  }

  $('btn-traj-pause').addEventListener('click', () => {
    App.traj.paused = !App.traj.paused;
    syncTrajPlayButton();
    if (!App.traj.paused) {
      App.traj.dirty = true;
      refreshUnifiedChart();
    }
    schedulePersistVisualState();
  });
  syncTrajPlayButton();

  // Clear
  $('btn-traj-clear').addEventListener('click', () => {
    App.traj.buffer = { state: [], action_fitted: [], action_raw: [] };
    App.traj.startTimeSec = null;
    App.traj.lastX = 0;
    App.traj.xLeft = 0; App.traj.xRight = 0;
    App.traj.dirty = true;
    refreshUnifiedChart();
  });

  // Collapse
  $('btn-traj-collapse').addEventListener('click', () => {
    const body     = $('traj-body');
    const btn      = $('btn-traj-collapse');
    const panelT   = $('panel-traj');
    const panelL   = $('panel-lang');
    const collapsed = body.classList.toggle('collapsed');
    panelT.classList.toggle('body-collapsed', collapsed);
    panelL.classList.toggle('expanded', collapsed);
    btn.textContent = collapsed ? '▲' : '▼';
  });

  // Select all / none
  $('btn-joints-all').addEventListener('click', () => {
    const t = App.traj;
    for (let i = 0; i < TRAJ_JOINT_COUNT; i++) {
      if (!t.selectedJoints.has(i)) {
        t.selectedJoints.add(i);
        const chip = document.querySelector(`.joint-sel-chip[data-idx="${i}"]`);
        if (chip) { chip.classList.add('active'); _applyChipColor(chip, true, JOINT_COLORS[i]); }
      }
    }
    t.dirty = true;
    refreshUnifiedChart();
    schedulePersistVisualState();
  });

  $('btn-joints-none').addEventListener('click', () => {
    const t = App.traj;
    [...t.selectedJoints].forEach(i => {
      const chip = document.querySelector(`.joint-sel-chip[data-idx="${i}"]`);
      if (chip) { chip.classList.remove('active'); _applyChipColor(chip, false, JOINT_COLORS[i]); }
    });
    t.selectedJoints.clear();
    refreshUnifiedChart();
    schedulePersistVisualState();
  });

  startTrajUpdateTimer();
}

// ═══════════════════════════════════════════════════════
//  Event wiring — config, client control, manual ctrl
// ═══════════════════════════════════════════════════════

/** Return path starting from /conf segment (e.g. /conf/user.py) */
function _confRelPath(fullPath) {
  const normalized = fullPath.replace(/\\/g, '/');
  const idx = normalized.lastIndexOf('/conf/');
  return idx >= 0 ? normalized.slice(idx) : normalized;
}

/**
 * 初始化并绑定页面中各功能面板的事件处理程序
 * - 配置面板：支持通过文件选择器加载配置、保存、另存为、搜索过滤、应用待改动、重置为服务器配置；加载成功后渲染配置树与语言预设，并在界面上显示配置相对路径
 * - 布局控制：支持折叠配置面板并动态调整主布局列宽
 * - 运行控制：绑定客户端的 Start/Stop/Pause/Resume/Reset 按钮，必要时在启动前自动提交待改动补丁
 * - 数据录制/回放：切换录制状态、选择回放目录并发送回放命令，同时在界面上显示选择的目录
 * - 语言指令：加载语言任务 JSON 文件、渲染任务选择器、发送语言指令，支持 Ctrl+Enter 快捷发送与面板折叠
 * - 手动控制：为夹爪、头部、腰部的控制按钮绑定发送命令，发送成功后以通知提示
 * - 统一使用后端 API 接口进行异步交互，并通过通知反馈结果；在多数失败场景下已内部捕获并提示
 * 使用约定：应在页面初始化时调用一次，以确保 DOM 已就绪且必需的元素均存在
 * @returns {void} 无返回值
 * @throws {Error} 当必需的 DOM 元素缺失导致事件绑定失败，或个别未被内部捕获的 API/渲染异常发生时可能抛出错误
 */
function wireEvents() {
  // Config file bar — Load via file picker
  $('conf-file-input').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const path = file.path || (CONF_DIR + '/' + file.name);
    // const path = file.path || null;
    try {
      const res = await apiFetch('/api/config/load_file', { method: 'POST', body: JSON.stringify({ path }) });
      App.config = res.config || {}; App.pendingPatch = {};
      clearPending();
      renderConfigTree(App.config);
      await loadDefaultLangFile();
      applyLangConfigSelection();
      applyVisualConfig(App.config);
      // Show relative path from /conf onward
      const display = $('conf-path-display');
      if (display) {
        const rel = _confRelPath(path);
        display.textContent = rel;
        display.title = path;
        display.dataset.fullPath = path;
      }
      toast('Config file loaded.', 'ok');
    } catch (e) { /* toasted */ }
    e.target.value = '';
  });

  // Save As — modal with conf/ as default prefix
  $('btn-saveas-file').addEventListener('click', () => {
    const display = $('conf-path-display');
    const current = (display && display.dataset.fullPath) || '';
    $('saveas-path').value = current || (CONF_DIR + '/my_config.py');
    $('modal-saveas').classList.remove('hidden');
  });
  $('btn-saveas-confirm').addEventListener('click', async () => {
    const path = $('saveas-path').value.trim();
    if (!path) return;
    $('modal-saveas').classList.add('hidden');
    try {
      await apiFetch('/api/config/save_file', { method: 'POST', body: JSON.stringify({ path }) });
      const display = $('conf-path-display');
      if (display) { display.textContent = _confRelPath(path); display.title = path; display.dataset.fullPath = path; }
      toast(`Saved as ${_confRelPath(path)}`, 'ok');
    } catch (e) { /* toasted */ }
  });
  $('btn-saveas-cancel').addEventListener('click', () => $('modal-saveas').classList.add('hidden'));

  $('conf-search').addEventListener('input', e => filterConfigTree(e.target.value));

  $('btn-apply-config').addEventListener('click', async () => {
    if (!Object.keys(App.pendingPatch).length) { toast('No pending changes.', 'warn', 2000); return; }

    const configTree = $('config-tree');
    const prevScrollTop = configTree ? configTree.scrollTop : 0;
    const prevScrollLeft = configTree ? configTree.scrollLeft : 0;
    const restoreConfigTreeScroll = () => {
      if (!configTree) return;
      configTree.scrollTop = prevScrollTop;
      configTree.scrollLeft = prevScrollLeft;
    };

    try {
      const res = await apiFetch('/api/config/patch', { method: 'POST', body: JSON.stringify({ patch: App.pendingPatch }) });
      App.config = res.config || {}; App.pendingPatch = {};
      clearPending();
      renderConfigTree(App.config);
      await loadDefaultLangFile();
      applyLangConfigSelection();
      applyVisualConfig(App.config);
      restoreConfigTreeScroll();
      requestAnimationFrame(restoreConfigTreeScroll);
      toast('Config applied.', 'ok');
      // Auto-save after apply
      const display = $('conf-path-display');
      const path = (display && display.dataset.fullPath) || (display && display.textContent.trim()) || '';
      if (path) {
        try {
          await apiFetch('/api/config/save_file', { method: 'POST', body: JSON.stringify({ path }) });
          toast(`Saved to ${_confRelPath(path)}`, 'ok');
        } catch (_) { /* toasted */ }
      }
    } catch (e) { /* toasted */ }
  });

  $('btn-config-collapse').addEventListener('click', () => {
    const leftCol = $('left-col');
    const collapsed = leftCol.classList.toggle('collapsed');
    $('btn-config-reveal').classList.toggle('hidden', !collapsed);
    updateLayoutColumns();
  });
  $('btn-config-reveal').addEventListener('click', () => {
    $('left-col').classList.remove('collapsed');
    $('btn-config-reveal').classList.add('hidden');
    updateLayoutColumns();
  });

  // Client control
  $('btn-start').addEventListener('click', async () => {
    if (App.isRunning) {
      try { await apiFetch('/api/client/stop', { method: 'POST' }); } catch (e) { /* toasted */ }
      return;
    }
    if (Object.keys(App.pendingPatch).length) {
      try {
        await apiFetch('/api/config/patch', { method: 'POST', body: JSON.stringify({ patch: App.pendingPatch }) });
        App.pendingPatch = {}; clearPending();
      } catch (e) { return; }
    }
    try { await apiFetch('/api/client/start', { method: 'POST' }); toast('Client starting…', 'info'); } catch (e) { /* toasted */ }
  });

  $('btn-pause').addEventListener('click', async () => {
    try {
      if (App.isPaused) {
        await apiFetch('/api/client/resume', { method: 'POST' });
        // toast('Client resumed.', 'ok');
      } else {
        await apiFetch('/api/client/pause', { method: 'POST' });
        // toast('Client paused.', 'warn');
      }
    } catch (e) { /* toasted */ }
  });

  $('btn-reset').addEventListener('click',  async () => {
    await sendCommand('reset');
    toast('Robot reset initiated.', 'info');
  });

  // Record button — toggle recording via command
  $('btn-record').addEventListener('click', async () => {
    const btn = $('btn-record');
    const recording = btn.classList.toggle('btn-active');
    await sendCommand('record', { enable: recording });
    toast(recording ? 'Recording started.' : 'Recording stopped.', recording ? 'ok' : 'warn', 2500);
  });

  // Replay — folder picker triggers load
  $('replay-folder-input').addEventListener('change', async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    // Derive folder path from the first file's webkitRelativePath or path
    const first = files[0];
    let folderPath = '';
    if (first.path) {
      // Electron / NW.js: absolute path available
      folderPath = first.path.replace(/[\\/][^\\/]+$/, '');
    } else if (first.webkitRelativePath) {
      // Browser: use the top-level folder name only (server resolves relative)
      folderPath = first.webkitRelativePath.split('/')[0];
    } else {
      folderPath = first.name;
    }
    // Show path pill
    const pill = $('replay-path-display');
    if (pill) { pill.textContent = folderPath; pill.title = folderPath; }
    try {
      await apiFetch('/api/client/command', { method: 'POST', body: JSON.stringify({ command: 'replay', params: { path: folderPath } }) });
      toast(`Replay loaded: ${folderPath}`, 'ok', 3000);
    } catch (_) { /* toasted */ }
    e.target.value = '';
  });

  // Language Command panel — JSON file picker
  $('lang-file-input').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const path = file.path || file.name;
    try {
      const res = await apiFetch('/api/lang_file/load', { method: 'POST', body: JSON.stringify({ path }) });
      buildLangTasksFromData(res.data);
      renderLangTaskSelect();

      if (!App.config || typeof App.config !== 'object') App.config = {};
      if (!App.config.language || typeof App.config.language !== 'object') App.config.language = {};
      App.config.language.file_path = path;

      App.pendingPatch['language.file_path'] = path;
      markPending();

      try {
        const patchRes = await apiFetch('/api/config/patch', {
          method: 'POST',
          body: JSON.stringify({ patch: { 'language.file_path': path } }),
        });
        App.config = patchRes.config || App.config;
        delete App.pendingPatch['language.file_path'];
        if (!Object.keys(App.pendingPatch).length) clearPending();

        const display = $('conf-path-display');
        const cfgPath = (display && display.dataset.fullPath) || (display && display.textContent.trim()) || '';
        if (cfgPath) {
          await apiFetch('/api/config/save_file', { method: 'POST', body: JSON.stringify({ path: cfgPath }) });
        }
      } catch (_) {
        App.pendingPatch['language.file_path'] = path;
        markPending();
      }

      toast('Language file loaded.', 'ok', 2000);
    } catch (_) { /* toasted */ }
    e.target.value = '';
  });

  // Language Command panel — send
  $('btn-lang-send').addEventListener('click', async () => {
    const lang = $('lang-cmd-text').value.trim();
    if (!lang) { toast('Enter a language instruction.', 'warn'); return; }

    // 1. Write current Task / SubTask selection into pendingPatch
    const taskSel    = $('lang-task-select');
    const subtaskSel = $('lang-subtask-select');
    const task  = taskSel    ? taskSel.value                    : null;
    const idx   = subtaskSel ? parseInt(subtaskSel.value, 10)   : NaN;
    if (task != null) {
      App.pendingPatch['language.task_id']  = task;
      App.pendingPatch['language.sub_task_id'] = isNaN(idx) ? 0 : idx;
      markPending();
    }

    // 2. Trigger Config Apply (patch + save) — reuse the same handler
    $('btn-apply-config').click();

    // 3. Send language command to robot
    await sendCommand('set_language', { language: lang });
    toast('Language updated & robot reset.', 'info');
  });
  $('lang-cmd-text').addEventListener('keydown', e => { if (e.key === 'Enter' && e.ctrlKey) $('btn-lang-send').click(); });

  // Language Command panel collapse
  $('btn-lang-collapse').addEventListener('click', () => {
    const body = $('lang-body');
    const btn  = $('btn-lang-collapse');
    const collapsed = body.classList.toggle('collapsed');
    btn.textContent = collapsed ? '▲' : '▼';
  });

  // Manual robot control
  $('btn-gripper').addEventListener('click', async () => sendCommand('gripper', { pos: [parseFloat($('gripper-l').value), parseFloat($('gripper-r').value)] }));
  $('btn-head').addEventListener('click',    async () => sendCommand('head',    { pos: [parseFloat($('head-yaw').value),   parseFloat($('head-pitch').value)]  }));
  $('btn-waist').addEventListener('click',   async () => sendCommand('waist',   { pos: [parseFloat($('waist-pitch').value), parseFloat($('waist-height').value)] }));
  $('btn-arm-reset').addEventListener('click', async () => { await sendCommand('reset'); toast('Arm reset command sent.', 'ok'); });
  $('btn-gripper-open').addEventListener('click', async () => {
    $('gripper-l').value = '1';
    $('gripper-r').value = '1';
    await sendCommand('gripper', { pos: [1, 1] });
    toast('Gripper opened.', 'ok');
  });
  $('btn-gripper-close').addEventListener('click', async () => {
    $('gripper-l').value = '0';
    $('gripper-r').value = '0';
    await sendCommand('gripper', { pos: [0, 0] });
    toast('Gripper closed.', 'ok');
  });
  $('btn-save-data').addEventListener('click',    async () => { await sendCommand('save_data');    toast('Data saved.',      'ok');   });
  $('btn-discard-data').addEventListener('click', async () => { await sendCommand('discard_data'); toast('Data discarded.', 'warn'); });
}

async function sendCommand(command, params = {}) {
  try {
    await apiFetch('/api/client/command', { method: 'POST', body: JSON.stringify({ command, params }) });
  } catch (e) { /* toasted */ }
}

// ═══════════════════════════════════════════════════════
//  Status poll fallback
// ═══════════════════════════════════════════════════════
function startStatusPoll() {
  setInterval(async () => {
    if (App.wsAlive) return;
    try {
      const res  = await fetch('/api/client/status');
      const json = await res.json();
      if (json.data) renderStats(json.data);
    } catch (e) { /* ignore */ }
  }, 1000);
}

// ═══════════════════════════════════════════════════════
//  Init
// ═══════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  wireEvents();
  setupCameraPanel();
  setupTrajPanel();
  setupLangPanel();
  setupRecordingPanel();
  createUnifiedChart();                  // create single unified trajectory chart
  buildJointSelector(TRAJ_JOINT_COUNT);  // pre-build fixed 14-joint selector
  connectWS();
  startStatusPoll();
  initConfDir().then(async () => {
    await loadConfigFromServer();
    await loadDefaultLangFile();
  });
});
