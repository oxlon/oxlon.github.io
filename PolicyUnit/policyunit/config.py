"""Paths and global constants of the PolicyUnit (derived from the package location;
override sibling locations with environment variables MIIS_MICRO_DIR, MIIS_RISK_DIR,
MIIS_OXLON_DIR, MIIS_MINISTRY_DIR)."""
from __future__ import annotations

import os
from pathlib import Path

PKG = Path(__file__).resolve().parent
ROOT = PKG.parent                                   # PolicyUnit/
MP = ROOT.parent                                    # MIIS_Micro_Risk_Policy/

MICRO_ROOT = Path(os.environ.get("MIIS_MICRO_DIR", MP / "MicroUnit"))
RISK_ROOT = Path(os.environ.get("MIIS_RISK_DIR", MP / "RiskUnit"))
OXLON_ROOT = Path(os.environ.get("MIIS_OXLON_DIR", MP / "Macro_OxLon"))
MINISTRY_ROOT = Path(os.environ.get("MIIS_MINISTRY_DIR", MP / "Macro_MinistryUnit"))

CONFIG = ROOT / "config"
SCENARIOS = CONFIG / "scenarios"
DATA = ROOT / "data"
RAW = DATA / "raw"
OUTPUT = ROOT / "output"
WORK = ROOT / "work"
DOCS = ROOT / "docs"
LOGS = ROOT / "logs"

INSTRUMENTS_CSV = CONFIG / "instruments.csv"
ADAPTERS_CSV = CONFIG / "adapters.csv"
KPI_CSV = CONFIG / "kpi.csv"
FISCAL_PARAMS_CSV = CONFIG / "fiscal_params.csv"
LONGRUN_PARAMS_CSV = CONFIG / "longrun_params.csv"
INDICATORS_CSV = CONFIG / "indicators.csv"
IO_SECTORS_CSV = CONFIG / "io_sectors.csv"          # owned by the IO agent

# CAEM pinned copy (copied unchanged from RiskUnit/data/ministry or Macro_MinistryUnit)
CAEM_COPY = DATA / "ministry" / "CAEM.xlsx"
CAEM_UPSTREAM = MINISTRY_ROOT / "Ministry_CAEM" / "CAEM.xlsx"
CAEM_RISK_COPY = RISK_ROOT / "data" / "ministry" / "CAEM.xlsx"
CAEM_MD5 = "12c22d22eda046e050643004a8d7eec5"

# OxLon: only ever used through a COPY (never inside Macro_OxLon)
OXLON_COPY = Path(os.environ.get("POLICY_OXLON_COPY", WORK / "oxlon"))
# Hosted runs (GitHub Actions): the OxLon model copy (126 MB, incl. a 113 MB DSK workbook) is not in the
# repository -> POLICY_OXLON_DISABLED=1 marks the engine unavailable; every other engine is unchanged.
OXLON_DISABLED = os.environ.get("POLICY_OXLON_DISABLED", "0") == "1"
OXLON_DISABLED_NOTE_AZ = ("OxLon mühərriki bu mühitdə (GitHub Actions) əlçatan deyil: OxLon model nüsxəsi "
                          "(126 MB, o cümlədən 113 MB-lıq DSK iş kitabı) repozitoriyaya daxil edilmir. Müqayisə "
                          "OxLon kanalı olmadan aparılır; OxLon nəticələri yerli quraşdırmada hesablanır.")

MICRO_YEARS = [2026, 2027, 2028, 2029, 2030]       # MicroUnit chain horizon
FIRST_YEAR = 2026
LONG_END = int(os.environ.get("POLICY_LONG_END", 2035))
ALL_YEARS = list(range(FIRST_YEAR, LONG_END + 1))
CAEM_H0_YEAR = 2025                                 # CAEM horizon h=1 <-> 2026

RISK_API = os.environ.get("POLICY_RISK_API", "http://127.0.0.1:8791/api/v1")
NO_NETWORK = os.environ.get("POLICY_NO_NETWORK", "0") == "1"

ENGINE_MODULES = {                                  # engine id -> module candidates (plug-in)
    "micro": ["policyunit.eng_micro"],
    "caem": ["policyunit.eng_caem"],
    "oxlon": ["policyunit.eng_oxlon"],
    "io": ["policyunit.eng_io"],
    "microsim": ["policyunit.eng_microsim", "policyunit.eng_micro_sim"],
    "longrun": ["policyunit.eng_longrun"],
    "riskfx": ["policyunit.eng_riskfx"],
}
ENGINE_ORDER = ["micro", "caem", "oxlon", "riskfx", "io", "microsim", "longrun"]

ENGINE_LABEL_AZ = {
    "micro": "MikroUnit struktur zənciri (FR1→FR12)",
    "caem": "Nazirlik CAEM modeli — müqayisə",
    "oxlon": "OxLon makro (yalnız neft/tərəfdaş/məzənnə kanalları)",
    "io": "Girdi-çıxdı (Leontief/Ghosh) modeli",
    "microsim": "Ev təsərrüfatı mikrosimulyasiyası",
    "longrun": "Uzun müddət (struktur ekstrapolyasiya)",
    "riskfx": "RiskUnit FX ötürməsi (kalibrlənmiş, 2015–17)",
}


def ensure_dirs():
    for p in (OUTPUT, WORK, LOGS, DATA / "ministry"):
        p.mkdir(parents=True, exist_ok=True)
