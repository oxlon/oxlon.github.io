/* eqcharts.js — charts inside the regression-output dialog: recursive coefficient path (± 1,96 standart xəta,
   full-sample estimate, leave-one-out range), fitted vs actual, residuals. */
(function () {
  'use strict';
  var U = window.U;
  function recChart(e, k) {
    var r = e.rb.rec, y = r.y, c = (r.c || {})[k] || [], se = (r.se || {})[k] || [];
    var full = null; e.co.forEach(function (x) { if (x.n === k) full = x.c; });
    var lo = c.map(function (v, i) { return U.isNum(v) && U.isNum(se[i]) ? v - 1.96 * se[i] : null; });
    var hi = c.map(function (v, i) { return U.isNum(v) && U.isNum(se[i]) ? v + 1.96 * se[i] : null; });
    var data = [];
    if (se.length) {
      data.push({ type: 'scatter', mode: 'lines', x: y, y: hi, line: { width: 0 }, showlegend: false, hoverinfo: 'skip' });
      data.push({ type: 'scatter', mode: 'lines', x: y, y: lo, line: { width: 0 }, fill: 'tonexty', fillcolor: 'rgba(31,111,178,0.15)', name: '± 1,96 standart xəta', hoverinfo: 'skip' });
    }
    data.push({ type: 'scatter', mode: 'lines+markers', x: y, y: c, name: 'Rekursiv qiymətləndirmə', line: { color: '#1F6FB2', width: 2.4 } });
    if (U.isNum(full)) data.push({ type: 'scatter', mode: 'lines', x: [y[0], y[y.length - 1]], y: [full, full], name: 'Tam nümunə', line: { color: '#455463', dash: 'dash', width: 1.6 } });
    var loo = (e.rb.loo || {})[k];
    var lay = U.layout('əmsal: ' + k, 0, { noFc: true, h: 280, xt: 'nümunənin son ili' });
    lay.xaxis.range = null; lay.xaxis.autorange = true; lay.xaxis.dtick = y.length <= 15 ? 1 : null;
    if (loo && U.isNum(loo[0])) {
      lay.shapes = [{ type: 'rect', xref: 'paper', yref: 'y', x0: 0, x1: 1, y0: loo[0], y1: loo[1], fillcolor: 'rgba(224,123,0,0.10)', line: { width: 0 }, layer: 'below' }];
      lay.annotations = [{ text: 'bir ili çıxarmaqla aralıq', xref: 'paper', yref: 'y', x: 1, y: loo[1], xanchor: 'right', yanchor: 'bottom', showarrow: false, font: { size: 11, color: '#8A5300' } }];
    }
    lay.shapes = (lay.shapes || []).concat([{ type: 'line', xref: 'paper', yref: 'y', x0: 0, x1: 1, y0: 0, y1: 0, line: { color: '#B8C2C4', width: 1 } }]);
    U.plot(U.$('#eq-rec'), data, lay);
  }
  U.eqCharts = function (e) {
    var sel = U.$('#eq-rc');
    if (sel) {
      var ks = Object.keys(e.rb.rec.c || {}), pref = ks.filter(function (k) { return k !== 'const'; });
      if (pref.length) sel.value = pref[0];
      recChart(e, sel.value);
      sel.onchange = function () { recChart(e, sel.value); };
    }
    var f = e.fv;
    if (!f || !f.y) { var el = U.$('#eq-fit'); if (el) el.innerHTML = '<p class="small muted">Bu tənlik üçün qiymətləndirilmiş sıra ixrac olunmayıb.</p>'; return; }
    var lay = U.layout(e.dep.l || e.dep.c, 0, { noFc: true, h: 300 });
    lay.xaxis.range = null; lay.xaxis.autorange = true; lay.xaxis.dtick = f.y.length <= 15 ? 1 : null;
    U.plot(U.$('#eq-fit'), [
      { type: 'scatter', mode: 'lines+markers', x: f.y, y: f.a, name: 'Faktiki', line: { color: '#455463', width: 2.2 }, marker: { size: 5 } },
      { type: 'scatter', mode: 'lines', x: f.y, y: f.f, name: 'Qiymətləndirilmiş', line: { color: '#0E6F7C', width: 2.4, dash: 'dash' } }], lay);
    var l2 = U.layout('qalıq', 0, { noFc: true, h: 220 });
    l2.xaxis.range = null; l2.xaxis.autorange = true; l2.showlegend = false; l2.xaxis.dtick = f.y.length <= 15 ? 1 : null;
    l2.shapes = [{ type: 'line', xref: 'paper', yref: 'y', x0: 0, x1: 1, y0: 0, y1: 0, line: { color: '#738190', width: 1 } }];
    U.plot(U.$('#eq-res'), [{ type: 'bar', x: f.y, y: f.r, name: 'Qalıq', marker: { color: (f.r || []).map(function (v) { return v >= 0 ? '#1E7B4F' : '#B3261E'; }) } }], l2);
  };
})();
