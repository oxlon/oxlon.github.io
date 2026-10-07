/* p_sec2.js — Sektor təsirləri (FR2), part 2: competitiveness indicators, price-model results (unit shocks and the
   scenario's price effects), IO vs MicroUnit comparison by FR1 sector, IO tables / update and the page router. */
(function () {
  'use strict';
  var U = window.U;
  var SUB = [['', 'Təsirlənən sektorlar'], ['multiplikator', 'Multiplikatorlar'], ['elaqe', 'Əlaqələr və açar sektorlar'], ['reqabet', 'Rəqabətlilik'], ['qiymet', 'Qiymət modeli'], ['muqayise', 'IO və MikroUnit'], ['cedvel', 'IO cədvəlləri']];
  function comp(v) {
    var t = U.ioTab('P2_io_competitiveness', U.HQ.get('t')), R = t.rows;
    v.insertAdjacentHTML('beforeend', '<div class="expl"><b>Rəqabətlilik göstəriciləri</b>: vahid əmək xərci (əmək ödənişi / əlavə dəyər — aşağı yaxşıdır), əmək məhsuldarlığı, idxal nüfuzu (daxili bazarda idxalın payı), ixrac yönümü (buraxılışda ixracın payı), ixracda daxili əlavə dəyər. FR10 sütunları — MikroUnit sənaye modulunun 2025 göstəriciləri və 2026–2030 proqnoz artımı.</div>' +
      '<div class="toolbar">' + U.seg('s-tab', t.tables.map(function (x) { return [x, x]; }), t.cur) + '</div><div class="cols2"><div class="card pad"><h3>İxrac yönümü və idxal nüfuzu</h3><div id="c-io" class="ch"></div></div><div class="card pad"><h3>Vahid əmək xərci və məhsuldarlıq</h3><div id="c-ulc" class="ch"></div></div></div>' +
      U.dt('s-comp', R, [{ k: 'name_az', l: 'Sektor' }, { k: 'output_mln', l: 'Buraxılış, mln AZN', n: 1, d: 0 }, { k: 'va_mln', l: 'ƏD, mln AZN', n: 1, d: 0 }, { k: 'emp_thsd', l: 'Məşğulluq, min', n: 1, d: 1 }, { k: 'lab_prod_thsd_azn', l: 'Məhsuldarlıq, min AZN', n: 1, d: 1 }, { k: 'ulc_comp_va', l: 'Vahid əmək xərci', n: 1, d: 3 }, { k: 'import_penetration', l: 'İdxal nüfuzu', p: 1, d: 1 }, { k: 'export_orientation', l: 'İxrac yönümü', p: 1, d: 1 }, { k: 'va_in_exports_share', l: 'İxracda daxili ƏD', p: 1, d: 1 }, { k: 'fr10_forecast_growth_2026_30_pct_pa', l: 'FR10 artım 2026–30, %/il', n: 1, d: 2 }, { k: 'fr10_branches', l: 'FR10 sahələri' }], { title: 'Rəqabətlilik — ' + t.cur, file: 'reqabetlilik' }));
    var S = R.slice().sort(function (a, b) { return b.export_orientation - a.export_orientation; });
    U.barH(U.$('#c-io', v), S.map(function (r) { return r.name_az; }), null, 'pay', { sets: [{ name: 'ixrac yönümü', v: S.map(function (r) { return r.export_orientation; }), c: '#1E7B4F' }, { name: 'idxal nüfuzu', v: S.map(function (r) { return r.import_penetration; }), c: '#B3261E' }] });
    var P = R.filter(function (r) { return U.isNum(r.lab_prod_thsd_azn) && r.lab_prod_thsd_azn < 300; });
    U.scatter(U.$('#c-ulc', v), P.map(function (r) { return { x: r.lab_prod_thsd_azn, y: r.ulc_comp_va, t: r.sector, s: 9 + Math.sqrt(r.va_mln || 0) / 12, h: r.name_az }; }), 'əmək məhsuldarlığı, min AZN/nəfər', 'vahid əmək xərci', { h: 360 });
    U.$('#s-tab', v).onclick = function (e) { var b = e.target.closest('[data-v]'); if (b) { U.HQ.set('t', b.getAttribute('data-v')); location.hash = '#/sektor/reqabet?' + U.HQ.toString(); } };
  }
  function price(v, sc) {
    var P = U.T('P2_io_price_shocks'), shocks = U.uniq(P.map(function (r) { return r.shock + '|' + r.size + '|' + (r.target || ''); })), cur = U.HQ.get('p') || shocks[0];
    var R = P.filter(function (r) { return r.shock + '|' + r.size + '|' + (r.target || '') === cur; }), cpi = R.filter(function (r) { return r.sector === 'CPI'; })[0], S = R.filter(function (r) { return r.sector !== 'CPI'; }).sort(function (a, b) { return b.dp_basic_pct - a.dp_basic_pct; });
    var SN = { fuel_price: 'Yanacaq qiyməti', elec_tariff: 'Elektrik tarifi', gas_tariff: 'Qaz tarifi', water_tariff: 'Su tarifi', labour_cost: 'Əmək xərci', fx_deval: 'Manatın devalvasiyası', import_tariff: 'İdxal rüsumu', vat_rate: 'ƏDV dərəcəsi', product_tax: 'Məhsul vergisi' };
    var lab = function (k) { var p = k.split('|'); return (SN[p[0]] || p[0]) + ' +' + p[1] + (p[0] === 'vat_rate' || p[0] === 'import_tariff' || p[0] === 'product_tax' ? ' f.b.' : ' %') + (p[2] ? ' (' + U.SECN(p[2]) + ')' : ''); };
    var SP = U.T('P2_io_scenarios').filter(function (r) { return r.scenario === sc && /^io_price:|^io_cpi/.test(r.indicator); });
    v.insertAdjacentHTML('beforeend', '<div class="expl"><b>Leontief qiymət modeli</b>: xərc artımı (tarif, vergi, məzənnə, əmək haqqı) aralıq alışlar vasitəsilə bütün sektorların qiymətlərinə ötürülür; mənfəət marjası sabit, tələb reaksiyası yoxdur — yəni yuxarı sərhəd. İQİ — istehlak səbəti çəkiləri ilə.</div>' +
      '<div class="toolbar"><label class="small"><b>Vahid şok</b> ' + U.sel('p-sh', shocks.map(function (k) { return [k, lab(k)]; }), cur) + '</label>' + (cpi ? '<span class="chip warn">İQİ: ' + U.sg(cpi.dp_consumer_item_pct, 3) + ' %</span>' : '') + '</div>' +
      '<div class="cols2"><div class="card pad"><h3>Sektor əsas qiymətləri — ' + U.esc(lab(cur)) + '</h3><div id="p-ch" class="ch"></div></div><div>' + U.dt('p-t', S.map(function (r) { return Object.assign({ name: U.SECN(r.sector) }, r); }), [{ k: 'name', l: 'Sektor' }, { k: 'dp_basic_pct', l: 'Əsas qiymət, %', n: 1, d: 3 }, { k: 'dp_consumer_item_pct', l: 'İstehlak qiyməti, %', n: 1, d: 3 }], { title: 'Qiymət şoku', file: 'qiymet_soku' }) + '</div></div>' +
      U.sec('Seçilmiş ssenarinin qiymət təsiri', U.sname(sc), SP.length ? U.dt('p-sc', SP, [{ k: 'label_az', l: 'Göstərici' }, { k: 'year', l: 'İl', n: 1 }, { k: 'delta_pct', l: 'Dəyişmə, %', n: 1, d: 3 }, { k: 'method', l: 'Metod' }, { k: 'note_az', l: 'Qeyd' }], { title: 'IO qiymət nəticələri', file: 'io_qiymet_' + sc }) : '<p class="small muted">Bu ssenaridə qiymət kanalı yoxdur.</p>'));
    U.barH(U.$('#p-ch', v), S.map(function (r) { return U.SECN(r.sector); }), S.map(function (r) { return r.dp_basic_pct; }), '% dəyişmə', { color: '#B3261E' });
    U.$('#p-sh', v).onchange = function (e) { U.HQ.set('p', e.target.value); location.hash = '#/sektor/qiymet?' + U.HQ.toString(); };
  }
  function cmp(v, sc) {
    var IO = U.T('P2_io_scenarios').filter(function (r) { return r.scenario === sc && /^io_va:/.test(r.indicator); }), map = {};
    U.T('cfg_io_sectors').forEach(function (r) { map[r.code] = r.fr1_group; });
    if (!IO.length) { v.insertAdjacentHTML('beforeend', U.empty('IO və MikroUnit müqayisəsi', 'Bu ssenari üçün IO əlavə dəyər nəticəsi yoxdur.')); return; }
    var yr = IO[0].year, g = {};
    IO.forEach(function (r) { var k = map[r.group] || map[r.indicator.split(':')[1]] || 'oth', o = g[k] = g[k] || { b: 0, d: 0 }; o.b += r.baseline || 0; o.d += r.delta || 0; });
    var MI = (window.POL.eff ? U.T('P1_effects') : []).filter(function (r) { return r.scenario === sc && r.engine === 'micro' && r.year === yr && /^sector_va:/.test(r.indicator); }), mi = {};
    MI.forEach(function (r) { mi[r.indicator.split(':')[1]] = r; });
    var rows = Object.keys(g).sort().map(function (k) { var m = mi[k]; return { fr1: (m && m.label_az ? m.label_az.replace(/^[^—]*— /, '') : k), io: g[k].b ? g[k].d / g[k].b * 100 : null, micro: m ? m.delta_pct : null, diff: m && g[k].b ? g[k].d / g[k].b * 100 - m.delta_pct : null }; });
    v.insertAdjacentHTML('beforeend', '<div class="expl">Eyni ssenarinin <b>' + yr + '</b>-ci il sektor əlavə dəyərinə təsiri iki metodla: IO (sabit əmsallı Leontief, yalnız tələb kanalı, qiymət reaksiyası yoxdur) və MikroUnit zənciri (FR1 sektor tənlikləri, qiymət və gəlir geri əlaqələri). IO sektorları FR1 qruplarına cəmlənib. Fərqlər adətən: IO-da sıxışdırma (crowding-out) və maliyyələşmə effekti yoxdur, MikroUnit-də sektorlar arası alış zənciri yoxdur.</div>' +
      '<div class="cols2"><div class="card pad"><div id="x-ch" class="ch"></div></div><div>' + U.dt('x-t', rows, [{ k: 'fr1', l: 'Sektor (FR1)' }, { k: 'io', l: 'IO, %', n: 1, d: 3 }, { k: 'micro', l: 'MikroUnit, %', n: 1, d: 3 }, { k: 'diff', l: 'Fərq, f.b.', n: 1, d: 3 }], { title: 'Əlavə dəyər, % baza ilə fərq — ' + yr, file: 'io_vs_mikro_' + sc }) + '</div></div>');
    U.barH(U.$('#x-ch', v), rows.map(function (r) { return r.fr1; }), null, '% baza ilə fərq', { sets: [{ name: 'IO', v: rows.map(function (r) { return r.io; }), c: '#1F6FB2' }, { name: 'MikroUnit', v: rows.map(function (r) { return r.micro; }), c: '#0E6F7C' }] });
  }
  function tables(v, sc) {
    var D = U.T('D_io_tables'), tabs = U.uniq(D.map(function (r) { return r.table; })), cur = U.HQ.get('t') && tabs.indexOf(U.HQ.get('t')) >= 0 ? U.HQ.get('t') : tabs[tabs.length - 1], info = U.T('P2_io_update_info')[0] || {};
    v.insertAdjacentHTML('beforeend', '<div class="toolbar">' + U.seg('s-tab', tabs.map(function (x) { return [x, x]; }), cur) + '</div>' + U.dt('d-io', D.filter(function (r) { return r.table === cur; }), null, { title: 'Aqreqasiya olunmuş IO cədvəli — ' + cur + ' (mln AZN, əsas qiymətlər)', file: 'io_cedveli' }) +
      U.sec('2025-ə yeniləmə (GRAS)', 'iterasiya ' + U.nf(info.iterations, 0) + ' · maksimal nisbi qalıq ' + U.sig(info.max_rel_resid) + ' · yığıldı: ' + (info.converged ? 'bəli' : 'xeyr') + ' · MH uyğunsuzluğu ' + U.nf(info.na_discrepancy_pct_output, 2) + ' %', U.dt('d-up', U.T('P2_io_update_2025'), null, { title: 'GRAS hədəfləri və nəticələri (min AZN)', file: 'io_gras_2025' }) + U.dt('d-upi', U.T('P2_io_update_info'), null, { title: 'GRAS yığılması', bare: true })) +
      U.sec('Məhsul → sektor xəritəsi', 'DSK 2021 CPA məhsulları (81) → 23 IO sektoru', U.dt('d-map', U.T('D_io_sector_map').map(function (r) { return Object.assign({ name: U.SECN(r.sector) }, r); }), [{ k: 'cpa', l: 'CPA' }, { k: 'product_name_en', l: 'Məhsul (DSK cədvəlindəki ingiliscə ad)' }, { k: 'sector', l: 'Sektor kodu' }, { k: 'name', l: 'Sektor' }], { title: 'CPA → IO sektoru', file: 'cpa_xeritesi' })) +
      U.sec('Bütün IO ssenari nəticələri', U.sname(sc), U.dt('d-sc', U.T('P2_io_scenarios').filter(function (r) { return r.scenario === sc; }), null, { title: 'P2 IO nəticələri', file: 'io_neticeler_' + sc, lim: 100 })));
    U.$('#s-tab', v).onclick = function (e) { var b = e.target.closest('[data-v]'); if (b) { U.HQ.set('t', b.getAttribute('data-v')); location.hash = '#/sektor/cedvel?' + U.HQ.toString(); } };
  }
  U.pages.sektor = function (v, p) {
    var sub = p[1] || '';
    v.innerHTML = U.head('FR2 — girdi-çıxdı (IO) modeli', 'Sektor təsirləri', 'Hansı sektorlar siyasətdən qazanır və ya itirir: buraxılış, əlavə dəyər, məşğulluq və qiymətlərin % dəyişməsi; multiplikatorlar, sektorlar arası əlaqələr, rəqabətlilik və IO ilə MikroUnit nəticələrinin müqayisəsi.') + '<div id="s-hd"></div>' + U.subtabs('sektor', SUB, sub) + '<div id="s-body"></div>';
    var b = U.$('#s-body', v);
    U.need(['io'], b, function () {
      var sc = U.cur(); if (U.HQ.get('s')) U.setCur(sc); U.resetScens(); sc = U.cur();
      U.$('#s-hd', v).innerHTML = '<div class="toolbar">' + U.scenSel('s-sc', sc) + '</div>';
      U.bindSel(v, 's-sc', function (id) { U.HQ.set('s', id); location.hash = '#/sektor' + (sub ? '/' + sub : '') + '?' + U.HQ.toString(); });
      if (sub === 'multiplikator') U.secMult(b); else if (sub === 'elaqe') U.secLink(b); else if (sub === 'reqabet') comp(b); else if (sub === 'qiymet') price(b, sc);
      else if (sub === 'muqayise') U.need(['eff'], b, function () { cmp(b, sc); }); else if (sub === 'cedvel') tables(b, sc); else U.secAffected(b, sc);
    });
  };
})();
