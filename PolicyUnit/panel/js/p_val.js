/* p_val.js — Tarixi validasiya (NFR1): historical policy events, predicted vs observed (with intervals), deviations,
   classes and verdicts, methods summary, proposed tolerance rule, IO and microsimulation validation, and the rendered
   deviation report (docs/Sapma_hesabati.md). */
(function () {
  'use strict';
  var U = window.U;
  var SUB = [['', 'Hadisələr və hökmlər'], ['muqayise', 'Proqnoz və fakt'], ['io', 'IO validasiyası'], ['mikrosim', 'Mikrosimulyasiya'], ['hesabat', 'Sapma hesabatı']];
  var CLS = function (c) { return '<span class="chip ' + (/^uyğun$/.test(c) ? 'acc' : /qismən/.test(c) ? 'warn' : /uyğunsuz/.test(c) ? 'bad' : '') + '">' + U.esc(c || '—') + '</span>'; };
  function events(v) {
    var E = U.T('V_nfr1_events'), Mt = U.T('V_nfr1_methods'), T = U.T('V_nfr1_tolerance'), C = U.T('V_nfr1_comparisons');
    v.insertAdjacentHTML('beforeend', '<div class="expl">Model keçmiş siyasət qərarlarına tətbiq olunur və nəticə faktla müqayisə edilir: <b>proqnoz</b> — modelin hadisə üçün hesabladığı təsir, <b>fakt</b> — müşahidə olunan dəyişmə minus əks-faktual (hadisə olmasaydı nə olardı). Sinif: uyğun / qismən uyğun / uyğunsuz / müəyyən deyil (test gücü aşağıdır). «Nümunədaxili» — model həmin dövrün məlumatı ilə qiymətləndirilib (daha yumşaq sınaq).</div>' +
      '<div class="scards">' + E.map(function (e) { var L = C.filter(function (r) { return r.event_id === e.event_id; }); return '<article class="scard"><div class="meta"><span class="chip">' + U.esc(e.event_id) + '</span>' + U.sigchip(e.verdict_az) + '<span>nümunədaxili: ' + U.esc(e.in_sample) + '</span></div><h3>' + U.esc(e.event_name_az) + '</h3><div class="small muted">' + U.esc(e.event_date_az) + '</div>' +
        '<table class="egrid"><tbody><tr><td>Müqayisə sayı</td><td>' + e.n_comparisons + '</td></tr><tr><td>Metodlar</td><td>' + e.n_methods + '</td></tr><tr><td>Uyğun / qismən / uyğunsuz</td><td>' + U.pct(e.share_ok, 0) + ' / ' + U.pct(e.share_part, 0) + ' / ' + U.pct(e.share_fail, 0) + '</td></tr><tr><td>İstiqamət dəqiqliyi</td><td>' + U.pct(e.dir_hit_rate, 0) + '</td></tr><tr><td>Sadə etalondan yaxşı</td><td>' + U.pct(e.beats_naive_rate, 0) + '</td></tr><tr><td>NFR2 (≥ 2 metod)</td><td>' + U.esc(e.nfr2_ok) + '</td></tr></tbody></table>' +
        '<div class="small">' + L.filter(function (r) { return r.primary_method === 1 || r.primary_method === true; }).map(function (r) { return CLS(r.class_az) + ' ' + U.esc(r.label_az); }).join('<br>') + '</div><div class="acts"><a class="btn sm" href="#/validasiya/muqayise?e=' + U.enc(e.event_id) + '">Proqnoz və fakt</a></div></article>'; }).join('') + '</div>' +
      U.sec('Metodlar üzrə', 'bütün hadisələr', U.dt('v-m', Mt, [{ k: 'method_az', l: 'Metod' }, { k: 'n', l: 'Müqayisə', n: 1 }, { k: 'events', l: 'Hadisələr' }, { k: 'share_ok', l: 'Uyğun', p: 1 }, { k: 'dir_hit_rate', l: 'İstiqamət', p: 1 }, { k: 'beats_naive_rate', l: 'Etalondan yaxşı', p: 1 }, { k: 'median_pct_error', l: 'Median xəta, %', n: 1, d: 1 }, { k: 'mean_score', l: 'Orta bal', n: 1, d: 2 }], { title: 'Metodlar', file: 'V_nfr1_methods' })) +
      U.sec('Tolerantlıq qaydası', 'Nazirlik hədd müəyyən etməyib — TƏKLİF', U.dt('v-t', T, null, { title: 'Təklif olunan tolerantlıq', bare: true })) + U.tolSens() + U.sec('Əlavə', 'hadisələr və vintajlar', '' + U.dt('v-e', E, null, { title: 'Hadisələr (tam)', file: 'V_nfr1_events' }) + U.dt('v-rm', U.T('V_nfr1_run_meta'), null, { title: 'İşin metaməlumatı və vintajlar', bare: true })));
  }
  function cmp(v) {
    var C = U.T('V_nfr1_comparisons'), ev = U.uniq(C.map(function (r) { return r.event_id; })), e = U.HQ.get('e') || ev[0], L = C.filter(function (r) { return r.event_id === e; });
    var ev0 = U.T('V_nfr1_events').filter(function (x) { return x.event_id === e; })[0] || {};
    v.insertAdjacentHTML('beforeend', '<div class="toolbar">' + U.seg('v-ev', ev.map(function (x) { var n = (U.T('V_nfr1_events').filter(function (y) { return y.event_id === x; })[0] || {}).event_name_az || x; return [x, x + ' · ' + (n.length > 34 ? n.slice(0, 32) + '…' : n)]; }), e) + '</div>' +
      '<div class="card pad"><h3>' + U.esc(ev0.event_name_az || e) + ' — proqnoz (interval ilə) və fakt</h3><div id="v-ch" class="ch"></div><p class="small muted">Nöqtə — modelin proqnozu (xətt — model intervalı), romb — müşahidə olunan təsir (fakt − əks-faktual).</p></div>' +
      U.dt('v-c', L, [{ k: 'label_az', l: 'Göstərici' }, { k: 'year', l: 'İl', n: 1 }, { k: 'method_az', l: 'Metod' }, { k: 'in_sample', l: 'Nümunədaxili' }, { k: 'pred', l: 'Proqnoz', n: 1, d: 2 }, { k: 'pred_lo', l: 'aşağı', n: 1, d: 2 }, { k: 'pred_hi', l: 'yuxarı', n: 1, d: 2 }, { k: 'obs_effect', l: 'Fakt təsir', n: 1, d: 2 }, { k: 'error', l: 'Sapma', n: 1, d: 2 }, { k: 'pct_error', l: 'Sapma, %', n: 1, d: 0 }, { k: 'dir_hit', l: 'İstiqamət' }, { k: 'beats_naive', l: 'Etalondan yaxşı' }, { k: 'class_az', l: 'Sinif', f: CLS }, { k: 'note_az', l: 'Qeyd' }], { title: 'Proqnoz və fakt — ' + e, file: 'sapma_' + e }) +
      U.sec('Müşahidə olunan təsirlər', 'əks-faktual qaydası və mənbə', U.dt('v-o', U.T('V_nfr1_observed').filter(function (r) { return r.event_id === e; }), [{ k: 'label_az', l: 'Göstərici' }, { k: 'year', l: 'İl', n: 1 }, { k: 'obs_raw', l: 'Fakt', n: 1, d: 2 }, { k: 'cf', l: 'Əks-faktual', n: 1, d: 2 }, { k: 'obs_effect', l: 'Təsir', n: 1, d: 2 }, { k: 'obs_effect_alt', l: 'Alternativ', n: 1, d: 2 }, { k: 'sigma_cf', l: 'σ', n: 1, d: 2 }, { k: 'cf_rule', l: 'Qayda' }, { k: 'obs_source', l: 'Mənbə' }, { k: 'obs_note_az', l: 'Qeyd' }], { title: 'Müşahidə olunan təsirlər', file: 'V_nfr1_observed' })));
    var lab = L.map(function (r) { return r.label_az.slice(0, 40) + ' · ' + (r.method_az || '').split(' (')[0].slice(0, 30); });
    U.plot(U.$('#v-ch', v), [{ type: 'scatter', mode: 'markers', name: 'proqnoz', y: lab, x: L.map(function (r) { return r.pred; }), error_x: { type: 'data', symmetric: false, array: L.map(function (r) { return U.isNum(r.pred_hi) ? r.pred_hi - r.pred : 0; }), arrayminus: L.map(function (r) { return U.isNum(r.pred_lo) ? r.pred - r.pred_lo : 0; }), color: '#0E6F7C' }, marker: { size: 9, color: '#0E6F7C' }, orientation: 'h' },
      { type: 'scatter', mode: 'markers', name: 'fakt', y: lab, x: L.map(function (r) { return r.obs_effect; }), marker: { size: 11, symbol: 'diamond', color: '#E07B00' } }],
      Object.assign(U.layout('', { h: Math.max(300, 30 * L.length + 90), hm: 'closest' }), { yaxis: { autorange: 'reversed', automargin: true, tickfont: { size: 10.5 } }, xaxis: { zeroline: true, zerolinecolor: '#9AA6B2', title: { text: 'təsir (göstəricinin vahidində)' } } }));
    U.$('#v-ev', v).onclick = function (x) { var b = x.target.closest('[data-v]'); if (b) location.hash = '#/validasiya/muqayise?e=' + U.enc(b.getAttribute('data-v')); };
  }
  function io(v) {
    var S = U.T('V_io_stability_summary');
    v.insertAdjacentHTML('beforeend', '<div class="expl"><b>IO validasiyası</b>: (1) E7 — 30.06.2024 yanacaq və tarif paketi: IO qiymət modelinin İQİ maddələri üzrə nəticəsi DSK faktı ilə; (2) əmsalların sabitliyi — köhnə cədvəllə sonrakı ilin sektor buraxılışının geriyə proqnozu, sadə etalonla müqayisə.</div>' +
      U.dt('vi-e7', U.T('V_io_e7_fuel_2024'), null, { title: 'E7: IO qiymət modeli və DSK İQİ', file: 'V_io_e7_fuel_2024' }) + U.dt('vi-e7s', U.T('V_io_e7_sectors'), null, { title: 'E7: sektor qiymətləri', file: 'V_io_e7_sectors', lim: 30 }) + U.dt('vi-e7x', U.T('V_io_e7_sensitivity'), null, { title: 'E7: həssaslıq', bare: true }) +
      '<div class="cols2"><div>' + U.dt('vi-ss', S, null, { title: 'Sabitlik testi xülasəsi', bare: true }) + '</div><div class="card pad"><div id="vi-ch" class="ch"></div></div></div>' + U.dt('vi-st', U.T('V_io_stability'), null, { title: 'Sabitlik testi: sektorlar', file: 'V_io_stability', lim: 50 }));
    U.bars(U.$('#vi-ch', v), S.map(function (r) { return r.pair; }), [{ name: 'IO çəkili MAPE, %', y: S.map(function (r) { return r.io_wmape; }), c: '#0E6F7C' }, { name: 'sadə etalon, %', y: S.map(function (r) { return r.naive_wmape; }), c: '#E07B00' }], 'çəkili MAPE, %', { cat: true, h: 280 });
  }
  function ms(v) {
    v.insertAdjacentHTML('beforeend', U.SYN + U.dt('vm-s', U.T('V_microsim_summary'), null, { title: 'Mikrosimulyasiya sapma xülasəsi', bare: true }) + U.dt('vm-19', U.T('V_microsim_2019_package'), null, { title: '2019 sosial paketi + vergi islahatı (E1+E2)', file: 'V_microsim_2019_package' }) +
      U.dt('vm-25', U.T('V_microsim_2025_minwage'), null, { title: '2025 minimum əmək haqqı 345 → 400 AZN: maaş intervalları', file: 'V_microsim_2025_minwage' }) +
      U.dt('vm-c18', U.T('V_microsim_calibration_2018'), null, { title: 'Kalibrləmə uyğunluğu 2018 (nümunədaxili)', file: 'V_microsim_calibration_2018', lim: 40 }) + U.dt('vm-c24', U.T('V_microsim_calibration_2024'), null, { title: 'Kalibrləmə uyğunluğu 2024 (nümunədaxili)', file: 'V_microsim_calibration_2024', lim: 40 }));
  }
  function report(v) {
    U.need(['docs'], v, function () { var d = ((window.POL.docs || {}).docs || []).filter(function (x) { return x.slug === 'Sapma_hesabati'; })[0];
      v.innerHTML = d ? '<div class="toolbar"><a class="btn sm" href="../docs/Sapma_hesabati.md" download>Mənbə faylı (.md)</a><button class="btn sm" id="vr-p">Çap / PDF</button></div><div class="card docbody">' + d.html + '</div>' : U.empty('Sapma hesabatı (docs/Sapma_hesabati.md)');
      var p = U.$('#vr-p', v); if (p) p.onclick = function () { window.print(); }; });
  }
  U.pages.validasiya = function (v, p) {
    var sub = p[1] || '';
    v.innerHTML = U.head('NFR1 — retrospektiv validasiya', 'Tarixi validasiya', 'Model keçmiş siyasət hadisələrində necə işləyib: proqnoz və fakt, sapmalar, hökmlər və sapma hesabatı.') + U.subtabs('validasiya', SUB, sub) + '<div id="v-body"></div>';
    var b = U.$('#v-body', v);
    U.need(['val'], b, function () { if (sub === 'muqayise') cmp(b); else if (sub === 'io') io(b); else if (sub === 'mikrosim') ms(b); else if (sub === 'hesabat') report(b); else events(b); });
  };
})();
