/* p_mon.js — Monitor: every automatic feed (D2 status / freshness, vintage archive), daily signals with z-scores (D5),
   consensus across units and model risk (D3). Market panel (D4, V2) and the full forecast-impact table (D6): p_mon2.js. */
(function () {
  'use strict';
  var U = window.U;
  U.MON = {};
  function feeds(el) {
    var d2 = U.T('D2_feed_status'), cnt = U.by(d2.map(function (r) { return { t: r.tazelik == null || r.tazelik === '' ? 'bazar sırası (yaş hədd yoxdur)' : r.tazelik }; }), 't'), st = U.by(d2, 'status');
    el.innerHTML = '<div class="tiles">' + Object.keys(cnt).map(function (k) { return U.tile('Təzəlik: ' + U.esc(k), U.nf(cnt[k].length, 0) + '<small>axın</small>', '', k === 'təzə' ? 'ok' : k === 'köhnə' ? 'bad' : 'warn'); }).join('') +
      Object.keys(st).map(function (k) { return U.tile('Son yükləmə: ' + U.esc(k), U.nf(st[k].length, 0) + '<small>axın</small>', /xeta/.test(k) ? 'son uğurlu vintaj istifadə olunur' : '', /xeta/.test(k) ? 'warn' : 'ok'); }).join('') + '</div>' +
      '<div class="toolbar"><button class="btn sm pri" id="mn-ref">' + U.icon('play', 14) + ' Axınları indi yenilə (gündəlik dövr)</button><span class="small muted">Server lazımdır; yeniləmə fonda gedir (≈ 1–6 dəq.), sonra paneli yenidən yığın (tam dövr bunu avtomatik edir) və səhifəni yeniləyin.</span></div><div id="mn-job"></div>' +
      U.dt('mn-d2', d2, [{ k: 'feed', l: 'Axın' }, { k: 'source', l: 'Mənbə' }, { k: 'tezlik', l: 'Tezlik' }, { k: 'esas_sira', l: 'Əsas sıra' }, { k: 'son_deyer', l: 'Son dəyər', n: 1 }, { k: 'vahid', l: 'Vahid' }, { k: 'last_obs', l: 'Son müşahidə' },
        { k: 'yas_gun', l: 'Yaş, gün', n: 1, d: 0 }, { k: 'tazelik', l: 'Təzəlik', f: U.sigchip }, { k: 'status', l: 'Status', f: U.sigchip }, { k: 'n_obs', l: 'Müşahidə', n: 1, d: 0 }, { k: 'retrieved_utc', l: 'Yükləndi (UTC)' },
        { k: 'url', l: 'Ünvan', f: function (v) { return v && /^https?:/.test(v) && v.indexOf('*') < 0 && v.indexOf('YYYY') < 0 ? '<a href="' + U.esc(v) + '" target="_blank" rel="noopener">mənbə</a>' : '<span class="small muted">' + U.esc(v || '') + '</span>'; } }, { k: 'note', l: 'Qeyd' }],
        { title: 'Avtomatik məlumat axınları (D2) — ' + d2.length, file: 'D2_feed_status', sort: ['tazelik', 1] }) +
      U.dt('mn-vm', U.T('vintages_manifest'), null, { title: 'Vintaj arxivi (data/vintages/manifest.csv): hər yükləmə, SHA-256 ilə', file: 'vintaj_arxivi', lim: 60 }) +
      U.dt('mn-n2', U.T('NFR2_update_log'), null, { title: 'NFR2 yeniləmə jurnalı: tətik, dəyişən girişlər, müddət, SLA', file: 'NFR2_update_log' });
    U.$('#mn-ref', el).onclick = function () { U.H.refresh(U.$('#mn-job', el)); };
  }
  function signals(el) {
    var d5 = U.T('D5_daily_monitor'), ind = U.uniq(d5.map(function (r) { return r.indicator; }));
    var best = ind.map(function (k) { var rs = d5.filter(function (r) { return r.indicator === k; }); return rs.sort(function (a, b) { return Math.abs(b.z_score) - Math.abs(a.z_score); })[0]; });
    el.innerHTML = '<div class="note-b">Hər göstəricinin son müşahidəsi bölmələrin (OxLon, MikroUnit FR1, Nazirlik CAEM, Bottom-up, BVF) baza fərziyyəsi ilə müqayisə olunur. z = sapma / σ (σ-nın əsası cədvəldədir). |z| ≥ 1 — diqqət, |z| ≥ 2 — xəbərdarlıq.</div>' +
      '<div class="card pad"><h3>z-skorlar — hər göstərici üzrə ən böyük sapma</h3><div id="mn-z" class="ch"></div></div>' +
      U.dt('mn-d5', d5, [{ k: 'label_az', l: 'Göstərici' }, { k: 'latest', l: 'Son dəyər', n: 1 }, { k: 'unit', l: 'Vahid' }, { k: 'date', l: 'Tarix' }, { k: 'baseline_source', l: 'Baza mənbəyi' }, { k: 'baseline_year', l: 'İl', n: 1, d: 0 },
        { k: 'baseline_assumption', l: 'Baza fərziyyəsi', n: 1 }, { k: 'deviation', l: 'Sapma', n: 1 }, { k: 'deviation_pct', l: 'Sapma, %', n: 1, d: 1 }, { k: 'sigma', l: 'σ', n: 1 }, { k: 'z_score', l: 'z-skor', n: 1, d: 2 }, { k: 'z_basis', l: 'σ-nın əsası' }, { k: 'signal', l: 'Siqnal (proqnoz fərziyyəsinə görə)', f: U.sigchip }, { k: 'note', l: 'Qeyd' }, { k: 'istinad', l: 'İstinad' }],
        { title: 'Gündəlik monitor (D5) — bütün sətirlər, proqnoz fərziyyəsinə görə (ikitərəfli: |z| ≥ 1 diqqət, ≥ 2 xəbərdarlıq)', file: 'D5_daily_monitor' });
    best.sort(function (a, b) { return a.z_score - b.z_score; });
    U.barH(U.$('#mn-z', el), best.map(function (r) { return r.label_az + ' (' + r.baseline_source + ')'; }), best.map(function (r) { return r.z_score; }), 'z-skor', { color: best.map(function (r) { return Math.abs(r.z_score) >= 2 ? '#B3261E' : Math.abs(r.z_score) >= 1 ? '#E0A100' : '#9AA6B2'; }) });
  }
  var SRC = [['v_oxlon', 'OxLon'], ['v_caem', 'CAEM'], ['v_bu60', 'Bottom-up'], ['v_v8', '8 vərəq'], ['v_fr1', 'MikroUnit FR1'], ['v_imf', 'BVF'], ['v_mspec', 'Nazirlik spes.']];
  function consensus(el) {
    var b = U.T('D3_consensus_baselines'), vars = U.uniq(b.map(function (r) { return r.variable; })), cur = U.MON.cv || vars[1] || vars[0];
    el.innerHTML = '<div class="note-b">Eyni göstərici üçün bölmələrin baza proqnozları nə qədər fərqlənir? Böyük fikir ayrılığı model riskidir (R19). Bayraqlar: qeyri-real, köhnəlmiş (əvvəlki vintaj), kənar dəyər — bayraqlı mənbələr «təmiz» göstəricilərə daxil edilmir.</div>' +
      '<div class="toolbar">' + U.sel('mn-cv', vars.map(function (v) { var r = b.filter(function (x) { return x.variable === v; })[0]; return [v, r.label_az + ' (' + r.unit + ')']; }), cur) + '</div>' +
      '<div class="card pad"><h3 id="mn-ct"></h3><div id="mn-cc" class="ch"></div></div>' +
      U.dt('mn-mr', U.T('D3_model_risk'), null, { title: 'Model riski göstəricisi (D3) — R19 üçün', file: 'D3_model_risk' }) +
      U.dt('mn-cb', b, null, { title: 'Bölmələrarası baza proqnozları (D3) — bütün sütunlar', file: 'D3_consensus_baselines' }) +
      U.dt('mn-cl', U.T('D3_consensus_long'), null, { title: 'D3 uzun forma: mənbə, növ, bayraq və səbəb', file: 'D3_consensus_long' });
    var draw = function (v) {
      var rs = b.filter(function (r) { return r.variable === v; }).sort(function (a, c) { return a.year - c.year; });
      U.$('#mn-ct', el).textContent = rs[0].label_az + ' (' + rs[0].unit + ') — mənbələr üzrə';
      U.lines(U.$('#mn-cc', el), SRC.filter(function (s) { return rs.some(function (r) { return U.isNum(r[s[0]]); }); }).map(function (s, i) { return { x: rs.map(function (r) { return r.year; }), y: rs.map(function (r) { return r[s[0]]; }), name: s[1], mode: 'lines+markers', c: U.PAL[i] }; })
        .concat([{ x: rs.map(function (r) { return r.year; }), y: rs.map(function (r) { return r.disagreement_index; }), name: 'fikir ayrılığı indeksi', y2: true, dash: 'dot', c: '#9AA6B2', mode: 'lines' }]), rs[0].unit, { years: true, y2: 'indeks' });
    };
    draw(cur);
    U.$('#mn-cv', el).onchange = function (e) { U.MON.cv = e.target.value; draw(e.target.value); };
  }
  U.pages.monitor = function (v, p) {
    var sub = p[1] || '';
    v.innerHTML = U.head('NFR2 — avtomatik məlumat toplama və gündəlik monitor', 'Monitor', 'Bütün avtomatik məlumat axınları (AMB, DSK, Maliyyə Nazirliyi, ARDNF, BFB, FRED, GPR, EPU, USGS, ERA5), bazar paneli, gündəlik siqnallar, bugünkü məlumatın proqnozlara təsiri və bölmələrarası konsensus.') +
      U.subtabs('monitor', [['', 'Axınlar'], ['bazar', 'Bazar paneli'], ['siqnal', 'Siqnallar (D5)'], ['tesir', 'Proqnoz təsiri (D6)'], ['konsensus', 'Konsensus və model riski (D3)']], sub) + '<div id="mn-body"></div>';
    var b = U.$('#mn-body', v);
    if (sub === 'bazar') U.MON.market(b); else if (sub === 'siqnal') signals(b); else if (sub === 'tesir') U.MON.impact(b); else if (sub === 'konsensus') consensus(b); else feeds(b);
  };
})();
