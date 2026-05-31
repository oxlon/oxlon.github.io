/* CAEM interactive dashboard — CAEM figures + live FPP engine (scenario recompute + fan charts). */
let FIGS = [], GROUPS = [], CUR = null, RUN = null, META = null, BASE = null, FAN0 = null, NFIG = 0, NLIVE = 0;
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

/* ---------------- bilingual EN / AZ (primary chrome) ---------------- */
let LANG = "en", CURMODE = "home";
try { LANG = localStorage.getItem("caem_lang") || "en"; } catch (e) { }
const AZ = {
  "hdr.title": "Makro-Fiskal Model", "hdr.sub": "Azərbaycan Respublikası · Maliyyə Proqramlaşdırma mühərriki",
  "con.title": "⚙ Ssenari paneli",
  "con.hint": "Proqnoza şok tətbiq edin və Hesabla düyməsini basın — CANLI qrafiklər və yelpik qrafikləri yenidən hesablanır, ssenari bazis xəttinin üzərinə qırmızı punktirlə düşür. Neft, qiymətlər və məzənnə %-lə; qalanları faiz bəndi ilə.",
  "con.apply": "Tətbiq", "con.to": "–", "con.editdata": "✎ Məlumatı yenilə", "con.save": "💾 Yadda saxla",
  "con.run": "Hesabla ▸", "con.reset": "Sıfırla", "con.presets": "Hazır ssenarilər",
  "cat.external": "Xarici", "cat.real": "Real iqtisadiyyat və fiskal", "cat.mon": "Monetar və məzənnə",
  "fld.oil": "Neft qiyməti", "fld.partner": "Tərəfdaş artımı", "fld.import": "İdxal qiyməti", "fld.export": "İxrac qiyməti",
  "fld.nonoil": "Qeyri-neft artımı", "fld.potential": "Potensial artım", "fld.supply": "Təklif şoku", "fld.tax": "Vergi tədbirləri",
  "fld.policy": "Uçot dərəcəsi", "fld.fx": "Məzənnə (dəyərsizləşmə)", "fld.foreign": "Xarici faiz", "fld.risk": "Risk mükafatı",
  "nav.home": "🏠 Əsas səhifə və icmal", "nav.live": "📈 Canlı proqnoz və yelpik qrafikləri",
  "nav.methods": "📐 Metodologiya və mənbələr", "nav.scen": "📂 Saxlanmış ssenarilər",
  "nav.summary": "★ İcmal panelləri", "nav.detail": "Ətraflı təhlil",
};
const tx = (k, def) => (LANG === "az" && AZ[k]) ? AZ[k] : def;     // translate-or-default
function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    if (el.dataset.en === undefined) el.dataset.en = el.textContent;
    const az = AZ[el.dataset.i18n];
    el.textContent = (LANG === "az" && az) ? az : el.dataset.en;
  });
  const lg = document.getElementById("lang");
  if (lg) lg.innerHTML = `<b class="${LANG === "en" ? "on" : ""}" data-l="en">EN</b><span>·</span><b class="${LANG === "az" ? "on" : ""}" data-l="az">AZ</b>`;
}
function setLang(l) { LANG = l; try { localStorage.setItem("caem_lang", l); } catch (e) { } applyI18n(); buildNav(); setActive(CURMODE); }

async function init() {
  await CAEM.load();                       // static client-side engine — no backend
  META = CAEM.meta();
  const data = CAEM.figures();
  FIGS = data.figures; NFIG = data.n; NLIVE = data.engine_driven;
  try { const j = CAEM.run({}); BASE = j.baseline; FAN0 = j.fan; } catch (e) { BASE = {}; FAN0 = {}; }
  $("#meta").innerHTML = `${NFIG} figures · ${NLIVE} live · forecast <b>${META.first_forecast}+</b>`;
  const seen = {};
  FIGS.forEach(f => { const k = groupOf(f.sheet); (seen[k] = seen[k] || []).push(f); });   // combine the 3 price-risk sheets
  GROUPS = Object.keys(seen).map((s, i) => ({ sheet: s, figs: seen[s], hue: HUES[i % HUES.length] }));
  buildNav(); wireRun(); applyI18n();
  $("#brand").style.cursor = "pointer"; $("#brand").onclick = showHome;
  $("#lang").onclick = e => { const l = e.target.dataset.l; if (l && l !== LANG) setLang(l); };
  $("#infoscrim").onclick = closeInfo; $("#infoclose").onclick = closeInfo;
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeInfo(); });
  showHome();
}

const SUMMARY_SHEETS = new Set(["6b. Forecasts Summary", "A1. At a glance", "Fancharts", "7. Scenario", "8b. Summary"]);
// the 3 single-figure price-risk sheets are shown together on one page (figures keep their own .sheet)
const RISK_COMBINED = "Risk: Oil / Food / Import price";
const RISK_SHEETS = ["Risk-oil price", "Risk-food price", "Risk-import price"];
const groupOf = s => RISK_SHEETS.includes(s) ? RISK_COMBINED : s;
function buildNav() {
  const navlink = g => {
    const live = g.figs.filter(f => isLive(f)).length, sm = SUMMARY_SHEETS.has(g.sheet);
    return `<div class="navlink${sm ? " summary" : ""}" data-s="${enc(g.sheet)}" style="--hue:${g.hue};border-left-color:hsl(${g.hue},55%,68%)">
      <span class="cdot" style="background:${headCol(g.hue)}"></span><span class="nl">${esc(g.sheet || "—")}</span>
      <span class="n">${g.figs.length}${live ? " · " + live + "▲" : ""}</span></div>`;
  };
  const summ = GROUPS.filter(g => SUMMARY_SHEETS.has(g.sheet)), detail = GROUPS.filter(g => !SUMMARY_SHEETS.has(g.sheet));
  $("#nav").innerHTML =
    `<div class="navhome" id="navhome">${tx("nav.home", "🏠 Home &amp; overview")}</div>
     <div class="navlive" id="navlive">${tx("nav.live", "📈 Live forecast &amp; fan charts")}</div>
     <div class="navlive navmethods" id="navmethods">${tx("nav.methods", "📐 Methods &amp; data sources")}</div>
     <div class="navlive navscen" id="navscen">${tx("nav.scen", "📂 Saved scenarios &amp; compare")}</div>
     <div class="navsec">${tx("nav.summary", "★ Summary dashboards")}</div>` + summ.map(navlink).join("") +
    `<div class="navsec">${tx("nav.detail", "Detailed analysis")} <span>figures · live ▲</span></div>` + detail.map(navlink).join("");
  document.querySelectorAll("#nav .navlink").forEach(a => a.onclick = () => showGroup(dec(a.dataset.s)));
  $("#navhome").onclick = showHome;
  $("#navlive").onclick = showLive;
  $("#navmethods").onclick = showMethods;
  $("#navscen").onclick = showScenarios;
}

function setActive(mode) {
  CURMODE = mode;
  $("#navhome").classList.toggle("active", mode === "home");
  $("#navlive").classList.toggle("active", mode === "live");
  $("#navmethods").classList.toggle("active", mode === "methods");
  $("#navscen").classList.toggle("active", mode === "scenarios");
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
    <div class="ghead" style="color:#1f5a8c;border-color:#1f5a8c">📈 Live forecast <span class="dlgrp"><button id="prpdf" class="dlbtn">🖨 PDF report</button><button id="dlxls" class="dlbtn">⤓ Excel</button><button id="dlcsv" class="dlbtn">⤓ CSV</button></span></div>
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
  $("#dlcsv").onclick = downloadCSV; $("#dlxls").onclick = exportExcel; $("#prpdf").onclick = printReport;
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
/* real .xls workbook (SpreadsheetML 2003 — opens natively in Excel, fully offline, no library) */
function exportExcel() {
  const src = RUN || { baseline: BASE, scenario: BASE };
  const vars = ["real_gdp_growth", "nonoil_growth", "output_gap", "inflation", "policy_rate",
    "fiscal_balance", "primary_balance", "gross_debt", "terms_of_trade"];
  const yrs = Object.keys(BASE.real_gdp_growth || {}).map(Number).sort((a, b) => a - b);
  const x = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const cell = v => (typeof v === "number" && isFinite(v)) ? `<Cell><Data ss:Type="Number">${v}</Data></Cell>` : `<Cell><Data ss:Type="String">${x(v)}</Data></Cell>`;
  const sheet = (name, rows) => `<Worksheet ss:Name="${x(name)}"><Table>${rows.map(r => `<Row>${r.map(cell).join("")}</Row>`).join("")}</Table></Worksheet>`;
  const frows = [["variable", "scope"].concat(yrs)];
  vars.forEach(v => ["baseline", "scenario"].forEach(sc => { const d = (src[sc] || {})[v] || {}; if (Object.keys(d).length) frows.push([v, sc].concat(yrs.map(y => d[y] != null ? d[y] : ""))); }));
  const m = META.scorecard || {}, a = m.actual || {}, c = m.caem_forecast || {};
  const scrows = [["Indicator", "CAEM forecast", "2025 actual"], ["Real GDP growth", c.real_gdp_growth, a.gdp_realg],
    ["Non-oil growth", c.nonoil_growth, a.nonoil_realg], ["CPI inflation", c.inflation, a.cpi_infl], ["Fiscal balance %GDP", c.fiscal_balance, a.fiscal_bal_pct]];
  const xml = `<?xml version="1.0"?><?mso-application progid="Excel.Sheet"?>` +
    `<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">` +
    sheet("Forecast", frows) + sheet("2025 scorecard", scrows) + `</Workbook>`;
  const el = document.createElement("a");
  el.href = URL.createObjectURL(new Blob([xml], { type: "application/vnd.ms-excel" }));
  el.download = "caem_forecast.xls"; el.click(); URL.revokeObjectURL(el.href);
}
/* print-ready report → the browser's "Save as PDF" produces the document */
function printReport() {
  const src = RUN || { baseline: BASE, scenario: BASE }, ff = LIVE_FF || META.first_forecast;
  const yrs = Object.keys(BASE.real_gdp_growth || {}).map(Number).sort((a, b) => a - b).filter(y => y >= 2023);
  const vars = [["Real GDP growth", "real_gdp_growth", "%"], ["Non-oil growth", "nonoil_growth", "%"], ["Inflation (CPI)", "inflation", "%"],
    ["Policy rate", "policy_rate", "%"], ["Fiscal balance", "fiscal_balance", "%GDP"], ["Gross public debt", "gross_debt", "%GDP"]];
  const cols = yrs.map(y => `<th${y >= ff ? ' class="fc"' : ""}>${y}</th>`).join("");
  const rows = vars.map(([lab, v, u]) => { const d = (src.scenario || {})[v] || (src.baseline || {})[v] || {}; return `<tr><td>${lab} (${u})</td>${yrs.map(y => `<td${y >= ff ? ' class="fc"' : ""}>${d[y] != null ? d[y].toFixed(1) : "—"}</td>`).join("")}</tr>`; }).join("");
  const onScn = RUN && Object.values(RUN.shock || {}).some(v => typeof v === "number" && v);
  const shockTxt = onScn ? FIELDS.filter(f => RUN.shock[f]).map(f => `${f.replace(/_/g, " ")} ${RUN.shock[f] > 0 ? "+" : ""}${RUN.shock[f]}`).join(", ") : "baseline (no shock)";
  const date = new Date().toISOString().slice(0, 10);
  const html = `<div class="rep-head"><div class="rep-eyebrow">REPUBLIC OF AZERBAIJAN · MINISTRY OF ECONOMY</div>
      <h1>CAEM Macro-Fiscal Forecast</h1>
      <div class="rep-meta">Financial Programming model · forecast ${ff}+ (2025 = last actual) · scenario: ${esc(shockTxt)} · generated ${date}</div></div>
    <h2>Forecast summary</h2>
    <table class="rep-t"><thead><tr><th>Indicator</th>${cols}</tr></thead><tbody>${rows}</tbody></table>
    <h2>2025 forecast vs official outturn</h2>${scorecardHTML()}
    <div class="rep-foot">Reproduced &amp; extended from CAEM.xlsb (IMF Financial Programming &amp; Policies). 2025 actuals: State Statistical Committee of Azerbaijan. Shaded years = forecast horizon. Prepared by Oxlon Forecasting.</div>`;
  let rep = $("#report"); if (!rep) { rep = document.createElement("div"); rep.id = "report"; document.body.appendChild(rep); }
  rep.innerHTML = html;
  document.body.classList.add("printing"); window.print(); document.body.classList.remove("printing");
}

/* ---------------- a CAEM dashboard ---------------- */
function showGroup(sheet) {
  CUR = sheet; setActive(sheet);
  const g = GROUPS.find(x => x.sheet === sheet);
  const live = g.figs.filter(f => isLive(f)).length;
  const isRisk = sheet === RISK_COMBINED;
  const solo = !isRisk && g.figs.length <= 2;            // 1–2 figures → render large for detail
  const sub = isRisk
    ? `Three price-risk scenarios — <b>oil</b>, <b>food</b> and <b>import</b> prices — each shown as a fan around the baseline path (the band widens with the horizon). Shock the matching console input (Oil price, Import price) to re-centre its fan. Shaded band = forecast (${LIVE_FF || META.first_forecast}+); 2025 = last actual.`
    : `${g.figs.length} figures from CAEM sheet “${esc(sheet)}”${live ? ` · ${live} recompute live` : ""}.
    ${RUN ? "Dashed red = current scenario." : "Run a scenario above to overlay it."} Shaded band = forecast (${LIVE_FF || META.first_forecast}+); 2025 = last actual.`;
  $("#view").innerHTML = `<div class="ghead" style="color:${headCol(g.hue)};border-color:${headCol(g.hue)}">${esc(sheet)}</div>
    <div class="gsub">${sub}</div>
    <div class="figgrid${solo ? " solo" : ""}" id="grid"></div>`;
  const grid = $("#grid");
  g.figs.forEach((f, i) => {
    const t = tone(g.hue, i);
    const title = isRisk ? f.title.replace(/^Risk-/i, "").replace(/^./, c => c.toUpperCase()) : f.title;
    const card = document.createElement("div"); card.className = "figcard" + (solo ? " big" : ""); card.style.borderTopColor = t;
    card.innerHTML = `<div class="ft">${esc(title)}${isLive(f) ? '<span class="live">LIVE</span>' : ""}</div>
      ${f.unit ? `<div class="fu">${esc(f.unit)}</div>` : ""}<div class="fc" id="fc${i}"></div>`;
    grid.appendChild(card);
    drawFig(`fc${i}`, f, t, solo);
    attachInfo(card, f);
  });
  window.scrollTo({ top: 0 });
}

/* ---------------- methods & data-sources manual ---------------- */
function showMethods() {
  CUR = null; setActive("methods");
  const p = META.params || {}, ph = p.phillips || [], ty = p.taylor || [];
  const prov = (META.provenance && META.provenance.actuals) || {}, caem = (META.provenance && META.provenance.caem_default) || "CAEM.xlsb";
  const sc = META.scorecard || {}, a = sc.actual || {}, c = sc.caem_forecast || {};
  const provRows = Object.keys(prov).map(k => {
    const x = prov[k];
    return `<tr><td>${esc((META.fan_labels && META.fan_labels[k]) || k.replace(/_/g, " "))}</td><td><b>${esc(x.value)}</b> ${esc(x.unit || "")}</td>
      <td>${esc(x.source || "")}${x.url ? ` · <a href="${esc(x.url)}" target="_blank" rel="noopener">link</a>` : ""}</td><td>${esc(x.date || "")}</td></tr>`;
  }).join("");
  const eqs = [
    ["Potential output / output gap",
      "\\hat y_t = 100\\,(\\ln Y_t - \\ln Y^*_t),\\quad Y^*=\\mathrm{HP}_{\\lambda=100}(\\ln Y)",
      "gap = 100·(lnY − lnY*),  Y* = HP(λ=100)",
      "HP filter on log real non-oil GDP; gap = actual − trend (CAEM sheet B1a, endpoint-extended with the forecast).", "≈ 0.18 pp"],
    ["Inflation — open-economy Phillips curve",
      "\\pi_t = c_1\\pi_{t-1} + (1{-}c_1{-}c_2)\\,E[\\pi] + c_2(\\pi^{m}{+}\\Delta e{-}\\bar\\pi^{m}) + c_3\\,\\hat y_t + \\varepsilon_t",
      "π = c1·π(-1)+(1-c1-c2)·E[π]+c2·(import push)+c3·gap+shock",
      `Persistence, inflation expectations, import-price pass-through and the output gap. c₁=${ph[0]}, c₂=${ph[1]}, c₃=${ph[2]} (CAEM 1b).`, "≈ 0.01 pp"],
    ["Policy rate — smoothed Taylor rule",
      "i_t = \\rho\\,i_{t-1} + (1{-}\\rho)\\big(r^*{+}\\pi^*{+}a(\\pi_t{-}\\pi^*){+}b\\,\\hat y_t\\big) + \\varepsilon_t",
      "i = ρ·i(-1)+(1-ρ)·(r*+π*+a(π-π*)+b·gap)+shock",
      `Smoothing toward a neutral rate, plus an inflation-gap and output-gap response. a=${ty[0]}, b=${ty[1]}, ρ=${ty[2]} (CAEM 1c).`, "≈ 0.07 pp"],
    ["Public debt — ratio recursion",
      "d_t = d_{t-1}\\,\\dfrac{1+i}{(1+g)(1+\\pi)} - pb_t",
      "d = d(-1)·(1+i)/((1+g)(1+π)) − primary balance",
      "Debt ratio evolves with the effective interest rate i, growth g, inflation π and the primary balance pb (CAEM 3b).", "dynamics"],
  ];
  const els = [["Oil price → non-oil growth", "0.02 pp / 1%"], ["Oil price → fiscal balance", "0.12 pp of GDP / 1%"],
    ["Oil price → inflation", "0.01 pp / 1%"], ["Partner growth → non-oil growth", "0.30 pp / 1pp"],
    ["Exchange rate (depr.) → growth", "0.05 pp / 1%"], ["Exchange rate → fiscal", "0.06 pp of GDP / 1%"],
    ["Foreign rate → domestic rate", "0.5 pass-through"], ["Oil price → terms of trade", "0.30 / 1%"]];
  $("#view").innerHTML = `
    <div class="ghead" style="color:#8a6d1f;border-color:#8a6d1f">📐 Methods &amp; data sources</div>
    <div class="gsub">Every equation, its calibration, and every data source — auditable and reproducible. The structural
      blocks reproduce CAEM (validated against the workbook); the oil/fiscal/external channels are transparent, labelled elasticities.</div>

    <h3 class="lh">1 · Core equations (reproduced from CAEM, validated)</h3>
    <div class="mtbl"><table class="dt"><thead><tr><th>Block</th><th>Specification</th><th>Validation</th></tr></thead><tbody>
      ${eqs.map(([n, tex, plain, note, v]) => `<tr><td><b>${n}</b></td><td>${kx(tex, plain)}${note ? `<div class="eqcal">${esc(note)}</div>` : ""}</td><td class="sc-ok">${esc(v)}</td></tr>`).join("")}
    </tbody></table></div>

    <h3 class="lh">2 · Scenario channels (transparent, Azerbaijan-calibrated elasticities)</h3>
    <div class="note-eco">These are <b>not</b> CAEM's full accounting — they are labelled reduced-form responses so every scenario number is traceable to a stated elasticity.</div>
    <div class="mtbl"><table class="dt"><tbody>${els.map(([n, v]) => `<tr><td>${n}</td><td class="sc-mid">${v}</td></tr>`).join("")}</tbody></table></div>

    <h3 class="lh">3 · Fan charts (uncertainty)</h3>
    <p class="mp">Central path from the engine; 50 / 80 / 90% bands widen with the horizon as σ·z·√h, where σ is the
      variable's historical annual-change standard deviation (one extreme outlier dropped; capped 0.4–1.8). A calibrated
      uncertainty range, not a prediction of the band edges.</p>

    <h3 class="lh">4 · Data &amp; provenance</h3>
    <p class="mp">Default source for all series: <b>${esc(caem)}</b></p>
    <div class="mtbl"><table class="dt"><thead><tr><th>2025 official actual</th><th>Value</th><th>Source</th><th>Released</th></tr></thead>
      <tbody>${provRows || '<tr><td colspan="4">No official actuals loaded.</td></tr>'}</tbody></table></div>
    <p class="mp"><b>Honest scope:</b> the four official 2025 indicators above are folded into the model; the remaining series
      still carry CAEM's 2024-vintage estimate for 2025 until each is sourced from the SSC / CBAR. The ingestion pipeline
      (<code>apply_actuals.py</code>) refreshes everything when a new actuals CSV is supplied.</p>

    <h3 class="lh">5 · 2025 forecast vs outturn (model skill)</h3>
    ${scorecardHTML()}

    ${ministryModelsHTML()}

    <div class="hfoot">Reproduced &amp; extended from CAEM.xlsb in Python; the live dashboard runs the same engine in the browser (validated identical).
      Methodology references: IMF Financial Programming &amp; Policies; Cabinet of Ministers Decree No. 75.</div>`;
  window.scrollTo({ top: 0 });
}
/* a compact, accurate reading guide for the EViews variable names — convention, not invented per-variable meanings */
function eqDecoderHTML() {
  const ops = [
    ["DLOG(x)", "annual change in the natural log of x — i.e. its growth rate (Δln x)"],
    ["LOG(x)", "natural log of x — used to write the long-run (level) relationships"],
    ["ECM_x , ECM_x(−1)", "error-correction term for x: how far x sits from its estimated long-run equilibrium; the lagged term pulls x back toward it"],
    ["x(−1), x(−2)", "one- and two-year lags of x"],
    ["@BEFORE(\"y\") · @DURING(\"y₁ y₂\") · @AFTER(\"y\") · (T=y) · (T&gt;y)", "EViews date dummies — they switch coefficients on for structural breaks / regime shifts"],
  ];
  const morph = [
    ["M / X", "imports / exports"],
    ["G / S", "goods / services"],
    ["O / NO", "oil / non-oil"],
    ["R… / VA_…", "real (constant-price) / sector value added"],
    ["ER · NEER · REER", "manat/USD rate · nominal · real effective exchange rate"],
    ["CPI · OPWTI/OPIWTI", "consumer price index · WTI crude oil price"],
    ["W · L · HC", "wage · employment · household consumption"],
    ["TIKINTI · TICARET", "Azerbaijani sector names: construction · trade"],
  ];
  const cell = arr => `<div class="mtbl"><table class="dt eqdec"><tbody>${arr.map(([k, v]) => `<tr><td class="eqdec-k">${k}</td><td>${v}</td></tr>`).join("")}</tbody></table></div>`;
  return `<div class="eqdecwrap"><div class="eqdec-h">Reading the names</div>
    <div class="eqdec-grid"><div><div class="eqdec-sub">Transformations &amp; dummies</div>${cell(ops)}</div>
      <div><div class="eqdec-sub">Variable naming convention</div>${cell(morph)}</div></div>
    <p class="mp eqdec-ex"><b>Worked example — ECM_MGNO.</b> Read it as <b>ECM</b> (error-correction) of <b>M·G·NO</b> = non-oil goods imports.
      Its long run, <span class="mono">LOG(MGNO) = f(HC, I−IO, NEER)</span>, ties non-oil imports to household consumption and non-oil investment
      (total investment I minus oil investment IO) and the nominal effective exchange rate; the lag <span class="mono">ECM_MGNO(−1)</span> then
      enters the short-run growth equation <span class="mono">DLOG(MGNO)</span> and corrects deviations from that equilibrium.</p></div>`;
}
/* the Ministry's own estimated econometric equations (Databiz / EViews model book) — real coefficients */
function ministryModelsHTML() {
  const EQ = (typeof CAEM !== "undefined" && CAEM.equations) ? CAEM.equations() : { equations: [] };
  const eqs = EQ.equations || [];
  if (!eqs.length) return "";
  const byWb = {}; eqs.forEach(e => { (byWb[e.workbook] = byWb[e.workbook] || []).push(e); });
  const eqItem = e => {
    const lhs = clean(e.lhs), rhs = clean(e.rhs), d = (e.desc || "").trim();
    return `<div class="eqit"><div class="eqit-h"><span class="eqit-lhs">${esc(lhs)}</span>${d ? `<span class="eqit-d">${esc(d)}</span>` : ""}</div>
      ${rhs ? `<div class="eqit-rhs">= ${esc(rhs)}</div>` : ""}</div>`;
  };
  const blocks = Object.keys(byWb).map(wb =>
    `<h4 class="eqwb">${esc(wb)} <span class="tagi">${byWb[wb].length} equations</span></h4>
     <div class="eqlist">${byWb[wb].map(eqItem).join("")}</div>`).join("");
  return `<h3 class="lh">6 · Ministry econometric models (Databiz model book)</h3>
    <div class="note-eco">These are the Ministry's <b>own</b> estimated equations — single-equation error-correction and
      regime-switching specifications (EViews) from six workbooks (SNA, BoP, Inflation, Social, Industry, Trade; ${eqs.length}
      equations with their actual coefficients). Each one forecasts a single series — a sector's output, an import/export
      category, a price or a monetary aggregate — from its own drivers and a long-run anchor. They are documented here for
      continuity with the Ministry's methods; CAEM remains the live forecasting spine, and wiring these as live satellite
      forecasters is the defined next phase.</div>
    ${eqDecoderHTML()}
    ${blocks}`;
}

/* ---------------- saved scenarios + compare (localStorage) ---------------- */
const SCEN_KEY = "caem_scenarios_v1";
const loadScens = () => { try { return JSON.parse(localStorage.getItem(SCEN_KEY) || "[]"); } catch (e) { return []; } };
const saveScens = a => { try { localStorage.setItem(SCEN_KEY, JSON.stringify(a)); } catch (e) { } };
function currentScenario() {
  const shock = {}; FIELDS.forEach(f => shock[f] = +$("#s_" + f).value || 0);
  return { shock, actuals: JSON.parse(JSON.stringify(ACTUALS || {})), start: +$("#s_start").value || 2026, end: +$("#s_end").value || 2030 };
}
function saveCurrentScenario() {
  const name = (prompt("Name this scenario / forecast round:", "Scenario " + (loadScens().length + 1)) || "").trim();
  if (!name) return;
  const a = loadScens(); a.unshift(Object.assign({ name, ts: new Date().toISOString().slice(0, 10) }, currentScenario()));
  saveScens(a); $("#status").textContent = "saved: " + name;
  if ($("#navscen").classList.contains("active")) showScenarios();
}
function applyScenario(s) {
  ACTUALS = JSON.parse(JSON.stringify(s.actuals || {}));
  $("#s_start").value = s.start || 2026; $("#s_end").value = s.end || 2030;
  FIELDS.forEach(f => $("#s_" + f).value = (s.shock && s.shock[f]) || 0);
  doRun();
}
function showScenarios() {
  CUR = null; setActive("scenarios");
  const list = loadScens();
  const rows = list.map((s, i) => {
    const sh = FIELDS.filter(f => s.shock && s.shock[f]).map(f => `${f.replace(/_/g, " ")} ${s.shock[f] > 0 ? "+" : ""}${s.shock[f]}`).join(", ") || "baseline";
    const act = Object.keys(s.actuals || {}).length ? ` · data: ${Object.keys(s.actuals).join(", ")}` : "";
    return `<tr><td><input type="checkbox" class="scchk" data-i="${i}"></td><td><b>${esc(s.name)}</b><div class="sc-sub">${esc(s.ts)}</div></td>
      <td>${esc(sh)}${esc(act)}</td><td><button class="lk" data-load="${i}">Load &amp; run</button> <button class="lk del" data-del="${i}">Delete</button></td></tr>`;
  }).join("");
  $("#view").innerHTML = `
    <div class="ghead" style="color:#1f5a8c;border-color:#1f5a8c">📂 Saved scenarios &amp; forecast rounds</div>
    <div class="gsub">Save the current console state (shocks + entered data) as a named scenario or forecast round, reload it later,
      or tick 2–3 to compare side by side. Stored in this browser (clears with browser data).</div>
    <div class="mtbl"><table class="dt"><thead><tr><th></th><th>Name</th><th>Shock / data</th><th></th></tr></thead>
      <tbody>${rows || '<tr><td colspan="4">No saved scenarios yet — set shocks in the console and press 💾 Save.</td></tr>'}</tbody></table></div>
    ${list.length ? `<div class="dm-act"><button id="cmpbtn" class="btn">Compare selected</button> <button id="clrscen" class="btn ghost">Delete all</button></div>` : ""}
    <div id="cmpout"></div>`;
  document.querySelectorAll("[data-load]").forEach(b => b.onclick = () => applyScenario(loadScens()[+b.dataset.load]));
  document.querySelectorAll("[data-del]").forEach(b => b.onclick = () => { const a = loadScens(); a.splice(+b.dataset.del, 1); saveScens(a); showScenarios(); });
  if ($("#clrscen")) $("#clrscen").onclick = () => { if (confirm("Delete all saved scenarios?")) { saveScens([]); showScenarios(); } };
  if ($("#cmpbtn")) $("#cmpbtn").onclick = compareScenarios;
  window.scrollTo({ top: 0 });
}
function compareScenarios() {
  const list = loadScens();
  const sel = [...document.querySelectorAll(".scchk:checked")].map(c => list[+c.dataset.i]).filter(Boolean);
  if (!sel.length) { $("#cmpout").innerHTML = '<p class="mp">Tick at least one saved scenario to compare.</p>'; return; }
  const base = CAEM.run({});
  const yrs = Object.keys(base.baseline.real_gdp_growth || {}).map(Number);
  const yr = String(Math.max(...(yrs.length ? yrs : [2030])));
  const cols = [{ name: "Baseline", r: base }].concat(sel.map(s => ({ name: s.name, r: CAEM.run(Object.assign({}, s.shock, { actuals: s.actuals, start: s.start, end: s.end })) })));
  const head = `<tr><th>Indicator (${yr})</th>` + cols.map(c => `<th>${esc(c.name)}</th>`).join("") + `</tr>`;
  const body = IMPACT_VARS.map(([lab, v, u]) =>
    `<tr><td>${lab}</td>` + cols.map(c => { const d = (c.r.scenario && c.r.scenario[v]) || {}; const val = d[yr]; return `<td>${val == null ? "—" : val.toFixed(1) + " " + u}</td>`; }).join("") + `</tr>`).join("");
  $("#cmpout").innerHTML = `<h3 class="lh">Comparison at ${yr}</h3><div class="mtbl"><table class="dt"><thead>${head}</thead><tbody>${body}</tbody></table></div>`;
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
  hovermode: "x unified", hoverlabel: { font: { size: 10.5, family: "Inter,sans-serif" }, bgcolor: "#fff", bordercolor: "#d2d7dd" },
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
  traces.push({ x, y: fan.central, mode: "lines+markers", line: { color: FAN_CENTRAL, width: 2.6 }, marker: { size: 3.6, color: FAN_CENTRAL }, hovertemplate: "<b>central</b>: %{y:.2f}<extra></extra>", showlegend: false });
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
  const errs = [];
  const tr = rows.map(([n, f, ac]) => {
    const e = ac - f, cls = Math.abs(e) < 0.6 ? "ok" : Math.abs(e) < 1.5 ? "mid" : "bad";
    errs.push(Math.abs(e));
    return `<tr><td>${n}</td><td>${f.toFixed(1)}</td><td><b>${ac.toFixed(1)}</b></td><td class="sc-${cls}">${e > 0 ? "+" : ""}${e.toFixed(1)} pp</td></tr>`;
  }).join("");
  const mae = errs.reduce((x, y) => x + y, 0) / (errs.length || 1);
  return `<div class="scorecard"><div class="sc-h">2025 scorecard — CAEM forecast vs official outturn <span class="tagi">State Statistical Committee, released Jan 2026</span></div>
    <table class="sc-t"><thead><tr><th>Indicator</th><th>CAEM forecast</th><th>2025 actual</th><th>Error</th></tr></thead><tbody>${tr}
      <tr class="sc-mae"><td><b>Mean absolute error</b></td><td></td><td></td><td><b>${mae.toFixed(1)} pp</b></td></tr></tbody></table>
    <div class="sc-note">CAEM (2024 vintage) <b>over-predicted growth</b> (GDP 3.0% vs 1.4%; non-oil 4.6% vs 2.7%) and a <b>deficit that turned into a surplus</b> (−1.1% vs +0.4% of GDP); <b>inflation was close</b> (5.1% vs 5.6%). The live model is re-anchored to these 2025 actuals and forecasts 2026+.
      <br><span class="tagi">Track record: one vintage available (the 2024-vintage call vs the 2025 outturn). Each future forecast round — saved via 💾 and the apply_actuals pipeline — extends this table into a rolling accuracy record.</span></div></div>`;
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

/* ---------------- per-figure info + PNG export ---------------- */
function attachInfo(card, f) {
  card.insertAdjacentHTML("beforeend",
    `<button class="figpng" title="Download high-resolution PNG">⤓ PNG</button><button class="finfo" title="About this figure">ⓘ info</button>`);
  card.querySelector(".finfo").onclick = e => { e.stopPropagation(); openInfo(figInfo(f)); };
  card.querySelector(".figpng").onclick = e => {
    e.stopPropagation();
    const gd = card.querySelector(".fc");
    if (gd && window.Plotly) Plotly.downloadImage(gd, { format: "png", scale: 3, filename: "caem_" + (f.title || "figure").replace(/[^\w]+/g, "_").slice(0, 44) });
  };
}
function kx(latex, plain) {
  if (window.katex) { try { return `<div class="id-eq">${katex.renderToString(latex, { throwOnError: false, displayMode: false })}</div>`; } catch (e) { } }
  return `<div class="id-eq mono">${esc(plain || latex)}</div>`;
}
const VARDESC = {
  real_gdp_growth: "Total real GDP growth — oil and non-oil sectors combined; the headline output measure.",
  nonoil_growth: "Non-oil real GDP growth — the part of the economy policy most affects; it drives the output gap.",
  inflation: "Headline CPI inflation, generated by the open-economy Phillips curve.",
  policy_rate: "Nominal policy (refinancing) rate, set by the smoothed Taylor rule.",
  output_gap: "Output gap: actual minus HP-filter potential, % of potential non-oil GDP — the cyclical position.",
  trend_growth: "HP-filter trend (potential) growth of non-oil GDP.",
  gross_debt: "Gross public debt, % of GDP, from the debt-dynamics recursion.",
  fiscal_balance: "Fiscal (primary) balance, % of GDP.",
  primary_balance: "Primary fiscal balance, % of GDP — the overall balance excluding interest payments.",
  terms_of_trade: "Terms of trade — export prices relative to import prices; oil-dominated for Azerbaijan.",
};
const VAREQ = {
  inflation: ["\\pi_t = c_1\\pi_{t-1} + (1{-}c_1{-}c_2)\\,E[\\pi] + c_2(\\pi^{m}{+}\\Delta e{-}\\bar\\pi^{m}) + c_3\\,\\hat y_t + \\varepsilon_t", "π = c1·π(-1)+(1-c1-c2)·E[π]+c2·(import push)+c3·gap+shock"],
  policy_rate: ["i_t = \\rho\\,i_{t-1} + (1{-}\\rho)\\,(r^*{+}\\pi^*{+}a(\\pi_t{-}\\pi^*){+}b\\,\\hat y_t)", "i = ρ·i(-1)+(1-ρ)·(r*+π*+a(π-π*)+b·gap)"],
  output_gap: ["\\hat y_t = 100(\\ln Y_t-\\ln Y^*_t),\\; Y^*=\\mathrm{HP}_{\\lambda=100}(\\ln Y)", "gap = 100·(lnY − lnY*),  Y* = HP(λ=100)"],
  trend_growth: ["g^*_t = e^{\\,\\ln Y^*_t-\\ln Y^*_{t-1}}-1,\\; Y^*=\\mathrm{HP}_{\\lambda=100}", "trend growth from HP(λ=100) of lnY"],
  gross_debt: ["d_t = d_{t-1}\\dfrac{1+i}{(1+g)(1+\\pi)} - pb_t", "d = d(-1)·(1+i)/((1+g)(1+π)) − primary balance"],
};
const TITLEDESC = [[/required to close the output gap/i, "Normative calculation (not a forecast): the constant annual real GDP growth that would close the current output gap over each horizon — the 1-, 2-, … 5-year lines."]];
function figInfo(f) {
  const P = META.params || {}, ph = P.phillips || [], ty = P.taylor || [], v = f.engine_var, sheet = f.sheet || "";
  let shows = VARDESC[v];
  for (const [re, d] of TITLEDESC) if (re.test(f.title)) { shows = d; break; }
  if (!shows) shows = f.fan ? "Engine central forecast with confidence bands that widen over the horizon."
    : f.radar ? "Risk scores across dimensions, compared year-on-year."
      : (f.series && f.series.length >= 3 && (COMPO.test(f.title) || detectTotalIdx(f.series) >= 0))
        ? `Decomposition — the components (${(f.series || []).map(s => clean(s.name)).filter(Boolean).slice(0, 4).join(", ")}) sum to the total.`
        : `Reproduced from CAEM sheet “${esc(sheet)}”.`;
  const calib = { inflation: `c₁=${ph[0]}, c₂=${ph[1]}, c₃=${ph[2]} (CAEM 1b).`, policy_rate: `a=${ty[0]}, b=${ty[1]}, ρ=${ty[2]} (CAEM 1c).`,
    output_gap: "CAEM sheet B1a.", trend_growth: "CAEM B1a.", gross_debt: "CAEM 3b; effective rate ≈ 3%.",
    fiscal_balance: "Scenario response: oil ≈ 0.12 pp/1%, tax, FX.", primary_balance: "Scenario response: oil, tax, FX.", terms_of_trade: "Scenario response: oil ± export/import prices." }[v] || "";
  let model = v ? ((VAREQ[v] ? kx(VAREQ[v][0], VAREQ[v][1]) : "") + (calib ? `<p>${calib}</p>` : ""))
    : f.fan ? `<p>Fan chart. Central path from the engine; 50/80/90% bands widen as σ·z·√h — σ from the equation's robust in-sample residuals (inflation &amp; policy rate) or the variable's historical annual-change σ.</p>`
      : `<p>Reproduced directly from CAEM sheet “${esc(sheet)}” — the values are CAEM's own computed output.</p>`;
  const yrs = [...new Set((f.series || []).flatMap(s => s.x))].filter(y => typeof y === "number").sort((a, b) => a - b);
  let table = "";
  if ((f.series || []).length && yrs.length) {
    const names = f.series.map((s, i) => clean(s.name) || ("Series " + (i + 1)));
    const idx = f.series.map(s => { const m = {}; s.x.forEach((x, i) => m[x] = s.y[i]); return m; });
    const body = yrs.map(y => `<tr><td>${y}</td>${idx.map(m => `<td>${m[y] == null ? "" : Math.round(m[y] * 100) / 100}</td>`).join("")}</tr>`).join("");
    table = `<h4>Data <button id="infocsv" class="lk">⤓ CSV</button></h4>
      <div class="id-tblwrap"><table class="id-tbl"><thead><tr><th>Year</th>${names.map(n => `<th>${esc(n.slice(0, 16))}</th>`).join("")}</tr></thead><tbody>${body}</tbody></table></div>`;
  }
  const prov = (META.provenance && META.provenance.actuals) || {}, pv = prov[v];
  const src = pv
    ? `<b>2025 actual:</b> ${esc(pv.value)}${pv.unit ? " " + esc(pv.unit) : ""} — ${esc(pv.source)}${pv.date ? ` (released ${esc(pv.date)})` : ""}${pv.url ? ` · <a href="${esc(pv.url)}" target="_blank" rel="noopener">source</a>` : ""}. Other years: CAEM model.`
    : esc((META.provenance && META.provenance.caem_default) || "CAEM.xlsb workbook.");
  const live = v ? `<h4>Live</h4><p>Recomputes when you change a Scenario-console input and press <b>Run</b>; the dashed red line is the scenario vs the solid baseline.</p>` : "";
  const vintage = (v || f.fan) ? `2025 = official outturn; the model forecasts <b>2026+</b> (shaded).`
    : `Shaded = forecast <b>2026+</b>; 2025 = last actual. This figure's 2025 point is CAEM's estimate — official 2025 outturns are in the scorecard.`;
  const html = `${f.unit ? `<p class="id-unit">${esc(f.unit)}</p>` : ""}
    <h4>What it shows</h4><p>${shows}</p>
    <h4>Model &amp; data</h4>${model}
    <h4>How to read it</h4><p>${vintage}</p>${live}
    ${table}
    <h4>Source &amp; provenance</h4><p class="id-src">${src} · CAEM sheet “${esc(sheet)}”.</p>`;
  return { title: f.title, html, f };
}
function downloadFigData(f) {
  const yrs = [...new Set((f.series || []).flatMap(s => s.x))].filter(y => typeof y === "number").sort((a, b) => a - b);
  const names = f.series.map((s, i) => clean(s.name) || ("series" + (i + 1)));
  const idx = f.series.map(s => { const m = {}; s.x.forEach((x, i) => m[x] = s.y[i]); return m; });
  const rows = [["year"].concat(names)].concat(yrs.map(y => [y].concat(idx.map(m => m[y] == null ? "" : m[y]))));
  const csv = "# " + (f.title || "figure") + "\n" + rows.map(r => r.join(",")).join("\n");
  const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  a.download = "caem_" + (f.title || "data").replace(/[^\w]+/g, "_").slice(0, 40) + ".csv"; a.click(); URL.revokeObjectURL(a.href);
}
function openInfo(info) {
  $("#infotitle").textContent = info.title; $("#infobody").innerHTML = info.html;
  const csv = $("#infocsv"); if (csv && info.f) csv.onclick = () => downloadFigData(info.f);
  $("#infodrawer").classList.add("open"); $("#infoscrim").classList.add("show");
}
function closeInfo() { $("#infodrawer").classList.remove("open"); $("#infoscrim").classList.remove("show"); }

/* ---------------- generic figure ---------------- */
function drawFig(div, f, primary, big) {
  const card = document.getElementById(div).closest(".figcard");
  const multi = f.series.length > 1;
  const leg = [];
  const hov = nm => "<b>" + esc(nm.slice(0, 24)) + "</b>: %{y:.2f}<extra></extra>";   // x in the unified header
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
      return { x: s.x, y: s.y, type: "scatter", mode: "lines+markers", line: { color: c, width: k === 0 ? 2.4 : 1.8, dash }, marker: { size: 3.6, color: c }, hovertemplate: hov(nm), showlegend: false };
    });
    if (RUN && f.engine_var && RUN.scenario[f.engine_var]) {
      const sv = RUN.scenario[f.engine_var], base = f.series[0];
      const xs = base.x.length ? base.x : Object.keys(sv).map(Number);
      const ys = xs.map((yr, i) => (sv[yr] != null ? sv[yr] : (base.y ? base.y[i] : null)));
      if (!multi) leg.push({ name: "Baseline", color: primary });
      traces.push({ x: xs, y: ys, type: "scatter", mode: "lines", line: { color: "#c0392b", width: 2.4, dash: "dash" }, hovertemplate: "<b>scenario</b>: %{y:.2f}<extra></extra>", showlegend: false });
      leg.push({ name: "Scenario", color: "#c0392b", dash: "dash" });
    }
    // shock-INPUT figure (e.g. Oil price): shocking the input transforms its own path exactly
    const sf = !f.engine_var && shockMatch(f.title);
    if (RUN && sf && RUN.shock[sf.field]) {
      const base = f.series[0], ff = LIVE_FF || META.first_forecast, v = RUN.shock[sf.field];
      const isPct = /change/i.test(f.unit || "") || /change/i.test(f.title);
      const ys = shockSeries(base.y, base.x, sf, v, ff, isPct);
      if (!multi) leg.push({ name: "Baseline", color: primary });
      traces.push({ x: base.x, y: ys, type: "scatter", mode: "lines", line: { color: "#c0392b", width: 2.4, dash: "dash" }, hovertemplate: "<b>scenario</b>: %{y:.2f}<extra></extra>", showlegend: false });
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
async function doRun() {
  const body = { start: +$("#s_start").value || 2026, end: +$("#s_end").value || 2030 };
  FIELDS.forEach(f => body[f] = +$("#s_" + f).value || 0);
  $("#status").textContent = "running…";
  RUN = CAEM.run(body);
  LIVE_FF = RUN.first_forecast || META.first_forecast;
  const g = (RUN.scenario.real_gdp_growth || {})["2028"], b = (RUN.baseline.real_gdp_growth || {})["2028"];
  const on = FIELDS.filter(f => body[f]).map(f => f.replace(/_/g, " ") + " " + (body[f] > 0 ? "+" : "") + body[f]);
  $("#status").textContent = (on.length ? "ran · " + on.join(", ") : "ran · baseline") +
    (g != null && b != null ? `  →  2028 GDP ${b.toFixed(1)}→${g.toFixed(1)}%` : "");
  refresh();
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
  $("#savescen").onclick = saveCurrentScenario;
  renderPresets();
}

init().catch(e => { $("#view").innerHTML = `<p style="color:#b13f2e">Load error: ${e}. Is the API running?</p>`; });
