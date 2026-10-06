/* p_stress.js — Stress testləri: the eight standing scenarios S1–S8 (FR3_stress_scenarios: deviation from the official
   baseline with and without measures), SOFAZ under the same scenarios (K4), policy levers needed (FR3_levers) and the
   historical analogues of the transmission (FR3_historical_analogues). The custom builder (#/stress/qurucu): p_stress2.js. */
(function () {
  'use strict';
  var U = window.U;
  var ST = U.ST = { s: 'S1' };
  var IND = ['qeyri-neft artımı, f.b.', 'inflyasiya, f.b.', 'büdcə balansı, % ÜDM'];
  function overview(el) {
    var t = U.T('FR3_stress_scenarios'), sc = U.uniq(t.map(function (r) { return r.ssenari; })), y = U.scoreYear();
    var cards = sc.map(function (s) {
      var rs = t.filter(function (r) { return r.ssenari === s; }), g = rs.filter(function (r) { return r.gosterici === IND[0] && r.il === y; })[0] || {}, c = rs.filter(function (r) { return r.gosterici === IND[1] && r.il === y; })[0] || {}, f = rs.filter(function (r) { return r.gosterici === IND[2] && r.il === y; })[0] || {};
      return '<button type="button" class="kpi' + (s === ST.s ? ' on' : '') + '" data-s="' + s + '"><span class="chip scen">' + s + '</span><span class="l">' + U.esc(rs[0].ad) + '</span><span class="small muted">' + U.esc(rs[0].sok_vektoru) + '</span>' +
        '<span class="small">' + y + ': qeyri-neft <b class="' + (g.sapma < 0 ? 'down' : 'up') + '">' + U.sg(g.sapma, 2) + '</b> · inflyasiya <b>' + U.sg(c.sapma, 2) + '</b> · büdcə <b class="' + (f.sapma < 0 ? 'down' : 'up') + '">' + U.sg(f.sapma, 2) + '</b></span></button>';
    }).join('');
    var rs = t.filter(function (r) { return r.ssenari === ST.s; });
    el.innerHTML = '<div class="kpis syncards" id="st-cards">' + cards + '</div>' +
      U.sec(ST.s + ' — ' + U.esc((rs[0] || {}).ad || ''), U.esc((rs[0] || {}).sok_vektoru || ''), '<div class="cols3">' + IND.map(function (g, i) { return '<div class="card pad"><h3>' + g + '</h3><div class="ch" id="st-g' + i + '"></div></div>'; }).join('') + '</div>' +
        '<p class="small muted">Sapma — rəsmi baza yolundan fərq. «Tədbirlə» — prosiklik investisiya kəsintisindən imtina (T09) və digər modelləşdirilmiş tədbirlər tətbiq edildikdə.</p>') +
      U.dt('st-t', t, [{ k: 'ssenari', l: 'Ssenari' }, { k: 'ad', l: 'Ad' }, { k: 'sok_vektoru', l: 'Şok vektoru' }, { k: 'gosterici', l: 'Göstərici' }, { k: 'il', l: 'İl', n: 1, d: 0 }, { k: 'sapma', l: 'Sapma', n: 1, d: 3 }, { k: 'sapma_tedbirle', l: 'Sapma (tədbirlə)', n: 1, d: 3 }, { k: 'tedbirin_effekti', l: 'Tədbirin effekti', n: 1, d: 3 }],
        { title: 'Bütün stress ssenariləri (FR3_stress_scenarios)', file: 'FR3_stress_scenarios' }) +
      U.dt('st-k4', U.T('K4_sofaz_adequacy').filter(function (r) { return r.ssenari === ST.s; }), null, { title: 'ARDNF bu ssenaridə (K4)', file: 'K4_' + ST.s, href: function () { return '#/var/ardnf'; } }) +
      U.dt('st-lv', U.T('FR3_levers'), null, { title: 'Siyasət alətləri: P10-u medianaya qaytarmaq üçün lazım olan ölçü (FR3_levers)', file: 'FR3_levers' }) +
      '<div class="card pad"><h3>Tarixi analoqlar: faktiki vs modelin izah etdiyi qeyri-neft sapması (FR3_historical_analogues)</h3><div id="st-an" class="ch"></div></div>' +
      U.dt('st-a', U.T('FR3_historical_analogues'), null, { title: 'Tarixi analoqlar — kanal bölgüsü', file: 'FR3_historical_analogues' });
    IND.forEach(function (g, i) {
      var r = rs.filter(function (q) { return q.gosterici === g; }).sort(function (a, b) { return a.il - b.il; }), x = r.map(function (q) { return q.il; });
      U.bars(U.$('#st-g' + i, el), x, [{ name: 'sapma', y: r.map(function (q) { return q.sapma; }), c: '#B3261E' }, { name: 'tədbirlə', y: r.map(function (q) { return q.sapma_tedbirle; }), c: '#1E7B4F' }], g.split(',').slice(-1)[0], { years: true, h: 260 });
    });
    var an = U.T('FR3_historical_analogues');
    U.lines(U.$('#st-an', el), [{ x: an.map(function (r) { return r.il; }), y: an.map(function (r) { return r.faktiki_sapma; }), name: 'faktiki sapma', mode: 'lines+markers', c: '#15202B' }, { x: an.map(function (r) { return r.il; }), y: an.map(function (r) { return r.proqnoz_sapma; }), name: 'model (kanalların cəmi)', mode: 'lines+markers', c: '#0E6F7C', dash: 'dash' }], 'f.b.', { years: false, zero: true });
    U.$('#st-cards', el).onclick = function (e) { var b = e.target.closest('[data-s]'); if (b) { ST.s = b.getAttribute('data-s'); overview(el); } };
  }
  U.pages.stress = function (v, p) {
    var sub = p[1] || '';
    v.innerHTML = U.head('FR3 — stress testləri və ssenari qurucusu', 'Stress testləri', 'Səkkiz daimi ssenari (S1–S8) rəsmi baza ilə müqayisədə və tədbirlərlə; «Ssenari qurucusu» ilə öz stressinizi qurun: amil şokları MikroUnit zəncirinə (FR1 → FR12) və RU birgə Monte Karlo simulyasiyasına verilir.') +
      U.subtabs('stress', [['', 'S1–S8 nəticələri'], ['qurucu', 'Ssenari qurucusu']], sub) + '<div id="st-body"></div>';
    var b = U.$('#st-body', v);
    if (sub === 'qurucu') U.ST.builder(b); else overview(b);
  };
})();
