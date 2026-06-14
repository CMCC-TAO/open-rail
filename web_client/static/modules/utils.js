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
  if (externalSignal) {
    if (externalSignal.aborted) {
      signal.__manualAbort = externalSignal.__manualAbort || false;
      controller.abort();
    } else {
      externalSignal.addEventListener('abort', () => {
        signal.__manualAbort = externalSignal.__manualAbort || false;
        controller.abort();
      }, { once: true });
    }
  }

  const timer = setTimeout(() => controller.abort(), Math.max(1000, Number(timeoutMs) || 3000));

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
        console.warn('[apiFetch] failed to parse JSON', { url, parseErr });
      }
    }

    if (!res.ok) {
      const errorMessage = json && (json.detail || json.message) ? (json.detail || json.message) : `${res.status} ${res.statusText}`;
      console.error('[apiFetch] request failed', { url, status: res.status, statusText: res.statusText, elapsedMs: elapsed.toFixed(1), body: json });
      throw new Error(errorMessage);
    }

    const responseLog = { url, status: res.status, statusText: res.statusText, elapsedMs: elapsed.toFixed(1), body: json };
    console.debug('[apiFetch] request success', responseLog);
    return json !== null ? json : { status: res.status, statusText: res.statusText };
  } catch (e) {
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
  }
}

async function sendControl(action, payload = {}) {
  try {
    await apiFetch(`/api/client/control/${action}`, { method: 'POST', body: JSON.stringify(payload || {}) });
  } catch (e) { /* toasted */ }
}

async function sendLanguageSet(language = '') {
  try {
    await apiFetch('/api/client/language/set', { method: 'POST', body: JSON.stringify({ language }) });
  } catch (e) { /* toasted */ }
}
