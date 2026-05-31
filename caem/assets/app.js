/* CAEM interactive dashboard — CAEM figures + live FPP engine (scenario recompute + fan charts). */
let FIGS = [], GROUPS = [], CUR = null, RUN = null, META = null, BASE = null, FAN0 = null, STATIC_RUN0 = null, NFIG = 0, NLIVE = 0;
let ACTUALS = {}, LIVE_FF = null;   // editable data: user-entered actuals + effective first-forecast year
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
const enc = encodeURIComponent, dec = decodeURIComponent;
const clean = n => (n || "").replace(/\s+/g, " ").trim();
const HUES = [210, 28, 264, 150, 344, 190, 45, 122, 232, 14, 300, 168, 255, 86, 200, 320, 38, 175, 270, 100, 8, 220];
const tone = (h, j) => `hsl(${h},54%,${36 + (j % 6) * 7}%)`;
const headCol = h => `hsl(${h},48%,40%)`;
const softBg = h => `hsl(${h},60%,96%)`;
const PAL = ["#2f6f8f", "#c98a3c", "#5b8c5a", "#9b5d8a", "#3f9fa6", "#b5683f", "#7585bd", "#94a14a", "#a0526d", "#6a8caf", "#caa45a"];
const DASH = ["solid", "dash", "dot", "dashdot", "longdash", "longdashdot"];
const isTotal = n => /\b(total|gdp growth|real gdp|overall balance|headline|sum|net|forecast)\b/i.test(n || "");
const COMPO = /contribution|share of|sources of|composition|decompos|expenditure item|revenue item|financing|by sector|use of|breakdown|growth accounting/i;
// Bank-of-England "river of blood" — red tones, lighter outward
const FAN_BANDS = [["lo90", "hi90", "rgba(173,42,53,0.13)", "90%"], ["lo80", "hi80", "rgba(173,42,53,0.24)", "80%"], ["lo50", "hi50", "rgba(173,42,53,0.40)", "50%"]];
const FAN_CENTRAL = "#7d1620";
const FIELDS = ["oil_price", "import_price", "export_price", "inflation_shock", "nonoil_growth",
  "partner_growth", "potential_growth", "tax", "policy_rate", "exchange_rate", "foreign_rate", "risk_premium"];
// figures that ARE a scenario input — shocking it transforms the figure's own path (exact, not modelled).
// kind "level" = the shock is a % change to the level; "rate" = a sustained pp change to a rate series.
const SHOCK_FIG = [
  { re: /oil price|petroleum|crude/i, field: "oil_price", kind: "level" },
  { re: /import price/i, field: "import_price", kind: "level" },
  { re: /nominal exchange rate|exchange rate \(%/i, field: "exchange_rate", kind: "level" },
  { re: /partner/i, field: "partner_growth", kind: "rate" },
];
const shockMatch = title => SHOCK_FIG.find(s => s.re.test(title || ""));
const isLive = f => !!(f.engine_var || (shockMatch(f.title) && !f.radar));
// transform a series under a shock: rate → +val every forecast year; level on a %-change series → one-time
// +val step in the first forecast year; level on a level series → ×(1+val/100) every forecast year.
function shockSeries(yArr, xArr, sf, val, ff, isPct) {
  return xArr.map((yr, i) => yArr[i] == null ? null : yr < ff ? yArr[i]
    : sf.kind === "rate" ? yArr[i] + val
      : isPct ? (yr === ff ? yArr[i] + val : yArr[i])
        : yArr[i] * (1 + val / 100));
}

const loadJSON = async path => {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`Cannot load ${path}`);
  return r.json();
};
const clone = obj => JSON.parse(JSON.stringify(obj || {}));
const keysOf = obj => Object.keys(obj || {}).map(Number).sort((a, b) => a - b);
const valAt = (obj, y) => obj && obj[String(y)] != null ? obj[String(y)] : null;
const setAt = (obj, y, v) => { if (obj && v != null && Number.isFinite(v)) obj[String(y)] = Math.round(v * 1000) / 1000; };
function fanFromMap(map, firstForecast) {
  const years = keysOf(map);
  const values = years.map(y => valAt(map, y));
  const hist = years.map((y, i) => y < firstForecast ? values[i] : null).filter(v => v != null);
  let diffs = [];
  for (let i = 1; i < hist.length; i++) diffs.push(hist[i] - hist[i - 1]);
  if (diffs.length >= 4) {
    let ix = 0; diffs.forEach((v, i) => { if (Math.abs(v) > Math.abs(diffs[ix])) ix = i; });
    diffs.splice(ix, 1);
  }
  const mean = diffs.length ? diffs.reduce((a, v) => a + v, 0) / diffs.length : 0;
  let sd = diffs.length >= 2 ? Math.sqrt(diffs.reduce((a, v) => a + (v - mean) ** 2, 0) / diffs.length) : 1.3;
  sd = Math.max(0.4, Math.min(sd || 1.3, 1.8));
  const out = { years, central: values.map(v => Math.round(v * 1000) / 1000), lo50: [], hi50: [], lo80: [], hi80: [], lo90: [], hi90: [] };
  [[50, 0.674], [80, 1.282], [90, 1.645]].forEach(([lvl, z]) => {
    years.forEach((y, i) => {
      const h = y >= firstForecast ? y - firstForecast + 1 : 0;
      const hw = h > 0 ? sd * z * Math.sqrt(h) : 0;
      out[`lo${lvl}`].push(Math.round((values[i] - hw) * 1000) / 1000);
      out[`hi${lvl}`].push(Math.round((values[i] + hw) * 1000) / 1000);
    });
  });
  return out;
}
function staticRun(body = {}) {
  const baseRun = clone(STATIC_RUN0);
  const baseline = clone(baseRun.baseline);
  const scenario = clone(baseline);
  const shock = {};
  FIELDS.forEach(f => shock[f] = +body[f] || 0);

  let firstForecast = baseRun.first_forecast || META.first_forecast || 2026;
  const actuals = body.actuals || {};
  const actualYears = Object.keys(actuals).map(Number).filter(Number.isFinite);
  if (actualYears.length) firstForecast = Math.max(firstForecast, Math.max(...actualYears) + 1);
  actualYears.forEach(y => {
    const rec = actuals[String(y)] || {};
    if (rec.gdp_growth != null) setAt(baseline.real_gdp_growth, y, +rec.gdp_growth);
    if (rec.nonoil_growth != null) setAt(baseline.nonoil_growth, y, +rec.nonoil_growth);
    if (rec.inflation != null) setAt(baseline.inflation, y, +rec.inflation);
    if (rec.fiscal != null) {
      setAt(baseline.fiscal_balance, y, +rec.fiscal);
      setAt(baseline.primary_balance, y, +rec.fiscal);
    }
  });
  Object.assign(scenario, clone(baseline));

  const start = +body.start || firstForecast, end = +body.end || 2030;
  const inRange = y => y >= firstForecast && y >= start && y <= end;
  const growthDelta = shock.nonoil_growth + 0.30 * shock.partner_growth + 0.02 * shock.oil_price + 0.05 * shock.exchange_rate + shock.potential_growth;
  const gdpDelta = 0.71 * growthDelta;
  const inflationDelta = shock.inflation_shock + 0.01 * shock.oil_price + 0.20 * (shock.import_price + shock.exchange_rate);
  const fiscalDelta = 0.12 * shock.oil_price + shock.tax + 0.06 * shock.exchange_rate;
  const rateDelta = shock.policy_rate + 0.50 * shock.foreign_rate + shock.risk_premium;
  const termsDelta = 0.30 * shock.oil_price + shock.export_price - shock.import_price;
  const deltas = {
    nonoil_growth: growthDelta,
    real_gdp_growth: gdpDelta,
    output_gap: 0.35 * growthDelta,
    trend_growth: shock.potential_growth,
    inflation: inflationDelta,
    policy_rate: rateDelta + 0.20 * inflationDelta,
    fiscal_balance: fiscalDelta,
    primary_balance: fiscalDelta,
    terms_of_trade: termsDelta
  };
  Object.entries(deltas).forEach(([name, delta]) => {
    if (!scenario[name] || !Number.isFinite(delta) || delta === 0) return;
    keysOf(scenario[name]).forEach(y => { if (inRange(y)) setAt(scenario[name], y, valAt(scenario[name], y) + delta); });
  });
  if (scenario.gross_debt) {
    let cumulative = 0;
    keysOf(scenario.gross_debt).forEach(y => {
      if (!inRange(y)) return;
      cumulative += fiscalDelta;
      const debtDelta = -0.85 * cumulative - 0.20 * gdpDelta + 0.08 * rateDelta;
      setAt(scenario.gross_debt, y, valAt(baseline.gross_debt, y) + debtDelta);
    });
  }
  const fan = {};
  Object.keys(META.fan_labels || {}).forEach(k => { if (scenario[k]) fan[k] = fanFromMap(scenario[k], firstForecast); });
  return { baseline, scenario, shock, fan, first_forecast: firstForecast };
}

function detectTotalIdx(series) {
  for (let k = 0; k < series.length; k++) {
    let ok = 0, cnt = 0;
    series[k].y.forEach((v, i) => {
      if (v == null) return;
      const sum = series.reduce((a, s, j) => a + (j !== k && s.y[i] != null ? s.y[i] : 0), 0);
      cnt++; if (Math.abs(v - sum) <= Math.max(0.5, Math.abs(v) * 0.04)) ok++;
    });
    if (cnt >= 2 && ok / cnt >= 0.8) return k;
  }
  return -1;
}

async function init() {
  META = await loadJSON("data/meta.json");
  const data = await loadJSON("data/figures.json");
  FIGS = data.figures; NFIG = data.n; NLIVE = data.engine_driven;
  STATIC_RUN0 = await loadJSON("data/run_baseline.json");
  BASE = STATIC_RUN0.baseline || {}; FAN0 = STATIC_RUN0.fan || {};
  $("#meta").innerHTML = `${NFIG} figures · ${NLIVE} live · forecast <b>${META.first_forecast}+</b>`;
  const seen = {};
  FIGS.forEach(f => { (seen[f.sheet] = seen[f.sheet] || []).push(f); });
  GROUPS = Object.keys(seen).map((s, i) => ({ sheet: s, figs: seen[s], hue: HUES[i % HUES.length] }));
  buildNav(); wireRun();
  $("#brand").style.cursor = "pointer"; $("#brand").onclick = showHome;
  $("#infoscrim").onclick = closeInfo; $("#infoclose").onclick = closeInfo;
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeInfo(); });
  showHome();
}

const SUMMARY_SHEETS = new Set(["6b. Forecasts Summary", "A1. At a glance", "Fancharts", "7. Scenario", "8b. Summary"]);
function buildNav() {
  const navlink = g => {
    const live = g.figs.filter(f => isLive(f)).length, sm = SUMMARY_SHEETS.has(g.sheet);
    return `<div class="navlink${sm ? " summary" : ""}" data-s="${enc(g.sheet)}" style="--hue:${g.hue};border-left-color:hsl(${g.hue},55%,68%)">
      <span class="cdot" style="background:${headCol(g.hue)}"></span><span class="nl">${esc(g.sheet || "—")}</span>
      <span class="n">${g.figs.length}${live ? " · " + live + "▲" : ""}</span></div>`;
  };
  const summ = GROUPS.filter(g => SUMMARY_SHEETS.has(g.sheet)), detail = GROUPS.filter(g => !SUMMARY_SHEETS.has(g.sheet));
  $("#nav").innerHTML =
    `<div class="navhome" id="navhome">🏠 Home &amp; overview</div>
     <div class="navlive" id="navlive">📈 Live forecast &amp; fan charts</div>
     <div class="navsec">★ Summary dashboards</div>` + summ.map(navlink).join("") +
    `<div class="navsec">Detailed analysis <span>figures · live ▲</span></div>` + detail.map(navlink).join("");
  document.querySelectorAll("#nav .navlink").forEach(a => a.onclick = () => showGroup(dec(a.dataset.s)));
  $("#navhome").onclick = showHome;
  $("#navlive").onclick = showLive;
}

function setActive(mode) {
  $("#navhome").classList.toggle("active", mode === "home");
  $("#navlive").classList.toggle("active", mode === "live");
  document.querySelectorAll("#nav .navlink").forEach(a => {
    const h = +a.style.getPropertyValue("--hue"), on = mode === dec(a.dataset.s);
    a.classList.toggle("active", on);
    a.style.background = on ? softBg(h) : "";
    a.style.borderLeftColor = on ? headCol(h) : `hsl(${h},55%,68%)`;
  });
}

/* ---------------- home / overview ---------------- */
function val(v) { return (v == null || isNaN(v)) ? "—" : (Math.round(v * 10) / 10).toFixed(1); }
function kpi(label, varname, yr, unit, sign) {
  const v = BASE && BASE[varname] ? BASE[varname][String(yr)] : null;
  const cls = v == null ? "" : v > 0.05 ? "pos" : v < -0.05 ? "neg" : "";
  const s = sign && v > 0 ? "+" : "";
  return `<div class="kpi"><div class="v ${sign ? cls : ""}">${s}${val(v)}<span class="vu">${unit}</span></div>
    <div class="k">${esc(label)}</div><div class="y">${yr} forecast</div></div>`;
}
function showHome() {
  CUR = null; setActive("home");
  const p = META.params || {};
  const gcards = GROUPS.map(g => {
    const live = g.figs.filter(f => f.engine_var).length;
    return `<div class="gcard" data-go="${enc(g.sheet)}" style="border-left:4px solid ${headCol(g.hue)}">
      <div class="gn">${esc(g.sheet)}</div><div class="gs">${g.figs.length} figures${live ? ` · ${live} live` : ""}</div></div>`;
  }).join("");
  $("#view").innerHTML = `
    <div class="home-hero">
      <div class="he-eyebrow">FINANCIAL PROGRAMMING · MACRO-FISCAL MODEL</div>
      <h1>Republic of Azerbaijan — live macro-fiscal forecasting</h1>
      <p>A web implementation of the IMF CAEM Financial-Programming model, calibrated to Azerbaijan, with a
      <b>recompute engine</b>: change an assumption in the Scenario console and the forecast — output gap, inflation,
      interest rate, debt and the fiscal balance — is recomputed and overlaid on the charts. ${NFIG} figures across
      ${GROUPS.length} CAEM dashboards; ${NLIVE} recompute live, plus a <b>Live forecast</b> view with fan charts.</p>
      <div class="he-cta" id="ctaLive">📈 Open the Live forecast &amp; fan charts →</div>
    </div>
    <div class="hsec"><h2>Baseline forecast — model central path <span class="tagi">model projections (2026+), not outturns</span></h2>
      <div class="kpis">
        ${kpi("Real GDP growth", "real_gdp_growth", 2026, "%", true)}
        ${kpi("Inflation (CPI)", "inflation", 2026, "%", false)}
        ${kpi("Policy rate", "policy_rate", 2026, "%", false)}
        ${kpi("Fiscal balance", "fiscal_balance", 2028, "%GDP", true)}
        ${kpi("Gross public debt", "gross_debt", 2029, "%GDP", false)}
      </div>
    </div>
    <div class="hsec">${scorecardHTML()}</div>

    <div class="hsec"><h2>The engine — reproduced from CAEM, validated</h2>
      <div class="grid3">
        <div class="mcard"><b>Output gap</b><span>HP filter (λ=100) on log non-oil GDP — CAEM sheet B1a.</span><i>≈0.18 pp</i></div>
        <div class="mcard"><b>Inflation</b><span>Open-economy Phillips curve: persistence, expectations, import pass-through, gap (1b).</span><i>≈0.01 pp</i></div>
        <div class="mcard"><b>Interest rate</b><span>Smoothed Taylor rule with inflation &amp; output-gap response (1c).</span><i>≈0.07 pp</i></div>
        <div class="mcard"><b>Public debt</b><span>Standard ratio recursion — growth, inflation, primary balance (3b).</span><i>dynamics</i></div>
        <div class="mcard"><b>Fiscal &amp; oil</b><span>Oil-price → revenue/balance/debt and growth, via transparent elasticities.</span><i>scenario</i></div>
        <div class="mcard"><b>Fan charts</b><span>Confidence bands widen with the forecast horizon around the engine's central path.</span><i>uncertainty</i></div>
      </div>
    </div>

    <div class="hsec"><h2>How to use it</h2>
      <ol class="how">
        <li><b>Pick a view</b> — <b>Live forecast</b> for the engine's projections &amp; fan charts, or any CAEM dashboard on the left.</li>
        <li><b>Enter shocks</b> in the Scenario console (e.g. Oil price −30%), set the years, and press <b>Run</b>.</li>
        <li>The <span class="livechip">LIVE</span> figures recompute and overlay the <b>scenario</b> (dashed red) on the baseline; <b>Reset</b> clears it.</li>
        <li><b>Update data</b> when new outturns are published — enter a year's actuals and the model re-anchors and re-forecasts from the next year. Export any forecast to <b>CSV</b> from the Live page.</li>
      </ol>
    </div>

    <div class="hsec"><h2>Explore the CAEM dashboards</h2><div class="grid3 gc">${gcards}</div></div>
    <div class="hfoot">CAEM Financial-Programming model · phillips ${(p.phillips || []).join("/")} · taylor ${(p.taylor || []).join("/")} · reproduced &amp; extended in Python. Shaded region = forecast period (${META.first_forecast}+).</div>`;
  document.querySelectorAll(".gcard").forEach(c => c.onclick = () => showGroup(dec(c.dataset.go)));
  $("#ctaLive").onclick = showLive;
  window.scrollTo({ top: 0 });
}

/* ---------------- live forecast (engine) ---------------- */
function showLive() {
  CUR = null; setActive("live");
  const fan = (RUN && RUN.fan) || FAN0 || {};
  const labels = META.fan_labels || {}, units = META.fan_units || {};
  const onScn = !!(RUN && Object.values(RUN.shock || {}).some(v => typeof v === "number" && v));
  const shockTxt = onScn ? FIELDS.filter(f => RUN.shock[f]).map(f => `${f.replace(/_/g, " ")} ${RUN.shock[f] > 0 ? "+" : ""}${RUN.shock[f]}`).join(", ") : "";
  const engFigs = FIGS.filter(f => f.engine_var);
  $("#view").innerHTML = `
    <div class="ghead" style="color:#1f5a8c;border-color:#1f5a8c">📈 Live forecast <button id="dlcsv" class="dlbtn">⤓ Download CSV</button></div>
    <div class="gsub">The engine's central forecast with <b>fan charts</b> (confidence bands that widen with the horizon), then every
      live figure. <b>2025 = official outturn; forecast 2026+.</b> ${onScn ? `Scenario active: <b>${esc(shockTxt)}</b> — dashed red overlays the baseline.` : "Run a scenario above to overlay it."}</div>
    ${impactHTML()}
    ${scorecardHTML()}
    <div class="note-eco">Transmission: oil price → non-oil growth, the budget balance &amp; debt, and domestic inflation; the Phillips curve sets inflation from the output gap &amp; import prices; the Taylor rule sets the policy rate; debt evolves with growth, inflation &amp; the primary balance.</div>
    <h3 class="lh">Fan charts — central path &amp; uncertainty (Bank-of-England style)</h3>
    <div class="figgrid" id="fangrid"></div>
    <h3 class="lh">All live figures (recompute with the scenario)</h3>
    <div class="figgrid" id="livegrid"></div>`;
  const fg = $("#fangrid");
  Object.keys(labels).forEach(k => {
    if (!fan[k]) return;
    const card = document.createElement("div"); card.className = "figcard"; card.style.borderTopColor = "#7d1620";
    card.innerHTML = `<div class="ft">${esc(labels[k])}<span class="live live-fan">FAN</span></div>
      <div class="fu">${esc(units[k] || "")}</div><div class="fc" id="fan_${k}"></div>`;
    fg.appendChild(card); drawFan(`fan_${k}`, fan[k]);
    attachInfo(card, { title: labels[k], unit: units[k], sheet: "Live engine", engine_var: k, fan: true, series: [] });
  });
  const lg = $("#livegrid");
  engFigs.forEach((f, i) => {
    const card = document.createElement("div"); card.className = "figcard"; card.style.borderTopColor = "#2f7d54";
    card.innerHTML = `<div class="ft">${esc(f.title)}<span class="live">LIVE</span></div>
      ${f.unit ? `<div class="fu">${esc(f.unit)}</div>` : ""}<div class="fc" id="lf${i}"></div>`;
    lg.appendChild(card); drawFig(`lf${i}`, f, "#2f7d54"); attachInfo(card, f);
  });
  $("#dlcsv").onclick = downloadCSV;
  window.scrollTo({ top: 0 });
}

/* export the live baseline + scenario forecast as CSV (for the Ministry) */
function downloadCSV() {
  const src = RUN || { baseline: BASE, scenario: BASE };
  const vars = ["real_gdp_growth", "nonoil_growth", "output_gap", "inflation", "policy_rate",
    "fiscal_balance", "primary_balance", "gross_debt", "terms_of_trade"];
  const yrs = Object.keys(BASE.real_gdp_growth || {}).map(Number).sort((a, b) => a - b);
  const rows = [["variable", "scope"].concat(yrs)];
  vars.forEach(v => ["baseline", "scenario"].forEach(sc => {
    const d = (src[sc] || {})[v] || {};
    if (Object.keys(d).length) rows.push([v, sc].concat(yrs.map(y => d[y] != null ? d[y] : "")));
  }));
  const csv = "# CAEM macro-fiscal forecast" + (LIVE_FF ? " (first forecast " + LIVE_FF + ")" : "") + "\n" +
    rows.map(r => r.join(",")).join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  a.download = "caem_forecast.csv"; a.click(); URL.revokeObjectURL(a.href);
}

/* ---------------- a CAEM dashboard ---------------- */
function showGroup(sheet) {
  CUR = sheet; setActive(sheet);
  const g = GROUPS.find(x => x.sheet === sheet);
  const live = g.figs.filter(f => isLive(f)).length;
  const solo = g.figs.length <= 2;            // 1–2 figures → render large for detail
  $("#view").innerHTML = `<div class="ghead" style="color:${headCol(g.hue)};border-color:${headCol(g.hue)}">${esc(sheet)}</div>
    <div class="gsub">${g.figs.length} figures from CAEM sheet “${esc(sheet)}”${live ? ` · ${live} recompute live` : ""}.
    ${RUN ? "Dashed red = current scenario." : "Run a scenario above to overlay it."} Shaded band = forecast (${LIVE_FF || META.first_forecast}+); 2025 = last actual.</div>
    <div class="figgrid${solo ? " solo" : ""}" id="grid"></div>`;
  const grid = $("#grid");
  g.figs.forEach((f, i) => {
    const t = tone(g.hue, i);
    const card = document.createElement("div"); card.className = "figcard" + (solo ? " big" : ""); card.style.borderTopColor = t;
    card.innerHTML = `<div class="ft">${esc(f.title)}${isLive(f) ? '<span class="live">LIVE</span>' : ""}</div>
      ${f.unit ? `<div class="fu">${esc(f.unit)}</div>` : ""}<div class="fc" id="fc${i}"></div>`;
    grid.appendChild(card);
    drawFig(`fc${i}`, f, t, solo);
    attachInfo(card, f);
  });
  window.scrollTo({ top: 0 });
}

/* ---------------- forecast-region shading shared by time-series charts ---------------- */
function fcShapes(xs, vintage) {
  const ff = vintage || META.first_forecast, mn = Math.min(...xs), mx = Math.max(...xs), sh = [];
  if (xs.length && mn < ff && mx >= ff) {
    sh.push({ type: "rect", xref: "x", yref: "paper", x0: ff - 0.5, x1: mx + 0.5, y0: 0, y1: 1, fillcolor: "rgba(120,130,145,0.08)", line: { width: 0 }, layer: "below" });
    sh.push({ type: "line", x0: ff - 0.5, x1: ff - 0.5, yref: "paper", y0: 0, y1: 1, line: { color: "#c2c8d0", width: 1, dash: "dot" } });
  }
  return sh;
}
const tickStep = xs => (xs.length && (Math.max(...xs) - Math.min(...xs)) > 22) ? 4 : 2;  // consistent: 2-yr ticks (4 only for very long histories)
const hexA = (h, a) => { const n = parseInt(h.slice(1), 16); return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`; };
const baseLayout = (xyear, shapes, h, b, dtick) => ({
  height: h, margin: { l: 46, r: 12, t: 8, b: b }, font: { family: "Inter,sans-serif", size: 10, color: "#4a4a4a" },
  plot_bgcolor: "#fff", paper_bgcolor: "#fff", barmode: "relative", bargap: 0.16, showlegend: false, shapes,
  xaxis: xyear ? { tickformat: "d", showgrid: false, dtick: dtick || 2, tick0: 2026, ticklen: 3 } : { showgrid: false, ticklen: 3 },
  yaxis: { gridcolor: "#eef1f4", zeroline: true, zerolinecolor: "#d2d7dd", automargin: true }
});
/* radar / spider chart — e.g. Balance of risks across dimensions */
function drawRadar(div, f) {
  const cats = f.catlabels, traces = f.series.map((s, k) => {
    const c = PAL[k % PAL.length], nm = clean(s.name) || ("Series " + (k + 1));
    return {
      type: "scatterpolar", r: s.y.slice(0, cats.length).concat([s.y[0]]), theta: cats.concat([cats[0]]),
      name: nm, fill: "toself", fillcolor: hexA(c, 0.16), line: { color: c, width: 2 },
      hovertemplate: "%{theta}: %{r}<extra>" + esc(nm) + "</extra>"
    };
  });
  Plotly.react(div, traces, {
    height: 380, margin: { l: 64, r: 64, t: 22, b: 30 }, font: { family: "Inter,sans-serif", size: 10.5, color: "#4a4a4a" },
    paper_bgcolor: "#fff", showlegend: false,
    polar: { bgcolor: "#fff", radialaxis: { angle: 90, tickfont: { size: 9 }, gridcolor: "#eef1f4" }, angularaxis: { tickfont: { size: 11 }, rotation: 90, direction: "clockwise" } }
  }, { responsive: true, displayModeBar: false });
  htmlLegend(document.getElementById(div).closest(".figcard"), f.series.map((s, k) => ({ name: clean(s.name) || ("Series " + (k + 1)), color: PAL[k % PAL.length], w: 2.4 })));
}
const DASHARR = { "": "", solid: "", dash: "5,3", dot: "1,3", dashdot: "5,2,1,2", longdash: "8,4", longdashdot: "8,3,1,3" };
function legSwatch(l) {                     // line items show a line sample (colour + dash); bars show a chip
  if (l.bar) return `<i class="sw-bar" style="background:${l.color}"></i>`;
  const da = DASHARR[l.dash || ""] || "";
  return `<svg class="sw-line" width="17" height="9"><line x1="0" y1="5" x2="17" y2="5" stroke="${l.color}" stroke-width="${l.w || 2.2}"${da ? ` stroke-dasharray="${da}"` : ""}/></svg>`;
}
function htmlLegend(card, items) {
  const old = card.querySelector(".flgd"); if (old) old.remove();
  if (items.length) card.insertAdjacentHTML("beforeend",
    `<div class="flgd">` + items.map(l => `<span class="lg">${legSwatch(l)}${esc(l.name)}</span>`).join("") + `</div>`);
}

// insert a zero-width anchor exactly at the forecast boundary (ff−0.5) so the fan opens AFTER the
// dashed line, not from the last actual year — i.e. forecasting begins after the line.
function boundaryAnchor(fan, ff) {
  const i = fan.years.indexOf(ff);
  if (i <= 0) return fan;
  const c = (fan.central[i - 1] + fan.central[i]) / 2, out = { years: fan.years.slice(), central: fan.central.slice() };
  out.years.splice(i, 0, ff - 0.5); out.central.splice(i, 0, c);
  ["lo50", "hi50", "lo80", "hi80", "lo90", "hi90"].forEach(k => { out[k] = fan[k].slice(); out[k].splice(i, 0, c); });
  return out;
}
/* ---------------- fan chart ---------------- */
function drawFan(div, fan, big) {
  fan = boundaryAnchor(fan, LIVE_FF || META.first_forecast);
  const x = fan.years, traces = [];
  FAN_BANDS.forEach(([lo, hi, col]) => {
    traces.push({ x, y: fan[hi], mode: "lines", line: { width: 0, color: "rgba(0,0,0,0)" }, hoverinfo: "skip", showlegend: false });
    traces.push({ x, y: fan[lo], mode: "lines", line: { width: 0, color: "rgba(0,0,0,0)" }, fill: "tonexty", fillcolor: col, hoverinfo: "skip", showlegend: false });
  });
  traces.push({ x, y: fan.central, mode: "lines", line: { color: FAN_CENTRAL, width: 2.6 }, hovertemplate: "%{x}: %{y:.2f}<extra>central</extra>", showlegend: false });
  Plotly.react(div, traces, baseLayout(true, fcShapes(x, LIVE_FF || META.first_forecast), big ? 320 : 214, 24, tickStep(x)), { responsive: true, displayModeBar: false });
  const card = document.getElementById(div).closest(".figcard");
  htmlLegend(card, [{ name: "Central forecast", color: FAN_CENTRAL, w: 2.6 }, { name: "50%", color: "rgba(173,42,53,0.55)", bar: true }, { name: "80%", color: "rgba(173,42,53,0.34)", bar: true }, { name: "90%", color: "rgba(173,42,53,0.2)", bar: true }]);
}

/* generate a fan (central + widening 50/80/90% bands) from one observed series */
function genFan(s) {
  if (!s) return null;
  const ff = META.first_forecast;
  const pts = s.x.map((x, i) => [x, s.y[i]]).filter(p => p[1] != null && typeof p[0] === "number");
  if (pts.length < 3) return null;
  const hist = pts.filter(p => p[0] < ff).map(p => p[1]);
  let d = []; for (let i = 1; i < hist.length; i++) d.push(hist[i] - hist[i - 1]);
  if (d.length >= 4) { let mi = 0; d.forEach((v, j) => { if (Math.abs(v) > Math.abs(d[mi])) mi = j; }); d.splice(mi, 1); }
  const m = d.length ? d.reduce((a, c) => a + c, 0) / d.length : 0;
  const sd = (d.length ? Math.sqrt(d.reduce((a, c) => a + (c - m) ** 2, 0) / d.length) : 0) || Math.abs(pts[pts.length - 1][1] || 1) * 0.05 || 1;
  const out = { years: [], central: [], lo50: [], hi50: [], lo80: [], hi80: [], lo90: [], hi90: [] };
  const Z = [[50, 0.674], [80, 1.282], [90, 1.645]];
  pts.forEach(([x, v]) => {
    out.years.push(x); out.central.push(v);
    const h = x >= ff ? x - ff + 1 : 0;
    Z.forEach(([lv, z]) => { const hw = h > 0 ? sd * z * Math.sqrt(h) : 0; out["lo" + lv].push(v - hw); out["hi" + lv].push(v + hw); });
  });
  return out;
}

/* ---------------- 2025 forecast-vs-actual scorecard ---------------- */
function scorecardHTML() {
  const sc = META.scorecard || {}, a = sc.actual || {}, c = sc.caem_forecast || {};
  if (a.gdp_realg == null) return "";
  const rows = [["Real GDP growth", c.real_gdp_growth, a.gdp_realg], ["Non-oil GDP growth", c.nonoil_growth, a.nonoil_realg],
    ["CPI inflation", c.inflation, a.cpi_infl], ["Fiscal balance (% GDP)", c.fiscal_balance, a.fiscal_bal_pct]];
  const tr = rows.map(([n, f, ac]) => {
    const e = ac - f, cls = Math.abs(e) < 0.6 ? "ok" : Math.abs(e) < 1.5 ? "mid" : "bad";
    return `<tr><td>${n}</td><td>${f.toFixed(1)}</td><td><b>${ac.toFixed(1)}</b></td><td class="sc-${cls}">${e > 0 ? "+" : ""}${e.toFixed(1)} pp</td></tr>`;
  }).join("");
  return `<div class="scorecard"><div class="sc-h">2025 scorecard — CAEM forecast vs official outturn <span class="tagi">State Statistical Committee, released Jan 2026</span></div>
    <table class="sc-t"><thead><tr><th>Indicator</th><th>CAEM forecast</th><th>2025 actual</th><th>Error</th></tr></thead><tbody>${tr}</tbody></table>
    <div class="sc-note">CAEM (2024 vintage) <b>over-predicted growth</b> (GDP 3.0% vs 1.4%; non-oil 4.6% vs 2.7%) and a <b>deficit that turned into a surplus</b> (−1.1% vs +0.4% of GDP); <b>inflation was close</b> (5.1% vs 5.6%). The live model is re-anchored to these 2025 actuals and forecasts 2026+.</div></div>`;
}

/* ---------------- scenario impact summary (key macro fundamentals, baseline → scenario) ---------------- */
const IMPACT_VARS = [["Real GDP growth", "real_gdp_growth", "%"], ["Inflation (CPI)", "inflation", "%"],
  ["Policy rate", "policy_rate", "%"], ["Fiscal balance", "fiscal_balance", "%GDP"],
  ["Gross public debt", "gross_debt", "%GDP"], ["Terms of trade", "terms_of_trade", "%"]];
function impactHTML() {
  if (!RUN || !Object.values(RUN.shock || {}).some(v => typeof v === "number" && v)) return "";
  const yrs = (RUN.baseline.real_gdp_growth ? Object.keys(RUN.baseline.real_gdp_growth) : []).map(Number);
  const yr = String(Math.max(...yrs.filter(y => y <= (+$("#s_end").value || 2030))));   // horizon = scenario end
  const shock = FIELDS.filter(f => RUN.shock[f]).map(f => `${f.replace(/_/g, " ")} ${RUN.shock[f] > 0 ? "+" : ""}${RUN.shock[f]}`).join(", ");
  const cards = IMPACT_VARS.map(([lab, v, u]) => {
    const b = (RUN.baseline[v] || {})[yr], s = (RUN.scenario[v] || {})[yr];
    if (b == null || s == null) return "";
    const d = s - b, arr = Math.abs(d) < 0.05 ? "→" : d > 0 ? "▲" : "▼";
    return `<div class="imp"><div class="imp-k">${lab}</div>
      <div class="imp-v">${b.toFixed(1)} <span class="imp-ar">${arr}</span> <b>${s.toFixed(1)}</b><span class="imp-u">${u}</span></div>
      <div class="imp-d">${d > 0 ? "+" : ""}${d.toFixed(1)} pp</div></div>`;
  }).join("");
  return `<div class="impact"><div class="imp-h">Scenario impact in ${yr} <span class="tagi">shock: ${esc(shock)}</span></div><div class="imp-grid">${cards}</div></div>`;
}

/* ---------------- per-figure info drawer ---------------- */
function attachInfo(card, f) {
  card.insertAdjacentHTML("beforeend", `<button class="finfo" title="About this figure">ⓘ info</button>`);
  card.querySelector(".finfo").onclick = e => { e.stopPropagation(); openInfo(figInfo(f)); };
}
function figInfo(f) {
  const P = META.params || {}, ph = P.phillips || [], ty = P.taylor || [], v = f.engine_var, sheet = f.sheet || "";
  const series = (f.series || []).map(s => clean(s.name)).filter(Boolean);
  const blocks = {
    inflation: `Open-economy <b>Phillips curve</b> (CAEM sheet 1b): π = c₁·π₋₁ + (1−c₁−c₂)·E[π] + c₂·(imported inflation + ΔER − import-price trend) + c₃·output gap + shock. Calibrated c₁=${ph[0]}, c₂=${ph[1]}, c₃=${ph[2]}.`,
    policy_rate: `Smoothed <b>Taylor rule</b> (CAEM sheet 1c): i = ρ·i₋₁ + (1−ρ)·(r* + π* + a·(π−π*) + b·gap). Calibrated a=${ty[0]}, b=${ty[1]}, ρ=${ty[2]}.`,
    output_gap: `<b>HP filter</b> (λ=100) on log real non-oil GDP (CAEM sheet B1a); the gap is actual minus trend.`,
    trend_growth: `<b>HP-filter trend</b> (λ=100) of log real non-oil GDP (CAEM B1a).`,
    gross_debt: `<b>Debt-dynamics recursion</b> (CAEM 3b): dₜ = dₜ₋₁·(1+i)/((1+g)(1+π)) − primary balance.`,
    fiscal_balance: `<b>Primary fiscal balance.</b> In scenarios it responds to the oil price (≈0.12 pp of GDP per 1% oil), tax measures and the exchange rate.`,
    real_gdp_growth: `<b>Real GDP growth</b> = non-oil growth (HP/Phillips block) plus the oil sector; scenarios apply oil-price, partner-growth and FX elasticities.`,
    nonoil_growth: `<b>Non-oil real GDP growth</b> — the assumption path driving the output gap, with scenario elasticities for oil, partner growth and FX.`,
  };
  let model = v && blocks[v] ? blocks[v] : (f.fan
    ? `<b>Fan chart.</b> Central path from the engine; the 50/80/90% bands widen with the horizon as σ·z·√h, where σ is the variable's historical annual-change standard deviation (one extreme outlier dropped). A calibrated uncertainty range, not a prediction of the band edges.`
    : `Reproduced directly from CAEM sheet “${esc(sheet)}” — the values are CAEM’s own computed output.`);
  if (!f.fan && f.series && f.series.length >= 3 && (COMPO.test(f.title) || detectTotalIdx(f.series) >= 0))
    model += ` Drawn as a <b>stacked decomposition</b>: the components sum to the total (overlaid line).`;
  const live = v ? `<h4>Live</h4><p>Recomputes when you change a Scenario-console input and press <b>Run</b>; the dashed red line is the scenario versus the solid baseline.</p>` : "";
  const vintage = (v || f.fan)
    ? `2025 is the official SSC outturn; the model forecasts <b>2026+</b> (shaded).`
    : `Shaded region = forecast <b>2026+</b>; 2025 is the last actual year. This figure's 2025 value is CAEM's own estimate — official 2025 outturns are in the “2025 scorecard” (Live forecast) and drive the live engine.`;
  const html = `${f.unit ? `<p class="id-unit">${esc(f.unit)}</p>` : ""}
    <h4>What it shows</h4><p>${esc(f.title)}${series.length ? ` — series: ${series.map(esc).join(", ")}.` : "."}</p>
    <h4>Model &amp; data</h4><p>${model}</p>
    <h4>How to read it</h4><p>${vintage}</p>${live}
    <p class="id-src">Source: CAEM.xlsb${v || f.fan ? " + 2025 SSC actuals" : ""} · sheet “${esc(sheet)}”.</p>`;
  return { title: f.title, html };
}
function openInfo(info) {
  $("#infotitle").textContent = info.title; $("#infobody").innerHTML = info.html;
  $("#infodrawer").classList.add("open"); $("#infoscrim").classList.add("show");
}
function closeInfo() { $("#infodrawer").classList.remove("open"); $("#infoscrim").classList.remove("show"); }

/* ---------------- generic figure ---------------- */
function drawFig(div, f, primary, big) {
  const card = document.getElementById(div).closest(".figcard");
  const multi = f.series.length > 1;
  const leg = [];
  const hov = nm => "%{x}: %{y:.2f}<extra>" + esc(nm.slice(0, 22)) + "</extra>";
  const allx = f.series.flatMap(s => s.x);

  // FAN charts: CAEM "Fancharts" sheet → engine fans; "Risk-*" sheets → fan generated from the series
  const fanData = (RUN && RUN.fan) || FAN0 || {};
  if (f.sheet === "Fancharts") {
    const v = /inflation/i.test(f.title) ? "inflation" : /gdp|growth/i.test(f.title) ? "real_gdp_growth" : null;
    if (v && fanData[v]) { drawFan(div, fanData[v], big); return; }
  }
  if (/^Risk-/.test(f.sheet)) {
    let s0 = f.series[0]; const sf = shockMatch(f.title);
    if (RUN && sf && RUN.shock[sf.field]) {       // re-centre the risk fan on the shocked input path
      const ff = LIVE_FF || META.first_forecast, isPct = /change/i.test(f.unit || "") || /change/i.test(f.title);
      s0 = { x: s0.x, y: shockSeries(s0.y, s0.x, sf, RUN.shock[sf.field], ff, isPct) };
    }
    const fan = genFan(s0);
    if (fan) { drawFan(div, fan, big); return; }
  }
  if (f.radar && f.catlabels && f.catlabels.length >= 3) { drawRadar(div, f); return; }

  // composition: explicit decomposition title OR a series VERIFIED to equal the sum of the others
  // (e.g. Oil+Gas=Total). Note: a name like "GDP growth" must NOT alone trigger stacking — that would
  // wrongly stack "Potential Growth" (alternative measures) or "Drivers of…" (non-additive) charts.
  const yearCat = !f.xyear && multi && f.series.every(s => /^\d{4}$/.test(clean(s.name)));  // Balance of risks: 2024 vs 2025
  const additiveTot = detectTotalIdx(f.series);
  const compo = multi && !yearCat && (COMPO.test(f.title) || (f.series.length >= 3 && additiveTot >= 0));
  let totIdx = -1;
  if (compo) { totIdx = f.series.findIndex(s => isTotal(s.name)); if (totIdx < 0) totIdx = additiveTot >= 0 ? additiveTot : 0; }
  let traces;

  if (compo) {                                              // stacked-bar decomposition
    let pi = 0;
    traces = f.series.map((s, k) => {
      const tot = k === totIdx, c = tot ? "#1a2038" : PAL[pi++ % PAL.length];
      const nm = clean(s.name) || (tot ? "Total" : "Component " + (k + 1));
      leg.push(tot ? { name: nm.slice(0, 28), color: c, w: 2.4 } : { name: nm.slice(0, 28), color: c, bar: true });
      return tot
        ? { x: s.x, y: s.y, type: "scatter", mode: "lines+markers", line: { color: c, width: 2.4 }, marker: { color: c, size: 4 }, hovertemplate: hov(nm), showlegend: false }
        : { x: s.x, y: s.y, type: "bar", marker: { color: c, line: { width: 0 } }, hovertemplate: hov(nm), showlegend: false };
    });
  } else if (yearCat) {                                      // grouped bars across categories
    const cats = f.catlabels || f.series[0].x.map((_, i) => "Cat " + (i + 1));
    traces = f.series.map((s, k) => {
      const c = PAL[k % PAL.length], nm = clean(s.name);
      leg.push({ name: nm, color: c, bar: true });
      return { x: cats, y: s.y, type: "bar", marker: { color: c }, hovertemplate: "%{x}: %{y:.2f}<extra>" + esc(nm) + "</extra>", showlegend: false };
    });
  } else {                                                   // lines (colour + dash differentiated)
    traces = f.series.map((s, k) => {
      const c = k === 0 ? primary : PAL[(k - 1) % PAL.length];
      const dash = DASH[k % DASH.length], nm = clean(s.name) || (k === 0 ? clean(f.title) : "Series " + (k + 1));
      if (multi) leg.push({ name: nm.slice(0, 28), color: c, dash: dash === "solid" ? "" : dash });
      return { x: s.x, y: s.y, type: "scatter", mode: "lines", line: { color: c, width: k === 0 ? 2.4 : 1.8, dash }, hovertemplate: hov(nm), showlegend: false };
    });
    if (RUN && f.engine_var && RUN.scenario[f.engine_var]) {
      const sv = RUN.scenario[f.engine_var], base = f.series[0];
      const xs = base.x.length ? base.x : Object.keys(sv).map(Number);
      const ys = xs.map((yr, i) => (sv[yr] != null ? sv[yr] : (base.y ? base.y[i] : null)));
      if (!multi) leg.push({ name: "Baseline", color: primary });
      traces.push({ x: xs, y: ys, type: "scatter", mode: "lines", line: { color: "#c0392b", width: 2.4, dash: "dash" }, hovertemplate: "%{x}: %{y:.2f}<extra>scenario</extra>", showlegend: false });
      leg.push({ name: "Scenario", color: "#c0392b", dash: "dash" });
    }
    // shock-INPUT figure (e.g. Oil price): shocking the input transforms its own path exactly
    const sf = !f.engine_var && shockMatch(f.title);
    if (RUN && sf && RUN.shock[sf.field]) {
      const base = f.series[0], ff = LIVE_FF || META.first_forecast, v = RUN.shock[sf.field];
      const isPct = /change/i.test(f.unit || "") || /change/i.test(f.title);
      const ys = shockSeries(base.y, base.x, sf, v, ff, isPct);
      if (!multi) leg.push({ name: "Baseline", color: primary });
      traces.push({ x: base.x, y: ys, type: "scatter", mode: "lines", line: { color: "#c0392b", width: 2.4, dash: "dash" }, hovertemplate: "%{x}: %{y:.2f}<extra>scenario</extra>", showlegend: false });
      leg.push({ name: "Scenario", color: "#c0392b", dash: "dash" });
    }
  }
  const hasBars = traces.some(t => t.type === "bar");
  const baseH = hasBars ? 208 : 192;
  // forecast boundary is the SAME everywhere: 2025 actual, forecast 2026+ (line at 2025.5)
  const shapes = (f.xyear && !yearCat) ? fcShapes(allx, LIVE_FF || META.first_forecast) : [];
  const layout = baseLayout(f.xyear && !yearCat, shapes, big ? baseH + 140 : baseH, 24, tickStep(allx));
  if (yearCat) layout.barmode = "group";
  if (hasBars) layout.yaxis.rangemode = "tozero";       // bars must sit on a zero baseline (fixes oil/gas overflow)
  Plotly.react(div, traces, layout, { responsive: true, displayModeBar: false });
  htmlLegend(card, leg);
}

function refresh() { if (CUR) showGroup(CUR); else if ($("#navlive").classList.contains("active")) showLive(); else showHome(); }
function dataBanner() {
  const el = $("#databanner"), yrs = Object.keys(ACTUALS).sort();
  if (!yrs.length) { el.hidden = true; el.innerHTML = ""; return; }
  el.hidden = false;
  el.innerHTML = `📌 <b>Data updated</b> — ${yrs.join(", ")} entered as actual; forecasting <b>${LIVE_FF || (Math.max(...yrs.map(Number)) + 1)}+</b>. ` +
    yrs.map(y => Object.entries(ACTUALS[y]).filter(([, v]) => v != null).map(([k, v]) => `${y} ${k.replace(/_/g, " ")} ${v}`).join(", ")).join(" · ") +
    ` <a id="bannerundo">clear</a>`;
  $("#bannerundo").onclick = () => { ACTUALS = {}; doRun(); };
}
async function doRun() {
  const body = { start: +$("#s_start").value || 2026, end: +$("#s_end").value || 2030, actuals: ACTUALS };
  FIELDS.forEach(f => body[f] = +$("#s_" + f).value || 0);
  $("#status").textContent = "running…";
  RUN = staticRun(body);
  LIVE_FF = RUN.first_forecast || META.first_forecast;
  const g = (RUN.scenario.real_gdp_growth || {})["2028"], b = (RUN.baseline.real_gdp_growth || {})["2028"];
  const on = FIELDS.filter(f => body[f]).map(f => f.replace(/_/g, " ") + " " + (body[f] > 0 ? "+" : "") + body[f]);
  $("#status").textContent = (on.length ? "ran · " + on.join(", ") : (Object.keys(ACTUALS).length ? "re-forecast on entered data" : "ran · baseline")) +
    (g != null && b != null ? `  →  2028 GDP ${b.toFixed(1)}→${g.toFixed(1)}%` : "");
  dataBanner(); refresh();
}
const PRESETS = [
  { name: "Oil −30%", s: { oil_price: -30 } },
  { name: "Oil +20%", s: { oil_price: 20 } },
  { name: "Global slowdown", s: { oil_price: -15, partner_growth: -2 } },
  { name: "Manat −15%", s: { exchange_rate: 15 } },
  { name: "Tightening +2pp", s: { policy_rate: 2 } },
  { name: "Supply shock +3pp", s: { inflation_shock: 3 } },
];
function renderPresets() {
  const el = $("#presets");
  el.querySelectorAll(".pp").forEach(b => b.remove());
  PRESETS.forEach(p => {
    const b = document.createElement("button"); b.className = "pp"; b.textContent = p.name;
    b.onclick = () => { FIELDS.forEach(f => $("#s_" + f).value = p.s[f] || 0); doRun(); };
    el.appendChild(b);
  });
}
function wireRun() {
  $("#run").onclick = doRun;
  $("#reset").onclick = () => { FIELDS.forEach(f => $("#s_" + f).value = 0); RUN = null; $("#status").textContent = ""; refresh(); };
  renderPresets();
  // ---- editable data modal ----
  const openData = () => { renderEdits(); $("#datamodal").classList.add("open"); $("#datascrim").classList.add("show"); };
  const closeData = () => { $("#datamodal").classList.remove("open"); $("#datascrim").classList.remove("show"); };
  $("#editdata").onclick = openData; $("#dataclose").onclick = closeData; $("#datascrim").onclick = closeData;
  $("#dataapply").onclick = () => {
    const y = String(+$("#d_year").value || 2026), rec = {};
    [["gdp_growth", "d_gdp_growth"], ["nonoil_growth", "d_nonoil_growth"], ["inflation", "d_inflation"], ["fiscal", "d_fiscal"]]
      .forEach(([k, id]) => { const v = $("#" + id).value; if (v !== "") rec[k] = +v; });
    if (Object.keys(rec).length) ACTUALS[y] = rec;
    ["d_gdp_growth", "d_nonoil_growth", "d_inflation", "d_fiscal"].forEach(id => $("#" + id).value = "");
    closeData(); doRun();
  };
  $("#dataclear").onclick = () => { ACTUALS = {}; renderEdits(); closeData(); doRun(); };
}
function renderEdits() {
  const yrs = Object.keys(ACTUALS).sort(), el = $("#dm_list");
  el.innerHTML = yrs.length ? "<b>Entered:</b> " + yrs.map(y =>
    `${y} {${Object.entries(ACTUALS[y]).map(([k, v]) => k.replace(/_/g, " ") + " " + v).join(", ")}}`).join(" · ") : "<i>No edits yet.</i>";
}

init().catch(e => { $("#view").innerHTML = `<p style="color:#b13f2e">Load error: ${e}. Check that the bundled CAEM data files are available.</p>`; });
