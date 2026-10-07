/* p_soc.js — Sosial təsirlər (FR3, mikrosimulyasiya): employment total vs formal (+ FR4 sections), income deciles with
   winners / losers, Gini, poverty headcount / gap / severity for the configurable poverty lines, static fiscal cost,
   baseline paths. Every household-based result carries the SİNTETİK banner. */
(function () {
  'use strict';
  var U = window.U;
  var SUB = [['', 'Xülasə'], ['desil', 'Gəlir desilləri'], ['mesgulluq', 'Məşğulluq'], ['fiskal', 'Fiskal təsir'], ['baza', 'Baza 2024–2030']];
  var LINES = [['', 'DSK rəsmi yoxsulluq xətti'], [':need', 'ÜSY ehtiyac meyarı'], [':subsist', 'Yaşayış minimumu']];
  function ind(sc, yr) { return U.T('P3_microsim_indicators').filter(function (r) { return r.scenario === sc && r.year === yr; }); }
  function get(L, k) { return L.filter(function (r) { return r.indicator === k; })[0] || null; }
  function tile(r, unit, dec, good) {
    if (!r) return '';
    var tn = U.isNum(r.delta) && Math.abs(r.delta) > 1e-9 ? (r.delta * good > 0 ? 'up' : 'down') : '';
    return '<div class="itile ' + tn + '"><div class="l">' + U.esc(r.label_az) + '</div><div class="v">' + U.sg(r.delta, dec) + ' <small>' + unit + '</small></div><div class="s">baza ' + U.nf(r.baseline, 2) + ' → ' + U.nf(r.value, 2) + ' ' + U.esc(r.unit || '') + '</div></div>';
  }
  function summary(v, sc, yr) {
    var L = ind(sc, yr), ln = U.HQ.get('l') || '';
    var pv = ['poverty_rate', 'poverty_gap', 'poverty_severity'].map(function (k) { return get(L, k + ln); });
    v.insertAdjacentHTML('beforeend', '<div class="expl">Mikrosimulyasiya hər ev təsərrüfatı üçün vergi və müavinət qaydalarını (<code>config/tax_benefit.csv</code>) siyasətlə və siyasətsiz tətbiq edir və fərqi toplayır: kim qazanır, kim itirir, yoxsulluq və bərabərsizlik necə dəyişir. Statik ilk raund — davranış reaksiyası (işdən çıxma, qeyri-formallaşma) «Risklər» bölməsində yan təsir kimi qiymətləndirilir.</div>' +
      '<div class="toolbar"><b class="small">Yoxsulluq xətti</b> ' + U.seg('o-line', LINES, ln) + '</div>' +
      '<div class="itiles">' + tile(get(L, 'employment'), 'min nəfər', 1, 1) + tile(get(L, 'employment_hired'), 'min nəfər', 1, 1) + tile(get(L, 'employment_informal'), 'min nəfər', 1, -1) +
      tile(get(L, 'gini'), 'bənd', 3, -1) + tile(get(L, 'gini_cons'), 'bənd', 3, -1) + pv.map(function (r) { return tile(r, 'f.b.', 3, -1); }).join('') +
      tile(get(L, 'income_mean_pc'), 'AZN/ay', 2, 1) + tile(get(L, 'income_median_pc'), 'AZN/ay', 2, 1) + tile(get(L, 'fiscal_cost'), 'mln AZN', 1, -1) + '</div>' +
      '<div class="cols2"><div class="card pad"><h3>Gəlirin dəyişməsi desillər üzrə (' + yr + ')</h3><div id="o-dec" class="ch"></div><p class="small muted">D1 — ən yoxsul 10 %, D10 — ən varlı 10 % (baza gəlirinə görə).</p></div><div class="card pad"><h3>Yoxsulluq və Gini — illər üzrə</h3><div id="o-path" class="ch"></div></div></div>' +
      U.dt('o-all', L, [{ k: 'label_az', l: 'Göstərici' }, { k: 'unit', l: 'Vahid' }, { k: 'baseline', l: 'Baza', n: 1 }, { k: 'value', l: 'Ssenari', n: 1 }, { k: 'delta', l: 'Fərq', n: 1, d: 3 }, { k: 'delta_pct', l: 'Fərq, % / f.b.', n: 1, d: 3 }, { k: 'tier', l: 'Sübut', f: function (t) { return U.tier(t); } }], { title: 'Bütün mikrosimulyasiya göstəriciləri — ' + yr, file: 'mikrosim_' + sc + '_' + yr }) + U.rangeSec(sc, /^(employment|wage|gini|poverty|hh_disp|income)/) + U.msStatus(sc));
    decChart(U.$('#o-dec', v), sc, yr);
    var H = U.T('P3_microsim_headline').filter(function (r) { return r.scenario === sc; }).sort(function (a, b) { return a.year - b.year; });
    U.lines(U.$('#o-path', v), [{ name: 'Yoxsulluq səviyyəsi, f.b.', x: H.map(function (r) { return r.year; }), y: H.map(function (r) { return r.poverty_rate; }), c: '#B3261E', mode: 'lines+markers' }, { name: 'Yoxsulluq dərinliyi, f.b.', x: H.map(function (r) { return r.year; }), y: H.map(function (r) { return r.poverty_gap; }), c: '#E07B00', mode: 'lines+markers' }, { name: 'Gini, bənd', x: H.map(function (r) { return r.year; }), y: H.map(function (r) { return r.gini; }), c: '#6A3FB5', mode: 'lines+markers' }], 'bazadan fərq', { years: true, zero: true, h: 300 });
    U.$('#o-line', v).onclick = function (e) { var b = e.target.closest('[data-v]'); if (b) { U.HQ.set('l', b.getAttribute('data-v')); location.hash = '#/sosial?' + U.HQ.toString(); } };
  }
  function decChart(el, sc, yr) {
    var D = U.T('P3_microsim_deciles').filter(function (r) { return r.scenario === sc && r.year === yr; }).sort(function (a, b) { return +a.decile.slice(1) - +b.decile.slice(1); });
    U.bars(el, D.map(function (r) { return r.decile; }), [{ name: 'gəlirin dəyişməsi, %', y: D.map(function (r) { return r.delta_pct_income_decile_pc; }), c: '#0E6F7C' }], '%', { cat: true, h: 300 });
  }
  function deciles(v, sc, yr) {
    var D = U.T('P3_microsim_deciles').filter(function (r) { return r.scenario === sc && r.year === yr; }).sort(function (a, b) { return +a.decile.slice(1) - +b.decile.slice(1); });
    v.insertAdjacentHTML('beforeend', '<div class="expl"><b>Qazananlar və uduzanlar</b>: hər desildə gəliri artan və azalan ev təsərrüfatlarının payı. Gəlir artımı aşağı desillərdə böyükdürsə, siyasət mütərəqqidir (bərabərsizliyi azaldır).</div><div class="cols2"><div class="card pad"><h3>Gəlirin dəyişməsi, %</h3><div id="d-1" class="ch"></div></div><div class="card pad"><h3>Qazanan və uduzanların payı, %</h3><div id="d-2" class="ch"></div></div></div>' +
      U.dt('d-t', D, [{ k: 'decile', l: 'Desil' }, { k: 'baseline_income_decile_pc', l: 'Baza gəliri, AZN/ay', n: 1, d: 1 }, { k: 'value_income_decile_pc', l: 'Ssenari, AZN/ay', n: 1, d: 1 }, { k: 'delta_pct_income_decile_pc', l: 'Dəyişmə, %', n: 1, d: 3 }, { k: 'value_winners_share', l: 'Qazananlar, %', n: 1, d: 1 }, { k: 'value_losers_share', l: 'Uduzanlar, %', n: 1, d: 1 }], { title: 'Desillər — ' + yr, file: 'desiller_' + sc }));
    decChart(U.$('#d-1', v), sc, yr);
    U.bars(U.$('#d-2', v), D.map(function (r) { return r.decile; }), [{ name: 'qazananlar', y: D.map(function (r) { return r.value_winners_share; }), c: '#1E7B4F' }, { name: 'uduzanlar', y: D.map(function (r) { return -r.value_losers_share; }), c: '#B3261E' }], '% ev təsərrüfatları', { cat: true, mode: 'relative', h: 300 });
  }
  function jobs(v, sc, yr) {
    var E = U.T('P3_microsim_employment').filter(function (r) { return r.scenario === sc && r.year === yr; }), S = E.filter(function (r) { return /^ms_hired:/.test(r.indicator); }).map(function (r) { var c = r.indicator.split(':')[1]; return Object.assign({ name: (U.FR4S.filter(function (x) { return x[0] === c; })[0] || [c, c])[1] }, r); });
    var F = U.hl(sc, 'employment_hired'), T = U.hl(sc, 'employment');
    v.insertAdjacentHTML('beforeend', '<div class="expl"><b>Ümumi məşğulluq</b> (muzdlu + öz hesabına) və <b>formal muzdlu iş yerləri</b> ayrıca göstərilir: siyasət formal iş yerlərini artıra, eyni zamanda qeyri-formal məşğulluğu azalda bilər. Makro (MikroUnit FR1/FR4) qiymətləndirməsi də yanında verilir.</div>' +
      (F.length || T.length ? U.dt('j-m', T.concat(F), [{ k: 'label_az', l: 'Göstərici (makro)' }, { k: 'horizon', l: 'Müddət' }, { k: 'years', l: 'İllər' }, { k: 'effect', l: 'Təsir', n: 1, d: 3 }, { k: 'effect_unit', l: 'Vahid' }, { k: 'source_engine', l: 'Mənbə' }], { title: 'Makro: ümumi və formal məşğulluq (FR1/FR4)', bare: true }) : '') +
      '<div class="card pad"><h3>Muzdlu işçilər bölmələr üzrə — ' + yr + ' (mikrosimulyasiya)</h3><div id="j-ch" class="ch"></div></div>' + U.dt('j-t', E, [{ k: 'indicator', l: 'Göstərici' }, { k: 'group', l: 'Bölmə' }, { k: 'baseline', l: 'Baza, min', n: 1, d: 1 }, { k: 'value', l: 'Ssenari, min', n: 1, d: 1 }, { k: 'delta', l: 'Fərq, min', n: 1, d: 2 }, { k: 'delta_pct', l: 'Fərq, %', n: 1, d: 3 }], { title: 'Məşğulluq (mikrosimulyasiya)', file: 'mesgulluq_' + sc }));
    U.barH(U.$('#j-ch', v), S.map(function (r) { return r.name; }), S.map(function (r) { return r.delta; }), 'min nəfər, bazadan fərq', { color: '#1F6FB2' });
  }
  function fiscal(v, sc) {
    var F = U.T('P3_microsim_fiscal').filter(function (r) { return r.scenario === sc; }), yrs = U.uniq(F.map(function (r) { return r.year; })).sort(), K = U.uniq(F.map(function (r) { return r.label_az; }));
    v.insertAdjacentHTML('beforeend', '<div class="expl">Vergi və müavinət qaydalarının <b>statik</b> fiskal təsiri (mln AZN/il): gəlir vergisi, sosial ayırmalar, ƏDV, ÜSY, pensiyalar (büdcədən DSMF-ə transfert konsepsiyası). «Birbaşa fiskal xərc» müsbətdirsə büdcəyə yükdür.</div><div class="card pad"><div id="f-ch" class="ch"></div></div>' +
      U.dt('f-t', F, [{ k: 'year', l: 'İl', n: 1 }, { k: 'label_az', l: 'Maddə' }, { k: 'baseline', l: 'Baza, mln AZN', n: 1, d: 1 }, { k: 'value', l: 'Ssenari, mln AZN', n: 1, d: 1 }, { k: 'delta', l: 'Fərq, mln AZN', n: 1, d: 1 }], { title: 'Fiskal təsir (mikrosimulyasiya)', file: 'fiskal_' + sc }));
    U.bars(U.$('#f-ch', v), yrs, K.filter(function (k) { return !/Birbaşa fiskal/.test(k); }).map(function (k, i) { return { name: k, y: yrs.map(function (y) { var r = F.filter(function (x) { return x.year === y && x.label_az === k; })[0]; return r ? r.delta : null; }), c: U.PAL[i % 10] }; }), 'mln AZN, bazadan fərq', { years: true, mode: 'relative', h: 360 });
  }
  function base(v) {
    var B = U.T('P3_microsim_baseline'), K = U.uniq(B.map(function (r) { return r.indicator; })), cur = U.HQ.get('i') || 'poverty_rate';
    v.insertAdjacentHTML('beforeend', '<div class="toolbar">' + U.sel('b-i', K.map(function (k) { return [k, (B.filter(function (r) { return r.indicator === k; })[0] || {}).label_az || k]; }), cur) + '</div><div class="card pad"><div id="b-ch" class="ch"></div></div>' + U.dt('b-t', B, null, { title: 'Mikrosimulyasiya bazası 2024–2030 (statik qocaldılma)', file: 'mikrosim_baza' }));
    var dr = function (k) { var R = B.filter(function (r) { return r.indicator === k; }).sort(function (a, b) { return a.year - b.year; }); U.lines(U.$('#b-ch', v), [{ name: (R[0] || {}).label_az || k, x: R.map(function (r) { return r.year; }), y: R.map(function (r) { return r.value; }), mode: 'lines+markers' }], (R[0] || {}).unit || '', { years: true, h: 300 }); };
    dr(cur); U.$('#b-i', v).onchange = function (e) { dr(e.target.value); };
  }
  U.pages.sosial = function (v, p) {
    var sub = p[1] || '';
    v.innerHTML = U.head('FR3 — mikrosimulyasiya', 'Sosial təsirlər', 'Məşğulluq (ümumi və formal), gəlir bölgüsü (desillər, Gini), yoxsulluq səviyyəsi və dərinliyi, fiskal xərc — ev təsərrüfatları səviyyəsində.') + U.SYN + '<div id="o-hd"></div>' + U.subtabs('sosial', SUB, sub) + '<div id="o-body"></div>';
    var b = U.$('#o-body', v);
    U.need(['soc'], b, function () {
      var ok = function (s) { return U.T('P3_microsim_headline').some(function (r) { return r.scenario === s.id; }); };
      var sc = U.cur(); if (!ok(U.scen(sc) || {})) sc = (U.scens().filter(ok)[0] || {}).id;
      if (!sc) { b.innerHTML = U.empty('Mikrosimulyasiya nəticələri'); return; }
      var yrs = U.uniq(U.T('P3_microsim_headline').filter(function (r) { return r.scenario === sc; }).map(function (r) { return r.year; })).sort(), yr = +U.HQ.get('y') || yrs[Math.min(1, yrs.length - 1)];
      if (yrs.indexOf(yr) < 0) yr = yrs[0];
      U.$('#o-hd', v).innerHTML = '<div class="toolbar">' + U.scenSel('o-sc', sc, ok) + '<label class="small"><b>İl</b> ' + U.sel('o-y', yrs.map(function (y) { return [y, y]; }), yr) + '</label></div>';
      U.bindSel(v, 'o-sc', function (id) { U.HQ.set('s', id); U.HQ.delete('y'); location.hash = '#/sosial' + (sub ? '/' + sub : '') + '?' + U.HQ.toString(); });
      U.$('#o-y', v).onchange = function (e) { U.HQ.set('y', e.target.value); U.HQ.set('s', sc); location.hash = '#/sosial' + (sub ? '/' + sub : '') + '?' + U.HQ.toString(); };
      if (sub === 'desil') deciles(b, sc, yr); else if (sub === 'mesgulluq') jobs(b, sc, yr); else if (sub === 'fiskal') fiscal(b, sc); else if (sub === 'baza') base(b); else summary(b, sc, yr);
    });
  };
})();
