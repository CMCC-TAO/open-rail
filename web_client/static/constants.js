/**
 * VLA Web Client — Frontend Logic
 *
 * WebSocket: ws://localhost:9000/ws
 *   Receives: { type: 'stats'|'status'|'error', data: {...} }
 *
 * REST endpoints:
 *   GET  /api/config
 *   POST /api/config/patch       { patch: { "key.path": value, ... } }
 *   POST /api/config/load_file   { path: "..." }
 *   POST /api/config/save_file   { path: "..." }
 *   GET  /api/client/status
 *   POST /api/client/start
 *   POST /api/client/stop
 *   POST /api/client/pause
 *   POST /api/client/resume
 *   POST /api/client/observe/start
 *   POST /api/client/infer/start
 *   POST /api/client/control/start
 *   POST /api/client/command     { command, params }
 */

'use strict';

// ═══════════════════════════════════════════════════════
//  Constants
// ═══════════════════════════════════════════════════════
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
const WS_CONNECT_TIMEOUT_MS = 5000;

// Visual WebSocket — connects to VisualizeServer (port 8765) for camera frames
const CAM_WS_URL = `${WS_SCHEME}://${WS_HOSTNAME}:8765`;
const CAM_WS_RECONNECT = 3000;
const CAM_WS_CONNECT_TIMEOUT_MS = 5000;

// Trajectory x-axis window span (seconds).
// Historical mapping: old point-count window used 600 points with fitting_time_step=3.75ms => 2.25s.
const TRAJ_WINDOW_SPAN_SEC = 10.0;
// Maximum supported trajectory window span (seconds).
const TRAJ_WINDOW_SPAN_SEC_MAX = 15.0;
// Hard cap for safety under very high-frequency streams.
const TRAJ_BUFFER_HARD_MAX_POINTS = 20000;
// Maximum points to render per joint series to avoid chart rendering stalls.
const TRAJ_RENDER_POINT_MAX = 700;
// Default trajectory chart update interval in ms (20 FPS)
const DEFAULT_TRAJ_UPDATE_MS = 50;

// Per-joint colour palette (14 colours, one per joint L0-L6 R0-R6)
const JOINT_COLORS = [
  // L0-L6: High contrast bright colors
  'rgb(220, 20, 60)',   // L0 - Crimson red
  'rgb(255, 140, 0)',   // L1 - Dark orange
  'rgb(255, 0, 255)',   // L2 - Magenta (changed from purple for better contrast)
  'rgb(0, 150, 0)',     // L3 - Forest green (changed from green for better contrast)
  'rgb(0, 70, 255)',    // L4 - Strong blue (changed from blue for better contrast)
  'rgb(75, 0, 130)',    // L5 - Indigo
  'rgb(186, 85, 211)',  // L6 - Medium purple (changed from violet for better contrast)
  
  // R0-R6: Contrasting colors from the first set
  'rgb(0, 191, 255)',   // R0 - Deep sky blue (changed from magenta to avoid repetition)
  'rgb(255, 20, 147)',  // R1 - Deep pink
  'rgb(139, 69, 19)',   // R2 - Saddle brown (changed from brown for better contrast)
  'rgb(184, 134, 11)',  // R3 - Dark goldenrod (changed from olive for better contrast)
  'rgb(0, 128, 128)',   // R4 - Teal
  'rgb(160, 32, 240)',  // R5 - Purple (changed from sienna for better contrast)
  'rgb(255, 105, 180)', // R6 - Hot pink (changed from crimson to ensure uniqueness)
];

// ═══════════════════════════════════════════════════════
//  State
// ═══════════════════════════════════════════════════════

function normalizeTrajWindowSpanSec(rawSpanSec, fallback = TRAJ_WINDOW_SPAN_SEC) {
  const fallbackVal = Number(fallback);
  const fallbackSafe = Number.isFinite(fallbackVal) && fallbackVal > 0
    ? Math.min(fallbackVal, TRAJ_WINDOW_SPAN_SEC_MAX)
    : 2.25;
  const span = Number(rawSpanSec);
  if (!Number.isFinite(span) || span <= 0) return fallbackSafe;
  return Math.min(span, TRAJ_WINDOW_SPAN_SEC_MAX);
}

let _visualPersistTimer = null;
let _visualPersistInFlight = false;

const App = {
  ws: null,
  wsAlive: false,
  reconnectTimer: null,
  wsConnectTimeoutTimer: null,
  isRunning: null,   // null = uninitialised; set on first stats push
  isPaused: false,   // true when client is paused (inference/commands paused but resources alive)
  isObserveRunning: false,
  isInferenceRunning: false,
  isControlRunning: false,
  currentFetchController: null,
  statusPollInFlight: false,

  // Camera WebSocket (port 8765 — VisualizeServer)
  camWs: null,
  camWsAlive: false,
  camWsReconnectTimer: null,
  camWsConnectTimeoutTimer: null,

  config: {},
  pendingPatch: {},
  langPresets: [],

  // Camera open/close state — default all closed
  camOpen: [false, false, false],

  // Language auto mode state
  langAuto: {
    lastProgress: null,
  },

  // ── Trajectory chart state ──
  traj: {
    // Set<'state'|'action_fitted'|'action_raw'> — which sources to display (can be combined)
    source: new Set(['state']),
    // Default manual mode: do not play until user clicks Play
    paused: true,
    // Number of joints (determined from first data push)
    numJoints: 0,
    // Which joints to display  Set<number>
    selectedJoints: new Set(),
    // Data buffer: { state: [...], action_fitted: [...], action_raw: [...] }
    buffer: { state: [], action_fitted: [], action_raw: [] },
    // Time axis baseline and monotonic guard (x-axis in seconds)
    startTimeSec: null,
    lastX: 0,
    // x window bounds
    xLeft: 0, xRight: 0,
    // fixed x-axis sliding window span in seconds
    windowSpanSec: normalizeTrajWindowSpanSec(TRAJ_WINDOW_SPAN_SEC),
    // Single unified Chart.js instance
    chart: null,
    // Dirty flag → batch updates at configured interval
    dirty: false,
    updateIntervalMs: DEFAULT_TRAJ_UPDATE_MS,
    updateTimer: null,
    lastUpdateAt: 0,
  },

  recordingListTimer: null,
  recordingTask: null,
  recordingTasksSnapshot: [],
  recordingChunk: null,
  recordingChunksSnapshot: [],
  recordingEpisodeId: null,
  recordingEpisodeSnapshot: [],
  latestState: [],
  isRecording: false,
};

