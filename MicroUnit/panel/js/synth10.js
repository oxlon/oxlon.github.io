/* synth10.js — FR10 Layer B: firm-level models (profitability, production function, TFP, distress, investment, market
   share, export): model cards, coefficient tables, marginal effects, ROC and calibration, parameter recovery. */
(function () {
  'use strict';
  var U = window.U, SEL = null;
  function n(v, d) { return U.isNum(v) ? U.nf(v, d) : '—'; }
  function coefTbl(rows, tcol) {
    return '<table class="itbl"><thead><tr><th class="l">İzahedici dəyişən</th><th>Əmsal</th><th>Standart xəta</th><th>' + (tcol || 't') + '</th><th>p-dəyəri</th><th>95 % etibarlılıq intervalı</th></tr></thead><tbody>' +
      rows.map(function (r) { return '<tr><td class="lab">' + U.esc(r.term_az || r.term) + '<span class="u">' + U.esc(r.term || '') + '</span></td><td class="n"><b>' + U.sig(r.coef != null ? r.coef : r.ame) + '</b></td><td class="n">' + U.sig(r.se) + '</td><td class="n">' + n(r.t != null ? r.t : r.z, 2) + '</td><td class="n">' + U.pf(r.p) + '</td><td class="n">[' + U.sig(r.ci_low) + '; ' + U.sig(r.ci_high) + ']</td></tr>'; }).join('') + '</tbody></table>';
  }
  function card(m) {
    var fit = m.auc != null ? 'AUC ' + n(m.auc, 3) : m.r2 != null ? 'R² ' + n(m.r2, 3) + (m.r2_type ? ' (' + U.esc(m.r2_type) + ')' : '') : m.RTS != null ? 'miqyas effekti ' + n(m.RTS, 3) : '';
    return '<button type="button" class="kpi' + (SEL === m.model_id ? ' on' : '') + '" data-m="' + U.esc(m.model_id) + '"><div class="l">' + U.esc(m.block || '') + '</div><div style="font-weight:700;font-size:14px">' + U.esc(m.title_az) + '</div>' +
      '<div class="small muted">' + U.esc(m.estimator || '') + '</div><div class="small">' + n(m.n_obs, 0) + ' müşahidə · ' + n(m.n_firms, 0) + ' müəssisə · ' + (m.year_min || '') + '–' + (m.year_max || '') + '</div><div class="d flat">' + fit + '</div></button>';
  }
  function detail(D, m) {
    var id = m.model_id, co = D.coef[id] || [], h = '<div class="card pad" style="margin-top:14px"><div class="eyebrow">' + U.esc(m.block || '') + '</div><h2 class="mh">' + U.esc(m.title_az) + '</h2>' +
      '<p class="small">' + U.esc(m.estimator || '') + ' · asılı dəyişən <code>' + U.esc(m.dependent || '') + '</code> · ' + n(m.n_obs, 0) + ' müşahidə, ' + n(m.n_firms, 0) + ' müəssisə, ' + n(m.n_clusters, 0) + ' klaster</p>' +
      (D.interp[id] ? '<p class="small" style="background:var(--surface-2);padding:8px 10px;border-radius:8px">' + U.esc(D.interp[id]) + '</p>' : '') +
      '<div class="itbl-wrap">' + coefTbl(co) + '</div><div class="grid g3" style="margin-top:10px">' +
      [['R²', m.r2, 3], ['Düzəldilmiş R²', m.r2_adj, 3], ['Reqressiyanın standart xətası', m.ser, 4], ['Wald F (p)', m.wald_F, 2, m.wald_F_p], ['Log-həqiqətəbənzərlik', m.loglik, 1], ['LR χ² (p)', m.lr_chi2, 1, m.lr_p],
        ['AIC / BIC', m.aic, 1, null, m.bic], ['AUC (nümunə daxilində / kənar)', m.auc, 3, null, m.auc_oos], ['Brier balı', m.brier, 4], ['Hosmer–Lemeshow (p)', m.hosmer_lemeshow, 2, m.hosmer_lemeshow_p], ['Hadisə tezliyi', m.event_rate, 4], ['Miqyas effekti (RTS)', m.RTS, 3]]
        .filter(function (r) { return U.isNum(r[1]); }).map(function (r) { return '<div class="kv1"><span>' + r[0] + '</span><b>' + n(r[1], r[2]) + (U.isNum(r[4]) ? ' / ' + n(r[4], r[2]) : '') + (U.isNum(r[3]) ? ' (p ' + U.pf(r[3]) + ')' : '') + '</b></div>'; }).join('') + '</div>';
    var kind = /distress/.test(id) ? 'distress' : /export/.test(id) ? 'export' : null;
    if (kind) {
      h += '<div class="grid g2w" style="margin-top:12px"><div><h4>Orta marjinal effektlər</h4><div class="itbl-wrap">' + coefTbl(D.ame[kind] || [], 'z') + '</div><div id="sy-ame"></div></div>' +
        '<div><h4>ROC əyrisi</h4><div id="sy-roc"></div><h4>Kalibrləmə (desillər)</h4><div id="sy-cal"></div></div></div>';
    }
    var pf = (D.pf || []).filter(function (r) { return r.model_id === id; })[0];
    if (pf) h += '<p class="small">Miqyas effekti (βL + βK): <b>' + n(pf.RTS, 3) + '</b> [' + n(pf.ci_low, 3) + '; ' + n(pf.ci_high, 3) + '] · sabit gəlir testi: Wald F = ' + n(pf.crs_wald_F, 1) + ', p ' + U.pf(pf.crs_p) + '</p>';
    var rec = (D.rec || []).filter(function (r) { return r.model_id === id; });
    if (rec.length) h += '<h4>Parametrlərin bərpası (generatorun həqiqi dəyərləri ilə müqayisə)</h4><div class="itbl-wrap"><table class="itbl"><thead><tr><th class="l">Parametr</th><th>Həqiqi</th><th>Qiymətləndirmə</th><th>95 % EI</th><th>Örtük</th><th class="l">Qeyd</th></tr></thead><tbody>' +
      rec.map(function (r) { return '<tr><td class="lab">' + U.esc(r.term_az || r.term) + '</td><td class="n">' + U.sig(r.true) + '</td><td class="n">' + U.sig(r.estimate) + '</td><td class="n">' + (U.isNum(r.ci_low) ? '[' + U.sig(r.ci_low) + '; ' + U.sig(r.ci_high) + ']' : '—') + '</td><td>' +
        (r.covered === true || r.covered === 'True' ? '<span class="chip acc">bəli</span>' : r.covered === false || r.covered === 'False' ? '<span class="chip bad">xeyr</span>' : '—') + '</td><td class="small" style="white-space:normal">' + U.esc(r.note_az || '') + '</td></tr>'; }).join('') + '</tbody></table></div>';
    return h + '</div>';
  }
  function charts(D, m) {
    var kind = /distress/.test(m.model_id) ? 'distress' : /export/.test(m.model_id) ? 'export' : null;
    if (!kind) return;
    var a = D.ame[kind] || [];
    U.barH(U.$('#sy-ame'), a.map(function (r) { return r.term_az || r.term; }), a.map(function (r) { return r.ame; }), 'orta marjinal effekt (ehtimal)', { color: '#1F6FB2', err: [a.map(function (r) { return r.ame - r.ci_low; }), a.map(function (r) { return r.ci_high - r.ame; })] });
    var roc = D.roc[kind] || {}, cols = ['#0E6F7C', '#E07B00'];
    U.lines(U.$('#sy-roc'), Object.keys(roc).map(function (k, i) { return { x: roc[k].fpr, y: roc[k].tpr, name: k, c: cols[i % 2], mode: 'lines' }; }).concat([{ x: [0, 1], y: [0, 1], name: 'təsadüfi təsnifat', c: '#B8C2C4', dash: 'dot', mode: 'lines' }]), 'həqiqi müsbət nisbəti', { h: 280, xfmt: '.1f', xt: 'yalan müsbət nisbəti' });
    var cal = D.cal[kind] || [], by = {};
    cal.forEach(function (r) { (by[r.sample] = by[r.sample] || []).push(r); });
    U.lines(U.$('#sy-cal'), Object.keys(by).map(function (k, i) { return { x: by[k].map(function (r) { return r.mean_predicted; }), y: by[k].map(function (r) { return r.observed_rate; }), name: k, c: cols[i % 2] }; })
      .concat([{ x: [0, 1], y: [0, 1], name: 'mükəmməl kalibrləmə', c: '#B8C2C4', dash: 'dot', mode: 'lines' }]), 'müşahidə olunan tezlik', { h: 260, xfmt: '.2f', xt: 'proqnozlaşdırılan ehtimal' });
  }
  U.syn10 = function (el) {
    var D = (window.MICRO.SYNE || {}).FR10;
    if (!D || !D.models.length) { el.innerHTML = '<p class="muted">FR10 B qatının ekonometrik nəticələri tapılmadı.</p>'; return; }
    if (!SEL) SEL = D.models[0].model_id;
    var m = D.models.filter(function (x) { return x.model_id === SEL; })[0] || D.models[0];
    el.innerHTML = '<section class="sec"><div class="sec-h"><h2>FR10: müəssisə səviyyəsində modellər (' + D.models.length + ')</h2><p>Karta klikləyin — əmsallar, uyğunluq, marjinal effektlər və parametrlərin bərpası aşağıda açılır.</p></div>' +
      '<div class="kpis syncards">' + D.models.map(card).join('') + '</div>' + detail(D, m) + '</section>' +
      '<section class="sec"><div class="sec-h"><h2>Monte-Karlo: qiymətləndiricilərin ardıcıllığı</h2><p>Generator dəfələrlə təkrarlanır; orta qiymətləndirmə həqiqi dəyərə yaxın olmalı, 95 % EI örtüyü ≈ 0,95.</p></div><div class="card itbl-wrap"><table class="itbl"><thead><tr><th class="l">Model / parametr</th><th>Həqiqi</th><th>Orta təxmin</th><th>MK st. sapma</th><th>Orta st. xəta</th><th>Örtük</th><th>Təkrar</th></tr></thead><tbody>' +
      (D.mc || []).map(function (r) { return '<tr><td class="lab">' + U.esc(r.term_az || r.term) + '<span class="u">' + U.esc(r.model_id) + '</span></td><td class="n">' + U.sig(r.true) + '</td><td class="n">' + U.sig(r.mean_estimate) + '</td><td class="n">' + U.sig(r.mc_sd) + '</td><td class="n">' + U.sig(r.mean_se) + '</td><td class="n">' + n(r.coverage_95, 2) + '</td><td class="n">' + n(r.reps, 0) + '</td></tr>'; }).join('') + '</tbody></table></div></section>' +
      '<details class="faq"><summary>Nümunə qaydaları</summary><ul class="small">' + (D.rules || []).map(function (r) { return '<li><b>' + U.esc(r.scope_az) + '</b>: ' + U.esc(r.rule_az) + '</li>'; }).join('') + '</ul></details>';
    charts(D, m);
    el.onclick = function (e) { var b = e.target.closest('[data-m]'); if (b) { SEL = b.getAttribute('data-m'); U.syn10(el); } };
  };
})();
