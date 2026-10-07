"""req.py — the exact Azerbaijani requirement texts, read from the source documents at build time.

FR1, FR3, FR4: micro_tasks.md (headline + agreed elaboration).
FR5: the detailed Technical Assignment (docx table row FR5: requirement + acceptance criterion).
FR10, FR12: the Ministry's written approvals, `Sorğu cvb Bakiniti 24.08.2026.xlsx`, sheet
"Yazılı təsdiq tələbi" (approved wording / recommendation of 24 Aug 2026).
"""
import json
import re
import zipfile
from pathlib import Path

from . import core

TASKS = core.ROOT / "micro_tasks.md"
XLSX = core.ROOT / "Sorğu cvb Bakiniti 24.08.2026.xlsx"
DOCX = core.ROOT / "MIIS_Etrafli_Texniki Tapşırıq.docx"
# The three source documents sit one level above MicroUnit and are not part of the published deploy tree
# (GitHub): every build that can read them refreshes this snapshot, a build without them reads it.
SNAPSHOT = Path(__file__).with_name("req_snapshot.json")


def _tasks():
    txt = core.raw(TASKS)
    out = {}
    for m in re.finditer(r"^### (FR\d+)\s*-\s*(.+?)\n(.*?)(?=^### |\Z)", txt, re.S | re.M):
        code, head, rest = m.group(1), m.group(2).strip(), m.group(3)
        paras = [p.strip() for p in re.split(r"\n\s*\n", rest) if p.strip()]
        out[code] = {"orig": head, "extra": paras, "source": "micro_tasks.md"}
    return out


def _docx_fr5():
    core.mark(DOCX)
    x = zipfile.ZipFile(DOCX).read("word/document.xml").decode("utf8")
    paras = [re.sub(r"<[^>]+>", "", p).strip() for p in re.findall(r"<w:p[ >].*?</w:p>", x)]
    for i, p in enumerate(paras):
        if p == "FR5" and i + 4 < len(paras) and paras[i + 1] == "Funksional" and "pullu" in paras[i + 2]:
            return {"orig": paras[i + 2],
                    "extra": ["Qəbul meyarı: " + paras[i + 4]],
                    "source": DOCX.name + " (FR5 sətri)"}
    return None


def _xlsx():
    try:
        import openpyxl
    except ImportError:
        return {}
    core.mark(XLSX)
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    ws = wb["Yazılı təsdiq tələbi"]
    out = {}
    for r in ws.iter_rows(values_only=True):
        if not r or len(r) < 5 or r[1] not in ("FR10", "FR12"):
            continue
        head = (r[2] or "").strip()
        body = (r[4] or "").replace("\xa0", " ")
        date = r[6] or ""
        if r[1] == "FR10":
            appr = body.split("Təsdiq - D.Ə.:")[-1].strip()
            extra = ["<strong>Təsdiq (D.Ə., " + str(date) + "):</strong> " + core.esc(appr)]
        else:
            first, _, rec = body.partition("Tövsiyə - D.Ə.:")
            seen, bullets = set(), []
            for ln in first.splitlines():
                ln = ln.strip()
                if ln.startswith("•"):
                    b = ln.lstrip("• ").strip()
                    if b not in seen:
                        seen.add(b)
                        bullets.append(b)
            extra = ["<strong>Təklif olunan və razılaşdırılmış redaksiya:</strong><ul>"
                     + "".join(f"<li>{core.esc(b)}</li>" for b in bullets) + "</ul>",
                     "<strong>Tövsiyə (D.Ə., " + str(date) + "):</strong> " + core.esc(rec.strip())]
        out[r[1]] = {"orig": head, "extra": extra, "source": XLSX.name, "html": True}
    return out


def texts():
    if not all(p.exists() for p in (TASKS, DOCX, XLSX)):
        core.mark(SNAPSHOT)
        return json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    t = _tasks()
    fr5 = _docx_fr5()
    if fr5:
        t["FR5"] = fr5
    t.update(_xlsx())
    try:
        SNAPSHOT.write_text(json.dumps(t, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    except OSError:
        pass
    return t


def block(code, t):
    """Render §1 Tələb as the macro site's blockquote."""
    r = t[code]
    paras = [f'<p><strong>Olduğu kimi (MİİS TT §15.5.2, {code}):</strong> «{core.esc(r["orig"])}»</p>']
    for e in r["extra"]:
        if r.get("html"):
            paras.append(f"<p>{e}</p>" if not e.endswith("</ul>") else f"<div>{e}</div>")
        else:
            paras.append(f"<p>{core.esc(e)}</p>")
    paras.append(f'<p>Mənbə: <code>{core.esc(r["source"])}</code></p>')
    return "<blockquote>" + "".join(paras) + "</blockquote>"
