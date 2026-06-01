/* CAEM interactive dashboard — CAEM figures + live FPP engine (scenario recompute + fan charts). */
let FIGS = [], GROUPS = [], CUR = null, RUN = null, META = null, BASE = null, FAN0 = null, NFIG = 0, NLIVE = 0;
let ACTUALS = {}, LIVE_FF = null;   // editable data: user-entered actuals + effective first-forecast year
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
const enc = encodeURIComponent, dec = decodeURIComponent;
const clean = n => (n || "").replace(/\s+/g, " ").trim();
const HUES = [210, 28, 264, 150, 344, 190, 45, 122, 232, 14, 300, 168, 255, 86, 200, 320, 38, 175, 270, 100, 8, 220];
const tone = (h, j) => `hsl(${h},44%,${36 + (j % 6) * 7}%)`;
const headCol = h => `hsl(${h},40%,38%)`;
const softBg = h => `hsl(${h},30%,96%)`;
const PAL = ["#0f6b62", "#b07d3c", "#3f6f8f", "#b23b30", "#5f7d52", "#8a5d7a", "#2f8a7e", "#9a7b3c", "#6a6f8f", "#c0683f", "#4e8d80"];
const DASH = ["solid", "dash", "dot", "dashdot", "longdash", "longdashdot"];
const isTotal = n => /\b(total|gdp growth|real gdp|overall balance|headline|sum|net|forecast)\b/i.test(n || "");
const COMPO = /contribution|share of|sources of|composition|decompos|expenditure item|revenue item|financing|by sector|use of|breakdown|growth accounting/i;
// Bank-of-England "river of blood" — red tones, lighter outward
const FAN_BANDS = [["lo90", "hi90", "rgba(173,42,53,0.13)", "90%"], ["lo80", "hi80", "rgba(173,42,53,0.24)", "80%"], ["lo50", "hi50", "rgba(173,42,53,0.40)", "50%"]];
const FAN_CENTRAL = "#7d1620";
const FIELDS = ["oil_price", "import_price", "export_price", "inflation_shock", "nonoil_growth",
  "partner_growth", "potential_growth", "tax", "policy_rate", "exchange_rate", "foreign_rate", "risk_premium"];
// single source for each scenario input: label, unit, and a plain-language definition (EN/AZ) — drives the
// scenario descriptor on figures and the per-field info buttons.
const FIELD_META = {
  oil_price: { en: "Oil price", az: "Neft qiyməti", u: "%", den: "Brent / Azeri crude price. Azerbaijan's exports and state budget are oil-dependent, so this is the dominant external driver of growth, the fiscal balance and the external accounts.", daz: "Brent / Azəri xam neft qiyməti. Azərbaycanın ixracı və dövlət büdcəsi neftdən asılıdır, ona görə bu — artımın, büdcə balansının və xarici hesabların əsas xarici amilidir." },
  import_price: { en: "Import price", az: "İdxal qiyməti", u: "%", den: "World price of imported goods (in foreign currency); feeds domestic inflation through import pass-through.", daz: "İdxal mallarının dünya qiyməti (xarici valyutada); idxal ötürülməsi ilə daxili inflyasiyaya təsir edir." },
  export_price: { en: "Export price", az: "İxrac qiyməti", u: "%", den: "World price of Azerbaijan's exports; together with import prices it sets the terms of trade.", daz: "Azərbaycan ixracının dünya qiyməti; idxal qiymətləri ilə birlikdə ticarət şərtlərini müəyyən edir." },
  inflation_shock: { en: "Supply-side price shock", az: "Təklif tərəfli qiymət şoku", u: "pp", den: "An exogenous supply-side price shock (e.g. food, energy or administered prices), in percentage points added to inflation.", daz: "Ekzogen təklif tərəfli qiymət şoku (məs. ərzaq, enerji və ya tənzimlənən qiymətlər), inflyasiyaya əlavə edilən faiz bəndi ilə." },
  nonoil_growth: { en: "Non-oil growth", az: "Qeyri-neft artımı", u: "pp", den: "A direct shock to non-oil real GDP growth — e.g. a structural reform or a sectoral shock.", daz: "Qeyri-neft real ÜDM artımına birbaşa şok — məs. struktur islahat və ya sektoral şok." },
  partner_growth: { en: "Partner growth", az: "Tərəfdaş artımı", u: "pp", den: "GDP growth of Azerbaijan's main trading partners — a proxy for external demand for non-oil exports.", daz: "Azərbaycanın əsas ticarət tərəfdaşlarının ÜDM artımı — qeyri-neft ixracına xarici tələbin göstəricisi." },
  potential_growth: { en: "Potential growth", az: "Potensial artım", u: "pp", den: "A shift in trend (potential) output growth — the economy's non-inflationary capacity.", daz: "Trend (potensial) məhsul artımında dəyişiklik — iqtisadiyyatın inflyasiyasız tutumu." },
  tax: { en: "Fiscal measures", az: "Fiskal tədbirlər", u: "%GDP", den: "Discretionary fiscal measures (revenue or spending), in % of GDP applied to the budget balance.", daz: "Diskresion fiskal tədbirlər (gəlir və ya xərc), büdcə balansına tətbiq olunan % ÜDM ilə." },
  policy_rate: { en: "Policy rate", az: "Uçot dərəcəsi", u: "pp", den: "A shift in the Central Bank refinancing rate beyond the smoothed Taylor-rule path.", daz: "Mərkəzi Bankın yenidən maliyyələşdirmə dərəcəsində hamarlanmış Taylor qaydası trayektoriyasından kənar dəyişiklik." },
  exchange_rate: { en: "Manat depreciation", az: "Manatın dəyərsizləşməsi", u: "%", den: "A depreciation of the manat against the US dollar (a higher value = weaker manat).", daz: "Manatın ABŞ dollarına qarşı dəyərsizləşməsi (yüksək dəyər = zəif manat)." },
  foreign_rate: { en: "Foreign rate", az: "Xarici faiz", u: "pp", den: "The foreign (US / global) interest rate — it passes through to the domestic rate and affects capital flows.", daz: "Xarici (ABŞ / qlobal) faiz dərəcəsi — daxili dərəcəyə ötürülür və kapital axınlarına təsir edir." },
  risk_premium: { en: "Risk premium", az: "Risk mükafatı", u: "pp", den: "The sovereign risk premium added to the domestic interest rate.", daz: "Daxili faiz dərəcəsinə əlavə edilən suveren risk mükafatı." },
};
const fieldLabel = f => { const m = FIELD_META[f]; return m ? (LANG === "az" ? m.az : m.en) : f.replace(/_/g, " "); };
const fieldUnit = f => (FIELD_META[f] && FIELD_META[f].u) || "";
// human-readable description of the active scenario, e.g. "Oil price −20%, Partner growth −2pp"
function scenarioText() {
  if (!RUN || !RUN.shock) return "";
  return FIELDS.filter(f => RUN.shock[f]).map(f => `${fieldLabel(f)} ${RUN.shock[f] > 0 ? "+" : "−"}${Math.abs(RUN.shock[f])}${fieldUnit(f)}`).join(", ");
}
// a Plotly annotation (top-left, inside canvas) naming the active scenario — visible on-screen AND in PNG exports
function scnAnno() {
  const t = scenarioText(); if (!t) return null;
  return {
    text: (LANG === "az" ? "Ssenari: " : "Scenario: ") + t + (LANG === "az" ? "  (punktir)" : "  (dashed)"),
    xref: "paper", yref: "paper", x: 0.01, y: 0.99, xanchor: "left", yanchor: "top", showarrow: false,
    font: { size: 10, color: "#b23b30", family: "Hanken Grotesk, sans-serif" }, align: "left",
    bgcolor: "rgba(255,255,255,0.82)", bordercolor: "rgba(177,50,42,0.5)", borderwidth: 1, borderpad: 3
  };
}
function scnLegName() { const t = scenarioText(), s = (LANG === "az" ? "Ssenari" : "Scenario"); return t ? s + " · " + (t.length > 26 ? t.slice(0, 25) + "…" : t) : s; }
// figures that ARE a scenario input — shocking it transforms the figure's own path (exact, not modelled).
// kind "level" = the shock is a % change to the level; "rate" = a sustained pp change to a rate series.
const SHOCK_FIG = [
  { re: /oil price|petroleum|crude/i, field: "oil_price", kind: "level" },
  { re: /import price/i, field: "import_price", kind: "level" },
  { re: /nominal exchange rate|exchange rate \(%/i, field: "exchange_rate", kind: "level" },
  { re: /partner/i, field: "partner_growth", kind: "rate" },
];
const shockMatch = title => SHOCK_FIG.find(s => s.re.test(title || ""));
// current-account figures (single-series, % of GDP) respond to an oil-price shock via a labelled
// elasticity (oil +1% → CA +0.12 pp of GDP) — perturbs the real CAEM baseline, like the fiscal/ToT channels.
const CA_ELAS = 0.12;
const caElas = f => !f.engine_var && f.series && f.series.length === 1 && /current account/i.test(f.title || "") && /%\s*of GDP|Percent of GDP/i.test(f.unit || "");
const isLive = f => !!(f.engine_var || (shockMatch(f.title) && !f.radar) || caElas(f));
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
  "con.title": "Ssenari paneli",
  "con.hint": "Proqnoza şok tətbiq edin və Hesabla düyməsini basın. CANLI qrafiklər və yelpik qrafikləri yenidən hesablanır, ssenari bazis xəttinin üzərinə qırmızı punktirlə düşür. Neft, qiymətlər və məzənnə %-lə, qalanları faiz bəndi ilə.",
  "con.apply": "Tətbiq", "con.to": "–", "con.editdata": "✎ Məlumatı yenilə", "con.save": "💾 Yadda saxla",
  "con.run": "Hesabla ▸", "con.reset": "Sıfırla", "con.presets": "Hazır ssenarilər", "con.adjust": "Şokları tənzimlə",
  "cat.external": "Xarici", "cat.real": "Real iqtisadiyyat və fiskal", "cat.mon": "Monetar və məzənnə",
  "fld.oil": "Neft qiyməti", "fld.partner": "Tərəfdaş artımı", "fld.import": "İdxal qiyməti", "fld.export": "İxrac qiyməti",
  "fld.nonoil": "Qeyri-neft artımı", "fld.potential": "Potensial artım", "fld.supply": "Təklif şoku", "fld.tax": "Vergi tədbirləri",
  "fld.policy": "Uçot dərəcəsi", "fld.fx": "Məzənnə (dəyərsizləşmə)", "fld.foreign": "Xarici faiz", "fld.risk": "Risk mükafatı",
  "nav.home": "🏠 Əsas səhifə və icmal", "nav.live": "📈 Canlı proqnoz və yelpik qrafikləri",
  "nav.methods": "📐 Metodologiya və mənbələr", "nav.scen": "📂 Saxlanmış ssenarilər",
  "nav.summary": "★ İcmal panelləri", "nav.detail": "Ətraflı təhlil", "nav.detailsub": "qrafik · canlı ▲",
  // home / overview
  "home.eyebrow": "MALİYYƏ PROQRAMLAŞDIRMASI · MAKRO-FİSKAL MODEL",
  "home.h1": "Azərbaycan Respublikası üçün canlı makro-fiskal proqnozlaşdırma",
  "home.cta": "Canlı proqnozu və yelpik qrafiklərini açın →",
  "home.baseline": "Bazis — modelin mərkəzi trayektoriyası", "home.baseline.k": "ƏSAS PROQNOZ",
  "home.baseline.tag": "model proqnozları (2026+), faktiki nəticə deyil",
  "home.engine": "Mühərrik necə işləyir", "home.engine.tag": "CAEM-dən təkrar yaradılıb, iş kitabına qarşı yoxlanılıb",
  "home.built": "Oxlon nə qurub", "home.howto": "İstifadə qaydası", "home.explore": "CAEM panellərini araşdırın",
  "home.figs": "qrafik", "home.live": "canlı",
  "home.methodslink": "Metodologiya və mənbələr", "home.vintage": "Proqnoz buraxılışı", "home.lastactual": "Son faktiki",
  // engine mini-cards
  "eng.gap": "Məhsul buraxılışı kəsiri", "eng.gap.d": "Loqarifmik qeyri-neft ÜDM üzrə HP filtri (λ=100), CAEM B1a vərəqi.",
  "eng.inf": "İnflyasiya", "eng.inf.d": "Açıq iqtisadiyyat Phillips əyrisi: davamlılıq, gözləntilər, idxal ötürülməsi, kəsir (1b).",
  "eng.rate": "Faiz dərəcəsi", "eng.rate.d": "İnflyasiya və məhsul kəsirinə reaksiya verən hamarlanmış Taylor qaydası (1c).",
  "eng.debt": "Dövlət borcu", "eng.debt.d": "Standart nisbət rekursiyası, artım, inflyasiya və ilkin balans əsasında (3b).",
  "eng.fisc": "Fiskal və neft", "eng.fisc.d": "Neft qiyməti → gəlir/balans/borc və artım, şəffaf elastiklik əmsalları vasitəsilə.",
  "eng.fan": "Yelpik qrafikləri", "eng.fan.d": "Etibarlılıq zolaqları proqnoz üfüqü boyunca mərkəzi trayektoriya ətrafında genişlənir.",
  "eng.valid": "doğrulama", "eng.scn": "ssenari", "eng.dyn": "dinamika", "eng.unc": "qeyri-müəyyənlik",
  // live view
  "live.h": "📈 Canlı proqnoz", "live.fans": "Yelpik qrafikləri — mərkəzi trayektoriya və qeyri-müəyyənlik (Bank of England üslubu)",
  "live.all": "Bütün canlı qrafiklər (ssenari ilə yenidən hesablanır)",
  "btn.pdf": "🖨 PDF hesabat", "btn.xls": "⤓ Excel", "btn.csv": "⤓ CSV",
  // scorecard
  "sc.h": "2025 hesab kartı, CAEM proqnozu faktiki nəticəyə qarşı", "sc.tag": "Dövlət Statistika Komitəsi, yanvar 2026-da dərc olunub",
  "sc.indicator": "Göstərici", "sc.forecast": "CAEM proqnozu", "sc.actual": "2025 faktiki", "sc.error": "Xəta", "sc.mae": "Orta mütləq xəta",
  // impact + compare
  "imp.h": "Ssenari təsiri", "imp.shock": "şok", "cmp.at": "Müqayisə",
  // methods headings
  "m.h": "📐 Metodologiya və məlumat mənbələri",
  "m.h1": "1 · Əsas tənliklər (CAEM-dən təkrar yaradılıb, yoxlanılıb)",
  "m.h2": "2 · Ssenari kanalları (şəffaf, Azərbaycana uyğunlaşdırılmış elastiklik əmsalları)",
  "m.h3": "3 · Yelpik qrafikləri (qeyri-müəyyənlik)",
  "m.h4": "4 · Məlumat və mənbələr", "m.h5": "5 · 2025 proqnozu faktiki nəticəyə qarşı (modelin dəqiqliyi)",
  "m.col.block": "Blok", "m.col.spec": "Spesifikasiya", "m.col.valid": "Doğrulama",
  // scenarios view
  "scn.h": "📂 Saxlanmış ssenarilər və proqnoz dövrləri",
  "scn.name": "Ad", "scn.shock": "Şok / məlumat", "scn.load": "Yüklə və işə sal", "scn.del": "Sil",
  "scn.cmp": "Seçilmişləri müqayisə et", "scn.delall": "Hamısını sil",
  // group / figure scaffolding
  "grp.figs": "qrafik", "grp.live": "canlı yenilənir", "grp.dashed": "Qırmızı punktir = cari ssenari.",
  "grp.runhint": "Bazis üzərinə əlavə etmək üçün yuxarıdakı paneldə ssenari təyin edin.", "grp.shade": "Kölgələnmiş zolaq = proqnoz",
  "grp.lastact": "2025 = son faktiki", "u.forecast": "proqnoz",
  // info drawer
  "id.eyebrow": "BU QRAFİK HAQQINDA", "id.shows": "Nə göstərir", "id.model": "Model və məlumat", "id.read": "Necə oxunmalı",
  "id.live": "Canlı", "id.src": "Mənbə və mənşə", "id.data": "Məlumat", "id.year": "İl",
  "id.live.p": "Ssenari panelində giriş dəyişdirib <b>Hesabla</b> basdıqda yenidən hesablanır; qırmızı punktir xətt ssenarini bütöv bazis xəttinə qarşı göstərir.",
  "id.vintage": "2025 = rəsmi faktiki; model <b>2026+</b> proqnozlaşdırır (kölgələnib).",
  "id.vintage2": "Kölgələnmiş = proqnoz <b>2026+</b>; 2025 = son faktiki. Bu qrafikin 2025 nöqtəsi CAEM-in qiymətləndirməsidir — rəsmi 2025 nəticələri hesab kartındadır.",
  "id.fan": "Yelpik qrafiki. Mərkəzi trayektoriya mühərrikdən; 50/80/90% zolaqları σ·z·√h kimi genişlənir — σ tənliyin daxili qalıqlarından (inflyasiya və uçot dərəcəsi) və ya dəyişənin tarixi illik dəyişmə σ-sından.",
  // quarterly & nowcast view
  "nav.qtr": "📅 Rüblük və nowcast", "qtr.h": "📅 Rüblük göstəricilər və nowcast",
  "nav.nb": "📓 Dəftərlər (Colab)", "nb.h": "📓 Təkrar istehsal oluna bilən dəftərlər",
  "nav.bench": "📊 Proqnoz müqayisəsi", "bench.h": "📊 Proqnoz müqayisəsi, İMF və CAEM ilə",
  "nb.open": "Colab-da aç ↗", "nb.pending": "Colab linki gözlənilir",
  "qtr.nowcast": "Nowcast körpüsü", "qtr.implied": "rüblük əsasda nəzərdə tutulan illik", "qtr.official": "rəsmi illik",
  "qtr.q": "rüb", "qtr.observed": "müşahidə olunub",
  // per-figure buttons
  "fig.enlarge": "Böyüt", "fig.png": "Yüksək keyfiyyətli PNG yüklə", "fig.info": "Bu qrafik haqqında", "fig.infolbl": "məlumat",
  "id.terms": "Bu qrafikdəki terminlər", "leg.baseline": "Bazis",
};
// per-variable descriptions in Azerbaijani (mirror of VARDESC)
const VARDESC_AZ = {
  real_gdp_growth: "Ümumi real ÜDM artımı — neft və qeyri-neft sektorları birlikdə; əsas məhsul göstəricisi.",
  nonoil_growth: "Qeyri-neft real ÜDM artımı — siyasətin ən çox təsir etdiyi hissə; məhsul kəsirini formalaşdırır.",
  inflation: "Əsas İQİ inflyasiyası, açıq iqtisadiyyat Phillips əyrisi ilə yaradılır.",
  policy_rate: "Nominal uçot (yenidən maliyyələşdirmə) dərəcəsi, hamarlanmış Taylor qaydası ilə təyin olunur.",
  output_gap: "Məhsul kəsiri: faktiki minus HP-filtr potensialı, qeyri-neft ÜDM potensialının %-i — tsiklik mövqe.",
  trend_growth: "Qeyri-neft ÜDM-in HP-filtr trend (potensial) artımı.",
  gross_debt: "Ümumi dövlət borcu, ÜDM-in %-i, borc-dinamika rekursiyasından.",
  fiscal_balance: "Fiskal (ilkin) balans, ÜDM-in %-i.",
  primary_balance: "İlkin fiskal balans, ÜDM-in %-i — faiz ödənişləri istisna olmaqla ümumi balans.",
  terms_of_trade: "Ticarət şərtləri — ixrac qiymətləri idxal qiymətlərinə nisbətdə; Azərbaycan üçün neft üstünlüklü.",
};
// indicator labels — translated wherever they appear (KPIs, scorecard, impact, compare)
const IND_AZ = {
  "Real GDP growth": "Real ÜDM artımı", "Non-oil GDP growth": "Qeyri-neft ÜDM artımı", "Non-oil growth": "Qeyri-neft artımı",
  "Inflation (CPI)": "İnflyasiya (İQİ)", "CPI inflation": "İQİ inflyasiyası", "Policy rate": "Uçot dərəcəsi",
  "Fiscal balance": "Büdcə balansı", "Fiscal balance (% GDP)": "Büdcə balansı (% ÜDM)",
  "Gross public debt": "Ümumi dövlət borcu", "Terms of trade": "Ticarət şərtləri", "Primary balance": "İlkin balans",
};
const tx = (k, def) => (LANG === "az" && AZ[k]) ? AZ[k] : def;     // translate-or-default
const tInd = s => (LANG === "az" && IND_AZ[s]) ? IND_AZ[s] : s;    // translate an indicator label
// ---- refined monochrome line-icons: replace the informal emoji in the nav and section titles ----
const ICONS = {
  home:    '<path d="M3 11l9-7 9 7"/><path d="M5.5 9.7V20h13V9.7"/><path d="M10 20v-5.2h4V20"/>',
  live:    '<path d="M4 5v14h16"/><path d="M7 14.5l3.3-3.6 3 2L18 6"/>',
  methods: '<path d="M12 6.4C9.7 5 7.4 5 4.5 6.1V19c2.9-1.1 5.2-1.1 7.5.3 2.3-1.4 4.6-1.4 7.5-.3V6.1C16.6 5 14.3 5 12 6.4z"/><path d="M12 6.4V19.3"/>',
  qtr:     '<rect x="3.5" y="5" width="17" height="15" rx="2.2"/><path d="M3.5 9.6h17"/><path d="M8 3.4v3.2M16 3.4v3.2"/>',
  nb:      '<path d="M9.2 8.2L5.6 12l3.6 3.8"/><path d="M14.8 8.2L18.4 12l-3.6 3.8"/>',
  bench:   '<path d="M3.5 20h17"/><path d="M6.6 20v-5.6"/><path d="M12 20V4.6"/><path d="M17.4 20v-8.6"/>',
  scen:    '<path d="M12 3.6l8.4 4.5L12 12.6 3.6 8.1z"/><path d="M3.6 12.6L12 17.1l8.4-4.5"/>'
};
const ic = n => ICONS[n] ? `<span class="nico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${ICONS[n]}</svg></span>` : "";
const deLead = s => String(s).replace(/^\s*(?:[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}⭐★☆⚙]️?\s*)+/u, "");
function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    if (el.dataset.en === undefined) el.dataset.en = el.textContent;
    const az = AZ[el.dataset.i18n];
    el.textContent = (LANG === "az" && az) ? az : el.dataset.en;
  });
  const lg = document.getElementById("lang");
  if (lg) lg.innerHTML = `<b class="${LANG === "en" ? "on" : ""}" data-l="en">EN</b><span>·</span><b class="${LANG === "az" ? "on" : ""}" data-l="az">AZ</b>`;
}
function rerender() {
  if (CURMODE === "home") showHome(); else if (CURMODE === "live") showLive();
  else if (CURMODE === "methods") showMethods(); else if (CURMODE === "scenarios") showScenarios();
  else if (CURMODE === "quarterly") showQuarterly();
  else if (CURMODE === "notebooks") showNotebooks();
  else showGroup(CURMODE);
}
function setLang(l) { LANG = l; try { localStorage.setItem("caem_lang", l); } catch (e) { } applyI18n(); buildNav(); renderPresets(); rerender(); }

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
  buildNav(); wireRun(); wireFieldInfo(); applyI18n();
  $("#brand").style.cursor = "pointer"; $("#brand").onclick = showHome;
  $("#lang").onclick = e => { const l = e.target.dataset.l; if (l && l !== LANG) setLang(l); };
  $("#infoscrim").onclick = closeInfo; $("#infoclose").onclick = closeInfo;
  $("#figscrim").onclick = closeFigModal; $("#figmodalclose").onclick = closeFigModal;
  document.addEventListener("keydown", e => { if (e.key === "Escape") { closeInfo(); closeFigModal(); } });
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
    `<div class="navhome" id="navhome">${ic("home")}${deLead(tx("nav.home", "🏠 Home &amp; overview"))}</div>
     <div class="navlive" id="navlive">${ic("live")}${deLead(tx("nav.live", "📈 Live forecast &amp; fan charts"))}</div>
     <div class="navlive navmethods" id="navmethods">${ic("methods")}${deLead(tx("nav.methods", "📐 Methods &amp; data sources"))}</div>
     <div class="navlive navqtr" id="navqtr">${ic("qtr")}${deLead(tx("nav.qtr", "📅 Quarterly &amp; nowcast"))}</div>
     <div class="navlive navnb" id="navnb">${ic("nb")}${deLead(tx("nav.nb", "📓 Notebooks (Colab)"))}</div>
     <div class="navlive navbench" id="navbench">${ic("bench")}${deLead(tx("nav.bench", "📊 Forecast benchmark"))}</div>
     <div class="navlive navscen" id="navscen">${ic("scen")}${deLead(tx("nav.scen", "📂 Saved scenarios &amp; compare"))}</div>
     <div class="navsec">${tx("nav.summary", "★ Summary dashboards")} <span>${tx("nav.detailsub", "figures · live ▲")}</span></div>` + summ.map(navlink).join("") +
    `<div class="navsec">${tx("nav.detail", "Detailed analysis")} <span>${tx("nav.detailsub", "figures · live ▲")}</span></div>` + detail.map(navlink).join("");
  document.querySelectorAll("#nav .navlink").forEach(a => a.onclick = () => showGroup(dec(a.dataset.s)));
  $("#navhome").onclick = showHome;
  $("#navlive").onclick = showLive;
  $("#navmethods").onclick = showMethods;
  $("#navqtr").onclick = showQuarterly;
  $("#navnb").onclick = showNotebooks;
  $("#navbench").onclick = showBenchmark;
  $("#navscen").onclick = showScenarios;
}

function setActive(mode) {
  CURMODE = mode;
  $("#navhome").classList.toggle("active", mode === "home");
  $("#navlive").classList.toggle("active", mode === "live");
  $("#navmethods").classList.toggle("active", mode === "methods");
  $("#navqtr").classList.toggle("active", mode === "quarterly");
  $("#navnb").classList.toggle("active", mode === "notebooks");
  $("#navbench").classList.toggle("active", mode === "benchmark");
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
    <div class="k">${esc(tInd(label))}</div><div class="y">${yr} ${tx("u.forecast", "forecast")}</div></div>`;
}
function showHome() {
  CUR = null; setActive("home");
  const p = META.params || {};
  const gcards = GROUPS.map(g => {
    const live = g.figs.filter(f => f.engine_var).length;
    return `<div class="gcard" data-go="${enc(g.sheet)}" style="border-left:4px solid ${headCol(g.hue)}">
      <div class="gn">${esc(g.sheet)}</div><div class="gs">${g.figs.length} ${tx("home.figs", "figures")}${live ? ` · ${live} ${tx("home.live", "live")}` : ""}</div></div>`;
  }).join("");
  const intro = LANG === "az"
    ? `IMF CAEM Maliyyə Proqramlaşdırma modelinin Azərbaycana uyğunlaşdırılmış veb tətbiqi. Ssenari panelində fərziyyəni dəyişin və mərkəzi proqnoz — məhsul kəsiri, inflyasiya, uçot dərəcəsi, borc və büdcə balansı — yenidən hesablanıb qrafiklərə əlavə olunur.`
    : `A web implementation of the IMF CAEM Financial-Programming model, calibrated to Azerbaijan. Change an assumption in the Scenario console and the central forecast — output gap, inflation, the policy rate, debt and the fiscal balance — recomputes and overlays the charts.`;
  const mc = [
    [tx("eng.gap", "Output gap"), tx("eng.gap.d", "HP filter (λ=100) on log non-oil GDP, CAEM sheet B1a."), "≈0.18 pp"],
    [tx("eng.inf", "Inflation"), tx("eng.inf.d", "Open-economy Phillips curve: persistence, expectations, import pass-through, gap (1b)."), "≈0.01 pp"],
    [tx("eng.rate", "Interest rate"), tx("eng.rate.d", "Smoothed Taylor rule with inflation &amp; output-gap response (1c)."), "≈0.07 pp"],
    [tx("eng.debt", "Public debt"), tx("eng.debt.d", "Standard ratio recursion in growth, inflation and the primary balance (3b)."), tx("eng.dyn", "dynamics")],
    [tx("eng.fisc", "Fiscal &amp; oil"), tx("eng.fisc.d", "Oil-price → revenue/balance/debt and growth, via transparent elasticities."), tx("eng.scn", "scenario")],
    [tx("eng.fan", "Fan charts"), tx("eng.fan.d", "Confidence bands widen with the forecast horizon around the engine's central path."), tx("eng.unc", "uncertainty")],
  ];
  const how = LANG === "az"
    ? [`<b>Görünüş seçin.</b> <b>Canlı proqnoz</b> mühərrikin mərkəzi trayektoriyasını və yelpik qrafiklərini təqdim edir; soldakı panellər qrafikləri mövzu üzrə qruplaşdırır.`,
      `Ssenari panelində <b>ssenari təyin edin</b> — məsələn, neft qiymətinin 30% düşməsi — üfüqü seçin və işə salın.`,
      `Canlı qrafiklər yenidən hesablanır və <b>ssenari</b> bazis xəttinin üzərinə qırmızı punktir kimi düşür; <b>Sıfırla</b> bazisi bərpa edir.`,
      `İstənilən proqnoz Canlı görünüşdən <b>CSV</b>, <b>Excel</b> və ya <b>PDF</b> kimi ixrac edilə bilər.`]
    : [`<b>Select a view.</b> The <b>Live forecast</b> presents the engine’s central path and fan charts; the dashboards listed on the left group the figures by theme.`,
      `<b>Define a scenario</b> in the console — for example a 30% fall in the oil price — set the horizon and run it.`,
      `The live figures recompute and the <b>scenario</b> is overlaid on the baseline as a dashed red line; <b>Reset</b> restores the baseline.`,
      `Any forecast can be exported to <b>CSV</b>, <b>Excel</b> or <b>PDF</b> from the Live view.`];
  const built = LANG === "az" ? [
    ["Məlumat bazası", "Rəsmi seriyalar (Dövlət Statistika Komitəsi, Mərkəzi Bank, Maliyyə Nazirliyi və Gömrük) harmonlaşdırılıb və 2025 son faktiki il kimi əsaslanıb."],
    ["Model dəsti", "Struktur CAEM blokları (məhsul kəsiri, Phillips əyrisi, Taylor qaydası, borc dinamikası), üstəgəl ekonometrik və maşın öyrənməsi ansamblı, hər seriya üçün nümunədənkənar bacarığa görə seçilir."],
    ["Doğrulama", "Nüvə CAEM iş kitabına təxminən 0.1 faiz bəndi dəqiqliklə təkrar istehsal olunub, proqnoz isə IMF Article IV ilə müqayisə edilib."],
    ["Nə edir", "Canlı ssenari yenidən hesablanması, Bank-of-England yelpik qrafikləri və CSV, Excel, PDF ixracı."],
  ] : [
    ["Data foundation", "Official series from the Statistics Committee, the Central Bank, the Ministry of Finance and Customs, harmonised, with 2025 anchored as the last actual year."],
    ["Model suite", "Structural CAEM blocks (output gap, Phillips curve, Taylor rule, debt dynamics), plus an econometric and machine-learning ensemble selected per series on out-of-sample skill."],
    ["Validation", "The core is reproduced to about 0.1 of a percentage point against the CAEM workbook, and the forecast is benchmarked against the IMF Article IV projection."],
    ["What it does", "Live scenario recompute, Bank-of-England fan charts, and export to CSV, Excel and PDF, all in the browser with no backend."],
  ];
  $("#view").innerHTML = `
    <div class="home-hero">
      <div class="he-inner">
        <div class="he-eyebrow">${tx("home.eyebrow", "FINANCIAL PROGRAMMING · MACRO-FISCAL MODEL")}</div>
        <h1>${tx("home.h1", "Live macro-fiscal forecasting for the Republic of Azerbaijan")}</h1>
        <p>${intro}</p>
        <div class="he-actions">
          <span class="he-cta" id="ctaLive">${tx("home.cta", "Open the live forecast &amp; fan charts →")}</span>
          <span class="he-link" id="ctaMethods">${tx("home.methodslink", "Methods &amp; data sources")}</span>
        </div>
        <div class="he-stamp">
          <span>${tx("home.vintage", "Forecast vintage")} <b>${META.first_forecast}+</b></span>
          <span>${tx("home.lastactual", "Last actual")} <b>2025</b></span>
          <span><b>${NFIG}</b> ${tx("home.figs", "figures")} · <b>${NLIVE}</b> ${tx("home.live", "live")}</span>
        </div>
      </div>
    </div>
    <div class="hsec hsec-lead"><div class="lead-h"><span class="lead-k">${tx("home.baseline.k", "HEADLINE FORECAST")}</span><h2>${tx("home.baseline", "Baseline — model central path")} <span class="tagi">${tx("home.baseline.tag", "model projections (2026+), not outturns")}</span></h2></div>
      <div class="kpis">
        ${kpi("Real GDP growth", "real_gdp_growth", 2026, "%", true)}
        ${kpi("Inflation (CPI)", "inflation", 2026, "%", false)}
        ${kpi("Policy rate", "policy_rate", 2026, "%", false)}
        ${kpi("Fiscal balance", "fiscal_balance", 2028, "%GDP", true)}
        ${kpi("Gross public debt", "gross_debt", 2029, "%GDP", false)}
      </div>
    </div>
    <div class="hsec">${scorecardHTML()}</div>

    <div class="hsec"><h2>${tx("home.engine", "How the engine works")} <span class="tagi">${tx("home.engine.tag", "reproduced from CAEM, validated against the workbook")}</span></h2>
      <div class="grid3">
        ${mc.map(([t, d, v]) => `<div class="mcard mcard-go"><b>${t}</b><span>${d}</span><i>${v}</i></div>`).join("")}
      </div>
    </div>

    <div class="hsec"><h2>${tx("home.explore", "Explore the CAEM dashboards")}</h2><div class="grid3 gc">${gcards}</div></div>
    <div class="hfoot">CAEM Financial-Programming model · phillips ${(p.phillips || []).join("/")} · taylor ${(p.taylor || []).join("/")} · reproduced &amp; extended in Python. ${tx("grp.shade", "Shaded region = forecast")} (${META.first_forecast}+).</div>`;
  document.querySelectorAll(".gcard").forEach(c => c.onclick = () => showGroup(dec(c.dataset.go)));
  document.querySelectorAll(".mcard-go").forEach(c => c.onclick = showLive);
  $("#ctaLive").onclick = showLive;
  if ($("#ctaMethods")) $("#ctaMethods").onclick = showMethods;
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
  const liveSub = LANG === "az"
    ? `Mühərrikin mərkəzi proqnozu <b>yelpik qrafikləri</b> ilə (üfüq boyunca genişlənən etibarlılıq zolaqları), sonra hər bir canlı qrafik. <b>2025 = rəsmi faktiki; proqnoz 2026+.</b> ${onScn ? `Aktiv ssenari: <b>${esc(shockTxt)}</b> — qırmızı punktir bazis üzərinə düşür.` : "Bazis üzərinə əlavə etmək üçün yuxarıdakı paneldə ssenari təyin edin."}`
    : `The engine's central forecast with <b>fan charts</b> (confidence bands that widen with the horizon), then every live figure. <b>2025 = official outturn; forecast 2026+.</b> ${onScn ? `Scenario active: <b>${esc(shockTxt)}</b> — dashed red overlays the baseline.` : "Define a scenario in the console above to overlay it on the baseline."}`;
  const transmission = LANG === "az"
    ? `Ötürülmə: neft qiyməti → qeyri-neft artımı, büdcə balansı və borc, və daxili inflyasiya; Phillips əyrisi inflyasiyanı məhsul kəsiri və idxal qiymətlərindən təyin edir; Taylor qaydası uçot dərəcəsini müəyyən edir; borc artım, inflyasiya və ilkin balansla dəyişir.`
    : `Transmission: oil price → non-oil growth, the budget balance &amp; debt, and domestic inflation; the Phillips curve sets inflation from the output gap &amp; import prices; the Taylor rule sets the policy rate; debt evolves with growth, inflation &amp; the primary balance.`;
  $("#view").innerHTML = `
    <div class="ghead" style="color:var(--ink);border-color:var(--accent)">${ic("live")}${deLead(tx("live.h", "📈 Live forecast"))} <span class="dlgrp"><button id="prpdf" class="dlbtn">${tx("btn.pdf", "🖨 PDF report")}</button><button id="dlxls" class="dlbtn">${tx("btn.xls", "⤓ Excel")}</button><button id="dlcsv" class="dlbtn">${tx("btn.csv", "⤓ CSV")}</button></span></div>
    <div class="gsub">${liveSub}</div>
    ${impactHTML()}
    ${scorecardHTML()}
    <div class="note-eco">${transmission}</div>
    <h3 class="lh">${tx("live.fans", "Fan charts — central path &amp; uncertainty (Bank-of-England style)")}</h3>
    <div class="figgrid" id="fangrid"></div>
    <h3 class="lh">${tx("live.all", "All live figures (recompute with the scenario)")}</h3>
    <div class="figgrid" id="livegrid"></div>`;
  const fg = $("#fangrid");
  Object.keys(labels).forEach(k => {
    if (!fan[k]) return;
    const lbl = tInd(labels[k]), fk = fan[k];
    const card = document.createElement("div"); card.className = "figcard"; card.style.borderTopColor = "#7d1620";
    card.innerHTML = `<div class="ft">${esc(lbl)}<span class="live live-fan">FAN</span></div>
      <div class="fu">${esc(units[k] || "")}</div><div class="fc" id="fan_${k}"></div>`;
    fg.appendChild(card); drawFan(`fan_${k}`, fan[k], false, true);
    const fanSeries = [
      { name: lbl, x: fk.years, y: fk.central },
      { name: (LANG === "az" ? "Aşağı 90%" : "Low 90%"), x: fk.years, y: fk.lo90 },
      { name: (LANG === "az" ? "Yuxarı 90%" : "High 90%"), x: fk.years, y: fk.hi90 },
    ];
    attachInfo(card, { title: lbl, unit: units[k], sheet: "Live engine", engine_var: k, fan: true, series: fanSeries });
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
  const ff = LIVE_FF || META.first_forecast;
  const sub = isRisk
    ? (LANG === "az"
      ? `Üç qiymət-riski ssenarisi — <b>neft</b>, <b>ərzaq</b> və <b>idxal</b> qiymətləri — hər biri bazis trayektoriyası ətrafında yelpik kimi göstərilir (zolaq üfüqlə genişlənir). Uyğun panel girişini (Neft qiyməti, İdxal qiyməti) şoklayaraq onun yelpiyini yenidən mərkəzləşdirin. ${tx("grp.shade", "Shaded band = forecast")} (${ff}+); ${tx("grp.lastact", "2025 = last actual")}.`
      : `Three price-risk scenarios — <b>oil</b>, <b>food</b> and <b>import</b> prices — each shown as a fan around the baseline path (the band widens with the horizon). Shock the matching console input (Oil price, Import price) to re-centre its fan. Shaded band = forecast (${ff}+); 2025 = last actual.`)
    : (LANG === "az"
      ? `“${esc(sheet)}” CAEM vərəqindən ${g.figs.length} ${tx("grp.figs", "figures")}${live ? ` · ${live} ${tx("grp.live", "recompute live")}` : ""}. ${RUN ? tx("grp.dashed", "Dashed red = current scenario.") : tx("grp.runhint", "Define a scenario in the console above to overlay it on the baseline.")} ${tx("grp.shade", "Shaded band = forecast")} (${ff}+); ${tx("grp.lastact", "2025 = last actual")}.`
      : `${g.figs.length} figures from CAEM sheet “${esc(sheet)}”${live ? ` · ${live} recompute live` : ""}. ${RUN ? "Dashed red = current scenario." : "Define a scenario in the console above to overlay it on the baseline."} Shaded band = forecast (${ff}+); 2025 = last actual.`);
  $("#view").innerHTML = `<div class="ghead" style="color:var(--ink);border-color:${headCol(g.hue)}">${esc(sheet)}</div>
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
  const az = LANG === "az";
  const els = az
    ? [["Neft qiyməti → qeyri-neft artımı", "0.02 f.b. / 1%"], ["Neft qiyməti → büdcə balansı", "0.12 f.b. ÜDM / 1%"],
      ["Neft qiyməti → inflyasiya", "0.01 f.b. / 1%"], ["Tərəfdaş artımı → qeyri-neft artımı", "0.30 f.b. / 1 f.b."],
      ["Məzənnə (dəyərsizləşmə) → artım", "0.05 f.b. / 1%"], ["Məzənnə → fiskal balans", "0.06 f.b. ÜDM / 1%"],
      ["Xarici faiz → daxili faiz", "0.5 ötürülmə"], ["Neft qiyməti → ticarət şərtləri", "0.30 / 1%"],
      ["Neft qiyməti → cari hesab", "0.12 f.b. ÜDM / 1%"]]
    : [["Oil price → non-oil growth", "0.02 pp / 1%"], ["Oil price → fiscal balance", "0.12 pp of GDP / 1%"],
      ["Oil price → inflation", "0.01 pp / 1%"], ["Partner growth → non-oil growth", "0.30 pp / 1pp"],
      ["Exchange rate (depr.) → growth", "0.05 pp / 1%"], ["Exchange rate → fiscal", "0.06 pp of GDP / 1%"],
      ["Foreign rate → domestic rate", "0.5 pass-through"], ["Oil price → terms of trade", "0.30 / 1%"],
      ["Oil price → current account", "0.12 pp of GDP / 1%"]];
  $("#view").innerHTML = `
    <div class="ghead" style="color:var(--ink);border-color:var(--accent)">${ic("methods")}${deLead(tx("m.h", "📐 Methods &amp; data sources"))}</div>
    <div class="gsub">${az ? "Hər tənlik, onun kalibrlənməsi və hər məlumat mənbəyi yoxlanıla və təkrar istehsal oluna biləndir. Struktur bloklar CAEM-i təkrar yaradır (iş kitabına qarşı doğrulanıb), neft, fiskal və xarici kanallar isə şəffaf, etiketlənmiş elastiklik əmsallarıdır." : "Every equation, its calibration and every data source is auditable and reproducible. The structural blocks reproduce CAEM, validated against the workbook, and the oil, fiscal and external channels are transparent, labelled elasticities."}</div>

    <h3 class="lh">${tx("m.h1", "1 · Core equations (reproduced from CAEM, validated)")}</h3>
    ${eqs.map(([n, tex, plain, note, v], i) => `<div class="methodeq">
      <div class="me-h"><b>${esc(n)}</b><span class="me-v">${esc(v)}</span></div>
      ${kx(tex, plain, "(" + (i + 1) + ")")}
      ${note ? `<div class="eqcal">${esc(note)}</div>` : ""}
    </div>`).join("")}

    <h3 class="lh">${tx("m.h2", "2 · Scenario channels (transparent, Azerbaijan-calibrated elasticities)")}</h3>
    <div class="note-eco">${az ? "Şəffaf, etiketlənmiş ixtisar olunmuş reaksiyalar: hər ssenari rəqəmi göstərilən elastikliyə qədər izlənə bilir və CAEM-in tam uçot çərçivəsini tamamlayır." : "Transparent, labelled reduced-form responses: every scenario number is traceable to a stated elasticity, complementing CAEM's full accounting framework."}</div>
    <div class="mtbl"><table class="dt"><tbody>${els.map(([n, v]) => `<tr><td>${n}</td><td class="sc-mid">${v}</td></tr>`).join("")}</tbody></table></div>

    <h3 class="lh">${tx("m.h3", "3 · Fan charts (uncertainty)")}</h3>
    <p class="mp">${az ? "Mərkəzi trayektoriya mühərrikdən; 50 / 80 / 90% zolaqları üfüqlə σ·z·√h kimi genişlənir, burada σ dəyişənin tarixi illik dəyişməsinin standart kənarlaşmasıdır (bir kəskin kənar dəyər çıxarılıb; 0.4–1.8 ilə məhdudlaşdırılıb). Kalibrlənmiş qeyri-müəyyənlik diapazonu, zolaq kənarlarının proqnozu deyil." : "Central path from the engine; 50 / 80 / 90% bands widen with the horizon as σ·z·√h, where σ is the variable's historical annual-change standard deviation (one extreme outlier dropped; capped 0.4–1.8). A calibrated uncertainty range, not a prediction of the band edges."}</p>

    <h3 class="lh">${tx("m.h4", "4 · Data &amp; provenance")}</h3>
    <p class="mp">${az ? "Bütün seriyalar üçün standart mənbə" : "Default source for all series"}: <b>${esc(caem)}</b></p>
    <div class="mtbl"><table class="dt"><thead><tr><th>${az ? "2025 rəsmi faktiki" : "2025 official actual"}</th><th>${az ? "Dəyər" : "Value"}</th><th>${az ? "Mənbə" : "Source"}</th><th>${az ? "Dərc olunub" : "Released"}</th></tr></thead>
      <tbody>${provRows || `<tr><td colspan="4">${az ? "Rəsmi faktiki məlumat yüklənməyib." : "No official actuals loaded."}</td></tr>`}</tbody></table></div>
    <p class="mp">${az ? "<b>Məlumat əhatəsi:</b> yuxarıdakı dörd rəsmi 2025 göstəricisi modelə daxil edilib; qalan seriyalar DSK / AMB tərəfindən dərc olunana qədər CAEM-in 2024 buraxılışı qiymətləndirməsini saxlayır. Daxiletmə ardıcıllığı (<code>apply_actuals.py</code>) yeni rəsmi məlumat dərc olunduqda bütün məlumat bazasını yeniləyir." : "<b>Data coverage:</b> the four official 2025 indicators above are incorporated into the model; the remaining series retain CAEM's 2024-vintage estimate for 2025 pending their release by the SSC / CBAR. The ingestion pipeline (<code>apply_actuals.py</code>) updates the full dataset as new official figures are published."}</p>

    <h3 class="lh">${tx("m.h5", "5 · 2025 forecast vs outturn (model skill)")}</h3>
    ${scorecardHTML()}

    ${ministryModelsHTML()}

    ${accountingHTML()}

    <div class="hfoot">${az ? "Python-da CAEM.xlsb-dən təkrar yaradılıb və genişləndirilib; canlı panel eyni mühərriki brauzerdə işlədir (identik olduğu doğrulanıb). Metodologiya istinadları: IMF Maliyyə Proqramlaşdırması və Siyasətləri; Nazirlər Kabinetinin 75 saylı Qərarı." : "Reproduced &amp; extended from CAEM.xlsb in Python; the live dashboard runs the same engine in the browser (validated identical). Methodology references: IMF Financial Programming &amp; Policies; Cabinet of Ministers Decree No. 75."}</div>`;
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
  const az = LANG === "az";
  const head = az ? "6 · Nazirliyin ekonometrik modelləri (Databiz model kitabı)" : "6 · Ministry econometric models (Databiz model book)";
  const note = az
    ? `Bunlar Nazirliyin <b>öz</b> qiymətləndirdiyi tənliklərdir — altı iş kitabından (SNA, BoP, İnflyasiya, Sosial, Sənaye, Ticarət; faktiki əmsalları olan ${eqs.length} tənlik) tək-tənlikli xəta-korreksiya və rejim-dəyişən spesifikasiyaları (EViews). Hər biri tək bir seriyanı — sektorun məhsulunu, idxal/ixrac kateqoriyasını, qiyməti və ya monetar aqreqatı — öz hərəkətverici amillərindən və uzunmüddətli lövbərdən proqnozlaşdırır. Nazirliyin metodları ilə davamlılıq üçün sənədləşdirilib; CAEM canlı proqnozlaşdırma onurğası olaraq qalır, bunları canlı peyk proqnozlaşdırıcıları kimi qoşmaq isə müəyyən edilmiş növbəti mərhələdir.`
    : `These are the Ministry's <b>own</b> estimated equations — single-equation error-correction and regime-switching specifications (EViews) from six workbooks (SNA, BoP, Inflation, Social, Industry, Trade; ${eqs.length} equations with their actual coefficients). Each one forecasts a single series — a sector's output, an import/export category, a price or a monetary aggregate — from its own drivers and a long-run anchor. They are documented here for continuity with the Ministry's methods; CAEM remains the live forecasting spine, and wiring these as live satellite forecasters is the defined next phase.`;
  return `<h3 class="lh">${head}</h3>
    <div class="note-eco">${note}</div>
    ${eqDecoderHTML()}
    ${blocks}`;
}

/* T1.2 — FPP accounting identities. The public-debt-dynamics decomposition is exact and recomputes live;
   the BoP/monetary identities are honestly scoped (the extracted components sit on different bases). */
function accountingHTML() {
  const az = LANG === "az";
  const onScn = RUN && Object.values(RUN.shock || {}).some(v => typeof v === "number" && v);
  const D = onScn ? RUN.scenario : (BASE || {});
  const debt = D.gross_debt || {}, gg = D.real_gdp_growth || {}, pi = D.inflation || {}, pb = D.primary_balance || {};
  const ff = (RUN && RUN.first_forecast) || META.first_forecast, i = 0.03;
  const yrs = Object.keys(debt).map(Number).sort((a, b) => a - b).filter(y => y >= ff);
  const dprev = y => { if (debt[y - 1] != null) return debt[y - 1]; const g = (gg[y] || 0) / 100, p = (pi[y] || 0) / 100; return debt[y] != null ? (debt[y] + (pb[y] || 0)) * (1 + g) * (1 + p) / (1 + i) : null; };
  const sgn = v => (v > 0 ? "+" : "") + v.toFixed(2);
  const rows = yrs.map(y => {
    const dp = dprev(y); if (dp == null || debt[y] == null) return "";
    const g = (gg[y] || 0) / 100, p = (pi[y] || 0) / 100, Dn = (1 + g) * (1 + p);
    const interest = dp * i / Dn, erosion = -dp * (g + p + g * p) / Dn, prim = -(pb[y] || 0), dd = debt[y] - dp;
    return `<tr><td>${y}</td><td>${dp.toFixed(1)}</td><td>${sgn(interest)}</td><td>${sgn(erosion)}</td><td>${sgn(prim)}</td><td class="${dd > 0.05 ? "sc-bad" : dd < -0.05 ? "sc-ok" : ""}"><b>${sgn(dd)}</b></td><td>${debt[y].toFixed(1)}</td></tr>`;
  }).join("");
  const eq = kx("\\Delta d_t = \\underbrace{\\tfrac{i}{(1+g)(1+\\pi)}\\,d_{t-1}}_{\\text{interest}} \\;\\underbrace{-\\,\\tfrac{g+\\pi+g\\pi}{(1+g)(1+\\pi)}\\,d_{t-1}}_{\\text{growth \\& inflation}}\\;\\underbrace{-\\;pb_t}_{\\text{primary balance}}", "Δd = interest − (growth & inflation erosion) − primary balance");
  const heads = az
    ? ["İl", "Borc (əvvəl)", "Faiz (+)", "Artım və inflyasiya (−)", "İlkin balans", "Δ Borc", "Borc (son)"]
    : ["Year", "Debt (start)", "Interest (+)", "Growth & inflation (−)", "Primary balance", "Δ Debt", "Debt (end)"];
  const intro = az
    ? "Maliyyə proqramlaşdırmasının əsas dayanıqlılıq eyniliyi: borc nisbətinin illik dəyişməsi faiz xərcinə, artım və inflyasiyanın aşınmasına və ilkin balansa <b>dəqiq</b> ayrılır (sütunlar Δ Borcu verir) və hər ssenari ilə canlı yenidən hesablanır."
    : "The core financial-programming sustainability identity: the annual change in the debt ratio decomposes <b>exactly</b> into the interest cost, the growth-and-inflation erosion, and the primary balance (the columns sum to Δ Debt) — and recomputes live under any scenario.";
  const bop = az
    ? "<b>Tədiyə balansı və monetar icmal.</b> Cari hesab neft şokuna canlı reaksiya verir (etiketlənmiş elastiklik). Tam tədiyə balansı eyniliyi (cari hesab + maliyyə hesabı = ehtiyatların dəyişməsi) və monetar icmal (geniş pul = xalis xarici aktivlər + xalis daxili aktivlər) müəyyən edilmiş genişləndirmədir: komponent seriyalarının CAEM.xlsb-dən yenidən çıxarılmasını tələb edir, çünki hazırda göstərilən rəqəmlər ayrı uçot bazalarında tərtib olunub."
    : "<b>Balance of payments &amp; monetary survey.</b> The current account responds live to an oil shock (labelled elasticity). The full balance-of-payments identity (current account + financial account = change in reserves) and the monetary survey (broad money = net foreign assets + net domestic assets) are a defined extension: they require the component series to be re-extracted from CAEM.xlsb, as the figures currently displayed are compiled on separate accounting bases.";
  return `<h3 class="lh">${az ? "7 · Uçot eynilikləri (FPP)" : "7 · Accounting identities (FPP)"}</h3>
    <p class="mp">${intro}</p>
    <div class="id-eq" style="margin:8px 0 12px;overflow-x:auto">${eq}</div>
    <div class="mtbl"><table class="dt"><thead><tr>${heads.map(h => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table></div>
    <p class="mp">${az ? "Faiz xərci ≈ effektiv dərəcə (3%) × əvvəlki ilin borcu; ümumi balans = ilkin balans − faiz xərci. Bütün dəyərlər % ÜDM." : "Interest cost ≈ effective rate (3%) × prior-year debt; the overall balance = primary balance − interest cost. All values in % of GDP."}${onScn ? ` <span class="tagi">${az ? "cari ssenari" : "current scenario"}</span>` : ""}</p>
    <div class="note-eco">${bop}</div>`;
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
  const az = LANG === "az";
  const rows = list.map((s, i) => {
    const sh = FIELDS.filter(f => s.shock && s.shock[f]).map(f => `${f.replace(/_/g, " ")} ${s.shock[f] > 0 ? "+" : ""}${s.shock[f]}`).join(", ") || (az ? "bazis" : "baseline");
    const act = Object.keys(s.actuals || {}).length ? ` · ${az ? "məlumat" : "data"}: ${Object.keys(s.actuals).join(", ")}` : "";
    return `<tr><td><input type="checkbox" class="scchk" data-i="${i}"></td><td><b>${esc(s.name)}</b><div class="sc-sub">${esc(s.ts)}</div></td>
      <td>${esc(sh)}${esc(act)}</td><td><button class="lk" data-load="${i}">${tx("scn.load", "Load &amp; run")}</button> <button class="lk del" data-del="${i}">${tx("scn.del", "Delete")}</button></td></tr>`;
  }).join("");
  const emptyMsg = az ? "Hələ saxlanmış ssenari yoxdur — paneldə şoklar təyin edin və 💾 Yadda saxla düyməsini basın." : "No saved scenarios yet — set shocks in the console and press 💾 Save.";
  $("#view").innerHTML = `
    <div class="ghead" style="color:var(--ink);border-color:var(--accent)">${ic("scen")}${deLead(tx("scn.h", "📂 Saved scenarios &amp; forecast rounds"))}</div>
    <div class="gsub">${az ? "Cari panel vəziyyətini (şoklar + daxil edilmiş məlumat) adlandırılmış ssenari və ya proqnoz dövrü kimi saxlayın, sonra yenidən yükləyin, ya da yan-yana müqayisə üçün 2–3-nü işarələyin. Bu brauzerdə saxlanılır (brauzer məlumatı ilə silinir)." : "Save the current console state (shocks + entered data) as a named scenario or forecast round, reload it later, or tick 2–3 to compare side by side. Stored in this browser (clears with browser data)."}</div>
    <div class="mtbl"><table class="dt"><thead><tr><th></th><th>${tx("scn.name", "Name")}</th><th>${tx("scn.shock", "Shock / data")}</th><th></th></tr></thead>
      <tbody>${rows || `<tr><td colspan="4">${emptyMsg}</td></tr>`}</tbody></table></div>
    ${list.length ? `<div class="dm-act"><button id="cmpbtn" class="btn">${tx("scn.cmp", "Compare selected")}</button> <button id="clrscen" class="btn ghost">${tx("scn.delall", "Delete all")}</button></div>` : ""}
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
  const az = LANG === "az";
  if (!sel.length) { $("#cmpout").innerHTML = `<p class="mp">${az ? "Müqayisə üçün ən azı bir saxlanmış ssenari işarələyin." : "Tick at least one saved scenario to compare."}</p>`; return; }
  const base = CAEM.run({});
  const yrs = Object.keys(base.baseline.real_gdp_growth || {}).map(Number);
  const yr = String(Math.max(...(yrs.length ? yrs : [2030])));
  const cols = [{ name: az ? "Bazis" : "Baseline", r: base }].concat(sel.map(s => ({ name: s.name, r: CAEM.run(Object.assign({}, s.shock, { actuals: s.actuals, start: s.start, end: s.end })) })));
  const head = `<tr><th>${tx("sc.indicator", "Indicator")} (${yr})</th>` + cols.map(c => `<th>${esc(c.name)}</th>`).join("") + `</tr>`;
  const body = IMPACT_VARS.map(([lab, v, u]) =>
    `<tr><td>${esc(tInd(lab))}</td>` + cols.map(c => { const d = (c.r.scenario && c.r.scenario[v]) || {}; const val = d[yr]; return `<td>${val == null ? "—" : val.toFixed(1) + " " + u}</td>`; }).join("") + `</tr>`).join("");
  $("#cmpout").innerHTML = `<h3 class="lh">${tx("cmp.at", "Comparison")} — ${yr}</h3><div class="mtbl"><table class="dt"><thead>${head}</thead><tbody>${body}</tbody></table></div>`;
}

/* ---------------- quarterly indicators + nowcast bridge (real SSC higher-frequency data) ---------------- */
let QDATA = null;
// [key, EN label, AZ label, colour]
const QSERIES = [
  ["gdp_yoy", "Real GDP growth", "Real ÜDM artımı", "#2f6f8f"],
  ["nonoil_yoy", "Non-oil GDP growth", "Qeyri-neft ÜDM artımı", "#5b8c5a"],
  ["cpi_yoy", "CPI inflation", "İQİ inflyasiyası", "#c98a3c"],
  ["m2_yoy", "Broad money (M2)", "Geniş pul (M2)", "#7585bd"],
  ["brent", "Brent crude", "Brent xam neft", "#9b5d8a"],
  ["policy_rate", "Policy rate", "Uçot dərəcəsi", "#b5683f"],
];
const QUNIT_AZ = { "% y-o-y": "% illik", "USD/barrel": "USD/barel", "%": "%" };
// quarterly indicator key → engine annual-forecast variable (the engine forecasts these four)
const QVAR = { gdp_yoy: "real_gdp_growth", nonoil_yoy: "nonoil_growth", cpi_yoy: "inflation", policy_rate: "policy_rate" };
function drawQuarterly(div, periods, actual, fc, color, boundary) {
  const tickvals = periods.filter(p => p.endsWith("Q1") && (+p.slice(0, 4)) % 2 === 0), ticktext = tickvals.map(p => p.slice(0, 4));
  const traces = [{
    x: periods, y: actual, type: "scatter", mode: "lines+markers", connectgaps: false,
    line: { color, width: 2 }, marker: { size: 3, color }, hovertemplate: "%{x}: %{y:.2f}<extra></extra>"
  }];
  if (fc && fc.some(v => v != null)) traces.push({
    x: periods, y: fc, type: "scatter", mode: "lines", connectgaps: true,
    line: { color: "#b23b30", width: 2, dash: "dash" }, hovertemplate: "%{x}: %{y:.2f} ★<extra></extra>"
  });
  const shapes = [];
  if (boundary != null) {
    shapes.push({ type: "rect", xref: "x", yref: "paper", x0: boundary - 0.5, x1: periods.length - 0.5, y0: 0, y1: 1, fillcolor: "rgba(120,130,145,0.08)", line: { width: 0 }, layer: "below" });
    shapes.push({ type: "line", xref: "x", yref: "paper", x0: boundary - 0.5, x1: boundary - 0.5, y0: 0, y1: 1, line: { color: "#c2c8d0", width: 1, dash: "dot" } });
  }
  Plotly.react(div, traces, {
    height: 196, margin: { l: 42, r: 10, t: 8, b: 26 }, font: { family: "Hanken Grotesk,sans-serif", size: 10, color: "#4e4a43" },
    plot_bgcolor: "#fff", paper_bgcolor: "#fff", showlegend: false, hovermode: "x unified", shapes,
    hoverlabel: { font: { size: 10.5, family: "Hanken Grotesk,sans-serif" }, bgcolor: "#fff", bordercolor: "rgba(26,26,23,0.16)" },
    xaxis: { type: "category", tickvals, ticktext, tickangle: 0, showgrid: false, ticklen: 3 },
    yaxis: { gridcolor: "rgba(26,26,23,0.06)", zeroline: true, zerolinecolor: "rgba(26,26,23,0.16)", automargin: true }
  }, { responsive: true, displayModeBar: false });
}
/* ---------------- reproducible notebooks (Colab) ---------------- */
// After uploading the project folder to Google Drive and opening each notebook in Colab, paste its
// Colab share link here (slug -> url). Until then, cards show a "link pending" chip.
const NB_LINKS = {
  "00_index": "https://colab.research.google.com/drive/1439-ucgBbWzb0ERlLNEY04I-lMizcNaC",
  "01_data_foundation": "https://colab.research.google.com/drive/1DFftEyOo7vKSXahPjxVGeIlVjxhDkdlA",
  "02_output_growth": "https://colab.research.google.com/drive/1I_p8uK14UY4WR31kAFKqPghWoQEebq0X",
  "03_inflation_monetary": "https://colab.research.google.com/drive/1IrPAHqKPfZ1FEjSSh1gXordQFXO08hIa",
  "04_regression_library": "https://colab.research.google.com/drive/1jSpQaXIwyCNkOj4sC2hl3tSN5Y_PSE6o",
  "05_structural_var": "https://colab.research.google.com/drive/1nXtBBYKhU1GWrTslwLFj-bwwf39DoEUW",
  "06_cointegration_vecm": "https://colab.research.google.com/drive/1bPAic4HgnT_vvm75lZBjjCBYzhoPiEgV",
  "07_fiscal_budget_debt": "https://colab.research.google.com/drive/1RlqEuzLJZs-Bp45_Psj-bt4qDGZ4mgBS",
  "08_external_bop": "https://colab.research.google.com/drive/1tpkYX9gCIdigpqk3_-CtABPAM995hF0m",
  "09_labour_demography": "https://colab.research.google.com/drive/1evETxBciF0hYicS0B9hxglcBFONIXMxB",
  "10_machine_learning": "https://colab.research.google.com/drive/1USgPoYzfL6Kbf26h1_Dbhflb-B9YzMdA",
  "11_deep_learning": "https://colab.research.google.com/drive/1qIE38uEz72M3zrt-MSudoJRRJqzarlft",
  "12_bayesian_statespace": "https://colab.research.google.com/drive/1DLz10Uy8WDCme8ZxHXCJJyyO34u3VIEP",
  "13_structural_models": "https://colab.research.google.com/drive/1Fr_LzLCqhZPIKW6WpcSkmN5iBrzugPrl",
  "14_scenarios_risk": "https://colab.research.google.com/drive/1pZiUq4vMDbwgPlOR0DSz88l06HS03G7K",
  "15_caem_summary": "https://colab.research.google.com/drive/1W4DUNRYUOr2oH1HRva9dN6K_Fy72Tqz2",
};
const NOTEBOOKS = [
  ["00", "00_index", "Index & reproducibility", "İndeks və təkrar istehsal", "Table of contents, environment, the data-provenance catalogue.", "Mündəricat, mühit, məlumat mənbələri kataloqu.", "provenance"],
  ["01", "01_data_foundation", "Data foundation & the Decree-75 mandate", "Məlumat bazası və 75 saylı mandat", "Statutory indicators, the 3-frequency data architecture, the 2025 outturn.", "Statutar göstəricilər, məlumat arxitekturası, 2025 nəticəsi.", "EDA · sources"],
  ["02", "02_output_growth", "Output, growth & potential", "Məhsul, artım və potensial", "Production-side GDP identity, sector ECMs, HP-filter output gap.", "İstehsal tərəfi ÜDM eyniliyi, sektor ECM, HP kəsiri.", "HP filter · ECM"],
  ["03", "03_inflation_monetary", "Inflation & monetary policy", "İnflyasiya və monetar siyasət", "Open-economy Phillips curve, pass-through, smoothed Taylor rule.", "Açıq iqtisadiyyat Phillips əyrisi, ötürülmə, Taylor qaydası.", "Phillips · Taylor"],
  ["04", "04_regression_library", "Econometric regression library", "Ekonometrik reqressiya kitabxanası", "Nested OLS/ARDL/ECM, HAC inference, the 92 Ministry equations.", "OLS/ARDL/ECM, HAC, 92 Nazirlik tənliyi.", "OLS · ARDL · HAC"],
  ["05", "05_structural_var", "Structural VAR & impulse responses", "Struktur VAR və impuls reaksiyaları", "SVAR (oil·FX·inflation), Cholesky IRFs, variance decomposition.", "SVAR, Cholesky IRF, dispersiya dekompozisiyası.", "SVAR · IRF · FEVD"],
  ["06", "06_cointegration_vecm", "Cointegration & VECM", "Kointeqrasiya və VECM", "Johansen test and revenue–expenditure error-correction.", "Johansen testi və gəlir–xərc xəta korreksiyası.", "Johansen · VECM"],
  ["07", "07_fiscal_budget_debt", "Fiscal, budget & debt dynamics", "Fiskal, büdcə və borc dinamikası", "Debt-dynamics decomposition, revenue/expenditure, customs.", "Borc dinamikası, gəlir/xərc, gömrük.", "debt · ARDL"],
  ["08", "08_external_bop", "External sector & balance of payments", "Xarici sektor və tədiyə balansı", "Trade/gravity elasticities, UIP+PPP, the BoP identity.", "Ticarət elastiklikləri, UIP+PPP, TB eyniliyi.", "elasticities · BoP"],
  ["09", "09_labour_demography", "Labour, demography & consumption", "Əmək, demoqrafiya və istehlak", "Okun's law, wage Phillips curve, consumption, population.", "Okun qanunu, əmək haqqı, istehlak, əhali.", "Okun · wages"],
  ["10", "10_machine_learning", "Machine-learning forecasting", "Maşın öyrənməsi proqnozu", "Walk-forward horse-race: Ridge/Lasso/RF/GB/MLP vs random walk.", "Walk-forward: Ridge/Lasso/RF/GB/MLP.", "ML · backtest"],
  ["11", "11_deep_learning", "Deep learning (monthly)", "Dərin öyrənmə (aylıq)", "Neural net + LSTM / Prophet / TFT for monthly inflation.", "Neyron şəbəkə + LSTM / Prophet / TFT.", "LSTM · Prophet · TFT"],
  ["12", "12_bayesian_statespace", "Bayesian & state-space", "Bayes və vəziyyət-fəza", "SARIMA, Kalman potential output, dynamic factor, Bayesian VAR.", "SARIMA, Kalman, dinamik amil, Bayes VAR.", "SARIMA · Kalman · DFM"],
  ["13", "13_structural_models", "Structural macro models", "Struktur makro modellər", "3-equation New-Keynesian DSGE and input–output multipliers.", "Yeni-Keynsçi DSGE və xərc-buraxılış multiplikatorları.", "DSGE · IO"],
  ["14", "14_scenarios_risk", "Scenarios, fan charts & risk", "Ssenarilər, yelpik qrafikləri və risk", "Oil scenarios, Bank-of-England fan charts, a risk heat-map.", "Neft ssenariləri, yelpik qrafikləri, risk istilik xəritəsi.", "scenarios · fans"],
  ["15", "15_caem_summary", "Integrated CAEM & forecast summary", "İnteqrasiya olunmuş CAEM və xülasə", "The full semi-structural model, 2026–2030 forecast, scorecard, nowcast.", "Tam yarı-struktur model, 2026–2030 proqnoz, hesab kartı.", "CAEM · summary"],
  ["16", "16_forecast_benchmark", "Forecast benchmark", "Proqnoz müqayisəsi", "A skill-weighted multi-model ensemble against IMF Article IV and the CAEM dashboard, with backtest skill scores.", "İMF Article IV və CAEM dashboard ilə müqayisədə bacarıq-çəkili çoxmodelli ansambl, geriyə-test bacarıq balları ilə.", "ensemble · benchmark"],
];
function showNotebooks() {
  CUR = null; setActive("notebooks");
  const az = LANG === "az";
  const intro = az
    ? "On yeddi akademik keyfiyyətli, təkrar istehsal oluna bilən Jupyter dəftəri — hər biri bir təhlil bölməsini real məlumatdan başlayaraq qiymətləndirilmiş modelə, qrafiklərə və proqnoza qədər izah edir (LaTeX riyaziyyatı ilə). İki veb məhsulunun analitik onurğası."
    : "Seventeen academic-quality, reproducible Jupyter notebooks — each works one analytical section end-to-end, from the real data through the estimated model to the figures and the forecast, with the mathematics derived in LaTeX. The analytical backbone of the two web products.";
  const howto = az
    ? "<b>Təkrar istehsal.</b> Bu paneldəki və texniki hesabatdakı hər qrafik, cədvəl və əmsal bu dəftərlər tərəfindən mənbə məlumatından bir keçidlə yenidən yaradılır. Hər dəftər özü-özünə kifayət edir və kartındakı linkdən Google Colab-da açılır."
    : "<b>Reproducibility.</b> Every figure, table and coefficient in this dashboard and in the technical report is regenerated by these notebooks from the source data in a single pass. Each notebook is self-contained and opens in Google Colab from the link on its card.";
  const cards = NOTEBOOKS.map(([n, slug, en, aze, be, ba, m]) => {
    return `<div class="nbcard"><div class="nb-n">${n}</div><div class="nb-b">
      <div class="nb-t">${esc(az ? aze : en)}</div><div class="nb-d">${esc(az ? ba : be)}</div>
      <div class="nb-m">${m.split(" · ").map(x => `<span>${esc(x)}</span>`).join("")}</div></div></div>`;
  }).join("");
  $("#view").innerHTML = `<div class="ghead" style="color:var(--ink);border-color:var(--accent)">${ic("nb")}${deLead(tx("nb.h", "📓 Reproducible notebooks"))}</div>
    <div class="gsub">${intro}</div>
    <div class="note-eco">${howto}</div>
    <div class="nbgrid">${cards}</div>`;
  window.scrollTo({ top: 0 });
}
/* ---------------- Forecast benchmark: our ensemble vs IMF / CAEM / prior baseline ---------------- */
let BENCH = null, REFS = null;
const REFMETA = [["IMF_ArticleIV_26_112", "IMF", "#c0392b", null],
                 ["CAEM_xlsb", "CAEM.xlsb", "#b9852a", "dash"]];
function benchTraces(v) {
  const ours = BENCH[v].ensemble, bands = BENCH[v].bands, fy = [2026, 2027, 2028, 2029, 2030, 2031], ex = [2025].concat(fy), tr = [];
  const bcol = s => fy.map(y => bands[String(y)] ? bands[String(y)][s] : null);
  const lo90 = bcol("p90").map(b => b ? b[0] : null), hi90 = bcol("p90").map(b => b ? b[1] : null);
  const lo50 = bcol("p50").map(b => b ? b[0] : null), hi50 = bcol("p50").map(b => b ? b[1] : null);
  tr.push({ x: fy, y: lo90, mode: "lines", line: { width: 0 }, hoverinfo: "skip", showlegend: false });
  tr.push({ x: fy, y: hi90, mode: "lines", line: { width: 0 }, fill: "tonexty", fillcolor: "rgba(14,124,139,0.10)", hoverinfo: "skip", showlegend: false });
  tr.push({ x: fy, y: lo50, mode: "lines", line: { width: 0 }, hoverinfo: "skip", showlegend: false });
  tr.push({ x: fy, y: hi50, mode: "lines", line: { width: 0 }, fill: "tonexty", fillcolor: "rgba(14,124,139,0.20)", hoverinfo: "skip", showlegend: false });
  REFMETA.forEach(([k, lab, c, dash]) => {
    const d = REFS[k] && REFS[k][v]; if (!d) return;
    const xs = ex.filter(y => d[String(y)] != null);
    tr.push({ x: xs, y: xs.map(y => d[String(y)]), mode: "lines+markers", name: lab, line: { color: c, width: 1.7, dash: dash || undefined }, marker: { size: 5, symbol: "square" }, hovertemplate: "%{x}: %{y:.1f}%<extra>" + lab + "</extra>" });
  });
  tr.push({ x: ex, y: ex.map(y => ours[String(y)]), mode: "lines+markers", name: "Oxlon ensemble", line: { color: "#0f6b62", width: 3 }, marker: { size: 6 }, hovertemplate: "%{x}: %{y:.1f}%<extra>Oxlon ensemble</extra>" });
  return tr;
}
async function showBenchmark() {
  CUR = null; setActive("benchmark");
  try {
    if (!BENCH) BENCH = await (await fetch("data/canonical_forecast.json")).json();
    if (!REFS) REFS = await (await fetch("data/reference_forecasts.json")).json();
  } catch (e) { $("#view").innerHTML = `<div class="ghead">${ic("bench")}${deLead(tx("bench.h", "📊 Forecast benchmark"))}</div><p class="gsub">data/canonical_forecast.json not found</p>`; return; }
  const az = LANG === "az";
  const intro = az
    ? "Oxlon ansamblı müstəqil və bacarıqla-çəkilmişdir: doqquz model üzrə qurulub, hər biri geriyə-test edilib və 2025 faktiki nəticəsinə əsaslanır. IMF Article IV (26/112) və Nazirliyin CAEM.xlsb modeli ilə yanaşı göstərilir. Ansambl IMF və CAEM mənzərəsini yaxından təkrar istehsal edir (2026-2029 üzrə artımda ≈0.1 f.b., inflyasiyada ≈0.6 f.b. orta fərq), bu da metodu doğrulayır."
    : "The Oxlon ensemble is independent and skill-weighted across nine models, each back-tested and anchored on the 2025 outturn, shown beside the IMF Article IV (26/112) and the Ministry's CAEM.xlsb. It reproduces the IMF and CAEM picture closely, with mean gaps of about 0.1 point on growth and 0.6 on inflation over 2026 to 2029, which validates the method.";
  const tbl = (v, lab) => {
    const ours = BENCH[v].ensemble, yrs = [2025, 2026, 2027, 2028, 2029, 2030, 2031];
    const cols = [["Oxlon", null], ["IMF", "IMF_ArticleIV_26_112"], ["CAEM", "CAEM_xlsb"]];
    const cell = x => (x == null) ? "·" : (+x).toFixed(1);
    let h = `<table style="border-collapse:collapse;font-size:11px;margin:0 14px 6px 0"><caption style="text-align:left;font-weight:600;color:var(--ink);padding:3px 0">${esc(lab)} (%)</caption><tr style="color:var(--muted)"><td style="padding:2px 9px">Year</td>${cols.map(c => `<td style="padding:2px 9px;text-align:right">${esc(c[0])}</td>`).join("")}</tr>`;
    yrs.forEach(y => {
      h += `<tr><td style="padding:2px 9px;color:var(--muted)">${y}</td>` + cols.map(([l2, k]) => {
        let val; if (k === null) val = ours[String(y)]; else { const d = REFS[k] && REFS[k][v]; val = d ? d[String(y)] : null; }
        return `<td style="padding:2px 9px;text-align:right;${k === null ? "font-weight:700;color:var(--accent)" : ""}">${cell(val)}</td>`;
      }).join("") + "</tr>";
    });
    return h + "</table>";
  };
  $("#view").innerHTML = `<div class="ghead" style="color:var(--ink);border-color:var(--accent)">${ic("bench")}${deLead(tx("bench.h", "📊 Forecast benchmark against IMF and CAEM"))}</div>
    <div class="gsub">${intro}</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:6px">
      <div class="figcard"><div class="ft">${az ? "Real ÜDM artımı" : "Real GDP growth"} <span class="fcbadge">+ 50/90% fan</span></div><div class="fc" id="benchgdp" style="height:300px"></div></div>
      <div class="figcard"><div class="ft">${az ? "İnflyasiya (İQİ)" : "CPI inflation"} <span class="fcbadge">+ 50/90% fan</span></div><div class="fc" id="benchcpi" style="height:300px"></div></div>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:14px">${tbl("gdp_realg", az ? "Real ÜDM artımı" : "Real GDP growth")}${tbl("cpi_infl", az ? "İnflyasiya" : "CPI inflation")}</div>
    <div class="note-eco" style="margin-top:12px"><b>${az ? "Nəticə" : "Result"}:</b> ${esc(BENCH.method_note || "")}</div>`;
  const lay = () => { const L = baseLayout(true, [], 286, 40, 1); L.showlegend = true; L.legend = { orientation: "h", y: -0.22, font: { size: 9 } }; L.margin = { l: 40, r: 10, t: 6, b: 40 }; return L; };
  Plotly.newPlot($("#benchgdp"), benchTraces("gdp_realg"), lay(), { responsive: true, displaylogo: false, displayModeBar: false });
  Plotly.newPlot($("#benchcpi"), benchTraces("cpi_infl"), lay(), { responsive: true, displaylogo: false, displayModeBar: false });
  window.scrollTo({ top: 0 });
}
async function showQuarterly() {
  CUR = null; setActive("quarterly");
  const az = LANG === "az";
  const intro = az
    ? "Yüksək tezlikli real göstəricilər — DSK rüblük milli hesablar və aylıq DSK/AMB göstəriciləri (rüblərə ortalanmış) — sonra modelin <b>illik proqnozu</b> (2026–2030, qırmızı punktir, kölgələnmiş) faktiki rüblük axına calanır. Bu, il-içi dinamikanı və cari ilin proqnozunu (nowcast) bir yerdə göstərir."
    : "Real higher-frequency indicators — SSC quarterly national accounts and monthly SSC/CBAR indicators (averaged to quarters) — joined to the model's <b>annual forecast</b> (2026–2030, dashed red, shaded). This shows within-year dynamics and the current-year projection (nowcast) together.";
  $("#view").innerHTML = `<div class="ghead" style="color:var(--ink);border-color:var(--accent)">${ic("qtr")}${deLead(tx("qtr.h", "📅 Quarterly indicators &amp; forecast"))}</div>
    <div class="gsub">${intro} <span id="qstatus"></span></div>
    <div id="qnow"></div>
    <div class="figgrid" id="qgrid"></div>`;
  const grid = $("#qgrid");
  try {
    if (!QDATA) QDATA = await (await fetch("data/quarterly.json")).json();
  } catch (e) { $("#qstatus").textContent = "— data/quarterly.json not found"; return; }
  const Q = QDATA, P = Q.periods, U = (Q.meta && Q.meta.units) || {};
  const FCP = []; for (let y = 2026; y <= 2030; y++) for (let q = 1; q <= 4; q++) FCP.push(y + "Q" + q);
  const allP = P.concat(FCP), boundary = P.length;
  // nowcast box: the model's current-year (2026) projection + the 2025 quarterly→annual method check
  const g26 = (BASE.real_gdp_growth || {})["2026"], i26 = (BASE.inflation || {})["2026"], p26 = (BASE.policy_rate || {})["2026"], nc = Q.nowcast;
  const ncRow = (lab, val, u) => `<div class="nc-row"><div class="nc-lab">${esc(lab)}</div><div class="nc-val"><span>${az ? "model proqnozu" : "model projection"}: <b>${val == null ? "—" : val.toFixed(1) + (u || "%")}</b></span></div></div>`;
  const check = nc
    ? (az ? `<b>Metod yoxlanışı.</b> 2025 rüblük göstəriciləri orta hesabla ${nc.gdp_implied.toFixed(1)}% təşkil edir və rəsmi illik nəticəni (${nc.gdp_official.toFixed(1)}%) təkrar istehsal edir — bu, rüblükdən-illiyə körpünü doğrulayır. 2026 rüblük məlumatı dərc olunduqca bu proqnoz dəqiqləşəcək.`
      : `<b>Method check.</b> The 2025 quarterly readings average ${nc.gdp_implied.toFixed(1)}%, reproducing the official annual outturn (${nc.gdp_official.toFixed(1)}%) — validating the quarterly-to-annual bridge. As 2026 quarterly data is published this projection will be refined.`)
    : "";
  $("#qnow").innerHTML = `<div class="nowcast"><div class="nc-h">${az ? "Cari ilin proqnozu — 2026" : "Current-year nowcast — 2026"} <span class="tagi">${az ? "model · illik" : "model · annual"}</span></div>
    ${ncRow(az ? "Real ÜDM artımı" : "Real GDP growth", g26)}
    ${ncRow(az ? "İnflyasiya (İQİ)" : "Inflation (CPI)", i26)}
    ${ncRow(az ? "Uçot dərəcəsi" : "Policy rate", p26)}
    <div class="nc-note">${check}</div></div>`;
  QSERIES.forEach((s, i) => {
    const [key, en, azl, color] = s, vals = (Q.series && Q.series[key]) || [];
    if (!vals.some(v => v != null)) return;
    const label = az ? azl : en, unit = (az ? (QUNIT_AZ[U[key]] || U[key]) : U[key]) || "";
    const ev = QVAR[key], fa = ev && BASE[ev] ? BASE[ev] : null;   // engine annual forecast for this indicator
    let actualY = vals, fcY = null, px = P;
    if (fa) {
      px = allP; actualY = vals.concat(FCP.map(() => null)); fcY = P.map(() => null);
      let li = -1; for (let k = vals.length - 1; k >= 0; k--) if (vals[k] != null) { li = k; break; }
      if (li >= 0) fcY[li] = vals[li];                             // connect the dashed forecast to the last actual
      FCP.forEach(p => { const v = fa[p.slice(0, 4)]; fcY.push(v != null ? v : null); });
    }
    const card = document.createElement("div"); card.className = "figcard"; card.style.borderTopColor = color;
    card.innerHTML = `<div class="ft">${esc(label)}${fa ? ` <span class="fcbadge">${az ? "+ proqnoz" : "+ forecast"}</span>` : ""}</div><div class="fu">${esc(unit)}</div><div class="fc" id="q${i}"></div>`;
    grid.appendChild(card);
    drawQuarterly(`q${i}`, px, actualY, fcY, color, fa ? boundary : null);
    const series = [{ name: label, x: P, y: vals }];
    if (fa) series.push({ name: (az ? "Model proqnozu (illik)" : "Model forecast (annual)"), x: ["2026", "2027", "2028", "2029", "2030"], y: ["2026", "2027", "2028", "2029", "2030"].map(y => fa[y] != null ? fa[y] : null) });
    attachInfo(card, { title: label, unit, sheet: "Quarterly (SSC)", series, quarterly: true });
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
  height: h, margin: { l: 46, r: 12, t: 8, b: b }, font: { family: "Hanken Grotesk,sans-serif", size: 10, color: "#4e4a43" },
  plot_bgcolor: "#fff", paper_bgcolor: "#fff", barmode: "relative", bargap: 0.16, showlegend: false, shapes,
  hovermode: "x unified", hoverlabel: { font: { size: 10.5, family: "Hanken Grotesk,sans-serif" }, bgcolor: "#fff", bordercolor: "rgba(26,26,23,0.16)" },
  xaxis: xyear ? { tickformat: "d", showgrid: false, dtick: dtick || 2, tick0: 2026, ticklen: 3 } : { showgrid: false, ticklen: 3 },
  yaxis: { gridcolor: "rgba(26,26,23,0.06)", zeroline: true, zerolinecolor: "rgba(26,26,23,0.16)", automargin: true }
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
    height: 380, margin: { l: 64, r: 64, t: 22, b: 30 }, font: { family: "Hanken Grotesk,sans-serif", size: 10.5, color: "#4e4a43" },
    paper_bgcolor: "#fff", showlegend: false,
    polar: { bgcolor: "#fff", radialaxis: { angle: 90, tickfont: { size: 9 }, gridcolor: "rgba(26,26,23,0.06)" }, angularaxis: { tickfont: { size: 11 }, rotation: 90, direction: "clockwise" } }
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
function drawFan(div, fan, big, scn) {
  fan = boundaryAnchor(fan, LIVE_FF || META.first_forecast);
  const x = fan.years, traces = [];
  FAN_BANDS.forEach(([lo, hi, col]) => {
    traces.push({ x, y: fan[hi], mode: "lines", line: { width: 0, color: "rgba(0,0,0,0)" }, hoverinfo: "skip", showlegend: false });
    traces.push({ x, y: fan[lo], mode: "lines", line: { width: 0, color: "rgba(0,0,0,0)" }, fill: "tonexty", fillcolor: col, hoverinfo: "skip", showlegend: false });
  });
  traces.push({ x, y: fan.central, mode: "lines+markers", line: { color: FAN_CENTRAL, width: 2.6 }, marker: { size: 3.6, color: FAN_CENTRAL }, hovertemplate: "<b>central</b>: %{y:.2f}<extra></extra>", showlegend: false });
  const layout = baseLayout(true, fcShapes(x, LIVE_FF || META.first_forecast), big ? 320 : 214, 24, tickStep(x));
  const an = scnAnno(); if (scn && an) layout.annotations = [an];
  Plotly.react(div, traces, layout, { responsive: true, displayModeBar: false });
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
    return `<tr><td>${esc(tInd(n))}</td><td>${f.toFixed(1)}</td><td><b>${ac.toFixed(1)}</b></td><td class="sc-${cls}">${e > 0 ? "+" : ""}${e.toFixed(1)} pp</td></tr>`;
  }).join("");
  const mae = errs.reduce((x, y) => x + y, 0) / (errs.length || 1);
  const note = LANG === "az"
    ? `CAEM (2024 buraxılışı) <b>artımı yüksək proqnozlaşdırdı</b> (ÜDM 3.0% / 1.4%; qeyri-neft 4.6% / 2.7%) və <b>kəsirin profisitə çevrildiyini</b> (−1.1% / +0.4% ÜDM); <b>inflyasiya yaxın idi</b> (5.1% / 5.6%). Canlı model bu 2025 faktiki göstəricilərinə yenidən bağlanıb və 2026+ proqnozlaşdırır.<br><span class="tagi">Dəqiqlik tarixçəsi: bir buraxılış mövcuddur (2024 buraxılışı proqnozu 2025 nəticəsinə qarşı). Hər gələcək proqnoz dövrü, 💾 və apply_actuals ardıcıllığı ilə saxlanılaraq, bu cədvəli davamlı dəqiqlik qeydinə çevirir.</span>`
    : `CAEM (2024 vintage) <b>over-predicted growth</b> (GDP 3.0% vs 1.4%; non-oil 4.6% vs 2.7%) and a <b>deficit that turned into a surplus</b> (−1.1% vs +0.4% of GDP); <b>inflation was close</b> (5.1% vs 5.6%). The live model is re-anchored to these 2025 actuals and forecasts 2026+.<br><span class="tagi">Track record: one vintage available (the 2024-vintage call vs the 2025 outturn). Each future forecast round, saved via 💾 and the apply_actuals pipeline, extends this table into a rolling accuracy record.</span>`;
  return `<div class="scorecard"><div class="sc-h">${tx("sc.h", "2025 scorecard, CAEM forecast versus official outturn")} <span class="tagi">${tx("sc.tag", "State Statistical Committee, released Jan 2026")}</span></div>
    <table class="sc-t"><thead><tr><th>${tx("sc.indicator", "Indicator")}</th><th>${tx("sc.forecast", "CAEM forecast")}</th><th>${tx("sc.actual", "2025 actual")}</th><th>${tx("sc.error", "Error")}</th></tr></thead><tbody>${tr}
      <tr class="sc-mae"><td><b>${tx("sc.mae", "Mean absolute error")}</b></td><td></td><td></td><td><b>${mae.toFixed(1)} pp</b></td></tr></tbody></table>
    <div class="sc-note">${note}</div></div>`;
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
    return `<div class="imp"><div class="imp-k">${esc(tInd(lab))}</div>
      <div class="imp-v">${b.toFixed(1)} <span class="imp-ar">${arr}</span> <b>${s.toFixed(1)}</b><span class="imp-u">${u}</span></div>
      <div class="imp-d">${d > 0 ? "+" : ""}${d.toFixed(1)} pp</div></div>`;
  }).join("");
  return `<div class="impact"><div class="imp-h">${tx("imp.h", "Scenario impact in")} ${yr} <span class="tagi">${tx("imp.shock", "shock")}: ${esc(shock)}</span></div><div class="imp-grid">${cards}</div></div>`;
}

/* ---------------- per-figure info + PNG export ---------------- */
function attachInfo(card, f) {
  card.insertAdjacentHTML("beforeend",
    `<div class="figbtns"><button class="figbtn figbig" title="${tx("fig.enlarge", "Enlarge")}">⛶</button><button class="figbtn figpng" title="${tx("fig.png", "Download high-resolution PNG")}">⤓ PNG</button><button class="figbtn finfo" title="${tx("fig.info", "About this figure")}">ⓘ ${tx("fig.infolbl", "info")}</button></div>`);
  card.querySelector(".finfo").onclick = e => { e.stopPropagation(); openInfo(figInfo(f)); };
  card.querySelector(".figpng").onclick = e => { e.stopPropagation(); exportPNG(card, f); };
  card.querySelector(".figbig").onclick = e => { e.stopPropagation(); enlargeFig(card, f); };
}
// export a clean, titled PNG (figure name as title, unit on the y-axis; no FAN/LIVE badges)
function exportPNG(card, f) {
  const gd = card.querySelector(".fc"); if (!gd || !window.Plotly) return;
  const title = clean(f.title || "figure"), unit = f.unit ? clean(f.unit) : "";
  const m = gd.layout.margin || {}, prevT = m.t || 8;
  const prevY = (gd.layout.yaxis && gd.layout.yaxis.title && gd.layout.yaxis.title.text) || "";
  Plotly.relayout(gd, {
    "title.text": title, "title.font.size": 15, "title.font.family": "Hanken Grotesk,sans-serif", "title.font.color": "#1a1a17",
    "title.x": 0.01, "title.xanchor": "left", "title.y": 0.97, "title.yanchor": "top", "margin.t": 42,
    "yaxis.title.text": unit, "yaxis.title.font.size": 11, "yaxis.title.font.color": "#6b7280"
  }).then(() => Plotly.downloadImage(gd, { format: "png", scale: 3, width: 920, height: 540, filename: "caem_" + title.replace(/[^\w]+/g, "_").slice(0, 44) }))
    .then(() => Plotly.relayout(gd, { "title.text": "", "margin.t": prevT, "yaxis.title.text": prevY }));
}
// open a large overlay of the figure by cloning the rendered traces+layout (works for any chart type)
function enlargeFig(card, f) {
  const gd = card.querySelector(".fc"); if (!gd || !window.Plotly || !gd.data) return;
  const title = clean(f.title || "figure"), unit = f.unit ? clean(f.unit) : "";
  $("#figmodaltitle").innerHTML = `<b>${esc(title)}</b>${unit ? `<span class="fm-unit">${esc(unit)}</span>` : ""}`;
  const data = JSON.parse(JSON.stringify(gd.data)), layout = JSON.parse(JSON.stringify(gd.layout));
  layout.height = Math.max(360, Math.min(window.innerHeight - 220, 660));
  layout.margin = Object.assign(layout.margin || {}, { t: 16, r: 26, l: 58, b: 42 });
  layout.font = Object.assign(layout.font || {}, { size: 13 });
  layout.autosize = true; delete layout.width;
  ["xaxis", "yaxis"].forEach(ax => { if (layout[ax]) layout[ax].tickfont = { size: 12 }; });
  Plotly.newPlot($("#figmodalplot"), data, layout, { responsive: true, displayModeBar: true, displaylogo: false });
  const lg = card.querySelector(".flgd");
  $("#figmodallegend").innerHTML = lg ? lg.outerHTML : "";
  $("#figmodal").classList.add("open"); $("#figscrim").classList.add("show");
}
function closeFigModal() { $("#figmodal").classList.remove("open"); $("#figscrim").classList.remove("show"); const p = $("#figmodalplot"); if (p && window.Plotly) Plotly.purge(p); }
// LaTeX → a clean, display-mode equation block in the /az/models.html style
// (teal-spined .eq card, optional right-aligned equation number).
function kx(latex, plain, num) {
  const tag = num ? `<span class="num">${esc(num)}</span>` : "";
  if (window.katex) { try { return `<div class="eq">${katex.renderToString(latex, { throwOnError: false, displayMode: true })}${tag}</div>`; } catch (e) { } }
  return `<div class="eq mono">${esc(plain || latex)}${tag}</div>`;
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
// plain-language definitions of the technical terms that appear in figure/series names (academic but clear, non-fabricated)
const GLOSSARY = [
  { re: /partner growth|trading.?partner/i, term: "Partner growth", en: "Weighted GDP growth of Azerbaijan's main trading partners — a proxy for external demand for non-oil exports.", az: "Azərbaycanın əsas ticarət tərəfdaşlarının çəkili ÜDM artımı — qeyri-neft ixracına xarici tələbin göstəricisi." },
  { re: /relative .*price|relative (export|import)/i, term: "Relative price", en: "An export/import price expressed relative to domestic prices — a competitiveness and pass-through measure.", az: "İxrac/idxal qiymətinin daxili qiymətlərə nisbəti — rəqabətqabiliyyətlilik və ötürülmə göstəricisi." },
  { re: /output gap/i, term: "Output gap", en: "Actual output minus potential (HP-filter trend), as % of potential — the economy's cyclical position.", az: "Faktiki məhsul minus potensial (HP-filtr trendi), potensialın %-i — iqtisadiyyatın tsiklik mövqeyi." },
  { re: /potential/i, term: "Potential output", en: "The trend level of output — the economy's non-inflationary capacity. CAEM estimates it two ways: a statistical HP filter and a production-function (growth-accounting) decomposition.", az: "Məhsulun trend səviyyəsi — iqtisadiyyatın inflyasiyasız tutumu. CAEM onu iki üsulla qiymətləndirir: statistik HP filtri və istehsal funksiyası (artım uçotu) dekompozisiyası." },
  { re: /growth accounting|growth decomp|production function/i, term: "Growth accounting", en: "A production-function decomposition of GDP growth into the contributions of capital, labour and total factor productivity; \"Potential growth (Growth decomp)\" is potential built up from the trends of these inputs.", az: "ÜDM artımının kapital, əmək və məcmu amil məhsuldarlığının töhfələrinə istehsal funksiyası dekompozisiyası; \"Potensial artım (Growth decomp)\" bu amillərin trendlərindən qurulan potensialdır." },
  { re: /\bTFP\b|total factor productivity/i, term: "Total factor productivity (TFP)", en: "The part of output growth not explained by measured capital and labour — broadly, efficiency and technology.", az: "Ölçülən kapital və əməklə izah olunmayan məhsul artımının hissəsi — geniş mənada səmərəlilik və texnologiya." },
  { re: /HP filter|HP-filter/i, term: "HP filter", en: "The Hodrick–Prescott statistical filter (λ=100) that separates a series' trend (potential) from its cycle (gap).", az: "Seriyanın trendini (potensial) tsiklindən (kəsir) ayıran Hodrick–Prescott statistik filtri (λ=100)." },
  { re: /\bcapital\b/i, term: "Capital", en: "The contribution of the capital stock (accumulated investment) to growth in the production-function decomposition.", az: "İstehsal funksiyası dekompozisiyasında kapital ehtiyatının (yığılmış investisiya) artıma töhfəsi." },
  { re: /\blabou?r\b/i, term: "Labour", en: "The contribution of employment (and hours) to growth in the production-function decomposition.", az: "İstehsal funksiyası dekompozisiyasında məşğulluğun (və saatların) artıma töhfəsi." },
  { re: /terms of trade/i, term: "Terms of trade", en: "Export prices relative to import prices; oil-dominated for Azerbaijan.", az: "İxrac qiymətlərinin idxal qiymətlərinə nisbəti; Azərbaycan üçün neft üstünlüklü." },
  { re: /real effective exchange|\bREER\b/i, term: "Real effective exchange rate (REER)", en: "The trade-weighted exchange rate adjusted for relative prices — external price competitiveness.", az: "Nisbi qiymətlərə görə düzəlişlə ticarət-çəkili məzənnə — xarici qiymət rəqabətqabiliyyətliliyi." },
  { re: /primary balance/i, term: "Primary balance", en: "The fiscal balance excluding interest payments, % of GDP.", az: "Faiz ödənişləri istisna olmaqla fiskal balans, ÜDM-in %-i." },
  { re: /current account/i, term: "Current account", en: "Net external transactions (trade + income + transfers), % of GDP; a surplus adds to reserves.", az: "Xalis xarici əməliyyatlar (ticarət + gəlir + transfertlər), ÜDM-in %-i; profisit ehtiyatları artırır." },
  { re: /broad money|\bM2\b|\bM3\b/i, term: "Broad money", en: "Currency in circulation plus bank deposits (M2/M3).", az: "Dövriyyədəki nağd pul üstəgəl bank əmanətləri (M2/M3)." },
  { re: /expected inflation|inflation expectation/i, term: "Expected inflation", en: "Forward-looking inflation expectations entering the Phillips curve.", az: "Phillips əyrisinə daxil olan gələcəyə yönəlik inflyasiya gözləntiləri." },
  { re: /imported inflation|import price/i, term: "Imported inflation", en: "The contribution of import prices and the exchange rate to domestic CPI.", az: "İdxal qiymətlərinin və məzənnənin daxili İQİ-yə töhfəsi." },
  { re: /neutral.*rate|natural.*rate/i, term: "Neutral (natural) rate", en: "The real interest rate consistent with output at potential and stable inflation.", az: "Məhsulun potensialda və inflyasiyanın sabit olması ilə uyğun real faiz dərəcəsi." },
  { re: /interest rate gap/i, term: "Interest rate gap", en: "The real policy rate minus the neutral rate — positive = restrictive policy.", az: "Real uçot dərəcəsi minus neytral dərəcə — müsbət = sərt siyasət." },
  { re: /non-?oil/i, term: "Non-oil", en: "The economy excluding the hydrocarbon (oil & gas) sector — what fiscal and monetary policy most affect.", az: "Karbohidrogen (neft-qaz) sektoru istisna olmaqla iqtisadiyyat — fiskal və monetar siyasətin ən çox təsir etdiyi." },
  { re: /reserves/i, term: "Reserves", en: "Official FX reserves; shown as % of GDP, months of imports, or vs short-term debt.", az: "Rəsmi valyuta ehtiyatları; ÜDM-in %-i, idxal ayları və ya qısamüddətli borca nisbətdə." },
  { re: /fiscal balance|budget balance/i, term: "Fiscal balance", en: "Government revenue minus expenditure, % of GDP (a deficit if negative).", az: "Dövlət gəlirləri minus xərclər, ÜDM-in %-i (mənfi olarsa kəsir)." },
  { re: /gross.*debt|public debt/i, term: "Gross public debt", en: "Total outstanding general-government debt, % of GDP.", az: "Ümumi dövlət borcunun cəmi, ÜDM-in %-i." },
  { re: /policy rate|refinanc/i, term: "Policy rate", en: "The central bank's refinancing rate — the main monetary-policy instrument.", az: "Mərkəzi bankın yenidən maliyyələşdirmə dərəcəsi — əsas monetar siyasət aləti." },
];
function glossaryFor(f) {
  const az = LANG === "az";
  const hay = [f.title || ""].concat((f.series || []).map(s => s.name || "")).join(" · ");
  const seen = new Set(), out = [];
  for (const g of GLOSSARY) { if (g.re.test(hay) && !seen.has(g.term)) { seen.add(g.term); out.push([g.term, az ? g.az : g.en]); } if (out.length >= 6) break; }
  return out;
}
function figInfo(f) {
  // Fancharts-sheet figures are drawn as the engine fan, so describe THAT (central + 90% interval) rather
  // than the anonymous percentile-band series that would otherwise show as "Series 1…6".
  if (f.sheet === "Fancharts" && !f.fan) {
    const fv = /inflation/i.test(f.title) ? "inflation" : /gdp|growth/i.test(f.title) ? "real_gdp_growth" : null;
    const fd = (((typeof RUN !== "undefined" && RUN && RUN.fan) || FAN0 || {}))[fv];
    if (fv && fd) {
      const lbl = tInd((META.fan_labels && META.fan_labels[fv]) || clean(f.title));
      f = {
        title: f.title, unit: f.unit || (META.fan_units && META.fan_units[fv]) || "", sheet: f.sheet, engine_var: fv, fan: true,
        series: [{ name: lbl, x: fd.years, y: fd.central }, { name: (LANG === "az" ? "Aşağı 90%" : "Low 90%"), x: fd.years, y: fd.lo90 }, { name: (LANG === "az" ? "Yuxarı 90%" : "High 90%"), x: fd.years, y: fd.hi90 }]
      };
    }
  }
  const P = META.params || {}, ph = P.phillips || [], ty = P.taylor || [], v = f.engine_var, sheet = f.sheet || "";
  const az = LANG === "az";
  const compoNames = (f.series || []).map(s => clean(s.name)).filter(Boolean).slice(0, 4).join(", ");
  const isQ = !!f.quarterly;
  let shows = (az && VARDESC_AZ[v]) ? VARDESC_AZ[v] : VARDESC[v];
  for (const [re, d] of TITLEDESC) if (re.test(f.title)) { shows = az ? "Normativ hesablama (proqnoz deyil): cari məhsul kəsirini hər üfüqdə bağlayacaq sabit illik real ÜDM artımı — 1, 2, … 5 illik xətlər." : d; break; }
  if (!shows) shows = isQ ? (az ? "Müşahidə olunmuş rüblük göstərici (faktiki) — il-içi dinamikanı izləmək və nowcast körpüsünü qidalandırmaq üçün." : "Observed quarterly outturn (actual) — shown to track within-year dynamics and feed the nowcast bridge.")
    : f.fan ? (az ? "Mühərrikin mərkəzi proqnozu, üfüq boyunca genişlənən etibarlılıq zolaqları ilə." : "Engine central forecast with confidence bands that widen over the horizon.")
    : f.radar ? (az ? "Ölçülər üzrə risk balları, ildən-ilə müqayisə olunur." : "Risk scores across dimensions, compared year-on-year.")
      : (f.series && f.series.length >= 3 && (COMPO.test(f.title) || detectTotalIdx(f.series) >= 0))
        ? (az ? `Dekompozisiya — komponentlər (${compoNames}) cəmlənərək ümumi göstəricini verir.` : `Decomposition — the components (${compoNames}) sum to the total.`)
        : (() => {
          const nm = (f.series || []).map(s => clean(s.name)).filter(Boolean);
          if (nm.length >= 2) return az ? `Bu qrafik müqayisə edir: ${nm.join(", ")}. Hər seriyanın izahı aşağıdakı «Terminlər» bölməsindədir.` : `This figure compares ${nm.join(", ")}. Each series is defined under "Terms" below.`;
          return az ? `“${esc(sheet)}” CAEM vərəqindən təkrar yaradılıb.` : `Reproduced from CAEM sheet “${esc(sheet)}”.`;
        })();
  const calib = { inflation: `c₁=${ph[0]}, c₂=${ph[1]}, c₃=${ph[2]} (CAEM 1b).`, policy_rate: `a=${ty[0]}, b=${ty[1]}, ρ=${ty[2]} (CAEM 1c).`,
    output_gap: "CAEM sheet B1a.", trend_growth: "CAEM B1a.", gross_debt: "CAEM 3b; effective rate ≈ 3%.",
    fiscal_balance: "Scenario response: oil ≈ 0.12 pp/1%, tax, FX.", primary_balance: "Scenario response: oil, tax, FX.", terms_of_trade: "Scenario response: oil ± export/import prices." }[v] || "";
  let model = v ? ((VAREQ[v] ? kx(VAREQ[v][0], VAREQ[v][1]) : "") + (calib ? `<p>${calib}</p>` : ""))
    : isQ ? `<p>${az ? "Müşahidə olunmuş məlumat, model nəticəsi deyil. Mənbə: DSK rüblük milli hesablar / aylıq AMB göstəriciləri, rüblərə ortalanmış." : "Observed data, not a model output. Source: SSC quarterly national accounts / monthly CBAR indicators, averaged to quarters."}</p>`
    : f.fan ? `<p>${tx("id.fan", "Fan chart. Central path from the engine; 50/80/90% bands widen as σ·z·√h — σ from the equation's robust in-sample residuals (inflation &amp; policy rate) or the variable's historical annual-change σ.")}</p>`
      : `<p>${az ? `“${esc(sheet)}” CAEM vərəqindən birbaşa təkrar yaradılıb — dəyərlər CAEM-in öz hesabladığı nəticədir.` : `Reproduced directly from CAEM sheet “${esc(sheet)}” — the values are CAEM's own computed output.`}</p>`;
  const xs = [...new Set((f.series || []).flatMap(s => s.x))].filter(x => x != null);
  const allNum = xs.every(x => typeof x === "number");
  if (allNum) xs.sort((a, b) => a - b); else xs.sort();
  let table = "";
  if ((f.series || []).length && xs.length) {
    const names = f.series.map((s, i) => clean(s.name) || (f.series.length === 1 ? clean(f.title) : "Series " + (i + 1)));
    const idx = f.series.map(s => { const m = {}; s.x.forEach((x, i) => m[x] = s.y[i]); return m; });
    const body = xs.map(x => `<tr><td>${x}</td>${idx.map(m => `<td>${m[x] == null ? "" : Math.round(m[x] * 100) / 100}</td>`).join("")}</tr>`).join("");
    const xhdr = isQ ? (az ? "Rüb" : "Quarter") : tx("id.year", "Year");
    table = `<h4>${tx("id.data", "Data")} <button id="infocsv" class="lk">⤓ CSV</button></h4>
      <div class="id-tblwrap"><table class="id-tbl"><thead><tr><th>${xhdr}</th>${names.map(n => `<th>${esc(n.slice(0, 16))}</th>`).join("")}</tr></thead><tbody>${body}</tbody></table></div>`;
  }
  const prov = (META.provenance && META.provenance.actuals) || {}, pv = prov[v];
  const src = pv
    ? `<b>${az ? "2025 faktiki" : "2025 actual"}:</b> ${esc(pv.value)}${pv.unit ? " " + esc(pv.unit) : ""} — ${esc(pv.source)}${pv.date ? ` (${az ? "dərc" : "released"} ${esc(pv.date)})` : ""}${pv.url ? ` · <a href="${esc(pv.url)}" target="_blank" rel="noopener">${az ? "mənbə" : "source"}</a>` : ""}. ${az ? "Digər illər: CAEM modeli." : "Other years: CAEM model."}`
    : isQ ? (az ? "Dövlət Statistika Komitəsi / Azərbaycan Mərkəzi Bankı." : "State Statistical Committee / Central Bank of Azerbaijan.")
    : esc((META.provenance && META.provenance.caem_default) || "CAEM.xlsb workbook.");
  const live = v ? `<h4>${tx("id.live", "Live")}</h4><p>${tx("id.live.p", "Recomputes when a Scenario-console input is changed and the forecast is run; the dashed red line is the scenario against the solid baseline.")}</p>` : "";
  const vintage = isQ ? (az ? "Bütün nöqtələr faktiki nəticələrdir; ən son rüblər nowcast-ı təyin edir." : "All points are observed outturns; the most recent quarters anchor the nowcast.")
    : (v || f.fan) ? tx("id.vintage", "2025 = official outturn; the model forecasts <b>2026+</b> (shaded).")
    : tx("id.vintage2", "Shaded = forecast <b>2026+</b>; 2025 = last actual. This figure's 2025 point is CAEM's estimate — official 2025 outturns are in the scorecard.");
  const srcSuffix = isQ ? "" : ` · ${az ? "CAEM vərəqi" : "CAEM sheet"} “${esc(sheet)}”.`;
  const terms = glossaryFor(f);
  const termsHtml = terms.length ? `<h4>${tx("id.terms", "Terms in this figure")}</h4><dl class="id-gloss">${terms.map(([t, d]) => `<dt>${esc(t)}</dt><dd>${esc(d)}</dd>`).join("")}</dl>` : "";
  const html = `${f.unit ? `<p class="id-unit">${esc(f.unit)}</p>` : ""}
    <h4>${tx("id.shows", "What it shows")}</h4><p>${shows}</p>
    <h4>${tx("id.model", "Model &amp; data")}</h4>${model}
    <h4>${tx("id.read", "How to read it")}</h4><p>${vintage}</p>${live}
    ${table}
    ${termsHtml}
    <h4>${tx("id.src", "Source &amp; provenance")}</h4><p class="id-src">${src}${srcSuffix}</p>`;
  return { title: f.title, html, f };
}
function downloadFigData(f) {
  const xs = [...new Set((f.series || []).flatMap(s => s.x))].filter(x => x != null);
  const allNum = xs.every(x => typeof x === "number");
  if (allNum) xs.sort((a, b) => a - b); else xs.sort();
  const names = f.series.map((s, i) => clean(s.name) || (f.series.length === 1 ? clean(f.title) : "series" + (i + 1)));
  const idx = f.series.map(s => { const m = {}; s.x.forEach((x, i) => m[x] = s.y[i]); return m; });
  const rows = [[f.quarterly ? "period" : "year"].concat(names)].concat(xs.map(x => [x].concat(idx.map(m => m[x] == null ? "" : m[x]))));
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
  let hasScn = false;
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
      const tot = k === totIdx, c = tot ? "#1a1a17" : PAL[pi++ % PAL.length];
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
      if (!multi) leg.push({ name: tx("leg.baseline", "Baseline"), color: primary });
      traces.push({ x: xs, y: ys, type: "scatter", mode: "lines", line: { color: "#c0392b", width: 2.4, dash: "dash" }, hovertemplate: "<b>scenario</b>: %{y:.2f}<extra></extra>", showlegend: false });
      hasScn = true; leg.push({ name: scnLegName(), color: "#c0392b", dash: "dash" });
    }
    // shock-INPUT figure (e.g. Oil price): shocking the input transforms its own path exactly
    const sf = !f.engine_var && shockMatch(f.title);
    if (RUN && sf && RUN.shock[sf.field]) {
      const base = f.series[0], ff = LIVE_FF || META.first_forecast, v = RUN.shock[sf.field];
      const isPct = /change/i.test(f.unit || "") || /change/i.test(f.title);
      const ys = shockSeries(base.y, base.x, sf, v, ff, isPct);
      if (!multi) leg.push({ name: tx("leg.baseline", "Baseline"), color: primary });
      traces.push({ x: base.x, y: ys, type: "scatter", mode: "lines", line: { color: "#c0392b", width: 2.4, dash: "dash" }, hovertemplate: "<b>scenario</b>: %{y:.2f}<extra></extra>", showlegend: false });
      hasScn = true; leg.push({ name: scnLegName(), color: "#c0392b", dash: "dash" });
    }
    // current-account figures respond to an oil-price shock (labelled elasticity: oil +1% → CA +0.12 pp of GDP)
    if (RUN && caElas(f) && RUN.shock.oil_price) {
      const base = f.series[0], ff = LIVE_FF || META.first_forecast, v = RUN.shock.oil_price;
      const ys = base.x.map((yr, i) => base.y[i] == null ? null : (yr < ff ? base.y[i] : base.y[i] + CA_ELAS * v));
      if (!multi) leg.push({ name: tx("leg.baseline", "Baseline"), color: primary });
      traces.push({ x: base.x, y: ys, type: "scatter", mode: "lines", line: { color: "#c0392b", width: 2.4, dash: "dash" }, hovertemplate: "<b>scenario</b>: %{y:.2f}<extra></extra>", showlegend: false });
      hasScn = true; leg.push({ name: scnLegName(), color: "#c0392b", dash: "dash" });
    }
  }
  const hasBars = traces.some(t => t.type === "bar");
  const baseH = hasBars ? 208 : 192;
  // forecast boundary is the SAME everywhere: 2025 actual, forecast 2026+ (line at 2025.5)
  const shapes = (f.xyear && !yearCat) ? fcShapes(allx, LIVE_FF || META.first_forecast) : [];
  const layout = baseLayout(f.xyear && !yearCat, shapes, big ? baseH + 140 : baseH, 24, tickStep(allx));
  if (yearCat) layout.barmode = "group";
  if (hasBars) layout.yaxis.rangemode = "tozero";       // bars must sit on a zero baseline (fixes oil/gas overflow)
  const an = scnAnno(); if (hasScn && an) layout.annotations = [an];   // name the active scenario, in-canvas (shows in PNG too)
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
// realistic, historically-grounded named scenarios (global & domestic, positive & negative)
const PRESETS = [
  { name: "Oil price crash", az: "Neft qiymətinin çökməsi", s: { oil_price: -35 } },              // 2014-15 / 2020 collapse
  { name: "Commodity upswing", az: "Əmtəə qiymətlərinin yüksəlişi", s: { oil_price: 25, partner_growth: 1.5 } }, // 2021-22 boom
  { name: "Global recession", az: "Qlobal tənəzzül", s: { oil_price: -15, partner_growth: -2.5 } },// 2009-style
  { name: "Manat devaluation", az: "Manatın devalvasiyası", s: { exchange_rate: 20 } },            // 2015 devaluation
  { name: "Non-oil reform boom", az: "Qeyri-neft islahat artımı", s: { nonoil_growth: 2, potential_growth: 1 } },
  { name: "Fiscal consolidation", az: "Fiskal konsolidasiya", s: { tax: 1.5 } },
];
function renderPresets() {
  const el = $("#presets");
  el.querySelectorAll(".pp").forEach(b => b.remove());
  PRESETS.forEach(p => {
    const b = document.createElement("button"); b.className = "pp"; b.textContent = (LANG === "az" && p.az) ? p.az : p.name;
    b.onclick = () => { FIELDS.forEach(f => $("#s_" + f).value = p.s[f] || 0); doRun(); };
    el.appendChild(b);
  });
}
// small ⓘ button on each scenario field → a popover defining that input (from FIELD_META)
function wireFieldInfo() {
  let pop = $("#fieldpop");
  if (!pop) { pop = document.createElement("div"); pop.id = "fieldpop"; document.body.appendChild(pop); pop.onclick = e => e.stopPropagation(); }
  FIELDS.forEach(f => {
    const inp = $("#s_" + f); if (!inp) return;
    const fld = inp.closest(".fld"); if (!fld || fld.querySelector(".fldi")) return;
    const b = document.createElement("button"); b.className = "fldi"; b.type = "button"; b.textContent = "ⓘ"; b.setAttribute("aria-label", "info");
    fld.appendChild(b);
    b.onclick = e => {
      e.stopPropagation(); const m = FIELD_META[f]; if (!m) return;
      pop.innerHTML = `<b>${esc(fieldLabel(f))}</b> <span class="fp-u">${esc(fieldUnit(f))}</span><p>${LANG === "az" ? m.daz : m.den}</p>`;
      pop.classList.add("show");
      const r = b.getBoundingClientRect();
      pop.style.left = Math.max(8, Math.min(r.left - 6, window.innerWidth - pop.offsetWidth - 10)) + "px";
      pop.style.top = (r.bottom + 6 + window.scrollY) + "px";
    };
  });
  document.addEventListener("click", () => { const p = $("#fieldpop"); if (p) p.classList.remove("show"); });
}
function wireRun() {
  $("#run").onclick = doRun;
  $("#reset").onclick = () => { FIELDS.forEach(f => $("#s_" + f).value = 0); RUN = null; $("#status").textContent = ""; refresh(); };
  $("#savescen").onclick = saveCurrentScenario;
  renderPresets();
}

init().catch(e => { $("#view").innerHTML = `<p style="color:#b13f2e">Load error: ${e}. Is the API running?</p>`; });
