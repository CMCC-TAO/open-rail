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
 *   POST /api/client/command     { command, params }
 */

'use strict';

// ═══════════════════════════════════════════════════════
//  Constants
// ═══════════════════════════════════════════════════════
const WS_URL    = `ws://${location.host}/ws`;
const RECONNECT = 3000;

// Max data points per series (mirrors visual/app.js maxChartPoints)
const MAX_CHART_POINTS  = 1500;
// Chart update interval in ms (20 FPS, same as visual/)
const CHART_UPDATE_MS   = 50;

// Per-joint colour palette (14 colours, one per joint L0-L6 R0-R6)
const JOINT_COLORS = [
  // L0-L6: blue family
  'rgb(30, 120, 220)',   // L0
  'rgb(0, 180, 240)',    // L1
  'rgb(0, 210, 180)',    // L2
  'rgb(60, 200, 80)',    // L3
  'rgb(140, 200, 40)',   // L4
  'rgb(200, 180, 0)',    // L5
  'rgb(240, 130, 0)',    // L6
  // R0-R6: red/purple family
  'rgb(220, 50, 50)',    // R0
  'rgb(220, 40, 140)',   // R1
  'rgb(160, 40, 220)',   // R2
  'rgb(100, 60, 220)',   // R3
  'rgb(40, 100, 210)',   // R4
  'rgb(0, 160, 160)',    // R5
  'rgb(80, 160, 80)',    // R6
];

// ═══════════════════════════════════════════════════════
//  State
// ═══════════════════════════════════════════════════════
const App = {
  ws: null,
  wsAlive: false,
  reconnectTimer: null,
  isRunning: null,   // null = uninitialised; set on first stats push

  config: {},
  pendingPatch: {},
  langPresets: [],

  // Camera open/close state — default all open
  camOpen: [true, true, true],

  // ── Trajectory chart state ──
  traj: {
    // Set<'state'|'action'> — which sources to display (both can be active simultaneously)
    source: new Set(['state']),
    paused: false,
    // Number of joints (determined from first data push)
    numJoints: 0,
    // Which joints to display  Set<number>
    selectedJoints: new Set(),
    // Data buffer: { 'state': [{x, joints_y}, ...], 'action': [{x, joints_y}, ...] }
    buffer: { state: [], action: [] },
    // step counter (x-axis)
    stepCounter: 0,
    // x window bounds
    xLeft: 0, xRight: 0,
    // Single unified Chart.js instance
    chart: null,
    // Dirty flag → batch updates at CHART_UPDATE_MS
    dirty: false,
    updateTimer: null,
    lastUpdateAt: 0,
  },
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
    // Binary frame: camera image data (mirrors visual/app.js handleBinaryCameraData)
    if (ev.data instanceof ArrayBuffer || ev.data instanceof Blob) {
      decodeCameraBinaryFrame(ev.data);
      return;
    }
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

function handleWSMessage(msg) {
  switch (msg.type) {
    case 'stats':  renderStats(msg.data); break;
    case 'status': toast(msg.data.message, msg.data.running ? 'ok' : 'warn'); setRunningUI(msg.data.running); break;
    case 'error':  toast(msg.data.message, 'error'); setRunningUI(false); break;
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
    const buf = raw instanceof Blob ? await raw.arrayBuffer() : raw;
    const view = new DataView(buf);
    const headerLen = view.getUint32(0, false);  // big-endian
    const headerBytes = new Uint8Array(buf, 4, headerLen);
    const header = JSON.parse(new TextDecoder().decode(headerBytes));
    if (header.type !== 'camera_data_binary') return;
    const cameraId = header.camera_id;
    if (cameraId === undefined || cameraId === null) return;
    const imageBytes = new Uint8Array(buf, 4 + headerLen);
    handleCameraFrame(Number(cameraId), imageBytes);
  } catch (e) { /* malformed frame, ignore */ }
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
  135.12, 142.67, 118.45, 156.30, 127.89, 163.54, 109.22,
  // Arm-Right J7-J13
  148.76, 131.09, 170.43, 125.61, 158.97, 114.28, 177.35,
  // Gripper   J14-J15
  100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00
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

function getDefaultState()  { if (!_defaultStateCache)  _defaultStateCache  = _makeDefaultJointValues(0.02); return _defaultStateCache; }
function getDefaultAction() { if (!_defaultActionCache) _defaultActionCache = _makeDefaultJointValues(0.04); return _defaultActionCache; }

// ═══════════════════════════════════════════════════════
//  Stats rendering
// ═══════════════════════════════════════════════════════
function renderStats(data) {
  setRunningUI(data.running);

  $('val-infer-count').textContent = data.infer_count ?? '–';
  $('val-infer-time').textContent  = data.avg_infer_time != null
    ? (data.avg_infer_time * 1000).toFixed(1) + ' ms' : '–';
  $('val-traj-time').textContent   = data.avg_traj_time != null
    ? (data.avg_traj_time * 1000).toFixed(1) + ' ms' : '–';

  // Use default joint values when client is not running and no real data available
  const stateVals  = (data.current_state  && data.current_state.length)  ? data.current_state  : getDefaultState();
  const actionVals = (data.current_action && data.current_action.length) ? data.current_action : getDefaultAction();
  renderJointsGrouped('state',  stateVals);
  renderJointsGrouped('action', actionVals);

  $('debug-info').textContent = data.debug_info || '';

  // Feed trajectory chart (only real data, not defaults)
  ingestTrajData(data.current_state || [], data.current_action || []);
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
    const val = typeof v === 'number' ? v.toFixed(2) : v;
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
function setRunningUI(running) {
  if (App.isRunning === running) return;
  App.isRunning = running;
  $('status-badge').textContent = running ? 'RUNNING' : 'STOPPED';
  $('status-badge').className = `status-badge ${running ? 'running' : 'stopped'}`;
  $('btn-start').disabled  = running;
  $('btn-stop').disabled   = !running;
  $('btn-pause').disabled  = !running;
  $('btn-resume').disabled = !running;
  $('btn-reset').disabled  = !running;
}

// ═══════════════════════════════════════════════════════
//  Config rendering — BASIC group split into sub-groups
// ═══════════════════════════════════════════════════════

// Keys to exclude from the config tree (handled separately)
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
  'fps', 'height', 'width',
]);

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
      parentEl.appendChild(createCfgRow(`${prefix}.${key}`, key, val));
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
      parentEl.appendChild(createCfgRow(`${prefix}.${key}`, key, val));
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
    'robots', // Move ROBOTS to the top of the sub-groups (immediately after BASIC)
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
  header.className = 'cfg-group-header open';
  header.innerHTML = `<span class="cfg-group-toggle">▶</span><span>${label}</span>`;
  const body = document.createElement('div');
  body.className = 'cfg-group-body';
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
  header.className = 'cfg-group-header open';
  header.innerHTML = `<span class="cfg-group-toggle">▶</span><span>${label}</span>`;
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
  if (CONFIG_SELECT_OPTIONS[bareKey]) {
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
  const raw = input.tagName === 'SELECT' ? input.value : input.value.trim();
  const bareKey = dotKey.includes('.') ? dotKey.split('.').pop() : dotKey;
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
  $('pending-badge').classList.remove('hidden');
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
  const taskSel    = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');

  // Task select → rebuild subtask list
  if (taskSel) {
    taskSel.addEventListener('change', () => {
      renderLangSubtaskSelect();
    });
  }

  // Subtask select → fill textarea
  if (subtaskSel) {
    subtaskSel.addEventListener('change', () => {
      const taskName = taskSel ? taskSel.value : null;
      const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
      const idx = parseInt(subtaskSel.value, 10);
      if (!isNaN(idx) && subtasks[idx] !== undefined) {
        $('lang-cmd-text').value = subtasks[idx];
      }
    });
  }
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

async function loadConfigFromServer() {
  try {
    const res = await apiFetch('/api/config');
    App.config = res.config || {};
    App.pendingPatch = {};
    $('pending-badge').classList.add('hidden');
    renderConfigTree(App.config);
    if (App.config.language && Array.isArray(App.config.language)) {
      renderLangPresets(App.config.language);
    }
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

/** Load the default language command JSON from server and populate Language Command panel. */
async function loadDefaultLangFile() {
  try {
    const res = await apiFetch('/api/default_lang_file');
    if (res.data) {
      buildLangTasksFromData(res.data);
      renderLangTaskSelect();
    }
  } catch (_) { /* non-fatal: lang panel stays empty */ }
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
  updateInterval: 33,   // 30 FPS
  updateTimer: null,
};

/** Recalculate and apply grid-template-columns based on current collapsed state. */
function updateLayoutColumns() {
  const configCollapsed = document.querySelector('.panel-config').classList.contains('collapsed');
  const visualCollapsed = $('panel-visual').classList.contains('collapsed');
  const left  = configCollapsed ? '0px'   : '280px';
  const right = visualCollapsed ? '0px'   : '300px';
  // When a column is 0, also suppress the gap on that side by adjusting padding
  const layout = document.querySelector('.layout');
  layout.style.gridTemplateColumns = `${left} 1fr ${right}`;
  // Suppress padding on collapsed sides so no whitespace strip remains
  const gap = getComputedStyle(document.documentElement).getPropertyValue('--panel-gap').trim();
  layout.style.paddingLeft   = configCollapsed ? '0' : gap;
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
    $(`btn-cam-${i}`).addEventListener('click', () => { toggleCamera(i); updateAllToggleBtn(); });
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
  });

  // Start 30FPS render timer (same as visual/app.js cameraUpdateTimer)
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
    // Show placeholder if no image yet
    if (!imgEl.src || imgEl.src === location.href) {
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
  }
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
            usePointStyle: true, padding: 8,
            font: { size: 9 }, color: '#1f2328',
            boxWidth: 20,
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

/* ── Ingest new data point ── */
function ingestTrajData(stateArr, actionArr) {
  if (App.traj.paused) return;
  const n = Math.max(stateArr.length, actionArr.length);
  if (n === 0) return;

  // Build selector if numJoints changed
  buildJointSelector(n);

  const t   = App.traj;
  const x   = ++t.stepCounter;

  if (stateArr.length > 0) {
    t.buffer.state.push({ x, joints_y: stateArr.slice() });
    if (t.buffer.state.length > MAX_CHART_POINTS) t.buffer.state.shift();
  }
  if (actionArr.length > 0) {
    t.buffer.action.push({ x, joints_y: actionArr.slice() });
    if (t.buffer.action.length > MAX_CHART_POINTS) t.buffer.action.shift();
  }

  // Update x window
  const stateRight  = t.buffer.state.length  ? t.buffer.state[t.buffer.state.length - 1].x   : -Infinity;
  const actionRight = t.buffer.action.length ? t.buffer.action[t.buffer.action.length - 1].x : -Infinity;
  const stateLeft   = t.buffer.state.length  ? t.buffer.state[0].x   : -Infinity;
  const actionLeft  = t.buffer.action.length ? t.buffer.action[0].x : -Infinity;
  const span  = Math.max(stateRight - stateLeft, actionRight - actionLeft);
  const right = Math.max(stateRight, actionRight);
  if (Number.isFinite(right)) {
    t.xRight = right;
    if (span > 0) t.xLeft = right - span;
  }

  t.dirty = true;
}

/* ── Extract series data for one joint from one buffer ── */
function getJointSeriesData(bufferKey, jointIdx) {
  const buf = App.traj.buffer[bufferKey];
  if (!buf || buf.length === 0) return [];
  const { xLeft: left, xRight: right } = App.traj;
  const visible = (Number.isFinite(left) && Number.isFinite(right) && right > left)
    ? buf.filter(p => p.x >= left && p.x <= right)
    : buf;
  return visible.map(p => ({ x: p.x, y: p.joints_y[jointIdx] }));
}

/* ── Rebuild all datasets in the unified chart ── */
function refreshUnifiedChart() {
  const t = App.traj;
  if (!t.chart) return;

  const src = t.source;   // Set<'state'|'action'>
  const datasets = [];
  let allY = [];

  const sorted = [...t.selectedJoints].sort((a, b) => a - b);

  for (const jointIdx of sorted) {
    const color  = JOINT_COLORS[jointIdx] || 'rgb(100,100,100)';
    const label  = TRAJ_JOINT_LABELS[jointIdx] ?? `J${jointIdx}`;
    const alpha  = color.replace('rgb(', 'rgba(').replace(')', ', 0.08)');

    if (src.has('state')) {
      const data = getJointSeriesData('state', jointIdx);
      datasets.push({
        label: label + (src.has('action') ? ' (S)' : ''),
        data,
        borderColor: color,
        backgroundColor: alpha,
        borderWidth: 1.5,
        borderDash: [4, 3],       // dashed = state
        pointRadius: 0, pointHoverRadius: 3,
        tension: 0.1, fill: false,
      });
      allY = allY.concat(data.map(p => p.y).filter(Number.isFinite));
    }

    if (src.has('action')) {
      const data = getJointSeriesData('action', jointIdx);
      datasets.push({
        label: label + (src.has('state') ? ' (A)' : ''),
        data,
        borderColor: color,
        backgroundColor: alpha,
        borderWidth: 1.5,
        borderDash: [],            // solid = action
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
  App.traj.updateTimer = setInterval(() => {
    if (!App.traj.dirty || App.traj.paused) return;
    const now = Date.now();
    if (now - App.traj.lastUpdateAt < CHART_UPDATE_MS) return;
    refreshUnifiedChart();
    App.traj.dirty = false;
    App.traj.lastUpdateAt = now;
  }, CHART_UPDATE_MS);
}

/* ── Wire trajectory controls ── */
function setupTrajPanel() {
  // Source buttons: toggle independently; at least one must remain active
  const srcBtns = { state: $('btn-traj-state'), action: $('btn-traj-action') };
  function syncSrcButtons() {
    Object.entries(srcBtns).forEach(([k, btn]) => {
      btn.className = 'btn btn-xs' + (App.traj.source.has(k) ? ' btn-active' : '');
    });
  }
  function toggleSource(src) {
    const s = App.traj.source;
    if (s.has(src)) {
      // Only deselect if the other source is still selected
      if (s.size > 1) s.delete(src);
    } else {
      s.add(src);
    }
    App.traj.dirty = true;
    syncSrcButtons();
  }
  $('btn-traj-state').addEventListener('click',  () => toggleSource('state'));
  $('btn-traj-action').addEventListener('click', () => toggleSource('action'));

  // Pause
  $('btn-traj-pause').addEventListener('click', () => {
    App.traj.paused = !App.traj.paused;
    $('btn-traj-pause').innerHTML = App.traj.paused
      ? '<span class="btn-icon">▶</span> Play'
      : '<span class="btn-icon">⏸</span> Play';
    $('btn-traj-pause').className   = 'btn btn-xs' + (App.traj.paused ? ' btn-active' : '');
  });

  // Clear
  $('btn-traj-clear').addEventListener('click', () => {
    App.traj.buffer = { state: [], action: [] };
    App.traj.stepCounter = 0;
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
  });

  $('btn-joints-none').addEventListener('click', () => {
    const t = App.traj;
    [...t.selectedJoints].forEach(i => {
      const chip = document.querySelector(`.joint-sel-chip[data-idx="${i}"]`);
      if (chip) { chip.classList.remove('active'); _applyChipColor(chip, false, JOINT_COLORS[i]); }
    });
    t.selectedJoints.clear();
    refreshUnifiedChart();
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
      $('pending-badge').classList.add('hidden');
      renderConfigTree(App.config);
      if (App.config.language) renderLangPresets(App.config.language);
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

  $('btn-save-file').addEventListener('click', async () => {
    const display = $('conf-path-display');
    const path = (display && display.dataset.fullPath) || (display && display.textContent.trim()) || '';
    if (!path) { toast('No config file loaded. Use Load first.', 'warn'); return; }
    try {
      await apiFetch('/api/config/save_file', { method: 'POST', body: JSON.stringify({ path }) });
      toast(`Saved to ${_confRelPath(path)}`, 'ok');
    } catch (e) { /* toasted */ }
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
    try {
      const res = await apiFetch('/api/config/patch', { method: 'POST', body: JSON.stringify({ patch: App.pendingPatch }) });
      App.config = res.config || {}; App.pendingPatch = {};
      $('pending-badge').classList.add('hidden');
      renderConfigTree(App.config);
      if (App.config.language) renderLangPresets(App.config.language);
      toast('Config applied.', 'ok');
    } catch (e) { /* toasted */ }
  });

  $('btn-reset-config').addEventListener('click', async () => {
    App.pendingPatch = {}; $('pending-badge').classList.add('hidden');
    await loadConfigFromServer();
  });

  $('btn-config-collapse').addEventListener('click', () => {
    const panel = document.querySelector('.panel-config');
    const collapsed = panel.classList.toggle('collapsed');
    $('btn-config-reveal').classList.toggle('hidden', !collapsed);
    updateLayoutColumns();
  });
  $('btn-config-reveal').addEventListener('click', () => {
    document.querySelector('.panel-config').classList.remove('collapsed');
    $('btn-config-reveal').classList.add('hidden');
    updateLayoutColumns();
  });

  // Client control
  $('btn-start').addEventListener('click', async () => {
    if (Object.keys(App.pendingPatch).length) {
      try {
        await apiFetch('/api/config/patch', { method: 'POST', body: JSON.stringify({ patch: App.pendingPatch }) });
        App.pendingPatch = {}; $('pending-badge').classList.add('hidden');
      } catch (e) { return; }
    }
    try { await apiFetch('/api/client/start', { method: 'POST' }); toast('Client starting…', 'info'); } catch (e) { /* toasted */ }
  });

  $('btn-stop').addEventListener('click', async () => {
    try { await apiFetch('/api/client/stop', { method: 'POST' }); } catch (e) { /* toasted */ }
  });

  $('btn-pause').addEventListener('click',  async () => sendCommand('pause'));
  $('btn-resume').addEventListener('click', async () => sendCommand('resume'));
  $('btn-reset').addEventListener('click',  async () => { await sendCommand('reset'); toast('Robot reset initiated.', 'info'); });

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
      toast('Language file loaded.', 'ok', 2000);
    } catch (_) { /* toasted */ }
    e.target.value = '';
  });

  // Language Command panel — send
  $('btn-lang-send').addEventListener('click', async () => {
    const lang = $('lang-cmd-text').value.trim();
    if (!lang) { toast('Enter a language instruction.', 'warn'); return; }
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
  createUnifiedChart();                  // create single unified trajectory chart
  buildJointSelector(TRAJ_JOINT_COUNT);  // pre-build fixed 14-joint selector
  connectWS();
  startStatusPoll();
  initConfDir().then(() => loadConfigFromServer());
  loadDefaultLangFile();
});
