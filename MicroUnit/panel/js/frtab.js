/* frtab.js — one tab per requirement: indicator tree, indicator view (KPIs, chart, explicit table), group matrix. */
(function () {
  'use strict';
  var U = window.U, META = window.MICRO.META;
  var VAR = {}, MODE = {}, Q = {};
  function frOf(slug) { return META.frs.filter(function (f) { return f.slug === slug; })[0]; }
  function members(code, g) { return U.S.filter(function (s) { return s.f === code && s.g === g; }); }
  function variants(list) { var o = []; list.forEach(function (s) { if (o.indexOf(s.v) < 0) o.push(s.v); }); return o; }
  function entities(list) { var o = [], seen = {}; list.forEach(function (s) { if (!seen[s.e]) { seen[s.e] = 1; o.push(s); } }); return o; }
  function pickVar(code, g, e) {
    var l = members(code, g).filter(function (s) { return s.e === e; }), want = VAR[code + '|' + g];
    return l.filter(function (s) { return s.v === want; })[0] || l[0];
  }
  function tree(f, cur) {
    var q = U.fold(Q[f.c] || ''), h = '<div class="card tree" data-tour="tree"><input type="search" id="tq" placeholder="Göstərici axtar…" value="' + U.esc(Q[f.c] || '') + '">';
    U.groups(f.c).forEach(function (g, gi) {
      var ents = entities(members(f.c, g)).filter(function (s) { return !q || U.fold(s.e + ' ' + s.g).indexOf(q) >= 0; });
      if (!ents.length) return;
      h += '<div class="tsec">' + U.esc(g) + ' <span class="muted">' + ents.length + '</span></div>' +
        '<a class="tsheet' + (cur === 'g' + gi ? ' on' : '') + '" href="#/' + f.slug + '/g/' + gi + '"><b>▦ Hamısı</b> — cədvəl</a>' +
        ents.map(function (s) { return '<a class="tsheet' + (cur === 'e' + gi + '|' + s.e ? ' on' : '') + '" href="#/' + f.slug + '/s/' + pickVar(f.c, g, s.e).n + '">' + U.esc(s.e) + '</a>'; }).join('');
    });
    (EXTRA[f.c] || []).forEach(function (x) { h += '<div class="tsec">Əlavə</div><a class="tsheet' + (cur === 'x' + x[0] ? ' on' : '') + '" href="#/' + f.slug + '/x/' + x[0] + '">' + x[1] + '</a>'; });
    return h + '</div>';
  }
  var EXTRA = { FR10: [['ew', '⚑ Erkən xəbərdarlıq']], FR12: [['io', '⚖ Ssenari təhlili (sənaye iqtisadiyyatı)'], ['ew', '⚑ Erkən xəbərdarlıq']] };
  function seg(id, opts, on) {
    return '<div class="seg" id="' + id + '">' + opts.map(function (o) { return '<button data-v="' + U.esc(o[0]) + '" class="' + (o[0] === on ? 'on' : '') + '">' + U.esc(o[1]) + '</button>'; }).join('') + '</div>';
  }
  function kpi(l, val, sub, cls) { return '<div class="kpi" style="cursor:default"><div class="l">' + l + '</div><div class="v">' + val + '</div><div class="d ' + (cls || 'flat') + '">' + sub + '</div></div>'; }
  function viewSeries(f, s) {
    var k = U.scOf(s), sib = members(f.c, s.g).filter(function (x) { return x.e === s.e; }), c = U.cagr(s, k), o = s.o;
    var lh = U.lastHist(s), gd = U.gdec(s);
    var h = '<div class="eyebrow">' + f.c + ' · ' + U.esc(s.g) + '</div><div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:4px"><h1 class="h1" style="font-size:24px">' + U.esc(s.e) + '</h1>' +
      '<span style="margin-left:auto;display:flex;gap:8px"><button class="btn sm" id="b-dr">ⓘ Təfsilat</button><button class="btn sm" id="b-csv">' + U.icon('dl').replace('<svg', '<svg width="14" height="14"') + ' CSV</button></span></div>' +
      '<p class="small" style="margin:6px 0 10px">' + (s.u ? '<span class="chip">' + U.esc(s.u) + '</span> ' : '') + (s.q ? '<span class="chip acc" title="5-ci və 95-ci faizlər arasındakı aralıq (Əsas ssenari)">5–95 % zolağı</span> ' : '') +
      (U.scens(s).length === 1 ? '<span class="chip warn" title="Modul bu sıra üçün yalnız Əsas ssenarini ixrac edir">yalnız Əsas ssenari</span> ' : '') + (s.nt ? '<span class="chip">' + U.esc(s.nt) + '</span>' : '') + '</p>';
    if (sib.length > 1) h += '<div class="toolbar" style="margin-top:0"><span class="small muted">Göstərici:</span>' + seg('vseg', sib.map(function (x) { return [String(x.n), x.v || 'əsas']; }), String(s.n)) + '</div>';
    h += '<div class="kpis k4">' +
      kpi(lh && lh[0] === 2025 ? '2025 — faktiki' : '2025 — başlanğıc', U.nf(s.b, s.d) + '<small>' + U.esc(s.u) + '</small>', lh ? 'son faktiki il: ' + lh[0] : 'tarixi sıra yoxdur') +
      kpi('2030 — ' + U.SCN[k] + ' ssenari', U.nf(s.s[k][4], s.d) + '<small>' + U.esc(s.u) + '</small>', U.YEARS.length + ' illik proqnoz', 'dl') +
      kpi(s.k === 'rate' ? 'Dəyişmə 2025 → 2030' : 'Orta illik artım 2026–2030', U.sg(c, gd) + '<small>' + U.gunit(s) + '</small>', s.k === 'rate' ? 'faiz bəndi' : 'mürəkkəb illik temp', U.trend(c)) +
      (s.q ? kpi('2030 — 5–95 % zolağı', U.nf(s.q[0][4], s.d) + ' … ' + U.nf(s.q[1][4], s.d), 'Əsas ssenari, 90 % aralıq') :
        o ? kpi('Theil U: təsadüfi gəzişmə', U.nf(o.rw, 2), o.rw < 1 ? 'model etalondan yaxşıdır' : 'model etalondan yaxşı deyil', o.rw < 1 ? 'up' : 'down') :
          kpi('Mənbə', '<span style="font-size:14px">' + U.esc(s.src) + '</span>', 'çıxış faylı')) + '</div>';
    h += '<div class="card pad" style="margin-top:14px"><div id="ch"></div></div>' +
      '<div class="card" style="margin-top:14px"><div class="grp-h">İllər üzrə proqnoz — açıq dəyərlər</div><div class="itbl-wrap">' + U.yearTable(s) + '</div></div>';
    return h;
  }
  function viewGroup(f, gi) {
    var g = U.groups(f.c)[gi], list = members(f.c, g), vs = variants(list), key = f.c + '|' + g, v = VAR[key];
    if (vs.indexOf(v) < 0) v = vs[0];
    var mode = MODE[key] || 'l', rows = list.filter(function (s) { return s.v === v; });
    return '<div class="eyebrow">' + f.c + ' · qrup</div><h1 class="h1" style="font-size:24px;margin-top:4px">' + U.esc(g) + ' — hamısı</h1>' +
      '<div class="toolbar">' + (vs.length > 1 ? seg('gvar', vs.map(function (x) { return [x, x || 'əsas']; }), v) : '') +
      seg('gmode', [['l', 'Səviyyə'], ['g', 'İllik artım']], mode) +
      '<span class="small muted">' + rows.length + ' göstərici · ssenari: ' + U.SCN[U.scen()] + ' · sətrə klikləyin — qrafik açılır</span>' +
      '<button class="btn sm" id="g-csv" style="margin-left:auto">CSV</button></div>' +
      '<div class="card itbl-wrap" style="max-height:none">' + U.matrix(rows, mode) + '</div>' +
      '<p class="small muted">Artım xanalarının rəngi: yaşıl — artım, qırmızı — azalma; rəng nə qədər tünd, dəyişmə o qədər böyük. Faiz göstəricilərində dəyişmə faiz bəndi ilə verilir.</p>';
  }
  U.pages.__fr = function (v, p) {
    var f = frOf(p[0]), kind = p[1], arg = p[2], s = null, cur = '', body;
    if (kind === 's' && U.S[+arg] && U.S[+arg].f === f.c) { s = U.S[+arg]; VAR[f.c + '|' + s.g] = s.v; cur = 'e' + U.groups(f.c).indexOf(s.g) + '|' + s.e; body = viewSeries(f, s); }
    else if (kind === 'g' && U.groups(f.c)[+arg]) { cur = 'g' + arg; body = viewGroup(f, +arg); }
    else if (kind === 'x' && U.extra) { cur = 'x' + arg; body = U.extra(f, arg); }
    else { var first = U.fr(f.c)[0]; s = first; cur = 'e0|' + s.e; body = viewSeries(f, s); }
    v.innerHTML = '<div class="small muted" style="margin-bottom:10px">' + U.esc(f.lead) + '</div><div class="exp-layout">' + tree(f, cur) + '<div id="main-col" style="min-width:0">' + body + '</div></div>';
    if (s) {
      U.seriesChart(U.$('#ch'), s);
      U.$('#b-dr').onclick = function () { U.openDrawer(s); };
      if (p[3] === 'info') setTimeout(function () { U.openDrawer(s); }, 0);
      U.$('#b-csv').onclick = function () { U.download(f.c + '_' + s.e.replace(/[^\wəöüğışçİ]+/gi, '_') + '.csv', new Blob([U.csvOf([U.HEAD].concat(U.seriesRows(s)))], { type: 'text/csv' })); };
      var vs = U.$('#vseg'); if (vs) vs.onclick = function (e) { var b = e.target.closest('[data-v]'); if (b) location.hash = '#/' + f.slug + '/s/' + b.getAttribute('data-v'); };
    }
    if (kind === 'g') {
      var g = U.groups(f.c)[+arg], key = f.c + '|' + g;
      v.onclick = function (e) {
        var b = e.target.closest('#gvar [data-v], #gmode [data-v]');
        if (b) { if (b.parentNode.id === 'gvar') VAR[key] = b.getAttribute('data-v'); else MODE[key] = b.getAttribute('data-v'); U.route(true); return; }
        if (e.target.id === 'g-csv') { var vv = VAR[key] !== undefined ? VAR[key] : variants(members(f.c, g))[0]; var rows = members(f.c, g).filter(function (x) { return x.v === vv; });
          U.download(f.c + '_qrup.csv', new Blob([U.csvOf([U.HEAD].concat([].concat.apply([], rows.map(U.seriesRows))))], { type: 'text/csv' })); return; }
        var tr = e.target.closest('tr[data-n]'); if (tr) location.hash = '#/' + f.slug + '/s/' + tr.getAttribute('data-n');
      };
    }
    var tq = U.$('#tq');
    tq.oninput = function () { Q[f.c] = tq.value; var pos = tq.selectionStart; U.route(true); var t = U.$('#tq'); t.focus(); t.setSelectionRange(pos, pos); };
  };
  META.frs.forEach(function (f) { U.pages[f.slug] = U.pages.__fr; });
})();
