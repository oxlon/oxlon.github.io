/* eqviews.js — «Tənliklər» index per FR (every estimated equation incl. variants; filters: sub-task, used in forecast,
   verdict, text) and «Dayanıqlıq» overview (verdict counts, failed tests, coefficient tornado per component). */
(function () {
  'use strict';
  var U = window.U, F = {}, TOR = {};
  function flt(f) { return F[f.c] || (F[f.c] = { st: '', u: '', v: '', q: '' }); }
  function rows(f) {
    var o = flt(f), w = U.fold(o.q.trim()).split(/\s+/).filter(Boolean);
    return U.eqRows(f.c).filter(function (e) {
      return (!o.st || e.st === o.st) && (!o.u || (o.u === '1') === !!e.used) && (!o.v || (e.v || '—') === o.v) &&
        w.every(function (x) { return U.fold(e.id + ' ' + e.t + ' ' + e.est).indexOf(x) >= 0; });
    });
  }
  function num(v, d) { return U.isNum(v) ? U.nf(v, d) : '—'; }
  function uu(v) { return U.isNum(v) ? '<b class="' + (v < 1 ? 'up' : 'down') + '">' + U.nf(v, 2) + '</b>' : '—'; }
  U.viewEqIndex = function (f) {
    var o = flt(f), sts = [], all = U.eqRows(f.c);
    all.forEach(function (e) { if (sts.indexOf(e.st) < 0) sts.push(e.st); });
    var l = rows(f).map(function (e, i) { return [sts.indexOf(e.st), i, e]; }).sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; }).map(function (x) { return x[2]; }), hd = U.eqHdr(f.c);
    var h = '<div class="eyebrow">' + f.c + ' · tənliklər</div><h1 class="h1" style="font-size:24px;margin-top:4px">Tənliklər: ' + all.length + ' qiymətləndirmə</h1>' +
      '<p class="lead" style="font-size:14.5px">Dəftərdə qiymətləndirilmiş hər tənlik — proqnozda istifadə olunanlar, variantlar və rədd edilmiş spesifikasiyalar. Sətrə klikləyin — tam reqressiya nəticəsi açılır.' +
      (hd.mode ? ' Məlumat rejimi: <b>' + (hd.mode === 'OBSERVED' ? 'müşahidə' : U.esc(hd.mode)) + '</b>.' : '') + '</p>' +
      '<div class="toolbar"><input type="search" id="eq-q" placeholder="Axtar: id, ad, üsul…" value="' + U.esc(o.q) + '">' +
      '<select id="eq-st" class="btn sm">' + U.opt('', 'Bütün alt-bölmələr', o.st) + sts.map(function (s) { return U.opt(s, s, o.st); }).join('') + '</select>' +
      '<select id="eq-u" class="btn sm">' + U.opt('', 'Hamısı', o.u) + U.opt('1', 'Proqnozda istifadə olunanlar', o.u) + U.opt('0', 'Variantlar / rədd edilmişlər', o.u) + '</select>' +
      '<select id="eq-v" class="btn sm">' + U.opt('', 'Bütün hökmlər', o.v) + ['stabil', 'qismən stabil', 'qeyri-stabil', '—'].map(function (v) { return U.opt(v, v === '—' ? 'hökm yoxdur' : v, o.v); }).join('') + '</select>' +
      '<span class="small muted">' + l.length + ' / ' + all.length + '</span></div>' +
      '<div class="card itbl-wrap"><table class="itbl eqtbl"><thead><tr><th class="l">Tənlik</th><th class="l">Üsul</th><th>n</th><th>R²</th><th>düz. R²</th><th>DW</th><th>koint. p</th><th>U (TG)</th><th>U (SA)</th><th class="l">Hökm</th></tr></thead><tbody>';
    var last = null;
    l.forEach(function (e) {
      if (e.st !== last) { last = e.st; h += '<tr class="grow"><td colspan="10">' + U.esc(e.st) + '</td></tr>'; }
      h += '<tr data-eq="' + U.esc(e.id) + '" class="click"><td class="lab" style="white-space:normal"><b>' + U.esc(e.t) + '</b><span class="u">' + U.esc(e.id) + '</span></td><td class="small">' + U.esc(e.est) + '</td>' +
        '<td class="n">' + (e.n == null ? '—' : e.n) + '</td><td class="n">' + num(e.r2, 3) + '</td><td class="n">' + num(e.r2a, 3) + '</td><td class="n">' + num(e.dw, 2) + '</td><td class="n">' + U.pf(e.cp) + '</td>' +
        '<td class="n">' + uu(e.urw) + '</td><td class="n">' + uu(e.uc) + '</td><td class="chipcell">' + U.vchip(e.v) + ' ' + U.uchip(e) + '</td></tr>';
    });
    h += '</tbody></table></div>';
    if (hd.rule) h += '<details class="faq" style="margin-top:12px"><summary>Dayanıqlıq hökmünün qaydası və konvensiyalar</summary><p class="small">' + U.esc(hd.rule) + '</p><p class="small">' + U.esc(hd.conv || '') + '</p></details>';
    return h;
  };
  U.bindEqIndex = function (v, f, openId) {
    var o = flt(f);
    var re = function () { U.route(true); };
    U.$('#eq-q').oninput = U.debounce(function (e) { o.q = e.target.value; var p = e.target.selectionStart; re(); var t = U.$('#eq-q'); t.focus(); t.setSelectionRange(p, p); }, 250);
    U.$('#eq-st').onchange = function (e) { o.st = e.target.value; re(); };
    U.$('#eq-u').onchange = function (e) { o.u = e.target.value; re(); };
    U.$('#eq-v').onchange = function (e) { o.v = e.target.value; re(); };
    if (openId) U.openEq(openId, function () { history.replaceState(null, '', '#/' + f.slug + '/tenlik'); });
  };
  U.viewRob = function (f) {
    var rc = U.robCounts(f.c), l = U.eqRows(f.c).filter(function (e) { return e.used; });
    var comps = U.fr(f.c).filter(function (s) { return (window.MICRO.SENS || {})[s.i]; });
    var h = '<div class="eyebrow">' + f.c + ' · dayanıqlıq</div><h1 class="h1" style="font-size:24px;margin-top:4px">Modellərin dayanıqlığı</h1>' +
      '<p class="lead" style="font-size:14.5px">Proqnozda istifadə olunan hər tənlik üçün: əmsallar nümunə genişləndikcə (rekursiv) və bir il çıxarıldıqda işarəsini saxlayırmı, struktur qırılma (Chow, CUSUM) varmı, və nümunədən kənar yoxlamada sadə etalonları keçirmi.</p>' +
      '<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(170px,1fr))">' +
      [['stabil', 'up'], ['qismən stabil', 'flat'], ['qeyri-stabil', 'down'], ['', 'flat']].map(function (x) {
        return '<div class="kpi" style="cursor:default"><div class="l">' + (x[0] ? U.vchip(x[0]) : 'hökm tətbiq olunmur') + '</div><div class="v">' + (rc.c[x[0]] || 0) + '<small>/ ' + rc.used + '</small></div><div class="d ' + x[1] + '">proqnozda istifadə olunan tənlik</div></div>'; }).join('') + '</div>';
    if (comps.length) {
      var cur = TOR[f.c] && U.byId[TOR[f.c]] ? TOR[f.c] : comps[0].i;
      h += '<section class="sec"><div class="sec-h"><h2>Əmsallara həssaslıq (tornado)</h2><p>Əmsal ±1 standart xəta dəyişdikdə seçilmiş komponentin 2030-cu il dəyəri neçə faiz dəyişir.</p></div><div class="card pad"><div class="toolbar" style="margin-top:0"><label class="small muted">Komponent</label><select id="tor-sel" class="btn sm">' +
        comps.map(function (s) { return U.opt(s.i, s.e, cur); }).join('') + '</select></div><div id="tor"></div></div></section>';
    }
    h += '<section class="sec"><div class="sec-h"><h2>Tənliklər üzrə hökmlər</h2><p>Sətrə klikləyin — rekursiv qrafik, Chow və CUSUM testləri, bir ili çıxarmaqla aralıqlar.</p></div><div class="card itbl-wrap"><table class="itbl eqtbl"><thead><tr><th class="l">Tənlik</th><th class="l">Hökm</th><th class="l">Uğursuz testlər</th><th>koint. p</th><th>U (TG)</th><th>U (SA)</th></tr></thead><tbody>' +
      l.map(function (e) { return '<tr data-eq="' + U.esc(e.id) + '" class="click"><td class="lab" style="white-space:normal"><b>' + U.esc(e.t) + '</b><span class="u">' + U.esc(e.id) + '</span></td><td>' + U.vchip(e.v) + '</td><td class="small" style="white-space:normal">' + U.esc(e.ft || '—') + '</td><td class="n">' + U.pf(e.cp) + '</td><td class="n">' + uu(e.urw) + '</td><td class="n">' + uu(e.uc) + '</td></tr>'; }).join('') +
      '</tbody></table></div></section>';
    return h;
  };
  U.bindRob = function (v, f) {
    var sel = U.$('#tor-sel'); if (!sel) return;
    U.tornado(U.$('#tor'), window.MICRO.SENS[sel.value]);
    sel.onchange = function () { TOR[f.c] = sel.value; U.tornado(U.$('#tor'), window.MICRO.SENS[sel.value]); };
  };
})();
