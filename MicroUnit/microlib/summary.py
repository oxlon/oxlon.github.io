"""statsmodels-like plain-text regression summary with Azerbaijani labels (contract glossary E)."""
from __future__ import annotations

W = 92


def _f(v, d=4, w=None):
    if v is None:
        s = "—"
    elif isinstance(v, bool):
        s = "bəli" if v else "xeyr"
    elif isinstance(v, (int,)) and not isinstance(v, bool):
        s = str(v)
    else:
        try:
            x = float(v)
            s = f"{x:.{d}f}" if abs(x) < 1e6 else f"{x:.{d}e}"
        except (TypeError, ValueError):
            s = str(v)
    return s.rjust(w) if w else s


def _pair(l1, v1, l2="", v2=""):
    left = f"{l1:<34}{str(v1):>12}"
    right = f"{l2:<34}{str(v2):>12}" if l2 else ""
    return f"{left}    {right}".rstrip()


def build_summary(eq):
    s, f, dg, rb = eq["sample"], eq["fit"], eq["diagnostics"], eq["robustness"]
    L = ["=" * W, f"Reqressiya nəticəsi — tənlik {eq['id']}", eq.get("title_az", ""), "=" * W]
    L.append(_pair("Asılı dəyişən:", eq["dependent"]["code"], "Determinasiya əmsalı (R²):", _f(f.get("r2"), 4)))
    L.append(_pair("  (" + eq["dependent"].get("label_az", "")[:30] + ")", "", "Düzəldilmiş R²:",
                   _f(f.get("r2_adj"), 4)))
    L.append(_pair("Qiymətləndirmə üsulu:", eq["estimator"], "F-statistikası:", _f(f.get("f_stat"), 3)))
    L.append(_pair("Kovariasiya növü:", eq["cov_type"].split("(")[0][:12], "p-dəyəri (F):", _f(f.get("f_p"), 4)))
    L.append(_pair("Müşahidələr:", _f(s.get("n")), "Log-həqiqətəbənzərlik:", _f(f.get("loglik"), 3)))
    L.append(_pair("Qalıq sərbəstlik dərəcəsi:", _f(s.get("df_resid")), "AIC:", _f(f.get("aic"), 3)))
    L.append(_pair("Parametrlər (k):", _f(s.get("k")), "BIC:", _f(f.get("bic"), 3)))
    L.append(_pair("Nümunə:", f"{s.get('start')}–{s.get('end')}", "Reqressiyanın standart xətası:",
                   _f(f.get("ser"), 4)))
    if f.get("r2_levels") is not None:
        L.append(_pair("", "", "R² (səviyyə qalığı üzrə):", _f(f.get("r2_levels"), 4)))
    L.append(f"Kovariasiya: {eq['cov_type']}")
    L.append("-" * W)
    nw = max([16] + [len(c["name"]) + 1 for c in eq["coefficients"]])
    nw = min(nw, 30)
    L.append(f"{'':<{nw}}{'əmsal':>11}{'standart xəta':>15}{'t-statistikası':>16}{'p-dəyəri':>10}"
             f"{'[0.025':>10}{'0.975]':>10}")
    L.append(f"{'':<{nw}}{'':>11}{'':>15}{'':>16}{'':>10}{'95% etibarlılıq intervalı':>20}")
    L.append("-" * W)
    for c in eq["coefficients"]:
        tag = " (sabitlənmiş)" if c.get("fixed") else ""
        L.append(f"{c['name'][:nw - 1]:<{nw}}{_f(c['coef'], 4, 11)}{_f(c['se'], 4, 15)}{_f(c['t'], 3, 16)}"
                 f"{_f(c['p'], 3, 10)}{_f(c['ci_low'], 3, 10)}{_f(c['ci_high'], 3, 10)}{tag}")
    aug = [c for c in eq["coefficients"] if c.get("role") == "dols_aug"]
    if aug:
        L.append(f"  * d_… hədləri DOLS fərq (lead/lag) hədləridir; proqnozda yalnız uzunmüddətli əmsallar istifadə olunur.")
    L.append("=" * W)
    L.append("Qalıq diaqnostikası")
    L.append(_pair("Durbin-Watson:", _f(dg.get("dw"), 3), "Jarque-Bera (normallıq) p:", _f(dg.get("jb_p"), 3)))
    L.append(_pair("Breusch-Godfrey avtokorrelyasiya p:", _f(dg.get("bg_lm_p"), 3),
                   "  (gecikmə 1 üzrə p):", _f(dg.get("bg_lm_p_lag1"), 3)))
    L.append(_pair("White heteroskedastiklik p:", _f(dg.get("white_p"), 3), "Breusch-Pagan p:",
                   _f(dg.get("bp_p"), 3)))
    L.append(_pair("Ramsey RESET p:", _f(dg.get("reset_p"), 3), "VIF (maks.):", _f(dg.get("vif_max"), 2)))
    L.append(_pair("Şərt ədədi (standartlaşdırılmış):", _f(dg.get("cond_number"), 1), "BP (qiymətl. dəyər üzrə) p:",
                   _f(dg.get("bp_fitted_p"), 3)))
    if dg.get("dw_levels") is not None:
        L.append(_pair("DW (səviyyə qalığı):", _f(dg.get("dw_levels"), 3), "JB p (səviyyə qalığı):",
                       _f(dg.get("jb_p_levels"), 3)))
    eg = dg.get("eg_coint_p")
    L.append(_pair("Kointeqrasiya (Engle-Granger) p:", _f(eg, 3), f"MacKinnon '{dg.get('eg_trend')}', N:",
                   _f(dg.get("eg_N"))))
    if dg.get("coint_established") is not None:
        L.append("  Kointeqrasiya " + ("müəyyən edilib (p ≤ 0.10)." if dg["coint_established"] else
                                       "müəyyən edilməyib: t-statistikaları təsviri xarakter daşıyır."))
    df_ = dg.get("diff_form")
    if df_:
        for c, v in df_["coef"].items():
            lo, hi = df_["ci"][c]
            lv = df_["level"].get(c)
            flag = "  <-- səviyyə əmsalı intervaldan kənardadır" if c in df_["outside"] else ""
            L.append(f"  Fərq forması: {c} = {_f(v, 3)} [{_f(lo, 3)}, {_f(hi, 3)}] vs səviyyə {_f(lv, 3)}{flag}")
        L.append("  Fərq forması ilə uyğunluq: " + ("bəli" if df_["coherent"] else "xeyr"))
    L.append("-" * W)
    L.append("Dayanıqlıq (robustness)")
    ch = rb.get("chow") or {}
    L.append(_pair("Struktur qırılma (Chow) ili:", _f(ch.get("break_year")), "Chow F / p-dəyəri:",
                   f"{_f(ch.get('f'), 2)} / {_f(ch.get('p'), 3)}"))
    for r in rb.get("chow_tests", []):
        L.append(f"    Chow {r.get('label')}: {r.get('break_year')}  F={_f(r.get('f'), 2)}  p={_f(r.get('p'), 3)}"
                 + (f"  ({r['reason']})" if r.get("reason") else ""))
    L.append(_pair("CUSUM (rekursiv qalıqlar) p:", _f(rb.get("cusum_p"), 3), "Hökm:", rb.get("verdict", "—")))
    rec = rb.get("recursive") or {}
    if rec.get("years"):
        L.append(f"  Rekursiv qiymətləndirmə: {rec['years'][0]}–{rec['years'][-1]} ({len(rec['years'])} pəncərə)")
    for c, rg in (rb.get("loo_year_range") or {}).items():
        if rg:
            L.append(f"  Bir ili çıxarmaqla {c}: [{_f(rg[0], 3)}, {_f(rg[1], 3)}]")
    if rb.get("notes_az"):
        L.append("  Qeyd: " + rb["notes_az"])
    ho = eq.get("holdout")
    if ho:
        L.append("-" * W)
        L.append(f"Nümunədən kənar yoxlama (kəsim {ho.get('cut')}): RMSE={_f(ho.get('rmse'), 4)}  "
                 f"Theil U (təsadüfi gəzişmə)={_f(ho.get('theil_u_rw'), 3)}  "
                 f"Theil U (sabit artım)={_f(ho.get('theil_u_const'), 3)}  DM p={_f(ho.get('dm_p_rw'), 3)}")
    if eq.get("restrictions"):
        L.append("-" * W)
        for r in eq["restrictions"]:
            L.append(f"Məhdudiyyət: {r.get('text_az', '')}  test={r.get('test')}  stat={_f(r.get('stat'), 3)}"
                     f"  p={_f(r.get('p'), 3)}  tətbiq edilib: {_f(r.get('imposed'))}")
    L.append("=" * W)
    if eq.get("notes_az"):
        L.append("Qeydlər: " + eq["notes_az"])
    L.append("Standart xətalar və qalıq (residual) diaqnostikası statsmodels ilə müstəqil yenidən hesablanıb.")
    if eq.get("synthetic"):
        L.append("DİQQƏT: sintetik məlumatlar.")
    return "\n".join(L)
