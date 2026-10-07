#!/usr/bin/env python3
"""build_panel.py — data bundles of the Siyasət paneli (PolicyUnit decision panel, MİİS §15.5.4) from PolicyUnit/output.

    python3 panel/build_panel.py            # from PolicyUnit/ (≈ 10 s)
    python3 panel/build_panel.py --verify   # + determinism check: a second build in a temp folder must be byte-identical
    python3 panel/build_panel.py --shots    # + headless-Chrome screenshots of every page (desktop 1440, phone 390), 0 JS errors
    python3 panel/build_panel.py --partial  # development only: missing required files → warning instead of failure

Writes panel/data/*.js (window.POL.<bundle> = {<output file stem>: compact table, ...}), PolicyUnit/index.html (hub),
panel/js/labels.js, panel/i18n/untranslated.txt, panel/coverage_report.csv and panel/py/policyunit_bundle.zip + py/bundle.js
(in-browser Python backend, _build/pybundle.py; --no-pybundle skips). Checks (exit 1 on failure): required
outputs exist; every bundle parses and every JS file passes `node --check`; routes and links resolve; completeness (every
output is shown or listed as intentionally hidden; every official scenario has results); no untranslated English.
Output is deterministic (sorted keys, fixed rounding, date stamp from output/P1_run_meta.json).
Structure copied from RiskUnit/panel/build_panel.py (no runtime imports from other units).
"""
import argparse
import filecmp
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _build import bcore as C, b_data, b_docs, b_hub, b_check, b_i18n, b_labels, pybundle   # noqa: E402


def build(data_dir):
    C.USED.clear()
    C.MISSING.clear()
    C.BUNDLES.clear()
    tr = b_i18n.Tr()
    parts = b_data.build(tr) + b_docs.build(tr)
    sizes = {}
    srcs = [C.OUT / f for f in sorted(C.USED) if (C.OUT / f).exists()]
    run = (dict(parts)["core"].get("_meta") or {}).get("run") or {}
    stamp = {"date": str(run.get("run_at") or "")[:16].replace("T", " "), "md5": C.md5_files(srcs), "files": len(srcs),
             "vintage": run.get("vintage") or {}, "scenarios": len(run.get("scenarios") or [])}
    for name, T in parts:
        if name == "core":
            T["_meta"]["stamp"] = stamp
            T["_meta"]["hidden"] = b_check.HIDDEN
            T["_meta"]["used"] = {k: sorted(v) for k, v in sorted(C.USED.items())}
            T["_meta"]["missing"] = sorted(set(C.MISSING))
        sizes[name] = C.bundle(f"{name}.js", name, T, data_dir)
    return sizes, stamp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="ikinci yığımla determinizm yoxlaması")
    ap.add_argument("--shots", action="store_true", help="hər səhifənin ekran görüntüləri (headless Chrome)")
    ap.add_argument("--partial", action="store_true", help="yalnız inkişaf üçün: çatışmayan fayl xəbərdarlıqdır")
    ap.add_argument("--no-pybundle", action="store_true", help="brauzer üçün Python paketini (panel/py/) yeniləmə")
    a = ap.parse_args()
    data = C.PANEL / "data"
    sizes, stamp = build(data)
    ok = True
    if C.MISSING:
        print(f"TƏLƏB OLUNAN FAYL YOXDUR ({len(set(C.MISSING))}): " + ", ".join(sorted(set(C.MISSING))))
        print("  → əvvəlcə `python3 run_all.py` (və ya müvafiq mərhələni) işə salın.")
        if not a.partial:
            print("  yığım dayandırıldı.")
            return 1
        print("  (--partial: davam edilir; panel bu bölmələrdə «məlumat yoxdur» göstərir)")
    for n, s in sorted(sizes.items()):
        print(f"  data/{n}.js  {s / 1024:8.1f} KB")
    hl = C.csv("P1_headline.csv", "core")
    stats = {"scenarios": len(list((C.CONFIG / "scenarios").glob("*.json"))),
             "instruments": len(C.cfg("instruments.csv")), "kpi": len(C.cfg("kpi.csv")),
             "outputs": len({p.name for p in C.OUT.glob("*.*")}), "indicators": hl["indicator"].nunique() if hl is not None else 0}
    hub = b_hub.build(stats, stamp)
    if not a.no_pybundle:                                  # in-browser backend: panel/py/policyunit_bundle.zip + bundle.js
        print(pybundle.report(pybundle.build(C.PANEL, "policy_web")))
    labels = b_labels.build()
    checks = [("PAKETLƏR", b_check.check_parse(data)), ("SÜTUN ETİKETLƏRİ", b_labels.check(labels))]
    lerr, pages = b_check.check_links(hub)
    checks.append(("KEÇİDLƏR VƏ MARŞRUTLAR", lerr))
    cerr, ids = b_check.check_complete()
    checks.append(("TAMLIQ", cerr))
    bad = b_check.check_english(hub)
    checks.append(("TƏRCÜMƏ", [" | ".join(b) for b in bad]))
    rows = [{"fayl": f, "paket": ";".join(sorted(v))} for f, v in sorted(C.USED.items())]
    rows += [{"fayl": f, "paket": "gizli: " + why} for f, why in sorted(b_check.HIDDEN.items())]
    C.pd.DataFrame(rows).to_csv(C.PANEL / "coverage_report.csv", index=False)
    for title, errs in checks:
        if errs:
            ok = False
            print(f"{title} YOXLAMASI UĞURSUZ: {len(errs)}")
            for e in errs[:40]:
                print("  -", e)
        else:
            print(f"{title} OK")
    print(f"səhifələr: {len(pages)} ({', '.join(p or 'başlanğıc' for p in pages)}); ssenari: {len(ids)}; çıxış: {len(rows)}")
    if a.verify:
        with tempfile.TemporaryDirectory() as td:
            build(Path(td))
            diff = [p.name for p in sorted(data.glob("*.js")) if not filecmp.cmp(p, Path(td) / p.name, shallow=False)]
        if diff:
            ok = False
            print("DETERMİNİZM UĞURSUZ: " + ", ".join(diff))
        else:
            print("DETERMİNİZM OK — ikinci yığım bayt-bayt eynidir")
    if a.shots and ok:
        r = subprocess.run(["node", str(C.PANEL / "_build" / "shots.mjs")], cwd=C.PANEL)
        ok = ok and r.returncode == 0
    print("möhür", stamp["md5"], stamp["date"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
