function syncRecordingSwitchUI() {
  const running = !!App.isRunning;
  const recording = !!App.isRecording;
  const btnStartStop = $('btn-recording-startstop');
  if (!btnStartStop) return;

  btnStartStop.disabled = !running;
  
  // Update button text/icon/style based on recording status
  if (recording) {
    btnStartStop.innerHTML = '<i class="fas fa-stop"></i> Stop';
    btnStartStop.className = 'btn btn-xs btn-danger';
  } else {
    btnStartStop.innerHTML = '<i class="fas fa-play"></i> Start';
    btnStartStop.className = 'btn btn-xs btn-success';
  }
}

function renderRecordingConfigTree(cfg = App.config) {
  const root = $('recording-config-tree');
  if (!root) return;
  root.innerHTML = '';
  const recordCfg = (cfg && typeof cfg === 'object' && cfg.record && typeof cfg.record === 'object') ? cfg.record : {};
  buildTree(recordCfg, 'record', root);
  syncRecordingSwitchUI();
}

function getRecordingSaveItems() {
  const items = [];
  if ($('chk-record-episode')?.checked) items.push('Episode');
  if ($('chk-record-expdata')?.checked) items.push('ExpData');
  return items;
}

async function stopDataRecordingIfNeeded({ silent = false, refreshList = true } = {}) {
  if (!App.isRunning || !App.isRecording) {
    syncRecordingSwitchUI();
    return false;
  }

  try {
    if (!silent) toast('Recording stopping.', 'info');
    await apiFetch('/api/client/record/stop', {
      method: 'POST',
      body: JSON.stringify({}),
    });

    App.isRecording = false;
    if (!App.config || typeof App.config !== 'object') App.config = {};
    if (!App.config.record || typeof App.config.record !== 'object') App.config.record = {};
    App.config.record.switch = false;

    renderRecordingConfigTree(App.config);
    if (!silent) toast('Recording stopped.', 'warn');
    if (refreshList) await refreshRecordingFileList();
    syncRecordingSwitchUI();
    return true;
  } catch (_) {
    syncRecordingSwitchUI();
    return false;
  }
}

function renderRecordingFileList(data) {
  const listEl = $('recording-file-list');
  const taskSel = $('recording-task-select');
  const chunkSel = $('recording-chunk-select');
  if (!listEl) return;

  const episodes = Array.isArray(data?.episodes)
    ? data.episodes
    : (Array.isArray(data?.files) ? data.files : []);
  const tasks = Array.isArray(data?.tasks) ? data.tasks : [];
  const chunks = Array.isArray(data?.chunks) ? data.chunks : [];
  const serverSelectedTask = typeof data?.selected_task === 'string' ? data.selected_task : '';
  const serverSelectedChunk = typeof data?.selected_chunk === 'string' ? data.selected_chunk : '';

  if (taskSel) {
    const prevTasks = Array.isArray(App.recordingTasksSnapshot) ? App.recordingTasksSnapshot : [];
    const prevSet = new Set(prevTasks);
    const addedTasks = tasks.filter(name => !prevSet.has(name));

    const requestedTask = String(App.recordingTask || '').trim();
    const prefixedTask = requestedTask
      ? (tasks.find(name => name === requestedTask || name.startsWith(`${requestedTask}_`)) || '')
      : '';

    const selectedTask = addedTasks.length > 0
      ? addedTasks[0]
      : (prefixedTask
        ? prefixedTask
        : (tasks.includes(serverSelectedTask) ? serverSelectedTask : (tasks[0] || '')));

    taskSel.innerHTML = tasks
      .map(name => {
        const safe = String(name)
          .replaceAll('&', '&amp;')
          .replaceAll('<', '&lt;')
          .replaceAll('>', '&gt;');
        return `<option value="${safe}">${safe}</option>`;
      })
      .join('');

    taskSel.disabled = tasks.length === 0;
    taskSel.value = selectedTask;
    App.recordingTask = selectedTask || null;
    App.recordingTasksSnapshot = tasks.slice();
  }

  if (chunkSel) {
    const prevChunks = Array.isArray(App.recordingChunksSnapshot) ? App.recordingChunksSnapshot : [];
    const prevSet = new Set(prevChunks);
    const addedChunks = chunks.filter(name => !prevSet.has(name));

    const selectedChunk = addedChunks.length > 0
      ? addedChunks[0]
      : (chunks.includes(App.recordingChunk)
        ? App.recordingChunk
        : (chunks.includes(serverSelectedChunk) ? serverSelectedChunk : (chunks[chunks.length - 1] || '')));

    chunkSel.innerHTML = chunks
      .map(name => {
        const safe = String(name)
          .replaceAll('&', '&amp;')
          .replaceAll('<', '&lt;')
          .replaceAll('>', '&gt;');
        return `<option value="${safe}">${safe}</option>`;
      })
      .join('');

    chunkSel.disabled = chunks.length === 0;
    chunkSel.value = selectedChunk;
    App.recordingChunk = selectedChunk || null;
    App.recordingChunksSnapshot = chunks.slice();
  }

  if (!episodes.length) {
    App.recordingEpisodeSnapshot = [];
    App.recordingEpisodeId = null;
    listEl.innerHTML = '<div class="recording-file-item empty">(empty)</div>';
    return;
  }

  const top = episodes.slice(0, 500);
  const episodeIds = top
    .map(ep => String(ep?.id || ep?.name || ''))
    .filter(Boolean);
  const prevEpisodeIds = Array.isArray(App.recordingEpisodeSnapshot) ? App.recordingEpisodeSnapshot : [];
  const prevEpisodeSet = new Set(prevEpisodeIds);
  const addedEpisodeIds = episodeIds.filter(id => !prevEpisodeSet.has(id));

  let selectedEpisodeId = App.recordingEpisodeId;
  if (addedEpisodeIds.length > 0) {
    selectedEpisodeId = addedEpisodeIds[0];
  } else if (!episodeIds.includes(selectedEpisodeId)) {
    selectedEpisodeId = episodeIds[0] || null;
  }
  App.recordingEpisodeId = selectedEpisodeId;
  App.recordingEpisodeSnapshot = episodeIds;

  listEl.innerHTML = top
    .map(item => {
      const id = String(item?.id || item?.name || '');
      const name = String(item?.name || id.replace(/^chunk-\d{3}\//, ''));
      const safeId = id
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;');
      const safeName = name
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;');
      const frames = Number.isFinite(Number(item?.frames)) ? Number(item.frames) : 0;
      const duration = Number.isFinite(Number(item?.duration_sec)) ? Number(item.duration_sec) : 0;
      const activeCls = id === selectedEpisodeId ? ' active' : '';
      return `<div class="recording-file-item${activeCls}" data-episode-id="${safeId}" title="${safeName}"><span class="recording-file-item-name">${safeName}</span><span class="recording-file-item-meta">${frames} | ${duration.toFixed(1)}s</span><span class="recording-file-item-actions"><button class="recording-file-item-delete" data-episode-id="${safeId}" title="Delete episode" aria-label="Delete episode"><svg class="recording-file-item-delete-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3h6l1 2h4v2H4V5h4l1-2zm-1 6h2v9H8V9zm4 0h2v9h-2V9zm4 0h2v9h-2V9z"/></svg></button></span></div>`;
    })
    .join('');

  listEl.querySelectorAll('.recording-file-item[data-episode-id]').forEach(el => {
    el.addEventListener('click', () => {
      const id = el.getAttribute('data-episode-id') || null;
      App.recordingEpisodeId = id;
      listEl.querySelectorAll('.recording-file-item.active').forEach(node => node.classList.remove('active'));
      el.classList.add('active');
    });
  });

  listEl.querySelectorAll('.recording-file-item-delete[data-episode-id]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const episodeId = btn.getAttribute('data-episode-id') || '';
      const row = btn.closest('.recording-file-item');
      if (!episodeId || !row || !row.classList.contains('active')) return;
      await deleteRecordingEpisode(episodeId);
    });
  });
}

async function deleteRecordingEpisode(episodeId) {
  if (!App.recordingTask || !episodeId) return;
  const ok = window.confirm(`Delete ${episodeId} ? This cannot be undone.`);
  if (!ok) return;

  try {
    await apiFetch('/api/client/record/delete', {
      method: 'DELETE',
      body: JSON.stringify({ task: App.recordingTask, episode_id: episodeId }),
    });
    if (App.recordingEpisodeId === episodeId) App.recordingEpisodeId = null;
    toast(`Deleted ${episodeId}.`, 'ok', 1800);
    await refreshRecordingFileList();
  } catch (_) { /* toasted */ }
}

async function refreshRecordingFileList() {
  try {
    const requestedTask = App.recordingTask;
    const requestedChunk = App.recordingChunk;
    const params = new URLSearchParams();
    if (requestedTask) params.set('task', requestedTask);
    if (requestedChunk) params.set('chunk', requestedChunk);

    const q = params.toString();
    const res = await apiFetch(`/api/client/record/episodes${q ? `?${q}` : ''}`);
    renderRecordingFileList(res);

    const changed = ((App.recordingTask || '') !== (requestedTask || '')) || ((App.recordingChunk || '') !== (requestedChunk || ''));
    if (changed) {
      const params2 = new URLSearchParams();
      if (App.recordingTask) params2.set('task', App.recordingTask);
      if (App.recordingChunk) params2.set('chunk', App.recordingChunk);
      const q2 = params2.toString();
      const res2 = await apiFetch(`/api/client/record/episodes${q2 ? `?${q2}` : ''}`);
      renderRecordingFileList(res2);
    }
  } catch (_) { /* toasted */ }
}

function isRecordingPanelExpanded() {
  const body = $('recording-body');
  return !!body && !body.classList.contains('collapsed');
}

function stopRecordingFileListPolling() {
  if (App.recordingListTimer) {
    clearInterval(App.recordingListTimer);
    App.recordingListTimer = null;
  }
}

function startRecordingFileListPolling() {
  if (App.recordingListTimer) return;
  App.recordingListTimer = setInterval(() => {
    if (!isRecordingPanelExpanded()) return;
    refreshRecordingFileList();
  }, 5000);
}

function syncRecordingFileListPolling() {
  if (isRecordingPanelExpanded()) {
    refreshRecordingFileList();
    startRecordingFileListPolling();
  } else {
    stopRecordingFileListPolling();
  }
}

function setupLeftPanelAccordion() {
  const panels = [
    { panelId: 'panel-config',    headerId: 'panel-config-header',    bodyId: 'config-body',    btnId: 'btn-config-collapse' },
    { panelId: 'panel-recording', headerId: 'panel-recording-header', bodyId: 'recording-body', btnId: 'btn-recording-collapse' },
    { panelId: 'panel-manual',    headerId: 'panel-manual-header',    bodyId: 'manual-body',    btnId: 'btn-manual-collapse' },
  ];

  const panelBodyIds = panels.map(p => p.bodyId);
  let currentExpandedBodyId = null;
  let autoCollapsedHistory = [];

  const setExpanded = (targetBodyId, reason = 'switch') => {
    if (!targetBodyId || !panelBodyIds.includes(targetBodyId)) return;

    if (currentExpandedBodyId && currentExpandedBodyId !== targetBodyId && reason !== 'init') {
      autoCollapsedHistory = autoCollapsedHistory.filter(id => id !== currentExpandedBodyId && id !== targetBodyId);
      autoCollapsedHistory.push(currentExpandedBodyId);
    }

    panels.forEach(({ panelId, bodyId, btnId }) => {
      const panel = $(panelId);
      const body = $(bodyId);
      const btn = btnId ? $(btnId) : null;
      if (!body) return;
      const expanded = bodyId === targetBodyId;
      body.classList.toggle('collapsed', !expanded);
      panel?.classList.toggle('panel-expanded', expanded);
      if (btn) {
        const isConfigBtn = btnId === 'btn-config-collapse';
        btn.innerHTML = isConfigBtn
          ? (expanded ? '<i class="fas fa-chevron-up"></i>' : '<i class="fas fa-chevron-down"></i>')
          : (expanded ? '<i class="fas fa-chevron-down"></i>' : '<i class="fas fa-chevron-up"></i>');
      }
    });

    currentExpandedBodyId = targetBodyId;
    syncRecordingFileListPolling();
  };

  const togglePanel = (bodyId) => {
    if (!panelBodyIds.includes(bodyId)) return;

    if (currentExpandedBodyId !== bodyId) {
      setExpanded(bodyId, 'switch');
      return;
    }

    let fallbackBodyId = null;
    while (autoCollapsedHistory.length > 0) {
      const candidate = autoCollapsedHistory.pop();
      if (candidate && candidate !== bodyId && panelBodyIds.includes(candidate)) {
        fallbackBodyId = candidate;
        break;
      }
    }
    if (!fallbackBodyId) {
      fallbackBodyId = panelBodyIds.find(id => id !== bodyId) || bodyId;
    }
    setExpanded(fallbackBodyId, 'fallback');
  };

  panels.forEach(({ headerId, bodyId, btnId }) => {
    const header = $(headerId);
    if (header) {
      header.addEventListener('click', (e) => {
        if (e.target.closest('.panel-header-actions')) return;
        togglePanel(bodyId);
      });
    }

    if (btnId) {
      const btn = $(btnId);
      btn?.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        togglePanel(bodyId);
      });
    }
  });

  // Default: Configuration expanded, Recording/Manual collapsed.
  setExpanded('config-body', 'init');
}

async function setRecordSwitch(enable) {
  const target = !!enable;
  const current = !!(App.config && App.config.record && App.config.record.switch);
  if (current === target) {
    syncRecordingSwitchUI();
    return;
  }

  const res = await apiFetch('/api/client/config/patch', {
    method: 'POST',
    body: JSON.stringify({ patch: { 'record.switch': target } }),
  });
  App.config = res.config || App.config;
  delete App.pendingPatch['record.switch'];
  if (!Object.keys(App.pendingPatch).length) clearPending();
  renderRecordingConfigTree(App.config);
}

// ═══════════════════════════════════════════════════════
//  Execution Log
// ═══════════════════════════════════════════════════════
function formatDurMs(ms) {
  if (ms == null) return '--';
  const s = ms / 1000;
  return s < 1 ? `${ms}ms` : `${s.toFixed(2)}s`;
}
function toDurSec(ms) {
  return ms != null ? +(ms / 1000).toFixed(2) : null;
}

const ExecLog = {
  enabled: false,
  records: [],        // newest first
  maxRecords: 200,
  storageKey: 'vla_exec_log_v1',
  _timerInterval: null,
  _nextId: 1,         // auto-increment record ID
  isInitializing: true, // Guard against auto-starting during page load
};

function loadExecLogFromStorage() {
  try {
    const raw = localStorage.getItem(ExecLog.storageKey);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        // Drop any record still 'running' — stale data from a previous session
        ExecLog.records = parsed.filter(r => r.status !== 'running');
        if (ExecLog.records.length !== parsed.length) saveExecLogToStorage();
        // Restore _nextId to max existing id + 1
        const maxId = parsed.reduce((m, r) => Math.max(m, Number(r.id) || 0), 0);
        ExecLog._nextId = maxId + 1;
      }
    }
  } catch (_) {}
}

function saveExecLogToStorage() {
  try {
    localStorage.setItem(ExecLog.storageKey, JSON.stringify(ExecLog.records));
  } catch (_) {}
}

/** Start a new execution record. Finalizes any in-flight record as 'switched'.
 *  Only creates a record when App.isRunning is true and logging is enabled.
 */
function startExecRecord(taskName, subTaskIdx, instruction) {
  if (ExecLog.isInitializing) return; // Prevent records during initialization
  if (!ExecLog.enabled) return;
  if (!App.isRunning) return;

  // Finalize existing running record
  _finalizeRunningRecord('switched');

  const now = Date.now();
  const record = {
    id: ExecLog._nextId++,
    taskName: taskName || '',
    subTaskIdx: Number.isFinite(subTaskIdx) ? subTaskIdx : 0,
    instruction: instruction || '',
    startTime: now,
    endTime: null,
    durationMs: null,
    pausedAt: null,
    pausedMs: 0,
    score: null,
    note: '',
    status: 'running',
  };

  ExecLog.records.unshift(record);
  if (ExecLog.records.length > ExecLog.maxRecords) {
    ExecLog.records.length = ExecLog.maxRecords;
  }
  saveExecLogToStorage();
  renderExecLog();
  _updateScoreRow();
}

/** Finalize running record with given status and optional score.
 *  Duration excludes accumulated pause time.
 */
function _finalizeRunningRecord(status, score = null) {
  const running = ExecLog.records.find(r => r.status === 'running');
  if (!running) return;
  running.endTime = Date.now();
  const pausedMs = Number(running.pausedMs) || 0;
  const pausedAt = running.pausedAt != null ? Number(running.pausedAt) : null;
  const totalPausedMs = pausedMs + (pausedAt != null ? running.endTime - pausedAt : 0);
  running.durationMs = Math.max(0, running.endTime - running.startTime - totalPausedMs);
  running.pausedAt = null;
  running.status = status;
  if (score !== null) running.score = score;
}

/** Pause the timer for the currently running record. */
function pauseExecRecord() {
  const running = ExecLog.records.find(r => r.status === 'running');
  if (!running || running.pausedAt != null) return;
  running.pausedAt = Date.now();
  const tbody = $('exec-log-tbody');
  if (tbody) {
    const row = tbody.querySelector(`tr[data-id="${running.id}"]`);
    const timer = row && row.querySelector('.exec-log-timer');
    if (timer) timer.dataset.pausedat = running.pausedAt;
  }
}

/** Resume the timer for the currently running record. */
function resumeExecRecord() {
  const running = ExecLog.records.find(r => r.status === 'running');
  if (!running || running.pausedAt == null) return;
  running.pausedMs = (Number(running.pausedMs) || 0) + (Date.now() - running.pausedAt);
  running.pausedAt = null;
  const tbody = $('exec-log-tbody');
  if (tbody) {
    const row = tbody.querySelector(`tr[data-id="${running.id}"]`);
    const timer = row && row.querySelector('.exec-log-timer');
    if (timer) {
      timer.dataset.pausedms = running.pausedMs;
      timer.dataset.pausedat = '';
    }
  }
}

/** Finalize running record as interrupted (called on system Stop). */
function interruptRunningExecRecord() {
  _finalizeRunningRecord('interrupted');
  saveExecLogToStorage();
  renderExecLog();
  _updateScoreRow();
}

/** Auto-start a record from current UI selection (called on system Start). */
function autoStartExecRecord() {
  if (!ExecLog.enabled) return;
  const taskSel = $('lang-task-select');
  const subSel  = $('lang-subtask-select');
  const textEl  = $('lang-cmd-text');
  const task = taskSel ? taskSel.value : '';
  const idx  = subSel  ? Number(subSel.value) : 0;
  const lang = textEl  ? textEl.value.trim() : '';
  if (!lang) return;
  startExecRecord(task, idx, lang);
}

/** Update the score of a record by id (called from score <select> change). */
function updateExecRecordScore(id, scoreStr) {
  const rec = ExecLog.records.find(r => r.id === id);
  if (!rec) return;
  rec.score = scoreStr === '' ? null : Number(scoreStr);
  if (rec.score != null && rec.status !== 'running') rec.status = 'scored';
  if (rec.score === null && rec.status === 'scored') rec.status = 'switched';
  saveExecLogToStorage();
  renderExecLog();
}

/** Called by score buttons: 0 / 0.5 / 1 */
function scoreExecRecord(score) {
  _finalizeRunningRecord('scored', score);
  saveExecLogToStorage();
  renderExecLog();
  _updateScoreRow();
}

/** Delete a single record by id */
function deleteExecRecord(id) {
  const idx = ExecLog.records.findIndex(r => r.id === id);
  if (idx >= 0) ExecLog.records.splice(idx, 1);
  saveExecLogToStorage();
  renderExecLog();
}

/** Update note text for a record */
function updateExecRecordNote(id, note) {
  const rec = ExecLog.records.find(r => r.id === id);
  if (!rec) return;
  rec.note = note;
  saveExecLogToStorage();
}

/** Show/hide score row depending on module state and running record */
function _updateScoreRow() {
  const row = $('exec-score-row');
  if (!row) return;
  const hasRunning = ExecLog.records.some(r => r.status === 'running');
  row.style.display = (ExecLog.enabled && hasRunning) ? 'flex' : 'none';
}

/** Sync disabled state of ExecLog Rec button with App.isRunning */
function syncExecLogRecButton() {
  const recBtn = $('btn-exec-log-rec');
  if (!recBtn) return;
  recBtn.disabled = !App.isRunning;
}

/** Render the execution log table */
function renderExecLog() {
  const tbody = $('exec-log-tbody');
  const countEl = $('exec-log-count');
  if (!tbody) return;

  if (countEl) countEl.textContent = `(${ExecLog.records.length})`;

  const recBtn = $('btn-exec-log-rec');
  const isRecording = ExecLog.records.some(r => r.status === 'running');
  if (recBtn) {
    recBtn.classList.toggle('recording', isRecording);
    syncExecLogRecButton();
  }

  // Stop old timer
  if (ExecLog._timerInterval) {
    clearInterval(ExecLog._timerInterval);
    ExecLog._timerInterval = null;
  }

  tbody.innerHTML = '';
  ExecLog.records.forEach(r => {
    const scoreClass = r.score === 0 ? 'exec-log-score-0' : r.score === 0.5 ? 'exec-log-score-05' : r.score === 1 ? 'exec-log-score-1' : '';
    const rowScoreClass = r.status === 'scored' ? `exec-log-scored ${scoreClass}` : '';
    const timeStr = new Date(r.startTime).toLocaleTimeString('zh-CN', { hour12: false });
    const noteEscaped = (r.note || '').replace(/"/g, '&quot;').replace(/</g, '&lt;');

    let durHtml;
    if (r.durationMs != null) {
      durHtml = formatDurMs(r.durationMs);
    } else if (r.status === 'running') {
      durHtml = `<span class="exec-log-timer" data-start="${r.startTime}" data-pausedms="${r.pausedMs || 0}" data-pausedat="${r.pausedAt || ''}">...</span>`;
    } else {
      durHtml = '--';
    }

    const scoreVal = r.score != null ? String(r.score) : '';
    const scoreCls = r.score === 0 ? 'score-val-0' : r.score === 0.5 ? 'score-val-05' : r.score === 1 ? 'score-val-1' : '';
    const scoreHtml = `<select class="exec-log-score-sel ${scoreCls}" data-id="${r.id}">
      <option value="">--</option>
      <option value="0"${scoreVal==='0'?' selected':''}>0</option>
      <option value="0.5"${scoreVal==='0.5'?' selected':''}>0.5</option>
      <option value="1"${scoreVal==='1'?' selected':''}>1</option>
    </select>`;

    const instrShort = r.instruction.length > 36 ? r.instruction.substring(0, 36) + '…' : r.instruction;
    const taskShort = r.taskName.length > 10 ? r.taskName.substring(0, 10) + '…' : r.taskName;
    const taskSubTitle = `${r.taskName} #${r.subTaskIdx + 1}\n${r.instruction}`;

    const tr = document.createElement('tr');
    tr.className = `exec-log-row exec-log-${r.status} ${rowScoreClass}`;
    tr.dataset.id = r.id;
    tr.innerHTML = `
      <td class="col-id" title="${taskSubTitle.replace(/"/g, '&quot;')}"><span class="exec-log-recidx">${r.id}</span> ${taskShort} <span class="exec-log-subidx">${r.subTaskIdx + 1}</span></td>
      <td class="col-inst" title="${r.instruction}">${instrShort}</td>
      <td class="col-start" title="${r.startTime ? new Date(r.startTime).toLocaleString() : '--'}">${timeStr}</td>
      <td class="col-dur" title="${r.durationMs != null ? formatDurMs(r.durationMs) : (r.status === 'running' ? 'running' : '--')}">${durHtml}</td>
      <td class="col-score">${scoreHtml}</td>
      <td class="col-note"><input type="text" class="exec-log-note-input" value="${noteEscaped}" data-id="${r.id}" placeholder="Note…" title="${noteEscaped}" /></td>
      <td class="col-del"><button class="btn exec-log-del-btn" data-id="${r.id}" title="Delete">✕</button></td>
    `;
    tbody.appendChild(tr);
  });

  // Bind events
  tbody.querySelectorAll('.exec-log-del-btn').forEach(btn => {
    btn.addEventListener('click', () => deleteExecRecord(Number(btn.dataset.id)));
  });
  tbody.querySelectorAll('.exec-log-note-input').forEach(inp => {
    inp.addEventListener('change', () => updateExecRecordNote(Number(inp.dataset.id), inp.value));
  });
  tbody.querySelectorAll('.exec-log-score-sel').forEach(sel => {
    sel.addEventListener('change', () => updateExecRecordScore(Number(sel.dataset.id), sel.value));
  });

  // Start live timer for running records
  const hasRunning = ExecLog.records.some(r => r.status === 'running');
  if (hasRunning) {
    ExecLog._timerInterval = setInterval(() => {
      const timers = tbody.querySelectorAll('.exec-log-timer');
      if (timers.length === 0) {
        clearInterval(ExecLog._timerInterval);
        ExecLog._timerInterval = null;
        return;
      }
      const now = Date.now();
      timers.forEach(el => {
        const start = Number(el.dataset.start);
        const pausedMs = Number(el.dataset.pausedms) || 0;
        const pausedAt = el.dataset.pausedat ? Number(el.dataset.pausedat) : null;
        if (Number.isFinite(start)) {
          const totalPausedMs = pausedMs + (pausedAt != null ? now - pausedAt : 0);
          const ms = Math.max(0, now - start - totalPausedMs);
          el.textContent = formatDurMs(ms);
        }
      });
    }, 200);
  }
}

/** Export all records as CSV download */
function exportExecLogCSV() {
  const headers = ['ID', 'Task', 'Sub#', 'Instruction', 'StartTime', 'Duration(s)', 'Paused(s)', 'Score', 'Status', 'Note'];
  const rows = ExecLog.records.map(r => {
    const dur = r.durationMs != null ? toDurSec(r.durationMs) : '';
    const paused = r.pausedMs != null ? toDurSec(r.pausedMs) : '';
    const instr = `"${(r.instruction || '').replace(/"/g, '""')}"`;
    const note = `"${(r.note || '').replace(/"/g, '""')}"`;
    const start = new Date(r.startTime).toLocaleString('zh-CN');
    const task = `"${r.taskName}"`;
    return [r.id, task, r.subTaskIdx + 1, instr, start, dur, paused, r.score != null ? r.score : '', r.status, note].join(',');
  });
  const csv = '\ufeff' + [headers.join(','), ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `exec_log_${new Date().toISOString().slice(0, 19).replace(/[:\-T]/g, '')}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

/** Save records to server (POST → logs/exec_log_<ts>.json) */
async function saveExecLogToServer() {
  try {
    const out = ExecLog.records.map(r => ({
      id: r.id,
      taskName: r.taskName,
      subTaskIdx: r.subTaskIdx + 1,
      instruction: r.instruction,
      startTime: new Date(r.startTime).toLocaleString('zh-CN'),
      endTime: r.endTime ? new Date(r.endTime).toLocaleString('zh-CN') : null,
      duration_s: toDurSec(r.durationMs),
      paused_s: toDurSec(r.pausedMs) ?? 0,
      score: r.score,
      note: r.note,
      status: r.status,
    }));
    await apiFetch('/api/client/exec_log/save', {
      method: 'POST',
      body: JSON.stringify({ records: out }),
      timeoutMs: 5000,
    });
    toast('Execution log saved.', 'ok', 2000);
  } catch (_) {}
}

/** Toggle ExecLog panel on/off, expand/collapse the recording panel accordingly */
function toggleExecLog(enabled) {
  ExecLog.enabled = !!enabled;
  const panel = $('exec-log-panel');
  if (panel) panel.style.display = ExecLog.enabled ? 'flex' : 'none';
  const recBody = $('recording-body');
  if (recBody) recBody.classList.toggle('exec-log-open', ExecLog.enabled);
  _updateScoreRow();
}

function setupRecordingPanel() {
  // Handle the unified start/stop button
  const startStopBtn = $('btn-recording-startstop');
  if (startStopBtn) {
    startStopBtn.addEventListener('click', async function() {
      if (!App.isRunning) {
        toast('Client is not running.', 'warn');
        syncRecordingSwitchUI();
        return;
      }

      if (App.isRecording) {
        // Stop recording
        await stopDataRecordingIfNeeded({ silent: false, refreshList: true });
      } else {
        // Start recording
        const saveItems = getRecordingSaveItems();
        try {
          const res = await apiFetch('/api/client/record/start', {
            method: 'POST',
            body: JSON.stringify({ save_items: saveItems }),
          });
          const currentTaskDir = typeof res?.recording_task_dir === 'string' ? res.recording_task_dir : '';
          const currentTask = typeof res?.recording_task === 'string' ? res.recording_task : '';
          if (currentTaskDir) {
            App.recordingTask = currentTaskDir;
            App.recordingChunk = null;
            App.recordingChunksSnapshot = [];
          } else if (currentTask) {
            // Fallback for older backend: select newest dir with task prefix.
            App.recordingTask = currentTask;
            App.recordingChunk = null;
            App.recordingChunksSnapshot = [];
          }

          App.isRecording = true;
          if (!App.config || typeof App.config !== 'object') App.config = {};
          if (!App.config.record || typeof App.config.record !== 'object') App.config.record = {};
          App.config.record.switch = true;
          renderRecordingConfigTree(App.config);
          await refreshRecordingFileList();
          toast('Recording started.', 'ok');
        } catch (_) { /* toasted */ }
      }
      syncRecordingSwitchUI();
    });
  }

  const taskSel = $('recording-task-select');
  taskSel?.addEventListener('change', async () => {
    App.recordingTask = taskSel.value || null;
    App.recordingChunk = null;
    App.recordingChunksSnapshot = [];
    await refreshRecordingFileList();
  });

  const chunkSel = $('recording-chunk-select');
  chunkSel?.addEventListener('change', async () => {
    App.recordingChunk = chunkSel.value || null;
    await refreshRecordingFileList();
  });

  syncRecordingSwitchUI();
  syncRecordingFileListPolling();
}

// TODO Check if needed
// 更新开始录制函数
function startRecording() {
  if (!App.isRunning || App.isRecording) return;

  const episodeEnabled = $('#chk-record-episode').checked;
  const expdataEnabled = $('#chk-record-expdata').checked;
  
  // 发送开始录制请求到后端
  sendWsMessage({ type: 'start_recording', payload: { 
    record_episode: episodeEnabled, 
    record_expdata: expdataEnabled 
  }});
}

// 更新停止录制函数
function stopRecording() {
  if (!App.isRunning || !App.isRecording) return;
  
  // 发送停止录制请求到后端
  sendWsMessage({ type: 'stop_recording', payload: {} });
}

// ── Execution Log initialization ──────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  // 为单一按钮添加事件监听器
  const startStopBtn = $('btn-recording-startstop');
  if (startStopBtn) {
    startStopBtn.addEventListener('click', function() {
      if (App.isRecording) {
        stopRecording();
      } else {
        startRecording();
      }
    });
  }

  // ExecLog checkbox: toggle panel visibility
  const execlogChk = $('chk-record-exec-log');
  if (execlogChk) {
    execlogChk.addEventListener('change', () => {
      if (typeof toggleExecLog === 'function') toggleExecLog(execlogChk.checked);
    });
  }

  // Rec button: start / interrupt
  $('btn-exec-log-rec')?.addEventListener('click', () => {
    if (typeof ExecLog === 'undefined') return;
    const isRecording = ExecLog.records.some(r => r.status === 'running');
    if (isRecording) {
      if (typeof interruptRunningExecRecord === 'function') interruptRunningExecRecord();
    } else {
      if (typeof autoStartExecRecord === 'function') autoStartExecRecord();
    }
  });

  // Score buttons
  document.querySelectorAll('.exec-score-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (typeof scoreExecRecord === 'function') scoreExecRecord(Number(btn.dataset.score));
    });
  });

  // Toolbar actions
  $('btn-log-export')?.addEventListener('click', () => {
    if (typeof exportExecLogCSV === 'function') exportExecLogCSV();
  });
  $('btn-log-save')?.addEventListener('click', () => {
    if (typeof saveExecLogToServer === 'function') saveExecLogToServer();
  });
  $('btn-log-clear')?.addEventListener('click', () => {
    if (typeof ExecLog === 'undefined') return;
    if (!confirm('Clear all execution log records?')) return;
    ExecLog.records = [];
    ExecLog._nextId = 1;
    if (typeof saveExecLogToStorage === 'function') saveExecLogToStorage();
    if (typeof renderExecLog === 'function') renderExecLog();
    if (typeof _updateScoreRow === 'function') _updateScoreRow();
  });

  // Init: restore from localStorage
  if (typeof loadExecLogFromStorage === 'function') loadExecLogFromStorage();
  
  // Set initial state without triggering auto-start
  if (execlogChk) {
    ExecLog.enabled = !!execlogChk.checked;
    toggleExecLog(ExecLog.enabled);
  }
  
  if (typeof renderExecLog === 'function') renderExecLog();
  if (typeof syncExecLogRecButton === 'function') syncExecLogRecButton();

  // Initialization complete - allow new records to be created after a short delay
  setTimeout(() => {
    ExecLog.isInitializing = false;
  }, 500);

  // On page unload, finalize any running record
  window.addEventListener('beforeunload', () => {
    if (typeof ExecLog === 'undefined') return;
    const running = ExecLog.records.find(r => r.status === 'running');
    if (!running) return;
    _finalizeRunningRecord('interrupted');
    saveExecLogToStorage();
  });
});
