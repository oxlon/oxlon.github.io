"""Instrument catalogue, adapter registry and parameter files (config/*.csv).
Plug-in architecture (NFR4): engines read their own adapter rows; a new instrument or scenario
needs only CSV/JSON rows. Transform grammar: `pct|add|level|target|target_gdp|shock_gdp|target_rev|
custom:<fn>` with an optional multiplier suffix `*k`."""
from __future__ import annotations

import importlib
from functools import lru_cache

import pandas as pd

from . import config

INSTR_COLS = ["id", "name_az", "family", "unit", "default_size", "min", "max", "engines",
              "description_az"]
ADAPTER_COLS = ["instrument", "engine", "target_key", "transform", "note_az"]
FAMILIES = ["vergi", "xərc", "sosial", "əmək", "monetar", "ticarət", "sektor", "tənzimləmə"]
UNITS = ["pct", "pp", "mln_azn", "abs"]


class ConfigError(ValueError):
    """Configuration error with an Azerbaijani message."""


def _read(path, cols):
    if not path.exists():
        raise ConfigError(f"konfiqurasiya faylı tapılmadı: {path}")
    df = pd.read_csv(path, dtype=str, keep_default_na=False, skipinitialspace=True)
    miss = [c for c in cols if c not in df.columns]
    if miss:
        raise ConfigError(f"{path.name}: sütun(lar) çatışmır: {', '.join(miss)}")
    return df.apply(lambda s: s.str.strip())


@lru_cache(maxsize=1)
def instruments() -> pd.DataFrame:
    df = _read(config.INSTRUMENTS_CSV, INSTR_COLS)
    for c in ("default_size", "min", "max"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c, d in (("cost_rule", "none"), ("cost_in_fr1", "no")):
        if c not in df.columns:
            df[c] = d
        df[c] = df[c].replace("", d)
    return df.set_index("id", drop=False)


@lru_cache(maxsize=1)
def adapters() -> pd.DataFrame:
    return _read(config.ADAPTERS_CSV, ADAPTER_COLS)


def reload():
    instruments.cache_clear()
    adapters.cache_clear()
    params.cache_clear()


def instrument(iid: str) -> dict:
    df = instruments()
    if iid not in df.index:
        raise ConfigError(f"naməlum siyasət aləti '{iid}' (instruments.csv-də yoxdur)")
    return df.loc[iid].to_dict()


def engines_for(iid: str) -> list[str]:
    return [e.strip() for e in instrument(iid)["engines"].split(";") if e.strip()]


def adapters_for(engine: str, iid: str | None = None) -> pd.DataFrame:
    a = adapters()
    a = a[a["engine"] == engine]
    return a if iid is None else a[a["instrument"] == iid]


def parse_transform(t: str) -> tuple[str, float]:
    """'add*0.5' -> ('add', 0.5); 'custom:fn' -> ('custom:fn', 1.0)."""
    t = (t or "").strip()
    if "*" in t:
        name, k = t.rsplit("*", 1)
        try:
            return name.strip(), float(k)
        except ValueError as e:
            raise ConfigError(f"transform '{t}': miqyas ədəd olmalıdır") from e
    return t, 1.0


@lru_cache(maxsize=4)
def params(name: str = "fiscal") -> dict:
    path = {"fiscal": config.FISCAL_PARAMS_CSV, "longrun": config.LONGRUN_PARAMS_CSV}[name]
    df = _read(path, ["param", "value"])
    out = {}
    for p, v in zip(df["param"], df["value"]):
        try:
            out[p] = float(v)
        except ValueError:
            out[p] = v
    return out


def engine_module(engine: str):
    """Import the engine module (plug-in); None if it does not exist yet."""
    for name in config.ENGINE_MODULES.get(engine, [f"policyunit.eng_{engine}"]):
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError as e:
            if e.name != name:
                raise
    return None


def validate_catalogue() -> list[str]:
    """Consistency checks of instruments/adapters (Azerbaijani messages; empty = OK)."""
    err = []
    ins = instruments()
    for iid, r in ins.iterrows():
        if r["family"] not in FAMILIES:
            err.append(f"{iid}: naməlum ailə '{r['family']}'")
        if r["unit"] not in UNITS:
            err.append(f"{iid}: naməlum vahid '{r['unit']}'")
        for e in engines_for(iid):
            if e not in config.ENGINE_MODULES:
                err.append(f"{iid}: naməlum mühərrik '{e}'")
        if not (r["min"] <= r["default_size"] <= r["max"]):
            err.append(f"{iid}: default_size [min, max] intervalından kənardır")
    for _, a in adapters().iterrows():
        if a["instrument"] not in ins.index:
            err.append(f"adapters.csv: naməlum alət '{a['instrument']}'")
        try:
            parse_transform(a["transform"])
        except ConfigError as e:
            err.append(str(e))
    return err
