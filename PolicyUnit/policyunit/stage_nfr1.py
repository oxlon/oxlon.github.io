"""run_all stage: NFR1 retrospective validation (V_nfr1_* outputs + docs/Sapma_hesabati.md).
Runs after the IO and microsimulation stages, whose E7 / 2019 / 2025 validation files it reads."""
from __future__ import annotations


def _run(args, log):
    from . import validate
    r = validate.run(log=log)
    log(f"  yazıldı: {len(r['files'])} fayl ({r['meta']['seconds']} s)")


def register(R):
    R.add("nfr1.validate", _run, owner="nfr1", after=["core.scenarios", "io.outputs", "microsim.outputs"],
          optional=True, description_az="NFR1: tarixi siyasət hadisələri üzrə retrospektiv validasiya və sapma hesabatı")
