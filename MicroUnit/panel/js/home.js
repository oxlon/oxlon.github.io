/* home.js — Başlanğıc: one KPI card per requirement, 2025 → 2030, average growth, sparkline, status chip. */
(function () {
  'use strict';
  var U = window.U, META = window.MICRO.META;
  var ST = { done: ['acc', 'qarşılanıb'], partial: ['warn', 'qismən'], gap: ['', 'açıq'] };
  function kv(s) {
    var k = U.scOf(s), v30 = s.s[k][4], c = U.cagr(s, k), lh = U.lastHist(s);
    var lab25 = lh && lh[0] === 2025 ? '2025 faktiki' : '2025 başlanğıc';
    return { k: k, v30: v30, c: c, lab25: lab25 };
  }
  function card(f) {
    var s = U.byId[f.kpi[0]], s2 = U.byId[f.kpi[1]], a = kv(s), b = kv(s2), st = ST[f.st] || ST.gap;
    return '<a class="kpi" href="#/' + f.slug + '" data-tour="card-' + f.slug + '" style="text-decoration:none;color:inherit">' +
      '<div style="display:flex;justify-content:space-between;gap:6px;align-items:center"><span class="chip scen">' + f.c + '</span>' +
      '<span class="chip ' + st[0] + '" title="Tələbin icra statusu">' + st[1] + '</span></div>' +
      '<div class="l" style="min-height:0;margin-top:4px;font-size:14px;color:var(--ink)">' + U.esc(f.full) + '</div>' +
      '<div class="small muted">' + U.esc(U.label(s)) + (s.u ? ', ' + U.esc(s.u) : '') + '</div>' +
      '<div class="v">' + U.nf(a.v30, s.d) + '<small>2030 · ' + U.SCN[a.k] + '</small></div>' +
      '<div class="small muted">' + a.lab25 + ': <b class="tnum" style="color:var(--ink-2)">' + U.nf(s.b, s.d) + '</b></div>' +
      '<div class="d ' + U.trend(a.c) + '">' + (s.k === 'rate' ? 'dəyişmə 2025→2030: ' : 'orta illik artım: ') + U.sg(a.c, U.gdec(s)) + ' ' + U.gunit(s) + '</div>' +
      U.spark(s, 240, 44) +
      '<div class="small" style="border-top:1px solid var(--line-2);padding-top:6px;margin-top:4px;color:var(--ink-2)">' + U.esc(U.label(s2)) +
      ': <b class="tnum">' + U.nf(s2.b, s2.d) + ' → ' + U.nf(b.v30, s2.d) + '</b> <span class="' + U.trend(b.c) + '">(' + U.sg(b.c, U.gdec(s2)) + ' ' + U.gunit(s2) + ')</span></div></a>';
  }
  function action(href, ic, t, p, go) {
    return '<a class="card action" href="' + href + '"><span class="ic">' + U.icon(ic) + '</span><h3>' + t + '</h3><p>' + p + '</p><span class="go">' + go + ' →</span></a>';
  }
  U.pages[''] = function (v) {
    var nser = U.S.length, npath = U.S.reduce(function (a, s) { return a + U.scens(s).length; }, 0), nband = U.S.filter(function (s) { return s.q; }).length;
    v.innerHTML = '<div class="hero"><div><div class="eyebrow">İqtisadiyyat Nazirliyi · MİİS §15.5.2</div>' +
      '<h1 class="h1" style="margin-top:6px">Mikro Model — İş paneli, 2026–2030</h1>' +
      '<p class="lead">Altı funksional tələbin bütün proqnozları bir yerdə: hər göstərici üçün qrafik, illər üzrə açıq cədvəl, üç ssenari və qeyri-müəyyənlik zolağı. Karta klikləyin — tələbin bölməsi açılır.</p></div>' +
      '<div class="hero-kpis"><div class="hk"><b>' + U.nf(nser, 0) + '</b><span>proqnoz göstəricisi</span></div>' +
      '<div class="hk"><b>' + U.nf(npath, 0) + '</b><span>ssenari üzrə proqnoz sırası (hər biri 2026–2030)</span></div>' +
      '<div class="hk"><b>' + U.nf(nband, 0) + '</b><span>göstəricidə 5–95 % zolağı</span></div></div></div>' +
      '<section class="sec"><div class="sec-h"><h2>Altı tələb</h2><p>Dəyərlər yuxarıda seçilmiş ssenari üzrədir; status — tələbin icra vəziyyəti.</p></div>' +
      '<div class="kpis" style="grid-template-columns:repeat(auto-fill,minmax(290px,1fr))">' + META.frs.map(card).join('') + '</div></section>' +
      '<section class="sec"><div class="sec-h"><h2>Növbəti addım</h2></div><div class="grid g4">' +
      action('#/cedvel', 'table', 'Proqnoz cədvəlləri', 'Bütün modulların bütün sıraları: süzgəc, axtarış, CSV və Excel ixracı.', 'Cədvəli aç') +
      action('#/ssenari', 'sliders', 'Ssenarilər', 'Əsas göstəricilər Əsas, Mənfi və İslahat ssenariləri üzrə il-il müqayisədə.', 'Müqayisə et') +
      action('#/sintetik', 'flask', 'Sintetik məlumat', 'FR10/FR12 müəssisə səviyyəsi: boru xəttinin nümayişi və faylın əvəz edilməsi.', 'Bax') +
      action('../site/index.html', 'book', 'Klassik görünüş', 'Metodologiya, məlumat mənbələri, yoxlamalar və məhdudiyyətlər — sənəd şəklində.', 'Aç') +
      '</div></section>' +
      '<p class="small muted" style="margin-top:28px">Hər rəqəm <code>MicroUnit/output</code> fayllarından <code>build_panel.py</code> ilə yığılıb · ' + META.stamp.files + ' fayl · möhür ' + META.stamp.md5 + ' · ' + META.stamp.date + '</p>';
  };
})();
