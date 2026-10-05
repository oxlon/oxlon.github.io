"""pg_lb12.py — fr/fr12-sintetik.html: FR12 Layer B (firm-level competition econometrics) — model
summaries, coefficient tables with IRR / odds ratios, survival curves, Boone indicator, cohorts,
parameter recovery — under the red synthetic banner while layer_b_data_mode is SYNTHETIC."""
from . import core, html, figs, v2data as V, v2nav
from .core import esc
from .v2data import pval, isnum
from .v2eqparts import cf
from .pg_lb10 import banner

RAMP = ["#0b4f4f", "#0f6b6b", "#3d8b8b", "#6aa9a9", "#97c6c6", "#b8d8d8", "#d3e6e6"]
RATIO_AZ = {"IRR": "hadisə nisbəti (IRR)", "OR": "şans nisbəti (OR)", "HR": "təhlükə nisbəti (HR)"}


def coef_table(d):
    rows = []
    for r in d.itertuples(index=False):
        p = r.p
        ratio = "—"
        if isnum(r.ratio):
            ratio = f"{cf(r.ratio, 3)} [{cf(r.ratio_ci_low, 3)} … {cf(r.ratio_ci_high, 3)}]"
        rows.append([f"<code>{esc(r.term)}</code>", esc(V.az(r.term_az or "")), cf(r.coef), cf(r.se), cf(r.z, 3),
                     f'<span{" class=sig" if isnum(p) and p < 0.05 else ""}>{pval(p)}</span>',
                     f"{cf(r.ci_low)} … {cf(r.ci_high)}", ratio])
    rt = d.ratio_type.dropna().unique()
    rlab = RATIO_AZ.get(rt[0], str(rt[0])) if len(rt) else "nisbət"
    return html.table(["Kod", "İzahedici dəyişən", "Əmsal", "Standart xəta", "z", "p-dəyəri",
                       "95 % etibarlılıq intervalı", f"{rlab} [95 %]"], rows, cls="tbl tbl-dense tbl-eq",
                      cols=["c-tight", "c-text", "c-num", "c-num", "c-num", "c-num", "c-tight", "c-tight"])


def survival_fig(sv):
    data = []
    for i, (c, g) in enumerate(sv.groupby("cohort", sort=True)):
        col = RAMP[i % len(RAMP)]
        g = g.sort_values("age")
        data.append({"type": "scatter", "mode": "lines+markers", "name": f"{c}: Kaplan–Meier",
                     "x": [int(a) for a in g.age], "y": figs._clean(g.km_survival), "legendgroup": str(c),
                     "line": {"color": col, "width": 2}, "marker": {"size": 6, "color": col},
                     "hovertemplate": "%{y:.3f}"})
        data.append({"type": "scatter", "mode": "lines", "name": "logit modeli (nöqtəli xətt)" if i == 0 else f"{c}: logit modeli", "x": [int(a) for a in g.age],
                     "y": figs._clean(g.pred_logit), "legendgroup": str(c), "showlegend": i == 0,
                     "line": {"color": col, "width": 1.4, "dash": "dot"}, "hovertemplate": "%{y:.3f}"})
    lay = figs.layout("sağ qalanların payı", forecast=False, height=440)
    lay["xaxis"] = {"title": {"text": "yaş, il"}, "dtick": 1, "gridcolor": "#eceff1", "zeroline": False}
    return {"data": data, "layout": lay}


def boone_table(b):
    pv = b.pivot_table(index="section", columns="year", values="boone_beta")
    yrs = list(pv.columns)
    rows = [[f"<code>{esc(s)}</code>"] + [cf(pv.loc[s, y], 2) for y in yrs] for s in pv.index]
    return html.table(["NACE bölməsi"] + [str(int(y)) for y in yrs], rows, cls="tbl tbl-dense",
                      cols=["c-tight"] + ["c-num"] * len(yrs))


def cohort_table(c):
    pv = c.pivot_table(index="cohort", columns="age", values="survivor_share")
    ages = list(pv.columns)
    rows = [[str(int(k))] + [core.num(pv.loc[k, a] * 100, 1) if isnum(pv.loc[k, a]) else "—" for a in ages]
            for k in pv.index]
    return html.table(["Kohort"] + [f"{int(a)} yaş" for a in ages], rows, cls="tbl tbl-dense",
                      cols=["c-tight"] + ["c-num"] * len(ages))


def recovery_table(r):
    rows = []
    for x in r.itertuples(index=False):
        cov = '<span class="skill-pos">bəli</span>' if str(x.covered) == "True" else '<span class="skill-neg">xeyr</span>'
        rows.append([esc(V.az(x.block)), f"<code>{esc(x.parameter)}</code>", cf(x.true), cf(x.estimate),
                     f"{cf(x.ci_low)} … {cf(x.ci_high)}", cov, cf(x.error)])
    return html.table(["Blok", "Parametr", "Həqiqi dəyər", "Qiymətləndirmə", "95 % etibarlılıq intervalı",
                       "İnterval həqiqi dəyəri örtür", "Xəta"], rows, cls="tbl tbl-dense",
                      cols=["c-text", "c-tight", "c-num", "c-num", "c-tight", "c-tight", "c-num"])


def build(texts, pre="../"):
    m = "FR12"
    path = "fr/fr12-sintetik.html"
    summ = core.csv("FR12_SYNTHETIC_econ_summary.csv")
    coefs = core.csv("FR12_SYNTHETIC_econ_coefficients.csv")
    sv = core.csv("FR12_SYNTHETIC_econ_survival.csv")
    rec = core.csv("FR12_SYNTHETIC_econ_recovery.csv")
    nd = core.csv("FR12_SYNTHETIC_econ_recovery_not_defined.csv")
    secs = [("modeller", "Modellər"), ("sag-qalma", "Sağ qalma əyriləri"), ("boone", "Boone indikatoru"),
            ("kohortlar", "Kohortlar"), ("berpa", "Parametr bərpası")]
    o = ["<h1>FR12 — Müəssisə səviyyəsində rəqabət ekonometrikası (B qatı)</h1>", v2nav.strip(m, path),
         banner(m, pre, "Bu səhifədəki bütün modellər uydurma biznes reyestrində qiymətləndirilib."),
         '<p class="lead-in">Giriş və çıxışın amilləri (Puasson, mənfi binomial, diskret zamanlı təhlükə (hazard) '
         "modelləri), struktur–davranış–nəticə əlaqəsi, bazar paylarının mobilliyi, yeni müəssisələrin ölçüsü və "
         "artımı, Boone rəqabət indikatoru. DSK biznes reyestri yükləndikdə eyni kod real məlumatla işləyəcək; indi "
         "məqsəd qiymətləndiricilərin generatorun həqiqi parametrlərini bərpa etdiyini göstərməkdir.</p>",
         html.h2("modeller", 1, "Modellər və əmsallar"),
         f"<p>{core.num(len(summ), 0)} model; karta klikləyin — əmsallar, nisbətlər (IRR / OR) və şərh açılır.</p>"]
    for r in summ.itertuples(index=False):
        c = coefs[coefs.model == r.model]
        body = f'<p class="interp">{esc(V.az(r.interpretation_az))}</p>'
        if len(c):
            cov = c.cov_type.dropna().unique()
            body += (f'<p class="eq-meta">Kovariasiya: {esc(V.az(cov[0])) if len(cov) else "—"}</p>'
                     f"<h4>Əmsallar</h4>{coef_table(c)}")
        o.append(f'<details class="eq lb" id="lb-{esc(r.model)}"><summary><span class="eq-head"><span class="eq-title">'
                 f'{esc(V.az(r.model_az))}</span> <code class="eq-id">{esc(r.model)}</code></span>'
                 f'<span class="eq-chips">{html.pill("gap", "SİNTETİK")}</span><span class="perf"><span class="pf">'
                 f'<span class="pf-k">n</span> {core.num(r.n, 0)}</span><span class="pf"><span class="pf-k">əmsal</span> '
                 f'{core.num(len(c), 0)}</span></span></summary><div class="eq-body">{body}</div></details>')
    o += [html.h2("sag-qalma", 2, "Sağ qalma əyriləri"),
          html.fig("lb12_survival", "Kohortlar üzrə sağ qalma: Kaplan–Meier və logit təhlükə modeli", survival_fig(sv),
                   "Bərk xətt — Kaplan–Meier qiymətləndirməsi, nöqtəli xətt — logit təhlükə modelinin proqnozu; "
                   "rəng — giriş ili (kohort).", "SİNTETİK məlumat."),
          html.h2("boone", 3, "Boone indikatoru (bölmə × il)"),
          "<p>Boone meyli — mənfəətin orta xərcə elastikliyi; mənfi və mütləq qiyməti böyük olduqca rəqabət "
          "güclüdür (səmərəsiz müəssisə bazardan daha çox cəzalandırılır).</p>",
          boone_table(core.csv("FR12_SYNTHETIC_econ_boone_sector_year.csv")),
          html.h2("kohortlar", 4, "Kohortlar: sağ qalanların payı, %"),
          cohort_table(core.csv("FR12_SYNTHETIC_econ_cohorts.csv")),
          html.h2("berpa", 5, "Parametr bərpası"),
          "<p>Generatorun həqiqi parametrləri ilə qiymətləndirmələrin müqayisəsi.</p>", recovery_table(rec),
          html.h3("Həqiqi parametri olmayan modellər"),
          "<ul>" + "".join(f"<li><strong>{esc(V.az(x.model))}</strong> — {esc(V.az(x.why_no_true_parameter_az))}</li>"
                           for x in nd.itertuples(index=False)) + "</ul>",
          f'<p>Bütün fayllar: <a href="fr12.html#files">FR12 · Fayllar</a>; sintetik faylın necə əvəz olunduğu: '
          f'<a href="{pre}synthetic.html">Sintetik məlumat</a>.</p>']
    return "\n".join(o), secs
