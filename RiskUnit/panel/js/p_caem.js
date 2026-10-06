/* p_caem.js — CAEM: σ-band signals of the Ministry's risk sheets with current data (C1, band reproduction), balance of
   risks Ministry vs data-driven (C2), category map to the RU register (C3), the AZE Model shock library explorer (C4,
   labelled «Nazirlik CAEM modeli — müqayisə»), transmission comparison (C5) and the findings register (C6). */
(function () {
  'use strict';
  var U = window.U;
  var CA = U.CA = { ind: null, lib: null, vars: ['dy', 'dP', 'pb_y'] };
  var CLC = { 'mənfi': '#B3261E', neytral: '#9AA6B2', 'əlverişli': '#1E7B4F' };
  function signals(el) {
    var c1 = U.T('C1_caem_signals'), inds = U.uniq(c1.map(function (r) { return r.indicator; })), i = CA.ind || inds[0], rs = c1.filter(function (r) { return r.indicator === i && r.primary; }).sort(function (a, b) { return a.year - b.year; });
    var vars = U.uniq(c1.filter(function (r) { return r.indicator === i; }).map(function (r) { return r.variant; }));
    el.innerHTML = '<div class="note-b">CAEM risk vərəqləri (neft, ərzaq, idxal qiyməti, tərəfdaş ÜDM-i; + GPR) hər göstəricini tarixi orta ± kσ zolaqlarına bölür və 0–5 bal verir. Burada eyni qayda cari məlumata və OxLon / MikroUnit bazasına tətbiq olunur; Nazirliyin orijinal təsnifatı da təkrarlanır (variantlar).</div>' +
      '<div class="toolbar">' + U.seg('ca-i', inds.map(function (x) { return [x, (c1.filter(function (r) { return r.indicator === x; })[0] || {}).indicator_az]; }), i) + '</div>' +
      '<div class="cols2"><div class="card pad"><h3>Dəyər və siqnal sinfi (əsas variant)</h3><div id="ca-v" class="ch"></div></div><div class="card pad"><h3>Bal (0–5) variantlar üzrə</h3><div id="ca-s" class="ch"></div></div></div>' +
      U.dt('ca-t', c1.filter(function (r) { return r.indicator === i; }), null, { title: 'CAEM σ-zolaq siqnalları (C1): ' + U.esc((rs[0] || {}).indicator_az || i), file: 'C1_' + i }) +
      U.dt('ca-b', U.T('C1_band_reproduction'), null, { title: 'Nazirlik zolaq təsnifatının Python təkrarı — vərəqin öz sütunları ilə uyğunluq (C1_band_reproduction)', file: 'C1_band_reproduction' });
    U.lines(U.$('#ca-v', el), [{ x: rs.map(function (r) { return r.year; }), y: rs.map(function (r) { return r.value; }), name: 'dəyər', mode: 'lines+markers', c: '#455463', marker: { size: 9, color: rs.map(function (r) { return CLC[r.class_az] || '#9AA6B2'; }) } }], '', { years: false });
    U.lines(U.$('#ca-s', el), vars.map(function (vv, k) { var r = c1.filter(function (q) { return q.indicator === i && q.variant === vv; }).sort(function (a, b) { return a.year - b.year; }); return { x: r.map(function (q) { return q.year; }), y: r.map(function (q) { return q.score_0_5; }), name: vv, mode: 'lines+markers', c: U.PAL[k] }; }), 'bal', { yr: [0, 5] });
    U.$('#ca-i', el).onclick = function (e) { var b = e.target.closest('[data-v]'); if (b) { CA.ind = b.getAttribute('data-v'); signals(el); } };
  }
  function balance(el) {
    var c2 = U.T('C2_balance_of_risks'), tot = c2.filter(function (r) { return r.category === 'CƏMİ'; }), parts = c2.filter(function (r) { return r.category !== 'CƏMİ'; }), by = U.by(tot, 'version');
    el.innerHTML = '<div class="note-b">Risk balansı indeksi = Σ (bal × çəki), 0–100. Nazirliyin balları əl ilə yazılıb (2022, 2024, 2025); RU məlumat əsaslı balları C1 siqnalı, göstərici bazası və FR2 riskindən hesablayır (2022–2030). &lt; 45 — risklər müsbət nəticələrə, &gt; 55 — mənfi nəticələrə meyllidir.</div>' +
      '<div class="cols2"><div class="card pad"><h3>İndeks: Nazirlik vs məlumat əsaslı</h3><div id="cb-i" class="ch"></div></div><div class="card pad"><h3>Kateqoriya balları (məlumat əsaslı)</h3><div id="cb-k" class="ch"></div></div></div>' +
      U.dt('cb-t', c2, null, { title: 'Risk balansı (C2_balance_of_risks) — bütün sətirlər', file: 'C2_balance_of_risks' });
    U.lines(U.$('#cb-i', el), Object.keys(by).map(function (k, i) { var r = by[k].sort(function (a, b) { return a.year - b.year; }); return { x: r.map(function (q) { return q.year; }), y: r.map(function (q) { return q.weighted; }), name: k, mode: 'lines+markers', c: i ? '#0E6F7C' : '#E07B00' }; })
      .concat([{ x: [2021.5, 2030.5], y: [45, 45], name: '45', c: '#9AA6B2', dash: 'dot', w: 1 }, { x: [2021.5, 2030.5], y: [55, 55], name: '55', c: '#9AA6B2', dash: 'dot', w: 1 }]), 'indeks', { years: true, yr: [0, 100] });
    var dd = U.by(parts.filter(function (r) { return /RU/.test(r.version); }), 'category_az');
    U.lines(U.$('#cb-k', el), Object.keys(dd).map(function (k, i) { var r = dd[k].sort(function (a, b) { return a.year - b.year; }); return { x: r.map(function (q) { return q.year; }), y: r.map(function (q) { return q.score; }), name: k, mode: 'lines+markers', c: U.PAL[i] }; }), 'bal (1–5)', { years: true, yr: [0, 5.2] });
  }
  function shocks(el) {
    U.need(['c4lib'], el, function () {
      var L = U.raw('C4_caem_shock_library'), keys = Object.keys(L.s).sort(), k = CA.lib && L.s[CA.lib] ? CA.lib : keys[0], vn = {}, ix = {};
      U.T('C4_caem_variables').forEach(function (r) { vn[r.variable] = r.variable_name + ' (' + r.unit + ')'; });
      U.T('C4_caem_shock_index').forEach(function (r) { ix[r.library.split(' ')[0].replace('.', '') + '|' + r.shock_id] = r; });
      var label = function (key) { var p = key.split('|'), r = U.T('C4_caem_shock_index').filter(function (q) { return q.shock_id === p[1]; })[0]; var q = ix[p[0].split(' ')[0].replace('.', '') + '|' + p[1]] || r || {}; return '«' + String(q.library || p[0]).split(' (')[0] + '» vərəqi · ' + (q.shock || p[1]); };
      var vs = Object.keys(L.s[k]).sort(), sel = CA.vars.filter(function (v) { return vs.indexOf(v) >= 0; });
      el.innerHTML = '<div class="note-w"><b>Nazirlik CAEM modeli — müqayisə.</b> AZE Model gecikmiş hədli sistemdir; RU-nun əsas ötürmə kanalı deyil (struktur MikroUnit zənciri əsasdır). Kitabxana yalnız müqayisə və Nazirliklə uyğunlaşdırma üçündür.</div>' +
        '<div class="toolbar">' + U.sel('c4-s', keys.map(function (x) { return [x, label(x)]; }), k) + '</div><div class="chips" id="c4-v">' + vs.map(function (v) { return '<label class="ck"><input type="checkbox" value="' + U.esc(v) + '"' + (sel.indexOf(v) >= 0 ? ' checked' : '') + '> ' + U.esc(vn[v] || v) + '</label>'; }).join('') + '</div>' +
        '<div class="card pad"><h3>İmpuls cavabları: ' + U.esc(label(k)) + '</h3><div id="c4-c" class="ch" style="min-height:340px"></div></div>' +
        U.dt('c4-i', U.T('C4_caem_shock_index'), null, { title: 'Şok kitabxanasının indeksi (C4)', file: 'C4_caem_shock_index' }) + U.dt('c4-va', U.T('C4_caem_variables'), null, { title: 'AZE Model dəyişənləri (C4)', file: 'C4_caem_variables' }) +
        U.dt('c4-x', U.T('C4_caem_irf_validation'), null, { title: 'AZE Model təkrarının yoxlaması (C4_caem_irf_validation)', file: 'C4_caem_irf_validation' });
      U.lines(U.$('#c4-c', el), sel.map(function (v, i) { return { x: L.h, y: L.s[k][v], name: vn[v] || v, mode: 'lines+markers', c: U.PAL[i] }; }), 'cavab', { xt: 'üfüq (il)', zero: true, h: 340 });
      U.$('#c4-s', el).onchange = function (e) { CA.lib = e.target.value; shocks(el); };
      U.$('#c4-v', el).onchange = function () { CA.vars = U.$$('#c4-v input:checked', el).map(function (x) { return x.value; }); shocks(el); };
    });
  }
  U.pages.caem = function (v, p) {
    var sub = p[1] || '';
    v.innerHTML = U.head('Nazirliyin CAEM risk-təsir və risk-kateqoriya vərəqləri', 'CAEM', 'CAEM iş kitabının risk vərəqləri cari məlumatla yenidən hesablanır, RU reyestri ilə uyğunlaşdırılır və yoxlanılır. CAEM rəqəmləri Nazirliyin girişləridir — yoxlanılır, həqiqət kimi qəbul edilmir; aşkar edilən qüsurlar Nazirlik üçün reyestrdədir.') +
      U.subtabs('caem', [['', 'Siqnallar (C1)'], ['balans', 'Risk balansı (C2)'], ['kateqoriya', 'Kateqoriyalar (C3)'], ['sok', 'Şok kitabxanası (C4)'], ['oturme', 'Ötürmə müqayisəsi (C5)'], ['tapinti', 'Tapıntılar (C6)']], sub) + '<div id="ca-body"></div>';
    var b = U.$('#ca-body', v);
    if (sub === 'balans') balance(b);
    else if (sub === 'kateqoriya') b.innerHTML = U.dt('cc-t', U.T('C3_category_map'), null, { title: 'CAEM kateqoriyaları ↔ RU risk reyestri (C3_category_map) və yeni reyestr sətri təklifləri', file: 'C3_category_map', href: function (r) { return r.ru_risk_id ? '#/reyestr/' + r.ru_risk_id : null; } });
    else if (sub === 'sok') shocks(b);
    else if (sub === 'oturme') { U.SC.f = U.SC.f || 'brent'; U.need(['scal'], b, function () { U.SC2.models(b); }); }
    else if (sub === 'tapinti') { var c6 = U.T('C6_caem_findings'), sv = U.by(c6, 'severity_az');
      b.innerHTML = '<div class="tiles">' + Object.keys(sv).map(function (k) { return U.tile('Ciddilik: ' + U.esc(k), U.nf(sv[k].length, 0) + '<small>tapıntı</small>', '', k === 'yüksək' ? 'bad' : k === 'orta' ? 'warn' : 'ok'); }).join('') + '</div>' +
        U.dt('cf-t', c6, [{ k: 'finding_id', l: '№' }, { k: 'severity_az', l: 'Ciddilik', f: U.sigchip }, { k: 'sheet', l: 'Vərəq' }, { k: 'cell_range', l: 'Xanalar' }, { k: 'issue_az', l: 'Qüsur' }, { k: 'evidence', l: 'Sübut' }, { k: 'consequence_az', l: 'Nəticəsi' }, { k: 'recommendation_az', l: 'Tövsiyə' }], { title: 'CAEM tapıntılar reyestri (C6) — Nazirlik üçün', file: 'C6_caem_findings' }); }
    else signals(b);
  };
})();
