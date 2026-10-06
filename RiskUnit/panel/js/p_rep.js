/* p_rep.js — Hesabat qurucusu, part 1: report configuration (sections, risks, years, views, notes), the two templates
   («Rəhbərlik üçün gündəlik xülasə», «Analitik hesabat») and the section builders → a block list shared by the preview,
   print/PDF, Excel, Word and CSV exports (p_rep2.js). Blocks: {t:'h1'|'h2'|'p'|'small'} · {t:'table', name, rows} ·
   {t:'chart', draw(el)}. */
(function () {
  'use strict';
  var U = window.U;
  U.SECS = [['today', 'Bu günün xülasəsi'], ['top', 'Ən yüksək risklər'], ['alerts', 'Xəbərdarlıqlar'], ['changes', 'Nə dəyişdi'], ['impact', 'Məlumatın proqnozlara təsiri (D6)'], ['dist', 'Paylanmalar'],
    ['register', 'Risk reyestri (tam)'], ['drill', 'Seçilmiş risklərin təhlili'], ['var', 'VaR / ES və X-risk altında'], ['car', 'CaR və borc davamlılığı'], ['stress', 'Stress testləri S1–S8'], ['meas', 'Tədbirlər portfeli'],
    ['plan', 'İcra planı və gecikmələr'], ['caem', 'CAEM: risk balansı və tapıntılar'], ['nfr', 'Geriyə sınaq (NFR1)'], ['notes', 'Qeydlər']];
  U.TPL = {
    rehberlik: { title: 'Rəhbərlik üçün gündəlik xülasə', sections: ['today', 'top', 'alerts', 'changes', 'impact', 'dist', 'stress', 'meas', 'notes'], years: [2026, 2027], views: ['baseline'], risks: [] },
    analitik: { title: 'Analitik hesabat — iqtisadi risklər', sections: U.SECS.map(function (s) { return s[0]; }), years: U.YEARS.slice(), views: ['baseline', 'live'], risks: ['R01', 'R12', 'R13', 'R19'] }
  };
  var R = U.REP = { title: U.TPL.rehberlik.title, author: '', tpl: 'rehberlik', sections: U.TPL.rehberlik.sections.slice(), years: [2026, 2027], views: ['baseline'], risks: [], notes: '', charts: true };
  try { var st = JSON.parse(U.ls('riskPanel.report') || 'null'); if (st && st.sections) Object.keys(st).forEach(function (k) { R[k] = st[k]; }); } catch (e) { /* ignore */ }
  U.repSave = function () { U.ls('riskPanel.report', JSON.stringify(R)); };
  U.repApply = function (k) { var t = U.TPL[k]; R.tpl = k; R.title = t.title; R.sections = t.sections.slice(); R.years = t.years.slice(); R.views = t.views.slice(); R.risks = t.risks.slice(); U.repSave(); };
  function tb(name, head, rows) { return { t: 'table', name: name, rows: [head].concat(rows) }; }
  function n(v, d) { return U.isNum(v) ? +v.toFixed(d == null ? 3 : d) : (v == null ? '' : v); }
  var VN = { g: 'Qeyri-neft ÜDM-in real artımı, %', cpi: 'İnflyasiya, %', fis: 'Büdcə balansı, % ÜDM', brent: 'Brent, USD/barel' };
  var B = {};
  B.today = function () {
    var sc = U.T('FR2_risk_scores'), hi = sc.filter(function (r) { return r.prioritet === 'yüksək'; }), al = U.T('FR2_alerts'), bi = U.boriIndex('məlumat əsaslı (RU)'), y = +String(U.META.stamp.as_of).slice(0, 4), b = bi.filter(function (r) { return r.year === y; })[0] || {};
    var d = U.T('FR2_distribution').filter(function (r) { return r.gosterici === 'g' && r.il === y + 1; })[0] || {}, br = U.T('D5_daily_monitor').filter(function (r) { return r.indicator === 'brent_spot'; })[0] || {};
    return [{ t: 'p', text: 'Vəziyyət tarixi ' + U.META.stamp.as_of + '. Yüksək prioritetli risklər: ' + hi.length + ' (' + hi.map(function (r) { return r.risk_id + ' ' + r.ad; }).join('; ') + '). Xəbərdarlıqlar: ' + al.length + ', o cümlədən ' + al.filter(function (a) { return a.ciddilik === 'yüksək'; }).length + ' yüksək ciddilikli.' },
      { t: 'p', text: 'Risk balansı indeksi (' + y + ', məlumat əsaslı): ' + U.nf(b.weighted, 1) + ' — ' + (b.read_off_az || '') + '. Qeyri-neft artımı ' + (y + 1) + ': median ' + U.nf(d.p50, 2) + ' %, 5 % kvantil (GaR) ' + U.nf(d.p05, 2) + ' %. Brent spot ' + U.nf(br.latest, 2) + ' USD (' + (br.date || '') + '), baza fərziyyəsi ' + U.nf(br.baseline_assumption, 1) + ' USD.' }];
  };
  B.top = function () { var pv = U.prevScores(); return [tb('Ən yüksək risklər', ['Risk', 'Ad', 'Ailə', 'Sahib', 'Ehtimal, %', 'P', 'T', 'Skor', 'Prioritet', 'Əvvəlki skor'], U.T('FR2_risk_scores').slice().sort(function (a, b) { return b.skor - a.skor; }).slice(0, 8).map(function (r) { var p = pv.by[r.risk_id]; return [r.risk_id, r.ad, r.aile, r.sahib, U.isNum(r.ehtimal) ? n(r.ehtimal * 100, 1) : '', r.P_bal, r.I_bal, r.skor, r.prioritet, p ? p.skor : '']; }))]; };
  B.alerts = function () { return [tb('Xəbərdarlıqlar', ['Ciddilik', 'Növ', 'Risk', 'Mesaj'], U.T('FR2_alerts').filter(function (a) { return a.ciddilik !== 'aşağı'; }).map(function (a) { return [a.ciddilik, a.tip, a.risk_id || '', a.mesaj]; }))]; };
  B.changes = function () { var pv = U.prevScores(); return [{ t: 'small', text: 'Müqayisə: ' + (pv.date || '—') + ' → ' + U.META.stamp.as_of },
    tb('Skor dəyişmələri', ['Risk', 'Ad', 'Əvvəl', 'İndi'], U.T('FR2_risk_scores').filter(function (r) { var p = pv.by[r.risk_id]; return !p || p.skor !== r.skor; }).map(function (r) { var p = pv.by[r.risk_id]; return [r.risk_id, r.ad, p ? p.skor : 'yeni', r.skor]; })),
    tb('Yeni məlumat vintajları', ['Axın', 'Əvvəlki son tarix', 'Son tarix', 'Yeni müşahidə'], U.T('D7_changes').map(function (r) { return [r.item, r.previous_date, r.date, r.change]; }))]; };
  B.impact = function () { return [{ t: 'small', text: 'Bugünkü məlumatın rəsmi bazadan sapması → proqnoz təsiri (şərti hesablama, proqnoz deyil).' }, tb('Proqnoz təsiri', ['Amil', 'Göstərici', 'Vahid', 'İl', 'Baza', 'Bugünkü məlumatla', 'Fərq', 'Fərq, %', 'Kanal'],
    U.T('D6_headline').filter(function (r) { return R.years.indexOf(r.year) >= 0; }).map(function (r) { return [r.driver, r.label_az, r.unit, r.year, n(r.baseline, 2), n(r.implied, 2), n(r.delta, 3), n(r.delta_pct, 2), r.channel]; }))]; };
  B.dist = function () {
    var out = [];
    ['g', 'cpi', 'fis', 'brent'].forEach(function (g) {
      out.push({ t: 'h2', text: VN[g] });
      var rows = [];
      R.views.forEach(function (v) { U.T(v === 'live' ? 'FR2_distribution_live' : 'FR2_distribution').filter(function (r) { return r.gosterici === g && R.years.indexOf(r.il) >= 0; }).forEach(function (r) { rows.push([U.VIEWN[v], r.il, n(r.baza, 2), n(r.p05, 2), n(r.p10, 2), n(r.p25, 2), n(r.p50, 2), n(r.p75, 2), n(r.p90, 2), n(r.p95, 2), n(r.ES10, 2)]); }); });
      out.push(tb('Paylanma ' + g, ['Baxış', 'İl', 'Baza', 'P5', 'P10', 'P25', 'Median', 'P75', 'P90', 'P95', 'ES10'], rows));
      if (R.charts) out.push({ t: 'chart', draw: function (el) { var b = U.T('FR2_distribution').filter(function (r) { return r.gosterici === g; }), l = U.T('FR2_distribution_live').filter(function (r) { return r.gosterici === g; }); U.fan(el, R.views[0] === 'live' ? l : b, { live: R.views.length > 1 ? (R.views[0] === 'live' ? b : l) : null, yt: VN[g], h: 300 }); } });
    });
    return out;
  };
  B.register = function () { return [tb('Risk reyestri', ['Risk', 'Ailə', 'Ad', 'Növ', 'Sahib', 'Ehtimal, %', 'P', 'T', 'Skor', 'Prioritet', 'Qalıq skor', 'Tədbir sayı'], U.regRows().sort(function (a, b) { return b.skor - a.skor; }).map(function (r) { return [r.risk_id, r.aile, r.ad, r.nov, r.sahib, U.isNum(r.ehtimal) ? n(r.ehtimal * 100, 1) : '', r.P_bal, r.I_bal, r.skor, r.prioritet, r.qaliq == null ? '' : r.qaliq, r.tedbir == null ? '' : r.tedbir]; }))]; };
  B.drill = function () {
    var out = [];
    R.risks.forEach(function (rid) {
      var r = U.T('FR2_risk_scores').filter(function (x) { return x.risk_id === rid; })[0], g = U.T('input_risk_reyestri').filter(function (x) { return x.risk_id === rid; })[0] || {}; if (!r) return;
      out.push({ t: 'h2', text: rid + ' — ' + r.ad }, { t: 'p', text: (g.tesvir || '') + ' Hadisə: ' + (g.hadise_terifi || '') + '. Ehtimal üsulu: ' + (g.ehtimal_metodu || '') + '. Ötürmə: ' + (g.oturme_kanali || '') + '.' },
        { t: 'p', text: 'Ehtimal ' + U.pct(r.ehtimal, 1) + ' (P' + r.P_bal + '), təsir T' + r.I_bal + ' (' + r.I_olcu + '), skor ' + r.skor + ' — ' + r.prioritet + ' prioritet. Sahib: ' + r.sahib + '.' },
        tb(rid + ' tədbirlər', ['Tədbir', 'Ad', 'Status', 'Məsul', 'Xərc, mln AZN', 'Risk azalması'], U.T('M1_measures_v2').filter(function (m) { return U.hasId(m.risk_idler, rid); }).map(function (m) { return [m.tedbir_id, m.tedbir, m.status_az, m.mesul, n(m.xerc_mln_azn, 1), n(m.effekt_hedef_funksiya, 3)]; })));
    });
    return out.length ? out : [{ t: 'small', text: 'Risk seçilməyib.' }];
  };
  B['var'] = function () { return [tb('VaR / ES: ARDNF, 1 il', ['Metod', 'Etibarlılıq', 'VaR, mln USD', 'ES, mln USD'], U.T('V3_var_es').filter(function (r) { return r.portfel === 'sofaz' && r.horizont === '1il'; }).map(function (r) { return [r.metod_ad, r.etibarlilik, n(r.VaR_mln_usd, 0), n(r.ES_mln_usd, 0)]; })),
    tb('X-risk altında', ['Göstərici', 'Ad', 'Vahid', 'İl', 'Baza', 'P5', 'Risk altında'], U.T('K1_at_risk_summary').map(function (r) { return [r.gosterici, r.ad, r.vahid, r.il, n(r.baza, 2), n(r.p05, 2), n(r.risk_altinda, 2)]; }))]; };
  B.car = function () { return [tb('Fiskal kapital (CaR)', ['Variant', 'İl', 'Orta, mln USD', 'P5', 'CaR 95 %', 'ES 95 %', 'P(NW/ÜDM < 75 %)'], U.T('K2_car_distribution').map(function (r) { return [r.variant, r.il, n(r.NW_orta_mln_usd, 0), n(r.NW_p05, 0), n(r.CaR95_mln_usd, 0), n(r.ES95_mln_usd, 0), n(r.P_NW_ÜDM_lt_75, 4)]; })),
    tb('Borc davamlılığı', ['Variant', 'İl', 'Baza', 'Median', 'P5', 'P95', 'P(borc > 30 %)'], U.T('K3_dsa_fan').map(function (r) { return [r.variant, r.il, n(r.baza_FR1_MN, 2), n(r.p50, 2), n(r.p05, 2), n(r.p95, 2), n(r.P_borc_gt_30, 4)]; }))]; };
  B.stress = function () { var y = U.scoreYear(); return [tb('Stress ssenariləri ' + y, ['Ssenari', 'Ad', 'Şok vektoru', 'Göstərici', 'Sapma', 'Sapma (tədbirlə)'], U.T('FR3_stress_scenarios').filter(function (r) { return r.il === y; }).map(function (r) { return [r.ssenari, r.ad, r.sok_vektoru, r.gosterici, n(r.sapma, 3), n(r.sapma_tedbirle, 3)]; }))]; };
  B.meas = function () { var f = U.T('M4_frontier').filter(function (r) { return r.budce_mln_azn === 500; })[0] || {}; return [{ t: 'p', text: 'Optimal portfel (büdcə 500 mln AZN): ' + (f.secilmis_tedbirler || '') + '; xərc ' + U.nf(f.secilmis_xerc_mln_azn, 1) + ' mln AZN; risk azalması ' + U.nf(f.hedef_funksiya, 2) + ' %; risk iştahı ' + (f.istah_mumkun ? 'ödənilir' : 'ödənilmir') + '.' },
    tb('Plandakı tədbirlər', ['Tədbir', 'Ad', 'Strategiya', 'Məsul', 'Xərc, mln AZN', 'Status'], U.T('M1_measures_v2').filter(function (m) { return m.optimal_planda_500; }).map(function (m) { return [m.tedbir_id, m.tedbir, m.strategiya_v2, m.mesul, n(m.xerc_mln_azn, 1), m.status_az]; })),
    tb('Səmərəli sərhəd', ['Büdcə', 'Xərc', 'Risk azalması, %', 'Tədbir sayı', 'İştah ödənilir'], U.T('M4_frontier').map(function (r) { return [r.budce_mln_azn, n(r.secilmis_xerc_mln_azn, 1), n(r.hedef_funksiya, 2), r.tedbir_sayi, r.istah_mumkun ? 'bəli' : 'xeyr']; }))]; };
  B.plan = function () { return [tb('İcra planı', ['Tədbir', 'Mərhələ', 'Başlama', 'Bitmə', 'Status', 'Qalan gün', 'Xəbərdarlıq'], U.T('M6_implementation_plan').filter(function (r) { return r.plan === 'optimal plan'; }).map(function (r) { return [r.tedbir_id, r.merhele, r.baslama, r.bitme, r.status, r.qalan_gun, r.xeberdarliq || '']; }))]; };
  B.caem = function () { return [tb('Risk balansı indeksi', ['Versiya', 'İl', 'İndeks', 'Oxunuş'], U.boriIndex().map(function (r) { return [r.version, r.year, n(r.weighted, 1), r.read_off_az || '']; })),
    tb('CAEM tapıntıları (yüksək ciddilik)', ['№', 'Vərəq', 'Qüsur', 'Tövsiyə'], U.T('C6_caem_findings').filter(function (r) { return r.severity_az === 'yüksək'; }).map(function (r) { return [r.finding_id, r.sheet, r.issue_az, r.recommendation_az]; }))]; };
  B.nfr = function () { return [tb('Geriyə sınaq', ['Test', 'Model', 'Hədəf', 'n', 'Metrika', 'Dəyər', 'Hədd', 'Nəticə'], U.T('NFR1_backtest_results').map(function (r) { return [r.test_id, r.model, r.hedef, r.n, r.metrik, n(r.deyer, 3), r.hedd, r.netice]; }))]; };
  B.notes = function () { return R.notes ? R.notes.split(/\n+/).map(function (p) { return { t: 'p', text: p }; }) : []; };
  U.repModel = function () {
    var out = [{ t: 'title', text: R.title }, { t: 'small', text: 'İqtisadiyyat Nazirliyi · MİİS §15.5.3 risk bölməsi · vəziyyət ' + U.META.stamp.as_of + ' · baza ' + U.META.stamp.baseline_id + (R.author ? ' · ' + R.author : '') }];
    U.SECS.forEach(function (s) { if (R.sections.indexOf(s[0]) < 0) return; var b = B[s[0]](); if (!b.length) return; out.push({ t: 'h1', text: s[1] }); out = out.concat(b); });
    out.push({ t: 'small', text: 'Mənbə: RiskUnit/output (möhür ' + U.META.stamp.md5 + ', ' + U.META.stamp.date + '). Risk bölməsi öz mərkəzi proqnozunu vermir; bazalar makro və mikro bölmələrdəndir.' });
    return out;
  };
})();
