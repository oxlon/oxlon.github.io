"""
analysis_stress — POST /stress/run: fərdi amil şokları → (1) MikroUnit zənciri FR1→FR3→FR4→FR5→FR10→FR12
(scalability.run_chain, bazadan fərq), (2) RU birgə Monte Karlo (simulate.run) — deterministik stress sapması
(measures.stress_scenarios ilə eyni qayda: yalnız elan olunmuş şoklar, T09 tədbiri ilə/tədbirsiz) və şoka
şərtli paylanma (digər amillər təsadüfi) vs şərtsiz paylanma.
"""
import time

import numpy as np

from analysis_base import MICRO_ONLY, RU_KEYS, _num, merge_overrides
from apicore import ApiError

QS = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)
KIND_AZ = {"g": "qeyri-neft artımı, f.b.", "cpi": "inflyasiya, f.b.", "fis": "büdcə balansı, % ÜDM"}


def ru_from_shocks(B, shocks):
    """Factor shocks → simulate.run override keys (documented approximations; notes returned)."""
    st = B.sc_state()
    sc = B.mods[2]
    T, j, hy = len(st["years"]), st["years"].index(st["hy"]), st["hy"]
    rel = np.ones(T)
    acc, notes, used = {}, [], False

    def add(key, vec):
        acc[key] = acc.get(key, np.zeros(T)) + np.asarray(vec, float)

    def at_j(x):
        v = np.zeros(T)
        v[j] = x
        return v

    def from_j(x):                                   # chain convention v2.1: shocks start in the score year
        v = np.zeros(T)
        v[j:] = x
        return v
    for s in shocks:
        f, k, size = s["factor"], s["k_sigma"], s["size"]
        sig = float(st["S"][f]["sigma"])
        used = True
        if f == "brent":
            rel[j:] *= np.exp(k * sig)
        elif f == "partner":
            add("partner_dev", at_j(k * sig))
        elif f == "remit":
            add("remit_dev", at_j(size))
        elif f == "rate":
            add("lend_dev", from_j(0.5 * k * sig * sc.coef_base("FR1.G3_lendrate|deprate")))
            notes.append("rate → RU kredit faizi sapması = 0,5 × uçot dərəcəsi şoku × FR1 G3 depozit əmsalı (şok ilindən)")
        elif f == "drought":
            add("spi", at_j(k))
        elif f == "food":
            add("food_dev", at_j(k * sig))
        elif f == "import":
            add("imp_dev", at_j(k * sig))
        elif f == "quake":
            add("quake_damage", at_j(size))
        elif f == "fx":
            if size >= 10:
                acc["deval_year"] = hy
                notes.append("fx ≥ 10%% → RU-da %d-ci ildə devalvasiya hadisəsi (ölçü RU parametridir, şokun ölçüsü deyil)" % hy)
            else:
                notes.append("fx < 10%: RU Monte Karlo-da devalvasiya hadisəsi yaranmır — yalnız MikroUnit zənciri")
        elif f == "geo":
            D = st["D"]
            ch = D["ch"]
            bgb, bgp, bgr = (float(ch[c]["coef"]) for c in (("gpr_brent", "annual_avg"), ("partner_gpr", "dl_gpr_reg"),
                                                             ("remit_gpr", "dl_gpr_reg")))
            rel[j] *= np.exp(bgb * k * sig)
            add("partner_dev", at_j(bgp * k * sig * 100))
            add("remit_dev", at_j(bgr * k * sig * 100))
        elif f == "geo_stress":
            add("remit_dev", at_j(-30.0 * 0.5 * k))
            add("partner_dev", at_j(-2.0 * 0.5 * k))
            add("lend_dev", at_j(1.0 * 0.5 * k))
        elif f in MICRO_ONLY:
            notes.append("%s: RU birgə Monte Karlo-da ayrıca kanal yoxdur — təsir yalnız MikroUnit zənciri ilə" % f)
    out = {k: v.tolist() if hasattr(v, "tolist") else v for k, v in acc.items()}
    if used and not np.allclose(rel, 1.0):
        out["brent_path"] = (np.asarray(st["centre"]) * rel).tolist()
    return out, notes


def validate_ru(ov, T, years):
    out = {}
    for k, v in (ov or {}).items():
        if k not in RU_KEYS:
            raise ApiError(400, "bad_override", "Naməlum RU şok açarı: %r. Mümkün olanlar: %s" % (k, ", ".join(RU_KEYS)))
        if k == "deval_year":
            y = int(_num(v, k))
            if y not in years:
                raise ApiError(400, "bad_override", "deval_year %s–%s aralığında olmalıdır" % (years[0], years[-1]))
            out[k] = y
            continue
        if not isinstance(v, (list, tuple)) or len(v) != T:
            raise ApiError(400, "bad_override", "«%s» %d dəyərlik siyahı olmalıdır (%s–%s)" % (k, T, years[0], years[-1]))
        out[k] = [_num(x, k) for x in v]
        if k == "brent_path" and min(out[k]) <= 0:
            raise ApiError(400, "bad_override", "brent_path müsbət olmalıdır")
    return out


def micro_block(B, ov, top):
    """Chain run with merged overrides → headline rows + top components (score year)."""
    st = B.sc_state()
    sc = B.mods[2]
    fl, clip = sc.run_chain(ov, "api-stress")
    dd = sc.derived_delta(st["base"], fl, st["D"]["rgdpnon_2025"])
    rows = sc.head_rows("ssenari", {"ad": "fərdi ssenari", "vahid": ""}, "stress", None, None, st["base"], fl, dd,
                         st["bl"], clip, st["lab"])
    keep = ("hedef_id", "hedef_ad", "vahid", "il", "baza", "ssenari", "delta", "delta_pct")
    head = [{k: r[k] for k in keep} for r in rows]
    return head, components(B, fl, top), clip, fl


def components(B, fl, top, hy=None):
    st = B.sc_state()
    sc = B.mods[2]
    cat, base = st["cat"], st["base"]
    hy = hy or st["hy"]
    gdp = base.get(("fr1:gdp_n", hy))
    rows = []
    for i, c in cat.iterrows():
        if (i, hy) not in base:
            continue
        e, u = sc.effect(c["kind"], c["unit_az"], base[(i, hy)], fl.get((i, hy), np.nan), gdp)
        if e is None or not np.isfinite(e) or abs(e) < 1e-12:
            continue
        rows.append({"komponent_id": i, "komponent_ad": c["label_az"], "modul": c["module"], "qrup": c["group_az"],
                     "vahid": c["unit_az"], "olcu_sinfi": u, "il": hy, "baza": base[(i, hy)], "ssenari": fl.get((i, hy)),
                     "tesir": float(e)})
    rows.sort(key=lambda r: (r["olcu_sinfi"] != "%", -abs(r["tesir"])))
    pct = [r for r in rows if r["olcu_sinfi"] == "%"][:top]
    other = [r for r in rows if r["olcu_sinfi"] != "%"][:max(top // 3, 5)]
    return {"n_affected": len(rows), "top_pct": pct, "top_abs": other}


def policy_shift(B, micro_raw):
    """Deterministic policy shift from `micro_overrides` ALONE: MicroUnit chain with the overrides vs the chain Baseline,
    headline deltas in the joint simulation's units (scalability.derived_delta: non-oil real growth pp, CPI pp,
    budget balance Δ mln AZN / Baseline FR1 gdp_n × 100). Returns ({kind: np.array[T]}, chain warnings)."""
    st = B.sc_state()
    sc = B.mods[2]
    ov, _ = merge_overrides([micro_raw], sc.coef_base)
    fl, clip = sc.run_chain(ov, "api-policy")
    dd = sc.derived_delta(st["base"], fl, st["D"]["rgdpnon_2025"])
    sh = {k: np.array([float(dd.get((tid, y), np.nan)) for y in st["years"]])
          for k, tid in (("g", "ru:nonoil_g"), ("cpi", "ru:cpi"), ("fis", "ru:budget_gdp"))}
    return {k: np.nan_to_num(v) for k, v in sh.items()}, clip


def _tail_stats(x, side, h):
    m = max(int(0.1 * len(x)), 1)
    xs = np.sort(x)
    tail = xs[:m] if side == "<" else xs[-m:]
    P = float((x < h).mean() if side == "<" else (x > h).mean())
    return P, float(tail.mean())


def ru_block(B, ru_ov, with_measures, stochastic, n, policy=None):
    st = B.sc_state()
    factors = B.mods[1]
    yrs = st["years"]
    from riskunit import measures
    D = measures.stress_vector(ru_ov, with_measures=with_measures, n=4000)     # the S1–S8 rule (public, FR3 owner)
    dev = []
    for r in D.to_dict("records"):
        row = {k: (None if isinstance(v, float) and v != v else v) for k, v in r.items()}
        if policy is not None:
            ps = float(policy[row["kind"]][yrs.index(row["il"])])
            row["siyaset_sapmasi"], row["sapma_siyasetle"] = ps, row["sapma"] + ps
        dev.append(row)
    out = {"ru_overrides_used": ru_ov, "deviation": dev}
    if policy is not None:
        out["policy_shift"] = [{"kind": k, "gosterici": KIND_AZ[k], "il": y, "deyisme": float(policy[k][t])}
                               for k in ("g", "cpi", "fis") for t, y in enumerate(yrs)]
    if stochastic:
        p = factors.params()
        thr = {"g": ("<", float(p["nonoil_gar_threshold"])), "cpi": (">", float(p["cpi_threshold"])),
               "fis": ("<", float(p["fiscal_threshold"]))}
        U = B.sim(n, None, cache_key="uncond")
        Cn = B.sim(n, ru_ov) if ru_ov else U
        views = [("şərtsiz", U, None)] + ([("şoka şərtli", Cn, None)] if ru_ov else [])
        if policy is not None:
            views.append(("şoka şərtli + siyasət" if ru_ov else "siyasətlə", Cn, policy))
        dist, met = [], {}
        for view, r, shift in views:
            for kind in ("g", "cpi", "fis"):
                X = r.total(kind)
                if shift is not None:
                    X = X + shift[kind][None, :]               # deterministic policy shift of every draw
                side, h = thr[kind]
                for t, y in enumerate(yrs):
                    x = X[:, t]
                    P, es = _tail_stats(x, side, h)
                    dist.append({"baxis": view, "kind": kind, "gosterici": KIND_AZ[kind], "il": y, "baza": float(r.base[kind][t]),
                                 **{"p%02d" % round(q * 100): float(np.quantile(x, q)) for q in QS},
                                 "orta": float(x.mean()), "P_hedd": P, "ES10": es, "hedd": "%s %g" % (side, h)})
                    if y == st["hy"]:
                        met.setdefault(kind, {})[view] = {"P_hedd": P, "ES10": es, "median": float(np.median(x))}
        if policy is not None:
            a, b = views[-2][0], views[-1][0]
            for kind, d in met.items():
                d["siyasetin_effekti"] = {"P_hedd": d[b]["P_hedd"] - d[a]["P_hedd"], "ES10": d[b]["ES10"] - d[a]["ES10"],
                                          "median": d[b]["median"] - d[a]["median"], "muqayise": "%s − %s" % (b, a)}
        out["distribution"], out["metrics"] = dist, met
    return out


def run(B, req):
    t0 = time.time()
    req = req or {}
    st = B.sc_state()
    tim = {"prepare_s": B.timings.get("sc_prepare_s")}
    shocks = [B.resolve(s) for s in (req.get("shocks") or [])]
    micro_raw = req.get("micro_overrides") or {}
    if not isinstance(micro_raw, dict):
        raise ApiError(400, "bad_override", "«micro_overrides» obyekt olmalıdır ({\"FR1\": {...}})")
    if not shocks and not micro_raw and not req.get("ru_overrides"):
        raise ApiError(400, "empty_scenario", "Ən azı bir şok verilməlidir (shocks, ru_overrides və ya micro_overrides)")
    sc = B.mods[2]
    ov, notes = merge_overrides([s["ov"] for s in shocks] + [micro_raw], sc.coef_base)
    res = {"name": req.get("name") or "fərdi ssenari", "score_year": st["hy"], "years": st["years"],
           "baseline_id": st["key"].split("|")[0],
           "shocks": [{k: v for k, v in s.items() if k != "ov"} for s in shocks], "notes": notes}
    t = time.time()
    if ov:
        head, comp, clip, _ = micro_block(B, ov, int(req.get("top_components") or 40))
        res["micro"] = {"headline": head, "components": comp, "warnings": clip, "overrides": ov}
    else:
        res["micro"] = None
    policy = None
    if micro_raw:
        policy, _ = policy_shift(B, micro_raw)
    tim["micro_chain_s"] = round(time.time() - t, 3)
    t = time.time()
    derived, n2 = ru_from_shocks(B, shocks)
    ru_ov = {**derived, **validate_ru(req.get("ru_overrides"), len(st["years"]), st["years"])}
    res["notes"] += n2
    n = int(min(max(int(_num(req.get("n", 4000), "n")), 500), 20000))
    if ru_ov or policy is not None:
        res["ru"] = ru_block(B, ru_ov, req.get("with_measures", True) is not False, req.get("stochastic", True) is not False,
                             n, policy)
        if policy is not None:
            res["notes"].append("micro_overrides (siyasət) RU paylanmasına deterministik sürüşmə kimi daxil edilib: MikroUnit "
                                "zənciri override-larla vs Baseline → qeyri-neft artımı (f.b.), İQİ (f.b.), büdcə balansı "
                                "(Δ mln AZN / FR1 gdp_n, % ÜDM); hər ssenari bu yolla sürüşdürülür, hədd ehtimalı və ES10 "
                                "siyasətlə/siyasətsiz yenidən hesablanır (qeyri-müəyyənlik dəyişmir).")
    else:
        res["ru"] = None
        res["notes"].append("RU birgə Monte Karlo-ya uyğun şok yoxdur — yalnız MikroUnit zənciri")
    tim["ru_sim_s"] = round(time.time() - t, 3)
    res["notes"].append("Təsirlər bazadan fərqdir; RU öz mərkəzi yolunu dərc etmir (bazalar OxLon/MicroUnit).")
    res["timings"], res["seconds"] = tim, round(time.time() - t0, 3)
    return res
