"""pg_lb10.py — fr/fr10-sintetik.html: FR10 Layer B (enterprise-level econometrics) — model cards,
coefficient tables, average marginal effects, ROC and calibration, production function, parameter
recovery — every view under the red synthetic banner while layer_b_data_mode is SYNTHETIC."""
from . import core, html, figs, v2data as V, v2nav
from .core import esc
from .v2data import pval, isnum
from .v2eqparts import cf

SAMPLE_AZ = {"in-sample": "nümunə daxilində", "out-of-sample (last two years)": "nümunədən kənar (son iki il)",
             "out-of-sample": "nümunədən kənar"}


def mode(m):
    return str(V.registry(m).get("layer_b_data_mode") or "SYNTHETIC").upper()


def banner(m, pre, what):
    if mode(m) == "REAL":
        return ('<div class="box"><p><strong>REAL MƏLUMAT.</strong> Bu bölmə Nazirliyin müəssisə məlumatı ilə '
                "qiymətləndirilib; nəticələr yalnız Nazirliyin sistemində saxlanılmalıdır.</p></div>")
    return html.synth_banner(pre, what)


def coef_rows(d, term_col="term", az_col="term_az", stat="t"):
    rows = []
    for r in d.itertuples(index=False):
        p = getattr(r, "p")
        rows.append([f"<code>{esc(getattr(r, term_col))}</code>", esc(V.az(getattr(r, az_col, "") or "")),
                     cf(r.coef), cf(r.se), cf(getattr(r, stat), 3),
                     f'<span{" class=sig" if isnum(p) and p < 0.05 else ""}>{pval(p)}</span>',
                     f"{cf(r.ci_low)} … {cf(r.ci_high)}"])
    return html.table(["Kod", "İzahedici dəyişən", "Əmsal", "Standart xəta", f"{stat}-statistikası", "p-dəyəri",
                       "95 % etibarlılıq intervalı"], rows, cls="tbl tbl-dense tbl-eq",
                      cols=["c-tight", "c-text", "c-num", "c-num", "c-num", "c-num", "c-tight"])


def roc_fig(frames, title_auc):
    data = [{"type": "scatter", "mode": "lines", "name": "təsadüfi təsnifat", "x": [0, 1], "y": [0, 1],
             "line": {"color": figs.GREY2, "dash": "dot", "width": 1.2}, "hoverinfo": "skip"}]
    cols = [figs.ACCENT, figs.GREY]
    for i, (lab, d) in enumerate(frames):
        d = d.sort_values(["fpr", "tpr"])
        data.append({"type": "scatter", "mode": "lines", "name": lab, "x": figs._clean(d.fpr), "y": figs._clean(d.tpr),
                     "line": {"color": cols[i % 2], "width": 2.4, "dash": "solid" if i == 0 else "dash"},
                     "hovertemplate": "yalançı müsbət %{x:.2f}, həqiqi müsbət %{y:.2f}"})
    lay = figs.layout("həqiqi müsbət nisbəti", forecast=False, height=380)
    lay["xaxis"] = {"title": {"text": "yalançı müsbət nisbəti"}, "range": [0, 1], "gridcolor": "#eceff1", "zeroline": False}
    lay["yaxis"]["range"] = [0, 1.02]
    lay["hovermode"] = "closest"
    return {"data": data, "layout": lay}


def calib_fig(d):
    data = [{"type": "scatter", "mode": "lines", "name": "mükəmməl kalibrləmə", "x": [0, 1], "y": [0, 1],
             "line": {"color": figs.GREY2, "dash": "dot", "width": 1.2}, "hoverinfo": "skip"}]
    for i, (s, g) in enumerate(d.groupby("sample", sort=True)):
        data.append({"type": "scatter", "mode": "lines+markers", "name": SAMPLE_AZ.get(s, s),
                     "x": figs._clean(g.mean_predicted), "y": figs._clean(g.observed_rate),
                     "line": {"color": [figs.ACCENT, figs.GREY][i % 2], "width": 2}, "marker": {"size": 8},
                     "hovertemplate": "proqnoz %{x:.3f}, faktiki %{y:.3f}"})
    hi = float(max(d.mean_predicted.max(), d.observed_rate.max())) * 1.05
    lay = figs.layout("faktiki hadisə tezliyi", forecast=False, height=360)
    lay["xaxis"] = {"title": {"text": "orta proqnoz ehtimalı (desil üzrə)"}, "range": [0, hi], "gridcolor": "#eceff1", "zeroline": False}
    lay["yaxis"]["range"] = [0, hi]
    lay["hovermode"] = "closest"
    return {"data": data, "layout": lay}


def model_card(r, coefs, interp):
    meta = [("Blok", esc(V.az(r.block))), ("Üsul", esc(V.az(r.estimator))), ("Asılı dəyişən", f"<code>{esc(r.dependent)}</code>"),
            ("Müşahidələr", core.num(r.n_obs, 0)), ("Müəssisələr", core.num(r.n_firms, 0) if isnum(r.n_firms) else "—"),
            ("İllər", f"{int(r.year_min)}–{int(r.year_max)}" if isnum(r.year_min) else "—"),
            (esc(V.az(str(r.r2_type))) if isinstance(r.r2_type, str) else "R²", cf(r.r2, 3))]
    for k, lab in (("auc", "AUC (nümunə daxilində)"), ("auc_oos", "AUC (nümunədən kənar)"), ("brier", "Brier balı"),
                   ("hosmer_lemeshow_p", "Hosmer–Lemeshow, p"), ("RTS", "Miqyas effekti (α + β)"), ("crs_p", "Sabit miqyas testi, p")):
        val = getattr(r, k, None)
        if isnum(val):
            meta.append((lab, pval(val) if k.endswith("_p") else cf(val, 3)))
    kv = "".join(f'<span class="pf"><span class="pf-k">{k}</span> {v}</span>' for k, v in meta)
    it = f'<p class="interp">{esc(V.az(interp))}</p>' if isinstance(interp, str) else ""
    c = coefs[coefs.model_id == r.model_id]
    return (f'<details class="eq lb" id="lb-{esc(r.model_id)}"><summary><span class="eq-head"><span class="eq-title">'
            f'{esc(V.az(r.title_az))}</span> <code class="eq-id">{esc(r.model_id)}</code></span>'
            f'<span class="eq-chips">{html.pill("gap", "SİNTETİK")}</span><span class="perf">{kv}</span></summary>'
            f'<div class="eq-body">{it}<h4>Əmsallar</h4>{coef_rows(c)}</div></details>')


def ame_table(d):
    rows = [[f"<code>{esc(r.term)}</code>", esc(V.az(r.term_az)), cf(r.ame), cf(r.se), cf(r.z, 3), pval(r.p),
             f"{cf(r.ci_low)} … {cf(r.ci_high)}"] for r in d.itertuples(index=False)]
    return html.table(["Kod", "İzahedici dəyişən", "Orta marjinal effekt", "Standart xəta", "z", "p-dəyəri",
                       "95 % etibarlılıq intervalı"], rows, cls="tbl tbl-dense",
                      cols=["c-tight", "c-text", "c-num", "c-num", "c-num", "c-num", "c-tight"])


def recovery_tables(rec, mc):
    rows = []
    for r in rec.itertuples(index=False):
        if not isnum(r.true):
            rows.append([f"<code>{esc(r.model_id)}</code>", "—", esc(V.az(r.note_az or "")), "—", "—", "—", "—"])
            continue
        cov = '<span class="skill-pos">bəli</span>' if r.covered is True or str(r.covered) == "True" else \
            '<span class="skill-neg">xeyr</span>'
        rows.append([f"<code>{esc(r.model_id)}</code>", f"<code>{esc(r.term)}</code> {esc(V.az(r.term_az or ''))}",
                     cf(r.true), cf(r.estimate), f"{cf(r.ci_low)} … {cf(r.ci_high)}", cov, cf(r.bias_in_se, 2)])
    t1 = html.table(["Model", "Parametr", "Həqiqi dəyər", "Qiymətləndirmə", "95 % etibarlılıq intervalı",
                     "İnterval həqiqi dəyəri örtür", "Sürüşmə, standart xəta ilə"], rows, cls="tbl tbl-dense",
                    cols=["c-tight", "c-text", "c-num", "c-num", "c-tight", "c-tight", "c-num"])
    rows = [[f"<code>{esc(r.model_id)}</code>", f"<code>{esc(r.term)}</code> {esc(V.az(r.term_az or ''))}", cf(r.true),
             cf(r.mean_estimate), cf(r.mc_sd), core.num(r.coverage_95 * 100, 0) + core.NBSP + "%",
             core.num(r.reps, 0), "bəli" if str(r.consistent_estimator) == "True" else "xeyr"]
            for r in mc.itertuples(index=False)]
    t2 = html.table(["Model", "Parametr", "Həqiqi dəyər", "Orta qiymətləndirmə", "Monte-Karlo standart sapması",
                     "95 % örtük", "Təkrar", "Ardıcıl qiymətləndirici"], rows, cls="tbl tbl-dense",
                    cols=["c-tight", "c-text", "c-num", "c-num", "c-num", "c-num", "c-num", "c-tight"])
    return t1, t2


def build(texts, pre="../"):
    m = "FR10"
    path = "fr/fr10-sintetik.html"
    models = core.csv("FR10_SYNTHETIC_econ_models.csv")
    coefs = core.csv("FR10_SYNTHETIC_econ_coefficients.csv")
    interp = dict(zip(*[core.csv("FR10_SYNTHETIC_econ_interpretation_az.csv")[c] for c in ("model_id", "interpretation_az")]))
    rules = core.csv("FR10_SYNTHETIC_econ_sample_rules.csv")
    droc, eroc = core.csv("FR10_SYNTHETIC_econ_distress_roc.csv"), core.csv("FR10_SYNTHETIC_econ_export_roc.csv")
    dcal, ecal = core.csv("FR10_SYNTHETIC_econ_distress_calibration.csv"), core.csv("FR10_SYNTHETIC_econ_export_calibration.csv")
    rec, mc = core.csv("FR10_SYNTHETIC_econ_recovery.csv"), core.csv("FR10_SYNTHETIC_econ_recovery_mc.csv")
    t1, t2 = recovery_tables(rec, mc)
    secs = [("modeller", "Model kartları"), ("marjinal", "Marjinal effektlər"), ("roc", "ROC və kalibrləmə"),
            ("berpa", "Parametr bərpası"), ("qaydalar", "Nümunə qaydaları")]
    o = ["<h1>FR10 — Müəssisə səviyyəsində ekonometrika (B qatı)</h1>", v2nav.strip(m, path),
         banner(m, pre, "Bu səhifədəki bütün modellər uydurma müəssisə panelində qiymətləndirilib."),
         '<p class="lead-in">B qatı müəssisələrin rentabelliyini, istehsal funksiyasını, TFP-ni, maliyyə çətinliyini, '
         "investisiya normasını və ixrac iştirakını izah edən modellərdir. Nazirlik real müəssisə panelini yükləyəndə "
         "(İş paneli → «Məlumat yüklə» və ya API) eyni kod real məlumatla yenidən işləyir və bu nişan avtomatik "
         f"«REAL» olur. İndi isə məqsəd boru xəttinin düzgün işlədiyini göstərməkdir: generatorun həqiqi parametrləri "
         f"məlum olduğu üçün qiymətləndiricilərin onları bərpa edib-etmədiyini yoxlamaq olur.</p>",
         html.h2("modeller", 1, "Model kartları"),
         f"<p>{core.num(len(models), 0)} model; karta klikləyin — əmsallar cədvəli açılır.</p>"]
    o += [model_card(r, coefs, interp.get(r.model_id)) for r in models.itertuples(index=False)]
    o += [html.h2("marjinal", 2, "Orta marjinal effektlər (logit modelləri)"),
          html.h3("Maliyyə çətinliyi ehtimalı"), ame_table(core.csv("FR10_SYNTHETIC_econ_distress_ame.csv")),
          html.h3("İxrac iştirakı ehtimalı"), ame_table(core.csv("FR10_SYNTHETIC_econ_export_ame.csv")),
          html.h2("roc", 3, "ROC əyriləri və kalibrləmə"),
          html.fig("lb10_roc_distress", "Maliyyə çətinliyi modeli: ROC əyrisi",
                   roc_fig([(SAMPLE_AZ.get(s, s), g) for s, g in droc.groupby("sample", sort=True)], True),
                   "Əyri diaqonaldan nə qədər yuxarıdadırsa, model çətinlikdə olan müəssisələri o qədər yaxşı ayırır.",
                   "SİNTETİK məlumat."),
          html.fig("lb10_cal_distress", "Maliyyə çətinliyi modeli: kalibrləmə (desillər)", calib_fig(dcal),
                   "Nöqtələr diaqonala yaxındırsa, proqnoz ehtimalları faktiki tezliyə uyğundur.", "SİNTETİK məlumat."),
          html.fig("lb10_roc_export", "İxrac iştirakı modeli: ROC əyrisi",
                   roc_fig([(SAMPLE_AZ.get(s, s), g) for s, g in eroc.groupby("sample", sort=True)], True),
                   "Nümunə daxilində ROC əyrisi.", "SİNTETİK məlumat."),
          html.fig("lb10_cal_export", "İxrac iştirakı modeli: kalibrləmə (desillər)", calib_fig(ecal),
                   "Desillər üzrə orta proqnoz ehtimalı və faktiki ixracçı payı.", "SİNTETİK məlumat."),
          html.h2("berpa", 4, "Parametr bərpası"),
          "<p>Generatorun həqiqi parametrləri ilə qiymətləndirmələrin müqayisəsi: interval həqiqi dəyəri örtürsə və "
          "Monte-Karlo təkrarlarında örtük 95 %-ə yaxındırsa, qiymətləndirici düzgün işləyir.</p>",
          html.h3("Bir nümunədə bərpa"), t1, html.h3("Monte-Karlo bərpası"), t2,
          html.h2("qaydalar", 5, "Nümunə qaydaları"),
          html.table(["Əhatə", "Qayda"], [[esc(V.az(r.scope_az)), esc(V.az(r.rule_az))] for r in rules.itertuples(index=False)],
                     cols=["c-tight", "c-text"]),
          f'<p>Bütün fayllar: <a href="fr10.html#files">FR10 · Fayllar</a>; sintetik faylın necə əvəz olunduğu: '
          f'<a href="{pre}synthetic.html">Sintetik məlumat</a>.</p>']
    return "\n".join(o), secs
