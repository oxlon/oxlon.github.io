"""
status_view — /api/v1/status: son icra, məlumatın versiyası (vintage), FR10/FR12 məlumat rejimi (SYNTHETIC/REAL).
"""
import csv, hashlib, os, time
from datetime import datetime, timezone
from pathlib import Path

import apidb
import nbextract
from apicore import API_VERSION, MODULES, now_iso, read_json

SYN_STATUS = "SYNTHETIC — not real enterprise data"
LAYER_B = {"FR10": ("firm_panel", "FR10_firm_panel"), "FR12": ("business_register", "FR12_business_register")}
DSK_FOLDERS = ["dsk", "dsk_services", "dsk_enterprise", "dsk_competition"]
_CACHE = {}


def _iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha(path):
    st = path.stat()
    key = ("sha", str(path), st.st_size, st.st_mtime_ns)
    if key not in _CACHE:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        _CACHE[key] = h.hexdigest()
    return _CACHE[key]


def _last_year(path):
    st = path.stat()
    key = ("year", str(path), st.st_size, st.st_mtime_ns)
    if key not in _CACHE:
        try:
            from validate_workbook import read_book, years
            _, mats = read_book(path, ["Real sektor"])
            ys = years(mats.get("Real sektor", []))
            _CACHE[key] = ys[-1] if ys else None
        except Exception:
            _CACHE[key] = None
    return _CACHE[key]


def file_mode(path):
    """Real adlı CSV-də sintetik nişan varmı (ilk 5000 sətir)? xlsx — REAL qəbul olunur."""
    if path.suffix.lower() != ".csv":
        return "REAL"
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            rd = csv.DictReader(f)
            if "data_status" not in (rd.fieldnames or []):
                return "REAL"
            vals = [r.get("data_status") for _, r in zip(range(5000), rd)]
    except OSError:
        return None
    return "SYNTHETIC" if vals and all(v == SYN_STATUS for v in vals) else "REAL"


def data_mode(cfg, module):
    folder, base = LAYER_B[module]
    d = cfg.data / folder
    real = [d / (base + e) for e in (".csv", ".xlsx") if (d / (base + e)).exists()]
    src = real[0] if real else d / (base + "_SYNTHETIC.csv")
    in_mode = file_mode(src) if real else "SYNTHETIC"
    out = cfg.output
    n_real = len(list(out.glob("%s_FIRM_*.csv" % module)))
    n_syn = len(list(out.glob("%s_SYNTHETIC_*.csv" % module)))
    out_mode = "REAL" if n_real and not n_syn else ("SYNTHETIC" if n_syn and not n_real else ("MIXED" if n_real else None))
    eq = read_json(out / ("%s_equations.json" % module)) or {}
    mode = eq.get("data_mode") or out_mode
    return {"mode": mode, "input_mode": in_mode, "input_file": str(src.relative_to(cfg.root)) if src.exists() else None,
            "output_mode": out_mode, "outputs": {"FIRM": n_real, "SYNTHETIC": n_syn},
            "rerun_needed": bool(in_mode and out_mode and in_mode != out_mode),
            "note_az": ("Nəticələr SİNTETİK məlumata əsaslanır — texniki nümayiş, təhlil nəticəsi deyil"
                        if mode == "SYNTHETIC" else "Nəticələr real məlumata əsaslanır — yalnız Nazirliyin sistemində saxlayın"
                        if mode == "REAL" else "Rejim müəyyən edilmədi")}


def vintage(cfg, uploads=None):
    wbn = nbextract.workbook_name(cfg.root)
    wb = cfg.data / wbn
    out = {"workbook": {"file": "data/" + wbn, "present": wb.exists()}}
    if wb.exists():
        st = wb.stat()
        out["workbook"].update(bytes=st.st_size, modified=_iso(st.st_mtime), sha256=_sha(wb), last_annual_year=_last_year(wb))
    if uploads is not None:
        last = {}
        for u in uploads.list(limit=500, status="applied"):
            last.setdefault(u["kind"], {"upload_id": u["id"], "filename": u["filename"], "applied_at": u["applied_at"],
                                        "target": u["target"]})
        out["last_applied"] = last
        if "workbook" in last:
            out["workbook"]["original_filename"] = last["workbook"]["filename"]
    dsk = {}
    for f in DSK_FOLDERS:
        files = [p for p in (cfg.data / f).rglob("*.xls")] if (cfg.data / f).is_dir() else []
        dsk[f] = {"files": len(files), "latest": _iso(max(p.stat().st_mtime for p in files)) if files else None}
    out["dsk"] = dsk
    outs = [p for p in cfg.output.glob("*.csv")] if cfg.output.is_dir() else []
    out["outputs"] = {"csv_files": len(outs), "latest": _iso(max(p.stat().st_mtime for p in outs)) if outs else None}
    return out


def status(cfg, runs, uploads, engine, started_at):
    last = runs.last()
    lr = None
    if last:
        lr = {k: last.get(k) for k in ("id", "status", "trigger", "plan", "started_at", "finished_at", "source")}
        m = read_json(cfg.logs / last["id"] / "manifest.json") or {}
        lr["identical_to_previous"] = (m.get("reproducibility") or {}).get("identical")
        lr["error"] = m.get("error") or last.get("error")
    return {"status": "ok", "version": API_VERSION, "time": now_iso(), "server_started": started_at,
            "root": str(cfg.root), "running": runs.busy(), "pending": runs.pending, "last_run": lr,
            "data_vintage": vintage(cfg, uploads),
            "data_modes": {m: data_mode(cfg, m) for m in LAYER_B},
            "catalogs": {m: (cfg.output / ("%s_indicator_catalog.csv" % m)).exists() for m in MODULES},
            "equations": {m: (cfg.output / ("%s_equations.json" % m)).exists() for m in MODULES},
            "engine": engine.available(),
            "dry_run_runs": cfg.dry_run_runs,
            "events": apidb.events(cfg.db, 15)}
