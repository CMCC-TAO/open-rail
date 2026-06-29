// ═══════════════════════════════════════════════════════
//  Config rendering — BASIC group split into sub-groups
// ═══════════════════════════════════════════════════════

// Keys to exclude from the config tree (handled separately or rendered via createLangLinkRow)
const CONFIG_EXCLUDED_GROUP_KEYS = new Set(['language', 'record', 'controller']);

// Sub-sub conf groups to exclude from Configuration panel (dot-path)
const CONFIG_EXCLUDED_SUB_GROUP_KEYS = new Set([
  'visualize.camera',
  'visualize.trajectory',
]);

// Sub-group definitions for root-level leaf keys in the BASIC section
const BASIC_SUBGROUPS = {
  intra_chunk: ['intra_chunk_mode', 'fitting_deg', 'fitting_num_samples'],
  inter_chunk: ['inter_chunk_mode', 'search_length', 'smooth_action', 'smooth_base', 'smooth_length', 'smooth_ratio'],
};

// Select options for specific keys
const CONFIG_SELECT_OPTIONS = {
  inter_chunk_mode: ['search_action', 'poly', 'smooth_velocity', 'min_jerk', 'bspline'],
  intra_chunk_mode: ['raw', 'interpolation', 'fitting'],
  fitting_deg: [3, 4, 5, 6],
  // preprocess: ['crop_and_resize', 'pad_and_resize', 'resize', 'none'],
  method: ['resize', 'none'],
  type: ['a2d', 'mock', 'ti5_t170c', 'navi_wa2'],
  mode: ['async', 'sync'],
  codec: ['mp4v', 'avc1']
};

// Keys that must be treated as integers (rendered as number input, parsed with parseInt)
const CONFIG_INT_KEYS = new Set([
  'fitting_num_samples', 'search_length', 'smooth_length', 'gripper_offset',
  'fps', 'height', 'width', 'updata_period', 'max_len', 'observe_fps_window_size', 'filter_window_size', 'gripper_dim', 'head_dim', 'joint_dim', 'state_shape', 'action_shape', 'chunk_size', 'channel'
]);

const CONFIG_HIDDEN_DOT_KEYS = new Set([
  'language.task_id',
  'language.sub_task_id',
  'language.auto_mode',
  'language.task_progress_threshold',
  'language.task_progress_win_size',
  'visualize.camera.connect_when_running',
  'visualize.camera.open_head',
  'visualize.camera.open_wrist_left',
  'visualize.camera.open_wrist_right',
  'visualize.trajectory.play',
  'visualize.trajectory.source',
  'visualize.trajectory.selected_joints',
  'visualize.trajectory.window_span_sec',
  'record.switch',
  'record.save_dir',
  'record.record_exp_data',
  'record.info.data_path',
  'record.info.total_chunks',
  'record.info.total_episodes',
  'record.info.total_frames',
  'record.info.total_tasks',
  'record.info.total_videos',
  'record.info.video_path',
  'controller.raw_fps',
  'controller.wait_time',
  'controller.period',
  'controller.speed',
  'controller.gripper_offset',
  'vision.preprocess.method',
  'vision.preprocess.width',
  'rdm.mode',
]);

// Read-only keys in config tree UI (display only, not editable in panel)
const CONFIG_READONLY_DOT_KEYS = new Set([
  'visualize.max_size',
  'visualize.ping_interval',
  'visualize.ping_timeout',
  'visualize.host',
  'visualize.port',
  'vla_zmq.client_ip',
  'vla_zmq.client_port',
  'vla_zmq.server_ip',
  'vla_zmq.server_port',
  'rdm.max_len'
]);

// Default key list for the fixed "Main Parameters" area.
// Format: { "dot.key": "Display Label" }
// You can override it in config by setting one of:
//   - main_parameters: { "dot.key": "Label", ... }
//   - visualize.main_parameters: { "dot.key": "Label", ... }
const DEFAULT_MAIN_PARAMETER_KEYS = {
  'robots.type': 'Robot Type',
  'rdm.mode': 'Mode',
  'controller.wait_time': 'Wait Time[ms]',
  'controller.period': 'Control Period[ms]',
  'controller.speed': 'Control Speed',
  'controller.gripper_offset': 'Gripper Offset',
  'inter_chunk.inter_chunk_mode': 'Inter-Chunk Mode',
  'intra_chunk.intra_chunk_mode': 'Intra-Chunk Mode',
  'vision.preprocess.method': 'Img Proc Method',
  'vision.preprocess.width': 'Img Proc Width',
};

// 2. Define custom order for sub-groups
// List the keys in the order you want them to appear.
// Keys not listed here will appear at the end in their original order.
const CUSTOM_GROUP_ORDER = [
  'robots',
  'inter_chunk',
  'intra_chunk',
  'vision',
  'rdm',
  'visualize',
  'vla_zmq',
  // Add other keys here if you want to reorder them too, e.g., 'record', 'traj'
];
let _cfgInputSyncing = false;

function getConfigValueByDotKey(cfg, dotKey) {
  if (!cfg || typeof cfg !== 'object') return undefined;
  const parts = String(dotKey || '').split('.').filter(Boolean);
  if (!parts.length) return undefined;

  let node = cfg;
  for (const p of parts) {
    if (node == null || typeof node !== 'object' || !(p in node)) return undefined;
    node = node[p];
  }
  return node;
}

function resolveMainParameterKeys(cfg) {
  // First check if there are custom main parameters defined in the config
  const fromRoot = getConfigValueByDotKey(cfg, 'main_parameters');
  const fromVisual = getConfigValueByDotKey(cfg, 'visualize.main_parameters');
  
  // Determine the source - either from config or default
  let sourceObj = DEFAULT_MAIN_PARAMETER_KEYS;
  
  // Check if the config defines main parameters as an array (old format) or object (new format)
  if (fromRoot && typeof fromRoot === 'object' && !Array.isArray(fromRoot)) {
    // New format: object with key-value pairs
    sourceObj = fromRoot;
  } else if (fromVisual && typeof fromVisual === 'object' && !Array.isArray(fromVisual)) {
    // New format: object with key-value pairs
    sourceObj = fromVisual;
  } else if (Array.isArray(fromRoot)) {
    // Old format: array of keys - convert to object with same keys and labels
    sourceObj = {};
    fromRoot.forEach(key => {
      sourceObj[key] = key; // Use the key itself as the label
    });
  } else if (Array.isArray(fromVisual)) {
    // Old format: array of keys - convert to object with same keys and labels
    sourceObj = {};
    fromVisual.forEach(key => {
      sourceObj[key] = key; // Use the key itself as the label
    });
  }

  const seen = new Set();
  const result = [];
  
  // Process the object entries to return array of {key, label} pairs
  Object.entries(sourceObj).forEach(([key, label]) => {
    const k = String(key || '').trim();
    const l = String(label || '').trim();
    
    if (!k || seen.has(k)) return;
    
    seen.add(k);
    result.push({ key: k, label: l });
  });

  return result;
}

function setCfgInputValue(input, dotKey, value) {
  if (!input) return;

  if (input.tagName === 'SELECT' && input.multiple) {
    const selectedSet = new Set((Array.isArray(value) ? value : [value]).map(v => String(v)));
    const selectedLower = new Set([...selectedSet].map(v => v.toLowerCase()));
    Array.from(input.options).forEach(opt => {
      const key = dotKey === 'visualize.trajectory.source'
        ? String(opt.value).toLowerCase()
        : String(opt.value);
      opt.selected = dotKey === 'visualize.trajectory.source'
        ? selectedLower.has(key)
        : selectedSet.has(key);
    });
    return;
  }

  if (input.tagName === 'SELECT') {
    input.value = String(value);
    return;
  }

  if (Array.isArray(value)) {
    input.value = JSON.stringify(value);
  } else {
    input.value = value == null ? '' : String(value);
  }
}

function syncCfgInputsByDotKey(dotKey, value, sourceInput = null) {
  const rows = document.querySelectorAll(`.cfg-row[data-key="${dotKey}"]`);
  if (!rows.length) return;

  _cfgInputSyncing = true;
  try {
    rows.forEach((row) => {
      const input = row.querySelector('input, select');
      if (!input || input === sourceInput) return;
      setCfgInputValue(input, dotKey, value);
      input.style.borderColor = '';

      if (dotKey === 'robots.type' && input.tagName === 'SELECT') {
        input.dispatchEvent(new Event('change'));
      }
    });
  } finally {
    _cfgInputSyncing = false;
  }
}

function renderMainParameters(cfg) {
  const root = $('main-params-tree');
  if (!root) return;
  root.innerHTML = '';

  const params = resolveMainParameterKeys(cfg);
  params.forEach(({ key: dotKey, label }) => {
    const value = getConfigValueByDotKey(cfg, dotKey);
    if (value === undefined) return;
    // Use the custom label instead of the dotKey for display
    root.appendChild(createCfgRow(dotKey, label, value));
  });
}

function getCfgMultiSelectOptions(dotKey) {
  if (dotKey === 'visualize.trajectory.source') {
    return [
      { value: 'State', label: 'State' },
      { value: 'ActionFitted', label: 'ActionFitted' },
      { value: 'ActionRaw', label: 'ActionRaw' },
    ];
  }

  if (dotKey === 'visualize.trajectory.selected_joints') {
    return getTrajJointLabels().map((name, idx) => ({ value: String(idx), label: `${name} (${idx})` }));
  }

  return null;
}

function _cfgGroupHeaderLabel(header) {
  const spans = header.querySelectorAll('span');
  return (spans[1]?.textContent || header.textContent || '').trim();
}

function _cfgGroupHeaderPath(header) {
  const parts = [];
  let group = header.closest('.cfg-group');
  while (group) {
    const h = group.querySelector(':scope > .cfg-group-header');
    if (h) parts.unshift(_cfgGroupHeaderLabel(h));
    const parentBody = group.parentElement;
    if (!parentBody || !parentBody.classList.contains('cfg-group-body')) break;
    group = parentBody.closest('.cfg-group');
  }
  return parts.join('/');
}

function captureConfigTreeUiState() {
  const configTree = $('config-tree');
  const configBody = $('config-body');
  const openGroups = new Set();

  if (configTree) {
    configTree.querySelectorAll('.cfg-group-header.open').forEach((header) => {
      openGroups.add(_cfgGroupHeaderPath(header));
    });
  }

  return {
    openGroups,
    treeScrollTop: configTree ? configTree.scrollTop : 0,
    treeScrollLeft: configTree ? configTree.scrollLeft : 0,
    bodyScrollTop: configBody ? configBody.scrollTop : 0,
    bodyScrollLeft: configBody ? configBody.scrollLeft : 0,
  };
}

function restoreConfigTreeUiState(state) {
  const configTree = $('config-tree');
  const configBody = $('config-body');
  if (!state) return;

  if (configTree) {
    configTree.querySelectorAll('.cfg-group').forEach((group) => {
      const header = group.querySelector(':scope > .cfg-group-header');
      const body = group.querySelector(':scope > .cfg-group-body');
      if (!header || !body) return;
      const open = state.openGroups.has(_cfgGroupHeaderPath(header));
      header.classList.toggle('open', open);
      body.style.display = open ? '' : 'none';
    });

    configTree.scrollTop = state.treeScrollTop || 0;
    configTree.scrollLeft = state.treeScrollLeft || 0;
  }

  if (configBody) {
    configBody.scrollTop = state.bodyScrollTop || 0;
    configBody.scrollLeft = state.bodyScrollLeft || 0;
  }
}

function renderConfigTree(cfg) {
  const root = $('config-tree');
  const uiState = captureConfigTreeUiState();
  root.innerHTML = '';
  renderMainParameters(cfg);
  buildTree(cfg, '', root);
  restoreConfigTreeUiState(uiState);
}

function buildTree(obj, prefix, parentEl) {
  const basicEntries    = [];
  const subGroupEntries = [];

  for (const [key, val] of Object.entries(obj)) {
    // Skip excluded keys at root level
    if (!prefix && CONFIG_EXCLUDED_GROUP_KEYS.has(key)) continue;

    const dotKey = prefix ? `${prefix}.${key}` : key;
    const isGroup = val !== null && typeof val === 'object' && !Array.isArray(val);

    // Record -> info -> features: flatten legacy nested cam group into dotted keys
    // (cam.hand_left / cam.hand_right / cam.head) so no standalone "cam" subgroup appears.
    if (prefix === 'record.info.features' && key === 'cam' && isGroup) {
      for (const [camKey, camVal] of Object.entries(val)) {
        const mergedKey = `cam.${camKey}`;
        const mergedDotKey = `${prefix}.${mergedKey}`;
        const mergedIsGroup = camVal !== null && typeof camVal === 'object' && !Array.isArray(camVal);
        if (mergedIsGroup) {
          subGroupEntries.push([mergedKey, camVal]);
        } else {
          if (CONFIG_HIDDEN_DOT_KEYS.has(mergedDotKey)) continue;
          parentEl.appendChild(createCfgRow(mergedDotKey, mergedKey, camVal));
        }
      }
      continue;
    }

    if (isGroup) {
      if (CONFIG_EXCLUDED_SUB_GROUP_KEYS.has(dotKey)) continue;
      subGroupEntries.push([key, val]);
    } else if (!prefix) {
      basicEntries.push([key, val]);
    } else {
      if (CONFIG_HIDDEN_DOT_KEYS.has(dotKey)) continue;
      parentEl.appendChild(createCfgRow(dotKey, key, val));
    }
  }

  // 1. Render BASIC group first (if there are root-level leaves)
  if (basicEntries.length > 0) {
    // Assign each basic entry to its sub-group or "others"
    const sgMap = {};
    for (const sgName of Object.keys(BASIC_SUBGROUPS)) sgMap[sgName] = [];
    sgMap['others'] = [];

    for (const [k, v] of basicEntries) {
      let placed = false;
      for (const [sgName, keys] of Object.entries(BASIC_SUBGROUPS)) {
        if (keys.includes(k)) { sgMap[sgName].push([k, v]); placed = true; break; }
      }
      if (!placed) sgMap['others'].push([k, v]);
    }

    // Build the outer BASIC group
    const basicBody = document.createElement('div');
    basicBody.className = 'cfg-group-body';

    for (const [sgName, entries] of Object.entries(sgMap)) {
      if (entries.length === 0) continue;
      const rows = entries.map(([k, v]) => createCfgRow(k, k, v));
      basicBody.appendChild(buildGroup(sgName.replace('_', '-'), rows));
    }

    parentEl.appendChild(buildGroupFromEl('BASIC', basicBody));
  }

  // 2. Sort subGroupEntries based on CUSTOM_GROUP_ORDER
  subGroupEntries.sort((a, b) => {
    const keyA = a[0].toLowerCase();
    const keyB = b[0].toLowerCase();
    
    const indexA = CUSTOM_GROUP_ORDER.indexOf(keyA);
    const indexB = CUSTOM_GROUP_ORDER.indexOf(keyB);
    
    // If both are in the custom list, sort by their index
    if (indexA !== -1 && indexB !== -1) {
      return indexA - indexB;
    }
    // If only A is in the list, A comes first
    if (indexA !== -1) return -1;
    // If only B is in the list, B comes first
    if (indexB !== -1) return 1;
    // If neither is in the list, maintain original relative order (stable sort)
    return 0;
  });

  // 4. Render sorted sub-groups
  for (const [key, val] of subGroupEntries) {
    const dotKey  = prefix ? `${prefix}.${key}` : key;
    const body    = document.createElement('div');
    body.className = 'cfg-group-body';
    // ROBOTS group: custom rendering with type-driven sub-group visibility
    if (!prefix && key === 'robots') {
      _buildRobotsGroup(val, body);
    } else {
      buildTree(val, dotKey, body);
    }
    parentEl.appendChild(buildGroupFromEl(key, body));
  }
}
// ═══════════════════════════════════════════════════════
//  Robots group — dynamic sub-group visibility by type
// ═══════════════════════════════════════════════════════

/**
 * Renders the robots config group with dynamic sub-group visibility.
 * The robots.type select controls which sub-group (a2d / mock / …) is shown.
 *
 * robots object structure (example):
 *   { type: 'a2d', a2d: {...}, mock: {...} }
 *
 * Layout inside parentEl:
 *   ┌── type row (select)
 *   ├── [sub-group: a2d]   ← shown only when type === 'a2d'
 *   └── [sub-group: mock]  ← shown only when type === 'mock'
 */
function _buildRobotsGroup(obj, parentEl) {
  const TYPE_KEY = 'type';
  const currentType = String(obj[TYPE_KEY] ?? '');

  // Separate leaf keys from sub-group keys
  const leaves = [];        // [ [key, val], ... ]  — non-object entries (incl. type)
  const subGroups = [];     // [ [key, val], ... ]  — object entries (the robot types)

  for (const [k, v] of Object.entries(obj)) {
    const isGroup = v !== null && typeof v === 'object' && !Array.isArray(v);
    if (isGroup) {
      subGroups.push([k, v]);
    } else {
      leaves.push([k, v]);
    }
  }

  // ── 1. Render leaf rows (type + any other flat keys) ──────────────────
  // Put 'type' first
  const typeEntry = leaves.find(([k]) => k === TYPE_KEY);
  const otherLeaves = leaves.filter(([k]) => k !== TYPE_KEY);
  const orderedLeaves = typeEntry ? [typeEntry, ...otherLeaves] : otherLeaves;

  // Build a dedicated select for robots.type that drives visibility
  const knownTypes = subGroups.map(([k]) => k);

  let typeInput = null;
  for (const [k, v] of orderedLeaves) {
    const dotKey = `robots.${k}`;
    const row = document.createElement('div');
    row.className = 'cfg-row';
    row.dataset.key = dotKey;

    const keyEl = document.createElement('div');
    keyEl.className = 'cfg-key'; keyEl.title = dotKey; keyEl.textContent = k;

    const valEl = document.createElement('div');
    valEl.className = 'cfg-value';

    let input;
    if (k === TYPE_KEY && knownTypes.length > 0) {
      // Build select from known sub-group names
      input = document.createElement('select');
      knownTypes.forEach(opt => {
        const o = document.createElement('option');
        o.value = opt; o.textContent = opt;
        if (opt === currentType) o.selected = true;
        input.appendChild(o);
      });
      typeInput = input;
    } else {
      input = document.createElement('input');
      input.type = 'text'; input.value = v === null ? '' : String(v);
    }
    input.className = 'input-text';
    input.addEventListener('input',  () => onCfgChange(dotKey, input, v));
    input.addEventListener('change', () => onCfgChange(dotKey, input, v));
    valEl.appendChild(input);
    row.appendChild(keyEl); row.appendChild(valEl);
    parentEl.appendChild(row);
  }

  // ── 2. Render sub-groups with initial visibility ──────────────────────
  const subGroupEls = {};  // { typeName: groupEl }

  for (const [k, v] of subGroups) {
    const dotKey = `robots.${k}`;
    const body = document.createElement('div');
    body.className = 'cfg-group-body';
    buildTree(v, dotKey, body);
    const groupEl = buildGroupFromEl(k, body);
    groupEl.dataset.robotType = k;
    // Show only the group matching current type
    groupEl.style.display = (k === currentType) ? '' : 'none';
    subGroupEls[k] = groupEl;
    parentEl.appendChild(groupEl);
  }

  // ── 3. Wire type select → sub-group visibility ────────────────────────
  if (typeInput) {
    typeInput.addEventListener('change', () => {
      const selected = typeInput.value;
      for (const [k, el] of Object.entries(subGroupEls)) {
        el.style.display = (k === selected) ? '' : 'none';
      }
    });
  }
}

function buildGroup(label, rowEls) {
  const group  = document.createElement('div');
  group.className = 'cfg-group';
  const header = document.createElement('div');
  header.className = 'cfg-group-header';
  header.innerHTML = `<span class="cfg-group-toggle"><i class="fas fa-chevron-right"></i></span><span>${label}</span>`;
  const body = document.createElement('div');
  body.className = 'cfg-group-body';
  body.style.display = 'none';
  rowEls.forEach(r => body.appendChild(r));
  header.addEventListener('click', () => {
    const open = header.classList.toggle('open');
    body.style.display = open ? '' : 'none';
  });
  group.appendChild(header);
  group.appendChild(body);
  return group;
}

function buildGroupFromEl(label, bodyEl) {
  const group  = document.createElement('div');
  group.className = 'cfg-group';
  const header = document.createElement('div');
  header.className = 'cfg-group-header';
  header.innerHTML = `<span class="cfg-group-toggle"><i class="fas fa-chevron-right"></i></span><span>${label}</span>`;
  bodyEl.style.display = 'none';
  header.addEventListener('click', () => {
    const open = header.classList.toggle('open');
    bodyEl.style.display = open ? '' : 'none';
  });
  group.appendChild(header);
  group.appendChild(bodyEl);
  return group;
}

function setConfigValueByDotKey(cfg, dotKey, value) {
  if (!cfg || typeof cfg !== 'object') return;
  const parts = String(dotKey || '').split('.').filter(Boolean);
  if (!parts.length) return;

  let node = cfg;
  for (let i = 0; i < parts.length - 1; i++) {
    const k = parts[i];
    if (node[k] == null || typeof node[k] !== 'object') node[k] = {};
    node = node[k];
  }
  node[parts[parts.length - 1]] = value;
}

function createCfgRow(dotKey, label, value) {
  const row = document.createElement('div');
  row.className = 'cfg-row';
  row.dataset.key = dotKey;

  const keyEl = document.createElement('div');
  keyEl.className = 'cfg-key'; keyEl.title = dotKey; keyEl.textContent = label;

  const valEl = document.createElement('div');
  valEl.className = 'cfg-value';

  // Extract the bare key name (last segment) for option lookup
  const bareKey = dotKey.includes('.') ? dotKey.split('.').pop() : dotKey;

  if (dotKey === 'robots.mock.dataset_path') {
    row.style.flexDirection = 'column';
    row.style.alignItems = 'stretch';
    row.style.gap = '4px';

    const topLine = document.createElement('div');
    topLine.style.display = 'flex';
    topLine.style.alignItems = 'center';
    topLine.style.justifyContent = 'space-between';
    topLine.style.gap = '8px';

    keyEl.style.minWidth = '0';

    const pathEl = document.createElement('div');
    pathEl.textContent = value === null ? '' : String(value);
    pathEl.title = value === null ? '' : String(value);
    pathEl.style.width = '100%';
    pathEl.style.whiteSpace = 'normal';
    pathEl.style.overflowWrap = 'anywhere';
    pathEl.style.wordBreak = 'break-word';
    pathEl.style.fontSize = '10px';
    pathEl.style.lineHeight = '1.2';
    pathEl.style.background = 'transparent';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-xs';
    btn.textContent = 'Browse';
    let isBrowsing = false;

    btn.addEventListener('click', async () => {
      if (isBrowsing) return;
      isBrowsing = true;
      btn.disabled = true;
      btn.textContent = 'Browsing...';

      let selectedPath = '';
      try {
        const initialPath = String(value || '').trim();
        const url = `/api/client/robot/select_directory${initialPath ? `?path=${encodeURIComponent(initialPath)}` : ''}`;
        const pickRes = await apiFetch(url, {
          // Native directory chooser blocks server response until user confirms/cancels.
          // Use a long timeout to avoid aborting before path is selected.
          timeoutMs: 600000,
          suppressAbortToast: true,
        });
        selectedPath = String(pickRes?.path || '').trim();
      } catch (_) {
        selectedPath = '';
      } finally {
        isBrowsing = false;
        btn.disabled = false;
        btn.textContent = 'Browse';
      }
      if (!selectedPath) return;

      pathEl.textContent = selectedPath;
      pathEl.title = selectedPath;

      try {
        const patchRes = await apiFetch('/api/client/config/patch', {
          method: 'POST',
          body: JSON.stringify({ patch: { [dotKey]: selectedPath } }),
        });

        App.config = patchRes.config || App.config || {};
        setConfigValueByDotKey(App.config, dotKey, selectedPath);
        delete App.pendingPatch[dotKey];
        if (!Object.keys(App.pendingPatch).length) clearPending();

        renderConfigTree(App.config);
        renderRecordingConfigTree(App.config);

        try {
          await apiFetch('/api/client/config/save', { method: 'POST', body: JSON.stringify({ path: CONF_FILE }) });
          toast(`dataset_path updated and saved to ${CONF_FILE}.`, 'ok', 2200);
        } catch (_) {
          toast(`dataset_path updated, but save to ${CONF_FILE} failed.`, 'warn', 2600);
        }
      } catch (_) {
        App.pendingPatch[dotKey] = selectedPath;
        markPending();
      }
    });

    topLine.appendChild(keyEl);
    topLine.appendChild(btn);

    valEl.appendChild(pathEl);
    row.appendChild(topLine);
    row.appendChild(valEl);
    return row;
  }

  let input;
  const multiSelectOptions = getCfgMultiSelectOptions(dotKey);
  if (multiSelectOptions) {
    input = document.createElement('select');
    input.multiple = true;
    input.size = Math.min(8, Math.max(2, multiSelectOptions.length));

    const selectedRaw = Array.isArray(value)
      ? value
      : (value == null ? [] : String(value).split(',').map(v => v.trim()).filter(Boolean));

    const selectedSet = new Set(
      selectedRaw.map(v => {
        if (dotKey === 'visualize.trajectory.source') return String(v).trim().toLowerCase();
        return String(parseInt(v, 10));
      })
    );

    multiSelectOptions.forEach(opt => {
      const o = document.createElement('option');
      o.value = opt.value;
      o.textContent = opt.label;
      const key = dotKey === 'visualize.trajectory.source'
        ? String(opt.value).toLowerCase()
        : String(parseInt(opt.value, 10));
      if (selectedSet.has(key)) o.selected = true;
      input.appendChild(o);
    });
  } else if (CONFIG_SELECT_OPTIONS[bareKey]) {
    // Predefined select options
    input = document.createElement('select');
    CONFIG_SELECT_OPTIONS[bareKey].forEach(opt => {
      const o = document.createElement('option');
      o.value = opt; o.textContent = opt;
      if (String(value) === String(opt)) o.selected = true;
      input.appendChild(o);
    });
  } else if (typeof value === 'boolean') {
    input = document.createElement('select');
    ['true', 'false'].forEach(opt => {
      const o = document.createElement('option');
      o.value = opt; o.textContent = opt;
      if (String(value) === opt) o.selected = true;
      input.appendChild(o);
    });
  } else if (Array.isArray(value)) {
    input = document.createElement('input');
    input.type = 'text'; input.value = JSON.stringify(value); input.title = 'JSON array';
  } else if (CONFIG_INT_KEYS.has(bareKey)) {
    input = document.createElement('input');
    input.type = 'number'; input.step = '1'; input.value = value === null ? '' : String(Math.round(Number(value)));
  } else {
    input = document.createElement('input');
    input.type = 'text'; input.value = value === null ? '' : String(value);
  }

  input.className = 'input-text';
  if (CONFIG_READONLY_DOT_KEYS.has(dotKey)) {
    row.classList.add('cfg-row-readonly');
    input.disabled = true;
    input.title = `${dotKey} is managed by runtime actions and is read-only here.`;
  } else {
    input.addEventListener('input',  () => onCfgChange(dotKey, input, value));
    input.addEventListener('change', () => onCfgChange(dotKey, input, value));
  }
  valEl.appendChild(input);
  row.appendChild(keyEl);
  row.appendChild(valEl);
  return row;
}

function onCfgChange(dotKey, input, originalValue) {
  if (_cfgInputSyncing) return;
  const bareKey = dotKey.includes('.') ? dotKey.split('.').pop() : dotKey;

  if (input.tagName === 'SELECT' && input.multiple) {
    const selected = Array.from(input.selectedOptions).map(o => o.value);
    let parsed = selected;

    if (dotKey === 'visualize.trajectory.selected_joints') {
      parsed = selected.map(v => parseInt(v, 10)).filter(Number.isFinite);
    } else if (dotKey === 'visualize.trajectory.source') {
      parsed = selected
        .map(v => String(v).trim().toLowerCase())
        .map(v => {
          if (v === 'state') return 'State';
          if (v === 'action' || v === 'actionfitted' || v === 'action_fitted') return 'ActionFitted';
          if (v === 'origin' || v === 'actionraw' || v === 'action_raw') return 'ActionRaw';
          return null;
        })
        .filter(Boolean);
    }

    input.style.borderColor = '';
    App.pendingPatch[dotKey] = parsed;
    syncCfgInputsByDotKey(dotKey, parsed, input);
    markPending();
    return;
  }

  const raw = input.tagName === 'SELECT' ? input.value : input.value.trim();
  let parsed;
  if (typeof originalValue === 'boolean') {
    parsed = raw === 'true';
  } else if (CONFIG_INT_KEYS.has(bareKey)) {
    parsed = parseInt(raw, 10);
    if (isNaN(parsed)) { input.style.borderColor = 'var(--danger)'; return; }
  } else if (typeof originalValue === 'number') {
    parsed = Number(raw);
    if (isNaN(parsed)) { input.style.borderColor = 'var(--danger)'; return; }
  } else if (Array.isArray(originalValue)) {
    try { parsed = JSON.parse(raw); } catch { input.style.borderColor = 'var(--danger)'; return; }
  } else if (CONFIG_SELECT_OPTIONS[bareKey] && typeof CONFIG_SELECT_OPTIONS[bareKey][0] === 'number') {
    parsed = parseInt(raw, 10);
    if (isNaN(parsed)) { input.style.borderColor = 'var(--danger)'; return; }
  } else {
    parsed = raw;
  }
  input.style.borderColor = '';
  App.pendingPatch[dotKey] = parsed;
  syncCfgInputsByDotKey(dotKey, parsed, input);
  if (dotKey === 'record.switch') {
    if (!App.config || typeof App.config !== 'object') App.config = {};
    if (!App.config.record || typeof App.config.record !== 'object') App.config.record = {};
    App.config.record.switch = !!parsed;
    syncRecordingSwitchUI();
  }
  markPending();
}

/** Mark pending changes: show badge + highlight Apply button */
function markPending() {
  $('pending-badge').classList.remove('hidden');
  const btn = $('btn-apply-config');
  if (btn) btn.classList.add('btn-primary');
}

/** Clear pending state: hide badge + restore Apply button to normal */
function clearPending() {
  $('pending-badge').classList.add('hidden');
  const btn = $('btn-apply-config');
  if (btn) btn.classList.remove('btn-primary');
}

/**
 * Create a real cfg-row for task_id or sub_task_id.
 * Both are real config fields that write to App.pendingPatch when changed.
 *   task_id  → string key into LangCmd.tasks (Task <select>)
 *   sub_task_id → integer index into the selected task's subtask array
 */
function createLangLinkRow(dotKey, label) {
  const row = document.createElement('div');
  row.className = 'cfg-row';
  row.dataset.key = dotKey;

  const keyEl = document.createElement('div');
  keyEl.className = 'cfg-key'; keyEl.title = dotKey; keyEl.textContent = label;

  const valEl = document.createElement('div');
  valEl.className = 'cfg-value';

  const sel = document.createElement('select');
  sel.className = 'input-text';
  // IDs: cfg-language-task / cfg-language-index
  sel.id = dotKey === 'language.task_id' ? 'cfg-language-task' : 'cfg-language-index';

  valEl.appendChild(sel);
  row.appendChild(keyEl);
  row.appendChild(valEl);

  if (dotKey === 'language.task_id') {
    sel.addEventListener('change', () => {
      const task = sel.value;
      // Rebuild sub_task_id options (display sync only, pendingPatch written on Apply)
      syncLangIndexOptions(task, 0);
      // Sync → Language Command panel Task select
      const taskSel = $('lang-task-select');
      if (taskSel && taskSel.value !== task) {
        taskSel.value = task;
        taskSel.dispatchEvent(new Event('change'));
      }
    });
  } else {
    // sub_task_id
    sel.addEventListener('change', () => {
      // Sync → Language Command panel Sub-task select (display sync only)
      const subtaskSel = $('lang-subtask-select');
      if (subtaskSel && subtaskSel.value !== sel.value) {
        subtaskSel.value = sel.value;
        subtaskSel.dispatchEvent(new Event('change'));
      }
    });
  }

  return row;
}

/** Populate the cfg-language-task select from current LangCmd.tasks.
 *  @param {string} [currentTask]  - task to pre-select (from App.config)
 *  @param {number} [currentIndex] - index to pre-select in sub_task_id (from App.config)
 */
function syncLangTaskOptions(currentTask, currentIndex) {
  const sel = $('cfg-language-task');
  if (!sel) return;
  const prev = currentTask !== undefined ? currentTask : sel.value;
  sel.innerHTML = '';
  Object.keys(LangCmd.tasks).forEach(name => {
    const o = document.createElement('option');
    o.value = name; o.textContent = name;
    sel.appendChild(o);
  });
  if (prev && LangCmd.tasks[prev]) sel.value = prev;
  else if (sel.options.length > 0) sel.selectedIndex = 0;
  syncLangIndexOptions(sel.value, currentIndex);
}

/** Populate the cfg-language-index select from the given task's sub-tasks.
 *  @param {string} taskName
 *  @param {number} [currentIndex] - index to pre-select
 */
function syncLangIndexOptions(taskName, currentIndex) {
  const sel = $('cfg-language-index');
  if (!sel) return;
  const subtasks = (taskName && LangCmd.tasks[taskName]) ? LangCmd.tasks[taskName] : [];
  sel.innerHTML = '';
  subtasks.forEach((text, i) => {
    const o = document.createElement('option');
    o.value = i;
    o.textContent = `${i + 1}. ${text.substring(0, 60)}${text.length > 60 ? '…' : ''}`;
    o.title = text;
    sel.appendChild(o);
  });
  // Pre-select given index, or restore previous
  if (currentIndex !== undefined && !isNaN(currentIndex)) {
    sel.value = currentIndex;
  }
  if (!sel.value && sel.options.length > 0) sel.selectedIndex = 0;
}

function filterConfigTree(query) {
  const q = query.toLowerCase().trim();
  $('config-tree').querySelectorAll('.cfg-row').forEach(row => {
    row.style.display = (!q || row.dataset.key.toLowerCase().includes(q)) ? '' : 'none';
  });
  $('config-tree').querySelectorAll('.cfg-group').forEach(g => {
    // Robot type sub-groups (data-robot-type) are controlled exclusively by the
    // type select in _buildRobotsGroup; never let the filter override their visibility.
    if (g.dataset.robotType) return;
    if (!q) { g.style.display = ''; return; }
    const body = g.querySelector('.cfg-group-body');
    if (!body) return;
    g.style.display = [...body.querySelectorAll('.cfg-row')].some(r => r.style.display !== 'none') ? '' : 'none';
  });
}


// ═══════════════════════════════════════════════════════
//  Config load
// ═══════════════════════════════════════════════════════

// Conf directory path (absolute), fetched once from server
let CONF_FILE = 'default_conf.yaml';

async function initConfDir() {
  try {
    const res = await apiFetch('/api/client/config/path');
    if (res.path) CONF_FILE = res.path;
  } catch (_) { /* fallback to 'conf' */ }
}

function _toBool(v, fallback) {
  return typeof v === 'boolean' ? v : fallback;
}

function _toInt(v, fallback, min = null) {
  const n = parseInt(v, 10);
  if (!Number.isFinite(n)) return fallback;
  if (min != null && n < min) return min;
  return n;
}

function normalizeTrajWindowSpanSec(rawSpanSec, fallback = TRAJ_WINDOW_SPAN_SEC) {
  const fallbackVal = Number(fallback);
  const fallbackSafe = Number.isFinite(fallbackVal) && fallbackVal > 0
    ? Math.min(fallbackVal, TRAJ_WINDOW_SPAN_SEC_MAX)
    : 2.25;
  const span = Number(rawSpanSec);
  if (!Number.isFinite(span) || span <= 0) return fallbackSafe;
  return Math.min(span, TRAJ_WINDOW_SPAN_SEC_MAX);
}

function trimTrajBufferToMaxWindow(bufferKey, latestX) {
  const t = App.traj;
  const buf = t.buffer[bufferKey];
  if (!buf || buf.length === 0 || !Number.isFinite(latestX)) return;

  const cutoff = latestX - TRAJ_WINDOW_SPAN_SEC_MAX;
  while (buf.length > 0 && Number.isFinite(buf[0].x) && buf[0].x < cutoff) {
    buf.shift();
  }
  if (buf.length > TRAJ_BUFFER_HARD_MAX_POINTS) {
    buf.splice(0, buf.length - TRAJ_BUFFER_HARD_MAX_POINTS);
  }
}

function syncTrajWindowSpanUI() {
  const span = normalizeTrajWindowSpanSec(App.traj.windowSpanSec, TRAJ_WINDOW_SPAN_SEC);
  const uiValue = Math.round(span);
  const slider = $('traj-window-span-slider');
  const value = $('traj-window-span-value');
  if (slider) {
    slider.min = '1';
    slider.max = String(TRAJ_WINDOW_SPAN_SEC_MAX);
    slider.step = '1';
    slider.value = String(uiValue);
  }
  if (value) value.textContent = `${uiValue}s`;
}

function applyVisualConfig(cfg = App.config) {
  const root = (cfg && typeof cfg === 'object') ? cfg : {};
  syncTrajLayoutFromConfig(root);
  // Prefer new key `visualize`, keep backward compatibility with legacy `visual`.
  const visualCfg = (root.visualize && typeof root.visualize === 'object')? root.visualize : {};

  const camCfg = (visualCfg.camera && typeof visualCfg.camera === 'object') ? visualCfg.camera : {};
  const trajCfg = (visualCfg.trajectory && typeof visualCfg.trajectory === 'object') ? visualCfg.trajectory : {};

  camState.updateInterval = _toInt(camCfg.updata_period, camState.updateInterval || 33, 16);
  restartCameraUpdateTimer();

  const hasNamedCamOpen = ['open_head', 'open_wrist_left', 'open_wrist_right'].some(k => k in camCfg);
  const camOpenCfg = hasNamedCamOpen
    ? [camCfg.open_head, camCfg.open_wrist_left, camCfg.open_wrist_right]
    : (Array.isArray(camCfg.default_open) ? camCfg.default_open : App.camOpen);
  const nextCamOpen = [0, 1, 2].map(i => !!camOpenCfg[i]);
  for (let i = 0; i < 3; i++) {
    if (App.camOpen[i] !== nextCamOpen[i]) toggleCamera(i);
  }
  const camAllBtn = $('btn-cam-all-toggle');
  if (camAllBtn) {
    const allOn = App.camOpen.every(v => v);
    camAllBtn.innerHTML = allOn ? '<i class="fas fa-pause"></i> Close All' : '<i class="fas fa-play"></i> Open All';
    camAllBtn.className = allOn ? 'btn btn-xs btn-danger' : 'btn btn-xs btn-success';
  }

  if (typeof trajCfg.play === 'boolean') {
    App.traj.paused = !trajCfg.play;
  } else {
    App.traj.paused = _toBool(trajCfg.default_paused, App.traj.paused);
  }
  App.traj.updateIntervalMs = _toInt(trajCfg.updata_period, App.traj.updateIntervalMs || DEFAULT_TRAJ_UPDATE_MS, 16);
  const cfgWindowSpanSec = Number(trajCfg.window_span_sec ?? trajCfg.window_sec ?? trajCfg.window_seconds);
  App.traj.windowSpanSec = normalizeTrajWindowSpanSec(cfgWindowSpanSec, App.traj.windowSpanSec);
  syncTrajWindowSpanUI();

  const sourceCfgRaw = Array.isArray(trajCfg.source)
    ? trajCfg.source
    : (Array.isArray(trajCfg.default_source) ? trajCfg.default_source : null);
  if (Array.isArray(sourceCfgRaw)) {
    const source = new Set();
    sourceCfgRaw.forEach(k => {
      const key = String(k).trim().toLowerCase();
      if (key === 'state') source.add('state');
      else if (key === 'action' || key === 'actionfitted' || key === 'action_fitted') source.add('action_fitted');
      else if (key === 'origin' || key === 'actionraw' || key === 'action_raw') source.add('action_raw');
    });
    App.traj.source = source;
  }

  const selectedJointsRaw = trajCfg.selected_joints ?? trajCfg.default_selected_joints;
  const hasSelectedJointsCfg = selectedJointsRaw !== undefined && selectedJointsRaw !== null;
  let jointTokens = [];
  if (Array.isArray(selectedJointsRaw)) {
    jointTokens = selectedJointsRaw;
  } else if (typeof selectedJointsRaw === 'string') {
    jointTokens = selectedJointsRaw.split(',').map(v => v.trim()).filter(Boolean);
  }
  if (hasSelectedJointsCfg && jointTokens.length === 0) {
    App.traj.selectedJoints = new Set();
  } else if (jointTokens.length > 0) {
    const labels = getTrajJointLabels();
    const labelToIndex = new Map(labels.map((name, idx) => [String(name).toLowerCase(), idx]));
    const split = Math.ceil(getTrajJointCount() / 2);
    const joints = jointTokens
      .map(v => {
        if (typeof v === 'number') return v;
        const s = String(v).trim();
        const labelIdx = labelToIndex.get(s.toLowerCase());
        if (labelIdx !== undefined) return labelIdx;
        if (/^[LR]\d+$/i.test(s)) return parseInt(s.slice(1), 10) + (s[0].toUpperCase() === 'R' ? split : 0);
        return parseInt(s, 10);
      })
      .filter(v => Number.isFinite(v) && v >= 0 && v < getTrajJointCount());
    if (joints.length > 0) App.traj.selectedJoints = new Set(joints);
  }

  renderJointSelector();
  document.querySelectorAll('.joint-sel-chip').forEach(chip => {
    const idx = parseInt(chip.dataset.idx, 10);
    const active = App.traj.selectedJoints.has(idx);
    chip.classList.toggle('active', active);
    _applyChipColor(chip, active, getTrajJointColor(idx));
  });

  const chkState = $('chk-traj-state');
  const chkActionFitted = $('chk-traj-action-fitted');
  const chkActionRaw = $('chk-traj-action-raw');
  const btnAllSource = $('btn-traj-all');
  if (chkState) chkState.checked = App.traj.source.has('state');
  if (chkActionFitted) chkActionFitted.checked = App.traj.source.has('action_fitted');
  if (chkActionRaw) chkActionRaw.checked = App.traj.source.has('action_raw');
  if (btnAllSource) {
    const allSelected = App.traj.source.has('state') && App.traj.source.has('action_fitted') && App.traj.source.has('action_raw');
    btnAllSource.textContent = allSelected ? 'None' : 'All';
  }
  const btnPlay = $('btn-traj-pause');
  if (btnPlay) {
    btnPlay.innerHTML = App.traj.paused
      ? '<i class="fas fa-play"></i> Play'
      : '<i class="fas fa-pause"></i> Pause';
    btnPlay.className = 'btn btn-xs btn-ctrl';
  }

  startTrajUpdateTimer();
  App.traj.dirty = true;
  refreshUnifiedChart();

  if (App.isRunning) {
    connectCamWS();
    // syncRuntimeCameraConfig();
  }
}

function getVisualStatePatch() {
  return {
    'visualize.camera.open_head': !!App.camOpen[0],
    'visualize.camera.open_wrist_left': !!App.camOpen[1],
    'visualize.camera.open_wrist_right': !!App.camOpen[2],
    'visualize.trajectory.play': !App.traj.paused,
    'visualize.trajectory.source': [...App.traj.source].map(s => {
      if (s === 'action_fitted') return 'ActionFitted';
      if (s === 'action_raw') return 'ActionRaw';
      return 'State';
    }),
    'visualize.trajectory.selected_joints': [...App.traj.selectedJoints].sort((a, b) => a - b),
    'visualize.trajectory.window_span_sec': normalizeTrajWindowSpanSec(App.traj.windowSpanSec, TRAJ_WINDOW_SPAN_SEC),
  };
}

function syncVisualStateToLocalConfig(patch) {
  if (!App.config || typeof App.config !== 'object') App.config = {};
  if (!App.config.visualize || typeof App.config.visualize !== 'object') App.config.visualize = {};
  if (!App.config.visualize.camera || typeof App.config.visualize.camera !== 'object') App.config.visualize.camera = {};
  if (!App.config.visualize.trajectory || typeof App.config.visualize.trajectory !== 'object') App.config.visualize.trajectory = {};

  App.config.visualize.camera.open_head = patch['visualize.camera.open_head'];
  App.config.visualize.camera.open_wrist_left = patch['visualize.camera.open_wrist_left'];
  App.config.visualize.camera.open_wrist_right = patch['visualize.camera.open_wrist_right'];
  App.config.visualize.trajectory.play = patch['visualize.trajectory.play'];
  delete App.config.visualize.trajectory.default_paused;
  App.config.visualize.trajectory.source = patch['visualize.trajectory.source'];
  App.config.visualize.trajectory.selected_joints = patch['visualize.trajectory.selected_joints'];
  App.config.visualize.trajectory.window_span_sec = patch['visualize.trajectory.window_span_sec'];
}

function syncVisualStateToConfigInputs(patch) {
  Object.entries(patch).forEach(([dotKey, value]) => {
    syncCfgInputsByDotKey(dotKey, value, null);
  });
}

async function persistVisualStateNow() {
  const patch = getVisualStatePatch();
  syncVisualStateToLocalConfig(patch);
  syncVisualStateToConfigInputs(patch);

  // Visual panel changes are auto-applied; never show "unsaved changes" for them.
  Object.keys(App.pendingPatch)
    .filter(k => k.startsWith('visualize.camera.') || k.startsWith('visualize.trajectory.'))
    .forEach(k => delete App.pendingPatch[k]);
  if (!Object.keys(App.pendingPatch).length) clearPending();

  if (App.isRunning) {
    try {
      await apiFetch('/api/client/visualize/config', {
        method: 'POST',
        body: JSON.stringify({
          open_head: patch['visualize.camera.open_head'],
          open_wrist_left: patch['visualize.camera.open_wrist_left'],
          open_wrist_right: patch['visualize.camera.open_wrist_right'],
        }),
      });
    } catch (_) {
      // no-op: keep local UI effective
    }
    return;
  }

  if (_visualPersistInFlight) return;

  _visualPersistInFlight = true;
  try {
    const res = await apiFetch('/api/client/config/patch', {
      method: 'POST',
      body: JSON.stringify({ patch }),
    });
    App.config = res.config || App.config;

    await apiFetch('/api/client/config/save', { method: 'POST', body: JSON.stringify({ path: CONF_FILE }) });
  } catch (_) {
    // no-op: visual state already effective in UI
  } finally {
    _visualPersistInFlight = false;
  }
}

function schedulePersistVisualState(delay = 120) {
  if (_visualPersistTimer) clearTimeout(_visualPersistTimer);
  _visualPersistTimer = setTimeout(() => {
    _visualPersistTimer = null;
    persistVisualStateNow();
  }, delay);
}

async function loadConfigFromServer() {
  try {
    const res = await apiFetch('/api/client/config');
    App.config = res.config || {};
    App.pendingPatch = {};
    clearPending();
    renderConfigTree(App.config);
    renderRecordingConfigTree(App.config);
    applyVisualConfig(App.config);
    // Apply language-related UI state from config (task/sub-task/auto/threshold/win_size)
    // On initial startup from YAML config, default sub-task to first entry.
    applyLangConfigSelection(true);
    toast(`Config ${CONF_FILE} loaded.`, 'ok', 2000);
  } catch (e) { /* already toasted */ }
}
