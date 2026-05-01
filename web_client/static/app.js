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

// Series colours — same palette as visual/app.js
const COLOR_STATE  = 'rgb(54, 162, 235)';   // blue
const COLOR_ACTION = 'rgb(255, 99, 132)';   // red

// ═══════════════════════════════════════════════════════
//  State
// ═══════════════════════════════════════════════════════
const App = {
  ws: null,
  wsAlive: false,
  reconnectTimer: null,
  isRunning: false,

  config: {},
  pendingPatch: {},
  langPresets: [],

  // Camera open/close state — default all open
  camOpen: [true, true, true],

  // ── Trajectory chart state ──
  traj: {
    // 'state' | 'action' | 'both'
    source: 'state',
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
    // Chart.js instances keyed by joint index  { 0: Chart, 1: Chart, ... }
    charts: {},
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
//  Stats rendering
// ═══════════════════════════════════════════════════════
function renderStats(data) {
  setRunningUI(data.running);

  $('val-infer-count').textContent = data.infer_count ?? '–';
  $('val-infer-time').textContent  = data.avg_infer_time != null
    ? (data.avg_infer_time * 1000).toFixed(1) + ' ms' : '–';
  $('val-traj-time').textContent   = data.avg_traj_time != null
    ? (data.avg_traj_time * 1000).toFixed(1) + ' ms' : '–';
  $('val-language').textContent    = data.language || '–';

  renderKV('config-snapshot', data.config_snapshot || {});
  renderKV('obs-act-info', { ...data.info_obs, ...data.info_act });
  renderJoints('joint-state',  data.current_state  || []);
  renderJoints('joint-action', data.current_action || []);
  $('debug-info').textContent = data.debug_info || '';

  // Feed trajectory chart
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
//  Config rendering — BASIC group for ungrouped leaf keys
// ═══════════════════════════════════════════════════════
function renderConfigTree(cfg) {
  const root = $('config-tree');
  root.innerHTML = '';
  buildTree(cfg, '', root);
}

function buildTree(obj, prefix, parentEl) {
  const basicEntries    = [];
  const subGroupEntries = [];

  for (const [key, val] of Object.entries(obj)) {
    const isGroup = val !== null && typeof val === 'object' && !Array.isArray(val);
    if (isGroup) {
      subGroupEntries.push([key, val]);
    } else if (!prefix) {
      basicEntries.push([key, val]);
    } else {
      parentEl.appendChild(createCfgRow(`${prefix}.${key}`, key, val));
    }
  }

  // BASIC group for root-level leaves
  if (basicEntries.length > 0) {
    parentEl.appendChild(buildGroup('BASIC', basicEntries.map(([k, v]) => createCfgRow(k, k, v))));
  }

  // Sub-groups
  for (const [key, val] of subGroupEntries) {
    const dotKey  = prefix ? `${prefix}.${key}` : key;
    const body    = document.createElement('div');
    body.className = 'cfg-group-body';
    buildTree(val, dotKey, body);
    // Collect leaf rows from body for the group wrapper
    parentEl.appendChild(buildGroupFromEl(key.toUpperCase(), body));
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

  let input;
  if (typeof value === 'boolean') {
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
  let parsed;
  if (typeof originalValue === 'boolean') {
    parsed = raw === 'true';
  } else if (typeof originalValue === 'number') {
    parsed = Number(raw);
    if (isNaN(parsed)) { input.style.borderColor = 'var(--danger)'; return; }
  } else if (Array.isArray(originalValue)) {
    try { parsed = JSON.parse(raw); } catch { input.style.borderColor = 'var(--danger)'; return; }
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
    if (!q) { g.style.display = ''; return; }
    const body = g.querySelector('.cfg-group-body');
    if (!body) return;
    g.style.display = [...body.querySelectorAll('.cfg-row')].some(r => r.style.display !== 'none') ? '' : 'none';
  });
}

// ═══════════════════════════════════════════════════════
//  Language presets
// ═══════════════════════════════════════════════════════
function renderLangPresets(presets) {
  App.langPresets = presets || [];
  const container = $('lang-presets');
  container.innerHTML = '';
  App.langPresets.forEach((lang, i) => {
    const chip = document.createElement('div');
    chip.className = 'lang-preset-chip';
    chip.title = lang;
    chip.textContent = `${i + 1}. ${lang.substring(0, 60)}${lang.length > 60 ? '…' : ''}`;
    chip.addEventListener('click', () => {
      $('lang-input').value = lang;
      container.querySelectorAll('.lang-preset-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
    });
    container.appendChild(chip);
  });
}

// ═══════════════════════════════════════════════════════
//  Config load
// ═══════════════════════════════════════════════════════
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
    toast('Config loaded.', 'ok', 2000);
  } catch (e) { /* already toasted */ }
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

function setupCameraPanel() {
  // Collapse button
  $('btn-visual-collapse').addEventListener('click', () => {
    const panel  = $('panel-visual');
    const layout = document.querySelector('.layout');
    if (panel.dataset.collapsed === 'true') {
      panel.dataset.collapsed = 'false';
      layout.style.gridTemplateColumns = '300px 1fr 360px';
      $('btn-visual-collapse').textContent = '▶';
    } else {
      panel.dataset.collapsed = 'true';
      layout.style.gridTemplateColumns = '300px 1fr 32px';
      $('btn-visual-collapse').textContent = '◀';
    }
  });

  // Individual open/close buttons
  for (let i = 0; i < 3; i++) {
    $(`btn-cam-${i}`).addEventListener('click', () => toggleCamera(i));
  }

  // All On / All Off
  $('btn-cam-all-open').addEventListener('click', () => {
    for (let i = 0; i < 3; i++) {
      if (!App.camOpen[i]) toggleCamera(i);
    }
  });
  $('btn-cam-all-close').addEventListener('click', () => {
    for (let i = 0; i < 3; i++) {
      if (App.camOpen[i]) toggleCamera(i);
    }
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
    preview.classList.add('open');
    statusEl.textContent = 'ON'; statusEl.classList.add('active');
    btnEl.textContent = 'Close';
    // Show placeholder until first frame arrives
    if (phEl) { phEl.style.display = ''; phEl.textContent = 'Waiting for stream…'; }
    // If there is already a pending frame, render it immediately
    if (camState.pendingData[idx]) {
      updateCameraDisplay(idx, camState.pendingData[idx]);
    }
  } else {
    preview.classList.remove('open');
    statusEl.textContent = 'OFF'; statusEl.classList.remove('active', 'error');
    btnEl.textContent = 'Open';
    // Release blob URL
    if (imgEl.src && imgEl.src.startsWith('blob:')) URL.revokeObjectURL(imgEl.src);
    imgEl.src = '';
    imgEl.classList.remove('loaded');
    if (phEl) { phEl.style.display = ''; phEl.textContent = 'Waiting for stream…'; }
  }
}

// ═══════════════════════════════════════════════════════
//  Joint Trajectory — Chart.js implementation
//  Mirrors visual/app.js architecture:
//    - Dedicated Chart per joint
//    - State (blue) + Action (red) series
//    - 50ms batch update timer
//    - Zoom/pan via chartjs-plugin-zoom
// ═══════════════════════════════════════════════════════

/* ── Build Chart.js config ── */
function makeChartConfig(jointLabel) {
  return {
    type: 'line',
    data: { datasets: [] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      parsing: false,   // we supply {x, y} objects directly
      scales: {
        x: {
          type: 'linear',
          title: { display: false },
          ticks: {
            maxTicksLimit: 6,
            color: '#656d76',
            font: { size: 9 },
          },
          grid: { color: 'rgba(208,215,222,.5)' },
        },
        y: {
          title: { display: true, text: 'rad', color: '#656d76', font: { size: 9 } },
          ticks: { maxTicksLimit: 5, color: '#656d76', font: { size: 9 } },
          grid: { color: 'rgba(208,215,222,.5)' },
        },
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: { usePointStyle: true, padding: 10, font: { size: 9 }, color: '#1f2328' },
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
  };
}

/* ── Create DOM card + Chart instance for one joint ── */
function createJointChart(jointIdx) {
  const t = App.traj;
  if (t.charts[jointIdx]) return;  // already exists

  const card = document.createElement('div');
  card.className = 'traj-chart-card';
  card.id = `traj-card-${jointIdx}`;

  const title = document.createElement('div');
  title.className = 'traj-chart-title';
  title.textContent = `Joint ${jointIdx}`;
  card.appendChild(title);

  const wrap = document.createElement('div');
  wrap.className = 'traj-chart-wrap';
  const canvas = document.createElement('canvas');
  canvas.id = `traj-cv-${jointIdx}`;
  wrap.appendChild(canvas);
  card.appendChild(wrap);

  $('traj-charts-grid').appendChild(card);

  const cfg = makeChartConfig(`Joint ${jointIdx}`);
  t.charts[jointIdx] = new Chart(canvas.getContext('2d'), cfg);
}

/* ── Remove Chart DOM card ── */
function removeJointChart(jointIdx) {
  const t = App.traj;
  if (t.charts[jointIdx]) {
    t.charts[jointIdx].destroy();
    delete t.charts[jointIdx];
  }
  const card = $(`traj-card-${jointIdx}`);
  if (card) card.remove();
}

/* ── Build joint selector chips ── */
function buildJointSelector(numJoints) {
  const t = App.traj;
  if (t.numJoints === numJoints) return;
  t.numJoints = numJoints;

  const container = $('joint-selector');
  container.innerHTML = '';
  // Default: first 4 joints selected
  t.selectedJoints = new Set([0, 1, 2, 3].filter(i => i < numJoints));

  for (let i = 0; i < numJoints; i++) {
    const chip = document.createElement('span');
    chip.className = 'joint-sel-chip' + (t.selectedJoints.has(i) ? ' active' : '');
    chip.textContent = `J${i}`;
    chip.dataset.idx = i;
    chip.addEventListener('click', () => {
      if (t.selectedJoints.has(i)) {
        t.selectedJoints.delete(i);
        chip.classList.remove('active');
        removeJointChart(i);
      } else {
        t.selectedJoints.add(i);
        chip.classList.add('active');
        createJointChart(i);
        refreshChartForJoint(i);
      }
    });
    container.appendChild(chip);
  }

  // Rebuild chart cards for initially selected joints
  $('traj-charts-grid').innerHTML = '';
  t.charts = {};
  [...t.selectedJoints].sort((a, b) => a - b).forEach(i => createJointChart(i));
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

  // Update x window (mirror visual/app.js logic)
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

/* ── Extract series data for one joint ── */
function getJointSeriesData(bufferKey, jointIdx) {
  const buf = App.traj.buffer[bufferKey];
  if (!buf || buf.length === 0) return [];
  const { xLeft: left, xRight: right } = App.traj;
  const visible = (Number.isFinite(left) && Number.isFinite(right) && right > left)
    ? buf.filter(p => p.x >= left && p.x <= right)
    : buf;
  return visible.map(p => ({ x: p.x, y: p.joints_y[jointIdx] }));
}

/* ── Refresh one Chart.js instance ── */
function refreshChartForJoint(jointIdx) {
  const t     = App.traj;
  const chart = t.charts[jointIdx];
  if (!chart) return;

  const src  = t.source;
  const datasets = [];
  let allY = [];

  if (src === 'state' || src === 'both') {
    const data = getJointSeriesData('state', jointIdx);
    datasets.push({
      label: 'State',
      data,
      borderColor: COLOR_STATE,
      backgroundColor: 'rgba(54,162,235,.08)',
      borderWidth: 1.5,
      pointRadius: 0, pointHoverRadius: 3,
      tension: 0.1, fill: false,
    });
    allY = allY.concat(data.map(p => p.y).filter(Number.isFinite));
  }

  if (src === 'action' || src === 'both') {
    const data = getJointSeriesData('action', jointIdx);
    datasets.push({
      label: 'Action',
      data,
      borderColor: COLOR_ACTION,
      backgroundColor: 'rgba(255,99,132,.08)',
      borderWidth: 1.5,
      pointRadius: 0, pointHoverRadius: 3,
      tension: 0.1, fill: false,
    });
    allY = allY.concat(data.map(p => p.y).filter(Number.isFinite));
  }

  chart.data.datasets = datasets;

  // Dynamic Y range with 10% padding (mirror visual/app.js)
  if (allY.length > 0) {
    const yMin = Math.min(...allY);
    const yMax = Math.max(...allY);
    const pad  = (yMax - yMin) * 0.1 || 0.1;
    chart.options.scales.y.min = yMin - pad;
    chart.options.scales.y.max = yMax + pad;
  } else {
    chart.options.scales.y.min = undefined;
    chart.options.scales.y.max = undefined;
  }

  // Sync X window
  const { xLeft, xRight } = t;
  if (Number.isFinite(xLeft) && Number.isFinite(xRight) && xRight > xLeft) {
    chart.options.scales.x.min = xLeft;
    chart.options.scales.x.max = xRight;
  } else {
    chart.options.scales.x.min = undefined;
    chart.options.scales.x.max = undefined;
  }

  chart.update('none');
}

/* ── Batch update timer (50 ms, 20 FPS) ── */
function startTrajUpdateTimer() {
  App.traj.updateTimer = setInterval(() => {
    if (!App.traj.dirty || App.traj.paused) return;
    const now = Date.now();
    if (now - App.traj.lastUpdateAt < CHART_UPDATE_MS) return;
    [...App.traj.selectedJoints].forEach(i => refreshChartForJoint(i));
    App.traj.dirty = false;
    App.traj.lastUpdateAt = now;
  }, CHART_UPDATE_MS);
}

/* ── Wire trajectory controls ── */
function setupTrajPanel() {
  // Source buttons
  const srcBtns = { state: $('btn-traj-state'), action: $('btn-traj-action'), both: $('btn-traj-both') };
  function setSource(src) {
    App.traj.source = src;
    App.traj.dirty  = true;
    Object.entries(srcBtns).forEach(([k, btn]) => {
      btn.className = 'btn btn-xs' + (k === src ? ' btn-active' : '');
    });
  }
  $('btn-traj-state').addEventListener('click',  () => setSource('state'));
  $('btn-traj-action').addEventListener('click', () => setSource('action'));
  $('btn-traj-both').addEventListener('click',   () => setSource('both'));

  // Pause
  $('btn-traj-pause').addEventListener('click', () => {
    App.traj.paused = !App.traj.paused;
    $('btn-traj-pause').textContent = App.traj.paused ? '▶' : '⏸';
    $('btn-traj-pause').className   = 'btn btn-xs' + (App.traj.paused ? ' btn-active' : '');
  });

  // Clear
  $('btn-traj-clear').addEventListener('click', () => {
    App.traj.buffer = { state: [], action: [] };
    App.traj.stepCounter = 0;
    App.traj.xLeft = 0; App.traj.xRight = 0;
    App.traj.dirty = true;
    [...App.traj.selectedJoints].forEach(i => refreshChartForJoint(i));
  });

  // Collapse
  $('btn-traj-collapse').addEventListener('click', () => {
    const body = $('traj-body');
    const btn  = $('btn-traj-collapse');
    const collapsed = body.classList.toggle('collapsed');
    btn.textContent = collapsed ? '▲' : '▼';
  });

  // Select all / none
  $('btn-joints-all').addEventListener('click', () => {
    const t = App.traj;
    for (let i = 0; i < t.numJoints; i++) {
      if (!t.selectedJoints.has(i)) {
        t.selectedJoints.add(i);
        createJointChart(i);
        const chip = document.querySelector(`#joint-selector .joint-sel-chip[data-idx="${i}"]`);
        if (chip) chip.classList.add('active');
      }
    }
    t.dirty = true;
  });

  $('btn-joints-none').addEventListener('click', () => {
    const t = App.traj;
    [...t.selectedJoints].forEach(i => {
      removeJointChart(i);
      const chip = document.querySelector(`#joint-selector .joint-sel-chip[data-idx="${i}"]`);
      if (chip) chip.classList.remove('active');
    });
    t.selectedJoints.clear();
  });

  startTrajUpdateTimer();
}

// ═══════════════════════════════════════════════════════
//  Event wiring — config, client control, manual ctrl
// ═══════════════════════════════════════════════════════
function wireEvents() {
  // Config file bar
  $('btn-load-file').addEventListener('click', async () => {
    const path = $('conf-path').value.trim();
    if (!path) { toast('Enter a config file path.', 'warn'); return; }
    try {
      const res = await apiFetch('/api/config/load_file', { method: 'POST', body: JSON.stringify({ path }) });
      App.config = res.config || {}; App.pendingPatch = {};
      $('pending-badge').classList.add('hidden');
      renderConfigTree(App.config);
      if (App.config.language) renderLangPresets(App.config.language);
      toast('Config file loaded.', 'ok');
    } catch (e) { /* toasted */ }
  });

  $('btn-save-file').addEventListener('click', async () => {
    const path = $('conf-path').value.trim();
    if (!path) { toast('Enter a save path.', 'warn'); return; }
    try {
      await apiFetch('/api/config/save_file', { method: 'POST', body: JSON.stringify({ path }) });
      toast(`Saved to ${path}`, 'ok');
    } catch (e) { /* toasted */ }
  });

  $('btn-saveas-file').addEventListener('click', () => {
    $('saveas-path').value = $('conf-path').value || 'conf/my_config.py';
    $('modal-saveas').classList.remove('hidden');
  });
  $('btn-saveas-confirm').addEventListener('click', async () => {
    const path = $('saveas-path').value.trim();
    if (!path) return;
    $('modal-saveas').classList.add('hidden');
    try {
      await apiFetch('/api/config/save_file', { method: 'POST', body: JSON.stringify({ path }) });
      $('conf-path').value = path; toast(`Saved as ${path}`, 'ok');
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
    const layout = document.querySelector('.layout');
    if (panel.classList.toggle('collapsed')) {
      layout.style.gridTemplateColumns = '32px 1fr 360px';
      $('btn-config-collapse').textContent = '▶';
    } else {
      layout.style.gridTemplateColumns = '300px 1fr 360px';
      $('btn-config-collapse').textContent = '◀';
    }
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

  // Language
  $('btn-set-lang').addEventListener('click', async () => {
    const lang = $('lang-input').value.trim();
    if (!lang) { toast('Enter a language instruction.', 'warn'); return; }
    await sendCommand('set_language', { language: lang });
    toast('Language updated & robot reset.', 'info');
  });
  $('lang-input').addEventListener('keydown', e => { if (e.key === 'Enter') $('btn-set-lang').click(); });

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
  connectWS();
  startStatusPoll();
  loadConfigFromServer();
});
