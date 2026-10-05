#!/usr/bin/env python3
"""build_panel.py — write the data bundles of the Mikro Model İş paneli from MicroUnit/output.

    python3 panel/build_panel.py          # from MicroUnit/

Every forecast series that FR1, FR3, FR4, FR5, FR10 and FR12 export (levels, growth, all scenarios,
5–95 % bands where the module exports them) goes into panel/data/fr*.js; the SYNTHETIC Layer-B
demonstration into panel/data/synthetic.js; texts and lists into panel/data/meta.js; the hub
MicroUnit/index.html (links to site/ and panel/).

Coverage: panel/coverage_report.csv lists every indicator × scenario with the number of forecast
years present. The build FAILS (exit 1) if any series that has a forecast lacks one of 2026–2030, or a
scenario is missing for a series that exports scenarios. Output is deterministic (sorted keys, fixed
rounding); set SOURCE_DATE_EPOCH to pin the date stamp.
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _build import pcore as C, p_hub                            # noqa: E402
from _build import p_fr1, p_fr3, p_fr4, p_fr5, p_fr10, p_fr12, p_synth, p_meta  # noqa: E402


def main():
    R = C.Reg()
    for mod in (p_fr1, p_fr3, p_fr4, p_fr5, p_fr10, p_fr12):
        n0 = len(R.S)
        mod.build(R)
        print(f"{mod.__name__.split('.')[-1]:7s} {len(R.S) - n0:4d} series")
    data = C.PANEL / "data"
    R.write(data)
    syn = p_synth.build(data)
    meta = p_meta.build(data, {r["i"] for r in R.S})
    p_hub.build(R.S, meta)
    nsc = sum(len(r["s"]) for r in R.S)
    cov = C.pd.DataFrame(R.cov)
    print(f"series {len(R.S)}, scenario paths {nsc}, values {nsc * 5} (levels) + {nsc * 5} (growth); "
          f"bands {sum('q' in r for r in R.S)}; synthetic panels {len(syn)}; stamp {meta['stamp']['md5']}")
    print("coverage:", cov.status.value_counts().to_dict())
    if R.errors:
        print(f"COVERAGE FAILED: {len(R.errors)} series lack forecast years or scenarios:")
        for e in R.errors[:50]:
            print("  -", e)
        return 1
    print("COVERAGE OK — every exported forecast series has all years 2026–2030 in every scenario it carries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
