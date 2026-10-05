"""
data_views — çıxış fayllarından oxuma: göstərici kataloqları, proqnozlar, tənliklər.

Proqnozlar `output/FRx_indicator_catalog.csv` (müqavilə §C: id, source_csv, source_column, ...) üzrə
mənbə CSV-dən oxunur. Kataloq hələ yoxdursa və ya sətir həll edilmirsə, panelin yığılmış
bundle-larından (panel/data/frX.js) istifadə olunur — cavabda `source` sahəsi bunu göstərir.
"""
import csv, json, os, re
from pathlib import Path

from apicore import ApiError, MODULES, SCENARIOS

SCEN_NORM = {"baseline": "Baseline", "b": "Baseline", "əsas": "Baseline", "adverse": "Adverse", "a": "Adverse",
             "mənfi": "Adverse", "reform": "Reform", "r": "Reform", "islahat": "Reform", "actual": "Actual",
             "faktiki": "Actual", "history": "Actual"}
PANEL_YEARS = [2026, 2027, 2028, 2029, 2030]
_CACHE = {}


def _cached(path, loader):
    p = Path(path)
    try:
        st = p.stat()
    except OSError:
        return None
    key = (str(p), loader.__name__)
    hit = _CACHE.get(key)
    if hit and hit[0] == (st.st_size, st.st_mtime_ns):
        return hit[1]
    val = loader(p)
    _CACHE[key] = ((st.st_size, st.st_mtime_ns), val)
    return val


def _load_csv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    return (rows[0], rows[1:]) if rows else ([], [])


def _load_catalog(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return [{k.strip(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(f)]


def _load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))


def _load_bundle(p):
    txt = p.read_text(encoding="utf-8")
    i, j = txt.find(".concat("), txt.rfind(");")
    if i < 0 or j < 0:
        return []
    return json.loads(txt[i + 8:j])


def fnum(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        f = float(v)
    else:
        s = str(v).strip()
        if s == "" or s.lower() in ("nan", "none", "null", "inf", "-inf"):
            return None
        try:
            f = float(s)
        except ValueError:
            return None
    return f if f == f and f not in (float("inf"), float("-inf")) else None


def year_of(v):
    f = fnum(v)
    return int(f) if f is not None and float(f).is_integer() and 1900 <= f <= 2100 else None


def norm_scen(v):
    return SCEN_NORM.get(str(v).strip().lower(), str(v).strip())


class Views:
    def __init__(self, cfg):
        self.cfg = cfg

    # ------------------------------------------------------------ catalogs
    def catalog(self, module):
        return _cached(self.cfg.output / ("%s_indicator_catalog.csv" % module), _load_catalog)

    def catalog_ids(self):
        out = {}
        for m in MODULES:
            c = self.catalog(m)
            out[m] = {r.get("id") for r in c} if c is not None else None
        return out

    def panel_records(self, module):
        return _cached(self.cfg.root / "panel" / "data" / ("%s.js" % module.lower()), _load_bundle) or []

    def catalog_view(self, module=None, q=None):
        mods = [module] if module else MODULES
        items, sources = [], {}
        for m in mods:
            cat = self.catalog(m)
            if cat is not None:
                sources[m] = "catalog"
                items += [dict(r, module=r.get("module") or m) for r in cat]
            else:
                recs = self.panel_records(m)
                sources[m] = "panel" if recs else "none"
                for r in recs:
                    items.append({"id": r.get("i"), "module": m, "group_az": r.get("g"), "label_az": _label(r),
                                  "unit_az": r.get("u"), "kind": r.get("k"), "has_forecast": "True",
                                  "scenarios": ";".join(norm_scen(k) for k in sorted((r.get("s") or {}))),
                                  "has_band": str("q" in r), "source_csv": r.get("src", ""), "source_column": ""})
        if q:
            ql = q.lower()
            items = [r for r in items if ql in (r.get("id") or "").lower() or ql in (r.get("label_az") or "").lower()]
        return {"items": items, "total": len(items), "sources": sources}

    # ------------------------------------------------------------ forecasts
    def series_from_csv(self, src, column, sid):
        """(scenario, year, value) — geniş (sütun = göstərici) və ya uzun (id/code, year, value) formatlı CSV."""
        path = self.cfg.output / Path(src).name
        loaded = _cached(path, _load_csv)
        if not loaded:
            raise LookupError("mənbə fayl tapılmadı: %s" % src)
        header, rows = loaded
        h = [x.strip() for x in header]
        low = [x.lower() for x in h]
        sample = rows[:400]

        def col_where(pred, among):
            for c in among:
                vals = [r[c] for r in sample if c < len(r) and r[c].strip() != ""]
                if vals and all(pred(v) for v in vals):
                    return c
            return None
        first = range(min(4, len(h)))
        yc = next((low.index(k) for k in ("year", "il", "period") if k in low), None)
        if yc is None:
            yc = col_where(lambda v: year_of(v) is not None, first)
        sc = next((low.index(k) for k in ("scenario", "ssenari") if k in low), None)
        if sc is None:
            sc = col_where(lambda v: norm_scen(v) in SCENARIOS + ["Actual"], first)
        if yc is None:
            raise LookupError("il sütunu müəyyən edilmədi: %s" % src)
        if column and column in h and column.lower() not in ("value",):
            vc, filt = h.index(column), None
        else:
            vc = low.index("value") if "value" in low else None
            idc = next((low.index(k) for k in ("id", "indicator", "series", "code", "variable", "entity") if k in low), None)
            if vc is None or idc is None:
                raise LookupError("sütun tapılmadı: %s#%s" % (src, column))
            key = column or sid
            filt = (idc, {key, sid, sid.split(":", 1)[-1]})
        out = []
        for r in rows:
            if filt and (filt[0] >= len(r) or r[filt[0]] not in filt[1]):
                continue
            y = year_of(r[yc]) if yc < len(r) else None
            if y is None or vc >= len(r):
                continue
            out.append((norm_scen(r[sc]) if sc is not None and sc < len(r) else None, y, fnum(r[vc])))
        return out

    def forecasts(self, module=None, ids=None, scenarios=None, y0=None, y1=None, limit=200000):
        if not module and not ids:
            raise ApiError(400, "bad_parameter", "«module» və ya «id» parametri tələb olunur")
        mods = [module] if module else sorted({module_of(i) for i in ids} & set(MODULES))
        if ids and not mods:
            raise ApiError(400, "bad_parameter", "İdentifikator «fr<k>:<kod>» formatında olmalıdır, məs. fr1:rgdp")
        want = set(ids or [])
        scen = set(scenarios or [])
        items, meta, warns, used = [], {}, [], set()

        def keep(s, y):
            return (not scen or s in scen) and (y0 is None or y >= y0) and (y1 is None or y <= y1)
        for m in mods:
            cat, done = self.catalog(m), set()
            if cat is not None:
                for r in cat:
                    sid = r.get("id")
                    if not sid or (want and sid not in want):
                        continue
                    try:
                        pts = self.series_from_csv(r.get("source_csv", ""), r.get("source_column", ""), sid)
                    except (LookupError, OSError, ValueError) as e:
                        warns.append({"id": sid, "message": "Kataloq sətri həll edilmədi: %s" % e})
                        continue
                    default = (r.get("scenarios") or "Baseline").split(";")[0].strip() or "Baseline"
                    meta[sid] = {k: r.get(k) for k in ("module", "group_az", "label_az", "label_en", "unit_az", "freq", "kind",
                                                       "has_band", "equation_ids", "imputed_years", "source_csv", "source_column")}
                    meta[sid]["source"] = "catalog"
                    for s, y, v in pts:
                        s = s or norm_scen(default)
                        if keep(s, y):
                            items.append({"id": sid, "module": m, "scenario": s, "period": y, "value": v})
                    done.add(sid)
                    used.add("catalog")
            if cat is None or (want and want - done):
                recs = self.panel_records(m)
                if cat is None and not recs:
                    warns.append({"module": m, "message": "%s üçün nə kataloq (output/%s_indicator_catalog.csv), nə də panel məlumatı var" % (m, m)})
                for r in recs:
                    sid = r.get("i")
                    if sid in done or (want and sid not in want):
                        continue
                    yrs = r.get("y") or PANEL_YEARS
                    meta[sid] = {"module": m, "group_az": r.get("g"), "label_az": _label(r), "unit_az": r.get("u"),
                                 "kind": r.get("k"), "has_band": "q" in r, "source_csv": r.get("src"), "source": "panel"}
                    for y, v in r.get("h") or []:
                        if keep("Actual", int(y)):
                            items.append({"id": sid, "module": m, "scenario": "Actual", "period": int(y), "value": fnum(v)})
                    for k, vals in (r.get("s") or {}).items():
                        s = norm_scen(k)
                        for y, v in zip(yrs, vals):
                            if keep(s, y):
                                items.append({"id": sid, "module": m, "scenario": s, "period": y, "value": fnum(v)})
                    used.add("panel")
        if want:
            miss = sorted(want - set(meta))
            if miss and not items:
                raise ApiError(404, "not_found", "Göstərici tapılmadı: %s" % ", ".join(miss[:20]))
            if miss:
                warns.append({"message": "Tapılmayan göstəricilər: %s" % ", ".join(miss[:50])})
        total = len(items)
        return {"items": items[:limit], "total": total, "truncated": total > limit, "series": meta,
                "source": "+".join(sorted(used)) or "none", "warnings": warns}

    # ------------------------------------------------------------ equations
    def equations(self, module=None, eq_id=None, full=False):
        if eq_id and not module:
            m = re.match(r"^(FR\d+)\.", eq_id, re.I)
            module = m.group(1).upper() if m and m.group(1).upper() in MODULES else None
        mods = [module] if module else MODULES
        items, info, missing = [], {}, []
        for m in mods:
            p = self.cfg.output / ("%s_equations.json" % m)
            try:
                d = _cached(p, _load_json)
            except ValueError as e:
                info[m] = {"error": "JSON oxunmadı: %s" % e}
                continue
            if d is None:
                missing.append(m)
                continue
            eqs = d.get("equations") or []
            info[m] = {"generated": d.get("generated"), "data_mode": d.get("data_mode"), "count": len(eqs)}
            for e in eqs:
                if eq_id and e.get("id") != eq_id:
                    continue
                items.append(e if (full or eq_id) else compact(e))
        if eq_id and not items:
            if missing:
                raise ApiError(404, "not_found", "Tənlik tapılmadı: %s (%s_equations.json hələ yaradılmayıb)" % (eq_id, missing[0]))
            raise ApiError(404, "not_found", "Tənlik tapılmadı: %s" % eq_id)
        out = {"items": items, "total": len(items), "modules": info, "missing": missing}
        if missing:
            out["message"] = ("Tənlik reyestri hələ yaradılmayıb: %s. Dəftərin son hücrəsi output/FRx_equations.json faylını "
                              "yazdıqdan sonra burada görünəcək." % ", ".join(missing))
        return out


def module_of(sid):
    """«fr10:emp:agr» (v2) və ya «FR10|qrup|ad|variant» (köhnə panel id-si) → «FR10»."""
    m = re.match(r"^fr(\d+)[:|.]", str(sid or ""), re.I)
    return ("FR" + m.group(1)) if m else None


def compact(e):
    """Siyahı üçün yığcam görünüş: uyğunlaşdırılmış sıralar, rekursiv yollar və mətn xülasəsi çıxarılır."""
    out = {k: v for k, v in e.items() if k not in ("fitted", "summary_text", "robustness")}
    rob = e.get("robustness") or {}
    if rob:
        out["robustness"] = {k: rob.get(k) for k in ("verdict", "chow", "cusum_p", "notes_az") if k in rob}
    return out


def _label(r):
    return r.get("e", "") + ((" — " + r["v"]) if r.get("v") else "")
