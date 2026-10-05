/* home.js — Başlanğıc: plain-language intro, one card per requirement (2025 → 2030, growth, sparkline, robustness),
   and the four main tasks (scenario builder, report builder, tables, equations). */
(function () {
  'use strict';
  var U = window.U, META = U.META;
  var ST = { done: ['acc', 'qarşılanıb'], partial: ['warn', 'qismən'], gap: ['', 'açıq'] };
  function card(f) {
    var s = U.byId[f.kpi[0]], s2 = U.byId[f.kpi[1]], k = U.scOf(s), c = U.cagr(s, k), k2 = U.scOf(s2), c2 = U.cagr(s2, k2), st = ST[f.st] || ST.gap, rc = U.robCounts(f.c), why = f.st === 'partial' ? (META.why || {})[f.c] : '';
    return '<a class="kpi" href="#/' + f.slug + '" data-tour="card-' + f.slug + '" style="text-decoration:none;color:inherit">' +
      '<div style="display:flex;justify-content:space-between;gap:6px;align-items:center"><span class="chip scen">' + f.c + '</span>' +
      '<span class="chip ' + st[0] + '" title="' + U.esc(why ? 'Niyə qismən: ' + why + '. Ətraflı: tələbin «Ümumi baxış» bölməsi (proqnozlaşdırılmayan göstəricilər və səbəbləri) və «Dayanıqlıq».' : 'Tələbin icra statusu') + '">' + st[1] + '</span></div>' +
      (why ? '<div class="small why"><b>Niyə qismən:</b> ' + U.esc(why) + '</div>' : '') +
      '<div class="l" style="min-height:0;margin-top:4px;font-size:14px;color:var(--ink)">' + U.esc(f.full) + '</div>' +
      '<div class="small muted">' + U.esc(s.e) + (s.u ? ', ' + U.esc(s.u) : '') + '</div>' +
      '<div class="v">' + U.nf(s.s[k][4], s.d) + '<small>2030 · ' + U.SCN[k] + '</small></div>' +
      '<div class="small muted">' + U.lab25(s) + ': <b class="tnum" style="color:var(--ink-2)">' + U.nf(U.b25(s, k), s.d) + '</b></div>' +
      '<div class="d ' + U.trend(c) + '">' + (U.isRate(s) ? 'dəyişmə 2025→2030: ' : 'orta illik artım: ') + U.sg(c, U.gdec(s)) + ' ' + U.gunit(s) + '</div>' + U.spark(s, 240, 44) +
      '<div class="small" style="border-top:1px solid var(--line-2);padding-top:6px;margin-top:4px;color:var(--ink-2)">' + U.esc(s2.e) +
      ': <b class="tnum">' + U.nf(U.b25(s2, k2), s2.d) + ' → ' + U.nf(s2.s[k2][4], s2.d) + '</b> <span class="' + U.trend(c2) + '">(' + U.sg(c2, U.gdec(s2)) + ' ' + U.gunit(s2) + ')</span></div>' +
      '<div class="small muted" style="margin-top:4px">' + U.fr(f.c).length + ' komponent · ' + rc.all + ' tənlik · dayanıqlıq: ' + rc.c['stabil'] + ' stabil, ' + rc.c['qismən stabil'] + ' qismən, ' + rc.c['qeyri-stabil'] + ' qeyri-stabil</div></a>';
  }
  function action(href, ic, t, p, go) {
    return '<a class="card action" href="' + href + '"><span class="ic">' + U.icon(ic) + '</span><h3>' + t + '</h3><p>' + p + '</p><span class="go">' + go + ' →</span></a>';
  }
  U.pages[''] = function (v) {
    var nser = U.S.length, npath = U.S.reduce(function (a, s) { return a + U.scens(s).length; }, 0), neq = U.eqRows().length;
    v.innerHTML = '<div class="hero"><div><div class="eyebrow">İqtisadiyyat Nazirliyi · MİİS §15.5.2</div>' +
      '<h1 class="h1" style="margin-top:6px">Mikro Model — İş paneli, 2026–2030</h1>' +
      '<p class="lead">Altı funksional tələbin bütün proqnozları bir yerdə. Hər komponent üçün: qrafik, 2026–2030 cədvəli (üç ssenari, səviyyə, artım, zolaq) və altında onu izah edən tənlik — dayanıqlıq hökmü ilə. Öz ssenarinizi qurun və ya hesabat hazırlayın.</p></div>' +
      '<div class="hero-kpis"><div class="hk"><b>' + U.nf(nser, 0) + '</b><span>proqnoz komponenti</span></div>' +
      '<div class="hk"><b>' + U.nf(npath, 0) + '</b><span>ssenari üzrə sıra (hər biri 2026–2030)</span></div>' +
      '<div class="hk"><b>' + U.nf(neq, 0) + '</b><span>qiymətləndirilmiş tənlik, tam nəticə ilə</span></div></div></div>' +
      '<section class="sec"><div class="sec-h"><h2>Nə etmək istəyirsiniz?</h2></div><div class="grid g4">' +
      action('#/ssenari', 'sliders', 'Ssenari qurmaq', 'Neftin qiyməti, əmsal və ya alət dəyişin — FR1-in nəticəsi FR3, FR4, FR5, FR10 və FR12-yə ötürülür.', 'Qurucunu aç') +
      action('#/hesabat', 'doc', 'Hesabat hazırlamaq', 'Göstəriciləri, ssenariləri və illəri seçin: Excel, Word, PDF və ya CSV.', 'Hesabat qurucusu') +
      action('#/cedvel', 'table', 'Bütün proqnozlar', 'Altı tələbin bütün komponentləri bir cədvəldə: süzgəc, axtarış, ixrac.', 'Cədvəli aç') +
      action('#/fr1/tenlik', 'fx', 'Tənliklərə baxmaq', 'Hər tənliyin tam reqressiya nəticəsi, diaqnostika və dayanıqlıq testləri.', 'Tənliklər') +
      '</div></section>' +
      '<section class="sec"><div class="sec-h"><h2>Altı tələb</h2><p>Dəyərlər yuxarıda seçilmiş ssenari üzrədir. Karta klikləyin — tələbin bölməsi açılır.</p></div>' +
      '<div class="kpis" style="grid-template-columns:repeat(auto-fill,minmax(290px,1fr))">' + META.frs.map(card).join('') + '</div></section>' +
      '<section class="sec"><div class="grid g4">' +
      action('#/sintetik', 'flask', 'Müəssisə səviyyəsi', 'FR10/FR12 B qatı: sintetik məlumatla tam ekonometrika — nümayiş, tapıntı deyil.', 'Bax') +
      action('#/beledci', 'book', 'Bələdçi', 'Panelin 2 dəqiqəlik izahı, lüğət və suallar.', 'Oxu') +
      action('../site/index.html', 'book', 'Klassik görünüş', 'Metodologiya, məlumat mənbələri, yoxlamalar və məhdudiyyətlər — sənəd şəklində.', 'Aç') +
      '</div></section>' +
      '<p class="small muted" style="margin-top:28px">Hər rəqəm modulların çıxış fayllarından yığılıb · ' + META.stamp.files + ' fayl · möhür ' + META.stamp.md5 + ' · ' + META.stamp.date + '</p>';
  };
})();
