/* CAEM engine — client-side JS port of the Python FPP engine (model.py + api._fan).
   Runs entirely in the browser: HP output gap, open-economy Phillips curve, smoothed Taylor rule,
   debt dynamics, transparent oil/fiscal/external elasticities, fan charts and editable-data re-anchoring.
   No backend — the static site (data/series.json + data/figures.json) is all it needs. */
const CAEM = (() => {
  let S = null, FIGS = null, E = null, EQ = null;
  const EL = { OIL_GROWTH: 0.02, OIL_FISCAL: 0.12, OIL_CPI: 0.01, PARTNER: 0.30, FX_GROWTH: 0.05, FX_FISCAL: 0.06,
    W_FOREIGN_RATE: 0.5, TOT_OIL: 0.30 };
  const KEYS = ["real_gdp_growth", "nonoil_growth", "output_gap", "trend_growth", "inflation", "policy_rate",
    "gross_debt", "fiscal_balance", "primary_balance", "terms_of_trade"];
  const FAN_LABELS = { real_gdp_growth: "Real GDP growth", inflation: "Inflation (CPI)", policy_rate: "Policy rate",
    fiscal_balance: "Fiscal balance", gross_debt: "Gross public debt" };
  const FAN_UNITS = { real_gdp_growth: "Percent", inflation: "Percent", policy_rate: "Percent",
    fiscal_balance: "Percent of GDP", gross_debt: "Percent of GDP" };
  const FAN_Z = [[90, 1.645], [80, 1.282], [50, 0.674]];
  const r3 = v => Math.round(v * 1000) / 1000;

  // ---- dense linear solve (Gaussian elimination, partial pivot) — n≈34, trivial ----
  function solve(A, b) {
    const n = b.length;
    for (let c = 0; c < n; c++) {
      let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
      [A[c], A[p]] = [A[p], A[c]]; [b[c], b[p]] = [b[p], b[c]];
      const piv = A[c][c];
      for (let r = c + 1; r < n; r++) { const f = A[r][c] / piv; for (let k = c; k < n; k++) A[r][k] -= f * A[c][k]; b[r] -= f * b[c]; }
    }
    const x = new Array(n);
    for (let r = n - 1; r >= 0; r--) { let s = b[r]; for (let k = r + 1; k < n; k++) s -= A[r][k] * x[k]; x[r] = s / A[r][r]; }
    return x;
  }
  // Hodrick–Prescott trend: solve (I + λ·DᵀD) trend = y, D = 2nd-difference matrix.
  function hpTrend(y, lam) {
    const n = y.length, A = Array.from({ length: n }, () => new Array(n).fill(0));
    for (let i = 0; i < n; i++) A[i][i] = 1;
    for (let k = 0; k < n - 2; k++) {
      const idx = [k, k + 1, k + 2], c = [1, -2, 1];
      for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) A[idx[a]][idx[b]] += lam * c[a] * c[b];
    }
    return solve(A, y.slice());
  }

  const sdMap = obj => { const o = {}; if (obj) for (const [y, v] of Object.entries(obj)) o[+y] = v; return o; };
  function buildEngine() {
    const lvl = sdMap(S.series.nonoil_gdp_real_level), p = S.params || {};
    const years = Object.keys(lvl).map(Number).sort((a, b) => a - b);
    const base_growth = {};
    for (let i = 1; i < years.length; i++) base_growth[years[i]] = (lvl[years[i]] / lvl[years[i - 1]] - 1) * 100;
    return {
      years, first_fc: +S.meta.first_forecast, lam: +S.meta.hp_lambda, base_level: Object.assign({}, lvl), base_growth,
      c1: p.cpi_c1_persistence ?? 0.10, c2: p.cpi_c2_import ?? 0.20, c3: p.cpi_c3_gap ?? 0.40,
      imp: sdMap(S.series.imported_inflation), er: sdMap(S.series.er_change), trd: sdMap(S.series.trend_rel_import_price),
      exp: sdMap(S.series.expected_inflation), infl_act: sdMap(S.series.inflation_actual),
      ta: p.taylor_a_inflgap ?? 1.2, tb: p.taylor_b_gap ?? 0.75, trho: p.taylor_rho ?? 0.8,
      rstar: sdMap(S.series.natural_real_rate), pol: sdMap(S.series.policy_rate), ptgt: sdMap(S.series.policy_target),
      debt0: sdMap(S.series.debt_ratio), dg: sdMap(S.series.debt_growth), dpi: sdMap(S.series.debt_inflation),
      dpb: sdMap(S.series.debt_primary_balance), tot: sdMap(S.series.terms_of_trade),
    };
  }
  // extend the forecast horizon to H (=2030): the exogenous input series end 2029, so carry the last
  // value forward one year (a transparent flat-extension of the assumptions) and trim beyond H so every
  // engine figure/fan ends on the same year rather than at 2028/2029.
  // The exogenous input series end 2029, so carry the last value forward to the horizon H (=2030) — a
  // transparent flat-extension of the assumptions — so every engine figure/fan reaches 2030 instead of
  // 2028/2029. The level series (and thus the HP filter) is left untouched, so validated values are preserved;
  // output beyond H is trimmed in pack()/run() via HORIZON.
  function extendHorizon(e, H) {
    const carry = m => { const ys = Object.keys(m).map(Number); if (!ys.length) return; const last = Math.max(...ys); for (let y = last + 1; y <= H; y++) if (!(y in m)) m[y] = m[last]; };
    ["exp", "imp", "er", "trd", "rstar", "ptgt", "dg", "dpi", "dpb", "tot"].forEach(k => { if (e[k]) carry(e[k]); });
    e.horizon = H;
    return e;
  }
  function clone(e) {
    const c = Object.assign({}, e);
    ["base_level", "base_growth", "infl_act", "dg", "dpb"].forEach(k => c[k] = Object.assign({}, e[k]));
    return c;
  }
  function applyActuals(e, actuals) {
    if (!actuals || !Object.keys(actuals).length) return e;
    e.first_fc = Math.max(e.first_fc, Math.max(...Object.keys(actuals).map(Number)) + 1);
    const lvlYears = Object.keys(e.base_level).map(Number).sort((a, b) => a - b);
    for (const [ys, v] of Object.entries(actuals)) {
      const y = +ys;
      if (v.inflation != null) e.infl_act[y] = +v.inflation;
      if (v.gdp_growth != null) e.dg[y] = +v.gdp_growth;
      if (v.fiscal != null) e.dpb[y] = +v.fiscal;
      if (v.nonoil_growth != null && (y - 1) in e.base_level) {
        e.base_growth[y] = +v.nonoil_growth;
        e.base_level[y] = e.base_level[y - 1] * (1 + (+v.nonoil_growth) / 100);
        lvlYears.forEach(yy => { if (yy > y && (yy - 1) in e.base_level) e.base_level[yy] = e.base_level[yy - 1] * (1 + (e.base_growth[yy] || 0) / 100); });
      }
    }
    return e;
  }
  function potential(e, level) {
    const ys = Object.keys(level).map(Number).sort((a, b) => a - b);
    const ln = ys.map(y => Math.log(level[y])), tr = hpTrend(ln, e.lam);
    const trend = {}, gap = {}, tg = {};
    ys.forEach((y, i) => { trend[y] = Math.exp(tr[i]); gap[y] = (ln[i] - tr[i]) * 100; });
    for (let i = 1; i < ys.length; i++) tg[ys[i]] = (Math.exp(tr[i] - tr[i - 1]) - 1) * 100;
    return { trend, gap, trend_growth: tg };
  }
  function inflation(e, gap, af, ipa) {
    af = af || {}; ipa = ipa || {}; const pi = {};
    e.years.forEach(y => {
      if (y < e.first_fc) { pi[y] = e.infl_act[y] ?? null; return; }
      const lag = (pi[y - 1] != null ? pi[y - 1] : e.infl_act[y - 1] ?? null);
      const Ex = e.exp[y] ?? null, push = (e.imp[y] || 0) + (e.er[y] || 0) - (e.trd[y] || 0) + (ipa[y] || 0), g = gap[y];
      pi[y] = (lag == null || Ex == null || g == null) ? null
        : e.c1 * lag + (1 - e.c1 - e.c2) * Ex + e.c2 * push + e.c3 * g + (af[y] || 0);
    });
    return pi;
  }
  function interest(e, infl, gap, af) {
    af = af || {}; const r = {};
    e.years.forEach(y => {
      if (y < e.first_fc) { r[y] = e.pol[y] ?? null; return; }
      const lag = (r[y - 1] != null ? r[y - 1] : e.pol[y - 1] ?? null);
      const rs = e.rstar[y] ?? null, tgt = e.ptgt[y] ?? 4.0, pi = infl[y], g = gap[y];
      r[y] = (lag == null || rs == null || pi == null || g == null) ? null
        : e.trho * lag + (1 - e.trho) * (rs + tgt + e.ta * (pi - tgt) + e.tb * g) + (af[y] || 0);
    });
    return r;
  }
  function debt(e, gdpg, infl, primary) {
    const eff = 3.0, ys = e.years.filter(y => y >= e.first_fc); if (!ys.length) return {};
    const d = {}, out = {};
    d[e.first_fc - 1] = e.debt0[e.first_fc - 1] || e.debt0[e.first_fc] || 15.0;
    ys.forEach(y => {
      const g = (gdpg[y] || 0) / 100, pi = ((infl[y] ?? e.dpi[y]) || 0) / 100, pb = primary[y] || 0;
      out[y] = d[y - 1] * (1 + eff / 100) / ((1 + g) * (1 + pi)) - pb; d[y] = out[y];
    });
    return out;
  }
  function runForecast(e, body) {
    const g = k => +(body[k] || 0);
    const oil = g("oil_price"), imp = g("import_price"), exp = g("export_price"), inflsh = g("inflation_shock"),
      noil = g("nonoil_growth"), part = g("partner_growth"), potg = g("potential_growth"), tax = g("tax"),
      polr = g("policy_rate"), fx = g("exchange_rate"), fr = g("foreign_rate"), rp = g("risk_premium");
    const start = +(body.start || 2026), end = +(body.end || 2030), ys = e.years;
    const infc = y => (y >= e.first_fc && y >= start && y <= end);
    const growth = {}, level = {}; level[ys[0]] = e.base_level[ys[0]];
    for (let i = 1; i < ys.length; i++) {
      const y = ys[i]; let gg = e.base_growth[y];
      if (infc(y)) gg += noil + EL.PARTNER * part + EL.OIL_GROWTH * oil + EL.FX_GROWTH * fx + potg;
      growth[y] = gg; level[y] = level[ys[i - 1]] * (1 + gg / 100);
    }
    const pot = potential(e, level), ipa = {}, sup = {}, irate = {};
    ys.forEach(y => { if (infc(y)) { ipa[y] = imp + fx; sup[y] = inflsh + EL.OIL_CPI * oil; irate[y] = polr + EL.W_FOREIGN_RATE * fr + rp; } });
    const infl = inflation(e, pot.gap, sup, ipa), rate = interest(e, infl, pot.gap, irate), rgdp = {};
    ys.forEach(y => { if (e.dg[y] == null) return; rgdp[y] = e.dg[y] + ((y >= e.first_fc) ? ((growth[y] || 0) - (e.base_growth[y] || 0)) * 0.71 : 0); });
    const pb = {}; ys.forEach(y => { if (y >= e.first_fc) pb[y] = (e.dpb[y] || 0) + (infc(y) ? (EL.OIL_FISCAL * oil + tax + EL.FX_FISCAL * fx) : 0); });
    const gdebt = debt(e, rgdp, infl, pb), tot = {};
    ys.forEach(y => { if (e.tot[y] != null) tot[y] = e.tot[y] + (infc(y) ? (EL.TOT_OIL * oil + exp - imp) : 0); });
    return { years: ys, first_forecast: e.first_fc, nonoil_growth: growth, real_gdp_growth: rgdp,
      trend: pot.trend, output_gap: pot.gap, trend_growth: pot.trend_growth, inflation: infl, policy_rate: rate,
      gross_debt: gdebt, fiscal_balance: pb, primary_balance: Object.assign({}, pb), terms_of_trade: tot };
  }
  function pack(res, H) {
    const o = {};
    KEYS.forEach(k => { if (res[k]) { o[k] = {}; for (const [y, v] of Object.entries(res[k])) if (v != null && (!H || +y <= H)) o[k][y] = r3(v); } });
    return o;
  }
  const pstdev = a => { if (a.length < 2) return 0; const m = a.reduce((x, y) => x + y, 0) / a.length; return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / a.length); };
  // in-sample residual σ of the structural equations (Phillips, Taylor) over history — a more honest
  // fan width than the raw change-stdev for those variables. Cached on the engine instance.
  function residualSigma(e) {
    if (e._residSig) return e._residSig;
    const gap = potential(e, e.base_level).gap, ri = [], rp = [];
    e.years.forEach(y => {
      if (y >= e.first_fc) return;
      const lag = e.infl_act[y - 1], Ex = e.exp[y], g = gap[y], act = e.infl_act[y];
      if (lag != null && Ex != null && g != null && act != null)
        ri.push(e.c1 * lag + (1 - e.c1 - e.c2) * Ex + e.c2 * ((e.imp[y] || 0) + (e.er[y] || 0) - (e.trd[y] || 0)) + e.c3 * g - act);
      const pl = e.pol[y - 1], rs = e.rstar[y], tg = e.ptgt[y] ?? 4.0, pa = e.pol[y], pi = e.infl_act[y];
      if (pl != null && rs != null && pa != null && g != null && pi != null)
        rp.push(e.trho * pl + (1 - e.trho) * (rs + tg + e.ta * (pi - tg) + e.tb * g) - pa);
    });
    const robust = arr => {   // drop the single largest |residual| (e.g. the 2022 inflation spike) then σ
      if (arr.length >= 4) { let mi = 0; arr.forEach((v, j) => { if (Math.abs(v) > Math.abs(arr[mi])) mi = j; }); arr = arr.slice(0, mi).concat(arr.slice(mi + 1)); }
      return arr;
    };
    const cl = v => Math.max(0.3, Math.min(v || 0, 2.2));
    e._residSig = { inflation: ri.length >= 4 ? cl(pstdev(robust(ri))) : null, policy_rate: rp.length >= 4 ? cl(pstdev(robust(rp))) : null };
    return e._residSig;
  }
  function fan(s, ff, sdOverride) {
    const vals = {}; for (const [y, v] of Object.entries(s)) if (v != null) vals[+y] = v;
    const ys = Object.keys(vals).map(Number).sort((a, b) => a - b);
    const hist = ys.filter(y => y < ff).map(y => vals[y]);
    let d = []; for (let i = 1; i < hist.length; i++) d.push(hist[i] - hist[i - 1]);
    if (d.length >= 4) { let mi = 0; d.forEach((v, j) => { if (Math.abs(v) > Math.abs(d[mi])) mi = j; }); d.splice(mi, 1); }
    let sd = (sdOverride != null) ? sdOverride : (d.length >= 2 ? pstdev(d) : 1.3);
    if (sdOverride == null) sd = Math.max(0.4, Math.min(sd, 1.8));
    const out = { years: [], central: [] }; FAN_Z.forEach(([lv]) => { out["lo" + lv] = []; out["hi" + lv] = []; });
    ys.forEach(y => {
      const v = vals[y], h = y >= ff ? (y - ff + 1) : 0;
      out.years.push(y); out.central.push(r3(v));
      FAN_Z.forEach(([lv, z]) => { const hw = h > 0 ? sd * z * Math.sqrt(h) : 0; out["lo" + lv].push(r3(v - hw)); out["hi" + lv].push(r3(v + hw)); });
    });
    return out;
  }
  return {
    async load() {
      S = await (await fetch("data/series.json")).json();
      FIGS = await (await fetch("data/figures.json")).json();
      try { EQ = await (await fetch("data/equations.json")).json(); } catch (e) { EQ = { equations: [] }; }
      E = extendHorizon(buildEngine(), 2030);
    },
    equations() { return EQ || { equations: [] }; },
    meta() {
      return { first_forecast: E.first_fc, caem_vintage: 2025, years: E.years, fan_labels: FAN_LABELS, fan_units: FAN_UNITS,
        scorecard: (S.meta && S.meta.scorecard) || {}, provenance: (S.meta && S.meta.provenance) || {},
        params: { phillips: [E.c1, E.c2, E.c3], taylor: [E.ta, E.tb, E.trho] } };
    },
    figures() { return FIGS; },
    run(body) {
      body = body || {}; const actuals = body.actuals || {};
      const eng = Object.keys(actuals).length ? applyActuals(clone(E), actuals) : E;
      const base = runForecast(eng, { start: body.start, end: body.end });
      const sc = runForecast(eng, body);
      const shock = Object.assign({}, body); delete shock.actuals;
      const f = {}, rs = residualSigma(eng);   // structural-equation residual σ for inflation & policy rate
      ["real_gdp_growth", "inflation", "policy_rate", "fiscal_balance", "gross_debt"].forEach(k => {
        if (sc[k] && Object.keys(sc[k]).length) f[k] = fan(sc[k], eng.first_fc, rs[k]);
      });
      return { baseline: pack(base, eng.horizon), scenario: pack(sc, eng.horizon), shock, fan: f, first_forecast: eng.first_fc };
    }
  };
})();
