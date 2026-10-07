"""Synthetic household microdata generator (FR3). SİNTETİK — real ev təsərrüfatı məlumatı deyil.

Generates a person-level roster (household variables repeated on every member row) with
demography, activity status (formal employee by NACE section and tax regime, informal /
own-account, agriculture, unemployed, pensioner, student, inactive, child) and raw incomes.
Wages are drawn from the DSK wage-band x sector distribution (004_11, Nov 2024) with a Pareto
top band matched to DSK average wages by sector (004_2). All other amounts are raw shapes:
levels, weights and decile profile are fixed afterwards by ms_calib (entropy calibration +
source reconciliation factors). Constants marked [K] are approximate and replaceable."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .ms_rawdata import SECTORS, TARGETS

WATERMARK = "SİNTETİK — real ev təsərrüfatı məlumatı deyil"
# [K] economic regions (2021 classification) — approx. population share, urban share
REGIONS = {"Bakı": (23.5, 1.0), "Abşeron-Xızı": (6.0, .6), "Naxçıvan": (4.6, .3),
           "Gəncə-Daşkəsən": (5.6, .55), "Qazax-Tovuz": (6.8, .35), "Şəki-Zaqatala": (6.2, .3),
           "Lənkəran-Astara": (9.3, .3), "Quba-Xaçmaz": (5.5, .3), "Mərkəzi Aran": (7.4, .4),
           "Mil-Muğan": (5.0, .35), "Şirvan-Salyan": (4.7, .45), "Dağlıq Şirvan": (2.9, .3),
           "Qarabağ": (8.5, .35), "Şərqi Zəngəzur": (4.0, .3)}
SIZE_P = {"urban": [.08, .15, .17, .24, .19, .10, .04, .03],      # [K] sizes 1..8
          "rural": [.04, .09, .12, .19, .22, .16, .10, .08]}
BUDGET_SECTORS = {"pubadm", "educ", "health", "art"}
PENSION_AGE = {2018: (64, 61), 2024: (65, 64)}                     # [K] men, women


def _labour(year=2024):
    t = pd.read_csv(TARGETS / "labour_targets.csv")
    t = t[t.year == year].set_index("key")["value"]
    emp = np.array([t[f"employed:{s}"] for s in SECTORS])
    hired = np.array([t[f"hired:{s}"] for s in SECTORS])
    t24 = pd.read_csv(TARGETS / "labour_targets.csv").query("year == 2024").set_index("key")
    st = np.array([t24.value[f"hired_state:{s}"] / t24.value[f"hired:{s}"] for s in SECTORS])
    return emp, hired, st                    # state share by sector: 2024 structure


def _wage_sampler(year=2024):
    b = pd.read_csv(TARGETS / "wage_bands.csv").query("year == @year")
    avg = pd.read_csv(TARGETS / "wage_avg_sector.csv").query("year == @year")
    avg = avg.set_index("sector")["value"]
    out = {}
    for s in SECTORS:
        x = b[b.sector == s].reset_index(drop=True)
        p = x["count"].to_numpy(float)
        mids = np.where(np.isfinite(x.hi), 0.5 * (x.lo + x.hi), np.nan)
        top_lo = float(x.lo.iloc[-1])
        top_mean = (avg[s] * p.sum() - np.nansum(mids * p)) / max(p[-1], 1)
        top_mean = max(top_mean, top_lo * 1.25)
        alpha = top_mean / (top_mean - top_lo)
        out[s] = (x.lo.to_numpy(float), x.hi.to_numpy(float), p / p.sum(), alpha)
    return out


def draw_wages(sector, rng, year=2024):
    """Gross monthly wage per person + full-time flag (below-MW band = part-time)."""
    samp = _wage_sampler(year)
    w = np.zeros(len(sector))
    ft = np.ones(len(sector), bool)
    for s in SECTORS:
        idx = np.where(sector == s)[0]
        if not len(idx):
            continue
        lo, hi, p, a = samp[s]
        k = rng.choice(len(p), size=len(idx), p=p)
        u = rng.random(len(idx))
        top = ~np.isfinite(hi[k])
        lo_k, hi_k = lo[k], np.where(top, lo[k], hi[k])
        lo_k = np.where(k == 0, 0.35 * hi[0], lo_k)
        w[idx] = lo_k + u * (hi_k - lo_k)
        w[idx[top]] = np.minimum(lo[k][top] * (1 - u[top]) ** (-1 / a), 25000.0)
        ft[idx[k == 0]] = False
    return w, ft


def generate(n_hh=12000, seed=20241, year=2024):
    rng = np.random.default_rng(seed)
    names = list(REGIONS)
    rp = np.array([REGIONS[r][0] for r in names]); rp = rp / rp.sum()
    reg = rng.choice(len(names), n_hh, p=rp)
    urban = rng.random(n_hh) < np.array([REGIONS[names[r]][1] for r in reg])
    size = np.where(urban, rng.choice(8, n_hh, p=SIZE_P["urban"]),
                    rng.choice(8, n_hh, p=SIZE_P["rural"])) + 1
    rows = []
    for h in range(n_hh):
        hs = rng.random() < 0.8
        ha = float(np.clip(rng.normal(50, 14), 20, 90))
        mem = [("head", ha, "M" if hs else "F")]
        if size[h] >= 2 and rng.random() < 0.82:
            mem.append(("spouse", float(np.clip(ha + rng.normal(-3, 4), 18, 92)),
                        "F" if hs else "M"))
        while len(mem) < size[h]:
            if ha < 60 and rng.random() < 0.10:
                mem.append(("parent", float(rng.uniform(65, 90)), rng.choice(["M", "F"])))
            else:
                ca = ha - 22 - rng.uniform(0, 18)
                ca = ca if ca >= 0 else rng.uniform(0, 6)
                mem.append(("child", float(min(ca, 45)), rng.choice(["M", "F"])))
        for rel, age, sex in mem:
            rows.append((h, rel, int(age), sex))
    p = pd.DataFrame(rows, columns=["hh", "rel", "age", "sex"])
    p["region"] = np.array(names)[reg[p.hh]]
    p["urban"] = urban[p.hh].astype(int)
    p["hh_size"] = size[p.hh]
    _activity(p, rng, year)
    _incomes(p, rng, year)
    p.insert(0, "data_status", WATERMARK)
    p["hh_id"] = "H" + (p.hh + 1).astype(str).str.zfill(6)
    p["person_id"] = p.hh_id + "_" + (p.groupby("hh").cumcount() + 1).astype(str)
    return p.drop(columns="hh")


def _activity(p, rng, year):
    n = len(p)
    am, af = PENSION_AGE.get(year, PENSION_AGE[2024])
    page = np.where(p.sex == "M", am, af)
    u = rng.random(n)
    st = np.full(n, "inactive", object)
    st[p.age < 15] = "child"
    st[(p.age >= 15) & (p.age <= 17) & (u < .92)] = "student"
    st[(p.age >= 18) & (p.age <= 23) & (u < .30)] = "student"
    st[(p.age >= page) & (u < .93)] = "pensioner"
    dis = (p.age >= 18) & (p.age < page) & (rng.random(n) < .045) & (st == "inactive")
    st[dis] = "pensioner"
    wa = (st == "inactive") & (p.age >= 15) & (p.age < page)
    part = np.where(p.sex == "M", .84, np.where(p.urban == 1, .58, .72))
    lf = wa & (rng.random(n) < part)
    unemp = lf & (rng.random(n) < .055)
    st[unemp] = "unemployed"
    empl = np.where(lf & ~unemp)[0]
    emp, hired, sshare = _labour(year)
    cells = np.concatenate([hired, np.clip(emp - hired, 0, None)])  # 19 hired + 19 own-acc.
    sector = np.full(n, "", object)
    for urb in (0, 1):
        idx = empl[p.urban.to_numpy()[empl] == urb]
        w = cells.copy()
        w[19] *= (3.0 if urb == 0 else 0.15)                       # own-account agriculture
        w[:19] *= (0.7 if urb == 0 else 1.3)
        k = rng.choice(38, len(idx), p=w / w.sum())
        sector[idx] = np.array(SECTORS * 2)[k]
        st[idx] = np.where(k < 19, "employee", np.where(k == 19, "agri", "selfemp"))
    own = np.full(n, "", object)
    is_e = st == "employee"
    own[is_e] = np.where(rng.random(n)[is_e] < sshare[[SECTORS.index(s) for s in sector[is_e]]],
                         "state", "nonstate")
    own[is_e & (sector == "mining")] = "state"                     # oil-gas regime = state
    p["status"], p["sector"], p["ownership"] = st, sector, own
    p["regime"] = np.where(own == "state", "state", np.where(own == "nonstate", "priv", ""))
    p["oil"] = (is_e & (sector == "mining")).astype(int)
    p["budget"] = (is_e & (own == "state") & np.isin(sector, list(BUDGET_SECTORS))).astype(int)
    p["pension_type"] = np.where(st == "pensioner", np.where(dis, "disability", "age"), "")


def _incomes(p, rng, year):
    n = len(p)
    is_e = (p.status == "employee").to_numpy()
    w, ft = draw_wages(p.sector.to_numpy(), rng, year if year in (2024, 2025) else 2024)
    if year not in (2024, 2025):             # back-cast: 2024 shape x DSK state/non-state ratio
        lt = pd.read_csv(TARGETS / "labour_targets.csv").set_index(["year", "key"])["value"]
        r_st = lt[(year, "wage_state")] / lt[(2024, "wage_state")]
        r_ns = lt[(year, "wage_nonstate")] / lt[(2024, "wage_nonstate")]
        w = w * np.where(p.ownership == "state", r_st, r_ns)
    p["wage_gross"] = np.where(is_e, np.round(w, 1), 0.0)
    p["formal_ft"] = (is_e & ft).astype(int)
    ln = lambda s, m=1.0: m * np.exp(rng.normal(0, s, n))
    p["inc_selfemp"] = np.where(p.status == "selfemp", ln(.75) * np.where(p.urban, 1.2, 1), 0)
    plot = (p.rel == "head") & (rng.random(n) < np.where(p.urban == 1, .15, .65))
    p["inc_agri"] = np.where(p.status == "agri", ln(.8), 0) + np.where(plot, ln(.8, .5), 0)
    lt = pd.read_csv(TARGETS / "labour_targets.csv").query("year == @year").set_index("key")
    pen = ln(.28, float(lt.value["pension_avg"])) * np.where(p.pension_type == "disability", .8, 1)
    p["pension"] = np.where(p.status == "pensioner", np.round(pen, 1), 0.0)
    p["benefit_other"] = np.where(rng.random(n) < .05, rng.uniform(100, 250, n), 0.0)
    hh = p.hh.to_numpy()
    nh = hh.max() + 1
    rh = rng.random((nh, 5))
    hv = lambda q, s, m: np.where(rh[:, q] < s, m * np.exp(rng.normal(0, .8, nh)), 0)
    for col, q, share, med in (("inc_property", 0, .03, 150), ("remit", 1, .06, 250),
                               ("transfer_hh", 2, .55, 100)):
        p[col] = np.round(hv(q, share, med)[hh], 1)
    p["utsy_u"] = np.round(rh[:, 3][hh], 4)
    p["cons_noise"] = np.round(rng.normal(0, .22, nh)[hh], 4)
