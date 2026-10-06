/* p_nfr.js — Geriyə sınaq (NFR1): every test with n and result («yoxlanıla bilmir» where n = 0 — never counted as
   passed), calibration factors applied to the simulation, PIT histograms (Brent density, macro fan), the rolling GaR
   check and the early-warning predictions. */
(function () {
  'use strict';
  var U = window.U;
  function hist(el, vals, title) {
    var bins = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; vals.forEach(function (v) { if (U.isNum(v)) bins[Math.min(9, Math.floor(v * 10))]++; });
    var n = vals.filter(U.isNum).length;
    U.bars(el, bins.map(function (b, i) { return (i / 10 + 0.05).toFixed(2); }), [{ name: 'PIT sayı', y: bins, c: '#0E6F7C' }, { name: 'ideal (bərabər)', y: bins.map(function () { return n / 10; }), c: '#E07B00' }], 'say (n = ' + n + ')', { cat: true, h: 260, xt: title });
  }
  U.pages.sinaq = function (v) {
    var R = U.T('NFR1_backtest_results'), ok = R.filter(function (r) { return r.netice === 'keçdi'; }).length, no = R.filter(function (r) { return r.netice === 'keçmədi'; }).length, nt = R.filter(function (r) { return /bilmir|bilməz/.test(r.netice); });
    var g = U.T('NFR1_gar_rolling'), ew = U.T('NFR1_ews_brent_predictions'), sl = U.T('NFR1_ews_slowdown');
    v.innerHTML = U.head('NFR1 — dəqiqlik və etibarlılıq', 'Geriyə doğru sınaq', 'Hər model sadə etalona qarşı, yalnız proqnoz anında mövcud olan məlumatla yoxlanılır; hər test n ilə göstərilir. <b>«Yoxlanıla bilmir» «keçdi» deyil</b>; mənfi nəticələr saxlanılır və izah olunur. Kalibrləmə qaydası simulyasiyaya avtomatik tətbiq olunur.') +
      '<div class="tiles" style="margin-top:16px">' + U.tile('Test', U.nf(R.length, 0), 'rüb ' + U.esc((R[0] || {}).rub || '') + ' · ' + U.esc((R[0] || {}).tarix || '')) + U.tile('Keçdi', U.nf(ok, 0), '', 'ok') + U.tile('Keçmədi', U.nf(no, 0), 'mənfi nəticə — izahı cədvəldə', no ? 'bad' : 'ok') +
      U.tile('Yoxlanıla bilmir (n = 0)', U.nf(nt.length, 0), nt.map(function (r) { return r.test_id; }).join(', '), nt.length ? 'warn' : '') + '</div>' +
      U.dt('nf-t', R, [{ k: 'test_id', l: 'Test' }, { k: 'model', l: 'Model' }, { k: 'hedef', l: 'Hədəf' }, { k: 'n', l: 'n', n: 1, d: 0, f: function (v) { return v === 0 ? '<b class="down">0</b>' : U.nf(v, 0); } }, { k: 'pencere', l: 'Pəncərə' }, { k: 'metrik', l: 'Metrika' },
        { k: 'deyer', l: 'Dəyər', n: 1, d: 3 }, { k: 'hedd', l: 'Hədd' }, { k: 'netice', l: 'Nəticə', f: function (v) { return /bilmir|bilməz/.test(v) ? '<span class="chip warn">' + U.esc(v) + '</span>' : U.sigchip(v); } }, { k: 'melumat_bazasi', l: 'Məlumat bazası' }, { k: 'qeyd', l: 'Qeyd' }],
        { title: 'Sınaq nəticələri (NFR1_backtest_results)', file: 'NFR1_backtest_results', rowCls: function (r) { return /bilmir/.test(r.netice) ? 'sub' : ''; } }) +
      U.dt('nf-c', U.T('NFR1_calibration'), null, { title: 'Kalibrləmə əmsalları (NFR1_calibration): qalıq σ miqyası və qərar', file: 'NFR1_calibration' }) +
      (U.has('NFR1_calibration_shrinkage') ? U.dt('nf-sh', U.T('NFR1_calibration_shrinkage'), null, { title: 'Kalibrləmə əmsallarının büzülməsi və örtüyün yenidən yoxlanılması (NFR1_calibration_shrinkage)', file: 'NFR1_calibration_shrinkage' }) : '') +
      '<div class="cols2"><div class="card pad"><h3>Brent sıxlıq proqnozu: PIT (NFR1_brent_density_pit)</h3><div id="nf-p1" class="ch"></div><p class="small muted">Yaxşı kalibrlənmiş sıxlıqda PIT bərabər paylanır.</p></div>' +
      '<div class="card pad"><h3>Makro yelpik: PIT (NFR1_macro_fan_pit)</h3><div id="nf-p2" class="ch"></div></div>' +
      '<div class="card pad"><h3>GaR sürüşən yoxlama: faktiki vs kvantillər (NFR1_gar_rolling)</h3><div id="nf-g" class="ch"></div></div>' +
      '<div class="card pad"><h3>Erkən xəbərdarlıq: Brent çöküşü ehtimalı (NFR1_ews_brent_predictions)</h3><div id="nf-e" class="ch"></div></div></div>' +
      U.dt('nf-s', sl, null, { title: 'Erkən xəbərdarlıq: qeyri-neft artımının zəifləməsi (NFR1_ews_slowdown)', file: 'NFR1_ews_slowdown' }) +
      U.dt('nf-g2', g, null, { title: 'GaR sürüşən yoxlama — cədvəl', file: 'NFR1_gar_rolling' }) +
      U.dt('nf-b', U.T('NFR1_brent_density_pit'), null, { title: 'Brent sıxlıq PIT — cədvəl (CRPS model vs normal etalon)', file: 'NFR1_brent_density_pit' }) +
      U.dt('nf-m', U.T('NFR1_macro_fan_pit'), null, { title: 'Makro yelpik PIT — cədvəl', file: 'NFR1_macro_fan_pit' }) +
      U.dt('nf-r', U.T('NFR1_backtest_register'), null, { title: 'Rüblük sınaq reyestri (NFR1_backtest_register) — arxiv forması', file: 'NFR1_backtest_register', lim: 20 });
    hist(U.$('#nf-p1', v), U.T('NFR1_brent_density_pit').map(function (r) { return r.pit; }), 'PIT');
    hist(U.$('#nf-p2', v), U.T('NFR1_macro_fan_pit').map(function (r) { return r.pit; }), 'PIT');
    var x = g.map(function (r) { return r.hedef_il; });
    U.lines(U.$('#nf-g', v), [U.band ? null : null].filter(Boolean).concat([{ x: x, y: g.map(function (r) { return r.faktiki; }), name: 'faktiki', mode: 'lines+markers', c: '#15202B' }, { x: x, y: g.map(function (r) { return r.q10; }), name: 'model P10', c: '#B3261E', dash: 'dash' }, { x: x, y: g.map(function (r) { return r.q50; }), name: 'model median', c: '#0E6F7C' },
      { x: x, y: g.map(function (r) { return r.q90; }), name: 'model P90', c: '#1E7B4F', dash: 'dash' }, { x: x, y: g.map(function (r) { return r.bench_q10; }), name: 'etalon P10', c: '#B3261E', dash: 'dot', w: 1.2 }]), '%', { years: true });
    U.lines(U.$('#nf-e', v), [{ x: ew.map(function (r) { return r.ay; }), y: ew.map(function (r) { return r.ehtimal; }), name: 'ehtimal', c: '#0E6F7C', w: 1.4 }, { x: ew.map(function (r) { return r.ay; }), y: ew.map(function (r) { return r.hedd; }), name: 'hədd', c: '#E07B00', dash: 'dot', w: 1.2 },
      { x: ew.filter(function (r) { return r.hadise; }).map(function (r) { return r.ay; }), y: ew.filter(function (r) { return r.hadise; }).map(function () { return 1; }), name: 'faktiki çöküş', mode: 'markers', marker: { size: 6, color: '#B3261E' } }], 'ehtimal', { xtype: 'category' });
  };
})();
