"""P3_ outputs of the microsimulation (FR3): example policies + every configured scenario that
uses the microsim engine (run together with the micro and io engines so that the macro/IO
linkage is active), baseline path 2024–2030.

    python3 -m policyunit.ms_outputs"""
from __future__ import annotations

import pandas as pd

from . import catalog, config, integrate
from . import eng_microsim as E
from .engine_base import OUT_COLS

OWNER = "microsim"
WM = "SİNTETİK — real ev təsərrüfatı məlumatı deyil. "
EXAMPLES = [  # id, name_az, instrument, size, target
    ("ex_mw20", "Minimum əmək haqqı +20 % (2026)", "min_wage", 20, None),
    ("ex_tsa30", "ÜSY ödənişləri +30 % (2026)", "tsa_benefit", 30, None),
    ("ex_need30", "ÜSY ehtiyac meyarı +30 % (2026)", "tsa_need", 30, None),
    ("ex_pens10", "Pensiyalar +10 % (2026)", "pension_index", 10, None),
    ("ex_pit_priv2", "Qeyri-neft özəl sektor gəlir vergisi ≤2500: +2 f.b. (3→5 %, 2026)",
     "pit_nonoil_private", 2, None),
    ("ex_pit_m2", "Gəlir vergisi bütün pillələr −2 f.b. (2026)", "pit_rate", -2, None),
    ("ex_vat_m2", "ƏDV −2 f.b. (2026)", "vat_rate", -2, None),
    ("ex_constr_jobs10", "Tikintidə formal iş yerləri +10 % (2026)", "sector_jobs", 10, "constr"),
]
HEAD = ["poverty_rate", "poverty_gap", "poverty_severity", "poverty_rate:need", "gini",
        "gini_cons", "income_mean_pc", "income_median_pc", "employment_hired",
        "employment_informal", "wage_nominal", "fiscal_cost"]


def example_scenarios(year=2026):
    return [{"id": i, "name_az": n, "description_az": n, "start_year": year, "tags": ["FR3"],
             "instruments": [{"instrument": ins, "years": [year], "size": sz, "target": tg,
                              "unit": "", "financing": None}]}
            for i, n, ins, sz, tg in EXAMPLES]


STATUS = []


def _run(s, linked):
    if linked:
        r = integrate.run_scenario(s, ["micro", "io", "microsim"])
        res = r["results"].get("microsim")
        st = r["status"].get("microsim", {})
    else:
        res, st = E.run(s, {}), {"status": "ok"}
    direct = all(it["instrument"] in E.DIRECT for it in s["instruments"])
    src = sorted({x for y in range(2024, 2031)
                  for x in E.ms_links.from_ctx({"results": r["results"]}, y)["source"]}
                 ) if linked else []
    STATUS.append({"scenario": s["id"], "scenario_name": s["name_az"],
                   "status": st.get("status", "yoxdur"),
                   "channel": "birbaşa alət (vergi-müavinət qaydası)" if direct else
                   ("əlaqə: " + "; ".join(src) if src else "əlaqə siqnalı yoxdur (dəyişiklik 0)"),
                   "rows": 0 if res is None else len(res.frame),
                   "message_az": st.get("message_az", "")})
    if res is None:
        return None
    f = res.frame.copy()
    f.insert(0, "scenario_name", s["name_az"])
    f.insert(0, "scenario", s["id"])
    return f


def baseline_path():
    rows = []
    s = {"id": "baseline", "name_az": "Baza", "start_year": 2024, "instruments": []}
    for y in E.YEARS:
        r = E.simulate(s, y, {})
        f = E.indicators(r, y, E.base()[2])
        rows.append(f[f.indicator.isin(HEAD) | f.indicator.str.startswith("ms_fiscal:")])
    f = pd.concat(rows, ignore_index=True)[["indicator", "label_az", "unit", "year", "baseline",
                                           "group", "note_az"]]
    return f.rename(columns={"baseline": "value"})


def write_all(log=print):
    from . import scenario as scn
    frames = []
    STATUS.clear()
    for s in example_scenarios():
        frames.append(_run(s, linked=False))
    for sid in scn.all_ids():                            # EVERY configured scenario, linked
        s = scn.load(sid)
        try:
            frames.append(_run(s, linked=True))
        except Exception as e:                           # noqa: BLE001
            STATUS.append({"scenario": sid, "scenario_name": s["name_az"], "status": "xəta",
                           "channel": "", "rows": 0, "message_az": f"{type(e).__name__}: {e}"})
    f = pd.concat([x for x in frames if x is not None], ignore_index=True)
    out = {}
    w = lambda df, nm, d: out.setdefault(nm, catalog.write_csv(df, nm, OWNER, WM + d))
    w(f, "P3_microsim_indicators.csv", "Mikrosimulyasiya: bütün göstəricilər (ssenari × il × "
      "qrup; tidy OUT_COLS)")
    h = f[f.indicator.isin(HEAD)].pivot_table(index=["scenario", "scenario_name", "year"],
                                              columns="indicator", values="delta").reset_index()
    w(h, "P3_microsim_headline.csv", "Mikrosimulyasiya: əsas göstəricilərin bazadan fərqi "
      "(yoxsulluq f.b., Gini bənd, gəlir AZN, məşğulluq min nəfər, fiskal mln AZN)")
    d = f[f.indicator.isin(["income_decile_pc", "winners_share", "losers_share"])]
    d = d.pivot_table(index=["scenario", "year", "group"], columns="indicator",
                      values=["baseline", "value", "delta_pct"]).reset_index()
    d.columns = ["_".join(c).strip("_") for c in d.columns]
    keep = ["scenario", "year", "group", "baseline_income_decile_pc", "value_income_decile_pc",
            "delta_pct_income_decile_pc", "value_winners_share", "value_losers_share"]
    w(d[keep].rename(columns={"group": "decile"}), "P3_microsim_deciles.csv",
      "Mikrosimulyasiya: desil üzrə real gəlir (baza desili), dəyişmə %, qazanan/uduzan payı")
    fi = f[f.indicator.str.startswith("ms_fiscal:") | (f.indicator == "fiscal_cost")]
    w(fi[["scenario", "scenario_name", "year", "indicator", "label_az", "baseline", "value",
          "delta"]], "P3_microsim_fiscal.csv", "Mikrosimulyasiya: vergi və müavinətlərin statik "
      "fiskal təsiri (mln AZN/il; pensiya = büdcədən DSMF-ə transfert konsepsiyası)")
    se = f[f.indicator.str.startswith("ms_hired:") | f.indicator.isin(
        ["employment", "employment_hired", "employment_informal", "ms_unemp_rate"])]
    w(se[["scenario", "year", "indicator", "group", "baseline", "value", "delta", "delta_pct"]],
      "P3_microsim_employment.csv", "Mikrosimulyasiya: məşğulluq — formal/qeyri-formal, NACE "
      "bölmələri üzrə muzdlu işçilər (min nəfər)")
    w(pd.DataFrame(STATUS), "P3_microsim_status.csv", "Mikrosimulyasiya: hər ssenari üzrə icra "
      "statusu və kanal (birbaşa alət / makro-IO əlaqəsi)")
    w(baseline_path(), "P3_microsim_baseline.csv", "Mikrosimulyasiya bazası 2024–2030 "
      "(MikroUnit FR1/FR4 bazası ilə statik qocaldılma)")
    log(f"[ms_outputs] {len(out)} fayl, {f.scenario.nunique()} ssenari")
    return out


if __name__ == "__main__":
    write_all()
