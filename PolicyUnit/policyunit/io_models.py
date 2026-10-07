"""Fixed-coefficient IO models for the PolicyUnit (MİİS §15.5.4 FR2).

Leontief quantity model (domestic coefficients, Type I and Type II), Leontief cost-push price
model, Ghosh supply-side model, Rasmussen linkages, key sectors, hypothetical extraction.
Assumptions (stated in docs/Metodologiya_IO.md): constant technical coefficients, no supply
constraints, prices do not affect quantities (and vice versa), import shares by product fixed
(import proportionality), full cost pass-through in the price model.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import io_data as D


class IOModel:
    """Domestic IO model built from an aggregated (or product) IOT."""

    def __init__(self, t: D.IOT, emp: pd.Series | None = None, hh_income_ratio: float | None = None,
                 mpc: float | None = None, tax_wedge: float | None = None, label: str = ""):
        self.t, self.year, self.label = t, t.year, label or f"DSK {t.year}"
        self.codes = list(t.codes)
        n = self.n = len(self.codes)
        x = self.x = np.asarray(t.x, float)
        xs = np.where(x > 0, x, 1.0)
        sp = D.domestic_split(t)
        self.s_imp = sp["s"]
        self.Zd, self.Zm, self.fdd, self.fdm = sp["Zd"], sp["Zm"], sp["fdd"], sp["fdm"]
        self.Ad = self.Zd / xs[None, :]
        self.Am = self.Zm / xs[None, :]
        self.A = t.Z / xs[None, :]
        self.I = np.eye(n)
        self.L = np.linalg.inv(self.I - self.Ad)
        va = t.va.loc[D.VA_KEYS].to_numpy()
        self.va_vec = va.sum(0)
        self.v = self.va_vec / xs                     # VA coefficient
        self.w = (va[0] + va[1]) / xs                 # compensation incl. social contributions
        self.wce = va[0] / xs                         # wages (compensation of employees row)
        self.tx = t.tax / xs                          # net product taxes paid per unit output
        self.m = self.Zm.sum(0) / xs                  # direct import coefficient
        self.emp = (emp.reindex(self.codes).fillna(0.0).to_numpy() if emp is not None
                    else np.zeros(n))                 # thousand persons
        self.e = self.emp * 1e3 / (xs / 1e3)          # persons per million AZN of output
        # Ghosh allocation coefficients B (row-normalised domestic flows)
        self.B = self.Zd / xs[:, None]
        self.G = np.linalg.inv(self.I - self.B)
        self._hh_closure(hh_income_ratio, mpc, tax_wedge)

    # ------------------------------------------------------------------ Type II closure
    def _hh_closure(self, hh_income_ratio, mpc, tax_wedge):
        """Households endogenous: income row h = (compensation + share of mixed income)/x,
        consumption column c = mpc*(1-tax_wedge) * domestic HH consumption structure.
        hh_income_ratio = HBS self-employment / employment income (e002en, 2024: 117.6/135.1);
        mixed income is taken from net income of sectors where households operate."""
        hbs = 117.6 / 135.1 if hh_income_ratio is None else hh_income_ratio
        va = self.t.va
        ce = (va.loc["ce"] + va.loc["sc"]).to_numpy()
        ni = va.loc["ni"].to_numpy().copy()
        corp = {"OILGAS", "PETR", "FIN", "ENERGY", "PUB", "MINOTH", "CHEM", "METMIN"}
        hh_sect = np.array([c not in corp for c in self.codes])
        if len(self.codes) > 30:  # product-level table: use CPA codes
            hh_sect = np.array([not c.startswith(("06", "09", "19", "35", "64", "65", "84"))
                                for c in self.codes])
        target_mixed = hbs * va.loc["ce"].to_numpy().sum()
        pool = np.where(hh_sect, np.maximum(ni, 0.0), 0.0)
        alpha = min(1.0, target_mixed / pool.sum()) if pool.sum() > 0 else 0.0
        self.alpha_mixed = alpha
        xs = np.where(self.x > 0, self.x, 1.0)
        self.h = (ce + alpha * pool) / xs
        hh_tot_pp = float(self.t.fd["hh"].sum() + self.t.fd_tax.get("hh", 0.0))
        y_hh = float((self.h * self.x).sum())
        self.mpc = mpc if mpc is not None else min(0.95, hh_tot_pp / y_hh) if y_hh > 0 else 0.8
        self.tax_wedge = 0.10 if tax_wedge is None else tax_wedge
        self.c = self.mpc * (1 - self.tax_wedge) * self.fdd["hh"].to_numpy() / hh_tot_pp
        n = self.n
        Abar = np.zeros((n + 1, n + 1))
        Abar[:n, :n] = self.Ad
        Abar[n, :n] = self.h
        Abar[:n, n] = self.c
        self.Lbar = np.linalg.inv(np.eye(n + 1) - Abar)

    # ------------------------------------------------------------------ quantity model
    def quantity(self, df: np.ndarray, type2: bool = False) -> dict:
        """Effects of a domestic final-demand change df (thousand AZN) on output, VA,
        compensation, employment (thousand persons) and imports (thousand AZN)."""
        df = np.asarray(df, float)
        if type2:
            dx = (self.Lbar[:self.n, :self.n] @ df)
        else:
            dx = self.L @ df
        return {"dx": dx, "dva": self.v * dx, "dcomp": self.w * dx,
                "demp": self.e * dx / 1e6, "dimp": self.m * dx}

    def multipliers(self) -> pd.DataFrame:
        L, Lb, n = self.L, self.Lbar[:self.n, :self.n], self.n
        out = pd.DataFrame(index=self.codes)
        out["output_I"] = L.sum(0)
        out["output_II"] = Lb.sum(0)
        out["va_I"] = self.v @ L
        out["va_II"] = self.v @ Lb
        out["comp_I"] = self.w @ L
        out["comp_II"] = self.w @ Lb
        out["emp_I"] = self.e @ L                    # persons per 1 mln AZN final demand
        out["emp_II"] = self.e @ Lb
        out["imp_I"] = self.m @ L                    # indirect import content per 1 AZN
        out["imp_II"] = self.m @ Lb
        out["type_ratio_output"] = out["output_II"] / out["output_I"]
        out["emp_direct"] = self.e
        with np.errstate(divide="ignore", invalid="ignore"):
            out["emp_typeI_mult"] = np.where(self.e > 0, out["emp_I"] / self.e, np.nan)
            out["income_typeI_mult"] = np.where(self.w > 0, out["comp_I"] / self.w, np.nan)
        return out

    # ------------------------------------------------------------------ linkages
    def linkages(self) -> pd.DataFrame:
        n, L, G = self.n, self.L, self.G
        bl = L.sum(0)
        fl_g = G.sum(1)
        fl_l = L.sum(1)
        out = pd.DataFrame(index=self.codes)
        out["bl_raw"] = bl
        out["bl_index"] = bl / bl.mean()                       # Rasmussen backward (power)
        out["fl_ghosh_raw"] = fl_g
        out["fl_index"] = fl_g / fl_g.mean()                   # forward (Ghosh, Miller-Blair)
        out["fl_leontief_index"] = fl_l / fl_l.mean()          # sensitivity of dispersion
        cv_b = L.std(0) / L.mean(0)
        out["bl_cv"] = cv_b                                    # dispersion (lower = broader)
        out["key"] = np.where((out["bl_index"] > 1) & (out["fl_index"] > 1), "açar",
                     np.where(out["bl_index"] > 1, "geri əlaqə yönümlü",
                     np.where(out["fl_index"] > 1, "irəli əlaqə yönümlü", "zəif əlaqəli")))
        return out

    def extraction(self) -> pd.DataFrame:
        """Hypothetical extraction (Miller-Lahr): total (row+column removed, own final
        demand kept outside), backward (column of A zeroed), forward (row of B zeroed, Ghosh).
        Losses in % of total domestic output."""
        f = self.fdd.sum(axis=1).to_numpy()
        vprim = self.va_vec + self.t.tax + self.Zm.sum(0) + self.t.cif
        X = self.x.sum()
        rows = []
        for k in range(self.n):
            keep = np.ones(self.n, bool)
            keep[k] = False
            Lk = np.linalg.inv(np.eye(self.n - 1) - self.Ad[np.ix_(keep, keep)])
            x_tot = Lk @ f[keep]
            tot = (self.x[keep].sum() - x_tot.sum()) / X * 100
            Ab = self.Ad.copy()
            Ab[:, k] = 0.0
            xb = np.linalg.solve(self.I - Ab, f)
            back = (X - xb.sum()) / X * 100
            Bf = self.B.copy()
            Bf[k, :] = 0.0
            xf = vprim @ np.linalg.inv(self.I - Bf)
            fwd = (X - xf.sum()) / X * 100
            rows.append({"sector": self.codes[k], "extract_total_pct": tot,
                         "extract_backward_pct": back, "extract_forward_pct": fwd,
                         "own_output_share_pct": self.x[k] / X * 100})
        return pd.DataFrame(rows).set_index("sector")

    # ------------------------------------------------------------------ price model
    def price(self, dv=None, dpm=None, exog: dict | None = None, dtax_int=None) -> dict:
        """Leontief cost-push price model (index p = 1 at base, full pass-through):
            p_j = sum_i a^d_ij p_i + sum_i a^m_ij pm_i + v_j + t_j
        dv       : change in primary-input cost per unit of output (wage, tax on production,
                   productivity = -g*v_j), vector n
        dpm      : relative change of import prices by product (tariff, FX), vector n
        exog     : {sector: dp} regulated/administered prices (exogenous, e.g. fuel +11%)
        dtax_int : change in non-deductible product-tax cost per unit output, vector n
        Returns dp (domestic basic prices), dpm, and the cost-push vector."""
        n = self.n
        dv = np.zeros(n) if dv is None else np.asarray(dv, float)
        dpm = np.zeros(n) if dpm is None else np.asarray(dpm, float)
        dti = np.zeros(n) if dtax_int is None else np.asarray(dtax_int, float)
        push = dv + dpm @ self.Am + dti               # cost push per column
        exog = exog or {}
        K = np.array([self.codes.index(k) for k in exog], int)
        dp = np.zeros(n)
        if len(K):
            dp[K] = [exog[k] for k in exog]
        N = np.array([i for i in range(n) if i not in set(K.tolist())], int)
        A_NN = self.Ad[np.ix_(N, N)]
        rhs = push[N] + (dp[K] @ self.Ad[np.ix_(K, N)] if len(K) else 0.0)
        dp[N] = np.linalg.solve((np.eye(len(N)) - A_NN).T, rhs)
        return {"dp": dp, "dpm": dpm, "push": push}

    def cpi_weights(self, supply: pd.DataFrame | None = None) -> pd.DataFrame:
        """HH consumption basket by sector at purchasers' prices: domestic and imported
        parts at basic prices, plus net product taxes (supply-table rate by product)."""
        hd = self.fdd["hh"].to_numpy()
        hm = self.fdm["hh"].to_numpy()
        tau = np.zeros(self.n)
        if supply is not None:
            s = supply.reindex(self.codes).fillna(0.0)
            tau = np.where(s["total_bp"] > 0, s["net_taxes"] / s["total_bp"].where(s["total_bp"] > 0, 1), 0.0)
        tot = (hd + hm) * (1 + tau)
        return pd.DataFrame({"hh_dom": hd, "hh_imp": hm, "tau": tau,
                             "w": tot / tot.sum()}, index=self.codes)

    def cpi_effect(self, pr: dict, w: pd.DataFrame, exog_retail: dict | None = None,
                   dtax_final=None) -> pd.Series:
        """Consumer price change by sector basket item (fraction) and total.
        exog_retail: regulated retail price changes applying to ALL household purchases of
        the item (domestic and imported); dtax_final: change of product-tax rate on HH."""
        dp, dpm = pr["dp"], pr["dpm"]
        hd, hm, tau = w["hh_dom"].to_numpy(), w["hh_imp"].to_numpy(), w["tau"].to_numpy()
        base = np.where(hd + hm > 0, hd + hm, 1.0)
        item = (hd * dp + hm * dpm) / base
        if exog_retail:
            for k, v in exog_retail.items():
                item[self.codes.index(k)] = v
        if dtax_final is not None:
            item = (1 + item) * (1 + tau + np.asarray(dtax_final)) / (1 + tau) - 1
        s = pd.Series(item, index=self.codes)
        s["CPI"] = float((w["w"].to_numpy() * item).sum())
        return s

    # ------------------------------------------------------------------ Ghosh model
    def ghosh(self, dvprim) -> np.ndarray:
        """Ghosh supply-side model: dx' = dv' (I - B)^-1 for a change of primary inputs
        (thousand AZN). LIMITATION: assumes fixed output (allocation) coefficients, i.e.
        perfectly elastic demand and substitutable inputs; quantity interpretation is
        implausible (Oosterhaven 1988) — use only as a forward-linkage / supply-shock
        ordering indicator, or in its price interpretation (Dietzenbacher 1997)."""
        return np.asarray(dvprim, float) @ self.G

    def supply_shock(self, sector: str, rel: float) -> pd.DataFrame:
        """Ghosh forward propagation of a supply cut of `rel` (e.g. -0.10) in one sector."""
        k = self.codes.index(sector)
        dv = np.zeros(self.n)
        dv[k] = rel * (self.x[k] - self.Zd[:, k].sum())
        dx = self.ghosh(dv)
        return pd.DataFrame({"dx": dx, "dx_pct": dx / np.where(self.x > 0, self.x, 1) * 100},
                            index=self.codes)

    # ------------------------------------------------------------------ competitiveness
    def competitiveness(self) -> pd.DataFrame:
        t = self.t
        va = self.va_vec
        comp = (t.va.loc["ce"] + t.va.loc["sc"]).to_numpy()
        e = t.fd["exp"].to_numpy()
        dom_use = self.x - e + t.imp
        out = pd.DataFrame(index=self.codes)
        out["output_mln"] = self.x / 1e3
        out["va_mln"] = va / 1e3
        out["emp_thsd"] = self.emp
        with np.errstate(divide="ignore", invalid="ignore"):
            out["lab_prod_thsd_azn"] = np.where(self.emp > 0, va / self.emp / 1e3, np.nan)
            out["ulc_comp_va"] = np.where(va > 0, comp / va, np.nan)          # nominal ULC
            out["comp_per_emp_azn_month"] = np.where(self.emp > 0, comp / self.emp / 12, np.nan)
            out["import_penetration"] = np.where(dom_use > 0, t.imp / dom_use, np.nan)
            out["export_orientation"] = np.where(self.x > 0, e / self.x, np.nan)
            out["import_content_direct"] = self.m
            dva_exp = self.v * (self.L @ self.fdd["exp"].to_numpy())
            out["va_in_exports_share"] = dva_exp / dva_exp.sum()
            out["domestic_va_per_export_azn"] = (self.v @ self.L)
        return out


def build(year: int = 2021, aggregated: bool = True, table: D.IOT | None = None,
          emp_year: int | None = None, **kw) -> IOModel:
    """Convenience constructor: DSK table of `year`, aggregated to io_sectors.csv."""
    t = table if table is not None else D.load_iot(year)
    if aggregated and len(t.codes) > 30:
        t = D.aggregate(t)
    emp = D.employment(emp_year or t.year) if aggregated else None
    return IOModel(t, emp, **kw)
