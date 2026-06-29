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
  if (!select || !check) return;
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
  const targets = [select.closest('.robot-preset-row'), select, check].filter(Boolean);
  if (supported) {
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
  ['head', 'waist', 'body'].forEach(action => {
    populate(`${action}-preset`, `chk-${action}`, action);
  });
};

[
  ['chk-arm-left', 'arm-left-preset'],
  ['chk-arm-right', 'arm-right-preset'],
  ['chk-gripper-left', 'gripper-left-preset'],
  ['chk-gripper-right', 'gripper-right-preset'],
  ['chk-head', 'head-preset'],
  ['chk-waist', 'waist-preset'],
  ['chk-body', 'body-preset'],
].forEach(([checkId, selectId]) => {
  $(checkId)?.addEventListener('change', () => {
    const select = $(selectId);
    if (select) select.disabled = !checked(checkId);
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

const sendBody = async () => {
  const payload = { source: 'manual' };
  ['head', 'waist', 'body'].forEach(action => {
    if (checked(`chk-${action}`)) {
      const value = readPreset(`${action}-preset`);
      if (value) payload[action] = value;
    }
  });
  return Object.keys(payload).length > 1 && sendControl('body', payload);
};

$('btn-arm')?.addEventListener('click', async () => {
  if (await sendPair('arm', 'arm', 'arm')) toast('Arm set.', 'ok');
});
$('btn-arm-reset')?.addEventListener('click', async () => {
  if (checked('chk-arm-left')) selectDefault('arm-left-preset');
  if (checked('chk-arm-right')) selectDefault('arm-right-preset');
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
  if (await sendBody()) toast('Head / Waist / Body set.', 'ok');
});
$('btn-body-reset')?.addEventListener('click', async () => {
  ['head', 'waist', 'body'].forEach(action => {
    if (checked(`chk-${action}`)) selectDefault(`${action}-preset`);
  });
  if (await sendBody()) toast('Head / Waist / Body reset.', 'ok');
});

const sendWheel = async (linear, angular, message) => {
  await sendControl('wheel', { pos: [linear, angular] });
  toast(message, 'ok');
};
$('btn-wheel-forward')?.addEventListener('click', () => sendWheel(0.1, 0, 'Wheel forward.'));
$('btn-wheel-backward')?.addEventListener('click', () => sendWheel(-0.1, 0, 'Wheel backward.'));
$('btn-wheel-left')?.addEventListener('click', () => sendWheel(0, 0.1, 'Wheel turn left.'));
$('btn-wheel-right')?.addEventListener('click', () => sendWheel(0, -0.1, 'Wheel turn right.'));

document.addEventListener('app-config-updated', refreshControls);
refreshControls();
}
