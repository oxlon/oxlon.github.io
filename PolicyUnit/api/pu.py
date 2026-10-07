"""
pu — körpü: API PolicyUnit paketinin (policyunit/*) yalnız açıq funksiyalarını çağırır (scenario, registry,
integrate, kpi, compare, side_effects, risk_link, microbridge, caem_core). Paket bu faylın yanındakı PolicyUnit/
qovluğundan idxal olunur; mühərrik çağırışları ENGINE_LOCK ilə ardıcıllaşdırılır (MikroUnit zənciri, CAEM iş kitabı
axın-təhlükəsiz deyil). Sınaqlarda `bind(cfg)` konfiqurasiya qovluğunu müvəqqəti surətə yönəldir.
"""
import hashlib, importlib, json, os, sys, threading, time
from pathlib import Path

from apicore import DEFAULT_ROOT, ApiError, read_json
from az_errors import az_exc

PU_ROOT = DEFAULT_ROOT
if str(PU_ROOT) not in sys.path:
    sys.path.insert(0, str(PU_ROOT))

ENGINE_LOCK = threading.RLock()
UNIT_AZ = {"pct": "bazaya nisbətən %", "pp": "faiz bəndi (f.b.)", "mln_azn": "mln AZN / il (nominal)", "abs": "mütləq dəyər"}
FINANCING_AZ = {"deficit": "kəsir (borcla)", "sofaz": "ARDNF transferti", "tax": "vergi artımı",
                "reallocation": "xərclərin yenidən bölüşdürülməsi", None: "maliyyələşmə tələb olunmur"}
HORIZON_AZ = {"qısa": "qısa müddət (başlanğıc il və növbəti il: t0, t0+1)", "orta": "orta müddət (başlanğıc ildən 2–3 il sonra: t0+2…t0+3)",
              "uzun": "uzun müddət (≥ t0+4, yəni 5-ci il və sonrası)"}
CONFIG_FILES = ("instruments.csv", "adapters.csv", "kpi.csv", "tax_benefit.csv", "fiscal_params.csv", "longrun_params.csv",
                "side_effect_rules.csv", "mitigation_map.csv", "io_sectors.csv", "indicators.csv")


def P(name):
    """policyunit.<name> (lazy import; ApiError 503 with an Azerbaijani message when missing)."""
    try:
        return importlib.import_module("policyunit." + name)
    except ModuleNotFoundError as e:
        raise ApiError(503, "module_missing", "PolicyUnit modulu tapılmadı: policyunit.%s" % name, detail=str(e))


def call(fn, *a, **kw):
    """Serialised engine call; Python errors → 422 with an Azerbaijani explanation."""
    with ENGINE_LOCK:
        try:
            return fn(*a, **kw)
        except ApiError:
            raise
        except Exception as e:
            raise ApiError(422, "engine_error", "Hesablama alınmadı: %s" % az_exc(e),
                           detail="%s: %s" % (type(e).__name__, str(e)[:500]))


def bind(cfg):
    """Point policyunit.config at cfg.config_dir / cfg.root (only when they differ from the package defaults)."""
    c = P("config")
    if Path(cfg.config_dir) != Path(c.CONFIG):
        c.CONFIG, c.SCENARIOS = Path(cfg.config_dir), Path(cfg.config_dir) / "scenarios"
        for attr, fn in (("INSTRUMENTS_CSV", "instruments.csv"), ("ADAPTERS_CSV", "adapters.csv"), ("KPI_CSV", "kpi.csv"),
                         ("FISCAL_PARAMS_CSV", "fiscal_params.csv"), ("LONGRUN_PARAMS_CSV", "longrun_params.csv"),
                         ("INDICATORS_CSV", "indicators.csv"), ("IO_SECTORS_CSV", "io_sectors.csv")):
            setattr(c, attr, Path(cfg.config_dir) / fn)
    if Path(cfg.root) != Path(c.ROOT):
        c.OUTPUT = Path(cfg.root) / "output"
    reload()


def reload():
    try:
        P("registry").reload()
    except ApiError:
        pass


# ------------------------------------------------------------------ engines
_ENG = {"at": 0, "rows": None}


def engines(max_age=120):
    """[{id, label_az, available, message_az}] — import check of every engine plug-in (cached)."""
    if _ENG["rows"] is not None and time.time() - _ENG["at"] < max_age:
        return _ENG["rows"]
    c, reg = P("config"), P("registry")
    rows = []
    for e in c.ENGINE_ORDER:
        try:
            with ENGINE_LOCK:
                mod = reg.engine_module(e)
            ok = mod is not None
            msg = "" if ok else "modul hələ qoşulmayıb"
            why = getattr(mod, "unavailable_reason", None)
            if ok and callable(why) and why():                  # e.g. OxLon off in hosted CI
                ok, msg = False, why()
        except Exception as ex:
            ok, msg = False, "modul yüklənmədi: %s: %s" % (type(ex).__name__, str(ex)[:200])
        rows.append({"id": e, "label_az": c.ENGINE_LABEL_AZ.get(e, e), "available": ok, "message_az": msg})
    _ENG.update(at=time.time(), rows=rows)
    return rows


# ------------------------------------------------------------------ vintage (baseline ids)
def _md5(p, n=None):
    h = hashlib.md5()
    try:
        with open(p, "rb") as f:
            for blk in iter(lambda: f.read(1 << 20), b""):
                h.update(blk)
    except OSError:
        return None
    return h.hexdigest()[:n] if n else h.hexdigest()


_VIN = {}


def _memo(key, paths, fn):
    """Recompute fn() only when (size, mtime) of the paths change."""
    sig = []
    for p in paths:
        try:
            st = os.stat(p)
            sig.append((str(p), st.st_size, st.st_mtime_ns))
        except OSError:
            sig.append((str(p), None))
    hit = _VIN.get(key)
    if hit and hit[0] == sig:
        return hit[1]
    v = fn()
    _VIN[key] = (sig, v)
    return v


def config_hash(cfg):
    files = [Path(cfg.config_dir) / f for f in CONFIG_FILES]
    return _memo("config", files, lambda: hashlib.md5("".join(str(_md5(p)) for p in files).encode()).hexdigest()[:12])


def vintage(cfg):
    """Baseline vintage ids of the CURRENT upstream state + one combined `vintage_id`."""
    c = P("config")
    mf = [c.MICRO_ROOT / "output" / n for n in ("FR1_equations.json", "FR1_forecast_full.csv", "FR1_multipliers.csv")]
    out = {"micro_vintage": _memo("micro", mf, lambda: P("microbridge").vintage()["micro_vintage"])}
    cp = c.CAEM_COPY
    out["caem_md5"] = _memo("caem", [cp], lambda: _md5(cp))
    out["caem_pinned_ok"] = out["caem_md5"] == c.CAEM_MD5
    up = c.CAEM_UPSTREAM
    out["caem_upstream_md5"] = _memo("caem_up", [up], lambda: _md5(up))
    fl = c.OXLON_ROOT / "delivery" / "2_neticeler" / "forecast_long.csv"
    out["oxlon_forecast_md5"] = _memo("oxlon", [fl], lambda: _md5(fl, 12))
    man = c.DATA / "io" / "MANIFEST_md5.csv"
    out["io_manifest_md5"] = _memo("io", [man], lambda: _md5(man, 12))
    rs = c.RISK_ROOT / "output" / "_run_summary_v2.json"
    out["risk_baseline_id"] = _memo("risk", [rs], lambda: (read_json(rs) or {}).get("baseline_id"))
    out["config_hash"] = config_hash(cfg)
    key = "|".join(str(out[k]) for k in ("micro_vintage", "caem_md5", "oxlon_forecast_md5", "io_manifest_md5",
                                          "risk_baseline_id", "config_hash"))
    out["vintage_id"] = "PV-" + hashlib.md5(key.encode()).hexdigest()[:10]
    return out


def last_run_meta(cfg):
    return read_json(Path(cfg.output) / "P1_run_meta.json") or {}


def risk_api_state(cfg, timeout=1.5):
    import urllib.request
    base = (cfg.risk_api or P("config").RISK_API).rstrip("/")
    if os.environ.get("POLICY_NO_NETWORK") == "1":
        return {"url": base, "ok": False, "message_az": "POLICY_NO_NETWORK=1 — RiskUnit keşdən oxunur"}
    try:
        with urllib.request.urlopen(base + "/health", timeout=timeout) as r:
            ok = json.loads(r.read().decode()).get("status") == "ok"
        return {"url": base, "ok": ok, "message_az": "işləyir" if ok else "cavab gözlənilən deyil"}
    except Exception as e:
        return {"url": base, "ok": False, "message_az": "əlçatmazdır (%s) — hesablamada avtomatik başladılır və ya keş "
                                                     "istifadə olunur" % az_exc(e)}


def horizons(start):
    eb = P("engine_base")
    c = P("config")
    out = {}
    for y in range(int(start), c.LONG_END + 1):
        out.setdefault(eb.horizon(y, start), []).append(y)
    return {k: {"years": v, "label_az": HORIZON_AZ[k]} for k, v in out.items()}
