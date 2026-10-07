"""FR1 v2.2 tables (§7.3 scenarios, §7.4 results and path, §7.5 bands, §7.6 multipliers, §8.4 accounts), EN and AZ."""
from .common import num, plan_fmt, pm
from .fr1 import EXP, SCEN, FY, sp

SCEN_TPL = {"en": """| Driver | Baseline | Adverse | Reform |
|---|---|---|---|
| Brent by 2030 | ~66 USD/bbl | ~48 | ~80 |
| Oil output 2027–30 (v2.2) | Ministry plan growth: {OIL}% | pre-v2.2 Baseline decline: −4.2, −3.8, −3.5, −3.0% | plan + 1.2, 0.8, 0.5, 0 pp |
| Gas output 2027–30 (v2.2) | Ministry plan growth: {GAS}% | plan − 1 pp | plan + 3 pp |
| State Investment Programme 2026 | {SIP} mln AZN (approved) | same | same |
| Gas export price | → 300 USD/kcm | 230 | 380 |
| Public investment (policy level, real) | +1.5% p.a. | −4% p.a. | +5% p.a. |
| Policy / deposit rate | easing | tightening | easing |
| Exchange rate | 1.70 | 1.70 | 1.70 |
| External demand | +3% p.a. | +0.5% p.a. | +5% p.a. |
| Non-oil TFP | trend | trend | +0.4 log points a year from 2027 on every sector with a TFP/trend term (agr, man, elc, wat, tou, tra, ict, oth) — now actually applied by the solver |""",
            "az": """| Amil | Əsas | Mənfi | İslahat |
|---|---|---|---|
| 2030-cu ilədək Brent | ~66 USD/barel | ~48 | ~80 |
| Neft hasilatı 2027–30 (v2.2) | Nazirliyin planının artımı: {OIL}% | v2.2-dən əvvəlki Əsas ssenarinin azalması: −4.2, −3.8, −3.5, −3.0% | plan + 1.2, 0.8, 0.5, 0 f.b. |
| Qaz hasilatı 2027–30 (v2.2) | Nazirliyin planının artımı: {GAS}% | plan − 1 f.b. | plan + 3 f.b. |
| Dövlət İnvestisiya Proqramı 2026 | {SIP} mln AZN (təsdiq edilmiş) | eyni | eyni |
| Qazın ixrac qiyməti | → 300 USD/min kub metr | 230 | 380 |
| Dövlət investisiyası (siyasət səviyyəsi, real) | illik +1.5% | illik −4% | illik +5% |
| Uçot / depozit faiz dərəcəsi | yumşalma | sərtləşmə | yumşalma |
| Məzənnə | 1.70 | 1.70 | 1.70 |
| Xarici tələb | illik +3% | illik +0.5% | illik +5% |
| Qeyri-neft TFP | trend | trend | 2027-ci ildən etibarən TFP/trend termini olan hər sektor üzrə ildə +0.4 loqarifmik bənd (agr, man, elc, wat, tou, tra, ict, oth) — indi həlledici tərəfindən faktiki olaraq tətbiq olunur |"""}


def scen_table(F, lang):
    yrs = [2027, 2028, 2029, 2030]
    fmt = lambda k: ", ".join(plan_fmt(F.plan_g[k][y]) for y in yrs)
    return SCEN_TPL[lang].format(OIL=fmt("oil"), GAS=fmt("gas"), SIP=sp(F.sip))


RES_LAB = {"en": ["| | Baseline | Adverse | Reform |", "Real GDP growth, avg % p.a. 2026–30", "v2 (2026-10-05) 2.56; first round 1.34; original 1.23",
                  "Real non-oil GDP growth, avg % p.a.", "v2 (2026-10-05) 4.18; first round 2.68; original 2.35", "CPI inflation 2030, %",
                  "Unemployment 2030, %", "Budget balance 2030, % of GDP", "Public debt 2030, % of GDP",
                  "Hydrocarbon share of value added 2030, %", "Nominal GDP 2030, bn AZN",
                  "Non-oil budget balance 2030, % of non-oil GDP (v2.2)"],
           "az": ["| | Əsas | Mənfi | İslahat |", "Real ÜDM artımı, orta illik %, 2026–30", "v2 (2026-10-05) 2.56; birinci raund 1.34; ilkin versiya 1.23",
                  "Real qeyri-neft ÜDM artımı, orta illik %", "v2 (2026-10-05) 4.18; birinci raund 2.68; ilkin versiya 2.35", "İQİ inflyasiyası 2030, %",
                  "İşsizlik 2030, %", "Büdcə balansı 2030, ÜDM-ə nisbətən %", "Dövlət borcu 2030, ÜDM-ə nisbətən %",
                  "Əlavə dəyərdə karbohidrogenlərin payı 2030, %", "Nominal ÜDM 2030, mlrd AZN",
                  "Qeyri-neft büdcə balansı 2030, qeyri-neft ÜDM-ə nisbətən % (v2.2)"]}


def results_table(F, lang):
    L = RES_LAB[lang] + (["this run", "earlier versions"] if lang == "en" else ["cari icra", "əvvəlki versiyalar"])
    v21, v22 = F.ref["v21"], F.ref["v22"]
    c = {s: F.fc[s].loc[2030] for s in SCEN}
    row = lambda lab, f: f"| {lab} | " + " | ".join(f(s) for s in SCEN) + " |"
    g, n = F.avg_rgdp, F.avg_non
    out = [L[0], "|---|---|---|---|",
           f"| {L[1]} | **{g['Baseline']:.2f}** ({L[-2]}; {L[-1]}: v2.2 {v22['avg_growth_rgdp']['Baseline']:.2f}, v2.1 {v21['avg_growth_rgdp']['Baseline']:.2f}, {L[2]}) | {g['Adverse']:.2f} | {g['Reform']:.2f} |",
           f"| {L[3]} | **{n['Baseline']:.2f}** ({L[-2]}; {L[-1]}: v2.2 {v22['avg_growth_rgdpnon']['Baseline']:.2f}, v2.1 {v21['avg_growth_rgdpnon']['Baseline']:.2f}, {L[4]}) | {n['Adverse']:.2f} | {n['Reform']:.2f} |",
           row(L[5], lambda s: f"{c[s].infl:.2f}"), row(L[6], lambda s: f"{c[s].unemp:.2f}"),
           row(L[7], lambda s: pm(c[s].balance_n / c[s].gdp_n * 100)), row(L[8], lambda s: num(c[s].debt_azn / c[s].gdp_n * 100)),
           row(L[9], lambda s: num(F.hc30[s])), row(L[10], lambda s: num(c[s].gdp_n / 1000, 0)),
           row(L[11], lambda s: num(c[s].nobd_pct))]
    return "\n".join(out)


def path_table(F, lang):
    from ._fr1_en import PATH_ROWS
    head = "Baseline path, % growth (v2.3):" if lang == "en" else "Əsas ssenari trayektoriyası, artım %-lə (v2.3):"
    out = [head, "", "| | " + " | ".join(map(str, FY)) + " |", "|---|---|---|---|---|---|"]
    for k, en, az in PATH_ROWS:
        out.append(f"| {en if lang == 'en' else az} | " + " | ".join(num(v, 2) for v in F.g(k)) + " |")
    return "\n".join(out)


def band_table(F, lang):
    from ._fr1_en import BAND_ROWS, band_err
    out = ["| 2030, baseline | 5–95% band (% of median) | 25–75% | hold-out 5-year error |" if lang == "en" else
           "| 2030, Əsas | 5–95% zolağı (medianın %-i) | 25–75% | nümunədən kənar yoxlamanın 5 illik xətası |", "|---|---|---|---|"]
    for k, en, az in BAND_ROWS:
        w1, w2 = F.band[k]
        out.append(f"| {en if lang == 'en' else az} | {w1:.1f} | {w2:.1f} | {pm(band_err(F, k), 1)}% |")
    return "\n".join(out)


def mult_table(F, lang):
    from ._fr1_en import MULT_ROWS
    out = ["| | Brent +10 USD/bbl | Public investment +1 bn AZN | Credit easing (estimated) | Credit easing + judgemental overlay | External demand +10% |"
           if lang == "en" else
           "| | Brent +10 USD/barel | Dövlət investisiyası +1 mlrd AZN | Kredit şərtlərinin yumşaldılması (qiymətləndirilmiş) | Kredit şərtlərinin yumşaldılması + ekspert mülahizəsinə əsaslanan əlavə (overlay) | Xarici tələb +10% |",
           "|---|---|---|---|---|---|"]
    for k, en, az in MULT_ROWS:
        out.append(f"| {en if lang == 'en' else az} | " + " | ".join(pm(F.mult(e, k)) for e in EXP) + " |")
    return "\n".join(out)


ACC_AZ = {"GDP at market prices": "**ÜDM**", "Non-oil GDP": "**Qeyri-neft ÜDM**", "Oil and gas GDP": "Neft-qaz ÜDM",
          "Tourism & catering": "Turizm və ictimai iaşə", "Information & communication": "İnformasiya və rabitə",
          "Manufacturing": "Emal sənayesi", "Transport & storage": "Nəqliyyat və anbar təsərrüfatı",
          "Water supply & waste": "Su təchizatı və tullantıların emalı", "Trade & vehicle repair": "Ticarət və nəqliyyat vasitələrinin təmiri",
          "Net taxes on products": "Məhsula xalis vergilər", "Agriculture, forestry & fishing": "Kənd təsərrüfatı",
          "Electricity, gas & steam": "Elektrik enerjisi, qaz və buxar", "Social & other services": "Sosial və digər xidmətlər",
          "Construction": "Tikinti", "Mining & quarrying": "Mədənçıxarma"}
ACC_EN = {"GDP at market prices": "**GDP**", "Non-oil GDP": "**Non-oil GDP**", "Tourism & catering": "**Tourism & catering**",
          "Agriculture, forestry & fishing": "Agriculture"}


def acc_table(F, lang):
    from ._fr1_en import acc_rows
    if lang == "en":
        out = ["| | Real growth<br>% p.a. | Deflator infl.<br>% p.a. | Nominal growth<br>cum. % | Nominal 2030<br>mln AZN |", "|---|---|---|---|---|"]
    else:
        out = ["| | Real artım<br>illik % | Deflyator inflyasiyası<br>illik % | Nominal artım<br>kumulyativ % | Nominal 2030<br>mln AZN |", "|---|---|---|---|---|"]
    for e in acc_rows(F):
        r = F.ACC.loc[e]
        if lang == "en":
            rg = f"{r.real_growth_avg_pct:+.1f}".replace("-", "−")
            rg = f"**{rg}**" if e == "Tourism & catering" else rg
            out.append(f"| {ACC_EN.get(e, e)} | {rg} | {r.deflator_infl_avg_pct:+.1f} | "
                       f"{r.nominal_growth_cum_pct:+.1f} | {r.nominal_2030:,.0f} |".replace("+-", "−").replace("| -", "| −"))
        else:
            rg = f"{r.real_growth_avg_pct:+.1f}"
            rg = f"**{rg}**" if e == "Tourism & catering" else rg
            out.append(f"| {ACC_AZ[e]} |" + f" {rg} | {r.deflator_infl_avg_pct:+.1f} | {r.nominal_growth_cum_pct:+.1f} | "
                       f"{r.nominal_2030:,.0f} |".replace(",", " ").replace("-", "−"))
    return "\n".join(out)
