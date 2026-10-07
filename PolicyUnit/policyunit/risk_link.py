"""FR4 — integration with the RiskUnit (MİİS §15.5.3) ONLY over HTTP (`config.RISK_API`, tokens
demo-read / demo-write unless POLICY_RISK_TOKEN_READ/WRITE are set). Never imports riskunit.

* `Client` — GET/POST with a response cache under work/risk_cache/ (key = sha1 of method+path+body).
  POLICY_NO_NETWORK=1 or an unreachable server -> the last cached response is reused and the status
  says so ("keş (tarix)"); nothing cached -> "əlçatmaz" (rows with NaN, never a crash).
* `server()` — context manager: starts `RiskUnit/api/server.py --db PU/work/risk_scratch.db` in the
  background if no RiskUnit answers on the port, and stops it afterwards (only if we started it).
* `profile()` — conditional risk distributions with vs without the policy (P4_risk_profile).
* `mitigate()` — mitigation portfolio (RiskUnit optimize/run) + rule map + policy-specific proposals."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from . import config

CACHE = config.WORK / "risk_cache"
SCRATCH_DB = config.WORK / "risk_scratch.db"
ACTOR = "PolicyUnit-FR4"
TOK_R = os.environ.get("POLICY_RISK_TOKEN_READ", "demo-read")
TOK_W = os.environ.get("POLICY_RISK_TOKEN_WRITE", "demo-write")


class Client:
    def __init__(self, base: str | None = None, offline: bool | None = None, timeout: float = 180):
        self.base = (base or config.RISK_API).rstrip("/")
        self.offline = config.NO_NETWORK if offline is None else offline
        self.timeout = timeout
        self.log = []                                  # (path, status, fetched_at)
        self.memo = {}
        self.baseline = None                           # RiskUnit baseline_id the cache must match
        CACHE.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------ low level
    def _key(self, method, path, body):
        raw = method + " " + path + " " + json.dumps(body or {}, sort_keys=True, ensure_ascii=False)
        return hashlib.sha1(raw.encode()).hexdigest()[:20]

    def _http(self, method, path, body=None):
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode()
        tok = TOK_W if method != "GET" else TOK_R
        req = urllib.request.Request(f"{self.base}/{path.lstrip('/')}", data=data, method=method,
                                     headers={"Authorization": f"Bearer {tok}", "X-Actor": ACTOR,
                                              "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode())

    def alive(self) -> bool:
        if self.offline:
            return False
        try:
            return self._http("GET", "health").get("status") == "ok"
        except Exception:  # noqa: BLE001
            return False

    def call(self, method: str, path: str, body=None, use_cache_first=False):
        """-> (response | None, status_az, fetched_at)."""
        k = self._key(method, path, body)
        if k in self.memo:                             # identical request within one run
            return self.memo[k]
        out = self._call(k, method, path, body, use_cache_first)
        if out[0] is not None:
            self.memo[k] = out
        return out

    def _call(self, k, method, path, body, use_cache_first):
        f = CACHE / f"{k}.json"
        if not self.offline and not use_cache_first:
            try:
                res = self._http(method, path, body)
                at = time.strftime("%Y-%m-%d %H:%M:%S")
                bid = (res.get("baseline_id") if isinstance(res, dict) else None) or self.baseline
                f.write_text(json.dumps({"fetched_at": at, "method": method, "path": path, "request": body,
                                         "baseline_id": bid, "response": res}, ensure_ascii=False), encoding="utf-8")
                self.log.append((path, "canlı", at))
                return res, "canlı", at
            except urllib.error.HTTPError as e:          # 4xx/5xx: Azerbaijani message of the RiskUnit
                try:
                    msg = json.loads(e.read().decode()).get("error", {}).get("message", str(e))
                except Exception:  # noqa: BLE001
                    msg = str(e)
                self.log.append((path, f"xəta {e.code}", ""))
                return None, f"RiskUnit xətası {e.code}: {msg}", ""
            except Exception:  # noqa: BLE001 — server absent: fall back to the cache
                pass
        if f.exists():
            d = json.loads(f.read_text(encoding="utf-8"))
            st = f"keş ({d['fetched_at']})" + ("; POLICY_NO_NETWORK=1" if self.offline else "; server əlçatmazdır")
            self.log.append((path, st, d["fetched_at"]))
            return d["response"], st, d["fetched_at"]
        self.log.append((path, "əlçatmaz", ""))
        return None, "əlçatmaz (server yoxdur və keş tapılmadı)", ""


def current_baseline() -> str | None:
    """RiskUnit's current baseline vintage id (its last pipeline run; read-only summary file)."""
    try:
        return json.loads((config.RISK_ROOT / "output" / "_run_summary_v2.json").read_text(encoding="utf-8"))["baseline_id"]
    except Exception:  # noqa: BLE001
        return None


def server_baseline(c: Client) -> str | None:
    """Baseline id the running server works with (it reads RiskUnit outputs at start)."""
    try:
        return c._http("GET", "status").get("baseline_id")
    except Exception:  # noqa: BLE001
        return None


def purge_stale(baseline: str | None, log=print) -> int:
    """Delete cached responses of another RiskUnit baseline vintage."""
    if not baseline:
        return 0
    n = 0
    for f in CACHE.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            bid = d.get("baseline_id") or (d.get("response") or {}).get("baseline_id")
        except Exception:  # noqa: BLE001
            bid = None
        if bid != baseline:
            f.unlink(missing_ok=True)
            n += 1
    if n:
        log(f"  RiskUnit keşi: {n} köhnə cavab silindi (cari baza {baseline})")
    return n


FALLBACK_PORTS = range(8793, 8800)       # 8791 RiskUnit API, 8792 PolicyUnit API, 8790 MicroUnit API


def free_port(ports=FALLBACK_PORTS) -> str | None:
    """First free local port for a RiskUnit server started by FR4 itself."""
    import socket
    for p_ in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_:
            try:
                s_.bind(("127.0.0.1", p_))
                return str(p_)
            except OSError:
                continue
    return None


def _start(c: Client, port: str, wait_s: float, log):
    script = config.RISK_ROOT / "api" / "server.py"
    if not script.exists():
        log(f"  RiskUnit server.py tapılmadı: {script} — keşdən istifadə olunur")
        return None
    config.LOGS.mkdir(parents=True, exist_ok=True)
    out = open(config.LOGS / "risk_server.log", "a", encoding="utf-8")
    db = SCRATCH_DB if port == "8791" else SCRATCH_DB.with_name(f"risk_scratch_{port}.db")
    proc = subprocess.Popen([sys.executable, str(script), "--port", port, "--db", str(db), "--quiet"],
                            stdout=out, stderr=subprocess.STDOUT, env=dict(os.environ, RISK_NO_NETWORK="1"),
                            cwd=str(config.RISK_ROOT))
    t0 = time.time()
    while time.time() - t0 < wait_s and not c.alive():
        if proc.poll() is not None:
            break
        time.sleep(0.5)
    log(f"  RiskUnit API başladıldı (port {port}, pid {proc.pid}, {'hazır' if c.alive() else 'cavab vermir'}; "
        f"{time.time() - t0:.1f} s)")
    return proc


def _stop(proc, log):
    if proc is None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    log(f"  RiskUnit API dayandırıldı (pid {proc.pid}; bu iş tərəfindən başladılmışdı)")


@contextlib.contextmanager
def server(client: Client | None = None, wait_s: float = 60, log=print):
    """Yield a Client on a RiskUnit server whose baseline equals RiskUnit's current baseline_id:
    start one (scratch DB) if none answers; if OUR server is stale, restart it; if a foreign server on the port
    is stale, start our own on the first free port 8793–8799 (never 8792 = PolicyUnit API; a
    server we did not start is never stopped). Cached responses of another baseline are purged. Our servers are stopped."""
    c = client or Client()
    c.baseline = current_baseline()
    procs = []
    if not c.offline:
        u = urlparse(c.base)
        port = str(u.port or 8791)
        if not c.alive():
            procs.append(_start(c, port, wait_s, log))
        sb = server_baseline(c) if c.alive() else None
        if c.baseline and sb and sb != c.baseline:
            if procs and procs[-1] is not None:
                log(f"  RiskUnit serverinin bazası köhnədir ({sb} ≠ {c.baseline}) — yenidən başladılır")
                _stop(procs.pop(), log)
                procs.append(_start(c, port, wait_s, log))
            else:                                   # never touch a foreign server; 8792 = PolicyUnit API
                alt = free_port()
                if alt is None:
                    log("  XƏBƏRDARLIQ: 8793–8799 aralığında boş port yoxdur — köhnə bazalı server istifadə olunur")
                    alt = port
                log(f"  {port} portundakı RiskUnit serveri (bizim deyil) köhnə bazadadır ({sb} ≠ {c.baseline}) — "
                    f"öz serverimiz {alt} portunda başladılır")
                if alt != port:
                    c.base = c.base.replace(f":{port}", f":{alt}")
                    c.fallback_port = alt                 # recorded (log + Client attribute)
                    procs.append(_start(c, alt, wait_s, log))
            sb = server_baseline(c)
        if sb and c.baseline and sb != c.baseline:
            log(f"  XƏBƏRDARLIQ: RiskUnit serverinin bazası ({sb}) cari bazadan ({c.baseline}) fərqlidir")
        c.baseline = sb or c.baseline
    purge_stale(c.baseline, log)
    try:
        yield c
    finally:
        for p_ in procs:
            _stop(p_, log)


def sigma(c: Client) -> dict:
    """Factor σ (log units) from GET stress/inputs (cached)."""
    r, _, _ = c.call("GET", "stress/inputs")
    out = {}
    for f in (r or {}).get("factors", []):
        if f.get("amil") in ("brent", "fx"):
            out[f["amil"]] = float(f["sigma"])
    return out


# ------------------------------------------------------------------ conditional risk distributions
import math  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import norm  # noqa: E402

QS = (5, 10, 25, 50, 75, 90, 95)
KIND_AZ = {"g": "qeyri-neft artımı (f.b.)", "cpi": "inflyasiya (f.b.)", "fis": "büdcə balansı (% ÜDM)"}
CHAIN_ID = {"g": "ru:nonoil_g", "cpi": "ru:cpi", "fis": "ru:budget_gdp"}
DUMMY_RU = {"lend_dev": [0.0] * 5}          # neutral RU key: returns the distributions, shifts nothing
RISK_COLS = ["scenario", "variant", "variant_name_az", "kind", "indicator_az", "year", "threshold", "P_without",
             "P_with", "dP", "ES10_without", "ES10_with", "dES10", "es_method", "p10_without", "p10_with",
             "median_without", "median_with", "esas_menbe", "source", "esas_menbe_izah", "ru_policy_shift", "P_with_ru",
             "dP_ru", "shift_pu", "P_with_pu", "dP_pu",
             "agree_dP", "ru_chain_shift", "note_az", "status", "baseline_id", "fetched_at"]


def policy_shift(frame: pd.DataFrame, s: dict, base_g=None) -> dict:
    """Policy effect on the three RU kinds per year 2026–2030 (PolicyUnit core results, P1)."""
    from .side_effects import View
    V = View(frame, s)
    Y = config.MICRO_YEARS
    base_g = base_g or [5.0] * len(Y)

    def path(ind, col):
        g = V.ind(ind)
        d = dict(zip(g.year, g[col])) if len(g) else {}
        return [float(d.get(y, 0.0)) if np.isfinite(d.get(y, 0.0)) else 0.0 for y in Y]
    L, out, prev = path("gdp_nonoil_real", "delta_pct"), [], 0.0
    for i, lt in enumerate(L):
        out.append(100 * ((1 + lt / 100) / (1 + prev / 100) - 1) * (1 + base_g[i] / 100))
        prev = lt
    return {"g": out, "cpi": path("infl", "delta"), "fis": path("budget_balance_pct", "delta")}


def _cdf(x, row, h, P_h, side):
    pts = sorted([(row[f"p{q:02d}"], q / 100) for q in QS] + [(h, P_h if side == "<" else 1 - P_h)])
    xs, ps = np.array([p[0] for p in pts]), np.maximum.accumulate([p[1] for p in pts])
    sl = max((row["p10"] - row["p05"]) / 0.3633, 1e-6)
    su = max((row["p95"] - row["p90"]) / 0.3633, 1e-6)
    if x < xs[0]:
        return float(norm.cdf(norm.ppf(min(max(ps[0], 1e-6), 1 - 1e-6)) + (x - xs[0]) / sl))
    if x > xs[-1]:
        return float(norm.cdf(norm.ppf(min(max(ps[-1], 1e-6), 1 - 1e-6)) + (x - xs[-1]) / su))
    return float(np.interp(x, xs, ps))


def _es_approx(row, side):
    if side == "<":
        return row["p10"] - 0.4734 * (row["p10"] - row["p05"]) / 0.3633
    return row["p90"] + 0.4734 * (row["p95"] - row["p90"]) / 0.3633


def primary_source(s: dict, overrides) -> tuple[str, str]:
    """Primary-source rule for the with-policy risk figures (doc §4):
    (c) FX/devaluation -> RiskUnit (its calibrated FX pass-through layer riskunit/fx.py, 2015–18, is absent
        from the PolicyUnit chain); (b) PU-only overlays/financing (SOFAZ/tax/reallocation financing, direct
        cost outside FR1, VAT/tax/subsidy proxies) or no micro_overrides -> PolicyUnit shift, RiskUnit =
        cross-check; (a) scenario fully represented by micro_overrides -> RiskUnit."""
    if any(it["instrument"] == "fx_deval" for it in s["instruments"]):
        return ("RiskUnit", "(c) məzənnə ssenarisi: RiskUnit əsasdır — onun kalibrlənmiş məzənnə ötürmə qatı "
                "(riskunit/fx.py, 2015–2018 kalibrasiyası) PolicyUnit zəncirində yoxdur; hər iki rəqəm göstərilir")
    if not overrides:
        return ("PolicyUnit", "(b) micro_overrides yoxdur (yalnız overlay/CAEM kanalı): PolicyUnit sürüşməsi əsasdır, "
                "RiskUnit çarpaz yoxlamadır")
    try:
        from . import eng_micro
        m = eng_micro.plan(s)
        pu_only = bool(m["use_overlay"] or m["proxy"])
    except Exception:  # noqa: BLE001
        pu_only = False
    if pu_only:
        return ("PolicyUnit", "(b) ssenaridə RiskUnit-in görmədiyi PolicyUnit overlay/maliyyələşmə kanalı var (ARDNF/vergi "
                "maliyyələşməsi, FR1-dən kənar xərc, proksi): PolicyUnit sürüşməsi əsasdır, RiskUnit çarpaz yoxlamadır")
    return ("RiskUnit", "(a) ssenari tam micro_overrides ilə təmsil olunur: RiskUnit əsasdır, PolicyUnit çarpaz yoxlamadır")


def _rows(sid, var, dist, metrics, shift, chain, score_year, status, bid, at, base_view, pol_view, ru_shift, note,
          primary=("RiskUnit", "")):
    """One row per kind × year. Primary with-policy figures = RiskUnit's own policy view (pol_view) when the
    request carried micro_overrides; PolicyUnit's location shift of base_view by P1 effects = cross-check (_pu)."""
    out = []
    idx = {(r["baxis"], r["kind"], int(r["il"])): r for r in dist}
    for (view, k, y), r in idx.items():
        if view != base_view:
            continue
        side, h = r["hedd"].split()[0], float(r["hedd"].split()[1])
        d = shift[k][config.MICRO_YEARS.index(y)]
        pu = _cdf(h - d, r, h, r["P_hedd"], side)
        pu = pu if side == "<" else 1 - pu
        exact = y == score_year and metrics.get(k, {}).get(base_view)
        es0 = r.get("ES10")
        if es0 is None:
            es0 = metrics[k][base_view]["ES10"] if exact else _es_approx(r, side)
        rp = idx.get((pol_view, k, y)) if pol_view else None
        pru = rp["P_hedd"] if rp is not None else np.nan
        if rp is not None and primary[0] == "RiskUnit":
            pw, esw, p10w, medw, src = rp["P_hedd"], rp.get("ES10", es0 + ru_shift.get((k, y), 0.0)), rp["p10"], \
                rp["p50"], "RiskUnit stress/run (siyasət baxışı)"
            em = "RiskUnit"
        else:
            pw, esw, p10w, medw = pu, es0 + d, r["p10"] + d, r["p50"] + d
            src, em = "PolicyUnit sürüşməsi (P1 əsas metod)", "PolicyUnit"
        out.append({"scenario": sid, "variant": var[0], "variant_name_az": var[1], "kind": k,
                    "indicator_az": KIND_AZ[k], "year": y, "threshold": r["hedd"], "P_without": r["P_hedd"],
                    "P_with": pw, "dP": pw - r["P_hedd"], "ES10_without": es0, "ES10_with": esw, "dES10": esw - es0,
                    "es_method": "RiskUnit dəqiq" if r.get("ES10") is not None or exact else "kvantillərdən təxmin",
                    "p10_without": r["p10"], "p10_with": p10w, "median_without": r["p50"], "median_with": medw,
                    "esas_menbe": em, "source": src, "esas_menbe_izah": primary[1],
                    "ru_policy_shift": ru_shift.get((k, y), np.nan), "P_with_ru": pru, "dP_ru": pru - r["P_hedd"],
                    "shift_pu": d, "P_with_pu": pu, "dP_pu": pu - r["P_hedd"], "agree_dP": abs(pru - pu),
                    "ru_chain_shift": chain.get((k, y), np.nan), "note_az": note, "status": status,
                    "baseline_id": bid, "fetched_at": at})
    return out


def _empty(sid, var, status):
    return [{**{c: np.nan for c in RISK_COLS}, "scenario": sid, "variant": var[0], "variant_name_az": var[1],
             "kind": k, "indicator_az": KIND_AZ[k], "status": status} for k in KIND_AZ]


def _ru_shift(r):
    return {(x["kind"], int(x["il"])): float(x["deyisme"]) for x in (r.get("ru") or {}).get("policy_shift") or []}


def _any_cached_unconditional():
    """Last cached stress/run response with the (scenario-independent) unconditional distribution."""
    best = None
    for f in CACHE.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        r = d.get("response") or {}
        if d.get("path") == "stress/run" and any(x.get("baxis") == "şərtsiz" for x in (r.get("ru") or {}).get("distribution", [])):
            if best is None or d["fetched_at"] > best[1]:
                best = (r, d["fetched_at"])
    if best is None:
        return None, "", ""
    return best[0], f"keş: başqa sorğunun şərtsiz paylanması ({best[1]})", best[1]


def profile(c: Client, s: dict, frame: pd.DataFrame, overrides: dict, variants: list[dict],
            vframes: dict, n: int = 4000, note: str = "") -> pd.DataFrame:
    """Base: RiskUnit unconditional ('şərtsiz') vs its policy view ('siyasətlə', micro_overrides applied as a
    deterministic shift of every draw). Adverse variants: 'şoka şərtli' vs 'şoka şərtli + siyasət'. Without
    micro_overrides (overlay-only / CAEM-only instruments) the PolicyUnit location shift is the primary figure."""
    sid, rows = s["id"], []
    body = {"name": f"PolicyUnit FR4 {sid}", "n": n, "with_measures": False, "top_components": 10}
    if overrides:
        body["micro_overrides"] = overrides
    else:
        body["ru_overrides"] = DUMMY_RU
    r, st, at = c.call("POST", "stress/run", body)
    if (r is None or not r.get("ru")) and overrides:
        # RiskUnit cannot take this scenario's overrides (or failed): distributions only, PU shift primary
        r, st2, at = c.call("POST", "stress/run", {k: v for k, v in body.items() if k != "micro_overrides"}
                            | {"ru_overrides": DUMMY_RU})
        st = f"{st2}; micro_overrides RiskUnit-də alınmadı ({st}) — PolicyUnit sürüşməsi əsasdır"
        overrides = None
    if r is None or not r.get("ru"):
        r, st3, at = _any_cached_unconditional()
        st = f"{st3}; bu ssenari üçün RiskUnit cavabı yoxdur ({st})" if r else st
    if r is None or not r.get("ru"):
        return pd.DataFrame(_empty(sid, ("base", "əsas ssenari"), st), columns=RISK_COLS)
    hy, bid = r.get("score_year"), r.get("baseline_id")
    dist = r["ru"]["distribution"]
    gb = [d["baza"] for d in sorted((d for d in dist if d["kind"] == "g" and d["baxis"] == "şərtsiz"),
                                    key=lambda d: d["il"])]
    chain = {}
    for h in ((r.get("micro") or {}).get("headline") or []):
        for k, cid in CHAIN_ID.items():
            if h["hedef_id"] == cid:
                chain[(k, int(h["il"]))] = h["delta"]
    prim = primary_source(s, overrides)
    pv = "siyasətlə" if overrides and any(d["baxis"] == "siyasətlə" for d in dist) else None
    rows += _rows(sid, ("base", "əsas ssenari"), dist, r["ru"]["metrics"], policy_shift(frame, s, gb), chain, hy,
                  st, bid, at, "şərtsiz", pv, _ru_shift(r), note, prim)
    for v in variants:
        if not v.get("ru") or v["id"] not in vframes:
            continue
        b2 = {"name": f"PolicyUnit FR4 şərt {v['id']}", "shocks": v["ru"]["shocks"], "n": n,
              "with_measures": False, "top_components": 5}
        if overrides:
            b2["micro_overrides"] = overrides
        r2, st2, at2 = c.call("POST", "stress/run", b2)
        if r2 is None or not r2.get("ru"):
            rows += _empty(sid, (v["id"], v["name_az"]), st2)
            continue
        d2 = r2["ru"]["distribution"]
        pv2 = "şoka şərtli + siyasət" if overrides and any(d["baxis"] == "şoka şərtli + siyasət" for d in d2) else None
        rows += _rows(sid, (v["id"], v["name_az"]), d2, r2["ru"]["metrics"], policy_shift(vframes[v["id"]], s, gb), {},
                      hy, st2, r2.get("baseline_id"), at2, "şoka şərtli", pv2, _ru_shift(r2), note, prim)
    return pd.DataFrame(rows, columns=RISK_COLS)


# ------------------------------------------------------------------ mitigation proposals
MIT_COLS = ["scenario", "priority", "source", "rule_id", "family", "risk_ids", "measure_id", "measure_az",
            "proposal_type", "proposal_az", "responsible_az", "cost_mln_azn", "role", "marginal_contrib", "kpi_az",
            "trigger_variant", "status"]
APP_KEY = {"g": "P_g_max", "cpi": "P_cpi_max", "fis": "P_fis_max"}


def load_map(path=None) -> pd.DataFrame:
    df = pd.read_csv(path or config.CONFIG / "mitigation_map.csv", dtype=str, keep_default_na=False)
    need = ["rule_id", "risk_ids", "measures", "proposal_type", "proposal_az", "responsible_az", "kpi_az"]
    miss = [x for x in need if x not in df.columns]
    if miss:
        raise ValueError("mitigation_map.csv: çatışmayan sütun(lar): " + ", ".join(miss))
    return df


def measures(c: Client) -> pd.DataFrame:
    r, _, _ = c.call("GET", "optimize/inputs")
    m = pd.DataFrame((r or {}).get("measures", []))
    return m.set_index("tedbir_id") if len(m) else m


def _row(sid, **kw):
    return {**{k: "" for k in MIT_COLS}, "scenario": sid, **kw}


def mitigate(c: Client, s: dict, se: list[dict], prof: pd.DataFrame, mmap: pd.DataFrame | None = None,
             appetite_default=None) -> pd.DataFrame:
    sid = s["id"]
    mmap = load_map() if mmap is None else mmap
    M = measures(c)
    base = [x for x in se if x["variant"] == "base"]
    only_adv = {x["rule_id"]: x for x in se if x["variant"] != "base"} 
    for x in base:
        only_adv.pop(x["rule_id"], None)
    trig = sorted(base, key=lambda x: -x["severity"]) + list(only_adv.values())
    rows, tids = [], []
    for x in trig:
        pr = "yüksək" if x["severity"] >= 3 else "orta" if x["severity"] == 2 else "aşağı"
        tv = "əsas ssenari" if x["variant"] == "base" else "yalnız: " + x["variant_name_az"]
        for _, m in mmap[mmap.rule_id == x["rule_id"]].iterrows():
            rows.append(_row(sid, priority=pr, source="siyasətə xas təklif (mitigation_map.csv)", rule_id=x["rule_id"],
                             family=x["family"], risk_ids=m["risk_ids"], proposal_type=m["proposal_type"],
                             proposal_az=m["proposal_az"], responsible_az=m["responsible_az"], kpi_az=m["kpi_az"],
                             trigger_variant=tv, status="təklif"))
            for t in filter(None, m["measures"].split(";")):
                if t in tids:
                    continue
                tids.append(t)
                ok = len(M) and t in M.index
                rows.append(_row(sid, priority=pr, source="RiskUnit tədbir reyestri (T01–T30)", rule_id=x["rule_id"],
                                 family=x["family"], risk_ids=M.at[t, "risk_idler"] if ok else m["risk_ids"],
                                 measure_id=t, measure_az=M.at[t, "tedbir"] if ok else "",
                                 proposal_type=M.at[t, "strategiya_v2"] if ok else "",
                                 responsible_az=M.at[t, "mesul"] if ok else "",
                                 cost_mln_azn=float(M.at[t, "xerc_mln_azn"]) if ok else np.nan,
                                 trigger_variant=tv, status=M.at[t, "status"] if ok else "reyestr əlçatmaz"))
    if not tids:
        return pd.DataFrame(rows, columns=MIT_COLS)
    inc = [t for t in tids if len(M) and t in M.index and M.at[t, "status"] != "dayandırılıb"]
    cost = float(sum(M.at[t, "xerc_mln_azn"] for t in inc)) if inc else 0.0
    app = {}
    b = prof[(prof.variant == "base")].dropna(subset=["dP"])
    if len(b):                                  # year in which the policy raises each risk most
        b = b.loc[b.groupby("kind")["dP"].idxmax()]
        dflt = appetite_default or {"P_g_max": 0.2, "P_cpi_max": 0.5, "P_fis_max": 0.4}
        for r in b.itertuples():
            if r.dP > 0.005:
                app[APP_KEY[r.kind]] = round(max(0.02, dflt[APP_KEY[r.kind]] - r.dP), 4)
    body = {"budget": round(max(100.0, 1.2 * cost + 50.0), 1), "include": inc}
    if app:
        body["appetite"] = app
    r, st, _ = c.call("POST", "optimize/run", body)
    if r is None:
        rows.append(_row(sid, source="RiskUnit optimize/run", status=st))
        return pd.DataFrame(rows, columns=MIT_COLS)
    note = (f"büdcə {body['budget']} mln AZN; risk iştahı siyasətin əlavə etdiyi risk qədər sərtləşdirilib: {app}"
            if app else f"büdcə {body['budget']} mln AZN; standart risk iştahı")
    for p in r.get("portfolio", []):
        rows.append(_row(sid, priority="portfel", source="RiskUnit optimize/run", measure_id=p["tedbir_id"],
                         measure_az=p["tedbir"], proposal_type=p["strategiya_v2"], responsible_az=p["mesul"],
                         cost_mln_azn=p["xerc_mln_azn"], role=p["rol"], marginal_contrib=p["marginal_tohfe"],
                         proposal_az=note, status=st))
    rids = {i for x in trig for i in str(x["risk_ids"]).split(";") if i}
    for q in r.get("residual", []):
        if q["risk_id"] in rids:
            rows.append(_row(sid, priority="qalıq risk", source="RiskUnit qalıq risk (plan sonrası)", risk_ids=q["risk_id"],
                             measure_id=q.get("plandaki_tedbirler", ""), measure_az=q.get("ad", ""),
                             proposal_az=f"qalıq skor {q.get('qaliq_skor_plan')}, prioritet {q.get('qaliq_prioritet')}",
                             status=st))
    return pd.DataFrame(rows, columns=MIT_COLS)


def financing_proposal(s: dict, se: list[dict]) -> list[dict]:
    """Compare the base financing with the generated alternative: fiscal side effects that disappear."""
    b = {x["rule_id"]: x for x in se if x["variant"] == "base" and x["family"] in ("fiskal sürüşmə", "borc dayanıqlılığı")}
    a = {x["rule_id"]: x for x in se if x["variant"] == "fin_alt"}
    if not b or not any(x["variant"] == "fin_alt" for x in se):
        return []
    gone = [k for k in b if k not in a or a[k]["severity"] < b[k]["severity"]]
    new = [k for k in a if k not in b and a[k]["family"] in ("sosial bölgü", "inflyasiya")]
    if not gone:
        return []
    name = next(x["variant_name_az"] for x in se if x["variant"] == "fin_alt")
    txt = (f"{name}: {', '.join(gone)} yan təsir(lər)i aradan qalxır və ya zəifləyir"
           + (f"; lakin yeni yan təsir(lər): {', '.join(new)}" if new else ""))
    return [_row(s["id"], priority="orta", source="FR4 alternativ maliyyələşmə ssenarisi", rule_id=";".join(gone),
                 family="fiskal sürüşmə", proposal_type="maliyyələşmə", proposal_az=txt,
                 responsible_az="Maliyyə Nazirliyi", trigger_variant="fin_alt", status="təklif")]


def kpi_inputs(sid: str, se: list[dict], prof: pd.DataFrame, start: int) -> list[dict]:
    out = [{"scenario": sid, "kpi": "side_effects", "value": float(sum(1 for x in se if x["variant"] == "base"))}]
    g = prof[(prof.variant == "base") & (prof.kind == "g") & (prof.year >= start)]["dES10"].dropna()
    if len(g):
        out.append({"scenario": sid, "kpi": "risk_es", "value": round(float(g.mean()), 4)})
    return out
