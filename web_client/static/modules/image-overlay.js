const OVERLAY_CAMERA_KEYS = ['cam.head', 'cam.hand_left', 'cam.hand_right'];
const imageOverlayState = {
  selection: null,
  requestId: 0,
  retryTimer: null,
  indices: [],
  cameras: [],
  status: '',
  capturing: false,
};

function getImageOverlaySettings(cfg = App.config) {
  const defaults = { path: 'data/recording', index: 0, opacity: 50, enable: false };
  const settings = { ...defaults, ...cfg?.record?.image_overlay };
  for (const key of Object.keys(defaults)) {
    const dotKey = `record.image_overlay.${key}`;
    if (Object.hasOwn(App.pendingPatch, dotKey)) settings[key] = App.pendingPatch[dotKey];
  }
  return settings;
}

function setImageOverlayValue(key, value) {
  App.pendingPatch[`record.image_overlay.${key}`] = value;
  if (key === 'enable' && value) imageOverlayState.selection = null;
  markPending();
  syncImageOverlay();
}

function buildImageOverlayGroup(cfg) {
  const settings = getImageOverlaySettings(cfg);
  const rows = [];
  function addControl(label, input) {
    const row = document.createElement('div');
    row.className = 'cfg-row';
    const key = document.createElement('label');
    key.className = 'cfg-key';
    key.textContent = label;
    key.htmlFor = input.id;
    const value = document.createElement('div');
    value.className = 'cfg-value';
    value.appendChild(input);
    row.append(key, value);
    rows.push(row);
  }

  const path = document.createElement('input');
  path.id = 'image-overlay-path';
  path.className = 'input-text';
  path.type = 'text';
  path.value = settings.path;
  path.title = settings.path;
  path.placeholder = 'data/recording';
  path.disabled = imageOverlayState.capturing;
  path.addEventListener('change', () => setImageOverlayValue('path', path.value.trim()));
  addControl('Path', path);

  const index = document.createElement('select');
  index.id = 'image-overlay-index';
  index.className = 'input-text';
  index.title = 'Reference image index';
  index.disabled = imageOverlayState.capturing;
  index.addEventListener('change', () => setImageOverlayValue('index', Number(index.value)));
  addControl('Index', index);

  const opacity = document.createElement('input');
  opacity.id = 'image-overlay-opacity';
  opacity.className = 'input-text';
  opacity.type = 'number';
  opacity.min = '0';
  opacity.max = '100';
  opacity.step = '1';
  opacity.value = settings.opacity;
  opacity.addEventListener('input', () => {
    if (opacity.value !== '' && opacity.checkValidity()) {
      setImageOverlayValue('opacity', Number(opacity.value));
    }
  });
  addControl('Opacity (%)', opacity);

  const enable = document.createElement('input');
  enable.id = 'image-overlay-enable';
  enable.type = 'checkbox';
  enable.checked = !!settings.enable;
  enable.addEventListener('change', () => setImageOverlayValue('enable', enable.checked));
  const enableLabel = document.createElement('label');
  enableLabel.append(enable, 'Enable');

  const capture = document.createElement('button');
  capture.id = 'image-overlay-capture';
  capture.className = 'btn btn-sm';
  capture.type = 'button';
  capture.title = 'Save using the latest saved index + 1';
  capture.textContent = imageOverlayState.capturing ? 'Capturing…' : 'Capture';
  capture.disabled = imageOverlayState.capturing;
  capture.addEventListener('click', captureImageOverlay);
  const actions = document.createElement('div');
  actions.className = 'image-overlay-actions';
  actions.append(enableLabel, capture);
  rows.push(actions);

  const status = document.createElement('div');
  status.id = 'image-overlay-status';
  status.className = 'image-overlay-status';
  status.setAttribute('aria-live', 'polite');
  status.textContent = imageOverlayState.status;
  status.title = imageOverlayState.status;
  rows.push(status);
  const group = buildGroup('image overlay', rows);
  group.id = 'image-overlay-group';
  const header = group.querySelector('.cfg-group-header');
  header.addEventListener('click', () => {
    const tree = $('recording-config-tree');
    if (tree && header.classList.contains('open')) {
      tree.scrollTop += group.getBoundingClientRect().top - tree.getBoundingClientRect().top;
    }
  });
  return group;
}

function updateImageOverlayIndexOptions(settings) {
  const select = $('image-overlay-index');
  if (!select) return;
  const indices = imageOverlayState.indices;
  const choices = [...new Set([...indices, settings.index])].sort((a, b) => a - b);
  select.replaceChildren(...choices.map(value => {
    const option = document.createElement('option');
    option.value = String(value);
    option.textContent = String(value).padStart(6, '0');
    option.selected = value === settings.index;
    return option;
  }));
}

function setImageOverlayStatus(message) {
  imageOverlayState.status = message;
  const status = $('image-overlay-status');
  if (status) {
    status.textContent = message;
    status.title = message;
  }
}

function applyImageOverlay(settings) {
  OVERLAY_CAMERA_KEYS.forEach((camera, idx) => {
    const preview = $(`cam-preview-${idx}`);
    if (!preview) return;
    let image = $(`cam-overlay-${idx}`);
    if (!image) {
      image = document.createElement('img');
      image.id = `cam-overlay-${idx}`;
      image.className = 'cam-overlay';
      image.alt = '';
      image.setAttribute('aria-hidden', 'true');
      preview.appendChild(image);
    }
    image.style.opacity = String(settings.opacity / 100);
    const visible = settings.enable && imageOverlayState.cameras.includes(camera);
    image.hidden = !visible;
    if (!visible) {
      image.classList.remove('loaded');
      image.removeAttribute('src');
      delete image.dataset.source;
      return;
    }
    const query = new URLSearchParams({ path: settings.path, index: settings.index, camera });
    const source = `/api/client/overlay/image?${query}`;
    if (image.dataset.source === source) return;
    image.classList.remove('loaded');
    image.dataset.source = source;
    image.onload = () => {
      if (image.dataset.source === source) image.classList.add('loaded');
    };
    image.onerror = () => {
      if (image.dataset.source !== source) return;
      image.classList.remove('loaded');
      setImageOverlayStatus(`Failed to load ${camera}.`);
    };
    image.src = source;
  });
}

function syncImageOverlay(cfg = App.config) {
  const settings = getImageOverlaySettings(cfg);
  const selection = JSON.stringify([settings.path, settings.index]);
  if (selection !== imageOverlayState.selection) {
    imageOverlayState.selection = selection;
    imageOverlayState.indices = [];
    imageOverlayState.cameras = [];
    refreshImageOverlay(settings);
  }
  updateImageOverlayIndexOptions(settings);
  applyImageOverlay(settings);
}

async function refreshImageOverlay(settings, attempt = 0) {
  clearTimeout(imageOverlayState.retryTimer);
  imageOverlayState.retryTimer = null;
  const requestId = ++imageOverlayState.requestId;
  if (!settings.path.trim()) {
    setImageOverlayStatus('Enter an image overlay path.');
    return;
  }
  setImageOverlayStatus('Loading…');
  try {
    const query = new URLSearchParams({ path: settings.path, index: settings.index });
    const result = await apiFetch(`/api/client/overlay/frames?${query}`, {
      timeoutMs: 10000,
      suppressToast: true,
    });
    if (requestId !== imageOverlayState.requestId) return;
    imageOverlayState.indices = result.indices || [];
    imageOverlayState.cameras = result.cameras || [];
    const folder = `overlay/${String(settings.index).padStart(6, '0')}`;
    const missing = OVERLAY_CAMERA_KEYS.filter(key => !imageOverlayState.cameras.includes(key));
    setImageOverlayStatus(missing.length ? `${folder}: missing ${missing.join(', ')}` : folder);
    const current = getImageOverlaySettings();
    updateImageOverlayIndexOptions(current);
    applyImageOverlay(current);
  } catch (error) {
    if (requestId !== imageOverlayState.requestId) return;
    const retryable = error.name === 'TimeoutError' || error instanceof TypeError || error.status >= 500;
    if (retryable && attempt < 2) {
      setImageOverlayStatus(`Unable to load overlay images; retrying (${attempt + 1}/2)…`);
      imageOverlayState.retryTimer = setTimeout(() => {
        if (requestId === imageOverlayState.requestId) refreshImageOverlay(settings, attempt + 1);
      }, 1000);
    } else {
      imageOverlayState.selection = null;
      setImageOverlayStatus(error.message);
    }
  }
}

async function captureImageOverlay() {
  if (imageOverlayState.capturing) return;
  const settings = getImageOverlaySettings();
  imageOverlayState.capturing = true;
  renderRecordingConfigTree(App.config);
  try {
    const result = await apiFetch('/api/client/overlay/capture', {
      method: 'POST',
      body: JSON.stringify({ path: settings.path }),
      timeoutMs: 10000,
    });
    setConfigValueByDotKey(App.config, 'record.image_overlay.index', result.index);
    App.pendingPatch['record.image_overlay.index'] = result.index;
    markPending();
    imageOverlayState.selection = null;
    toast(`Images captured to ${result.path}.`, 'ok');
  } catch (_) { /* apiFetch reports the error */ }
  finally {
    imageOverlayState.capturing = false;
    renderRecordingConfigTree(App.config);
  }
}
