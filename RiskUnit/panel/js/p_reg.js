/* p_reg.js — Risk reyestri: R01–R19 table (family, owner, P, I, score, priority, trend, residual), 5×5 heat map, all
   alerts, score history, risk factors (FR1 indicators, channels, chronology, hazards). #/reyestr/<id> → p_risk.js. */
(function () {
  'use strict';
  var U = window.U;
  var F = { fam: '', pr: '' };
  U.heatColor = function (s) { return s >= 15 ? '#F4C7C3' : s >= 12 ? '#F9DDD6' : s >= 6 ? '#FFF0C7' : '#DDF0E4'; };
  U.heat5 = function (sel) {
    var sc = U.T('FR2_risk_scores'), cell = {};
    sc.forEach(function (r) { var k = r.P_bal + '_' + r.I_bal; (cell[k] = cell[k] || []).push(r); });
    var h = '<div class="heat5" role="table" aria-label="İstilik xəritəsi">';
    for (var p = 5; p >= 1; p--) {
      h += '<div class="ax" title="Ehtimal balı">P' + p + '</div>';
      for (var i = 1; i <= 5; i++) {
        var rs = cell[p + '_' + i] || [];
        h += '<div class="hc" style="background:' + U.heatColor(p * i) + '">' + rs.map(function (r) { return '<a class="rk" href="#/reyestr/' + r.risk_id + '" title="' + U.esc(r.ad + ' · skor ' + r.skor) + '"' + (sel === r.risk_id ? ' style="background:#15202B;color:#fff"' : '') + '>' + r.risk_id + '</a>'; }).join('') + '<span class="sc">' + p * i + '</span></div>';
      }
    }
    return h + '<div></div>' + [1, 2, 3, 4, 5].map(function (i) { return '<div class="ax" title="Təsir balı">T' + i + '</div>'; }).join('') + '</div>' +
      '<div class="heat-cap"><span>Ehtimal ↑ (P1 ≤ 5 % … P5 > 50 %)</span><span>Təsir → (T1 … T5)</span></div>';
  };
  U.regRows = function () {
    var sc = U.T('FR2_risk_scores'), reg = U.by(U.T('input_risk_reyestri'), 'risk_id'), pv = U.prevScores(), m5 = U.by(U.T('M5_residual_v2'), 'risk_id'), cov = U.by(U.T('FR3_coverage'), 'risk_id');
    return sc.map(function (r) {
      var g = (reg[r.risk_id] || [{}])[0], p = pv.by[r.risk_id], q = (m5[r.risk_id] || [{}])[0], c = (cov[r.risk_id] || [{}])[0];
      return { risk_id: r.risk_id, aile: r.aile, ad: r.ad, nov: r.nov, sahib: r.sahib, ehtimal: r.ehtimal, P_bal: r.P_bal, I_bal: r.I_bal, skor: r.skor, prioritet: r.prioritet, I_olcu: r.I_olcu, ufuq: r.ufuq,
        trend: p ? r.skor - p.skor : null, qaliq: q.qaliq_skor_plan, qaliq_pr: q.qaliq_prioritet, tedbir: c.tedbir_sayi, caem: g.caem_kateqoriya, gosterici: g.gosterici, sira: r.sira };
    });
  };
  function regTable(rows) {
    return U.dt('reg', rows, [
      { k: 'risk_id', l: 'Risk', f: function (v) { return '<a href="#/reyestr/' + v + '"><b>' + v + '</b></a>'; } },
      { k: 'aile', l: 'Ailə', f: function (v) { return U.fam(v); } }, { k: 'ad', l: 'Ad', cls: 'lw', f: function (v, r) { return '<a href="#/reyestr/' + r.risk_id + '" style="color:var(--ink)">' + U.esc(v) + '</a>'; } },
      { k: 'nov', l: 'Növ' }, { k: 'sahib', l: 'Sahib' }, { k: 'ehtimal', l: 'Ehtimal', n: 1, p: 1, d: 1 }, { k: 'P_bal', l: 'P', n: 1, d: 0, t: 'Ehtimal balı 1–5' }, { k: 'I_bal', l: 'T', n: 1, d: 0, t: 'Təsir balı 1–5' },
      { k: 'skor', l: 'Skor', n: 1, f: function (v) { return U.score(v); } }, { k: 'prioritet', l: 'Prioritet', f: U.prio },
      { k: 'trend', l: 'Trend', n: 1, t: 'əvvəlki hesablamaya nisbətən skor dəyişməsi', f: function (v) { return v == null ? '<span class="chip">yeni</span>' : v ? '<b class="' + (v > 0 ? 'down' : 'up') + '">' + (v > 0 ? '↑ ' : '↓ ') + U.sg(v, 0) + '</b>' : '<span class="muted">→ 0</span>'; } },
      { k: 'I_olcu', l: 'Təsir ölçüsü' }, { k: 'ufuq', l: 'Üfüq', n: 1, d: 0 }, { k: 'tedbir', l: 'Tədbir', n: 1, d: 0 },
      { k: 'qaliq', l: 'Qalıq skor (plan)', n: 1, f: function (v, r) { return U.isNum(v) ? U.score(v) + ' ' + U.prio(r.qaliq_pr) : '—'; } }, { k: 'caem', l: 'CAEM kateqoriyası' }],
      { title: 'Risk reyestri — ' + rows.length + ' risk', file: 'risk_reyestri', sort: ['skor', -1], maxh: 0, href: function (r) { return '#/reyestr/' + r.risk_id; } });
  }
  function main(el) {
    var rows = U.regRows().filter(function (r) { return (!F.fam || r.aile === F.fam) && (!F.pr || r.prioritet === F.pr); });
    var fams = U.uniq(U.T('FR2_risk_scores').map(function (r) { return r.aile; }));
    el.innerHTML = '<div class="toolbar">' + U.seg('rg-fam', [['', 'Bütün ailələr']].concat(fams.map(function (f) { return [f, f + ' · ' + (U.FAM[f] || '')]; })), F.fam) +
      U.seg('rg-pr', [['', 'Bütün prioritetlər'], ['yüksək', 'yüksək'], ['orta', 'orta'], ['aşağı', 'aşağı']], F.pr) + '</div>' +
      '<div class="cols2"><div class="card pad"><h3>İstilik xəritəsi (5 × 5)</h3>' + U.heat5() +
      '<p class="small muted">Rəng: skor ≥ 15 tünd qırmızı, ≥ 12 qırmızı (yüksək), ≥ 6 sarı (orta), digər yaşıl. Hədlər <code>input/hedler.csv</code>-dədir (Nazirlik təsdiq edir).</p>' +
      '</div><div class="card pad">' + U.dt('rg-hm', U.T('FR2_heatmap'), [{ k: 'P_bal', l: 'P', n: 1, d: 0 }, { k: 'I_bal', l: 'T', n: 1, d: 0 }, { k: 'skor', l: 'Skor', n: 1, d: 0 }, { k: 'riskler', l: 'Risklər' }], { title: 'İstilik xəritəsinin xanaları (FR2_heatmap)', file: 'FR2_heatmap', lim: 25, maxh: 220 }) +
      '<h3 style="margin-top:14px">Ailələr</h3>' + fams.map(function (f) { var rs = U.T('FR2_risk_scores').filter(function (r) { return r.aile === f; }); return '<div class="kv1"><span>' + U.fam(f) + ' ' + U.esc(U.FAM[f] || '') + '</span><b>' + rs.length + ' risk · maks. skor ' + Math.max.apply(null, rs.map(function (r) { return r.skor; })) + '</b></div>'; }).join('') + '</div></div>' + regTable(rows);
    el.onclick = function (e) { var b = e.target.closest('#rg-fam [data-v], #rg-pr [data-v]'); if (!b) return; F[b.parentNode.id === 'rg-fam' ? 'fam' : 'pr'] = b.getAttribute('data-v'); main(el); };
  }
  function history(el) {
    var h = U.T('FR2_score_history'), by = U.by(h, 'risk_id');
    el.innerHTML = '<div class="card pad"><h3>Skor tarixçəsi (FR2_score_history)</h3><div id="rg-hc" class="ch"></div><p class="small muted">Hər tam hesablama dövrü bir nöqtə əlavə edir; hesablama tarixləri: ' + U.uniq(h.map(function (r) { return r.as_of; })).join(', ') + '.</p></div>' +
      U.dt('rg-h', h, null, { title: 'Bütün skor qeydləri', file: 'FR2_score_history' });
    U.lines(U.$('#rg-hc', el), Object.keys(by).sort().map(function (k) { var r = by[k].sort(function (a, b) { return a.as_of < b.as_of ? -1 : 1; }); return { x: r.map(function (q) { return q.as_of; }), y: r.map(function (q) { return q.skor; }), name: k, mode: 'lines+markers' }; }), 'skor', { xtype: 'category', h: 380 });
  }
  function factors(el) {
    el.innerHTML = U.dt('rg-ib', U.T('FR1_indicator_base'), null, { title: 'Risk göstəriciləri bazası (FR1) — tarixi paylanmaya görə: son dəyər, tarixi faiz, z (proqnoz fərziyyəsindən sapma — D5 monitorunda)', file: 'FR1_indicator_base' }) +
      U.dt('rg-tc', U.T('FR1_transmission_channels'), null, { title: 'Ötürmə kanalları (FR1): əmsal, standart xəta, p, n, R², sübut', file: 'FR1_transmission_channels' }) +
      U.dt('rg-ch', U.T('FR1_event_chronology'), null, { title: 'Hadisə xronologiyası (FR1)', file: 'FR1_event_chronology' }) +
      U.dt('rg-hz', U.T('FR1_hazard_parameters'), null, { title: 'Təbii təhlükə parametrləri (FR1)', file: 'FR1_hazard_parameters' }) +
      (U.has('FR2_threshold_sensitivity') ? U.dt('rg-ts', U.T('FR2_threshold_sensitivity'), null, { title: 'Nəticə riskləri (R11–R13): hədd şəbəkəsi üzrə ehtimal və bazanın həddə məsafəsi (FR2_threshold_sensitivity)', file: 'FR2_threshold_sensitivity' }) : '') +
      (U.has('FR2_model_risk') ? U.dt('rg-mr', U.T('FR2_model_risk'), null, { title: 'R19 model riski: köhnəlməmiş konsensus və bazanın fərqi (FR2_model_risk)', file: 'FR2_model_risk' }) : '') +
      (U.has('FR1_fx_transmission') ? U.dt('rg-fx', U.T('FR1_fx_transmission'), null, { title: 'Məzənnə ötürməsi (FR1_fx_transmission): İQİ, qeyri-neft səviyyəsi, xarici borc', file: 'FR1_fx_transmission' }) : '') +
      U.dt('rg-hd', U.T('input_hedler'), null, { title: 'Ehtimal və təsir pillələri, hədlər (input/hedler.csv)', file: 'hedler' }) +
      U.dt('rg-ia', U.T('input_risk_istahi'), null, { title: 'Risk iştahı (input/risk_istahi.csv) — Nazirlik qərarı', file: 'risk_istahi' });
  }
  U.pages.reyestr = function (v, p) {
    if (p[1] && /^R\d+/.test(p[1])) return U.riskPage(v, p[1], p[2]);
    var sub = p[1] || '';
    v.innerHTML = U.head('FR1 · FR2 — risklərin təhlili və prioritetləşdirilməsi', 'Risk reyestri', 'Hər risk üçün ehtimal (P) və təsir (T) birgə Monte Karlo simulyasiyasından və ya işarələnmiş ekspert örtüyündən gəlir; skor = P × T (1–25). Sətrə klikləyin — riskin tam təhlili açılır.') +
      U.subtabs('reyestr', [['', 'Reyestr və istilik xəritəsi'], ['xeberdarliq', 'Xəbərdarlıqlar'], ['tarixce', 'Skor tarixçəsi'], ['amiller', 'Göstəricilər və kanallar']], sub) + '<div id="rg-body"></div>';
    var b = U.$('#rg-body', v);
    if (sub === 'xeberdarliq') b.innerHTML = U.dt('rg-al', U.T('FR2_alerts'), [{ k: 'ciddilik', l: 'Ciddilik', f: U.sigchip }, { k: 'tip', l: 'Növ' }, { k: 'risk_id', l: 'Risk', f: function (v) { return v ? '<a href="#/reyestr/' + v + '">' + v + '</a>' : '—'; } }, { k: 'mesaj', l: 'Mesaj' }, { k: 'as_of', l: 'Tarix' }], { title: 'Bütün xəbərdarlıqlar (FR2_alerts)', file: 'FR2_alerts' });
    else if (sub === 'tarixce') history(b);
    else if (sub === 'amiller') factors(b);
    else main(b);
  };
})();
