"""
validate_dsk — DSK-nın köhnə Excel (BIFF .xls) cədvəllərinin yoxlanılması və alt qovluğun müəyyənləşdirilməsi.

Qovluq → onu oxuyan ilk mərhələ:
    data/dsk                         → FR4  (əmək bazarı)
    data/dsk_services                → FR5  (pullu xidmətlər)
    data/dsk_enterprise/<bölmə>      → FR10 (sənaye, sahibkarlıq, statistik vahidlər, milli hesablar)
    data/dsk_competition/<current|vintages> → FR12 (rəqabət)
"""
import csv, re
from pathlib import Path

import nbextract as X

XLS_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
DSK_DIRS = {"dsk": "FR4", "dsk_services": "FR5",
            "dsk_enterprise/industry": "FR10", "dsk_enterprise/entrepreneurship": "FR10",
            "dsk_enterprise/st_units": "FR10", "dsk_enterprise/nat_accounts": "FR10",
            "dsk_competition/current": "FR12", "dsk_competition/vintages": "FR12"}
FR10_LOCAL_DIR = {"industry": "industry", "entrepreneurship": "entrepreneurship", "st_units": "st_units",
                  "system_nat_accounts": "nat_accounts"}


def norm_subfolder(sub):
    s = str(sub or "").replace("\\", "/").strip().strip("/")
    if s.startswith("data/"):
        s = s[5:]
    return s


def referenced_sheets(root):
    """{fayl: {vərəq, ...}} — dəftərlərdə `open_workbook(.../'fayl.xls').sheet_by_name('vərəq')` kimi."""
    out = {}
    for m in ("FR4", "FR5", "FR10", "FR12"):
        p = Path(root) / ("%s.ipynb" % m)
        if p.exists():
            for fn, sh in X.regex_all(p, r"'([^'/]+\.xls)'\)\)?\.sheet_by_name\(\s*'([^']+)'"):
                out.setdefault(fn, set()).add(sh)
    return out


def _rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def known_locations(root):
    """{fayl: {alt qovluq, ...}} — mövcud fayllar, FR4/FR5 yükləmə siyahıları və FR10/FR12 manifestləri."""
    root, loc = Path(root), {}
    for sub in DSK_DIRS:
        d = root / "data" / sub
        if d.is_dir():
            for p in d.glob("*.xls"):
                loc.setdefault(p.name, set()).add(sub)
    for nb, var, sub in (("FR4", "DSK_FILES", "dsk"), ("FR5", "SFILES", "dsk_services")):
        for fn in X.assigned(root / ("%s.ipynb" % nb), var, []) or []:
            if isinstance(fn, str):
                loc.setdefault(fn, set()).add(sub)
    m10 = root / "output" / "FR10_dsk_manifest.csv"
    if m10.exists():
        for r in _rows(m10):
            d = FR10_LOCAL_DIR.get(r.get("section", ""))
            if d and r.get("file"):
                loc.setdefault(r["file"], set()).add("dsk_enterprise/" + d)
    m12 = root / "output" / "FR12_dsk_manifest.csv"
    if m12.exists():
        for r in _rows(m12):
            lp = norm_subfolder(r.get("local_path", ""))
            if lp.startswith("dsk_competition/") and r.get("file"):
                loc.setdefault(r["file"], set()).add(lp.rsplit("/", 1)[0])
    return loc


def infer_subfolder(root, filename):
    c = sorted(known_locations(root).get(filename, set()))
    return c[0] if len(c) == 1 else None, c


def _yr(v):
    if isinstance(v, float) and v.is_integer() and 1985 <= v <= 2035:
        return int(v)
    if isinstance(v, str):
        m = re.fullmatch(r"\s*((?:19|20)\d{2})\s*\**\s*(\d\))?\s*", v) or re.search(r"as of 01\.01\.((?:19|20)\d{2})", v)
        if m:
            return int(m.group(1))
    return None


def validate_dsk(path, filename, subfolder, root):
    errors, warnings = [], []
    sub = norm_subfolder(subfolder)
    if sub not in DSK_DIRS:
        errors.append({"message": "Alt qovluq yanlışdır: «%s». Mümkün olanlar: %s" % (subfolder, ", ".join(DSK_DIRS))})
        return {"ok": False, "kind": "dsk", "errors": errors, "warnings": warnings, "summary": {}}
    with open(path, "rb") as fh:
        head = fh.read(8)
    if head != XLS_MAGIC:
        errors.append({"message": "Fayl köhnə Excel (BIFF .xls) formatında deyil — ehtimal ki, DSK saytının HTML səhifəsidir"})
        return {"ok": False, "kind": "dsk", "errors": errors, "warnings": warnings, "summary": {"subfolder": sub}}
    try:
        import xlrd
        wb = xlrd.open_workbook(str(path))
    except Exception as e:
        errors.append({"message": "Fayl xlrd ilə açılmadı: %s" % e})
        return {"ok": False, "kind": "dsk", "errors": errors, "warnings": warnings, "summary": {"subfolder": sub}}
    sheets = wb.sheet_names()
    expected = referenced_sheets(root).get(filename, set())
    for s in sorted(expected - set(sheets)):
        errors.append({"sheet": s, "message": "Dəftərin oxuduğu vərəq yoxdur: «%s»" % s})
    existing = Path(root) / "data" / sub / filename
    old_sheets = []
    if existing.exists():
        try:
            with open(existing, "rb") as fh:
                magic = fh.read(8)
            if magic == XLS_MAGIC:
                old_sheets = xlrd.open_workbook(str(existing), on_demand=True).sheet_names()
        except Exception:
            old_sheets = []
        by_name = sub in ("dsk", "dsk_services")          # FR4 / FR5 read their sheets by name
        for s in old_sheets:
            if s not in sheets and s not in expected:
                (errors if by_name else warnings).append(
                    {"sheet": s, "message": "Əvvəlki faylda olan vərəq yeni faylda yoxdur: «%s»" % s})
    else:
        warnings.append({"message": "data/%s/%s hazırda yoxdur — dəftərlər bu adı oxumaya bilər" % (sub, filename)})
    sh = wb.sheet_by_index(0)
    ys = sorted({y for r in range(min(sh.nrows, 14)) for c in range(sh.ncols) for y in [_yr(sh.cell_value(r, c))] if y})
    if not ys:
        warnings.append({"message": "Birinci vərəqin ilk 14 sətrində il başlığı tapılmadı"})
    return {"ok": not errors, "kind": "dsk", "errors": errors, "warnings": warnings,
            "summary": {"subfolder": sub, "stage": DSK_DIRS[sub], "sheets": sheets, "expected_sheets": sorted(expected),
                        "previous_sheets": old_sheets, "years": [ys[0], ys[-1]] if ys else None, "rows": sh.nrows}}
