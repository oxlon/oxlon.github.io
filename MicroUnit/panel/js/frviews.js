/* frviews.js — FR overview (plain-language intro, KPIs, groups, robustness counts, not-forecast list), group table and
   the combined table of every component of an FR (all scenarios, level / growth / both, CSV and Excel). */
(function () {
  'use strict';
  var U = window.U, MODE = {}, SCF = {};
  function counts(fr) {
    var c = { 'stabil': 0, 'qismən stabil': 0, 'qeyri-stabil': 0, '': 0 }, used = U.eqRows(fr).filter(function (e) { return e.used; });
    used.forEach(function (e) { c[e.v || ''] = (c[e.v || ''] || 0) + 1; });
    return { c: c, used: used.length, all: U.eqRows(fr).length };
  }
  U.robCounts = counts;
  U.viewOverview = function (f) {
    var rc = counts(f.c), gs = U.groups(f.c), nf = (U.META.nf || {})[f.c] || [];
    var h = '<div class="eyebrow">' + f.c + ' · ümumi baxış</div><h1 class="h1" style="font-size:26px;margin-top:4px">' + U.esc(f.full) + '</h1>' +
      '<p class="lead" style="font-size:15px">' + U.esc(f.intro) + '</p>' +
      '<div class="kpis" style="margin-top:14px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr))">' + f.kpi.map(function (id) {
        var s = U.byId[id], k = U.scOf(s), c = U.cagr(s, k);
        return '<a class="kpi" href="' + U.href(s) + '" style="color:inherit;text-decoration:none"><div class="l">' + U.esc(s.e) + '</div><div class="v">' + U.nf(s.s[k][4], s.d) + '<small>2030 · ' + U.SCN[k] + '</small></div>' +
          '<div class="small muted">' + U.lab25(s) + ': ' + U.nf(U.b25(s, k), s.d) + ' ' + U.esc(s.u) + '</div><div class="d ' + U.trend(c) + '">' + (U.isRate(s) ? 'dəyişmə: ' : 'orta illik artım: ') + U.sg(c, U.gdec(s)) + ' ' + U.gunit(s) + '</div>' + U.spark(s) + '</a>';
      }).join('') +
      '<a class="kpi" href="#/' + f.slug + '/dayaniqliq" style="color:inherit;text-decoration:none"><div class="l">Proqnozda istifadə olunan tənliklərin dayanıqlığı</div><div class="v">' + rc.used + '<small>tənlik (' + rc.all + ' cəmi)</small></div>' +
      '<div class="small" style="display:flex;gap:6px;flex-wrap:wrap;margin-top:4px">' + U.vchip('stabil') + ' ' + rc.c['stabil'] + ' ' + U.vchip('qismən stabil') + ' ' + rc.c['qismən stabil'] + ' ' + U.vchip('qeyri-stabil') + ' ' + rc.c['qeyri-stabil'] + '</div>' +
      '<div class="d flat">ətraflı: dayanıqlıq səhifəsi →</div></a></div>' +
      '<section class="sec"><div class="sec-h"><h2>Komponent qrupları</h2><p>Qrupu açın — bütün komponentlər üç ssenaridə, 2026–2030 illər üzrə bir cədvəldə.</p></div><div class="grid g3">' +
      gs.map(function (g, gi) { var ms = U.members(f.c, g); return '<a class="card action" href="#/' + f.slug + '/g/' + gi + '"><h3>' + U.esc(g) + '</h3><p>' + ms.length + ' komponent · ' +
        U.esc(ms.slice(0, 3).map(function (s) { return s.e; }).join('; ')) + (ms.length > 3 ? '…' : '') + '</p><span class="go">Cədvəli aç →</span></a>'; }).join('') + '</div></section>';
    if (nf.length) h += '<section class="sec"><div class="sec-h"><h2>Proqnoz edilməyən komponentlər</h2><p>Modul bunları qiymətləndirmir; səbəb və mümkün əvəzedicilər.</p></div><div class="card itbl-wrap"><table class="itbl"><thead><tr><th class="l">Komponent</th><th class="l">Səbəb</th><th class="l">Əvəzedici göstəricilər</th></tr></thead><tbody>' +
      nf.map(function (r) { return '<tr><td class="lab">' + U.esc(r.l) + '<span class="u">' + U.esc(r.id) + '</span></td><td class="small" style="white-space:normal">' + U.esc(r.why) + '</td><td class="small">' +
        r.alt.map(function (a) { var s = U.byId[a]; return s ? '<a href="' + U.href(s) + '">' + U.esc(s.e) + '</a>' : U.esc(a); }).join(', ') + '</td></tr>'; }).join('') + '</tbody></table></div></section>';
    return h;
  };
  U.spark = function (s, W, H) {
    W = W || 240; H = H || 40;
    var k = U.scOf(s), pts = (s.h || []).filter(function (p) { return p[0] <= 2025; }).slice(-10).map(function (p) { return [p[0], p[1]]; });
    if (U.isNum(U.b25(s, k)) && !pts.some(function (p) { return p[0] === 2025; })) pts.push([2025, U.b25(s, k)]);
    U.YEARS.forEach(function (y, i) { if (U.isNum(s.s[k][i])) pts.push([y, s.s[k][i]]); });
    if (pts.length < 2) return '';
    var x0 = pts[0][0], lo = Infinity, hi = -Infinity;
    pts.forEach(function (p) { lo = Math.min(lo, p[1]); hi = Math.max(hi, p[1]); });
    if (hi === lo) { hi += 1; lo -= 1; }
    var X = function (y) { return 3 + (y - x0) * (W - 8) / (2030 - x0 || 1); }, Y = function (v) { return 4 + (H - 8) * (1 - (v - lo) / (hi - lo)); };
    var line = function (a, c, w) { return '<polyline fill="none" stroke="' + c + '" stroke-width="' + w + '" stroke-linejoin="round" points="' + a.map(function (p) { return X(p[0]).toFixed(1) + ',' + Y(p[1]).toFixed(1); }).join(' ') + '"/>'; };
    return '<svg class="spark" viewBox="0 0 ' + W + ' ' + H + '" aria-hidden="true"><rect x="' + X(2025.5) + '" y="0" width="' + (W - X(2025.5)) + '" height="' + H + '" fill="#F2F7FB"/>' +
      line(pts.filter(function (p) { return p[0] <= 2025; }), '#738190', 1.5) + line(pts.filter(function (p) { return p[0] >= 2025; }), U.SCC[k], 2) + '</svg>';
  };
  function tools(f, key, n) {
    var mode = MODE[key] || 'l', sc = SCF[key] || 'all';
    return '<div class="toolbar">' + U.seg('gmode', [['l', 'Səviyyə'], ['g', 'İllik artım'], ['b', 'İkisi']], mode) +
      U.seg('gsc', [['all', 'Bütün ssenarilər'], ['B', 'Əsas'], ['A', 'Mənfi'], ['R', 'İslahat']], sc) +
      '<span class="small muted">' + n + ' komponent</span><span style="margin-left:auto;display:flex;gap:8px"><button class="btn sm" id="g-csv">CSV</button><button class="btn sm pri" id="g-xlsx">Excel (.xlsx)</button></span></div>';
  }
  function ks(key) { var sc = SCF[key] || 'all'; return sc === 'all' ? U.SC : [sc]; }
  U.viewGroup = function (f, gi) {
    var g = U.groups(f.c)[gi], list = U.members(f.c, g), key = f.c + '|' + gi;
    return '<div class="eyebrow">' + f.c + ' · qrup</div><h1 class="h1" style="font-size:24px;margin-top:4px">' + U.esc(g) + '</h1>' + tools(f, key, list.length) +
      '<div class="card itbl-wrap">' + U.groupTable(list, MODE[key] || 'l', ks(key)) + '</div>' +
      '<p class="small muted">Artım xanalarının rəngi: yaşıl — artım, qırmızı — azalma. Faiz və pay göstəricilərində dəyişmə faiz bəndi ilə verilir. Komponentin adına klikləyin — qrafik, tənliklər və dayanıqlıq açılır.</p>';
  };
  U.viewAll = function (f) {
    var list = U.fr(f.c), key = f.c + '|all';
    return '<div class="eyebrow">' + f.c + ' · bütün komponentlər</div><h1 class="h1" style="font-size:24px;margin-top:4px">' + U.esc(f.full) + ': 2026–2030 cədvəli</h1>' + tools(f, key, list.length) +
      '<div class="card itbl-wrap">' + U.groupTable(list, MODE[key] || 'l', ks(key), { groups: true }) + '</div>';
  };
  U.bindGroup = function (v, f, gi) {
    var key = f.c + '|' + (gi == null ? 'all' : gi), list = gi == null ? U.fr(f.c) : U.members(f.c, U.groups(f.c)[gi]);
    v.onclick = function (e) {
      var b = e.target.closest('#gmode [data-v], #gsc [data-v]');
      if (b) { if (b.parentNode.id === 'gmode') MODE[key] = b.getAttribute('data-v'); else SCF[key] = b.getAttribute('data-v'); U.route(true); return; }
      var name = f.c + '_' + (gi == null ? 'hamisi' : 'qrup_' + gi);
      if (e.target.id === 'g-csv') U.csvList(name + '.csv', list, ks(key));
      if (e.target.id === 'g-xlsx') U.download(name + '.xlsx', U.xlsx([{ name: f.c + ' 2026-2030', rows: [U.HEAD].concat([].concat.apply([], list.map(function (s) { return U.seriesRows(s, ks(key)); }))), widths: [6, 26, 30, 44, 16, 9, 12] }]));
    };
  };
})();
