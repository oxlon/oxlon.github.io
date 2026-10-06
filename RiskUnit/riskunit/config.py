"""MIIS §15.5.3 risk unit — paths, horizons, seeds and scoring scales.

Every number that a Ministry user may want to change without touching code lives in
input/*.csv (thresholds, registers, roles). This file holds only structural settings.
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent                      # MIIS_Micro_Risk_Policy (sibling units live here)

# Upstream units. Overridable so the package runs on the Ministry's own server layout.
# v2: the macro model of record is read from its *delivered* contract (Macro_OxLon/delivery),
# which is SHA-256-identical to the former OxLon/18august/model copy (verified 2026-10-06).
# MIIS_MACRO_DIR may point either to a delivery root (2_neticeler/ + 4_melumat/) or to a model
# root (outputs/ + data/); the layout is detected below.
MACRO_DIR = Path(os.environ.get("MIIS_MACRO_DIR", PROJECT / "Macro_OxLon" / "delivery"))
MICRO_DIR = Path(os.environ.get("MIIS_MICRO_DIR", PROJECT / "MicroUnit"))
MINISTRY_DIR = Path(os.environ.get("MIIS_MINISTRY_DIR", PROJECT / "Macro_MinistryUnit"))

INPUT = ROOT / "input"
DATA = ROOT / "data"
VINTAGES = DATA / "vintages"
UPSTREAM_STORE = DATA / "upstream"          # tidy store of the three upstream units (D1)
WORK = ROOT / "work"                        # scratch copies for re-runs (never inside upstreams)
OUTPUT = ROOT / "output"
MONITOR_HISTORY = OUTPUT / "monitor_history"  # daily snapshots of D5/D6 (for D7 changes)
REPORTS = ROOT / "reports"
SITE = ROOT / "site"
DOCS = ROOT / "docs"
SCHEDULER = ROOT / "scheduler"
CATALOG_V2 = OUTPUT / "_catalog_v2.csv"

for _p in (VINTAGES, OUTPUT, REPORTS, SITE, UPSTREAM_STORE, MONITOR_HISTORY):
    _p.mkdir(parents=True, exist_ok=True)

LAST_ACTUAL = 2025          # last full year of national accounts in both upstream units
FORECAST_YEARS = list(range(2026, 2031))
SEED = 20261002
N_SIM = 20000               # joint Monte Carlo draws (FR2)


def as_of() -> date:
    """Reference date of the run. RISK_AS_OF=YYYY-MM-DD pins it (tests, reproducible reruns)."""
    v = os.environ.get("RISK_AS_OF")
    return date.fromisoformat(v) if v else date.today()


def no_network() -> bool:
    """RISK_NO_NETWORK=1: every fetcher uses its last good cache (tests, offline servers)."""
    return os.environ.get("RISK_NO_NETWORK", "") == "1"


def score_year(d: date | None = None) -> int:
    """Year on which risks are scored: the next calendar year once half of the current
    year is observed, otherwise the current year (12-month-ahead convention)."""
    d = d or as_of()
    return d.year + 1 if d.month >= 7 else d.year


def _macro_layout(base: Path) -> tuple[Path, Path]:
    """(outputs dir, data dir) for a delivery root or a model root."""
    if (base / "2_neticeler").is_dir():
        return base / "2_neticeler", base / "4_melumat"
    return base / "outputs", base / "data"


MACRO_OUT, MACRO_DATA = _macro_layout(MACRO_DIR)
# assumptions.csv is part of the delivered contract (2_neticeler) but sits in data/ of a model root
_ASSUME_DIR = MACRO_OUT if (MACRO_OUT / "assumptions.csv").exists() else MACRO_DATA

# Upstream files the unit reads; the manifest hashes every one of them (baseline identifier).
MACRO_FILES = {
    "forecast_long": MACRO_OUT / "forecast_long.csv",
    "validation_backtest": MACRO_OUT / "validation_backtest.csv",
    "assumptions": _ASSUME_DIR / "assumptions.csv",
    "external_block": MACRO_DATA / "external_block_annual.csv",
    "monthly_panel": MACRO_DATA / "monthly_panel.csv",
    "macro_annual": MACRO_DATA / "macro_annual.csv",
    "public_panel": MACRO_DATA / "public_sources_panel.csv",
}
# v2 additions (hashed in the manifest, optional for the v1 pipeline)
MACRO_FILES_V2 = {
    "equations_catalog": MACRO_OUT / "equations_catalog.csv",
    "series_dictionary": MACRO_OUT / "series_dictionary.csv",
    "assumption_registry": (MACRO_OUT if (MACRO_OUT / "assumption_registry.csv").exists() else MACRO_DATA)
    / "assumption_registry.csv",
}
MICRO_FILES = {
    "fr1_multipliers": MICRO_DIR / "output" / "FR1_multipliers.csv",
    "fr1_forecast": MICRO_DIR / "output" / "FR1_forecast_full.csv",
    "fr1_draws": MICRO_DIR / "output" / "FR1_fan_draws.csv",
    "fr1_holdout": MICRO_DIR / "output" / "FR1_holdout_validation.csv",
    "fr10_ews": MICRO_DIR / "output" / "FR10_early_warning.csv",
    "fr10_plausibility": MICRO_DIR / "output" / "FR10_plausibility.csv",
    "fr12_ews": MICRO_DIR / "output" / "FR12_early_warning.csv",
    "fr12_false_listing": MICRO_DIR / "output" / "FR12_early_warning_false_listing.csv",
    "fr12_scenarios": MICRO_DIR / "output" / "FR12_scenario_summary.csv",
}
MICRO_MODULES = ["FR1", "FR3", "FR4", "FR5", "FR10", "FR12"]
MICRO_FILES_V2 = {
    **{f"{m.lower()}_tidy": MICRO_DIR / "output" / f"{m}_forecast_tidy.csv" for m in MICRO_MODULES},
    **{f"{m.lower()}_catalog": MICRO_DIR / "output" / f"{m}_indicator_catalog.csv" for m in MICRO_MODULES},
    **{f"{m.lower()}_equations": MICRO_DIR / "output" / f"{m}_equations.json" for m in MICRO_MODULES},
    "fr10_cross_multipliers": MICRO_DIR / "output" / "FR10_cross_sector_multipliers.csv",
}
MINISTRY_FILES = {
    "caem": MINISTRY_DIR / "Ministry_CAEM" / "CAEM.xlsx",
    "bottomup_report": MINISTRY_DIR / "Ministry_Bottom_up_Model" / "MOE REPORT 3 PAGES.xlsx",
    "vereq8": MINISTRY_DIR / "Ministry_Bottom_up_Model" / "8 vərəq.xlsx",
    "eviews_data": MINISTRY_DIR / "eviews" / "eviews_data.csv",
}
