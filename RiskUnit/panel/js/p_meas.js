/* p_meas.js — Tədbirlər, part 1: measures register v2 (M1) with quantified effects (M2) and one measure's detail
   dialog, the portfolio optimiser: efficient frontier with a budget slider (M4), optimal portfolios (M3) and the live
   re-optimisation (/optimize/run). Plan, strategy, residual risk and the daily decision table: p_meas2.js. */
(function () {
  'use strict';
  var U = window.U;
  var M = U.MS = { b: 500 };
  var EFF = [['d_ES10_g', 'ES10 qeyri-neft'], ['d_P_g', 'P(GaR)'], ['d_ES10_cpi', 'ES10 inflyasiya'], ['d_P_cpi', 'P(inflyasiya)'], ['d_ES10_fis', 'ES10 büdcə'], ['d_P_fis', 'P(büdcə)'], ['d_CaR95', 'CaR 95 %'], ['d_VaR95_ARDNF', 'ARDNF VaR'], ['d_ORaR95', 'neft gəlirinə risk']];
  M.detail = function (id) {
    var m = U.T('M1_measures_v2').filter(function (r) { return r.tedbir_id === id; })[0]; if (!m) return;
    var e = U.T('M2_measure_effects').filter(function (r) { return r.tedbir_id === id; }), ph = U.T('M6_implementation_plan').filter(function (r) { return r.tedbir_id === id; }), hs = U.T('FR3_status_history').filter(function (r) { return r.tedbir_id === id; });
    var old = U.T('FR3_measures_register').filter(function (r) { return r.tedbir_id === id; })[0] || {};
    U.openModal('<div class="eyebrow">Tədbir · ' + U.esc(m.strategiya_v2) + ' · ' + U.esc(m.alet_novu) + '</div><h2 class="mh">' + id + ' — ' + U.esc(m.tedbir) + '</h2>' +
      '<div class="pill-row">' + U.ids(m.risk_idler).map(function (r) { return '<a class="chip scen" href="#/reyestr/' + r + '">' + r + '</a>'; }).join('') + U.sigchip(m.status_az) + (m.optimal_planda_500 ? '<span class="chip acc">optimal planda (500 mln)</span>' : '') + (m.gecikir ? '<span class="chip bad">gecikir</span>' : '') + '</div>' +
      '<div class="cols2" style="margin-top:12px"><div>' + U.kv([['Məsul', U.esc(m.mesul)], ['Başlama — müddət', U.esc(m.baslama) + ' — ' + U.esc(m.muddet)], ['Status', U.esc(m.status_az) + ' (mərhələ ' + U.esc(m.merhele_no) + '/4) · növbəti addım: ' + U.esc(m.novbeti_addim)], ['KPI', U.esc(m.kpi)], ['KPI həddi', U.esc(m.kpi_hedd)],
        ['Xərc', U.nf(m.xerc_mln_azn, 1) + ' mln AZN — ' + U.esc(m.xerc_esasi)], ['Hazırlıq', U.nf(m.hazirliq_ay, 0) + ' ay'], ['Qeyd (v1 reyestr)', U.esc(old.qeyd)]]) + '</div><div>' +
      U.kv([['Kəmiyyətləndirmə', U.esc(m.kemiyyet_metodu)], ['Effekt modeli', U.esc(m.effekt_modeli) + ' · kanal ' + U.esc(m.effekt_kanal) + ' · güc ' + U.nf(m.effekt_guc, 2)], ['Effektin əsası', U.esc(m.effekt_esasi)], ['Sübut', U.esc(m['effekt_sübutu'])],
        ['Risk azalması (hədəf funksiyası)', U.nf(m.effekt_hedef_funksiya, 3)], ['Xərc-effektivlik (100 mln AZN-ə)', U.nf(m.xerc_effektivliyi_100mln, 2)]]) + '</div></div>' +
      U.dt('md-e', e, [{ k: 'metrika_ad', l: 'Metrika' }, { k: 'vahid', l: 'Vahid' }, { k: 'baza', l: 'Baza', n: 1, d: 3 }, { k: 'tedbirle', l: 'Tədbirlə', n: 1, d: 3 }, { k: 'delta', l: 'Fərq', n: 1, d: 4 }, { k: 'yaxsilasma', l: 'Yaxşılaşma', n: 1, d: 4 }, { k: 'metod', l: 'Metod' }, { k: 'esas', l: 'Əsas' }], { title: 'Risk paylanmasına təsir (M2)', file: id + '_M2' }) +
      U.dt('md-p', ph, [{ k: 'merhele', l: 'Mərhələ' }, { k: 'baslama', l: 'Başlama' }, { k: 'bitme', l: 'Bitmə' }, { k: 'status', l: 'Status', f: U.sigchip }, { k: 'is_axini_addimi', l: 'Addım' }, { k: 'qalan_gun', l: 'Qalan gün', n: 1, d: 0 }, { k: 'plan', l: 'Plan' }, { k: 'xeberdarliq', l: 'Xəbərdarlıq' }], { title: 'İcra mərhələləri (M6)', file: id + '_M6' }) +
      U.dt('md-h', hs, null, { title: 'Status tarixçəsi (FR3)', file: id + '_status' }));
  };
  function register(el) {
    var m1 = U.T('M1_measures_v2'), st = U.by(m1, 'strategiya_v2'), ss = U.by(m1, 'status_az'), plan = m1.filter(function (r) { return r.optimal_planda_500; });
    el.innerHTML = '<div class="tiles">' + U.tile('Tədbirlər', U.nf(m1.length, 0), Object.keys(st).map(function (k) { return k + ': ' + st[k].length; }).join(' · ')) + U.tile('Status', Object.keys(ss).map(function (k) { return ss[k].length + ' ' + k; }).join(' · '), 'təklif → təsdiq → icrada → tamamlandı') +
      U.tile('Optimal plan (500 mln AZN)', U.nf(plan.length, 0) + '<small>tədbir</small>', 'xərc ' + U.nf(U.sum(plan.map(function (r) { return r.xerc_mln_azn; })), 1) + ' mln AZN', 'ok', '#/tedbir/portfel') + U.tile('Gecikən', U.nf(m1.filter(function (r) { return r.gecikir; }).length, 0), 'müddəti keçmiş, tamamlanmamış', m1.some(function (r) { return r.gecikir; }) ? 'bad' : 'ok', '#/tedbir/plan') + '</div>' +
      '<div class="card pad"><h3>Risk azalması vs xərc (M1): hər nöqtə bir tədbir</h3><div id="ms-sc" class="ch"></div></div>' +
      U.dt('ms-t', m1, [{ k: 'tedbir_id', l: 'Tədbir', f: function (v) { return '<b>' + v + '</b>'; } }, { k: 'tedbir', l: 'Ad' }, { k: 'risk_idler', l: 'Risklər', f: function (v) { return U.ids(v).map(function (r) { return '<a href="#/reyestr/' + r + '">' + r + '</a>'; }).join(' '); } }, { k: 'strategiya_v2', l: 'Strategiya' }, { k: 'alet_novu', l: 'Alət' }, { k: 'mesul', l: 'Məsul' },
        { k: 'status_az', l: 'Status', f: U.sigchip }, { k: 'muddet', l: 'Müddət' }, { k: 'xerc_mln_azn', l: 'Xərc, mln AZN', n: 1, d: 1 }, { k: 'kemiyyet_metodu', l: 'Kəmiyyətləndirmə' }, { k: 'effekt_hedef_funksiya', l: 'Risk azalması', n: 1, d: 3 }, { k: 'xerc_effektivliyi_100mln', l: 'Xərc-effektivlik', n: 1, d: 2 }]
        .concat(EFF.map(function (e) { return { k: e[0], l: 'Δ ' + e[1], n: 1, d: 4 }; })).concat([{ k: 'optimal_planda_500', l: 'Optimal planda' }, { k: 'kpi', l: 'KPI' }]),
        { title: 'Tədbirlər reyestri v2 (M1) — sətrə klikləyin', file: 'M1_measures_v2', onRow: function (r) { M.detail(r.tedbir_id); } }) +
      U.dt('ms-m2', U.T('M2_measure_effects'), null, { title: 'Bütün kəmiyyətləndirilmiş effektlər (M2)', file: 'M2_measure_effects', lim: 40 }) +
      U.dt('ms-v1', U.T('FR3_measures_register'), null, { title: 'v1 tədbirlər reyestri (FR3_measures_register) — müqayisə üçün', file: 'FR3_measures_register', lim: 30 }) +
      U.dt('ms-cv', U.T('FR3_coverage'), null, { title: 'Hər risk üçün tədbir örtüyü (FR3_coverage)', file: 'FR3_coverage', href: function (r) { return '#/reyestr/' + r.risk_id; } });
    U.scatter(U.$('#ms-sc', el), m1.filter(function (r) { return U.isNum(r.xerc_mln_azn); }).map(function (r) { return { x: Math.max(0.1, r.xerc_mln_azn), y: r.effekt_hedef_funksiya, t: r.tedbir_id, c: r.optimal_planda_500 ? '#0E6F7C' : '#9AA6B2', h: r.tedbir_id + ' ' + r.tedbir + '<br>xərc ' + U.nf(r.xerc_mln_azn, 1) + ' mln · azalma ' + U.nf(r.effekt_hedef_funksiya, 3) }; }), 'xərc, mln AZN (log)', 'risk azalması (hədəf funksiyası)');
    var p = U.$('#ms-sc', el); if (p && p.layout && window.Plotly) window.Plotly.relayout(p, { 'xaxis.type': 'log' });
    var q = U.HQ.get('t'); if (q) setTimeout(function () { M.detail(q); }, 50);
  }
  M.register = register;
  U.pages.tedbir = function (v, p) {
    var sub = p[1] || '';
    v.innerHTML = U.head('FR3 — risk azaldıcı tədbirlər və strateji yanaşmalar', 'Tədbirlər', 'Hər tədbirin risk paylanmasına kəmiyyətləndirilmiş təsiri (mühərrik — MikroUnit zənciri və RU Monte Karlo; ekspert parametrləri işarələnib), büdcə daxilində optimal portfel, icra planı və status iş axını, risk ailələri üzrə strategiya və gündəlik qərar cədvəli. Xərclər Nazirliyin təsdiqləməli olduğu fərziyyələrdir.') +
      U.subtabs('tedbir', [['', 'Reyestr və effektlər'], ['portfel', 'Portfel və səmərəli sərhəd'], ['plan', 'İcra planı'], ['strategiya', 'Strategiya və qalıq risk'], ['qerar', 'Gündəlik qərar (S7)']], sub === 'reyestr' ? '' : sub) + '<div id="ms-body"></div>';
    var b = U.$('#ms-body', v);
    if (sub === 'portfel') U.MS.portfolio(b); else if (sub === 'plan') U.MS.plan(b); else if (sub === 'strategiya') U.MS.strategy(b); else if (sub === 'qerar') U.MS.decision(b); else register(b);
  };
})();
