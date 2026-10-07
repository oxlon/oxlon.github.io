/* p_stress2.js — custom stress builder: factor shocks (S0 factors, size in σ or natural units) → /api/v1/stress/run
   (MicroUnit chain FR1→FR12 + RU joint Monte Carlo); results vs the official baseline; save / load / delete (API, or this
   browser + JSON when offline); an offline linear preview from the S1 grid. */
(function () {
  'use strict';
  var U = window.U, ST = U.ST;
  var PRE = [['Neft −2σ', [['brent', -2]]], ['Neft −2σ + devalvasiya +1σ', [['brent', -2], ['fx', 1]]], ['Tərəfdaş resessiyası −2σ', [['partner', -2]]], ['Geosiyasi eskalasiya', [['geo_stress', 1]]],
    ['Quraqlıq −2σ + ərzaq +1σ', [['drought', -2], ['food', 1]]], ['İnflyasiya sürprizi +1σ + faiz +1σ', [['costpush', 1], ['rate', 1]]], ['Güclü zəlzələ', [['quake', 2]]]];
  function load() { try { return JSON.parse(U.ls('riskPanel.stress') || 'null'); } catch (e) { return null; } }
  var B = ST.B = load() || { name: 'Neft −2σ', shocks: [{ factor: 'brent', k_sigma: -2 }], with_measures: true, stochastic: true, n: 4000 };
  function save() { U.ls('riskPanel.stress', JSON.stringify(B)); }
  function F(a) { return U.T('S0_factor_sigma').filter(function (f) { return f.amil === a; })[0] || {}; }
  /* natural size of a k·σ shock: the model's own size from the S1 grid (log factors are non-linear, e.g. Brent −2σ ≠ 2 × 1σ),
     piecewise-linear between grid points; before data/s1.js is loaded (or outside the grid) ≈ k × 1σ */
  function nat(s) {
    var f = F(s.factor), k = +s.k_sigma, lin = k * (f.olcu_1sigma || 0), m = {};
    U.T('S1_scalability_grid').forEach(function (r) { if (r.amil === s.factor && r.variant !== 'canlı' && U.isNum(r.olcu)) m[r.k_sigma] = r.olcu; });
    var ks = Object.keys(m).map(Number).concat([0]).sort(function (a, b) { return a - b; }); m[0] = 0;
    if (ks.length < 3 || k < ks[0] || k > ks[ks.length - 1]) return '≈ ' + U.sg(lin, 2);
    for (var i = 1; i < ks.length; i++) if (k <= ks[i]) { var a = ks[i - 1], b = ks[i]; if (k === b || k === a) return U.sg(m[k], 2); return '≈ ' + U.sg(m[a] + (m[b] - m[a]) * (k - a) / (b - a), 2); }
    return '≈ ' + U.sg(lin, 2);
  }
  function rows() {
    return B.shocks.map(function (s, i) { var f = F(s.factor);
      return '<div class="crow"><div><select class="btn sm" data-i="' + i + '" data-k="factor">' + U.T('S0_factor_sigma').map(function (x) { return U.opt(x.amil, x.amil_ad, s.factor); }).join('') + '</select><div class="small muted" style="margin-top:4px">1σ = ' + U.nf(f.olcu_1sigma) + ' ' + U.esc(f.vahid) + ' · ' + U.esc(f.oturme_kanali || '') + (U.isNum(f.canli_k_sigma) ? ' · bu gün ' + U.sg(f.canli_k_sigma, 2) + 'σ' : '') + '</div></div>' +
        '<div class="c-r"><input type="range" min="-3" max="3" step="0.25" value="' + s.k_sigma + '" data-i="' + i + '" data-k="k"><input class="cnum" value="' + U.nf(s.k_sigma, 2) + '" data-i="' + i + '" data-k="kn" aria-label="σ"> σ = <b class="tnum">' + nat(s) + '</b> ' + U.esc(f.vahid || '') +
        (U.isNum(f.canli_k_sigma) ? ' <button class="btn sm ghost" data-i="' + i + '" data-k="live">bugünkü</button>' : '') + ' <button class="btn sm ghost" data-i="' + i + '" data-k="del" title="Sil">✕</button></div></div>'; }).join('');
  }
  function preview(el) {
    U.need(['s1'], el, function () {
      var y = U.scoreYear(), acc = {};
      B.shocks.forEach(function (s) {
        var g = U.T('S1_scalability_grid').filter(function (r) { return r.amil === s.factor && r.variant !== 'canlı' && r.il === y; }), ks = U.uniq(g.map(function (r) { return r.k_sigma; })).sort(function (a, b) { return a - b; });
        if (!ks.length) return; var lo = ks.filter(function (k) { return k <= s.k_sigma; }).pop(), hi = ks.filter(function (k) { return k >= s.k_sigma; })[0]; if (lo == null) lo = hi; if (hi == null) hi = lo;
        U.HEADT.forEach(function (t) { var a = g.filter(function (r) { return r.hedef_id === t && r.k_sigma === lo; })[0], b = g.filter(function (r) { return r.hedef_id === t && r.k_sigma === hi; })[0]; if (!a || !b) return;
          var w = hi === lo ? 0 : (s.k_sigma - lo) / (hi - lo), d = a.delta + w * (b.delta - a.delta); acc[t] = acc[t] || { hedef_ad: a.hedef_ad, vahid: a.vahid, delta: 0 }; acc[t].delta += d; });
      });
      el.innerHTML = U.dt('sb-pv', Object.keys(acc).map(function (k) { return acc[k]; }), [{ k: 'hedef_ad', l: 'Göstərici' }, { k: 'vahid', l: 'Vahid' }, { k: 'delta', l: 'Bazadan fərq, ' + y + ' (təqribi)', n: 1, d: 3 }],
        { title: 'Oflayn təqribi baxış: S1 şəbəkəsindən xətti interpolyasiya və şokların cəmi', file: 'stress_teqribi', note: 'Qarşılıqlı təsirlər və paylanma nəzərə alınmır — dəqiq nəticə üçün «Hesabla» (server).' });
    });
  }
  function result(el, r) {
    var mh = (r.micro || {}).headline || [], dev = (r.ru || {}).deviation || [], dist = (r.ru || {}).distribution || [], y = r.score_year || U.scoreYear();
    var hy = mh.filter(function (q) { return q.il === y && U.HEADT.indexOf(q.hedef_id) >= 0; });
    el.innerHTML = '<div class="note-b"><b>' + U.esc(r.name || B.name) + '</b> · baza ' + U.esc(r.baseline_id || '') + ' · ' + U.nf(r.seconds, 1) + ' s' + (r.notes && r.notes.length ? '<br>' + r.notes.map(U.esc).join('<br>') : '') + ((r.micro || {}).warnings || []).map(function (w) { return '<br><span class="warn">⚠ ' + U.esc(w) + '</span>'; }).join('') + '</div>' +
      '<div class="cols2"><div class="card pad"><h3>Baş göstəricilər, ' + y + ' — bazadan fərq</h3><div id="sb-c" class="ch"></div></div><div class="card pad"><h3>RU simulyasiyası: sapma, tədbirlə və tədbirsiz</h3><div id="sb-d" class="ch"></div></div></div>' +
      U.dt('sb-h', mh, null, { title: 'MikroUnit zənciri: baş göstəricilər 2026–2030 (baza, ssenari, fərq)', file: 'stress_bas_gostericiler' }) +
      U.dt('sb-k', (function (c) { c = c || {}; return Array.isArray(c) ? c : (c.top_pct || []).concat((c.top_abs || []).filter(function (x) { return !(c.top_pct || []).some(function (y) { return y.komponent_id === x.komponent_id; }); })); })((r.micro || {}).components), null, { title: 'Ən çox təsirlənən komponentlər' + (((r.micro || {}).components || {}).n_affected ? ' (təsirlənən: ' + r.micro.components.n_affected + ')' : ''), file: 'stress_komponentler' }) +
      U.dt('sb-v', dev, null, { title: 'RU birgə Monte Karlo: sapma və tədbirin effekti', file: 'stress_ru_sapma' }) + U.dt('sb-p', dist, null, { title: 'Paylanma: şoka şərtli vs şərtsiz', file: 'stress_paylanma' }) +
      (r.ru && r.ru.metrics ? U.dt('sb-m', [].concat.apply([], Object.keys(r.ru.metrics).map(function (k) { var m = r.ru.metrics[k] || {}; return Object.keys(m).map(function (b) { return Object.assign({ gosterici: k, baxis: b }, m[b]); }); })), null, { title: 'Metrikalar (ES10, hədd pozulma ehtimalı)', file: 'stress_metrikalar' }) : '');
    U.barH(U.$('#sb-c', el), hy.map(function (q) { return q.hedef_ad + ' (' + q.vahid + ')'; }), hy.map(function (q) { return q.delta; }), 'bazadan fərq', { color: hy.map(function (q) { return q.delta >= 0 ? '#1E7B4F' : '#B3261E'; }) });
    var g = dev.filter(function (q) { return q.kind === 'g' || /qeyri-neft/.test(q.gosterici || ''); });
    U.lines(U.$('#sb-d', el), [{ x: g.map(function (q) { return q.il; }), y: g.map(function (q) { return q.sapma; }), name: 'qeyri-neft: sapma', c: '#B3261E', mode: 'lines+markers' }, { x: g.map(function (q) { return q.il; }), y: g.map(function (q) { return q.sapma_tedbirle; }), name: 'tədbirlə', c: '#1E7B4F', mode: 'lines+markers', dash: 'dash' }], 'f.b.', { years: true, zero: true });
  }
  function savedList(el) {
    var loc = []; try { loc = JSON.parse(U.ls('riskPanel.stressSaved') || '[]'); } catch (e) { loc = []; }
    var render = function (srv) {
      var all = (srv || []).map(function (s) { return { id: s.id, name: s.name, src: 'server', created: s.created, req: s.request, res: s.result }; }).concat(loc.map(function (s, i) { return { id: 'L' + i, name: s.name, src: 'bu brauzer', created: s.created, req: s.request, res: s.result }; }));
      el.innerHTML = all.length ? U.dt('sb-sv', all, [{ k: 'name', l: 'Ad' }, { k: 'src', l: 'Harada' }, { k: 'created', l: 'Yaradılıb' }, { k: 'id', l: '', f: function (v) { return '<button class="btn sm" data-ld="' + U.esc(v) + '">Aç</button> <button class="btn sm ghost" data-rm="' + U.esc(v) + '">Sil</button>'; } }], { title: 'Saxlanmış stress ssenariləri', file: 'stress_saxlanmis' }) : '<p class="small muted">Saxlanmış ssenari yoxdur.</p>';
      el.onclick = function (e) {
        var ld = e.target.closest('[data-ld]'), rm = e.target.closest('[data-rm]'), id = (ld || rm || {}).getAttribute && (ld || rm).getAttribute(ld ? 'data-ld' : 'data-rm'); if (!id) return;
        var it = all.filter(function (s) { return s.id === id; })[0]; if (!it) return;
        if (ld) { var open = function (res) { var q = it.req || {}; B.name = it.name; B.shocks = q.shocks || B.shocks; if (q.with_measures != null) B.with_measures = !!q.with_measures; if (q.stochastic != null) B.stochastic = !!q.stochastic; if (q.n) B.n = q.n; save(); ST.last = res || null; ST.builder(ST.el); };
          if (it.src === 'server' && !it.res) U.API.savedGet(id).then(function (j) { open(j.result); }, function () { open(null); }); else open(it.res); }
        else if (it.src === 'server') U.API.del(id).then(function () { savedList(el); }, function (er) { U.toast(er.message); });
        else { loc.splice(+id.slice(1), 1); U.ls('riskPanel.stressSaved', JSON.stringify(loc)); savedList(el); }
      };
    };
    if (U.API.fileMode() || U.API.online === false) render([]); else U.API.saved('stress').then(function (j) { render(j.scenarios || []); }, function () { render([]); });
  }
  function req() { return { name: B.name, shocks: B.shocks.map(function (s) { return { factor: s.factor, k_sigma: s.k_sigma }; }), with_measures: B.with_measures, stochastic: B.stochastic, n: B.n, top_components: 40 }; }
  ST.builder = function (el) {
    ST.el = el;
    el.innerHTML = '<div class="presets">' + PRE.map(function (p, i) { return '<button class="btn sm" data-pre="' + i + '">' + U.esc(p[0]) + '</button>'; }).join('') + '</div>' +
      '<div class="card" style="margin-top:12px"><div class="grp-h">Şoklar<span class="muted small" style="font-weight:400">σ vahidində; təbii ölçü avtomatik göstərilir</span></div><div id="sb-rows">' + rows() + '</div>' +
      '<div class="toolbar" style="padding:0 16px"><button class="btn sm" id="sb-add">+ Amil əlavə et</button><label><input type="checkbox" id="sb-wm"' + (B.with_measures ? ' checked' : '') + '> tədbirlə müqayisə (T09)</label><label><input type="checkbox" id="sb-st"' + (B.stochastic ? ' checked' : '') + '> şərti paylanma</label>' +
      '<label>ssenari sayı <input class="cnum" id="sb-n" value="' + B.n + '"></label><label>Ad <input class="cnum" style="width:220px;text-align:left" id="sb-nm" value="' + U.esc(B.name) + '"></label></div>' +
      '<div class="toolbar" style="padding:0 16px 12px"><button class="btn pri" id="sb-run">' + U.icon('play', 14) + ' Hesabla</button><button class="btn" id="sb-save">Saxla</button><button class="btn ghost" id="sb-exp">JSON ixrac</button><label class="btn ghost">JSON idxal<input type="file" id="sb-imp" accept=".json" hidden></label></div></div>' +
      '<div id="sb-off"></div><div id="sb-res"></div>' + U.sec('Saxlanmış ssenarilər', '', '<div id="sb-saved"></div>');
    var off = U.$('#sb-off', el);
    if (U.API.mode() === 'brauzer') off.innerHTML = U.API.browserHtml('stress testinin hesablanması');
    else if (U.API.fileMode() || U.API.online === false) { off.innerHTML = U.API.offlineHtml('Stress testinin hesablanması') + '<div id="sb-pv"></div>'; preview(U.$('#sb-pv', el)); }
    if (ST.last) result(U.$('#sb-res', el), ST.last);
    savedList(U.$('#sb-saved', el));
    var redraw = function () { save(); U.$('#sb-rows', el).innerHTML = rows(); var pv = U.$('#sb-pv', el); if (pv) preview(pv); };
    if (!U.has('S1_scalability_grid')) U.lazy('s1').then(function () { var r = U.$('#sb-rows', el); if (r && ST.el === el) r.innerHTML = rows(); }, function () { /* keep ≈ k × 1σ */ });
    el.oninput = function (e) { var t = e.target, i = t.getAttribute('data-i'); if (i == null) return; var s = B.shocks[+i];
      if (t.getAttribute('data-k') === 'k') { s.k_sigma = +t.value; var row = t.closest('.crow'); row.querySelector('[data-k=kn]').value = U.nf(s.k_sigma, 2); row.querySelector('b.tnum').textContent = nat(s); save(); } };
    el.onchange = function (e) { var t = e.target, i = t.getAttribute('data-i'), k = t.getAttribute('data-k');
      if (i != null && k === 'k') { var pv0 = U.$('#sb-pv', el); if (pv0) preview(pv0); } else if (i != null && k === 'factor') { B.shocks[+i].factor = t.value; redraw(); } else if (i != null && k === 'kn') { var x = U.parseNum(t.value); if (U.isNum(x)) { B.shocks[+i].k_sigma = Math.max(-5, Math.min(5, x)); redraw(); } }
      else if (t.id === 'sb-wm') { B.with_measures = t.checked; save(); } else if (t.id === 'sb-st') { B.stochastic = t.checked; save(); } else if (t.id === 'sb-n') { B.n = Math.max(500, Math.min(20000, U.parseNum(t.value) || 4000)); save(); } else if (t.id === 'sb-nm') { B.name = t.value; save(); }
      else if (t.id === 'sb-imp' && t.files[0]) { var fr = new FileReader(); fr.onload = function () { try { var j = JSON.parse(fr.result); B.name = j.name || 'İdxal'; B.shocks = (j.request || j).shocks || []; save(); ST.last = j.result || null; ST.builder(el); } catch (er) { U.toast('JSON oxunmadı'); } }; fr.readAsText(t.files[0]); } };
    el.onclick = function (e) { var t = e.target.closest('button,[data-pre]'); if (!t) return;
      var i = t.getAttribute('data-i'), k = t.getAttribute('data-k');
      if (t.hasAttribute('data-pre')) { var p = PRE[+t.getAttribute('data-pre')]; B.name = p[0]; B.shocks = p[1].map(function (x) { return { factor: x[0], k_sigma: x[1] }; }); save(); ST.builder(el); return; }
      if (k === 'del') { B.shocks.splice(+i, 1); redraw(); return; }
      if (k === 'live') { B.shocks[+i].k_sigma = Math.round(F(B.shocks[+i].factor).canli_k_sigma * 100) / 100; redraw(); return; }
      if (t.id === 'sb-add') { B.shocks.push({ factor: 'fx', k_sigma: 1 }); redraw(); return; }
      if (t.id === 'sb-exp') { U.download((B.name || 'stress').replace(/\W+/g, '_') + '.json', new Blob([JSON.stringify({ kind: 'stress', name: B.name, request: req(), result: ST.last || null }, null, 1)], { type: 'application/json' })); return; }
      if (t.id === 'sb-run') { var r = U.$('#sb-res', el); r.innerHTML = '<p class="small muted">Hesablanır… (≈ 5–10 s)</p>'; U.API.stress(req()).then(function (j) { ST.last = j; off.innerHTML = ''; result(r, j); }, function (er) { r.innerHTML = U.API.failHtml('Stress testinin hesablanması', er); }); return; }
      if (t.id === 'sb-save') { var body = { name: B.name, kind: 'stress', request: req(), result: ST.last || undefined };
        U.API.save(body).then(function () { U.toast('Serverdə saxlanıldı'); savedList(U.$('#sb-saved', el)); }, function () { var loc = []; try { loc = JSON.parse(U.ls('riskPanel.stressSaved') || '[]'); } catch (er) { loc = []; } loc.push(Object.assign({ created: new Date().toISOString().slice(0, 16) }, body)); U.ls('riskPanel.stressSaved', JSON.stringify(loc)); U.toast('Server yoxdur — bu brauzerdə saxlanıldı'); savedList(U.$('#sb-saved', el)); }); }
    };
  };
})();
