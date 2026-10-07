"""Output catalogue `output/_catalog.csv` (file, owner, description_az, columns, frequency).
Every module registers its outputs with `register(...)` (merge by file name) or writes through
`write_csv(df, name, owner, description_az, frequency)`."""
from __future__ import annotations

import pandas as pd

from . import config

CAT_COLS = ["file", "owner", "description_az", "columns", "frequency", "rows", "updated"]


def _path():
    return config.OUTPUT / "_catalog.csv"


def read() -> pd.DataFrame:
    p = _path()
    if p.exists():
        df = pd.read_csv(p, dtype=str, keep_default_na=False)
        for c in CAT_COLS:
            if c not in df.columns:
                df[c] = ""
        return df[CAT_COLS]
    return pd.DataFrame(columns=CAT_COLS)


def register(file: str, owner: str, description_az: str, columns, frequency: str = "hər işə salınmada",
             rows: int | None = None):
    config.ensure_dirs()
    df = read()
    df = df[df["file"] != file]
    row = {"file": file, "owner": owner, "description_az": description_az,
           "columns": ";".join(columns) if not isinstance(columns, str) else columns,
           "frequency": frequency, "rows": "" if rows is None else str(rows),
           "updated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True).sort_values("file")
    df.to_csv(_path(), index=False)


def write_csv(df: pd.DataFrame, name: str, owner: str, description_az: str,
              frequency: str = "hər işə salınmada") -> str:
    config.ensure_dirs()
    p = config.OUTPUT / name
    df.to_csv(p, index=False)
    register(name, owner, description_az, list(df.columns), frequency, len(df))
    return str(p)
