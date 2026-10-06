/* p_home.js — Başlanğıc «Bu gün»: plain-language intro, headline tiles, top risks, new alerts, what changed since the
   previous run (D7 + score history), today's data → official forecasts (D6), baseline vs live distribution, balance of
   risks (C2) and quick links. Part 2 (sections) in p_home2.js. */
(function () {
  'use strict';
  var U = window.U;
  U.H = {};
  U.prevScores = function () {
    var h = U.T('FR2_score_history'), dates = U.uniq(h.map(function (r) { return r.as_of; })).sort();
    var cur = U.META.stamp.as_of, prev = dates.filter(function (d) { return d < cur; }).pop(), o = {};
    h.filter(function (r) { return r.as_of === prev; }).forEach(function (r) { o[r.risk_id] = r; });
    return { date: prev, by: o };
  };
  U.boriIndex = function (version) {
    return U.T('C2_balance_of_risks').filter(function (r) { return r.category === 'CƏMİ' && (!version || r.version === version); });
  };
  function tile(l, v, s, cls, href) {
    return '<' + (href ? 'a href="' + href + '"' : 'div') + ' class="tile ' + (cls || '') + '"><span class="l">' + l + '</span><span class="v">' + v + '</span>' + (s ? '<span class="s">' + s + '</span>' : '') + '</' + (href ? 'a' : 'div') + '>';
  }
  U.tile = tile;
  function tiles() {
    var sc = U.T('FR2_risk_scores'), hi = sc.filter(function (r) { return r.prioritet === 'yüksək'; }), al = U.T('FR2_alerts');
    var nh = al.filter(function (a) { return a.ciddilik === 'yüksək'; }).length;
    var d2 = U.T('D2_feed_status'), fresh = d2.filter(function (r) { return r.tazelik === 'təzə'; }).length, err = d2.filter(function (r) { return /xeta|xəta/.test(r.status || ''); }).length;
    var bi = U.boriIndex('məlumat əsaslı (RU)'), y0 = +String(U.META.stamp.as_of).slice(0, 4), bcur = bi.filter(function (r) { return r.year === y0; })[0] || bi[bi.length - 1];
    var dist = U.T('FR2_distribution').filter(function (r) { return r.gosterici === 'g' && r.il === y0 + 1; })[0] || {};
    var b5 = U.T('D5_daily_monitor').filter(function (r) { return r.indicator === 'brent_spot'; })[0] || {};
    var k1 = U.T('K1_at_risk_summary').filter(function (r) { return r.gosterici === 'CaR' || /CaR/.test(r.gosterici); })[0];
    return '<div class="tiles" data-tour="today">' +
      tile('Yüksək prioritetli risklər', U.nf(hi.length, 0) + '<small>/ ' + sc.length + '</small>', hi.map(function (r) { return r.risk_id; }).join(', '), hi.length ? 'bad' : 'ok', '#/reyestr') +
      tile('Xəbərdarlıqlar', U.nf(al.length, 0), nh + ' yüksək ciddilikli', nh ? 'warn' : 'ok', '#/reyestr/xeberdarliq') +
      tile('Risk balansı indeksi ' + (bcur ? bcur.year : ''), bcur ? U.nf(bcur.weighted, 1) + '<small>/ 100</small>' : '—', bcur ? U.esc(bcur.read_off_az || '') : '', bcur && bcur.weighted > 55 ? 'bad' : bcur && bcur.weighted < 45 ? 'ok' : 'warn', '#/caem/balans') +
      tile('Qeyri-neft artımı ' + (y0 + 1) + ': GaR 5 %', U.nf(dist.p05, 2) + '<small>%</small>', 'median ' + U.nf(dist.p50, 2) + ' % · baza ' + U.nf(dist.baza, 2) + ' %', dist.p05 < 2 ? 'warn' : 'ok', '#/paylanma') +
      tile('Brent (spot)', U.nf(b5.latest, 2) + '<small>USD</small>', b5.date ? b5.date + ' · baza fərziyyəsi ' + U.nf(b5.baseline_assumption, 1) + ' (z = ' + U.nf(b5.z_score, 1) + ')' : '', /xəbərdarlıq/.test(b5.signal || '') ? 'bad' : /diqqət/.test(b5.signal || '') ? 'warn' : 'ok', '#/monitor/siqnal') +
      tile('Məlumat axınları', fresh + '<small>/ ' + d2.length + ' təzə</small>', err ? err + ' axında son yükləmə xətası — son yaxşı vintaj istifadə olunur' : 'hamısı uğurla yükləndi', err ? 'warn' : 'ok', '#/monitor') +
      (k1 ? tile('Fiskal kapitala risk (CaR 95 %)', U.nf(k1.risk_altinda, 0) + '<small>' + U.esc(k1.vahid) + '</small>', k1.il + ' · ' + U.esc(k1.ad), '', '#/var/car') : '') + '</div>';
  }
  function topRisks() {
    var sc = U.T('FR2_risk_scores').slice().sort(function (a, b) { return b.skor - a.skor || b.ehtimal - a.ehtimal; }).slice(0, 6), pv = U.prevScores();
    return '<div class="card">' + sc.map(function (r) {
      var p = pv.by[r.risk_id], d = p ? r.skor - p.skor : null;
      return '<a class="arow" href="#/reyestr/' + r.risk_id + '"><span>' + U.fam(r.aile) + '</span><span><b>' + r.risk_id + '</b> ' + U.esc(r.ad) + '<br><span class="small muted">ehtimal ' + U.pct(r.ehtimal) + ' · P ' + r.P_bal + ' × T ' + r.I_bal + ' · ölçü: ' + U.esc(r.I_olcu) + '</span></span>' +
        '<span style="text-align:right">' + U.score(r.skor) + ' ' + U.prio(r.prioritet) + '<br><span class="small ' + (d > 0 ? 'down' : d < 0 ? 'up' : 'muted') + '">' + (d == null ? 'yeni' : d ? (d > 0 ? '↑ ' : '↓ ') + U.sg(d, 0) : 'dəyişməyib') + '</span></span></a>';
    }).join('') + '<div class="arow"><span></span><a href="#/reyestr">Bütün 19 risk və istilik xəritəsi →</a><span></span></div></div>';
  }
  function alerts() {
    var al = U.T('FR2_alerts'), ord = { 'yüksək': 0, 'orta': 1, 'aşağı': 2 };
    al = al.slice().sort(function (a, b) { return (ord[a.ciddilik] || 3) - (ord[b.ciddilik] || 3); });
    return '<div class="card alist">' + al.slice(0, 8).map(function (a) {
      return '<a class="arow" href="' + (a.risk_id ? '#/reyestr/' + a.risk_id : '#/reyestr/xeberdarliq') + '"><span>' + U.sigchip(a.ciddilik) + '</span><span>' + U.esc(a.mesaj) + '<br><span class="small muted">' + U.esc(a.tip) + (a.risk_id ? ' · ' + a.risk_id : '') + '</span></span><span class="when">' + U.esc(a.as_of) + '</span></a>';
    }).join('') + (al.length > 8 ? '<div class="arow"><span></span><a href="#/reyestr/xeberdarliq">Bütün ' + al.length + ' xəbərdarlıq →</a><span></span></div>' : '') + '</div>';
  }
  U.pages[''] = function (v) {
    var st = U.META.stamp, run = U.META.run || {};
    v.innerHTML = '<div class="hero"><div><div class="eyebrow">İqtisadiyyat Nazirliyi · MİİS §15.5.3 · qərar dəstək sistemi</div>' +
      '<h1 class="h1" style="margin-top:6px">Bu gün — ' + U.esc(st.as_of) + '</h1>' +
      '<p class="lead">Azərbaycan iqtisadiyyatı üçün risklərin gündəlik mənzərəsi. Avtomatik toplanan bazar və statistika məlumatı rəsmi makro (OxLon, Nazirlik) və mikro (FR1–FR12) proqnozlarla müqayisə olunur; hər riskin ehtimalı, təsiri, tədbirləri və qalıq riski bir kliklə açılır. Risk bölməsi öz mərkəzi proqnozunu vermir — o, rəsmi proqnozun ətrafındakı qeyri-müəyyənliyi ölçür.</p></div>' +
      '<div class="card pad small"><b>Son hesablama</b><br>' + U.esc(run.rejim || '') + ' · ' + U.esc(st.date) + ' UTC · ' + U.nf(run.muddet_san, 0) + ' san<br>baza identifikatoru <code>' + U.esc(st.baseline_id) + '</code> · ' + st.files + ' çıxış faylı<br>' +
      (run.merheleler || []).filter(function (s) { return s.status !== 'ok'; }).map(function (s) { return '<span class="chip warn">' + U.esc(s.stage + ' ' + s.status) + '</span> '; }).join('') +
      '<span class="muted">' + (run.merheleler || []).filter(function (s) { return s.status === 'ok'; }).length + ' / ' + (run.merheleler || []).length + ' mərhələ uğurlu</span>' +
      '<div class="toolbar" style="margin:8px 0 0"><button class="btn sm" id="h-refresh">' + U.icon('play', 14) + ' Məlumatı indi yenilə</button><a class="btn sm ghost" href="#/metod/icra">İcra jurnalı</a></div><div id="h-job"></div></div></div>' +
      U.sec('Əsas göstəricilər', 'Kartı klikləyin — müvafiq bölmə açılır.', tiles()) +
      '<div class="cols2"><div>' + U.sec('İndi ən yüksək risklər', 'skor = ehtimal balı × təsir balı (1–25); oxlar əvvəlki hesablamaya nisbətən dəyişməni göstərir', topRisks()) + '</div>' +
      '<div>' + U.sec('Yeni xəbərdarlıqlar', 'FR2 xəbərdarlıq qaydaları: yüksək prioritet, skor artımı, göstərici həddi, köhnəlmiş baza', alerts()) + '</div></div>' +
      '<div id="h-more"></div>';
    U.H.more(U.$('#h-more', v));
    U.$('#h-refresh', v).onclick = function () { U.H.refresh(U.$('#h-job', v)); };
  };
})();
