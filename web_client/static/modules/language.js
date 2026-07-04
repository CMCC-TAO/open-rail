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

function formatLangTaskOptionLabel(taskName, index) {
  return `${index + 1}.${taskName}`;
}

function getLangSubtaskMaxCharsByWidth(subtaskSelectEl) {
  const width = subtaskSelectEl && subtaskSelectEl.clientWidth ? subtaskSelectEl.clientWidth : 0;
  if (!Number.isFinite(width) || width <= 0) return 36;
  // Reserve width for index/prefix + right check icon area + select paddings.
  const reservedPx = 81;
  const avgCharPx = 7.4;
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
  Object.keys(LangCmd.tasks).forEach((taskName, index) => {
    const opt = document.createElement('option');
    opt.value = taskName;
    opt.textContent = formatLangTaskOptionLabel(taskName, index);
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
    if (taskSel) taskSel.disabled = enabled;
    if (subtaskSel) subtaskSel.disabled = enabled;
    const sendBtn = $('btn-lang-send');
    if (sendBtn) sendBtn.disabled = enabled;
    ['btn-lang-edit', 'btn-lang-add', 'btn-lang-del'].forEach(id => {
      const btn = $(id);
      if (btn) btn.disabled = enabled;
    });
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

      const confRes = await apiFetch('/api/client/config/path');
      if (confRes.path) {
        await apiFetch('/api/client/config/save', {
          method: 'POST',
          body: JSON.stringify({ path: confRes.path }),
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
        return;
      }

      await persistLanguagePatch({ 'language.auto_mode': false });
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
/** Save LangCmd.tasks back to the configured language file. */
async function saveLangFile() {
  const path = App.config && App.config.language && App.config.language.file_path;
  if (!path) { toast('No language file configured.', 'warn'); return; }
  try {
    await apiFetch('/api/client/language/save', {
      method: 'POST',
      body: JSON.stringify({ path, data: LangCmd.tasks }),
    });
  } catch (e) { /* toasted */ }
}

/** Edit the instruction at the selected sub-task index with the textarea content. */
async function editLangSubtask() {
  const taskSel = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  const textEl = $('lang-cmd-text');
  if (!taskSel || !subtaskSel || !textEl) return;
  const taskName = taskSel.value;
  const idx = Number(subtaskSel.value);
  const lang = textEl.value.trim();
  if (!taskName || !LangCmd.tasks[taskName]) { toast('Select a task first.', 'warn'); return; }
  if (!Number.isFinite(idx) || idx < 0 || idx >= LangCmd.tasks[taskName].length) { toast('Select a sub-task first.', 'warn'); return; }
  if (!lang) { toast('Enter a language instruction.', 'warn'); return; }

  LangCmd.tasks[taskName][idx] = lang;
  App.currentInstruction = lang;
  await saveLangFile();
  renderLangSubtaskSelect();
  subtaskSel.value = String(idx);
  App._langSwitching = true;
  try {
    await sendLanguageSet(lang);
  } finally {
    App._langSwitching = false;
  }
  toast('Sub-task instruction updated.', 'ok');
}

/** Add a new sub-task after the current list using the textarea content. */
async function addLangSubtask() {
  const taskSel = $('lang-task-select');
  const textEl = $('lang-cmd-text');
  if (!taskSel || !textEl) return;
  const taskName = taskSel.value;
  const lang = textEl.value.trim();
  if (!taskName || !LangCmd.tasks[taskName]) { toast('Select a task first.', 'warn'); return; }
  if (!lang) { toast('Enter a language instruction.', 'warn'); return; }

  LangCmd.tasks[taskName].push(lang);
  const newIdx = LangCmd.tasks[taskName].length - 1;
  App.currentInstruction = lang;
  await saveLangFile();
  renderLangSubtaskSelect();
  const subtaskSel = $('lang-subtask-select');
  if (subtaskSel) subtaskSel.value = String(newIdx);
  applyLangConfigSelection();
  App._langSwitching = true;
  try {
    await sendLanguageSet(lang);
  } finally {
    App._langSwitching = false;
  }
  toast('Sub-task added.', 'ok');
}

/** Delete the selected sub-task from the current task. */
async function deleteLangSubtask() {
  const taskSel = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  if (!taskSel || !subtaskSel) return;
  const taskName = taskSel.value;
  const idx = Number(subtaskSel.value);
  if (!taskName || !LangCmd.tasks[taskName]) { toast('Select a task first.', 'warn'); return; }
  if (!Number.isFinite(idx) || idx < 0 || idx >= LangCmd.tasks[taskName].length) { toast('Select a sub-task first.', 'warn'); return; }
  if (!confirm('Delete this sub-task?')) return;

  LangCmd.tasks[taskName].splice(idx, 1);
  await saveLangFile();
  renderLangSubtaskSelect();
  const newIdx = Math.max(0, Math.min(idx, LangCmd.tasks[taskName].length - 1));
  if (LangCmd.tasks[taskName].length > 0) {
    subtaskSel.value = String(newIdx);
    applyLangConfigSelection();
    const textEl = $('lang-cmd-text');
    const lang = textEl ? textEl.value.trim() : '';
    if (lang) {
      App._langSwitching = true;
      try { await sendLanguageSet(lang); } finally { App._langSwitching = false; }
    }
  } else {
    $('lang-cmd-text').value = '';
  }
  toast('Sub-task deleted.', 'ok');
}

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
  if (taskSel) taskSel.disabled = editable;
  const subtaskSel = $('lang-subtask-select');
  if (subtaskSel) subtaskSel.disabled = editable;
  const sendBtn = $('btn-lang-send');
  if (sendBtn) sendBtn.disabled = editable;
  if (taskSel && task && LangCmd.tasks[task]) {
    taskSel.value = task;
  } else if (taskSel && taskSel.options.length > 0 && !taskSel.value) {
    taskSel.selectedIndex = 0;
  }

  // Rebuild subtask list for the selected task
  renderLangSubtaskSelect();

  // Sync Lang Panel Sub-task select
  const taskName = taskSel ? taskSel.value : null;
  const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
  const safeIndex = subtasks.length > 0
    ? Math.max(0, Math.min(index, subtasks.length - 1))
    : -1;

  if (subtaskSel) {
    if (safeIndex >= 0) {
      subtaskSel.value = String(safeIndex);
      const appliedTask = App.config && App.config.language ? App.config.language.task_id : null;
      const appliedIdx = App.config && App.config.language ? App.config.language.sub_task_id : null;
      const useCurrentInstruction = (
        App.currentInstruction &&
        appliedTask === taskName &&
        appliedIdx === safeIndex
      );
      $('lang-cmd-text').value = useCurrentInstruction ? App.currentInstruction : (subtasks[safeIndex] ?? '');
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
function isLanguageShortcutTypingTarget(el) {
  if (!el) return false;
  const tag = (el.tagName || '').toLowerCase();
  return tag === 'input' || tag === 'textarea' || el.isContentEditable;
}

function applyLangSubtaskShortcut(targetIndex) {
  const taskSel = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  const sendBtn = $('btn-lang-send');
  const task = taskSel ? taskSel.value : null;
  const subtasks = (task && LangCmd.tasks[task]) ? LangCmd.tasks[task] : [];

  if (!subtaskSel || !sendBtn || !subtasks.length) {
    toast('No language instruction available.', 'warn');
    return;
  }

  const idx = Number(targetIndex);
  if (!Number.isInteger(idx) || idx < 0 || idx >= subtasks.length) {
    toast(`Language instruction ${idx + 1} is not available.`, 'warn');
    return;
  }

  subtaskSel.value = String(idx);
  subtaskSel.selectedIndex = idx;
  subtaskSel.dispatchEvent(new Event('change'));
  sendBtn.click();
}

function setupLanguageShortcuts() {
  let lKeyDown = false;

  document.addEventListener('keydown', (e) => {
    if (isLanguageShortcutTypingTarget(e.target)) return;

    const key = String(e.key || '').toLowerCase();
    if (key === 'l') {
      lKeyDown = true;
      return;
    }
    if (!lKeyDown || e.repeat) return;

    const subtaskSel = $('lang-subtask-select');
    const count = subtaskSel ? subtaskSel.options.length : 0;
    if (!count) return;

    if (/^[0-9]$/.test(key)) {
      e.preventDefault();
      const target = key === '0' ? 9 : Number(key) - 1;
      applyLangSubtaskShortcut(target);
      return;
    }

    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      e.preventDefault();
      const current = Number.isInteger(subtaskSel.selectedIndex) && subtaskSel.selectedIndex >= 0
        ? subtaskSel.selectedIndex
        : 0;
      const next = e.key === 'ArrowUp'
        ? (current - 1 + count) % count
        : (current + 1) % count;
      applyLangSubtaskShortcut(next);
    }
  });

  document.addEventListener('keyup', (e) => {
    if (String(e.key || '').toLowerCase() === 'l') lKeyDown = false;
  });

  window.addEventListener('blur', () => {
    lKeyDown = false;
  });
}

setupLanguageShortcuts();
// Language Command panel — JSON file picker
// $('lang-file-input').addEventListener('change', async (e) => {
//   const file = e.target.files[0];
//   if (!file) return;
//   const path = file.path || file.name;
//   try {
//     const res = await apiFetch('/api/client/language/load', { method: 'POST', body: JSON.stringify({ path }) });
//     buildLangTasksFromData(res.data);
//     renderLangTaskSelect();
//
//     if (!App.config || typeof App.config !== 'object') App.config = {};
//     if (!App.config.language || typeof App.config.language !== 'object') App.config.language = {};
//     App.config.language.file_path = path;
//
//     App.pendingPatch['language.file_path'] = path;
//     markPending();
//
//     try {
//       const patchRes = await apiFetch('/api/client/config/patch', {
//         method: 'POST',
//         body: JSON.stringify({ patch: { 'language.file_path': path } }),
//       });
//       App.config = patchRes.config || App.config;
//       delete App.pendingPatch['language.file_path'];
//       if (!Object.keys(App.pendingPatch).length) clearPending();
//
//       const confRes = await apiFetch('/api/client/config/path');
//       if (confRes.path) {
//         await apiFetch('/api/client/config/save', {
//           method: 'POST',
//           body: JSON.stringify({ path: confRes.path }),
//         });
//       }
//     } catch (_) {
//       App.pendingPatch['language.file_path'] = path;
//       markPending();
//     }
//
//     toast('Language file loaded.', 'ok', 2000);
//   } catch (_) { /* toasted */ }
//   e.target.value = '';
// });

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
  try {
    await sendLanguageSet(lang);
  } finally {
  }
  toast('Language command updated.', 'info');

});
$('lang-cmd-text').addEventListener('keydown', e => { if (e.key === 'Enter' && e.ctrlKey) $('btn-lang-send').click(); });

$('btn-lang-edit').addEventListener('click', editLangSubtask);
$('btn-lang-add').addEventListener('click', addLangSubtask);
$('btn-lang-del').addEventListener('click', deleteLangSubtask);

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

}
