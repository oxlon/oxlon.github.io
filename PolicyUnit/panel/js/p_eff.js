/* p_eff.js — Makro və mikro təsirlər (FR1), part 1: horizon tabs, effect helpers on P1_effects (lazy bundle «eff») and
   the macro view (infographic tiles, short text, effect-by-horizon chart, paths by engine incl. the labelled long-run
   extension 2031–2035, baseline vs scenario levels). */
(function () {
  'use strict';
  var U = window.U;
  U.MACRO = ['gdp_real', 'gdp_nonoil_real', 'cpi', 'infl', 'unemp_rate', 'employment', 'employment_hired', 'wage_real', 'hh_disp_real', 'cons_real', 'budget_balance_pct', 'debt_pct', 'fiscal_cost', 'ca_proxy'];
  U.effRows = function (sc, f) { return U.T('P1_effects').filter(function (r) { return r.scenario === sc && (!f || f(r)); }); };
  /* horizon mean of delta_pct (levels: %, rates: f.b.) per engine × indicator */
  U.hzMean = function (rows, hz, col) {
    col = col || 'delta_pct'; var o = {};
    rows.forEach(function (r) { if (r.horizon !== hz || !U.isNum(r[col])) return; var k = r.engine + '|' + r.indicator, x = o[k] = o[k] || { engine: r.engine, indicator: r.indicator, label_az: r.label_az, unit: r.unit, group: r.group, tier: r.tier, method: r.method, note_az: r.note_az, s: 0, n: 0, d: 0 }; x.s += r[col]; x.n++; if (U.isNum(r.delta)) x.d += r.delta; });
    return Object.keys(o).map(function (k) { var x = o[k]; x.v = x.s / x.n; x.dsum = x.d; x.dmean = x.d / x.n; return x; });
  };
  U.isRate = function (unit) { return /^%$|% ÜDM|^%\s*$/.test(String(unit || '')) || unit === '%'; };
  U.hzYears = function (sc, hz) { var r = U.hl(sc).filter(function (x) { return x.horizon === hz; })[0]; return r ? r.years : ''; };
  U.hztabs = function (base, sc, hz) {
    return '<div class="hztabs" role="tablist">' + U.HZ.map(function (h) { var y = U.hzYears(sc, h[0]); return '<a role="tab" href="#/' + base + '?s=' + U.enc(sc) + '&h=' + U.enc(h[0]) + '" class="' + (h[0] === hz ? 'on' : '') + '"><b>' + U.esc(h[1]) + '</b><small>' + U.esc(h[2]) + (y ? ' · ' + U.esc(y) : '') + '</small></a>'; }).join('') + '</div>';
  };
  U.scHead = function (sc) {
    var s = U.scen(sc) || {};
    return '<div class="card pad" style="margin-top:10px"><div class="row" style="display:flex;gap:10px;flex-wrap:wrap;align-items:baseline"><h3 style="margin:0">' + U.esc(s.name || sc) + '</h3><span class="muted small">' + U.esc(s.src || '') + (s.start ? ' · başlanğıc ' + s.start : '') + '</span></div>' +
      (s.desc ? '<p class="small" style="margin:6px 0 0">' + U.esc(s.desc) + '</p>' : '') +
      (s.ins && s.ins.length ? '<div class="chips" style="margin-top:6px">' + s.ins.map(function (i) { var m = U.instr(i.instrument) || {}; return U.fam(m.family) + '<span class="small">' + U.esc(m.name_az || i.instrument) + ': <b>' + U.sg(i.size, 2) + '</b> ' + U.esc(U.UNITN[i.unit] || i.unit || '') + (i.target ? ' · hədəf ' + U.esc(i.target) : '') + (i.financing ? ' · ' + U.esc(U.FINN[i.financing] || i.financing) : '') + ' · ' + U.esc(i.years === 'all' ? 'daimi' : (i.years || []).join(', ')) + '</span>'; }).join(' ') + '</div>' : '') + '</div>';
  };
  function tiles(sc, hz) {
    var L = U.MACRO.map(function (k) { return U.hl1(sc, k, hz); }).filter(Boolean);
    if (!L.length) return U.empty('Bu müddət üçün makro nəticə');
    return '<div class="itiles">' + L.map(function (r) {
      var tn = U.tone(r.indicator, r.effect);
      return '<div class="itile ' + tn + '" title="' + U.esc(r.method + (r.note_az ? ' · ' + r.note_az : '')) + '"><div class="l">' + U.esc(r.label_az) + '</div><div class="v ' + tn + '">' + U.eff(r.effect, r.effect_unit) + '</div><div class="s">' + U.tier(r.tier) + ' ' + U.esc(U.ENGS[r.source_engine] || r.source_engine) + ' · ' + U.esc(r.effect_unit) + '</div></div>';
    }).join('') + '</div>';
  }
  U.hzText = function (sc, hz) {
    var g = U.hl1(sc, 'gdp_real', hz), c = U.hl1(sc, 'cpi', hz), u = U.hl1(sc, 'unemp_rate', hz), b = U.hl1(sc, 'budget_balance_pct', hz), d = U.hl1(sc, 'debt_pct', hz), h = (U.HZ.filter(function (x) { return x[0] === hz; })[0] || [])[1] || hz;
    var t = [];
    if (g) t.push('real ÜDM bazadan orta hesabla <b>' + U.eff(g.effect, g.effect_unit) + '</b> fərqlənir');
    if (c) t.push('qiymət səviyyəsi <b>' + U.eff(c.effect, c.effect_unit) + '</b>');
    if (u) t.push('işsizlik səviyyəsi <b>' + U.eff(u.effect, u.effect_unit) + '</b>');
    if (b) t.push('büdcə balansı <b>' + U.eff(b.effect, b.effect_unit) + '</b> ÜDM-ə');
    if (d) t.push('dövlət borcu <b>' + U.eff(d.effect, d.effect_unit) + '</b> ÜDM-ə');
    return t.length ? '<div class="expl"><b>' + U.esc(h) + ' (' + U.esc(U.hzYears(sc, hz)) + '):</b> ' + t.join(', ') + '. Rəqəmlər ssenari − baza fərqidir (eyni vintaj); rəng — əlverişli (yaşıl) və ya əlverişsiz (qırmızı) istiqamət.' + (hz === 'uzun' ? ' Uzun müddət 2030-dan sonra <b>struktur ekstrapolyasiyadır</b> (kapital, əmək, TFP) — proqnoz deyil, istiqamət göstəricisidir.' : '') + '</div>' : '';
  };
  /* model-gap caveats carried in note_az (e.g. no disemployment channel for the minimum wage) — visible, not only in tooltips */
  U.hzWarn = function (sc) {
    var w = U.uniq(U.hl(sc).map(function (r) { var m = /(YAN TƏSİR XƏBƏRDARLIĞI:[^.]*\.?)/.exec(r.note_az || ''); return m ? m[1] : ''; }).filter(Boolean));
    return w.length ? '<div class="vmsg warn" style="margin:8px 0"><b>Diqqət:</b> ' + w.map(U.esc).join(' ') + '</div>' : '';
  };
  U.effMacro = function (v, sc, hz) {
    var rows = U.effRows(sc, function (r) { return r.group !== 'sektor' && r.group !== 'bazar' && r.engine !== 'io'; });
    v.insertAdjacentHTML('beforeend', U.hzText(sc, hz) + U.hzWarn(sc) + tiles(sc, hz) +
      U.sec('Müddətlər üzrə təsir', 'Əsas göstəricilər: qısa, orta və uzun müddət (əsas metod)', '<div class="card pad"><div id="e-hz" class="ch"></div></div>') +
      U.sec('İllər üzrə yol — metodlara görə', 'Bazadan fərq (səviyyələr üçün %, dərəcələr üçün f.b.); boz zona — 2031–2035 uzun müddət ekstrapolyasiyası', '<div class="toolbar" style="margin-top:0">' + U.sel('e-ind', U.uniq(rows.map(function (r) { return r.indicator; })).filter(function (k) { return U.MACRO.indexOf(k) >= 0; }).map(function (k) { return [k, (rows.filter(function (r) { return r.indicator === k; })[0] || {}).label_az || k]; }), U.HQ.get('i') || 'gdp_real') + '</div><div class="cols2"><div class="card pad"><div id="e-path" class="ch"></div><p class="small" id="e-bad"></p></div><div class="card pad"><div id="e-lvl" class="ch"></div><p class="small muted" id="e-lvl-n"></p></div></div>') + U.rangeSec(sc));
    var K = ['gdp_real', 'gdp_nonoil_real', 'cpi', 'unemp_rate', 'employment_hired', 'wage_real', 'budget_balance_pct', 'debt_pct'].filter(function (k) { return U.hl(sc, k).length; });
    var lab = K.map(function (k) { var r = U.hl(sc, k)[0]; return r.label_az + ' (' + U.unitShort(r.effect_unit) + ')'; });
    U.barH(U.$('#e-hz', v), lab, null, 'bazadan fərq', { sets: U.HZ.map(function (h, i) { return { name: h[1], c: ['#0E6F7C', '#1F6FB2', '#8A5300'][i], v: K.map(function (k) { var r = U.hl1(sc, k, h[0]); return r ? r.effect : null; }) }; }) });
    var draw = function (ind) {
      var R = rows.filter(function (r) { return r.indicator === ind; }), by = U.by(R, 'engine'), sets = [];
      Object.keys(by).sort().forEach(function (e) { var x = by[e].slice().sort(function (a, b) { return a.year - b.year; }); var bad = by[e].some(function (r) { return U.BAD(r.note_az); }); sets.push({ name: (U.ENG[e] || e) + (bad ? ' — ETİBARSIZ' : ''), x: x.map(function (r) { return r.year; }), y: x.map(function (r) { return r.delta_pct; }), c: U.ENGC[e], dash: e === 'longrun' ? 'dot' : e === 'caem' ? 'dash' : 'solid', mode: 'lines+markers' }); });
      var bd = R.filter(function (r) { return U.BAD(r.note_az); })[0]; U.$('#e-bad', v).innerHTML = bd ? U.noteFmt(bd.note_az) : '';
      U.lines(U.$('#e-path', v), sets, U.isRate((R[0] || {}).unit) ? 'f.b.' : '% baza ilə fərq', { years: true, zero: true, fc: 2031, h: 320 });
      var L = R.filter(function (r) { return (r.engine === 'micro' || r.engine === 'longrun') && U.isNum(r.baseline); }).sort(function (a, b) { return a.year - b.year; });
      if (L.length) U.lines(U.$('#e-lvl', v), [{ name: 'Baza', x: L.map(function (r) { return r.year; }), y: L.map(function (r) { return r.baseline; }), c: '#E07B00', dash: 'dash' }, { name: 'Ssenari', x: L.map(function (r) { return r.year; }), y: L.map(function (r) { return r.value; }), c: '#0E6F7C' }], (R[0] || {}).unit || '', { years: true, fc: 2031, h: 320 });
      else U.$('#e-lvl', v).innerHTML = '<p class="muted small">Səviyyə yolu yoxdur (CAEM yalnız sapmaları verir).</p>';
      U.$('#e-lvl-n', v).textContent = 'Səviyyələr: MikroUnit (2026–2030) və uzun müddət ekstrapolyasiyası (2031–2035). Vahid: ' + ((R[0] || {}).unit || '—') + '.';
    };
    draw(U.$('#e-ind', v).value);
    U.$('#e-ind', v).onchange = function (e) { draw(e.target.value); };
  };
})();
