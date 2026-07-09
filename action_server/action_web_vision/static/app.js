/**
 * Action Web Vision — Main Application Logic
 */
'use strict';

const $ = id => document.getElementById(id);

// ═══════════════════════════════════════════════════════
//  WebSocket (port 9000) — camera + state + stats
// ═══════════════════════════════════════════════════════
function connectWS() {
  if (App.ws && App.ws.readyState <= 1) return;
  App.ws = new WebSocket(WS_URL);

  clearTimeout(App.wsConnectTimeoutTimer);
  App.wsConnectTimeoutTimer = setTimeout(() => {
    if (App.ws && App.ws.readyState === WebSocket.CONNECTING) {
      try { App.ws.close(); } catch (_) {}
    }
  }, WS_CONNECT_TIMEOUT_MS);

  App.ws.onopen = () => {
    clearTimeout(App.wsConnectTimeoutTimer);
    App.wsAlive = true;
    updateWSIndicator(true);
    clearTimeout(App.reconnectTimer);
    App.ws._pingTimer = setInterval(() => {
      if (App.ws && App.ws.readyState === 1) App.ws.send(JSON.stringify({ type: 'ping' }));
    }, 15000);
  };

  App.ws.onmessage = (ev) => {
    if (ev.data instanceof ArrayBuffer || ev.data instanceof Blob) {
      handleCameraBinary(ev.data);
      return;
    }
    try {
      handleWSMessage(JSON.parse(ev.data));
    } catch (e) { /* ignore */ }
  };

  App.ws.onclose = () => {
    clearTimeout(App.wsConnectTimeoutTimer);
    App.wsAlive = false;
    updateWSIndicator(false);
    clearInterval(App.ws._pingTimer);
    App.reconnectTimer = setTimeout(connectWS, RECONNECT);
  };

  App.ws.onerror = () => { try { App.ws.close(); } catch (_) {} };
}

function updateWSIndicator(connected) {
  const el = $('ws-indicator');
  if (el) el.className = `ws-dot ${connected ? 'connected' : 'disconnected'}`;
}

function handleWSMessage(msg) {
  switch (msg.type) {
    case 'joint_data':
      if (msg.data && msg.data.type === 'state' && Array.isArray(msg.data.joints_y)) {
        ingestTrajData(msg.data.joints_y, [], [], msg.data.timestamp);
        // Update task progress if present
        updateTaskProgress(msg.data.task_progress);
      }
      break;
    case 'stats':
      if (msg.data) renderStats(msg.data);
      break;
    case 'grasp_state':
      if (Array.isArray(msg.data) && msg.data.length >= 2) {
        updateGraspState(msg.data[0], msg.data[1]);
      }
      break;
    case 'pong':
      break;
  }
}

// ═══════════════════════════════════════════════════════
//  Camera binary frame decoding
// ═══════════════════════════════════════════════════════
async function handleCameraBinary(raw) {
  try {
    const arrayBuffer = raw instanceof Blob ? await raw.arrayBuffer() : raw;
    if (!(arrayBuffer instanceof ArrayBuffer) || arrayBuffer.byteLength < 4) return;
    const dataView = new DataView(arrayBuffer);
    const headerLength = dataView.getUint32(0, false);
    if (headerLength <= 0 || (4 + headerLength) > arrayBuffer.byteLength) return;
    const headerBytes = new Uint8Array(arrayBuffer, 4, headerLength);
    const header = JSON.parse(new TextDecoder().decode(headerBytes));
    if (header.type !== 'camera_data_binary') return;

    const payloadStart = 4 + headerLength;
    const declaredSize = Number(header.data_size);
    const payloadEnd = Number.isFinite(declaredSize) && declaredSize > 0
      ? Math.min(arrayBuffer.byteLength, payloadStart + declaredSize)
      : arrayBuffer.byteLength;
    if (payloadEnd <= payloadStart) return;
    const imageData = new Uint8Array(arrayBuffer.slice(payloadStart, payloadEnd));

    const cameraId = header.camera_id;
    if (cameraId === undefined || cameraId === null) return;
    if (!App.camOpen[cameraId]) return;
    App.pendingFrames[cameraId] = imageData;
    App.pendingUpdate = true;
  } catch (e) { /* ignore */ }
}

function renderCameraFrames() {
  if (!App.pendingUpdate) return;
  Object.keys(App.pendingFrames).forEach(idx => {
    const i = Number(idx);
    if (!App.camOpen[i]) return;
    updateCameraDisplay(i, App.pendingFrames[i]);
  });
  App.pendingUpdate = false;
}

function startCameraRenderLoop() {
  setInterval(renderCameraFrames, 33); // ~30 FPS
}

// ── Camera aspect ratio ──
function updateCameraAspectRatio(idx, width, height) {
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) return;
  const preview = $(`cam-preview-${idx}`);
  if (!preview) return;
  preview.style.aspectRatio = `${width} / ${height}`;
}

function updateCameraDisplay(idx, imageBytes) {
  const imgEl = $(`cam-img-${idx}`);
  const phEl = $(`cam-placeholder-${idx}`);
  if (!imgEl) return;
  const blob = new Blob([imageBytes], { type: 'image/jpeg' });
  const blobUrl = URL.createObjectURL(blob);
  const tmp = new Image();
  tmp.onload = () => {
    updateCameraAspectRatio(idx, tmp.naturalWidth, tmp.naturalHeight);
    if (imgEl.src && imgEl.src.startsWith('blob:')) URL.revokeObjectURL(imgEl.src);
    imgEl.src = blobUrl;
    imgEl.classList.add('loaded');
    if (phEl) phEl.style.display = 'none';
    const statusEl = $(`cam-status-${idx}`);
    if (statusEl) { statusEl.textContent = 'ON'; statusEl.classList.add('active'); statusEl.classList.remove('error'); }
  };
  tmp.onerror = () => URL.revokeObjectURL(blobUrl);
  tmp.src = blobUrl;
}

// ═══════════════════════════════════════════════════════
//  VisualizeServer WebSocket (port 8765) — action curves
// ═══════════════════════════════════════════════════════
function connectCamWS() {
  if (App.camWs && App.camWs.readyState <= 1) return;
  App.camWs = new WebSocket(CAM_WS_URL);
  App.camWs.binaryType = 'arraybuffer';

  clearTimeout(App.camWsConnectTimeoutTimer);
  App.camWsConnectTimeoutTimer = setTimeout(() => {
    if (App.camWs && App.camWs.readyState === WebSocket.CONNECTING) {
      try { App.camWs.close(); } catch (_) {}
    }
  }, CAM_WS_CONNECT_TIMEOUT_MS);

  App.camWs.onopen = () => {
    clearTimeout(App.camWsConnectTimeoutTimer);
    App.camWsAlive = true;
    clearTimeout(App.camWsReconnectTimer);
    updateCamWSIndicator(true);
  };

  App.camWs.onmessage = (ev) => {
    if (ev.data instanceof ArrayBuffer || ev.data instanceof Blob) return; // ignore cam binary from 8765
    try {
      handleCamWSMessage(JSON.parse(ev.data));
    } catch (e) { /* ignore */ }
  };

  App.camWs.onclose = () => {
    clearTimeout(App.camWsConnectTimeoutTimer);
    App.camWsAlive = false;
    updateCamWSIndicator(false);
    App.camWsReconnectTimer = setTimeout(connectCamWS, CAM_WS_RECONNECT);
  };

  App.camWs.onerror = () => { try { App.camWs.close(); } catch (_) {} };
}

function updateCamWSIndicator(alive) {
  const el = $('cam-ws-indicator');
  if (el) el.className = `ws-dot ${alive ? 'connected' : 'disconnected'}`;
}

function handleCamWSMessage(msg) {
  if (!msg || msg.type !== 'joint_data' || !msg.data) return;
  const { tab, type, joints_y, timestamp } = msg.data;
  if (tab !== 'position' || !Array.isArray(joints_y) || joints_y.length === 0) return;
  if (type === 'action_fitted') {
    ingestTrajData([], joints_y, [], timestamp);
  } else if (type === 'action_raw' || type === 'origin') {
    ingestTrajData([], [], joints_y, timestamp);
  } else if (type === 'state') {
    // ignore state from 8765 (already have from 9000)
  }
}

// ═══════════════════════════════════════════════════════
//  Task progress bar
// ═══════════════════════════════════════════════════════
const _tpFill = () => $('task-progress-fill');
const _tpVal  = () => $('task-progress-value');

function updateTaskProgress(rawProgress) {
  const fillEl = _tpFill();
  const valueEl = _tpVal();
  if (!fillEl || !valueEl) return;

  const parsed = Number(rawProgress);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    fillEl.style.width = '0%';
    valueEl.textContent = '0.0%';
    return;
  }

  const clamped = Math.max(0, Math.min(1, parsed));
  const pct = (clamped * 100).toFixed(1);
  fillEl.style.width = `${pct}%`;
  valueEl.textContent = `${pct}%`;
}

// ═══════════════════════════════════════════════════════
//  Stats rendering
// ═══════════════════════════════════════════════════════
function renderStats(data) {
  const cpuVal = Number(data.cpu_usage);
  const gpuVal = Number(data.gpu_usage);
  const memVal = Number(data.mem_usage);
  const bwVal = Number(data.bandwidth_m);
  setResourceText($('val-cpu-usage'), 'CPU', cpuVal, '%');
  setResourceText($('val-gpu-usage'), 'GPU', gpuVal, '%');
  setResourceText($('val-mem-usage'), 'MEM', memVal, '%');
  setResourceText($('val-bw-usage'), 'BW', bwVal, 'M');
}

function setResourceText(el, label, value, unit) {
  if (!el) return;
  if (Number.isFinite(value)) {
    el.innerHTML = `<span class="resource-label">${label}</span><span class="resource-value">${value.toFixed(1)}${unit}</span>`;
  } else {
    el.innerHTML = `<span class="resource-label">${label}</span><span class="resource-value">--</span>`;
  }
}

// ═══════════════════════════════════════════════════════
//  Grasp state display — panel cards below joint state
// ═══════════════════════════════════════════════════════
function updateGraspState(leftGrasping, rightGrasping) {
  _setGraspCard('grasp-left-card',  'grasp-left-indicator',  'grasp-left-text',  leftGrasping);
  _setGraspCard('grasp-right-card', 'grasp-right-indicator', 'grasp-right-text', rightGrasping);
}

function _setGraspCard(cardId, indicatorId, textId, grasping) {
  const card  = $(cardId);
  const dot   = $(indicatorId);
  const txt   = $(textId);
  if (!card || !dot || !txt) return;
  if (grasping) {
    card.classList.add('grasping');
    dot.classList.add('grasping');
    txt.textContent = 'GRASPING';
  } else {
    card.classList.remove('grasping');
    dot.classList.remove('grasping');
    txt.textContent = 'IDLE';
  }
}

// ═══════════════════════════════════════════════════════
//  Joint state display — init once, update text only
// ═══════════════════════════════════════════════════════
const _jcValRefs = { armL: [], armR: [], handL: [], handR: [] };
let _jcInited = false;

function _initJointChips() {
  if (_jcInited) return;
  _jcInited = true;
  const groups = [
    { el: $('joint-state-arm-l'),  refs: _jcValRefs.armL,  prefix: 'L',  count: 7, offset: 0 },
    { el: $('joint-state-arm-r'),  refs: _jcValRefs.armR,  prefix: 'R',  count: 7, offset: 0 },
    { el: $('joint-state-hand-l'), refs: _jcValRefs.handL, prefix: 'LH', count: 6, offset: 0 },
    { el: $('joint-state-hand-r'), refs: _jcValRefs.handR, prefix: 'RH', count: 6, offset: 0 },
  ];
  for (const g of groups) {
    if (!g.el) continue;
    g.el.innerHTML = '';
    for (let i = 0; i < g.count; i++) {
      const chip = document.createElement('div');
      chip.className = 'joint-chip';
      const lbl = document.createElement('span');
      lbl.className = 'jc-label';
      lbl.textContent = `${g.prefix}${i}:`;
      const val = document.createElement('span');
      val.className = 'jc-val';
      val.textContent = '--';
      chip.appendChild(lbl);
      chip.appendChild(val);
      g.el.appendChild(chip);
      g.refs.push(val);
    }
  }
}

function renderJointState(stateVals) {
  if (!stateVals) return;
  _initJointChips();
  // Arm joints: indices 0-13
  if (stateVals.length >= 14) {
    for (let i = 0; i < 7; i++) {
      const v = typeof stateVals[i] === 'number' ? stateVals[i].toFixed(4) : '--';
      if (_jcValRefs.armL[i]) _jcValRefs.armL[i].textContent = v;
    }
    for (let i = 7; i < 14; i++) {
      const v = typeof stateVals[i] === 'number' ? stateVals[i].toFixed(4) : '--';
      if (_jcValRefs.armR[i - 7]) _jcValRefs.armR[i - 7].textContent = v;
    }
  }
  // Hand joints: indices 14-25
  if (stateVals.length >= 26) {
    for (let i = 14; i < 20; i++) {
      const v = typeof stateVals[i] === 'number' ? stateVals[i].toFixed(4) : '--';
      if (_jcValRefs.handL[i - 14]) _jcValRefs.handL[i - 14].textContent = v;
    }
    for (let i = 20; i < 26; i++) {
      const v = typeof stateVals[i] === 'number' ? stateVals[i].toFixed(4) : '--';
      if (_jcValRefs.handR[i - 20]) _jcValRefs.handR[i - 20].textContent = v;
    }
  }
}

// ═══════════════════════════════════════════════════════
//  Trajectory chart — Chart.js implementation
// ═══════════════════════════════════════════════════════
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
          title: { display: true, text: 'Time (s)', color: '#aaa', font: { size: 10 } },
          ticks: { maxTicksLimit: 8, color: '#888', font: { size: 9 } },
          grid: { color: 'rgba(255,255,255,.06)' },
        },
        y: {
          title: { display: true, text: 'rad', color: '#aaa', font: { size: 10 } },
          ticks: { maxTicksLimit: 6, color: '#888', font: { size: 9 } },
          grid: { color: 'rgba(255,255,255,.06)' },
        },
      },
      plugins: {
        legend: {
          display: true, position: 'top',
          labels: {
            usePointStyle: true, pointStyle: 'line', padding: 4,
            font: { size: 9 }, color: '#ccc',
            boxWidth: 16,
          },
        },
        tooltip: { mode: 'index', intersect: false },
      },
      interaction: { intersect: false, mode: 'index' },
    },
  });
}

function buildJointSelector() {
  const t = App.traj;
  const rowL = $('joint-row-l');
  const rowR = $('joint-row-r');
  if (!rowL || !rowR) return;
  rowL.innerHTML = '';
  rowR.innerHTML = '';
  for (let i = 0; i < 14; i++) {
    const chip = document.createElement('span');
    const color = JOINT_COLORS[i];
    chip.className = 'joint-sel-chip' + (t.selectedJoints.has(i) ? ' active' : '');
    chip.textContent = i < 7 ? `L${i}` : `R${i - 7}`;
    chip.dataset.idx = i;
    applyChipColor(chip, t.selectedJoints.has(i), color);
    chip.addEventListener('click', () => {
      if (t.selectedJoints.has(i)) { t.selectedJoints.delete(i); chip.classList.remove('active'); applyChipColor(chip, false, color); }
      else { t.selectedJoints.add(i); chip.classList.add('active'); applyChipColor(chip, true, color); }
      refreshUnifiedChart();
    });
    (i < 7 ? rowL : rowR).appendChild(chip);
  }
  refreshUnifiedChart();
}

function applyChipColor(chip, active, color) {
  if (active) {
    chip.style.borderColor = color;
    chip.style.color = color;
  } else {
    chip.style.borderColor = '';
    chip.style.color = '';
  }
}

// ═══════════════════════════════════════════════════════
//  Hand trajectory chart — separate from arm chart
// ═══════════════════════════════════════════════════════
function createHandChart() {
  const ht = App.handTraj;
  if (ht.chart) return;
  const canvas = $('hand-traj-canvas');
  if (!canvas) return;
  ht.chart = new Chart(canvas.getContext('2d'), {
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
          title: { display: true, text: 'Time (s)', color: '#aaa', font: { size: 10 } },
          ticks: { maxTicksLimit: 8, color: '#888', font: { size: 9 } },
          grid: { color: 'rgba(255,255,255,.06)' },
        },
        y: {
          title: { display: true, text: 'Hand Pos', color: '#aaa', font: { size: 10 } },
          ticks: { maxTicksLimit: 6, color: '#888', font: { size: 9 } },
          grid: { color: 'rgba(255,255,255,.06)' },
        },
      },
      plugins: {
        legend: {
          display: true, position: 'top',
          labels: {
            usePointStyle: true, pointStyle: 'line', padding: 4,
            font: { size: 9 }, color: '#ccc', boxWidth: 16,
          },
        },
        tooltip: { mode: 'index', intersect: false },
      },
      interaction: { intersect: false, mode: 'index' },
    },
  });
}

function buildHandJointSelector() {
  const ht = App.handTraj;
  const rowL = $('hand-joint-row-l');
  const rowR = $('hand-joint-row-r');
  if (!rowL || !rowR) return;
  rowL.innerHTML = '';
  rowR.innerHTML = '';
  // Hand joints: indices 14-25 (LH0-LH5=14-19, RH0-RH5=20-25)
  for (let i = 14; i < 26; i++) {
    const chip = document.createElement('span');
    const localIdx = i - 14; // 0-11 for color lookup
    const color = HAND_JOINT_COLORS[localIdx];
    chip.className = 'joint-sel-chip' + (ht.selectedJoints.has(i) ? ' active' : '');
    chip.textContent = i < 20 ? `LH${i - 14}` : `RH${i - 20}`;
    chip.dataset.idx = i;
    applyChipColor(chip, ht.selectedJoints.has(i), color);
    chip.addEventListener('click', () => {
      if (ht.selectedJoints.has(i)) { ht.selectedJoints.delete(i); chip.classList.remove('active'); applyChipColor(chip, false, color); }
      else { ht.selectedJoints.add(i); chip.classList.add('active'); applyChipColor(chip, true, color); }
      refreshHandChart();
    });
    (i < 20 ? rowL : rowR).appendChild(chip);
  }
  refreshHandChart();
}

function refreshHandChart() {
  const t = App.traj;
  const ht = App.handTraj;
  if (!ht.chart) return;
  const src = t.source;
  const datasets = [];
  let yMin = Number.POSITIVE_INFINITY;
  let yMax = Number.NEGATIVE_INFINITY;

  const sorted = [...ht.selectedJoints].sort((a, b) => a - b);
  if (sorted.length === 0 || src.size === 0) {
    ht.chart.data.datasets = [];
    ht.chart.update('none');
    return;
  }

  for (const jointIdx of sorted) {
    const localIdx = jointIdx - 14;
    const color = HAND_JOINT_COLORS[localIdx] || 'rgb(100,100,100)';
    const label = jointIdx < 20 ? `LH${jointIdx - 14}` : `RH${jointIdx - 20}`;
    const alpha = color.replace('rgb(', 'rgba(').replace(')', ', 0.08)');

    if (src.has('state')) {
      const data = getJointSeriesData('state', jointIdx);
      datasets.push({
        label: label + ' (S)', data,
        borderColor: color, backgroundColor: alpha,
        borderWidth: 1.5, borderDash: [1, 3],
        pointRadius: 0, pointHoverRadius: 3, tension: 0.1, fill: false,
      });
      for (let i = 0, len = data.length; i < len; i += 1) {
        const y = data[i].y;
        if (Number.isFinite(y)) {
          if (y < yMin) yMin = y;
          if (y > yMax) yMax = y;
        }
      }
    }
    if (src.has('action_fitted')) {
      const data = getJointSeriesData('action_fitted', jointIdx);
      datasets.push({
        label: label + ' (AF)', data,
        borderColor: color, backgroundColor: alpha,
        borderWidth: 2, borderDash: [],
        pointRadius: 0, pointHoverRadius: 3, tension: 0.1, fill: false,
      });
      for (let i = 0, len = data.length; i < len; i += 1) {
        const y = data[i].y;
        if (Number.isFinite(y)) {
          if (y < yMin) yMin = y;
          if (y > yMax) yMax = y;
        }
      }
    }
    if (src.has('action_raw')) {
      const data = getJointSeriesData('action_raw', jointIdx);
      datasets.push({
        label: label + ' (AR)', data,
        borderColor: color, backgroundColor: alpha,
        borderWidth: 1, borderDash: [4, 3],
        pointRadius: 0, pointHoverRadius: 3, tension: 0.1, fill: false,
      });
      for (let i = 0, len = data.length; i < len; i += 1) {
        const y = data[i].y;
        if (Number.isFinite(y)) {
          if (y < yMin) yMin = y;
          if (y > yMax) yMax = y;
        }
      }
    }
  }

  ht.chart.data.datasets = datasets;

  // Dynamic Y range with 10% padding
  if (yMin !== Number.POSITIVE_INFINITY && yMax !== Number.NEGATIVE_INFINITY) {
    const pad = (yMax - yMin) * 0.1 || 0.1;
    ht.chart.options.scales.y.min = yMin - pad;
    ht.chart.options.scales.y.max = yMax + pad;
  } else {
    ht.chart.options.scales.y.min = undefined;
    ht.chart.options.scales.y.max = undefined;
  }

  const { xLeft, xRight } = t;
  if (Number.isFinite(xLeft) && Number.isFinite(xRight) && xRight > xLeft) {
    ht.chart.options.scales.x.min = xLeft;
    ht.chart.options.scales.x.max = xRight;
  }

  ht.chart.update('none');
}

function ingestTrajData(stateArr, actionFittedArr, actionRawArr = [], timestampSec = null) {
  const t = App.traj;
  if (stateArr.length === 0 && actionFittedArr.length === 0 && actionRawArr.length === 0) return;

  const nowSec = Number.isFinite(Number(timestampSec)) ? Number(timestampSec) : (Date.now() / 1000);
  if (t.startTimeSec == null) t.startTimeSec = nowSec;
  let x = nowSec - t.startTimeSec;
  if (!Number.isFinite(x) || x < 0) x = t.lastX;
  if (x < t.lastX) x = t.lastX;
  t.lastX = x;

  if (stateArr.length > 0) {
    t.buffer.state.push({ x, joints_y: stateArr.slice() });
    trimBuffer('state', x);
    // Also update joint state display
    renderJointState(stateArr);
  }
  if (actionFittedArr.length > 0) {
    t.buffer.action_fitted.push({ x, joints_y: actionFittedArr.slice() });
    trimBuffer('action_fitted', x);
    // Auto-show action curves when data arrives
    t.source.add('action_fitted');
    syncSourceButtonUI();
  }
  if (actionRawArr.length > 0) {
    t.buffer.action_raw.push({ x, joints_y: actionRawArr.slice() });
    trimBuffer('action_raw', x);
    t.source.add('action_raw');
    syncSourceButtonUI();
  }

  if (t.source.size === 0) return;
  recomputeXWindow();
  t.dirty = true;
  App.handTraj.dirty = true;
}

function trimBuffer(key, currentX) {
  const t = App.traj;
  const buf = t.buffer[key];
  const cutoff = currentX - t.windowSpanSec * 2;
  while (buf.length > 0 && buf[0].x < cutoff) buf.shift();
  if (buf.length > TRAJ_BUFFER_HARD_MAX_POINTS) buf.splice(0, buf.length - TRAJ_BUFFER_HARD_MAX_POINTS);
}

function recomputeXWindow() {
  const t = App.traj;
  const candidates = [];
  ['state', 'action_fitted', 'action_raw'].forEach(k => {
    const buf = t.buffer[k];
    if (buf && buf.length > 0) candidates.push(buf[buf.length - 1].x);
  });
  if (!candidates.length) return;
  t.xRight = Math.max(...candidates);
  t.xLeft = Math.max(0, t.xRight - t.windowSpanSec);
}

function getJointSeriesData(bufferKey, jointIdx) {
  const buf = App.traj.buffer[bufferKey];
  if (!buf || buf.length === 0) return [];
  const { xLeft, xRight } = App.traj;
  let start = 0, end = buf.length;
  if (Number.isFinite(xLeft) && Number.isFinite(xRight) && xRight > xLeft) {
    while (start < buf.length && buf[start].x < xLeft) start++;
    while (end > start && buf[end - 1].x > xRight) end--;
  }
  const len = end - start;
  if (len <= 0) return [];
  if (len <= TRAJ_RENDER_POINT_MAX) {
    const out = new Array(len);
    for (let i = 0; i < len; i++) out[i] = { x: buf[start + i].x, y: buf[start + i].joints_y[jointIdx] };
    return out;
  }
  const step = Math.ceil(len / TRAJ_RENDER_POINT_MAX);
  const out = [];
  for (let i = 0; i < len; i += step) out.push({ x: buf[start + i].x, y: buf[start + i].joints_y[jointIdx] });
  return out;
}

function refreshUnifiedChart() {
  const t = App.traj;
  if (!t.chart) return;
  const src = t.source;
  const datasets = [];
  let yMin = Number.POSITIVE_INFINITY;
  let yMax = Number.NEGATIVE_INFINITY;

  const sorted = [...t.selectedJoints].sort((a, b) => a - b);
  if (sorted.length === 0 || src.size === 0) {
    t.chart.data.datasets = [];
    t.chart.update('none');
    return;
  }

  for (const jointIdx of sorted) {
    const color = JOINT_COLORS[jointIdx] || 'rgb(100,100,100)';
    const label = jointIdx < 7 ? `L${jointIdx}` : `R${jointIdx - 7}`;
    const alpha = color.replace('rgb(', 'rgba(').replace(')', ', 0.08)');

    if (src.has('state')) {
      const data = getJointSeriesData('state', jointIdx);
      datasets.push({
        label: label + ' (S)', data,
        borderColor: color, backgroundColor: alpha,
        borderWidth: 1.5, borderDash: [1, 3],
        pointRadius: 0, pointHoverRadius: 3, tension: 0.1, fill: false,
      });
      for (let i = 0, len = data.length; i < len; i += 1) {
        const y = data[i].y;
        if (Number.isFinite(y)) {
          if (y < yMin) yMin = y;
          if (y > yMax) yMax = y;
        }
      }
    }
    if (src.has('action_fitted')) {
      const data = getJointSeriesData('action_fitted', jointIdx);
      datasets.push({
        label: label + ' (AF)', data,
        borderColor: color, backgroundColor: alpha,
        borderWidth: 2, borderDash: [],
        pointRadius: 0, pointHoverRadius: 3, tension: 0.1, fill: false,
      });
      for (let i = 0, len = data.length; i < len; i += 1) {
        const y = data[i].y;
        if (Number.isFinite(y)) {
          if (y < yMin) yMin = y;
          if (y > yMax) yMax = y;
        }
      }
    }
    if (src.has('action_raw')) {
      const data = getJointSeriesData('action_raw', jointIdx);
      datasets.push({
        label: label + ' (AR)', data,
        borderColor: color, backgroundColor: alpha,
        borderWidth: 1, borderDash: [4, 3],
        pointRadius: 0, pointHoverRadius: 3, tension: 0.1, fill: false,
      });
      for (let i = 0, len = data.length; i < len; i += 1) {
        const y = data[i].y;
        if (Number.isFinite(y)) {
          if (y < yMin) yMin = y;
          if (y > yMax) yMax = y;
        }
      }
    }
  }

  t.chart.data.datasets = datasets;

  // Dynamic Y range with 10% padding
  if (yMin !== Number.POSITIVE_INFINITY && yMax !== Number.NEGATIVE_INFINITY) {
    const pad = (yMax - yMin) * 0.1 || 0.1;
    t.chart.options.scales.y.min = yMin - pad;
    t.chart.options.scales.y.max = yMax + pad;
  } else {
    t.chart.options.scales.y.min = undefined;
    t.chart.options.scales.y.max = undefined;
  }

  const { xLeft, xRight } = t;
  if (Number.isFinite(xLeft) && Number.isFinite(xRight) && xRight > xLeft) {
    t.chart.options.scales.x.min = xLeft;
    t.chart.options.scales.x.max = xRight;
  }

  t.chart.update('none');
}

function startTrajUpdateTimer() {
  if (App.traj.updateTimer) clearInterval(App.traj.updateTimer);
  App.traj.updateTimer = setInterval(() => {
    if (!App.traj.dirty && !App.handTraj.dirty) return;
    const now = Date.now();
    if (now - App.traj.lastUpdateAt < App.traj.updateIntervalMs) return;
    if (App.traj.dirty) {
      refreshUnifiedChart();
      App.traj.dirty = false;
    }
    if (App.handTraj.dirty) {
      refreshHandChart();
      App.handTraj.dirty = false;
    }
    App.traj.lastUpdateAt = now;
    App.handTraj.lastUpdateAt = now;
  }, App.traj.updateIntervalMs);
}

// ── Source buttons ──
function syncSourceButtonUI() {
  // Update the source checkboxes dynamically
  const s = App.traj.source;
  const stateChk = $('chk-traj-state');
  const fittedChk = $('chk-traj-action-fitted');
  const rawChk = $('chk-traj-action-raw');
  if (stateChk) stateChk.checked = s.has('state');
  if (fittedChk) fittedChk.checked = s.has('action_fitted');
  if (rawChk) rawChk.checked = s.has('action_raw');
}

// ── Camera toggle ──
function toggleCamera(idx) {
  App.camOpen[idx] = !App.camOpen[idx];
  const preview = $(`cam-preview-${idx}`);
  const statusEl = $(`cam-status-${idx}`);
  const btnEl = $(`btn-cam-${idx}`);
  if (App.camOpen[idx]) {
    if (preview) preview.classList.remove('closed');
    if (statusEl) { statusEl.textContent = 'ON'; statusEl.classList.add('active'); statusEl.classList.remove('error'); }
    if (btnEl) btnEl.textContent = 'Close';
  } else {
    if (preview) preview.classList.add('closed');
    if (statusEl) { statusEl.textContent = 'OFF'; statusEl.classList.remove('active', 'error'); }
    if (btnEl) btnEl.textContent = 'Open';
  }
}

// ═══════════════════════════════════════════════════════
//  Init
// ═══════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  // Camera toggle buttons
  for (let i = 0; i < 3; i++) {
    const btn = $(`btn-cam-${i}`);
    if (btn) btn.addEventListener('click', () => toggleCamera(i));
  }

  // Source checkboxes
  $('chk-traj-state')?.addEventListener('change', e => { if (e.target.checked) App.traj.source.add('state'); else App.traj.source.delete('state'); App.traj.dirty = true; App.handTraj.dirty = true; });
  $('chk-traj-action-fitted')?.addEventListener('change', e => { if (e.target.checked) App.traj.source.add('action_fitted'); else App.traj.source.delete('action_fitted'); App.traj.dirty = true; App.handTraj.dirty = true; });
  $('chk-traj-action-raw')?.addEventListener('change', e => { if (e.target.checked) App.traj.source.add('action_raw'); else App.traj.source.delete('action_raw'); App.traj.dirty = true; App.handTraj.dirty = true; });

  // Clear button
  $('btn-traj-clear')?.addEventListener('click', () => {
    App.traj.buffer = { state: [], action_fitted: [], action_raw: [] };
    App.traj.startTimeSec = null;
    App.traj.lastX = 0;
    App.traj.dirty = true;
    App.handTraj.dirty = true;
    refreshUnifiedChart();
    refreshHandChart();
  });

  // Joint selector all/none (arm)
  $('btn-joints-all')?.addEventListener('click', () => {
    for (let i = 0; i < 14; i++) App.traj.selectedJoints.add(i);
    document.querySelectorAll('#joint-row-l .joint-sel-chip, #joint-row-r .joint-sel-chip').forEach(c => { c.classList.add('active'); applyChipColor(c, true, JOINT_COLORS[c.dataset.idx]); });
    refreshUnifiedChart();
  });
  $('btn-joints-none')?.addEventListener('click', () => {
    for (let i = 0; i < 14; i++) App.traj.selectedJoints.delete(i);
    document.querySelectorAll('#joint-row-l .joint-sel-chip, #joint-row-r .joint-sel-chip').forEach(c => { c.classList.remove('active'); applyChipColor(c, false, ''); });
    refreshUnifiedChart();
  });

  // Hand joint selector all/none
  $('btn-hand-joints-all')?.addEventListener('click', () => {
    for (let i = 14; i < 26; i++) App.handTraj.selectedJoints.add(i);
    document.querySelectorAll('#hand-joint-row-l .joint-sel-chip, #hand-joint-row-r .joint-sel-chip').forEach(c => { c.classList.add('active'); applyChipColor(c, true, HAND_JOINT_COLORS[c.dataset.idx - 14]); });
    refreshHandChart();
  });
  $('btn-hand-joints-none')?.addEventListener('click', () => {
    for (let i = 14; i < 26; i++) App.handTraj.selectedJoints.delete(i);
    document.querySelectorAll('#hand-joint-row-l .joint-sel-chip, #hand-joint-row-r .joint-sel-chip').forEach(c => { c.classList.remove('active'); applyChipColor(c, false, ''); });
    refreshHandChart();
  });

  // Hand chart clear
  $('btn-hand-traj-clear')?.addEventListener('click', () => {
    // Share the same buffer — clear also affects arm chart
    App.traj.buffer = { state: [], action_fitted: [], action_raw: [] };
    App.traj.startTimeSec = null;
    App.traj.lastX = 0;
    App.traj.dirty = true;
    App.handTraj.dirty = true;
    refreshUnifiedChart();
    refreshHandChart();
  });

  // Window slider
  const winSlider = $('traj-window-span-slider');
  winSlider?.addEventListener('input', e => {
    App.traj.windowSpanSec = normalizeTrajWindowSpanSec(Number(e.target.value));
    $('traj-window-span-value').textContent = App.traj.windowSpanSec + 's';
    recomputeXWindow();
    App.traj.dirty = true;
  });

  createUnifiedChart();
  buildJointSelector();
  createHandChart();
  buildHandJointSelector();
  startTrajUpdateTimer();
  startCameraRenderLoop();
  connectWS();
  connectCamWS();

  // Initial sync source UI
  syncSourceButtonUI();

  // Window slider init
  if (winSlider) {
    winSlider.value = App.traj.windowSpanSec;
    $('traj-window-span-value').textContent = App.traj.windowSpanSec + 's';
  }
});
