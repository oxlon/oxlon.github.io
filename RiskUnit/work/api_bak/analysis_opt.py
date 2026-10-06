"""
analysis_opt — POST /optimize/run: büdcə + risk iştahı + daxil/xaric tədbirlər → optimal portfel (optimize.optimise:
MILP başlanğıcı + dəqiq yerli axtarış; məcburi/xaric tədbirlər fixed=/excluded= ilə), sərhəd nöqtəsi, metrikalar (baza vs plan), risk iştahının ödənilməsi, qalıq
risk (optimize.residual). Hazırlıq (optimize.prepare: RU Monte Karlo + MikroUnit cavabları) yaddaşda saxlanılır.
"""
import threading, time

from analysis_base import _num
from apicore import ApiError, as_list
from data_views import records

APPETITE_KEYS = ("P_g_max", "P_cpi_max", "P_fis_max", "CaR_max_mln_usd")


class Optimizer:
    def __init__(self, base):
        self.B = base
        self.lock = threading.RLock()
        self._st = None

    @property
    def opt(self):
        from riskunit import optimize
        return optimize

    def state(self):
        with self.lock:
            k = self.B.key()
            if self._st and self._st["key"] == k:
                return self._st
            o = self.opt
            t0 = time.time()
            C = o.prepare()
            M = o.measure_table(C)
            W = o.weights()
            m0 = o.evaluate(C, M, {})
            _, E = o.individual_effects(C, M, m0, W)
            self._st = {"key": k, "C": C, "M": M, "W": W, "m0": m0, "E": E, "A": o.appetite(),
                        "prepare_s": round(time.time() - t0, 2)}
            return self._st

    def inputs(self):
        st = self.state()
        o, M = self.opt, st["M"]
        cols = [c for c in ("tedbir", "risk_idler", "strategiya_v2", "mesul", "status", "xerc_mln_azn", "xerc_esasi",
                            "effekt_modeli", "effekt_kanal", "effekt_guc", "effekt_esasi") if c in M.columns]
        T = M[cols].reset_index().merge(st["E"][["tedbir_id", "effekt_hedef_funksiya", "xerc_effektivliyi_100mln",
                                                  "kemiyyet_metodu"]], on="tedbir_id", how="left")
        return {"measures": records(T), "appetite": st["A"], "budgets": list(o.BUDGETS), "plan_budgets": list(o.PLAN_BUDGETS),
                "metrics": {k: {"ad": v[0], "vahid": v[1], "yaxsi_istiqamet": "artım" if v[2] > 0 else "azalma"}
                            for k, v in o.METRICS_AZ.items()},
                "weights": st["W"], "base_metrics": {k: st["m0"][k] for k in o.METRICS_AZ}, "prepare_s": st["prepare_s"]}

    def run(self, req):
        t0 = time.time()
        req = req or {}
        st = self.state()
        o, C, M, W, m0, E = self.opt, st["C"], st["M"], st["W"], st["m0"], st["E"]
        A = dict(st["A"])
        for k, v in (req.get("appetite") or {}).items():
            if k not in APPETITE_KEYS:
                raise ApiError(400, "bad_parameter", "Naməlum risk iştahı açarı: %r (%s)" % (k, ", ".join(APPETITE_KEYS)))
            A[k] = _num(v, k)
        inc, exc = as_list(req.get("include")), as_list(req.get("exclude"))
        bad = [t for t in inc + exc if t not in M.index]
        if bad:
            raise ApiError(400, "unknown_measure", "Naməlum tədbir(lər): %s" % ", ".join(bad))
        if set(inc) & set(exc):
            raise ApiError(400, "bad_parameter", "Eyni tədbir həm daxil, həm xaric edilə bilməz: %s" % ", ".join(set(inc) & set(exc)))
        cost = lambda s: float(sum(M.at[t, "xerc_mln_azn"] for t in s))  # noqa: E731
        notes = []
        if req.get("selection"):
            sel = {}
            for t, w in req["selection"].items():
                if t not in M.index:
                    raise ApiError(400, "unknown_measure", "Naməlum tədbir: %s" % t)
                sel[t] = min(max(_num(w, t), 0.0), 1.0)
            m = o.evaluate(C, M, sel)
            plan, base_pkg, budget, mode = sorted(t for t, w in sel.items() if w > 0), [], None, "qiymətləndirmə"
        else:
            budget = _num(req.get("budget", 500), "budget")
            if budget < 0:
                raise ApiError(400, "bad_parameter", "Büdcə mənfi ola bilməz")
            cand = [t for t in M.index if M.at[t, "effekt_modeli"] != "none" and M.at[t, "status"] != "dayandırılıb"]
            base_pkg = [t for t in M.index if M.at[t, "effekt_modeli"] == "none" and M.at[t, "xerc_mln_azn"] <= 1.0
                        and t not in exc and t not in inc]
            r = o.optimise(C, M, E, m0, W, A, budget - cost(base_pkg), cand, fixed=inc, excluded=exc)
            if not r["budget_ok"]:
                raise ApiError(422, "over_budget", "Məcburi tədbirlərin xərci (%.1f mln AZN) büdcəni (%.1f) aşır"
                               % (cost(base_pkg) + cost(inc), budget))
            plan, m, mode = list(r["sel"]), r["m"], "optimallaşdırma"
            if inc:
                notes.append("Məcburi tədbirlər (%s) portfeldə sabit saxlanıldı (optimize.optimise fixed=)." % ", ".join(inc))
            if not r["appetite_feasible"]:
                notes.append("Bu büdcə ilə bütün risk iştahı hədlərini ödəmək mümkün deyil — hədəf funksiyası maksimallaşdırıldı.")
        obj = o.objective(m, m0, W, C)
        ok = o.appetite_ok(m, A)
        full = set(plan)
        port = []
        for t in plan + [x for x in base_pkg if x not in full]:
            marg = obj - o.objective(o.evaluate(C, M, {x: 1.0 for x in plan if x != t}), m0, W, C) if t in full else 0.0
            port.append({"tedbir_id": t, "tedbir": M.at[t, "tedbir"], "strategiya_v2": M.at[t, "strategiya_v2"],
                         "mesul": M.at[t, "mesul"], "xerc_mln_azn": float(M.at[t, "xerc_mln_azn"]),
                         "rol": ("məcburi" if t in inc else "optimal seçim" if t in full else "imkanlandırıcı minimum paket")
                         if mode == "optimallaşdırma" else "seçim", "marginal_tohfe": marg})
        metrics = [{"metrika": k, "ad": v[0], "vahid": v[1], "baza": m0[k], "plan": m[k], "delta": m[k] - m0[k],
                    "yaxsilasma": (m[k] - m0[k]) * v[2]} for k, v in o.METRICS_AZ.items()]
        R5 = o.residual(C, M, m0, set(plan), base_pkg)
        res = {"mode": mode, "budget": budget, "portfolio": port, "cost": cost(plan) + cost([x for x in base_pkg if x not in full]),
               "objective": obj, "metrics": metrics,
               "appetite": {"hedler": A, "odenilir": ok, "hamisi": all(ok.values())},
               "frontier_point": {"budce_mln_azn": budget, "xerc": cost(plan), "hedef_funksiya": obj},
               "residual": records(R5[R5["risk_id"] != "ÜMUMİ"]), "notes": notes}
        if req.get("frontier"):
            F, _, _, _ = o.portfolios(C, M, E, m0, W, A)
            res["frontier"] = records(F)
        else:
            F = self.B.cfg.output / "M4_frontier.csv"
            if F.exists():
                import pandas as pd
                res["frontier"] = records(pd.read_csv(F))
                res["notes"].append("Sərhəd: son tam icranın M4_frontier.csv faylı (standart risk iştahı ilə).")
        res["seconds"], res["prepare_s"] = round(time.time() - t0, 3), st["prepare_s"]
        return res
