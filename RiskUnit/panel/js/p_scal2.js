/* p_scal2.js — Miqyaslanma part 2: elasticities (S2) and non-linearity / threshold sizes (S3) under the explorer, the
   live /scalability/run call, the impact map over every MicroUnit component (S4), transmission-carrying parameters (S5)
   and the cross-model comparison (S6, C5 incl. the FR1 oscillation check). */
(function () {
  'use strict';
  var U = window.U, SC = U.SC;
  var S2 = U.SC2 = {};
  S2.more = function (el, f, k) {
    var s2 = U.T('S2_elasticities').filter(function (r) { return r.amil === f.amil && r.k_sigma === k && U.HEADT.concat(['fr1:rgdp', 'fr1:infl', 'fr1:balance_n', 'fr1:rev_oil_n']).indexOf(r.hedef_id) >= 0; });
    var s3 = U.T('S3_nonlinearity').filter(function (r) { return r.amil === f.amil; });
    var thr = s3.filter(function (r) { return r.hedd_ad; }), nm = {};
    U.T('S1_scalability_grid').forEach(function (r) { nm[r.hedef_id] = r.hedef_ad; });
    s2 = s2.map(function (r) { return Object.assign({ hedef_ad: nm[r.hedef_id] || r.hedef_id }, r); });
    el.innerHTML = U.sec('Elastikliklər (S2)', 'σ vahidinə və təbii vahidə düşən cavab; log amillər üçün nisbi elastiklik — seçilmiş ölçüdə', U.dt('sc-e', s2, [{ k: 'hedef_ad', l: 'Göstərici' }, { k: 'il', l: 'İl', n: 1, d: 0 }, { k: 'delta_per_sigma', l: '1σ-ya düşən cavab', n: 1, d: 4 }, { k: 'delta_per_unit', l: 'Təbii vahidə düşən cavab', n: 1, d: 5 }, { k: 'vahid_cavab_izah', l: 'Vahid' }, { k: 'elastiklik', l: 'Elastiklik', n: 1, d: 4 }], { title: 'Elastikliklər: ' + U.esc(f.amil_ad) + ', ' + U.sg(k, 2) + 'σ', file: 'S2_' + f.amil })) +
      U.sec('Qeyri-xəttilik və hədd ölçüləri (S3)', 'asimmetriya = |cavab(−kσ)| / |cavab(+kσ)|; əyrilik; risk iştahı həddinin hansı σ ölçüsündə keçildiyi',
        U.dt('sc-th', thr, [{ k: 'hedd_ad', l: 'Hədd' }, { k: 'il', l: 'İl', n: 1, d: 0 }, { k: 'hedd', l: 'Hədd dəyəri', n: 1 }, { k: 'baza_seviyye', l: 'Baza səviyyəsi', n: 1, d: 2 }, { k: 'k_hedd_menfi', l: 'Keçən şok (−), σ', n: 1, f: kf }, { k: 'olcu_hedd_menfi', l: 'Təbii ölçü (−)', n: 1, f: kf },
          { k: 'k_hedd_musbet', l: 'Keçən şok (+), σ', n: 1, f: kf }, { k: 'olcu_hedd_musbet', l: 'Təbii ölçü (+)', n: 1, f: kf }, { k: 'inandiriciliq_hedd', l: 'İnandırıcılıq həddi, σ', n: 1 }], { title: 'Risk iştahı həddləri: neçə σ-lıq şok həddi keçir? («—» — ±3σ daxilində keçilmir)', file: 'S3_hedd_' + f.amil }) +
        U.dt('sc-nl', s3, [{ k: 'hedef_ad', l: 'Göstərici', cls: 'lw' }, { k: 'il', l: 'İl', n: 1, d: 0 }, { k: 'vahid', l: 'Vahid' }, { k: 'cavab_m1', l: 'Cavab −1σ', n: 1, d: 3 }, { k: 'cavab_p1', l: 'Cavab +1σ', n: 1, d: 3 }, { k: 'asimmetriya_1', l: 'Asimmetriya ±1σ', n: 1, d: 2 }, { k: 'asimmetriya_3', l: 'Asimmetriya ±3σ', n: 1, d: 2 },
          { k: 'eyrilik_1', l: 'Əyrilik ±1σ', n: 1, d: 3 }, { k: 'miqyas_sapmasi_+3', l: 'Miqyas sapması +3σ', n: 1, d: 3 }, { k: 'miqyas_sapmasi_-3', l: 'Miqyas sapması −3σ', n: 1, d: 3 }, { k: 'qeyri_xetti', l: 'Qeyri-xətti' }, { k: 'qeyd', l: 'Qeyd' }], { title: 'Qeyri-xəttilik (S3): ' + U.esc(f.amil_ad) + ' — bütün göstəricilər', file: 'S3_' + f.amil }));
  };
  function kf(v) { return U.isNum(v) ? U.nf(v, 2) : '<span class="muted">—</span>'; }
  S2.run = function (el, f, size, unit) {
    if (!U.isNum(size)) { U.toast('Ölçünü rəqəmlə yazın'); return; }
    var body = { factor: f.amil, live: true, top_components: 40 };
    if (unit === 'size') body.sizes = [size]; else body.k_sigma = [size];
    el.innerHTML = '<p class="small muted">Hesablanır… (MikroUnit zənciri, ≈ 1–5 s)</p>';
    U.API.scal(body).then(function (r) {
      el.innerHTML = '<p class="small">Hazırdır · ' + U.nf(r.seconds, 1) + ' s · ölçülər: ' + (r.sizes || []).map(function (s) { return U.sg(s.k_sigma, 2) + 'σ = ' + U.sg(s.size, 2); }).join(', ') + '</p>' +
        U.dt('sc-rh', r.headline || [], null, { title: 'Baş göstəricilər (canlı hesablama)', file: 'miqyaslanma_canli_' + f.amil }) +
        U.dt('sc-rc', r.components || [], null, { title: 'Ən çox təsirlənən komponentlər', file: 'miqyaslanma_komponentler_' + f.amil }) +
        (r.parameters && r.parameters.length ? U.dt('sc-rp', r.parameters, null, { title: 'Ötürməni daşıyan parametrlər', file: 'miqyaslanma_parametrler_' + f.amil }) : '');
    }, function (e) { el.innerHTML = U.API.failHtml('Canlı miqyaslanma hesablaması', e); });
  };
  S2.map = function (el) {
    var F = S2.F = S2.F || { lv: 'komponent', m: '' }, s4 = U.T('S4_impact_map').filter(function (r) { return r.amil === SC.f; }), mods = U.uniq(s4.map(function (r) { return r.modul; })).sort();
    var rows = s4.filter(function (r) { return r.seviyye === F.lv && (!F.m || r.modul === F.m); }).sort(function (a, b) { return (b.ehemiyyet || 0) - (a.ehemiyyet || 0); }), top = rows.slice(0, 25), f = U.T('S0_factor_sigma').filter(function (x) { return x.amil === SC.f; })[0] || {};
    el.innerHTML = '<div class="note-b">+1σ şokunda (' + U.esc(f.amil_ad || '') + ': ' + U.nf(f.olcu_1sigma) + ' ' + U.esc(f.vahid || '') + ') MikroUnit-in bütün komponentləri (≈ 1 500) nə qədər təsirlənir. Əhəmiyyət — 2027 və 2030 təsirlərinin normallaşdırılmış ölçüsü (0–1).</div>' +
      '<div class="toolbar">' + U.seg('s4-lv', [['komponent', 'Komponentlər'], ['qrup', 'Qruplar']], F.lv) + U.sel('s4-m', [['', 'Bütün modullar']].concat(mods.map(function (m) { return [m, m]; })), F.m) + '<span class="small muted">' + U.nf(rows.length, 0) + ' sətir</span></div>' +
      '<div class="card pad"><h3>Ən çox təsirlənən ' + (F.lv === 'qrup' ? 'qruplar' : 'komponentlər') + ' (2027)</h3><div id="s4-c" class="ch"></div></div>' +
      U.dt('s4-t', rows, [{ k: 'sira', l: 'Sıra', n: 1, d: 0 }, { k: 'modul', l: 'Modul' }, { k: 'qrup', l: 'Qrup' }, { k: 'komponent_ad', l: 'Komponent' }, { k: 'komponent_id', l: 'Kod' }, { k: 'komponent_sayi', l: 'Komponent sayı', n: 1, d: 0 }, { k: 'sinif', l: 'Sinif' },
        { k: 'olcu_sinfi', l: 'Ölçü' }, { k: 'tesir_2027', l: 'Təsir 2027', n: 1, d: 3 }, { k: 'tesir_2030', l: 'Təsir 2030', n: 1, d: 3 }, { k: 'ehemiyyet', l: 'Əhəmiyyət', n: 1, d: 3, f: function (v) { return U.isNum(v) ? '<span class="bar-in" style="display:inline-block;width:70px;vertical-align:middle"><i style="width:' + Math.round(v * 100) + '%"></i></span> ' + U.nf(v, 2) : '—'; } }],
        { title: 'Təsir xəritəsi (S4_impact_map): ' + U.esc(f.amil_ad || ''), file: 'S4_' + SC.f });
    U.barH(U.$('#s4-c', el), top.map(function (r) { return r.modul + ' · ' + r.komponent_ad; }), top.map(function (r) { return r.tesir_2027; }), 'təsir 2027 (% və ya f.b.)', { color: top.map(function (r) { return r.tesir_2027 >= 0 ? '#1E7B4F' : '#B3261E'; }) });
    U.$('#s4-lv', el).onclick = function (e) { var b = e.target.closest('[data-v]'); if (b) { F.lv = b.getAttribute('data-v'); S2.map(el); } };
    U.$('#s4-m', el).onchange = function (e) { F.m = e.target.value; S2.map(el); };
  };
  S2.params = function (el) {
    var s5 = U.T('S5_parameter_sensitivity').filter(function (r) { return r.amil === SC.f; }), a = s5.filter(function (r) { return r.parametr; }), b = s5.filter(function (r) { return !r.parametr && r.komponent_id; });
    var tops = a.slice().sort(function (x, y) { return Math.abs(y.nisbi_dalgalanma || 0) - Math.abs(x.nisbi_dalgalanma || 0); }).slice(0, 15);
    el.innerHTML = '<div class="note-b">FR1 əmsalları ±1 standart xəta dəyişəndə şokun cavabı nə qədər dəyişir (hədəfli, şok altında) və aşağı axın modullarının statik həssaslığı (MikroUnit FRx_coef_sensitivity × S4 əhəmiyyəti). Böyük dalğalanma — nəticə həmin əmsala həssasdır.</div>' +
      '<div class="card pad"><h3>Ən həssas parametrlər (nisbi dalğalanma)</h3><div id="s5-c" class="ch"></div></div>' +
      U.dt('s5-a', a, [{ k: 'hedef_ad', l: 'Hədəf' }, { k: 'tenlik', l: 'Tənlik' }, { k: 'parametr_ad', l: 'Parametr' }, { k: 'parametr', l: 'Kod' }, { k: 'deyer', l: 'Əmsal', n: 1, d: 4 }, { k: 'se', l: 'SE', n: 1, d: 4 }, { k: 'cavab_baza', l: 'Cavab', n: 1, d: 4 },
        { k: 'cavab_minus_1se', l: '−1 SE', n: 1, d: 4 }, { k: 'cavab_plus_1se', l: '+1 SE', n: 1, d: 4 }, { k: 'd_cavab_d_parametr', l: 'd cavab / d əmsal', n: 1, d: 4 }, { k: 'nisbi_dalgalanma', l: 'Nisbi dalğalanma', n: 1, p: 1, d: 1 }, { k: 'metod', l: 'Metod' }], { title: 'FR1 parametrləri (S5, hədəfli ±1 SE)', file: 'S5_' + SC.f }) +
      U.dt('s5-b', b, [{ k: 'modul', l: 'Modul' }, { k: 'komponent_ad', l: 'Komponent' }, { k: 'swing', l: 'Dalğalanma', n: 1, d: 4 }, { k: 'ehemiyyet', l: 'Əhəmiyyət', n: 1, d: 3 }, { k: 'oturme_cekili_dalgalanma', l: 'Ötürmə çəkili dalğalanma', n: 1, d: 4 }, { k: 'metod', l: 'Metod' }], { title: 'Aşağı axın modulları (statik həssaslıq)', file: 'S5_asagi_axin_' + SC.f });
    U.barH(U.$('#s5-c', el), tops.map(function (r) { return r.hedef_ad + ' ← ' + r.parametr_ad + ' (' + r.tenlik + ')'; }), tops.map(function (r) { return r.nisbi_dalgalanma * 100; }), 'nisbi dalğalanma, %', { color: '#6A3FB5' });
  };
  S2.models = function (el) {
    var s6 = U.T('S6_cross_model').filter(function (r) { return r.amil === SC.f; }), ks = U.uniq(s6.map(function (r) { return r.konsept; })), c = S2.kc && ks.indexOf(S2.kc) >= 0 ? S2.kc : ks[0];
    var c5 = U.T('C5_transmission_comparison'), sh = U.uniq(c5.map(function (r) { return r.shock_key; })), s = S2.sh || sh[0];
    el.innerHTML = '<div class="note-b">Eyni +1σ şok müxtəlif modellərdə: MikroUnit zənciri (RU-nun əsas ötürməsi), MikroUnit FR1, OxLon həssaslıqları və <b>Nazirlik CAEM modeli — müqayisə</b> (gecikmiş hədli sistem; əsas ötürmə kanalı deyil). Böyük fərq model qeyri-müəyyənliyidir.</div>' +
      '<div class="toolbar">' + U.sel('s6-k', ks.map(function (k) { var r = s6.filter(function (x) { return x.konsept === k; })[0]; return [k, r.konsept_ad + ' (' + r.vahid + ')']; }), c) + '</div><div class="card pad"><div id="s6-c" class="ch"></div></div>' +
      U.dt('s6-t', s6, null, { title: 'Modellər arası dispersiya (S6): ' + SC.f, file: 'S6_' + SC.f }) +
      U.sec('Ötürmə müqayisəsi (C5)', 'müqayisəli şoklar: CAEM AZE Model vs MikroUnit FR1 vs OxLon', '<div class="toolbar">' + U.sel('c5-s', sh.map(function (k) { return [k, c5.filter(function (x) { return x.shock_key === k; })[0].shock_az]; }), s) + '</div><div class="cols2" id="c5-g"></div>' +
        U.dt('c5-t', c5, null, { title: 'C5 ötürmə müqayisəsi — bütün sətirlər', file: 'C5_transmission_comparison' }) + U.dt('c5-o', U.T('C5_fr1_oscillation'), null, { title: 'FR1 addım cavablarında işarə salınımı yoxlaması (C5)', file: 'C5_fr1_oscillation' }));
    var rs = s6.filter(function (r) { return r.konsept === c; }), by = U.by(rs, 'model');
    U.lines(U.$('#s6-c', el), Object.keys(by).map(function (m, i) { var r = by[m].sort(function (a, b) { return a.il - b.il; }); return { x: r.map(function (q) { return q.il; }), y: r.map(function (q) { return q.deyer; }), name: m, mode: 'lines+markers', c: /CAEM/.test(m) ? '#8A5300' : U.PAL[i], dash: /CAEM/.test(m) ? 'dash' : /dispersiya/.test(m) ? 'dot' : 'solid' }; }), (rs[0] || {}).vahid, { years: true, zero: true });
    var cs = c5.filter(function (r) { return r.shock_key === s; }), cc = U.uniq(cs.map(function (r) { return r.concept; }));
    U.$('#c5-g', el).innerHTML = cc.map(function (k, i) { return '<div class="card pad"><h3>' + U.esc(cs.filter(function (r) { return r.concept === k; })[0].concept_az) + '</h3><div class="ch" id="c5c-' + i + '"></div></div>'; }).join('');
    cc.forEach(function (k, i) { var b2 = U.by(cs.filter(function (r) { return r.concept === k; }), 'model'); U.lines(U.$('#c5c-' + i, el), Object.keys(b2).map(function (m, j) { var r = b2[m].sort(function (a, b) { return a.year - b.year; }); return { x: r.map(function (q) { return q.year; }), y: r.map(function (q) { return q.value; }), name: m, mode: 'lines+markers', c: /CAEM/.test(m) ? '#8A5300' : U.PAL[j], dash: /CAEM/.test(m) ? 'dash' : 'solid' }; }), (cs[0] || {}).unit, { years: true, zero: true, h: 260 }); });
    U.$('#s6-k', el).onchange = function (e) { S2.kc = e.target.value; S2.models(el); };
    U.$('#c5-s', el).onchange = function (e) { S2.sh = e.target.value; S2.models(el); };
  };
})();
