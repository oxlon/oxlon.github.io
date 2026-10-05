"""Writes panel/i18n/az.csv from the rows_*.py source lists (+ FR10 branch names en → az from the outputs).
    python3 panel/i18n/src/make_az.py
"""
import csv, importlib.util, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
PANEL = HERE.parent.parent
sys.path.insert(0, str(PANEL))
rows = []
for p in sorted(HERE.glob("rows_*.py")):
    spec = importlib.util.spec_from_file_location(p.stem, p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    rows += [(r[0], r[1], r[2], p.stem) for r in m.ROWS]
try:
    import pandas as pd
    from _build.pnames import nace
    sc = pd.read_csv(PANEL.parent / "output" / "FR10_branch_scorecard.csv", dtype={"nace2": str})
    have = {r[1] for r in rows}
    for code, en in sorted(set(zip(sc.nace2, sc.branch))):
        if isinstance(en, str) and en not in have and nace(code) != code:
            rows.append(("phrase", en, nace(code), "FR10_branch_scorecard"))
except Exception as e:                                   # pragma: no cover
    print("branch names skipped:", e)
seen, out = set(), []
for r in rows:
    if (r[0], r[1]) not in seen:
        seen.add((r[0], r[1])); out.append(r)
with (PANEL / "i18n" / "az.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh); w.writerow(["mode", "en", "az", "note"]); w.writerows(out)
print(len(out), "rows ->", PANEL / "i18n" / "az.csv")
