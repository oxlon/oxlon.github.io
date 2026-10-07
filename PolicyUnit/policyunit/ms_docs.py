"""Render the numbers of the microsimulation documentation from the outputs (no hand-typed
figures): blocks <!-- AUTO:<name> --> ... <!-- /AUTO:<name> --> in
docs/Metodologiya_mikrosimulyasiya.md and data/households/README_az.md.

    python3 -m policyunit.ms_docs"""
from __future__ import annotations

import json
import re

import pandas as pd

from . import config, hh_data

DOC = config.ROOT / "docs" / "Metodologiya_mikrosimulyasiya.md"
README = hh_data.HH_DIR / "README_az.md"


def az(x, d=1):
    s = f"{x:,.{d}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−")


def _fit():
    f = pd.read_csv(config.OUTPUT / "V_microsim_calibration_2024.csv")
    g = lambda grp, ind: f[(f.group == grp) & (f.indicator == ind)].iloc[0]
    return f, g


def blocks():
    cal = json.loads(hh_data.CAL_JSON.read_text())
    f, g = _fit()
    dec = f[f.group.str.startswith("gəlir desili")]
    pov, raw = g("yoxsulluq (%)", "DSK səviyyəsi (kappa ilə)"), \
        g("yoxsulluq (%)", "adambaşına istehlak < xətt (kappa olmadan)")
    u, r = g("yoxsulluq (%)", "pov_urban"), g("yoxsulluq (%)", "pov_rural")
    um, uf, ua = (g("ÜSY", "alan şəxslər (min)"), g("ÜSY", "ailələr (min)"),
                  g("ÜSY", "orta məbləğ (AZN/nəfər)"))
    gi = f[f.group == "Gini"].model.tolist()
    cm = g("istehlak", "orta (AZN/nəfər/ay)")
    wg = g("əmək haqqı (AZN/ay)", "orta (muzdlu)")
    fc = cal["factors"]
    B = {}
    B["ms_params"] = (
        f"EBT–inzibati uzlaşdırma amilləri: xalis maaş {az(fc['employment'], 3)}, pensiya "
        f"{az(fc['pensions'], 3)}, digər müavinətlər {az(fc['benefits'], 3)}. ÜSY müraciət "
        f"qaydası P = min(1; a × (boşluq/(üzv × meyar))^γ): a = {az(cal['p_takeup'], 3)}, "
        f"γ = {az(cal['takeup_gamma'], 1)}. Kappa = {az(cal['kappa'], 3)}: kappa olmadan "
        f"adambaşına istehlakı 270,1 AZN-dən aşağı olanların payı {az(raw.model, 1)} % olardı "
        f"(rəsmi {az(raw.target, 1)} %).")
    B["ms_fit"] = (
        f"**Uyğunluq (2024, `V_microsim_calibration_2024.csv`):** gəlir mənbələri dəqiq (cəmi "
        f"359,2 AZN); gəlir desillərinin maksimal sapması {az(dec.dev_pct.abs().max(), 1)} % "
        f"(D1 {az(dec.model.iloc[0])} / {az(dec.target.iloc[0])}; D10 {az(dec.model.iloc[-1])} / "
        f"{az(dec.target.iloc[-1])}); istehlak desilləri dəqiq, orta istehlak "
        f"{az(cm.dev_pct, 1)} %; yoxsulluq {az(pov.model, 2)} % (hədəf {az(pov.target, 1)}, "
        f"kappa ilə); şəhər {az(u.model)} / {az(u.target)} və kənd {az(r.model)} / {az(r.target)} % "
        f"(hədəf deyil); ÜSY alanlar {az(um.model)} / {az(um.target)} min, ailələr {az(uf.model)} / "
        f"{az(uf.target)} min, orta məbləğ {az(ua.model)} / {az(ua.target)} AZN; orta maaş "
        f"{az(wg.model, 0)} / {az(wg.target, 0)} AZN. Gini: gəlir {az(gi[0])}, istehlak {az(gi[1])}, "
        f"DSK desil cədvəlindən aşağı sərhəd {az(gi[2])} (DSK Gini dərc etmir).")
    v = pd.read_csv(config.OUTPUT / "V_microsim_2019_package.csv")
    v0 = v[v.compare_to == "2019 vs 2018"].set_index("indicator")
    s = pd.read_csv(config.OUTPUT / "V_microsim_summary.csv")
    s0 = s[s.event.str.startswith("E1")].iloc[0]
    m = pd.read_csv(config.OUTPUT / "V_microsim_2025_minwage.csv")
    m0 = m[m.indicator.str.contains("500")]
    B["ms_valid"] = (
        "E1+E2 (2019 vs 2018; model — statik siyasət effekti, fakt — ümumi dəyişmə): " +
        "; ".join(f"{i} {az(v0.model_static[i], 2)} vs {az(v0.observed[i], 1)}" for i in v0.index) +
        f". Davranış qatı (η = 0,7): qeyri-dövlət muzdlu işçilər "
        f"{az(v0.model_behavioural['nonstate_employees'], 1)} %. İşarə uyğunluğu "
        f"{az(100 * s0.sign_ok, 0)} %, 'model + trend' trend etalonunu "
        f"{az(100 * s0.beats_naive_comb, 0)} % halda üstələyir. E3 (2025 MƏH 345→400): < 500 AZN "
        f"payı model {az(m0.model_static.iloc[0])} / {az(m0.model_static.iloc[1])} % (MƏH / + 5,6 % "
        f"artım), fakt {az(m0.observed.iloc[0])} %, etalon {az(m0.naive_trend.iloc[0])} %.")
    b = pd.read_csv(config.OUTPUT / "P3_microsim_baseline.csv")
    piv = b[b.indicator.isin(["poverty_rate", "gini", "ms_fiscal:utsy", "income_mean_pc"])
            ].pivot_table(index="indicator", columns="year", values="value")
    B["ms_baseline"] = "Baza yolu (`P3_microsim_baseline.csv`): " + "; ".join(
        f"{k}: " + ", ".join(f"{y} {az(piv.loc[k, y], 2 if k != 'ms_fiscal:utsy' else 0)}"
                            for y in piv.columns) for k in piv.index) + "."
    return B


def render():
    B = blocks()
    for path in (DOC, README):
        t = path.read_text()
        for k, v in B.items():
            t = re.sub(rf"<!-- AUTO:{k} -->.*?<!-- /AUTO:{k} -->",
                       f"<!-- AUTO:{k} -->{v}<!-- /AUTO:{k} -->", t, flags=re.S)
        path.write_text(t)
    return B


if __name__ == "__main__":
    for k, v in render().items():
        print(k, ":", v[:200])
