function syncRecordingSwitchUI() {
  const running = !!App.isRunning;
  const recording = !!App.isRecording;
  const btnStartStop = $('btn-recording-startstop');
  if (!btnStartStop) return;

  btnStartStop.disabled = !running;
  
  // Update button text and style based on recording status
  if (recording) {
    btnStartStop.textContent = 'Stop';
    btnStartStop.className = 'btn btn-sm btn-danger';
  } else {
    btnStartStop.textContent = 'Start';
    btnStartStop.className = 'btn btn-sm btn-success';
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
        try {
          toast('Recording stopping.', 'info');
          await apiFetch('/api/client/record/stop', {
            method: 'POST',
            body: JSON.stringify({}),
          });

          App.isRecording = false;
          if (!App.config || typeof App.config !== 'object') App.config = {};
          if (!App.config.record || typeof App.config.record !== 'object') App.config.record = {};
          App.config.record.switch = false;
          renderRecordingConfigTree(App.config);
          toast('Recording stopped.', 'warn');
          await refreshRecordingFileList();
        } catch (_) { /* toasted */ }
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

// 为单一按钮添加事件监听器
document.addEventListener('DOMContentLoaded', function() {
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
});
