function syncRecordingSwitchUI() {
  const running = !!App.isRunning;
  const recording = !!App.isRecording;
  const btnStartStop = $('btn-recording-startstop');
  if (!btnStartStop) return;
  const btnPauseResume = $('btn-recording-pauseresume');
  if (!btnPauseResume) return;

  btnStartStop.disabled = !running;
  btnPauseResume.disabled = !running || !recording
  
  // Update button text/icon/style based on recording status
  if (recording) {
    btnStartStop.innerHTML = '<i class="fas fa-stop"></i> Stop';
    btnStartStop.className = 'btn btn-sm btn-danger';
  } else {
    btnStartStop.innerHTML = '<i class="fas fa-play"></i> Start';
    btnStartStop.className = 'btn btn-sm btn-success';
  }
  if (recording) {
    btnPauseResume.innerHTML = '<i class="fas fa-pause"></i> Pause';
    btnPauseResume.className = 'btn btn-sm btn-danger';
  } else {
    btnPauseResume.innerHTML = '<i class="fas fa-play"></i> Resume';
    btnPauseResume.className = 'btn btn-sm btn-success';
  }
}

function syncRecordingCheckboxesFromConfig(cfg = App.config) {
  const episodeChk = $('chk-record-episode');
  const evalLogChk = $('chk-record-eval-log');
  const autoChk = $('chk-record-auto');
  const expDataChk = $('chk-record-expdata');
  const recordCfg = (cfg && typeof cfg === 'object' && cfg.record && typeof cfg.record === 'object') ? cfg.record : null;

  if (episodeChk && recordCfg && typeof recordCfg.is_record_episode === 'boolean') {
    episodeChk.checked = recordCfg.is_record_episode;
  }
  if (evalLogChk && recordCfg && typeof recordCfg.is_record_eval_log === 'boolean') {
    evalLogChk.checked = recordCfg.is_record_eval_log;
  }
  if (autoChk && recordCfg && typeof recordCfg.auto === 'boolean') {
    autoChk.checked = recordCfg.auto;
  }
  if (expDataChk && recordCfg && typeof recordCfg.is_record_expe_data === 'boolean') {
    expDataChk.checked = recordCfg.is_record_expe_data;
  }
  if (evalLogChk && typeof setEvalLogEnabled === 'function') {
    setEvalLogEnabled(!!evalLogChk.checked);
  }
}

async function persistRecordingConfigChange(patch) {
  if (!patch || typeof patch !== 'object' || !Object.keys(patch).length) return App.config;

  const res = await apiFetch('/api/client/config/patch', {
    method: 'POST',
    body: JSON.stringify({ patch }),
  });
  App.config = res.config || App.config;
  renderRecordingConfigTree(App.config);
  syncRecordingCheckboxesFromConfig(App.config);

  try {
    const confRes = await apiFetch('/api/client/config/path');
    if (confRes.path) {
      await apiFetch('/api/client/config/save', {
        method: 'POST',
        body: JSON.stringify({ path: confRes.path }),
      });
    }
  } catch (e) {
    console.error('Failed to save recording config:', e);
  }

  return App.config;
}

function renderRecordingConfigTree(cfg = App.config) {
  const root = $('recording-config-tree');
  if (!root) return;
  root.innerHTML = '';
  const recordCfg = (cfg && typeof cfg === 'object' && cfg.record && typeof cfg.record === 'object') ? cfg.record : {};
  buildTree(recordCfg, 'record', root);
  syncRecordingCheckboxesFromConfig(cfg);
  syncRecordingSwitchUI();
}

async function stopDataRecordingIfNeeded({ silent = false, refreshList = true } = {}) {
  if (!App.isRunning || !App.isRecording) {
    syncRecordingSwitchUI();
    return false;
  }
  // if (refreshList) await refreshRecordingFileList();

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
    if (refreshList) await refreshRecordingFileList();
    syncRecordingSwitchUI();
    if (!silent) toast('Recording stopped.', 'warn');
    return true;
  } catch (_) {
    syncRecordingSwitchUI();
    return false;
  }
}

async function renderRecordingFileList(data) {
  const listEl = $('recording-file-list');
  const taskSel = $('recording-task-select');
  const chunkSel = $('recording-chunk-select');
  if (!listEl) return;

  const episodes = Array.isArray(data?.episodes)
    ? data.episodes
    : (Array.isArray(data?.files) ? data.files : []);
  const evalResults = Array.isArray(data?.eval_results) ? data.eval_results : [];
  const tasks = Array.isArray(data?.tasks) ? data.tasks : [];
  const chunks = Array.isArray(data?.chunks) ? data.chunks : [];
  const serverSelectedTask = typeof data?.selected_task === 'string' ? data.selected_task : '';
  const serverSelectedChunk = typeof data?.selected_chunk === 'string' ? data.selected_chunk : '';

  renderEvaluationResults(evalResults);

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
      return `<div class="recording-file-item${activeCls}" data-episode-id="${safeId}" title="${safeName}"><span class="recording-file-item-name">${safeName}</span><span class="recording-file-item-meta">${frames}|${duration.toFixed(1)}s</span><span class="recording-file-item-actions"><button class="recording-file-item-delete" data-episode-id="${safeId}" title="Delete episode" aria-label="Delete episode"><svg class="recording-file-item-delete-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3h6l1 2h4v2H4V5h4l1-2zm-1 6h2v9H8V9zm4 0h2v9h-2V9zm4 0h2v9h-2V9z"/></svg></button></span></div>`;
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

function getEvaluationScoreOptions() {
  const fromRecord = App?.config?.record?.evaluation?.scores;
  const fromRoot = App?.config?.evaluation?.scores;
  const scores = Array.isArray(fromRecord) ? fromRecord : (Array.isArray(fromRoot) ? fromRoot : []);
  return scores.filter(v => v !== null && v !== undefined && v !== '');
}

async function updateEvaluationScore(recordId, score) {
  if (!App.recordingTask) return;
  await apiFetch('/api/client/record/eval/score', {
    method: 'POST',
    body: JSON.stringify({
      task: App.recordingTask,
      record_id: Number(recordId),
      score: score,
    }),
  });
}

async function updateEvaluationNote(recordId, note) {
  // Reserved for future backend API integration.
  if (!App.recordingTask) return;
  await apiFetch('/api/client/record/eval/note', {
    method: 'POST',
    body: JSON.stringify({
      task: App.recordingTask,
      record_id: Number(recordId),
      note: note,
    }),
  });
}

function renderEvaluationResults(evalResults = []) {
  const tbody = $('eval-log-tbody');
  const countEl = $('eval-log-count');
  if (!tbody) return;

  const list = Array.isArray(evalResults) ? evalResults.slice() : [];
  list.sort((a, b) => Number(b?.id ?? -1) - Number(a?.id ?? -1));
  App.evalResultsSnapshot = list.map(item => ({ ...(item || {}) }));

  if (countEl) countEl.textContent = String(list.length);

  if (!list.length) {
    App.evalResultSnapshot = [];
    App.evalResultActiveId = null;
    tbody.innerHTML = '<tr><td colspan="6" class="eval-log-empty">(empty)</td></tr>';
    return;
  }

  const esc = (val) => String(val ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
  const escAttr = (val) => esc(val).replaceAll('"', '&quot;');
  const scoreOptions = getEvaluationScoreOptions();

  const recordIds = list
    .map(item => String(item?.id ?? ''))
    .filter(Boolean);
  const prevRecordIds = Array.isArray(App.evalResultSnapshot) ? App.evalResultSnapshot : [];
  const prevRecordSet = new Set(prevRecordIds);
  const addedRecordIds = recordIds.filter(id => !prevRecordSet.has(id));

  let activeRecordId = App.evalResultActiveId;
  if (addedRecordIds.length > 0) {
    activeRecordId = addedRecordIds[0];
  } else if (!recordIds.includes(String(activeRecordId ?? ''))) {
    activeRecordId = recordIds[0] || null;
  }
  activeRecordId = activeRecordId ? String(activeRecordId) : null;
  App.evalResultActiveId = activeRecordId;
  App.evalResultSnapshot = recordIds;

  tbody.innerHTML = list.map((item) => {
    const idNum = Number(item?.id ?? -1);
    const id = String(idNum);
    const subTask = item?.sub_task_id ?? '';
    const durationNum = Number(item?.duration);
    const duration = Number.isFinite(durationNum) ? durationNum.toFixed(1) : '';
    const note = item?.note ?? '';
    const currentScore = (item?.score === null || item?.score === undefined) ? '' : String(item.score);
    const activeCls = id === activeRecordId ? ' active' : '';
    const scoreOptionsHtml = ['<option value=""></option>']
      .concat(scoreOptions.map((opt) => {
        const val = String(opt);
        const selected = val === currentScore ? ' selected' : '';
        return `<option value="${escAttr(val)}"${selected}>${esc(val)}</option>`;
      }))
      .join('');

    return `
      <tr class="eval-log-row${activeCls}" data-record-id="${escAttr(id)}">
        <td class="col-id">${esc(id)}</td>
        <td class="col-task">${esc(subTask)}</td>
        <td class="col-dur">${esc(duration)}s</td>
        <td class="col-score"><select class="eval-log-score-sel" data-record-id="${escAttr(id)}">${scoreOptionsHtml}</select></td>
        <td class="col-note"><input class="eval-log-note-input" data-record-id="${escAttr(id)}" value="${escAttr(note)}" placeholder="Add note" /></td>
        <td class="col-del"><button class="eval-log-del-btn" data-record-id="${escAttr(id)}" title="Delete evaluation result" aria-label="Delete evaluation result"><svg class="recording-file-item-delete-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3h6l1 2h4v2H4V5h4l1-2zm-1 6h2v9H8V9zm4 0h2v9h-2V9zm4 0h2v9h-2V9z"/></svg></button></td>
      </tr>
    `;
  }).join('');

  const setActiveEvalRecord = (recordId, row = null) => {
    const targetId = String(recordId ?? '').trim();
    if (!targetId) return;
    App.evalResultActiveId = targetId;

    tbody.querySelectorAll('.eval-log-row.active').forEach(node => node.classList.remove('active'));
    const target = row || tbody.querySelector(`.eval-log-row[data-record-id="${CSS.escape(targetId)}"]`);
    if (target) target.classList.add('active');
  };

  tbody.querySelectorAll('.eval-log-row[data-record-id]').forEach((row) => {
    row.addEventListener('click', () => {
      const id = row.getAttribute('data-record-id') || '';
      setActiveEvalRecord(id, row);
    });
  });

  tbody.querySelectorAll('.eval-log-score-sel[data-record-id]').forEach((sel) => {
    sel.addEventListener('focus', () => {
      const row = sel.closest('.eval-log-row');
      if (!row) return;
      const id = row.getAttribute('data-record-id') || '';
      setActiveEvalRecord(id, row);
    });

    sel.addEventListener('change', async () => {
      const recordId = Number(sel.getAttribute('data-record-id'));
      if (!Number.isFinite(recordId)) return;

      const raw = sel.value;
      const score = raw === '' ? null : Number(raw);
      if (raw !== '' && !Number.isFinite(score)) {
        toast('Invalid score value.', 'warn');
        await refreshRecordingFileList();
        return;
      }

      sel.disabled = true;
      try {
        await updateEvaluationScore(recordId, score);
      } catch (_) {
      } finally {
        sel.disabled = false;
        await refreshRecordingFileList();
      }
    });
  });

  tbody.querySelectorAll('.eval-log-note-input[data-record-id]').forEach((input) => {
    let currentValue = String(input.value || '');

    input.addEventListener('focus', () => {
      const row = input.closest('.eval-log-row');
      if (!row) return;
      const id = row.getAttribute('data-record-id') || '';
      setActiveEvalRecord(id, row);
    });

    input.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter') return;
      e.preventDefault();
      input.blur();
    });

    input.addEventListener('change', async () => {
      const recordId = Number(input.getAttribute('data-record-id'));
      if (!Number.isFinite(recordId)) return;

      const nextValue = String(input.value ?? '');
      if (nextValue === currentValue) return;

      input.disabled = true;
      try {
        await updateEvaluationNote(recordId, nextValue);
        currentValue = nextValue;
      } catch (_) {
        // Reserved: backend not connected yet.
      } finally {
        await refreshRecordingFileList();
        input.disabled = false;
      }
    });
  });

  tbody.querySelectorAll('.eval-log-del-btn[data-record-id]').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const recordId = Number(btn.getAttribute('data-record-id'));
      if (!Number.isFinite(recordId)) return;
      const row = btn.closest('.eval-log-row');
      if (row) {
        const id = row.getAttribute('data-record-id') || '';
        setActiveEvalRecord(id, row);
      }
      await deleteEvaluationResult(recordId);
    });
  });
}

async function deleteEvaluationResult(recordId) {
  if (!App.recordingTask || !recordId) return;
  const ok = window.confirm(`Delete Evaluation Record ${recordId} ? This cannot be undone.`);
  if (!ok) return;

  try {
    await apiFetch('/api/client/record/delete', {
      method: 'DELETE',
      body: JSON.stringify({ task: App.recordingTask, record_id: recordId }),
    });
    await refreshRecordingFileList();
    toast(`Deleted record ${recordId}.`, 'ok', 1800);
  } catch (_) { /* toasted */ }
}

async function deleteRecordingEpisode(episodeId) {
  if (!App.recordingTask || !episodeId) return;
  const ok = window.confirm(`Delete LeRobot Episode ${episodeId} ? This cannot be undone.`);
  if (!ok) return;

  try {
    await apiFetch('/api/client/record/delete', {
      method: 'DELETE',
      body: JSON.stringify({ task: App.recordingTask, episode_id: episodeId }),
    });
    if (App.recordingEpisodeId === episodeId) App.recordingEpisodeId = null;
    await refreshRecordingFileList();
    toast(`Deleted ${episodeId}.`, 'ok', 1800);
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
    // startRecordingFileListPolling();
  } else {
    // stopRecordingFileListPolling();
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
        try {
          const res = await apiFetch('/api/client/record/start', {
            method: 'POST',
            body: JSON.stringify({}),
          });
          const currentTaskDir = typeof res?.recording_task_dir === 'string' ? res.recording_task_dir : '';
          if (currentTaskDir) {
            App.recordingTask = currentTaskDir;
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

// ── Evaluation Log initialization ──────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  // Record Config collapse/expand
  const cfgCollapseBtn = $('btn-recording-config-collapse');
  const wrap = $('recording-config-wrap');

  if (cfgCollapseBtn) {
    const icon = cfgCollapseBtn.querySelector('i');

    if (wrap) {
      wrap.classList.add('collapsed');
    }

    if (icon) {
      icon.className = 'fas fa-chevron-down';
    }

    cfgCollapseBtn.addEventListener('click', () => {
      if (!wrap) return;
      wrap.classList.toggle('collapsed');
      if (icon) {
        icon.className = wrap.classList.contains('collapsed')
          ? 'fas fa-chevron-down'
          : 'fas fa-chevron-up';
      }
    });
  }

  // Restore checkbox states from config and keep UI in sync
  const episodeChk = $('chk-record-episode');
  const evallogChk = $('chk-record-eval-log');
  const autoChk = $('chk-record-auto');
  const expDataChk = $('chk-record-expdata');

  syncRecordingCheckboxesFromConfig(App.config);

  if (episodeChk) {
    episodeChk.addEventListener('change', async () => {
      if (!App.config || typeof App.config !== 'object') App.config = {};
      if (!App.config.record || typeof App.config.record !== 'object') App.config.record = {};

      const previousValue = !!App.config.record.is_record_episode;
      App.config.record.is_record_episode = episodeChk.checked;

      try {
        await persistRecordingConfigChange({ 'record.is_record_episode': episodeChk.checked });
      } catch (e) {
        App.config.record.is_record_episode = previousValue;
        episodeChk.checked = previousValue;
        syncRecordingCheckboxesFromConfig(App.config);
        console.error('Failed to update recording episode config:', e);
      }
    });
  }

  if (evallogChk) {
    evallogChk.addEventListener('change', async () => {
      if (!App.config || typeof App.config !== 'object') App.config = {};
      if (!App.config.record || typeof App.config.record !== 'object') App.config.record = {};

      const previousValue = !!App.config.record.is_record_eval_log;
      App.config.record.is_record_eval_log = evallogChk.checked;

      try {
        await persistRecordingConfigChange({ 'record.is_record_eval_log': evallogChk.checked });
      } catch (e) {
        App.config.record.is_record_eval_log = previousValue;
        evallogChk.checked = previousValue;
        syncRecordingCheckboxesFromConfig(App.config);
        console.error('Failed to update evaluation log config:', e);
      }
    });
  }

  if (autoChk) {
    autoChk.addEventListener('change', async () => {
      if (!App.config || typeof App.config !== 'object') App.config = {};
      if (!App.config.record || typeof App.config.record !== 'object') App.config.record = {};

      const previousValue = !!App.config.record.auto;
      App.config.record.auto = autoChk.checked;

      try {
        await persistRecordingConfigChange({ 'record.auto': autoChk.checked });
      } catch (e) {
        App.config.record.auto = previousValue;
        autoChk.checked = previousValue;
        syncRecordingCheckboxesFromConfig(App.config);
        console.error('Failed to update auto config:', e);
      }
    });
  }

  if (expDataChk) {
    expDataChk.addEventListener('change', async () => {
      if (!App.config || typeof App.config !== 'object') App.config = {};
      if (!App.config.record || typeof App.config.record !== 'object') App.config.record = {};

      const previousValue = !!App.config.record.is_record_expe_data;
      App.config.record.is_record_expe_data = expDataChk.checked;

      try {
        await persistRecordingConfigChange({ 'record.is_record_expe_data': expDataChk.checked });
      } catch (e) {
        App.config.record.is_record_expe_data = previousValue;
        expDataChk.checked = previousValue;
        syncRecordingCheckboxesFromConfig(App.config);
        console.error('Failed to update experiment data config:', e);
      }
    });
  }

  // $('btn-log-clear')?.addEventListener('click', () => {
  //   if (typeof ExecLog === 'undefined') return;
  //   if (!confirm('Clear all execution log records?')) return;
  //   ExecLog.records = [];
  //   ExecLog._nextId = 1;
  //   if (typeof saveExecLogToStorage === 'function') saveExecLogToStorage();
  //   if (typeof renderExecLog === 'function') renderExecLog();
  //   if (typeof _updateScoreRow === 'function') _updateScoreRow();
  // });

  // Init: restore from localStorage
  // if (typeof loadExecLogFromStorage === 'function') loadExecLogFromStorage();
  
  // Set initial state without triggering auto-start
  // if (execlogChk) {
  //   ExecLog.enabled = !!execlogChk.checked;
  //   toggleExecLog(ExecLog.enabled);
  // }
  
  // if (typeof renderExecLog === 'function') renderExecLog();
  // if (typeof syncExecLogRecButton === 'function') syncExecLogRecButton();

  // Initialization complete - allow new records to be created after a short delay
  // setTimeout(() => {
  //   ExecLog.isInitializing = false;
  // }, 500);

  // On page unload, finalize any running record
  // window.addEventListener('beforeunload', () => {
  //   if (typeof ExecLog === 'undefined') return;
  //   const running = ExecLog.records.find(r => r.status === 'running');
  //   if (!running) return;
  //   _finalizeRunningRecord('interrupted');
  //   saveExecLogToStorage();
  // });
});
