/* scen.js — Ssenarilər: key indicators of every requirement compared across Əsas / Mənfi / İslahat, year by year. */
(function () {
  'use strict';
  var U = window.U, META = window.MICRO.META, SEL = 0;
  function diff(s, k, i) {
    var a = s.s[k][i], b = s.s.B[i];
    if (!U.isNum(a) || !U.isNum(b)) return null;
    return s.k === 'rate' ? a - b : (b ? (a / b - 1) * 100 : null);
  }
  U.pages.ssenari = function (v) {
    var keys = META.scen.map(function (k) { return U.byId[k]; });
    var h = '<div class="eyebrow">Müqayisə</div><h1 class="h1" style="margin-top:4px">Ssenarilər: Əsas, Mənfi, İslahat</h1>' +
      '<p class="lead">FR1-in üç makro ssenarisi (neftin qiyməti və hasilatı, dövlət investisiyası, xarici tələb, faiz siyasəti, TFP) bütün modullardan keçir. Aşağıda hər tələbin əsas göstəriciləri illər üzrə; «fərq» — ssenarinin Əsasdan fərqi (faiz göstəricilərində faiz bəndi).</p>' +
      '<div class="card pad" style="margin-top:18px"><div class="toolbar" style="margin-top:0"><label class="small muted">Qrafik üçün göstərici</label><select id="sc-sel" class="btn sm">' +
      keys.map(function (s, i) { return '<option value="' + i + '"' + (i === SEL ? ' selected' : '') + '>' + s.f + ' · ' + U.esc(U.label(s)) + '</option>'; }).join('') +
      '</select><a class="btn sm" id="sc-open" href="#/' + keys[SEL].f.toLowerCase() + '/s/' + keys[SEL].n + '">Göstəricinin bölməsi →</a></div><div id="sc-ch"></div></div>' +
      '<div class="card pad" style="margin-top:14px"><div class="sec-h" style="margin-bottom:4px"><h2>2030-da Əsas ssenaridən fərq</h2><p>Mənfi və İslahat ssenariləri, %; faiz göstəricilərində faiz bəndi.</p></div><div id="sc-bar"></div></div>' +
      '<div class="card" style="margin-top:14px"><div class="grp-h">İllər üzrə açıq müqayisə</div><div class="itbl-wrap"><table class="itbl"><thead><tr><th class="l">Göstərici / ssenari</th><th>2025</th>' +
      U.YEARS.map(function (y) { return '<th class="fc">' + y + '</th>'; }).join('') + '<th>Fərq 2030</th></tr></thead><tbody>';
    keys.forEach(function (s) {
      h += '<tr class="sub" data-n="' + s.n + '"><td class="lab" colspan="8" style="padding-left:10px;background:var(--surface-2)"><b>' + s.f + ' · ' + U.esc(U.label(s)) + '</b><span class="u">' + U.esc(s.u) + '</span></td></tr>';
      U.scens(s).forEach(function (k) {
        var dd = k === 'B' ? null : diff(s, k, 4);
        h += '<tr data-n="' + s.n + '"><td class="lab"><b style="color:' + U.SCC[k] + '">' + U.SCN[k] + '</b></td><td class="n">' + (k === 'B' ? U.nf(s.b, s.d) : '') + '</td>' +
          s.s[k].map(function (x) { return '<td class="n fc">' + U.nf(x, s.d) + '</td>'; }).join('') +
          '<td class="n dcell ' + U.trend(dd) + '">' + (k === 'B' ? '—' : U.sg(dd, 2) + ' ' + (s.k === 'rate' ? 'f.b.' : '%')) + '</td></tr>';
      });
    });
    v.innerHTML = h + '</tbody></table></div></div>';
    var s0 = keys[SEL], data = [];
    U.SC.forEach(function (k) { if (s0.s[k]) data.push({ type: 'scatter', mode: 'lines+markers', name: U.SCN[k], x: [2025].concat(U.YEARS), y: [s0.b].concat(s0.s[k]), line: { color: U.SCC[k], dash: U.SCD[k], width: 2.6 } }); });
    if (s0.h) data.unshift({ type: 'scatter', mode: 'lines', name: 'Faktiki', x: s0.h.map(function (p) { return p[0]; }), y: s0.h.map(function (p) { return p[1]; }), line: { color: '#455463', width: 2 } });
    U.plot(U.$('#sc-ch'), data, U.layout(s0.u, Math.max(s0.h ? s0.h[0][0] : 2020, 2015), { h: 340 }));
    var labs = keys.map(function (s) { return s.f + ' · ' + U.label(s); });
    U.plot(U.$('#sc-bar'), ['A', 'R'].map(function (k) {
      return { type: 'bar', orientation: 'h', name: U.SCN[k], y: labs, x: keys.map(function (s) { return s.s[k] ? diff(s, k, 4) : null; }), marker: { color: U.SCC[k] } };
    }), (function () { var l = U.layout('', 0, { noFc: true, h: 420 }); l.xaxis = { gridcolor: '#EDF1F4', zeroline: true, zerolinecolor: '#B8C2C4', fixedrange: true };
      l.yaxis = { autorange: 'reversed', automargin: true, fixedrange: true }; l.barmode = 'group'; l.hovermode = 'y unified'; l.margin.l = 10; return l; })());
    U.$('#sc-sel').onchange = function (e) { SEL = +e.target.value; U.route(true); };
    v.onclick = function (e) { var tr = e.target.closest('tr[data-n]'); if (tr) location.hash = '#/' + U.S[+tr.getAttribute('data-n')].f.toLowerCase() + '/s/' + tr.getAttribute('data-n'); };
  };
})();
