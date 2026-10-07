/* common.js — policy-specific helpers: scenarios (official + IO / microsimulation examples), the current scenario,
   horizons (Ministry definition 24.08.2026), engines, evidence-tier chips, headline lookups and effect formatting. */
(function () {
  'use strict';
  var U = window.U, R = window.POL;
  U.HZ = [['qısa', 'Qısa müddət', 'başlanğıc il və növbəti il (t0, t0+1)'], ['orta', 'Orta müddət', 'başlanğıc ildən 2–3 il sonra (t0+2…t0+3)'], ['uzun', 'Uzun müddət', '≥ t0+4 (5-ci il və sonrası)']];
  U.HZN = { 'qısa': 'qısa', 'orta': 'orta', 'uzun': 'uzun' };
  U.ENG = { micro: 'MikroUnit struktur zənciri', caem: 'CAEM (Nazirlik modeli — müqayisə)', oxlon: 'OxLon (xarici kanallar)', io: 'Girdi-çıxdı (IO)', microsim: 'Mikrosimulyasiya', longrun: 'Uzun müddət (struktur ekstrapolyasiya)', riskfx: 'RiskUnit FX ötürməsi (kalibrlənmiş)', microsim_spill: 'Mikrosimulyasiya + spill-over' };
  U.ENGS = { micro: 'MikroUnit', caem: 'CAEM', oxlon: 'OxLon', io: 'IO', microsim: 'Mikrosim.', longrun: 'Uzun müddət', riskfx: 'RiskUnit FX', microsim_spill: 'Mikrosim. + spill-over' };
  U.ENGC = { micro: '#0E6F7C', caem: '#E07B00', oxlon: '#6A3FB5', io: '#1F6FB2', microsim: '#C2185B', longrun: '#8A5300', riskfx: '#5B7F00', microsim_spill: '#E57399' };
  U.FAMC = { 'vergi': '#1F6FB2', 'xərc': '#0E6F7C', 'sosial': '#C2185B', 'əmək': '#6A3FB5', 'monetar': '#E07B00', 'ticarət': '#1E7B4F', 'sektor': '#8A5300', 'tənzimləmə': '#455463' };
  U.TIER = { A: 'A — birbaşa qiymətləndirilmiş, nümunədən kənar yoxlanılıb', B: 'B — qiymətləndirilmiş, nümunədaxili yoxlanılıb', C: 'C — struktur modeldən (kalibrlənmiş zəncir), birbaşa yoxlanılmayıb', D: 'D — proksi / fərziyyə (ehtiyatla şərh edin)' };
  U.tier = function (t) {
    if (!t) return '';
    return String(t).split('').filter(function (c) { return U.TIER[c]; }).map(function (c) { return '<span class="tier t' + c + '" title="Sübut səviyyəsi ' + U.esc(U.TIER[c]) + '">' + c + '</span>'; }).join('');
  };
  U.SYN = '<div class="synth" role="note"><b>SİNTETİK — real ev təsərrüfatı məlumatı deyil.</b> Ev təsərrüfatı səviyyəsində nəticələr DSK 2024 aqreqatlarına kalibrlənmiş sintetik nümunə ilə hesablanıb; Nazirliyin EBT / İQS mikroməlumatı şablon və sütun xəritəsi ilə qoşulduqda yenidən hesablanır.</div>';
  U.empty = function (what, why) { return '<div class="card pad empty"><b>' + U.esc(what) + ' — məlumat yoxdur.</b><p class="small muted" style="margin:6px 0 0">' + (why || 'Müvafiq mərhələ hələ işə salınmayıb: <code>python3 run_all.py</code>, sonra <code>python3 panel/build_panel.py</code>.') + '</p></div>'; };
  U.instr = function (id) { return U.T('cfg_instruments').filter(function (r) { return r.id === id; })[0] || null; };
  U.fam = function (f) { var c = U.FAMC[f] || '#738190'; return '<span class="chip" style="background:' + c + '1A;color:' + c + '">' + U.esc(f || '') + '</span>'; };
  U.UNITN = { pct: '% (bazaya nisbətən)', pp: 'f.b. (faiz bəndi)', mln_azn: 'mln AZN/il', abs: 'ədəd' };
  U.FINN = { deficit: 'borc (kəsir)', sofaz: 'ARDNF transferti', tax: 'vergi artımı', reallocation: 'xərclərin yenidən bölüşdürülməsi' };
  /* ---- scenarios ---- */
  var SC = null;
  U.scens = function () {
    if (SC) return SC;
    SC = []; var seen = {};
    (R.core.scen || []).forEach(function (s) { seen[s.id] = 1; SC.push({ id: s.id, name: s.name_az, desc: s.description_az, start: s.start_year, ins: s.instruments || [], tags: s.tags || [], src: 'rəsmi', file: s._file }); });
    var add = function (stem, nk, src) {
      U.T(stem).forEach(function (r) { if (!seen[r.scenario]) { seen[r.scenario] = 1; SC.push({ id: r.scenario, name: r[nk] || r.scenario, desc: '', start: r.year || null, ins: [], tags: [], src: src }); } });
    };
    add('P3_microsim_headline', 'scenario_name', 'mikrosimulyasiya nümunəsi');
    ((R.core._meta || {}).ioscen || []).forEach(function (x) { if (!seen[x[0]]) { seen[x[0]] = 1; SC.push({ id: x[0], name: x[1], desc: '', start: null, ins: [], tags: [], src: 'IO nümunəsi' }); } });
    return SC;
  };
  U.resetScens = function () { SC = null; };
  U.scen = function (id) { return U.scens().filter(function (s) { return s.id === id; })[0] || null; };
  U.official = function () { return U.scens().filter(function (s) { return s.src === 'rəsmi'; }); };
  U.cur = function () {
    var q = U.HQ && U.HQ.get('s'), v = q || U.ls('policyPanel.sc');
    if (!v || !U.scen(v)) v = (U.T('P5_ranking')[0] || {}).scenario || (U.official()[0] || {}).id;
    return v;
  };
  U.setCur = function (id) { U.ls('policyPanel.sc', id); };
  U.sname = function (id) { var s = U.scen(id); return s ? s.name : id; };
  /* scenario selector; filter(s) → bool */
  U.scenSel = function (elId, cur, filter) {
    var L = U.scens().filter(function (s) { return !filter || filter(s); });
    var g = {}; L.forEach(function (s) { (g[s.src] = g[s.src] || []).push(s); });
    return '<select id="' + elId + '" class="btn sm scensel" aria-label="Ssenari">' + Object.keys(g).map(function (k) {
      return '<optgroup label="' + U.esc(k === 'rəsmi' ? 'Rəsmi ssenarilər' : k === 'IO nümunəsi' ? 'IO nümunə ssenariləri' : 'Mikrosimulyasiya nümunələri') + '">' + g[k].map(function (s) { return U.opt(s.id, s.name, cur); }).join('') + '</optgroup>';
    }).join('') + '</select>';
  };
  U.bindSel = function (v, elId, fn) { var e = U.$('#' + elId, v); if (e) e.onchange = function () { U.setCur(e.value); fn(e.value); }; };
  /* ---- headline effects ---- */
  U.hl = function (sc, ind, hz) { return U.T('P1_headline').filter(function (r) { return r.scenario === sc && (!ind || r.indicator === ind) && (!hz || r.horizon === hz); }); };
  U.hl1 = function (sc, ind, hz) { return U.hl(sc, ind, hz)[0] || null; };
  U.unitShort = function (u) { u = String(u || ''); return /^%/.test(u) ? '%' : /^f\.b/.test(u) ? 'f.b.' : /mln AZN/.test(u) ? 'mln AZN' : u; };
  U.eff = function (v, unit, dec) { if (!U.isNum(v)) return '—'; var us = U.unitShort(unit); return U.sg(v, dec == null ? (us === 'mln AZN' ? 0 : Math.abs(v) >= 10 ? 1 : 2) : dec) + ' ' + us; };
  /* direction: +1 higher is better, −1 lower is better, 0 neutral */
  U.GOOD = { gdp_real: 1, gdp_nonoil_real: 1, employment: 1, employment_hired: 1, wage_real: 1, hh_disp_real: 1, cons_real: 1, unemp_rate: -1, cpi: -1, infl: -1, debt_pct: -1, budget_balance_pct: 1, budget_balance: 1, fiscal_cost: -1, gini: -1, poverty_rate: -1, poverty_gap: -1, ca_proxy: 1, employment_informal: -1 };
  U.tone = function (ind, v) { var d = U.GOOD[ind]; if (!d || !U.isNum(v) || Math.abs(v) < 1e-9) return ''; return v * d > 0 ? 'up' : 'down'; };
  /* microsimulation headline (by year) → horizon means */
  U.msHz = function (sc, col) {
    var rows = U.T('P3_microsim_headline').filter(function (r) { return r.scenario === sc && U.isNum(r[col]); }), o = {};
    if (!rows.length) return null;
    var s = U.scen(sc), t0 = (s && s.start) || Math.min.apply(null, rows.map(function (r) { return r.year; }));
    rows.forEach(function (r) { var k = r.year - t0, h = k <= 1 ? 'qısa' : k <= 3 ? 'orta' : 'uzun'; (o[h] = o[h] || []).push(r[col]); });
    Object.keys(o).forEach(function (h) { o[h] = col === 'fiscal_cost' ? U.sum(o[h]) : U.sum(o[h]) / o[h].length; });
    return o;
  };
  U.horizonOf = function (y, t0) { var k = y - t0; return k <= 1 ? 'qısa' : k <= 3 ? 'orta' : 'uzun'; };
  U.VMAP.horizon = { 'qısa': 'qısa', 'orta': 'orta', 'uzun': 'uzun' };
  U.VMAP.engine = U.ENGS; U.VMAP.source_engine = U.ENGS;
  U.VMAP.direction = { higher: 'çox yaxşıdır ↑', lower: 'az yaxşıdır ↓' };
  U.VMAP.default_selected = { yes: 'bəli', no: 'xeyr' };
  U.VMAP.stat = { effect: 'təsir', cost: 'xərc', elasticity: 'elastiklik', sum: 'cəm', max: 'maksimum', min: 'minimum', count: 'say', mean: 'orta' };
  U.VMAP.kind = { level: 'səviyyə', rate: 'dərəcə', growth: 'artım', did: 'fərqlərin fərqi (DiD)' };
  U.VMAP.compare = { yes: 'bəli', no: 'xeyr' };
})();
