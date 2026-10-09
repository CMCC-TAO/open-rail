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
      checkbox.checked = App.traj.source.has(source);
      checkbox.disabled = !!App.traj.simulationLayout && source !== 'state';
    }
  }
  const button = $('btn-traj-pause');
  const allSources = $('btn-traj-all');
  if (allSources) allSources.disabled = !!App.traj.simulationLayout;
  if (button) button.innerHTML = App.traj.paused
    ? '<i class="fas fa-play"></i> Play' : '<i class="fas fa-pause"></i> Pause';
}

function applySimulationTrajectory(trajectory) {
  if (!trajectory?.labels?.length || !trajectory.samples?.length) return;
  const t = App.traj;
  if (!simulationTrajectory.saved) {
    simulationTrajectory.saved = {
      selectedJoints: new Set(t.selectedJoints), source: new Set(t.source), paused: t.paused,
      windowSpanSec: t.windowSpanSec,
    };
  }
  if (simulationTrajectory.streamId !== trajectory.stream_id) {
    simulationTrajectory.streamId = trajectory.stream_id;
    simulationTrajectory.sequence = 0;
    t.simulationLayout = { streamId: trajectory.stream_id, labels: trajectory.labels };
    t.selectedJoints = new Set(trajectory.labels.map((_, i) => i));
    t.source = new Set(['state']);
    t.paused = false;
    resetSimulationTrajectoryBuffer();
    syncTrajLayoutFromConfig();
    syncSimulationTrajectoryControls();
    $('trajectory-source-label').textContent = '仿真关节轨迹 · 环境 1';
  }
  for (const sample of trajectory.samples) {
    if (sample.sequence <= simulationTrajectory.sequence) continue;
    if (!Array.isArray(sample.state) || sample.state.length !== trajectory.labels.length) continue;
    ingestTrajData(sample.state, [], [], sample.timestamp, 'simulation');
    simulationTrajectory.sequence = sample.sequence;
  }
}

function restoreSimulationTrajectory() {
  if (!simulationTrajectory.saved) return;
  delete App.traj.simulationLayout;
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
