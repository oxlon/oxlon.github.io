"""
analysis_scal — POST /scalability/run: bir amil × bir neçə ölçü (k σ və ya təbii vahid, + bugünkü canlı sapma)
→ MikroUnit zənciri (scalability.run_chain, bazadan fərq) → başlıq göstəriciləri (S1 formatı), σ-ya düşən cavab və
asimmetriya, bütün komponentlərə təsir (S4 məntiqi: scalability.effect, yaxın-sıfır baza → səviyyə fərqi və ya % ÜDM), qrup xülasəsi, ötürməni daşıyan
parametrlər (S5 faylından).
"""
import time

import numpy as np

from analysis_base import _num
from analysis_stress import components
from apicore import ApiError
from data_views import records

MAX_SIZES = 12


def run(B, req, views=None):
    t0 = time.time()
    req = req or {}
    st = B.sc_state()
    sc = B.mods[2]
    f = str(req.get("factor") or "").strip()
    if f not in st["S"]:
        raise ApiError(400, "unknown_factor", "Naməlum amil: %r. Mümkün olanlar: %s" % (f, ", ".join(st["S"])))
    spec = st["S"][f]
    runs = []
    if req.get("sizes"):
        for s in req["sizes"]:
            r = B.resolve({"factor": f, "size": s})
            runs.append(("ölçü", r))
    for k in (req.get("k_sigma") or ([] if req.get("sizes") else [-2, -1, 1, 2])):
        runs.append(("σ-şəbəkə", B.resolve({"factor": f, "k_sigma": k})))
    live = st["live"].get(f)
    if req.get("live", True) is not False and live and live.get("ov") is not None:
        runs.append(("canlı", {"factor": f, "k_sigma": float(live["k"]), "size": float(live["size"]), "ov": live["ov"],
                               "tesvir": live.get("tesvir", "")}))
    if not runs:
        raise ApiError(400, "bad_parameter", "Ən azı bir ölçü verilməlidir (k_sigma və ya sizes)")
    if len(runs) > MAX_SIZES:
        raise ApiError(400, "too_many", "Ən çox %d ölçü (bir sorğuda)" % MAX_SIZES)
    targets = set(req.get("targets") or [])
    top = int(_num(req.get("top_components", 60), "top_components"))
    head, comps, sizes, warn = [], {}, [], []
    for variant, r in runs:
        if r["ov"] is None:
            continue
        fl, clip = sc.run_chain(r["ov"], "api-%s@%.3g" % (f, r["k_sigma"]))
        dd = sc.derived_delta(st["base"], fl, st["D"]["rgdpnon_2025"])
        rows = sc.head_rows(f, spec, variant, r["k_sigma"], r["size"], st["base"], fl, dd, st["bl"], clip, st["lab"])
        if targets:
            rows = [x for x in rows if x["hedef_id"] in targets]
        head += [{k: v for k, v in x.items() if k not in ("amil", "amil_ad", "olcu_vahidi", "qeyd")} for x in rows]
        warn += clip
        label = "%s k=%+.2fσ" % (variant, r["k_sigma"])
        comps[label] = components(B, fl, 10 ** 6)
        sizes.append({"variant": variant, "k_sigma": r["k_sigma"], "size": r["size"], "vahid": spec["vahid"],
                      "label": label, "tesvir": r.get("tesvir", "")})
    res = {"factor": next((x for x in records(st["S0"]) if x["amil"] == f), {"amil": f}), "sizes": sizes,
           "headline": head, "elasticity": elasticity(head), "warnings": sorted(set(warn))}
    res["components"], res["groups"] = merge_components(comps, sizes, top)
    res["parameters"] = parameters(views, f)
    res["score_year"], res["seconds"] = st["hy"], round(time.time() - t0, 3)
    res["notes"] = ["Cavablar MikroUnit zəncirinin öz Baseline icrasından fərqdir (xəttiləşdirmə fərz edilmir).",
                    "σ: %s (n=%s)." % (spec["sigma_esasi"], spec["n"])]
    return res


def elasticity(head):
    """Per target × year: response per σ for every size, and ±k asymmetry when both signs are present."""
    by = {}
    for r in head:
        if r["k_sigma"] is None or abs(r["k_sigma"]) < 1e-9 or r["delta"] is None or not np.isfinite(r["delta"]):
            continue
        by.setdefault((r["hedef_id"], r["hedef_ad"], r["vahid"], r["il"]), []).append((r["k_sigma"], r["delta"]))
    out = []
    for (tid, ad, unit, y), kv in by.items():
        kv.sort()
        per = [d / k for k, d in kv]
        pos = {round(k, 6): d for k, d in kv if k > 0}
        asym = [abs(d) / abs(pos[round(-k, 6)]) for k, d in kv if k < 0 and round(-k, 6) in pos and abs(pos[round(-k, 6)]) > 1e-12]
        out.append({"hedef_id": tid, "hedef_ad": ad, "vahid": unit, "il": y,
                    "delta_per_sigma": [{"k_sigma": k, "delta": d, "per_sigma": d / k} for k, d in kv],
                    "orta_per_sigma": float(np.mean(per)), "eyri_yayilma": float(np.max(per) - np.min(per)) if len(per) > 1 else 0.0,
                    "asimmetriya": float(np.mean(asym)) if asym else None})
    return out


def merge_components(comps, sizes, top):
    labels = [s["label"] for s in sizes]
    allc = {}
    for lab in labels:
        c = comps[lab]
        for r in c["top_pct"] + c["top_abs"]:
            e = allc.setdefault(r["komponent_id"], {k: r[k] for k in ("komponent_id", "komponent_ad", "modul", "qrup", "vahid",
                                                                      "olcu_sinfi", "il", "baza")} | {"tesir": {}})
            e["tesir"][lab] = r["tesir"]
    ref = next((s["label"] for s in sizes if abs(s["k_sigma"] - 1) < 1e-9), labels[0])
    rows = list(allc.values())
    for cls in ("%", None):
        sub = [r for r in rows if (r["olcu_sinfi"] == "%") == (cls == "%")]
        mx = max([abs(r["tesir"].get(ref) or 0) for r in sub] or [0]) or 1.0
        for r in sub:
            r["ehemiyyet"] = abs(r["tesir"].get(ref) or 0) / mx
    rows.sort(key=lambda r: -r["ehemiyyet"])
    groups = {}
    for r in rows:
        g = groups.setdefault((r["modul"], r["qrup"]), {"modul": r["modul"], "qrup": r["qrup"], "komponent_sayi": 0,
                                                       "max_ehemiyyet": 0.0, "en_cox": None})
        g["komponent_sayi"] += 1
        if r["ehemiyyet"] > g["max_ehemiyyet"]:
            g["max_ehemiyyet"], g["en_cox"] = r["ehemiyyet"], r["komponent_ad"]
    G = sorted(groups.values(), key=lambda g: -g["max_ehemiyyet"])
    for r in rows:
        r["tesir"] = [{"label": lab, "tesir": r["tesir"].get(lab)} for lab in labels]
    return rows[:top], G


def parameters(views, f):
    if views is None:
        return []
    S5 = views.frame("S5_parameter_sensitivity.csv", required=False)
    if S5 is None:
        return []
    d = S5[(S5["amil"] == f) & S5["metod"].astype(str).str.startswith("hədəfli")]
    d = d.sort_values("nisbi_dalgalanma", key=lambda s: s.abs(), ascending=False).head(25)
    cols = [c for c in ("hedef_id", "hedef_ad", "il", "parametr", "tenlik", "parametr_ad", "deyer", "se", "cavab_baza",
                        "cavab_plus_1se", "cavab_minus_1se", "d_cavab_d_parametr", "nisbi_dalgalanma") if c in d.columns]
    return records(d[cols])
