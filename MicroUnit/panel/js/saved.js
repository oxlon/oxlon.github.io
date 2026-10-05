/* saved.js — saved custom scenarios (server: list / open / duplicate / delete / export; offline: the copies exported into
   the bundle, data/saved.js) and the comparison of the three ready scenarios Əsas / Mənfi / İslahat. */
(function () {
  'use strict';
  var U = window.U, B = U.B, LIST = null, ERR = null, SEL = 0;
  function bundle() { return (window.MICRO.SAVED || []).map(function (s) { s.offline = true; return s; }); }
  U.savedAll = function () { return LIST || bundle(); };
  U.savedLoaded = function () { return LIST !== null; };
  U.savedBundle = bundle;
  function load() {
    return U.API.saved().then(function (j) { LIST = j.items || []; ERR = null; }, function (e) { LIST = null; ERR = e.message; });
  }
  U.savedLoad = load;
  function ovText(o) {
    var tot = 0, p = [];
    Object.keys(o || {}).forEach(function (m) {
      var x = o[m] || {}, a = Object.keys(x.exogenous || {}).length, c = Object.keys(x.coefficients || {}).length, l = Object.keys(x.levers || {}).length;
      if (a + c + l) { tot += a + c + l; p.push(m + ' (' + [a ? a + ' ekzogen' : '', c ? c + ' əmsal' : '', l ? l + ' alət' : ''].filter(Boolean).join(', ') + ')'); }
    });
    return tot ? tot + ' giriş, ' + p.length + ' modul: ' + p.join('; ') : 'dəyişiklik yoxdur (baza ssenarisi)';
  }
  /* the server list carries no overrides: read them per scenario (two at a time, cached by id + update time) */
  var OVC = {};
  function ovKey(s) { return s.id + '|' + (s.updated_at || s.updated || ''); }
  function fillCounts(items) {
    var todo = items.filter(function (s) { return !s.offline && !s.overrides && !(ovKey(s) in OVC); }).slice(0, 60);
    var put = function (s) { [].forEach.call(document.querySelectorAll('[data-ovc]'), function (c) { if (c.getAttribute('data-ovc') === s.id) c.textContent = OVC[ovKey(s)] ? ovText(OVC[ovKey(s)]) : '—'; }); };
    var next = function () { var s = todo.shift(); if (!s) return null; return U.API.savedGet(s.id).then(function (r) { OVC[ovKey(s)] = r.overrides || {}; }, function () { OVC[ovKey(s)] = null; }).then(function () { put(s); return next(); }); };
    next(); next();
  }
  function openSaved(s) {
    var apply = function (r) {
      var o = r.overrides || {}; B.ov = {}; B.out = {};
      Object.keys(o).forEach(function (m) { B.ov[m] = { exogenous: o[m].exogenous || {}, coefficients: o[m].coefficients || {}, levers: o[m].levers || {} }; });
      B.base = r.scenario || 'Baseline'; B.name = r.name || ''; B.note = r.note || ''; B.savedId = r.offline ? null : r.id; B.savedName = r.name; U.bNorm();
      var info = { base: B.base, overrides: U.bClean(), name: B.name };
      if (r.result && r.result.results) U.bSetResult(r.result, info); else if (r.series) U.bSetCompact(r.series, info);
      location.hash = '#/ssenari'; U.toast('«' + (r.name || '') + '» açıldı');
    };
    if (s.offline) return apply(s);
    U.API.savedGet(s.id).then(apply, function (e) { U.toast(e.message); });
  }
  U.savedOpen = openSaved;
  U.savedPage = function (v) {
    var on = U.API.online, items = U.savedAll();
    var h = U.bHead('saxlanmis') + (on === false ? U.API.offlineHtml() : '') +
      '<p class="lead" style="font-size:14.5px">' + (LIST ? 'Serverdə saxlanmış ssenarilər.' : 'Server əlçatan deyil — panelin məlumat faylına ixrac olunmuş ssenarilər göstərilir (yalnız baxış).') +
      ' «Aç» — fərziyyələri qurucuya və nəticəni müqayisəyə yükləyir.</p>' + (ERR && on ? '<p class="small down">' + U.esc(ERR) + '</p>' : '') +
      '<div class="toolbar"><button type="button" class="btn sm" id="sv-ref">Yenilə</button><span class="small muted">' + items.length + ' ssenari</span></div>' +
      '<div class="card itbl-wrap"><table class="itbl"><thead><tr><th class="l">Ad</th><th class="l">Baza</th><th class="l">Dəyişikliklər</th><th class="l">Müəllif</th><th class="l">Yenilənib</th><th class="l"></th></tr></thead><tbody>' +
      (items.length ? items.map(function (s, i) {
        return '<tr data-i="' + i + '"><td class="lab"><b>' + U.esc(s.name) + '</b>' + (s.note ? '<span class="u">' + U.esc(s.note) + '</span>' : '') + '</td><td>' + U.SCN[U.SCK[s.scenario] || 'B'] + '</td>' +
          '<td class="small" data-ovc="' + U.esc(s.id) + '">' + U.esc(s.overrides ? ovText(s.overrides) : OVC[ovKey(s)] ? ovText(OVC[ovKey(s)]) : ovKey(s) in OVC ? '—' : 'yüklənir…') + '</td><td class="small">' + U.esc(s.author || '') + '</td><td class="small">' + U.esc(String(s.updated_at || s.updated || '').slice(0, 16).replace('T', ' ')) + '</td>' +
          '<td style="white-space:nowrap"><button type="button" class="btn sm pri" data-a="open">Aç</button> <button type="button" class="btn sm" data-a="json">JSON</button>' +
          (s.offline ? '' : ' <button type="button" class="btn sm" data-a="dup">Dublikat</button> <button type="button" class="btn sm ghost" data-a="del">Sil</button>') + '</td></tr>';
      }).join('') : '<tr><td colspan="6" class="muted">Saxlanmış ssenari yoxdur. Qurucuda ssenari yaradıb «Saxla» düyməsini basın.</td></tr>') + '</tbody></table></div>' +
      '<p class="small muted">Server olmadan baxmaq üçün: ssenarini «JSON» ilə ixrac edib <code>panel/scenarios/</code> qovluğuna qoyun və paneli yenidən yığın (<code>python3 panel/build_panel.py</code>); serverdə saxlanmış ssenarilər də yığım zamanı paketə daxil edilir.</p>';
    v.innerHTML = h;
    fillCounts(items);
    if (LIST === null && on !== false && !ERR) load().then(function () { if (/saxlanmis/.test(location.hash)) U.route(true); });
    v.onclick = function (e) {
      var t = e.target, s = t.closest('#ss-sub [data-v]');
      if (s) { location.hash = '#/ssenari' + (s.getAttribute('data-v') === 'qurucu' ? '' : '/' + s.getAttribute('data-v')); return; }
      if (t.id === 'api-set2' || t.id === 'api-set') { U.API.openSettings(); return; }
      if (t.id === 'api-retry' || t.id === 'sv-ref') { U.API.ping().then(function () { return load(); }).then(function () { U.route(true); }); return; }
      var a = t.getAttribute('data-a'), tr = t.closest('tr[data-i]'); if (!a || !tr) return;
      var it = items[+tr.getAttribute('data-i')];
      if (a === 'open') openSaved(it);
      if (a === 'json') (it.offline ? Promise.resolve(it) : U.API.savedGet(it.id)).then(function (r) {
        U.download(String(r.name || 'ssenari').replace(/[^\wəöüğışçİ\-]+/gi, '_') + '.json', new Blob([JSON.stringify({ format: 'mikro-ssenari/1', name: r.name, scenario: r.scenario, note: r.note, overrides: r.overrides, author: r.author, result: r.result || r.series }, null, 1)], { type: 'application/json' }));
      }, function (er) { U.toast(er.message); });
      if (a === 'dup') U.API.savedGet(it.id).then(function (r) { return U.API.save({ name: r.name + ' (surət)', author: r.author, scenario: r.scenario, overrides: r.overrides, result: r.result, note: r.note }); })
        .then(function () { U.toast('Dublikat yaradıldı'); return load(); }).then(function () { U.route(true); }, function (er) { U.toast(er.message); });
      if (a === 'del' && window.confirm('«' + it.name + '» silinsin?')) U.API.del(it.id).then(function () { U.toast('Silindi'); return load(); }).then(function () { U.route(true); }, function (er) { U.toast(er.message); });
    };
  };
  function diff(s, k, i) { var a = s.s[k][i], b = s.s.B[i]; if (!U.isNum(a) || !U.isNum(b)) return null; return U.isRate(s) ? a - b : (b ? (a / b - 1) * 100 : null); }
  U.readyPage = function (v) {
    var keys = U.META.scen.map(function (k) { return U.byId[k]; }).filter(Boolean);
    var h = U.bHead('hazir') + '<p class="lead" style="font-size:14.5px">FR1-in üç makro ssenarisi (neftin qiyməti və hasilatı, dövlət investisiyası, xarici tələb, faiz siyasəti, TFP) bütün modullardan keçir. «Fərq» — ssenarinin Əsasdan fərqi (faiz göstəricilərində faiz bəndi).</p>' +
      '<div class="card pad"><div class="toolbar" style="margin-top:0"><label class="small muted">Qrafik üçün göstərici</label><select id="sc-sel" class="btn sm">' +
      keys.map(function (s, i) { return U.opt(i, s.f + ' · ' + s.e, SEL); }).join('') + '</select><a class="btn sm" href="' + U.href(keys[SEL]) + '">Komponentin bölməsi →</a></div><div id="sc-ch"></div></div>' +
      '<div class="card" style="margin-top:14px"><div class="grp-h">İllər üzrə açıq müqayisə</div><div class="itbl-wrap"><table class="itbl"><thead><tr><th class="l">Göstərici / ssenari</th><th>2025</th>' +
      U.YEARS.map(function (y) { return '<th class="fc">' + y + '</th>'; }).join('') + '<th>Fərq 2030</th></tr></thead><tbody>';
    keys.forEach(function (s) {
      h += '<tr class="grow"><td colspan="8">' + s.f + ' · ' + U.esc(s.e) + ' <span class="u">' + U.esc(s.u) + '</span></td></tr>';
      U.scens(s).forEach(function (k) { var dd = k === 'B' ? null : diff(s, k, 4);
        h += '<tr><td class="lab"><b style="color:' + U.SCC[k] + '">' + U.SCN[k] + '</b></td><td class="n">' + U.nf(U.b25(s, k), s.d) + '</td>' + s.s[k].map(function (x) { return '<td class="n fc">' + U.nf(x, s.d) + '</td>'; }).join('') +
          '<td class="n dcell ' + U.trend(dd) + '">' + (k === 'B' ? '—' : U.sg(dd, 2) + ' ' + U.gunit(s)) + '</td></tr>'; });
    });
    v.innerHTML = h + '</tbody></table></div></div>';
    var s0 = keys[SEL];
    U.seriesChart(U.$('#sc-ch'), s0, { h: 340, all: true });
    U.$('#sc-sel').onchange = function (e) { SEL = +e.target.value; U.route(true); };
    v.onclick = function (e) { var s = e.target.closest('#ss-sub [data-v]'); if (s) location.hash = '#/ssenari' + (s.getAttribute('data-v') === 'qurucu' ? '' : '/' + s.getAttribute('data-v')); if (e.target.id === 'api-set2') U.API.openSettings(); };
  };
})();
