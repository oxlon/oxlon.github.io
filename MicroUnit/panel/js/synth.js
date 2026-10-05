/* synth.js — FR10/FR12 Layer B (firm level). Routes #/sintetik[/fr10|/fr12|/numayis|/evez]. Every view carries the red
   «SİNTETİK MƏLUMAT — real müəssisə məlumatı deyil» banner; when the modules run on REAL files the labels switch. */
(function () {
  'use strict';
  var U = window.U;
  U.synMode = function (fr) { return ((window.MICRO.SYNE || {})[fr] || {}).mode || 'SYNTHETIC'; };
  U.synBanner = function (fr) {
    if (U.synMode(fr) === 'REAL') return '<div class="card pad realbn" role="note"><b>REAL MƏLUMAT — ' + fr + ' müəssisə səviyyəsi Nazirliyin faylı ilə hesablanıb.</b><div class="small">Nəticələr məxfidir: yalnız Nazirliyin sistemində saxlanılmalıdır.</div></div>';
    return '<div class="card pad synbn" role="note"><span class="ic">' + U.icon('warn') + '</span><div><b>SİNTETİK MƏLUMAT — real müəssisə məlumatı deyil.</b>' +
      '<div class="small">Bu bölmədəki bütün cədvəl və qrafiklər uydurma, DSK cəmlərinə kalibrlənmiş fayllardan qurulub və yalnız hesablama xəttinin (ekonometrik mühərrikin) işlədiyini göstərir. Heç biri Azərbaycan müəssisələri haqqında tapıntı deyil.</div></div></div>';
  };
  function tests(list) {
    return '<table class="itbl"><tbody>' + list.map(function (t) { return '<tr><td class="lab small" style="min-width:220px;white-space:normal">' + U.esc(t.t) + '</td><td class="small muted" style="white-space:normal">' + U.esc(t.v) + '</td><td>' +
      (t.ok ? '<span class="chip acc">keçdi</span>' : '<span class="chip bad">keçmədi</span>') + '</td></tr>'; }).join('') + '</tbody></table>';
  }
  function demo(v) {
    var Y = window.MICRO.SYN, f = Y.files;
    v.insertAdjacentHTML('beforeend', '<div class="grid g3" style="margin-top:14px"><div class="card pad"><div class="eyebrow">FR10 müəssisə paneli</div><p style="margin:6px 0 0"><b class="tnum">' + U.nf(f.p_rows, 0) + '</b> sətir · <b class="tnum">' + U.nf(f.p_firms, 0) +
      '</b> uydurma müəssisə · ' + f.p_nace + ' NACE bölməsi · ' + f.p_y0 + '–' + f.p_y1 + '</p></div><div class="card pad"><div class="eyebrow">FR12 biznes reyestri</div><p style="margin:6px 0 0"><b class="tnum">' + U.nf(f.r_rows, 0) + '</b> sətir · <b class="tnum">' + U.nf(f.r_records, 0) + '</b> qeyd (' + f.r_last + ': ' +
      U.nf(f.r_active, 0) + ' fəal vahid) · ' + f.r_nace + ' bölmə · ' + f.r_regions + ' region</p></div><div class="card pad"><div class="eyebrow">Real məlumat yükləndikdə</div><p style="margin:6px 0 0">Çıxışlar <code>FR10_FIRM_*</code> və <code>FR12_FIRM_*</code> adlanır, su nişanı olmur; A qatının nəticələri dəyişmir.</p></div></div>' +
      '<section class="sec"><div class="sec-h"><h2>FR10: maliyyə əmsallarının paylanması</h2><p>' + U.esc(Y.wm10) + '</p></div><div class="grid g4" id="ratios"></div></section>' +
      '<section class="sec"><div class="sec-h"><h2>NACE bölmələri üzrə HHI</h2></div><div class="grid g2w"><div class="card pad"><div class="small muted">FR10, ' + Y.hhi10.year + '</div><div id="h10"></div></div><div class="card pad"><div class="small muted">FR12, ' + Y.hhi12.year + ' (25 ən yüksək)</div><div id="h12"></div></div></div></section>' +
      '<section class="sec"><div class="sec-h"><h2>Giriş və çıxış əmsalları</h2></div><div class="card pad"><div id="ee"></div></div></section>' +
      '<section class="sec"><div class="sec-h"><h2>Hesablama xəttinin testləri</h2></div><div class="grid g2w">' +
      '<div class="card"><div class="grp-h">FR10 hesablama xətti</div><div class="itbl-wrap">' + tests(Y.pipe10) + '</div></div><div class="card"><div class="grp-h">FR12 hesablama xətti</div><div class="itbl-wrap">' + tests(Y.pipe12) + '</div></div>' +
      '<div class="card"><div class="grp-h">FR10: faylın əvəz edilməsi</div><div class="itbl-wrap">' + tests(Y.swap10) + '</div></div><div class="card"><div class="grp-h">FR12: faylın əvəz edilməsi</div><div class="itbl-wrap">' + tests(Y.swap12) + '</div></div></div></section>');
    var R = U.$('#ratios');
    Y.ratios.forEach(function (r, i) {
      var d = document.createElement('div'); d.className = 'card pad'; d.innerHTML = '<div class="small"><b>' + U.esc(r.n) + '</b> · mediana ' + U.nf(r.med, 2) + ' · ' + U.nf(r.cnt, 0) + ' müəssisə</div><div id="rt' + i + '"></div>';
      R.appendChild(d);
      var l = U.layout('müəssisə sayı', 0, { noFc: true, h: 220 }); l.xaxis = { gridcolor: '#EDF1F4', fixedrange: true, title: { text: r.n } }; l.margin = { l: 48, r: 10, t: 10, b: 40 }; l.hovermode = 'closest';
      U.plot(U.$('#rt' + i), [{ type: 'bar', x: r.x, y: r.y, marker: { color: '#9AA6B2' }, name: 'sintetik' }], l);
    });
    U.barH(U.$('#h10'), Y.hhi10.lab, Y.hhi10.hhi, 'HHI', { h: 520 });
    U.barH(U.$('#h12'), Y.hhi12.lab, Y.hhi12.hhi, 'HHI', { h: 520 });
    U.lines(U.$('#ee'), [{ x: Y.ee10.year, y: Y.ee10.entry, name: 'FR10 giriş, %', c: '#0E6F7C' }, { x: Y.ee10.year, y: Y.ee10.exit, name: 'FR10 çıxış, %', c: '#B3261E' },
      { x: Y.ee12.year, y: Y.ee12.entry, name: 'FR12 giriş, %', c: '#1F6FB2' }, { x: Y.ee12.year, y: Y.ee12.exit, name: 'FR12 çıxış, %', c: '#E07B00' }], '%', { xt: 'il' });
  }
  function swap() {
    return '<section class="sec"><div class="sec-h"><h2>Sintetik faylı real məlumatla necə əvəz etməli</h2></div><div class="card recipe"><ol>' +
      '<li>Real faylı eyni sxemdə saxlayın: <code>data/firm_panel/FR10_firm_panel.csv</code> (və ya .xlsx) və <code>data/business_register/FR12_business_register.csv</code>. Və ya API ilə yükləyin: <code>POST /api/v1/uploads</code> (növ <code>firm_panel</code> / <code>business_register</code>) — fayl yoxlanılır və tətbiq olunur.</li>' +
      '<li>Yolu mühit dəyişənində də vermək olar: <code>FIRM_PANEL_PATH</code>, <code>BUSREG_PATH</code> (üstünlük: dəyişən → real adlı fayl → sintetik).</li>' +
      '<li>Şablondan başlayın (<code>*_TEMPLATE.csv/.xlsx</code>); başlıqlar Azərbaycan dilində də ola bilər (<code>*_column_map.csv</code>).</li>' +
      '<li><code>FR10.ipynb</code> / <code>FR12.ipynb</code> dəftərini yenidən icra edin (və ya <code>python3 run_all.py --stage FR10</code>) — rejim REAL olur, çıxışlar <code>*_FIRM_*</code> adlanır.</li>' +
      '<li>Sonra <code>python3 panel/build_panel.py</code>: bu bölmə avtomatik «REAL MƏLUMAT» nişanına keçir. Məxfilik: real nəticələr Nazirliyin sistemindən çıxmamalıdır.</li></ol></div></section>';
  }
  U.pages.sintetik = function (v, p) {
    var sub = p[1] || 'fr10';
    v.innerHTML = '<div class="eyebrow">FR10 · FR12 — B qatı (müəssisə səviyyəsi)</div><h1 class="h1" style="margin:4px 0 10px">Müəssisə səviyyəsində ekonometrika</h1>' +
      '<div class="toolbar">' + U.seg('sy-sub', [['fr10', 'FR10 modelləri'], ['fr12', 'FR12 modelləri'], ['numayis', 'Məlumatın nümayişi'], ['evez', 'Real faylla əvəz etmək']], sub) + '</div>' +
      U.synBanner(sub === 'fr12' ? 'FR12' : 'FR10') + '<div id="sy-body"></div>';
    var body = U.$('#sy-body');
    if (sub === 'fr10' && U.syn10) U.syn10(body);
    else if (sub === 'fr12' && U.syn12) U.syn12(body);
    else if (sub === 'numayis') demo(body);
    else body.innerHTML = swap();
    v.onclick = function (e) { var b = e.target.closest('#sy-sub [data-v]'); if (b) location.hash = '#/sintetik/' + b.getAttribute('data-v'); };
  };
})();
