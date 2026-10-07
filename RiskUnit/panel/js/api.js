/* api.js — client of the Risk API (RiskUnit/api, /api/v1, api/openapi.yaml). Served by the server (http) the panel calls
   its own origin; opened as a file it shows how to start the server (RiskModel_Baslat.command / .bat) — every result
   already in the bundle stays visible. */
(function () {
  'use strict';
  var U = window.U;
  var A = U.API = { online: null, info: null, listeners: [] };
  A.PORT = 8791;
  A.base = function () {
    var u = U.ls('riskPanel.api');
    if (u) return u.replace(/\/+$/, '');
    if (/^https?:/.test(location.protocol)) return location.origin + '/api/v1';
    return 'http://127.0.0.1:' + A.PORT + '/api/v1';
  };
  A.token = function () { return U.ls('riskPanel.token') || 'demo-write'; };
  A.onChange = function (fn) { A.listeners.push(fn); };
  function set(on, info) {
    var ch = A.online !== on; A.online = on; A.info = info || A.info;
    if (ch) A.listeners.forEach(function (f) { try { f(on); } catch (e) { if (window.console) console.error(e); } });
  }
  A.fileMode = function () { return location.protocol === 'file:' && !U.ls('riskPanel.api'); };
  /* live request: server when reachable; otherwise the in-browser Python backend (pyweb.js) for the routes it supports */
  A.mode = function () { return U.PY ? U.PY.mode(A.online) : (A.online ? 'server' : 'paket'); };
  A.req = function (method, path, body, opt) {
    if (U.PY && A.online !== true && U.PY.supports(method, path)) {
      return (A.online === null ? A.ping() : Promise.resolve(false)).then(function (on) { return on ? A.net(method, path, body, opt) : A.viaPy(method, path, body); });
    }
    return A.net(method, path, body, opt);
  };
  A.viaPy = function (method, path, body) {
    return U.PY.req(method, path, body).then(function (r) { A.lastVia = 'brauzer'; if (r.status >= 400) throw A.err(r.body, r.status); return r.body; });
  };
  A.net = function (method, path, body, opt) {
    opt = opt || {}; A.lastVia = 'server';
    if (A.fileMode()) { set(false); return Promise.reject(new Error('Panel fayl kimi açılıb: canlı hesablama üçün serveri başladın (RiskModel_Baslat.command / .bat) və paneli http://127.0.0.1:' + A.PORT + '/panel/ ünvanında açın.')); }
    var h = { Authorization: 'Bearer ' + A.token() };
    if (body !== undefined) h['Content-Type'] = 'application/json';
    var ctl = window.AbortController ? new AbortController() : null, tm = setTimeout(function () { if (ctl) ctl.abort(); }, opt.timeout || 90000);
    return fetch(A.base() + path, { method: method, headers: h, body: body === undefined ? undefined : JSON.stringify(body), signal: ctl ? ctl.signal : undefined })
      .then(function (r) {
        clearTimeout(tm);
        if (opt.blob) return r.ok ? r.blob() : r.json().then(function (j) { throw A.err(j, r.status); });
        return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok) throw A.err(j, r.status); set(true); return j; });
      }, function (e) {
        clearTimeout(tm); set(false);
        throw new Error('Server əlçatan deyil (' + A.base() + '). ' + (e && e.name === 'AbortError' ? 'Cavab gecikdi.' : 'Serveri başladın: RiskModel_Baslat.command / .bat'));
      });
  };
  A.err = function (j, st) {
    var e = (j && j.error) || {}, m = e.message || ('Xəta ' + st);
    if (st === 401 || st === 403) m += ' — nişan (token) yanlışdır və ya yazı hüququ yoxdur. «Server ayarları»nda yoxlayın.';
    if (st === 409) m += ' — başqa yeniləmə artıq gedir.';
    var x = new Error(m); x.status = st; x.detail = e.detail; return x;
  };
  A.ping = function () {
    if (A.fileMode()) { set(false); return Promise.resolve(false); }
    return fetch(A.base() + '/health', { method: 'GET' }).then(function (r) { return r.json(); }).then(function (j) { set(true, j); return true; }, function () { set(false); return false; });
  };
  A.status = function () { return A.req('GET', '/status'); };
  A.stressInputs = function () { return A.req('GET', '/stress/inputs'); };
  /* analysis calls wait until the server's analysis cache is warm (status.analysis_ready.status === 'hazır') */
  A.whenReady = function (tries) {
    tries = tries == null ? 45 : tries;
    if (A.online !== true && U.PY && U.PY.able()) return (A.online === null ? A.ping() : Promise.resolve(false)).then(function (on) { return on ? A.whenReady(tries) : {}; });
    return A.status().then(function (s) {
      var st = ((s && s.analysis_ready) || {}).status;
      if (!st || st === 'hazır' || st === 'ready') return s;
      if (st === 'xəta' || st === 'error') throw new Error('Serverdə analiz keşi hazırlanmadı (xəta) — server jurnalına baxın.');
      if (tries <= 0) throw new Error('Analiz keşi hələ isinir — bir az sonra yenidən cəhd edin.');
      U.toast('Server analiz keşini hazırlayır (' + st + ')…');
      return new Promise(function (ok) { setTimeout(ok, 2000); }).then(function () { return A.whenReady(tries - 1); });
    });
  };
  A.stress = function (body) { return A.whenReady().then(function () { return A.req('POST', '/stress/run', body, { timeout: 120000 }); }); };
  A.scal = function (body) { return A.whenReady().then(function () { return A.req('POST', '/scalability/run', body, { timeout: 120000 }); }); };
  A.optimize = function (body) { return A.whenReady().then(function () { return A.req('POST', '/optimize/run', body, { timeout: 180000 }); }); };
  A.events = function (since) { return A.req('GET', '/events?since=' + (since || 0) + '&limit=50'); };
  A.saved = function (kind) { return A.req('GET', '/scenarios/saved' + (kind ? '?kind=' + kind : '')); };
  A.savedGet = function (id) { return A.req('GET', '/scenarios/saved/' + encodeURIComponent(id)); };
  A.save = function (body) { return A.req('POST', '/scenarios/saved', body); };
  A.del = function (id) { return A.req('DELETE', '/scenarios/saved/' + encodeURIComponent(id)); };
  A.rerun = function (id) { return A.req('POST', '/scenarios/saved/' + encodeURIComponent(id) + '/run', {}, { timeout: 180000 }); };
  A.refresh = function (mode) { return A.req('POST', '/refresh', { mode: mode || 'daily' }); };
  A.job = function (id) { return A.req('GET', '/refresh/' + encodeURIComponent(id) + '?tail=40'); };
  A.jobs = function () { return A.req('GET', '/refresh'); };
  A.reportXlsx = function (body) { return A.req('POST', '/reports/xlsx', body, { blob: true, timeout: 120000 }); };
  /* banner shown when a live feature is used without the server */
  /* error of a live call: server answered (HTTP status) → show its Azerbaijani message, not the launcher; else launcher */
  A.failHtml = function (what, e) {
    if (e && e.status) return '<div class="card pad offline" role="alert"><b>' + U.esc(what || 'Hesablama') + ' alınmadı.</b><p class="small" style="margin:6px 0">' + U.esc(e.message) + '</p>' +
      (e.status === 400 || e.status === 422 ? '<p class="small muted" style="margin:0">Girişləri dəyişib yenidən cəhd edin.</p>' : '') + '</div>';
    return A.offlineHtml(what) + '<p class="small muted">' + U.esc(e && e.message || '') + '</p>';
  };
  A.offlineHtml = function (what) {
    return '<div class="card pad offline" role="note"><b>' + U.esc(what || 'Canlı hesablama') + ' üçün yerli server lazımdır.</b>' +
      '<p class="small" style="margin:6px 0">Panel fayl kimi açılıb və ya server işləmir. Aşağıdakı bütün nəticələr (paketdəki son tam hesablama) indi də görünür; yalnız yeni hesablama aparıla bilmir.</p>' +
      '<ol class="small" style="margin:4px 0 8px;padding-left:18px"><li><b>RiskModel_Baslat.command</b> (macOS) və ya <b>RiskModel_Baslat.bat</b> (Windows) faylını <code>RiskUnit</code> qovluğunda iki dəfə klikləyin.</li>' +
      '<li>Brauzerdə <code>http://127.0.0.1:' + A.PORT + '/panel/</code> açılacaq. Və ya terminalda: <code>python3 api/server.py</code>.</li></ol>' +
      '<button type="button" class="btn sm" data-api="retry">Yenidən yoxla</button> <button type="button" class="btn sm ghost" data-api="set">Server ayarları</button></div>';
  };
  /* note shown instead of the launcher when the browser computes */
  A.browserHtml = function (what) {
    return '<div class="card pad" role="note" style="border-left:3px solid var(--accent, #0E6F7C)"><b>Server yoxdur — ' + U.esc(what || 'canlı hesablama') + ' bu brauzerdə Python ilə aparılır.</b>' +
      '<p class="small" style="margin:6px 0 0">API-nin çağırdığı eyni Python funksiyaları (MikroUnit zənciri + RU birgə Monte Karlo, eyni toxum) Pyodide ilə brauzerdə icra olunur; ilk dəfə ≈ ' + U.nf(U.PY.estMB(), 0) + ' MB yüklənir (sonra brauzer yaddaşından). Saxlama və hesabatların serverdə yaradılması yalnız serverlə mümkündür.</p></div>';
  };
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-api]'); if (!b) return;
    if (b.getAttribute('data-api') === 'set') A.openSettings();
    else { U.ls('riskPanel.api', U.ls('riskPanel.api') || null); A.ping().then(function (ok) { U.toast(ok ? 'Server əlçatandır' : 'Server əlçatan deyil'); if (ok) U.route(true); }); }
  });
  A.openSettings = function () {
    U.openModal('<h2 class="mh">Server ayarları</h2><p class="small muted">Standart: panel serverdən açılıbsa eyni ünvan; faylla açılıbsa http://127.0.0.1:' + A.PORT + '/api/v1 (server CORS-a icazə verməlidir). Nişan — serverin RISK_API_TOKENS dəyişənindəki yazı nişanı (sınaq: demo-write).</p>' +
      '<p class="small">Vəziyyət: <b>' + (A.online ? 'server əlçatandır' : 'server əlçatan deyil') + '</b>' + (A.info && A.info.version ? ' · versiya ' + U.esc(A.info.version) : '') + '</p>' +
      '<div class="form"><label>API ünvanı<input id="ap-url" value="' + U.esc(U.ls('riskPanel.api') || '') + '" placeholder="' + U.esc(A.base()) + '"></label>' +
      '<label>Nişan (token)<input id="ap-tok" type="password" value="' + U.esc(U.ls('riskPanel.token') || '') + '" placeholder="demo-write"></label></div>' +
      '<div class="toolbar"><button class="btn pri" id="ap-ok">Yadda saxla və yoxla</button><button class="btn" id="ap-x">Bağla</button></div>');
    U.$('#ap-x').onclick = function () { U.closeModal(); };
    U.$('#ap-ok').onclick = function () {
      U.ls('riskPanel.api', U.$('#ap-url').value.trim() || null); U.ls('riskPanel.token', U.$('#ap-tok').value.trim() || null);
      U.closeModal(); A.ping().then(function (ok) { U.toast(ok ? 'Server əlçatandır' : 'Server əlçatan deyil'); U.renderBar(); U.route(true); });
    };
  };
})();
