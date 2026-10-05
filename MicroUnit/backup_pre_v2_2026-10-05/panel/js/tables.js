/* tables.js — the explicit year-by-year table of one indicator, and the group matrix with heat-coloured growth. */
(function () {
  'use strict';
  var U = window.U;
  function head(first, y0) {
    return '<thead><tr><th class="l">' + first + '</th>' + (y0 ? '<th>2025<span class="st">' + y0 + '</span></th>' : '') +
      U.YEARS.map(function (y) { return '<th class="fc">' + y + '<span class="st">proqnoz</span></th>'; }).join('') + '<th>Orta illik<span class="st">2026–2030</span></th></tr></thead>';
  }
  /* rows: for each scenario a level row and a growth row; then the band (Əsas) */
  U.yearTable = function (s, all) {
    var ks = all || U.scenRaw() === 'all' ? U.scens(s) : [U.scOf(s)];
    var gd = U.gdec(s), gu = U.gunit(s), b25 = U.isNum(s.b) ? U.nf(s.b, s.d) : '—';
    var lastH = U.lastHist(s), y0 = lastH && lastH[0] === 2025 ? 'faktiki' : (s.nt && /cari/.test(s.nt) ? 'cari qiym.' : 'başlanğıc');
    var h = '<table class="itbl">' + head('Ssenari / göstərici', y0) + '<tbody>';
    ks.forEach(function (k) {
      var c = U.cagr(s, k);
      h += '<tr><td class="lab"><b style="color:' + U.SCC[k] + '">' + U.SCN[k] + '</b> · səviyyə<span class="u">' + U.esc(s.u) + '</span></td><td class="n">' + b25 + '</td>' +
        s.s[k].map(function (v) { return '<td class="n fc"><b>' + U.nf(v, s.d) + '</b></td>'; }).join('') +
        '<td class="n dcell ' + U.trend(c) + '">' + U.sg(c, gd) + (U.isNum(c) ? ' ' + gu : '') + '</td></tr>';
      h += '<tr class="sub"><td class="lab">' + (s.k === 'rate' ? 'dəyişmə, f.b.' : 'illik artım, %') + '</td><td class="n"></td>' +
        s.gr[k].map(function (v) { return '<td class="n fc dcell ' + U.trend(v) + '">' + U.sg(v, gd) + '</td>'; }).join('') + '<td></td></tr>';
    });
    if (s.q) {
      h += '<tr class="sub"><td class="lab">5–95 % zolağı (Əsas)</td><td class="n"></td>' + s.q[0].map(function (lo, i) {
        return '<td class="n fc small" style="white-space:normal;line-height:1.3">' + U.nf(lo, s.d) + ' …<br>' + U.nf(s.q[1][i], s.d) + '</td>'; }).join('') + '<td></td></tr>';
    }
    return h + '</tbody></table>';
  };
  /* group matrix: members × years, levels or growth, heat colouring on growth */
  U.matrix = function (list, mode) {
    var k = U.scen();
    var h = '<table class="itbl"><thead><tr><th class="l">Göstərici</th><th class="l">Vahid</th><th>2025</th>' +
      U.YEARS.map(function (y) { return '<th class="fc">' + y + '</th>'; }).join('') + '<th>Orta illik, 2026–30</th></tr></thead><tbody>';
    list.forEach(function (s) {
      var kk = s.s[k] ? k : 'B', c = U.cagr(s, kk), gd = U.gdec(s);
      var cells = mode === 'g'
        ? s.gr[kk].map(function (v) { return '<td class="n fc dcell" style="' + U.heat(v, s.k === 'rate' ? 1.5 : 8) + '">' + U.sg(v, gd) + '</td>'; }).join('')
        : s.s[kk].map(function (v) { return '<td class="n fc">' + U.nf(v, s.d) + '</td>'; }).join('');
      h += '<tr data-n="' + s.n + '"><td class="lab">' + U.esc(s.e) + (kk !== k ? ' <span class="chip">yalnız Əsas</span>' : '') + '</td><td class="small muted">' + U.esc(mode === 'g' ? U.gunit(s) : s.u) + '</td>' +
        '<td class="n">' + (mode === 'g' ? '' : U.nf(s.b, s.d)) + '</td>' + cells +
        '<td class="n dcell" style="' + U.heat(c, s.k === 'rate' ? 1.5 : 8) + '">' + U.sg(c, gd) + '</td></tr>';
    });
    return h + '</tbody></table>';
  };
  U.csvOf = function (rows) {
    return '﻿' + rows.map(function (r) { return r.map(function (x) { var t = x == null ? '' : String(x); return /[";,\n]/.test(t) ? '"' + t.replace(/"/g, '""') + '"' : t; }).join(';'); }).join('\r\n');
  };
  U.download = function (name, blob) {
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  };
  U.seriesRows = function (s) {
    var out = [];
    U.scens(s).forEach(function (k) {
      out.push([s.f, s.g, s.e, s.v, s.u, U.SCN[k], s.b].concat(s.s[k], s.gr[k]));
    });
    return out;
  };
  U.HEAD = ['FR', 'Qrup', 'Göstərici', 'Variant', 'Vahid', 'Ssenari', '2025'].concat(U.YEARS.map(String), U.YEARS.map(function (y) { return 'artım ' + y; }));
})();
