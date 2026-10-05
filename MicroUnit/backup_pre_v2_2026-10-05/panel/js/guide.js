/* guide.js — Bələdçi: short guide, how to read the panel, glossary, FAQ. */
(function () {
  'use strict';
  var U = window.U, META = window.MICRO.META;
  U.pages.beledci = function (v) {
    var toc = [['g-what', 'Panel nədir'], ['g-read', 'Necə oxumalı'], ['g-fr', 'Altı tələb'], ['g-gloss', 'Lüğət'], ['g-faq', 'Suallar']];
    v.innerHTML = '<div class="eyebrow">Bələdçi</div><h1 class="h1" style="margin-top:4px">Panel 2 dəqiqəyə</h1>' +
      '<div class="guide" style="margin-top:22px"><nav class="toc">' + toc.map(function (t) { return '<a href="#/beledci" data-to="' + t[0] + '">' + t[1] + '</a>'; }).join('') +
      '<button class="btn sm" style="margin-top:10px" id="g-tour">Turu başlat</button></nav><div>' +
      '<section class="gsec" id="g-what"><h2>Panel nədir</h2><p>Mikroiqtisadi modulun (MİİS §15.5.2) bütün proqnoz nəticələrini — 2026–2030 illəri üzrə, üç ssenaridə — göstərən iş paneli. Hər rəqəm modulun çıxış fayllarından yığılıb; panel heç nə hesablamır, yalnız göstərir. İnternet lazım deyil: faylı açmaq kifayətdir.</p></section>' +
      '<section class="gsec" id="g-read"><h2>Necə oxumalı</h2><div class="grid g3">' +
      '<div class="card recipe"><h4>Bir göstəricinin proqnozu</h4><ol><li>Yuxarıda tələbin bölməsini açın (məs. «FR4 Məşğulluq»).</li><li>Solda göstəricini seçin.</li><li>Kartlar: 2025, 2030, orta illik artım, zolaq.</li><li>Aşağıdakı cədvəldə hər il üçün dəyər və artım açıq yazılıb.</li></ol></div>' +
      '<div class="card recipe"><h4>Bir qrupun hamısı</h4><ol><li>Qrup başlığının altında «▦ Hamısı»nı seçin.</li><li>«Səviyyə» və ya «İllik artım» rejimini seçin.</li><li>Artım xanaları rənglənir: yaşıl — artım, qırmızı — azalma.</li></ol></div>' +
      '<div class="card recipe"><h4>Ssenariləri müqayisə</h4><ol><li>Yuxarıdakı mavi zolaqda ssenarini seçin — hər şey yenilənir.</li><li>«Hamısı» qrafiklərdə üç ssenarini birlikdə göstərir.</li><li>«Ssenarilər» bölməsi əsas göstəriciləri il-il müqayisə edir.</li></ol></div>' +
      '<div class="card recipe"><h4>Faylla işləmək</h4><ol><li>«Proqnoz cədvəlləri»ndə süzgəcləri seçin.</li><li>«CSV» və ya «Excel (.xlsx)» düyməsi — yalnız seçilmiş sətirlər yüklənir.</li></ol></div>' +
      '<div class="card recipe"><h4>Göstəricinin təfsilatı</h4><ol><li>Göstəricidə «ⓘ Təfsilat» düyməsi.</li><li>Tərif, model, sürücülər, nümunədən kənar yoxlama (Theil U), mənbə faylı və məhdudiyyətlər.</li></ol></div></div></section>' +
      '<section class="gsec" id="g-fr"><h2>Altı tələb</h2><ul>' + META.frs.map(function (f) { return '<li><a href="#/' + f.slug + '"><b>' + f.c + ' — ' + U.esc(f.full) + '</b></a>: ' + U.esc(f.lead) + '</li>'; }).join('') + '</ul></section>' +
      '<section class="gsec" id="g-gloss"><h2>Lüğət</h2><dl class="gloss">' + META.gloss.map(function (g) { return '<dt>' + U.esc(g[0]) + '</dt><dd>' + U.esc(g[1]) + '</dd>'; }).join('') + '</dl></section>' +
      '<section class="gsec" id="g-faq"><h2>Suallar</h2>' +
      '<details class="faq"><summary>Rəqəmlər haradan gəlir?</summary><p>Dəftərlər (FR1 → FR3 → FR4 → FR5 → FR10 → FR12) <code>MicroUnit/output</code> qovluğuna CSV faylları yazır; <code>python3 panel/build_panel.py</code> onları bu panelin məlumat fayllarına çevirir və hər sıranın 2026–2030 illərinin tam olduğunu yoxlayır (<code>panel/coverage_report.csv</code>).</p></details>' +
      '<details class="faq"><summary>Niyə bəzi göstəricilərdə yalnız Əsas ssenari var?</summary><p>Bəzi çıxışları modul yalnız Əsas ssenari üçün ixrac edir (məs. FR4-ün 8 qrupu, FR1-in ÜDM artımına töhfələri). Belə sıralar «yalnız Əsas ssenari» nişanı daşıyır; ssenarilər müvafiq ətraflı göstəricilərdədir.</p></details>' +
      '<details class="faq"><summary>Zolaq niyə bu qədər genişdir?</summary><p>İllik məlumatla beşillik proqnozun dürüst qeyri-müəyyənliyi belədir. Zolaq tarixi xətaların təkrar seçilməsi, parametr çəkilişləri və FR1-in makro çəkilişlərindən qurulur.</p></details>' +
      '<details class="faq"><summary>«Sintetik məlumat» nədir?</summary><p>FR10 və FR12-nin müəssisə səviyyəsi üçün uydurma test faylları. Nazirlik öz məlumatını öz sistemində yükləyənə qədər mühərrik onlarla yoxlanılır; nəticələri tapıntı deyil.</p></details>' +
      '<details class="faq"><summary>Metodologiya haradadır?</summary><p>«Klassik görünüş» (yuxarı sağda): tələb mətnləri, modellər, məlumat mənbələri, hold-out cədvəlləri və məhdudiyyətlər.</p></details></section></div></div>';
    U.$('#g-tour').onclick = U.startTour;
    v.onclick = function (e) { var a = e.target.closest('[data-to]'); if (a) { e.preventDefault(); var t = document.getElementById(a.getAttribute('data-to')); if (t) t.scrollIntoView({ behavior: 'smooth' }); } };
  };
})();
