"""v2eqparts.py — the tables inside an equation card (coefficients, fit, diagnostics, difference form,
restrictions, robustness, hold-out). All labels Azerbaijani (glossary of the v2 contract)."""
from . import core, html, v2data as V
from .core import esc
from .v2data import pval, isnum

NB = core.NBSP


def cf(x, d=4):
    """Coefficient-style number: fixed decimals, scientific for very small magnitudes."""
    if not isnum(x):
        return "—"
    x = float(x)
    if x != 0 and abs(x) < 10 ** -d:
        m, e = f"{x:.3e}".split("e")
        return (m.replace(".", ",").replace("-", core.MINUS) + "·10<sup>" + str(int(e)).replace("-", core.MINUS)
                + "</sup>")
    if abs(x) >= 1e5:
        d = 0
    elif abs(x) >= 100:
        d = 2
    return core.num(x, d)


def _why(reasons, key):
    r = (reasons or {}).get(key)
    return f' title="{esc(V.az(r))}"' if r else ""


def _cell(val, reasons=None, key=None, fmt=None):
    s = (fmt or cf)(val)
    if s == "—" and reasons and key in reasons:
        return f'<span class="na"{_why(reasons, key)}>—</span>'
    return s


def coef_table(e):
    rows = []
    for c in e.get("coefficients") or []:
        flags = []
        if c.get("fixed"):
            flags.append(html.pill("neutral", "sabitlənib"))
        if c.get("editable"):
            flags.append(html.pill("done", "ssenaridə dəyişdirilə bilər"))
        uv = c.get("used_value")
        if isnum(uv) and isnum(c.get("coef")) and abs(float(uv) - float(c["coef"])) > 1e-12 * max(1, abs(c["coef"])):
            flags.append(f'{html.pill("partial", "proqnozda")} {cf(uv)}')
        p = c.get("p")
        pcls = ' class="sig"' if isnum(p) and p < 0.05 else ""
        lab = V.az(c.get("label_az") or "")
        lab = "" if lab == c.get("name") else esc(lab)
        rows.append([f'<code>{esc(c.get("name"))}</code>' + (f'<span class="clab">{lab}</span>' if lab else ""),
                     cf(c.get("coef")), cf(c.get("se")), cf(c.get("t"), 2), f"<span{pcls}>{pval(p)}</span>",
                     f'{cf(c.get("ci_low"))} … {cf(c.get("ci_high"))}', " ".join(flags)])
    if not rows:
        return "<p>Bu tənlikdə qiymətləndirilmiş əmsal yoxdur (kalibrlənmiş qayda).</p>"
    return html.table(["İzahedici dəyişən", "Əmsal", "Standart xəta", "t", "p-dəyəri",
                       "95 % etibarlılıq intervalı", "Qeyd"], rows,
                      cls="tbl tbl-dense tbl-eq",
                      cols=["c-text", "c-num", "c-num", "c-num", "c-num", "c-tight", "c-text"])


FIT = [("r2", "Determinasiya əmsalı (R²)", 4), ("r2_adj", "Düzəldilmiş R²", 4), ("ser", "Reqressiyanın standart xətası", 4),
       ("loglik", "Log-həqiqətəbənzərlik", 3), ("aic", "AIC", 3), ("bic", "BIC", 3), ("f_stat", "F-statistikası", 3),
       ("f_p", "p-dəyəri (F)", None), ("r2_levels", "R² (səviyyə qalığı üzrə)", 4), ("lr_chi2", "LR χ²", 3),
       ("lr_p", "p-dəyəri (LR)", None)]


def fit_table(e):
    f = e.get("fit") or {}
    nr = f.get("null_reasons") or {}
    rows = []
    for k, lab, d in FIT:
        if k not in f and k not in nr:
            continue
        val = _cell(f.get(k), nr, k, pval if d is None else (lambda x, d=d: cf(x, d)))
        rows.append([esc(lab), val])
    s = e.get("sample") or {}
    rows.append(["Müşahidələr (n)", core.num(s.get("n"), 0) if isnum(s.get("n")) else "—"])
    rows.append(["Parametrlər (k)", core.num(s.get("k"), 0) if isnum(s.get("k")) else "—"])
    if f.get("f_type"):
        rows.append(["F testinin növü", esc(V.az(f["f_type"]))])
    return html.table(["Göstərici", "Dəyər"], rows, cls="tbl tbl-dense tbl-kv", cols=["c-text", "c-num"])


DIAG = [("dw", "Durbin–Watson", "dw"), ("bg_lm_p", "Breusch–Godfrey avtokorrelyasiya, p", "p"),
        ("bg_lm_p_lag1", "Breusch–Godfrey (1 gecikmə), p", "p"), ("jb_p", "Jarque–Bera normallıq, p", "p"),
        ("white_p", "White heteroskedastiklik, p", "p"), ("bp_p", "Breusch–Pagan heteroskedastiklik, p", "p"),
        ("reset_p", "Ramsey RESET (funksional forma), p", "p"), ("vif_max", "VIF (maksimum)", "vif"),
        ("cond_number", "Şərt ədədi (standartlaşdırılmış)", "cond"), ("dw_levels", "Durbin–Watson (səviyyə qalığı)", "dw"),
        ("jb_p_levels", "Jarque–Bera (səviyyə qalığı), p", "p"), ("eg_coint_p", "Kointeqrasiya (Engle–Granger), p", "coint"),
        ("eg_stat", "Engle–Granger statistikası", "x"), ("first_stage_F", "Birinci mərhələ F (alət gücü)", "iv"),
        ("sargan_p", "Sargan (artıq identifikasiya), p", "p"), ("auc", "ROC əyrisi altındakı sahə (AUC)", "auc"),
        ("brier", "Brier balı", "x"), ("hosmer_lemeshow_p", "Hosmer–Lemeshow, p", "p")]


def _read(kind, x):
    """Plain-language reading of a diagnostic: green when the check raises no concern."""
    if not isnum(x):
        return ""
    ok = lambda t: f'<span class="skill-pos">{t}</span>'          # noqa: E731
    no = lambda t: f'<span class="skill-neg">{t}</span>'          # noqa: E731
    if kind == "p":                     # H0 = no problem (no autocorrelation, normal, homoskedastic, …)
        return no("5 %-də rədd — problem ola bilər") if x < 0.05 else ok("problem aşkarlanmayıb")
    if kind == "coint":                 # H0 = NO cointegration
        return ok("kointeqrasiya var (p ≤ 0,10)") if x <= 0.10 else no("kointeqrasiya təsdiqlənmir")
    if kind == "dw":
        return ok("1,5–2,5 aralığında") if 1.5 <= x <= 2.5 else no("qalıqlarda avtokorrelyasiya ehtimalı")
    if kind == "vif":
        return ok("multikollinearlıq zəifdir") if x < 10 else no("güclü multikollinearlıq (VIF ≥ 10)")
    if kind == "cond":
        return ok("normal") if x < 30 else no("yüksək (≥ 30)")
    if kind == "iv":
        return ok("alətlər güclüdür (F ≥ 10)") if x >= 10 else no("zəif alətlər (F &lt; 10)")
    if kind == "auc":
        return ok("yaxşı ayırma") if x >= 0.7 else no("zəif ayırma")
    return ""


def diag_table(e):
    d = e.get("diagnostics") or {}
    nr = d.get("null_reasons") or {}
    rows = []
    for k, lab, kind in DIAG:
        if k not in d and k not in nr:
            continue
        fmt = pval if kind in ("p", "coint") else (lambda x: cf(x, 3))
        rows.append([esc(lab), _cell(d.get(k), nr, k, fmt), _read(kind, d.get(k))])
    if "coint_established" in d:
        ce = d.get("coint_established")
        rows.append(["Kointeqrasiya müəyyən edilib", "bəli" if ce else "xeyr",
                     "" if ce else "t-statistikaları təsviri xarakter daşıyır"])
    na = sorted({V.az(v) for v in nr.values()})
    note = (f'<p class="eq-na">Hesablanmayan testlər: {esc("; ".join(na))}.</p>' if na else "")
    return html.table(["Test", "Dəyər", "Oxunuşu"], rows, cls="tbl tbl-dense tbl-kv",
                      cols=["c-text", "c-num", "c-text"]) + note


def diff_form(e):
    df = (e.get("diagnostics") or {}).get("diff_form")
    if not df or not df.get("coef"):
        return ""
    rows = []
    for k, c in df["coef"].items():
        ci = (df.get("ci") or {}).get(k) or [None, None]
        lev = (df.get("level") or {}).get(k)
        out = k in (df.get("outside") or [])
        rows.append([f"<code>{esc(k)}</code>", cf(lev), cf(c), f"{cf(ci[0])} … {cf(ci[1])}",
                     '<span class="skill-neg">intervaldan kənar</span>' if out else '<span class="skill-pos">daxilində</span>'])
    coh = df.get("coherent")
    tail = ("<p>Fərq forması ilə uyğunluq: <strong>" + ("bəli" if coh else "xeyr") + "</strong>.</p>")
    return ("<h4>Fərq forması (birinci fərqlərdə eyni tənlik)</h4>"
            + html.table(["Kod", "Səviyyə əmsalı", "Fərq əmsalı", "95 % etibarlılıq intervalı", "Səviyyə əmsalı fərq intervalına görə"], rows,
                         cls="tbl tbl-dense", cols=["c-tight", "c-num", "c-num", "c-tight", "c-text"]) + tail)


def restrictions(e):
    rs = e.get("restrictions") or []
    if not rs:
        return ""
    rows = [[esc(V.az(r.get("text_az") or "")), esc(V.az(r.get("test") or "")), cf(r.get("stat"), 3), pval(r.get("p")),
             "bəli" if r.get("imposed") else "xeyr"] for r in rs]
    return ("<h4>Məhdudiyyətlər və onların testləri</h4>"
            + html.table(["Məhdudiyyət", "Test", "Statistika", "p-dəyəri", "Tətbiq edilib"], rows,
                         cls="tbl tbl-dense", cols=["c-text", "c-text", "c-num", "c-num", "c-tight"]))
