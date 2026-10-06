"""
risk_views — risk reyestri + FR2 skorları + qalıq risk + tədbirlər; hər risk üzrə ətraflı paket (drill-down).
"""
import pandas as pd

from apicore import ApiError
from data_views import records


def _contains(series, rid):
    return series.fillna("").astype(str).str.split(";").apply(lambda xs: rid in [x.strip() for x in xs])


class RiskViews:
    def __init__(self, views):
        self.v = views

    def _measures(self):
        return self.v.frame("M1_measures_v2.csv", required=False) if (self.v.cfg.output / "M1_measures_v2.csv").exists() \
            else self.v.frame("FR3_measures_register.csv", required=False)

    def _residual(self):
        M5 = self.v.frame("M5_residual_v2.csv", required=False)
        if M5 is not None and "qaliq_skor_plan" in M5.columns:
            M5 = M5[M5["risk_id"] != "ÜMUMİ"]
            return M5.set_index("risk_id")[["qaliq_skor_plan", "qaliq_prioritet"]].rename(
                columns={"qaliq_skor_plan": "qaliq_skor"}), "M5_residual_v2.csv"
        R = self.v.frame("FR3_residual_risk.csv", required=False)
        if R is not None:
            R = R.set_index("risk_id")[["skor_hedef"]].rename(columns={"skor_hedef": "qaliq_skor"})
            R["qaliq_prioritet"] = R["qaliq_skor"].apply(lambda s: "yüksək" if s >= 12 else "orta" if s >= 6 else "aşağı")
            return R, "FR3_residual_risk.csv"
        return None, None

    def table(self, qs=None):
        qs = qs or {}
        reg = self.v.input_frame("risk_reyestri.csv")
        S = self.v.frame("FR2_risk_scores.csv")
        if reg is None:
            raise ApiError(404, "not_found", "Risk reyestri tapılmadı (input/risk_reyestri.csv)")
        T = reg.merge(S.drop(columns=[c for c in S.columns if c in reg.columns and c != "risk_id"]), on="risk_id", how="left")
        res, src = self._residual()
        if res is not None:
            T = T.merge(res, left_on="risk_id", right_index=True, how="left")
        M = self._measures()
        T["tedbir_sayi"] = [int(_contains(M["risk_idler"], r).sum()) if M is not None else 0 for r in T["risk_id"]]
        A = self.v.frame("FR2_alerts.csv", required=False)
        T["xeberdarliq_sayi"] = [int((A["risk_id"] == r).sum()) if A is not None else 0 for r in T["risk_id"]]
        H = self.v.frame("FR2_score_history.csv", required=False)
        prev = {}
        if H is not None and len(H):
            last = H["hesablandi_utc"].max()
            older = H[H["hesablandi_utc"] < last]
            if len(older):
                prev = older.sort_values("hesablandi_utc").groupby("risk_id")["skor"].last().to_dict()
        T["skor_evvelki"] = T["risk_id"].map(prev)
        if "skor" in T.columns:
            T = T.sort_values(["skor", "risk_id"], ascending=[False, True])
        pr, fam = qs.get("priority"), qs.get("family")
        pr = pr[0] if isinstance(pr, list) else pr
        fam = fam[0] if isinstance(fam, list) else fam
        if pr:
            T = T[T["prioritet"] == pr]
        if fam:
            T = T[T["aile"] == fam]
        bid = S["baseline_id"].iloc[0] if "baseline_id" in S and len(S) else None
        sy = int(S["ufuq"].mode().iloc[0]) if "ufuq" in S and S["ufuq"].notna().any() else None
        return {"baseline_id": bid, "score_year": sy, "residual_source": src, "risks": records(T),
                "heatmap": records(self.v.frame("FR2_heatmap.csv", required=False))}

    def bundle(self, rid):
        rid = str(rid).strip().upper()
        tab = self.table()
        rows = [r for r in tab["risks"] if r["risk_id"] == rid]
        if not rows:
            raise ApiError(404, "not_found", "Risk tapılmadı: %s" % rid)
        risk = rows[0]
        f = lambda n: self.v.frame(n, required=False)  # noqa: E731
        out = {"risk": risk, "baseline_id": tab["baseline_id"], "score_year": tab["score_year"]}
        reg = self.v.input_frame("risk_reyestri.csv")
        out["register"] = records(reg[reg["risk_id"] == rid])[0] if reg is not None and (reg["risk_id"] == rid).any() else None
        S = f("FR2_risk_scores.csv")
        out["score"] = records(S[S["risk_id"] == rid])[0] if S is not None and (S["risk_id"] == rid).any() else None
        H = f("FR2_score_history.csv")
        out["history"] = records(H[H["risk_id"] == rid]) if H is not None else []
        C = f("FR2_contributions.csv")
        out["contributions"] = records(C[C["risk_id"].astype(str) == rid]) if C is not None else []
        A = f("FR2_alerts.csv")
        out["alerts"] = records(A[A["risk_id"] == rid]) if A is not None else []
        M = self._measures()
        out["measures"] = records(M[_contains(M["risk_idler"], rid)]) if M is not None else []
        R5 = f("M5_residual_v2.csv")
        R3 = f("FR3_residual_risk.csv")
        out["residual"] = records(R5[R5["risk_id"] == rid]) if R5 is not None else \
            records(R3[R3["risk_id"] == rid]) if R3 is not None else []
        S0 = f("S0_factor_sigma.csv")
        fac = S0[_contains(S0["risk_idler"], rid)] if S0 is not None else None
        out["factors"] = records(fac)
        S7 = f("S7_daily_decision.csv")
        out["daily_decision"] = records(S7[_contains(S7["risk_idler"], rid)]) if S7 is not None else []
        out["stress"] = self._stress_for(rid, f("FR3_stress_scenarios.csv"))
        out["stress_note"] = "S1–S8 ilə risk əlaqəsi API xəritəsidir (şok vektorunun kanallarına görə), modul çıxışı deyil"
        C3 = f("C3_category_map.csv")
        out["caem"] = records(C3[C3["ru_risk_id"].astype(str) == rid]) if C3 is not None else []
        out["monitor"] = self._monitor_for(out["register"], f("D5_daily_monitor.csv"))
        return out

    @staticmethod
    def _stress_for(rid, ST):
        """Daimi stress ssenariləri ilə əlaqə: scalability/simulate CHANNEL_RISK-ə görə sabit xəritə."""
        link = {"R01": ["S1", "S3", "S6", "S8"], "R03": ["S3"], "R05": ["S2", "S4"], "R06": ["S4"], "R07": ["S4"],
                "R08": ["S5"], "R09": ["S7"], "R14": ["S6"], "R02": ["S4"], "R11": ["S1", "S3"], "R12": ["S3"], "R13": ["S1", "S2", "S4"]}
        if ST is None:
            return []
        ids = link.get(rid, [])
        return records(ST[ST["ssenari"].isin(ids)]) if ids else []

    @staticmethod
    def _monitor_for(reg, D5):
        if reg is None or D5 is None:
            return []
        keys = [k.strip().lower() for k in str(reg.get("gosterici") or "").replace(",", ";").split(";") if k.strip()]
        if not keys:
            return []
        ind = D5["indicator"].astype(str).str.lower()
        mask = ind.apply(lambda s: any(k in s for k in keys))
        return records(D5[mask])
