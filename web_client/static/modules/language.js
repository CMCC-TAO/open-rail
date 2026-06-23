// ═══════════════════════════════════════════════════════
//  Language Command Panel
//  Two-level hierarchy loaded from a JSON file via file picker.
//  JSON format: { "TaskA": ["sub1","sub2",...], "TaskB": [...] }
//  Tasks → <select> level-1; Sub-tasks → <select> level-2 (ordered Array)
// ═══════════════════════════════════════════════════════
const LangCmd = {
  tasks: {},        // { taskName: [instruction0, instruction1, ...] }  — ordered array
};

function buildLangTasksFromData(data) {
  LangCmd.tasks = {};
  if (!data || typeof data !== 'object') return;

  if (Array.isArray(data)) {
    // Flat array → single "Default" task
    LangCmd.tasks['Default'] = data.filter(x => typeof x === 'string');
  } else {
    for (const [taskName, subtasks] of Object.entries(data)) {
      if (Array.isArray(subtasks)) {
        LangCmd.tasks[taskName] = subtasks.filter(x => typeof x === 'string');
      }
    }
  }
}

function getAppliedLangSelection() {
  const taskId = App.config && App.config.language ? App.config.language.task_id : undefined;
  const rawSubTaskId = App.config && App.config.language ? App.config.language.sub_task_id : undefined;
  const parsedSubTaskId = Number(rawSubTaskId);
  return {
    taskId,
    subTaskId: Number.isFinite(parsedSubTaskId) ? parsedSubTaskId : null,
  };
}

function setAppliedOptionMarker(optionEl, isApplied) {
  if (!optionEl) return;
  if (isApplied) optionEl.dataset.applied = '1';
  else delete optionEl.dataset.applied;
}

function formatLangTaskOptionLabel(taskName) {
  return taskName;
}

function getLangSubtaskMaxCharsByWidth(subtaskSelectEl) {
  const width = subtaskSelectEl && subtaskSelectEl.clientWidth ? subtaskSelectEl.clientWidth : 0;
  if (!Number.isFinite(width) || width <= 0) return 36;
  // Reserve width for index/prefix + right check icon area + select paddings.
  const reservedPx = 81;
  const avgCharPx = 7.2;
  const estimated = Math.floor((width - reservedPx) / avgCharPx);
  return Math.max(14, estimated);
}

function formatLangSubtaskOptionLabel(taskName, text, index, maxChars = 36) {
  const clipped = text.length > maxChars ? `${text.substring(0, maxChars)}…` : text;
  return `${index + 1}.${clipped}`;
}

function refreshLangAppliedMarkers(taskId, subTaskId) {
  const taskSel = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');

  const applied = getAppliedLangSelection();
  const fallbackTaskId = applied.taskId != null ? String(applied.taskId) : '';
  const resolvedTaskId = taskId != null ? String(taskId) : fallbackTaskId;

  const parsedSubTaskId = Number(subTaskId);
  const resolvedSubTaskId = Number.isFinite(parsedSubTaskId)
    ? parsedSubTaskId
    : (Number.isFinite(applied.subTaskId) ? applied.subTaskId : null);

  if (taskSel) {
    Array.from(taskSel.options).forEach((opt) => {
      setAppliedOptionMarker(opt, opt.value === resolvedTaskId);
    });
  }

  if (subtaskSel) {
    const visibleTaskId = taskSel ? taskSel.value : resolvedTaskId;
    const enableSubtaskMarker = visibleTaskId === resolvedTaskId && resolvedSubTaskId != null;
    Array.from(subtaskSel.options).forEach((opt) => {
      setAppliedOptionMarker(opt, enableSubtaskMarker && Number(opt.value) === resolvedSubTaskId);
    });
  }
}

function renderLangTaskSelect() {
  const taskSel    = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  if (!taskSel) return;

  const prevTask = taskSel.value;
  taskSel.innerHTML = '';

  const { taskId: appliedTaskId } = getAppliedLangSelection();
  Object.keys(LangCmd.tasks).forEach(taskName => {
    const opt = document.createElement('option');
    opt.value = taskName;
    opt.textContent = formatLangTaskOptionLabel(taskName);
    setAppliedOptionMarker(opt, taskName === appliedTaskId);
    taskSel.appendChild(opt);
  });

  // Restore or select first
  if (prevTask && LangCmd.tasks[prevTask]) taskSel.value = prevTask;
  if (!taskSel.value && taskSel.options.length > 0) taskSel.selectedIndex = 0;

  renderLangSubtaskSelect();
  // Sync Config panel: use App.config values if available, otherwise current selection
  const cfgTask  = (App.config && App.config.language && App.config.language.task_id) || taskSel.value;
  const cfgIndex = (App.config && App.config.language && App.config.language.sub_task_id != null) ? App.config.language.sub_task_id : undefined;
  syncLangTaskOptions(cfgTask, cfgIndex);
}

function renderLangSubtaskSelect() {
  const taskSel    = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  if (!subtaskSel) return;

  subtaskSel.innerHTML = '';
  const taskName = taskSel ? taskSel.value : null;
  const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
  const maxChars = getLangSubtaskMaxCharsByWidth(subtaskSel);

  const { taskId: appliedTaskId, subTaskId: appliedSubTaskId } = getAppliedLangSelection();
  subtasks.forEach((text, i) => {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = formatLangSubtaskOptionLabel(taskName, text, i, maxChars);
    setAppliedOptionMarker(opt, taskName === appliedTaskId && i === appliedSubTaskId);
    opt.title = text;
    subtaskSel.appendChild(opt);
  });
  // Sync Config panel sub_task_id options (preserve current selection)
  syncLangIndexOptions(taskName);
}

// Keep old renderLangPresets as compatibility alias (called on config load)
function renderLangPresets(presets) {
  App.langPresets = presets || [];
  // config.language (flat array) → put into LangCmd only if no JSON loaded yet
  if (Object.keys(LangCmd.tasks).length === 0) {
    buildLangTasksFromData(presets);
    renderLangTaskSelect();
  }
}

function setupLangPanel() {
  const taskSel = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  const autoChk = $('chk-lang-auto-mode');
  const thresholdInput = $('inp-lang-threshold');
  const winSizeInput = $('inp-lang-win-size');
  let thresholdSaveTimer = null;
  let winSizeSaveTimer = null;

  const setAutoModeEditable = (enabled) => {
    if (thresholdInput) thresholdInput.disabled = !enabled;
    if (winSizeInput) winSizeInput.disabled = !enabled;
  };

  const getConfigSavePath = () => {
    const display = $('conf-path-display');
    return (display && display.dataset.fullPath) || (display && display.textContent.trim()) || '';
  };

  const persistLanguagePatch = async (patch) => {
    if (!App.config || typeof App.config !== 'object') App.config = {};
    if (!App.config.language || typeof App.config.language !== 'object') App.config.language = {};

    Object.entries(patch).forEach(([dotKey, value]) => {
      App.pendingPatch[dotKey] = value;
      if (dotKey.startsWith('language.')) {
        const key = dotKey.slice('language.'.length);
        App.config.language[key] = value;
      }
    });
    markPending();

    try {
      const res = await apiFetch('/api/client/config/patch', {
        method: 'POST',
        body: JSON.stringify({ patch }),
      });
      App.config = res.config || App.config;

      Object.keys(patch).forEach((dotKey) => delete App.pendingPatch[dotKey]);
      if (!Object.keys(App.pendingPatch).length) clearPending();

      const path = getConfigSavePath();
      if (path) {
        await apiFetch('/api/client/config/save', {
          method: 'POST',
          body: JSON.stringify({ path }),
        });
      }
      return true;
    } catch (_) {
      Object.entries(patch).forEach(([dotKey, value]) => {
        App.pendingPatch[dotKey] = value;
      });
      markPending();
      return false;
    }
  };

  const commitThreshold = async () => {
    if (!thresholdInput || thresholdInput.disabled) return;
    const raw = thresholdInput.value.trim();
    const value = Number(raw);
    if (!Number.isFinite(value)) {
      thresholdInput.style.borderColor = 'var(--danger)';
      return;
    }
    thresholdInput.style.borderColor = '';
    await persistLanguagePatch({ 'language.task_progress_threshold': value });
  };

  const commitWinSize = async () => {
    if (!winSizeInput || winSizeInput.disabled) return;
    const raw = winSizeInput.value.trim();
    const value = Number(raw);
    if (!Number.isInteger(value) || value <= 0) {
      winSizeInput.style.borderColor = 'var(--danger)';
      return;
    }
    winSizeInput.style.borderColor = '';
    await persistLanguagePatch({ 'language.task_progress_win_size': value });
  };

  // Task select → rebuild subtask list and default to first sub-task.
  if (taskSel) {
    taskSel.addEventListener('change', () => {
      renderLangSubtaskSelect();
      // App.langAuto.lastProgress = null;

      // Default select first sub-task after task switch.
      const taskName = taskSel.value;
      const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
      if (subtaskSel) {
        if (subtaskSel.options.length > 0) {
          subtaskSel.selectedIndex = 0;
          subtaskSel.value = '0';
        } else {
          subtaskSel.value = '';
        }
      }
      $('lang-cmd-text').value = subtasks[0] ?? '';

      // Sync Config panel selects to task + first sub-task.
      const cfgTaskSel = $('cfg-language-task');
      if (cfgTaskSel) cfgTaskSel.value = taskSel.value;
      syncLangIndexOptions(taskSel.value, 0);
      const cfgIdxSel = $('cfg-language-index');
      if (cfgIdxSel) cfgIdxSel.value = '0';
      refreshLangAppliedMarkers();
    });
  }

  // Subtask select → fill textarea + sync Config panel selects only (no pendingPatch yet)
  if (subtaskSel) {
    subtaskSel.addEventListener('change', () => {
      const taskName = taskSel ? taskSel.value : null;
      const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
      const idx = parseInt(subtaskSel.value, 10);
      if (!isNaN(idx) && subtasks[idx] !== undefined) {
        $('lang-cmd-text').value = subtasks[idx];
      }
      const cfgIdxSel = $('cfg-language-index');
      if (cfgIdxSel && cfgIdxSel.value !== subtaskSel.value) {
        cfgIdxSel.value = subtaskSel.value;
      }
    });
  }

  if (autoChk) {
    autoChk.addEventListener('change', async () => {
      // App.langAuto.lastProgress = null;
      const enabled = !!autoChk.checked;
      setAutoModeEditable(enabled);

      if (enabled) {
        const taskName = taskSel ? taskSel.value : null;
        const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];

        if (subtaskSel) {
          if (subtaskSel.options.length > 0) {
            subtaskSel.selectedIndex = 0;
            subtaskSel.value = '0';
            subtaskSel.dispatchEvent(new Event('change'));
          } else {
            subtaskSel.value = '';
          }
        }

        if (subtasks[0] !== undefined) {
          $('lang-cmd-text').value = subtasks[0];
        }

        await persistLanguagePatch({
          'language.auto_mode': true,
          'language.sub_task_id': 0,
        });
        autoStartExecRecord();
        return;
      }

      await persistLanguagePatch({ 'language.auto_mode': false });
      autoStartExecRecord();
    });
  }

  if (thresholdInput) {
    thresholdInput.addEventListener('input', () => {
      const value = Number(thresholdInput.value.trim());
      thresholdInput.style.borderColor = Number.isFinite(value) ? '' : 'var(--danger)';
      if (thresholdInput.disabled || !Number.isFinite(value)) return;
      if (thresholdSaveTimer) clearTimeout(thresholdSaveTimer);
      thresholdSaveTimer = setTimeout(() => {
        thresholdSaveTimer = null;
        commitThreshold();
      }, 300);
    });

    thresholdInput.addEventListener('change', async () => {
      if (thresholdSaveTimer) {
        clearTimeout(thresholdSaveTimer);
        thresholdSaveTimer = null;
      }
      await commitThreshold();
    });

    thresholdInput.addEventListener('keydown', async (e) => {
      if (e.key !== 'Enter') return;
      if (thresholdSaveTimer) {
        clearTimeout(thresholdSaveTimer);
        thresholdSaveTimer = null;
      }
      await commitThreshold();
    });
  }

  if (winSizeInput) {
    winSizeInput.addEventListener('input', () => {
      const value = Number(winSizeInput.value.trim());
      winSizeInput.style.borderColor = (Number.isInteger(value) && value > 0) ? '' : 'var(--danger)';
      if (winSizeInput.disabled || !Number.isInteger(value) || value <= 0) return;
      if (winSizeSaveTimer) clearTimeout(winSizeSaveTimer);
      winSizeSaveTimer = setTimeout(() => {
        winSizeSaveTimer = null;
        commitWinSize();
      }, 300);
    });

    winSizeInput.addEventListener('change', async () => {
      if (winSizeSaveTimer) {
        clearTimeout(winSizeSaveTimer);
        winSizeSaveTimer = null;
      }
      await commitWinSize();
    });

    winSizeInput.addEventListener('keydown', async (e) => {
      if (e.key !== 'Enter') return;
      if (winSizeSaveTimer) {
        clearTimeout(winSizeSaveTimer);
        winSizeSaveTimer = null;
      }
      await commitWinSize();
    });
  }

  setAutoModeEditable(!!(autoChk && autoChk.checked));
}

/** Load language command JSON from App.config.language.file_path (fallback to default endpoint). */
async function loadDefaultLangFile() {
  try {
    const langPath = App.config && App.config.language && App.config.language.file_path;
    let res;
    if (langPath) {
      res = await apiFetch('/api/client/language/load', { method: 'POST', body: JSON.stringify({ path: langPath }) });
    } else {
      res = await apiFetch('/api/client/language/load/default');
      if (!App.config || typeof App.config !== 'object') App.config = {};
      if (!App.config.language || typeof App.config.language !== 'object') App.config.language = {};
      if (res.path) App.config.language.file_path = res.path;
    }

    if (res.data) {
      buildLangTasksFromData(res.data);
      renderLangTaskSelect();
      // Apply task_id / sub_task_id from current config
      applyLangConfigSelection();
    }
  } catch (_) { /* non-fatal: lang panel stays empty */ }
}

/**
 * After lang data is loaded (or config reloaded), synchronize the Language Command panel
 * and Config panel selects to reflect App.config.task_id / sub_task_id.
 * Also fills lang-cmd-text with the corresponding instruction.
 */
function applyLangConfigSelection(forceFirstSubtask = false) {
  const task = App.config && App.config.language && App.config.language.task_id;
  const rawIndex = (App.config && App.config.language && App.config.language.sub_task_id != null) ? App.config.language.sub_task_id : 0;
  let index = Number(rawIndex);
  if (!Number.isFinite(index)) index = 0;

  const autoModeRaw = App.config && App.config.language && App.config.language.auto_mode;
  const autoMode = (autoModeRaw === true || autoModeRaw === 'true' || autoModeRaw === 1 || autoModeRaw === '1');
  if (forceFirstSubtask || autoMode) index = 0;
  const thresholdRaw = App.config && App.config.language && App.config.language.task_progress_threshold;
  const threshold = Number(thresholdRaw);
  const winSizeRaw = App.config && App.config.language && App.config.language.task_progress_win_size;
  const winSize = Number(winSizeRaw);

  const autoChk = $('chk-lang-auto-mode');
  if (autoChk) autoChk.checked = autoMode;

  const editable = !!(autoChk ? autoChk.checked : autoMode);

  const thresholdInput = $('inp-lang-threshold');
  if (thresholdInput) {
    const fallback = Number(thresholdInput.value);
    const displayThreshold = Number.isFinite(threshold)
      ? threshold
      : (Number.isFinite(fallback) ? fallback : 0.95);
    thresholdInput.value = String(displayThreshold);
    thresholdInput.disabled = !editable;
    thresholdInput.style.borderColor = '';
  }

  const winSizeInput = $('inp-lang-win-size');
  if (winSizeInput) {
    const fallback = Number(winSizeInput.value);
    const displayWinSize = (Number.isInteger(winSize) && winSize > 0)
      ? winSize
      : ((Number.isInteger(fallback) && fallback > 0) ? fallback : 10);
    winSizeInput.value = String(displayWinSize);
    winSizeInput.disabled = !editable;
    winSizeInput.style.borderColor = '';
  }

  // Sync Lang Panel Task select
  const taskSel = $('lang-task-select');
  if (taskSel && task && LangCmd.tasks[task]) {
    taskSel.value = task;
  } else if (taskSel && taskSel.options.length > 0 && !taskSel.value) {
    taskSel.selectedIndex = 0;
  }

  // Rebuild subtask list for the selected task
  renderLangSubtaskSelect();

  // Sync Lang Panel Sub-task select
  const subtaskSel = $('lang-subtask-select');
  const taskName = taskSel ? taskSel.value : null;
  const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
  const safeIndex = subtasks.length > 0
    ? Math.max(0, Math.min(index, subtasks.length - 1))
    : -1;

  if (subtaskSel) {
    if (safeIndex >= 0) {
      subtaskSel.value = String(safeIndex);
      $('lang-cmd-text').value = subtasks[safeIndex] ?? '';
    } else {
      subtaskSel.value = '';
      $('lang-cmd-text').value = '';
    }
  }

  if (App.config && App.config.language && safeIndex >= 0) {
    App.config.language.task_id = taskName || App.config.language.task_id;
    App.config.language.sub_task_id = safeIndex;
  }

  // Sync Config panel selects
  syncLangTaskOptions(taskName || task, safeIndex >= 0 ? safeIndex : 0);
  refreshLangAppliedMarkers(taskName || task, safeIndex >= 0 ? safeIndex : null);
}

function setupLanguageEvents() {
// Language Command panel — JSON file picker
$('lang-file-input').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const path = file.path || file.name;
  try {
    const res = await apiFetch('/api/client/language/load', { method: 'POST', body: JSON.stringify({ path }) });
    buildLangTasksFromData(res.data);
    renderLangTaskSelect();

    if (!App.config || typeof App.config !== 'object') App.config = {};
    if (!App.config.language || typeof App.config.language !== 'object') App.config.language = {};
    App.config.language.file_path = path;

    App.pendingPatch['language.file_path'] = path;
    markPending();

    try {
      const patchRes = await apiFetch('/api/client/config/patch', {
        method: 'POST',
        body: JSON.stringify({ patch: { 'language.file_path': path } }),
      });
      App.config = patchRes.config || App.config;
      delete App.pendingPatch['language.file_path'];
      if (!Object.keys(App.pendingPatch).length) clearPending();

      const display = $('conf-path-display');
      const cfgPath = (display && display.dataset.fullPath) || (display && display.textContent.trim()) || '';
      if (cfgPath) {
        await apiFetch('/api/client/config/save', { method: 'POST', body: JSON.stringify({ path: cfgPath }) });
      }
    } catch (_) {
      App.pendingPatch['language.file_path'] = path;
      markPending();
    }

    toast('Language file loaded.', 'ok', 2000);
  } catch (_) { /* toasted */ }
  e.target.value = '';
});

// Language Command panel — send
$('btn-lang-send').addEventListener('click', async () => {
  const taskSel = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  const autoChk = $('chk-lang-auto-mode');
  const task = taskSel ? taskSel.value : null;
  const subtasks = (task && LangCmd.tasks[task]) ? LangCmd.tasks[task] : [];

  let idx = subtaskSel ? parseInt(subtaskSel.value, 10) : NaN;
  if (!Number.isFinite(idx) || idx < 0) idx = 0;

  // Auto mode should always start from first sub-task.
  if (autoChk && autoChk.checked) {
    idx = 0;
    if (subtaskSel && subtaskSel.value !== '0') {
      subtaskSel.value = '0';
      subtaskSel.dispatchEvent(new Event('change'));
    }
  }

  let lang = $('lang-cmd-text').value.trim();
  if (autoChk && autoChk.checked && subtasks[0] !== undefined) {
    lang = String(subtasks[0]).trim();
    $('lang-cmd-text').value = lang;
  }

  if (!lang) { toast('Enter a language instruction.', 'warn'); return; }

  // 1. Write current Task / SubTask selection into pendingPatch
  if (task != null) {
    App.pendingPatch['language.task_id'] = task;
    App.pendingPatch['language.sub_task_id'] = idx;
    markPending();
  }

  // 2. Trigger Config Apply (patch + save) — reuse the same handler
  $('btn-apply-config').click();

  // 3. Send language command to robot
  await sendLanguageSet(lang);
  toast('Language command updated.', 'info');

  // 4. Start execution record (only when running + log enabled)
  startExecRecord(task, idx, lang);
});
$('lang-cmd-text').addEventListener('keydown', e => { if (e.key === 'Enter' && e.ctrlKey) $('btn-lang-send').click(); });

// Language Command panel collapse
$('btn-lang-collapse').addEventListener('click', () => {
  const langBody = $('lang-body');
  const trajBody = $('traj-body');

  // If trajectory is collapsed, this click should restore both panels to normal layout.
  if (trajBody.classList.contains('collapsed')) {
    trajBody.classList.remove('collapsed');
    langBody.classList.remove('collapsed');
    if (typeof updateCenterPanelLayoutState === 'function') {
      updateCenterPanelLayoutState();
    }
    syncCenterPanelCollapseUi();
    return;
  }

  langBody.classList.toggle('collapsed');
  if (typeof updateCenterPanelLayoutState === 'function') {
    updateCenterPanelLayoutState();
  }
  syncCenterPanelCollapseUi();
});

// Execution Log — toggle button
$('btn-lang-log').addEventListener('click', () => toggleExecLog());

// Execution Log — manual Rec button (toggle: start / interrupt)
$('btn-execlog-rec').addEventListener('click', () => {
  const isRecording = LangExecLog.records.some(r => r.status === 'running');
  if (isRecording) {
    interruptRunningExecRecord();
  } else {
    autoStartExecRecord();
  }
});

// Execution Log — score buttons
document.querySelectorAll('.lang-score-btn').forEach(btn => {
  btn.addEventListener('click', () => scoreExecRecord(Number(btn.dataset.score)));
});

// Execution Log — toolbar actions
$('btn-log-export').addEventListener('click', () => exportExecLogCSV());
$('btn-log-save').addEventListener('click', () => saveExecLogToServer());
$('btn-log-clear').addEventListener('click', () => {
  if (!confirm('Clear all execution log records?')) return;
  LangExecLog.records = [];
  LangExecLog._nextId = 1;
  saveExecLogToStorage();
  renderExecLog();
  _updateScoreRow();
});

// Execution Log — init: restore from localStorage
loadExecLogFromStorage();
renderExecLog();

// Column resize handles
initLangColResize();

// On page unload, finalize any running record so localStorage stays clean
window.addEventListener('beforeunload', () => {
  const running = LangExecLog.records.find(r => r.status === 'running');
  if (!running) return;
  running.status = 'interrupted';
  running.endTime = Date.now();
  const pausedMs = Number(running.pausedMs) || 0;
  running.durationMs = Math.max(0, running.endTime - running.startTime - pausedMs);
  saveExecLogToStorage();
});

}

// ═══════════════════════════════════════════════════════
//  Execution Log
// ═══════════════════════════════════════════════════════
const LangExecLog = {
  enabled: false,
  records: [],        // newest first
  maxRecords: 200,
  storageKey: 'vla_exec_log_v1',
  _timerInterval: null,
  _nextId: 1,         // auto-increment record ID
};

function loadExecLogFromStorage() {
  try {
    const raw = localStorage.getItem(LangExecLog.storageKey);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        // Drop any record still 'running' — stale data from a previous session
        LangExecLog.records = parsed.filter(r => r.status !== 'running');
        if (LangExecLog.records.length !== parsed.length) saveExecLogToStorage();
        // Restore _nextId to max existing id + 1
        const maxId = parsed.reduce((m, r) => Math.max(m, Number(r.id) || 0), 0);
        LangExecLog._nextId = maxId + 1;
      }
    }
  } catch (_) {}
}

function saveExecLogToStorage() {
  try {
    localStorage.setItem(LangExecLog.storageKey, JSON.stringify(LangExecLog.records));
  } catch (_) {}
}

/** Start a new execution record. Finalizes any in-flight record as 'switched'.
 *  Only creates a record when App.isRunning is true and logging is enabled.
 */
function startExecRecord(taskName, subTaskIdx, instruction) {
  if (!LangExecLog.enabled) return;
  if (!App.isRunning) return;

  // Finalize existing running record
  _finalizeRunningRecord('switched');

  const now = Date.now();
  const record = {
    id: LangExecLog._nextId++,
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

  LangExecLog.records.unshift(record);
  if (LangExecLog.records.length > LangExecLog.maxRecords) {
    LangExecLog.records.length = LangExecLog.maxRecords;
  }
  saveExecLogToStorage();
  renderExecLog();
  _updateScoreRow();
}

/** Finalize running record with given status and optional score.
 *  Duration excludes accumulated pause time.
 */
function _finalizeRunningRecord(status, score = null) {
  const running = LangExecLog.records.find(r => r.status === 'running');
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
  const running = LangExecLog.records.find(r => r.status === 'running');
  if (!running || running.pausedAt != null) return;
  running.pausedAt = Date.now();
  // Sync DOM span so the live timer callback sees updated state immediately
  const tbody = $('lang-log-tbody');
  if (tbody) {
    const row = tbody.querySelector(`tr[data-id="${running.id}"]`);
    const timer = row && row.querySelector('.lang-log-timer');
    if (timer) timer.dataset.pausedat = running.pausedAt;
  }
}

/** Resume the timer for the currently running record. */
function resumeExecRecord() {
  const running = LangExecLog.records.find(r => r.status === 'running');
  if (!running || running.pausedAt == null) return;
  running.pausedMs = (Number(running.pausedMs) || 0) + (Date.now() - running.pausedAt);
  running.pausedAt = null;
  // Sync DOM span
  const tbody = $('lang-log-tbody');
  if (tbody) {
    const row = tbody.querySelector(`tr[data-id="${running.id}"]`);
    const timer = row && row.querySelector('.lang-log-timer');
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
  if (!LangExecLog.enabled) return;
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
  const rec = LangExecLog.records.find(r => r.id === id);
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
  const idx = LangExecLog.records.findIndex(r => r.id === id);
  if (idx >= 0) LangExecLog.records.splice(idx, 1);
  saveExecLogToStorage();
  renderExecLog();
}

/** Update note text for a record */
function updateExecRecordNote(id, note) {
  const rec = LangExecLog.records.find(r => r.id === id);
  if (!rec) return;
  rec.note = note;
  saveExecLogToStorage();
}

/** Toggle the log module on/off */
function toggleExecLog() {
  LangExecLog.enabled = !LangExecLog.enabled;
  const btn = $('btn-lang-log');
  if (btn) btn.classList.toggle('btn-active', LangExecLog.enabled);
  const panel = $('lang-log-panel');
  if (panel) panel.style.display = LangExecLog.enabled ? 'flex' : 'none';
  _updateScoreRow();
}

/** Show/hide score row depending on module state and running record */
function _updateScoreRow() {
  const row = $('lang-score-row');
  if (!row) return;
  const hasRunning = LangExecLog.records.some(r => r.status === 'running');
  row.style.display = (LangExecLog.enabled && hasRunning) ? 'flex' : 'none';
}

/** Render the execution log table */
function renderExecLog() {
  const tbody = $('lang-log-tbody');
  const countEl = $('lang-log-count');
  if (!tbody) return;

  if (countEl) countEl.textContent = `(${LangExecLog.records.length})`;

  const recBtn = $('btn-execlog-rec');
  const isRecording = LangExecLog.records.some(r => r.status === 'running');
  if (recBtn) recBtn.classList.toggle('recording', isRecording);

  // Stop old timer
  if (LangExecLog._timerInterval) {
    clearInterval(LangExecLog._timerInterval);
    LangExecLog._timerInterval = null;
  }

  tbody.innerHTML = '';
  LangExecLog.records.forEach(r => {
    const scoreClass = r.score === 0 ? 'lang-log-score-0' : r.score === 0.5 ? 'lang-log-score-05' : r.score === 1 ? 'lang-log-score-1' : '';
    const rowScoreClass = r.status === 'scored' ? `lang-log-scored ${scoreClass}` : '';
    const timeStr = new Date(r.startTime).toLocaleTimeString('zh-CN', { hour12: false });
    const noteEscaped = (r.note || '').replace(/"/g, '&quot;').replace(/</g, '&lt;');

    let durHtml;
    if (r.durationMs != null) {
      const s = r.durationMs / 1000;
      durHtml = s < 1 ? `${r.durationMs}ms` : `${s.toFixed(1)}s`;
    } else if (r.status === 'running') {
      durHtml = `<span class="lang-log-timer" data-start="${r.startTime}" data-pausedms="${r.pausedMs || 0}" data-pausedat="${r.pausedAt || ''}">...</span>`;
    } else {
      durHtml = '--';
    }

    const scoreVal = r.score != null ? String(r.score) : '';
    const scoreCls = r.score === 0 ? 'score-val-0' : r.score === 0.5 ? 'score-val-05' : r.score === 1 ? 'score-val-1' : '';
    const scoreHtml = `<select class="lang-log-score-sel ${scoreCls}" data-id="${r.id}">
      <option value="">--</option>
      <option value="0"${scoreVal==='0'?' selected':''}>0</option>
      <option value="0.5"${scoreVal==='0.5'?' selected':''}>0.5</option>
      <option value="1"${scoreVal==='1'?' selected':''}>1</option>
    </select>`;

    const instrShort = r.instruction.length > 36 ? r.instruction.substring(0, 36) + '…' : r.instruction;
    const taskShort = r.taskName.length > 10 ? r.taskName.substring(0, 10) + '…' : r.taskName;
    const taskSubTitle = `${r.taskName} #${r.subTaskIdx + 1}\n${r.instruction}`;

    const tr = document.createElement('tr');
    tr.className = `lang-log-row lang-log-${r.status} ${rowScoreClass}`;
    tr.dataset.id = r.id;
    tr.innerHTML = `
      <td title="${taskSubTitle.replace(/"/g, '&quot;')}" class="lang-log-tasknum"><span class="lang-log-recidx">#${r.id}</span> ${taskShort} <span class="lang-log-subidx">${r.subTaskIdx + 1}</span></td>
      <td title="${r.instruction}">${instrShort}</td>
      <td>${timeStr}</td>
      <td>${durHtml}</td>
      <td>${scoreHtml}</td>
      <td><input type="text" class="lang-log-note-input" value="${noteEscaped}" data-id="${r.id}" placeholder="备注…" /></td>
      <td><button class="btn lang-log-del-btn" data-id="${r.id}" title="Delete">✕</button></td>
    `;
    tbody.appendChild(tr);
  });

  // Bind events
  tbody.querySelectorAll('.lang-log-del-btn').forEach(btn => {
    btn.addEventListener('click', () => deleteExecRecord(Number(btn.dataset.id)));
  });
  tbody.querySelectorAll('.lang-log-note-input').forEach(inp => {
    inp.addEventListener('change', () => updateExecRecordNote(Number(inp.dataset.id), inp.value));
  });
  tbody.querySelectorAll('.lang-log-score-sel').forEach(sel => {
    sel.addEventListener('change', () => updateExecRecordScore(Number(sel.dataset.id), sel.value));
  });

  // Start live timer for running records
  const hasRunning = LangExecLog.records.some(r => r.status === 'running');
  if (hasRunning) {
    LangExecLog._timerInterval = setInterval(() => {
      const timers = tbody.querySelectorAll('.lang-log-timer');
      if (timers.length === 0) {
        clearInterval(LangExecLog._timerInterval);
        LangExecLog._timerInterval = null;
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
          el.textContent = ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
        }
      });
    }, 500);
  }
}

/** Export all records as CSV download */
function exportExecLogCSV() {
  const headers = ['ID', 'Task', 'Sub#', 'Instruction', 'StartTime', 'Duration(s)', 'Paused(s)', 'Score', 'Status', 'Note'];
  const rows = LangExecLog.records.map(r => {
    const dur = r.durationMs != null ? (r.durationMs / 1000).toFixed(2) : '';
    const paused = r.pausedMs != null ? (r.pausedMs / 1000).toFixed(2) : '';
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
    // Build human-readable records with seconds-based durations
    const out = LangExecLog.records.map(r => ({
      id: r.id,
      taskName: r.taskName,
      subTaskIdx: r.subTaskIdx,
      instruction: r.instruction,
      startTime: new Date(r.startTime).toLocaleString('zh-CN'),
      endTime: r.endTime ? new Date(r.endTime).toLocaleString('zh-CN') : null,
      duration_s: r.durationMs != null ? +(r.durationMs / 1000).toFixed(2) : null,
      paused_s: r.pausedMs != null ? +(r.pausedMs / 1000).toFixed(2) : 0,
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

/** Drag-to-resize handler for lang-cmd-layout columns. */
function initLangColResize() {
  document.querySelectorAll('.lang-resize-handle').forEach(handle => {
    handle.addEventListener('mousedown', e => {
      e.preventDefault();
      const leftCol = handle.previousElementSibling;
      if (!leftCol) return;
      const startX = e.clientX;
      const startW = leftCol.getBoundingClientRect().width;
      handle.classList.add('dragging');
      const onMove = e => {
        const w = Math.max(50, startW + (e.clientX - startX));
        leftCol.style.width = w + 'px';
        leftCol.style.flex  = 'none';
      };
      const onUp = () => {
        handle.classList.remove('dragging');
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      };
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });
  });
}
