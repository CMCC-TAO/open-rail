function setupManualControlEvents() {
const checked = (id) => !!$(id)?.checked;
const robotConfig = () => {
  const type = String(App.config?.robots?.type || '');
  return App.config?.robots?.[type] || {};
};
const hasLayout = (action) => !!robotConfig().action_layout?.[action];
const presets = (action, side = null) => {
  const group = robotConfig().action_layout?.[action]?.presets;
  const items = side ? group?.[side] : group;
  return Array.isArray(items) ? items : [];
};
const presetKey = preset => String(preset?.key ?? preset?.name ?? '');
const readPreset = (id) => {
  try {
    const value = JSON.parse($(id)?.value || '');
    return Array.isArray(value) && value.every(Number.isFinite) ? value : null;
  } catch (_) {
    return null;
  }
};
const populate = (selectId, checkId, action, side = null) => {
  const select = $(selectId);
  const check = $(checkId);
  const edit = $(`${selectId}-edit`);
  if (!select || !check) return;
  const wasDisabled = check.disabled;
  const previous = select.value;
  select.innerHTML = '';
  presets(action, side).forEach(preset => {
    const key = presetKey(preset);
    const { value } = preset;
    if (!Array.isArray(value) || !value.every(v => Number.isFinite(Number(v)))) return;
    const option = document.createElement('option');
    option.textContent = key;
    option.dataset.key = key;
    option.value = JSON.stringify(value.map(Number));
    select.appendChild(option);
  });
  const layoutAvailable = hasLayout(action);
  const presetsAvailable = select.options.length > 0;
  const supported = layoutAvailable && presetsAvailable;
  const reason = !layoutAvailable
    ? `Disabled: action_layout does not define "${action}".`
    : `Disabled: no presets configured for "${action}".`;
  const targets = [select.closest('.robot-preset-row'), select, check].filter(Boolean);
  if (supported) {
    if (wasDisabled) check.checked = true;
    if ([...select.options].some(option => option.value === previous)) select.value = previous;
    targets.forEach(target => target.removeAttribute('title'));
  } else {
    select.innerHTML = '';
    const option = document.createElement('option');
    option.textContent = 'Disabled';
    select.appendChild(option);
    targets.forEach(target => { target.title = reason; });
  }
  check.disabled = !supported;
  if (!supported) check.checked = false;
  select.disabled = !supported || !check.checked;
  if (edit) {
    edit.disabled = select.disabled;
    edit.title = edit.disabled ? reason : 'Edit preset';
  }
};
const selectDefault = (id) => {
  const select = $(id);
  if (!select) return;
  const option = [...select.options].find(item => item.dataset.key === 'Default');
  if (option) select.value = option.value;
};

const handAction = () => {
  const action = String(robotConfig().hand_type || 'gripper');
  return hasLayout(action) ? action : 'gripper';
};
const refreshControls = () => {
  populate('arm-left-preset', 'chk-arm-left', 'arm', 'left');
  populate('arm-right-preset', 'chk-arm-right', 'arm', 'right');
  const hand = handAction();
  populate('gripper-left-preset', 'chk-gripper-left', hand, 'left');
  populate('gripper-right-preset', 'chk-gripper-right', hand, 'right');
  ['head', 'waist', 'body', 'wheel', 'leg'].forEach(action => {
    populate(`${action}-preset`, `chk-${action}`, action);
  });
};

const requestPreset = (key, current) => new Promise(resolve => {
  const modal = $('modal-preset-edit');
  const title = $('preset-edit-title');
  const keyInput = $('preset-edit-key');
  const valueInput = $('preset-edit-value');
  const confirm = $('btn-preset-edit-confirm');
  const cancel = $('btn-preset-edit-cancel');
  if (!modal || !title || !keyInput || !valueInput || !confirm || !cancel) {
    resolve(null);
    return;
  }

  const finish = result => {
    modal.classList.add('hidden');
    document.removeEventListener('keydown', onKeyDown);
    resolve(result);
  };
  const submit = () => finish({
    key: keyInput.value.trim(),
    value: valueInput.value,
  });
  const onKeyDown = event => {
    if (event.key === 'Enter') submit();
    if (event.key === 'Escape') finish(null);
  };

  title.textContent = `Edit Preset: ${key}`;
  keyInput.value = key;
  keyInput.readOnly = true;
  valueInput.value = JSON.stringify(current);
  confirm.onclick = submit;
  cancel.onclick = () => finish(null);
  modal.onclick = event => {
    if (event.target === modal) finish(null);
  };
  document.addEventListener('keydown', onKeyDown);
  modal.classList.remove('hidden');
  requestAnimationFrame(() => {
    valueInput.focus();
    valueInput.select();
  });
});

const parsePresetValue = (input, length) => {
  try {
    const value = JSON.parse(input);
    if (Array.isArray(value) && value.length === length && value.every(Number.isFinite)) {
      return value;
    }
  } catch (_) {
    // Fall through to the shared validation message.
  }
  toast(`Preset value must contain ${length} finite numbers.`, 'error');
  return null;
};

const savePresets = async (selectId, action, side, items, selectedKey, verb) => {
  const type = String(App.config?.robots?.type || '');
  const suffix = side ? `.${side}` : '';
  const patch = {
    [`robots.${type}.action_layout.${action}.presets${suffix}`]: items,
  };

  try {
    const res = await apiFetch('/api/client/config/patch', {
      method: 'POST',
      body: JSON.stringify({ patch }),
    });
    App.config = res.config || App.config;
    refreshControls();
    const select = $(selectId);
    const selected = [...select.options].find(item => item.dataset.key === selectedKey);
    if (selected) select.value = selected.value;

    const display = $('conf-path-display');
    const path = display?.dataset.fullPath || display?.textContent.trim() || '';
    if (path) {
      await apiFetch('/api/client/config/save', {
        method: 'POST',
        body: JSON.stringify({ path }),
      });
    }
    toast(`Preset "${selectedKey}" ${verb}.`, 'ok');
  } catch (_) { /* apiFetch already toasted */ }
};

const editPreset = async (selectId, action, side = null) => {
  const option = $(selectId)?.selectedOptions?.[0];
  const current = readPreset(selectId);
  if (!option?.dataset.key || !current) return;

  const key = option.dataset.key;
  const result = await requestPreset(key, current);
  if (!result) return;
  const value = parsePresetValue(result.value, current.length);
  if (!value) return;

  const updated = presets(action, side).map(item => {
    if (presetKey(item) !== key) return item;
    const normalized = { ...item, key, value };
    delete normalized.name;
    return normalized;
  });
  await savePresets(selectId, action, side, updated, key, 'updated');
};

[
  ['chk-arm-left', 'arm-left-preset'],
  ['chk-arm-right', 'arm-right-preset'],
  ['chk-gripper-left', 'gripper-left-preset'],
  ['chk-gripper-right', 'gripper-right-preset'],
  ['chk-head', 'head-preset'],
  ['chk-waist', 'waist-preset'],
  ['chk-body', 'body-preset'],
  ['chk-wheel', 'wheel-preset'],
  ['chk-leg', 'leg-preset'],
].forEach(([checkId, selectId]) => {
  $(checkId)?.addEventListener('change', () => {
    const select = $(selectId);
    if (select) select.disabled = !checked(checkId);
    const edit = $(`${selectId}-edit`);
    if (edit) edit.disabled = !checked(checkId);
  });
});

[
  ['arm-left-preset', () => 'arm', 'left'],
  ['arm-right-preset', () => 'arm', 'right'],
  ['gripper-left-preset', handAction, 'left'],
  ['gripper-right-preset', handAction, 'right'],
  ['head-preset', () => 'head'],
  ['waist-preset', () => 'waist'],
  ['body-preset', () => 'body'],
  ['wheel-preset', () => 'wheel'],
  ['leg-preset', () => 'leg'],
].forEach(([selectId, getAction, side = null]) => {
  $(`${selectId}-edit`)?.addEventListener('click', () => {
    editPreset(selectId, getAction(), side);
  });
});

const sendPair = async (endpoint, action, prefix) => {
  const payload = { source: 'manual' };
  for (const side of ['left', 'right']) {
    if (!checked(`chk-${prefix}-${side}`)) continue;
    const value = readPreset(`${prefix}-${side}-preset`);
    if (value) payload[`${side[0]}_${action}`] = value;
  }
  return Object.keys(payload).length > 1 && sendControl(endpoint, payload);
};

const sendActions = async (endpoint, actions) => {
  const payload = { source: 'manual' };
  actions.forEach(action => {
    if (checked(`chk-${action}`)) {
      const value = readPreset(`${action}-preset`);
      if (value) payload[action] = value;
    }
  });
  return Object.keys(payload).length > 1 && sendControl(endpoint, payload);
};

$('btn-arm')?.addEventListener('click', async () => {
  toast('Arm setting...', 'info');
  if (await sendPair('arm', 'arm', 'arm')) toast('Arm set.', 'ok');
});
$('btn-arm-reset')?.addEventListener('click', async () => {
  if (checked('chk-arm-left')) selectDefault('arm-left-preset');
  if (checked('chk-arm-right')) selectDefault('arm-right-preset');
  toast('Arm resetting...', 'info');
  if (await sendPair('arm', 'arm', 'arm')) toast('Arm reset.', 'ok');
});
$('btn-gripper')?.addEventListener('click', async () => {
  if (await sendPair('gripper', handAction(), 'gripper')) toast('Gripper / Hand set.', 'ok');
});
$('btn-gripper-reset')?.addEventListener('click', async () => {
  if (checked('chk-gripper-left')) selectDefault('gripper-left-preset');
  if (checked('chk-gripper-right')) selectDefault('gripper-right-preset');
  if (await sendPair('gripper', handAction(), 'gripper')) toast('Gripper / Hand reset.', 'ok');
});
$('btn-body')?.addEventListener('click', async () => {
  if (await sendActions('body', ['head', 'waist', 'body'])) toast('Head / Waist / Body set.', 'ok');
});
$('btn-body-reset')?.addEventListener('click', async () => {
  ['head', 'waist', 'body'].forEach(action => {
    if (checked(`chk-${action}`)) selectDefault(`${action}-preset`);
  });
  if (await sendActions('body', ['head', 'waist', 'body'])) toast('Head / Waist / Body reset.', 'ok');
});

$('btn-wheel')?.addEventListener('click', async () => {
  if (await sendActions('wheel', ['wheel', 'leg'])) toast('Wheel / Leg set.', 'ok');
});
$('btn-wheel-reset')?.addEventListener('click', async () => {
  ['wheel', 'leg'].forEach(action => {
    if (checked(`chk-${action}`)) selectDefault(`${action}-preset`);
  });
  if (await sendActions('wheel', ['wheel', 'leg'])) toast('Wheel / Leg reset.', 'ok');
});

document.addEventListener('app-config-updated', refreshControls);
refreshControls();
}
