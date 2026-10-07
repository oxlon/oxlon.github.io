"""
data_views — oxuma son nöqtələri: kataloq (output/_catalog.csv), çıxış faylları (CSV → JSON, süzgəc/səhifələmə/CSV).
(RiskUnit/api/data_views.py-dən uyğunlaşdırılıb.)

CSV-lər pandas ilə oxunur və faylın (mtime, ölçü) açarı ilə yaddaşda saxlanılır.
"""
import os, threading
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from apicore import ApiError, as_list, read_json, safe_relpath, within

RESERVED = {"limit", "offset", "sort", "cols", "q", "format"}
MAX_LIMIT = 20000


def _mtime_iso(p):
    return datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Views:
    def __init__(self, cfg):
        self.cfg = cfg
        self._cache, self._lock = {}, threading.Lock()

    # ------------------------------------------------------------ CSV cache
    def frame(self, name, required=True):
        p = self.cfg.output / name
        if not p.is_file():
            if required:
                raise ApiError(404, "not_found", "Çıxış faylı tapılmadı: %s" % name)
            return None
        st = p.stat()
        key = (str(p), st.st_mtime_ns, st.st_size)
        with self._lock:
            hit = self._cache.get(str(p))
            if hit and hit[0] == key:
                return hit[1]
        try:
            df = pd.read_csv(p, low_memory=False)
        except Exception as e:
            raise ApiError(422, "unreadable", "Fayl oxunmadı: %s" % name, detail=str(e)[:300])
        with self._lock:
            self._cache[str(p)] = (key, df)
        return df

    # ------------------------------------------------------------ catalog
    def catalog(self, prefix=None):
        cat = self.frame("_catalog.csv", required=False)
        rows, seen = [], set()
        if cat is not None:
            for r in cat.fillna("").astype(str).to_dict("records"):
                rows.append({**r, "columns": [c.strip() for c in str(r.get("columns", "")).split(";") if c.strip()]})
                seen.add(r["file"])
        for p in sorted(self.cfg.output.glob("*")):
            if p.is_file() and p.suffix in (".csv", ".json") and not p.name.startswith((".", "_")) and p.name not in seen:
                rows.append({"file": p.name, "owner": "", "description_az": "(kataloqda təsvir yoxdur)",
                             "columns": [], "frequency": "", "rows": "", "updated": ""})
        for r in rows:
            p = self.cfg.output / r["file"]
            r["exists"] = p.is_file()
            r["bytes"] = p.stat().st_size if r["exists"] else None
            r["mtime_utc"] = _mtime_iso(p) if r["exists"] else None
        if prefix:
            pre = as_list(prefix)
            rows = [r for r in rows if any(r["file"].startswith(x) for x in pre)]
        return {"files": rows, "n": len(rows)}

    def catalog_entry(self, name):
        cat = self.frame("_catalog.csv", required=False)
        if cat is None:
            return None
        m = cat[cat["file"] == name]
        return m.fillna("").astype(str).iloc[0].to_dict() if len(m) else None

    # ------------------------------------------------------------ outputs
    def output_path(self, name):
        rel = safe_relpath(name)
        p = self.cfg.output / rel
        if not within(self.cfg.output, p) or not p.is_file() or p.suffix.lower() not in (".csv", ".json"):
            raise ApiError(404, "not_found", "Çıxış faylı tapılmadı: %s" % rel)
        return rel, p

    def output(self, name, qs):
        rel, p = self.output_path(name)
        if p.suffix.lower() == ".json":
            return {"file": rel, "json": read_json(p), "catalog": self.catalog_entry(rel)}
        df = self.frame(rel)
        df = filter_frame(df, qs)
        total = len(df)
        try:
            limit = min(int(_q(qs, "limit", 500)), MAX_LIMIT)
            offset = max(int(_q(qs, "offset", 0)), 0)
        except ValueError:
            raise ApiError(400, "bad_parameter", "limit / offset tam ədəd olmalıdır")
        page = df.iloc[offset:offset + limit]
        return {"file": rel, "columns": list(df.columns), "total": total, "offset": offset, "limit": limit,
                "rows": records(page), "catalog": self.catalog_entry(rel)}

    def output_csv(self, name, qs):
        rel, p = self.output_path(name)
        df = filter_frame(self.frame(rel), qs)
        return rel, df.to_csv(index=False).encode("utf-8")

# ------------------------------------------------------------------ helpers
def _q(qs, k, default=None):
    v = qs.get(k)
    if isinstance(v, list):
        v = v[0] if v else None
    return default if v in (None, "") else v


def records(df):
    if df is None:
        return []
    return df.astype(object).where(pd.notna(df), None).to_dict("records")


def filter_frame(df, qs):
    for k, v in qs.items():
        if k in RESERVED:
            continue
        if k not in df.columns:
            raise ApiError(400, "bad_parameter", "Naməlum sütun: %r. Mövcud sütunlar: %s" % (k, ", ".join(map(str, df.columns))[:600]))
        vals = []
        for x in (v if isinstance(v, list) else [v]):
            vals += as_list(x)
        col = df[k]
        if pd.api.types.is_numeric_dtype(col):
            try:
                nums = [float(x) for x in vals]
            except ValueError:
                raise ApiError(400, "bad_parameter", "«%s» sütunu ədədidir: %r" % (k, vals))
            df = df[col.isin(nums)]
        else:
            df = df[col.astype(str).isin(vals)]
    q = _q(qs, "q")
    if q:
        txt = df.select_dtypes(exclude="number").astype(str)
        mask = txt.apply(lambda s: s.str.contains(q, case=False, regex=False)).any(axis=1) if len(txt.columns) else False
        df = df[mask]
    sort = _q(qs, "sort")
    if sort:
        keys = as_list(sort)
        cols = [s.lstrip("-") for s in keys]
        bad = [c for c in cols if c not in df.columns]
        if bad:
            raise ApiError(400, "bad_parameter", "Sıralama üçün naməlum sütun: %s" % ", ".join(bad))
        df = df.sort_values(cols, ascending=[not s.startswith("-") for s in keys], kind="stable")
    cols = as_list(_q(qs, "cols"))
    if cols:
        bad = [c for c in cols if c not in df.columns]
        if bad:
            raise ApiError(400, "bad_parameter", "Naməlum sütun: %s" % ", ".join(bad))
        df = df[cols]
    return df
