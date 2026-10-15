// ═══════════════════════════════════════════════════════
//  DOM helpers
// ═══════════════════════════════════════════════════════
const $ = id => document.getElementById(id);

function toast(msg, type = 'info', duration = 3500) {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  $('toast-container').appendChild(el);
  setTimeout(() => {
    el.style.animation = 'fadeOut .2s forwards';
    el.addEventListener('animationend', () => el.remove());
  }, duration);
}

function abortCurrentFetchRequest() {
  if (App.currentFetchController) {
    try {
      if (App.currentFetchController.signal) {
        App.currentFetchController.signal.__manualAbort = true;
      }
      App.currentFetchController.abort();
    } catch (_) {
      // ignore abort errors
    }
    App.currentFetchController = null;
  }
}

function beginFetchRequest() {
  abortCurrentFetchRequest();
  const controller = new AbortController();
  controller.signal.__manualAbort = false;
  App.currentFetchController = controller;
  return controller;
}

async function apiFetch(url, opts = {}) {
  const { timeoutMs = 3000, expectJson = true, suppressToast = false, suppressAbortToast = false, signal: externalSignal = null, ...fetchOpts } = opts || {};
  const startTime = performance.now();

  // Always wrap an external AbortSignal in a local controller so timeouts still apply.
  const controller = new AbortController();
  const signal = controller.signal;
  const forwardAbort = () => {
    signal.__manualAbort = externalSignal.__manualAbort || false;
    controller.abort(externalSignal.reason);
  };
  if (externalSignal) {
    if (externalSignal.aborted) {
      forwardAbort();
    } else {
      externalSignal.addEventListener('abort', forwardAbort, { once: true });
    }
  }

  const requestTimeoutMs = Math.max(1000, Number(timeoutMs) || 3000);
  let timedOut = false;
  const timer = setTimeout(() => {
    if (signal.aborted) return;
    timedOut = true;
    controller.abort(new DOMException(`Request timed out after ${requestTimeoutMs / 1000}s: ${url}`, 'TimeoutError'));
  }, requestTimeoutMs);

  try {
    const res = await fetch(url, {
      headers: fetchOpts.headers || { 'Content-Type': 'application/json' },
      signal,
      ...fetchOpts,
    });

    const elapsed = performance.now() - startTime;
    const contentType = String(res.headers.get('content-type') || '').toLowerCase();
    let json = null;
    if (expectJson && contentType.includes('application/json')) {
      try {
        json = await res.json();
      } catch (parseErr) {
        if (signal.aborted) throw signal.reason;
        console.warn('[apiFetch] failed to parse JSON', { url, parseErr });
      }
    }

    if (!res.ok) {
      const errorMessage = json && (json.detail || json.message) ? (json.detail || json.message) : `${res.status} ${res.statusText}`;
      console.error('[apiFetch] request failed', { url, status: res.status, statusText: res.statusText, elapsedMs: elapsed.toFixed(1), body: json });
      const error = new Error(errorMessage);
      error.status = res.status;
      throw error;
    }

    const responseLog = { url, status: res.status, statusText: res.statusText, elapsedMs: elapsed.toFixed(1), body: json };
    console.debug('[apiFetch] request success', responseLog);
    return json !== null ? json : { status: res.status, statusText: res.statusText };
  } catch (e) {
    if (timedOut) e = signal.reason;
    const elapsed = performance.now() - startTime;
    const abortWasManual = signal && signal.__manualAbort;
    const errLog = { url, elapsedMs: elapsed.toFixed(1), error: e && e.message ? e.message : e, abortWasManual };
    console.error('[apiFetch] request error', errLog);
    if (e && e.name === 'AbortError') {
      if (!suppressToast && !abortWasManual && !suppressAbortToast) {
        toast(`Request aborted: ${url}`, 'error');
      }
    } else if (!suppressToast) {
      toast(e && e.message ? e.message : String(e), 'error');
    }
    throw e;
  } finally {
    if (timer) clearTimeout(timer);
    if (externalSignal) externalSignal.removeEventListener('abort', forwardAbort);
  }
}

async function sendControl(action, payload = {}) {
  try {
    const timeoutMs = action === 'arm' || action === 'reset' ? 30000 : 3000;
    await apiFetch(`/api/client/control/${action}`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
      timeoutMs,
    });
    return true;
  } catch (e) {
    return false;
  }
}
