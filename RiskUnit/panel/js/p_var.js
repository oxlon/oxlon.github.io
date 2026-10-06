/* p_var.js — VaR və CaR, part 1: exposures of the sovereign balance sheet (V1) and open data requests (V1b), VaR / ES
   by portfolio, method, horizon and confidence level (V3), Euler / marginal contributions (V4), backtests with traffic
   lights (V5) and the rolling VaR history (V6). CaR, DSA, SOFAZ adequacy, CCA: p_car.js. */
(function () {
  'use strict';
  var U = window.U;
  U.VR = { pf: 'sofaz', h: '1il', c: 0.99 };
  var HZ = [['1g', '1 gün'], ['1a', '1 ay'], ['1il', '1 il']];
  function expo(el) {
    var v1 = U.T('V1_exposures'), cat = U.by(v1, 'kateqoriya'), cls = cat['ARDNF aktiv sinfi'] || [], ccy = cat['ARDNF valyuta'] || [];
    var tot = v1.filter(function (r) { return r.kod === 'sofaz_total'; })[0] || {}, fc = v1.filter(function (r) { return r.kod === 'fiscal_capital'; })[0] || {}, sr = v1.filter(function (r) { return r.kod === 'strategic_reserves'; })[0] || {}, db = v1.filter(function (r) { return r.kod === 'debt_public_total'; })[0] || {};
    el.innerHTML = '<div class="tiles">' + U.tile('ARDNF aktivləri', U.nf(tot.mln_usd, 0) + '<small>mln USD</small>', U.esc(tot.tarix || '') + ' · ' + U.esc(tot.menbe || '')) + U.tile('Strateji valyuta ehtiyatları', U.nf(sr.mln_usd, 0) + '<small>mln USD</small>', 'ARDNF + AMB') +
      U.tile('Dövlət borcu', U.nf(db.mln_usd, 0) + '<small>mln USD</small>', U.nf(db.deyer, 0) + ' mln AZN') + U.tile('Fiskal kapital', U.nf(fc.mln_usd, 0) + '<small>mln USD</small>', 'ARDNF + AMB − dövlət borcu', 'ok') + '</div>' +
      '<div class="cols2"><div class="card pad"><h3>ARDNF: aktiv sinifləri, %</h3><div id="vx-c" class="ch"></div></div><div class="card pad"><h3>ARDNF: valyuta strukturu, %</h3><div id="vx-v" class="ch"></div></div></div>' +
      U.dt('vx-t', v1, [{ k: 'kateqoriya', l: 'Kateqoriya' }, { k: 'ad_az', l: 'Məruz qalma' }, { k: 'deyer', l: 'Dəyər', n: 1 }, { k: 'vahid', l: 'Vahid' }, { k: 'mln_usd', l: 'mln USD', n: 1, d: 0 }, { k: 'mln_azn', l: 'mln AZN', n: 1, d: 0 }, { k: 'pay_faiz', l: 'Pay, %', n: 1, d: 1 },
        { k: 'tarix', l: 'Tarix' }, { k: 'menbe', l: 'Mənbə' }, { k: 'status', l: 'Status', f: U.sigchip }, { k: 'qeyd', l: 'Qeyd' }], { title: 'Suveren balans məruz qalmaları (V1) — ' + v1.length, file: 'V1_exposures' }) +
      U.dt('vx-r', U.T('V1b_data_requests'), null, { title: 'Açıq olmayan məlumatlar üzrə sorğular (V1b) — Nazirlik göndərməlidir', file: 'V1b_data_requests' });
    U.bars(U.$('#vx-c', el), cls.map(function (r) { return r.ad_az; }), [{ name: 'pay, %', y: cls.map(function (r) { return r.pay_faiz; }), c: '#0E6F7C' }], '%', { cat: true, h: 280 });
    U.bars(U.$('#vx-v', el), ccy.map(function (r) { return r.ad_az; }), [{ name: 'pay, %', y: ccy.map(function (r) { return r.pay_faiz; }), c: '#1F6FB2' }], '%', { cat: true, h: 280 });
  }
  function ctl(id) {
    var pfs = U.uniq(U.T('V3_var_es').map(function (r) { return r.portfel; })), names = {};
    U.T('V3_var_es').forEach(function (r) { names[r.portfel] = r.portfel_ad; });
    return '<div class="toolbar" id="' + id + '">' + U.seg('vr-pf', pfs.map(function (p) { return [p, names[p]]; }), U.VR.pf) + U.seg('vr-h', HZ, U.VR.h) + U.seg('vr-c', [[0.95, '95 %'], [0.99, '99 %']], U.VR.c) + '</div>';
  }
  function bindCtl(el, redraw) {
    el.onclick = function (e) { var b = e.target.closest('#vr-pf [data-v], #vr-h [data-v], #vr-c [data-v]'); if (!b) return; var k = b.parentNode.id.slice(3); U.VR[k] = k === 'c' ? +b.getAttribute('data-v') : b.getAttribute('data-v'); redraw(); };
  }
  function varPage(el) {
    var V = U.VR, v3 = U.T('V3_var_es'), sel = v3.filter(function (r) { return r.portfel === V.pf && r.horizont === V.h && r.etibarlilik === V.c; });
    var v4 = U.T('V4_var_contributions').filter(function (r) { return r.portfel === V.pf && r.horizont === V.h && r.etibarlilik === V.c; });
    el.innerHTML = ctl('vr-ctl') + '<div class="note-b">VaR — verilmiş üfüqdə verilmiş etibarlılıq səviyyəsi ilə aşılmayan itki; ES (gözlənilən itki) — VaR aşıldıqda orta itki. Beş metod müqayisə olunur; GARCH və oxşar volatillik dinamikası istifadə edilmir (yaşa görə çəki sabit λ ilə). «Kök-zaman» yalnız müqayisə üçündür.</div>' +
      '<div class="cols2"><div class="card pad"><h3>VaR və ES metodlar üzrə, mln USD</h3><div id="vr-b" class="ch"></div></div><div class="card pad"><h3>VaR töhfəsi (Eyler, t-kopula MK) — ' + (v4.length ? '' : 'bu portfel üçün yoxdur') + '</h3><div id="vr-k" class="ch"></div></div></div>' +
      U.dt('vr-t', sel, [{ k: 'metod_ad', l: 'Metod' }, { k: 'VaR_mln_usd', l: 'VaR, mln USD', n: 1, d: 0 }, { k: 'ES_mln_usd', l: 'ES, mln USD', n: 1, d: 0 }, { k: 'VaR_mln_azn', l: 'VaR, mln AZN', n: 1, d: 0 }, { k: 'ES_mln_azn', l: 'ES, mln AZN', n: 1, d: 0 },
        { k: 'VaR_pct', l: 'VaR, %', n: 1, d: 2 }, { k: 'ES_pct', l: 'ES, %', n: 1, d: 2 }, { k: 'portfel_deyeri_mln_usd', l: 'Portfel, mln USD', n: 1, d: 0 }, { k: 'n_musahide', l: 'n', n: 1, d: 0 }, { k: 'pencere', l: 'Pəncərə' }, { k: 'etibarli', l: 'Etibarlıdır', f: function (v) { return v === false ? '<span class="chip warn">xeyr</span>' : v === true ? 'bəli' : '—'; } }, { k: 'etibar_qeydi', l: 'Etibarlılıq qeydi' }, { k: 'qeyd', l: 'Qeyd' }], { title: 'Seçim üzrə VaR / ES', file: 'VaR_secim' }) +
      U.dt('vr-a', v3, null, { title: 'Bütün VaR / ES qiymətləri (V3) — portfel × metod × üfüq × etibarlılıq', file: 'V3_var_es' }) +
      U.dt('vr-4', U.T('V4_var_contributions'), null, { title: 'Komponent və marjinal VaR / ES (V4) — bütün sətirlər', file: 'V4_var_contributions' });
    U.bars(U.$('#vr-b', el), sel.map(function (r) { return r.metod_ad; }), [{ name: 'VaR', y: sel.map(function (r) { return r.VaR_mln_usd; }), c: '#0E6F7C' }, { name: 'ES', y: sel.map(function (r) { return r.ES_mln_usd; }), c: '#B3261E' }], 'mln USD', { cat: true, h: 320 });
    var am = v4.filter(function (r) { return r.qrup === 'amil'; }).sort(function (a, b) { return b.tohfe_VaR - a.tohfe_VaR; });
    if (am.length) U.barH(U.$('#vr-k', el), am.map(function (r) { return r.komponent_ad; }), am.map(function (r) { return r.tohfe_VaR; }), 'VaR töhfəsi, mln USD', { sets: [{ v: am.map(function (r) { return r.tohfe_VaR; }), name: 'VaR töhfəsi', c: '#0E6F7C' }, { v: am.map(function (r) { return r.tohfe_ES; }), name: 'ES töhfəsi', c: '#B3261E' }] });
    bindCtl(el, function () { varPage(el); });
  }
  function light(v) { var t = String(v || ''); return /yaşıl/.test(t) ? '<span class="chip acc">● yaşıl</span>' : /sarı/.test(t) ? '<span class="chip warn">● sarı</span>' : /qırmızı/.test(t) ? '<span class="chip bad">● qırmızı</span>' : U.sigchip(t); }
  function back(el) {
    var v5 = U.T('V5_var_backtest'), v6 = U.T('V6_var_history'), ok = v5.filter(function (r) { return /keçdi|yaşıl/.test(r.netice); }).length, no = v5.filter(function (r) { return /keçmədi|qırmızı/.test(r.netice); }).length, nt = v5.filter(function (r) { return /bilməz|bilmir/.test(r.netice); }).length;
    el.innerHTML = '<div class="tiles">' + U.tile('Testlər', U.nf(v5.length, 0), 'portfel × üfüq × metod × test') + U.tile('Keçdi', U.nf(ok, 0), '', 'ok') + U.tile('Keçmədi', U.nf(no, 0), 'mənfi nəticələr saxlanılır və izah olunur', no ? 'bad' : 'ok') + U.tile('Yoxlanıla bilməz', U.nf(nt, 0), 'n = 0 və ya qısa tarixçə — «keçdi» sayılmır', nt ? 'warn' : '') + '</div>' +
      '<div class="card pad"><h3>ARDNF: hipotetik gündəlik mənfəət/zərər və sürüşən VaR 99 % (V6), mln USD</h3><div id="vb-h" class="ch" style="min-height:360px"></div><p class="small muted">Qırmızı nöqtələr — itkinin tarixi simulyasiya VaR 99 %-ni aşdığı günlər (pozuntular).</p></div>' +
      U.dt('vb-t', v5, [{ k: 'portfel', l: 'Portfel' }, { k: 'horizont', l: 'Üfüq' }, { k: 'metod', l: 'Metod' }, { k: 'etibarlilik', l: 'Etibarlılıq', n: 1, p: 1 }, { k: 'test', l: 'Test' }, { k: 'n', l: 'n', n: 1, d: 0 }, { k: 'pozuntu', l: 'Pozuntu', n: 1, d: 0 }, { k: 'gozlenilen', l: 'Gözlənilən', n: 1, d: 1 },
        { k: 'statistika', l: 'Statistika', n: 1, d: 3 }, { k: 'p_deyer', l: 'p', n: 1, f: U.pf }, { k: 'netice', l: 'Nəticə', f: light }, { k: 'dovr', l: 'Dövr' }, { k: 'qeyd', l: 'Qeyd' }], { title: 'VaR / ES geriyə doğru sınaqları (V5) — svetofor', file: 'V5_var_backtest' }) +
      U.dt('vb-6', v6, null, { title: 'Sürüşən VaR / ES tarixçəsi (V6) — bütün sütunlar', file: 'V6_var_history', lim: 60 });
    var x = v6.map(function (r) { return r.tarix; }), br = v6.filter(function (r) { return r.pozuntu_VaR99_hs; });
    U.lines(U.$('#vb-h', el), [{ x: x, y: v6.map(function (r) { return -r.sofaz_pnl_hipotetik; }), name: 'itki (− mənfəət/zərər)', c: '#9AA6B2', w: 1 }, { x: x, y: v6.map(function (r) { return r.VaR99_hs; }), name: 'VaR 99 % tarixi', c: '#0E6F7C' },
      { x: x, y: v6.map(function (r) { return r.VaR99_evt; }), name: 'VaR 99 % EVT', c: '#6A3FB5', dash: 'dot' }, { x: x, y: v6.map(function (r) { return r.ES99_hs; }), name: 'ES 99 % tarixi', c: '#B3261E', dash: 'dash' },
      { x: br.map(function (r) { return r.tarix; }), y: br.map(function (r) { return -r.sofaz_pnl_hipotetik; }), name: 'pozuntu', mode: 'markers', marker: { size: 8, color: '#B3261E' } }], 'mln USD', { xtype: 'date', h: 360 });
  }
  U.pages['var'] = function (v, p) {
    var sub = p[1] || '';
    v.innerHTML = U.head('İqtisadiyyatın ümumi məruz qalması', 'Riskə məruz dəyər (VaR) və kapital (CaR)', 'Suveren balansın məruz qalmaları (ARDNF, AMB ehtiyatları, dövlət və zəmanətli borc, büdcənin neft asılılığı), bazar riskinin VaR / ES qiymətləri, onların geriyə doğru sınağı, «X-risk altında» xülasəsi, fiskal kapitala risk (CaR), borc davamlılığı, ARDNF adekvatlığı və şərti öhdəliklər yanaşması.') +
      U.subtabs('var', [['', 'Məruz qalmalar'], ['var', 'VaR / ES'], ['geri', 'Geriyə sınaq'], ['car', 'X-risk altında və CaR'], ['dsa', 'Borc davamlılığı'], ['ardnf', 'ARDNF adekvatlığı və CCA']], sub) + '<div id="vr-body"></div>';
    var b = U.$('#vr-body', v);
    if (sub === 'var') varPage(b); else if (sub === 'geri') back(b); else if (sub === 'car' || sub === 'dsa' || sub === 'ardnf') U.CAR[sub](b); else expo(b);
  };
})();
