"""Live data feeds and the vintage archive (FR1 indicator base, NFR1 real-time data, NFR2).

Every download is normalised to long format (series, date, value), hashed and stored once
under data/vintages/<YYYY-MM-DD>/. data/vintages/manifest.csv records each retrieval, so a
backtest can reconstruct exactly what was known on any past date. When a source cannot be
reached the last good vintage is used and the manifest says so.
"""
from __future__ import annotations

import hashlib
import io
import json
import urllib.request
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from . import config

MANIFEST = config.VINTAGES / "manifest.csv"
MANIFEST_COLS = ["feed", "vintage", "retrieved_utc", "path", "sha256", "n_obs",
                 "first_obs", "last_obs", "url", "status"]

FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
GPR_URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"
EPU_URL = "https://www.policyuncertainty.com/media/Global_Policy_Uncertainty_Data.xlsx"
USGS_URL = ("https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=1950-01-01"
            "&endtime={end}&minlatitude=38.3&maxlatitude=42.0&minlongitude=44.7"
            "&maxlongitude=50.7&minmagnitude=4.5&orderby=time-asc")
ERA5_URL = ("https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
            "&start_date=1960-01-01&end_date={end}&daily=precipitation_sum&timezone=Asia%2FBaku")

# Agricultural reference points for the drought index (ERA5 reanalysis grid cells):
# Ganja-Gazakh, Aran (Kura-Araz lowland), Shaki-Zagatala, Lankaran.
ERA5_POINTS = {"ganca": (40.68, 46.36), "aran": (40.00, 47.50),
               "seki": (41.20, 47.17), "lenkeran": (38.75, 48.85)}

GPR_COLS = {"GPR": "gpr_global", "GPRC_RUS": "gpr_rus", "GPRC_TUR": "gpr_tur",
            "GPRC_UKR": "gpr_ukr", "GPRC_ISR": "gpr_isr", "GPRC_CHN": "gpr_chn",
            "GPRC_SAU": "gpr_sau"}


class NoNetwork(RuntimeError):
    """RISK_NO_NETWORK=1 — the caller falls back to the last good cached vintage."""


_LAST_HIT: dict[str, float] = {}
MIN_INTERVAL = 1.0           # polite: at most one request per second per host
BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/120.0 Safari/537.36 MIIS-15.5.3-risk-unit")


_DEAD_HOSTS: dict[str, tuple[str, float]] = {}   # host -> (reason, time): a connection-level failure (after one
DEAD_TTL = 600.0                   # retry) skips the host for 10 min (v2.4: 9 × 30 s timeouts cost 4,5 min on 2026-10-06)


class HostDown(RuntimeError):
    """The host failed at connection level earlier in this run — not retried again."""


def _reason(exc: Exception) -> str:
    r = getattr(exc, "reason", None)
    return f"{type(exc).__name__}: {r if r is not None else exc}"[:160]


def _get(url: str, timeout: int = 20, ua: str | None = None) -> bytes:
    """HTTP GET with a ≤ 20 s timeout, ≤ 1 request/s per host, one retry on a connection-level error,
    a per-run dead-host breaker, and RISK_NO_NETWORK=1 support."""
    import time
    import urllib.error
    from urllib.parse import urlparse
    if config.no_network():
        raise NoNetwork("şəbəkə qadağandır (RISK_NO_NETWORK=1)")
    host = urlparse(url).netloc
    if host in _DEAD_HOSTS and time.time() - _DEAD_HOSTS[host][1] < DEAD_TTL:
        raise HostDown(f"{host} əlçatmaz (bu dövrdə əvvəlki sorğu: {_DEAD_HOSTS[host][0]})")
    for attempt in (1, 2):
        try:
            return _get_once(url, host, timeout, ua)
        except urllib.error.HTTPError:
            raise                                   # the server answered: not a connectivity problem
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if attempt == 2:
                _DEAD_HOSTS[host] = (_reason(exc), time.time())
                raise
            time.sleep(2.0)
    raise RuntimeError("unreachable")


def _get_once(url: str, host: str, timeout: int, ua: str | None) -> bytes:
    import time
    wait = MIN_INTERVAL - (time.time() - _LAST_HIT.get(host, 0.0))
    if wait > 0:
        time.sleep(wait)
    headers = {"User-Agent": ua or "MIIS-15.5.3-risk-unit", "Accept": "*/*"}
    if host.endswith("stlouisfed.org"):            # FRED's bot filter (2026-10) drops custom/browser UAs: urllib default
        headers = {}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=min(timeout, 20)) as r:
            return r.read()
    finally:
        _LAST_HIT[host] = time.time()


def _fred(series_id: str, code: str):
    def parse(raw: bytes) -> pd.DataFrame:
        d = pd.read_csv(io.BytesIO(raw))
        d.columns = ["date", "value"]
        d["value"] = pd.to_numeric(d["value"], errors="coerce")
        d = d.dropna()
        d["series"] = code
        return d[["series", "date", "value"]]
    return FRED.format(series_id), parse


def _gpr(raw: bytes) -> pd.DataFrame:
    g = pd.read_excel(io.BytesIO(raw))
    g = g[["month", *GPR_COLS]].rename(columns=GPR_COLS)
    g["date"] = pd.to_datetime(g["month"]).dt.strftime("%Y-%m-%d")
    out = g.drop(columns="month").melt("date", var_name="series", value_name="value").dropna()
    return out[["series", "date", "value"]]


def _epu(raw: bytes) -> pd.DataFrame:
    e = pd.read_excel(io.BytesIO(raw))
    e = e[pd.to_numeric(e["Year"], errors="coerce").notna()]
    e["date"] = [f"{int(y):04d}-{int(m):02d}-01" for y, m in zip(e["Year"], e["Month"])]
    col = "GEPU_current" if "GEPU_current" in e.columns else [c for c in e.columns if "GEPU" in c][0]
    out = pd.DataFrame({"series": "epu_global", "date": e["date"],
                        "value": pd.to_numeric(e[col], errors="coerce")}).dropna()
    return out


def _usgs(raw: bytes) -> pd.DataFrame:
    q = pd.read_csv(io.BytesIO(raw))
    out = pd.DataFrame({"series": "eq_mag", "date": q["time"].str[:10], "value": q["mag"],
                        "lat": q["latitude"], "lon": q["longitude"], "depth": q["depth"],
                        "place": q["place"]})
    return out.sort_values("date").reset_index(drop=True)


def _era5(raw_by_point: dict[str, bytes]) -> pd.DataFrame:
    frames = []
    for name, raw in raw_by_point.items():
        js = json.loads(raw)
        d = pd.DataFrame({"date": pd.to_datetime(js["daily"]["time"]),
                          "p": js["daily"]["precipitation_sum"]}).dropna()
        m = d.set_index("date")["p"].resample("MS").agg(["sum", "count"])
        m = m[m["count"] >= 25]                       # drop incomplete months
        frames.append(pd.DataFrame({"series": f"precip_{name}",
                                    "date": m.index.strftime("%Y-%m-%d"),
                                    "value": m["sum"].round(2).values}))
    return pd.concat(frames, ignore_index=True)


def feed_specs(end: str):
    specs = {
        "brent": _fred("DCOILBRENTEU", "brent_usd_daily"),
        "vix": _fred("VIXCLS", "vix"),
        "ust10": _fred("DGS10", "ust10y"),
        "fedfunds": _fred("FEDFUNDS", "fedfunds"),
        "eurusd": _fred("DEXUSEU", "eurusd"),
        "gpr": (GPR_URL, _gpr),
        "epu": (EPU_URL, _epu),
        "usgs": (USGS_URL.format(end=end), _usgs),
    }
    return specs


def read_manifest() -> pd.DataFrame:
    if MANIFEST.exists():
        return pd.read_csv(MANIFEST, dtype=str)
    return pd.DataFrame(columns=MANIFEST_COLS)


def _store(feed: str, df: pd.DataFrame, url: str, man: pd.DataFrame, vintage: str) -> dict:
    body = df.to_csv(index=False, lineterminator="\n").encode()
    sha = hashlib.sha256(body).hexdigest()
    prev = man[(man.feed == feed) & (man.status == "ok")]
    if len(prev) and prev.iloc[-1]["sha256"] == sha:
        path = prev.iloc[-1]["path"]                  # unchanged: point at the stored copy
    else:
        rel = f"{vintage}/{feed}.csv"
        (config.VINTAGES / vintage).mkdir(parents=True, exist_ok=True)
        (config.VINTAGES / rel).write_bytes(body)
        path = rel
    return {"feed": feed, "vintage": vintage,
            "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "path": path, "sha256": sha, "n_obs": len(df), "first_obs": str(df["date"].min()),
            "last_obs": str(df["date"].max()), "url": url, "status": "ok"}


def _fail_status(exc: Exception) -> str:
    """'keş: şəbəkə yoxdur' offline; otherwise 'xeta: <type>: <reason>' (the reason was dropped before v2.4)."""
    return "keş: şəbəkə yoxdur" if isinstance(exc, NoNetwork) else f"xeta: {_reason(exc)}"


def fetch_all(verbose: bool = True) -> pd.DataFrame:
    """Download every feed once; returns the manifest rows written by this call."""
    vintage = config.as_of().isoformat()
    end = vintage
    man = read_manifest()
    rows = []
    for feed, (url, parse) in feed_specs(end).items():
        try:
            prev = None
            if url.startswith(FRED.split("?")[0]):    # incremental: fetch the last ~4 months, merge with the history
                try:
                    prev = latest(feed)
                    start = (pd.Timestamp(prev["date"].max()) - pd.Timedelta(days=120)).date().isoformat()
                    url = f"{url}&cosd={start}"
                except FileNotFoundError:
                    prev = None
            df = parse(_get(url))
            if prev is not None:
                df = (pd.concat([prev[["series", "date", "value"]], df], ignore_index=True)
                      .drop_duplicates(["series", "date"], keep="last").sort_values("date").reset_index(drop=True))
            rows.append(_store(feed, df, url, man, vintage))
        except Exception as exc:                       # keep the last good vintage
            rows.append({"feed": feed, "vintage": vintage,
                         "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                         "path": "", "sha256": "", "n_obs": 0, "first_obs": "", "last_obs": "",
                         "url": url, "status": _fail_status(exc)})
        if verbose:
            r = rows[-1]
            print(f"  {feed:9s} {r['status']:>10s}  {r['n_obs']:>7} müşahidə, son: {r['last_obs']}")
    try:
        raw = {k: _get(ERA5_URL.format(lat=la, lon=lo, end=end), timeout=20)
               for k, (la, lo) in ERA5_POINTS.items()}
        rows.append(_store("era5", _era5(raw), ERA5_URL.split("?")[0], man, vintage))
    except Exception as exc:
        rows.append({"feed": "era5", "vintage": vintage,
                     "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "path": "", "sha256": "", "n_obs": 0, "first_obs": "", "last_obs": "",
                     "url": ERA5_URL.split("?")[0], "status": _fail_status(exc)})
    if verbose:
        r = rows[-1]
        print(f"  {'era5':9s} {r['status']:>10s}  {r['n_obs']:>7} müşahidə, son: {r['last_obs']}")
    new = pd.DataFrame(rows, columns=MANIFEST_COLS).astype(str)
    pd.concat([man, new], ignore_index=True).to_csv(MANIFEST, index=False, lineterminator="\n")
    return new


def latest(feed: str, as_of: str | None = None) -> pd.DataFrame:
    """Most recent good vintage of a feed retrieved on or before `as_of` (real-time view)."""
    man = read_manifest()
    m = man[(man.feed == feed) & (man.status == "ok")]
    if as_of:
        m = m[m.vintage <= as_of]
    if m.empty:
        raise FileNotFoundError(f"'{feed}' üçün saxlanılmış vintaj yoxdur — `python3 update.py --fetch`")
    return pd.read_csv(config.VINTAGES / m.iloc[-1]["path"])


def monthly(feed: str, series: str | None = None, how: str = "mean") -> pd.Series:
    d = latest(feed)
    if series:
        d = d[d.series == series]
    s = pd.Series(d["value"].values, index=pd.to_datetime(d["date"])).sort_index()
    return getattr(s.resample("MS"), how)().dropna()


def annual(feed: str, series: str | None = None, how: str = "mean", min_months: int = 12) -> pd.Series:
    m = monthly(feed, series, how="mean" if how == "mean" else "sum")
    g = m.groupby(m.index.year)
    out = g.mean() if how == "mean" else g.sum()
    return out[g.count() >= min_months]


def feed_status() -> pd.DataFrame:
    """Last good retrieval per feed with the age of its newest observation (NFR2 freshness)."""
    man = read_manifest()
    ok = man[man.status == "ok"].groupby("feed").tail(1).copy()
    ok["age_days"] = [(pd.Timestamp(config.as_of()) - pd.Timestamp(x)).days if x else np.nan
                      for x in ok["last_obs"]]
    return ok[["feed", "vintage", "retrieved_utc", "last_obs", "age_days", "n_obs", "sha256"]]
