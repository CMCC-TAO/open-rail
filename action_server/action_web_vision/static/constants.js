/**
 * Action Web Vision — Constants & State
 *
 * WebSocket: ws://localhost:9000/ws
 *   Receives:
 *     - Binary: camera_data_binary (camera_id: 0=head, 1=wrist-left, 2=wrist-right)
 *     - JSON: { type: 'joint_data', data: { tab:'position', type:'state', joints_y:[...], timestamp } }
 *     - JSON: { type: 'stats', data: { cpu_usage, gpu_usage, mem_usage, bandwidth_m, task_progress } }
 *
 * VisualizeServer: ws://localhost:8765
 *   Receives (when task active):
 *     - Binary: camera_data_binary
 *     - JSON: { type: 'joint_data', data: { type:'action_fitted'|'action_raw'|'state', ... } }
 */
'use strict';

// ── WebSocket URLs ─────────────────────────────────────────────────────────
const WS_SCHEME = location.protocol === 'https:' ? 'wss' : 'ws';

function resolveWsHostname(hostname) {
  const normalized = String(hostname || '').trim().toLowerCase();
  if (!normalized || normalized === '0.0.0.0' || normalized === '::' || normalized === '[::]' || normalized === '::0') {
    return '127.0.0.1';
  }
  return hostname;
}

const WS_HOSTNAME = resolveWsHostname(location.hostname);
const WS_PORT = location.port ? `:${location.port}` : '';
const WS_URL = `${WS_SCHEME}://${WS_HOSTNAME}${WS_PORT}/ws`;
const RECONNECT = 3000;

// VisualizeServer (action curves) — port 8765
const CAM_WS_URL = `${WS_SCHEME}://${WS_HOSTNAME}:8765`;
const CAM_WS_RECONNECT = 3000;

// ── Trajectory ─────────────────────────────────────────────────────────────
const TRAJ_WINDOW_SPAN_SEC = 10.0;
const TRAJ_WINDOW_SPAN_SEC_MAX = 15.0;
const TRAJ_BUFFER_HARD_MAX_POINTS = 20000;
const TRAJ_RENDER_POINT_MAX = 700;
const DEFAULT_TRAJ_UPDATE_MS = 50;

// 14-joint palette
const JOINT_COLORS = [
  'rgb(220, 20, 60)',   // L0
  'rgb(255, 140, 0)',   // L1
  'rgb(255, 0, 255)',   // L2
  'rgb(0, 150, 0)',     // L3
  'rgb(0, 70, 255)',    // L4
  'rgb(75, 0, 130)',    // L5
  'rgb(186, 85, 211)',  // L6
  'rgb(0, 191, 255)',   // R0
  'rgb(255, 20, 147)',  // R1
  'rgb(139, 69, 19)',   // R2
  'rgb(184, 134, 11)',  // R3
  'rgb(0, 128, 128)',   // R4
  'rgb(160, 32, 240)',  // R5
  'rgb(255, 105, 180)', // R6
];

function normalizeTrajWindowSpanSec(rawSpanSec, fallback = TRAJ_WINDOW_SPAN_SEC) {
  const fallbackVal = Number(fallback);
  const fallbackSafe = Number.isFinite(fallbackVal) && fallbackVal > 0
    ? Math.min(fallbackVal, TRAJ_WINDOW_SPAN_SEC_MAX)
    : 2.25;
  const span = Number(rawSpanSec);
  if (!Number.isFinite(span) || span <= 0) return fallbackSafe;
  return Math.min(span, TRAJ_WINDOW_SPAN_SEC_MAX);
}

// ── App State ──────────────────────────────────────────────────────────────
const App = {
  ws: null,
  wsAlive: false,
  reconnectTimer: null,

  // VisualizeServer WebSocket (port 8765)
  camWs: null,
  camWsAlive: false,
  camWsReconnectTimer: null,

  // Camera state
  camOpen: [true, true, true],
  pendingFrames: {},
  pendingUpdate: false,
  lastCamUpdate: 0,
  camUpdateTimer: null,

  // Trajectory state
  traj: {
    source: new Set(['state']),
    numJoints: 14,
    selectedJoints: new Set([0, 1, 2, 3]),
    buffer: { state: [], action_fitted: [], action_raw: [] },
    startTimeSec: null,
    lastX: 0,
    xLeft: 0, xRight: 0,
    windowSpanSec: normalizeTrajWindowSpanSec(TRAJ_WINDOW_SPAN_SEC),
    chart: null,
    dirty: false,
    updateIntervalMs: DEFAULT_TRAJ_UPDATE_MS,
    updateTimer: null,
    lastUpdateAt: 0,
  },
};
