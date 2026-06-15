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

  App.ws.onopen = () => {
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
      }
      break;
    case 'stats':
      if (msg.data) renderStats(msg.data);
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

function updateCameraDisplay(idx, imageBytes) {
  const imgEl = $(`cam-img-${idx}`);
  const phEl = $(`cam-placeholder-${idx}`);
  if (!imgEl) return;
  const blob = new Blob([imageBytes], { type: 'image/jpeg' });
  const blobUrl = URL.createObjectURL(blob);
  const tmp = new Image();
  tmp.onload = () => {
    if (imgEl.src && imgEl.src.startsWith('blob:')) URL.revokeObjectURL(imgEl.src);
    imgEl.src = blobUrl;
    imgEl.classList.add('loaded');
    if (phEl) phEl.style.display = 'none';
    const statusEl = $(`cam-status-${idx}`);
    if (statusEl) { statusEl.textContent = 'ON'; statusEl.classList.add('active'); }
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

  App.camWs.onopen = () => {
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
//  Joint state display
// ═══════════════════════════════════════════════════════
function renderJointState(stateVals) {
  if (!stateVals || stateVals.length < 14) return;
  const elArmL = $('joint-state-arm-l');
  const elArmR = $('joint-state-arm-r');
  if (!elArmL || !elArmR) return;
  elArmL.innerHTML = '';
  elArmR.innerHTML = '';
  for (let i = 0; i < 7; i++) {
    const v = typeof stateVals[i] === 'number' ? stateVals[i].toFixed(4) : '--';
    elArmL.innerHTML += `<div class="joint-chip">L${i}:<br>${v}</div>`;
  }
  for (let i = 7; i < 14; i++) {
    const v = typeof stateVals[i] === 'number' ? stateVals[i].toFixed(4) : '--';
    elArmR.innerHTML += `<div class="joint-chip">R${i - 7}:<br>${v}</div>`;
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
  const sorted = [...t.selectedJoints].sort((a, b) => a - b);
  if (sorted.length === 0 || src.size === 0) {
    t.chart.data.datasets = [];
    t.chart.update('none');
    return;
  }

  for (const jointIdx of sorted) {
    const color = JOINT_COLORS[jointIdx] || 'rgb(100,100,100)';
    const label = jointIdx < 7 ? `L${jointIdx}` : `R${jointIdx - 7}`;

    if (src.has('state')) {
      const data = getJointSeriesData('state', jointIdx);
      datasets.push({
        label: label + ' (S)', data,
        borderColor: color, borderWidth: 1.5, borderDash: [1, 3],
        pointRadius: 0, tension: 0.1, fill: false,
      });
    }
    if (src.has('action_fitted')) {
      const data = getJointSeriesData('action_fitted', jointIdx);
      datasets.push({
        label: label + ' (AF)', data,
        borderColor: color, borderWidth: 2, borderDash: [],
        pointRadius: 0, tension: 0.1, fill: false,
      });
    }
    if (src.has('action_raw')) {
      const data = getJointSeriesData('action_raw', jointIdx);
      datasets.push({
        label: label + ' (AR)', data,
        borderColor: color, borderWidth: 1, borderDash: [4, 3],
        pointRadius: 0, tension: 0.1, fill: false,
      });
    }
  }

  t.chart.data.datasets = datasets;

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
    if (!App.traj.dirty) return;
    const now = Date.now();
    if (now - App.traj.lastUpdateAt < App.traj.updateIntervalMs) return;
    refreshUnifiedChart();
    App.traj.dirty = false;
    App.traj.lastUpdateAt = now;
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
    if (statusEl) { statusEl.textContent = 'ON'; statusEl.classList.add('active'); }
    if (btnEl) btnEl.textContent = 'Close';
  } else {
    if (preview) preview.classList.add('closed');
    if (statusEl) { statusEl.textContent = 'OFF'; statusEl.classList.remove('active'); }
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
  $('chk-traj-state')?.addEventListener('change', e => { if (e.target.checked) App.traj.source.add('state'); else App.traj.source.delete('state'); App.traj.dirty = true; });
  $('chk-traj-action-fitted')?.addEventListener('change', e => { if (e.target.checked) App.traj.source.add('action_fitted'); else App.traj.source.delete('action_fitted'); App.traj.dirty = true; });
  $('chk-traj-action-raw')?.addEventListener('change', e => { if (e.target.checked) App.traj.source.add('action_raw'); else App.traj.source.delete('action_raw'); App.traj.dirty = true; });

  // Clear button
  $('btn-traj-clear')?.addEventListener('click', () => {
    App.traj.buffer = { state: [], action_fitted: [], action_raw: [] };
    App.traj.startTimeSec = null;
    App.traj.lastX = 0;
    App.traj.dirty = true;
    refreshUnifiedChart();
  });

  // Joint selector all/none
  $('btn-joints-all')?.addEventListener('click', () => {
    for (let i = 0; i < 14; i++) App.traj.selectedJoints.add(i);
    document.querySelectorAll('.joint-sel-chip').forEach(c => { c.classList.add('active'); applyChipColor(c, true, JOINT_COLORS[c.dataset.idx]); });
    refreshUnifiedChart();
  });
  $('btn-joints-none')?.addEventListener('click', () => {
    App.traj.selectedJoints.clear();
    document.querySelectorAll('.joint-sel-chip').forEach(c => { c.classList.remove('active'); applyChipColor(c, false, ''); });
    refreshUnifiedChart();
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
