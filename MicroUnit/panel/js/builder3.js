/* builder3.js — Ssenari qurucusu, part 3: results of a run (or of a saved scenario) against the chosen base scenario:
   headline tiles, per-module chart and the full 2026–2030 table of every component with the difference. */
(function () {
  'use strict';
  var U = window.U, B = U.B, PER = 120;
  var RV = B.rv = { mod: 'FR1', g: '', q: '', only: true, mode: 'b', page: 0, sel: 'fr1:rgdp' };
  U.bSetResult = function (raw, info) {
    var res = {}, warn = [];
    var R = (raw && raw.results) || {};
    Object.keys(R).forEach(function (m) {
      var ser = R[m].series || {};
      Object.keys(ser).forEach(function (id) { var o = ser[id]; res[id] = [2025].concat(U.YEARS).map(function (y) { var v = o[y] != null ? o[y] : o[String(y)]; return U.isNum(v) ? v : null; }); });
      (R[m].warnings || []).forEach(function (w) { warn.push(m + ': ' + (typeof w === 'string' ? w : JSON.stringify(w))); });
    });
    var er = (raw && raw.errors) || [], wr = (raw && raw.warnings) || [], sk = (raw && raw.skipped) || [];
    var each = function (x, pre) { if (Array.isArray(x)) x.forEach(function (w) { warn.push(pre + (typeof w === 'string' ? w : JSON.stringify(w))); });
      else if (x && typeof x === 'object') Object.keys(x).forEach(function (k) { warn.push(pre + k + ': ' + (typeof x[k] === 'string' ? x[k] : JSON.stringify(x[k]))); }); };
    each(er, 'xəta — '); each(wr, ''); each(sk, 'buraxılıb — ');
    B.raw = raw; B.res = res; B.resInfo = info; B.warn = warn;
  };
  U.bSetCompact = function (series, info) { B.raw = null; B.res = series; B.resInfo = info; B.warn = []; };
  function refK() { return U.SCK[(B.resInfo || {}).base] || 'B'; }
  U.bDiff = function (s, alt, base) {
    if (!U.isNum(alt) || !U.isNum(base)) return null;
    return U.isRate(s) ? alt - base : (base !== 0 ? (alt / base - 1) * 100 : null);
  };
  function changed(s) {
    var a = B.res[s.i], k = refK(); if (!a || !s.s || !s.s[k]) return false;
    return s.s[k].some(function (v, i) { var d = U.bDiff(s, a[i + 1], v); return U.isNum(d) && Math.abs(d) > 1e-6; });
  }
  function list() {
    var w = U.fold(RV.q.trim()).split(/\s+/).filter(Boolean);
    return U.fr(RV.mod).filter(function (s) { return B.res[s.i] && s.s && (!RV.g || s.g === RV.g) && (!RV.only || changed(s)) && w.every(function (x) { return U.fold(s.e + ' ' + s.i).indexOf(x) >= 0; }); });
  }
  function tile(id) {
    var s = U.byId[id], a = B.res[id], k = refK(); if (!s || !a) return '';
    var d = U.bDiff(s, a[5], s.s[k][4]);
    return '<div class="kpi" data-sel="' + U.esc(id) + '"><div class="l">' + s.f + ' · ' + U.esc(s.e) + '</div><div class="v">' + U.nf(a[5], s.d) + '<small>2030</small></div>' +
      '<div class="small muted">' + U.SCN[k] + ': ' + U.nf(s.s[k][4], s.d) + ' ' + U.esc(s.u) + '</div><div class="d ' + U.trend(d) + '">fərq: ' + U.sg(d, 2) + ' ' + U.gunit(s) + '</div></div>';
  }
  U.bResultsHtml = function () {
    if (!B.res) return '<div class="card pad muted">Nəticə hələ yoxdur. Fərziyyələri dəyişin və «Hesabla» düyməsini basın, və ya «Saxlanmış ssenarilər»dən birini açın.</div>';
    var k = refK(), info = B.resInfo || {}, l = list(), pages = Math.max(1, Math.ceil(l.length / PER));
    if (RV.page >= pages) RV.page = 0;
    var vis = l.slice(RV.page * PER, (RV.page + 1) * PER), cols = RV.mode === 'b' ? ['l', 'd'] : [RV.mode];
    var nch = {}; U.MODS.forEach(function (m) { nch[m] = U.fr(m).filter(function (s) { return B.res[s.i] && changed(s); }).length; });
    var h = '<div class="sec-h"><h2>Nəticələr: «' + U.esc(info.name || 'ssenari') + '» — ' + U.SCN[k] + ' ssenarisi ilə müqayisədə</h2><p>Fərq: səviyyə göstəricilərində %, faiz və pay göstəricilərində faiz bəndi. Kafelə və ya sətrə klikləyin — qrafik dəyişir.</p></div>' +
      (B.warn && B.warn.length ? '<details class="card pad" style="margin-bottom:12px"><summary>Mühərrik xəbərdarlıqları: ' + B.warn.length + '</summary><ul class="small">' + B.warn.slice(0, 40).map(function (w) { return '<li>' + U.esc(w) + '</li>'; }).join('') + '</ul></details>' : '') +
      '<div class="kpis" id="r-tiles">' + U.META.scen.map(tile).join('') + '</div>' +
      '<div class="card pad" style="margin-top:14px"><div id="r-ch"></div></div>' +
      '<div class="card" style="margin-top:14px"><div class="toolbar" style="margin:12px 14px"><div class="sectabs" id="r-mod">' + U.MODS.map(function (m) { return '<button type="button" class="stab' + (m === RV.mod ? ' on' : '') + '" data-v="' + m + '">' + m + ' <span class="cnt">' + nch[m] + '</span></button>'; }).join('') + '</div>' +
      '<select id="r-g" class="btn sm">' + U.opt('', 'Bütün qruplar', RV.g) + U.groups(RV.mod).map(function (g) { return U.opt(g, g, RV.g); }).join('') + '</select>' +
      '<input type="search" id="r-q" placeholder="komponent…" value="' + U.esc(RV.q) + '" style="height:28px;border:1px solid var(--line);border-radius:7px;padding:0 8px">' +
      '<label class="small"><input type="checkbox" id="r-only"' + (RV.only ? ' checked' : '') + '> yalnız dəyişənlər</label>' + U.seg('r-mode', [['l', 'Səviyyə'], ['d', 'Fərq'], ['b', 'İkisi']], RV.mode) +
      '<button type="button" class="btn sm" id="r-csv" style="margin-left:auto">CSV</button></div>' +
      '<div class="small muted" style="margin:0 14px 8px">' + l.length + ' komponent · səhifə ' + (RV.page + 1) + ' / ' + pages + ' · hər komponent üçün iki sətir: ssenari və ' + U.SCN[k] + '</div>' +
      '<div class="itbl-wrap"><table class="itbl"><thead><tr><th class="l">Komponent</th><th class="l"></th><th>2025</th>' +
      cols.map(function (c) { return U.YEARS.map(function (y) { return '<th class="fc">' + y + (c === 'd' ? '<span class="st">fərq</span>' : '') + '</th>'; }).join(''); }).join('') + '</tr></thead><tbody>';
    vis.forEach(function (s) {
      var a = B.res[s.i], bv = s.s[k];
      h += '<tr data-sel="' + U.esc(s.i) + '" class="click"><td class="lab" rowspan="2"><b>' + U.esc(s.e) + '</b><span class="u">' + U.esc(s.u) + '</span></td><td><b style="color:' + U.SCC.C + '">Ssenari</b></td><td class="n">' + U.nf(U.isNum(a[0]) ? a[0] : U.b25(s, k), s.d) + '</td>';
      cols.forEach(function (c) { h += U.YEARS.map(function (y, i) { var d = U.bDiff(s, a[i + 1], bv[i]); return c === 'd' ? '<td class="n fc dcell" style="' + U.heat(d, U.isRate(s) ? 1 : 3) + '">' + U.sg(d, 2) + (U.isNum(d) ? '<small> ' + U.gunit(s) + '</small>' : '') + '</td>' : '<td class="n fc"><b>' + U.nf(a[i + 1], s.d) + '</b></td>'; }).join(''); });
      h += '</tr><tr class="sub" data-sel="' + U.esc(s.i) + '"><td style="color:' + U.SCC[k] + '">' + U.SCN[k] + '</td><td class="n">' + U.nf(U.b25(s, k), s.d) + '</td>';
      cols.forEach(function (c) { h += U.YEARS.map(function (y, i) { return c === 'd' ? '<td class="n fc"></td>' : '<td class="n fc">' + U.nf(bv[i], s.d) + '</td>'; }).join(''); });
      h += '</tr>';
    });
    h += '</tbody></table></div><div class="toolbar" style="margin:10px 14px"><button type="button" class="btn sm" id="r-prev"' + (RV.page ? '' : ' disabled') + '>← Əvvəlki</button><button type="button" class="btn sm" id="r-next"' + (RV.page < pages - 1 ? '' : ' disabled') + '>Növbəti →</button></div></div>';
    return h;
  };
  U.bResultsBind = function () {
    var s = U.byId[RV.sel], k = refK();
    if (!s || !B.res[RV.sel]) { s = U.fr(RV.mod).filter(function (x) { return B.res[x.i] && x.s; })[0]; if (s) RV.sel = s.i; }
    if (s && U.$('#r-ch')) U.compareChart(U.$('#r-ch'), s, { label: U.SCN[k] + ' ssenari', y: s.s[k], k: k }, { label: (B.resInfo || {}).name || 'Ssenari', y: B.res[s.i].slice(1) }, { h: 330 });
    var ch = U.$('#r-ch'); if (ch && s) ch.setAttribute('data-title', s.f + ' · ' + s.e);
    var q = U.$('#r-q');
    if (q) q.oninput = U.debounce(function () { RV.q = q.value; RV.page = 0; redraw(); var t = U.$('#r-q'); t.focus(); }, 300);
    var g = U.$('#r-g'); if (g) g.onchange = function () { RV.g = g.value; RV.page = 0; redraw(); };
    var o = U.$('#r-only'); if (o) o.onchange = function () { RV.only = o.checked; RV.page = 0; redraw(); };
  };
  function redraw() { var r = U.$('#b-results'); if (r) { r.innerHTML = U.bResultsHtml(); U.bResultsBind(); } }
  U.bRedraw = redraw;
  U.bResultsClick = function (e) {
    var t = e.target, s;
    if ((s = t.closest('#r-mod [data-v]'))) { RV.mod = s.getAttribute('data-v'); RV.g = ''; RV.page = 0; var f = U.fr(RV.mod).filter(function (x) { return B.res && B.res[x.i] && changed(x); })[0]; if (f) RV.sel = f.i; redraw(); return true; }
    if ((s = t.closest('#r-mode [data-v]'))) { RV.mode = s.getAttribute('data-v'); redraw(); return true; }
    if (t.id === 'r-prev') { RV.page--; redraw(); return true; }
    if (t.id === 'r-next') { RV.page++; redraw(); return true; }
    if (t.id === 'r-csv') {
      var k = refK(), rows = [['FR', 'İdentifikator', 'Komponent', 'Vahid', 'Sıra', '2025'].concat(U.YEARS.map(String))];
      U.S.forEach(function (x) { var a = B.res[x.i]; if (!a || !x.s || !x.s[k]) return; rows.push([x.f, x.i, x.e, x.u, 'Ssenari'].concat(a)); rows.push([x.f, x.i, x.e, x.u, U.SCN[k], U.b25(x, k)].concat(x.s[k])); });
      U.download('ssenari_' + ((B.resInfo || {}).name || 'netice').replace(/[^\wəöüğışçİ]+/gi, '_') + '.csv', new Blob([U.csvOf(rows)], { type: 'text/csv' })); return true;
    }
    if ((s = t.closest('[data-sel]')) && t.closest('#b-results')) { RV.sel = s.getAttribute('data-sel'); var x = U.byId[RV.sel]; if (x && x.f !== RV.mod) RV.mod = x.f; U.bResultsBind(); U.$('#r-ch').scrollIntoView({ behavior: 'smooth', block: 'center' }); return true; }
    return false;
  };
})();
