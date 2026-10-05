"""FR5 Azerbaijani AUTO blocks, part 2: splits, hold-outs, FR1 comparison, forecast, bands, scenarios, levers, headline."""
import numpy as np
import pandas as pd

from .docgen_az import num, pct, md_table
from ._docgen_az_fr5 import ctx, part1, g, yr, SCEN


def blocks(ns):
    n = ctx(ns)
    tr, rd, FY, LA = n.tr, n.rd, n.FC_YEARS, n.LAST_ACT
    G, e1, t2 = part1(n)
    sp, fs = rd("institutional_split"), rd("fan_splits")
    s30 = sp[(sp.scenario == "Baseline") & (sp.year == FY[-1])].iloc[0]
    f30 = fs[fs.year == FY[-1]].set_index("series")
    G["splits"] = (f"Hər iki bölgü {yr(LA)} ilin dəyərlərində sabit paylarla proqnozlaşdırılır (fərdi sahibkarlar "
                   f"{num(s30.indiv_share * 100, 2)}%, dövlət {num(s30.state_share * 100, 2)}%). {yr(FY[-1])} il üçün Əsas "
                   f"ssenari dəyərləri: hüquqi şəxslər {num(s30.legal_value, 0)}, fərdi sahibkarlar {num(s30.indiv_value, 0)}, "
                   f"dövlət {num(s30.state_value, 0)}, qeyri-dövlət {num(s30.nonstate_value, 0)} mln manat. {yr(FY[-1])} il "
                   f"üçün 90% zolaqlar: fərdi sahibkarların payı {num(f30.loc['indiv_share', 'share_pct_p5'], 1)}–"
                   f"{num(f30.loc['indiv_share', 'share_pct_p95'], 1)}%, dövlətin payı "
                   f"{num(f30.loc['state_share', 'share_pct_p5'], 1)}–{num(f30.loc['state_share', 'share_pct_p95'], 1)}%.")
    hv = rd("holdout_validation", index_col=0)
    G["holdout"] = md_table(hv.T.rename_axis(""), fmt={}, tr=n.trx)
    fc = rd("fr1_comparison", index_col=0)
    gy = int(fc["volume diff, %"].abs().idxmax())
    G["fr1gap"] = (f"FR5 bu sıra üzrə FR1-in öz proqnozundan {yr(FY[0])} ildə {pct(fc.loc[FY[0], 'volume diff, %'])}, "
                   f"{yr(FY[-1])} ildə {pct(fc.loc[FY[-1], 'volume diff, %'])}, ən çox isə {pct(fc.loc[gy, 'volume diff, %'])} "
                   f"({gy}) fərqlənir. Hər ikisi {yr(LA)} ilin eyni dəyərindən başlayır və eyni FR1 amillərindən istifadə edir, "
                   "lakin tənliklər fərqlidir: bu fərq təsdiq deyil, modelləşdirmədəki real fərqdir.")
    tv, tn = rd("total_volume", index_col=0), rd("total_value", index_col=0)
    q25, n25 = float(n.Q_LONG.loc[LA]), float(n.PS_N.total.loc[LA])
    gq = ((tv.Baseline.iloc[-1] / q25) ** (1 / len(FY)) - 1) * 100
    gn = ((tn.Baseline.iloc[-1] / n25) ** (1 / len(FY)) - 1) * 100
    path = pd.concat([pd.Series([q25], index=[LA]), tv.Baseline]).pct_change().dropna() * 100
    drv = rd("fr1_drivers_baseline", index_col=0)
    rp = drv["relative price of services (log)"]
    t = lambda x: f"{x:,.0f}".replace(",", " ")  # noqa: E731
    G["forecast"] = (f"| | {LA} | {FY[-1]} | illik |\n|---|---|---|---|\n"
                     f"| Həcm, 2015-ci il qiymətləri ilə mln manat | {t(q25)} | {t(tv.Baseline.iloc[-1])} | **{gq:+.2f}%** |\n"
                     f"| Dəyər, cari qiymətlərlə mln manat | {t(n25)} | {t(tn.Baseline.iloc[-1])} | **{gn:+.2f}%** |\n\n"
                     "Həcmin illik artımı: " + ", ".join(f"{int(y)} {pct(v)}" for y, v in path.items()) + ". "
                     "FR1 Əsas ssenarisində adambaşına real gəlir: "
                     + ", ".join(f"{int(y)} {pct(v)}" for y, v in drv["income per head growth, %"].dropna().items())
                     + f"; xidmətlər deflyatorunun artımı orta hesabla ildə {pct(drv['deflator growth, %'].dropna().mean())}; "
                     f"xidmətlərin nisbi qiyməti {yr(FY[-1])} ilədək {num(rp.iloc[-1] - rp.iloc[0], 3, True)} log bəndi dəyişir.")
    hg = rd("type_growth_vs_history", index_col=0)
    hg2 = hg[["label", "forecast_2026_2030", "max_forecast_year", "hist_2010_2019", "hist_2021_2025", "best_5yr_avg",
              "best_5yr_window", "exceeds_best_5yr"]].rename(columns={
                  "forecast_2026_2030": "forecast avg 2026–30 %", "max_forecast_year": "max forecast year %",
                  "hist_2010_2019": "2010–19 %", "hist_2021_2025": "2021–25 %", "best_5yr_avg": "best 5-yr avg %",
                  "best_5yr_window": "window", "exceeds_best_5yr": "exceeds best 5-yr"})
    flg = [tr(hg.label.get(i, i)) for i in hg.index[hg.exceeds_best_5yr.astype(bool)]]
    G["types"] = (md_table(hg2, tr=tr) + "\n\nQeyd edilənlər (proqnoz ortası növün öz ən yaxşı beş illik ortasından "
                  "yuxarıdır): " + (", ".join(flg) or "yoxdur") + ".")
    fq, fn = rd("fan_volume", index_col=0), rd("fan_value", index_col=0)
    fd, fm = rd("fan_decomposition", index_col=0), rd("fan_meta").iloc[0]
    av, Y = f"{FY[0]}-{FY[-1]} avg growth", str(FY[-1])
    rng = lambda a, b: f"{pct(a, 1)} ilə {pct(b, 1)} arası"  # noqa: E731
    G["bands"] = (f"*Ehtiyat: yalnız {int(fm.n_paths_joint)} birgə tarixi qalıq yolu (başlanğıc illəri {int(fm.first_start)}–"
                  f"{int(fm.last_start)}) istifadə oluna bilir; zolaqlar göstərici xarakteri daşıyır.* 1 000 təkrarlama "
                  f"(mərkəzləşdirilmiş yollar, işarə məhdudiyyəti ilə parametr çəkilişləri — E1 çəkilişlərinin "
                  f"{num(e1.iloc[0]['sign_reject_rate'] * 100, 1)}%-i rədd edilir — və FR1-in {int(fm.n_fr1_draws)} makro "
                  f"çəkilişi): {yr(FY[-1])} ildə həcmin 90% zolağı {num(fq.loc[Y, 'level_p5'], 0)}–{num(fq.loc[Y, 'level_p95'], 0)} "
                  f"mln manat (median {num(fq.loc[Y, 'level_p50'], 0)}); həcmin orta artımı "
                  f"{rng(fq.loc[av, 'growth_pct_p5'], fq.loc[av, 'growth_pct_p95'])} (median {pct(fq.loc[av, 'growth_pct_p50'])}); "
                  f"dəyərin orta artımı {rng(fn.loc[av, 'growth_pct_p5'], fn.loc[av, 'growth_pct_p95'])} "
                  f"(median {pct(fn.loc[av, 'growth_pct_p50'])}). Yalnız FR5-in öz qalıq və parametr qeyri-müəyyənliyi: "
                  f"{rng(fd.iloc[0, 0], fd.iloc[0, -1])}. E1 və bölgü yollarının öz tam nümunələri üzrə birləşdirildiyi variant: "
                  f"həcm {rng(fd.iloc[2, 0], fd.iloc[2, -1])}, dəyər {rng(fd.iloc[3, 0], fd.iloc[3, -1])}. Kvartillərarası "
                  f"zolağın daxilində olan nöqtəvi proqnozlar: həcm {int(fm.iqr_volume_years_inside)}/{len(FY)} il, dəyər "
                  f"{int(fm.iqr_value_years_inside)}/{len(FY)}, paylar {int(fm.iqr_share_typeyears_inside)}/{13 * len(FY)} növ-il.")
    sc = rd("scenario_summary", index_col=0)
    G["scen"] = (f"**Ssenarilər** ({yr(FY[-1])} ildə həcm): "
                 + ", ".join(f"{SCEN.get(s, s)} {num(sc.loc[s, 'volume_2030'], 0)}" for s in sc.index)
                 + f" mln manat — {num((sc.volume_2030.max() / sc.volume_2030.min() - 1) * 100, 1)}% diapazon; həcmin artımı: "
                 + ", ".join(f"{SCEN.get(s, s)} {pct(sc.loc[s, 'volume_growth_pa'])}" for s in sc.index) + "; dəyərin artımı: "
                 + ", ".join(f"{SCEN.get(s, s)} {pct(sc.loc[s, 'value_growth_pa'])}" for s in sc.index) + ".")
    lvr, tpl = rd("sensitivity_levers", index_col=0), rd("type_price_levers", index_col=0)
    vcol = f"həcm, {FY[-1]}"
    G["levers"] = (md_table(lvr[["volume_2030", "diff_pct", "value_diff_pct"]].rename(columns={
                       "volume_2030": vcol, "diff_pct": "volume vs baseline %", "value_diff_pct": "value vs baseline %"}),
                       fmt={vcol: "{:,.0f}"}, tr=tr, index_name="lever")
                   + f"\n\nNövlər üzrə nisbi qiymət rıçaqları yalnız növlərin daxilində həcm/qiymət bölgüsünü dəyişir; məsələn, "
                   f"rabitə xidmətlərinin {yr(FY[0])} ildə həcm artımı Əsas ssenaridə {pct(tpl.loc['Communication services'].iloc[0])}, "
                   f"2020–25-ci illərin qiymət dreyfi davam etdirilsə {pct(tpl.loc['Communication services'].iloc[1])} olur.")
    ch2 = t2.index[t2.decision.astype(str).str.startswith("CHOSEN")][0]
    G["rev"] = (f"Cari əsas nəticələr (bu icra): 1-ci pillə = {n.trx(e1.iloc[0]['spec'])}, η = {num(e1.iloc[1]['coef'], 3)}; "
                f"2-ci pillə = {tr(ch2)}"
                + (f", Engel meylinin büzülməsi κ = {g(fm.kappa)}" if np.isfinite(fm.kappa) else "")
                + f"; 2026–2030-cu illərdə həcm ildə {pct(gq)}, dəyər {pct(gn)}; E1 üzrə işarəyə görə rədd edilmə nisbəti "
                f"{num(e1.iloc[0]['sign_reject_rate'] * 100, 1)}%; FR5-in {len(list(n.OUT.glob('FR5_*.csv')))} CSV çıxışı.")
    return G
