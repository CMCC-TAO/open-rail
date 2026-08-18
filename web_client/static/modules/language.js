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

// function getLangSubtaskMaxCharsByWidth(subtaskSelectEl) {
//   const width = subtaskSelectEl && subtaskSelectEl.clientWidth ? subtaskSelectEl.clientWidth : 0;
//   if (!Number.isFinite(width) || width <= 0) return 36;
//   // Reserve width for index/prefix + right check icon area + select paddings.
//   const reservedPx = 81;
//   const avgCharPx = 7.4;
//   const estimated = Math.floor((width - reservedPx) / avgCharPx);
//   return Math.max(14, estimated);
// }

function formatLangSubtaskOptionLabel(text, index) {
  // const clipped = text.length > maxChars ? `${text.substring(0, maxChars)}…` : text;
  return `${index + 1}.${text}`;
}

// function formatLangSubtaskOptionLabelOld(taskName, text, index, maxChars = 36) {
//   const clipped = text.length > maxChars ? `${text.substring(0, maxChars)}…` : text;
//   return `${index + 1}.${clipped}`;
// }

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
  syncAutoModeStartSubtaskOptions(taskName);
  // const maxChars = getLangSubtaskMaxCharsByWidth(subtaskSel);

  const { taskId: appliedTaskId, subTaskId: appliedSubTaskId } = getAppliedLangSelection();
  subtasks.forEach((text, i) => {
    const opt = document.createElement('option');
    opt.value = i;
    // opt.textContent = formatLangSubtaskOptionLabel(taskName, text, i, maxChars);
    opt.textContent = formatLangSubtaskOptionLabel(text, i);
    setAppliedOptionMarker(opt, taskName === appliedTaskId && i === appliedSubTaskId);
    opt.title = text;
    subtaskSel.appendChild(opt);
  });
  // Sync Config panel sub_task_id options (preserve current selection)
  syncLangIndexOptions(taskName);
}

async function persistLanguagePatch (patch) {
  if (!App.config || typeof App.config !== 'object') App.config = {};
  if (!App.config.language || typeof App.config.language !== 'object') App.config.language = {};

  try {
    const res = await apiFetch('/api/client/config/patch', {
      method: 'POST',
      body: JSON.stringify({ patch }),
    });
    App.config = res.config || App.config;

    const confRes = await apiFetch('/api/client/config/path');
    if (confRes.path) {
      await apiFetch('/api/client/config/save', {
        method: 'POST',
        body: JSON.stringify({ path: confRes.path }),
      });
    }
    return true;
  } catch (_) {
    return false;
  }
};
function syncAutoModeStartSubtaskOptions(taskName, selectedId) {
  const startSel = $('sel-lang-auto-start-subtask');
  if (!startSel) return;

  const activeTask = taskName || $('lang-task-select')?.value;
  const subtasks = (activeTask && LangCmd.tasks[activeTask]) ? LangCmd.tasks[activeTask] : [];
  startSel.innerHTML = '';

  subtasks.forEach((text, i) => {
    const opt = document.createElement('option');
    opt.value = String(i);
    // display as 1-based index to match SubTask list UI
    opt.textContent = String(i + 1);
    opt.title = text;
    startSel.appendChild(opt);
  });

  if (!subtasks.length) {
    startSel.value = '';
    return;
  }

  const parsedSelected = Number(selectedId);
  const fallback = Number(App.config?.language?.auto_mode_start_sub_task_id);
  const candidate = Number.isFinite(parsedSelected)
    ? parsedSelected
    : (Number.isFinite(fallback) ? fallback : 0);
  const safe = Math.max(0, Math.min(candidate, subtasks.length - 1));
  startSel.value = String(safe);
}

function applyConfigAutoStartSubtask(rawSubTaskId) {
  syncAutoModeStartSubtaskOptions($('lang-task-select')?.value, rawSubTaskId);
}

function setAutoModeEditable(checked) {
  const thresholdInput = $('inp-lang-threshold');
  if (thresholdInput) thresholdInput.disabled = !checked;

  const winSizeInput = $('inp-lang-win-size');
  if (winSizeInput) winSizeInput.disabled = !checked;

  const startSel = $('sel-lang-auto-start-subtask');
  if (startSel) startSel.disabled = !checked;

  const taskSel = $('lang-task-select');
  if (taskSel) taskSel.disabled = checked;

  const subtaskSel = $('lang-subtask-select');
  if (subtaskSel) subtaskSel.disabled = checked;

  const textEditArea = $('lang-cmd-text');
  if (textEditArea) textEditArea.disabled = checked;

  ['btn-lang-edit', 'btn-lang-add', 'btn-lang-del', 'btn-lang-send'].forEach(id => {
    const btn = $(id);
    if (btn) btn.disabled = checked;
  });
}

function applyConfigAutoMode(autoMode) {
  const autoCheckLangMode = $('chk-lang-auto-mode');
  if (autoCheckLangMode) autoCheckLangMode.checked = !!autoMode;
  setAutoModeEditable(!!autoMode);
}

function applyConfigThreshold(threshold) {
  const thresholdInput = $('inp-lang-threshold');
  if (!thresholdInput) return;
  const displayThreshold = Number.isFinite(threshold) ? threshold : 0.95;
  thresholdInput.value = String(displayThreshold);
  thresholdInput.style.borderColor = '';
}

function applyConfigWinSize(winSize) {
  const winSizeInput = $('inp-lang-win-size');
  if (!winSizeInput) return;
  const displayWinSize = Number.isInteger(winSize) && winSize > 0 ? winSize : 10;
  winSizeInput.value = String(displayWinSize);
  winSizeInput.style.borderColor = '';
}

function applyConfigTaskSelection(task) {
  const taskSel = $('lang-task-select');
  if (!taskSel) return;

  if (task && LangCmd.tasks[task]) {
    taskSel.value = task;
  } else if (!taskSel.value && taskSel.options.length > 0) {
    taskSel.selectedIndex = 0;
  }

  renderLangSubtaskSelect();
}

function applyConfigSubtaskSelection(rawIndex, autoMode, forceFirstSubtask) {
  const taskSel = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  const textEl = $('lang-cmd-text');
  if (!taskSel || !subtaskSel || !textEl) return;

  let index = Number(rawIndex);
  if (!Number.isFinite(index)) index = 0;
  if (forceFirstSubtask || autoMode) index = 0;

  const taskName = taskSel.value;
  const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
  const safeIndex = subtasks.length > 0 ? Math.max(0, Math.min(index, subtasks.length - 1)) : -1;

  if (safeIndex >= 0) {
    subtaskSel.value = String(safeIndex);
    textEl.value = subtasks[safeIndex] ?? '';
  } else {
    subtaskSel.value = '';
    textEl.value = '';
  }

  if (App.config && App.config.language && safeIndex >= 0) {
    App.config.language.task_id = taskName || App.config.language.task_id;
    App.config.language.sub_task_id = safeIndex;
  }

  syncLangTaskOptions(taskName || taskSel.value, safeIndex >= 0 ? safeIndex : 0);
  refreshLangAppliedMarkers(taskName || taskSel.value, safeIndex >= 0 ? safeIndex : null);
}

function applyLangConfigSelection(forceFirstSubtask = false) {
  const languageConfig = App.config && App.config.language ? App.config.language : {};
  const autoMode = !!languageConfig.auto_mode;
  const threshold = Number(languageConfig.task_progress_threshold);
  const winSize = Number(languageConfig.task_progress_win_size);

  applyConfigAutoMode(autoMode);
  applyConfigThreshold(threshold);
  applyConfigWinSize(winSize);
  applyConfigTaskSelection(languageConfig.task_id);
  applyConfigAutoStartSubtask(languageConfig.auto_mode_start_sub_task_id);
  applyConfigSubtaskSelection(languageConfig.sub_task_id, autoMode, forceFirstSubtask);
}

function setupLangPanel() {
  const taskSel = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  const autoCheckLangMode = $('chk-lang-auto-mode');
  const thresholdInput = $('inp-lang-threshold');
  const winSizeInput = $('inp-lang-win-size');
  const autoStartSel = $('sel-lang-auto-start-subtask');
  let thresholdSaveTimer = null;
  let winSizeSaveTimer = null;

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
    applyConfigThreshold(value);
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
    applyConfigWinSize(value);
  };

  // Task select → rebuild subtask list and default to first sub-task.
  if (taskSel) {
    taskSel.addEventListener('change', () => {
      renderLangSubtaskSelect();

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
      syncAutoModeStartSubtaskOptions(taskName);
      $('lang-cmd-text').value = subtasks[0] ?? '';

      // Sync Config panel selects to task + first sub-task.
      const cfgTaskSel = $('cfg-language-task');
      if (cfgTaskSel) cfgTaskSel.value = taskSel.value;
      syncLangIndexOptions(taskSel.value, 0);
      const cfgIdxSel = $('cfg-language-index');
      if (cfgIdxSel) cfgIdxSel.value = '0';
      refreshLangAppliedMarkers();
      // applyConfigTaskSelection(taskName);
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
      // applyConfigSubtaskSelection(idx, false, false);
    });
  }

  if (autoStartSel) {
    autoStartSel.addEventListener('change', async () => {
      const taskName = taskSel ? taskSel.value : null;
      const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
      let startSubTaskId = Number(autoStartSel.value);
      if (!Number.isFinite(startSubTaskId)) startSubTaskId = 0;
      startSubTaskId = subtasks.length > 0 ? Math.max(0, Math.min(startSubTaskId, subtasks.length - 1)) : 0;


      // If auto-mode is enabled, also apply the start subtask to the visible SubTask select
      if (autoCheckLangMode && autoCheckLangMode.checked && subtaskSel && subtaskSel.options.length > 0) {
        autoStartSel.value = String(startSubTaskId);
        subtaskSel.value = String(startSubTaskId);
        subtaskSel.selectedIndex = startSubTaskId;
        subtaskSel.dispatchEvent(new Event('change'));
        await persistLanguagePatch({
          'language.sub_task_id': startSubTaskId,
          'language.auto_mode_start_sub_task_id': startSubTaskId
        });
      }

      // // Ensure UI reflects applied configuration: update config selection and applied markers
      // try {
      //   applyConfigSubtaskSelection(startSubTaskId, false, false);
      // } catch (e) {
      //   // ignore UI update errors
      // }
      refreshLangAppliedMarkers(taskName || (taskSel ? taskSel.value : null), startSubTaskId);
    });
  }

  if (autoCheckLangMode) {
    autoCheckLangMode.addEventListener('change', async () => {
      setAutoModeEditable(autoCheckLangMode.checked);

      if (autoCheckLangMode.checked) {
        const taskName = taskSel ? taskSel.value : null;
        const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
        const startRaw = autoStartSel ? autoStartSel.value : null;
        let startSubTaskId = Number(startRaw);
        if (!Number.isFinite(startSubTaskId)) {
          startSubTaskId = Number(App.config?.language?.auto_mode_start_sub_task_id);
        }
        if (!Number.isFinite(startSubTaskId)) startSubTaskId = 0;
        startSubTaskId = subtasks.length > 0 ? Math.max(0, Math.min(startSubTaskId, subtasks.length - 1)) : 0;

        if (subtaskSel) {
          if (subtaskSel.options.length > 0) {
            subtaskSel.selectedIndex = startSubTaskId;
            subtaskSel.value = String(startSubTaskId);
            subtaskSel.dispatchEvent(new Event('change'));
            applyConfigSubtaskSelection(startSubTaskId, false, false);
          } else {
            subtaskSel.value = '';
          }
        }

        if (subtasks[startSubTaskId] !== undefined) {
          $('lang-cmd-text').value = subtasks[startSubTaskId];
        }

        await persistLanguagePatch({
          'language.auto_mode': autoCheckLangMode.checked,
          'language.auto_mode_start_sub_task_id': startSubTaskId,
          'language.sub_task_id': startSubTaskId,
        });
        applyConfigAutoStartSubtask(startSubTaskId);
        return;
      }
      else {
        await persistLanguagePatch({ 'language.auto_mode': autoCheckLangMode.checked });
      }
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
  await saveLangFile();
  renderLangSubtaskSelect();
  subtaskSel.value = String(idx);
  try {
    if (idx == App.config.language.sub_task_id) {
      await sendLanguageSet(lang);
    } 
  } finally {
  }
  toast('Sub-task instruction updated.', 'ok');
}

async function sendLanguageSet(language = '') {
  try {
    await apiFetch('/api/client/language/set', { method: 'POST', body: JSON.stringify({ language }) });
  } catch (e) { /* toasted */ }
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
  await saveLangFile();
  renderLangSubtaskSelect();
  const subtaskSel = $('lang-subtask-select');
  if (subtaskSel) {
    subtaskSel.value = String(newIdx);
    subtaskSel.dispatchEvent(new Event('change'));
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
  if (LangCmd.tasks[taskName].length == 1) { toast('Sub-task at least one.', 'warn'); return; }
  if (!Number.isFinite(idx) || idx < 0 || idx >= LangCmd.tasks[taskName].length) { toast('Select a sub-task first.', 'warn'); return; }
  if (!confirm('Delete this sub-task?')) return;

  LangCmd.tasks[taskName].splice(idx, 1);
  await saveLangFile();
  renderLangSubtaskSelect();
  const newIdx = Math.max(0, Math.min(idx, LangCmd.tasks[taskName].length - 1));
  if (LangCmd.tasks[taskName].length > 0) {
    subtaskSel.value = String(newIdx);
    $('lang-cmd-text').value = LangCmd.tasks[taskName][newIdx];
  } else {
    $('lang-cmd-text').value = '';
  }
  toast('Sub-task deleted.', 'ok');
}

async function sendLanguageCommand() {
  const taskSel = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  const task = taskSel ? taskSel.value : null;
  if (task == null) { toast('Select a valid task.', 'warn'); return; }
  let lang = $('lang-cmd-text').value.trim();
  if (!lang) { toast('Enter a language instruction.', 'warn'); return; }

  const subtasks = LangCmd.tasks[task] ? LangCmd.tasks[task] : [];
  let idx = subtaskSel ? parseInt(subtaskSel.value, 10) : NaN;
  if (!Number.isFinite(idx) || idx < 0) idx = 0;
  if (App.config.language.task_id==task && App.config.language.sub_task_id == idx) {
    toast('Language command updated.', 'info');
    return;
  }
  if (App.config.record.switch && App.config.language.task_id != task) {
    toast('Can not change task when recording.', 'warn');
    return;
  }
  // console.info('old task: ', App.config.language.task_id, 'new task: ', task);
  // console.info('old sub_task: ', App.config.language.sub_task_id, 'new sub_task: ', idx);
  // console.info('recording: ', App.config.record.switch);
  // 1. persistLanguagePatch
  await persistLanguagePatch({
    'language.task_id': task,
    'language.sub_task_id': idx
  });
  // applyConfigTaskSelection(task);
  applyConfigSubtaskSelection(idx, false, false);

  // 2. Send language command to robot
  try {
    await sendLanguageSet(lang);
  }
  finally {
    if (App.config.record.switch) {
      handleSubTaskRecordingRefresh(true);
    }
  }
  toast('Language command updated.', 'info');
}
async function loadDefaultLangFile() {
  try {
    const langPath = App.config && App.config.language && App.config.language.file_path;
    let res;
    // TODO: load default language file
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
// Language Command panel — send
$('btn-lang-send').addEventListener('click', sendLanguageCommand); 

$('lang-cmd-text').addEventListener('keydown', e => { if (e.key === 'Enter' && e.ctrlKey) $('btn-lang-send').click(); });

$('btn-lang-edit').addEventListener('click', editLangSubtask);
$('btn-lang-add').addEventListener('click', addLangSubtask);
$('btn-lang-del').addEventListener('click', deleteLangSubtask);

// Language Command panel collapse
$('btn-lang-collapse').addEventListener('click', (e) => {
  e.preventDefault();
  e.stopPropagation();

  if (typeof handleCenterPanelCollapseToggle === 'function') {
    handleCenterPanelCollapseToggle('lang');
    return;
  }

  const langBody = $('lang-body');
  if (!langBody) return;
  langBody.classList.toggle('collapsed');
  if (typeof updateCenterPanelLayoutState === 'function') {
    updateCenterPanelLayoutState();
  }
  if (typeof syncCenterPanelCollapseUi === 'function') {
    syncCenterPanelCollapseUi();
  }
});

}
