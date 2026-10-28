const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const staticDir = path.join(__dirname, '..', 'web_client', 'static');
const settle = () => new Promise(resolve => setImmediate(resolve));

function setup(robotType = 'robotwin_aloha') {
  const elements = new Map();
  const timers = new Map();
  const requests = [];
  let timerId = 0;
  const element = id => {
    if (!elements.has(id)) {
      const node = new EventTarget();
      Object.assign(node, {
        src: '', value: 'simulation', style: {}, textContent: '',
        classList: { remove() {} },
        removeAttribute() { this.src = ''; },
        querySelector: () => element(id + '-label'),
      });
      elements.set(id, node);
    }
    return elements.get(id);
  };
  const document = new EventTarget();
  document.hidden = false;
  document.getElementById = element;
  const app = { config: { robots: { type: robotType } }, camOpen: [false, true, false] };
  const context = vm.createContext({
    document, CustomEvent, AbortController, Uint8Array, atob,
    URL: { revokeObjectURL() {} },
    App: app, camState: {}, CAM_NAMES: ['Head', 'Left', 'Right'],
    $: element,
    SIMULATION_ROBOT_TYPES: new Set(['robotwin_aloha', 'robocasa_pandas']),
    getSimulationClientConfig: () => app.config,
    initializeSimulation() {},
    restoreSimulationTrajectory() {},
    applySimulationTrajectory() {},
    handleCameraFrame() {},
    toggleCamera(index) { app.camOpen[index] = !app.camOpen[index]; },
    setTimeout(fn, delay) {
      const id = ++timerId;
      timers.set(id, { fn, delay });
      return id;
    },
    clearTimeout(id) { timers.delete(id); },
    fetch(url, options) {
      return new Promise(resolve => requests.push({ url, signal: options.signal, resolve }));
    },
  });
  vm.runInContext(fs.readFileSync(path.join(staticDir, 'modules/simulation-camera.js'), 'utf8'), context);
  const dashboard = fs.readFileSync(path.join(staticDir, 'modules/simulation-dashboard.js'), 'utf8');
  vm.runInContext(dashboard.replace(/^import .*;\n/, ''), context);
  return {
    app, document, requests, timers,
    state: () => vm.runInContext('simulationPreview', context),
    job(id = 'job-1', type = 'robotwin_aloha') {
      document.dispatchEvent(new CustomEvent('simulation-evaluation-state', {
        detail: { active: true, runningJob: { id, robotType: type } },
      }));
    },
    stop(active = false) {
      document.dispatchEvent(new CustomEvent('simulation-evaluation-state', {
        detail: { active, runningJob: null },
      }));
    },
    selectRobot(type) {
      app.config.robots.type = type;
      document.dispatchEvent(new CustomEvent('app-config-updated'));
    },
    source(value) {
      element('sim-preview-source').value = value;
      element('sim-preview-source').dispatchEvent(new Event('change'));
    },
    async respond(index = 0, id = 'job-1') {
      requests[index].resolve({
        ok: true,
        json: async () => ({ job: id ? { id, env_name: 'Test' } : null, frames: [] }),
      });
      await settle();
    },
    async tick(delay) {
      const entry = [...timers].find(([, timer]) => timer.delay === delay);
      assert.ok(entry, `Missing timer with delay ${delay}`);
      timers.delete(entry[0]);
      entry[1].fn();
      await settle();
    },
  };
}

test('idle and submitting evaluations do not request previews', () => {
  const h = setup();
  h.stop(true);
  assert.equal(h.requests.length, 0);
  assert.equal(h.timers.size, 0);
  assert.equal(h.state().enabled, false);
});

test('only a matching simulation robot can enable previews', () => {
  const h = setup('mock');
  h.job();
  h.selectRobot('robocasa_pandas');
  assert.equal(h.requests.length, 0);
  h.selectRobot('robotwin_aloha');
  assert.equal(h.requests.length, 1);
  assert.equal(h.requests[0].url, '/api/simulation/preview');
});

test('repeated running events keep a single polling loop', async () => {
  const h = setup();
  h.job();
  h.job();
  await h.respond();
  h.job();
  assert.deepEqual(h.app.camOpen, [true, true, true]);
  assert.equal(h.requests.length, 1);
  assert.equal(h.timers.size, 1);
  await h.tick(200);
  assert.equal(h.requests.length, 2);
});

test('finishing or stopping restores camera state and clears timers', async () => {
  const h = setup();
  h.job();
  await h.respond();
  h.stop(true);
  assert.deepEqual(h.app.camOpen, [false, true, false]);
  assert.equal(h.state().active, false);
  assert.equal(h.timers.size, 0);
});

test('late responses after cancellation cannot reopen a preview', async () => {
  const h = setup();
  h.job();
  h.stop();
  assert.equal(h.requests[0].signal.aborted, true);
  await h.respond();
  assert.equal(h.state().active, false);
  assert.equal(h.timers.size, 0);
  assert.deepEqual(h.app.camOpen, [false, true, false]);
});

test('changing the preview source cancels and can restart a running preview', async () => {
  const h = setup();
  h.job();
  h.source('robot');
  assert.equal(h.requests[0].signal.aborted, true);
  h.source('simulation');
  assert.equal(h.requests.length, 2);
  await h.respond(1);
  await h.respond(0);
  assert.equal(h.state().active, true);
  assert.equal(h.timers.size, 1);
});

test('switching robot types closes an active preview', async () => {
  const h = setup();
  h.job();
  await h.respond();
  h.selectRobot('robocasa_pandas');
  assert.equal(h.state().enabled, false);
  assert.equal(h.timers.size, 0);
  assert.deepEqual(h.app.camOpen, [false, true, false]);
});

test('restarting with a new job ignores the previous response', async () => {
  const h = setup();
  h.job();
  h.job('job-2');
  await h.respond(1, 'job-2');
  await h.respond(0);
  assert.equal(h.state().jobId, 'job-2');
  assert.equal(h.timers.size, 1);
});

test('a preview for another job is never displayed', async () => {
  const h = setup();
  h.job();
  await h.respond(0, 'other-job');
  assert.equal(h.state().active, false);
  assert.deepEqual(h.app.camOpen, [false, true, false]);
});

test('hidden pages pause requests and stopping cancels the visibility timer', async () => {
  const h = setup();
  h.document.hidden = true;
  h.job();
  assert.equal(h.requests.length, 0);
  h.document.hidden = false;
  await h.tick(1000);
  assert.equal(h.requests.length, 1);
  h.stop();
  await h.respond();
  assert.equal(h.timers.size, 0);
});
