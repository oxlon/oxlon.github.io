"""FR4 / NFR3 — decision-support panel and role-based reports.

One context (built by run_all.py) feeds every output, so the leadership panel, the analyst
panel, the PDF and Excel exports and the JSON API can never disagree:

  site/index.html                     leadership panel (rəhbərlik)
  site/analitik.html                  analyst panel (analitik)
  reports/risk_hesabati_<rol>.pdf     printed report per role (headless Chrome)
  reports/risk_hesabati_<rol>.xlsx    Excel report per role
  output/risk_api.json                machine-readable feed for the MİİS dashboard (TT §3.5 data model)

Which sections each role sees is set in input/rollar.csv — no code change needed.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from . import config, factors
from .charts import az, esc, hbars, heatmap_table, line_band

ROLE_TITLE = {"rehberlik": "Rəhbərlik icmalı", "analitik": "Analitik hesabat"}

RISK_CSS = """/* risk.css — the components the §15.5.3 panels need beyond base.css (copied verbatim
   from the §15.5.1/§15.5.2 sites). Same tokens, no new colours. */
p.lead-in{font-size:17.5px;color:var(--ink-2);margin-bottom:26px}
p.note{font-size:14px;color:var(--ink-2);line-height:1.55;margin:4px 0 22px}
.count-strip .cs-s{display:block;font-size:12.5px;color:var(--ink-3);margin-top:3px;line-height:1.35}
.count-strip .cs-n.is-gap{color:var(--status-gap)}
ul.alerts{list-style:none;padding-left:0;margin:0 0 24px}
ul.alerts li{padding:7px 0;border-bottom:1px solid var(--rule);font-size:15px;line-height:1.5}
ul.alerts li:last-child{border-bottom:0}ul.alerts .a-type{font-weight:600;margin:0 6px}
ul.alerts .a-id{color:var(--accent);font-weight:600;margin-right:4px}
.heat-wrap{display:grid;grid-template-columns:minmax(0,560px) minmax(0,1fr);gap:28px;align-items:start;margin:0 0 24px}
@media (max-width:1000px){.heat-wrap{grid-template-columns:1fr}}.heat-wrap .tbl-dense{min-width:0}
table.heat{border-collapse:separate;border-spacing:4px;font-size:13px}
table.heat th,table.heat td{border:0;padding:4px 6px}
table.heat th{font-size:11.5px;letter-spacing:.03em;text-transform:uppercase;color:var(--ink-2);font-weight:600;text-align:center}
table.heat th.plab{text-align:right;white-space:nowrap;text-transform:none;letter-spacing:0}
table.heat td{height:62px;width:19%;vertical-align:top;border-radius:4px;-webkit-print-color-adjust:exact;print-color-adjust:exact}
table.heat td.ch{background:var(--status-gap-bg);box-shadow:inset 0 0 0 1px #efc6c3}
table.heat td.cm{background:var(--status-partial-bg);box-shadow:inset 0 0 0 1px #ecdcb4}
table.heat td.cl{background:var(--status-done-bg);box-shadow:inset 0 0 0 1px #cfe5d4}
table.heat .sc{display:block;font-size:11px;color:var(--ink-3);font-variant-numeric:tabular-nums}
.hchip{display:inline-block;background:var(--bg);border:1px solid var(--rule-strong);border-radius:3px;padding:0 5px;margin:2px 2px 0 0;font-size:12.5px;font-weight:600;color:var(--ink)}
figure.chart-fig{margin:0 0 10px}
svg.chart{width:100%;height:auto;display:block;font-family:var(--sans)}
svg .grid{stroke:var(--rule);stroke-width:1}svg .zero{stroke:var(--ink-3);stroke-width:1}
svg .vline{stroke:var(--ink-3);stroke-dasharray:3 3}
svg .tick,svg .leg,svg .reflab,svg .bval{fill:var(--ink-2);font-size:12px}svg .blab{fill:var(--ink);font-size:12.5px}
svg .band{fill:var(--accent);fill-opacity:.12}svg .band2{fill:var(--accent);fill-opacity:.24}
svg .s1{fill:none;stroke:var(--accent);stroke-width:2.4}svg .s2{fill:none;stroke:var(--ink-3);stroke-width:1.6;stroke-dasharray:5 4}
svg .s3{fill:none;stroke:var(--status-gap);stroke-width:1.8}svg .s4{fill:none;stroke:var(--ink);stroke-width:1.6}
svg .ref{stroke:var(--status-gap);stroke-dasharray:6 4;stroke-width:1.4}svg .ref2{stroke:var(--ink-3);stroke-dasharray:2 3;stroke-width:1.2}
svg rect.neg{fill:var(--status-gap)}svg rect.pos{fill:var(--status-done)}svg rect.alt{fill:var(--ink-3);fill-opacity:.55}
.dl-row{display:flex;flex-wrap:wrap;gap:8px 16px;margin:0 0 26px;font-size:14.5px}
.panel-cta{display:flex;flex-wrap:wrap;align-items:center;gap:10px 16px;margin:0 0 26px;padding:14px 16px;background:var(--accent-soft);border:1px solid var(--rule);border-radius:8px}
.panel-cta p{margin:0;flex:1 1 260px;font-size:14.5px;color:var(--ink)}
a.btn-panel{display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:6px;background:var(--accent);color:#fff;font-weight:600;text-decoration:none;font-size:15px;white-space:nowrap}
a.btn-panel:hover,a.btn-panel:focus-visible{filter:brightness(1.12);text-decoration:none;color:#fff}
.nav-panel a{font-weight:600}
@media print{.panel-cta,.nav-panel{display:none}}
@media print{body{font-size:12px}.heat-wrap{grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:16px}
table.heat td{height:48px}.heat-wrap .tbl-dense{min-width:0;font-size:12px}.heat-wrap th,.heat-wrap td{padding:5px 6px}h2{break-after:avoid;margin-top:26px}.table-wrap,figure,table.heat,ul.alerts li{break-inside:avoid}
.table-wrap{overflow:visible}.count-strip li{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""


PILL = {"yüksək": "gap", "orta": "partial", "aşağı": "done", "xəbərdarlıq": "gap", "izləmə": "partial",
        "normal": "done", "keçdi": "done", "keçmədi": "gap", "ödənilib": "done", "ödənilməyib": "gap"}


def _pill(text):
    return f'<span class="pill pill-{PILL.get(text, "neutral")}">{esc(text)}</span>'


def _tbl(df: pd.DataFrame, num: dict | None = None, raw: set | None = None) -> str:
    """num: column -> decimals (formatted AZ, right-aligned c-num); raw: columns with trusted HTML."""
    num = num or {}
    raw = raw or set()
    cls = ["c-num" if c in num else ("c-id" if c in ("ID", "Risk_id", "Test", "№") else "c-text") for c in df.columns]
    head = "".join(f'<th class="{k}">{esc(c)}</th>' for c, k in zip(df.columns, cls))
    body = []
    for r in df.itertuples(index=False):
        cells = []
        for c, k, v in zip(df.columns, cls, r):
            if c in num:
                x = az(float(v), num[c]) if pd.notna(v) else "—"
            elif c in raw:
                x = v
            else:
                x = esc("" if (isinstance(v, float) and np.isnan(v)) else v)
            cells.append(f'<td class="{k}">{x}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (f'<div class="table-wrap"><table class="tbl tbl-dense"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


# ---------------------------------------------------------------- sections
def s_kpi(c):
    S, res, L = c["S"], c["res"], c["live"]
    j = res.col(res.score_year)
    g = res.total("g")[:, j]
    nh = int((S["prioritet"] == "yüksək").sum())
    be = float(res.meta["brent_centre"][j])
    bk = float(c["baseline"].at[res.score_year, "brent_breakeven_ca0"])
    mm = c["measures"]
    tiles = [
        (str(nh), "yüksək prioritetli risk", f"{len(S)} riskdən; skor ≥ {int(c['p']['score_high'])}"),
        (az(float(np.median(g)), 1, pct=True), f"qeyri-neft artımı {res.score_year} (median)",
         f"makro baza: {az(res.base['g'][j], 1, pct=True)}"),
        (az(float(np.quantile(g, 0.10)), 1, pct=True), f"Growth-at-Risk (P10), {res.score_year}",
         f"P5: {az(float(np.quantile(g, 0.05)), 1, pct=True)}"),
        (az(float((g < c['p']['nonoil_gar_threshold']).mean() * 100), 0, pct=True),
         f"P(qeyri-neft artımı < {az(c['p']['nonoil_gar_threshold'], 0)}%)", "birgə simulyasiya"),
        (f"{az(L['brent_last'], 1)} $", f"Brent, {L['brent_last_date']}",
         f"{res.score_year} mərkəzi yol {az(be, 0)} $; başabaş {az(bk, 1)} $"),
        (str(len(c["alerts"])), "aktiv xəbərdarlıq",
         f"tədbirlər: {int((mm['status'] == 'icrada').sum())} icrada, {int((mm['status'] == 'təklif').sum())} təklif, "
         f"{int(mm['gecikir'].sum())} gecikir"),
    ]
    body = "".join(f'<li><span class="cs-n{" is-gap" if i == 0 and nh else ""}">{v}</span><span class="cs-l">{esc(l)}</span>'
                   f'<span class="cs-s">{esc(s)}</span></li>' for i, (v, l, s) in enumerate(tiles))
    return f'<ul class="count-strip">{body}</ul>'


def s_alerts(c):
    A = c["alerts"]
    if A.empty:
        return '<p class="note">Aktiv xəbərdarlıq yoxdur.</p>'
    order = {"yüksək": 0, "orta": 1, "aşağı": 2}
    A = A.assign(o=A["ciddilik"].map(order)).sort_values(["o", "tip"])
    items = "".join(f'<li>{_pill(r.ciddilik)}<span class="a-type">{esc(r.tip)}</span>'
                    f'{f"<span class=a-id>{esc(r.risk_id)}</span>" if r.risk_id else ""}— {esc(r.mesaj)}</li>'
                    for r in A.itertuples())
    return f'<ul class="alerts">{items}</ul>'


def s_heatmap(c):
    S = c["S"]
    names = dict(zip(S["risk_id"], S["ad"]))
    leg = S.sort_values("risk_id")[["risk_id", "ad", "skor", "prioritet"]].copy()
    leg["prioritet"] = [_pill(x) for x in leg["prioritet"]]
    leg.columns = ["ID", "Risk", "Skor", "Prioritet"]
    return (f'<div class="heat-wrap"><div>{heatmap_table(S, names)}</div><div>{_tbl(leg, num={"Skor": 0}, raw={"Prioritet"})}</div></div>'
            f'<p class="note">Rəng: qırmızı — yüksək (skor ≥ {int(c["p"]["score_high"])}), sarı — orta (≥ {int(c["p"]["score_medium"])}), '
            f'yaşıl — aşağı. Xəritə təqdimat qatıdır; prioritetləşdirmənin kəmiyyət əsası risklərin aşağı quyruğa töhfəsidir '
            f'(analitik hesabat).</p>')


def s_top(c, n=None):
    S = c["S"].copy()
    if n:
        S = S.head(n)
    meas = c["measures"]
    first = {}
    for r in meas.itertuples():
        for rid in r.risk_idler.split(";"):
            first.setdefault(rid.strip(), f"{r.tedbir_id} · {r.mesul} · {r.status}")
    prev = c.get("prev_scores", pd.Series(dtype=float))
    def trend(r):
        if r.risk_id not in prev.index:
            return "yeni"
        d = r.skor - prev[r.risk_id]
        return "↑" if d > 0 else ("↓" if d < 0 else "=")
    def imp(r):
        return {"qeyri-neft ÜDM": f"{az(r.tesir_g, 2)} f.b. qeyri-neft", "inflyasiya": f"+{az(r.tesir_cpi, 2)} f.b. inflyasiya",
                "büdcə": f"{az(r.tesir_fis, 2)}% ÜDM büdcə"}[r.I_olcu]
    df = pd.DataFrame({
        "№": S["sira"], "ID": S["risk_id"], "Risk": S["ad"], "Ailə": S["aile"].map(factors.FAMILY_AZ),
        "Ehtimal": [az(x * 100, 0, pct=True) for x in S["ehtimal"]],
        "Təsir": [imp(r) for r in S.itertuples()], "P×T": [f"{r.P_bal}×{r.I_bal} = <b>{r.skor}</b>" for r in S.itertuples()],
        "Prioritet": [_pill(x) for x in S["prioritet"]], "Trend": [trend(r) for r in S.itertuples()],
        "Əsas tədbir · məsul · status": [first.get(x, "—") for x in S["risk_id"]]})
    return _tbl(df, raw={"P×T", "Prioritet"}) + (
        f'<p class="note">Ehtimal və təsir {c["res"].score_year}-ci il üçün eyni birgə simulyasiyadan hesablanır '
        f'({c["res"].meta["n"]:,} ssenari). Təsir: risk hadisəsi baş verdikdə kanal töhfəsinin gözləniləndən sapması. '
        f'Ehtimal mənbəyi «ekspert» olan risklər Nazirliyin təsdiqinə təqdim olunmuş örtükdür.</p>').replace(",", " ")


def s_fan(c):
    res, D = c["res"], c["dist"]
    g = D[D["gosterici"] == "g"].set_index("il")
    hist = factors.channels()["_panel"]["nonoil_g"].loc[2015:config.LAST_ACTUAL]
    x = list(hist.index) + list(g.index)
    nan = [np.nan] * len(hist)
    def ext(col):
        return nan[:-1] + [hist.iloc[-1]] + list(g[col])
    svg = line_band(x, [{"y": list(hist.values) + [np.nan] * len(g), "label": "faktiki", "cls": "s4"},
                        {"y": ext("p50"), "label": "median (risk)", "cls": "s1"},
                        {"y": nan + list(g["baza"]), "label": "makro baza", "cls": "s2"}],
                    bands=[{"lo": ext("p05"), "hi": ext("p95"), "cls": "band", "label": "P5–P95"},
                           {"lo": ext("p25"), "hi": ext("p75"), "cls": "band2", "label": "P25–P75"}],
                    hlines=[{"y": c["p"]["nonoil_gar_threshold"], "label": "R13 həddi", "cls": "ref"}],
                    vline=len(hist) - 1, title="Qeyri-neft ÜDM-in real artımı: faktiki və risk paylanması", ylab="%")
    gn = c["gar"]
    gar_ok = c["gar_validated"]
    tbl = pd.DataFrame({"İl": g.index, "Makro baza": g["baza"], "P5": g["p05"], "P10 (GaR)": g["p10"], "Median": g["p50"],
                        "P90": g["p90"], "ES10": g["ES10"]})
    return (svg + _tbl(tbl, num={k: 2 for k in tbl.columns if k != "İl"}) +
            f'<p class="note">Paylanma makro modelin (§15.5.1) mərkəzi yolu və yelpik eni ətrafında, risk amillərinin canlı '
            f'məlumatla şərtləndirilmiş birgə simulyasiyasıdır. ES10 — ən pis 10% ssenarinin ortası. Müstəqil yoxlama '
            f'(kvantil reqressiyası, {gn["n"]} müşahidə): {gn["year"]} üçün P10 {az(gn["q"][0.10], 1)}%, median '
            f'{az(gn["q"][0.50], 1)}% — {"NFR1 sınağından keçib" if gar_ok else "NFR1 sınağından keçmir, qərar üçün istifadə edilmir"}.</p>')


def s_brent(c):
    L, res = c["live"], c["res"]
    m = L["brent_monthly"].iloc[-36:]
    j = res.col(res.score_year)
    D = c["dist"][c["dist"]["gosterici"] == "brent"].set_index("il")
    xs = [d.strftime("%Y-%m") for d in m.index]
    svg = line_band(xs, [{"y": list(m.values), "label": "Brent, aylıq orta", "cls": "s1"}],
                    hlines=[{"y": float(c["baseline"].at[res.score_year, "brent_breakeven_ca0"]),
                             "label": f"cari hesab üçün başabaş {res.score_year}", "cls": "ref", "anchor": "start"},
                            {"y": float(res.brent_base[j]), "label": f"makro fərziyyə {res.score_year}", "cls": "ref2"}],
                    title="Brent: son 36 ay", ylab="USD/barel", xfmt=lambda s: s)
    tbl = pd.DataFrame({"İl": D.index, "Makro fərziyyə": D["baza"], "P10": D["p10"], "Median": D["p50"], "P90": D["p90"]})
    w = res.meta["w_struct"]
    return (svg + _tbl(tbl, num={k: 1 for k in tbl.columns if k != "İl"}) +
            f'<p class="note">Mərkəzi yol: makro struktur yolu ilə son ayın səviyyəsinin tərs-MSE çəkili birləşməsi '
            f'(struktur çəkisi {az(w, 2)}, makro geriyə doğru sınaqdan). {L["as_of"]} tarixinə: son müşahidə '
            f'{az(L["brent_last"], 2)} $ ({L["brent_last_date"]}), {config.as_of().year}-ci ilin ortası {az(L["brent_ytd_avg"], 1)} $.</p>')


def s_stress(c):
    st = c["stress"]
    y = c["res"].score_year
    g = st[(st["il"] == y) & (st["gosterici"].str.startswith("qeyri-neft"))]
    svg = hbars([f"{r.ssenari} · {r.ad}" for r in g.itertuples()], list(g["sapma"]), list(g["sapma_tedbirle"]),
                title=f"Stress ssenariləri: {y}-ci ildə qeyri-neft artımına təsir", unit="f.b.",
                lab1="tədbirsiz", lab2="prosiklik kəsintisiz (T09)")
    lv = c["levers"]
    inv = lv[lv["tedbir_id"] == "T09"].iloc[0]
    return (svg + f'<p class="note">Hər ssenari elan olunmuş şok vektorudur və eyni ötürmə mexanizmindən keçir. '
            f'Tədbir: Brent enəndə dövlət investisiyasının tarixi elastikliklə azaldılmaması (T09, T01). Kontrtsiklik '
            f'investisiya ilə risk amillərinin aşağı quyruğunu bağlamaq üçün təxminən {az(inv["lazim_olan_amil"], 1)} mlrd AZN '
            f'lazımdır (FR1 multiplikatoru).</p>')


def s_measures_summary(c):
    m, cov = c["measures"], c["coverage"]
    st = m["status"].value_counts().reindex(["təklif", "təsdiqlənib", "icrada", "tamamlanıb", "dayandırılıb"]).fillna(0).astype(int)
    tiles = "".join(f'<li><span class="cs-n">{v}</span><span class="cs-l">{esc(k)}</span></li>' for k, v in st.items())
    ok = (cov["tedbir_sayi"] > 0).all()
    late = m[m["gecikir"]]
    return (f'<ul class="count-strip">{tiles}<li><span class="cs-n{" is-gap" if len(late) else ""}">{len(late)}</span>'
            f'<span class="cs-l">gecikən</span></li></ul>'
            f'<p class="note">Qəbul şərti (hər risk üçün ən azı bir tədbir): {_pill("ödənilib" if ok else "ödənilməyib")} — '
            f'{len(cov)} risk, {len(m)} tədbir. ' + (f'Gecikən: {", ".join(late["tedbir_id"])}.' if len(late) else "Gecikən tədbir yoxdur.") + "</p>")


def s_register(c):
    S = c["S"]
    df = S[["risk_id", "ad", "aile", "nov", "sahib", "ufuq", "ehtimal", "ehtimal_menbe", "tesir_g", "tesir_cpi", "tesir_fis",
            "tesir_menbe", "P_bal", "I_bal", "I_olcu", "skor", "prioritet", "dispersiya_payi", "quyruq_tohfesi"]].copy()
    df["ehtimal"] = df["ehtimal"] * 100
    df["dispersiya_payi"] = df["dispersiya_payi"] * 100
    df.columns = ["ID", "Risk", "Ailə", "Növ", "Sahib", "Üfüq", "Ehtimal %", "Ehtimal mənbəyi", "Təsir: qeyri-neft f.b.",
                  "Təsir: inflyasiya f.b.", "Təsir: büdcə % ÜDM", "Təsir mənbəyi", "P", "T", "Ölçü", "Skor", "Prioritet",
                  "Dispersiya payı %", "Quyruq töhfəsi f.b."]
    return _tbl(df, num={"Ehtimal %": 1, "Təsir: qeyri-neft f.b.": 2, "Təsir: inflyasiya f.b.": 2, "Təsir: büdcə % ÜDM": 2,
                         "Dispersiya payı %": 1, "Quyruq töhfəsi f.b.": 2})


def s_contrib(c):
    C = c["contrib_g"]
    C = C[C["kanal"] != "resid"]
    svg = hbars(list(C["ad"]), list(C["quyruq_tohfesi_merkezlesmis"]),
                title="Ən pis 10% ssenaridə qeyri-neft artımına töhfə (gözləniləndən sapma)", unit="f.b.")
    r = c["contrib_g"][c["contrib_g"]["kanal"] == "resid"].iloc[0]
    tbl = c["contrib_g"][["ad", "risk_id", "orta", "dispersiya_payi", "quyruq_tohfesi", "quyruq_tohfesi_merkezlesmis"]].copy()
    tbl["dispersiya_payi"] *= 100
    tbl.columns = ["Kanal", "Risk", "Orta töhfə f.b.", "Dispersiya payı %", "P10 quyruğunda töhfə f.b.", "Mərkəzləşmiş f.b."]
    return (svg + _tbl(tbl, num={"Orta töhfə f.b.": 2, "Dispersiya payı %": 1, "P10 quyruğunda töhfə f.b.": 2, "Mərkəzləşmiş f.b.": 2}) +
            f'<p class="note">Eyler bölgüsü: kanalların töhfələrinin cəmi ümumi paylanmaya bərabərdir. Modelin qalıq '
            f'qeyri-müəyyənliyi (dispersiyanın {az(r["dispersiya_payi"] * 100, 0)}%-i) risk amili deyil və sıralamaya daxil edilmir.</p>')


def s_dist(c):
    D = c["dist"].copy()
    cols = ["ad", "il", "baza", "p05", "p10", "p25", "p50", "p75", "p90", "p95", "orta", "ES10"]
    D = D[cols]
    D.columns = ["Göstərici", "İl", "Baza", "P5", "P10", "P25", "P50", "P75", "P90", "P95", "Orta", "ES10"]
    return _tbl(D, num={k: 2 for k in D.columns if k not in ("Göstərici", "İl")}) + \
        '<p class="note">İnflyasiya üçün ES10 yuxarı quyruğun (ən yüksək 10%) ortasıdır.</p>'


def s_indicators(c):
    I = c["indicators"].copy()
    I["status"] = [_pill(x) for x in I["status"]]
    I["aile"] = I["aile"].map(factors.FAMILY_AZ)
    df = I[["ad", "aile", "vahid", "tezlik", "menbe", "son_tarix", "son_deyer", "tarixi_faiz", "z", "status"]]
    df.columns = ["Göstərici", "Ailə", "Vahid", "Tezlik", "Mənbə", "Son tarix", "Son dəyər", "Tarixi faiz", "z", "Status"]
    return _tbl(df, num={"Son dəyər": 2, "Tarixi faiz": 0, "z": 2}, raw={"Status"}) + \
        '<p class="note">Status: göstəricinin pis istiqamətdə tarixi paylanmanın ≥ 90-cı faizində olması — xəbərdarlıq, ≥ 75 — izləmə.</p>'


def s_channels(c):
    ch = pd.read_csv(config.OUTPUT / "FR1_transmission_channels.csv")
    df = ch[["izah", "izahedici", "emsal", "st_xeta", "p", "n", "nümunə", "tezlik", "sübut", "istifade"]]
    df.columns = ["Kanal", "İzahedici", "Əmsal", "St. xəta", "p", "n", "Nümunə", "Tezlik", "Sübut", "İstifadə"]
    M = c["mult"]
    return _tbl(df, num={"Əmsal": 3, "St. xəta": 3, "p": 3, "n": 0}) + (
        f'<h3>Struktur ötürmə (mikro FR1, birinci il)</h3><p class="note">Brent +10 $ → qeyri-neft ÜDM {az(M["brent10"], 2, sign=True)}%; '
        f'xarici tələb +10% → {az(M["extdem10"], 2, sign=True)}%; dövlət investisiyası +1 mlrd AZN → {az(M["stateinv1bn"], 2, sign=True)}%; '
        f'kredit yumşalması −200 b.p. → {az(M["credit_ease200"], 2, sign=True)}%. Şok yolları bu addım cavablarının '
        f'paylanmış gecikmə bükülməsi ilə ötürülür. Statistik zəif reduksiya kanalları sıfırlanmır: əmsal qeyri-müəyyənliyi '
        f'hər simulyasiyada N(b, se²) çəkilişi ilə daxil edilir.</p>')


def s_hazards(c):
    hz, p = c["hazards"], c["p"]
    ep = hz["eq_episodes"]
    ep = ep[ep["mag"] >= p["eq_mag_tier1"]].copy()
    ep["start"] = ep["start"].dt.strftime("%Y-%m-%d")
    t = ep[["start", "mag", "place"]]
    t.columns = ["Tarix", "M", "Yer (USGS)"]
    spi = hz["spi_hist"]
    svg = line_band(list(spi.index), [{"y": list(spi.values), "label": "SPI (hidroloji il)", "cls": "s1"}],
                    hlines=[{"y": p["spi_threshold"], "label": "quraqlıq həddi", "cls": "ref"}],
                    title="Quraqlıq indeksi SPI: kənd təsərrüfatı bölgələri, 1961–", ylab="SPI")
    return (f'<p class="note">Zəlzələ (USGS, 1950–cari, 30 günlük pəncərə ilə klasterləşdirilmiş epizodlar): '
            f'M 5,5–6,0 — {hz["eq_n_tier1"]} epizod (λ = {az(hz["eq_lambda_tier1"], 3)}/il); M ≥ 6,0 — {hz["eq_n_tier2"]} '
            f'epizod (λ = {az(hz["eq_lambda_tier2"], 3)}/il). Zərər parametrləri kalibrləmə fərziyyəsidir və FHN '
            f'məlumatı ilə əvəz edilməlidir (input/hedler.csv). Quraqlıq: SPI ≤ {az(p["spi_threshold"], 1)} tezliyi '
            f'{az(hz["p_drought"] * 100, 0)}%; son 12 ay ({hz["spi_now_end"]}) SPI = {az(hz["spi_now"], 2)}.</p>'
            + svg + _tbl(t, num={"M": 1}))


def s_chronology(c):
    E = c["chronology"].copy()
    df = E[["tarix", "aile", "hadise", "risk_idler", "gpr_qlobal_nisbet", "gpr_regional_nisbet", "brent_3ay_log_deyisme",
            "vix_nisbet", "zelzele_M", "usd_azn_il_deyisme_pct"]]
    df.columns = ["Tarix", "Ailə", "Hadisə", "Risklər", "GPR qlobal / 12 ay", "GPR regional / 12 ay", "Brent 3 ay, log %",
                  "VIX / 12 ay", "M", "USD/AZN il, %"]
    return _tbl(df, num={"GPR qlobal / 12 ay": 2, "GPR regional / 12 ay": 2, "Brent 3 ay, log %": 1, "VIX / 12 ay": 2, "M": 1,
                         "USD/AZN il, %": 1}) + \
        '<p class="note">Göstəricilərin hadisə ətrafındakı dəyişməsi məlumatdan hesablanır (əl ilə yazılmır).</p>'


def s_stress_full(c):
    st = c["stress"]
    piv = st.pivot_table(index=["ssenari", "ad", "gosterici"], columns="il", values="sapma").reset_index()
    piv.columns = [str(x) for x in piv.columns]
    desc = st.groupby("ssenari")["sok_vektoru"].first()
    d = pd.DataFrame({"Ssenari": desc.index, "Şok vektoru": desc.values})
    return _tbl(d) + _tbl(piv.rename(columns={"ssenari": "Ssenari", "ad": "Ad", "gosterici": "Göstərici"}),
                          num={str(y): 2 for y in config.FORECAST_YEARS})


def s_levers(c):
    lv = c["levers"][["alet", "tedbir_id", "olcu", "lazim_olan", "lazim_olan_amil", "mumkunluk", "izah"]].copy()
    lv.columns = ["Alət", "Tədbir", "Ölçü", "Tam P10 fərqi üçün", "Risk amilləri üçün", "Mümkünlük", "İzah"]
    return _tbl(lv, num={"Tam P10 fərqi üçün": 2, "Risk amilləri üçün": 2})


def s_measures(c):
    m = c["measures"]
    df = m[["tedbir_id", "risk_idler", "tedbir", "strategiya", "alet_novu", "mesul", "baslama", "muddet", "status",
            "gecikir", "effekt_tesir_pct", "effekt_menbeyi", "kpi", "yoxlama"]].copy()
    df["gecikir"] = df["gecikir"].map({True: "bəli", False: ""})
    df.columns = ["ID", "Risklər", "Tədbir", "Strategiya", "Alət", "Məsul", "Başlama", "Müddət", "Status", "Gecikir",
                  "Təsir azalması %", "Effekt mənbəyi", "KPI", "Yoxlama"]
    cov = c["coverage"][["risk_id", "ad", "tedbir_sayi", "aktiv_tedbir", "gecikən", "tedbirler", "qebul_serti"]]
    cov.columns = ["Risk", "Ad", "Tədbir sayı", "Aktiv", "Gecikən", "Tədbirlər", "Qəbul şərti"]
    return _tbl(df, num={"Təsir azalması %": 0}) + "<h3>Risk-tədbir əlaqəsi</h3>" + _tbl(cov)


def s_residual(c):
    r = c["residual"].copy()
    r["ehtimal_cari"] *= 100
    r["ehtimal_hedef"] *= 100
    r.columns = ["ID", "Risk", "Skor", "Ehtimal (cari) %", "Qalıq skor (cari)", "Ehtimal (hədəf) %", "Qalıq skor (hədəf)"]
    return _tbl(r, num={"Ehtimal (cari) %": 1, "Ehtimal (hədəf) %": 1}) + \
        ('<p class="note">Cari: tədbirlərin effekti icra statusu ilə çəkilir (təklif 0; təsdiqlənib 0,25; icrada 0,5; '
         'tamamlanıb 1). Hədəf: dayandırılmamış bütün tədbirlər tam icra olunduqda.</p>')


def s_backtest(c):
    T = c["bt_table"].copy()
    T["netice"] = [_pill(x) for x in T["netice"]]
    df = T[["test_id", "model", "hedef", "n", "pencere", "metrik", "deyer", "hedd", "netice", "melumat_bazasi", "qeyd"]]
    df.columns = ["Test", "Model", "Hədəf", "n", "Pəncərə", "Metrik", "Dəyər", "Hədd", "Nəticə", "Məlumat bazası", "Qeyd"]
    cal = c["calibration"][["hedef", "miqyas", "ehate80", "n", "qerar"]]
    cal.columns = ["Hədəf", "Miqyas", "80% əhatə", "n", "Qərar"]
    npass = int((c["bt_table"]["netice"] == "keçdi").sum())
    return (f'<p class="note">Rüb {esc(c["bt_table"]["rub"].iloc[0])}: {npass}/{len(c["bt_table"])} test keçdi. '
            'D — sadə etalona qarşı dəqiqlik; P — paylanma testləri; E — erkən xəbərdarlıq və hadisə ehtimalları; '
            'R — arxivləşdirilmiş real vaxt proqnozları. Keçməyən model qərar üçün istifadə edilmir və ya kalibrlənir '
            '(aşağıdakı cədvəl).</p>' + _tbl(df, num={"Dəyər": 3, "n": 0}, raw={"Nəticə"}) +
            "<h3>Kalibrləmə qərarları (simulyasiyaya avtomatik tətbiq olunur)</h3>" + _tbl(cal, num={"Miqyas": 2, "80% əhatə": 2}))


def s_feeds(c):
    F = c["feed_status"].copy()
    F.columns = ["Axın", "Vintaj", "Alınıb (UTC)", "Son müşahidə", "Yaş, gün", "Müşahidə", "SHA-256"]
    F["SHA-256"] = F["SHA-256"].str[:12]
    U = c.get("update_log")
    s = _tbl(F, num={"Yaş, gün": 0})
    if U is not None and len(U):
        u = U.tail(10)[["basladi_utc", "bitdi_utc", "tetik", "deyisen_girisler", "muddet_san", "sla_saat", "status"]].copy()
        u.columns = ["Başladı (UTC)", "Bitdi (UTC)", "Tətik", "Dəyişən girişlər", "Müddət, san", "Gecikmə, saat", "Status"]
        s += "<h3>Son yeniləmələr (NFR2)</h3>" + _tbl(u, num={"Müddət, san": 1, "Gecikmə, saat": 2})
    return s


def s_method(c):
    p, res = c["p"], c["res"]
    return (f'<p>Risk vahidi makro (§15.5.1) və mikro (§15.5.2) modellərin üzərində qurulur və öz mərkəzi yolunu nəşr etmir: '
            f'mərkəzi yollar və yelpik eni makro modelindir, büdcə bloku və şok ötürmə multiplikatorları mikro FR1 struktur '
            f'modelinindir. Bütün çıxışlar baza identifikatorunu daşıyır: <b>{esc(c["baseline_id"])}</b>.</p>'
            '<ul><li>FR1 — dörd ailə üzrə göstərici bazası (maliyyə; xarici-siyasi; təbii; daxili) + mikro EWS siqnalları; '
            'xarici-siyasi hadisələr Caldara–Iacoviello GPR indeksləri və hadisə xronologiyası ilə, təbii fəlakətlər '
            'təhlükə × məruz qalma × həssaslıq yanaşması ilə ölçülür.</li>'
            f'<li>FR2 — {res.meta["n"]:,} ssenarili birgə simulyasiya (tarixi illərin birgə butstrapı '
            f'{esc(res.meta["bootstrap_years"])}), risk skoru = ehtimal (1–5) × təsir (1–5); kəmiyyət prioriteti — '
            'aşağı quyruğa Eyler töhfəsi.</li>'.replace(",", " ") +
            '<li>FR3 — tədbirlər reyestri, risk-tədbir əlaqəsi, status izlənməsi, qalıq risk, 8 stress ssenarisi.</li>'
            '<li>NFR1 — rüblük geriyə doğru sınaq: sadə etalonlar, PIT/Berkowitz, Kupiec/Christoffersen, əhatə tolerantlığı, '
            'AUROC; nəticələr kalibrləməyə avtomatik tətbiq olunur.</li>'
            '<li>NFR2 — gündəlik avtomatik yeniləmə; yeni məlumatdan skorlara qədər ≤ 24 saat.</li></ul>'
            '<h3>Məlumat boşluqları (sorğu tələb olunur)</h3><ul>'
            '<li>Bank sektoru (problemli kreditlər, kapital adekvatlığı) — AMB (R04 hazırda ekspert örtüyüdür).</li>'
            '<li>Hidroloji sıralar və Xəzərin səviyyəsi — ETSN (R10 ekspert örtüyüdür).</li>'
            '<li>Fəlakət zərərləri — FHN (zəlzələ zərər parametrləri kalibrləmə fərziyyəsidir).</li>'
            '<li>ARDNF aktivləri — bufer adekvatlığı (T02).</li>'
            '<li>Milli hesabların real vaxt vintajları — arxiv 2026-10-02-dən yığılır.</li></ul>')


SECTIONS = {"kpi": s_kpi, "alerts": s_alerts, "heatmap": s_heatmap, "top": s_top, "fan": s_fan, "brent": s_brent,
            "stress": s_stress, "measures_summary": s_measures_summary, "register": s_register, "contrib": s_contrib,
            "dist": s_dist, "indicators": s_indicators, "channels": s_channels, "hazards": s_hazards,
            "chronology": s_chronology, "stress_full": s_stress_full, "levers": s_levers, "measures": s_measures,
            "residual": s_residual, "backtest": s_backtest, "feeds": s_feeds, "method": s_method}


def roles() -> pd.DataFrame:
    return pd.read_csv(config.INPUT / "rollar.csv")


ASSETS = config.SITE / "assets"

LEAD = {
    "rehberlik": ("Növbəti il üçün əsas iqtisadi risklər, onların ehtimalı və təsiri, aktiv xəbərdarlıqlar və risk "
                  "azaldıcı tədbirlərin icra vəziyyəti. Rəqəmlər makro (§15.5.1) və mikro (§15.5.2) modellərin baza yolu "
                  "ətrafında, canlı bazar məlumatı ilə şərtləndirilmiş birgə simulyasiyadan gəlir."),
    "analitik": ("Rəhbərlik icmalının bütün bölmələri və onların əsası: tam risk reyestri, töhfə bölgüsü, kvantillər, "
                 "göstərici bazası, ötürmə kanalları, təbii təhlükələr, stress ssenarilərinin yolları, tədbirlər "
                 "reyestri, qalıq risk, geriyə doğru sınaq və məlumat axınlarının vəziyyəti."),
}


PANEL_CTA = ('<div class="panel-cta"><p><strong>İş paneli</strong> — interaktiv qərar dəstəyi: risk reyestri və drill-down, canlı monitor, VaR/CaR, miqyaslanma, stress testləri, tədbirlərin optimallaşdırılması və hesabat qurucusu.</p><a class="btn-panel" href="../panel/index.html">İş panelini aç →</a></div>')


def _nav(role: str, sections: list[tuple[str, str]], for_print: bool) -> str:
    pages = [("index.html", "rehberlik"), ("analitik.html", "analitik")]
    lis = []
    for href, r in pages:
        cur = ' class="current"' if r == role else ""
        sub = ""
        if r == role:
            sub = '<ul class="nav-sections">' + "".join(
                f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in sections) + "</ul>"
        lis.append(f'<li><a{cur} href="{href}">{ROLE_TITLE[r]}</a>{sub}</li>')
    groups = [("Panellər (§15.5.3)", "".join(lis)),
              ("Hesabatlar", "".join(f'<li><a href="../reports/risk_hesabati_{r}.{ext}">{ROLE_TITLE[r]} — {ext.upper()}</a></li>'
                                     for r in ("rehberlik", "analitik") for ext in ("pdf", "xlsx"))),
              ("Sənədlər", '<li><a href="../docs/Risk_Metodologiyasi.md">Metodologiya</a></li>'
                           '<li><a href="../output/risk_api.json">JSON API (MİİS)</a></li>'
                           '<li><a href="../README.md">README</a></li>'),
              ("Əlaqəli modullar", '<li><a href="../../1551_v3/index.html">§15.5.1 Makroiqtisadi model</a></li>'
                                   '<li><a href="../../MicroUnit/site/index.html">§15.5.2 Mikroiqtisadi təhlil</a></li>')]
    html = "".join(f'<div class="nav-group"><span class="nav-title">{esc(t)}</span><ul>{u}</ul></div>' for t, u in groups)
    if not for_print:                                   # interactive decision-support panel (RiskUnit/panel)
        html = ('<div class="nav-group nav-panel"><span class="nav-title">İnteraktiv</span><ul>'
                '<li><a href="../panel/index.html">İş paneli →</a></li></ul></div>') + html
    return html


def build_html(c: dict, role: str, for_print: bool = False) -> str:
    R = roles()
    secs = R[R[role] == 1]
    body, toc = [], []
    for k, r in enumerate(secs.itertuples(), 1):
        fn = SECTIONS[r.bolme]
        html_part = fn(c, n=10) if (r.bolme == "top" and role == "rehberlik") else fn(c)
        body.append(f'<h2 id="{r.bolme}"><a class="anchor" href="#{r.bolme}" aria-hidden="true">#</a>'
                    f'<span class="section-num">{k}</span>{esc(r.ad)}</h2>\n{html_part}')
        toc.append((r.bolme, r.ad))
    fresh = c["feed_status"]
    res = c["res"]
    kicker = (f'MİİS §15.5.3 · vəziyyət {esc(c["live"]["as_of"])} · qiymətləndirmə ili {res.score_year} · '
              f'baza <code>{esc(c["baseline_id"])}</code> · {len(fresh)} məlumat axını, ən köhnə son müşahidə '
              f'{int(fresh["age_days"].max())} gün')
    page_css = "@page{size:A4 landscape;margin:10mm}" if role == "analitik" else "@page{size:A4;margin:12mm}"
    if for_print:
        css = (f"<style>{(ASSETS / 'base.css').read_text(encoding='utf-8')}\n{RISK_CSS}\n{page_css}</style>")
        sprite, menu, script = "", "", ""
    else:
        css = ('<link rel="stylesheet" href="assets/base.css">\n<link rel="stylesheet" href="assets/risk.css">'
               f"<style>{page_css}</style>")
        sprite = (ASSETS / "icons.svg").read_text(encoding="utf-8").strip()
        menu = ('<a class="skip" href="#main">Məzmuna keç</a>\n<button class="menu-button" id="menu-button" '
                'aria-expanded="false" aria-controls="sidebar"><svg class="icon" aria-hidden="true">'
                '<use href="#icon-menu"/></svg>Mündəricat</button>')
        script = '<script src="assets/site.js"></script>'
    footer = ('<footer class="site-footer">'
              f'<span class="stamp-row">MİİS §15.5.3 · yığılıb {esc(c["live"]["as_of"])} · baza <code>{esc(c["baseline_id"])}</code></span>'
              '<span class="stamp-row">Mənbələr: makro model §15.5.1 (<code>outputs/forecast_long.csv</code>), mikro bölmə §15.5.2 '
              '(FR1, FR10, FR12), FRED, Caldara–Iacoviello GPR, Baker–Bloom–Davis EPU, USGS ComCat, ERA5 (Open-Meteo).</span>'
              '<span class="stamp-row">Panel <code>python3 run_all.py</code> ilə yenidən qurulur; əl ilə redaktə edilmir.</span>'
              '</footer>')
    return f"""<!doctype html>
<html lang="az">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{ROLE_TITLE[role]} — MİİS §15.5.3</title>
<meta name="robots" content="noindex,nofollow">
{css}
</head>
<body>
{sprite}
{menu}
<div class="shell">
<nav class="sidebar" id="sidebar" aria-label="Panelin bölmələri">
  <div class="sidebar-head">
    <a class="mark" href="index.html">MİİS §15.5.3
      <span class="mark-sub">İqtisadi risklərin idarəedilməsi və qərar dəstəyi</span></a>
  </div>
  {_nav(role, toc, for_print)}
</nav>
<main class="content" id="main">
<h1>İqtisadi risklər — {ROLE_TITLE[role]}</h1>
<p class="page-kicker">{kicker}</p>
<p class="lead-in">{LEAD[role]}</p>
{"" if for_print else PANEL_CTA}
{chr(10).join(body)}
{footer}
</main>
</div>
{script}
</body>
</html>
"""


# ---------------------------------------------------------------- exports
def find_chrome() -> str | None:
    for p in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"):
        if Path(p).exists():
            return p
    for name in ("google-chrome", "chromium", "chromium-browser", "msedge"):
        if shutil.which(name):
            return shutil.which(name)
    return None


def write_pdf(html_text: str, out: Path) -> bool:
    chrome = find_chrome()
    tmp = out.with_suffix(".print.html")
    tmp.write_text(html_text, encoding="utf-8")
    if not chrome:
        return False
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out}",
           "--virtual-time-budget=3000", tmp.resolve().as_uri()]
    r = subprocess.run(cmd, capture_output=True, timeout=180)
    tmp.unlink(missing_ok=True)
    return r.returncode == 0 and out.exists()


def write_xlsx(c: dict, role: str, out: Path) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    S = c["S"]
    res = c["res"]
    j = res.col(res.score_year)
    g = res.total("g")[:, j]
    summary = pd.DataFrame([
        ("Vəziyyət tarixi", c["live"]["as_of"]), ("Qiymətləndirmə ili", res.score_year), ("Baza identifikatoru", c["baseline_id"]),
        ("Yüksək prioritetli risklər", int((S["prioritet"] == "yüksək").sum())),
        ("Qeyri-neft artımı — median, %", round(float(np.median(g)), 2)),
        ("Qeyri-neft artımı — P10 (GaR), %", round(float(np.quantile(g, 0.10)), 2)),
        ("Qeyri-neft artımı — makro baza, %", round(float(res.base["g"][j]), 2)),
        (f"P(qeyri-neft artımı < {c['p']['nonoil_gar_threshold']}%)", round(float((g < c["p"]["nonoil_gar_threshold"]).mean()), 3)),
        ("Brent — son müşahidə, USD", round(c["live"]["brent_last"], 2)),
        ("Aktiv xəbərdarlıqlar", len(c["alerts"]))], columns=["Göstərici", "Dəyər"])
    top = S[["sira", "risk_id", "ad", "aile", "ehtimal", "tesir_g", "tesir_cpi", "tesir_fis", "P_bal", "I_bal", "I_olcu",
             "skor", "prioritet", "sahib"]].copy()
    top.columns = ["Sıra", "ID", "Risk", "Ailə", "Ehtimal", "Təsir qeyri-neft f.b.", "Təsir inflyasiya f.b.",
                   "Təsir büdcə % ÜDM", "P", "T", "Ölçü", "Skor", "Prioritet", "Sahib"]
    heat = pd.DataFrame([[";".join(S[(S["P_bal"] == pb) & (S["I_bal"] == ib)]["risk_id"]) for ib in range(1, 6)]
                         for pb in range(5, 0, -1)], index=[f"P={k}" for k in range(5, 0, -1)],
                        columns=[f"T={k}" for k in range(1, 6)]).reset_index().rename(columns={"index": "Ehtimal \\ Təsir"})
    sheets = {"İcmal": summary, "Xəbərdarlıqlar": c["alerts"], "Risk xəritəsi": heat, "Prioritet risklər": top,
              "Tədbirlər (xülasə)": c["coverage"]}
    if role == "analitik":
        sheets.update({"Risk reyestri": S, "Paylanmalar": c["dist"], "Töhfələr": c["contrib_g"],
                       "Göstəricilər": c["indicators"],
                       "Ötürmə kanalları": pd.read_csv(config.OUTPUT / "FR1_transmission_channels.csv"),
                       "Stress ssenariləri": c["stress"], "Alətlər": c["levers"], "Tədbirlər reyestri": c["measures"],
                       "Qalıq risk": c["residual"], "Geriyə sınaq": c["bt_table"], "Kalibrləmə": c["calibration"],
                       "Məlumat axınları": c["feed_status"], "Hadisələr": c["chronology"],
                       "Tarixi analoqlar": pd.read_csv(config.OUTPUT / "FR3_historical_analogues.csv")})
    fill = {"yüksək": "F6D4CB", "orta": "F8E7C2", "aşağı": "E2EFE6"}
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name[:31], index=False)
            ws = xw.sheets[name[:31]]
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="0F6B6B")
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            for k, col in enumerate(df.columns, 1):
                width = min(60, max(10, int(df[col].astype(str).str.len().quantile(0.9) if len(df) else 10) + 2, len(str(col)) + 2))
                ws.column_dimensions[get_column_letter(k)].width = width
            ws.freeze_panes = "A2"
            if "Prioritet" in df.columns or "prioritet" in df.columns:
                pc = list(df.columns).index("Prioritet" if "Prioritet" in df.columns else "prioritet") + 1
                for row in ws.iter_rows(min_row=2, min_col=pc, max_col=pc):
                    for cell in row:
                        if cell.value in fill:
                            cell.fill = PatternFill("solid", fgColor=fill[cell.value])
            if name == "Risk xəritəsi":
                for i, pb in enumerate(range(5, 0, -1), start=2):
                    for k, ib in enumerate(range(1, 6), start=2):
                        sc = pb * ib
                        lvl = "yüksək" if sc >= c["p"]["score_high"] else ("orta" if sc >= c["p"]["score_medium"] else "aşağı")
                        ws.cell(row=i, column=k).fill = PatternFill("solid", fgColor=fill[lvl])


def write_api(c: dict) -> Path:
    """Machine-readable feed in the TT §3.5 data model: Indicator Time Series, Scenario,
    Forecast Result, Risk Register, Policy Measure, plus alerts and backtest status."""
    res = c["res"]
    D = c["dist"]
    unit = {"g": "%", "cpi": "%", "fis": "% ÜDM", "brent": "USD/barel"}
    fr = []
    for r in D.itertuples():
        fr.append({"forecast_id": f"RISK-{c['live']['as_of']}-{r.gosterici}-{r.il}", "model_id": "MIIS-15.5.3-MC",
                   "indicator_code": r.gosterici, "scenario_id": "RISK-DIST", "horizon": int(r.il) - config.as_of().year,
                   "period": int(r.il), "value": round(float(r.p50), 4), "unit": unit[r.gosterici],
                   "confidence_interval": {"p05": round(float(r.p05), 4), "p10": round(float(r.p10), 4),
                                           "p90": round(float(r.p90), 4), "p95": round(float(r.p95), 4)},
                   "baseline_value": round(float(r.baza), 4), "baseline_id": c["baseline_id"]})
    st = c["stress"]
    scen = [{"scenario_id": "RISK-DIST", "type": "stoxastik", "assumptions": "birgə Monte Karlo, canlı məlumatla şərtləndirilmiş",
             "parameters": {"n": res.meta["n"], "seed": res.meta["seed"]}, "author": "risk bölməsi"}]
    for sid, g in st.groupby("ssenari"):
        scen.append({"scenario_id": sid, "type": "stress", "name": g["ad"].iloc[0], "assumptions": g["sok_vektoru"].iloc[0],
                     "results": [{"indicator": r.gosterici, "period": int(r.il), "deviation": round(float(r.sapma), 4),
                                  "deviation_with_measure": round(float(r.sapma_tedbirle), 4)} for r in g.itertuples()],
                     "author": "risk bölməsi"})
    ind = [{"indicator_code": r.gosterici, "name": r.ad, "unit": r.vahid, "frequency": r.tezlik, "source": r.menbe,
            "family": r.aile, "last_period": str(r.son_tarix), "last_value": None if pd.isna(r.son_deyer) else float(r.son_deyer),
            "status": r.status} for r in c["indicators"].itertuples()]
    reg = json.loads(c["S"].to_json(orient="records", force_ascii=False))
    meas = json.loads(c["measures"].drop(columns=["status_w"]).to_json(orient="records", force_ascii=False))
    api = {"meta": {"module": "MİİS §15.5.3", "as_of": c["live"]["as_of"], "score_year": res.score_year,
                    "baseline_id": c["baseline_id"], "schema": "TT §3.5: Indicator Time Series, Scenario, Forecast Result, Risk Register, Policy Measure"},
           "indicator_time_series": ind, "scenario": scen, "forecast_result": fr, "risk_register": reg,
           "policy_measure": meas, "alerts": json.loads(c["alerts"].to_json(orient="records", force_ascii=False)),
           "backtest": json.loads(c["bt_table"].to_json(orient="records", force_ascii=False))}
    out = config.OUTPUT / "risk_api.json"
    out.write_text(json.dumps(api, ensure_ascii=False, indent=1, sort_keys=True, default=str), encoding="utf-8")
    return out


def build_all(c: dict, pdf: bool = True) -> dict:
    out = {}
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "risk.css").write_text(RISK_CSS, encoding="utf-8")
    for role, fname in (("rehberlik", "index.html"), ("analitik", "analitik.html")):
        p = config.SITE / fname
        p.write_text(build_html(c, role), encoding="utf-8")
        out[f"html_{role}"] = p
        x = config.REPORTS / f"risk_hesabati_{role}.xlsx"
        write_xlsx(c, role, x)
        out[f"xlsx_{role}"] = x
        if pdf:
            f = config.REPORTS / f"risk_hesabati_{role}.pdf"
            out[f"pdf_{role}"] = f if write_pdf(build_html(c, role, for_print=True), f) else None
    out["api"] = write_api(c)
    return out
