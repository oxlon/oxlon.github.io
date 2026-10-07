/* pyweb.js — third backend «Brauzerdə hesabla (Python brauzerdə)», identical in the three panels. When the local API
   is not reachable (e.g. GitHub Pages), api.js sends the supported live requests here: the SAME Python functions run
   in the browser (Pyodide in a Web Worker, js/pyworker.js + panel/py/<unit>_bundle.zip, see py/bundle.js → window.PYB).
   U.PY: able(), supports(method, path), ensure(), req(method, path, body) → {status, body, seconds}; loading card
   (one-time download, then cached by the browser); U.PY.mode(online) → 'server' | 'brauzer' | 'paket'. */
(function () {
  'use strict';
  var U = window.U, M = window.PYB, OFF = 'miis.py.off';
  var EST = { core: 12.6, numpy: 3.1, pandas: 5.3, scipy: 15.4, statsmodels: 8.7, sqlite3: 0.6 };
  var P = U.PY = { state: M ? 'idle' : 'none', err: null, loadS: null, bytes: 0, runS: null, listeners: [] };
  function fire() { P.listeners.forEach(function (f) { try { f(P.state); } catch (e) { if (window.console) console.error(e); } }); }
  P.onChange = function (f) { P.listeners.push(f); };
  P.able = function () {
    var off = false; try { off = !!U.ls(OFF); } catch (e) { off = false; }
    return !!(M && /^https?:/.test(location.protocol) && window.Worker && window.WebAssembly && P.state !== 'failed' && !off);
  };
  P.supports = function (method, path) {
    path = String(path).replace(/^\/+/, '').split('?')[0];
    return P.able() && M.routes.some(function (r) { return r[0] === method && new RegExp(r[1]).test(path); });
  };
  P.mode = function (online) { return online ? 'server' : P.able() ? 'brauzer' : 'paket'; };
  P.label = function (online) { return { server: 'Server: canlı', brauzer: 'Brauzer: Python', paket: 'Yalnız paket' }[P.mode(online)]; };
  P.title = function (online) {
    return { server: 'Yerli server əlçatandır — hesablamalar serverdə aparılır',
      brauzer: 'Server yoxdur — canlı hesablamalar bu brauzerdə Python ilə (Pyodide) aparılır; ilk dəfə ' + U.nf(P.estMB(), 0) + ' MB-a qədər yüklənir, sonra brauzer yaddaşından',
      paket: 'Server yoxdur və brauzerdə hesablama mümkün deyil (panel fayl kimi açılıb və ya yüklənmə alınmadı) — paketdəki nəticələr göstərilir' }[P.mode(online)];
  };
  P.estMB = function () {
    if (!M) return 0;
    var t = EST.core + M.bytes / 1e6;
    M.packages.forEach(function (p) { t += EST[p] || 0.5; });
    return t;
  };
  function mb(b) { return U.nf(b / 1e6, 1); }
  function css() {
    if (document.getElementById('py-css')) return;
    var s = document.createElement('style'); s.id = 'py-css';
    s.textContent = '#py-card{right:16px;bottom:16px;z-index:9999;width:min(360px,calc(100vw - 32px));background:var(--surface,#fff);color:var(--ink,#111);border:1px solid var(--line,#ddd);border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.14);padding:12px 14px;font-size:13px}' +
      '#py-card b{display:block;margin-bottom:4px}#py-card .pyb{height:6px;border-radius:3px;background:var(--line,#e5e5e5);margin:8px 0 4px;overflow:hidden}#py-card .pyb i{display:block;height:100%;width:0;background:var(--accent,#2563eb);transition:width .3s}' +
      '.srv.py i{background:var(--accent,#0E6F7C)}.srv.py{color:var(--accent,#0E6F7C)}' +
      '#py-card .pys{color:var(--muted,#666);font-size:12px}#py-card button{float:right;border:0;background:transparent;cursor:pointer;font-size:16px;line-height:1;color:var(--muted,#666)}';
    document.head.appendChild(s);
  }
  function card(title, text, frac, hide) {
    css();
    var c = document.getElementById('py-card');
    if (!c) { c = document.createElement('div'); c.id = 'py-card'; c.style.position = 'fixed'; c.setAttribute('role', 'status'); c.setAttribute('aria-live', 'polite'); document.body.appendChild(c); }
    c.hidden = false;
    c.innerHTML = '<button type="button" aria-label="Bağla" onclick="this.parentNode.hidden=true">×</button><b>' + U.esc(title) + '</b><div class="pys">' + U.esc(text) + '</div>' +
      (frac == null ? '' : '<div class="pyb"><i style="width:' + Math.round(Math.min(1, Math.max(0.02, frac)) * 100) + '%"></i></div>');
    clearTimeout(card.t);
    if (hide) card.t = setTimeout(function () { c.hidden = true; }, hide);
  }
  if (M) css();
  var W = null, seq = 0, pend = {}, ready = null, stageTxt = '';
  function loading() {
    var est = P.estMB();
    card('Python mühiti hazırlanır (bir dəfəlik)', stageTxt + ' · yükləndi ' + mb(P.bytes) + ' / ≈ ' + U.nf(est, 0) + ' MB. Sonrakı açılışlarda brauzer yaddaşından götürülür.', P.bytes / (est * 1e6));
  }
  function fail(msg) {
    P.state = 'failed'; P.err = msg; ready = null;
    if (W) { try { W.terminate(); } catch (e) { /* ignore */ } W = null; }
    Object.keys(pend).forEach(function (k) { pend[k].no(new Error(msg)); delete pend[k]; });
    card('Brauzerdə hesablama alınmadı', msg + ' — panel paketdəki nəticələri göstərir (yalnız paket rejimi).', null, 12000);
    fire();
  }
  P.ensure = function () {
    if (ready) return ready;
    if (!P.able()) return Promise.reject(new Error('Brauzerdə hesablama bu açılışda mümkün deyil (panel http(s) ünvanından açılmalıdır).'));
    P.state = 'loading'; stageTxt = 'başlanır'; loading(); fire();
    var t0 = Date.now();
    ready = new Promise(function (ok, no) {
      try { W = new Worker('js/pyworker.js'); } catch (e) { no(e); return; }
      pend[0] = { ok: ok, no: no };
      W.onmessage = function (ev) {
        var m = ev.data, p = pend[m.id];
        if (m.type === 'bytes' || m.type === 'stage') { P.bytes = m.bytes; if (m.text) stageTxt = m.text; if (P.state === 'loading') loading(); return; }
        if (m.type === 'ready') {
          P.state = 'ready'; P.loadS = (Date.now() - t0) / 1000; P.bytes = m.bytes;
          card('Python mühiti hazırdır', 'Yükləmə ' + U.nf(P.loadS, 1) + ' san., ' + mb(P.bytes) + ' MB (sıxılmış). Hesablamalar bu brauzerdə aparılır.', 1, 5000);
          fire();
        }
        if (!p) return;
        delete pend[m.id];
        if (m.type === 'err') { if (m.id === 0) { pend[0] = p; fail('Python mühiti yüklənmədi: ' + m.message); } else p.no(new Error('Brauzerdə hesablama xətası: ' + m.message)); return; }
        p.ok(m);
      };
      W.onerror = function (e) { fail('Python mühiti yüklənmədi: ' + ((e && e.message) || 'naməlum xəta')); };
      var meta = {}; Object.keys(M).forEach(function (k) { meta[k] = M[k]; });
      meta.zipUrl = new URL(M.zip + '?v=' + M.md5.slice(0, 12), location.href).href;
      W.postMessage({ cmd: 'init', id: 0, meta: meta });
    });
    return ready;
  };
  P.req = function (method, path, body) {
    path = String(path).replace(/^\/+/, '').split('?')[0];
    return P.ensure().then(function () {
      return new Promise(function (ok, no) { var id = ++seq; pend[id] = { ok: ok, no: no }; W.postMessage({ cmd: 'req', id: id, method: method, path: path, body: body }); });
    }).then(function (m) {
      var j = JSON.parse(m.json); P.runS = m.seconds;
      U.toast('Brauzerdə hesablandı: ' + U.nf(m.seconds, 1) + ' san. (Python, Pyodide)');
      return { status: j.status, body: j.body, seconds: m.seconds };
    });
  };
})();
