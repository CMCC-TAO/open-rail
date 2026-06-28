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
      ? '<i class="fas fa-play"></i> Play'
      : '<i class="fas fa-pause"></i> Pause';
    // btn.className = 'btn btn-xs btn-ctrl';
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
    const body = $('traj-body');
    const langBody = $('lang-body');

    // If Language panel is collapsed while Trajectory is normal,
    // this click should restore both panels to normal size.
    if (!body.classList.contains('collapsed') && langBody.classList.contains('collapsed')) {
      langBody.classList.remove('collapsed');
      body.classList.remove('collapsed');
      updateCenterPanelLayoutState();
      syncCenterPanelCollapseUi();
      return;
    }

    body.classList.toggle('collapsed');
    updateCenterPanelLayoutState();
    syncCenterPanelCollapseUi();
  });

  updateCenterPanelLayoutState();
  syncCenterPanelCollapseUi();

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
