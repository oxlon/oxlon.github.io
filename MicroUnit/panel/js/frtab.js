/* frtab.js — one tab per requirement. Routes: #/fr1 (overview) · #/fr1/c/<id> (component) · #/fr1/g/<n> (group table)
   · #/fr1/hamisi (every component) · #/fr1/tenlik[/<eq id>] (equations) · #/fr1/dayaniqliq (robustness) · #/fr10/x/ew. */
(function () {
  'use strict';
  var U = window.U, Q = {};
  U.FRX = { FR10: [['ew', '⚑ Erkən xəbərdarlıq']], FR12: [['io', '⚖ Ssenari təhlili (sənaye iqtisadiyyatı)'], ['ew', '⚑ Erkən xəbərdarlıq']] };
  function tree(f, cur, curG) {
    var q = U.fold(Q[f.c] || ''), sl = '#/' + f.slug;
    var h = '<div class="card tree" data-tour="tree"><input type="search" id="tq" placeholder="Komponent axtar…" value="' + U.esc(Q[f.c] || '') + '">' +
      '<a class="tsheet' + (cur === 'o' ? ' on' : '') + '" href="' + sl + '"><b>Ümumi baxış</b></a>' +
      '<a class="tsheet' + (cur === 'all' ? ' on' : '') + '" href="' + sl + '/hamisi"><b>▦ Bütün komponentlər</b> — cədvəl</a>' +
      '<a class="tsheet' + (cur === 'eq' ? ' on' : '') + '" href="' + sl + '/tenlik"><b>ƒ Tənliklər</b> <span class="muted">' + U.eqRows(f.c).length + '</span></a>' +
      '<a class="tsheet' + (cur === 'rob' ? ' on' : '') + '" href="' + sl + '/dayaniqliq"><b>✓ Dayanıqlıq</b></a>';
    (U.FRX[f.c] || []).forEach(function (x) { h += '<a class="tsheet' + (cur === 'x' + x[0] ? ' on' : '') + '" href="' + sl + '/x/' + x[0] + '">' + x[1] + '</a>'; });
    U.groups(f.c).forEach(function (g, gi) {
      var ms = U.members(f.c, g).filter(function (s) { return !q || U.fold(s.e + ' ' + s.g + ' ' + s.i).indexOf(q) >= 0; });
      if (!ms.length) return;
      var open = q || gi === curG;
      h += '<details class="tgrp"' + (open ? ' open' : '') + '><summary>' + U.esc(g) + ' <span class="muted">' + ms.length + '</span></summary>' +
        '<a class="tsheet' + (cur === 'g' + gi ? ' on' : '') + '" href="' + sl + '/g/' + gi + '"><b>▦ Qrupun cədvəli</b></a>' +
        ms.map(function (s) { return '<a class="tsheet' + (cur === s.i ? ' on' : '') + '" href="' + U.href(s) + '">' + U.esc(s.e) + (s.im ? ' <span class="impdot" title="' + U.IMPLAB + '"></span>' : '') + '</a>'; }).join('') + '</details>';
    });
    return h + '</div>';
  }
  function kpi(l, val, sub, cls) { return '<div class="kpi" style="cursor:default"><div class="l">' + l + '</div><div class="v">' + val + '</div><div class="d ' + (cls || 'flat') + '">' + sub + '</div></div>'; }
  function viewComp(f, s) {
    var k = U.scOf(s), c = U.cagr(s, k), lh = U.lastHist(s), gd = U.gdec(s), q = s.q && (s.q[k] || s.q.B);
    var h = '<div class="eyebrow">' + f.c + ' · ' + U.esc(s.g) + '</div><div class="hrow"><h1 class="h1" style="font-size:24px">' + U.esc(s.e) + '</h1>' +
      '<span class="hbtns"><button class="btn sm" id="b-csv">' + U.icon('dl', 14) + ' CSV</button><a class="btn sm" href="#/hesabat?c=' + U.enc(s.i) + '">Hesabata əlavə et</a></span></div>' +
      '<p class="small" style="margin:6px 0 10px">' + (s.u ? '<span class="chip">' + U.esc(s.u) + '</span> ' : '') + '<code class="small">' + U.esc(s.i) + '</code> ' +
      (q ? '<span class="chip acc" title="5-ci və 95-ci faizlər arasındakı aralıq">5–95 % zolağı</span> ' : '') + (s.im ? '<span class="chip warn">' + Object.keys(s.im).length + ' il doldurulub</span> ' : '') +
      (s.nf ? '<span class="chip">proqnoz edilmir</span>' : '') + '</p>';
    if (s.nf) return h + '<div class="card pad">Modul bu komponent üçün proqnoz vermir; səbəb «Ümumi baxış» bölməsindəki siyahıdadır.</div>' + '<div class="card" style="margin-top:14px"><div class="itbl-wrap">' + U.histTable(s, 14) + '</div></div>';
    h += '<div class="kpis k4">' +
      kpi(U.lab25(s), U.nf(U.b25(s, k), s.d) + '<small>' + U.esc(s.u) + '</small>', lh ? 'son faktiki il: ' + lh[0] : 'tarixi sıra yoxdur') +
      kpi('2030 — ' + U.SCN[k] + ' ssenari', U.nf(s.s[k][4], s.d) + '<small>' + U.esc(s.u) + '</small>', '5 illik proqnoz') +
      kpi(U.isRate(s) ? 'Dəyişmə 2025 → 2030' : 'Orta illik artım 2026–2030', U.sg(c, gd) + '<small>' + U.gunit(s) + '</small>', U.isRate(s) ? 'faiz bəndi' : 'mürəkkəb illik temp', U.trend(c)) +
      (q ? kpi('2030 — 5–95 % zolağı', U.nf(q[0][4], s.d) + ' … ' + U.nf(q[1][4], s.d), U.SCN[s.q[k] ? k : 'B'] + ' ssenari, 90 % aralıq') : kpi('Tənliklər', String(U.eqOf(s).length), 'bu komponenti izah edən')) + '</div>';
    h += '<div class="card pad" style="margin-top:14px"><div id="ch"></div></div>' +
      '<div class="card" style="margin-top:14px"><div class="grp-h">2026–2030: bütün ssenarilər — səviyyə, artım, zolaq</div><div class="itbl-wrap">' + U.compTable(s) + '</div></div>' +
      (s.h ? '<div class="card" style="margin-top:14px"><div class="grp-h">Son illərin faktiki dəyərləri</div><div class="itbl-wrap">' + U.histTable(s, 10) + '</div></div>' : '') +
      '<section class="sec" style="margin-top:22px"><div class="sec-h"><h2>Bu komponenti izah edən tənliklər</h2><p>Zolağa klikləyin — tam reqressiya nəticəsi açılır: əmsallar, diaqnostika, dayanıqlıq, nümunədən kənar yoxlama.</p></div>' + U.eqSection(s) + '</section>';
    var sens = (window.MICRO.SENS || {})[s.i];
    if (sens && sens.length) h += '<section class="sec"><div class="sec-h"><h2>Əmsallara həssaslıq (tornado)</h2><p>Hər əmsal ±1 standart xəta dəyişdikdə 2030-cu il dəyərinin dəyişməsi, %. Uzun zolaq — proqnoz həmin əmsala daha həssasdır.</p></div><div class="card pad"><div id="tor"></div></div></section>';
    return h + '<p class="small muted" style="margin-top:14px">Mənbə: <code>' + U.esc(s.src) + '</code></p>';
  }
  U.pages.__fr = function (v, p) {
    var f = U.frOf(p[0]), kind = p[1], arg = p[2], s = null, cur = 'o', curG = -1, body;
    if (kind === 'c' && U.byId[arg] && U.byId[arg].f === f.c) { s = U.byId[arg]; cur = s.i; curG = U.groups(f.c).indexOf(s.g); body = viewComp(f, s); }
    else if (kind === 'g' && U.groups(f.c)[+arg]) { cur = 'g' + arg; curG = +arg; body = U.viewGroup(f, +arg); }
    else if (kind === 'hamisi') { cur = 'all'; body = U.viewAll(f); }
    else if (kind === 'tenlik') { cur = 'eq'; body = U.viewEqIndex(f); }
    else if (kind === 'dayaniqliq') { cur = 'rob'; body = U.viewRob(f); }
    else if (kind === 'x' && U.extra) { cur = 'x' + arg; body = U.extra(f, arg); }
    else { if (kind === 'c') U.toast('Komponent tapılmadı: ' + arg); body = U.viewOverview(f); }
    v.innerHTML = '<div class="small muted" style="margin-bottom:10px">' + U.esc(f.lead) + '</div><div class="exp-layout">' + tree(f, cur, curG) + '<div id="main-col" style="min-width:0">' + body + '</div></div>';
    if (s && !s.nf) {
      U.seriesChart(U.$('#ch'), s);
      var sens = (window.MICRO.SENS || {})[s.i]; if (sens && sens.length) U.tornado(U.$('#tor'), sens);
    }
    if (s) U.$('#b-csv').onclick = function () { U.csvList(f.c + '_' + s.i.replace(/[^\w]+/g, '_') + '.csv', [s]); };
    if (kind === 'g' || kind === 'hamisi') U.bindGroup(v, f, kind === 'g' ? +arg : null);
    if (kind === 'tenlik') U.bindEqIndex(v, f, arg);
    if (kind === 'dayaniqliq') U.bindRob(v, f);
    if (!s && !kind && U.bindOverview) U.bindOverview(v, f);
    var tq = U.$('#tq');
    tq.oninput = U.debounce(function () { Q[f.c] = tq.value; var pos = tq.selectionStart; U.route(true); var t = U.$('#tq'); t.focus(); t.setSelectionRange(pos, pos); }, 200);
  };
  U.META.frs.forEach(function (f) { U.pages[f.slug] = U.pages.__fr; });
})();
