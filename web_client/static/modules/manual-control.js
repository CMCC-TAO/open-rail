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
  presets(action, side).forEach(({ name, value }) => {
    if (!Array.isArray(value) || !value.every(v => Number.isFinite(Number(v)))) return;
    const option = document.createElement('option');
    option.textContent = String(name);
    option.dataset.name = String(name);
    option.value = JSON.stringify(value.map(Number));
    select.appendChild(option);
  });
  const layoutAvailable = hasLayout(action);
  const presetsAvailable = select.options.length > 0;
  const supported = layoutAvailable && presetsAvailable;
  const reason = !layoutAvailable
    ? `Disabled: action_layout does not define "${action}".`
    : `Disabled: no presets configured for "${action}".`;
  const targets = [select.closest('.robot-preset-row'), select, check, edit].filter(Boolean);
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
  if (edit) edit.disabled = select.disabled;
};
const selectDefault = (id) => {
  const select = $(id);
  if (!select) return;
  const option = [...select.options].find(item => item.dataset.name === 'Default');
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

const requestPresetValue = (name, current) => new Promise(resolve => {
  const modal = $('modal-preset-edit');
  const title = $('preset-edit-title');
  const input = $('preset-edit-value');
  const confirm = $('btn-preset-edit-confirm');
  const cancel = $('btn-preset-edit-cancel');
  if (!modal || !title || !input || !confirm || !cancel) {
    resolve(null);
    return;
  }

  const finish = value => {
    modal.classList.add('hidden');
    document.removeEventListener('keydown', onKeyDown);
    resolve(value);
  };
  const onKeyDown = event => {
    if (event.key === 'Enter') finish(input.value);
    if (event.key === 'Escape') finish(null);
  };

  title.textContent = `Edit Preset: ${name}`;
  input.value = JSON.stringify(current);
  confirm.onclick = () => finish(input.value);
  cancel.onclick = () => finish(null);
  modal.onclick = event => {
    if (event.target === modal) finish(null);
  };
  document.addEventListener('keydown', onKeyDown);
  modal.classList.remove('hidden');
  requestAnimationFrame(() => {
    input.focus();
    input.select();
  });
});

const editPreset = async (selectId, action, side = null) => {
  const select = $(selectId);
  const option = select?.selectedOptions?.[0];
  const current = readPreset(selectId);
  if (!option?.dataset.name || !current) return;

  const name = option.dataset.name;
  const input = await requestPresetValue(name, current);
  if (input === null) return;

  let value;
  try {
    value = JSON.parse(input);
  } catch (_) {
    toast('Preset value must be a valid JSON array.', 'error');
    return;
  }
  if (!Array.isArray(value) || value.length !== current.length || !value.every(Number.isFinite)) {
    toast(`Preset value must contain ${current.length} finite numbers.`, 'error');
    return;
  }

  const type = String(App.config?.robots?.type || '');
  const items = presets(action, side);
  const updated = items.map(item => (
    String(item.name) === name ? { ...item, value } : item
  ));
  const suffix = side ? `.${side}` : '';
  const patch = {
    [`robots.${type}.action_layout.${action}.presets${suffix}`]: updated,
  };

  try {
    const res = await apiFetch('/api/client/config/patch', {
      method: 'POST',
      body: JSON.stringify({ patch }),
    });
    App.config = res.config || App.config;
    refreshControls();
    const refreshed = $(selectId);
    const selected = [...refreshed.options].find(item => item.dataset.name === name);
    if (selected) refreshed.value = selected.value;

    const display = $('conf-path-display');
    const path = display?.dataset.fullPath || display?.textContent.trim() || '';
    if (path) {
      await apiFetch('/api/client/config/save', {
        method: 'POST',
        body: JSON.stringify({ path }),
      });
    }
    toast(`Preset "${name}" updated.`, 'ok');
  } catch (_) { /* apiFetch already toasted */ }
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
