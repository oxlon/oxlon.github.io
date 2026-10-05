"""nbinfo.py — facts about the six notebooks, read from the .ipynb files (cells, recorded execution time)."""
import datetime as dt
import json

from . import core, html
from .core import v, esc

ORDER = ["FR1", "FR3", "FR4", "FR5", "FR10", "FR12"]
WHAT = {
    "FR1": "Sektorlar və bazarlar üzrə struktur sistem (AZSEM-FR1); üç makro ssenari və FR1 çəkilişləri — digər "
           "dəftərlərin girişi.",
    "FR3": "Orta aylıq əmək haqqı: tənliklər, 2026 cari qiymətləndirməsi, iki bölgünün birgə uzlaşdırılması, zolaqlar.",
    "FR4": "Məşğulluq: pay sistemi, dövlət/büdcə/neft blokları, nümunədən kənar yoxlama, rıçaqlar və zolaqlar.",
    "FR5": "Pullu xidmətlər: aqreqat tələb tənliyi və on üç növ üzrə multinomial-logit pay sistemi.",
    "FR10": "Müəssisələr: A qatı (sahələr, regionlar, məhsullar), proqnoz, erkən xəbərdarlıq; B qatı mühərriki və "
            "əvəzetmə testləri.",
    "FR12": "Rəqabət: göstəricilər, konsentrasiya hədləri, giriş/çıxış modeli, sənaye iqtisadiyyatı ssenariləri, erkən "
            "xəbərdarlıq; B qatı mühərriki.",
}


def deps(code):
    """Other modules whose output CSVs the notebook reads (scanned from its code cells)."""
    import re
    nb = json.loads(core.mark(core.UNIT / f"{code}.ipynb").read_text(encoding="utf-8"))
    src = "".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    found = {m.group(1) for m in re.finditer(r"['\"](FR\d+)_[A-Za-z0-9_]+\.csv", src) if m.group(1) != code}
    return ", ".join(sorted(found, key=lambda x: int(x[2:]))) or "—"


def _ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def info(code):
    p = core.mark(core.UNIT / f"{code}.ipynb")
    nb = json.loads(p.read_text(encoding="utf-8"))
    cells = nb["cells"]
    code_cells = [c for c in cells if c["cell_type"] == "code"]
    ts = [c.get("metadata", {}).get("execution", {}) for c in code_cells]
    ts = [t for t in ts if t.get("iopub.execute_input") and t.get("shell.execute_reply")]
    secs = None
    when = None
    if ts:
        t0 = min(_ts(t["iopub.execute_input"]) for t in ts)
        t1 = max(_ts(t["shell.execute_reply"]) for t in ts)
        secs = (t1 - t0).total_seconds()
        when = t1.strftime("%Y-%m-%d")
    errors = sum(1 for c in code_cells for o in c.get("outputs", []) if o.get("output_type") == "error")
    outs = len(list(core.OUT.glob(f"{code}_*.csv")))
    return {"cells": len(cells), "code": len(code_cells), "secs": secs, "when": when, "errors": errors, "outs": outs}


def run_block(pre):
    total = sum((info(c)["secs"] or 0) for c in ORDER)
    cmds = "\n".join(f"jupyter nbconvert --to notebook --execute --inplace {c}.ipynb" for c in ORDER)
    return (f"<p>Dəftərlər <code>MicroUnit/</code> qovluğundan bu ardıcıllıqla icra olunur (hər biri əvvəlkinin çıxış "
            f"fayllarını oxuyur), sonra sayt yenidən qurulur:</p>"
            f"<pre><code>cd MicroUnit\n{esc(cmds)}\npython3 site/build_site.py</code></pre>"
            f"<p>Son qeydə alınmış icrada altı dəftərin cəmi hesablama vaxtı təxminən {v(total / 60, 1)} dəqiqədir "
            f"(hər dəftər üzrə: <a href=\"{pre}notebooks.html\">Jupyter dəftərləri</a>). <code>build_site.py</code> "
            "sayt səhifələrini yazır, keçid yoxlayıcısını və qrafik yoxlamalarını işə salır; eyni gündə iki dəfə işə "
            "salındıqda bayt-bayt eyni səhifələr verir.</p>")


def table(pre):
    rows = []
    for c in ORDER:
        i = info(c)
        rows.append([html.flink(f"{c}.ipynb", pre), esc(WHAT[c]), esc(deps(c)), f"{v(i['cells'], 0)} / {v(i['code'], 0)}",
                     v(i["secs"], 0) if i["secs"] is not None else "—", esc(i["when"] or "—"), v(i["errors"], 0),
                     v(i["outs"], 0)])
    return html.table(["Dəftər", "Nə edir", "Girişləri", "Xanalar / kod", "İcra, san", "Son icra", "Xəta", "Çıxış CSV"],
                      rows, cols=["c-tight", "c-text", "c-tight", "c-num", "c-num", "c-tight", "c-num", "c-num"])
