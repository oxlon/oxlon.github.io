/* chart.js — Plotly charts in the panel's look: history, forecast per scenario, 5–95 % band, forecast shading. */
(function () {
  'use strict';
  var U = window.U;
  var FONT = '"Helvetica Neue", Helvetica, Arial, sans-serif';
  U.layout = function (ytitle, x0, opts) {
    opts = opts || {};
    var lay = {
      height: opts.h || 380, autosize: true, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
      font: { family: FONT, size: 12.5, color: '#15202B' }, separators: ', ', hovermode: 'x unified',
      margin: { l: 62, r: 18, t: 44, b: 40 },
      legend: { orientation: 'h', traceorder: 'normal', y: 1.02, yanchor: 'bottom', x: 0, xanchor: 'left', font: { size: 12, color: '#455463' } },
      xaxis: { gridcolor: '#EDF1F4', zeroline: false, tickformat: 'd', range: [x0 - 0.5, 2030.5], fixedrange: true },
      yaxis: { gridcolor: '#EDF1F4', zeroline: false, title: { text: ytitle || '', font: { size: 12, color: '#738190' } },
        separatethousands: true, exponentformat: 'none', fixedrange: true }
    };
    if (!opts.noFc) {
      lay.shapes = [{ type: 'rect', xref: 'x', yref: 'paper', layer: 'below', x0: 2025.5, x1: 2030.5, y0: 0, y1: 1, fillcolor: '#F2F7FB', line: { width: 0 } },
        { type: 'line', xref: 'x', yref: 'paper', x0: 2025.5, x1: 2025.5, y0: 0, y1: 1, line: { color: '#B8C2C4', width: 1, dash: 'dot' } }];
      lay.annotations = [{ text: 'Proqnoz 2026–2030', showarrow: false, xref: 'x', yref: 'paper', x: 2025.7, y: 1, xanchor: 'left', yanchor: 'top', font: { size: 11, color: '#738190' } }];
    }
    return lay;
  };
  U.plot = function (el, data, lay) {
    if (!window.Plotly) { el.textContent = 'Qrafik kitabxanası yüklənmədi'; return; }
    window.Plotly.newPlot(el, data, lay, { displaylogo: false, responsive: true, displayModeBar: false });
  };
  var RANK = 0;
  function tr(x, y, name, col, dash, w, extra) {
    var t = { type: 'scatter', mode: 'lines', x: x, y: y, name: name, line: { color: col, dash: dash || 'solid', width: w || 2.4 }, connectgaps: false };
    for (var k in extra || {}) t[k] = extra[k];
    t.legendrank = ++RANK;
    return t;
  }
  U.seriesChart = function (el, s, opt) {
    opt = opt || {};
    var raw = U.scenRaw(), act = U.scen(), d = s.d, data = [], hfmt = '%{y:,.' + Math.min(d, 3) + 'f}';
    var hx = [], hy = [];
    (s.h || []).forEach(function (p, i, a) { if (i && p[0] - a[i - 1][0] > 1) { hx.push(p[0] - 1); hy.push(null); } hx.push(p[0]); hy.push(p[1]); });
    if (s.q) {
      data.push(tr(U.YEARS, s.q[1], '5–95 % zolağı (yuxarı)', 'rgba(14,111,124,0)', 'solid', 0, { showlegend: false, hoverinfo: 'skip' }));
      data.push(tr(U.YEARS, s.q[0], '5–95 % zolağı (Əsas)', 'rgba(14,111,124,0)', 'solid', 0, { fill: 'tonexty', fillcolor: 'rgba(14,111,124,0.14)', hoverinfo: 'skip' }));
    }
    if (hx.length) data.push(tr(hx, hy, 'Faktiki', '#455463', 'solid', 2.2, { mode: hx.length < 4 ? 'lines+markers' : 'lines', hovertemplate: hfmt }));
    var show = raw === 'all' ? U.scens(s) : U.scens(s).filter(function (k) { return k === act || k === 'B'; });
    show.forEach(function (k) {
      var on = raw === 'all' || k === act;
      var x = U.isNum(s.b) ? [2025].concat(U.YEARS) : U.YEARS, y = U.isNum(s.b) ? [s.b].concat(s.s[k]) : s.s[k];
      data.push(tr(x, y, U.SCN[k] + ' ssenari', U.SCC[k], U.SCD[k], on ? 2.8 : 1.4,
        { mode: 'lines+markers', marker: { size: on ? 6 : 4 }, opacity: on ? 1 : 0.55, hovertemplate: hfmt }));
    });
    var x0 = hx.length ? Math.max(hx[0], 2030 - (opt.span || 21)) : 2024;
    U.plot(el, data, U.layout(s.u, x0, { h: opt.h }));
  };
})();
