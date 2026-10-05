/* api.js — client of the local data API (api/server.py, /api/v1). Served from the server (http) the panel calls its
   own origin; opened as a file it tries http://127.0.0.1:8790 and otherwise explains how to start the server. */
(function () {
  'use strict';
  var U = window.U;
  var A = U.API = { online: null, info: null, listeners: [] };
  A.base = function () {
    var u = U.ls('mikroPanel.api');
    if (u) return u.replace(/\/+$/, '');
    if (/^https?:/.test(location.protocol)) return location.origin + '/api/v1';
    return 'http://127.0.0.1:8790/api/v1';
  };
  A.token = function () { return U.ls('mikroPanel.token') || 'demo-write'; };
  A.onChange = function (fn) { A.listeners.push(fn); };
  function set(on, info) {
    var ch = A.online !== on; A.online = on; A.info = info || A.info;
    if (ch) A.listeners.forEach(function (f) { try { f(on); } catch (e) { if (window.console) console.error(e); } });
  }
  A.req = function (method, path, body, opt) {
    opt = opt || {};
    if (location.protocol === 'file:' && !U.ls('mikroPanel.api')) { set(false); return Promise.reject(new Error('Panel fayl kimi açılıb: hesablama üçün serveri başladın (MikroModel_Baslat.command / .bat) və paneli http://127.0.0.1:8790/panel/ ünvanında açın.')); }
    var h = { Authorization: 'Bearer ' + A.token() };
    if (body !== undefined) h['Content-Type'] = 'application/json';
    var ctl = window.AbortController ? new AbortController() : null, tm = setTimeout(function () { if (ctl) ctl.abort(); }, opt.timeout || 60000);
    return fetch(A.base() + path, { method: method, headers: h, body: body === undefined ? undefined : JSON.stringify(body), signal: ctl ? ctl.signal : undefined })
      .then(function (r) {
        clearTimeout(tm);
        if (opt.blob) return r.ok ? r.blob() : r.json().then(function (j) { throw A.err(j, r.status); });
        return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok) throw A.err(j, r.status); set(true); return j; });
      }, function (e) {
        clearTimeout(tm); set(false);
        throw new Error('Server əlçatan deyil (' + A.base() + '). ' + (e && e.name === 'AbortError' ? 'Cavab gecikdi.' : 'Serveri başladın: MikroModel_Baslat.command / .bat'));
      });
  };
  A.err = function (j, st) {
    var e = (j && j.error) || {};
    var m = e.message || ('Xəta ' + st);
    if (st === 401 || st === 403) m += ' — nişan (token) yanlışdır və ya yazı hüququ yoxdur. «Server ayarları»nda yoxlayın.';
    var x = new Error(m); x.status = st; x.detail = e.detail; return x;
  };
  A.ping = function () {
    if (location.protocol === 'file:' && !U.ls('mikroPanel.api')) { set(false); return Promise.resolve(false); }   // file:// pages cannot call the API (CORS)
    return fetch(A.base() + '/health', { method: 'GET' }).then(function (r) { return r.json(); }).then(function (j) { set(true, j); return true; }, function () { set(false); return false; });
  };
  A.inputs = function (m) { return A.req('GET', '/scenarios/inputs?module=' + m); };
  A.run = function (body) { return A.req('POST', '/scenarios/run', body, { timeout: 120000 }); };
  A.saved = function () { return A.req('GET', '/scenarios/saved'); };
  A.savedGet = function (id) { return A.req('GET', '/scenarios/saved/' + encodeURIComponent(id)); };
  A.save = function (body) { return A.req('POST', '/scenarios/saved', body); };
  A.del = function (id) { return A.req('DELETE', '/scenarios/saved/' + encodeURIComponent(id)); };
  A.status = function () { return A.req('GET', '/status'); };
  /* banner shown when the server is not reachable */
  A.offlineHtml = function () {
    return '<div class="card pad offline" role="note"><b>Ssenarini hesablamaq üçün yerli server lazımdır.</b>' +
      '<p class="small" style="margin:6px 0">Panel fayl kimi açılıb və ya server işləmir. Hesablama (zəncirvari ssenari), saxlama və silmə yalnız server işləyəndə mümkündür; aşağıdakı saxlanmış ssenarilərin nəticələrinə isə indi də baxa bilərsiniz.</p>' +
      '<ol class="small" style="margin:4px 0 8px;padding-left:18px"><li><b>MikroModel_Baslat.command</b> (macOS) və ya <b>MikroModel_Baslat.bat</b> (Windows) faylını <code>MicroUnit</code> qovluğunda iki dəfə klikləyin.</li>' +
      '<li>Brauzerdə <code>http://127.0.0.1:8790/panel/</code> açılacaq. Və ya terminalda: <code>python3 api/server.py</code>.</li></ol>' +
      '<button type="button" class="btn sm" id="api-retry">Yenidən yoxla</button> <button type="button" class="btn sm ghost" id="api-set">Server ayarları</button></div>';
  };
  A.settingsHtml = function () {
    return '<h2 class="mh">Server ayarları</h2><p class="small muted">Standart: panel serverdən açılıbsa eyni ünvan; faylla açılıbsa http://127.0.0.1:8790/api/v1. Nişan — serverin API_TOKENS dəyişənindəki yazı nişanı (sınaq: demo-write).</p>' +
      '<div class="form"><label>API ünvanı<input id="ap-url" value="' + U.esc(U.ls('mikroPanel.api') || '') + '" placeholder="' + U.esc(A.base()) + '"></label>' +
      '<label>Nişan (token)<input id="ap-tok" type="password" value="' + U.esc(U.ls('mikroPanel.token') || '') + '" placeholder="demo-write"></label>' +
      '<label>Müəllif (saxlanmış ssenarilər üçün)<input id="ap-au" value="' + U.esc(U.ls('mikroPanel.author') || '') + '"></label></div>' +
      '<div class="toolbar"><button class="btn pri" id="ap-ok">Yadda saxla</button><button class="btn" id="ap-x">Bağla</button></div>';
  };
  A.openSettings = function () {
    U.openModal(A.settingsHtml());
    U.$('#ap-x').onclick = function () { U.closeModal(); };
    U.$('#ap-ok').onclick = function () {
      U.ls('mikroPanel.api', U.$('#ap-url').value.trim() || null); U.ls('mikroPanel.token', U.$('#ap-tok').value.trim() || null); U.ls('mikroPanel.author', U.$('#ap-au').value.trim() || null);
      U.closeModal(); A.ping().then(function (ok) { U.toast(ok ? 'Server əlçatandır' : 'Server əlçatan deyil'); U.route(true); });
    };
  };
})();
