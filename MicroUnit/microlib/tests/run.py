"""Run all microlib tests:  python3 -m microlib.tests.run  [-v] [module ...]"""
from __future__ import annotations

import importlib
import sys
import time

from ._harness import run_module

MODULES = ["test_estimators", "test_diagnostics", "test_robustness", "test_registry", "test_registry_dols", "test_registry_other",
           "test_engines", "test_catalog"]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    verbose = "-v" in argv
    pick = [a for a in argv if not a.startswith("-")] or MODULES
    t0 = time.perf_counter()
    allres = []
    for m in pick:
        mod = importlib.import_module(f"microlib.tests.{m}")
        allres += run_module(mod)
    n_ok = sum(r[2] for r in allres)
    for mod, name, ok, err, dt in allres:
        if verbose or not ok:
            print(f"{'PASS' if ok else 'FAIL'}  {mod}.{name}  ({dt:.2f}s)")
            if not ok:
                print("   " + err.replace("\n", "\n   "))
    print(f"\nmicrolib tests: {n_ok}/{len(allres)} passed in {time.perf_counter() - t0:.1f}s")
    return 0 if n_ok == len(allres) else 1


if __name__ == "__main__":
    sys.exit(main())
