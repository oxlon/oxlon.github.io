"""
report_xlsx — server tərəfində Excel ixracı (openpyxl): seçilmiş çıxış faylları və/və ya analiz nəticəsi
(stress / miqyaslanma / optimallaşdırma cavabındakı cədvəllər ayrı vərəqlərə). Hər vərəqdə başlıq sətri,
dondurulmuş başlıq, avtomatik süzgəc; «Məlumat» vərəqində mənbə, baseline_id, yaradılma vaxtı.
Başlıqlar Azərbaycan dilindədir: panelin etiket cədvəli panel/i18n/columns_az.csv icra vaxtı oxunur (kod tapılmasa —
kodun özü); hər başlıq xanasının şərhində sütun kodu saxlanılır.
"""
import csv, io, re
from pathlib import Path

from apicore import DEFAULT_ROOT, ApiError, now_iso

LABELS_REL = Path("panel") / "i18n" / "columns_az.csv"
_LABELS = {}


def column_labels(root=None):
    """{code: Azerbaijani label} from the panel's label table (read at runtime, cached per file mtime)."""
    for base in ([Path(root)] if root else []) + [DEFAULT_ROOT]:
        p = base / LABELS_REL
        try:
            key = (str(p), p.stat().st_mtime)
        except OSError:
            continue
        if key not in _LABELS:
            with open(p, encoding="utf-8", newline="") as f:
                _LABELS.clear()
                _LABELS[key] = {r["key"]: r["az"] for r in csv.DictReader(f) if r.get("key") and r.get("az")}
        return _LABELS[key]
    return {}


def headers(cols, labels):
    """Azerbaijani header per column code (fallback: the code); duplicates get the code appended."""
    out, seen = [], set()
    for c in cols:
        h = labels.get(str(c), str(c))
        if h in seen:
            h = "%s (%s)" % (h, c)
        seen.add(h)
        out.append(h)
    return out

DEFAULT_FILES = ["FR2_risk_scores.csv", "FR2_alerts.csv", "D5_daily_monitor.csv", "K1_at_risk_summary.csv",
                 "V3_var_es.csv", "S7_daily_decision.csv", "FR3_stress_scenarios.csv"]
MAX_ROWS = 100000


def _sheet_name(s, used):
    s = re.sub(r"[\[\]\*\?/\\:]", "_", str(s))[:31] or "vərəq"
    base, i = s, 2
    while s in used:
        s = (base[:28] + "_%d" % i)
        i += 1
    used.add(s)
    return s


def _cell(v):
    if isinstance(v, (dict, list)):
        import json
        return json.dumps(v, ensure_ascii=False)[:32000]
    if isinstance(v, float) and v != v:
        return None
    return v


def tables_from_result(res, prefix=""):
    """Flatten a /run response: every list of dicts becomes a table; nested dicts are walked one level deeper."""
    out = []
    for k, v in (res or {}).items():
        if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
            out.append((prefix + k, v))
        elif isinstance(v, dict):
            out += tables_from_result(v, prefix + k + ".")
    return out


def build(views, files=None, result=None, title=None, meta=None):
    from openpyxl import Workbook
    from openpyxl.comments import Comment
    from openpyxl.styles import Font, PatternFill
    wb = Workbook()
    info = wb.active
    info.title = "Məlumat"
    used = {"Məlumat"}
    rows = [("Hesabat", title or "MİİS §15.5.3 — risk modulu ixracı"), ("Yaradıldı (UTC)", now_iso())]
    rows += [(k, str(v)) for k, v in (meta or {}).items()]
    tables = []
    for f in (files if files is not None else ([] if result else DEFAULT_FILES)):
        rel, p = views.output_path(f)
        if p.suffix.lower() != ".csv":
            raise ApiError(400, "bad_parameter", "Excel-ə yalnız CSV faylları ixrac olunur: %s" % rel)
        df = views.frame(rel)
        if len(df) > MAX_ROWS:
            df = df.head(MAX_ROWS)
            rows.append((rel, "ilk %d sətir" % MAX_ROWS))
        tables.append((rel.rsplit(".", 1)[0], list(df.columns), df.itertuples(index=False, name=None)))
        ent = views.catalog_entry(rel)
        if ent:
            rows.append((rel, ent.get("description_az", "")))
    for name, recs in tables_from_result(result or {}):
        cols = []
        for r in recs:
            cols += [c for c in r if c not in cols]
        tables.append((name, cols, ([r.get(c) for c in cols] for r in recs)))
    if not tables:
        raise ApiError(400, "empty_report", "İxrac üçün cədvəl yoxdur (files və ya result verin)")
    for k, v in rows:
        info.append([k, v])
    info.column_dimensions["A"].width, info.column_dimensions["B"].width = 34, 110
    bold, fill = Font(bold=True), PatternFill("solid", fgColor="DDE6F0")
    labels = column_labels(getattr(getattr(views, "cfg", None), "root", None))
    for name, cols, it in tables:
        ws = wb.create_sheet(_sheet_name(name, used))
        hdr = headers(cols, labels)
        ws.append(hdr)
        for c, code in zip(ws[1], cols):
            c.font, c.fill = bold, fill
            if str(code) != c.value:
                c.comment = Comment("kod: %s" % code, "MİİS")
        for r in it:
            ws.append([_cell(x) for x in r])
        ws.freeze_panes = "A2"
        if ws.max_row > 1 and cols:
            ws.auto_filter.ref = ws.dimensions
        for i, c in enumerate(cols[:60], start=1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = min(max(len(str(hdr[i - 1])) + 2, 10), 40)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
