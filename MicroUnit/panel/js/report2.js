/* report2.js — Hesabat qurucusu, part 2: the page (#/hesabat): choices on the left, live preview on the right,
   templates (localStorage + JSON) and the export buttons (report3.js). */
(function () {
  'use strict';
  var U = window.U, R = U.R, F = { q: '', g: '', fr: '' };
  function pickList() {
    var w = U.fold(F.q.trim()).split(/\s+/).filter(Boolean);
    return U.S.filter(function (s) { return R.frs.indexOf(s.f) >= 0 && (!F.fr || s.f === F.fr) && (!F.g || s.g === F.g) && w.every(function (x) { return U.fold(s.e + ' ' + s.i + ' ' + s.g).indexOf(x) >= 0; }); });
  }
  function custList() {
    var o = [];
    if (U.B && U.B.res) o.push({ id: 'cur', name: 'Qurucudakı cari ssenari: ' + ((U.B.resInfo || {}).name || 'adsız') });
    allSaved().forEach(function (s) { o.push({ id: s.id, name: s.name, offline: s.offline, item: s }); });
    return o;
  }
  /* server-saved scenarios plus the bundled (offline) copies that the server list does not already carry */
  function allSaved() {
    var l = U.savedAll().slice(), seen = {};
    l.forEach(function (s) { seen[s.id] = 1; seen['n:' + s.name] = 1; });
    if (U.savedLoaded && U.savedLoaded()) U.savedBundle().forEach(function (s) { if (!seen[s.id] && !seen['n:' + s.name]) l.push(s); });
    return l;
  }
  function ensureCustom(id) {
    if (U.CUST[id] && id !== 'cur') return Promise.resolve();   // the builder's current result can change between visits
    if (id === 'cur') { var B = U.B; if (!B.res) { delete U.CUST.cur; return Promise.reject(new Error('Qurucuda hesablanmış ssenari yoxdur')); } U.CUST.cur = { name: (B.resInfo || {}).name || 'Cari ssenari', base: (B.resInfo || {}).base, series: B.res, overrides: (B.resInfo || {}).overrides || {} }; return Promise.resolve(); }
    var it = allSaved().filter(function (s) { return s.id === id; })[0];
    if (!it) return Promise.reject(new Error('Ssenari tapılmadı'));
    if (it.offline) { U.CUST[id] = { name: it.name, base: it.scenario, series: it.series, overrides: it.overrides }; return Promise.resolve(); }
    return U.API.savedGet(id).then(function (r) {
      var tmp = U.B.res, ti = U.B.resInfo, tw = U.B.warn, traw = U.B.raw;
      U.bSetResult(r.result, {}); var ser = U.B.res; U.B.res = tmp; U.B.resInfo = ti; U.B.warn = tw; U.B.raw = traw;
      U.CUST[id] = { name: r.name, base: r.scenario, series: ser, overrides: r.overrides || {} };
    });
  }
  U.rEnsureCustom = ensureCustom;
  function side() {
    var pl = pickList(), shown = pl.slice(0, 250), groups = F.fr ? U.groups(F.fr) : [];
    var h = '<div class="card pad rside"><h3>1. Tələblər</h3><div class="chips">' + U.META.frs.map(function (f) { return '<label class="ck"><input type="checkbox" data-fr="' + f.c + '"' + (R.frs.indexOf(f.c) >= 0 ? ' checked' : '') + '> ' + f.c + '</label>'; }).join('') + '</div>' +
      '<h3>2. Komponentlər <span class="muted small">' + R.comps.length + ' seçilib</span></h3><div class="toolbar" style="margin:4px 0"><input type="search" id="rp-q" placeholder="axtar…" value="' + U.esc(F.q) + '">' +
      '<select id="rp-fr" class="btn sm">' + U.opt('', 'Bütün FR', F.fr) + R.frs.map(function (c) { return U.opt(c, c, F.fr); }).join('') + '</select>' +
      (F.fr ? '<select id="rp-g" class="btn sm">' + U.opt('', 'Bütün qruplar', F.g) + groups.map(function (g) { return U.opt(g, g, F.g); }).join('') + '</select>' : '') + '</div>' +
      '<div class="toolbar" style="margin:4px 0"><button type="button" class="btn sm" id="rp-key">Əsas göstəricilər</button><button type="button" class="btn sm" id="rp-all" title="Axtarışa və süzgəcə uyğun bütün komponentləri seçir (siyahıda ilk 250-si göstərilir)">Hamısını seç (' + pl.length + ')</button><button type="button" class="btn sm ghost" id="rp-none">Təmizlə</button></div>' +
      '<div class="picklist">' + shown.map(function (s) { return '<label class="ck"><input type="checkbox" data-c="' + U.esc(s.i) + '"' + (R.comps.indexOf(s.i) >= 0 ? ' checked' : '') + '> <span>' + s.f + ' · ' + U.esc(s.e) + '</span></label>'; }).join('') +
      (pl.length > shown.length ? '<div class="small muted">… daha ' + (pl.length - shown.length) + ' — axtarışı dəqiqləşdirin</div>' : '') + '</div>' +
      '<h3>3. Ssenarilər</h3><div class="chips">' + U.SC.map(function (k) { return '<label class="ck"><input type="checkbox" data-sc="' + k + '"' + (R.scen.indexOf(k) >= 0 ? ' checked' : '') + '> ' + U.SCN[k] + '</label>'; }).join('') + '</div>' +
      '<div class="chips" style="margin-top:4px">' + (custList().map(function (c) { return '<label class="ck"><input type="checkbox" data-cu="' + U.esc(c.id) + '"' + (R.custom.indexOf(c.id) >= 0 ? ' checked' : '') + '> ' + U.esc(c.name) + (c.offline ? ' <span class="muted">(paket)</span>' : '') + '</label>'; }).join('') || '<span class="small muted">Saxlanmış xüsusi ssenari yoxdur (Ssenarilər → Qurucu).</span>') + '</div>' +
      '<h3>4. İllər</h3><div class="toolbar" style="margin:4px 0"><select id="rp-y0" class="btn sm">' + range(2000, 2030).map(function (y) { return U.opt(y, y, R.y0); }).join('') + '</select> — <select id="rp-y1" class="btn sm">' + range(2026, 2030).map(function (y) { return U.opt(y, y, R.y1); }).join('') + '</select></div>' +
      '<h3>5. Məzmun</h3><div class="chips">' + [['tbl', 'Proqnoz cədvəlləri'], ['chart', 'Qrafiklər'], ['eq', 'Tənliklərin xülasəsi'], ['rob', 'Dayanıqlıq'], ['asm', 'Fərziyyələr'], ['notes', 'Qeydlər']].map(function (b) { return '<label class="ck"><input type="checkbox" data-bl="' + b[0] + '"' + (R.blocks[b[0]] ? ' checked' : '') + '> ' + b[1] + '</label>'; }).join('') + '</div>' +
      '<div class="form"><label>Başlıq<input id="rp-title" value="' + U.esc(R.title) + '"></label><label>Müəllif<input id="rp-au" value="' + U.esc(R.author) + '"></label><label>Qeydlər<textarea id="rp-notes" rows="3">' + U.esc(R.notes) + '</textarea></label></div>' +
      '<h3>6. Şablonlar</h3><div class="toolbar" style="margin:4px 0">' + tplSel() + '<button type="button" class="btn sm" id="rp-tsave">Şablonu saxla</button><button type="button" class="btn sm" id="rp-texp">JSON ixrac</button><label class="btn sm" style="cursor:pointer">JSON idxal<input type="file" id="rp-timp" accept=".json" hidden></label></div></div>';
    return h;
  }
  function range(a, b) { var o = []; for (var y = a; y <= b; y++) o.push(y); return o; }
  function tpls() { try { return JSON.parse(U.ls('mikroPanel.tpl') || '[]'); } catch (e) { return []; } }
  function tplSel() { var t = tpls(); return t.length ? '<select id="rp-tload" class="btn sm">' + U.opt('', 'Şablonu yüklə…', '') + t.map(function (x, i) { return U.opt(i, x.name, ''); }).join('') + '</select>' : ''; }
  function cfg() { var o = {}; Object.keys(R).forEach(function (k) { o[k] = R[k]; }); return JSON.parse(JSON.stringify(o)); }
  function apply(o) { Object.keys(o || {}).forEach(function (k) { if (k in R) R[k] = o[k]; }); }
  var redrawPrev = U.debounce(function () { var p = U.$('#rep-prev'); if (!p) return; p.innerHTML = U.rPreview(); U.rCharts(); U.rSave(); }, 250);
  U.rRedraw = function () { var p = U.$('#rep-prev'); if (p) { p.innerHTML = U.rPreview(); U.rCharts(); } };
  U.pages.hesabat = function (v) {
    var addC = U.HQ && U.HQ.get('c'); if (addC && U.byId[addC] && R.comps.indexOf(addC) < 0) { R.comps.push(addC); if (R.frs.indexOf(U.byId[addC].f) < 0) R.frs.push(U.byId[addC].f); }
    var pre = U.HQ && U.HQ.get('cur') && U.B.res ? ensureCustom('cur').then(function () { delete U.CUST.cur; return ensureCustom('cur'); }).then(function () { if (R.custom.indexOf('cur') < 0) R.custom.push('cur'); }) : Promise.resolve();
    // server-saved scenarios: load once per session (the bundled copies alone must not stop the request)
    if (U.API.online !== false && location.protocol !== 'file:' && !U.savedLoaded() && !U._rSavedTry) {
      U._rSavedTry = true;
      U.savedLoad().then(function () { if (U.savedLoaded() && /^#\/hesabat/.test(location.hash)) U.route(true); });
    }
    v.innerHTML = '<div class="eyebrow">Hesabat qurucusu</div><div class="hrow"><h1 class="h1" style="margin-top:4px">Öz hesabatınızı hazırlayın</h1><span class="hbtns">' +
      '<button type="button" class="btn sm" id="rx-print">Çap / PDF</button><button type="button" class="btn sm pri" id="rx-xlsx">Excel (.xlsx)</button><button type="button" class="btn sm pri" id="rx-docx">Word (.docx)</button><button type="button" class="btn sm" id="rx-csv">CSV</button></span></div>' +
      '<p class="lead" style="font-size:14.5px">Solda seçin — sağda hesabatın görünüşü dərhal yenilənir. Saxlanmış xüsusi ssenariləri də daxil edə bilərsiniz. Seçim brauzerdə yadda qalır; şablon kimi saxlayıb başqasına göndərmək olar.</p>' +
      '<div class="rep-layout">' + side() + '<div class="card rprev" id="rep-prev"><div class="muted pad">Hazırlanır…</div></div></div>';
    pre.then(function () { return Promise.all(R.custom.map(function (id) { return ensureCustom(id).catch(function () { R.custom = R.custom.filter(function (x) { return x !== id; }); }); })); }).then(U.rRedraw);
    var re = function () { U.rSave(); U.route(true); };
    v.onchange = function (e) {
      var t = e.target, a;
      if ((a = t.getAttribute('data-fr'))) { R.frs = t.checked ? R.frs.concat([a]) : R.frs.filter(function (x) { return x !== a; }); re(); return; }
      if ((a = t.getAttribute('data-c'))) { R.comps = t.checked ? R.comps.concat([a]) : R.comps.filter(function (x) { return x !== a; }); redrawPrev(); return; }
      if ((a = t.getAttribute('data-sc'))) { R.scen = U.SC.filter(function (k) { return k === a ? t.checked : R.scen.indexOf(k) >= 0; }); redrawPrev(); return; }
      if ((a = t.getAttribute('data-bl'))) { R.blocks[a] = t.checked; redrawPrev(); return; }
      if ((a = t.getAttribute('data-cu'))) {
        if (!t.checked) { R.custom = R.custom.filter(function (x) { return x !== a; }); redrawPrev(); return; }
        ensureCustom(a).then(function () { R.custom.push(a); redrawPrev(); }, function (er) { t.checked = false; U.toast(er.message); }); return;
      }
      if (t.id === 'rp-fr') { F.fr = t.value; F.g = ''; U.route(true); return; }
      if (t.id === 'rp-g') { F.g = t.value; U.route(true); return; }
      if (t.id === 'rp-y0' || t.id === 'rp-y1') { R[t.id === 'rp-y0' ? 'y0' : 'y1'] = +t.value; if (R.y0 > R.y1) R.y0 = Math.min(R.y0, 2025); redrawPrev(); return; }
      if (t.id === 'rp-tload' && t.value !== '') { apply(tpls()[+t.value].cfg); re(); U.toast('Şablon yükləndi'); return; }
      if (t.id === 'rp-timp' && t.files[0]) { var fr = new FileReader(); fr.onload = function () { try { apply(JSON.parse(fr.result).cfg || JSON.parse(fr.result)); re(); U.toast('Şablon idxal olundu'); } catch (er) { U.toast('Fayl oxunmadı'); } }; fr.readAsText(t.files[0]); }
    };
    v.oninput = function (e) {
      var t = e.target;
      if (t.id === 'rp-title') { R.title = t.value; redrawPrev(); } else if (t.id === 'rp-au') { R.author = t.value; redrawPrev(); } else if (t.id === 'rp-notes') { R.notes = t.value; redrawPrev(); }
      else if (t.id === 'rp-q') { F.q = t.value; clearTimeout(U.rq); U.rq = setTimeout(function () { var p = t.selectionStart; U.route(true); var x = U.$('#rp-q'); x.focus(); x.setSelectionRange(p, p); }, 300); }
    };
    v.onclick = function (e) {
      var id = e.target.id;
      if (id === 'rp-key') { R.comps = U.META.scen.concat(U.META.frs.map(function (f) { return f.kpi; }).reduce(function (a, b) { return a.concat(b); }, [])).filter(function (x, i, a) { return a.indexOf(x) === i && R.frs.indexOf(U.byId[x].f) >= 0; }); re(); }
      if (id === 'rp-all') {
        pickList().forEach(function (s) { if (R.comps.indexOf(s.i) < 0) R.comps.push(s.i); });
        // hundreds of Plotly charts make the preview, print and Word export very slow: charts off above 60 components
        if (R.comps.length > 60 && R.blocks.chart) { R.blocks.chart = false; U.toast(R.comps.length + ' komponent seçildi — sürət üçün qrafiklər söndürüldü («5. Məzmun»da yenidən qoşmaq olar)'); }
        re();
      }
      if (id === 'rp-none') { R.comps = []; re(); }
      if (id === 'rp-tsave') { var n = window.prompt('Şablonun adı', R.title); if (n) { var t = tpls(); t.push({ name: n, cfg: cfg() }); U.ls('mikroPanel.tpl', JSON.stringify(t)); re(); U.toast('Şablon saxlanıldı'); } }
      if (id === 'rp-texp') U.download('hesabat_sablonu.json', new Blob([JSON.stringify({ format: 'mikro-hesabat-sablonu/1', name: R.title, cfg: cfg() }, null, 1)], { type: 'application/json' }));
      if (id === 'rx-print') U.rPrint();
      if (id === 'rx-xlsx') U.REP.save('xlsx');
      if (id === 'rx-docx') U.REP.save('docx');
      if (id === 'rx-csv') U.REP.save('csv');
    };
  };
})();
