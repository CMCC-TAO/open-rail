const simulationTrajectory = { streamId: null, sequence: 0, saved: null };

function resetSimulationTrajectoryBuffer() {
  const t = App.traj;
  t.buffer = { state: [], action_fitted: [], action_raw: [] };
  t.startTimeSec = null;
  t.lastX = 0;
  t.xLeft = 0;
  t.xRight = 0;
  t.dirty = true;
}

function syncSimulationTrajectoryControls() {
  for (const [id, source] of [['chk-traj-state', 'state'], ['chk-traj-action-fitted', 'action_fitted'], ['chk-traj-action-raw', 'action_raw']]) {
    const checkbox = $(id);
    if (checkbox) {
      checkbox.disabled = false;
      checkbox.checked = App.traj.source.has(source);
    }
  }
  const button = $('btn-traj-pause');
  const allSources = $('btn-traj-all');
  if (allSources) {
    allSources.disabled = false;
    const sources = ['state', 'action_fitted', 'action_raw'];
    allSources.textContent = sources.every(source => App.traj.source.has(source)) ? 'None' : 'All';
  }
  if (button) button.innerHTML = App.traj.paused
    ? '<i class="fas fa-play"></i> Play' : '<i class="fas fa-pause"></i> Pause';
}

function applySimulationTrajectory(trajectory) {
  if (!trajectory?.labels?.length || !trajectory.samples?.length) return;
  const t = App.traj;
  const sources = ['state', 'action_fitted', 'action_raw'].filter(source =>
    trajectory.sources?.includes(source) || trajectory.samples.some(sample =>
      Array.isArray(sample[source]) && sample[source].length === trajectory.labels.length));
  if (!simulationTrajectory.saved) {
    simulationTrajectory.saved = {
      selectedJoints: new Set(t.selectedJoints), source: new Set(t.source), paused: t.paused,
      windowSpanSec: t.windowSpanSec,
    };
  }
  if (simulationTrajectory.streamId !== trajectory.stream_id) {
    simulationTrajectory.streamId = trajectory.stream_id;
    simulationTrajectory.sequence = 0;
    t.simulationLayout = { streamId: trajectory.stream_id, labels: trajectory.labels, sources };
    $('panel-traj').classList.add('simulation-trajectory');
    t.selectedJoints = new Set(trajectory.labels.map((_, i) => i));
    t.source = new Set(['state', 'action_fitted']);
    t.paused = false;
    resetSimulationTrajectoryBuffer();
    syncTrajLayoutFromConfig();
    syncSimulationTrajectoryControls();
    $('trajectory-source-label').textContent = 'Simulation Trajectories · Env 1';
  }
  t.simulationLayout.sources = sources;
  syncSimulationTrajectoryControls();
  for (const sample of trajectory.samples) {
    if (sample.sequence <= simulationTrajectory.sequence) continue;
    const values = source => Array.isArray(sample[source]) && sample[source].length === trajectory.labels.length
      ? sample[source] : [];
    ingestTrajData(values('state'), values('action_fitted'), values('action_raw'), sample.timestamp, 'simulation');
    simulationTrajectory.sequence = sample.sequence;
  }
}

function restoreSimulationTrajectory() {
  if (!simulationTrajectory.saved) return;
  delete App.traj.simulationLayout;
  $('panel-traj').classList.remove('simulation-trajectory');
  Object.assign(App.traj, simulationTrajectory.saved);
  simulationTrajectory.saved = null;
  simulationTrajectory.streamId = null;
  simulationTrajectory.sequence = 0;
  resetSimulationTrajectoryBuffer();
  syncTrajLayoutFromConfig();
  renderJointSelector();
  syncSimulationTrajectoryControls();
  syncTrajWindowSpanUI();
  refreshUnifiedChart();
  $('trajectory-source-label').textContent = 'Trajectory Viewer';
}
