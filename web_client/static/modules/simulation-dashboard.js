import { initializeSimulation } from "/static/simulation.js?v=20261026-preview-lifecycle";

const panel = document.getElementById("panel-simulation");
const source = document.getElementById("sim-preview-source");
let runningJob = null;

function syncSimulationPreview() {
  const robotType = getSimulationClientConfig().robots?.type;
  const enabled = SIMULATION_ROBOT_TYPES.has(robotType) &&
    runningJob?.robotType === robotType && source.value === "simulation";
  setSimulationPreviewJob(enabled ? runningJob.id : null);
}

source.addEventListener("change", syncSimulationPreview);
document.addEventListener("app-config-updated", syncSimulationPreview);
document.addEventListener("simulation-evaluation-state", event => {
  runningJob = event.detail.runningJob;
  syncSimulationPreview();
});
initializeSimulation(panel, "sim-", getSimulationClientConfig);
