/* frextra.js — FR10/FR12 extras: early-warning lists, FR12 industrial-organisation scenario table. */
(function () {
  'use strict';
  var U = window.U, META = U.META;
  function ew10() {
    var rows = META.ew10.slice().sort(function (a, b) { return (b.w - a.w) || (b.nf - a.nf) || (b.share - a.share); });
    return '<h1 class="h1" style="font-size:24px">Erkən xəbərdarlıq — emal sahələri</h1>' +
      '<p class="lead" style="font-size:14.5px">2023–25 göstəriciləri 2020–22 ilə müqayisə olunur və sahənin öz dəyişkənliyi ilə ölçülür. Bunlar şəffaf hədlərdir, ehtimal deyil. <b>' +
      rows.filter(function (r) { return r.w; }).length + '</b> sahə izləmə siyahısındadır.</p>' +
      '<div class="card itbl-wrap" style="margin-top:12px"><table class="itbl"><thead><tr><th class="l">Sahə</th><th>Emalda pay 2025, %</th><th class="l">Qaldırılmış bayraqlar</th><th class="l">Status</th></tr></thead><tbody>' +
      rows.map(function (r) { return '<tr><td class="lab">' + U.esc(r.n) + '</td><td class="n">' + U.nf(r.share, 2) + '</td><td class="lab small">' + (r.fl.join(', ') || '—') +
        '</td><td>' + (r.w ? '<span class="chip" style="background:var(--down-soft);color:var(--down)">izləmədə</span>' : r.fl.length ? '<span class="chip warn">tək bayraq</span>' : '<span class="chip acc">normal</span>') + '</td></tr>'; }).join('') +
      '</tbody></table></div>';
  }
  function ew12() {
    return '<h1 class="h1" style="font-size:24px">Erkən xəbərdarlıq — rəqabət</h1>' +
      '<p class="lead" style="font-size:14.5px">Konsentrasiya, giriş, çıxış, pay mobilliyi və «marja artır, giriş azalır» bayraqları; bal mövcud bayraqların çəkili payıdır. İzləmə siyahısı: bal ≥ 0,30 və ya ≥ 2 bayraq.</p>' +
      '<div class="card itbl-wrap" style="margin-top:12px"><table class="itbl"><thead><tr><th class="l">Fəaliyyət qrupu</th><th class="l">Bayraqlar</th><th>Bal</th><th class="l">Status</th></tr></thead><tbody>' +
      META.ew12.map(function (r) { return '<tr><td class="lab">' + U.esc(r.n) + '</td><td class="lab small">' + (r.fl.join(', ') || '—') + '</td><td class="n">' + U.nf(r.score, 2) +
        '</td><td>' + (r.w ? '<span class="chip" style="background:var(--down-soft);color:var(--down)">izləmədə</span>' : r.fl.length ? '<span class="chip warn">tək bayraq</span>' : '<span class="chip acc">normal</span>') + '</td></tr>'; }).join('') +
      '</tbody></table></div>';
  }
  function rng(a, d) { return U.nf(a[0], d) + ' … ' + U.nf(a[1], d); }
  function io() {
    return '<h1 class="h1" style="font-size:24px">Ssenari təhlili — sənaye iqtisadiyyatı</h1>' +
      '<p class="lead" style="font-size:14.5px">Kalibrlənmiş Kurno modeli: siyasət və ya bazar dəyişikliyinə sektorun ehtimal olunan reaksiyası. Nəticə tək rəqəm deyil, <b>aralıqdır</b> (HHI hədləri × tələb elastikliyi × davranış parametri). «Fərziyyə» işarəli bazarlar ictimai məlumatdan təxmini quruluşla kalibrlənib.</p>' +
      '<div class="card itbl-wrap" style="margin-top:12px"><table class="itbl"><thead><tr><th class="l">Ssenari</th><th class="l">Bazar</th><th class="l">Dəyişiklik</th><th class="l">Struktur</th><th>HHI</th><th>Qiymət, %</th><th>Buraxılış, %</th><th>İstehlakçı izafisi, %</th></tr></thead><tbody>' +
      META.io.map(function (r) { return '<tr title="' + U.esc(r.as) + '"><td>' + r.s + '</td><td class="lab">' + U.esc(r.m) + '</td><td class="lab small">' + U.esc(r.ch) + '<div class="muted">' + U.esc(r.as) + '</div></td><td><span class="chip ' + (r.src === 'fərziyyə' ? 'warn' : 'acc') + '">' + r.src + '</span></td>' +
        '<td class="n">' + rng(r.h, 0) + '</td><td class="n">' + rng(r.p, 2) + '</td><td class="n">' + rng(r.q, 2) + '</td><td class="n">' + rng(r.cs, 2) + '</td></tr>'; }).join('') +
      '</tbody></table></div><p class="small muted">Mənbə: FR12_scenario_summary.csv, FR12_scenario_assumptions.csv. Ssenari qurucusunda FR12-nin «IO ssenarisi» alətləri ilə dəyişdirilə bilər.</p>';
  }
  U.extra = function (f, arg) {
    if (f.c === 'FR10' && arg === 'ew') return ew10();
    if (f.c === 'FR12' && arg === 'ew') return ew12();
    if (f.c === 'FR12' && arg === 'io') return io();
    return '<p>Bölmə tapılmadı.</p>';
  };
})();
