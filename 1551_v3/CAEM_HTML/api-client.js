/* Məlumat mübadiləsi — Nazirliyin məlumat anbarı ilə API üzərindən əlaqə.
   Anbardan gələn yeni faktiki məlumatı modelə gətirir və modelin proqnozunu geri göndərir.
   Model-spesifik hər şey init(cfg) ilə ötürülür; modul hər iki paneldə eynidir. */
(function (root) {
  'use strict';
  var CFG = null, ST = null, PULL = null, BUSY = false;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function isNum(v) { return typeof v === 'number' && isFinite(v); }
  function nf(v, d) { return CFG.nf ? CFG.nf(v, d) : (isNum(v) ? v.toFixed(d == null ? 4 : d) : '—'); }

  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { } }
  function load() {
    var d = { url: '', token: '', actor: '', auto: 0, lastSeq: 0, lastSync: '' };
    try { var o = JSON.parse(lsGet(CFG.ns + '.api') || 'null'); if (o) for (var k in d) if (o[k] !== undefined) d[k] = o[k]; } catch (e) { }
    return d;
  }
  function save() { lsSet(CFG.ns + '.api', JSON.stringify(ST)); }

  /* ------------------------------------------------------------------ http */
  function api(path, opts) {
    opts = opts || {};
    var base = String(ST.url || '').replace(/\/+$/, '');
    if (!base) return Promise.reject(new Error('API ünvanı təyin edilməyib'));
    var h = { 'Accept': 'application/json' };
    if (ST.token) h['Authorization'] = 'Bearer ' + ST.token;
    if (opts.body) h['Content-Type'] = 'application/json';
    return fetch(base + path, { method: opts.method || 'GET', headers: h, body: opts.body ? JSON.stringify(opts.body) : undefined })
      .then(function (r) {
        return r.text().then(function (t) {
          var j = null; try { j = t ? JSON.parse(t) : null; } catch (e) { }
          if (!r.ok) {
            var m = (j && j.error && j.error.message) || ('HTTP ' + r.status);
            var e2 = new Error(m); e2.status = r.status; throw e2;
          }
          return j;
        });
      });
  }

  /* -------------------------------------------------------- pull from store */
  function pull() {
    if (BUSY) return; BUSY = true; render();
    var Y = CFG.years();
    api('/v1/observations?model=' + encodeURIComponent(CFG.model) + '&limit=50000')
      .then(function (d) {
        var items = (d && d.items) || [], rows = [], skipped = 0;
        items.forEach(function (it) {
          var id = CFG.resolve(it.code, it.period);
          if (id == null || id < 0) { skipped++; return; }
          var cur = CFG.value(id);
          if (!isNum(it.value)) return;
          if (isNum(cur) && Math.abs(cur - it.value) <= Math.max(1e-9, Math.abs(cur) * 1e-12)) return;
          rows.push({ id: id, code: it.code, period: it.period, from: isNum(cur) ? cur : null, to: it.value,
                      source: it.source || '', actor: it.actor || '', forecast: it.period > Y.lastActual });
        });
        rows.sort(function (a, b) { return a.code === b.code ? a.period - b.period : (a.code < b.code ? -1 : 1); });
        PULL = { at: new Date(), rows: rows, total: items.length, skipped: skipped, maxSeq: d.max_seq || 0, pick: {} };
        // Data entered in the warehouse is authoritative, so everything is pre-selected; rows that land
        // inside the model's forecast range are flagged so nobody overwrites a projection unknowingly.
        rows.forEach(function (r, i) { PULL.pick[i] = 1; });
        BUSY = false; render();
        CFG.toast(rows.length ? rows.length + ' fərqli nöqtə tapıldı' : 'Model anbarla eynidir — fərq yoxdur');
      })
      .catch(function (e) { BUSY = false; PULL = null; render(); CFG.toast('Anbardan oxunmadı: ' + e.message); });
  }
  function applyPull() {
    if (!PULL) return;
    var n = 0;
    PULL.rows.forEach(function (r, i) { if (PULL.pick[i]) { CFG.setCell(r.id, r.to, true); n++; } });
    if (!n) { CFG.toast('Heç bir sətir seçilməyib'); return; }
    ST.lastSeq = PULL.maxSeq; ST.lastSync = new Date().toISOString(); save();
    CFG.changed();
    PULL = null; render();
    CFG.toast(n + ' nöqtə modelə tətbiq olundu');
  }

  /* ---------------------------------------------------------- push forecast */
  function push() {
    if (BUSY) return;
    var name = prompt('Proqnoz versiyasının adı:', new Date().toISOString().slice(0, 10) + '-' + CFG.model);
    if (!name) return;
    var Y = CFG.years(), items = [];
    CFG.outputs().forEach(function (o) {
      for (var y = Y.lastActual + 1; y <= Y.last; y++) {
        var id = o.resolve(y); if (id == null || id < 0) continue;
        var v = CFG.value(id); if (!isNum(v)) continue;
        items.push({ model: CFG.model, code: o.code, period: y, value: v, label: o.label || '', unit: o.unit || '' });
      }
    });
    if (!items.length) { CFG.toast('Göndəriləcək nöqtə tapılmadı'); return; }
    BUSY = true; render();
    api('/v1/forecasts', { method: 'POST', body: { vintage: name, model: CFG.model, actor: ST.actor || 'panel', items: items } })
      .then(function (d) { BUSY = false; render(); CFG.toast('Dərc olundu: ' + d.vintage + ' · ' + d.points + ' nöqtə'); })
      .catch(function (e) { BUSY = false; render(); CFG.toast('Göndərilmədi: ' + e.message); });
  }

  function test() {
    if (BUSY) return; BUSY = true; render();
    api('/v1/health').then(function (d) {
      BUSY = false;
      ST.health = { ok: true, at: new Date().toISOString(), series: d.series, obs: d.observations, version: d.version };
      save(); render(); CFG.toast('Əlaqə var: ' + d.series + ' sıra, ' + d.observations + ' nöqtə');
    }).catch(function (e) {
      BUSY = false; ST.health = { ok: false, at: new Date().toISOString(), message: e.message };
      save(); render(); CFG.toast('Əlaqə yoxdur: ' + e.message);
    });
  }

  /* ----------------------------------------------------------------- render */
  var SHEET = [
    '.ap-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin:10px 0}',
    '.ap-f{display:flex;flex-direction:column;gap:4px}',
    '.ap-f label{font-size:12px;font-weight:600;color:var(--muted,#71808D)}',
    '.ap-f input{font:inherit;font-size:13px;padding:7px 9px;border:1px solid var(--line,#E7EBEF);border-radius:7px;background:var(--surface,#fff);color:inherit;width:100%}',
    '.ap-act{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:8px}',
    '.ap-st{font-size:12.5px;padding:7px 10px;border-radius:7px;border:1px solid var(--line,#E7EBEF);margin-top:8px}',
    '.ap-st.ok{border-color:#9FC4A8;background:#F1F8F3;color:#2F6B3D}',
    '.ap-st.bad{border-color:#E0A6A0;background:#FCF1F0;color:#A3352A}',
    '.ap-tw{max-height:360px;overflow:auto;border:1px solid var(--line,#E7EBEF);border-radius:8px;margin-top:10px}',
    '.ap-tbl{width:100%;border-collapse:collapse;font-size:12.5px;font-variant-numeric:tabular-nums}',
    '.ap-tbl th,.ap-tbl td{padding:5px 8px;border-bottom:1px solid var(--line-2,#EEF1F5);text-align:right;white-space:nowrap}',
    '.ap-tbl th.l,.ap-tbl td.l{text-align:left}',
    '.ap-tbl thead th{position:sticky;top:0;background:var(--surface-2,#F5F7FC);font-size:11px;text-transform:uppercase;letter-spacing:.03em;color:var(--muted,#71808D)}',
    '.ap-tbl td.new{font-weight:700;color:var(--scen,#1F6FB2)}',
    '.ap-tbl tr.fc td{background:#FDFBF5}',
    '.ap-note{font-size:12px;color:var(--ink-2,#4A5764);line-height:1.55;margin:8px 0 0}'
  ].join('\n');
  function injectCSS() { if ($('#ap-css')) return; var s = document.createElement('style'); s.id = 'ap-css'; s.textContent = SHEET; document.head.appendChild(s); }

  function render() {
    var el = $('#' + CFG.mount); if (!el) return;
    var h = '<div class="ap-grid">' +
      f('ap-url', 'API ünvanı', ST.url, 'http://127.0.0.1:8787') +
      f('ap-token', 'Nişan (token)', ST.token, '', 'password') +
      f('ap-actor', 'İstifadəçi adı', ST.actor, 'ad.soyad') + '</div>';
    h += '<div class="ap-act"><button class="btn sm" id="ap-test"' + (BUSY ? ' disabled' : '') + '>Əlaqəni yoxla</button>' +
      '<button class="btn sm pri" id="ap-pull"' + (BUSY || !ST.url ? ' disabled' : '') + '>Anbardan yeni məlumatı gətir</button>' +
      '<button class="btn sm" id="ap-push"' + (BUSY || !ST.url ? ' disabled' : '') + '>Proqnozu anbara göndər</button>' +
      (ST.lastSync ? '<span class="ap-note" style="margin:0">son sinxronizasiya: ' + esc(String(ST.lastSync).replace('T', ' ').slice(0, 16)) + '</span>' : '') + '</div>';
    if (ST.health) {
      h += ST.health.ok
        ? '<div class="ap-st ok">Əlaqə var · API ' + esc(ST.health.version || '') + ' · ' + ST.health.series + ' sıra, ' + ST.health.obs + ' nöqtə</div>'
        : '<div class="ap-st bad">Əlaqə yoxdur · ' + esc(ST.health.message || '') + '</div>';
    }
    if (BUSY) h += '<div class="ap-st">Gözləyin…</div>';
    if (PULL) {
      if (!PULL.rows.length) h += '<div class="ap-st ok">Anbardakı ' + PULL.total + ' nöqtə modeldəki dəyərlərlə eynidir — dəyişiklik yoxdur.</div>';
      else {
        var picked = 0; PULL.rows.forEach(function (r, i) { if (PULL.pick[i]) picked++; });
        h += '<p class="ap-note"><b>' + PULL.rows.length + ' fərq tapıldı</b> (anbarda ' + PULL.total + ' nöqtə' +
          (PULL.skipped ? ', ' + PULL.skipped + ' nöqtənin modeldə qarşılığı yoxdur' : '') + '). ' +
          'Hamısı seçilib. <b>Sarı fonlu sətirlər</b> modelin proqnoz dövrünə düşür — onları tətbiq etsəniz, hesablanmış dəyərin üzərinə yazılacaq.</p>';
        h += '<div class="ap-tw"><table class="ap-tbl"><thead><tr><th class="l"><input type="checkbox" id="ap-all"' + (picked === PULL.rows.length ? ' checked' : '') + '></th>' +
          '<th class="l">Kod</th><th>İl</th><th>Modeldə</th><th>Anbarda</th><th class="l">Mənbə</th></tr></thead><tbody>' +
          PULL.rows.map(function (r, i) {
            return '<tr' + (r.forecast ? ' class="fc"' : '') + '><td class="l"><input type="checkbox" data-pick="' + i + '"' + (PULL.pick[i] ? ' checked' : '') + '></td>' +
              '<td class="l">' + esc(r.code) + '</td><td>' + r.period + '</td>' +
              '<td>' + (r.from === null ? '—' : nf(r.from, 4)) + '</td><td class="new">' + nf(r.to, 4) + '</td>' +
              '<td class="l">' + esc(r.source) + (r.actor ? ' · ' + esc(r.actor) : '') + '</td></tr>';
          }).join('') + '</tbody></table></div>';
        h += '<div class="ap-act"><button class="btn sm pri" id="ap-apply">Seçilmiş ' + picked + ' nöqtəni modelə tətbiq et</button>' +
          '<button class="btn sm" id="ap-cancel">İmtina</button></div>';
      }
    }
    el.innerHTML = h;
    wire(el);
  }
  function f(id, lab, val, ph, type) {
    return '<div class="ap-f"><label for="' + id + '">' + lab + '</label><input id="' + id + '" type="' + (type || 'text') + '" value="' + esc(val || '') + '" placeholder="' + esc(ph || '') + '"></div>';
  }
  function wire(el) {
    [['ap-url', 'url'], ['ap-token', 'token'], ['ap-actor', 'actor']].forEach(function (p) {
      var i = $('#' + p[0], el); if (!i) return;
      i.addEventListener('change', function () { ST[p[1]] = i.value.trim(); save(); render(); });
    });
    var t = $('#ap-test', el); if (t) t.onclick = test;
    var p2 = $('#ap-pull', el); if (p2) p2.onclick = pull;
    var p3 = $('#ap-push', el); if (p3) p3.onclick = push;
    var ap = $('#ap-apply', el); if (ap) ap.onclick = applyPull;
    var cx = $('#ap-cancel', el); if (cx) cx.onclick = function () { PULL = null; render(); };
    var all = $('#ap-all', el);
    if (all) all.onchange = function () { PULL.rows.forEach(function (r, i) { PULL.pick[i] = all.checked ? 1 : 0; }); render(); };
    el.addEventListener('change', function (e) {
      var c = e.target.closest('[data-pick]'); if (!c) return;
      PULL.pick[+c.getAttribute('data-pick')] = c.checked ? 1 : 0; render();
    });
  }

  root.ApiClient = {
    init: function (cfg) { CFG = cfg; ST = load(); injectCSS(); },
    render: render,
    section: function (title) {
      return '<section class="sec"><div class="sec-h"><h2>' + esc(title || 'Məlumat mübadiləsi (API)') + '</h2>' +
        '<p>Nazirliyin məlumat anbarı ilə əlaqə: yeni faktiki məlumatı modelə gətirin, proqnozu anbara göndərin.</p></div>' +
        '<div class="card pad"><div id="' + CFG.mount + '"></div></div></section>';
    }
  };
})(typeof window !== 'undefined' ? window : globalThis);
