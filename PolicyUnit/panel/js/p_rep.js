/* p_rep.js — Hesabat qurucusu, part 1: report configuration (sections, scenarios, horizons, charts, notes), the two
   templates («Rəhbərlik üçün qısa hesabat», «Analitik hesabat — siyasət təsiri») and the section builders → a block list
   shared by the preview, print / PDF, Excel, Word and CSV exports (p_rep2.js; structure copied from the Risk paneli).
   Blocks: {t:'title'|'h1'|'h2'|'p'|'small'} · {t:'table', name, rows} · {t:'chart', draw(el)}. NFR3: graphs + tables + short text. */
(function () {
  'use strict';
  var U = window.U;
  U.SECS = [['summary', 'Qısa xülasə'], ['headline', 'Əsas göstəricilər (qısa / orta / uzun)'], ['macro', 'Makro yollar və metodlar'], ['micro', 'Sektor və bazar (MikroUnit)'], ['sector', 'Sektor təsirləri (IO)'], ['social', 'Sosial təsirlər (mikrosimulyasiya)'],
    ['risk', 'Yan təsirlər və risklər'], ['mitig', 'Azaldıcı tədbirlər'], ['kpi', 'KPI reytinqi'], ['methods', 'Metodların müqayisəsi'], ['valid', 'Tarixi validasiya'], ['notes', 'Qeydlər']];
  U.TPL = {
    rehberlik: { title: 'Rəhbərlik üçün qısa hesabat — siyasət təsiri', sections: ['summary', 'headline', 'social', 'risk', 'kpi', 'notes'], hz: ['qısa', 'orta', 'uzun'], n: 1 },
    analitik: { title: 'Analitik hesabat — iqtisadi siyasətin təsiri', sections: U.SECS.map(function (s) { return s[0]; }), hz: ['qısa', 'orta', 'uzun'], n: 3 }
  };
  var R = U.REP = { title: U.TPL.rehberlik.title, author: '', tpl: 'rehberlik', sections: U.TPL.rehberlik.sections.slice(), scen: [], hz: ['qısa', 'orta', 'uzun'], notes: '', charts: true };
  try { var st = JSON.parse(U.ls('policyPanel.report') || 'null'); if (st && st.sections) Object.keys(st).forEach(function (k) { R[k] = st[k]; }); } catch (e) { /* ignore */ }
  U.repSave = function () { U.ls('policyPanel.report', JSON.stringify(R)); };
  U.repApply = function (k) { var t = U.TPL[k]; R.tpl = k; R.title = t.title; R.sections = t.sections.slice(); R.hz = t.hz.slice(); var rk = U.T('P5_ranking').map(function (r) { return r.scenario; }); R.scen = U.uniq([U.cur()].concat(rk)).slice(0, t.n); U.repSave(); };
  if (!R.scen.length) R.scen = [U.cur()];
  function tb(name, head, rows) { return { t: 'table', name: name, rows: [head].concat(rows) }; }
  function n(v, d) { return U.isNum(v) ? +v.toFixed(d == null ? 3 : d) : (v == null ? '' : v); }
  function has(b) { return !!window.POL[b]; }
  var B = {};
  B.summary = function (sc) {
    var s = U.scen(sc) || {}, se = (U.META.se || {})[sc], rk = U.T('P5_ranking').filter(function (r) { return r.scenario === sc; })[0];
    return [{ t: 'p', text: (s.desc ? s.desc + ' ' : '') + U.story(sc) },
      { t: 'p', text: (rk ? 'KPI üzrə çoxkriteriyalı reytinqdə ' + rk.rank + '-ci yer (bal ' + U.nf(rk.score, 3) + '). ' : '') + (se ? 'Avtomatik aşkarlanan yan təsirlər: ' + se.n + ', o cümlədən yüksək və ya kritik — ' + se.n3 + '.' : '') + ' Rəqəmlər ssenari − baza fərqidir (eyni vintajlı baza proqnozu).' }];
  };
  B.headline = function (sc) {
    var rows = U.uniq(U.hl(sc).map(function (r) { return r.indicator; })).map(function (k) { var a = U.hl(sc, k)[0]; return [a.label_az, a.effect_unit].concat(R.hz.map(function (h) { var r = U.hl1(sc, k, h); return r ? n(r.effect) : ''; })).concat([U.ENGS[a.source_engine] || a.source_engine, a.tier]); });
    var out = [tb('Əsas göstəricilər — ' + U.sname(sc), ['Göstərici', 'Vahid'].concat(R.hz).concat(['Mənbə', 'Sübut']), rows)];
    if (R.charts) out.push({ t: 'chart', draw: function (el) { var K = ['gdp_real', 'cpi', 'unemp_rate', 'employment_hired', 'budget_balance_pct', 'debt_pct'].filter(function (k) { return U.hl(sc, k).length; }); U.barH(el, K.map(function (k) { var r = U.hl(sc, k)[0]; return r.label_az + ' (' + U.unitShort(r.effect_unit) + ')'; }), null, 'bazadan fərq', { h: 300, sets: R.hz.map(function (h, i) { return { name: h + ' müddət', c: ['#0E6F7C', '#1F6FB2', '#8A5300'][i], v: K.map(function (k) { var r = U.hl1(sc, k, h); return r ? r.effect : null; }) }; }) }); } });
    return out;
  };
  B.macro = function (sc) {
    if (!has('eff')) return [];
    var L = U.effRows(sc, function (r) { return r.indicator === 'gdp_real'; }), by = U.by(L, 'engine');
    var out = [{ t: 'small', text: 'Real ÜDM: bazadan % fərq illər üzrə, metodlara görə. 2031–2035 — uzun müddət struktur ekstrapolyasiyası (proqnoz deyil).' }];
    out.push(tb('Real ÜDM yolu — ' + U.sname(sc), ['Metod', 'İl', 'Baza', 'Ssenari', 'Fərq, %'], L.slice().sort(function (a, b) { return a.engine < b.engine ? -1 : a.engine > b.engine ? 1 : a.year - b.year; }).map(function (r) { return [U.ENGS[r.engine] || r.engine, r.year, n(r.baseline, 1), n(r.value, 1), n(r.delta_pct)]; })));
    if (R.charts) out.push({ t: 'chart', draw: function (el) { U.lines(el, Object.keys(by).sort().map(function (e) { var x = by[e].slice().sort(function (a, b) { return a.year - b.year; }); return { name: U.ENG[e] || e, x: x.map(function (r) { return r.year; }), y: x.map(function (r) { return r.delta_pct; }), c: U.ENGC[e], mode: 'lines+markers', dash: e === 'caem' ? 'dash' : e === 'longrun' ? 'dot' : 'solid' }; }), '% baza ilə fərq', { years: true, zero: true, fc: 2031, h: 300 }); } });
    return out;
  };
  B.micro = function (sc) {
    if (!has('eff')) return [];
    var M = U.hzMean(U.effRows(sc, function (r) { return r.engine === 'micro' && /^sector_va:|^hhi:/.test(r.indicator); }), 'orta');
    return M.length ? [tb('Sektor əlavə dəyəri və bazar konsentrasiyası (orta müddət, % fərq) — ' + U.sname(sc), ['Göstərici', '% fərq', 'Sübut'], M.sort(function (a, b) { return b.v - a.v; }).map(function (x) { return [x.label_az, n(x.v), x.tier]; }))] : [];
  };
  B.sector = function (sc) {
    if (!has('io')) return [];
    var A = U.T('P2_io_affected_sectors').filter(function (r) { return r.scenario === sc && r.kind === 'əlavə dəyər'; }).sort(function (a, b) { return a.rank - b.rank; }).slice(0, 12);
    if (!A.length) return [{ t: 'small', text: 'Bu ssenarinin alətləri girdi-çıxdı modelinə ötürülmür.' }];
    var out = [tb('Ən çox təsirlənən sektorlar (IO, əlavə dəyər, ' + A[0].year + ') — ' + U.sname(sc), ['Rütbə', 'Sektor', 'Dəyişmə, %', 'Dəyişmə, mln AZN'], A.map(function (r) { return [r.rank, r.name_az, n(r.delta_pct), n(r.delta, 1)]; }))];
    if (R.charts) out.push({ t: 'chart', draw: function (el) { U.barH(el, A.map(function (r) { return r.name_az; }), A.map(function (r) { return r.delta_pct; }), '% dəyişmə', { color: '#1F6FB2', h: 320 }); } });
    return out;
  };
  B.social = function (sc) {
    var H = U.T('P3_microsim_headline').filter(function (r) { return r.scenario === sc; });
    if (!H.length) return [{ t: 'small', text: 'Bu ssenari üçün mikrosimulyasiya nəticəsi yoxdur.' }];
    var out = [{ t: 'small', text: 'SİNTETİK — real ev təsərrüfatı məlumatı deyil. DSK 2024 aqreqatlarına kalibrlənmiş sintetik nümunə; statik ilk raund.' },
      tb('Sosial göstəricilər (bazadan fərq) — ' + U.sname(sc), ['İl', 'Gini, bənd', 'Yoxsulluq, f.b.', 'Yoxsulluq dərinliyi, f.b.', 'Orta gəlir, AZN', 'Muzdlu işçilər, min', 'Fiskal xərc, mln AZN'], H.map(function (r) { return [r.year, n(r.gini), n(r.poverty_rate), n(r.poverty_gap), n(r.income_mean_pc, 2), n(r.employment_hired, 1), n(r.fiscal_cost, 1)]; }))];
    if (R.charts && has('soc')) { var y = H[Math.min(1, H.length - 1)].year; out.push({ t: 'chart', draw: function (el) { var D = U.T('P3_microsim_deciles').filter(function (r) { return r.scenario === sc && r.year === y; }).sort(function (a, b) { return +a.decile.slice(1) - +b.decile.slice(1); }); U.bars(el, D.map(function (r) { return r.decile; }), [{ name: 'gəlirin dəyişməsi desillər üzrə, % (' + y + ')', y: D.map(function (r) { return r.delta_pct_income_decile_pc; }), c: '#0E6F7C' }], '%', { cat: true, h: 280 }); } }); }
    return out;
  };
  B.risk = function (sc) {
    if (!has('risk')) return [];
    var S = U.T('P4_side_effects').filter(function (r) { return r.scenario === sc && r.variant === 'base'; }).sort(function (a, b) { return b.severity - a.severity; });
    return S.length ? [tb('Yan təsirlər — ' + U.sname(sc), ['Ciddilik', 'Yan təsir', 'Ailə', 'Müddət', 'İzah', 'Risklər'], S.map(function (r) { return [r.severity_az, r.name_az, r.family, r.horizon, r.explanation_az, r.risk_ids]; }))] : [{ t: 'small', text: 'Yan təsir qaydası tetiklənməyib.' }];
  };
  B.mitig = function (sc) {
    if (!has('risk')) return [];
    var M = U.T('P4_mitigation').filter(function (r) { return r.scenario === sc && r.proposal_az; }).slice(0, 10);
    return M.length ? [tb('Azaldıcı tədbir təklifləri — ' + U.sname(sc), ['Prioritet', 'Növ', 'Təklif', 'Məsul', 'İzləmə göstəricisi'], M.map(function (r) { return [r.priority, r.proposal_type, r.proposal_az, r.responsible_az, r.kpi_az]; }))] : [];
  };
  B.methods = function (sc) {
    if (!has('cmp')) return [];
    var N = U.T('N2_method_comparison').filter(function (r) { return r.scenario === sc && r.horizon === 'orta'; }).slice(0, 12);
    return N.length ? [tb('Metodların müqayisəsi (orta müddət) — ' + U.sname(sc), ['Göstərici', 'Vahid', 'MikroUnit', 'CAEM', 'OxLon', 'IO', 'Mikrosim.', 'İşarə uyğun', 'İzah'], N.map(function (r) { return [r.label_az, r.effect_unit, n(r.micro), n(r.caem), n(r.oxlon), n(r.io), n(r.microsim), r.sign_agree === true || r.sign_agree === 'True' ? 'bəli' : 'xeyr', r.explanation_az]; }))] : [];
  };
  U.REPB = B;
})();
