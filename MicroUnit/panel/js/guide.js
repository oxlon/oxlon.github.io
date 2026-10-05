/* guide.js — Bələdçi: how to use the panel, glossary, FAQ. */
(function () {
  'use strict';
  var U = window.U, META = U.META;
  function recipe(t, steps) { return '<div class="card recipe"><h4>' + t + '</h4><ol>' + steps.map(function (s) { return '<li>' + s + '</li>'; }).join('') + '</ol></div>'; }
  U.pages.beledci = function (v) {
    var toc = [['g-what', 'Panel nədir'], ['g-read', 'Necə istifadə etməli'], ['g-fr', 'Altı tələb'], ['g-gloss', 'Lüğət'], ['g-faq', 'Suallar']];
    v.innerHTML = '<div class="eyebrow">Bələdçi</div><h1 class="h1" style="margin-top:4px">Panel 2 dəqiqəyə</h1>' +
      '<div class="guide" style="margin-top:22px"><nav class="toc">' + toc.map(function (t) { return '<a href="#/beledci" data-to="' + t[0] + '">' + t[1] + '</a>'; }).join('') +
      '<button class="btn sm" style="margin-top:10px" id="g-tour">Turu başlat</button></nav><div>' +
      '<section class="gsec" id="g-what"><h2>Panel nədir</h2><p>Mikroiqtisadi modulun (MİİS §15.5.2) bütün nəticələri bir yerdə: hər komponentin 2026–2030 proqnozu üç ssenaridə, onu izah edən tənliklər (tam reqressiya nəticəsi və dayanıqlıq testləri ilə), öz ssenarinizi qurmaq və hesabat hazırlamaq imkanı. Rəqəmlər modulların çıxış fayllarından yığılır. Baxış üçün internet və server lazım deyil; yalnız ssenarinin yenidən hesablanması üçün yerli server işləməlidir.</p></section>' +
      '<section class="gsec" id="g-read"><h2>Necə istifadə etməli</h2><div class="grid g3">' +
      recipe('Bir komponentin proqnozu', ['Yuxarıda tələbi açın (məs. «FR4 Məşğulluq»).', 'Solda qrupu açıb komponenti seçin.', 'Qrafik, 2026–2030 cədvəli (bütün ssenarilər, səviyyə, artım, zolaq) və faktiki illər görünür.', 'Aşağıda onu izah edən tənliklər — zolağa klikləyin.']) +
      recipe('Tənliyin tam nəticəsi', ['Komponentin altında və ya «ƒ Tənliklər» siyahısında tənliyə klikləyin.', 'Əmsallar, standart xəta, t, p, 95 % interval, uyğunluq və diaqnostika.', 'Dayanıqlıq: rekursiv qrafik, bir ili çıxarmaqla aralıqlar, Chow, CUSUM.', 'Mətn nəticəsini «Kopyala» ilə götürün.']) +
      recipe('Öz ssenarinizi qurmaq', ['«Ssenarilər» → «Qurucu».', 'Baza ssenarisini seçin; FR1-də məs. Brent qiymətinə «−20» yazıb «% tətbiq et».', 'İstəsəniz əmsalı dəyişin (95 % interval daxilində; kənara çıxmaq üçün icazə verin).', '«Hesabla» — nəticələr bütün modullar üzrə Əsas ilə müqayisədə. «Saxla» ilə yadda saxlayın.']) +
      recipe('Hesabat hazırlamaq', ['«Hesabat» bölməsini açın.', 'Tələbləri, komponentləri, ssenariləri (saxlanmış xüsusi ssenarilər daxil) və illəri seçin.', 'Məzmunu seçin: cədvəllər, qrafiklər, tənliklər, dayanıqlıq, fərziyyələr, qeydlər.', 'Excel, Word, CSV və ya «Çap / PDF».']) +
      recipe('Bir qrupun və ya tələbin hamısı', ['Solda «▦ Qrupun cədvəli» və ya «▦ Bütün komponentlər».', '«Səviyyə», «İllik artım» və ya «İkisi»; ssenarini süzün.', 'CSV və ya Excel ixracı.']) +
      recipe('Doldurulmuş illər', ['Mənbədə olmayan illər interpolyasiya ilə doldurulub.', 'Qrafikdə boş dairə və qırıq xətt, cədvəldə kursiv.', 'Xananın üzərinə gəlin — doldurma üsulu göstərilir.']) + '</div></section>' +
      '<section class="gsec" id="g-fr"><h2>Altı tələb</h2><ul>' + META.frs.map(function (f) { return '<li><a href="#/' + f.slug + '"><b>' + f.c + ' — ' + U.esc(f.full) + '</b></a>: ' + U.esc(f.intro) + '</li>'; }).join('') + '</ul></section>' +
      '<section class="gsec" id="g-gloss"><h2>Lüğət</h2><dl class="gloss">' + META.gloss.map(function (g) { return '<dt>' + U.esc(g[0]) + '</dt><dd>' + U.esc(g[1]) + '</dd>'; }).join('') + '</dl></section>' +
      '<section class="gsec" id="g-faq"><h2>Suallar</h2>' +
      '<details class="faq"><summary>Rəqəmlər haradan gəlir?</summary><p>Dəftərlər (FR1 → FR3 → FR4 → FR5 → FR10 → FR12) çıxış qovluğuna nəticələr yazır; <code>python3 panel/build_panel.py</code> onları bu panelin məlumat fayllarına çevirir və hər komponentin hər ssenaridə 2026–2030 illərinin tam olduğunu yoxlayır (<code>panel/coverage_report.csv</code>).</p></details>' +
      '<details class="faq"><summary>«Hesabla» düyməsi işləmir</summary><p>Ssenari hesablaması yerli server tələb edir: <code>MikroModel_Baslat.command</code> (macOS) və ya <code>MikroModel_Baslat.bat</code> (Windows) faylını iki dəfə klikləyin; panel <code>http://127.0.0.1:8790/panel/</code> ünvanında açılacaq.</p></details>' +
      '<details class="faq"><summary>Dayanıqlıq hökmü nə deməkdir?</summary><p>«Stabil» — proqnozda istifadə olunan əmsallar nümunə genişləndikcə və hər il çıxarıldıqda işarəsini saxlayır, Chow və CUSUM testləri qırılma göstərmir. «Qeyri-stabil» — işarə dəyişir və ya güclü qırılma var; belə tənliklərin proqnozunu ehtiyatla şərh edin.</p></details>' +
      '<details class="faq"><summary>Zolaq niyə genişdir?</summary><p>İllik məlumatla beşillik proqnozun dürüst qeyri-müəyyənliyi belədir. Zolaq tarixi xətaların təkrar seçilməsi, parametr çəkilişləri və FR1-in makro çəkilişlərindən qurulur.</p></details>' +
      '<details class="faq"><summary>«Sintetik məlumat» nədir?</summary><p>FR10 və FR12-nin müəssisə səviyyəsi üçün uydurma test faylları. Nazirlik öz məlumatını yükləyənə qədər ekonometrik mühərrik onlarla yoxlanılır; nəticələri tapıntı deyil.</p></details>' +
      '<details class="faq"><summary>Metodologiya haradadır?</summary><p>«Klassik görünüş» (yuxarı sağda): tələb mətnləri, modellər, məlumat mənbələri və məhdudiyyətlər.</p></details></section></div></div>';
    U.$('#g-tour').onclick = U.startTour;
    v.onclick = function (e) { var a = e.target.closest('[data-to]'); if (a) { e.preventDefault(); var t = document.getElementById(a.getAttribute('data-to')); if (t) t.scrollIntoView({ behavior: 'smooth' }); } };
  };
})();
