/* p_kpi.js — KPI və qiymətləndirmə (FR5): the KPI catalogue; the user selects ≥ 5 KPIs (enforced) and weights; multi-
   criteria ranking (min–max normalisation by direction, weighted mean — same rule as policyunit/kpi.py) and cost-
   effectiveness across scenarios; ranking / radar / heat-table charts; the run's default result; server compare. */
(function () {
  'use strict';
  var U = window.U, A = U.API, MIN = 5, KEY = 'policyPanel.kpi';
  function state() {
    var cat = U.T('P5_kpi_catalogue'), st = null; try { st = JSON.parse(U.ls(KEY) || 'null'); } catch (e) { st = null; }
    if (!st || !st.sel) st = { sel: cat.filter(function (k) { return k.selected === true || k.selected === 'True' || k.default_selected === 'yes'; }).map(function (k) { return k.id; }), w: {}, sc: U.official().map(function (s) { return s.id; }) };
    cat.forEach(function (k) { if (!U.isNum(st.w[k.id])) st.w[k.id] = k.default_weight; });
    return st;
  }
  function vals() {
    var all = U.T('kpi_all'), o = {};
    (all.length ? all : U.T('P5_kpi_values')).forEach(function (r) { (o[r.kpi] = o[r.kpi] || {})[r.scenario] = r.value; });
    U.T('P4_kpi_inputs').forEach(function (r) { (o[r.kpi] = o[r.kpi] || {})[r.scenario] = r.value; });
    return o;
  }
  U.kpiRank = function (st) {
    var cat = {}, V = vals(), cost = {}; U.T('P5_kpi_catalogue').forEach(function (k) { cat[k.id] = k; }); U.T('P5_ranking').forEach(function (r) { cost[r.scenario] = r.cost_mln_azn; });
    var N = {};
    st.sel.forEach(function (k) {
      var xs = st.sc.map(function (s) { return (V[k] || {})[s]; }).filter(U.isNum), lo = Math.min.apply(null, xs), hi = Math.max.apply(null, xs);
      st.sc.forEach(function (s) { var x = (V[k] || {})[s], n = !U.isNum(x) ? null : hi - lo < 1e-12 ? 0.5 : (x - lo) / (hi - lo); if (n != null && (cat[k] || {}).direction === 'lower') n = 1 - n; (N[s] = N[s] || {})[k] = n; });
    });
    var R = st.sc.map(function (s) {
      var sw = 0, sx = 0, miss = []; st.sel.forEach(function (k) { var n = (N[s] || {})[k], w = +st.w[k] || 0; if (n == null) miss.push(k); else { sw += w; sx += w * n; } });
      var sc = sw > 0 ? sx / sw : null, c = cost[s];
      return { scenario: s, scenario_name: U.sname(s), score: sc, complete: !miss.length, kpis_used: st.sel.length - miss.length, kpis_missing: miss.join('; '), cost_mln_azn: c, score_per_bn_azn: U.isNum(sc) && c > 1 ? sc / (c / 1000) : null };
    }).sort(function (a, b) { return (b.score == null ? -1 : b.score) - (a.score == null ? -1 : a.score); });
    R.forEach(function (r, i) { r.rank = i + 1; });
    return { rows: R, norm: N, V: V, cat: cat };
  };
  function picker(st) {
    var by = U.by(U.T('P5_kpi_catalogue'), 'horizon');
    return Object.keys(by).map(function (h) { return '<h4>' + U.esc(h) + ' müddət</h4><div class="kpick">' + by[h].map(function (k) { var on = st.sel.indexOf(k.id) >= 0; return '<label class="' + (on ? 'on' : '') + '" title="' + U.esc((k.description_az || '') + ' · ' + k.formula) + '"><input type="checkbox" data-k="' + U.esc(k.id) + '"' + (on ? ' checked' : '') + '><span>' + U.esc(k.name_az) + '<br><small class="muted">' + U.esc(k.unit) + ' · ' + (k.direction === 'lower' ? 'az yaxşıdır ↓' : 'çox yaxşıdır ↑') + '</small></span><input type="number" min="0" step="0.5" data-w="' + U.esc(k.id) + '" value="' + st.w[k.id] + '" aria-label="çəki"' + (on ? '' : ' disabled') + '></label>'; }).join('') + '</div>'; }).join('');
  }
  function results(v, st) {
    var ok = st.sel.length >= MIN && st.sc.length >= 2, box = U.$('#k-res', v);
    U.$('#k-cnt', v).innerHTML = '<span class="kcount' + (st.sel.length < MIN ? ' bad' : '') + '">' + st.sel.length + ' KPI seçilib</span>' + (st.sel.length < MIN ? ' — <b class="down">ən azı ' + MIN + ' KPI seçin</b> (TT FR5 tələbi)' : '') + ' · ' + st.sc.length + ' ssenari' + (st.sc.length < 2 ? ' — <b class="down">ən azı 2 ssenari seçin</b>' : '');
    if (!ok) { box.innerHTML = '<div class="vmsg bad">Reytinq üçün ən azı ' + MIN + ' KPI və 2 ssenari lazımdır.</div>'; return; }
    var K = U.kpiRank(st), R = K.rows, top = R.slice(0, 5);
    box.innerHTML = '<div class="expl">Hər KPI ssenarilər arasında 0–1 aralığına normallaşdırılır (ən yaxşı = 1, istiqamət nəzərə alınır); bal = Σ çəki × norm / Σ çəki (yalnız mövcud KPI-lar). Xərc-effektivlik = bal / 1 mlrd AZN birbaşa fiskal xərc (qısa + orta müddət). Lider: <b>' + U.esc(R[0].scenario_name) + '</b> (bal ' + U.nf(R[0].score, 3) + ').</div>' +
      '<div class="cols2"><div class="card pad"><h3>Çoxkriteriyalı reytinq</h3><div id="k-r" class="ch"></div></div><div class="card pad"><h3>Profil (ilk 5 ssenari, normallaşdırılmış)</h3><div id="k-rad" class="ch"></div></div></div>' +
      '<div class="cols2"><div class="card pad"><h3>Xərc-effektivlik</h3><div id="k-ce" class="ch"></div></div><div>' + U.dt('k-rank', R, [{ k: 'rank', l: 'Yer', n: 1 }, { k: 'scenario_name', l: 'Ssenari' }, { k: 'score', l: 'Bal', n: 1, d: 3 }, { k: 'kpis_used', l: 'KPI', n: 1 }, { k: 'complete', l: 'Tam', f: function (x) { return x ? 'bəli' : '<span class="chip warn" title="bəzi KPI-lar üçün giriş yoxdur — bal mövcud KPI-larla hesablanıb">natamam</span>'; } }, { k: 'cost_mln_azn', l: 'Xərc, mln AZN', n: 1, d: 0 }, { k: 'score_per_bn_azn', l: 'Bal / 1 mlrd AZN', n: 1, d: 3 }, { k: 'kpis_missing', l: 'Çatışmayan' }], { title: 'Reytinq (sizin seçiminiz)', file: 'kpi_reytinq' }) + '</div></div>' +
      U.dt('k-mat', st.sel.map(function (k) { var o = { _k: k, kpi: (K.cat[k] || {}).name_az || k, unit: (K.cat[k] || {}).unit, w: st.w[k] }; st.sc.forEach(function (s) { o[s] = (K.V[k] || {})[s]; }); return o; }), [{ k: 'kpi', l: 'KPI' }, { k: 'unit', l: 'Vahid' }, { k: 'w', l: 'Çəki', n: 1 }].concat(st.sc.map(function (s) { return { k: s, l: U.sname(s), n: 1, d: 3, f: function (x, o) { var n = (K.norm[s] || {})[o._k]; return U.isNum(x) ? '<span style="display:block;background:rgba(14,111,124,' + (U.isNum(n) ? (0.08 + 0.42 * n).toFixed(2) : 0) + ')">' + U.nf(x, Math.abs(x) >= 100 ? 0 : 3) + '</span>' : '—'; } }; })), { title: 'KPI × ssenari (xam dəyərlər; rəng — normallaşdırılmış bal)', file: 'kpi_matris' });
    U.barH(U.$('#k-r', v), R.map(function (r) { return r.scenario_name; }), R.map(function (r) { return r.score; }), 'bal (0–1)', { color: '#0E6F7C' });
    var C = R.filter(function (r) { return U.isNum(r.score_per_bn_azn); }).sort(function (a, b) { return b.score_per_bn_azn - a.score_per_bn_azn; });
    U.barH(U.$('#k-ce', v), C.map(function (r) { return r.scenario_name; }), C.map(function (r) { return r.score_per_bn_azn; }), 'bal / 1 mlrd AZN', { color: '#1F6FB2' });
    var th = st.sel.map(function (k) { return ((K.cat[k] || {}).name_az || k).replace(/ — /, '<br>'); });
    U.plot(U.$('#k-rad', v), top.map(function (r, i) { var y = st.sel.map(function (k) { var n = (K.norm[r.scenario] || {})[k]; return U.isNum(n) ? n : 0; }); return { type: 'scatterpolar', r: y.concat([y[0]]), theta: th.concat([th[0]]), name: r.scenario_name.length > 40 ? r.scenario_name.slice(0, 38) + '…' : r.scenario_name, fill: i ? 'none' : 'toself', line: { color: U.PAL[i] }, opacity: 0.9 }; }),
      { height: 420, paper_bgcolor: 'rgba(0,0,0,0)', font: { size: 11 }, margin: { l: 60, r: 60, t: 30, b: 30 }, polar: { radialaxis: { range: [0, 1], tickfont: { size: 9 } }, angularaxis: { tickfont: { size: 9.5 } } }, legend: { orientation: 'h', y: -0.15, font: { size: 10.5 } }, showlegend: true });
  }
  U.pages.kpi = function (v) {
    var st = state(), on = A.live();
    v.innerHTML = U.head('FR5 — konfiqurasiya edilə bilən KPI kataloqu', 'KPI və qiymətləndirmə', 'Ssenariləri sizin seçdiyiniz əsas göstəricilər (KPI) üzrə müqayisə edin: ən azı 5 KPI seçin, çəkiləri verin — reytinq və xərc-effektivlik dərhal yenilənir.') +
      '<div class="cols2" style="grid-template-columns:minmax(0,1.3fr) minmax(0,1fr)"><div class="card pad"><h3>KPI seçimi və çəkilər</h3><div id="k-cnt" class="small"></div><div class="toolbar" style="margin:6px 0"><button class="btn sm" id="k-def">Standart seçim</button><button class="btn sm ghost" id="k-all">Hamısı</button><button class="btn sm ghost" id="k-eq">Çəkiləri bərabərləşdir</button>' + (on ? '<button class="btn sm" id="k-srv">' + (A.online ? 'Serverdə müqayisə et' : 'Brauzerdə müqayisə et (Python)') + '</button>' + (A.online ? '<button class="btn sm ghost" id="k-save">Dəsti serverdə saxla</button>' : '') : '') + '</div>' + picker(st) + '</div>' +
      '<div class="card pad"><h3>Ssenarilər</h3><div class="chips" style="flex-direction:column;align-items:flex-start">' + U.official().map(function (s) { return '<label class="ck"><input type="checkbox" data-s="' + U.esc(s.id) + '"' + (st.sc.indexOf(s.id) >= 0 ? ' checked' : '') + '> ' + U.esc(s.name) + '</label>'; }).join('') + st.sc.filter(function (x) { return !U.official().some(function (s) { return s.id === x; }); }).map(function (x) { return '<label class="ck"><input type="checkbox" data-s="' + U.esc(x) + '" checked> ' + U.esc(U.sname(x)) + ' <span class="chip warn" title="yalnız «Serverdə müqayisə et» ilə">qaralama</span></label>'; }).join('') + '</div><div id="k-srvres"></div></div></div>' +
      '<div id="k-res"></div>' +
      U.sec('Son hesablamanın nəticəsi', 'standart KPI seçimi ilə (P5_*), FR4 girişləri (P4_kpi_inputs)', '<div class="expl">' + U.esc(U.CONS_TXT) + '</div>' + U.dt('k-p5r', U.T('P5_ranking'), [{ k: 'rank', l: 'Yer (standart)', n: 1 }, { k: 'rank_conservative', l: 'Yer (ehtiyatlı)', n: 1 }, { k: 'scenario_name', l: 'Ssenari' }, { k: 'score', l: 'Bal', n: 1, d: 3 }, { k: 'score_conservative', l: 'Ehtiyatlı bal', n: 1, d: 3 }, { k: 'complete', l: 'Tam', f: function (x) { return x === false || x === 'False' ? '<span class="chip warn">natamam</span>' : 'bəli'; } }, { k: 'kpis_used', l: 'KPI', n: 1 }, { k: 'cost_mln_azn', l: 'Xərc, mln AZN', n: 1, d: 0 }, { k: 'score_per_bn_azn', l: 'Bal / 1 mlrd AZN', n: 1, d: 3 }, { k: 'note_az', l: 'Qeyd' }], { title: 'P5 reytinqi: standart və ehtiyatlı', file: 'P5_ranking' }) + U.dt('k-p5v', U.T('P5_kpi_values'), null, { title: 'P5 KPI dəyərləri', file: 'P5_kpi_values', lim: 40 }) + (window.POL.risk ? U.dt('k-p4', U.T('P4_kpi_inputs'), null, { title: 'FR4 → FR5 girişləri', file: 'P4_kpi_inputs', lim: 30 }) : '<div id="k-p4w"></div>') +
        U.dt('k-cat', U.T('P5_kpi_catalogue'), [{ k: 'id', l: 'Kod' }, { k: 'name_az', l: 'KPI' }, { k: 'formula', l: 'Düstur' }, { k: 'horizon', l: 'Müddət' }, { k: 'unit', l: 'Vahid' }, { k: 'direction', l: 'İstiqamət' }, { k: 'default_weight', l: 'Çəki', n: 1 }, { k: 'source_engine', l: 'Mənbə' }, { k: 'description_az', l: 'Təsvir' }], { title: 'KPI kataloqu (config/kpi.csv)', file: 'kpi_kataloqu' }));
    var save = function () { U.ls(KEY, JSON.stringify(st)); results(v, st); };
    results(v, st);
    if (!window.POL.risk) U.lazy('risk').then(function () { var w = U.$('#k-p4w', v); if (w) { w.outerHTML = U.dt('k-p4', U.T('P4_kpi_inputs'), null, { title: 'FR4 → FR5 girişləri', file: 'P4_kpi_inputs', lim: 30 }); results(v, st); } }, function () { /* optional */ });
    v.onchange = function (e) {
      var t = e.target, d = t.dataset;
      if (d.k) { var i = st.sel.indexOf(d.k); if (t.checked && i < 0) st.sel.push(d.k); if (!t.checked && i >= 0) st.sel.splice(i, 1); var lb = t.closest('label'); lb.classList.toggle('on', t.checked); U.$('[data-w]', lb).disabled = !t.checked; }
      else if (d.w) st.w[d.w] = Math.max(0, U.parseNum(t.value) || 0);
      else if (d.s) { var j = st.sc.indexOf(d.s); if (t.checked && j < 0) st.sc.push(d.s); if (!t.checked && j >= 0) st.sc.splice(j, 1); } else return;
      save();
    };
    v.onclick = function (e) {
      var b = e.target.closest('button'); if (!b) return;
      if (b.id === 'k-def') { U.ls(KEY, null); U.route(true); } else if (b.id === 'k-all') { st.sel = U.T('P5_kpi_catalogue').map(function (k) { return k.id; }); U.ls(KEY, JSON.stringify(st)); U.route(true); }
      else if (b.id === 'k-eq') { Object.keys(st.w).forEach(function (k) { st.w[k] = 1; }); U.ls(KEY, JSON.stringify(st)); U.route(true); }
      else if (b.id === 'k-srv' || b.id === 'k-save') {
        if (st.sel.length < MIN) { U.toast('Ən azı ' + MIN + ' KPI seçin'); return; }
        var w = {}; st.sel.forEach(function (k) { w[k] = st.w[k]; });
        if (b.id === 'k-srv' && !A.online) U.$('#k-srvres', v).innerHTML = '<p class="small muted">Brauzerdə hesablanır: ' + st.sc.length + ' ssenari (Python; hər biri ≈ 3–6 s, ilk dəfə mühit də yüklənir)…</p>';
        var p = b.id === 'k-save' ? A.kpiSave({ name: 'Panel seçimi ' + new Date().toISOString().slice(0, 16).replace('T', ' '), kpis: st.sel, weights: w }).then(function () { U.toast('KPI dəsti saxlanıldı'); })
          : A.compare({ scenarios: st.sc, kpis: st.sel, weights: w, _local: U.localScen ? U.localScen(st.sc) : undefined }).then(function (r) { U.$('#k-srvres', v).innerHTML = (r.text_az ? '<div class="expl">' + U.esc(r.text_az) + '</div>' : '') + U.dt('k-srvr', r.ranking || [], null, { title: (A.lastVia === 'brauzer' ? 'Brauzer reytinqi (Python, cari vintaj)' : 'Server reytinqi (cari vintaj)'), file: 'server_reytinq' }); });
        p.catch(function (er) { U.$('#k-srvres', v).innerHTML = A.failHtml('Müqayisə', er); });
      }
    };
  };
})();
