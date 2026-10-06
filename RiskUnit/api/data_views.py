"""
data_views — oxuma son nöqtələri: kataloq, çıxış faylları (CSV → JSON, süzgəc/səhifələmə), monitor (D5/D6/D7),
vəziyyət (son icra, mərhələlər, D2 təzəliyi, xəbərdarlıqlar).

CSV-lər pandas ilə oxunur və faylın (mtime, ölçü) açarı ilə yaddaşda saxlanılır.
"""
import os, threading
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from apicore import ApiError, as_list, read_json, safe_relpath, within

RESERVED = {"limit", "offset", "sort", "cols", "q", "format"}
MAX_LIMIT = 20000
HEADLINE_D6 = ["fr1:rgdp", "fr1:rgdpnon", "fr1:infl", "fr1:balance_n", "fr1:rev_tot_n", "fr1:gdp_n", "mx:current_account",
               "mx:ca_gdp_ratio", "sofaz:assets_usd", "mx:gdp_realg", "mx:nonoil_realg", "mx:cpi_infl"]   # = monitor.HEADLINE + OxLon


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

    def input_frame(self, name):
        p = self.cfg.input / name
        return pd.read_csv(p) if p.is_file() else None

    # ------------------------------------------------------------ catalog
    def catalog(self, prefix=None):
        cat = self.frame("_catalog_v2.csv", required=False)
        rows, seen = [], set()
        if cat is not None:
            for r in cat.fillna("").to_dict("records"):
                rows.append({**r, "columns": [c.strip() for c in str(r.get("columns", "")).replace(",", ";").split(";") if c.strip()]})
                seen.add(r["file"])
        for p in sorted(self.cfg.output.glob("*")):
            if p.is_file() and p.suffix in (".csv", ".json") and not p.name.startswith(".") and p.name not in seen:
                rows.append({"file": p.name, "owner_module": "", "description_az": "(kataloqda təsvir yoxdur — v1 faylı)",
                             "columns": [], "update_frequency": "", "updated_utc": ""})
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
        cat = self.frame("_catalog_v2.csv", required=False)
        if cat is None:
            return None
        m = cat[cat["file"] == name]
        return m.fillna("").iloc[0].to_dict() if len(m) else None

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

    # ------------------------------------------------------------ monitor
    def monitor(self, qs):
        D5 = self.frame("D5_daily_monitor.csv", required=False)
        D6 = self.frame("D6_forecast_impact.csv", required=False)
        D7 = self.frame("D7_changes.csv", required=False)
        D2 = self.frame("D2_feed_status.csv", required=False)
        sig = _q(qs, "signal")
        if D5 is not None and sig:
            D5 = D5[D5["signal"].astype(str).str.startswith(sig)]
        d6_total = 0
        if D6 is not None:
            drv, yr = _q(qs, "driver"), _q(qs, "year")
            targets = as_list(_q(qs, "targets")) or HEADLINE_D6
            if drv:
                D6 = D6[D6["driver"].isin(as_list(drv))]
            if yr:
                D6 = D6[D6["year"].astype(str) == str(yr)]
            if targets != ["*"]:
                D6 = D6[D6["target_id"].isin(targets)]
            d6_total = len(D6)
            D6 = D6.head(int(_q(qs, "d6_limit", 400)))
        p = self.cfg.output / "D5_daily_monitor.csv"
        return {"as_of": _mtime_iso(p) if p.exists() else None, "D5": records(D5), "D6": records(D6), "D6_total": d6_total,
                "D7": records(D7), "feeds": records(D2)}

    # ------------------------------------------------------------ status
    def feeds_summary(self):
        D2 = self.frame("D2_feed_status.csv", required=False)
        if D2 is None:
            return {"n": 0, "by_freshness": {}, "rows": []}
        cols = [c for c in ("feed", "source", "tezlik", "son_deyer", "last_obs", "yas_gun", "tazelik", "status", "retrieved_utc")
                if c in D2.columns]
        return {"n": len(D2), "by_freshness": D2["tazelik"].fillna("—").value_counts().to_dict() if "tazelik" in D2 else {},
                "by_status": D2["status"].fillna("—").value_counts().to_dict() if "status" in D2 else {},
                "rows": records(D2[cols])}

    def alerts_summary(self, n=50):
        A = self.frame("FR2_alerts.csv", required=False)
        if A is None:
            return {"n": 0, "by_severity": {}, "rows": []}
        return {"n": len(A), "by_severity": A["ciddilik"].value_counts().to_dict() if "ciddilik" in A else {},
                "rows": records(A.head(n))}

    def upstream_summary(self):
        M = self.frame("spine_manifest.csv", required=False)
        if M is None:
            return None
        ok = M[M["sha256"].fillna("").astype(str) != ""]
        return {"files": len(M), "present": len(ok), "by_unit": M["unit"].value_counts().to_dict(),
                "manifest_mtime_utc": _mtime_iso(self.cfg.output / "spine_manifest.csv")}

    def status(self):
        full = read_json(self.cfg.output / "_run_summary_v2.json") or {}
        daily = read_json(self.cfg.output / "_run_summary_daily.json") or {}

        def brief(s):
            if not s:
                return None
            return {k: s.get(k) for k in ("yaradildi_utc", "rejim", "as_of", "sebeke", "baseline_id", "muddet_san",
                                          "ugursuz", "qiymetlendirme_ili", "bashliq", "yuksek_prioritet",
                                          "xeberdarliq_sayi", "stress_isare_yoxlamasi", "D6_uygunluq")}
        log = self.frame("NFR2_update_log.csv", required=False)
        return {"baseline_id": full.get("baseline_id") or daily.get("baseline_id"), "as_of": full.get("as_of"),
                "score_year": full.get("qiymetlendirme_ili"), "last_run": brief(full), "last_daily": brief(daily),
                "stages": full.get("merheleler", []), "stages_daily": daily.get("merheleler", []),
                "feeds": self.feeds_summary(), "alerts": self.alerts_summary(),
                "high_priority": full.get("yuksek_prioritet", []), "upstream": self.upstream_summary(),
                "update_log": records(log.tail(10)) if log is not None else []}


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
