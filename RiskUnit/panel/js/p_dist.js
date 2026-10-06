/* p_dist.js — Paylanmalar: fan charts and full tables for non-oil growth, CPI, budget balance and Brent 2026–2030 in both
   views (baseline-centred FR2_distribution / live FR2_distribution_live), channel contributions, GaR cross-check and
   band layering. */
(function () {
  'use strict';
  var U = window.U;
  var G = [['g', 'Qeyri-neft ÜDM-in real artımı', 2, 'GaR həddi'], ['cpi', 'İnflyasiya (illik orta)', 6, 'AMB hədəfinin yuxarı həddi'], ['fis', 'Büdcə balansı / ÜDM', -1, 'büdcə həddi'], ['brent', 'Brent neft qiyməti', null, '']];
  var QC = [{ k: 'il', l: 'İl', n: 1, d: 0 }, { k: 'baza', l: 'Rəsmi baza', n: 1, d: 2 }, { k: 'p05', l: 'P5', n: 1, d: 2 }, { k: 'p10', l: 'P10', n: 1, d: 2 }, { k: 'p25', l: 'P25', n: 1, d: 2 }, { k: 'p50', l: 'Median', n: 1, d: 2 },
    { k: 'p75', l: 'P75', n: 1, d: 2 }, { k: 'p90', l: 'P90', n: 1, d: 2 }, { k: 'p95', l: 'P95', n: 1, d: 2 }, { k: 'orta', l: 'Orta', n: 1, d: 2 }, { k: 'ES10', l: 'ES (10 % quyruq)', n: 1, d: 2 }];
  var CH = { g: 'qeyri-neft artımı', cpi: 'inflyasiya', fis: 'büdcə balansı' };
  function block(g, B, L) {
    var b = B.filter(function (r) { return r.gosterici === g[0]; }), l = L.filter(function (r) { return r.gosterici === g[0]; }), cur = U.view() === 'live' ? l : b, oth = U.view() === 'live' ? b : l;
    var u = (b[0] || {}).vahid || '', both = b.concat(l);
    return { html: '<div class="card pad"><h3>' + g[1] + ', ' + U.esc(u) + '</h3><p class="small muted">Zolaqlar — ' + U.VIEWN[U.view()].toLowerCase() + ' baxış (5–95, 10–90, 25–75 %); göy xətlər — digər baxış; narıncı — rəsmi baza' + (g[2] != null ? '; qırmızı nöqtəli — ' + g[3] + ' (' + U.nf(g[2], 0) + ')' : '') + '.</p><div class="ch" id="ds-' + g[0] + '"></div>' +
      U.dt('dt-' + g[0], both, [{ k: 'baxis', l: 'Baxış' }].concat(QC), { title: 'Kvantillər 2026–2030 (hər iki baxış)', file: 'paylanma_' + g[0], bare: false }) + '</div>',
      draw: function () { U.fan(U.$('#ds-' + g[0]), cur, { live: oth, yt: u, hline: g[2], hlab: g[3], d: g[0] === 'brent' ? 1 : 2 }); } };
  }
  function contrib(el) {
    var c = U.T('FR2_contributions'), y = U.uniq(c.map(function (r) { return r.il; }))[0];
    el.innerHTML = '<div class="cols3">' + ['g', 'cpi', 'fis'].map(function (g) { return '<div class="card pad"><h3>' + CH[g] + ', ' + y + '</h3><div class="ch" id="dc-' + g + '"></div></div>'; }).join('') + '</div>' +
      U.dt('dc-t', c, [{ k: 'gosterici', l: 'Göstərici', f: function (v) { return CH[v] || v; } }, { k: 'il', l: 'İl', n: 1, d: 0 }, { k: 'kanal', l: 'Kanal (kod)' }, { k: 'ad', l: 'Kanal' }, { k: 'risk_id', l: 'Risk', f: function (v) { return v ? '<a href="#/reyestr/' + v + '">' + v + '</a>' : '—'; } },
        { k: 'orta', l: 'Orta töhfə', n: 1, d: 3 }, { k: 'dispersiya_payi', l: 'Dispersiya payı', n: 1, p: 1, d: 1 }, { k: 'quyruq_tohfesi', l: 'Quyruq töhfəsi', n: 1, d: 3 }, { k: 'quyruq_tohfesi_merkezlesmis', l: 'Quyruq töhfəsi (mərkəzləşmiş)', n: 1, d: 3 }],
        { title: 'Kanal töhfələri (FR2_contributions) — Eyler bölgüsü', file: 'FR2_contributions' });
    ['g', 'cpi', 'fis'].forEach(function (g) {
      var rs = c.filter(function (r) { return r.gosterici === g; }).sort(function (a, b) { return Math.abs(b.quyruq_tohfesi) - Math.abs(a.quyruq_tohfesi); }).slice(0, 10);
      U.barH(U.$('#dc-' + g, el), rs.map(function (r) { return r.ad; }), rs.map(function (r) { return r.quyruq_tohfesi; }), 'aşağı quyruğa töhfə', { color: '#B3261E', h: 320 });
    });
  }
  function layering(el) {
    var t = U.T('FR2_band_layering'), v = U.view();
    el.innerHTML = '<div class="cols3">' + ['g', 'cpi', 'fis'].map(function (g) { return '<div class="card pad"><h3>' + CH[g] + ': σ qatları</h3><div class="ch" id="dl-' + g + '"></div></div>'; }).join('') + '</div>' +
      U.dt('dl-t', t, null, { title: 'Yelpik qatları (FR2_band_layering): hədəf σ = amillərin σ-sı ⊕ qalıq σ; mərkəzləmə və canlı sürüşmə', file: 'FR2_band_layering' });
    ['g', 'cpi', 'fis'].forEach(function (g) {
      var rs = t.filter(function (r) { return r.gosterici === g && r.baxis === v; }).sort(function (a, b) { return a.il - b.il; }), x = rs.map(function (r) { return r.il; });
      U.bars(U.$('#dl-' + g, el), x, [{ name: 'amillər', y: rs.map(function (r) { return r.sig_factors; }), c: '#0E6F7C' }, { name: 'qalıq', y: rs.map(function (r) { return r.sig_resid; }), c: '#9AA6B2' }, { name: 'hədəf (cəmi)', y: rs.map(function (r) { return r.sig_target; }), c: '#E07B00' }], 'σ', { years: true, h: 280 });
    });
  }
  U.pages.paylanma = function (v) {
    var B = U.T('FR2_distribution'), L = U.T('FR2_distribution_live'), gar = U.T('FR2_gar_crosscheck'), blocks = G.map(function (g) { return block(g, B, L); });
    v.innerHTML = U.head('FR2 — risk paylanmaları', 'Paylanmalar 2026–2030', 'Rəsmi baza proqnozunun ətrafında birgə Monte Karlo paylanması (20 000 ssenari). <b>Baza mərkəzli</b> baxışda 2027-dən median rəsmi bazadır (2026 isə il-əvvəlindən faktiki məlumatla şərtləndirilib — Brent: müşahidə olunmuş ayların ortası, qeyri-neft ÜDM və İQİ: DSK-nın il-əvvəlindən faktiki göstəriciləri; buna görə 2026 medianı rəsmi bazadan fərqlənə bilər) — skorlar və istilik xəritəsi bununla hesablanır. <b>Canlı</b> baxışda bugünkü Brent qiyməti nəzərə alınır (D6 ilə uyğun). Baxışı yuxarıdakı düymə ilə dəyişin.') +
      '<div class="cols2" style="margin-top:18px">' + blocks.map(function (b) { return b.html; }).join('') + '</div>' +
      U.sec('Kanal töhfələri', 'hansı risk kanalı aşağı quyruğa nə qədər verir (FR2_contributions)', '<div id="ds-co"></div>') +
      U.sec('GaR müstəqil yoxlaması', 'kvantil reqressiyası ilə qeyri-neft artımı kvantilləri (FR2_gar_crosscheck)', U.dt('ds-gar', gar.map(function (r) { var d = B.filter(function (q) { return q.gosterici === 'g' && q.il === r.il; })[0] || {}, k = { 0.1: 'p10', 0.25: 'p25', 0.5: 'p50', 0.75: 'p75', 0.9: 'p90' }[r.kvantil]; return Object.assign({ mc: d[k] }, r); }),
        [{ k: 'il', l: 'İl', n: 1, d: 0 }, { k: 'kvantil', l: 'Kvantil', n: 1, d: 2 }, { k: 'deyer', l: 'GaR reqressiyası', n: 1, d: 2 }, { k: 'mc', l: 'Birgə Monte Karlo (baza mərkəzli)', n: 1, d: 2 }, { k: 'n', l: 'n', n: 1, d: 0 }, { k: 'tesdiqlenib_NFR1', l: 'NFR1 ilə təsdiqlənib' }], { title: 'GaR yoxlaması', file: 'FR2_gar_crosscheck', note: 'GaR reqressiyası geriyə sınaqdan keçməyib (NFR1) — yalnız müqayisə üçündür.' })) +
      U.sec('Yelpik qatları', 'zolağın genişliyi haradan gəlir: amillər və modelin qalıq qeyri-müəyyənliyi', '<div id="ds-ly"></div>');
    blocks.forEach(function (b) { b.draw(); });
    contrib(U.$('#ds-co', v)); layering(U.$('#ds-ly', v));
  };
})();
