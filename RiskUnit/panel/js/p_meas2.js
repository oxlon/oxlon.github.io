/* p_meas2.js — Tədbirlər, part 2: portfolio optimiser (M4 frontier + budget slider, M3 portfolios, live /optimize/run),
   implementation plan Gantt and status workflow (M6, FR3_status_history), strategy by risk family (M7) with residual
   risk (M5), and the daily decision table (S7). */
(function () {
  'use strict';
  var U = window.U, M = U.MS;
  var MET = [['qaliq_ES10_g', 'ES10 qeyri-neft, %'], ['qaliq_P_g', 'P(GaR)'], ['qaliq_ES10_cpi', 'ES10 inflyasiya'], ['qaliq_P_cpi', 'P(inflyasiya)'], ['qaliq_ES10_fis', 'ES10 büdcə'], ['qaliq_P_fis', 'P(büdcə)'], ['qaliq_CaR95', 'CaR 95 %, mln USD'], ['qaliq_VaR95_ARDNF', 'ARDNF VaR'], ['qaliq_ORaR95', 'neft gəlirinə risk']];
  function nm(id) { var m = U.T('M1_measures_v2').filter(function (r) { return r.tedbir_id === id; })[0]; return m ? m.tedbir : id; }
  M.portfolio = function (el) {
    var f = U.T('M4_frontier').slice().sort(function (a, b) { return a.budce_mln_azn - b.budce_mln_azn; }), bs = f.map(function (r) { return r.budce_mln_azn; });
    if (bs.indexOf(M.b) < 0) M.b = bs[Math.min(bs.length - 1, 6)];
    var cur = f.filter(function (r) { return r.budce_mln_azn === M.b; })[0] || {}, sel = U.ids(cur.secilmis_tedbirler), m1 = U.by(U.T('M1_measures_v2'), 'tedbir_id');
    el.innerHTML = '<div class="note-b">Səmərəli sərhəd: hər büdcə üçün risk azalmasını (prioritet çəkili quyruq boşluğunun aradan qaldırılan payı) maksimallaşdıran tədbirlər dəsti; risk iştahı həddləri (P_g, P_cpi, P_fis, CaR) məhdudiyyətdir. Həll: MILP başlanğıcı + dəqiq yenidən qiymətləndirmə ilə yerli axtarış. Sürgünü çəkin.</div>' +
      '<div class="card pad"><div class="ctl"><label>Büdcə</label><input type="range" id="pf-b" min="0" max="' + (bs.length - 1) + '" step="1" value="' + bs.indexOf(M.b) + '"><b class="tnum" style="font-size:18px">' + U.nf(M.b, 0) + ' mln AZN</b>' +
      '<span class="small">seçilmiş xərc <b>' + U.nf(cur.secilmis_xerc_mln_azn, 1) + '</b> · risk azalması <b>' + U.nf(cur.hedef_funksiya, 2) + ' %</b> · ' + U.nf(cur.tedbir_sayi, 0) + ' tədbir · iştah ' + (cur.istah_mumkun ? '<span class="chip acc">ödənilir</span>' : '<span class="chip bad">ödənilmir</span>') + '</span></div></div>' +
      '<div class="cols2"><div class="card pad"><h3>Səmərəli sərhəd (M4): büdcə → risk azalması</h3><div id="pf-f" class="ch"></div></div><div class="card pad"><h3>Bu büdcədə seçilən tədbirlər</h3><div class="alist">' +
      sel.map(function (t) { var m = (m1[t] || [{}])[0]; return '<a class="arow" href="#/tedbir/reyestr?t=' + t + '"><span><b>' + t + '</b></span><span>' + U.esc(m.tedbir || t) + '<br><span class="small muted">' + U.esc(m.mesul || '') + ' · ' + U.esc(m.strategiya_v2 || '') + '</span></span><span class="when">' + U.nf(m.xerc_mln_azn, 1) + ' mln</span></a>'; }).join('') + '</div></div></div>' +
      '<div class="card pad"><h3>Qalıq metrikalar büdcəyə görə</h3><div id="pf-m" class="ch"></div></div>' +
      U.dt('pf-t', f, null, { title: 'Səmərəli sərhəd (M4_frontier) — bütün büdcələr', file: 'M4_frontier' }) +
      U.dt('pf-3', U.T('M3_portfolio'), null, { title: 'Optimal portfellər 100 / 500 / 1 500 mln AZN (M3): marjinal töhfə, iştah', file: 'M3_portfolio' }) +
      '<div class="card pad"><h3>Yenidən optimallaşdır (canlı)</h3><div class="ctl"><label>Büdcə, mln AZN <input class="num" id="op-b" value="' + M.b + '"></label><label>Məcburi daxil <input class="num" style="width:160px" id="op-i" placeholder="T01;T09"></label><label>Xaric <input class="num" style="width:160px" id="op-x" placeholder="T13"></label>' +
      '<label><input type="checkbox" id="op-f"> bütün sərhəd</label><button class="btn pri" id="op-run">' + U.icon('play', 14) + ' Optimallaşdır</button></div><div id="op-res"></div></div>';
    U.lines(U.$('#pf-f', el), [{ x: f.map(function (r) { return r.secilmis_xerc_mln_azn; }), y: f.map(function (r) { return r.hedef_funksiya; }), name: 'sərhəd', mode: 'lines+markers', c: '#0E6F7C', shape: 'hv' }, { x: [cur.secilmis_xerc_mln_azn], y: [cur.hedef_funksiya], name: 'seçilmiş büdcə', mode: 'markers', marker: { size: 14, color: '#E07B00' } }], 'risk azalması, %', { xt: 'xərc, mln AZN', hm: 'closest' });
    U.lines(U.$('#pf-m', el), MET.slice(0, 6).map(function (m, i) { var b0 = f[0][m[0]]; return { x: bs, y: f.map(function (r) { return U.isNum(b0) && b0 ? r[m[0]] / b0 * 100 : null; }), name: m[1], mode: 'lines+markers', c: U.PAL[i] }; }), 'büdcəsiz səviyyəyə nisbətən, %', { xt: 'büdcə, mln AZN', hm: 'closest' });
    U.$('#pf-b', el).oninput = function (e) { M.b = bs[+e.target.value]; M.portfolio(el); };
    U.$('#op-run', el).onclick = function () {
      var r = U.$('#op-res', el), body = { budget: U.parseNum(U.$('#op-b', el).value) || M.b, include: U.ids(U.$('#op-i', el).value), exclude: U.ids(U.$('#op-x', el).value), frontier: U.$('#op-f', el).checked };
      r.innerHTML = '<p class="small muted">Optimallaşdırılır… (ilk çağırış ≈ 5–15 s)</p>';
      U.API.optimize(body).then(function (j) {
        r.innerHTML = '<p class="small">Büdcə ' + U.nf(j.budget, 0) + ' mln AZN · xərc ' + U.nf(j.cost, 1) + ' · risk azalması ' + U.nf(j.objective, 2) + ' % · ' + U.nf(j.seconds, 1) + ' s</p>' + (j.notes || []).map(function (n) { return '<p class="small muted">' + U.esc(n) + '</p>'; }).join('') +
          U.dt('op-p', j.portfolio || [], null, { title: 'Portfel', file: 'optimal_portfel' }) + U.dt('op-m', j.metrics || [], null, { title: 'Metrikalar: baza vs plan', file: 'optimal_metrikalar' }) + U.dt('op-r', j.residual || [], null, { title: 'Qalıq risk', file: 'optimal_qaliq' }) +
          (j.frontier && j.frontier.length ? U.dt('op-f', j.frontier, null, { title: 'Sərhəd', file: 'optimal_serhed' }) : '');
      }, function (e) { r.innerHTML = U.API.failHtml('Portfelin yenidən optimallaşdırılması', e); });
    };
  };
  M.plan = function (el) {
    var m6 = U.T('M6_implementation_plan'), F = M.pf = M.pf || 'optimal plan', rows = m6.filter(function (r) { return !F || r.plan === F; }), ids = U.uniq(rows.map(function (r) { return r.tedbir_id; }));
    var d0 = new Date(U.META.stamp.as_of), all = rows.map(function (r) { return [new Date(r.baslama), new Date(r.bitme)]; }), t0 = Math.min.apply(null, all.map(function (a) { return +a[0]; }).concat([+d0])), t1 = Math.max.apply(null, all.map(function (a) { return +a[1]; }));
    var pos = function (d) { return ((+new Date(d) - t0) / (t1 - t0) * 100).toFixed(2) + '%'; }, ticks = [];
    for (var y = new Date(t0).getFullYear(); y <= new Date(t1).getFullYear(); y++) [0, 6].forEach(function (mo) { var d = new Date(y, mo, 1); if (+d >= t0 && +d <= t1) ticks.push(d); });
    var st = U.by(U.T('M1_measures_v2'), 'status_az'), late = m6.filter(function (r) { return r.gecikir || r.xeberdarliq; });
    el.innerHTML = '<div class="flow">' + ['təklif', 'təsdiq', 'icrada', 'tamamlandı'].map(function (s, i) { return (i ? '<span class="ar">→</span>' : '') + '<span class="st"><b>' + ((st[s] || []).length) + '</b> ' + s + '</span>'; }).join('') + '<span class="small muted" style="margin-left:12px">Status <code>input/tedbirler_reyestri.csv</code>-də dəyişdirilir; dəyişiklik tarixçəyə avtomatik yazılır.</span></div>' +
      (late.length ? '<div class="note-w"><b>Gecikmə xəbərdarlıqları:</b> ' + late.map(function (r) { return r.tedbir_id + ' ' + U.esc(r.merhele) + (r.xeberdarliq ? ' — ' + U.esc(r.xeberdarliq) : ''); }).join('; ') + '</div>' : '<p class="small up">Gecikən mərhələ yoxdur.</p>') +
      '<div class="toolbar">' + U.seg('pl-f', [['optimal plan', 'Optimal plan'], ['reyestr', 'Bütün reyestr'], ['', 'Hamısı']], F) + '<span class="legend">' + [['hazırlıq', '#9AA6B2'], ['təsdiq', '#1F6FB2'], ['icra', '#E07B00'], ['KPI qiymətləndirməsi', '#1E7B4F']].map(function (k) { return '<span><i class="dotline" style="background:' + k[1] + ';height:8px"></i>' + k[0] + '</span>'; }).join('') + '<span><i class="dotline" style="background:#B3261E"></i>bu gün</span></span></div>' +
      '<div class="card pad gantt"><div class="g-row"><span></span><div class="g-axis">' + ticks.map(function (d) { return '<span style="left:' + pos(d) + '">' + d.toISOString().slice(0, 7) + '</span>'; }).join('') + '</div></div>' +
      ids.map(function (id) { var ph = rows.filter(function (r) { return r.tedbir_id === id; });
        return '<div class="g-row"><a href="#/tedbir/reyestr?t=' + id + '" title="' + U.esc(ph[0].tedbir) + '"><b>' + id + '</b> ' + U.esc(String(ph[0].tedbir).slice(0, 46)) + '</a><div class="g-track">' + ph.map(function (r) {
          return '<span class="g-bar" title="' + U.esc(r.merhele + ': ' + r.baslama + ' – ' + r.bitme + ' · ' + r.status) + '" style="left:' + pos(r.baslama) + ';width:calc(' + pos(r.bitme) + ' - ' + pos(r.baslama) + ');background:' + ({ 'hazırlıq': '#9AA6B2', 'təsdiq': '#1F6FB2', 'icra': '#E07B00', 'KPI qiymətləndirməsi': '#1E7B4F' }[r.merhele] || '#0E6F7C') + '"></span>'; }).join('') + '<span class="g-today" style="left:' + pos(d0) + '"></span></div></div>'; }).join('') + '</div>' +
      '<p class="small muted">Rəng mərhələni göstərir: hazırlıq (boz), təsdiq (göy), icra (narıncı), KPI qiymətləndirməsi (yaşıl).</p>' +
      U.dt('pl-t', rows, null, { title: 'İcra planı (M6_implementation_plan)', file: 'M6_implementation_plan' }) + U.dt('pl-h', U.T('FR3_status_history'), null, { title: 'Status tarixçəsi (FR3_status_history)', file: 'FR3_status_history' });
    U.$('#pl-f', el).onclick = function (e) { var b = e.target.closest('[data-v]'); if (b) { M.pf = b.getAttribute('data-v'); M.plan(el); } };
  };
  M.strategy = function (el) {
    var m7 = U.T('M7_strategy'), m5 = U.T('M5_residual_v2').filter(function (r) { return r.risk_id; });
    el.innerHTML = '<div class="grid g3">' + m7.map(function (r) { return '<div class="card pad"><div class="pill-row" style="margin:0 0 6px">' + U.fam(r.aile) + '<span class="chip coef">' + U.esc(r.esas_yanasma) + '</span></div><h3>' + U.esc(r.aile_ad) + '</h3><p class="small">' + U.esc(r.strateji_izah) + '</p>' +
      U.kv([['Risklər', U.ids(r.riskler).map(function (x) { return '<a href="#/reyestr/' + x + '">' + x + '</a>'; }).join(' ')], ['Strategiya qarışığı', U.esc(r.strategiya_qarisigi)], ['Plandakı tədbirlər', U.ids(r.plandaki_tedbirler).map(function (x) { return '<a href="#/tedbir/reyestr?t=' + x + '" title="' + U.esc(nm(x)) + '">' + x + '</a>'; }).join(' ')],
        ['Plan xərci', U.nf(r.xerc_plan_mln_azn, 1) + ' mln AZN'], ['Risk azalmasına töhfə', U.nf(r.hedef_funksiya_tohfesi, 2)], ['Yüksək qalıq risk', r.yuksek_qaliq_risk ? '<b class="down">' + U.esc(r.yuksek_qaliq_risk) + '</b>' : 'yoxdur']]) + '</div>'; }).join('') + '</div>' +
      '<div class="card pad"><h3>Skor indi və plandan sonra qalıq skor (M5)</h3><div id="sg-r" class="ch"></div></div>' +
      U.dt('sg-5', U.T('M5_residual_v2'), null, { title: 'Qalıq risk (M5_residual_v2): kanal quyruq töhfələri baza / cari / plan', file: 'M5_residual_v2' }) + U.dt('sg-7', m7, null, { title: 'Strategiya (M7_strategy)', file: 'M7_strategy' });
    var rs = m5.slice().sort(function (a, b) { return b.FR2_skor - a.FR2_skor; });
    U.bars(U.$('#sg-r', el), rs.map(function (r) { return r.risk_id; }), [{ name: 'skor indi', y: rs.map(function (r) { return r.FR2_skor; }), c: '#B3261E' }, { name: 'qalıq skor (plan)', y: rs.map(function (r) { return r.qaliq_skor_plan; }), c: '#1E7B4F' }], 'skor', { cat: true });
  };
  M.decision = function (el) {
    el.innerHTML = '<div class="note-b">Gündəlik qərar cədvəli: bugünkü canlı sapmalar × elastikliklər → baş proqnozlara təsir, ən çox təsirlənən dəyişənlər, ən həssas parametrlər və təklif olunan tədbirlər — əlverişsiz bal üzrə sıralanıb.</div>' +
      U.dt('dq-t', U.T('S7_daily_decision'), null, { title: 'Gündəlik qərar cədvəli (S7_daily_decision)', file: 'S7_daily_decision' });
  };
})();
