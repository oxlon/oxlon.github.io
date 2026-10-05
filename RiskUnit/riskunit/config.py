"""MIIS §15.5.3 risk unit — paths, horizons, seeds and scoring scales.

Every number that a Ministry user may want to change without touching code lives in
input/*.csv (thresholds, registers, roles). This file holds only structural settings.
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Upstream units. Overridable so the package runs on the Ministry's own server layout.
MACRO_DIR = Path(os.environ.get("MIIS_MACRO_DIR", ROOT.parents[1] / "18august" / "model"))
MICRO_DIR = Path(os.environ.get("MIIS_MICRO_DIR", ROOT.parent / "MicroUnit"))

INPUT = ROOT / "input"
DATA = ROOT / "data"
VINTAGES = DATA / "vintages"
OUTPUT = ROOT / "output"
REPORTS = ROOT / "reports"
SITE = ROOT / "site"
DOCS = ROOT / "docs"

for _p in (VINTAGES, OUTPUT, REPORTS, SITE):
    _p.mkdir(parents=True, exist_ok=True)

LAST_ACTUAL = 2025          # last full year of national accounts in both upstream units
FORECAST_YEARS = list(range(2026, 2031))
SEED = 20261002
N_SIM = 20000               # joint Monte Carlo draws (FR2)


def as_of() -> date:
    """Reference date of the run. RISK_AS_OF=YYYY-MM-DD pins it (tests, reproducible reruns)."""
    v = os.environ.get("RISK_AS_OF")
    return date.fromisoformat(v) if v else date.today()


def score_year(d: date | None = None) -> int:
    """Year on which risks are scored: the next calendar year once half of the current
    year is observed, otherwise the current year (12-month-ahead convention)."""
    d = d or as_of()
    return d.year + 1 if d.month >= 7 else d.year


# Upstream files the unit reads; the manifest hashes every one of them (baseline identifier).
MACRO_FILES = {
    "forecast_long": MACRO_DIR / "outputs" / "forecast_long.csv",
    "validation_backtest": MACRO_DIR / "outputs" / "validation_backtest.csv",
    "assumptions": MACRO_DIR / "data" / "assumptions.csv",
    "external_block": MACRO_DIR / "data" / "external_block_annual.csv",
    "monthly_panel": MACRO_DIR / "data" / "monthly_panel.csv",
    "macro_annual": MACRO_DIR / "data" / "macro_annual.csv",
    "public_panel": MACRO_DIR / "data" / "public_sources_panel.csv",
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
