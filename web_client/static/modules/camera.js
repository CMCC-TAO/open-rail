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
const CAMERA_KEY_MAP = {
  0: 'visualize.camera.open_head',
  1: 'visualize.camera.open_wrist_left',
  2: 'visualize.camera.open_wrist_right',
};

// Per-camera runtime state (mirrors visual/ latestCameraData pattern)
const camState = {
  // latest pending binary frame per camera index
  pendingData: {},      // { 0: Uint8Array, 1: Uint8Array, 2: Uint8Array }
  aspectRatioByCam: {}, // { 0: ratio, 1: ratio, 2: ratio }
  pendingUpdate: false,
  lastUpdateTime: 0,
  updateInterval: 33,
  updateTimer: null,
};

function updateCameraAspectRatio(idx, width, height) {
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) return;
  const preview = $(`cam-preview-${idx}`);
  if (!preview) return;

  const ratio = width / height;
  const prevRatio = camState.aspectRatioByCam[idx];
  // Only update style when ratio actually changes to avoid unnecessary layout work.
  if (Number.isFinite(prevRatio) && Math.abs(prevRatio - ratio) < 0.01) return;

  camState.aspectRatioByCam[idx] = ratio;
  preview.style.aspectRatio = `${width} / ${height}`;
}

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

/** Update layout collapse classes; width and positions are fully managed in grid.css. */
function updateLayoutColumns() {
  const leftCollapsed = $('left-col').classList.contains('collapsed');
  const visualCollapsed = $('panel-visual').classList.contains('collapsed');
  const layout = document.querySelector('.layout');
  if (!layout) return;

  layout.classList.toggle('left-collapsed', leftCollapsed);
  layout.classList.toggle('right-collapsed', visualCollapsed);

  // Clear any legacy inline styles from previous implementations.
  layout.style.gridTemplateColumns = '';
  layout.style.paddingLeft = '';
  layout.style.paddingRight = '';
}

function setupCameraPanel() {
  // Collapse / expand the whole camera panel
  $('btn-visual-collapse').addEventListener('click', () => {
    const panel = $('panel-visual');
    const collapsed = panel.classList.toggle('collapsed');
    $('btn-visual-reveal').classList.toggle('hidden', !collapsed);
    $('btn-visual-collapse').classList.toggle('hidden', collapsed);
    updateLayoutColumns();
  });
  $('btn-visual-reveal').addEventListener('click', () => {
    $('panel-visual').classList.remove('collapsed');
    $('btn-visual-reveal').classList.add('hidden');
    $('btn-visual-collapse').classList.remove('hidden');
    updateLayoutColumns();
  });

  // Individual open/close buttons
  for (let i = 0; i < 3; i++) {
    $(`btn-cam-${i}`).addEventListener('click', () => {
      toggleCamera(i);
      updateAllToggleBtn();
      // schedulePersistVisualState();
    });
  }

  // All toggle: Open All (all closed) ↔ Close All (all open)
  function updateAllToggleBtn() {
    const allOn = App.camOpen.every(v => v);
    const btn = $('btn-cam-all-toggle');
    if (allOn) {
      btn.innerHTML = '<i class="fas fa-pause"></i> Close All';
      btn.className = 'btn btn-danger btn-xs';
    } else {
      btn.innerHTML = '<i class="fas fa-play"></i> Open All';
      btn.className = 'btn btn-success btn-xs';
    }
  }
  $('btn-cam-all-toggle').addEventListener('click', () => {
    const allOn = App.camOpen.every(v => v);
    for (let i = 0; i < 3; i++) {
      if (allOn && App.camOpen[i]) toggleCamera(i);
      else if (!allOn && !App.camOpen[i]) toggleCamera(i);
    }
    updateAllToggleBtn();
    // schedulePersistVisualState();
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
    updateCameraAspectRatio(idx, tmp.naturalWidth, tmp.naturalHeight);
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

function getCameraStatePatch(idx) {
  const key = CAMERA_KEY_MAP[idx];
   if (key === undefined) {
    return {};
  }
  return {
    [key]: !!App.camOpen[idx]
  };
}
async function toggleCamera(idx) {
  App.camOpen[idx] = !App.camOpen[idx];
  const preview  = $(`cam-preview-${idx}`);
  const statusEl = $(`cam-status-${idx}`);
  const btnEl    = $(`btn-cam-${idx}`);
  const imgEl    = $(`cam-img-${idx}`);
  const phEl     = $(`cam-placeholder-${idx}`);

  const patch = getCameraStatePatch(idx);
  const patchRes = await apiFetch('/api/client/config/patch', {
    method: 'POST',
    body: JSON.stringify({ patch }),
  });
  App.config = patchRes.config || App.config;

  const confRes = await apiFetch('/api/client/config/path');
  if (confRes.path) {
    await apiFetch('/api/client/config/save', {
      method: 'POST',
      body: JSON.stringify({ path: confRes.path }),
    });
  }
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

