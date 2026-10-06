/* p_mon2.js — Monitor part 2: market panel (D4: CBAR FX, policy rate and corridor, BSE yields, Brent / Azeri Light,
   SOFAZ, DSK, global indices; series explorer; V2 market factors) and the full forecast-impact table (D6) by FR module. */
(function () {
  'use strict';
  var U = window.U, MON = U.MON;
  var DRV = { brent: 'Brent neft qiyməti', policy_rate: 'Uçot dərəcəsi', cpi: 'İnflyasiya (DSK)', dsk_gdp: 'ÜDM (DSK)', dsk_gdp_nonoil: 'Qeyri-neft ÜDM (DSK)', dsk_gdp_oil: 'Neft-qaz ÜDM (DSK)',
    budget_execution: 'Büdcə icrası (DSK)', gold: 'Qızıl qiyməti (ARDNF + AMB)', eur_usd: 'EUR/USD məzənnəsi (ARDNF + AMB)' };
  function S(k) { return (U.raw('D4_market_panel') || {})[k]; }
  function line(k, opt) { var s = S(k); opt = opt || {}; return s ? { x: s.x, y: opt.idx ? s.y.map(function (v) { return U.isNum(v) && s.y[0] ? v / s.y[0] * 100 : null; }) : s.y, name: opt.name || s.name, mode: s.x.length < 40 ? 'lines+markers' : 'lines', shape: opt.hv ? 'hv' : 'linear', dash: opt.dash, c: opt.c, y2: opt.y2 } : null; }
  function chart(el, keys, yt, opt) { var sets = keys.map(function (k) { return Array.isArray(k) ? line(k[0], k[1]) : line(k, opt); }).filter(Boolean); U.lines(el, sets, yt, { xtype: 'date', h: 300, hm: 'x unified', y2: (opt || {}).y2t }); }
  function explorer(el) {
    var all = U.raw('D4_market_panel') || {}, keys = Object.keys(all).sort(), grps = U.uniq(keys.map(function (k) { return all[k].grp; })).sort();
    var g = MON.eg || (grps.indexOf('Neft') >= 0 ? 'Neft' : grps[0]), ks = keys.filter(function (k) { return all[k].grp === g; }), k = MON.ek && all[MON.ek] && all[MON.ek].grp === g ? MON.ek : ks[0], s = all[k];
    el.innerHTML = '<div class="toolbar">' + U.sel('mx-g', grps.map(function (x) { return [x, x]; }), g) + U.sel('mx-k', ks.map(function (x) { return [x, all[x].name + (all[x].unit ? ' (' + all[x].unit + ')' : '')]; }), k) + '<span class="small muted">' + s.x.length + ' müşahidə · ' + s.x[0] + ' – ' + s.x[s.x.length - 1] + ' · axın ' + U.esc(s.feed) + '</span></div>' +
      '<div class="card pad"><div id="mx-c" class="ch"></div></div>' + U.dt('mx-t', s.x.map(function (d, i) { return { date: d, value: s.y[i] }; }).reverse(), [{ k: 'date', l: 'Tarix' }, { k: 'value', l: s.name + (s.unit ? ', ' + s.unit : ''), n: 1 }], { title: 'Dəyərlər', file: k, lim: 40 });
    U.lines(U.$('#mx-c', el), [line(k)], s.unit, { xtype: s.x.length < 3 ? 'category' : 'date', h: 320 });
    U.$('#mx-g', el).onchange = function (e) { MON.eg = e.target.value; MON.ek = null; explorer(el); };
    U.$('#mx-k', el).onchange = function (e) { MON.ek = e.target.value; explorer(el); };
  }
  function factors(el) {
    var V = U.raw('V2_market_factors') || {}, fq = MON.vf || 'aylıq orta', d = V[fq] || V[Object.keys(V)[0]], cols = Object.keys(d.s), c = MON.vc || 'brent';
    el.innerHTML = '<div class="toolbar">' + U.seg('v2-f', Object.keys(V).map(function (x) { return [x, x]; }), fq) + U.sel('v2-c', cols.map(function (x) { return [x, U.colLabel(x)]; }), c) + '<span class="small muted">VaR modellərinin bazar risk amilləri (V2)</span></div><div class="card pad"><div id="v2-ch" class="ch"></div></div>';
    U.lines(U.$('#v2-ch', el), [{ x: d.x, y: d.s[c], name: U.colLabel(c), mode: 'lines' }], U.colLabel(c), { xtype: 'date', h: 300 });
    U.$('#v2-f', el).onclick = function (e) { var b = e.target.closest('[data-v]'); if (b) { MON.vf = b.getAttribute('data-v'); factors(el); } };
    U.$('#v2-c', el).onchange = function (e) { MON.vc = e.target.value; factors(el); };
  }
  MON.market = function (el) {
    U.need(['d4', 'v2'], el, function () {
      var sof = Object.keys(U.raw('D4_market_panel')).filter(function (k) { return /^sofaz_/.test(k); }).map(function (k) { var s = S(k); return { name: s.name, unit: s.unit, date: s.x[s.x.length - 1], value: s.y[s.y.length - 1] }; });
      el.innerHTML = '<div class="cols2"><div class="card pad"><h3>AMB rəsmi məzənnələri (ilk müşahidə = 100)</h3><div id="mk-fx" class="ch"></div></div><div class="card pad"><h3>Uçot dərəcəsi və faiz dəhlizi, %</h3><div id="mk-r" class="ch"></div></div>' +
        '<div class="card pad"><h3>Brent və Azeri Light, USD/barel</h3><div id="mk-b" class="ch"></div></div><div class="card pad"><h3>BFB: AMB notları və MN istiqrazlarının gəlirliliyi, %</h3><div id="mk-y" class="ch"></div></div>' +
        '<div class="card pad"><h3>Qlobal risk: VIX və ABŞ 10 illik gəlirlilik</h3><div id="mk-g" class="ch"></div></div><div class="card pad"><h3>Geosiyasi risk (GPR) və siyasət qeyri-müəyyənliyi (EPU)</h3><div id="mk-p" class="ch"></div></div></div>' +
        U.dt('mk-sf', sof, [{ k: 'name', l: 'ARDNF göstəricisi' }, { k: 'value', l: 'Dəyər', n: 1 }, { k: 'unit', l: 'Vahid' }, { k: 'date', l: 'Tarix' }], { title: 'ARDNF (oilfund.az) — son hesabat', file: 'ARDNF' }) +
        U.sec('Sıra seçici', 'D4 bazar və statistika panelinin bütün sıraları (115)', '<div id="mk-ex"></div>') + U.sec('Bazar risk amilləri (V2)', '', '<div id="mk-v2"></div>');
      chart(U.$('#mk-fx', el), ['cbar_usd', 'cbar_eur', 'cbar_rub', 'cbar_try', 'cbar_cny'], 'indeks', { idx: true });
      chart(U.$('#mk-r', el), [['cbar_policy_rate', { hv: true, c: '#0E6F7C' }], ['cbar_corridor_ceiling', { hv: true, dash: 'dot', c: '#B3261E' }], ['cbar_corridor_floor', { hv: true, dash: 'dot', c: '#1E7B4F' }]], '%');
      chart(U.$('#mk-b', el), [['brent_usd_daily', { c: '#0E6F7C' }], ['azeri_light_proxy', { c: '#E07B00', dash: 'dot' }]], 'USD/barel');
      chart(U.$('#mk-y', el), ['bfb_cbar_note_avg_yield', 'bfb_cbar_note_cut_yield', 'bfb_mof_bond_avg_yield', 'bfb_mof_bond_cut_yield'], '%');
      chart(U.$('#mk-g', el), [['vix', { c: '#B3261E' }], ['ust10y', { c: '#1F6FB2', y2: true }]], 'VIX', { y2t: '%' });
      chart(U.$('#mk-p', el), ['gpr_global', ['epu_global', { y2: true }]], 'GPR', { y2t: 'EPU' });
      explorer(U.$('#mk-ex', el)); factors(U.$('#mk-v2', el));
    });
  };
  var MODS = [['', 'Bütün komponentlər'], ['fr1:', 'FR1 makro-sektor'], ['fr3:', 'FR3 əmək haqqı'], ['fr4:', 'FR4 məşğulluq'], ['fr5:', 'FR5 xidmətlər'], ['fr10:', 'FR10 sənaye'], ['fr12:', 'FR12 rəqabət'], ['mx:', 'OxLon makro'], ['sofaz:', 'ARDNF']];
  MON.impact = function (el) {
    U.need(['d6'], el, function () {
      var d6 = U.T('D6_forecast_impact'), F = MON.F = MON.F || { dr: 'brent', m: '', y: 2027 };
      var drivers = U.uniq(d6.map(function (r) { return r.driver; })), years = U.uniq(d6.map(function (r) { return r.year; })).sort();
      var rows = d6.filter(function (r) { return (!F.dr || r.driver === F.dr) && (!F.m || String(r.target_id).indexOf(F.m) === 0) && (!F.y || r.year === +F.y); });
      el.innerHTML = '<div class="note-b">Hər sətir: bugünkü məlumatın (amil) rəsmi bazadan sapması → bir proqnoz komponentinə təsir. MikroUnit zənciri bütün FR1–FR12 komponentlərini (≈ 1 300) yenidən hesablayır; OxLon elastiklikləri və müşahidə hesabı başlıq göstəricilərinə tətbiq olunur. Şərti hesablamadır — rəsmi proqnoz dəyişdirilmir.</div>' +
        '<div class="toolbar">' + U.sel('d6-dr', [['', 'Bütün amillər']].concat(drivers.map(function (d) { return [d, DRV[d] ? DRV[d] + ' (' + d + ')' : d]; })), F.dr) + U.sel('d6-m', MODS, F.m) + U.sel('d6-y', [['', 'Bütün illər']].concat(years.map(function (y) { return [y, y]; })), F.y) +
        '<span class="small muted">' + U.nf(rows.length, 0) + ' sətir (cəmi ' + U.nf(d6.length, 0) + ')</span></div>' +
        '<div class="card pad"><h3>Ən böyük nisbi təsirlər (seçim üzrə, %)</h3><div id="d6-c" class="ch"></div></div>' +
        U.dt('d6-t', rows, U.H.d6cols.concat([{ k: 'target_id', l: 'Kod' }, { k: 'source', l: 'Mənbə' }]), { title: 'Proqnoz təsiri (D6_forecast_impact)', file: 'D6_forecast_impact', sort: null });
      var top = rows.filter(function (r) { return U.isNum(r.delta_pct); }).sort(function (a, b) { return Math.abs(b.delta_pct) - Math.abs(a.delta_pct); }).slice(0, 20);
      U.barH(U.$('#d6-c', el), top.map(function (r) { return r.label_az + ' · ' + r.year; }), top.map(function (r) { return r.delta_pct; }), 'bazadan fərq, %', { color: top.map(function (r) { return r.delta_pct >= 0 ? '#1E7B4F' : '#B3261E'; }) });
      ['dr', 'm', 'y'].forEach(function (k) { U.$('#d6-' + k, el).onchange = function (e) { F[k] = e.target.value; MON.impact(el); }; });
    });
  };
})();
