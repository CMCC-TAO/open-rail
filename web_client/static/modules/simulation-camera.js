const simulationPreview = { active: false, jobId: null, timestamp: null, savedOpen: null };

function clearCameraFrames() {
  camState.displayGeneration = (camState.displayGeneration || 0) + 1;
  camState.pendingData = {};
  camState.pendingUpdate = false;
  for (let i = 0; i < 3; i++) {
    const image = $(`cam-img-${i}`);
    if (image.src.startsWith('blob:')) URL.revokeObjectURL(image.src);
    image.removeAttribute('src');
    image.classList.remove('loaded');
    const placeholder = $(`cam-placeholder-${i}`);
    placeholder.textContent = 'Waiting for camera frames…';
    placeholder.style.display = App.camOpen[i] ? '' : 'none';
  }
}

async function applySimulationPreview(snapshot) {
  const job = snapshot.job;
  if (!job) {
    restoreSimulationTrajectory();
    if (!simulationPreview.active) return;
    clearCameraFrames();
    simulationPreview.active = false;
    simulationPreview.jobId = null;
    simulationPreview.timestamp = null;
    for (let i = 0; i < 3; i++) {
      if (App.camOpen[i] !== simulationPreview.savedOpen[i]) await toggleCamera(i, false);
      $(`cam-row-${i}`).querySelector('.cam-label').textContent = CAM_NAMES[i];
    }
    $('camera-source-label').textContent = 'Camera Viewer';
    return;
  }
  if (!simulationPreview.active) simulationPreview.savedOpen = [...App.camOpen];
  simulationPreview.active = true;
  if (simulationPreview.jobId !== job.id) {
    simulationPreview.jobId = job.id;
    simulationPreview.timestamp = null;
    for (let i = 0; i < 3; i++) {
      if (!App.camOpen[i]) await toggleCamera(i, false);
    }
    clearCameraFrames();
  }
  $('camera-source-label').textContent = `Simulation Cameras · ${job.env_name} · Environment 1`;
  applySimulationTrajectory(snapshot.trajectory);
  if (!snapshot.frames.length) {
    clearCameraFrames();
    simulationPreview.timestamp = null;
    return;
  }
  if (snapshot.timestamp === simulationPreview.timestamp) return;
  simulationPreview.timestamp = snapshot.timestamp;
  for (const frame of snapshot.frames) {
    const bytes = Uint8Array.from(atob(frame.jpeg), c => c.charCodeAt(0));
    $(`cam-row-${frame.camera_id}`).querySelector('.cam-label').textContent = frame.name;
    handleCameraFrame(frame.camera_id, bytes, 'simulation');
  }
}

async function pollSimulationPreview() {
  if (document.hidden) {
    setTimeout(pollSimulationPreview, 1000);
    return;
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 3000);
  try {
    const response = await fetch('/api/simulation/preview', { cache: 'no-store', signal: controller.signal });
    if (response.ok) await applySimulationPreview(await response.json());
  } catch (_) {
    if (simulationPreview.active) clearCameraFrames();
  } finally {
    clearTimeout(timeout);
    setTimeout(pollSimulationPreview, simulationPreview.active ? 200 : 1000);
  }
}
