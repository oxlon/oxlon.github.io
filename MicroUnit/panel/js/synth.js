/* synth.js — Sintetik məlumat: FR10/FR12 firm-level engine shown ONLY as a pipeline demonstration. */
(function () {
  'use strict';
  var U = window.U;
  function banner() {
    return '<div class="card pad" role="note" style="background:var(--down-soft);border-color:#EFC6C3;border-left:4px solid var(--down);display:flex;gap:12px">' +
      '<span style="color:var(--down);width:22px;flex:none">' + U.icon('warn') + '</span><div><b style="color:var(--down);font-size:16px">SİNTETİK MƏLUMAT — real müəssisə məlumatı deyil.</b>' +
      '<div style="margin-top:4px">Bu bölmədəki bütün qrafiklər uydurma fayllardan qurulub və yalnız <b>boru xəttinin (hesablama mühərrikinin) işlədiyini</b> göstərir. Heç biri Azərbaycan müəssisələri haqqında tapıntı deyil.</div></div></div>';
  }
  function bar(el, lab, val, xt, h) {
    var l = U.layout('', 0, { noFc: true, h: h || 360 });
    l.xaxis = { title: { text: xt }, gridcolor: '#EDF1F4', fixedrange: true }; l.yaxis = { autorange: 'reversed', automargin: true, fixedrange: true, tickfont: { size: 11 } };
    l.hovermode = 'closest'; l.margin.l = 10;
    U.plot(el, [{ type: 'bar', orientation: 'h', y: lab, x: val, marker: { color: '#9AA6B2' }, name: 'SİNTETİK' }], l);
  }
  function lines(el, sets, yt) {
    var l = U.layout(yt, 0, { noFc: true, h: 300 }); l.xaxis = { tickformat: 'd', gridcolor: '#EDF1F4', fixedrange: true };
    U.plot(el, sets.map(function (s) { return { type: 'scatter', mode: 'lines+markers', x: s[0], y: s[1], name: s[2], line: { color: s[3], width: 2.2 } }; }), l);
  }
  function tests(list) {
    return '<table class="itbl"><tbody>' + list.map(function (t) { return '<tr><td class="lab small" style="min-width:200px">' + U.esc(t.t) + '</td><td class="small muted" style="white-space:normal">' + U.esc(t.v) + '</td><td>' +
      (t.ok ? '<span class="chip acc">keçdi</span>' : '<span class="chip" style="background:var(--down-soft);color:var(--down)">keçmədi</span>') + '</td></tr>'; }).join('') + '</tbody></table>';
  }
  U.pages.sintetik = function (v) {
    var Y = window.MICRO.SYN, f = Y.files;
    v.innerHTML = '<div class="eyebrow">FR10 · FR12 — B qatı</div><h1 class="h1" style="margin:4px 0 14px">Müəssisə səviyyəsi: sintetik nümayiş</h1>' + banner() +
      '<div class="grid g3" style="margin-top:14px"><div class="card pad"><div class="eyebrow">FR10 müəssisə paneli</div><p style="margin:6px 0 0"><b class="tnum">' + U.nf(f.p_rows, 0) + '</b> sətir · <b class="tnum">' + U.nf(f.p_firms, 0) +
      '</b> uydurma müəssisə · ' + f.p_nace + ' NACE bölməsi · ' + f.p_y0 + '–' + f.p_y1 + '</p><p class="small muted">data/firm_panel/FR10_firm_panel_SYNTHETIC.csv</p></div>' +
      '<div class="card pad"><div class="eyebrow">FR12 biznes reyestri</div><p style="margin:6px 0 0"><b class="tnum">' + U.nf(f.r_rows, 0) + '</b> sətir · <b class="tnum">' + U.nf(f.r_records, 0) + '</b> qeyd (' + f.r_last + ': ' +
      U.nf(f.r_active, 0) + ' aktiv vahid) · ' + f.r_nace + ' bölmə · ' + f.r_regions + ' region</p><p class="small muted">data/business_register/FR12_business_register_SYNTHETIC.csv</p></div>' +
      '<div class="card pad"><div class="eyebrow">Real məlumat yükləndikdə</div><p style="margin:6px 0 0">Çıxışlar <code>FR10_FIRM_*</code> və <code>FR12_FIRM_*</code> adlanır, su nişanı olmur; A qatının nəticələri dəyişmir.</p></div></div>' +
      '<section class="sec"><div class="sec-h"><h2>FR10: maliyyə əmsallarının paylanması (sintetik, ' + 'NÜMAYİŞ)</h2><p>' + U.esc(Y.wm10) + '</p></div><div class="grid g4" id="ratios"></div></section>' +
      '<section class="sec"><div class="sec-h"><h2>NACE bölmələri üzrə HHI (sintetik)</h2></div><div class="grid g2w"><div class="card pad"><div class="small muted">FR10, ' + Y.hhi10.year + '</div><div id="h10"></div></div><div class="card pad"><div class="small muted">FR12, ' + Y.hhi12.year + ' (25 ən yüksək)</div><div id="h12"></div></div></div></section>' +
      '<section class="sec"><div class="sec-h"><h2>Giriş, çıxış və sağ qalma (sintetik)</h2></div><div class="grid g2w"><div class="card pad"><div id="ee"></div></div><div class="card pad"><div id="km"></div></div></div></section>' +
      '<section class="sec"><div class="sec-h"><h2>Mühərrik testləri</h2><p>Test adları çıxış fayllarından olduğu kimi (ingiliscə).</p></div><div class="grid g2w">' +
      '<div class="card"><div class="grp-h">FR10 boru xətti</div><div class="itbl-wrap">' + tests(Y.pipe10) + '</div></div><div class="card"><div class="grp-h">FR12 boru xətti</div><div class="itbl-wrap">' + tests(Y.pipe12) + '</div></div>' +
      '<div class="card"><div class="grp-h">FR10 faylın əvəz edilməsi</div><div class="itbl-wrap">' + tests(Y.swap10) + '</div></div><div class="card"><div class="grp-h">FR12 faylın əvəz edilməsi</div><div class="itbl-wrap">' + tests(Y.swap12) + '</div></div></div></section>' +
      '<section class="sec"><div class="sec-h"><h2>Faylı real məlumatla necə əvəz etməli</h2></div><div class="card recipe"><ol>' +
      '<li>Real faylı eyni sxemdə saxlayın: <code>data/firm_panel/FR10_firm_panel.csv</code> (və ya .xlsx, vərəq <code>data</code>) və <code>data/business_register/FR12_business_register.csv</code>.</li>' +
      '<li>Və ya yolu mühit dəyişənində verin: <code>FIRM_PANEL_PATH</code>, <code>BUSREG_PATH</code> (prioritet: dəyişən → real adlı fayl → sintetik).</li>' +
      '<li>Şablondan başlayın (<code>*_TEMPLATE.csv/.xlsx</code>), nümunə sətrini silin; başlıqlar ingilis və ya Azərbaycan dilində ola bilər (<code>*_column_map.csv</code>).</li>' +
      '<li><code>FR10.ipynb</code> / <code>FR12.ipynb</code> dəftərini yenidən icra edin — banner <code>DATA_MODE = REAL</code> çap edir; validator hesabatı <code>output/*_validation_report.csv</code>-dədir.</li>' +
      '<li>Sonra <code>python3 panel/build_panel.py</code> və <code>python3 site/build_site.py</code>. Məxfilik: identifikatorlar psevdonim qalır, real nəticələr Nazirliyin sistemindən çıxmır.</li></ol></div></section>';
    var R = U.$('#ratios');
    Y.ratios.forEach(function (r, i) {
      var d = document.createElement('div'); d.className = 'card pad'; d.innerHTML = '<div class="small"><b>' + U.esc(r.n) + '</b> · median ' + U.nf(r.med, 2) + ' · ' + U.nf(r.cnt, 0) + ' müəssisə</div><div id="rt' + i + '"></div>';
      R.appendChild(d);
      var l = U.layout('müəssisə sayı', 0, { noFc: true, h: 220 }); l.xaxis = { gridcolor: '#EDF1F4', fixedrange: true }; l.margin = { l: 48, r: 10, t: 10, b: 30 }; l.hovermode = 'closest';
      U.plot(U.$('#rt' + i), [{ type: 'bar', x: r.x, y: r.y, marker: { color: '#9AA6B2' }, name: 'SİNTETİK' }], l);
    });
    bar(U.$('#h10'), Y.hhi10.lab, Y.hhi10.hhi, 'HHI', 520);
    bar(U.$('#h12'), Y.hhi12.lab, Y.hhi12.hhi, 'HHI', 520);
    lines(U.$('#ee'), [[Y.ee10.year, Y.ee10.entry, 'FR10 giriş, %', '#0E6F7C'], [Y.ee10.year, Y.ee10.exit, 'FR10 çıxış, %', '#B3261E'],
      [Y.ee12.year, Y.ee12.entry, 'FR12 giriş, %', '#1F6FB2'], [Y.ee12.year, Y.ee12.exit, 'FR12 çıxış, %', '#E07B00']], '%');
    var l = U.layout('sağ qalma payı', 0, { noFc: true, h: 300 }); l.xaxis = { title: { text: 'yaş, il' }, gridcolor: '#EDF1F4', fixedrange: true };
    U.plot(U.$('#km'), Y.km.map(function (c) { return { type: 'scatter', mode: 'lines', line: { shape: 'hv', width: 2 }, x: c.age, y: c.s, name: 'kohort ' + c.c }; }), l);
  };
})();
