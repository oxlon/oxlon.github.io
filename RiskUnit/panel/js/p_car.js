/* p_car.js — VaR və CaR, part 2: X-at-Risk summary (K1), Capital-at-Risk distribution of fiscal capital (K2),
   stochastic debt sustainability fan (K3), SOFAZ adequacy under S1–S8 (K4) and the sovereign contingent-claims
   approach (K5, labelled as an approximation). */
(function () {
  'use strict';
  var U = window.U;
  var C = U.CAR = {};
  C.car = function (el) {
    var k1 = U.T('K1_at_risk_summary'), k2 = U.T('K2_car_distribution'), vs = U.uniq(k2.map(function (r) { return r.variant; }));
    el.innerHTML = '<div class="note-b">«X-risk altında»: hər göstərici üçün rəsmi baza ilə əlverişsiz 5 % kvantil arasındakı məsafə (risk altında olan məbləğ). Fiskal kapital = ARDNF + AMB ehtiyatları − dövlət borcu; CaR = gözlənilən dəyər − kvantil. Risk iştahı həddləri Nazirlik qərarıdır (DR10).</div>' +
      '<div class="tiles">' + k1.filter(function (r) { return r.il === 2027; }).map(function (r) { return U.tile(U.esc(r.gosterici) + ' · ' + U.esc(r.ad), U.nf(r.risk_altinda, Math.abs(r.risk_altinda) >= 100 ? 0 : 2) + '<small>' + U.esc(r.vahid) + '</small>', 'baza ' + U.nf(r.baza, 2) + (U.isNum(r.p05) ? ' · P5 ' + U.nf(r.p05, 2) : '') + ' · pis istiqamət: ' + U.esc(r.pis_istiqamet)); }).join('') + '</div>' +
      U.dt('ck-1', k1, null, { title: '«X-risk altında» xülasəsi (K1)', file: 'K1_at_risk_summary' }) +
      '<div class="cols2"><div class="card pad"><h3>Fiskal kapital, mln USD: orta, P5, P1 (K2)</h3><div id="ck-nw" class="ch"></div></div><div class="card pad"><h3>Riskə məruz kapital (CaR) və ES, mln USD</h3><div id="ck-cr" class="ch"></div></div></div>' +
      U.dt('ck-2', k2, null, { title: 'Fiskal kapitalın paylanması (K2): CaR / ES 95 və 99 %, risk iştahı həddlərinin aşılma ehtimalları', file: 'K2_car_distribution' });
    var sets = [];
    vs.forEach(function (v, i) { var r = k2.filter(function (q) { return q.variant === v; }).sort(function (a, b) { return a.il - b.il; }), x = r.map(function (q) { return q.il; });
      sets.push({ x: x, y: r.map(function (q) { return q.NW_orta_mln_usd; }), name: v + ': orta', c: U.PAL[i], mode: 'lines+markers' }, { x: x, y: r.map(function (q) { return q.NW_p05; }), name: v + ': P5', c: U.PAL[i], dash: 'dash' }, { x: x, y: r.map(function (q) { return q.NW_p01; }), name: v + ': P1', c: U.PAL[i], dash: 'dot' }); });
    U.lines(U.$('#ck-nw', el), sets, 'mln USD', { years: true });
    var r0 = k2.filter(function (q) { return q.variant === vs[0]; }).sort(function (a, b) { return a.il - b.il; });
    U.bars(U.$('#ck-cr', el), r0.map(function (q) { return q.il; }), [{ name: 'CaR 95 %', y: r0.map(function (q) { return q.CaR95_mln_usd; }), c: '#0E6F7C' }, { name: 'ES 95 %', y: r0.map(function (q) { return q.ES95_mln_usd; }), c: '#E07B00' }, { name: 'CaR 99 %', y: r0.map(function (q) { return q.CaR99_mln_usd; }), c: '#B3261E' }], 'mln USD (' + vs[0] + ')', { years: true });
  };
  C.dsa = function (el) {
    var k3 = U.T('K3_dsa_fan'), vs = U.uniq(k3.map(function (r) { return r.variant; })), v = C.dv || vs[0], rs = k3.filter(function (r) { return r.variant === v; }).sort(function (a, b) { return a.il - b.il; });
    el.innerHTML = '<div class="toolbar">' + U.sel('ck-dv', vs.map(function (x) { return [x, x]; }), v) + '</div><div class="cols2"><div class="card pad"><h3>Dövlət borcu / ÜDM, % — yelpik (K3)</h3><div id="ck-df" class="ch"></div></div>' +
      '<div class="card pad"><h3>Borc dinamikasının komponentləri, f.b.</h3><div id="ck-dc" class="ch"></div></div></div>' +
      U.dt('ck-3', k3, null, { title: 'Stoxastik borc davamlılığı (K3) — 3 variant, həddi aşma ehtimalları, ümumi maliyyələşmə ehtiyacı', file: 'K3_dsa_fan' });
    U.fan(U.$('#ck-df', el), rs.map(function (r) { return { il: r.il, p05: r.p05, p10: r.p10, p25: r.p25, p50: r.p50, p75: r.p75, p90: r.p90, p95: r.p95, baza: r.baza_FR1_MN }; }), { yt: '% ÜDM', hline: 30, hlab: 'DSA həddi 30 % ÜDM', baseLab: 'FR1 / MN bazası' });
    var x = rs.map(function (r) { return r.il; });
    U.bars(U.$('#ck-dc', el), x, [['tohfe_balans_pp', 'balans'], ['tohfe_faiz_soku_pp', 'faiz şoku'], ['tohfe_mezenne_pp', 'məzənnə'], ['tohfe_sert_ohdelik_pp', 'şərti öhdəlik'], ['tohfe_artim_pp', 'nominal artım']].map(function (k, i) { return { name: k[1], y: rs.map(function (r) { return r[k[0]]; }), c: U.PAL[i] }; }), 'f.b.', { years: true, mode: 'relative' });
    U.$('#ck-dv', el).onchange = function (e) { C.dv = e.target.value; C.dsa(el); };
  };
  C.ardnf = function (el) {
    var k4 = U.T('K4_sofaz_adequacy'), k5 = U.T('K5_cca'), psi = C.psi == null ? 1 : C.psi, rs = k4.filter(function (r) { return r.psi_kesir_ARDNF_den === psi; }), by = U.by(rs, 'ssenari');
    el.innerHTML = '<div class="toolbar">' + U.seg('ck-psi', [[1, 'ψ = 1: büdcə sapması ARDNF-dən örtülür'], [0, 'ψ = 0: yalnız plan transferti']], psi) + '</div>' +
      '<div class="cols2"><div class="card pad"><h3>ARDNF aktivləri S1–S8 stress ssenarilərində, mln USD (K4)</h3><div id="ck-a" class="ch"></div></div><div class="card pad"><h3>Transfert örtüyü, il</h3><div id="ck-o" class="ch"></div></div></div>' +
      U.dt('ck-4', k4, null, { title: 'ARDNF adekvatlığı (K4) — bütün ssenarilər və ψ variantları', file: 'K4_sofaz_adequacy' }) +
      '<div class="note-w"><b>TƏXMİNİ YANAŞMA.</b> Suveren şərti öhdəliklər yanaşması (CCA, Gray–Merton–Bodie) sadələşdirilmiş fərziyyələrlə qurulub: aktivlər log-normal, volatillik ARDNF portfelinin paylanmasından. Nəticələr reytinq və ya bazar qiymətləndirməsi deyil — yalnız müqayisə üçündür.</div>' +
      U.dt('ck-5', k5, null, { title: 'Şərti öhdəliklər yanaşması (K5): qəzaya qədər məsafə, risk-neytral ehtimal, təxmini spred', file: 'K5_cca' });
    var keys = Object.keys(by).sort();
    U.lines(U.$('#ck-a', el), keys.map(function (k, i) { var r = by[k].sort(function (a, b) { return a.il - b.il; }); return { x: r.map(function (q) { return q.il; }), y: r.map(function (q) { return q.ARDNF_mln_usd; }), name: k, mode: 'lines+markers', c: k === 'istinad' ? '#15202B' : U.PAL[i % 10], w: k === 'istinad' ? 3 : 2, dash: k === 'istinad' ? 'solid' : 'dot' }; }), 'mln USD', { years: true, h: 340 });
    U.lines(U.$('#ck-o', el), keys.map(function (k, i) { var r = by[k].sort(function (a, b) { return a.il - b.il; }); return { x: r.map(function (q) { return q.il; }), y: r.map(function (q) { return q.ortuk_ili; }), name: k, mode: 'lines+markers', c: k === 'istinad' ? '#15202B' : U.PAL[i % 10] }; }), 'il', { years: true, h: 340 });
    U.$('#ck-psi', el).onclick = function (e) { var b = e.target.closest('[data-v]'); if (b) { C.psi = +b.getAttribute('data-v'); C.ardnf(el); } };
  };
})();
