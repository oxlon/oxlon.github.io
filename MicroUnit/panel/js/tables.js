/* tables.js — full 2026–2030 tables: one component (all scenarios × level + growth + band), its history (imputed in
   italics), a group / a whole FR (components × scenarios); CSV and download helpers. */
(function () {
  'use strict';
  var U = window.U;
  function fcCell(s, k, i, v) {
    var act = s.fa && s.fa.indexOf(U.YEARS[i]) >= 0;
    return '<td class="n fc' + (act ? ' act" title="faktiki (müşahidə)' : '') + '"><b>' + U.nf(v, s.d) + '</b></td>';
  }
  function head(first, s) {
    return '<thead><tr><th class="l">' + first + '</th><th>' + (s ? U.lab25(s) : '2025') + '</th>' +
      U.YEARS.map(function (y) { return '<th class="fc">' + y + '<span class="st">proqnoz</span></th>'; }).join('') +
      '<th>Orta illik<span class="st">2026–2030</span></th></tr></thead>';
  }
  U.compTable = function (s, ks) {
    ks = ks || U.scens(s);
    if (!ks.length) return '<p class="muted">Bu komponent üçün proqnoz yoxdur.</p>';
    var gd = U.gdec(s), gu = U.gunit(s), h = '<table class="itbl">' + head('Ssenari / göstərici', s) + '<tbody>';
    ks.forEach(function (k) {
      var c = U.cagr(s, k);
      h += '<tr><td class="lab"><b style="color:' + U.SCC[k] + '">' + U.SCN[k] + '</b> · səviyyə<span class="u">' + U.esc(s.u) + '</span></td><td class="n">' + U.nf(U.b25(s, k), s.d) + '</td>' +
        s.s[k].map(function (v, i) { return fcCell(s, k, i, v); }).join('') +
        '<td class="n dcell ' + U.trend(c) + '">' + U.sg(c, gd) + (U.isNum(c) ? ' ' + gu : '') + '</td></tr>';
      h += '<tr class="sub"><td class="lab">' + (U.isRate(s) ? 'dəyişmə, f.b.' : 'illik artım, %') + '</td><td class="n"></td>' +
        s.gr[k].map(function (v) { return '<td class="n fc dcell ' + U.trend(v) + '">' + U.sg(v, gd) + '</td>'; }).join('') + '<td></td></tr>';
      var q = s.q && s.q[k];
      if (q) h += '<tr class="sub"><td class="lab">5–95 % zolağı</td><td class="n"></td>' + q[0].map(function (lo, i) {
        return '<td class="n fc small" style="white-space:normal;line-height:1.3">' + (U.isNum(lo) ? U.nf(lo, s.d) + ' …<br>' + U.nf(q[1][i], s.d) : '—') + '</td>'; }).join('') + '<td></td></tr>';
    });
    h += '</tbody></table>';
    if (s.fa) h += '<p class="small muted" style="margin:6px 10px">Çərçivəli xana — həmin il üçün faktiki (müşahidə olunan) dəyər: ' + s.fa.join(', ') + '.</p>';
    if (s.nc) h += '<p class="small muted" style="margin:6px 10px">2025 — modulun cari qiymətləndirməsi (il üzrə faktiki məlumat hələ dərc olunmayıb).</p>';
    return h;
  };
  U.impLegend = '<span class="implg"><i class="impdot"></i>' + 'Doldurulmuş (interpolyasiya) — kursiv, üzərinə gəldikdə üsul göstərilir</span>';
  U.histTable = function (s, n) {
    var h = (s.h || []).filter(function (p) { return p[0] <= 2025; }).slice(-(n || 12));
    if (!h.length) return '';
    var imp = h.some(function (p) { return p[2]; });
    return '<table class="itbl"><thead><tr><th class="l">Faktiki</th>' + h.map(function (p) { return '<th>' + p[0] + '</th>'; }).join('') + '</tr></thead><tbody><tr><td class="lab">' + U.esc(s.u) + '</td>' +
      h.map(function (p) {
        return p[2] ? '<td class="n imp" title="' + U.esc(U.IMPLAB + ': ' + ((s.im || {})[p[0]] || '')) + '">' + U.nf(p[1], s.d) + '</td>' : '<td class="n">' + U.nf(p[1], s.d) + '</td>';
      }).join('') + '</tr></tbody></table>' + (imp ? '<div class="small muted" style="margin:6px 10px">' + U.impLegend + '</div>' : '');
  };
  /* components × scenarios; mode l (level) | g (growth) | b (both) */
  U.groupTable = function (list, mode, ks, opt) {
    opt = opt || {};
    var cols = mode === 'b' ? ['l', 'g'] : [mode || 'l'];
    var h = '<table class="itbl"><thead><tr><th class="l">Komponent</th><th class="l">Ssenari</th><th>2025</th>';
    cols.forEach(function (c) { U.YEARS.forEach(function (y) { h += '<th class="fc">' + y + (c === 'g' ? '<span class="st">artım</span>' : '') + '</th>'; }); });
    h += '<th>Orta illik</th></tr></thead><tbody>';
    var lastG = null;
    list.forEach(function (s) {
      if (opt.groups && s.g !== lastG) { lastG = s.g; h += '<tr class="grow"><td colspan="' + (4 + 5 * cols.length) + '">' + U.esc(s.g) + '</td></tr>'; }
      var kk = (ks || U.SC).filter(function (k) { return s.s && s.s[k]; });
      if (!kk.length) { h += '<tr><td class="lab">' + U.esc(s.e) + '</td><td colspan="' + (3 + 5 * cols.length) + '" class="muted small">proqnoz edilmir</td></tr>'; return; }
      kk.forEach(function (k, j) {
        var c = U.cagr(s, k), gd = U.gdec(s);
        h += '<tr data-id="' + U.esc(s.i) + '">' + (j === 0 ? '<td class="lab" rowspan="' + kk.length + '"><a href="' + U.href(s) + '">' + U.esc(s.e) + '</a><span class="u">' + U.esc(s.u) + '</span></td>' : '') +
          '<td><b style="color:' + U.SCC[k] + '">' + U.SCN[k] + '</b></td><td class="n">' + U.nf(U.b25(s, k), s.d) + '</td>';
        cols.forEach(function (cm) {
          h += cm === 'g' ? s.gr[k].map(function (v) { return '<td class="n fc dcell" style="' + U.heat(v, U.isRate(s) ? 1.5 : 8) + '">' + U.sg(v, gd) + '</td>'; }).join('')
            : s.s[k].map(function (v) { return '<td class="n fc">' + U.nf(v, s.d) + '</td>'; }).join('');
        });
        h += '<td class="n dcell" style="' + U.heat(c, U.isRate(s) ? 1.5 : 8) + '">' + U.sg(c, gd) + '</td></tr>';
      });
    });
    return h + '</tbody></table>';
  };
  U.csvOf = function (rows) {
    return '﻿' + rows.map(function (r) { return r.map(function (x) { var t = x == null ? '' : String(x); return /[";,\n]/.test(t) ? '"' + t.replace(/"/g, '""') + '"' : t; }).join(';'); }).join('\r\n');
  };
  U.download = function (name, blob) {
    if (blob && typeof blob.then === 'function') return blob.then(function (b) { U.download(name, b); }, function (e) { U.toast('Xəta: ' + e.message); });   // xlsx/docx are built asynchronously
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 800);
  };
  U.HEAD = ['FR', 'İdentifikator', 'Qrup', 'Komponent', 'Vahid', 'Ssenari', '2025'].concat(U.YEARS.map(String), U.YEARS.map(function (y) { return 'artım ' + y; }));
  U.seriesRows = function (s, ks) {
    return (ks || U.scens(s)).filter(function (k) { return s.s && s.s[k]; }).map(function (k) {
      return [s.f, s.i, s.g, s.e, s.u, U.SCN[k], U.b25(s, k)].concat(s.s[k], s.gr[k]);
    });
  };
  U.csvList = function (name, list, ks) {
    U.download(name, new Blob([U.csvOf([U.HEAD].concat([].concat.apply([], list.map(function (s) { return U.seriesRows(s, ks); }))))], { type: 'text/csv' }));
  };
})();
