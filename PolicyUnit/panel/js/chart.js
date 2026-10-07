/* chart.js — Plotly charts in the panel's look (adapted from the MicroUnit İş paneli): fan charts with 5–95 / 10–90 /
   25–75 % bands, lines, bars, horizontal bars, scatter. Axis titles, legends and hover labels in Azerbaijani. */
(function () {
  'use strict';
  var U = window.U;
  var FONT = '"Helvetica Neue", Helvetica, Arial, sans-serif';
  U.PAL = ['#0E6F7C', '#1F6FB2', '#B3261E', '#E07B00', '#6A3FB5', '#1E7B4F', '#8A5300', '#455463', '#C2185B', '#00838F'];
  U.layout = function (ytitle, opts) {
    opts = opts || {};
    var lay = {
      height: opts.h || 340, autosize: true, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
      font: { family: FONT, size: 12.5, color: '#15202B' }, separators: ', ', hovermode: opts.hm || 'x unified',
      margin: { l: opts.ml || 62, r: 18, t: opts.mt == null ? 40 : opts.mt, b: opts.mb || 42 },
      legend: { orientation: 'h', traceorder: 'normal', y: 1.02, yanchor: 'bottom', x: 0, xanchor: 'left', font: { size: 12, color: '#455463' } },
      xaxis: { gridcolor: '#EDF1F4', zeroline: false, fixedrange: true, title: { text: opts.xt || '' }, automargin: true },
      yaxis: { gridcolor: '#EDF1F4', zeroline: !!opts.zero, zerolinecolor: '#9AA6B2', title: { text: ytitle || '', font: { size: 12, color: '#738190' } },
        separatethousands: true, exponentformat: 'none', fixedrange: true, automargin: true }
    };
    if (opts.years) { lay.xaxis.tickformat = 'd'; lay.xaxis.dtick = 1; }
    if (opts.fc) {
      lay.shapes = [{ type: 'rect', xref: 'x', yref: 'paper', layer: 'below', x0: opts.fc - 0.5, x1: (opts.fcEnd || Math.max(2030, opts.fc + 4)) + 0.5, y0: 0, y1: 1, fillcolor: '#F2F7FB', line: { width: 0 } }];
    }
    return lay;
  };
  var LOC = false;
  function locale() {
    if (LOC || !window.Plotly) return; LOC = true;
    window.Plotly.register({ moduleType: 'locale', name: 'az', dictionary: {}, format: {
      days: ['Bazar', 'Bazar ertəsi', 'Çərşənbə axşamı', 'Çərşənbə', 'Cümə axşamı', 'Cümə', 'Şənbə'], shortDays: ['B', 'B.e.', 'Ç.a.', 'Ç.', 'C.a.', 'C.', 'Ş.'],
      months: ['yanvar', 'fevral', 'mart', 'aprel', 'may', 'iyun', 'iyul', 'avqust', 'sentyabr', 'oktyabr', 'noyabr', 'dekabr'],
      shortMonths: ['yan', 'fev', 'mar', 'apr', 'may', 'iyn', 'iyl', 'avq', 'sen', 'okt', 'noy', 'dek'], date: '%d.%m.%Y', decimal: ',', thousands: ' ' } });
  }
  U.plot = function (el, data, lay) {
    locale();
    if (typeof el === 'string') el = U.$(el);
    if (!el) return;
    if (!window.Plotly) { el.textContent = 'Qrafik kitabxanası yüklənmədi'; return; }
    window.Plotly.newPlot(el, data, lay, { displaylogo: false, responsive: true, displayModeBar: false, locale: 'az' });
  };
  function tr(x, y, name, col, dash, w, extra) {
    var t = { type: 'scatter', mode: 'lines', x: x, y: y, name: name, line: { color: col, dash: dash || 'solid', width: w == null ? 2.4 : w }, connectgaps: false };
    for (var k in extra || {}) t[k] = extra[k];
    return t;
  }
  U.tr = tr;
  function band(x, lo, hi, name, alpha, col) {
    return [tr(x, hi, name + ' (yuxarı)', 'rgba(0,0,0,0)', 'solid', 0, { showlegend: false, hoverinfo: 'skip' }),
      tr(x, lo, name, 'rgba(0,0,0,0)', 'solid', 0, { fill: 'tonexty', fillcolor: 'rgba(' + (col || '14,111,124') + ',' + alpha + ')', hoverinfo: 'skip' })];
  }
  U.band = band;
  /* fan chart from distribution rows {il, p05..p95, baza, p50}; opt.live: second set drawn as dashed quantile lines */
  U.fan = function (el, rows, opt) {
    opt = opt || {};
    rows = rows.slice().sort(function (a, b) { return a.il - b.il; });
    var x = rows.map(function (r) { return r.il; }), g = function (k, rs) { return (rs || rows).map(function (r) { return r[k]; }); }, d = opt.d == null ? 2 : opt.d;
    var hv = '%{y:,.' + d + 'f}';
    var data = [].concat(band(x, g('p05'), g('p95'), '5–95 %', 0.12), band(x, g('p10'), g('p90'), '10–90 %', 0.18), band(x, g('p25'), g('p75'), '25–75 %', 0.26));
    data.push(tr(x, g('p50'), opt.medLab || 'Median', '#0A5560', 'solid', 2.6, { mode: 'lines+markers', marker: { size: 6 }, hovertemplate: hv }));
    if (rows.some(function (r) { return U.isNum(r.baza); })) data.push(tr(x, g('baza'), opt.baseLab || 'Rəsmi baza', '#E07B00', 'dash', 2, { mode: 'lines+markers', marker: { size: 5, symbol: 'diamond' }, hovertemplate: hv }));
    if (opt.live && opt.live.length) {
      var L = opt.live.slice().sort(function (a, b) { return a.il - b.il; });
      data.push(tr(x, g('p50', L), 'Canlı baxış: median', '#1F6FB2', 'dot', 2.4, { mode: 'lines+markers', marker: { size: 5 }, hovertemplate: hv }));
      data.push(tr(x, g('p05', L), 'Canlı baxış: 5 % və 95 %', '#1F6FB2', 'dash', 1.2, { hovertemplate: hv }));
      data.push(tr(x, g('p95', L), 'Canlı 95 %', '#1F6FB2', 'dash', 1.2, { showlegend: false, hovertemplate: hv }));
    }
    if (opt.hline != null) data.push(tr([x[0] - 0.4, x[x.length - 1] + 0.4], [opt.hline, opt.hline], opt.hlab || 'Hədd', '#B3261E', 'dot', 1.6, { hoverinfo: 'skip' }));
    var lay = U.layout(opt.yt || '', { h: opt.h || 380, years: true });
    lay.legend.font = { size: 11, color: '#455463' }; lay.legend.tracegroupgap = 2;
    U.plot(el, data, lay);
  };
  U.lines = function (el, sets, yt, opt) {
    opt = opt || {};
    var l = U.layout(yt, { h: opt.h || 300, years: opt.years, xt: opt.xt, zero: opt.zero, hm: opt.hm, fc: opt.fc });
    if (opt.xtype) l.xaxis.type = opt.xtype;
    if (opt.yr) l.yaxis.range = opt.yr;
    if (opt.ylog) l.yaxis.type = 'log';
    if (opt.y2) l.yaxis2 = { overlaying: 'y', side: 'right', title: { text: opt.y2 }, fixedrange: true, showgrid: false };
    U.plot(el, sets.map(function (s, i) {
      return { type: 'scatter', mode: s.mode || 'lines', x: s.x, y: s.y, name: s.name, yaxis: s.y2 ? 'y2' : 'y', line: { color: s.c || U.PAL[i % U.PAL.length], width: s.w || 2.2, dash: s.dash || 'solid', shape: s.shape || 'linear' },
        marker: s.marker || { size: 5 }, hovertemplate: s.hv, fill: s.fill, fillcolor: s.fillcolor, showlegend: s.showlegend };
    }), l);
  };
  U.bars = function (el, x, sets, yt, opt) {
    opt = opt || {};
    var l = U.layout(yt, { h: opt.h || 300, years: opt.years, xt: opt.xt, zero: true, hm: opt.hm || 'x unified' });
    l.barmode = opt.mode || 'group';
    if (opt.cat) l.xaxis.type = 'category';
    U.plot(el, sets.map(function (s, i) { return { type: 'bar', x: x, y: s.y, name: s.name, marker: { color: s.c || U.PAL[i % U.PAL.length] }, hovertemplate: s.hv }; }), l);
  };
  U.barH = function (el, lab, val, xt, opt) {
    opt = opt || {};
    var l = U.layout('', { h: opt.h || Math.max(220, 26 * lab.length + 80), hm: 'closest', mt: 16 });
    l.xaxis = { title: { text: xt }, gridcolor: '#EDF1F4', fixedrange: true, zeroline: true, zerolinecolor: '#9AA6B2', automargin: true };
    l.yaxis = { autorange: 'reversed', automargin: true, fixedrange: true, tickfont: { size: 11 } };
    l.margin.l = 10; l.showlegend = !!opt.sets;
    var sets = opt.sets || [{ v: val, c: opt.color, name: opt.name || '' }];
    U.plot(el, sets.map(function (s, i) {
      var t = { type: 'bar', orientation: 'h', y: lab.map(function (s) { return String(s).length > 64 ? String(s).slice(0, 62) + '…' : s; }), x: s.v, name: s.name, marker: { color: s.colors || s.c || U.PAL[i] }, hovertemplate: '%{x:,.3f}<extra>%{y}</extra>' };
      if (s.err) t.error_x = { type: 'data', symmetric: false, array: s.err[1], arrayminus: s.err[0], color: '#455463' };
      return t;
    }), l);
    if (opt.barmode) el.layout && (el.layout.barmode = opt.barmode);
  };
  U.scatter = function (el, pts, xt, yt, opt) {
    opt = opt || {};
    var l = U.layout(yt, { h: opt.h || 320, xt: xt, hm: 'closest', zero: true });
    U.plot(el, [{ type: 'scatter', mode: 'markers+text', x: pts.map(function (p) { return p.x; }), y: pts.map(function (p) { return p.y; }), text: pts.map(function (p) { return p.t || ''; }), textposition: 'top center',
      marker: { size: pts.map(function (p) { return p.s || 10; }), color: pts.map(function (p) { return p.c || '#0E6F7C'; }), line: { width: 1, color: '#fff' } }, hovertext: pts.map(function (p) { return p.h || ''; }), hoverinfo: 'text', showlegend: false }].concat(opt.extra || []), l);
  };
})();
