"""synth.py — facts about the two SYNTHETIC input files, counted from the files at build time."""
import pandas as pd

from . import core

PANEL = core.DATA / "firm_panel" / "FR10_firm_panel_SYNTHETIC.csv"
REG = core.DATA / "business_register" / "FR12_business_register_SYNTHETIC.csv"

# NACE Rev.2 division -> section letter (standard ranges)
_SECT = [(1, 3, "A"), (5, 9, "B"), (10, 33, "C"), (35, 35, "D"), (36, 39, "E"), (41, 43, "F"), (45, 47, "G"),
         (49, 53, "H"), (55, 56, "I"), (58, 63, "J"), (64, 66, "K"), (68, 68, "L"), (69, 75, "M"), (77, 82, "N"),
         (84, 84, "O"), (85, 85, "P"), (86, 88, "Q"), (90, 93, "R"), (94, 96, "S"), (97, 98, "T"), (99, 99, "U")]


def section(div):
    try:
        n = int(div)
    except (TypeError, ValueError):
        return None
    for a, b, s in _SECT:
        if a <= n <= b:
            return s
    return None


_memo = {}


def panel():
    if "p" not in _memo:
        core.mark(PANEL)
        p = pd.read_csv(PANEL, dtype={"nace2": str}, usecols=["data_status", "firm_id", "year", "nace2", "region"])
        _memo["p"] = {"rows": len(p), "firms": p.firm_id.nunique(), "nace": p.nace2.nunique(),
                      "regions": p.region.nunique(), "y0": int(p.year.min()), "y1": int(p.year.max()),
                      "marker": p.data_status.iloc[0], "all_marked": bool((p.data_status == p.data_status.iloc[0]).all()),
                      "cols": len(pd.read_csv(PANEL, nrows=0).columns)}
    else:
        core.mark(PANEL)
    return _memo["p"]


def register():
    if "r" not in _memo:
        core.mark(REG)
        r = pd.read_csv(REG, dtype={"nace2": str},
                        usecols=["data_status", "firm_id", "year", "nace2", "region", "status", "weight"])
        last = int(r.year.max())
        a = r[(r.year == last) & (r.status == "active")]
        _memo["r"] = {"rows": len(r), "records": r.firm_id.nunique(), "active": int(a.weight.sum()), "last": last,
                      "sections": r.nace2.map(section).nunique(), "nace": r.nace2.nunique(),
                      "regions": r.region.nunique(), "y0": int(r.year.min()), "y1": last,
                      "marker": r.data_status.iloc[0], "all_marked": bool((r.data_status == r.data_status.iloc[0]).all()),
                      "syn_ids": bool(r.firm_id.str.startswith("SYN-").all()),
                      "cols": len(pd.read_csv(REG, nrows=0).columns)}
    else:
        core.mark(REG)
    return _memo["r"]


def swap_rows(name):
    """Swap-test table rows: (test, passed, detail)."""
    s = core.csv(name)
    return [(r.test, bool(r.passed), r.detail) for r in s.itertuples()]


def pipeline_rows(name):
    s = core.csv(name)
    return [(r.test, bool(r.passed), getattr(r, "value", "")) for r in s.itertuples()]
