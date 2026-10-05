/* report.js — Hesabat qurucusu, part 1: report configuration (FRs, components, scenarios incl. saved custom ones, years,
   content blocks), the data model shared by every export, and the live HTML preview. Exports: report2.js. */
(function () {
  'use strict';
  var U = window.U, B = U.B;
  var R = U.R = { title: 'Mikro Model — proqnoz hesabatı', author: '', frs: ['FR1', 'FR3', 'FR4', 'FR5', 'FR10', 'FR12'], comps: [], scen: ['B', 'A', 'R'], custom: [],
    y0: 2022, y1: 2030, blocks: { tbl: true, chart: true, eq: true, rob: true, asm: true, notes: true }, notes: '' };
  U.CUST = {};   // id → {name, base, series, overrides}
  try { var st = JSON.parse(U.ls('mikroPanel.report') || 'null'); if (st && st.comps) Object.keys(st).forEach(function (k) { if (k !== 'custom') R[k] = st[k]; }); } catch (e) { /* ignore */ }
  if (!R.comps.length) R.comps = U.META.scen.slice(0, 6);
  U.rSave = function () { U.ls('mikroPanel.report', JSON.stringify(R)); };
  U.rYears = function () { var o = []; for (var y = R.y0; y <= R.y1; y++) o.push(y); return o; };
  /* value of component s in scenario column c ({k:'B'} or {cid}) for year y; imputed flag */
  function value(s, col, y) {
    if (y <= 2025 && !(y === 2025 && s.nc)) { var h = (s.h || []).filter(function (p) { return p[0] === y; })[0]; return h ? { v: h[1], imp: !!h[2] } : { v: null }; }
    if (col.cid) { var c = U.CUST[col.cid], a = c && c.series[s.i]; if (!a) return { v: null }; return { v: a[y - 2025] }; }
    if (y === 2025) return { v: U.b25(s, col.k) };
    return { v: s.s && s.s[col.k] ? s.s[col.k][y - 2026] : null };
  }
  U.rCols = function () {
    var cols = R.scen.map(function (k) { return { k: k, lab: U.SCN[k] + ' ssenari' }; });
    R.custom.forEach(function (id) { var c = U.CUST[id]; if (c) cols.push({ cid: id, lab: c.name + ' (xüsusi)' }); });
    return cols;
  };
  /* the report model: items [{s, rows:[{lab, vals:[{v, imp}]}], eqs}] */
  U.rModel = function () {
    var yrs = U.rYears(), cols = U.rCols();
    var items = R.comps.map(function (id) { return U.byId[id]; }).filter(function (s) { return s && R.frs.indexOf(s.f) >= 0; }).map(function (s) {
      return { s: s, rows: cols.filter(function (c) { return c.cid || (s.s && s.s[c.k]); }).map(function (c) { return { lab: c.lab, col: c, vals: yrs.map(function (y) { return value(s, c, y); }) }; }), eqs: U.eqOf(s).filter(function (e) { return e.used; }) };
    });
    return { title: R.title, author: R.author, date: new Date().toISOString().slice(0, 10), years: yrs, cols: cols, items: items };
  };
  U.rAssumptions = function () {
    var out = [], I = U.inputsOf('FR1');
    if (I) (I.exogenous || []).forEach(function (e) {
      R.scen.forEach(function (k) { var b = (e.baseline || {})[U.SCL[k]]; if (b) out.push([U.SCN[k] + ' ssenari', 'FR1', e.label_az || e.id, e.unit || ''].concat(b)); });
    });
    R.custom.forEach(function (id) {
      var c = U.CUST[id]; if (!c) return;
      Object.keys(c.overrides || {}).forEach(function (m) {
        var x = c.overrides[m] || {}, inp = U.inputsOf(m) || {};
        Object.keys(x.exogenous || {}).forEach(function (eid) { var e = (inp.exogenous || []).filter(function (q) { return q.id === eid; })[0] || {}; var v = x.exogenous[eid];
          out.push([c.name, m, (e.label_az || eid) + ' (dəyişdirilib)', e.unit || ''].concat(Array.isArray(v) ? v : ['%: ' + (v && v.pct)])); });
        Object.keys(x.coefficients || {}).forEach(function (key) { out.push([c.name, m, 'Əmsal ' + key, '', x.coefficients[key]]); });
        Object.keys(x.levers || {}).forEach(function (lid) { out.push([c.name, m, 'Alət ' + lid, '', String(x.levers[lid])]); });
      });
    });
    return out;
  };
  function tbl(it, yrs) {
    var s = it.s;
    return '<table class="rtbl"><thead><tr><th>Ssenari</th>' + yrs.map(function (y) { return '<th class="' + (y > 2025 ? 'fc' : '') + '">' + y + '</th>'; }).join('') + '</tr></thead><tbody>' +
      it.rows.map(function (r) { return '<tr><td>' + U.esc(r.lab) + '</td>' + r.vals.map(function (c) { return '<td class="n' + (c.imp ? ' imp' : '') + '"' + (c.imp ? ' title="' + U.IMPLAB + '"' : '') + '>' + U.nf(c.v, s.d) + '</td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table>';
  }
  U.rPreview = function () {
    var m = U.rModel(), h = '<div class="rdoc" id="rep-doc"><div class="r-title">' + U.esc(m.title) + '</div><div class="r-meta">İqtisadiyyat Nazirliyi · Mikro Model (MİİS §15.5.2) · ' + m.date + (R.author ? ' · ' + U.esc(R.author) : '') + '</div>' +
      '<p class="r-small">Tələblər: ' + R.frs.join(', ') + ' · ssenarilər: ' + m.cols.map(function (c) { return U.esc(c.lab); }).join(', ') + ' · illər: ' + R.y0 + '–' + R.y1 + ' · ' + m.items.length + ' komponent. 2025-dən sonrakı illər proqnozdur; kursiv — doldurulmuş (interpolyasiya).</p>';
    if (!m.items.length) return h + '<p class="muted">Komponent seçilməyib.</p></div>';
    var lastF = null;
    m.items.forEach(function (it, i) {
      var s = it.s;
      if (s.f !== lastF) { lastF = s.f; h += '<h2 class="r-h1">' + s.f + ' — ' + U.esc(U.frOf(s.f).full) + '</h2>'; }
      h += '<h3 class="r-h2">' + U.esc(s.e) + ' <span class="r-unit">' + U.esc(s.u) + '</span></h3>';
      if (R.blocks.chart) h += '<div class="r-chart" id="rch-' + i + '"></div>';
      if (R.blocks.tbl) h += tbl(it, m.years);
      if (R.blocks.eq && it.eqs.length) h += '<table class="rtbl r-eq"><thead><tr><th>Tənlik</th><th>Üsul</th><th>n</th><th>R²</th><th>DW</th><th>koint. p</th><th>Theil U (TG)</th>' + (R.blocks.rob ? '<th>Dayanıqlıq</th>' : '') + '</tr></thead><tbody>' +
        it.eqs.map(function (e) { return '<tr><td>' + U.esc(e.t) + '<br><span class="r-unit">' + U.esc(e.id) + '</span></td><td>' + U.esc(e.est) + '</td><td class="n">' + (e.n || '—') + '</td><td class="n">' + (U.isNum(e.r2) ? U.nf(e.r2, 3) : '—') + '</td><td class="n">' + (U.isNum(e.dw) ? U.nf(e.dw, 2) : '—') + '</td><td class="n">' + U.pf(e.cp) + '</td><td class="n">' + (U.isNum(e.urw) ? U.nf(e.urw, 2) : '—') + '</td>' + (R.blocks.rob ? '<td>' + U.esc(e.v || '—') + (e.ft ? '<br><span class="r-unit">' + U.esc(e.ft) + '</span>' : '') + '</td>' : '') + '</tr>'; }).join('') + '</tbody></table>';
    });
    if (R.blocks.asm) { var a = U.rAssumptions(); if (a.length) h += '<h2 class="r-h1">Fərziyyələr</h2><table class="rtbl"><thead><tr><th>Ssenari</th><th>Modul</th><th>Fərziyyə</th><th>Vahid</th>' + U.YEARS.map(function (y) { return '<th>' + y + '</th>'; }).join('') + '</tr></thead><tbody>' +
      a.map(function (r) { return '<tr>' + r.map(function (x, j) { return '<td' + (j > 3 ? ' class="n"' : '') + '>' + (typeof x === 'number' ? U.nf(x) : U.esc(x)) + '</td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table>'; }
    if (R.blocks.notes && R.notes) h += '<h2 class="r-h1">Qeydlər</h2><p>' + U.esc(R.notes).replace(/\n/g, '<br>') + '</p>';
    return h + '<p class="r-small">Mənbə: modulların çıxış faylları (möhür ' + U.META.stamp.md5 + ', ' + U.META.stamp.date + ').</p></div>';
  };
  U.rCharts = function () {
    if (!R.blocks.chart) return;
    U.rModel().items.forEach(function (it, i) {
      var el = U.$('#rch-' + i); if (!el) return;
      var data = U.histTraces((it.s.h || []).filter(function (p) { return p[0] <= 2025 && p[0] >= R.y0; }), null, 40);
      it.rows.forEach(function (r) {
        var k = r.col.k || 'C', ys = U.rYears().filter(function (y) { return y >= 2025; }), xs = [], vs = [];
        ys.forEach(function (y) { var c = r.vals[y - R.y0]; if (c && U.isNum(c.v)) { xs.push(y); vs.push(c.v); } });
        data.push({ type: 'scatter', mode: 'lines+markers', x: xs, y: vs, name: r.lab, line: { color: U.SCC[k], dash: U.SCD[k] || 'solid', width: 2.4 } });
      });
      var lay = U.layout(it.s.u, R.y0, { h: 300 }); lay.margin.t = 36;
      U.plot(el, data, lay);
    });
  };
})();
