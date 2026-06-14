function setupManualControlEvents() {
// Manual robot control
const getNum = (id, fallback = 0) => {
  const v = Number($(id)?.value);
  return Number.isFinite(v) ? v : fallback;
};
const getChecked = (id) => !!$(id)?.checked;

const getGripperState = () => {
  const value = getNum('gripper-value', 0);
  const useLeft = getChecked('chk-gripper-left');
  const useRight = getChecked('chk-gripper-right');
  return { value, useLeft, useRight };
};

const sendGripperBySelection = async (target = null) => {
  const { value, useLeft, useRight } = getGripperState();
  if (!useLeft && !useRight) {
    toast('Select Left or Right gripper first.', 'warn');
    return;
  }

  const val = Number.isFinite(target) ? target : value;
  $('gripper-value').value = String(val);
  const cur = Array.isArray(App.latestState) ? App.latestState : [];
  const curL = Number.isFinite(Number(cur[14])) ? Number(cur[14]) : 0;
  const curR = Number.isFinite(Number(cur[15])) ? Number(cur[15]) : 0;
  const nextL = useLeft ? val : curL;
  const nextR = useRight ? val : curR;
  await sendCommand('gripper', { pos: [nextL, nextR] });
};

$('btn-gripper-send').addEventListener('click', async () => {
  await sendGripperBySelection();
});
$('btn-gripper-open').addEventListener('click', async () => {
  await sendGripperBySelection(1);
  toast('Gripper opened.', 'ok');
});
$('btn-gripper-close').addEventListener('click', async () => {
  await sendGripperBySelection(0);
  toast('Gripper closed.', 'ok');
});

const HEAD_SAVE_KEY = 'manual.head.saved';
const WAIST_SAVE_KEY = 'manual.waist.saved';
const BODY_SAVE_KEY = 'manual.body.saved';
const ARM_SAVE_KEY = 'manual.arm.saved';

const approxEq = (a, b) => Math.abs(Number(a) - Number(b)) < 1e-9;
const samePose = (a, b) => Array.isArray(a) && Array.isArray(b) && a.length === b.length && a.every((v, i) => approxEq(v, b[i]));

const createManualCtrlState = ({ inputIds, setBtnId, saveBtnId, saveKey }) => {
  const readPose = () => inputIds.map(id => getNum(id, 0));
  let savedPose = readPose();
  try {
    const raw = localStorage.getItem(saveKey);
    const parsed = raw ? JSON.parse(raw) : null;
    if (parsed && typeof parsed === 'object') {
      const vals = inputIds.map(id => getNum(id, 0));
      const loaded = inputIds.map((id, idx) => {
        const key = id.replace(/^[^-]+-/, '');
        const v = Number(parsed[key]);
        return Number.isFinite(v) ? v : vals[idx];
      });
      savedPose = loaded;
    }
  } catch (_) {}

  let appliedPose = readPose();
  const setBtn = $(setBtnId);
  const saveBtn = $(saveBtnId);

  const refresh = () => {
    const cur = readPose();
    setBtn?.classList.toggle('btn-primary', !samePose(cur, appliedPose));
    saveBtn?.classList.toggle('btn-unsaved-star', !samePose(cur, savedPose));
  };

  inputIds.forEach(id => {
    $(id)?.addEventListener('input', refresh);
    $(id)?.addEventListener('change', refresh);
  });

  return {
    refresh,
    markApplied: () => { appliedPose = readPose(); refresh(); },
    markSaved: () => {
      savedPose = readPose();
      const payload = {};
      inputIds.forEach((id, idx) => {
        const key = id.replace(/^[^-]+-/, '');
        payload[key] = savedPose[idx];
      });
      localStorage.setItem(saveKey, JSON.stringify(payload));
      refresh();
    },
  };
};

const headCtrlState = createManualCtrlState({
  inputIds: ['head-yaw', 'head-pitch', 'head-roll'],
  setBtnId: 'btn-head',
  saveBtnId: 'btn-head-save',
  saveKey: HEAD_SAVE_KEY,
});
const waistCtrlState = createManualCtrlState({
  inputIds: ['waist-yaw', 'waist-pitch', 'waist-roll'],
  setBtnId: 'btn-waist',
  saveBtnId: 'btn-waist-save',
  saveKey: WAIST_SAVE_KEY,
});
const bodyCtrlState = createManualCtrlState({
  inputIds: ['body-height'],
  setBtnId: 'btn-body',
  saveBtnId: 'btn-body-save',
  saveKey: BODY_SAVE_KEY,
});

const formatArmPose = (arr) => `[${arr.map(v => Number(v).toFixed(3)).join(', ')}]`;
const parseArmPose = (text) => {
  if (typeof text !== 'string') return null;
  const stripped = text.trim().replace(/^\[/, '').replace(/\]$/, '');
  const parts = stripped.split(',').map(s => Number(s.trim())).filter(v => Number.isFinite(v));
  if (parts.length !== 7) return null;
  return parts;
};
const getDefaultArmPose = () => {
  const resetPose = App.config?.robots?.a2d?.reset_robot_pos;
  if (Array.isArray(resetPose) && resetPose.length >= 14) return resetPose.slice(0, 14).map(Number);
  const current = Array.isArray(App.latestState) ? App.latestState.slice(0, 14) : [];
  if (current.length >= 14) return current.map(Number);
  return new Array(14).fill(0);
};
const getArmInputsPose = () => {
  const left = parseArmPose($('arm-left-joints')?.value || '');
  const right = parseArmPose($('arm-right-joints')?.value || '');
  if (!left || !right) return null;
  return [...left, ...right];
};
const setArmInputsPose = (pose14) => {
  if (!Array.isArray(pose14) || pose14.length < 14) return;
  $('arm-left-joints').value = formatArmPose(pose14.slice(0, 7));
  $('arm-right-joints').value = formatArmPose(pose14.slice(7, 14));
};

let armSavedPose = getDefaultArmPose();
try {
  const raw = localStorage.getItem(ARM_SAVE_KEY);
  const parsed = raw ? JSON.parse(raw) : null;
  if (parsed && Array.isArray(parsed.left) && Array.isArray(parsed.right) && parsed.left.length === 7 && parsed.right.length === 7) {
    armSavedPose = [...parsed.left, ...parsed.right].map(Number);
  }
} catch (_) {}
setArmInputsPose(armSavedPose);
let armAppliedPose = armSavedPose.slice();

const syncArmEditors = () => {
  const leftOn = getChecked('chk-arm-left');
  const rightOn = getChecked('chk-arm-right');
  const leftEl = $('arm-left-joints');
  const rightEl = $('arm-right-joints');
  if (leftEl) leftEl.disabled = !leftOn;
  if (rightEl) rightEl.disabled = !rightOn;
};

const refreshArmState = () => {
  const cur = getArmInputsPose();
  const setBtn = $('btn-arm');
  const saveBtn = $('btn-arm-save');
  const dirtyApplied = !cur || !samePose(cur, armAppliedPose);
  const dirtySaved = !cur || !samePose(cur, armSavedPose);
  setBtn?.classList.toggle('btn-primary', dirtyApplied);
  saveBtn?.classList.toggle('btn-unsaved-star', dirtySaved);
};
['arm-left-joints', 'arm-right-joints'].forEach(id => {
  $(id)?.addEventListener('input', refreshArmState);
  $(id)?.addEventListener('change', refreshArmState);
});
['chk-arm-left', 'chk-arm-right'].forEach(id => {
  $(id)?.addEventListener('change', () => {
    syncArmEditors();
    refreshArmState();
  });
});

const sendArmBySelection = async () => {
  const useLeft = getChecked('chk-arm-left');
  const useRight = getChecked('chk-arm-right');
  if (!useLeft && !useRight) {
    toast('Select Left or Right arm first.', 'warn');
    return false;
  }
  const typed = getArmInputsPose();
  if (!typed) {
    toast('Arm joint format invalid. Use [v1, v2, ..., v7].', 'warn');
    return false;
  }
  const base = Array.isArray(App.latestState) && App.latestState.length >= 14
    ? App.latestState.slice(0, 14).map(Number)
    : getDefaultArmPose();
  const target = base.slice();
  if (useLeft) {
    for (let i = 0; i < 7; i++) target[i] = typed[i];
  }
  if (useRight) {
    for (let i = 7; i < 14; i++) target[i] = typed[i];
  }
  await sendCommand('arm', { pos: target });
  armAppliedPose = typed.slice();
  refreshArmState();
  return true;
};

const sendHead = async () => {
  await sendCommand('head', { pos: [getNum('head-yaw', 0), getNum('head-pitch', 0.436), getNum('head-roll', 0)] });
};
$('btn-head').addEventListener('click', async () => {
  await sendHead();
  headCtrlState.markApplied();
});
$('btn-head-reset').addEventListener('click', async () => {
  $('head-yaw').value = '0';
  $('head-pitch').value = '0.436';
  $('head-roll').value = '0';
  await sendHead();
  headCtrlState.markApplied();
  toast('Head reset.', 'ok');
});
$('btn-head-save').addEventListener('click', () => {
  headCtrlState.markSaved();
  toast('Head values saved.', 'ok');
});

const sendWaist = async () => {
  await sendCommand('waist', { pos: [getNum('waist-yaw', 0), getNum('waist-pitch', 0.297), getNum('waist-roll', 0)] });
};
$('btn-waist').addEventListener('click', async () => {
  await sendWaist();
  waistCtrlState.markApplied();
});
$('btn-waist-reset').addEventListener('click', async () => {
  $('waist-yaw').value = '0';
  $('waist-pitch').value = '0.297';
  $('waist-roll').value = '0';
  await sendWaist();
  waistCtrlState.markApplied();
  toast('Waist reset.', 'ok');
});
$('btn-waist-save').addEventListener('click', () => {
  waistCtrlState.markSaved();
  toast('Waist values saved.', 'ok');
});

const sendBody = async () => {
  const yaw = getNum('waist-yaw', 0);
  const pitch = getNum('waist-pitch', 0.297);
  const roll = getNum('body-height', 0);
  const waistRollEl = $('waist-roll');
  if (waistRollEl) waistRollEl.value = String(roll);
  await sendCommand('waist', { pos: [yaw, pitch, roll] });
  waistCtrlState.refresh();
};
$('btn-body').addEventListener('click', async () => {
  await sendBody();
  bodyCtrlState.markApplied();
  toast(`Body height set to ${getNum('body-height', 0)} mm.`, 'ok');
});
$('btn-body-reset').addEventListener('click', async () => {
  $('body-height').value = '20';
  await sendBody();
  bodyCtrlState.markApplied();
  toast('Body reset.', 'ok');
});
$('btn-body-save').addEventListener('click', () => {
  bodyCtrlState.markSaved();
  toast('Body values saved.', 'ok');
});

headCtrlState.refresh();
waistCtrlState.refresh();
bodyCtrlState.refresh();
syncArmEditors();
refreshArmState();

$('btn-arm').addEventListener('click', async () => {
  const ok = await sendArmBySelection();
  if (ok) toast('Arm set.', 'ok');
});
$('btn-arm-reset').addEventListener('click', async () => {
  const useLeft = getChecked('chk-arm-left');
  const useRight = getChecked('chk-arm-right');
  if (!useLeft && !useRight) {
    toast('Select Left or Right arm first.', 'warn');
    return;
  }
  const resetPose = getDefaultArmPose();
  const current = getArmInputsPose() || armAppliedPose || resetPose;
  const next = current.slice();
  if (useLeft) {
    for (let i = 0; i < 7; i++) next[i] = Number(resetPose[i]);
  }
  if (useRight) {
    for (let i = 7; i < 14; i++) next[i] = Number(resetPose[i]);
  }
  setArmInputsPose(next);
  const ok = await sendArmBySelection();
  if (ok) toast('Arm reset.', 'ok');
});
$('btn-arm-save').addEventListener('click', () => {
  const cur = getArmInputsPose();
  if (!cur) {
    toast('Arm joint format invalid. Use [v1, v2, ..., v7].', 'warn');
    return;
  }
  armSavedPose = cur.slice();
  localStorage.setItem(ARM_SAVE_KEY, JSON.stringify({ left: cur.slice(0, 7), right: cur.slice(7, 14) }));
  refreshArmState();
  toast('Arm values saved.', 'ok');
});



const sendWheel = async (linear, angular, msg = 'Wheel command sent.') => {
  await sendCommand('wheel', { pos: [linear, angular] });
  toast(msg, 'ok');
};

$('btn-wheel-forward').addEventListener('click',  async () => sendWheel(0.1, 0, 'Wheel forward.'));
$('btn-wheel-backward').addEventListener('click', async () => sendWheel(-0.1, 0, 'Wheel backward.'));
$('btn-wheel-left').addEventListener('click',     async () => sendWheel(0, 0.1, 'Wheel turn left.'));
$('btn-wheel-right').addEventListener('click',    async () => sendWheel(0, -0.1, 'Wheel turn right.'));


}
