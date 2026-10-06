"""Market risk factors and exposure-source fetchers for the VaR / CaR layer (RiskUnit v2).

Every fetcher follows the v2 contract: timeout <= 20 s, at most one request per second, the raw
response is cached under data/vintages/<source>/<YYYY-MM-DD>/, a failed fetch falls back to the
last good cache, every attempt is recorded in output/D2_feed_status.csv, and RISK_NO_NETWORK=1
switches every call to the cache (tests run offline).

Sources: FRED (Brent, Henry Hub, FX, UST curve, S&P 500, EM spreads, broad dollar, VIX, OECD equity
index), World Bank Pink Sheet (monthly gold, Brent, European gas), ECB SDW (TRY), CBAR daily
official rates XML (USD, EUR, GBP, RUB, TRY, CNY, JPY and gold XAU in AZN), CBAR statistical
bulletin (monthly averages, reserves, banking), SOFAZ and MinFin publications (exposures.py).
"""
from __future__ import annotations

import io
import os
import re
import time
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

UA = "MIIS-15.5.3-risk-unit (VaR/CaR)"
TIMEOUT = 20
STATUS_FILE = config.OUTPUT / "D2_feed_status.csv"
OWNER = "feeds_market"
_last_request = [0.0]


class FeedUnavailable(RuntimeError):
    """Neither the network nor a cached vintage could supply the data."""


def no_network() -> bool:
    return os.environ.get("RISK_NO_NETWORK", "0") == "1" or bool(getattr(config, "no_network", lambda: False)())


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_get(url: str, timeout: int = TIMEOUT, accept: str | None = None) -> bytes:
    """Polite GET: <= 1 request per second, bounded timeout, identifying user agent."""
    if no_network():
        raise FeedUnavailable("RISK_NO_NETWORK=1")
    wait = 1.0 - (time.time() - _last_request[0])
    if wait > 0:
        time.sleep(wait)
    hdr = {"User-Agent": UA}
    if accept:
        hdr["Accept"] = accept
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=timeout) as r:
            return r.read()
    finally:
        _last_request[0] = time.time()


def vintage_dir(source: str, day: str | None = None) -> Path:
    d = config.VINTAGES / source / (day or config.as_of().isoformat())
    d.mkdir(parents=True, exist_ok=True)
    return d


def latest_cached(source: str, name: str) -> Path | None:
    base = config.VINTAGES / source
    if not base.exists():
        return None
    for d in sorted((p for p in base.iterdir() if p.is_dir()), reverse=True):
        if (d / name).exists() and (d / name).stat().st_size > 0:
            return d / name
    return None


_STATUS_ROWS: list[dict] = []


def record(feed: str, source: str, url: str, status: str, path: Path | str | None,
           n_obs: int | None = None, last_obs: str | None = None, note: str = "") -> None:
    lvl = "ok" if status == "canlı" or (no_network() and status.startswith("keş")) else "xəbərdarlıq"
    _STATUS_ROWS.append({"feed": feed, "source": source, "owner_module": OWNER, "url": url,
                         "status": status, "seviyye": lvl, "retrieved_utc": _utc(), "path": str(path or ""),
                         "n_obs": "" if n_obs is None else int(n_obs), "last_obs": last_obs or "",
                         "note": note})


def flush_status() -> Path:
    """Read-modify-write D2_feed_status.csv: one row per feed (latest attempt wins); rows owned
    by other modules are kept untouched."""
    if not _STATUS_ROWS:
        return STATUS_FILE
    new = pd.DataFrame(_STATUS_ROWS).drop_duplicates("feed", keep="last")
    if STATUS_FILE.exists():
        old = pd.read_csv(STATUS_FILE, dtype=str)
        if "feed" in old.columns:
            old = old[~old["feed"].isin(new["feed"])]
        out = pd.concat([old, new.astype(str)], ignore_index=True)
    else:
        out = new
    out.to_csv(STATUS_FILE, index=False, lineterminator="\n")
    _STATUS_ROWS.clear()
    return STATUS_FILE


def fetch_raw(feed: str, source: str, name: str, url: str, accept: str | None = None,
              validate=None) -> tuple[bytes, str, Path]:
    """Fetch one raw response; cache it; fall back to the last good cache. Returns
    (bytes, status, path) with status 'canlı' (live) or 'keş: <reason>' (cache)."""
    try:
        raw = http_get(url, accept=accept)
        if validate is not None and not validate(raw):
            raise ValueError("cavab formatı gözlənilən deyil")
        p = vintage_dir(source) / name
        p.write_bytes(raw)
        return raw, "canlı", p
    except Exception as exc:                                   # noqa: BLE001 - any failure -> cache
        p = latest_cached(source, name)
        if p is None:
            record(feed, source, url, f"xəta: {type(exc).__name__}", None, note=str(exc)[:120])
            raise FeedUnavailable(f"{feed}: şəbəkə yoxdur və keş tapılmadı ({exc})") from exc
        why = "şəbəkəsiz rejim" if no_network() else type(exc).__name__
        return p.read_bytes(), f"keş: {why}", p


# ---------------------------------------------------------------- FRED
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
FRED_DAILY = {          # factor code -> (FRED id, unit, label_az)
    "brent": ("DCOILBRENTEU", "USD/barel", "Brent neft qiyməti"),
    "gas_hh": ("DHHNGSP", "USD/MMBtu", "Təbii qaz, Henry Hub"),
    "eurusd": ("DEXUSEU", "USD/EUR", "Avro məzənnəsi (USD/EUR)"),
    "gbpusd": ("DEXUSUK", "USD/GBP", "Funt sterlinq (USD/GBP)"),
    "usdcny": ("DEXCHUS", "CNY/USD", "Çin yuanı (CNY/USD)"),
    "usdjpy": ("DEXJPUS", "JPY/USD", "Yapon yeni (JPY/USD)"),
    "usd_broad": ("DTWEXBGS", "indeks", "ABŞ dollarının geniş indeksi"),
    "ust2": ("DGS2", "%", "ABŞ xəzinə istiqrazı 2 il"),
    "ust5": ("DGS5", "%", "ABŞ xəzinə istiqrazı 5 il"),
    "ust10": ("DGS10", "%", "ABŞ xəzinə istiqrazı 10 il"),
    "spx": ("SP500", "indeks", "S&P 500 (qlobal səhm proksisi)"),
    "em_spread": ("BAMLEMCBPIOAS", "%", "İnkişaf etməkdə olan bazarlar korporativ spredi (EMBI proksisi)"),
    "em_hy_spread": ("BAMLEMHBHYCRPIOAS", "%", "EM yüksək gəlirli korporativ spred"),
    "vix": ("VIXCLS", "indeks", "VIX dəyişkənlik indeksi"),
    # v2.4: long-history public credit spread (ICE BofA OAS on FRED covers only the last 3 years) and oil
    # implied volatility (CBOE OVX, WTI options) used to price the T26 put hedge
    "baa_spread": ("BAA10Y", "%", "Kredit spredi: Moody's Baa korporativ − UST 10 il (1986-dan)"),
    "ovx": ("OVXCLS", "indeks", "Neftin nəzərdə tutulan dəyişkənliyi (CBOE OVX, WTI opsionları)"),
}
FRED_MONTHLY = {
    "gas_eu": ("PNGASEUUSDM", "USD/MMBtu", "Təbii qaz, Avropa (TTF proksisi, aylıq)"),
    "eq_oecd_us": ("SPASTT01USM661N", "indeks", "ABŞ səhm qiymətləri indeksi (OECD, aylıq orta)"),
}


def _parse_fred(raw: bytes) -> pd.Series:
    d = pd.read_csv(io.BytesIO(raw))
    d.columns = ["date", "value"]
    d["value"] = pd.to_numeric(d["value"], errors="coerce")
    d = d.dropna()
    return pd.Series(d["value"].to_numpy(float), index=pd.to_datetime(d["date"])).sort_index()


def fred(code: str) -> pd.Series:
    spec = FRED_DAILY.get(code) or FRED_MONTHLY[code]
    url = FRED_URL.format(spec[0])
    raw, st, p = fetch_raw(f"fred_{code}", "fred", f"{spec[0]}.csv", url,
                           validate=lambda b: b[:40].lower().startswith(b"observation_date")
                           or b[:4].lower() == b"date")
    s = _parse_fred(raw)
    record(f"fred_{code}", "fred", url, st, p, len(s), s.index.max().date().isoformat())
    return s


# ---------------------------------------------------------------- World Bank Pink Sheet (monthly)
WB_PAGE = "https://www.worldbank.org/en/research/commodity-markets"
WB_FALLBACK = ("https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/"
               "related/CMO-Historical-Data-Monthly.xlsx")
WB_COLS = {"Crude oil, Brent": "brent", "Natural gas, Europe": "gas_eu", "Natural gas, US": "gas_hh",
           "Gold": "gold"}


def pink_sheet() -> pd.DataFrame:
    """Monthly average prices (USD), columns brent, gas_eu, gas_hh, gold; index = month start."""
    url = WB_FALLBACK
    if not no_network():
        try:
            page = http_get(WB_PAGE).decode("utf-8", "ignore")
            hit = re.findall(r"https?://[^\"']+CMO-Historical-Data-Monthly\.xlsx", page)
            url = hit[0] if hit else WB_FALLBACK
        except Exception:                                      # noqa: BLE001
            pass
    raw, st, p = fetch_raw("wb_pinksheet", "worldbank", "CMO-Historical-Data-Monthly.xlsx", url,
                           validate=lambda b: b[:2] == b"PK")
    d = pd.read_excel(io.BytesIO(raw), sheet_name="Monthly Prices", header=None)
    hdr = d.iloc[4].tolist()
    keep = {i: WB_COLS[h] for i, h in enumerate(hdr) if isinstance(h, str) and h in WB_COLS}
    body = d.iloc[6:, [0, *keep]].copy()
    body.columns = ["m", *keep.values()]
    body = body[body["m"].astype(str).str.match(r"^\d{4}M\d{2}$")]
    idx = pd.to_datetime(body["m"].str.replace("M", "-") + "-01")
    out = body.drop(columns="m").apply(pd.to_numeric, errors="coerce")
    out.index = idx
    out = out.dropna(how="all")
    record("wb_pinksheet", "worldbank", url, st, p, len(out), out.index.max().date().isoformat())
    return out


# ---------------------------------------------------------------- ECB (TRY long daily history)
ECB_URL = "https://data-api.ecb.europa.eu/service/data/EXR/D.{}.EUR.SP00.A?format=csvdata&startPeriod=2005-01-01"


def ecb_rate(ccy: str) -> pd.Series:
    """Units of `ccy` per EUR (ECB reference rate, daily)."""
    url = ECB_URL.format(ccy)
    raw, st, p = fetch_raw(f"ecb_{ccy.lower()}", "ecb", f"EXR_D_{ccy}_EUR.csv", url,
                           validate=lambda b: b[:3] == b"KEY")
    d = pd.read_csv(io.BytesIO(raw), usecols=["TIME_PERIOD", "OBS_VALUE"])
    s = pd.Series(pd.to_numeric(d["OBS_VALUE"], errors="coerce").to_numpy(),
                  index=pd.to_datetime(d["TIME_PERIOD"])).dropna().sort_index()
    record(f"ecb_{ccy.lower()}", "ecb", url, st, p, len(s), s.index.max().date().isoformat())
    return s


# ---------------------------------------------------------------- CBAR daily official rates (XML)
CBAR_XML = "https://www.cbar.az/currencies/{}.xml"
CBAR_CODES = ("USD", "EUR", "GBP", "RUB", "TRY", "CNY", "JPY", "XAU")
CBAR_DIR = config.VINTAGES / "cbar_fx"
_VAL_RE = re.compile(r'<Valute Code="([A-Z]{3})">\s*<Nominal>([^<]*)</Nominal>.*?<Value>([^<]*)</Value>', re.S)


def parse_cbar_xml(raw: bytes) -> pd.DataFrame:
    t = raw.decode("utf-8", "ignore")
    m = re.search(r'ValCurs Date="(\d{2})\.(\d{2})\.(\d{4})"', t)
    if not m:
        raise ValueError("CBAR XML: tarix tapılmadı")
    day = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    rows = []
    for code, nom, val in _VAL_RE.findall(t):
        if code in CBAR_CODES:
            n = re.findall(r"[\d.]+", nom)
            rows.append({"date": day, "code": code, "azn_per_unit":
                         float(val.replace(",", ".")) / (float(n[0]) if n else 1.0)})
    return pd.DataFrame(rows)


def _cbar_table_path() -> Path:
    return CBAR_DIR / "cbar_fx_daily.csv"


def cbar_daily(backfill_days: int = 0, max_requests: int = 40) -> pd.DataFrame:
    """Cumulative table (date, code, azn_per_unit) of CBAR official rates. Each run requests the
    business days missing between the last cached date and today (at most `max_requests`, oldest
    first when back-filling `backfill_days` of history). Raw XMLs are zipped per month."""
    CBAR_DIR.mkdir(parents=True, exist_ok=True)
    tp = _cbar_table_path()
    tab = pd.read_csv(tp) if tp.exists() else pd.DataFrame(columns=["date", "code", "azn_per_unit"])
    have = set(tab["date"].astype(str))
    today = config.as_of()
    start = today - timedelta(days=max(backfill_days, 7))
    want = [d for d in pd.bdate_range(start, today).date if d.isoformat() not in have]
    want = want[-max_requests:] if backfill_days == 0 else want[:max_requests]
    n_ok, last_err = 0, ""
    for d in want:
        url = CBAR_XML.format(d.strftime("%d.%m.%Y"))
        try:
            raw = http_get(url)
            df = parse_cbar_xml(raw)
            with zipfile.ZipFile(CBAR_DIR / f"raw_{d:%Y-%m}.zip", "a", zipfile.ZIP_DEFLATED) as z:
                if f"{d:%d.%m.%Y}.xml" not in z.namelist():
                    z.writestr(f"{d:%d.%m.%Y}.xml", raw)
            if len(df) and df["date"].iloc[0] == d.isoformat():
                tab = df if tab.empty else pd.concat([tab, df], ignore_index=True)
            n_ok += 1
        except FeedUnavailable:
            break
        except Exception as exc:                               # noqa: BLE001
            last_err = type(exc).__name__
    tab = tab.drop_duplicates(["date", "code"], keep="last").sort_values(["date", "code"])
    if n_ok:
        tab.to_csv(tp, index=False, lineterminator="\n")
        snap = vintage_dir("cbar_fx") / "cbar_fx_daily.csv"
        tab.to_csv(snap, index=False, lineterminator="\n")
    status = "canlı" if n_ok else ("keş: RISK_NO_NETWORK" if no_network() else f"keş: {last_err or 'yeni gün yoxdur'}")
    record("cbar_fx_daily", "cbar_fx", CBAR_XML.format("DD.MM.YYYY"), status, tp, len(tab),
           str(tab["date"].max()) if len(tab) else "", note=f"{n_ok} yeni gün")
    if tab.empty:
        raise FeedUnavailable("CBAR məzənnə keşi boşdur")
    return tab


# ---------------------------------------------------------------- CBAR statistical bulletin
CBAR_BULLETIN_PAGE = "https://www.cbar.az/page-40/statistical-bulletin"


def cbar_bulletin() -> tuple[bytes, str, Path, str]:
    """Latest monthly statistical bulletin workbook (68 tables). Returns (bytes, status, path, url)."""
    url = ""
    if not no_network():
        try:
            page = http_get(CBAR_BULLETIN_PAGE).decode("utf-8", "ignore")
            links = re.findall(r'href="(https://uploads\.cbar\.az/assets/[0-9a-f]+\.xlsx)"', page)
            url = links[-1] if links else ""
        except Exception:                                      # noqa: BLE001
            url = ""
    raw, st, p = fetch_raw("cbar_bulletin", "cbar_bulletin", "statistical_bulletin.xlsx",
                           url or CBAR_BULLETIN_PAGE, validate=lambda b: b[:2] == b"PK")
    record("cbar_bulletin", "cbar_bulletin", url or CBAR_BULLETIN_PAGE, st, p)
    return raw, st, p, url or CBAR_BULLETIN_PAGE


FRED_MONTHLY.update({
    "usdrub_m": ("CCUSMA02RUM618N", "RUB/USD", "Rusiya rublu (RUB/USD, aylıq orta, OECD)"),
    "usdtry_m": ("CCUSMA02TRM618N", "TRY/USD", "Türk lirəsi (TRY/USD, aylıq orta, OECD)"),
})

FACTOR_META = {k: (v[1], v[2], "FRED " + v[0]) for k, v in FRED_DAILY.items()}
FACTOR_META.update({
    "usdtry": ("TRY/USD", "Türk lirəsi (TRY/USD)", "ECB EXR (TRY/EUR) ÷ FRED DEXUSEU"),
    "usdrub": ("RUB/USD", "Rusiya rublu (RUB/USD)", "AMB rəsmi məzənnə XML"),
    "usdazn": ("AZN/USD", "Manat məzənnəsi (AZN/USD)", "AMB rəsmi məzənnə XML"),
    "gold": ("USD/unsiya", "Qızıl", "gündəlik: AMB XML (XAU÷USD); aylıq: Dünya Bankı Pink Sheet"),
    "gas_eu": ("USD/MMBtu", "Təbii qaz, Avropa (TTF proksisi)", "FRED PNGASEUUSDM (aylıq)"),
    "eq_oecd_us": ("indeks", "ABŞ səhm indeksi (OECD, aylıq)", "FRED SPASTT01USM661N"),
})


def _try(fn, *a, **k):
    try:
        return fn(*a, **k)
    except FeedUnavailable:
        return None


def daily_panel(backfill_days: int = 0, max_requests: int = 40) -> pd.DataFrame:
    """Business-day panel of market levels (wide). Missing sources simply drop out."""
    cols = {}
    for code in FRED_DAILY:
        s = _try(fred, code)
        if s is not None:
            cols[code] = s
    t = _try(ecb_rate, "TRY")
    if t is not None and "eurusd" in cols:
        cols["usdtry"] = (t / cols["eurusd"].reindex(t.index).ffill(limit=3)).dropna()
    cb = _try(cbar_daily, backfill_days, max_requests)
    if cb is not None and len(cb):
        w = cb.pivot_table(index="date", columns="code", values="azn_per_unit", aggfunc="last")
        w.index = pd.to_datetime(w.index)
        if "USD" in w:
            cols["usdazn"] = w["USD"].dropna()
            if "XAU" in w:
                cols["gold"] = (w["XAU"] / w["USD"]).dropna()
            if "RUB" in w:
                cols["usdrub"] = (w["USD"] / w["RUB"]).dropna()
    df = pd.DataFrame(cols).sort_index()
    df = df[df.index.dayofweek < 5]
    return df


def monthly_panel(daily: pd.DataFrame | None = None) -> pd.DataFrame:
    """Monthly-average panel (month start). Gold is taken from the Pink Sheet only (one consistent
    monthly-average source); Brent, European gas, OECD equities, RUB and TRY extend the history."""
    d = daily if daily is not None else daily_panel()
    m = d.resample("MS").mean()
    ps = _try(pink_sheet)
    if ps is not None:
        m = m.reindex(m.index.union(ps.index))
        m["gold"] = ps["gold"]
        m["brent"] = m["brent"].combine_first(ps["brent"]) if "brent" in m else ps["brent"]
        m["gas_eu"] = ps["gas_eu"]
    for code, col in (("gas_eu", "gas_eu"), ("eq_oecd_us", "eq_oecd_us"), ("usdrub_m", "usdrub"),
                      ("usdtry_m", "usdtry")):
        s = _try(fred, code)
        if s is None:
            continue
        s.index = s.index.to_period("M").to_timestamp()
        m = m.reindex(m.index.union(s.index))
        m[col] = s.reindex(m.index).combine_first(m[col]) if col in m else s.reindex(m.index)
    return m.sort_index()


def register_catalog(file: str, owner: str, description_az: str, columns, frequency: str) -> None:
    """One row per output file in output/_catalog_v2.csv (uses the spine helper when present)."""
    from . import spine
    if hasattr(spine, "register_output"):
        spine.register_output(file, owner, description_az, columns, frequency)
        return
    p = config.OUTPUT / "_catalog_v2.csv"
    cols = ";".join(columns) if isinstance(columns, (list, tuple, pd.Index)) else str(columns)
    row = {"file": file, "owner_module": owner, "description_az": description_az, "columns": cols,
           "update_frequency": frequency, "updated_utc": _utc()}
    cur = pd.read_csv(p, dtype=str) if p.exists() else pd.DataFrame(columns=list(row))
    cur = pd.concat([cur[cur["file"] != file], pd.DataFrame([row])], ignore_index=True)
    cur.sort_values("file").to_csv(p, index=False)


def build(ctx: dict | None = None) -> dict:
    """Fetch every market factor and write output/V2_market_factors.csv (wide; 'tezlik' column)."""
    ctx = ctx or {}
    d = daily_panel(ctx.get("cbar_backfill_days", 0), ctx.get("cbar_max_requests", 40))
    m = monthly_panel(d)
    dd = d[d.index >= "2007-01-01"].copy()
    dd.insert(0, "tezlik", "gündəlik")
    mm = m[m.index >= "1990-01-01"].copy()
    mm.insert(0, "tezlik", "aylıq orta")
    out = pd.concat([dd, mm]).rename_axis("tarix").reset_index()
    out["tarix"] = out["tarix"].dt.strftime("%Y-%m-%d")
    path = config.OUTPUT / "V2_market_factors.csv"
    out.round(6).to_csv(path, index=False, lineterminator="\n")
    bad = [f"{r['feed']} ({r['status']})" for r in _STATUS_ROWS if r.get("seviyye") != "ok"]
    flush_status()
    level = ("xəbərdarlıq: " + "; ".join(bad))[:300] if bad else "ok"   # market factors: never core (V2 keeps the cache)
    return {"daily": d, "monthly": m, "path": path, "stage_status": level}


def load_panels() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read the factor panels back from V2_market_factors.csv (no network)."""
    p = config.OUTPUT / "V2_market_factors.csv"
    if not p.exists():
        raise FeedUnavailable("V2_market_factors.csv yoxdur — `python3 -m riskunit.feeds_market`")
    x = pd.read_csv(p, parse_dates=["tarix"])
    d = x[x.tezlik == "gündəlik"].drop(columns="tezlik").set_index("tarix").dropna(how="all", axis=1)
    m = x[x.tezlik == "aylıq orta"].drop(columns="tezlik").set_index("tarix").dropna(how="all", axis=1)
    return d, m


def run(ctx: dict | None = None) -> dict:
    r = build(ctx)
    register_catalog("V2_market_factors.csv", "feeds_market",
                        "Bazar risk amilləri: Brent, qaz, valyuta məzənnələri, ABŞ gəlirlilik əyrisi, səhm, "
                        "qızıl, EM spredi (gündəlik və aylıq orta səviyyələr)",
                     list(pd.read_csv(r["path"], nrows=0).columns), "gündəlik")
    return {"V2_market_factors": str(r["path"]), "n_daily": len(r["daily"]), "n_monthly": len(r["monthly"]),
            "stage_status": r.get("stage_status", "ok")}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="VaR/CaR bazar amilləri (V2)")
    ap.add_argument("--backfill", type=int, default=0, help="AMB XML: geriyə doldurulacaq gün sayı")
    ap.add_argument("--max-requests", type=int, default=40)
    a = ap.parse_args()
    print(run({"cbar_backfill_days": a.backfill, "cbar_max_requests": a.max_requests}))
