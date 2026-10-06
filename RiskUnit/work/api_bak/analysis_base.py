"""
analysis_base — canlı analiz üçün ortaq vəziyyət: riskunit modullarının (scalability, simulate, optimize) yaddaşda
saxlanılan hazırlıqları, amil şoklarının həlli (k σ ↔ təbii vahid), MikroUnit override-larının birləşdirilməsi
və amil şoklarının RU birgə Monte Karlo şok açarlarına uyğunlaşdırılması.

riskunit modulları dəyişdirilmir — yalnız onların funksiyaları çağırılır. Keş açarı = baseline_id + MikroUnit
mühərrikinin barmaq izi; biri dəyişəndə hazırlıq yenidən qurulur (NFR2).
"""
import sys, threading, time

from apicore import ApiError

RU_KEYS = {"brent_path": "USD/barel", "partner_dev": "f.b. (artım sapması)", "remit_dev": "% (artım sapması)",
           "lend_dev": "f.b.", "spi": "SPI vahidi", "quake_damage": "% ÜDM", "imp_dev": "f.b.", "food_dev": "f.b.",
           "deval_year": "il"}
MICRO_ONLY = {"gas", "state_inv", "costpush", "npl"}


def ensure_path(root):
    p = str(root)
    if p not in sys.path:
        sys.path.insert(0, p)


class Base:
    """Lazy, thread-safe holder of the expensive preparations."""

    def __init__(self, cfg):
        self.cfg = cfg
        ensure_path(cfg.root)
        self.lock = threading.RLock()
        self._sc = None
        self.timings = {}

    # ------------------------------------------------------------ modules
    @property
    def mods(self):
        from riskunit import config, factors, scalability, simulate, spine
        return config, factors, scalability, simulate, spine

    def key(self):
        config, factors, sc, simulate, spine = self.mods
        try:
            bid = spine.baseline_id()
        except Exception:
            bid = "?"
        return bid + "|" + sc.engine_fingerprint() + "|" + config.as_of().isoformat()

    # ------------------------------------------------------------ scalability preparation
    def sc_state(self):
        with self.lock:
            k = self.key()
            if self._sc and self._sc["key"] == k:
                return self._sc
            config, factors, sc, simulate, spine = self.mods
            t0 = time.time()
            D = sc.factor_data()
            S = sc.factor_specs(D)
            live = sc.live_deviations(S, D)
            base, _ = sc.run_chain({}, "api-baseline")
            st = {"key": k, "D": D, "S": S, "live": live, "base": base, "bl": sc.base_levels(base), "lab": sc.labels(),
                  "cat": sc.micro_catalog(), "years": list(sc.YEARS), "hy": config.score_year(),
                  "S0": sc.sigma_table(S, live)}
            ref = simulate.run(n=200)
            st["centre"] = [float(x) for x in ref.meta["brent_centre"]]
            st["sim_cache"] = {}
            self.timings["sc_prepare_s"] = round(time.time() - t0, 2)
            self._sc = st
            return st

    def sim(self, n, overrides=None, cache_key=None):
        """simulate.run with an in-memory cache for the reference runs."""
        st = self.sc_state()
        simulate = self.mods[3]
        if cache_key is not None and (cache_key, n) in st["sim_cache"]:
            return st["sim_cache"][(cache_key, n)]
        r = simulate.run(n=n, overrides=overrides)
        if cache_key is not None:
            st["sim_cache"][(cache_key, n)] = r
        return r

    # ------------------------------------------------------------ shocks
    def resolve(self, shock):
        """{"factor", "k_sigma" | "size"} → dict(factor, k, size, ov, spec)."""
        st = self.sc_state()
        if not isinstance(shock, dict) or not shock.get("factor"):
            raise ApiError(400, "bad_shock", "Hər şokda «factor» sahəsi olmalıdır (məs. {\"factor\": \"brent\", \"k_sigma\": -2})")
        f = str(shock["factor"]).strip()
        if f not in st["S"]:
            raise ApiError(400, "unknown_factor", "Naməlum amil: %r. Mümkün olanlar: %s" % (f, ", ".join(st["S"])))
        spec = st["S"][f]
        if shock.get("k_sigma") is not None:
            k = _num(shock["k_sigma"], "k_sigma")
        elif shock.get("size") is not None:
            k = self.k_for_size(f, _num(shock["size"], "size"))
        else:
            raise ApiError(400, "bad_shock", "«%s» üçün k_sigma və ya size verilməlidir" % f)
        if abs(k) > 6:
            raise ApiError(400, "bad_shock", "Şok ölçüsü ±6σ-dan böyük ola bilməz (%s: %.2fσ)" % (f, k))
        if spec["kind"] == "hazard" and k < 0:
            raise ApiError(400, "bad_shock", "«%s» birtərəfli təhlükədir: k_sigma ≥ 0 olmalıdır" % f)
        ov, size = spec["build"](k)
        return {"factor": f, "ad": spec["ad"], "k_sigma": k, "size": float(size), "vahid": spec["vahid"],
                "risk_idler": spec["risk_idler"], "kanal": spec["kanal"], "ov": ov}

    def k_for_size(self, f, size):
        """Natural-unit size → k σ by bisection on the spec's own size function (monotone in k)."""
        spec = self.sc_state()["S"][f]
        lo, hi = (0.0, 6.0) if spec["kind"] == "hazard" else (-6.0, 6.0)
        s = lambda k: float(spec["build"](k)[1])  # noqa: E731
        a, b = s(lo), s(hi)
        if not (min(a, b) - 1e-9 <= size <= max(a, b) + 1e-9):
            raise ApiError(400, "bad_shock", "«%s» üçün ölçü %g mümkün aralıqdan kənardır [%.3g; %.3g] %s"
                           % (f, size, min(a, b), max(a, b), spec["vahid"]))
        inc = b > a
        for _ in range(60):
            m = (lo + hi) / 2
            if (s(m) < size) == inc:
                lo = m
            else:
                hi = m
        return (lo + hi) / 2


def _num(v, name):
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ApiError(400, "bad_parameter", "«%s» ədəd olmalıdır: %r" % (name, v))
    if x != x:
        raise ApiError(400, "bad_parameter", "«%s» ədəd olmalıdır" % name)
    return x


def merge_overrides(parts, coef_base):
    """Combine chain overrides: exogenous pct compound, add sum, values last-wins; coefficients as summed shifts
    from the engine value; RU.addf (one-year FR1 intercept impulses) summed per variable; RU.overlays AND-ed;
    levers update. Returns (merged, notes)."""
    import numpy as np
    out, notes = {}, []
    for ov in parts:
        for mod, d in (ov or {}).items():
            if not isinstance(d, dict):
                raise ApiError(400, "bad_override", "«%s» override obyekt olmalıdır" % mod)
            tgt = out.setdefault(mod, {})
            for sect, v in d.items():
                if sect == "exogenous":
                    ex = tgt.setdefault("exogenous", {})
                    for var, spec in v.items():
                        cur = ex.get(var)
                        if cur is None:
                            ex[var] = dict(spec)
                        elif "pct" in spec and "pct" in cur:
                            cur["pct"] = ((1 + np.asarray(cur["pct"], float) / 100) * (1 + np.asarray(spec["pct"], float) / 100) - 1) * 100
                        elif "add" in spec and "add" in cur:
                            cur["add"] = np.asarray(cur["add"], float) + np.asarray(spec["add"], float)
                        else:
                            ex[var] = dict(spec)
                            notes.append("%s.%s: fərqli növ override-lar — sonuncu götürüldü" % (mod, var))
                elif mod == "RU" and sect == "addf":           # one-year FR1 equation shifts: SUM per variable
                    ad = tgt.setdefault("addf", {})
                    for var, vec in (v or {}).items():
                        ad[var] = (np.asarray(ad[var], float) + np.asarray(vec, float)) if var in ad else np.asarray(vec, float)
                elif mod == "RU" and sect == "overlays":
                    tgt["overlays"] = bool(tgt.get("overlays", True)) and bool(v)
                elif sect == "coefficients" and mod == "FR1":
                    co = tgt.setdefault("coefficients", {})
                    for key, val in v.items():
                        b = coef_base(key)
                        co[key] = co.get(key, b) + (float(val) - b)
                elif isinstance(v, dict):
                    tgt.setdefault(sect, {}).update(v)
                else:
                    tgt[sect] = v
    for var, vec in ((out.get("RU") or {}).get("addf") or {}).items():
        out["RU"]["addf"][var] = np.asarray(vec, float).tolist()
    for mod in out.values():
        for spec in (mod.get("exogenous") or {}).values():
            for k in ("pct", "add"):
                if k in spec and hasattr(spec[k], "tolist"):
                    spec[k] = spec[k].tolist()
    return out, notes
