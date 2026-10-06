/* p_risk.js — one risk's drill-down (#/reyestr/<id>): definition, indicator and live value, probability method and score,
   transmission channel and contributions. Scalability, affected variables, CAEM, measures and residual: p_risk2.js. */
(function () {
  'use strict';
  var U = window.U;
  U.RK = {};
  function hasId(list, rid) { return U.ids(list).indexOf(rid) >= 0; }
  U.hasId = hasId;
  function nav(rid) {
    var ids = U.T('FR2_risk_scores').map(function (r) { return r.risk_id; }).sort();
    return '<nav class="rnav" aria-label="Risklər">' + ids.map(function (i) { return '<a href="#/reyestr/' + i + '" class="' + (i === rid ? 'on' : '') + '">' + i + '</a>'; }).join('') + '</nav>';
  }
  function head(r, g, pv) {
    var p = pv.by[r.risk_id], d = p ? r.skor - p.skor : null;
    return '<div class="eyebrow"><a href="#/reyestr">Risk reyestri</a> › ' + U.esc(U.FAM[r.aile] || r.aile) + '</div>' +
      '<div class="rhead" style="margin-top:6px"><div style="flex:1 1 420px"><h1 class="h1">' + r.risk_id + ' — ' + U.esc(r.ad) + '</h1>' +
      '<p class="lead">' + U.esc(g.tesvir || '') + '</p><div class="pill-row">' + U.fam(r.aile) + '<span class="chip">' + U.esc(r.nov) + '</span><span class="chip scen">sahib: ' + U.esc(r.sahib) + '</span><span class="chip">üfüq ' + r.ufuq + '</span>' + (g.caem_kateqoriya ? '<span class="chip coef">CAEM: ' + U.esc(g.caem_kateqoriya) + '</span>' : '') + '</div></div>' +
      '<div class="tiles" style="flex:1 1 420px;grid-template-columns:repeat(4,minmax(0,1fr))">' +
      U.tile('Skor', '<span style="font-size:30px">' + U.score(r.skor) + '</span><small>/ 25</small>', U.prio(r.prioritet) + (d == null ? '' : ' ' + (d ? (d > 0 ? '↑ ' : '↓ ') + U.sg(d, 0) : '→ dəyişməyib')), r.prioritet === 'yüksək' ? 'bad' : r.prioritet === 'orta' ? 'warn' : 'ok') +
      U.tile('Ehtimal', U.pct(r.ehtimal, 1), 'bal P' + r.P_bal + (p ? ' · əvvəl ' + U.pct(p.ehtimal, 1) : '')) +
      U.tile('Təsir', 'T' + r.I_bal, 'ölçü: ' + U.esc(r.I_olcu)) +
      U.tile('Gözlənilən itki', U.nf(r.gozlenilen_itki_g, 3) + '<small>f.b.</small>', 'qeyri-neft artımı (ehtimal × təsir)') + '</div></div>' + nav(r.risk_id);
  }
  function definition(r, g) {
    var ex = g.ekspert_ehtimal || g.ekspert_tesir_qeyri_neft || g.ekspert_tesir_cpi || g.ekspert_tesir_fiskal;
    return '<div class="cols2"><div class="card pad"><h3>Tərif</h3>' + U.kv([['Hadisənin tərifi', U.esc(g.hadise_terifi)], ['Göstərici(lər)', U.esc(g.gosterici)], ['Ehtimal üsulu', U.esc(g.ehtimal_metodu)], ['Ötürmə kanalı', U.esc(g.oturme_kanali)],
      ['Risk növü', U.esc(g.nov) + ' — ' + ({ amil: 'risk mənbəyi: ehtimal və təsir simulyasiyadan', 'nəticə': 'həddin pozulma ehtimalı və həddən kənar gözlənilən çatışmazlıq', siqnal: 'mikro erkən xəbərdarlıq siqnalından', ekspert: 'Nazirliyin təsdiqinə təqdim olunan ekspert örtüyü', model: 'bölmələrarası proqnoz fikir ayrılığı (D3)' }[g.nov] || '')],
      ['CAEM kateqoriyası', U.esc(g.caem_kateqoriya)], ['Qeyd', U.esc(g.qeyd)], ['Aktiv', g.aktiv === '1' ? 'bəli' : U.esc(g.aktiv)]]) +
      (ex ? '<div class="note-w"><b>Ekspert örtüyü</b> (Nazirlik təsdiq etməlidir): ehtimal ' + U.esc(g.ekspert_ehtimal || '—') + ', təsir qeyri-neft ' + U.esc(g.ekspert_tesir_qeyri_neft || '—') + ', inflyasiya ' + U.esc(g.ekspert_tesir_cpi || '—') + ', büdcə ' + U.esc(g.ekspert_tesir_fiskal || '—') + '</div>' : '') + '</div>' +
      '<div class="card pad"><h3>Ehtimal və təsir necə hesablanır</h3>' + U.kv([['Ehtimal', '<b>' + U.pct(r.ehtimal, 1) + '</b> → bal P' + r.P_bal], ['Ehtimalın mənbəyi', U.esc(r.ehtimal_menbe)],
      ['Təsir: qeyri-neft artımı', U.nf(r.tesir_g, 3) + ' f.b.'], ['Təsir: inflyasiya', U.nf(r.tesir_cpi, 3) + ' f.b.'], ['Təsir: büdcə balansı', U.nf(r.tesir_fis, 3) + ' % ÜDM'], ['Təsir balı', 'T' + r.I_bal + ' (ölçü: ' + U.esc(r.I_olcu) + ')'],
      ['Təsirin mənbəyi', U.esc(r.tesir_menbe)], ['Dispersiya payı', U.isNum(r.dispersiya_payi) ? U.pct(r.dispersiya_payi, 1) : '—'], ['Quyruq töhfəsi (Eyler)', U.nf(r.quyruq_tohfesi, 3)], ['Kəmiyyət sırası', U.nf(r.kemiyyet_sirasi, 0)],
      ['Baza identifikatoru', '<code>' + U.esc(r.baseline_id) + '</code> · ' + U.esc(r.as_of)]]) + bands(r) + '</div></div>';
  }
  function bands(r) {
    var hd = U.by(U.T('input_hedler'), 'acar'), v = function (k) { return hd[k] ? hd[k][0].deyer : null; };
    var pb = [v('p_band_1'), v('p_band_2'), v('p_band_3'), v('p_band_4')], key = { 'qeyri-neft ÜDM': 'i_nonoil', inflyasiya: 'i_cpi', 'büdcə': 'i_fiscal' }[r.I_olcu] || 'i_nonoil';
    var ib = [1, 2, 3, 4].map(function (i) { return v(key + '_' + i); });
    return '<p class="small muted" style="margin-top:8px">Ehtimal pillələri: P1 ≤ ' + U.pct(pb[0]) + ', P2 ≤ ' + U.pct(pb[1]) + ', P3 ≤ ' + U.pct(pb[2]) + ', P4 ≤ ' + U.pct(pb[3]) + ', P5 &gt; ' + U.pct(pb[3]) +
      '. Təsir pillələri (' + U.esc(r.I_olcu) + '): T1 ≤ ' + ib.map(function (x, i) { return U.nf(x, 2) + (i < 3 ? ', T' + (i + 2) + ' ≤ ' : ''); }).join('') + ', T5 daha çox. Prioritet: skor ≥ ' + v('score_high') + ' yüksək, ≥ ' + v('score_medium') + ' orta.</p>';
  }
  function indicator(r, g) {
    var gs = U.ids(g.gosterici), ib = U.T('FR1_indicator_base').filter(function (x) { return gs.indexOf(x.gosterici) >= 0; });
    var d5 = U.T('D5_daily_monitor').filter(function (x) { return gs.some(function (k) { return String(x.indicator).indexOf(k) >= 0; }); });
    var h = '';
    if (ib.length) h += U.dt('rk-ib', ib, [{ k: 'ad', l: 'Göstərici' }, { k: 'son_deyer', l: 'Son dəyər', n: 1 }, { k: 'vahid', l: 'Vahid' }, { k: 'son_tarix', l: 'Tarix' }, { k: 'menbe', l: 'Mənbə' }, { k: 'tarixi_faiz', l: 'Tarixi faiz', n: 1, d: 1, t: 'son dəyərin tarixi paylanmadakı faizi' }, { k: 'z', l: 'z (tarixi)', n: 1, d: 2, t: '(son − tarixi orta) / tarixi σ' }, { k: 'status', l: 'Status (tarixi paylanmaya görə)', f: U.sigchip, t: 'birtərəfli, yalnız risk istiqamətində' }, { k: 'status_qaydasi', l: 'Qayda' }], { title: 'Göstəricinin canlı dəyəri — tarixi paylanmaya görə (FR1 bazası)', file: r.risk_id + '_gosterici' });
    if (d5.length) h += U.dt('rk-d5', d5, [{ k: 'label_az', l: 'Göstərici' }, { k: 'latest', l: 'Son', n: 1 }, { k: 'date', l: 'Tarix' }, { k: 'baseline_source', l: 'Baza' }, { k: 'baseline_assumption', l: 'Fərziyyə', n: 1 }, { k: 'deviation_pct', l: 'Sapma, %', n: 1, d: 1 }, { k: 'z_score', l: 'z (fərziyyəyə görə)', n: 1, d: 2, t: '(son − fərziyyə) / proqnoz xətası σ' }, { k: 'signal', l: 'Siqnal (proqnoz fərziyyəsinə görə)', f: U.sigchip, t: 'ikitərəfli: |z| ≥ 1 diqqət, ≥ 2 xəbərdarlıq' }], { title: 'Gündəlik monitor (D5) — proqnoz fərziyyəsinə görə', file: r.risk_id + '_D5' });
    if (ib.length && d5.length) h += '<p class="small muted">İki fərqli istinad: FR1 statusu səviyyəni göstəricinin öz tarixi ilə müqayisə edir (birtərəfli, yalnız risk istiqamətində); D5 siqnalı isə bölmələrin proqnoz fərziyyəsindən sapmanı ölçür (ikitərəfli). Ona görə eyni səviyyə FR1-də «normal», D5-də «xəbərdarlıq» ola bilər.</p>';
    return h || '<p class="muted">Bu risk üçün birbaşa canlı göstərici yoxdur (nəticə və ya ekspert riski) — ehtimal birgə simulyasiyadan və ya ekspert örtüyündən gəlir.</p>';
  }
  function channel(r) {
    var tc = U.T('FR1_transmission_channels').filter(function (x) { return String(x.istifade || '').indexOf(r.risk_id) >= 0; });
    var co = U.T('FR2_contributions').filter(function (x) { return x.risk_id === r.risk_id; });
    var h = tc.length ? U.dt('rk-tc', tc, [{ k: 'kanal', l: 'Kanal' }, { k: 'izah', l: 'İzah' }, { k: 'asili', l: 'Asılı' }, { k: 'izahedici', l: 'İzahedici' }, { k: 'emsal', l: 'Əmsal', n: 1, d: 3 }, { k: 'st_xeta', l: 'SE', n: 1, d: 3 }, { k: 'p', l: 'p', n: 1, f: U.pf }, { k: 'n', l: 'n', n: 1, d: 0 }, { k: 'R2', l: 'R²', n: 1, d: 2 }, { k: 'nümunə', l: 'Nümunə' }, { k: 'sübut', l: 'Sübut', f: U.sigchip }, { k: 'istifade', l: 'İstifadə' }], { title: 'Ötürmə kanalının qiymətləndirilməsi (FR1)', file: r.risk_id + '_kanal' }) : '';
    if (co.length) h += U.dt('rk-co', co, [{ k: 'gosterici', l: 'Göstərici', f: function (v) { return { g: 'qeyri-neft artımı', cpi: 'inflyasiya', fis: 'büdcə' }[v] || v; } }, { k: 'il', l: 'İl', n: 1, d: 0 }, { k: 'ad', l: 'Kanal' }, { k: 'orta', l: 'Orta töhfə', n: 1, d: 3 }, { k: 'dispersiya_payi', l: 'Dispersiya payı', n: 1, p: 1, d: 1 }, { k: 'quyruq_tohfesi', l: 'Quyruq töhfəsi', n: 1, d: 3 }, { k: 'quyruq_tohfesi_merkezlesmis', l: 'Mərkəzləşmiş', n: 1, d: 3 }],
      { title: 'Paylanmaya töhfə (FR2_contributions): bu risk kanalı aşağı quyruğa nə qədər verir', file: r.risk_id + '_tohfe' });
    return h || '<p class="muted">Ayrıca kanal cədvəli yoxdur; ötürmə yuxarıdakı təsvirdə və təsir ölçüsündədir.</p>';
  }
  U.riskPage = function (v, rid) {
    var r = U.T('FR2_risk_scores').filter(function (x) { return x.risk_id === rid; })[0];
    if (!r) { v.innerHTML = '<div class="card pad"><b>Risk tapılmadı: ' + U.esc(rid) + '</b> <a href="#/reyestr">Reyestrə qayıt</a></div>'; return; }
    var g = U.T('input_risk_reyestri').filter(function (x) { return x.risk_id === rid; })[0] || {}, pv = U.prevScores();
    v.innerHTML = head(r, g, pv) + U.sec('Tərif, ehtimal və təsir', '', definition(r, g)) +
      U.sec('Göstərici və canlı dəyər', '', indicator(r, g)) + U.sec('Ötürmə kanalı', 'risk hadisəsi iqtisadiyyata necə ötürülür', channel(r)) +
      '<div id="rk-more"></div>';
    U.RK.more(U.$('#rk-more', v), r, g);
  };
})();
