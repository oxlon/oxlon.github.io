/* chart.js — Plotly charts in the panel's look: history (imputed points hollow + dashed), forecast per scenario,
   5–95 % band, forecast shading; comparison, tornado and generic helpers. Axis titles and legends in Azerbaijani. */
(function () {
  'use strict';
  var U = window.U;
  var FONT = '"Helvetica Neue", Helvetica, Arial, sans-serif';
  U.IMPLAB = 'Doldurulmuş (interpolyasiya)';
  U.layout = function (ytitle, x0, opts) {
    opts = opts || {};
    var lay = {
      height: opts.h || 380, autosize: true, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
      font: { family: FONT, size: 12.5, color: '#15202B' }, separators: ', ', hovermode: 'x unified',
      margin: { l: 62, r: 18, t: 44, b: 40 },
      legend: { orientation: 'h', traceorder: 'normal', y: 1.02, yanchor: 'bottom', x: 0, xanchor: 'left', font: { size: 12, color: '#455463' } },
      xaxis: { gridcolor: '#EDF1F4', zeroline: false, tickformat: 'd', range: [x0 - 0.5, 2030.5], fixedrange: true, title: { text: opts.xt || '' } },
      yaxis: { gridcolor: '#EDF1F4', zeroline: false, title: { text: ytitle || '', font: { size: 12, color: '#738190' } },
        separatethousands: true, exponentformat: 'none', fixedrange: true }
    };
    if (2030.5 - x0 <= 16) lay.xaxis.dtick = 1;
    if (!opts.noFc) {
      lay.shapes = [{ type: 'rect', xref: 'x', yref: 'paper', layer: 'below', x0: 2025.5, x1: 2030.5, y0: 0, y1: 1, fillcolor: '#F2F7FB', line: { width: 0 } },
        { type: 'line', xref: 'x', yref: 'paper', x0: 2025.5, x1: 2025.5, y0: 0, y1: 1, line: { color: '#B8C2C4', width: 1, dash: 'dot' } }];
      lay.annotations = [{ text: 'Proqnoz 2026–2030', showarrow: false, xref: 'x', yref: 'paper', x: 2025.7, y: 1, xanchor: 'left', yanchor: 'top', font: { size: 11, color: '#738190' } }];
    }
    return lay;
  };
  U.plot = function (el, data, lay) {
    if (!el) return;
    if (!window.Plotly) { el.textContent = 'Qrafik kitabxanası yüklənmədi'; return; }
    window.Plotly.newPlot(el, data, lay, { displaylogo: false, responsive: true, displayModeBar: false, locale: 'az' });
  };
  var RANK = 0;
  function tr(x, y, name, col, dash, w, extra) {
    var t = { type: 'scatter', mode: 'lines', x: x, y: y, name: name, line: { color: col, dash: dash || 'solid', width: w || 2.4 }, connectgaps: false };
    for (var k in extra || {}) t[k] = extra[k];
    t.legendrank = ++RANK;
    return t;
  }
  U.tr = tr;
  /* history traces: observed (solid, gaps at imputed points) + imputed runs (dashed, hollow markers) */
  U.histTraces = function (h, fmt, span) {
    var out = [], ox = [], oy = [], ix = [], iy = [], isz = [];
    h = (h || []).filter(function (p) { return p[0] >= 2030 - (span || 25); });
    h.forEach(function (p, i) {
      var prev = h[i - 1];
      if (prev && p[0] - prev[0] > 1) { ox.push(p[0] - 1); oy.push(null); }
      ox.push(p[0]); oy.push(p[2] ? null : p[1]);
    });
    h.forEach(function (p, i) {
      if (!p[2]) return;
      var a = h[i - 1], b = h[i + 1];
      if (a && !a[2] && (!ix.length || ix[ix.length - 1] !== a[0])) { if (ix.length) { ix.push(null); iy.push(null); isz.push(0); } ix.push(a[0]); iy.push(a[1]); isz.push(0); }
      ix.push(p[0]); iy.push(p[1]); isz.push(8);
      if (b && !b[2]) { ix.push(b[0]); iy.push(b[1]); isz.push(0); }
    });
    if (ox.length) out.push(tr(ox, oy, 'Faktiki', '#455463', 'solid', 2.2, { mode: ox.length < 4 ? 'lines+markers' : 'lines', hovertemplate: fmt }));
    if (ix.length) out.push(tr(ix, iy, U.IMPLAB, '#8A5300', 'dash', 1.8, { mode: 'lines+markers', hovertemplate: fmt,
      marker: { symbol: 'circle-open', size: isz, color: '#8A5300', line: { width: 2 } } }));
    return out;
  };
  U.seriesChart = function (el, s, opt) {
    opt = opt || {};
    var raw = opt.all ? 'all' : U.scenRaw(), act = U.scen(), d = s.d, data = [], fmt = '%{y:,.' + Math.min(d, 3) + 'f}';
    var q = s.q && (s.q[act] || s.q.B), qk = s.q && (s.q[act] ? act : 'B');
    if (q) {
      data.push(tr(U.YEARS, q[1], '5–95 % zolağı (yuxarı)', 'rgba(14,111,124,0)', 'solid', 0, { showlegend: false, hoverinfo: 'skip' }));
      data.push(tr(U.YEARS, q[0], '5–95 % zolağı (' + U.SCN[qk] + ')', 'rgba(14,111,124,0)', 'solid', 0, { fill: 'tonexty', fillcolor: 'rgba(14,111,124,0.14)', hoverinfo: 'skip' }));
    }
    data = data.concat(U.histTraces((s.h || []).filter(function (p) { return p[0] <= 2025; }), fmt, opt.span));
    var show = raw === 'all' ? U.scens(s) : U.scens(s).filter(function (k) { return k === act || k === 'B'; });
    show.forEach(function (k) {
      var on = raw === 'all' || k === act, b = U.b25(s, k);
      var x = U.isNum(b) ? [2025].concat(U.YEARS) : U.YEARS, y = U.isNum(b) ? [b].concat(s.s[k]) : s.s[k];
      data.push(tr(x, y, U.SCN[k] + ' ssenari', U.SCC[k], U.SCD[k], on ? 2.8 : 1.4,
        { mode: 'lines+markers', marker: { size: on ? 6 : 4 }, opacity: on ? 1 : 0.55, hovertemplate: fmt }));
    });
    var h0 = (s.h || [])[0], x0 = h0 ? Math.max(h0[0], 2030 - (opt.span || 21)) : 2024;
    U.plot(el, data, U.layout(s.u, x0, { h: opt.h }));
  };
  /* scenario vs reference: ref {label, y[5]}, alt {label, y[5]}, history of the base series */
  U.compareChart = function (el, s, ref, alt, opt) {
    opt = opt || {};
    var fmt = '%{y:,.' + Math.min(s.d, 3) + 'f}', data = U.histTraces((s.h || []).filter(function (p) { return p[0] <= 2025; }), fmt, 12);
    var b = U.b25(s, 'B'), x = U.isNum(b) ? [2025].concat(U.YEARS) : U.YEARS;
    var pre = function (y) { return U.isNum(b) ? [b].concat(y) : y; };
    data.push(tr(x, pre(ref.y), ref.label, U.SCC[ref.k || 'B'], 'solid', 2.4, { mode: 'lines+markers', hovertemplate: fmt }));
    data.push(tr(x, pre(alt.y), alt.label, U.SCC.C, 'dash', 2.8, { mode: 'lines+markers', marker: { size: 7 }, hovertemplate: fmt }));
    U.plot(el, data, U.layout(s.u, 2014, { h: opt.h || 340 }));
  };
  /* tornado: rows [{l, emin, epl}] — % change of the 2030 value when the coefficient moves −/+ 1 SE */
  U.tornado = function (el, rows, opt) {
    opt = opt || {};
    rows = rows.slice(0, opt.n || 12).reverse();
    var lab = rows.map(function (r) { var t = r.l || r.n; return t.length > 58 ? t.slice(0, 56) + '…' : t; });
    var lay = U.layout('', 0, { noFc: true, h: Math.max(220, 34 * rows.length + 90) });
    lay.barmode = 'overlay'; lay.hovermode = 'y unified'; lay.margin.l = 10;
    lay.xaxis = { title: { text: '2030-cu il dəyərinin dəyişməsi, %' }, gridcolor: '#EDF1F4', zeroline: true, zerolinecolor: '#738190', fixedrange: true, ticksuffix: '%' };
    lay.yaxis = { automargin: true, fixedrange: true, tickfont: { size: 11 } };
    U.plot(el, [
      { type: 'bar', orientation: 'h', y: lab, x: rows.map(function (r) { return r.emin; }), name: 'Əmsal −1 standart xəta', marker: { color: '#B3261E' }, hovertemplate: '%{x:.3f}%' },
      { type: 'bar', orientation: 'h', y: lab, x: rows.map(function (r) { return r.epl; }), name: 'Əmsal +1 standart xəta', marker: { color: '#1E7B4F' }, hovertemplate: '%{x:.3f}%' }], lay);
  };
  U.lines = function (el, sets, yt, opt) {
    opt = opt || {};
    var l = U.layout(yt, 0, { noFc: true, h: opt.h || 300 });
    l.xaxis = { tickformat: opt.xfmt || 'd', gridcolor: '#EDF1F4', fixedrange: true, title: { text: opt.xt || '' } };
    if (!opt.xfmt) l.xaxis.dtick = 1;
    if (opt.yr) l.yaxis.range = opt.yr;
    U.plot(el, sets.map(function (s) {
      return { type: 'scatter', mode: s.mode || 'lines+markers', x: s.x, y: s.y, name: s.name, line: { color: s.c, width: s.w || 2.2, dash: s.dash || 'solid', shape: s.shape || 'linear' },
        marker: s.marker || { size: 5 } };
    }), l);
  };
  U.barH = function (el, lab, val, xt, opt) {
    opt = opt || {};
    var l = U.layout('', 0, { noFc: true, h: opt.h || Math.max(240, 26 * lab.length + 80) });
    l.xaxis = { title: { text: xt }, gridcolor: '#EDF1F4', fixedrange: true, zeroline: true, zerolinecolor: '#B8C2C4' };
    l.yaxis = { autorange: 'reversed', automargin: true, fixedrange: true, tickfont: { size: 11 } };
    l.hovermode = 'closest'; l.margin.l = 10;
    var tr0 = { type: 'bar', orientation: 'h', y: lab, x: val, marker: { color: opt.color || '#9AA6B2' }, name: opt.name || '' };
    if (opt.err) tr0.error_x = { type: 'data', symmetric: false, array: opt.err[1], arrayminus: opt.err[0], color: '#455463' };
    U.plot(el, [tr0], l);
  };
})();
