#!/usr/bin/env python3
"""PolicyUnit pipeline (MİİS §15.5.4). Stage registry; other modules plug in WITHOUT editing this file:
any `policyunit/stage_*.py` exposing `register(R)` is discovered and may call
`R.add(name, fn, owner, after=[...], optional=True, description_az="...")`; fn(args, log) -> None.

  python3 run_all.py                       all stages, all scenarios
  python3 run_all.py --list                list stages
  python3 run_all.py --only core.scenarios --scenario mw20_2027 --kpi gdp_short,gdp_medium,...
Exit codes: 0 OK, 1 a required stage failed, 2 configuration error. Long runs: start in background
and poll logs/run_all.log (600 s watchdog)."""
from __future__ import annotations

import argparse
import importlib
import pkgutil
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from policyunit import config  # noqa: E402


class Registry:
    def __init__(self):
        self.stages = []

    def add(self, name, fn, owner="core", after=None, optional=False, description_az=""):
        self.stages = [s for s in self.stages if s["name"] != name]
        self.stages.append({"name": name, "fn": fn, "owner": owner, "after": list(after or []),
                            "optional": optional, "description_az": description_az})

    def ordered(self):
        done, out, pending = set(), [], list(self.stages)
        while pending:
            ready = [s for s in pending if all(a in done or a not in {x["name"] for x in self.stages} for a in s["after"])]
            if not ready:
                raise RuntimeError("stage asılılıqlarında dövr var: " + ", ".join(s["name"] for s in pending))
            for s in ready:
                out.append(s)
                done.add(s["name"])
                pending.remove(s)
        return out


def _validate(args, log):
    from policyunit import registry, scenario
    errs = registry.validate_catalogue()
    for sid in scenario.all_ids():
        try:
            scenario.load(sid)
        except scenario.ScenarioError as e:
            errs.append(f"{sid}: {e}")
    if errs:
        raise SystemExit("Konfiqurasiya xətaları:\n- " + "\n- ".join(errs))
    log(f"  kataloq OK; {len(scenario.all_ids())} ssenari")


def _scenarios(args, log):
    from policyunit import outputs
    ids = args.scenario.split(",") if args.scenario else None
    kpis = args.kpi.split(",") if args.kpi else None
    r = outputs.write_all(ids, kpis, log)
    log(f"  yazıldı: {', '.join(r['files'])} ({r['meta']['seconds']} s)")


def _kpi(args, log):
    from policyunit import outputs
    ids = args.scenario.split(",") if args.scenario else None
    kpis = args.kpi.split(",") if args.kpi else None
    outputs.write_kpi(ids, kpis, log)


def _io_outputs(args, log):
    from policyunit import io_outputs
    rc = io_outputs.main([])
    if rc:
        raise RuntimeError(f"io_outputs çıxış kodu {rc}")


def _microsim_outputs(args, log):
    from policyunit import ms_outputs
    ms_outputs.write_all(log)


def _freshness(args, log):
    """C5 + verification (1): output order/consistency and baseline vintage ids (policyunit.freshness)."""
    from policyunit import freshness
    df = freshness.check(getattr(args, "_t0", None), log)
    for r in df[df.status != "ok"].itertuples():
        log(f"  {r.status.upper()}: {r.check} — {r.message_az}")
    if (df.status == "xəta").any():
        raise RuntimeError(f"Təzəlik yoxlaması: {int((df.status == 'xəta').sum())} xəta (output/P1_freshness.csv)")
    log(f"  təzəlik yoxlaması: {int((df.status == 'ok').sum())} ok, {int((df.status == 'xəbərdarlıq').sum())} xəbərdarlıq")


def _noop(args, log):
    log("  no-op: KPI-lar artıq core.kpi mərhələsində FR4-dən sonra hesablanır")


def build_registry() -> Registry:
    R = Registry()
    R.add("core.validate", _validate, description_az="Alət, adapter və ssenari fayllarının yoxlanışı")
    R.add("io.outputs", _io_outputs, owner="io", after=["core.validate"], optional=True,
          description_az="FR2: girdi-çıxdı nəticələri → P2_, V_io_, D_io_")
    R.add("microsim.outputs", _microsim_outputs, owner="microsim", after=["core.validate", "io.outputs"],
          optional=True, description_az="FR3: mikrosimulyasiya nəticələri → P3_, V_microsim_")
    R.add("core.scenarios", _scenarios, after=["core.validate", "io.outputs", "microsim.outputs"],
          description_az="Bütün ssenarilər → P1_, N2_")
    R.add("core.kpi", _kpi, after=["core.scenarios", "microsim.outputs", "fr4.side_effects", "nfr1.validate"],
          description_az="FR5: KPI dəyərləri, çoxkriteriyalı bal və reytinq → P5_ (FR4/NFR1-dən sonra)")
    pkg = ROOT / "policyunit"
    for m in pkgutil.iter_modules([str(pkg)]):
        if m.name.startswith("stage_"):
            mod = importlib.import_module(f"policyunit.{m.name}")
            if hasattr(mod, "register"):
                mod.register(R)
    R.add("core.freshness", _freshness, after=["core.kpi", "panel.build", "fr4.kpi_refresh"],
          description_az="C5: çıxışların təzəlik və ardıcıllıq yoxlaması (P3/P4/V_nfr1 → P5 → panel)")
    if any(x["name"] == "fr4.kpi_refresh" for x in R.stages):      # superseded by core.kpi (kept as no-op)
        old = next(x for x in R.stages if x["name"] == "fr4.kpi_refresh")
        R.add("fr4.kpi_refresh", _noop, owner=old["owner"], after=old["after"], optional=True,
              description_az="(no-op) KPI-lar core.kpi mərhələsində FR4-dən sonra hesablanır")
    return R


def main(argv=None):
    ap = argparse.ArgumentParser(description="PolicyUnit run_all")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--skip", default="")
    ap.add_argument("--scenario", default="")
    ap.add_argument("--kpi", default="")
    args = ap.parse_args(argv)
    R = build_registry()
    stages = R.ordered()
    if args.list:
        for s in stages:
            print(f"{s['name']:24s} {s['owner']:10s} {'(isteğe bağlı) ' if s['optional'] else ''}{s['description_az']}")
        return 0
    only = set(filter(None, args.only.split(",")))
    skip = set(filter(None, args.skip.split(",")))
    config.LOGS.mkdir(parents=True, exist_ok=True)
    logf = open(config.LOGS / "run_all.log", "a", encoding="utf-8")

    def log(msg):
        print(msg, flush=True)
        logf.write(msg + "\n")
        logf.flush()

    log(f"=== run_all {time.strftime('%Y-%m-%d %H:%M:%S')}")
    args._t0 = time.time() - 1
    rc = 0
    for s in stages:
        if (only and s["name"] not in only) or s["name"] in skip:
            continue
        t0 = time.perf_counter()
        log(f"[{s['name']}] başladı")
        try:
            s["fn"](args, log)
            log(f"[{s['name']}] OK ({time.perf_counter() - t0:.1f} s)")
        except SystemExit as e:
            log(f"[{s['name']}] KONFİQURASİYA XƏTASI: {e}")
            return 2
        except Exception as e:  # noqa: BLE001
            log(f"[{s['name']}] XƏTA: {type(e).__name__}: {e}\n{traceback.format_exc(limit=5)}")
            if not s["optional"]:
                rc = 1
    log(f"=== bitdi rc={rc}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
