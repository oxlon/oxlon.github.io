/* synth12.js — FR12 Layer B: entry counts (Poisson / NegBin, IRR), exit hazard (logit / cloglog, OR), survival curves,
   cohorts, Boone competition slopes and parameter recovery. */
(function () {
  'use strict';
  var U = window.U, SEL = null, PAR = { small: 'kiçik müəssisə (ölçü qrupu)', medium: 'orta müəssisə (ölçü qrupu)', large: 'iri müəssisə (ölçü qrupu)' };
  function n(v, d) { return U.isNum(v) ? U.nf(v, d) : '—'; }
  function ctbl(rows) {
    return '<table class="itbl"><thead><tr><th class="l">İzahedici dəyişən</th><th class="l">Növ</th><th>Əmsal</th><th>Standart xəta</th><th>z</th><th>p-dəyəri</th><th>Nisbət</th><th>95 % EI (nisbət)</th></tr></thead><tbody>' +
      rows.map(function (r) { return '<tr><td class="lab">' + U.esc(r.term_az || r.term) + '<span class="u">' + U.esc(r.term) + '</span></td><td class="small">' + U.esc(r.term_type || '') + '</td><td class="n"><b>' + U.sig(r.coef) + '</b></td><td class="n">' + U.sig(r.se) + '</td><td class="n">' + n(r.z, 2) + '</td><td class="n">' + U.pf(r.p) + '</td>' +
        '<td class="n">' + (U.isNum(r.ratio) ? U.sig(r.ratio) + ' <span class="u">' + U.esc(r.ratio_type || '') + '</span>' : '—') + '</td><td class="n">' + (U.isNum(r.ratio_ci_low) ? '[' + U.sig(r.ratio_ci_low) + '; ' + U.sig(r.ratio_ci_high) + ']' : '—') + '</td></tr>'; }).join('') + '</tbody></table>';
  }
  function ratioChart(el, rows, xt) {
    rows = rows.filter(function (r) { return U.isNum(r.ratio) && !/sabit/.test(r.term_type || ''); });
    U.barH(el, rows.map(function (r) { return r.term_az || r.term; }), rows.map(function (r) { return r.ratio - 1; }), xt, { color: '#1F6FB2', err: [rows.map(function (r) { return r.ratio - r.ratio_ci_low; }), rows.map(function (r) { return r.ratio_ci_high - r.ratio; })] });
  }
  U.syn12 = function (el) {
    var D = (window.MICRO.SYNE || {}).FR12;
    if (!D || !D.summary.length) { el.innerHTML = '<p class="muted">FR12 B qatının ekonometrik nəticələri tapılmadı.</p>'; return; }
    if (!SEL) SEL = D.summary[0].model;
    var m = D.summary.filter(function (x) { return x.model === SEL; })[0] || D.summary[0];
    var coh = {}; (D.surv || []).forEach(function (r) { (coh[r.cohort] = coh[r.cohort] || []).push(r); });
    el.innerHTML = '<section class="sec"><div class="sec-h"><h2>FR12: müəssisə səviyyəsində modellər (' + D.summary.length + ')</h2><p>Karta klikləyin — əmsallar və nisbətlər (IRR — gözlənilən say nisbəti, OR — şans nisbəti) aşağıda.</p></div>' +
      '<div class="kpis syncards">' + D.summary.map(function (s) { return '<button type="button" class="kpi' + (s.model === SEL ? ' on' : '') + '" data-m="' + U.esc(s.model) + '"><div style="font-weight:700;font-size:14px">' + U.esc(s.model_az) + '</div><div class="small muted">' + n(s.n, 0) + ' müşahidə</div><div class="small" style="margin-top:4px">' + U.esc(s.interpretation_az || '') + '</div></button>'; }).join('') + '</div>' +
      '<div class="card pad" style="margin-top:14px"><h2 class="mh">' + U.esc(m.model_az) + '</h2><p class="small">' + U.esc(m.interpretation_az || '') + '</p><div class="itbl-wrap">' + ctbl(D.coef[m.model] || []) + '</div></div></section>' +
      '<section class="sec"><div class="sec-h"><h2>Giriş və çıxış: təsirlər</h2><p>Zolaq — nisbət − 1 (0 — təsir yoxdur), xətt — 95 % etibarlılıq intervalı.</p></div><div class="grid g2w"><div class="card pad"><h4>Girişlərin sayı: IRR − 1</h4><div id="sy-irr"></div></div><div class="card pad"><h4>Çıxış təhlükəsi: OR − 1</h4><div id="sy-or"></div></div></div></section>' +
      '<section class="sec"><div class="sec-h"><h2>Sağ qalma: Kaplan–Meyer və təhlükə modelləri</h2></div><div class="card pad"><div class="toolbar" style="margin-top:0"><label class="small muted">Kohort</label><select id="sy-coh" class="btn sm">' +
      Object.keys(coh).map(function (c) { return U.opt(c, c, Object.keys(coh)[0]); }).join('') + '</select></div><div id="sy-surv"></div></div></section>' +
      '<section class="sec"><div class="sec-h"><h2>Boone rəqabət göstəricisi</h2><p>Mənfəət ilə səmərəlilik arasındakı meyl: daha mənfi β — daha sərt rəqabət. Bölmələr üzrə, illər boyu.</p></div><div class="card pad"><div id="sy-boone"></div></div></section>' +
      '<section class="sec"><div class="sec-h"><h2>Parametrlərin bərpası</h2></div><div class="card itbl-wrap"><table class="itbl"><thead><tr><th class="l">Blok</th><th class="l">Parametr</th><th>Həqiqi</th><th>Qiymətləndirmə</th><th>95 % EI</th><th>Örtük</th></tr></thead><tbody>' +
      (D.rec || []).map(function (r) { return '<tr><td class="small" style="white-space:normal">' + U.esc(r.block) + '</td><td class="lab">' + U.esc(PAR[r.parameter] || r.parameter) + (PAR[r.parameter] ? '<span class="u">' + U.esc(r.parameter) + '</span>' : '') + '</td><td class="n">' + U.sig(r.true) + '</td><td class="n">' + U.sig(r.estimate) + '</td><td class="n">[' + U.sig(r.ci_low) + '; ' + U.sig(r.ci_high) + ']</td><td>' +
        (r.covered === true || r.covered === 'True' ? '<span class="chip acc">bəli</span>' : '<span class="chip bad">xeyr</span>') + '</td></tr>'; }).join('') + '</tbody></table></div>' +
      ((D.nodef || []).length ? '<ul class="small">' + D.nodef.map(function (r) { return '<li><b>' + U.esc(r.model) + '</b>: ' + U.esc(r.why_no_true_parameter_az) + '</li>'; }).join('') + '</ul>' : '') + '</section>';
    ratioChart(U.$('#sy-irr'), D.entry || [], 'IRR − 1');
    ratioChart(U.$('#sy-or'), D.exit || [], 'OR − 1');
    var drawS = function (c) {
      var r = coh[c] || [];
      U.lines(U.$('#sy-surv'), [{ x: r.map(function (x) { return x.age; }), y: r.map(function (x) { return x.km_survival; }), name: 'Kaplan–Meyer', c: '#455463', shape: 'hv' },
        { x: r.map(function (x) { return x.age; }), y: r.map(function (x) { return x.pred_logit; }), name: 'logit modeli', c: '#0E6F7C', dash: 'dash' },
        { x: r.map(function (x) { return x.age; }), y: r.map(function (x) { return x.pred_cloglog; }), name: 'cloglog modeli', c: '#E07B00', dash: 'dot' }], 'sağ qalma payı', { h: 300, xt: 'yaş, il' });
    };
    var cs = U.$('#sy-coh'); if (cs) { drawS(cs.value); cs.onchange = function () { drawS(cs.value); }; }
    var by = {}; (D.boone || []).forEach(function (r) { (by[r.section] = by[r.section] || []).push(r); });
    var pal = ['#0E6F7C', '#1F6FB2', '#B3261E', '#E07B00', '#6A3FB5', '#1E7B4F', '#8A5300', '#455463'];
    U.lines(U.$('#sy-boone'), Object.keys(by).map(function (k, i) { return { x: by[k].map(function (r) { return r.year; }), y: by[k].map(function (r) { return r.boone_beta; }), name: 'bölmə ' + k, c: pal[i % pal.length], w: 1.6 }; }), 'Boone β', { h: 360, xt: 'il' });
    el.onclick = function (e) { var b = e.target.closest('[data-m]'); if (b) { SEL = b.getAttribute('data-m'); U.syn12(el); } };
  };
})();
