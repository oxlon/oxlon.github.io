/* p_met.js — Metodologiya və mənbələr: methodology documents (rendered at build time), data sources and vintages,
   synthetic-data notice, data requests to the Ministry, configuration tables (NFR4), every output (where it is shown /
   hidden with reason) and the last run (engine status). */
(function () {
  'use strict';
  var U = window.U;
  var SUB = [['', 'Sənədlər'], ['menbe', 'Mənbələr və vintajlar'], ['sorgu', 'Məlumat sorğuları'], ['konfiq', 'Konfiqurasiya'], ['cixis', 'Bütün çıxışlar'], ['icra', 'Son icra']];
  var REQ = [['Ev təsərrüfatı büdcə sorğusu (EBT) 2018–2025 — anonimləşdirilmiş mikroməlumat: çəkilər, gəlir mənbələri, istehlak, yoxsulluq aqreqatı və ekvivalentlik şkalası', 'DSK', 'FR3: sintetik məlumatın real məlumatla əvəzlənməsi'],
    ['İşçi qüvvəsi sorğusu (İQS) 2018–2025 mikroməlumatı (formal / qeyri-formal məşğulluq)', 'DSK', 'FR3: məşğulluq, qeyri-formallaşma yan təsiri'],
    ['Maaş intervalı cədvəlləri (DSK 004_11) 2017–2023', 'DSK', 'minimum əmək haqqının təsiri, NFR1'],
    ['ÜSY alanlar (ailə ölçüsü, gəlir, məbləğ intervalı, region); pensiyaçılar növ və məbləğ intervalı üzrə', 'ƏƏSMN / DSMF', 'FR3: sosial ödənişlər'],
    ['Gəlir vergisi və sosial ayırmalar — gəlir intervalı və sektor üzrə', 'Vergilər Xidməti (VXX)', 'FR3: vergi alətləri, fiskal xərc'],
    ['2021 təklif-istifadə cədvəli üçün idxal istifadə matrisi; məhsul × fəaliyyət məşğulluğu', 'DSK', 'FR2: IO modelinin dəqiqliyi'],
    ['Aylıq İQİ maddə indeksləri və çəkiləri; yanacaq növləri üzrə satış həcmləri', 'DSK; SOCAR', 'FR2 qiymət modeli, NFR1 (E7)'],
    ['Fiskal bazaların dəqiqləşdirilməsi (ƏDV, mənfəət və gəlir vergisi gəlirləri, ÜSY, DSMF, büdcə maaş fondu)', 'Maliyyə Nazirliyi', 'birbaşa fiskal xərc (config/fiscal_params.csv)'],
    ['Tolerantlıq qaydasının (uyğun / qismən / uyğunsuz) təsdiqi', 'İqtisadiyyat Nazirliyi', 'NFR1 sapma hesabatı']];
  function docs(v, slug) {
    U.need(['docs'], v, function () {
      var D = window.POL.docs.docs || [], d = D.filter(function (x) { return x.slug === slug; })[0] || D[0];
      v.innerHTML = '<div class="docs-layout"><div class="card pad toc"><h3>Sənədlər</h3>' + D.map(function (x) { return '<div><a href="#/metod/' + U.esc(x.slug) + '"' + (x === d ? ' style="font-weight:700"' : '') + '>' + U.esc(x.title) + '</a></div>' + (x === d ? '<div class="small" style="margin:4px 0 8px 10px">' + x.toc.map(function (t) { return '<div><a href="#/metod/' + U.esc(x.slug) + '" data-h="' + t[1] + '">' + U.esc(t[2]) + '</a></div>'; }).join('') + '</div>' : ''); }).join('') + '</div>' +
        '<div class="card docbody">' + (d ? '<p class="small muted">Fayl: <code>' + U.esc(d.file) + '</code></p>' + d.html : 'Sənəd yoxdur') + '</div></div>';
      v.onclick = function (e) { var a = e.target.closest('[data-h]'); if (a) { e.preventDefault(); var h = U.$('#' + a.getAttribute('data-h'), v); if (h) h.scrollIntoView({ block: 'start' }); } };
    });
  }
  function sources(v) {
    var run = U.META.run || {}, vin = run.vintage || {};
    U.need(['docs'], v, function () {
      var P = window.POL.docs;
      v.innerHTML = '<div class="expl">Siyasət təsiri <b>baza proqnozu ilə eyni vintajda</b> hesablanır: MikroUnit FR1→FR12 zənciri (§15.5.2), Nazirliyin CAEM modelinin sabitlənmiş nüsxəsi, OxLon makro modeli (§15.5.1, xarici kanallar), DSK 2021 girdi-çıxdı cədvəli (2025-ə GRAS ilə yenilənib), DSK 2024 aqreqatlarına kalibrlənmiş sintetik ev təsərrüfatı nümunəsi və RiskUnit paylanmaları (§15.5.3, HTTP).</div>' + U.SYN +
        U.dt('m-vin', Object.keys(vin).map(function (k) { return { acar: k, deyer: vin[k] }; }), [{ k: 'acar', l: 'Vintaj' }, { k: 'deyer', l: 'Dəyər' }], { title: 'Son hesablamanın baza vintajları (' + U.esc(run.run_at || '') + ')', bare: true }) +
        U.dt('m-tb', U.T('cfg_tax_benefit'), null, { title: 'Vergi-müavinət parametrləri və mənbələri (config/tax_benefit.csv)', file: 'tax_benefit' }) +
        U.dt('m-fp', U.T('cfg_fiscal_params'), null, { title: 'Fiskal bazalar və mənbələri (config/fiscal_params.csv)', file: 'fiscal_params' }) +
        U.dt('m-lr', U.T('cfg_longrun_params'), null, { title: 'Uzun müddət ekstrapolyasiyasının parametrləri (config/longrun_params.csv)', bare: true }) +
        U.dt('m-he', U.T('cfg_historical_events'), null, { title: 'Tarixi siyasət hadisələri və müşahidə mənbələri (config/historical_events.csv)', file: 'historical_events' });
      void P;
    });
  }
  function requests(v) {
    v.innerHTML = '<div class="expl">Modelin dəqiqliyini artırmaq və sintetik məlumatı real məlumatla əvəz etmək üçün Nazirlikdən (və aidiyyəti qurumlardan) tələb olunan məlumatlar. Real ev təsərrüfatı məlumatı <code>data/households/PU_households_TEMPLATE.csv</code> şablonu və sütun xəritəsi ilə qoşulur; kod dəyişikliyi tələb olunmur.</div>' + U.SYN +
      U.dt('m-req', REQ.map(function (r, i) { return { n: i + 1, data: r[0], who: r[1], why: r[2] }; }), [{ k: 'n', l: '№', n: 1 }, { k: 'data', l: 'Məlumat' }, { k: 'who', l: 'Qurum' }, { k: 'why', l: 'Nə üçün' }], { title: 'Məlumat sorğuları', file: 'melumat_sorgulari' }) +
      '<p class="small muted">Ətraflı: «Sənədlər» → mikrosimulyasiya (§9), IO (§9), nüvə (§11) və sapma hesabatı.</p>';
  }
  function config(v) {
    U.need(['docs'], v, function () {
      v.innerHTML = '<div class="expl"><b>NFR4 — proqramlaşdırmasız genişlənmə.</b> Yeni ssenari = yeni JSON fayl (<code>config/scenarios/</code>) və ya «Ssenari qurucusu»; yeni alət = <code>instruments.csv</code> + <code>adapters.csv</code> sətirləri; yeni KPI, yan təsir qaydası, tədbir təklifi və tarixi hadisə — müvafiq CSV-də yeni sətir. <a href="#/metod/config_README_az">Təlimat</a>.</div>' +
        ['cfg_instruments:Siyasət alətləri (instruments.csv)', 'cfg_adapters:Adapterlər: alət → mühərrik → giriş (adapters.csv)', 'cfg_kpi:KPI kataloqu (kpi.csv)', 'cfg_side_effect_rules:Yan təsir qaydaları (side_effect_rules.csv)', 'cfg_mitigation_map:Tədbir təklifləri (mitigation_map.csv)', 'cfg_io_sectors:IO sektorları (io_sectors.csv)', 'cfg_indicators:Göstəricilər (indicators.csv)']
          .map(function (x) { var p = x.split(':'); return U.dt('m-' + p[0], U.T(p[0]), null, { title: p[1], file: p[0].slice(4), lim: 40 }); }).join('');
    });
  }
  function outputs(v) {
    U.need(['docs'], v, function () {
      var used = U.META.used || {}, hid = U.META.hidden || {}, PG = { core: 'Başlanğıc, KPI', eff: 'Makro və mikro', io: 'Sektorlar', soc: 'Sosial', risk: 'Risklər', cmp: 'Metodlar', val: 'Validasiya', docs: 'Metodologiya' };
      var C = U.T('_catalog').map(function (r) { var u = used[r.file]; return Object.assign({ where: hid[r.file] ? 'gizli: ' + hid[r.file] : u ? u.map(function (b) { return PG[b] || b; }).join(', ') : '—' }, r); });
      v.innerHTML = '<p class="small muted">Hər çıxış faylı paneldə göstərilir (harada — «Paneldə» sütunu) və ya səbəbi ilə gizlidir. Fayllar: <code>PolicyUnit/output/</code>.</p>' + U.dt('m-cat', C, [{ k: 'file', l: 'Fayl' }, { k: 'owner', l: 'Modul' }, { k: 'description_az', l: 'Təsvir' }, { k: 'rows', l: 'Sətir', n: 1 }, { k: 'updated', l: 'Yenilənib' }, { k: 'where', l: 'Paneldə' }], { title: 'Bütün çıxışlar (output/_catalog.csv)', file: 'cixislar' });
    });
  }
  function run(v) {
    var r = U.META.run || {}, S = U.T('P1_run_status');
    v.innerHTML = U.kv([['Son hesablama', U.esc(r.run_at || '')], ['Ssenarilər', U.esc((r.scenarios || []).length)], ['Vaxt, s', U.nf(r.seconds, 1)], ['Uzun müddətin sonu', U.esc(r.long_end || '')], ['Kataloq xətaları', U.esc((r.catalogue_errors || []).join('; ') || 'yoxdur')], ['Panel möhürü', U.esc((U.META.stamp || {}).md5 || '')]]) +
      U.dt('m-run', S, [{ k: 'scenario', l: 'Ssenari', f: function (x) { return U.esc(U.sname(x)); } }, { k: 'engine', l: 'Mühərrik' }, { k: 'status', l: 'Vəziyyət', f: function (x) { return U.sigchip(x); } }, { k: 'rows', l: 'Sətir', n: 1 }, { k: 'seconds', l: 'Vaxt, s', n: 1 }, { k: 'message_az', l: 'Mesaj' }], { title: 'Mühərriklərin vəziyyəti (P1_run_status)', file: 'P1_run_status' }) + U.fresh() + U.continuity();
  }
  U.pages.metod = function (v, p) {
    var sub = p[1] || '', known = SUB.some(function (s) { return s[0] === sub; });
    v.innerHTML = U.head('Şəffaflıq — metodologiya, mənbələr, konfiqurasiya', 'Metodologiya və mənbələr', 'Metodologiya sənədləri, məlumat mənbələri və vintajlar, sintetik məlumat bildirişi, Nazirliyə məlumat sorğuları, konfiqurasiya cədvəlləri və bütün çıxış faylları. Mərkəz səhifəsi: <a href="../index.html">PolicyUnit</a>; API: <a href="../api/openapi.yaml">openapi.yaml</a>.') + U.subtabs('metod', SUB, known ? sub : '') + '<div id="m-body"></div>';
    var b = U.$('#m-body', v);
    if (sub === 'menbe') sources(b); else if (sub === 'sorgu') requests(b); else if (sub === 'konfiq') config(b); else if (sub === 'cixis') outputs(b); else if (sub === 'icra') run(b); else docs(b, known ? '' : sub);
  };
})();
