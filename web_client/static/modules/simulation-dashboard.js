import { initializeSimulation } from "/static/simulation.js?v=20261012-parallel-envs";

const panel = document.getElementById("panel-simulation");
const source = document.getElementById("sim-preview-source");
source.addEventListener("change", async () => {
  simulationPreview.enabled = source.value === "simulation";
  if (!simulationPreview.enabled)
    await applySimulationPreview({ job: null, frames: [] });
});
initializeSimulation(panel, "sim-", getSimulationClientConfig);
