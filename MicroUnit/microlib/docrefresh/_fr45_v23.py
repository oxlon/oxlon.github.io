"""FR4 / FR5 v2.3 notes (2026-10-05): the add-factor decay sensitivity uses a FIXED half-life, not an estimated residual rho.

The 'after' figures are read from this run's FR4_sensitivity_levers.csv / FR5_sensitivity_levers.csv; the v2.2 'before'
figures (decay at the estimated residual rho) are frozen below (from the output/ snapshot taken before the v2.3 run).
Markers: AUTO:fr4v23_note (FR4: must not start with a tag FR4.ipynb matches as a prefix) and AUTO:v23_note (FR5).
"""
from .common import RefreshError, az, azpm, csv, pm

# v2.2 decay-at-rho sensitivity, 2030 Baseline (FR4: thousand persons, difference and %; FR5: volume, million manat 2015)
FR4_V22 = {"rho": {"E6 employed": 0.847, "E6 hired": 0.629, "E8": 0.524},
           "diff": {"state": (14.2, 1.44), "budget": (4.5, 0.79), "market_services": (-11.4, -2.09), "services": (0.0, 0.0)}}
FR5_V22 = {"rho_e1": 0.59, "diff": -483.2, "diff_pct": -4.44}
Q_EN = {"state": "state employment", "budget": "budget organisations", "market_services": "market services",
        "services": "services (total)"}
Q_AZ = {"state": "dövlət sektorunda məşğulluq", "budget": "büdcə təşkilatları", "market_services": "bazar xidmətləri",
        "services": "xidmətlər (cəmi)"}


def _hl(label):
    import re
    m = re.search(r"half-life ([0-9.]+) year", label)
    if not m:
        raise RefreshError(f"decay lever label without a half-life: {label!r}")
    return float(m.group(1))


def _sg(v, d):
    return num0(d) if round(float(v), d) == 0 else pm(v, d)


def _sga(v, d):
    return num0(d).replace(".", ",") if round(float(v), d) == 0 else azpm(v, d)


def num0(d):
    return "0." + "0" * d


def fr4_v23():
    L = csv("FR4_sensitivity_levers.csv")
    D = L[L.lever.str.startswith("SENSITIVITY ONLY: add-factors decay")]
    if D.empty:
        raise RefreshError("FR4_sensitivity_levers.csv: no add-factor decay row")
    hl = _hl(D.lever.iloc[0])
    R = FR4_V22["rho"]
    rows_en, rows_az = [], []
    for q in ("state", "budget", "market_services", "services"):
        r = D[D.quantity == q]
        if r.empty:
            raise RefreshError(f"FR4 decay row lacks {q}")
        r = r.iloc[0]; b = FR4_V22["diff"][q]
        rows_en.append(f"| {Q_EN[q]} | {_sg(b[0], 1)} ({_sg(b[1], 2)}%) | {_sg(r.difference, 1)} ({_sg(r.difference_pct, 2)}%) |")
        rows_az.append(f"| {Q_AZ[q]} | {_sga(b[0], 1)} ({_sga(b[1], 2)}%) | {_sga(r.difference, 1)} ({_sga(r.difference_pct, 2)}%) |")
    f = 0.5 ** (1 / hl)
    en = f"""## 18. v2.3 (2026-10-05) — add-factor decay with a fixed half-life (no estimated residual AR)

The client's constraint excludes any estimated residual-AR process. Up to v2.2 the Part 18 sensitivity "add-factors decay" let
the E6 bloc-split and E8 state-share add-factors fade at each equation's estimated first-order residual autocorrelation ρ̂
(E6 employed {R['E6 employed']:.2f}, hired {R['E6 hired']:.2f}; E8 {R['E8']:.2f}) — an estimated AR(1) coefficient inside a scenario path. From v2.3 the
decay is **fixed, not estimated**: the add-factor is multiplied by 0.5^(h/H), h = years after the anchor year (2024), with
half-life **H = {hl:g} year** ({f:.2f} a year) — the project's partial-year (nowcast) rule, as in FR1 and FR3. H is an engine lever
(`addfactor_half_life`, 0.25–10 years; it acts only with `addfactor_decay` on). ρ̂ remains a reported diagnostic (beside DW and
BG) and enters no forecast, scenario or sensitivity path; `FR4_add_factors.csv` lists the half-life and the yearly factor instead.
The Baseline, Adverse and Reform scenarios keep constant add-factors and are unchanged. Decay sensitivity, 2030 vs Baseline
(thousand persons):

| quantity | v2.2: decay at ρ̂ | v2.3: half-life {hl:g} year |
|---|---|---|
{chr(10).join(rows_en)}""" + (("\n\nThe fixed decay is faster than ρ̂, so more of E6's 2024 add-factor is gone by 2030 and market services move "
           "further; the state-share effect hardly changes (E8's ρ̂ was close to 0.5).") if f < min(R.values()) else "")
    azt = f"""## 18. v2.3 (2026-10-05) — düzəliş əmsallarının sabit yarımsönmə dövrü ilə sönməsi (qalıq AR qiymətləndirilmir)

Müştərinin tələbi qiymətləndirilmiş qalıq-AR prosesini istisna edir. v2.2-yə qədər Hissə 18-in "düzəliş əmsallarının sönməsi"
həssaslıq variantında E6 (blok bölgüsü) və E8 (dövlət payı) düzəlişləri hər tənliyin qiymətləndirilmiş birinci tərtib qalıq
avtokorrelyasiyası ρ̂ sürəti ilə sönürdü (E6 məşğul {az(R['E6 employed'])}, muzdlu {az(R['E6 hired'])}; E8 {az(R['E8'])}). v2.3-dən sönmə **sabitdir,
qiymətləndirilmir**: düzəliş 0,5^(h/H) ilə vurulur (h — lövbər ilindən, 2024, sonrakı illər), yarımsönmə dövrü **H = {az(hl, 0) if hl == int(hl) else az(hl)} il**
(ildə {az(f)}) — FR1 və FR3-dəki kimi layihənin natamam il qaydası. H mühərrikdə rıçaqdır (`addfactor_half_life`, 0,25–10 il;
yalnız `addfactor_decay` açıq olduqda təsir edir). ρ̂ yalnız diaqnostika kimi (DW və BG ilə yanaşı) göstərilir, heç bir proqnoz,
ssenari və ya həssaslıq yolunda istifadə olunmur; `FR4_add_factors.csv` ρ̂ əvəzinə yarımsönmə dövrünü və illik əmsalı verir.
Əsas, Mənfi və İslahat ssenariləri sabit düzəlişlərlə qalır və dəyişmir. Sönmə həssaslığı, 2030, Əsas ssenariyə nisbətən (min nəfər):

| kəmiyyət | v2.2: ρ̂ ilə sönmə | v2.3: yarımsönmə {az(hl, 0) if hl == int(hl) else az(hl)} il |
|---|---|---|
{chr(10).join(rows_az)}""" + (("\n\nSabit sönmə ρ̂-dən sürətlidir: 2030-a qədər E6-nın 2024 düzəlişinin daha çox hissəsi aradan qalxır və bazar "
           "xidmətləri daha çox dəyişir; dövlət payına təsir az dəyişir (E8-in ρ̂-su 0,5-ə yaxın idi).") if f < min(R.values()) else "")
    return en, azt


def fr5_v23():
    L = csv("FR5_sensitivity_levers.csv", index_col=0)
    D = L[L.index.str.startswith("add-factors decay")]
    if D.empty:
        raise RefreshError("FR5_sensitivity_levers.csv: no add-factor decay row")
    hl = _hl(D.index[0]); r = D.iloc[0]; f = 0.5 ** (1 / hl); B = FR5_V22
    hla = az(hl, 0) if hl == int(hl) else az(hl)
    en = f"""## v2.3 (2026-10-05): add-factor decay with a fixed half-life (no estimated residual AR)

Up to v2.2 the Part 17 sensitivity "add-factors decay" let the 2025 add-factors of E1, the share equations and the two splits fade
at each equation's estimated first-order residual autocorrelation ρ̂ (E1 ρ̂ = {B['rho_e1']:.2f}) — an estimated AR(1) coefficient inside
a scenario path, which the client's constraint excludes. From v2.3 the decay is **fixed, not estimated**: 0.5^(h/H), h = years
after 2025, half-life **H = {hl:g} year** ({f:.2f} a year; the project's partial-year rule). H is the engine lever `addf_half_life`
(0.25–10 years, active only with `addf_decay`). ρ̂ is still reported as a diagnostic only. The scenarios keep constant
add-factors and are unchanged. 2030 total volume under the decay sensitivity: {pm(r.diff_vs_baseline, 0)} million manat
({pm(r.diff_pct)}%) vs Baseline; v2.2 (decay at ρ̂): {pm(B['diff'], 0)} ({pm(B['diff_pct'])}%)."""
    azt = f"""## v2.3 (2026-10-05): düzəliş əmsallarının sabit yarımsönmə dövrü ilə sönməsi (qalıq AR qiymətləndirilmir)

v2.2-yə qədər Hissə 17-nin "düzəliş əmsallarının sönməsi" həssaslıq variantında E1-in, pay tənliklərinin və iki bölgünün 2025
düzəlişləri hər tənliyin qiymətləndirilmiş birinci tərtib qalıq avtokorrelyasiyası ρ̂ sürəti ilə sönürdü (E1 ρ̂ = {az(B['rho_e1'])}) — bu,
müştərinin tələbinin istisna etdiyi qiymətləndirilmiş AR(1) əmsalıdır. v2.3-dən sönmə **sabitdir, qiymətləndirilmir**: 0,5^(h/H),
h — 2025-dən sonrakı illər, yarımsönmə dövrü **H = {hla} il** (ildə {az(f)}; layihənin natamam il qaydası). H mühərrikdə
`addf_half_life` rıçağıdır (0,25–10 il, yalnız `addf_decay` açıq olduqda). ρ̂ yalnız diaqnostika kimi göstərilir. Ssenarilər sabit
düzəlişlərlə qalır və dəyişmir. Sönmə həssaslığında 2030 ümumi həcm Əsas ssenariyə nisbətən {azpm(r.diff_vs_baseline, 0)} mln manat
({azpm(r.diff_pct)}%); v2.2-də (ρ̂ ilə sönmə) {azpm(B['diff'], 0)} ({azpm(B['diff_pct'])}%)."""
    return en, azt
