// ═══════════════════════════════════════════════════════
//  Joint Trajectory — Chart.js implementation
//  Single unified chart: all selected joints on one canvas.
//  State series = dashed line; Action series = solid line.
//  Each joint has its own colour from JOINT_COLORS palette.
//  Zoom/pan via chartjs-plugin-zoom.
// ═══════════════════════════════════════════════════════

// Default labels; runtime labels are derived from the active robot action_layout.arm.
const TRAJ_DEFAULT_JOINT_LABELS = [
  'L0','L1','L2','L3','L4','L5','L6',
  'R0','R1','R2','R3','R4','R5','R6',
];
const TRAJ_JOINT_COUNT = TRAJ_DEFAULT_JOINT_LABELS.length;

function _asInt(value, fallback = null) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.trunc(n) : fallback;
}

function _hslToRgb(h, s, l) {
  s /= 100;
  l /= 100;
  const k = n => (n + h / 30) % 12;
  const a = s * Math.min(l, 1 - l);
  const f = n => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
  return [Math.round(255 * f(0)), Math.round(255 * f(8)), Math.round(255 * f(4))];
}

function getTrajJointColor(idx) {
  const i = _asInt(idx, 0);
  if (JOINT_COLORS[i]) return JOINT_COLORS[i];
  const [r, g, b] = _hslToRgb((i * 137.508) % 360, 72, 42);
  return `rgb(${r}, ${g}, ${b})`;
}

function getTrajJointCount() {
  return Math.max(0, _asInt(App.traj.numJoints, 0));
}

function getTrajJointLabels() {
  const labels = Array.isArray(App.traj.jointLabels) ? App.traj.jointLabels : [];
  return labels.length ? labels : TRAJ_DEFAULT_JOINT_LABELS.slice();
}

function _getCfgNode(obj, key) {
  if (!obj || typeof obj !== 'object') return undefined;
  return obj[key];
}

function _resolveCurrentActionLayout(cfg = App.config) {
  const root = (cfg && typeof cfg === 'object') ? cfg : {};
  const robots = _getCfgNode(root, 'robots');
  const robotTypeRaw = _getCfgNode(robots, 'type');
  const robotType = robotTypeRaw && typeof robotTypeRaw === 'object' && 'value' in robotTypeRaw
    ? String(robotTypeRaw.value)
    : String(robotTypeRaw || '').trim();
  const robotCfg = robotType ? _getCfgNode(robots, robotType) : null;
  const robotLayout = _getCfgNode(robotCfg, 'action_layout');
  if (robotLayout && typeof robotLayout === 'object') return robotLayout;

  const rdmLayout = _getCfgNode(_getCfgNode(root, 'rdm'), 'action_layout');
  if (rdmLayout && typeof rdmLayout === 'object') return rdmLayout;

  const intraLayout = _getCfgNode(_getCfgNode(root, 'intra_chunk'), 'action_layout');
  if (intraLayout && typeof intraLayout === 'object') return intraLayout;

  return null;
}

function _normalizeActionSegment(seg) {
  if (!seg || typeof seg !== 'object') return null;
  const start = _asInt(seg.start, null);
  const end = _asInt(seg.end, null);
  if (start === null || end === null || end <= start || start < 0) return null;
  return { start, end, name: String(seg.name || 'arm') };
}

function resolveTrajActionSegment(cfg = App.config, fallbackCount = TRAJ_JOINT_COUNT) {
  const layout = _resolveCurrentActionLayout(cfg);
  if (layout) {
    const arm = _normalizeActionSegment(layout.arm);
    if (arm) return arm;

    for (const [name, seg] of Object.entries(layout)) {
      if (!seg || typeof seg !== 'object') continue;
      const normalized = _normalizeActionSegment(Object.assign({}, seg, { name }));
      const policy = String(seg?.policy || '').toLowerCase();
      if (normalized && policy === 'gradual') return normalized;
    }
  }

  const count = Math.max(0, _asInt(fallbackCount, TRAJ_JOINT_COUNT));
  return { start: 0, end: count, name: 'arm' };
}

function _makeTrajJointLabels(count) {
  const n = Math.max(0, _asInt(count, 0));
  if (n === TRAJ_DEFAULT_JOINT_LABELS.length) return TRAJ_DEFAULT_JOINT_LABELS.slice();
  if (n > 1 && n % 2 === 0) {
    const half = n / 2;
    return [
      ...Array.from({ length: half }, (_, i) => `L${i}`),
      ...Array.from({ length: half }, (_, i) => `R${i}`),
    ];
  }
  return Array.from({ length: n }, (_, i) => `J${i}`);
}

// function _defaultSelectedJoints(count) {
//   return new Set(Array.from({ length: Math.min(4, Math.max(0, count)) }, (_, i) => i));
// }

function syncTrajLayoutFromConfig(cfg = App.config, fallbackCount = TRAJ_JOINT_COUNT) {
  const t = App.traj;
  const seg = resolveTrajActionSegment(cfg, fallbackCount);
  const count = Math.max(0, seg.end - seg.start);
  const changed = t.actionStart !== seg.start || t.actionEnd !== seg.end || t.actionName !== seg.name || t.numJoints !== count;

  t.actionStart = seg.start;
  t.actionEnd = seg.end;
  t.actionName = seg.name;
  t.numJoints = count;
  t.jointLabels = _makeTrajJointLabels(count);

  // const kept = new Set([...t.selectedJoints].filter(i => Number.isInteger(i) && i >= 0 && i < count));
  // t.selectedJoints = t.jointSelectionInitialized ? kept : _defaultSelectedJoints(count);
  // t.jointSelectionInitialized = true;

  if (changed) renderJointSelector();
  return changed;
}

function _sliceTrajArray(arr) {
  if (!Array.isArray(arr) || arr.length === 0) return [];
  syncTrajLayoutFromConfig(App.config, arr.length);
  const { actionStart, actionEnd, numJoints } = App.traj;
  if (Number.isInteger(actionStart) && Number.isInteger(actionEnd) && arr.length >= actionEnd) {
    return arr.slice(actionStart, actionEnd);
  }
  return arr.slice(0, Math.min(arr.length, numJoints || arr.length));
}

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

/* ── Build joint selector chips from active robot action_layout.arm ── */
function buildJointSelector(numJoints) {
  syncTrajLayoutFromConfig(App.config, numJoints || TRAJ_JOINT_COUNT);
}

async function renderJointSelector() {
  const t = App.traj;
  const count = getTrajJointCount();
  const labels = getTrajJointLabels();
  const split = count > 1 ? Math.ceil(count / 2) : count;

  // Rows are already in HTML; insert chips BEFORE the All/None buttons
  const rowL = $('joint-row-l');
  const rowR = $('joint-row-r');
  const btnAll  = $('btn-joints-all');
  const btnNone = $('btn-joints-none');
  if (!rowL || !rowR || !btnAll || !btnNone) return;

  rowL.querySelectorAll('.joint-sel-chip').forEach(el => el.remove());
  rowR.querySelectorAll('.joint-sel-chip').forEach(el => el.remove());

  for (let i = 0; i < count; i++) {
    const chip = document.createElement('span');
    const color = getTrajJointColor(i);
    chip.className = 'joint-sel-chip' + (t.selectedJoints.has(i) ? ' active' : '');
    chip.textContent = labels[i] ?? `J${i}`;
    chip.dataset.idx = i;
    _applyChipColor(chip, t.selectedJoints.has(i), color);
    chip.addEventListener('click', async () => {
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
      const patch = {
        'visualize.trajectory.selected_joints': [...t.selectedJoints].sort((a, b) => a - b),
      };
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
      console.log('selectedJoints:', t.selectedJoints);
    });
    if (i < split) {
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
  const stateSeries = _sliceTrajArray(stateArr);
  const actionFittedSeries = _sliceTrajArray(actionFittedArr);
  const actionRawSeries = _sliceTrajArray(actionRawArr);
  const n = Math.max(stateSeries.length, actionFittedSeries.length, actionRawSeries.length);
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

  if (stateSeries.length > 0) {
    t.buffer.state.push({ x, joints_y: stateSeries });
    trimTrajBufferToMaxWindow('state', x);
  }
  if (actionFittedSeries.length > 0) {
    t.buffer.action_fitted.push({ x, joints_y: actionFittedSeries });
    trimTrajBufferToMaxWindow('action_fitted', x);
  }
  if (actionRawSeries.length > 0) {
    t.buffer.action_raw.push({ x, joints_y: actionRawSeries });
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

  const xLeft = App.traj.xLeft;
  const xRight = App.traj.xRight;
  let start = 0;
  let end = buf.length;

  if (Number.isFinite(xLeft) && Number.isFinite(xRight) && xRight > xLeft) {
    while (start < buf.length && buf[start].x < xLeft) start++;
    while (end > start && buf[end - 1].x > xRight) end--;
  }

  const len = end - start;
  if (len <= TRAJ_RENDER_POINT_MAX) {
    const out = new Array(len);
    for (let i = 0; i < len; i += 1) {
      const p = buf[start + i];
      out[i] = { x: p.x, y: p.joints_y[jointIdx] };
    }
    return out;
  }

  const step = Math.ceil(len / TRAJ_RENDER_POINT_MAX);
  const out = [];
  for (let i = 0; i < len; i += step) {
    const p = buf[start + i];
    out.push({ x: p.x, y: p.joints_y[jointIdx] });
  }
  const last = buf[end - 1];
  const lastX = out.length ? out[out.length - 1].x : null;
  if (last && lastX !== last.x) {
    out.push({ x: last.x, y: last.joints_y[jointIdx] });
  }
  return out;
}

/* ── Rebuild all datasets in the unified chart ── */
function refreshUnifiedChart() {
  const t = App.traj;
  if (!t.chart) return;

  const src = t.source;   // Set<'state'|'action_fitted'|'action_raw'>
  const datasets = [];
  let yMin = Number.POSITIVE_INFINITY;
  let yMax = Number.NEGATIVE_INFINITY;

  const sorted = [...t.selectedJoints].sort((a, b) => a - b);
  if (sorted.length === 0 || src.size === 0) {
    t.chart.data.datasets = [];
    t.chart.update('none');
    return;
  }
  const enabledSources = ['state', 'action_fitted', 'action_raw'].filter(k => src.has(k));
  const showSuffix = enabledSources.length > 1;
  const labels = getTrajJointLabels();


  for (const jointIdx of sorted) {
    const color  = getTrajJointColor(jointIdx);
    const label  = labels[jointIdx] ?? `J${jointIdx}`;
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
        label: label + (showSuffix ? ' (AF)' : ''),
        data,
        borderColor: color,
        backgroundColor: alpha,
        borderWidth: 1.5,
        borderDash: [],
        pointRadius: 0, pointHoverRadius: 3,
        tension: 0.1, fill: false,
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
        label: label + (showSuffix ? ' (AR)' : ''),
        data,
        borderColor: color,
        backgroundColor: alpha,
        borderWidth: 1.5,
        borderDash: [4, 3],
        pointRadius: 0, pointHoverRadius: 3,
        tension: 0.1, fill: false,
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

function updateCenterPanelLayoutState() {
  const centerCol = document.querySelector('.center-col');
  const langBody = $('lang-body');
  const trajBody = $('traj-body');
  if (!centerCol || !langBody || !trajBody) return;

  centerCol.classList.toggle('lang-collapsed', langBody.classList.contains('collapsed'));
  centerCol.classList.toggle('traj-collapsed', trajBody.classList.contains('collapsed'));
}

function syncCenterPanelCollapseUi() {
  const langBody = $('lang-body');
  const langBtn = $('btn-lang-collapse');
  const trajBody = $('traj-body');
  const trajBtn = $('btn-traj-collapse');

  if (langBtn && langBody) {
    const langCollapsed = langBody.classList.contains('collapsed');
    // Language panel: swap icons for Collapse/Expand as requested.
    langBtn.innerHTML = langCollapsed ? '<i class="fas fa-chevron-down"></i>' : '<i class="fas fa-chevron-up"></i>';
    langBtn.title = langCollapsed ? 'Expand' : 'Collapse';
  }

  if (trajBtn && trajBody) {
    const trajCollapsed = trajBody.classList.contains('collapsed');
    trajBtn.innerHTML = trajCollapsed ? '<i class="fas fa-chevron-up"></i>' : '<i class="fas fa-chevron-down"></i>';
    trajBtn.title = trajCollapsed ? 'Expand' : 'Collapse';
  }
}

function restoreCenterPanelsToInitialState() {
  const langBody = $('lang-body');
  const trajBody = $('traj-body');
  if (!langBody || !trajBody) return;

  langBody.classList.remove('collapsed');
  trajBody.classList.remove('collapsed');
  updateCenterPanelLayoutState();
  syncCenterPanelCollapseUi();
}

function handleCenterPanelCollapseToggle(target) {
  const langBody = $('lang-body');
  const trajBody = $('traj-body');
  if (!langBody || !trajBody) return;

  const isLangTarget = target === 'lang';
  const isTrajTarget = target === 'traj';
  if (!isLangTarget && !isTrajTarget) return;

  const targetBody = isLangTarget ? langBody : trajBody;
  const otherBody = isLangTarget ? trajBody : langBody;

  const targetCollapsed = targetBody.classList.contains('collapsed');
  const otherCollapsed = otherBody.classList.contains('collapsed');

  // 规则：当另一面板已折叠且当前面板处于展开时，点击当前面板折叠按钮 -> 恢复到初始状态（两面板都展开）。
  if (!targetCollapsed && otherCollapsed) {
    restoreCenterPanelsToInitialState();
    return;
  }

  // 其他场景：仅切换当前面板折叠状态。
  targetBody.classList.toggle('collapsed');
  updateCenterPanelLayoutState();
  syncCenterPanelCollapseUi();
}

/* ── Wire trajectory controls ── */
async function setupTrajPanel() {
  // Source checkboxes: toggle independently; all can be deselected
  const srcChecks = {
    state: $('chk-traj-state'),
    action_fitted: $('chk-traj-action-fitted'),
    action_raw: $('chk-traj-action-raw'),
  };
  const btnAllSource = $('btn-traj-all');

  async function syncSrcButtons(updateConfig = true) {
    Object.entries(srcChecks).forEach(([k, chk]) => {
      if (!chk) return;
      chk.checked = App.traj.source.has(k);
    });
    if (btnAllSource) {
      const s = App.traj.source;
      const allSelected = s.has('state') && s.has('action_fitted') && s.has('action_raw');
      btnAllSource.textContent = allSelected ? 'None' : 'All';
    }
    if (updateConfig) {
      const patch = getTrajSourceStatePatch();
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
    }
  }
  function getTrajSourceStatePatch() {
    return {
      'visualize.trajectory.source': [...App.traj.source].map(s => {
        if (s === 'action_fitted') return 'ActionFitted';
        if (s === 'action_raw') return 'ActionRaw';
        return 'State';
      }),
    };
  }
  function getTrajPlayStatePatch() {
    return {
      'visualize.trajectory.play': !App.traj.paused,
    };
  }
  function getTrajJointsStatePatch() {
    return {
      'visualize.trajectory.selected_joints': [...App.traj.selectedJoints].sort((a, b) => a - b),
    };
  }
  function getTrajWindowSpanStatePatch() {
    return {
      'visualize.trajectory.window_span_sec': normalizeTrajWindowSpanSec(App.traj.windowSpanSec, TRAJ_WINDOW_SPAN_SEC),
    };
  }
  async function setSource(src, enabled) {
    const s = App.traj.source;
    if (enabled) s.add(src);
    else s.delete(src);
    if (s.size > 0) recomputeTrajXWindow();
    App.traj.dirty = true;
    syncSrcButtons();
    refreshUnifiedChart();
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
    });
  }
  // syncSrcButtons(updateConfig=false);

  const windowSlider = $('traj-window-span-slider');
  const applyWindowSpan = (raw) => {
    const next = normalizeTrajWindowSpanSec(Number(raw), App.traj.windowSpanSec);
    App.traj.windowSpanSec = next;
    syncTrajWindowSpanUI();
    if (App.traj.source.size > 0) recomputeTrajXWindow();
    App.traj.dirty = true;
    refreshUnifiedChart();
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
      ? '<i class="fas fa-play"></i> Play'
      : '<i class="fas fa-pause"></i> Pause';
    btn.className = 'btn btn-xs btn-ctrl';
  }

  $('btn-traj-pause').addEventListener('click', () => {
    App.traj.paused = !App.traj.paused;
    syncTrajPlayButton();
    if (!App.traj.paused) {
      App.traj.dirty = true;
      refreshUnifiedChart();
    }
  });
  // syncTrajPlayButton();

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
  $('btn-traj-collapse').addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    handleCenterPanelCollapseToggle('traj');
  });

  updateCenterPanelLayoutState();
  syncCenterPanelCollapseUi();

  // Select all / none
  $('btn-joints-all').addEventListener('click', () => {
    const t = App.traj;
    for (let i = 0; i < getTrajJointCount(); i++) {
      if (!t.selectedJoints.has(i)) {
        t.selectedJoints.add(i);
        const chip = document.querySelector(`.joint-sel-chip[data-idx="${i}"]`);
        if (chip) { chip.classList.add('active'); _applyChipColor(chip, true, getTrajJointColor(i)); }
      }
    }
    t.dirty = true;
    refreshUnifiedChart();
  });

  $('btn-joints-none').addEventListener('click', () => {
    const t = App.traj;
    [...t.selectedJoints].forEach(i => {
      const chip = document.querySelector(`.joint-sel-chip[data-idx="${i}"]`);
      if (chip) { chip.classList.remove('active'); _applyChipColor(chip, false, getTrajJointColor(i)); }
    });
    t.selectedJoints.clear();
    refreshUnifiedChart();
  });

  startTrajUpdateTimer();
}
