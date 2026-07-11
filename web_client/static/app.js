// ═══════════════════════════════════════════════════════
//  Stats rendering
// ═══════════════════════════════════════════════════════
function renderStats(data) {
  App.isObserveRunning = !!(data?.observe_running ?? (data?.running && !data?.paused));
  App.isInferenceRunning = !!(data?.inference_running ?? (data?.running && !data?.paused));
  App.isControlRunning = !!(data?.control_running ?? (data?.running && !data?.paused));
  setRunningUI(data.running, data.paused ?? false);

  $('val-obv-fps').textContent = data.obv_fps != null
    ? Number(data.obv_fps).toFixed(1) + ' fps' : '–';
  $('val-infer-count').textContent = data.infer_count ?? '–';
  $('img-proc-time').textContent   = data.img_proc_time != null
    ? Number(data.img_proc_time).toFixed(1) + ' ms' : '–';
  $('val-infer-time').textContent  = data.avg_infer_time != null
    ? (data.avg_infer_time * 1000).toFixed(1) + ' ms' : '–';
  $('val-intra-chunk-time').textContent   = data.avg_intra_traj_time != null
    ? (data.avg_intra_traj_time * 1000).toFixed(1) + ' ms' : '–';
  $('val-inter-chunk-time').textContent   = data.avg_inter_traj_time != null
    ? (data.avg_inter_traj_time * 1000).toFixed(1) + ' ms' : '–';
  $('val-net-latency').textContent   = data.avg_comm_time != null
    ? (data.avg_comm_time * 1000).toFixed(1) + ' ms' : '–';

  updateTaskProgress(data?.current_prob_progress ?? data?.info_act?.current_prob_progress, data?.sub_task_id);

  const cpuVal = Number(data.cpu_usage);
  const gpuVal = Number(data.gpu_usage);
  const memVal = Number(data.mem_usage);
  const bwVal = Number(data.bandwidth_m);
  const cpuEl = $('val-cpu-usage');
  const gpuEl = $('val-gpu-usage');
  const memEl = $('val-mem-usage');
  const bwEl = $('val-bw-usage');

  const setResourceValue = (el, value, label) => {
    if (!el) return;
    const valueEl = el.querySelector('.resource-value');
    if (valueEl) {
      valueEl.textContent = value;
    } else {
      el.textContent = `${label} ${value}`;
    }
  };

  setResourceValue(cpuEl, Number.isFinite(cpuVal) ? cpuVal.toFixed(1) + '%' : '--', 'CPU');
  setResourceValue(gpuEl, Number.isFinite(gpuVal) ? gpuVal.toFixed(1) + '%' : '--', 'GPU');
  setResourceValue(memEl, Number.isFinite(memVal) ? memVal.toFixed(1) + '%' : '--', 'MEM');
  setResourceValue(bwEl, Number.isFinite(bwVal) ? bwVal.toFixed(1) + 'M' : '--', 'NET');

  App.latestState = Array.isArray(data.current_state) ? data.current_state.slice() : [];
  
  // Update ZMQ info panel with data from the server
  updateZmqInfoPanel(data);
  // Update ZMQ indicator based on zmq_connected status from server
  if (typeof data.zmq_connected !== 'undefined') {
    updateZMQIndicator(!!data.zmq_connected);
  }

}

// Function to update ZMQ info panel
function updateZmqInfoPanel(data) {
  if (!data) return;
  
  // Update the individual fields in the ZMQ info panel
  const serverAddressElement = document.getElementById('zmq-server-address');
  // const portElement = document.getElementById('zmq-port');
  const modelTypeElement = document.getElementById('zmq-model-type');
  const modelPathElement = document.getElementById('zmq-model-path');
  const languageCmdElement = document.getElementById('zmq-language-cmd');
  const timestampElement = document.getElementById('zmq-timestamp');
  
  if (serverAddressElement && data.server_ip && data.server_port) {
    serverAddressElement.textContent = `--tcp://${data.server_ip}:${data.server_port}`
  }
  
  if (modelTypeElement && data.model_type) {
    modelTypeElement.textContent = `--${data.model_type}`;
  }
  
  if (modelPathElement && data.model_path) {
    modelPathElement.textContent = `--${data.model_path}`;
  }
  
  if (languageCmdElement && data.lang_cmd) {
    languageCmdElement.textContent = `--${data.lang_cmd}`;
  }
  if (timestampElement && data.timestamp) {
    timestampElement.textContent = `--${data.timestamp}`;
  }
}

function renderKV(containerId, obj) {
  const el = $(containerId);
  if (!el) return;
  el.innerHTML = '';
  for (const [k, v] of Object.entries(obj)) {
    const kEl = document.createElement('div'); kEl.className = 'kv-key'; kEl.textContent = k;
    const vEl = document.createElement('div'); vEl.className = 'kv-val'; vEl.textContent = v;
    el.appendChild(kEl); el.appendChild(vEl);
  }
}


function updateTaskProgress(rawProgress, subTaskId = null) {
  const fillEl = $('task-progress-fill');
  const valueEl = $('task-progress-value');
  if (!fillEl || !valueEl) return;

  const parsed = Number(rawProgress);
  if (!Number.isFinite(parsed)) {
    fillEl.style.width = '0%';
    valueEl.textContent = '--';
    // App.langAuto.lastProgress = null;
    return;
  }

  const clamped = Math.max(0, Math.min(1, parsed));
  fillEl.style.width = `${(clamped * 100).toFixed(1)}%`;
  valueEl.textContent = `${(clamped * 100).toFixed(1)}%`;
  renderSubTask(subTaskId);
  handleAutoModeCompletion(clamped, subTaskId);
}

async function handleAutoModeCompletion(progress, subTaskId = null) {
  const autoChk = $('chk-lang-auto-mode');
  if (!autoChk || !autoChk.checked) return;
  if (!App.isRunning || App.isPaused) return;

  if (!App.langAuto || typeof App.langAuto !== 'object') App.langAuto = {};
  if (App.langAuto.completionInFlight) return;

  const taskSel = $('lang-task-select');
  const taskName = taskSel ? taskSel.value : null;
  const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
  if (!Array.isArray(subtasks) || subtasks.length === 0) return;

  const latestSubTaskId = Number(subTaskId);
  if (!Number.isFinite(latestSubTaskId)) return;

  const lastSubTaskId = subtasks.length - 1;
  const thresholdRaw = App.config && App.config.language ? App.config.language.task_progress_threshold : 0.9;
  const threshold = Number.isFinite(Number(thresholdRaw)) ? Number(thresholdRaw) : 0.9;

  if (latestSubTaskId !== lastSubTaskId || progress < threshold) return;

  App.langAuto.completionInFlight = true;
  try {
    const patch = { 'language.sub_task_id': 0 };
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

    if (typeof applyLangConfigSelection === 'function') {
      applyLangConfigSelection(true);
    }

    await apiFetch('/api/client/pause', {
      method: 'POST',
      timeoutMs: 3000,
      suppressAbortToast: true,
    });

    toast('Auto Mode reached last sub-task, reset to 0 and paused.', 'info', 2600);
  } catch (_) {
    // no-op: apiFetch already handles toasts
  } finally {
    App.langAuto.completionInFlight = false;
  }
}

async function renderSubTask(subTaskId = null) {
  // console.log('renderSubTask called', { subTaskId });

  const autoChk = $('chk-lang-auto-mode');
  if (!autoChk || !autoChk.checked) {
    // console.log('renderSubTask skipped: auto mode disabled or checkbox not found');
    return;
  }

  if (subTaskId === null || subTaskId === undefined) {
    // console.log('renderSubTask skipped: no subTaskId provided');
    return;
  }

  const taskSel = $('lang-task-select');
  const subtaskSel = $('lang-subtask-select');
  const textEl = $('lang-cmd-text');
  if (!taskSel || !subtaskSel || !textEl) {
    // console.warn('renderSubTask aborted: missing DOM elements', { taskSel, subtaskSel, textEl });
    return;
  }

  const taskName = taskSel.value;
  const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
  if (!Array.isArray(subtasks) || subtasks.length === 0) {
    // console.warn('renderSubTask aborted: no subtasks available', { taskName, subtasks });
    return;
  }

  const targetIdx = Number(subTaskId);
  if (!Number.isFinite(targetIdx)) return;

  let curIdx = parseInt(subtaskSel.value, 10);
  if (!Number.isFinite(curIdx) || curIdx < 0) curIdx = 0;

  if (targetIdx < 0 || targetIdx >= subtasks.length) {
    console.warn('renderSubTask aborted: subTaskId out of range', { subTaskId: targetIdx, length: subtasks.length });
    return;
  }

  const appliedTaskIdRaw = App.config && App.config.language ? App.config.language.task_id : null;
  const appliedTaskId = appliedTaskIdRaw == null ? null : String(appliedTaskIdRaw);

  if (!App.config || typeof App.config !== 'object') App.config = {};
  if (!App.config.language || typeof App.config.language !== 'object') App.config.language = {};
  App.config.language.sub_task_id = targetIdx;

  if (typeof refreshLangAppliedMarkers === 'function') {
    const markerTaskId = appliedTaskId != null ? appliedTaskId : taskName;
    refreshLangAppliedMarkers(markerTaskId, targetIdx);
  }

  if (targetIdx === curIdx) {
    // console.log('renderSubTask no-op: target subTaskId equals current', { targetIdx, curIdx });
    return;
  }

  // console.log('renderSubTask switching subtask', { from: curIdx, to: targetIdx, taskName, subtaskText: subtasks[targetIdx] });
  subtaskSel.value = String(targetIdx);
  subtaskSel.dispatchEvent(new Event('change'));

  const lang = subtasks[targetIdx];
  if (typeof lang === 'string' && lang.trim()) {
    textEl.value = lang;
    await sendLanguageSet(lang);
  }
}

// ═══════════════════════════════════════════════════════
//  Running state UI
// ═══════════════════════════════════════════════════════
/**
 * Update button states and status badge.
 * @param {boolean} running  - Whether the vla_client process is alive.
 * @param {boolean} paused   - Whether observe/inference/control execution is paused.
 *
 * Button availability matrix:
 *   State            | Start/Stop | Pause/Resume | Reset
 *   -----------------+------------+--------------+------
 *   Not running      |  Start     |  ✗           |  ✗
 *   Running (active) |  Stop      |  Pause       |  ✓
 *   Running (paused) |  Stop      |  Resume      |  ✓
 */
async function syncRuntimeCameraConfig() {
  if (!App.isRunning) return;
  try {
    await apiFetch('/api/client/visualize/config', {
      method: 'POST',
      body: JSON.stringify({
        open_head: !!App.camOpen[0],
        open_wrist_left: !!App.camOpen[1],
        open_wrist_right: !!App.camOpen[2],
      }),
    });
  } catch (_) {
    // no-op
  }
}

function setThreadControlUI() {
  const btnObserve = $('btn-observe');
  const btnInfer = $('btn-infer');
  const btnControl = $('btn-control');
  if (!btnObserve || !btnInfer || !btnControl) return;

  const running = !!App.isRunning;
  const observeRunning = !!App.isObserveRunning;
  const inferenceRunning = !!App.isInferenceRunning;
  const controlRunning = !!App.isControlRunning;

  btnObserve.disabled = false;
  btnInfer.disabled = !running || !observeRunning;
  btnControl.disabled = !running || !observeRunning || !inferenceRunning;

  btnObserve.className = `btn btn-xs${observeRunning ? ' btn-active' : ''}`;
  btnInfer.className = `btn btn-xs${inferenceRunning ? ' btn-active' : ''}`;
  btnControl.className = `btn btn-xs${controlRunning ? ' btn-active' : ''}`;

  const observeSub = btnObserve.querySelector('.thread-btn-sub');
  const inferSub = btnInfer.querySelector('.thread-btn-sub');
  const controlSub = btnControl.querySelector('.thread-btn-sub');

  if (observeSub) observeSub.textContent = observeRunning ? 'Stop' : 'Start';
  if (inferSub) inferSub.textContent = inferenceRunning ? 'Stop' : 'Start';
  if (controlSub) controlSub.textContent = controlRunning ? 'Stop' : 'Start';
}

function applyThreadState(data) {
  if (!data) return;
  if (typeof data.observe_running === 'boolean') App.isObserveRunning = data.observe_running;
  if (typeof data.inference_running === 'boolean') App.isInferenceRunning = data.inference_running;
  if (typeof data.control_running === 'boolean') App.isControlRunning = data.control_running;
}

function syncStartPauseButtons(running, paused = false) {
  const btnStart = $('btn-start');
  const btnPause = $('btn-pause');

  if (running) {
    btnStart.innerHTML = '<i class="fas fa-stop"></i> Stop';
    btnStart.className = 'btn btn-danger btn-sm';
  } else {
    btnStart.innerHTML = '<i class="fas fa-play"></i> Start';
    btnStart.className = 'btn btn-success btn-sm';
  }

  if (!running) {
    btnPause.innerHTML = '<i class="fas fa-pause"></i> Pause';
    btnPause.className = 'btn btn-danger  btn-sm';
  } else if (paused) {
    btnPause.innerHTML = '<i class="fas fa-play"></i> Resume';
    btnPause.className = 'btn btn-success btn-sm';
  } else {
    btnPause.innerHTML = '<i class="fas fa-pause"></i> Pause';
    btnPause.className = 'btn btn-danger  btn-sm';
  }

  btnStart.disabled = btnStart.dataset.pending === '1';
  btnPause.disabled = (btnPause.dataset.pending === '1') || !running;
}

function setRunningUI(running, paused = false) {
  const unchanged = (App.isRunning === running && App.isPaused === paused);
  const wasRunning = App.isRunning === true;
  const wasPaused  = App.isPaused === true;
  App.isRunning = running;
  App.isPaused  = paused;

  if (!unchanged) {
    // Camera Visual: connect dedicated WS server when running
    if (running) {
      connectCamWS();
      // syncRuntimeCameraConfig();
    } else {
      disconnectCamWS();
    }

    // Status badge
    let badgeText, badgeClass;
    if (!running) {
      badgeText  = 'STOPPED';
      badgeClass = 'stopped';
    } else if (paused) {
      badgeText  = 'PAUSED';
      badgeClass = 'paused';
    } else {
      badgeText  = 'RUNNING';
      badgeClass = 'running';
    }
    $('status-badge').textContent = badgeText;
    $('status-badge').className   = `status-badge ${badgeClass}`;

    if (!running) {
      App.isRecording = false;
    }
    syncRecordingSwitchUI();
  }

  syncStartPauseButtons(running, paused);
  $('btn-reset').disabled = !running;             // available in both running states
  setThreadControlUI();
}

function isRuntimeShortcutTypingTarget(el) {
  if (!el) return false;
  const tag = (el.tagName || '').toLowerCase();
  return tag === 'input' || tag === 'textarea' || tag === 'select' || el.isContentEditable;
}

function clickButtonIfReady(id) {
  const btn = $(id);
  if (!btn || btn.disabled || btn.dataset.pending === '1') return;
  btn.click();
}

function setupRuntimeShortcuts() {
  document.addEventListener('keydown', (e) => {
    if (e.repeat || isRuntimeShortcutTypingTarget(e.target)) return;

    const key = e.key.toLowerCase();
    const isSpace = e.code === 'Space' || key === ' ';
    if (isSpace && !e.ctrlKey) {
      e.preventDefault();
      clickButtonIfReady('btn-pause');
      return;
    }

    if (isSpace && e.ctrlKey) {
      e.preventDefault();
      clickButtonIfReady('btn-control');
      return;
    }

    if (key === 'r' && e.shiftKey) {
      e.preventDefault();
      clickButtonIfReady('btn-reset');
    }
  });
}

// ═══════════════════════════════════════════════════════
//  Event wiring — config, client control, manual ctrl
// ═══════════════════════════════════════════════════════

/** Return path starting from /conf segment (e.g. /conf/user.py) */
function _confRelPath(fullPath) {
  const normalized = fullPath.replace(/\\/g, '/');
  const idx = normalized.lastIndexOf('/conf/');
  return idx >= 0 ? normalized.slice(idx) : normalized;
}

/**
 * 初始化并绑定页面中各功能面板的事件处理程序
 * - 配置面板：支持下拉选择配置文件、保存、另存为、搜索过滤、应用待改动、重置为服务器配置；加载成功后渲染配置树与语言预设，并在界面上显示配置相对路径
 * - 布局控制：支持折叠配置面板并动态调整主布局列宽
 * - 运行控制：绑定客户端的 Start/Stop/Pause/Resume/Reset 按钮，必要时在启动前自动提交待改动补丁
 * - 数据录制/回放：切换录制状态、选择回放目录并发送回放命令，同时在界面上显示选择的目录
 * - 语言指令：加载语言任务 JSON 文件、渲染任务选择器、发送语言指令，支持 Ctrl+Enter 快捷发送与面板折叠
 * - 手动控制：为夹爪、头部、腰部的控制按钮绑定发送命令，发送成功后以通知提示
 * - 统一使用后端 API 接口进行异步交互，并通过通知反馈结果；在多数失败场景下已内部捕获并提示
 * 使用约定：应在页面初始化时调用一次，以确保 DOM 已就绪且必需的元素均存在
 * @returns {void} 无返回值
 * @throws {Error} 当必需的 DOM 元素缺失导致事件绑定失败，或个别未被内部捕获的 API/渲染异常发生时可能抛出错误
 */
async function wireEvents() {
  // Add event listeners for ZMQ indicator hover
  const zmqIndicatorContainer = document.getElementById('zmq-indicator-container');
  const zmqInfoPanel = document.getElementById('zmq-info-panel');
  
  if (zmqIndicatorContainer && zmqInfoPanel) {
    zmqIndicatorContainer.addEventListener('mouseenter', () => {
      zmqInfoPanel.classList.remove('hidden');
    });
    
    zmqIndicatorContainer.addEventListener('mouseleave', () => {
      zmqInfoPanel.classList.add('hidden');
    });
    
    // zmqInfoPanel.addEventListener('mouseenter', () => {
    //   zmqInfoPanel.classList.remove('hidden');
    // });
    
    // zmqInfoPanel.addEventListener('mouseleave', () => {
    //   zmqInfoPanel.classList.add('hidden');
    // });
  }
  
  // Config file dropdown — load selected config
  const confSelect = $('conf-file-select');
  if (confSelect) {
    // Load available yaml files
    try {
      const res = await apiFetch('/api/client/config/yaml_files');
      const files = res.files || [];
      // confSelect.innerHTML = '<option value="">-- Select Config File --</option>';
      files.forEach(file => {
        const option = document.createElement('option');
        option.value = file;
        option.textContent = file;
        confSelect.appendChild(option);
      });
      
      // Set default value from CONF_FILE
      const defaultFile = String(CONF_FILE).split('/').pop();
      if (files.includes(defaultFile)) {
        confSelect.value = defaultFile;
      }
    } catch (e) {
      console.error('Failed to load yaml files:', e);
    }

    // Handle config file selection change
    confSelect.addEventListener('change', async (e) => {
      const selectedFile = e.target.value;
      if (!selectedFile) return;
      
      try {
        const res = await apiFetch('/api/client/config/load', { 
          method: 'POST', 
          body: JSON.stringify({ path: selectedFile }) 
        });
        App.config = res.config || {}; 
        App.pendingPatch = {};
        clearPending();
        renderConfigTree(App.config);
        renderRecordingConfigTree(App.config);
        await loadDefaultLangFile();
        applyLangConfigSelection();
        applyVisualConfig(App.config);
        const confRes = await apiFetch('/api/client/config/path', { 
          method: 'POST', 
          body: JSON.stringify({ path: selectedFile }) 
        });
        toast(`Config ${selectedFile} loaded.`, 'ok');
      } catch (e) {
        toast('Failed to load config file.', 'error');
        console.error(e);
      }
    });
  }

  // Save As — modal with conf/ as default prefix
  $('btn-saveas-file').addEventListener('click', async () => {
    const confRes = await apiFetch('/api/client/config/path');
    if (confRes.path) {
      $('saveas-path').value = confRes.path.replace(/\.yaml$/, '_1.yaml');
    }
    else {
      $('saveas-path').value = 'new_conf.yaml';
    }
    $('modal-saveas').classList.remove('hidden');
  });
  $('btn-saveas-confirm').addEventListener('click', async () => {
    const path = $('saveas-path').value.trim();
    if (!path) return;
    $('modal-saveas').classList.add('hidden');
    try {
      await apiFetch('/api/client/config/save', { method: 'POST', body: JSON.stringify({ path: path }) });
      toast(`Saved as ${path}`, 'ok');
    } catch (e) { /* toasted */ }
  });
  $('btn-saveas-cancel').addEventListener('click', () => $('modal-saveas').classList.add('hidden'));

  $('conf-search').addEventListener('input', e => filterConfigTree(e.target.value));
  setupMainParamsResize();

  $('btn-apply-config').addEventListener('click', async () => {
    const patchToApply = { ...App.pendingPatch, ...getVisualStatePatch() };
    if (!Object.keys(patchToApply).length) { toast('No pending changes.', 'warn', 2000); return; }

    const uiState = captureConfigTreeUiState();
    const restoreConfigTreeState = () => restoreConfigTreeUiState(uiState);

    try {
      const res = await apiFetch('/api/client/config/patch', { method: 'POST', body: JSON.stringify({ patch: patchToApply }) });
      App.config = res.config || {};
      App.pendingPatch = {};
      clearPending();
      renderConfigTree(App.config);
      renderRecordingConfigTree(App.config);
      await loadDefaultLangFile();
      applyLangConfigSelection();
      applyVisualConfig(App.config);
      restoreConfigTreeState();
      requestAnimationFrame(restoreConfigTreeState);
      // Auto-save after apply
      const confRes = await apiFetch('/api/client/config/path');
      if (confRes.path) {
        toast(`Config ${confRes.path} applied.`, 'ok');
        await apiFetch('/api/client/config/save', {
          method: 'POST',
          body: JSON.stringify({ path: confRes.path }),
        });
        toast(`Saved to ${confRes.path}`, 'ok');
      }
    } catch (e) { /* toasted */ }
  });

  // Left column collapse / reveal
  $('btn-config-hide').addEventListener('click', () => {
    const leftCol = $('left-col');
    const collapsed = leftCol.classList.toggle('collapsed');
    $('btn-config-hide').classList.toggle('hidden', collapsed);
    $('btn-config-reveal').classList.toggle('hidden', !collapsed);
    updateLayoutColumns();
  });
  $('btn-config-reveal').addEventListener('click', () => {
    $('left-col').classList.remove('collapsed');
    $('btn-config-hide').classList.remove('hidden');
    $('btn-config-reveal').classList.add('hidden');
    updateLayoutColumns();
  });

  // Client control
  $('btn-start').addEventListener('click', async () => {
    const btnStart = $('btn-start');
    const btnPause = $('btn-pause');
    
    // Prevent duplicate rapid clicks
    if (btnStart.dataset.pending === '1') return;
    btnStart.dataset.pending = '1';
    btnStart.disabled = true;
    if (btnPause) btnPause.disabled = true;

    try {
      if (App.isRunning) {
        // Stop request
        const prevPaused = App.isPaused;

        // If data recording is active, stop recording first.
        if (App.isRecording && typeof stopDataRecordingIfNeeded === 'function') {
          await stopDataRecordingIfNeeded({ silent: false, refreshList: false });
        }

        setRunningUI(false, false);
        try {
          await apiFetch('/api/client/stop', { method: 'POST', timeoutMs: 8000 });
        } catch (e) {
          setRunningUI(true, prevPaused);
        }
        finally {
          try {
            const json = await apiFetch('/api/client/status', { timeoutMs: 3000, suppressToast: true });
            if (json && json.data) renderStats(json.data);
          } catch (e) { /* ignore */ }
        }
        return;
      }

      // Apply config patch BEFORE starting
      const patchToApply = { ...App.pendingPatch, ...getVisualStatePatch() };
      if (Object.keys(patchToApply).length) {
        try {
          const res = await apiFetch('/api/client/config/patch', { method: 'POST', body: JSON.stringify({ patch: patchToApply }) });
          App.config = res.config || App.config;
          applyVisualConfig(App.config);
          App.pendingPatch = {};
          clearPending();
        } catch (e) { 
          delete btnStart.dataset.pending;
          setRunningUI(App.isRunning, App.isPaused);
          return;
        }
      }

      // Now start client
      toast('Client starting…', 'info');
      await apiFetch('/api/client/start', { method: 'POST', timeoutMs: 15000 });
    } catch (e) { /* toasted */ }
    finally {
      delete btnStart.dataset.pending;
      // Re-sync UI state (status broadcast will update, but unlock buttons)
      setRunningUI(App.isRunning, App.isPaused);
    }
  });

  $('btn-pause').addEventListener('click', async () => {
    const controller = beginFetchRequest();

    try {
      if (App.isPaused) {
        await apiFetch('/api/client/resume', { method: 'POST', timeoutMs: 3000, signal: controller.signal, suppressAbortToast: true });
      } else {
        await apiFetch('/api/client/pause', { method: 'POST', timeoutMs: 3000, signal: controller.signal, suppressAbortToast: true });
      }
    } catch (e) { /* toasted */ }
    finally {
      if (App.currentFetchController === controller) App.currentFetchController = null;
      setRunningUI(App.isRunning, App.isPaused);
    }
  });

  $('btn-reset').addEventListener('click',  async () => {
    await sendControl('reset');
    toast('Robot reset initiated.', 'info');
  });

  $('btn-observe').addEventListener('click', async () => {
    const btnObserve = $('btn-observe');
    if (!btnObserve) return;

    const controller = beginFetchRequest();

    try {
      const res = await apiFetch('/api/client/observe/start', { method: 'POST', timeoutMs: 3000, signal: controller.signal, suppressAbortToast: true });
      applyThreadState(res?.data);
      connectCamWS();
      // syncRuntimeCameraConfig();
      // setThreadControlUI();
    } catch (e) {
      if (e && e.name === 'AbortError') {
        // manual abort from repeated click; keep silent.
      }
    } finally {
      if (App.currentFetchController === controller) App.currentFetchController = null;
      setThreadControlUI();
    }
  });

  $('btn-infer').addEventListener('click', async () => {
    const btnInfer = $('btn-infer');
    if (!btnInfer || !App.isObserveRunning) return;

    const controller = beginFetchRequest();

    try {
      const res = await apiFetch('/api/client/infer/start', { method: 'POST', timeoutMs: 3000, signal: controller.signal, suppressAbortToast: true });
      applyThreadState(res?.data);
      setThreadControlUI();
    } catch (_) { /* toasted */ }
    finally {
      if (App.currentFetchController === controller) App.currentFetchController = null;
      setThreadControlUI();
    }
  });

  $('btn-control').addEventListener('click', async () => {
    const btnControl = $('btn-control');
    if (!btnControl || !App.isObserveRunning || !App.isInferenceRunning) return;

    const controller = beginFetchRequest();

    try {
      const res = await apiFetch('/api/client/control/start', { method: 'POST', timeoutMs: 3000, signal: controller.signal, suppressAbortToast: true });
      applyThreadState(res?.data);
      setThreadControlUI();
    } catch (_) { /* toasted */ }
    finally {
      if (App.currentFetchController === controller) App.currentFetchController = null;
      setThreadControlUI();
    }
  });


  // Delegated module setups
  setupLanguageEvents();
  setupManualControlEvents();
  setupRuntimeShortcuts();
}

// ═══════════════════════════════════════════════════════
//  Status poll fallback
// ═══════════════════════════════════════════════════════
function startStatusPoll() {
  setInterval(async () => {
    if (App.wsAlive || App.statusPollInFlight) return;
    App.statusPollInFlight = true;
    try {
      const json = await apiFetch('/api/client/status', { timeoutMs: 3000, suppressToast: true });
      if (json && json.data) renderStats(json.data);
    } catch (e) { /* ignore */ }
    finally {
      App.statusPollInFlight = false;
    }
  }, 4000);
}

document.addEventListener('DOMContentLoaded', () => {
  setupCameraPanel();
  setupTrajPanel();
  setupLangPanel();
  setupLeftPanelAccordion();
  setupRecordingPanel();
  createUnifiedChart();                  // create single unified trajectory chart
  buildJointSelector();                  // build from the active robot action_layout
  connectWS();
  startStatusPoll();
  initConfDir().then(async () => {
    await loadConfigFromServer();
    await loadDefaultLangFile();
    applyLangConfigSelection(true);
    wireEvents();
  });
});
