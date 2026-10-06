/* p_met.js — Metodologiya və mənbələr: the RiskUnit/docs methodology documents rendered at build time (data/docs.js),
   data sources and vintages (D2, vintage archive, spine manifest, upstream catalog D1), every output with where it is
   shown (and the intentionally hidden ones), and the last pipeline run (stages, timings). */
(function () {
  'use strict';
  var U = window.U;
  function docs(el, slug) {
    U.need(['docs'], el, function () {
      var D = U.raw('docs'), d = D.filter(function (x) { return x.slug === slug; })[0] || D[0];
      el.innerHTML = '<div class="docs-layout"><nav class="card pad toc">' + D.map(function (x) { return '<a class="tsheet' + (x.slug === d.slug ? ' on' : '') + '" href="#/metod/' + x.slug + '">' + U.esc(x.title) + '</a>'; }).join('') +
        '<div class="tsec">Bu sənəd</div>' + d.toc.map(function (t) { return '<a class="tsheet" href="#/metod/' + d.slug + '" data-to="' + t[1] + '" style="padding-left:' + (t[0] > 1 ? 30 : 16) + 'px">' + U.esc(t[2]) + '</a>'; }).join('') + '</nav>' +
        '<article class="card docbody"><p class="small muted">Mənbə: <a href="../' + U.esc(d.file) + '">' + U.esc(d.file) + '</a> · yığım zamanı çevrilib</p>' + d.html + '</article></div>';
      el.onclick = function (e) { var a = e.target.closest('[data-to]'); if (a) { e.preventDefault(); var t = document.getElementById(a.getAttribute('data-to')); if (t) t.scrollIntoView({ behavior: 'smooth' }); } };
    });
  }
  function sources(el) {
    U.need(['d1'], el, function () {
      var d2 = U.T('D2_feed_status');
      el.innerHTML = '<div class="note-b">Hər avtomatik axın xam cavabı <code>data/vintages/&lt;mənbə&gt;/&lt;tarix&gt;</code> altında saxlayır (SHA-256 ilə); yükləmə alınmasa son uğurlu vintaj istifadə olunur və status D2-də qeyd edilir. Yuxarı axın faylları (OxLon, Nazirlik, MikroUnit) heşlənir — yeni vintaj yenidən hesablamanı tətikləyir (NFR2).</div>' +
        U.dt('mt-d2', d2, [{ k: 'feed', l: 'Axın' }, { k: 'source', l: 'Mənbə' }, { k: 'tezlik', l: 'Tezlik' }, { k: 'last_obs', l: 'Son müşahidə' }, { k: 'tazelik', l: 'Təzəlik', f: U.sigchip }, { k: 'status', l: 'Status', f: U.sigchip }, { k: 'url', l: 'Ünvan' }], { title: 'Canlı məlumat mənbələri (D2)', file: 'menbeler' }) +
        U.dt('mt-sp', U.T('spine_manifest'), null, { title: 'Yuxarı axın faylları və heşləri (spine_manifest)', file: 'spine_manifest' }) +
        U.dt('mt-d1', U.T('D1_upstream_catalog'), null, { title: 'Yuxarı axın kataloqu (D1): makro, Nazirlik və mikro üzrə hər sıra', file: 'D1_upstream_catalog', lim: 100 }) +
        U.dt('mt-vm', U.T('vintages_manifest'), null, { title: 'Vintaj arxivi', file: 'vintajlar', lim: 40 });
    });
  }
  function outputs(el) {
    var used = U.META.used || {}, hid = U.META.hidden || {}, cat = U.by(U.T('_catalog_v2'), 'file'), WHERE = { core: 'Bu gün, Reyestr', mon: 'Monitor', d4: 'Monitor → Bazar', v2: 'Monitor → Bazar', d6: 'Monitor → Proqnoz təsiri', 'var': 'VaR və CaR', meas: 'Tədbirlər, Stress', caem: 'CAEM', nfr: 'Geriyə sınaq',
      scal: 'Miqyaslanma', s1: 'Miqyaslanma, Reyestr', s2: 'Miqyaslanma', s4: 'Miqyaslanma → Təsir xəritəsi', c4lib: 'CAEM → Şok kitabxanası', d1: 'Metodologiya → Mənbələr', docs: 'Metodologiya' };
    var rows = Object.keys(used).map(function (f) { var c = (cat[f] || [{}])[0]; return { file: f, harada: used[f].map(function (b) { return WHERE[b] || b; }).join('; '), owner_module: c.owner_module || '', description_az: c.description_az || '', update_frequency: c.update_frequency || '', updated_utc: c.updated_utc || '' }; })
      .concat(Object.keys(hid).map(function (f) { return { file: f, harada: 'göstərilmir: ' + hid[f] }; }));
    el.innerHTML = U.dt('mt-o', rows, [{ k: 'file', l: 'Fayl' }, { k: 'harada', l: 'Paneldə harada' }, { k: 'owner_module', l: 'Modul' }, { k: 'description_az', l: 'Təsvir' }, { k: 'update_frequency', l: 'Yenilənmə' }, { k: 'updated_utc', l: 'Yeniləndi (UTC)' }],
      { title: 'Bütün çıxışlar (' + rows.length + ') — kataloq (_catalog_v2.csv) və paneldəki yeri', file: 'cixislar', lim: 400 });
  }
  function run(el) {
    var r = U.META.run || {}, st = r.merheleler || [], dr = U.META.run_daily || {}, dl = dr.merheleler || [];
    el.innerHTML = '<div class="tiles">' + U.tile('Rejim', U.esc(r.rejim || ''), 'şəbəkə: ' + U.esc(r.sebeke || '')) + U.tile('Müddət', U.nf(r.muddet_san, 0) + '<small>san</small>', U.esc(r.yaradildi_utc || '')) + U.tile('Mərhələ', U.nf(st.length, 0), st.filter(function (s) { return (s.seviyye || (s.status === 'ok' ? 'ok' : 'xəta')) === 'xəta'; }).length + ' uğursuz · ' + st.filter(function (s) { return s.seviyye === 'xəbərdarlıq'; }).length + ' xəbərdarlıq') + U.tile('Baza', U.esc(r.baseline_id || ''), 'vəziyyət ' + U.esc(r.as_of || '')) + '</div>' +
      '<div class="card pad"><h3>Mərhələlərin müddəti, san</h3><div id="mt-c" class="ch"></div></div>' +
      U.dt('mt-r', st, [{ k: 'stage', l: 'Mərhələ' }, { k: 'name', l: 'Ad' }, { k: 'status', l: 'Status', f: U.sigchip }, { k: 'seconds', l: 'Müddət, san', n: 1, d: 1 }, { k: 'required', l: 'Məcburi' }], { title: 'Boru xəttinin son icrası (_run_summary_v2.json)', file: 'icra' }) +
      (dl.length ? '<h3 style="margin-top:18px">Son gündəlik dövr (axınlar və monitor): ' + U.esc(dr.yaradildi_utc || '') + ' · ' + U.nf(dr.muddet_san, 0) + ' san · şəbəkə: ' + U.esc(dr.sebeke || '') + '</h3>' +
        U.dt('mt-rd', dl, [{ k: 'stage', l: 'Mərhələ' }, { k: 'name', l: 'Ad' }, { k: 'status', l: 'Status', f: U.sigchip }, { k: 'seconds', l: 'Müddət, san', n: 1, d: 1 }], { title: 'Gündəlik dövrün son icrası (_run_summary_daily.json)', file: 'icra_gundelik' }) : '');
    U.barH(U.$('#mt-c', el), st.map(function (s) { return s.stage + ' · ' + s.name; }), st.map(function (s) { return s.seconds; }), 'san', { color: st.map(function (s) { return s.status === 'ok' ? '#0E6F7C' : '#B3261E'; }) });
  }
  U.pages.metod = function (v, p) {
    var sub = p[1] || '', isDoc = sub && ['menbe', 'cixis', 'icra'].indexOf(sub) < 0;
    v.innerHTML = U.head('NFR3 — şəffaflıq', 'Metodologiya və mənbələr', 'Metodologiya sənədləri, məlumat mənbələri və vintajlar, bütün çıxış faylları (paneldə harada göstərildiyi ilə) və son hesablamanın mərhələləri. Klassik hesabat səhifələri: <a href="../site/index.html">rəhbərlik</a> · <a href="../site/analitik.html">analitik</a>; API: <a href="' + (U.API.fileMode() ? '../api/openapi.yaml' : '/api/v1/openapi.yaml') + '">openapi.yaml</a>, <a href="../api/OXUYUN.md">oxuyun</a>.') +
      U.subtabs('metod', [['', 'Sənədlər'], ['menbe', 'Mənbələr və vintajlar'], ['cixis', 'Bütün çıxışlar'], ['icra', 'Son icra']], isDoc ? '' : sub) + '<div id="mt-body"></div>';
    var b = U.$('#mt-body', v);
    if (sub === 'menbe') sources(b); else if (sub === 'cixis') outputs(b); else if (sub === 'icra') run(b); else docs(b, isDoc ? sub : null);
  };
})();
