"""Harmonised indicator rows (OUT_COLS) of the microsimulation for one year:
poverty (headcount / gap / severity at the DSK line, the ÜSY need criterion and the
subsistence minimum — lines held at their BASELINE values), Gini (income, consumption),
mean/median income, deciles (fixed baseline ranking), winners/losers, employment (formal /
informal / by NACE section), average wage and the static fiscal cost (mln AZN per year)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import ms_metrics as M
from .engine_base import row

METHOD = "mikrosimulyasiya (statik, ilk raund)"


def _emp(q):
    w = q["weight"].to_numpy()
    st = q["status"].to_numpy()
    out = {"employment": w[np.isin(st, ["employee", "selfemp", "agri"])].sum() / 1e3,
           "employment_hired": w[st == "employee"].sum() / 1e3,
           "employment_informal": w[np.isin(st, ["selfemp", "agri"])].sum() / 1e3}
    lf = out["employment"] + w[st == "unemployed"].sum() / 1e3
    out["ms_unemp_rate"] = 100 * (lf - out["employment"]) / lf
    sec = q.loc[st == "employee"].groupby("sector")["weight"].sum() / 1e3
    return out, sec


def _fiscal(hh, per, q, f):
    w = q["weight"].to_numpy()
    k = 12 / 1e6
    out = {x: float(np.sum(w * per[x])) * k for x in ("pit", "ui_ee", "ui_er", "med_ee", "med_er")}
    out["ssc"] = float(np.sum(w * (per["ssc_ee"] + per["ssc_er"]))) * k
    out["ui"] = out.pop("ui_ee") + out.pop("ui_er")
    out["med"] = out.pop("med_ee") + out.pop("med_er")
    out["pensions"] = float(np.sum(w * per["pension"])) * k
    hw = hh["w"].to_numpy()
    out["utsy"] = float(np.sum(hw * hh["utsy"])) * k
    out["benefits_other"] = float(np.sum(hw * hh["y_benother"])) * k / f.get("benefits", 1.0)
    out["vat"] = float(np.sum(hw * hh["vat"])) * k
    bud = (q["budget"] == 1).to_numpy()
    out["budget_wagebill"] = float(np.sum(w[bud] * per["employer_cost"][bud])) * k
    return out


def pension_scale(year, model_bill):
    """Pension spending base shared with the core: config/fiscal_params.csv `pension_spending`
    via policyunit.fiscal.base_value (DSMF labour pensions, uprated with the FR1 average pension);
    the model supplies the % change. Base year (<= 2024): DSMF 2024 actual 6 469 mln."""
    try:
        if year <= 2024:
            return 6468.9 / model_bill
        from . import fiscal
        return float(fiscal.base_value("pension_spending", year)) / model_bill
    except Exception:                                    # noqa: BLE001
        return 1.0


LAB = {"poverty_rate": ("Yoxsulluq səviyyəsi (DSK xətti)", "%"),
       "poverty_gap": ("Yoxsulluq dərinliyi (DSK xətti)", "%"),
       "poverty_severity": ("Yoxsulluğun kəskinliyi (DSK xətti)", "%"),
       "gini": ("Gini əmsalı — gəlir (adambaşına)", "0–100"),
       "gini_cons": ("Gini əmsalı — istehlak (adambaşına)", "0–100"),
       "income_mean_pc": ("Orta adambaşına gəlir (nominal)", "AZN/ay"),
       "income_median_pc": ("Median adambaşına gəlir (nominal)", "AZN/ay"),
       "income_real_pc": ("Orta adambaşına real gəlir (qiymət dəyişməsi nəzərə alınmaqla)", "AZN/ay"),
       "cons_real_pc": ("Orta adambaşına real istehlak", "AZN/ay"),
       "hh_disp_real": ("Ev təsərrüfatlarının real gəliri (EBT anlayışı)", "mln AZN"),
       "wage_nominal": ("Orta aylıq nominal əmək haqqı (muzdlu)", "AZN"),
       "employment": ("Məşğulluq (muzdlu + öz hesabına)", "min nəfər"),
       "employment_hired": ("Muzdlu işçilər (formal)", "min nəfər"),
       "employment_informal": ("Öz hesabına / qeyri-formal məşğullar", "min nəfər"),
       "ms_unemp_rate": ("İşsizlik səviyyəsi (mikrosimulyasiya)", "%"),
       "fiscal_cost": ("Birbaşa fiskal xərc (+) / gəlir (−), statik, XALİS (müavinət və əmək xərci "
                       "artımı − vergi/haqq daxilolmalarının artımı)", "mln AZN")}


def indicators(r, year, synth):
    hb, pb, q = r["base"]
    hs, ps, qs = r["scen"]
    hba, cal, P0 = r["base_aligned"], r["cal"], r["P0"]
    kap = cal.get("kappa", 1.0)
    lines = {"dsk": (cal.get("pov_line_year", cal.get("pov_line", 270.1)), "c"),
             "need": (P0.get("need_criterion", year), "y")}
    sm = P0.get("subsist_min", year)
    if np.isfinite(sm):
        lines["subsist"] = (sm, "y")
    SB, SS = M.summary(hb, lines, kap), M.summary(hs, lines, kap)
    note = ("SİNTETİK məlumat — real ev təsərrüfatı məlumatı deyil; " if synth else "") + \
        "statik ilk raund; yoxsulluq xətləri baza səviyyəsində sabit"
    R = []
    add = lambda ind, b, v, grp="", lab=None, unit=None, pp=False: R.append(row(
        ind, lab or LAB[ind][0], unit or LAB[ind][1], year, b, v, METHOD, "D", grp, note,
        delta=(v - b) if pp else None, delta_pct=(v - b) if pp else None))
    for ln, (z, _) in lines.items():
        sfx = "" if ln == "dsk" else f":{ln}"
        nm = {"dsk": "DSK rəsmi xətti (kappa ilə)", "need": "ÜSY ehtiyac meyarı (gəlir)",
              "subsist": "yaşayış minimumu (gəlir)"}[ln]
        for key, lab in (("headcount", "poverty_rate"), ("gap", "poverty_gap"),
                         ("severity", "poverty_severity")):
            add(lab + sfx, SB[f"pov_{key}_{ln}"], SS[f"pov_{key}_{ln}"], ln,
                f"{LAB[lab][0].split(' (')[0]} — {nm}, xətt {z:.1f} AZN", "%")
    add("gini", 100 * SB["gini_income"], 100 * SS["gini_income"], pp=True)
    add("gini_cons", 100 * SB["gini_cons"], 100 * SS["gini_cons"], pp=True)
    pwb, pws = (hb.w * hb.n).to_numpy(), (hs.w * hs.n).to_numpy()
    add("income_mean_pc", SB["mean_income_pc"], SS["mean_income_pc"])
    add("income_median_pc", SB["median_income_pc"], SS["median_income_pc"])
    add("income_real_pc", SB["mean_income_pc"], float(np.sum(pws * hs.y_pc_real) / pws.sum()))
    add("cons_real_pc", SB["mean_cons_pc"], SS["mean_cons_pc"])
    add("hh_disp_real", float(np.sum(hb.w * hb.y_total)) * 12e-6,
        float(np.sum(hs.w * hs.y_total / hs.price_idx)) * 12e-6)
    eb, es = q.status == "employee", qs.status == "employee"
    add("wage_nominal", np.average(pb["gross"][eb], weights=q.weight[eb]),
        np.average(ps["gross"][es], weights=qs.weight[es]))
    (Eb, Sb), (Es, Ss) = _emp(q), _emp(qs)
    for k in Eb:
        add(k, Eb[k], Es[k], pp=(k == "ms_unemp_rate"))
    for s in sorted(set(Sb.index) | set(Ss.index)):
        add(f"ms_hired:{s}", float(Sb.get(s, 0)), float(Ss.get(s, 0)), s,
            f"Muzdlu işçilər — {s}", "min nəfər")
    dec_b = M.hh_deciles(hb.y_pc.to_numpy(), hb.w.to_numpy())
    pos = pd.Index(pd.factorize(q["hh_id"])[1]).get_indexer(
        [i.rstrip("s") for i in pd.factorize(qs["hh_id"])[1]])
    dec_s = dec_b[pos]
    mb = M.decile_means(hb.y_pc.to_numpy(), hb.n.to_numpy(), hb.w.to_numpy(), dec_b)
    ms_ = M.decile_means(hs.y_pc_real.to_numpy(), hs.n.to_numpy(), hs.w.to_numpy(), dec_s)
    wl = M.winners_losers(hs.y_pc_real.to_numpy() - hba.y_pc.to_numpy(), dec_s,
                          hs.w.to_numpy(), hs.n.to_numpy())
    for d in range(10):
        g = f"D{d + 1}"
        add("income_decile_pc", mb[d], ms_[d], g, f"Adambaşına real gəlir — {g} (baza desili)",
            "AZN/ay")
        add("winners_share", 0.0, wl[d][1], g, f"Qazananların payı — {g}", "%", pp=True)
        add("losers_share", 0.0, wl[d][2], g, f"Uduzanların payı — {g}", "%", pp=True)
    Fb, Fs = _fiscal(hb, pb, q, cal["factors"]), _fiscal(hs, ps, qs, cal["factors"])
    sc = pension_scale(year, Fb["pensions"])      # one base concept with the core (fiscal_params)
    Fb["pensions"], Fs["pensions"] = Fb["pensions"] * sc, Fs["pensions"] * sc
    lab = {"pit": "Gəlir vergisi", "ssc": "Sosial sığorta haqları (işçi + işəgötürən)",
           "ui": "İşsizlikdən sığorta haqları", "med": "İcbari tibbi sığorta haqları",
           "vat": "ƏDV (ev təsərrüfatı istehlakı, EBT əsaslı)", "utsy": "ÜSY ödənişləri",
           "pensions": "Pensiya xərcləri — DSMF əmək pensiyaları bazası (fiscal_params; artım = "
                       "büdcədən DSMF-ə transfert, BRÜT)",
           "benefits_other": "Digər sosial müavinətlər",
           "budget_wagebill": "Büdcə təşkilatlarının əmək xərci"}
    for k, v in lab.items():
        add(f"ms_fiscal:{k}", Fb[k], Fs[k], k, v + " (illik)", "mln AZN")
    spend = ("pensions", "utsy", "benefits_other", "budget_wagebill")
    rev = ("pit", "ssc", "ui", "med", "vat")
    cost = sum(Fs[k] - Fb[k] for k in spend) - sum(Fs[k] - Fb[k] for k in rev)
    R.append(row("fiscal_cost", LAB["fiscal_cost"][0], "mln AZN", year, 0.0, cost, METHOD, "D",
                 "", note, delta=cost, delta_pct=float("nan")))
    return pd.DataFrame(R)
