function setupManualControlEvents() {
const checked = (id) => !!$(id)?.checked;
const robotConfig = () => {
  const type = String(App.config?.robots?.type || '');
  return App.config?.robots?.[type] || {};
};
const hasLayout = (action) => !!robotConfig().action_layout?.[action];
const presetGroup = (action, side = null) => {
  const group = robotConfig().action_layout?.[action]?.presets;
  return side ? group?.[side] : group;
};
const presetKey = preset => String(preset?.key ?? preset?.name ?? '');
const presets = (action, side = null) => {
  const group = presetGroup(action, side);
  if (Array.isArray(group)) return group;
  if (group && typeof group === 'object') {
    return Object.entries(group).map(([key, value]) => ({ key, value }));
  }
  return [];
};
const readPreset = (id) => {
  try {
    const value = JSON.parse($(id)?.value || '');
    return Array.isArray(value) && value.every(Number.isFinite) ? value : null;
  } catch (_) {
    return null;
  }
};
const updateEditState = (select, edit, disabledReason = 'Preset control is disabled.') => {
  if (!select || !edit) return;
  edit.disabled = select.disabled;
  edit.title = select.disabled ? disabledReason : 'Edit preset';
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
  updateEditState(select, edit, reason);
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
  const valueInput = $('preset-edit-value');
  const confirm = $('btn-preset-edit-confirm');
  const cancel = $('btn-preset-edit-cancel');
  if (!modal || !title || !valueInput || !confirm || !cancel) {
    resolve(null);
    return;
  }

  const finish = result => {
    modal.classList.add('hidden');
    document.removeEventListener('keydown', onKeyDown);
    resolve(result);
  };
  const submit = () => finish({ value: valueInput.value });
  const onKeyDown = event => {
    if (event.key === 'Enter') submit();
    if (event.key === 'Escape') finish(null);
  };

  title.textContent = `Edit Preset: ${key}`;
  valueInput.value = JSON.stringify(current);
  valueInput.readOnly = false;
  confirm.hidden = false;
  cancel.textContent = 'Cancel';
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
  const path = `robots.${type}.action_layout.${action}.presets${suffix}`;
  const patch = Array.isArray(items)
    ? { [path]: items }
    : { [`${path}.${selectedKey}`]: items[selectedKey] };

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
    updateEditState(select, $(`${selectId}-edit`));

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

  const group = presetGroup(action, side);
  const updated = Array.isArray(group)
    ? group.map(item => {
        if (presetKey(item) !== key) return item;
        const normalized = { ...item, key, value };
        delete normalized.name;
        return normalized;
      })
    : { ...group, [key]: value };
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
    updateEditState(select, edit);
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
  $(selectId)?.addEventListener('change', () => {
    updateEditState($(selectId), $(`${selectId}-edit`));
  });
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

window.getRobotControlPayload = () => {
  const payload = { source: 'manual' };
  for (const [prefix, action] of [['arm', 'arm'], ['gripper', handAction()]]) {
    for (const side of ['left', 'right']) {
      if (!checked(`chk-${prefix}-${side}`)) continue;
      const value = readPreset(`${prefix}-${side}-preset`);
      if (value) payload[`${side[0]}_${action}`] = value;
    }
  }
  ['head', 'waist', 'body', 'wheel', 'leg'].forEach(action => {
    if (!checked(`chk-${action}`)) return;
    const value = readPreset(`${action}-preset`);
    if (value) payload[action] = value;
  });
  return Object.keys(payload).length > 1 ? payload : null;
};

$('btn-arm')?.addEventListener('click', async () => {
  toast('Sending arm command...', 'info');
  if (await sendPair('arm', 'arm', 'arm')) toast('Arm command sent.', 'ok');
});
$('btn-gripper')?.addEventListener('click', async () => {
  if (await sendPair('gripper', handAction(), 'gripper')) toast('Gripper / Hand command sent.', 'ok');
});
$('btn-body')?.addEventListener('click', async () => {
  if (await sendActions('body', ['head', 'waist', 'body'])) toast('Head / Waist / Body command sent.', 'ok');
});

$('btn-wheel')?.addEventListener('click', async () => {
  if (await sendActions('wheel', ['wheel', 'leg'])) toast('Wheel / Leg command sent.', 'ok');
});

document.addEventListener('app-config-updated', refreshControls);
refreshControls();
}
