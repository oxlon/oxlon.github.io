/* p_eff2.js — Makro və mikro təsirlər (FR1), part 2: micro view (sector performance FR1/FR10, market equilibrium FR12 —
   HHI, entry, exit; services FR5; regions), full year-by-year table and the page router (#/tesir[/mikro|/cedvel]). */
(function () {
  'use strict';
  var U = window.U;
  var SUB = [['', 'Makro'], ['mikro', 'Mikro: sektorlar və bazarlar'], ['cedvel', 'Bütün nəticələr (cədvəl)']];
  function bars(v, id, L, xt, title, note) {
    if (!L.length) return '';
    L.sort(function (a, b) { return b.v - a.v; });
    setTimeout(function () { var el = U.$('#' + id, v); if (el) U.barH(el, L.map(function (x) { return x.label_az.replace(/^[^—]*— /, ''); }), L.map(function (x) { return x.v; }), xt, { colors: null, sets: [{ v: L.map(function (x) { return x.v; }), colors: L.map(function (x) { return x.v >= 0 ? '#1E7B4F' : '#B3261E'; }), name: '' }] }); }, 0);
    return '<div class="card pad"><h3>' + U.esc(title) + '</h3>' + (note ? '<p class="small muted">' + note + '</p>' : '') + '<div id="' + id + '" class="ch"></div></div>';
  }
  function micro(v, sc, hz) {
    var R = U.effRows(sc, function (r) { return r.engine === 'micro' && /sektor|bazar|xidmət|regional/.test(r.group); });
    if (!R.length) { v.insertAdjacentHTML('beforeend', U.empty('Mikro (sektor və bazar) nəticələri', 'Bu ssenari MikroUnit zəncirindən keçmir (məs. yalnız IO və ya mikrosimulyasiya nümunəsi).')); return; }
    var M = U.hzMean(R, hz), pick = function (re) { return M.filter(function (x) { return re.test(x.indicator); }); };
    var va = pick(/^sector_va:/), pr = pick(/^sector_price:/), hhi = pick(/^hhi:/), ent = pick(/^entry:/), ex = pick(/^exit:/), sv = pick(/^services_real:/), rg = pick(/^region_output:/), ind = pick(/^(industry_output|hhi_man|margin|fr10)/);
    var mk = U.uniq(hhi.map(function (x) { return x.indicator.split(':')[1]; })), mrow = mk.map(function (k) { var g = function (L) { var x = L.filter(function (y) { return y.indicator.split(':')[1] === k; })[0]; return x ? x : {}; }; var h = g(hhi), e = g(ent), x = g(ex);
      return { bazar: (h.label_az || k).replace(/^[^—]*— /, '').replace(/ \(FR12\)$/, ''), hhi: h.v, entry: e.dmean, exit: x.dmean, tier: h.tier }; });
    v.insertAdjacentHTML('beforeend', '<div class="expl">Mikro təsirlər MikroUnit zəncirindən gəlir: <b>sektor performansı</b> (FR1 sektor əlavə dəyəri və deflatorları, FR10 sənaye), <b>bazar müvazinəti</b> (FR12: konsentrasiya HHI, bazara giriş və çıxış), <b>pullu xidmətlər</b> (FR5) və <b>regionlar</b>. Rəqəmlər seçilmiş müddətin orta fərqidir (%).</div>' +
      '<div class="cols2">' + bars(v, 'm-va', va, '% baza ilə fərq', 'Sektorların əlavə dəyəri (real)', 'FR1 sektor bölgüsü') + bars(v, 'm-pr', pr, '% baza ilə fərq', 'Sektor qiymətləri (deflatorlar)', 'qiymət artımı — xərc yükü') + '</div>' +
      U.sec('Bazar müvazinəti (FR12)', 'Konsentrasiya (HHI, yuxarı sərhəd), yeni və fəaliyyəti dayanan müəssisələr', mrow.length ? U.dt('m-mk', mrow, [{ k: 'bazar', l: 'Bazar' }, { k: 'hhi', l: 'HHI, % fərq', n: 1, d: 3 }, { k: 'entry', l: 'Yeni müəssisələr (fərq, say/il)', n: 1, d: 1 }, { k: 'exit', l: 'Dayanan müəssisələr (fərq, say/il)', n: 1, d: 1 }, { k: 'tier', l: 'Sübut', f: function (t) { return U.tier(t); } }], { title: 'FR12 bazarları — ' + hz + ' müddət', file: 'bazar_muvazineti' }) : U.empty('FR12 bazar nəticələri')) +
      '<div class="cols2">' + bars(v, 'm-sv', sv, '% baza ilə fərq', 'Pullu xidmətlər (FR5)', '') + bars(v, 'm-rg', rg, '% baza ilə fərq', 'Regional sənaye buraxılışı', 'regionlar arası fərq — regional disbalans riski (FR4)') + '</div>' +
      (ind.length ? U.dt('m-ind', ind, [{ k: 'label_az', l: 'Göstərici' }, { k: 'v', l: '% fərq (orta)', n: 1, d: 3 }, { k: 'unit', l: 'Vahid' }, { k: 'tier', l: 'Sübut', f: function (t) { return U.tier(t); } }], { title: 'Sənaye (FR10)', bare: true }) : ''));
  }
  function table(v, sc) {
    var R = U.effRows(sc);
    v.insertAdjacentHTML('beforeend', '<p class="small muted">Bütün mühərriklərin illik nəticələri (P1_effects): baza, ssenari, fərq. Səviyyələr üçün «Fərq, %», dərəcələr üçün f.b. CAEM yalnız sapmaları verir (baza və ssenari boşdur). Süzgəc: mühərrik, göstərici və ya qrup yazın.</p>' +
      U.dt('e-all', R, [{ k: 'engine', l: 'Mühərrik' }, { k: 'group', l: 'Qrup' }, { k: 'label_az', l: 'Göstərici' }, { k: 'unit', l: 'Vahid' }, { k: 'year', l: 'İl', n: 1 }, { k: 'horizon', l: 'Müddət' }, { k: 'baseline', l: 'Baza', n: 1 }, { k: 'value', l: 'Ssenari', n: 1 }, { k: 'delta', l: 'Fərq', n: 1 }, { k: 'delta_pct', l: 'Fərq, % / f.b.', n: 1, d: 3 }, { k: 'tier', l: 'Sübut', f: function (t) { return U.tier(t); } }, { k: 'note_az', l: 'Qeyd', f: U.noteFmt }], { title: 'İllik nəticələr — ' + U.sname(sc), file: 'tesirler_' + sc, lim: 150 }));
  }
  U.pages.tesir = function (v, p) {
    var sc = U.cur(), hz = U.HQ.get('h') || 'qısa', sub = p[1] || '';
    if (U.HQ.get('s')) U.setCur(sc);
    v.innerHTML = U.head('FR1 — makro və mikro təsirlər', 'Makro və mikro təsirlər', 'Siyasətin ÜDM, qiymətlər, məşğulluq, büdcə və sektorlara təsiri — baza proqnozu ilə müqayisədə. Müddəti seçin; hər rəqəmin yanında sübut səviyyəsi (A–D) və mənbə metod göstərilir.') +
      '<div class="toolbar">' + U.scenSel('e-sc', sc) + '<span class="small muted">Sübut səviyyəsi: ' + 'ABCD'.split('').map(function (c) { return U.tier(c) + ' ' + U.esc(U.TIER[c].split(' — ')[1]); }).join(' · ') + '</span></div>' +
      U.scHead(sc) + U.hztabs('tesir' + (sub ? '/' + sub : ''), sc, hz) + U.subtabs('tesir', SUB, sub).replace(/href="(#\/tesir[^"]*)"/g, function (m, h) { return 'href="' + h + '?s=' + U.enc(sc) + '&h=' + U.enc(hz) + '"'; }) + '<div id="e-body"></div>';
    U.bindSel(v, 'e-sc', function (id) { location.hash = '#/tesir' + (sub ? '/' + sub : '') + '?s=' + U.enc(id) + '&h=' + U.enc(hz); });
    var b = U.$('#e-body', v);
    U.need(['eff'], b, function () { if (sub === 'mikro') micro(b, sc, hz); else if (sub === 'cedvel') table(b, sc); else U.effMacro(b, sc, hz); });
  };
})();
