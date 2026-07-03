// ═══════════════════════════════════════════════════════
//  WebSocket
// ═══════════════════════════════════════════════════════
function connectWS() {
  if (App.ws && App.ws.readyState <= 1) return;
  App.ws = new WebSocket(WS_URL);

  clearTimeout(App.wsConnectTimeoutTimer);
  App.wsConnectTimeoutTimer = setTimeout(() => {
    if (App.ws && App.ws.readyState === WebSocket.CONNECTING) {
      try { App.ws.close(); } catch (_) {}
    }
  }, WS_CONNECT_TIMEOUT_MS);

  App.ws.onopen = () => {
    clearTimeout(App.wsConnectTimeoutTimer);
    App.wsAlive = true;
    updateWSIndicator(true);
    clearTimeout(App.reconnectTimer);
    App._pingTimer = setInterval(() => {
      if (App.ws.readyState === 1) App.ws.send(JSON.stringify({ type: 'ping' }));
    }, 15000);
  };

  App.ws.onmessage = (ev) => {
    try { handleWSMessage(JSON.parse(ev.data)); } catch (e) { /* ignore */ }
  };

  App.ws.onclose = () => {
    clearTimeout(App.wsConnectTimeoutTimer);
    App.wsAlive = false;
    updateWSIndicator(false);
    clearInterval(App._pingTimer);
    // If backend killed while running, interrupt the current log record
    if (App.isRunning && typeof interruptRunningExecRecord === 'function') {
      interruptRunningExecRecord();
    }
    App.reconnectTimer = setTimeout(connectWS, RECONNECT);
  };

  App.ws.onerror = () => App.ws.close();
}

// ═══════════════════════════════════════════════════════
//  Camera WebSocket (VisualizeServer — port 8765)
// ═══════════════════════════════════════════════════════
function connectCamWS() {
  if (App.camWs && App.camWs.readyState <= 1) return;
  App.camWs = new WebSocket(CAM_WS_URL);
  App.camWs.binaryType = 'arraybuffer';

  clearTimeout(App.camWsConnectTimeoutTimer);
  App.camWsConnectTimeoutTimer = setTimeout(() => {
    if (App.camWs && App.camWs.readyState === WebSocket.CONNECTING) {
      try { App.camWs.close(); } catch (_) {}
    }
  }, CAM_WS_CONNECT_TIMEOUT_MS);

  App.camWs.onopen = () => {
    clearTimeout(App.camWsConnectTimeoutTimer);
    App.camWsAlive = true;
    clearTimeout(App.camWsReconnectTimer);
  };

  App.camWs.onmessage = (ev) => {
    if (ev.data instanceof ArrayBuffer || ev.data instanceof Blob) {
      decodeCameraBinaryFrame(ev.data);
      return;
    }

    if (typeof ev.data === 'string') {
      try {
        handleCamWSMessage(JSON.parse(ev.data));
      } catch (e) { /* ignore malformed text frame */ }
    }
  };

  App.camWs.onclose = () => {
    clearTimeout(App.camWsConnectTimeoutTimer);
    App.camWsAlive = false;
    if (App.isRunning) {
      App.camWsReconnectTimer = setTimeout(connectCamWS, CAM_WS_RECONNECT);
    }
  };

  App.camWs.onerror = () => {
    if (App.camWs) App.camWs.close();
  };
}

function disconnectCamWS() {
  clearTimeout(App.camWsReconnectTimer);
  clearTimeout(App.camWsConnectTimeoutTimer);
  if (App.camWs) {
    App.camWs.onclose = null; // prevent auto-reconnect after manual close
    App.camWs.close();
    App.camWs = null;
  }
  App.camWsAlive = false;
}

function handleWSMessage(msg) {
  switch (msg.type) {
    case 'stats':  renderStats(msg.data); break;
    case 'status':
      if (msg?.data) {
        if (typeof msg.data.observe_running === 'boolean') App.isObserveRunning = msg.data.observe_running;
        if (typeof msg.data.inference_running === 'boolean') App.isInferenceRunning = msg.data.inference_running;
        if (typeof msg.data.control_running === 'boolean') App.isControlRunning = msg.data.control_running;
      }
      toast(msg.data.message, msg.data.running || msg.data.paused ? 'ok' : 'warn');
      setRunningUI(msg.data.running, msg.data.paused ?? false);
      break;
    case 'error':  toast(msg.data.message, 'error'); setRunningUI(false, false); break;
    case 'pong':   break;
  }
}


function updateWSIndicator(connected) {
  $('ws-indicator').className = `ws-dot ${connected ? 'connected' : 'disconnected'}`;
}

// Add function to update ZMQ indicator
function updateZMQIndicator(connected) {
  const zmqIndicator = document.getElementById('zmq-indicator');
  if (zmqIndicator) {
    zmqIndicator.className = `ws-dot ${connected ? 'connected' : 'disconnected'}`;
  }
}