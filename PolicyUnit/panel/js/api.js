/* api.js — client of the PolicyUnit API (PolicyUnit/api, /api/v1, api/openapi.yaml; copied from the Risk paneli). Served by
   the server (http) the panel calls its own origin; opened as a file it shows how to start the server
   (SiyasetModel_Baslat.command / .bat) — every result already in the bundle stays visible. */
(function () {
  'use strict';
  var U = window.U;
  var A = U.API = { online: null, info: null, listeners: [] };
  A.PORT = 8792;
  A.base = function () {
    var u = U.ls('policyPanel.api');
    if (u) return u.replace(/\/+$/, '');
    if (/^https?:/.test(location.protocol)) return location.origin + '/api/v1';
    return 'http://127.0.0.1:' + A.PORT + '/api/v1';
  };
  A.token = function () { return U.ls('policyPanel.token') || 'demo-write'; };
  A.onChange = function (fn) { A.listeners.push(fn); };
  function set(on, info) {
    var ch = A.online !== on; A.online = on; A.info = info || A.info;
    if (ch) A.listeners.forEach(function (f) { try { f(on); } catch (e) { if (window.console) console.error(e); } });
  }
  A.fileMode = function () { return location.protocol === 'file:' && !U.ls('policyPanel.api'); };
  /* live request: server when reachable; otherwise the in-browser Python backend (pyweb.js) for the routes it supports */
  A.mode = function () { return U.PY ? U.PY.mode(A.online) : (A.online ? 'server' : 'paket'); };
  A.live = function () { return A.mode() !== 'paket'; };
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
    if (A.fileMode()) { set(false); return Promise.reject(new Error('Panel fayl kimi açılıb: canlı hesablama üçün serveri başladın (SiyasetModel_Baslat.command / .bat) və paneli http://127.0.0.1:' + A.PORT + '/panel/ ünvanında açın.')); }
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
        throw new Error('Server əlçatan deyil (' + A.base() + '). ' + (e && e.name === 'AbortError' ? 'Cavab gecikdi.' : 'Serveri başladın: SiyasetModel_Baslat.command / .bat'));
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
    return fetch(A.base() + '/health', { method: 'GET' }).then(function (r) { return r.json(); }).then(function (j) { set(true, j); A.syncInstruments(); return true; }, function () { set(false); return false; });
  };
  /* NFR4: instruments added on the server (POST instruments/new) join the bundled catalogue, so the builder can use them */
  var SYNCED = false;
  A.syncInstruments = function () {
    if (SYNCED || A.fileMode()) return Promise.resolve(0);
    SYNCED = true;
    return A.instruments().then(function (j) {
      var cat = U.T('cfg_instruments'), have = {}, n = 0;
      cat.forEach(function (r) { have[r.id] = 1; });
      ((j && j.instruments) || []).forEach(function (r) {
        if (!r || !r.id || have[r.id]) return;
        cat.push({ id: r.id, name_az: r.name_az, family: r.family, unit: r.unit, default_size: r.default_size, min: r.min, max: r.max,
          engines: [].concat(r.engines || []).join(';'), description_az: r.description_az || '', cost_rule: r.cost_rule, cost_in_fr1: r.cost_in_fr1 });
        n++;
      });
      if (n && /^#\/qurucu/.test(location.hash)) U.route(true);
      return n;
    }, function () { SYNCED = false; return 0; });
  };
  A.status = function () { return A.req('GET', '/status'); };
  A.instruments = function () { return A.req('GET', '/instruments'); };
  A.schema = function () { return A.req('GET', '/scenarios/schema'); };
  A.list = function (src) { return A.req('GET', '/scenarios?source=' + (src || 'all')); };
  A.get = function (id) { return A.req('GET', '/scenarios/' + encodeURIComponent(id)); };
  A.validate = function (sc) { return A.req('POST', '/scenarios/validate', sc); };
  A.save = function (sc, official) { return A.req('POST', '/scenarios' + (official ? '?store=official' : ''), sc); };
  A.update = function (sc) { return A.req('PUT', '/scenarios/' + encodeURIComponent(sc.id), sc); };
  A.dup = function (id, body) { return A.req('POST', '/scenarios/' + encodeURIComponent(id) + '/duplicate', body || {}); };
  A.del = function (id) { return A.req('DELETE', '/scenarios/' + encodeURIComponent(id)); };
  A.promote = function (id) { return A.req('POST', '/scenarios/' + encodeURIComponent(id) + '/promote', {}); };
  /* run a saved scenario (or an unsaved one: {scenario}); follows a 202 by polling /runs/{id}; onProg(progress) */
  A.run = function (id, body, onProg) {
    var p = id ? A.req('POST', '/scenarios/' + encodeURIComponent(id) + '/run', body || {}, { timeout: 180000 }) : A.req('POST', '/runs', body, { timeout: 180000 });
    return p.then(function (j) { return j && j.run_id && !j.headline && j.status !== 'ok' ? A.poll(j.run_id, onProg) : j; });
  };
  A.poll = function (rid, onProg, n) {
    n = n == null ? 240 : n;
    return A.req('GET', '/runs/' + encodeURIComponent(rid)).then(function (j) {
      if (onProg && j.progress) onProg(j.progress, j);
      if (j.result) return j.result;
      if (j.status === 'failed' || j.status === 'xəta' || j.error) throw new Error((j.error && (j.error.message || j.error)) || j.status_az || 'Hesablama alınmadı');
      if (j.status === 'cancelled') throw new Error('Hesablama ləğv edildi');
      if (n <= 0) throw new Error('Hesablama çox uzun çəkdi — «Hesablamalar» siyahısından yoxlayın.');
      return new Promise(function (ok) { setTimeout(ok, 1500); }).then(function () { return A.poll(rid, onProg, n - 1); });
    });
  };
  A.cancel = function (rid) { return A.req('POST', '/runs/' + encodeURIComponent(rid) + '/cancel', {}); };
  A.compare = function (body) { return A.req('POST', '/compare', body, { timeout: 180000 }); };
  A.kpiSets = function () { return A.req('GET', '/kpi/sets'); };
  A.kpiSave = function (body) { return A.req('POST', '/kpi/sets', body); };
  A.events = function (since) { return A.req('GET', '/events?since=' + (since || 0) + '&limit=50'); };
  A.refresh = function (body) { return A.req('POST', '/refresh', body || {}); };
  A.job = function (id) { return A.req('GET', '/refresh/' + encodeURIComponent(id) + '?tail=40'); };
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
      '<p class="small" style="margin:6px 0">Panel fayl kimi açılıb və ya server işləmir. Paketdəki bütün nəticələr (son tam hesablama və nümunə ssenarilər) indi də görünür; yalnız yeni ssenari yoxlanıla, saxlanıla və hesablana bilmir.</p>' +
      '<ol class="small" style="margin:4px 0 8px;padding-left:18px"><li><b>SiyasetModel_Baslat.command</b> (macOS) və ya <b>SiyasetModel_Baslat.bat</b> (Windows) faylını <code>PolicyUnit</code> qovluğunda iki dəfə klikləyin.</li>' +
      '<li>Brauzerdə <code>http://127.0.0.1:' + A.PORT + '/panel/</code> açılacaq. Və ya terminalda: <code>python3 api/server.py</code>.</li></ol>' +
      '<button type="button" class="btn sm" data-api="retry">Yenidən yoxla</button> <button type="button" class="btn sm ghost" data-api="set">Server ayarları</button></div>';
  };
  /* note shown instead of the launcher when the browser computes */
  A.browserHtml = function (what) {
    return '<div class="card pad" role="note" style="border-left:3px solid var(--accent, #0E6F7C)"><b>Server yoxdur — ' + U.esc(what || 'canlı hesablama') + ' bu brauzerdə Python ilə aparılır.</b>' +
      '<p class="small" style="margin:6px 0 0">API-nin çağırdığı eyni Python funksiyaları (mühərriklər: MikroUnit, CAEM, I-O, mikrosimulyasiya, uzunmüddətli) Pyodide ilə brauzerdə icra olunur; ilk dəfə ≈ ' + U.nf(U.PY.estMB(), 0) + ' MB yüklənir (sonra brauzer yaddaşından). OxLon və RiskUnit FX mühərrikləri yalnız serverlə; yan təsirlər qaydalarla, risk profili PolicyUnit sürüşməsi ilə (əsas mənbə qaydası b). Saxlama bu brauzerdə aparılır.</p></div>';
  };
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-api]'); if (!b) return;
    if (b.getAttribute('data-api') === 'set') A.openSettings();
    else { U.ls('policyPanel.api', U.ls('policyPanel.api') || null); A.ping().then(function (ok) { U.toast(ok ? 'Server əlçatandır' : 'Server əlçatan deyil'); if (ok) U.route(true); }); }
  });
  A.openSettings = function () {
    U.openModal('<h2 class="mh">Server ayarları</h2><p class="small muted">Standart: panel serverdən açılıbsa eyni ünvan; faylla açılıbsa http://127.0.0.1:' + A.PORT + '/api/v1 (server CORS-a icazə verməlidir). Nişan — serverin POLICY_API_TOKENS dəyişənindəki nişan (sınaq: yazmaq üçün demo-write, yalnız oxumaq üçün demo-read).</p>' +
      '<p class="small">Vəziyyət: <b>' + (A.online ? 'server əlçatandır' : 'server əlçatan deyil') + '</b>' + (A.info && A.info.version ? ' · versiya ' + U.esc(A.info.version) : '') + '</p>' +
      '<div class="form"><label>API ünvanı<input id="ap-url" value="' + U.esc(U.ls('policyPanel.api') || '') + '" placeholder="' + U.esc(A.base()) + '"></label>' +
      '<label>Nişan (token)<input id="ap-tok" type="password" value="' + U.esc(U.ls('policyPanel.token') || '') + '" placeholder="demo-write"></label></div>' +
      '<div class="toolbar"><button class="btn pri" id="ap-ok">Yadda saxla və yoxla</button><button class="btn" id="ap-x">Bağla</button></div>');
    U.$('#ap-x').onclick = function () { U.closeModal(); };
    U.$('#ap-ok').onclick = function () {
      U.ls('policyPanel.api', U.$('#ap-url').value.trim() || null); U.ls('policyPanel.token', U.$('#ap-tok').value.trim() || null);
      U.closeModal(); A.ping().then(function (ok) { U.toast(ok ? 'Server əlçatandır' : 'Server əlçatan deyil'); U.renderBar(); U.route(true); });
    };
  };
})();
