/* p_home2.js — «Bu gün», part 2: what changed (D7 + scores), today's data → forecasts (D6 headline), signals (D5),
   baseline vs live distribution, balance of risks (C2), the daily decision table (S7), quick links; data refresh job. */
(function () {
  'use strict';
  var U = window.U, H = U.H;
  function changes() {
    var pv = U.prevScores(), sc = U.T('FR2_risk_scores'), rows = [];
    sc.forEach(function (r) { var p = pv.by[r.risk_id]; if (!p || p.skor !== r.skor || Math.abs(p.ehtimal - r.ehtimal) > 0.02) rows.push({ risk_id: r.risk_id, ad: r.ad, evvel: p ? p.skor : null, indi: r.skor, pe: p ? p.ehtimal : null, pi: r.ehtimal }); });
    rows.sort(function (a, b) { return Math.abs((b.indi - (b.evvel || 0))) - Math.abs((a.indi - (a.evvel || 0))); });
    var d7 = U.T('D7_changes');
    return '<div class="cols2"><div>' + U.dt('h-sc', rows, [{ k: 'risk_id', l: 'Risk', f: function (v) { return '<a href="#/reyestr/' + v + '"><b>' + v + '</b></a>'; } }, { k: 'ad', l: 'Ad' },
      { k: 'evvel', l: 'Skor (əvvəl)', n: 1, d: 0 }, { k: 'indi', l: 'Skor (indi)', n: 1, f: function (v, r) { return U.score(v) + (r.evvel != null ? ' <span class="small ' + (v > r.evvel ? 'down' : v < r.evvel ? 'up' : 'muted') + '">' + U.sg(v - r.evvel, 0) + '</span>' : ' <span class="chip">yeni</span>'); } },
      { k: 'pe', l: 'Ehtimal (əvvəl)', n: 1, p: 1 }, { k: 'pi', l: 'Ehtimal (indi)', n: 1, p: 1 }], { title: 'Skor dəyişmələri: ' + (pv.date || '—') + ' → ' + U.META.stamp.as_of, file: 'skor_deyismeleri', bare: false }) + '</div><div>' +
      U.dt('h-d7', d7, [{ k: 'item', l: 'Axın' }, { k: 'label_az', l: 'Dəyişiklik' }, { k: 'previous', l: 'Əvvəlki müşahidə sayı', n: 1, d: 0 }, { k: 'previous_date', l: 'Əvvəlki son tarix' }, { k: 'latest', l: 'İndi', n: 1, d: 0 }, { k: 'date', l: 'Son tarix' }, { k: 'change', l: 'Yeni müşahidə', n: 1, d: 0 }],
        { title: 'Yeni məlumat vintajları (D7)', file: 'D7_changes' }) + '</div></div>';
  }
  H.d6cols = [{ k: 'driver', l: 'Amil' }, { k: 'label_az', l: 'Proqnoz göstəricisi' }, { k: 'unit', l: 'Vahid' }, { k: 'year', l: 'İl', n: 1, d: 0 }, { k: 'baseline', l: 'Rəsmi baza', n: 1 }, { k: 'implied', l: 'Bugünkü məlumatla', n: 1 },
    { k: 'delta', l: 'Fərq', n: 1, f: function (v) { return '<b class="' + (v > 0 ? 'up' : v < 0 ? 'down' : '') + '">' + U.sg(v, Math.abs(v) >= 100 ? 0 : 2) + '</b>'; } }, { k: 'delta_pct', l: 'Fərq, %', n: 1, f: function (v) { return U.sg(v, 2); } }, { k: 'channel', l: 'Ötürmə kanalı' }, { k: 'scenario_note', l: 'Şərt' }];
  function impact(el) {
    var h = U.T('D6_headline'), y0 = +String(U.META.stamp.as_of).slice(0, 4);
    var chain = h.filter(function (r) { return /zənciri/.test(r.channel) && r.year === y0 + 1 && r.driver === 'brent' && r.target_id !== 'fr1:balance_n'; });
    el.innerHTML = '<div class="note-b">Bugünkü bazar və statistika məlumatı (məs. Brent spot, uçot dərəcəsi, DSK-nın Yanvar–ay göstəriciləri) rəsmi bazanın fərziyyəsindən fərqlənir. Bu fərq MikroUnit zənciri (FR1 → FR12), FR1 multiplikatorları, OxLon elastiklikləri və müşahidə hesabı ilə proqnozlara ötürülür. <b>Bu, şərti hesablamadır, yeni proqnoz deyil.</b></div>' +
      '<div class="card pad"><h3>Brent sapmasının ' + (y0 + 1) + ' üzrə təsiri (MikroUnit zənciri, bazadan %)</h3><div id="h-d6c" class="ch"></div></div>' +
      U.dt('h-d6', h.filter(function (r) { return r.year <= y0 + 1; }), H.d6cols, { title: 'Başlıq göstəriciləri (' + y0 + '–' + (y0 + 1) + ')', file: 'D6_basliq', lim: 40, note: 'Bütün 1 300-dən çox komponent üzrə tam cədvəl: <a href="#/monitor/tesir">Monitor → Proqnoz təsiri</a>. Büdcə balansının nisbi dəyişməsi kiçik bazaya görə qrafikdə göstərilmir (cədvəldədir).' });
    U.barH(U.$('#h-d6c', el), chain.map(function (r) { return r.label_az; }), chain.map(function (r) { return r.delta_pct; }), 'bazadan fərq, %', { color: chain.map(function (r) { return r.delta_pct >= 0 ? '#1E7B4F' : '#B3261E'; }) });
  }
  function signals() {
    var d5 = U.T('D5_daily_monitor').filter(function (r) { return !/normal/.test(r.signal || ''); }).sort(function (a, b) { return Math.abs(b.z_score) - Math.abs(a.z_score); });
    return U.dt('h-d5', d5, [{ k: 'label_az', l: 'Göstərici' }, { k: 'latest', l: 'Son dəyər', n: 1 }, { k: 'unit', l: 'Vahid' }, { k: 'date', l: 'Tarix' }, { k: 'baseline_source', l: 'Müqayisə bazası' }, { k: 'baseline_assumption', l: 'Baza fərziyyəsi', n: 1 },
      { k: 'z_score', l: 'z-skor', n: 1, d: 2 }, { k: 'signal', l: 'Siqnal', f: U.sigchip }], { title: 'Normal olmayan siqnallar (D5) — ' + d5.length, file: 'D5_siqnallar', lim: 12, href: function () { return '#/monitor/siqnal'; } });
  }
  function views(el) {
    var y0 = +String(U.META.stamp.as_of).slice(0, 4), B = U.T('FR2_distribution'), L = U.T('FR2_distribution_live'), rows = [];
    ['g', 'cpi', 'fis', 'brent'].forEach(function (g) { [y0, y0 + 1].forEach(function (y) {
      var b = B.filter(function (r) { return r.gosterici === g && r.il === y; })[0], l = L.filter(function (r) { return r.gosterici === g && r.il === y; })[0]; if (!b || !l) return;
      rows.push({ g: b.ad, v: b.vahid, il: y, baza: b.baza, bm: b.p50, b5: b.p05, b95: b.p95, lm: l.p50, l5: l.p05, l95: l.p95 }); }); });
    el.innerHTML = '<div class="card pad"><h3>Qeyri-neft ÜDM-in real artımı, % — ' + U.VIEWN[U.view()] + ' baxış (zolaqlar) və digər baxış (xətlər)</h3><div id="h-fan" class="ch"></div></div>' +
      U.dt('h-vw', rows, [{ k: 'g', l: 'Göstərici' }, { k: 'v', l: 'Vahid' }, { k: 'il', l: 'İl', n: 1, d: 0 }, { k: 'baza', l: 'Rəsmi baza', n: 1, d: 2 }, { k: 'bm', l: 'Baza mərkəzli: median', n: 1, d: 2 }, { k: 'b5', l: 'P5', n: 1, d: 2 }, { k: 'b95', l: 'P95', n: 1, d: 2 },
        { k: 'lm', l: 'Canlı: median', n: 1, d: 2 }, { k: 'l5', l: 'Canlı P5', n: 1, d: 2 }, { k: 'l95', l: 'Canlı P95', n: 1, d: 2 }], { title: 'İki baxış: baza mərkəzli və canlı şərtləndirilmiş', file: 'baxislar', href: function () { return '#/paylanma'; } });
    var cur = U.view() === 'live' ? L : B, oth = U.view() === 'live' ? B : L;
    U.fan(U.$('#h-fan', el), cur.filter(function (r) { return r.gosterici === 'g'; }), { live: oth.filter(function (r) { return r.gosterici === 'g'; }), yt: '%', hline: 2, hlab: 'GaR həddi 2 %' });
  }
  function bori(el) {
    var t = U.boriIndex(), by = U.by(t, 'version');
    el.innerHTML = '<div class="card pad"><h3>Risk balansı indeksi (0–100): Nazirlik vs məlumat əsaslı</h3><div id="h-c2" class="ch"></div><p class="small muted">&lt; 45 — risklər müsbət nəticələrə meyllidir; 45–55 — balanslaşdırılıb; &gt; 55 — mənfi nəticələrə meyllidir. Ətraflı: <a href="#/caem/balans">CAEM → Risk balansı</a>.</p></div>' +
      U.dt('h-s7', U.T('S7_daily_decision').slice(0, 8), [{ k: 'sira', l: '№', n: 1, d: 0 }, { k: 'amil_ad', l: 'Amil' }, { k: 'canli_sapma', l: 'Bugünkü sapma' }, { k: 'sigma_sapma', l: 'σ', n: 1, d: 2 }, { k: 'tesir_novu', l: 'Təsirin növü' },
        { k: 'qeyri_neft_seviyye_2027_pct', l: 'Qeyri-neft ÜDM 2027, %', n: 1, d: 3 }, { k: 'inflyasiya_2027_fb', l: 'İnflyasiya 2027, f.b.', n: 1, d: 3 }, { k: 'teklif_olunan_tedbirler', l: 'Təklif olunan tədbirlər' }],
        { title: 'Gündəlik qərar cədvəli (S7) — bu gün nəyə baxmalı', file: 'S7_daily_decision', href: function () { return '#/tedbir/qerar'; } });
    U.lines(U.$('#h-c2', el), Object.keys(by).map(function (k, i) { var r = by[k].sort(function (a, b) { return a.year - b.year; }); return { x: r.map(function (q) { return q.year; }), y: r.map(function (q) { return q.weighted; }), name: k, c: i ? '#0E6F7C' : '#E07B00', mode: 'lines+markers', dash: i ? 'solid' : 'dash' }; })
      .concat([{ x: [2021.5, 2030.5], y: [45, 45], name: 'balans zolağı', c: '#9AA6B2', dash: 'dot', w: 1, mode: 'lines' }, { x: [2021.5, 2030.5], y: [55, 55], name: '55', c: '#9AA6B2', dash: 'dot', w: 1, mode: 'lines', showlegend: false }]), 'indeks', { years: true, yr: [0, 100] });
  }
  function action(href, ic, t, p, go) { return '<a class="card action" href="' + href + '"><span class="ic">' + U.icon(ic) + '</span><h3>' + t + '</h3><p>' + p + '</p><span class="go">' + go + ' →</span></a>'; }
  H.more = function (el) {
    el.innerHTML = U.sec('Dünəndən nə dəyişdi', 'əvvəlki hesablama ilə müqayisə: risk skorları və yeni məlumat vintajları', changes()) +
      U.sec('Bugünkü məlumat rəsmi proqnozları necə dəyişir', 'göstərici → proqnoz təsiri (D6)', '<div id="h-imp"></div>') +
      U.sec('Siqnallar', 'proqnoz fərziyyəsinə görə: son müşahidə vs bölmələrin baza fərziyyələri; |z| ≥ 1 — diqqət, ≥ 2 — xəbərdarlıq (tarixi paylanmaya görə vəziyyət — FR1 bazasında)', signals()) +
      U.sec('Paylanma: baza mərkəzli və canlı', 'yuxarıdakı «Baxış» düyməsi ilə dəyişin', '<div id="h-vw"></div>') +
      U.sec('Risk balansı və gündəlik qərar', '', '<div id="h-bo"></div>') +
      U.sec('Nə etmək istəyirsiniz?', '', '<div class="grid g4">' +
        action('#/reyestr', 'list', 'Riski təhlil etmək', 'Ehtimal, təsir, ötürmə kanalı, təsirlənən dəyişənlər, tədbirlər və qalıq risk — hər risk üçün bir səhifə.', 'Reyestr') +
        action('#/stress/qurucu', 'bolt', 'Stress testi qurmaq', 'Amil şoklarını seçin (məs. neft −2σ + devalvasiya) — MikroUnit zənciri və RU simulyasiyası ilə hesablanır.', 'Ssenari qurucusu') +
        action('#/tedbir/portfel', 'tool', 'Tədbir portfeli seçmək', 'Büdcəni dəyişin — səmərəli sərhəd üzrə optimal tədbirlər və qalıq risk.', 'Optimallaşdırıcı') +
        action('#/hesabat', 'doc', 'Hesabat hazırlamaq', '«Rəhbərlik üçün gündəlik xülasə» və ya «Analitik hesabat»: PDF, Excel, Word, CSV.', 'Hesabat qurucusu') + '</div>');
    impact(U.$('#h-imp', el)); views(U.$('#h-vw', el)); bori(U.$('#h-bo', el));
  };
  H.refresh = function (el) {
    U.API.refresh('daily').then(function (j) {
      el.innerHTML = '<p class="small">Yeniləmə başladı (' + U.esc(j.id) + ') — mərhələlər icra olunur…</p>';
      var poll = function () { U.API.job(j.id).then(function (s) {
        var p = s.progress || {};
        el.innerHTML = '<p class="small"><b>' + U.esc(s.status_az || s.status) + '</b> · ' + U.esc(p.name || '') + (U.isNum(p.pct) ? ' · ' + U.nf(p.pct, 0) + ' %' : '') + '</p>';
        if (s.status === 'running' || s.status === 'queued') setTimeout(poll, 3000);
        else if (s.status === 'ok') el.innerHTML += '<p class="small up">Hazırdır — yeni məlumat <code>output/</code> qovluğuna yazıldı. Paneldə görünməsi üçün məlumat paketləri yenidən yığılmalıdır: tam (səhər) dövrü bunu avtomatik edir; indi görmək üçün <code>python3 panel/build_panel.py</code> əmrini işə salın, sonra səhifəni yeniləyin. <button type="button" class="btn sm" onclick="location.reload()">Səhifəni yenilə</button></p>';
        else el.innerHTML += '<p class="small down">Yeniləmə uğurla bitmədi — son uğurlu nəticələr qalır. Ətraflı: «İcra jurnalı» və <code>logs/api/</code>.</p>';
      }, function (e) { el.innerHTML = '<p class="small down">' + U.esc(e.message) + '</p>'; }); };
      setTimeout(poll, 2000);
    }, function (e) { el.innerHTML = U.API.failHtml('Məlumatın yenilənməsi', e); });
  };
})();
