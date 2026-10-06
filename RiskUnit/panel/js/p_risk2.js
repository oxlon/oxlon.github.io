/* p_risk2.js — drill-down part 2: score history and alerts, scalability curve of the risk's factors (S0/S1/S2),
   affected variables (S4) and parameters (S5), CAEM category and signal (C1/C3), measures (M1/M2), residual risk
   (FR3/M5) and the daily decision rows (S7). */
(function () {
  'use strict';
  var U = window.U, RK = U.RK;
  U.HEADT = ['ru:nonoil_g', 'ru:nonoil_lvl', 'ru:cpi', 'ru:budget_gdp', 'ru:tb_gdp', 'ru:debt_gdp'];
  U.scoreYear = function () { return +(U.T('FR2_risk_scores')[0] || {}).ufuq || 2027; };
  /* S1 response curve: delta in the score year vs k σ for the headline targets */
  U.curve = function (el, fac, targets, year) {
    var s1 = U.T('S1_scalability_grid').filter(function (r) { return r.amil === fac && r.il === year && targets.indexOf(r.hedef_id) >= 0; });
    var by = U.by(s1.filter(function (r) { return r.variant !== 'canlı'; }), 'hedef_id'), live = s1.filter(function (r) { return r.variant === 'canlı'; });
    var sets = targets.filter(function (t) { return by[t]; }).map(function (t, i) { var r = by[t].sort(function (a, b) { return a.k_sigma - b.k_sigma; });
      return { x: r.map(function (q) { return q.k_sigma; }), y: r.map(function (q) { return q.delta; }), name: r[0].hedef_ad + ' (' + r[0].vahid + ')', mode: 'lines+markers', c: U.PAL[i] }; });
    live.filter(function (r) { return by[r.hedef_id]; }).forEach(function (r) { sets.push({ x: [r.k_sigma], y: [r.delta], name: 'bu gün: ' + r.hedef_ad, mode: 'markers', marker: { size: 13, symbol: 'star', color: '#15202B' }, showlegend: false }); });
    U.lines(el, sets, 'bazadan fərq', { xt: 'şokun ölçüsü, σ (ulduz — bugünkü canlı sapma)', zero: true, h: 330, hm: 'closest' });
  };
  function factorBlock(el, f, rid) {
    var y = U.scoreYear();
    el.innerHTML = '<div class="note-b"><b>' + U.esc(f.amil_ad) + '</b>: 1σ = ' + U.nf(f.olcu_1sigma) + ' ' + U.esc(f.vahid) + ' (' + U.esc(f.sigma_esasi) + '); ötürmə: ' + U.esc(f.oturme_kanali) + '; pis istiqamət: ' + U.esc(f.pis_istiqamet) +
      (U.isNum(f.canli_k_sigma) ? '. <b>Bu gün:</b> ' + U.esc(f.canli_tesvir) + ' (' + U.sg(f.canli_k_sigma, 2) + 'σ)' : '') + '. <a href="#/miqyas?f=' + f.amil + '">Miqyaslanma bölməsində aç →</a></div>' +
      '<div class="cols2"><div class="card pad"><h3>Miqyaslanma əyrisi, ' + y + ' (S1)</h3><div class="ch" id="rk-cv"></div></div><div class="card pad"><h3>Ən çox təsirlənən komponentlər, +1σ (S4)</h3><div id="rk-s4" class="ch"></div></div></div><div id="rk-s5"></div>';
    U.need(['s1'], U.$('#rk-cv', el), function () { U.curve(U.$('#rk-cv', el), f.amil, U.HEADT.slice(0, 4), y); });
    U.need(['s4'], U.$('#rk-s4', el), function () {
      var s4 = U.T('S4_impact_map').filter(function (r) { return r.amil === f.amil && r.seviyye === 'komponent'; }).sort(function (a, b) { return b.ehemiyyet - a.ehemiyyet; }).slice(0, 14);
      U.barH(U.$('#rk-s4', el), s4.map(function (r) { return r.modul + ' · ' + r.komponent_ad; }), s4.map(function (r) { return r.tesir_2027; }), 'təsir 2027 (' + (s4[0] ? s4[0].olcu_sinfi : '') + ')', { color: '#6A3FB5' });
    });
    U.need(['scal'], U.$('#rk-s5', el), function () {
      var s5 = U.T('S5_parameter_sensitivity').filter(function (r) { return r.amil === f.amil && r.parametr; }).sort(function (a, b) { return Math.abs(b.nisbi_dalgalanma || 0) - Math.abs(a.nisbi_dalgalanma || 0); }).slice(0, 12);
      U.$('#rk-s5', el).innerHTML = U.dt('rk-s5t', s5, [{ k: 'hedef_ad', l: 'Hədəf' }, { k: 'tenlik', l: 'Tənlik' }, { k: 'parametr_ad', l: 'Parametr' }, { k: 'deyer', l: 'Əmsal', n: 1, d: 3 }, { k: 'se', l: 'SE', n: 1, d: 3 },
        { k: 'cavab_baza', l: 'Cavab', n: 1, d: 3 }, { k: 'cavab_minus_1se', l: 'Əmsal −1 SE', n: 1, d: 3 }, { k: 'cavab_plus_1se', l: 'Əmsal +1 SE', n: 1, d: 3 }, { k: 'nisbi_dalgalanma', l: 'Nisbi dalğalanma', n: 1, p: 1, d: 0 }],
        { title: 'Ötürməni daşıyan parametrlər (S5): əmsal ±1 SE dəyişəndə cavab necə dəyişir', file: rid + '_S5' });
    });
  }
  function factors(el, rid) {
    var fs = U.T('S0_factor_sigma').filter(function (f) { return U.hasId(f.risk_idler, rid); });
    if (!fs.length) { el.innerHTML = '<p class="muted">Bu risk üçün miqyaslanma amili yoxdur (nəticə, siqnal və ya model riski). Təsirlənən dəyişənlər üçün əlaqəli amillərə baxın: <a href="#/miqyas">Miqyaslanma</a>.</p>'; return; }
    el.innerHTML = (fs.length > 1 ? '<div class="toolbar">' + U.seg('rk-fs', fs.map(function (f) { return [f.amil, f.amil_ad]; }), fs[0].amil) + '</div>' : '') + '<div id="rk-fb"></div>';
    var draw = function (a) { factorBlock(U.$('#rk-fb', el), fs.filter(function (f) { return f.amil === a; })[0], rid); };
    draw(fs[0].amil);
    var sg = U.$('#rk-fs', el); if (sg) sg.onclick = function (e) { var b = e.target.closest('[data-v]'); if (!b) return; U.$$('button', sg).forEach(function (x) { x.classList.toggle('on', x === b); }); draw(b.getAttribute('data-v')); };
  }
  function caem(rid) {
    var c3 = U.T('C3_category_map').filter(function (r) { return r.ru_risk_id === rid; });
    if (!c3.length) return '<p class="muted">CAEM-də bu riskə uyğun kateqoriya yoxdur (yalnız RU reyestrində).</p>';
    var ind = U.uniq(c3.map(function (r) { return r.c1_indicator; })), c1 = U.T('C1_caem_signals').filter(function (r) { return ind.indexOf(r.indicator) >= 0 && r.primary && r.period !== 'tarix'; });
    return U.dt('rk-c3', c3, [{ k: 'caem_category_az', l: 'CAEM kateqoriyası' }, { k: 'caem_weight', l: 'Çəki', n: 1 }, { k: 'caem_sheet', l: 'Vərəq' }, { k: 'match_az', l: 'Uyğunluq' }, { k: 'note_az', l: 'Qeyd' }], { title: 'CAEM kateqoriyası (C3)', file: rid + '_C3' }) +
      (c1.length ? U.dt('rk-c1', c1, [{ k: 'indicator_az', l: 'Göstərici' }, { k: 'year', l: 'İl', n: 1, d: 0 }, { k: 'period', l: 'Dövr' }, { k: 'value', l: 'Dəyər', n: 1 }, { k: 'z', l: 'z', n: 1, d: 2 }, { k: 'band', l: 'Zolaq', n: 1, d: 0 }, { k: 'class_az', l: 'Siqnal', f: U.sigchip }, { k: 'score_0_5', l: 'Bal (0–5)', n: 1, d: 2 }, { k: 'source', l: 'Mənbə' }],
        { title: 'CAEM σ-zolaq siqnalı (C1)', file: rid + '_C1', href: function () { return '#/caem'; } }) : '');
  }
  function measures(rid) {
    var m = U.T('M1_measures_v2').filter(function (r) { return U.hasId(r.risk_idler, rid); });
    return U.dt('rk-m1', m, [{ k: 'tedbir_id', l: 'Tədbir', f: function (v) { return '<a href="#/tedbir/reyestr?t=' + v + '"><b>' + v + '</b></a>'; } }, { k: 'tedbir', l: 'Ad' }, { k: 'strategiya_v2', l: 'Strategiya' }, { k: 'mesul', l: 'Məsul' }, { k: 'status_az', l: 'Status', f: U.sigchip }, { k: 'muddet', l: 'Müddət' },
      { k: 'xerc_mln_azn', l: 'Xərc, mln AZN', n: 1, d: 1 }, { k: 'kemiyyet_metodu', l: 'Kəmiyyətləndirmə' }, { k: 'effekt_hedef_funksiya', l: 'Risk azalması (hədəf f.)', n: 1, d: 3 }, { k: 'd_ES10_g', l: 'Δ ES10 qeyri-neft', n: 1, d: 3 }, { k: 'd_ES10_cpi', l: 'Δ ES10 infl.', n: 1, d: 3 }, { k: 'optimal_planda_500', l: 'Optimal planda' }],
      { title: 'Risk azaldıcı tədbirlər (M1) — ' + m.length, file: rid + '_tedbirler', href: function (r) { return '#/tedbir/reyestr?t=' + r.tedbir_id; } });
  }
  function residual(rid) {
    var a = U.T('FR3_residual_risk').filter(function (r) { return r.risk_id === rid; }), b = U.T('M5_residual_v2').filter(function (r) { return r.risk_id === rid; });
    return '<div class="cols2"><div>' + U.dt('rk-r3', a, null, { title: 'Qalıq risk (FR3): cari status və hədəf', file: rid + '_FR3_qaliq' }) + '</div><div>' +
      U.dt('rk-r5', b, [{ k: 'kanallar', l: 'Kanallar' }, { k: 'FR2_skor', l: 'Skor indi', n: 1, d: 0 }, { k: 'qaliq_skor_plan', l: 'Qalıq skor (plan)', n: 1, d: 0 }, { k: 'qaliq_prioritet', l: 'Qalıq prioritet', f: U.prio }, { k: 'plandaki_tedbirler', l: 'Plandakı tədbirlər' },
        { k: 'quyruq_g_baza', l: 'Quyruq qeyri-neft: baza', n: 1, d: 3 }, { k: 'quyruq_g_plan', l: 'plan', n: 1, d: 3 }, { k: 'quyruq_cpi_baza', l: 'Quyruq infl.: baza', n: 1, d: 3 }, { k: 'quyruq_cpi_plan', l: 'plan', n: 1, d: 3 }], { title: 'Plandan sonra qalıq risk (M5)', file: rid + '_M5' }) + '</div></div>';
  }
  RK.more = function (el, r, g) {
    var rid = r.risk_id, al = U.T('FR2_alerts').filter(function (a) { return a.risk_id === rid; }), s7 = U.T('S7_daily_decision').filter(function (x) { return U.hasId(x.risk_idler, rid); });
    var extra = '';
    if (rid === 'R19' && U.has('FR2_model_risk')) extra += U.dt('rk-mr', U.T('FR2_model_risk'), null, { title: 'Model riski: konsensus, fərq və alternativ paylanma (FR2_model_risk)', file: 'R19_model_riski' });
    var ts = U.T('FR2_threshold_sensitivity').filter(function (x) { return x.risk_id === rid; });
    if (ts.length) extra += U.dt('rk-ts', ts, null, { title: 'Hədd həssaslığı: hədd dəyişsə ehtimal necə dəyişir (FR2_threshold_sensitivity)', file: rid + '_hedd' });
    if (rid === 'R03' && U.has('FR1_fx_transmission')) extra += U.dt('rk-fx', U.T('FR1_fx_transmission'), null, { title: 'Məzənnə ötürməsi (FR1_fx_transmission)', file: 'R03_mezenne_oturmesi' });
    el.innerHTML = (extra ? U.sec('Əlavə təhlil', '', extra) : '') + U.sec('Təsirlənən dəyişənlər və miqyaslanma', 'şokun ölçüsü dəyişdikcə əsas göstəricilər, komponentlər və ötürməni daşıyan parametrlər', '<div id="rk-fac"></div>') +
      U.sec('CAEM kateqoriyası və siqnal', '', caem(rid)) + U.sec('Tədbirlər', 'risk azaldıcı tədbirlər və onların kəmiyyətləndirilmiş effekti', measures(rid)) +
      U.sec('Qalıq risk', 'tədbirlərdən sonra qalan risk', residual(rid)) +
      U.sec('Xəbərdarlıqlar və gündəlik qərar', '', (al.length ? '<div class="card alist">' + al.map(function (a) { return '<div class="arow"><span>' + U.sigchip(a.ciddilik) + '</span><span>' + U.esc(a.mesaj) + '</span><span class="when">' + U.esc(a.tip) + '</span></div>'; }).join('') + '</div>' : '<p class="muted">Bu risk üçün xəbərdarlıq yoxdur.</p>') +
        (s7.length ? U.dt('rk-s7', s7, [{ k: 'amil_ad', l: 'Amil' }, { k: 'canli_sapma', l: 'Bugünkü sapma' }, { k: 'tesir_novu', l: 'Təsirin növü' }, { k: 'en_cox_tesirlenen', l: 'Ən çox təsirlənən' }, { k: 'teklif_olunan_tedbirler', l: 'Təklif olunan tədbirlər' }, { k: 'qerar_qeydi', l: 'Qərar qeydi' }], { title: 'Gündəlik qərar cədvəli (S7)', file: rid + '_S7' }) : '')) +
      U.sec('Skor tarixçəsi', '', '<div class="card pad"><div id="rk-hist" class="ch" style="min-height:240px"></div></div>');
    factors(U.$('#rk-fac', el), rid);
    var h = U.T('FR2_score_history').filter(function (x) { return x.risk_id === rid; }).sort(function (a, b) { return a.as_of < b.as_of ? -1 : 1; });
    U.lines(U.$('#rk-hist', el), [{ x: h.map(function (q) { return q.as_of; }), y: h.map(function (q) { return q.skor; }), name: 'skor', mode: 'lines+markers' }, { x: h.map(function (q) { return q.as_of; }), y: h.map(function (q) { return q.ehtimal * 100; }), name: 'ehtimal, %', mode: 'lines+markers', y2: true, dash: 'dot' }], 'skor', { xtype: 'category', h: 260, y2: 'ehtimal, %' });
  };
})();
