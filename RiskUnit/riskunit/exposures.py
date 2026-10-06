"""Sovereign / economy balance-sheet exposure database (RiskUnit v2, VaR/CaR layer).

Builds output/V1_exposures.csv — every stock and flow the VaR and Capital-at-Risk models use, in
mln USD and mln AZN, each with its source, publication date, retrieval status and URL — and
output/V1b_data_requests.csv, the list of numbers that are not public (Azerbaijani).

Sources (all fetched automatically, cached under data/vintages/<source>/<date>/):
  SOFAZ   oilfund.az "Recent figures" page (total assets) and the latest quarterly investment
          highlights PDF (currency, asset-class, maturity and rating breakdown);
  CBAR    statistical bulletin workbook (official reserves t.2.2, banking sector t.5.2, NPL t.5.6);
  MinFin  semi-annual public-debt statistical bulletin PDF (public, external, domestic and
          state-guaranteed debt, currency and interest-rate composition, Eurobonds);
  MicroUnit FR1 (budget oil revenue dependence, exports by commodity), Ministry Bottom-up
          'base 60' (SOFAZ revenue / transfer plan) — read-only upstreams.
PDF text is extracted with the poppler `pdftotext` binary when present; if a layout cannot be
parsed the last good parsed vintage is used, and as a last resort the documented seed values
below (publication of 30.06.2026 / 01.07.2026), flagged status='fiksatura'.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from . import config, feeds_market as fm

SOFAZ_RECENT = "https://www.oilfund.az/en/report-and-statistics/recent-figures"
SOFAZ_QUARTERLY = "https://www.oilfund.az/en/investments/quarterly-investment-results"
MINFIN_BULLETIN_PAGE = "https://www.maliyye.gov.az/static/306/dovlet-borcu-uzre-statistik-bulleten"
MINFIN_BASE = "https://www.maliyye.gov.az"
PEG = 1.70                                    # AZN per USD (de facto peg since 2017)

# Seed = values published by SOFAZ (H1-2026 highlights, 30.06.2026) and MinFin (statistical
# bulletin H1-2026, 01.07.2026). Used ONLY when neither the network nor a cached parse exists.
SEED_SOFAZ = {"date": "2026-06-30", "total_usd": 72596.6, "portfolio_usd": 72595.1,
              "ccy_pct": {"USD": 69.7, "EUR": 17.7, "GBP": 4.9, "CNY": 2.3, "JPY": 1.5, "OTHER": 3.9},
              "class_pct": {"fixed_income": 33.8, "equities": 28.1, "gold": 31.4, "real_estate": 6.7},
              "gold_tons": 178.1,
              "maturity_pct": {"0-1": 14.7, "1-3": 30.1, "3-5": 26.4, "5+": 28.8},
              "rating_pct": {"AAA": 28.0, "AA": 34.4, "A": 25.3, "BBB": 11.5, "NIG": 0.8},
              "start_year_usd": 73541.0, "url": "https://www.oilfund.az/storage/uploads/oqc1rqu5ms.pdf"}
SEED_DEBT = {"date": "2026-07-01", "total_azn": 23830.6, "ext_azn": 7848.6, "ext_usd": 4616.8,
             "dom_azn": 15982.0, "dom_securities_azn": 7234.6, "dom_assumed_guar_azn": 8747.4,
             "gdp_proj_azn": 130873.5, "floating_total_pct": 16.3, "floating_ext_pct": 49.4,
             "debt_service_exp_pct": 5.6, "ext_avg_maturity_y": 4.8, "strategic_reserves_usd_bn": 85.8,
             "ext_ccy_pct": {"USD": 86.4, "EUR": 6.1, "XDR": 2.9, "JPY": 3.1, "OTHER": 1.5},
             "ext_due_5y_pct": 59.5, "guar_total_azn": 7232.3, "guar_ext_azn": 4928.0,
             "guar_ext_usd": 2898.8, "guar_dom_azn": 2304.3,
             "guar_ccy_pct": {"USD": 52.8, "EUR": 22.0, "AZN": 17.9, "JPY": 5.0, "OTHER": 2.3},
             "guar_due_5y_pct": 65.5, "eurobond_2029_usd": 310.7, "eurobond_2032_usd": 1076.6,
             "url": "https://www.maliyye.gov.az/uploads/static-pages/files/6a9810b8688c1.pdf"}


def _num_en(s: str) -> float:
    """'72 597' / '72 595.1' -> float (SOFAZ English layout)."""
    return float(re.sub(r"[\s ,]", "", s))


def _num_az(s: str) -> float:
    """'23.830,6' / '4,8' -> float (Azerbaijani layout: dot thousands, comma decimals)."""
    return float(s.replace(".", "").replace(",", "."))


def pdf_text(raw: bytes) -> str:
    exe = shutil.which("pdftotext") or ("/opt/homebrew/bin/pdftotext"
                                         if Path("/opt/homebrew/bin/pdftotext").exists() else None)
    if exe is None:
        raise RuntimeError("pdftotext tapılmadı")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "in.pdf"
        p.write_bytes(raw)
        out = subprocess.run([exe, "-layout", str(p), "-"], capture_output=True, timeout=60, check=True)
    return out.stdout.decode("utf-8", "ignore")


def _cache_json(source: str, name: str, obj: dict) -> None:
    (fm.vintage_dir(source) / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def _last_json(source: str, name: str) -> dict | None:
    p = fm.latest_cached(source, name)
    return json.loads(p.read_text(encoding="utf-8")) if p else None


def _pairs(seg: str, labels: list[tuple[str, str]]) -> dict:
    """Percentages and their labels appear in the same order in a pdftotext block."""
    nums = [float(x) for x in re.findall(r"(\d{1,2}\.\d)\s*%", seg)]
    found = sorted((m.start(), key) for pat, key in labels for m in [re.search(pat, seg)] if m)
    if len(nums) < len(found) or not found:
        raise ValueError("faiz/etiket sayı uyğun deyil")
    return {key: nums[i] for i, (_, key) in enumerate(found)}


# ---------------------------------------------------------------- SOFAZ
def _find(s: str, phrase: str) -> int:
    """Position of a phrase whose words may be split across lines (-1 if absent)."""
    m = re.search(r"\s+".join(map(re.escape, phrase.split())), s)
    return m.start() if m else -1


def _parse_sofaz_pdf(t: str) -> dict:
    s = re.sub(r"[ \t ]+", " ", t)
    out: dict = {}
    m = re.search(r"assets by (\w+) (\d{4}):\s*([\d ]+(?:\.\d)?) mln", s)
    out["total_usd"] = _num_en(m.group(3)) if m else None
    m = re.search(r"Total investment portfolio:\s*\$([\d ]+\.\d) mln", s)
    out["portfolio_usd"] = _num_en(m.group(1)) if m else out["total_usd"]
    m = re.search(r"beginning of (\d{4}):\s*([\d ]+(?:\.\d)?) mln", s)
    out["start_year_usd"] = _num_en(m.group(2)) if m else None
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", s)
    out["date"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None
    m = re.search(r"gold investments\s+worth\s+USD\s+([\d ]+\.\d)\s+million\s+\((\d{1,2}\.\d)%\)", s)
    gold_pct = float(m.group(2)) if m else None
    m = re.search(r"\((\d{2,4}\.\d) TONS\)", s)
    out["gold_tons"] = float(m.group(1)) if m else None
    # currency amounts -> shares (gold is inside USD, as SOFAZ reports it)
    amt = {}
    for key, pat in (("USD", r"US Dollar\*?:\s*\$([\d ]+\.\d)"), ("OTHER", r"Other Currencies:\s*\$([\d ]+\.\d)")):
        m = re.search(pat, s)
        if m:
            amt[key] = _num_en(m.group(1))
    i = _find(s, "breakdown by foreign"); j = _find(s, "breakdown by asset class")
    seg = s[i:j] if i >= 0 and j > i else ""
    nums = [float(x) for x in re.findall(r"(\d{1,2}\.\d)%", seg)]
    tot = out["portfolio_usd"]
    ccy = {"USD": round(amt.get("USD", np.nan) / tot * 100, 1) if tot else None,
           "OTHER": round(amt.get("OTHER", np.nan) / tot * 100, 1) if tot else None}
    rest = [x for x in nums if all(abs(x - (v or -99)) > 0.05 for v in (ccy["USD"], ccy["OTHER"], gold_pct))]
    # remaining shares: the four largest named non-USD currencies are EUR > GBP > CNY > JPY
    rest = sorted(rest, reverse=True)[:4]
    if len(rest) == 4:
        ccy.update(dict(zip(["EUR", "GBP", "CNY", "JPY"], rest)))
    out["ccy_pct"] = ccy
    k = _find(s, "Classification of fixed")
    out["class_pct"] = _pairs(s[j:k], [(r"Fixed income", "fixed_income"), (r"Equities", "equities"),
                                       (r"Gold\s", "gold"), (r"Real estate", "real_estate")])
    i = _find(s, "placement period"); k2 = _find(s, "geographical regions")
    out["maturity_pct"] = _pairs(s[i:k2], [(r"OVER\s*5", "5+"), (r"0-1\s*YEAR", "0-1"),
                                            (r"3-5\s*YEAR", "3-5"), (r"1-3\s*YEAR", "1-3")])
    i = _find(s, "by credit rating"); k3 = _find(s, "placement period")
    out["rating_pct"] = _pairs(s[i:k3], [(r"NON-INVESTMENT", "NIG"), (r"\bAAA\b", "AAA"),
                                          (r"\bBBB\b", "BBB"), (r"\n\s*A\s*\n", "A"), (r"\n\s*AA\s*\n", "AA")])
    for key in ("class_pct", "maturity_pct", "rating_pct"):
        if abs(sum(out[key].values()) - 100) > 0.6:
            raise ValueError(f"SOFAZ {key}: cəm {sum(out[key].values()):.1f} ≠ 100")
    if abs(sum(v for v in ccy.values() if v) - 100) > 0.6:
        raise ValueError("SOFAZ valyuta bölgüsü: cəm ≠ 100")
    return out


def sofaz() -> dict:
    """Latest SOFAZ balance sheet. Total from the 'Recent figures' page (may be newer than the PDF)."""
    status, url = "fiksatura", SEED_SOFAZ["url"]
    data = None
    try:
        page, st_q, _ = fm.fetch_raw("sofaz_quarterly", "sofaz", "quarterly_results.html", SOFAZ_QUARTERLY)
        links = re.findall(r'href="(https://www\.oilfund\.az/storage/uploads/[a-z0-9]+\.pdf)"[^>]*>\s*([^<]*)',
                           page.decode("utf-8", "ignore"))
        url = links[0][0] if links else url
        raw, st, p = fm.fetch_raw("sofaz_highlights_pdf", "sofaz", "investment_highlights.pdf", url,
                                  validate=lambda b: b[:4] == b"%PDF")
        data = _parse_sofaz_pdf(pdf_text(raw))
        data["url"], status = url, ("canlı" if st == "canlı" else st)
        _cache_json("sofaz", "sofaz_parsed.json", data)
        fm.record("sofaz_highlights_pdf", "sofaz", url, st, p, last_obs=data.get("date"))
    except Exception as exc:                                       # noqa: BLE001
        data = _last_json("sofaz", "sofaz_parsed.json")
        status = f"keş: {type(exc).__name__}" if data else "fiksatura"
        data = data or dict(SEED_SOFAZ)
        fm.record("sofaz_highlights_pdf", "sofaz", url, status, None, note=str(exc)[:120])
    try:                                                           # newer total, if published
        raw, st, p = fm.fetch_raw("sofaz_recent", "sofaz", "recent_figures.html", SOFAZ_RECENT)
        txt = re.sub(r"<[^>]+>", " ", raw.decode("utf-8", "ignore"))
        m = re.search(r"as of (\w+) (\d{1,2})\s*,\s*(\d{4}).{0,80}?assets:\s*USD\s*([\d  ]+\.\d)\s*mln", txt, re.S)
        if m:
            d = pd.Timestamp(f"{m.group(1)} {m.group(2)} {m.group(3)}").date().isoformat()
            data["recent_total_usd"], data["recent_date"] = _num_en(m.group(4)), d
            data["recent_status"] = st
        fm.record("sofaz_recent", "sofaz", SOFAZ_RECENT, st, p, last_obs=data.get("recent_date"))
    except Exception as exc:                                       # noqa: BLE001
        fm.record("sofaz_recent", "sofaz", SOFAZ_RECENT, f"xəta: {type(exc).__name__}", None)
    data["status"] = status
    return data


# ---------------------------------------------------------------- MinFin public debt bulletin
_AZ_MONTHS = {"yanvar": 1, "fevral": 2, "mart": 3, "aprel": 4, "may": 5, "iyun": 6, "iyul": 7,
              "avqust": 8, "sentyabr": 9, "oktyabr": 10, "noyabr": 11, "dekabr": 12}


def _mix(seg: str) -> dict:
    keys = {"ABŞ dolları": "USD", "avro": "EUR", "XBH": "XDR", "yapon yeni": "JPY",
            "manat": "AZN", "digər valyutalar": "OTHER"}
    out = {}
    for lab, k in keys.items():
        m = re.search(re.escape(lab) + r"[^–\-]{0,80}[–-]\s*([\d,]+)\s*faiz", seg)
        if m:
            out[k] = _num_az(m.group(1))
    return out


def _parse_debt_pdf(t: str) -> dict:
    s = re.sub(r"\s+", " ", t)
    g = lambda pat: re.search(pat, s)                              # noqa: E731
    out: dict = {}
    m = g(r"(\d{4})-c[ıiuü] il (\d{2}) (\w+) tarixinə Azərbaycan Respublikasının dövlət borcu")
    out["date"] = f"{m.group(1)}-{_AZ_MONTHS[m.group(3).lower()]:02d}-{m.group(2)}" if m else None
    m = g(r"dövlət borcu \(daxili və xarici dövlət borcu\) ([\d.,]+) milyon manat.{0,40}?([\d.]+,\d) milyon manat məbləğində proqnoz")
    out["total_azn"], out["gdp_proj_azn"] = _num_az(m.group(1)), _num_az(m.group(2))
    m = g(r"borcunun ([\d.,]+) milyon manatı \(([\d.,]+) milyon ABŞ dolları\) və ya [\d,]+ faizi xarici")
    out["ext_azn"], out["ext_usd"] = _num_az(m.group(1)), _num_az(m.group(2))
    m = g(r"([\d.,]+) milyon manatı və ya [\d,]+ faizi daxili dövlət borcunun payına")
    out["dom_azn"] = _num_az(m.group(1))
    m = g(r"daxili dövlət borcunun ([\d.,]+) milyon manatı dövriyyədə olan dövlət qiymətli kağızlarının, ([\d.,]+) milyon manatı")
    if m:
        out["dom_securities_azn"], out["dom_assumed_guar_azn"] = _num_az(m.group(1)), _num_az(m.group(2))
    m = g(r"ümumi borc portfelinin ([\d,]+) faizini")
    out["floating_total_pct"] = _num_az(m.group(1)) if m else None
    m = g(r"dəyişkən faiz dərəcəsi ilə olan öhdəliklər xarici dövlət borcunun ([\d,]+) faizini")
    out["floating_ext_pct"] = _num_az(m.group(1)) if m else None
    m = g(r"dövlət büdcəsi xərclərinə nisbəti ([\d,]+) faiz")
    out["debt_service_exp_pct"] = _num_az(m.group(1)) if m else None
    m = g(r"Orta Ödəmə Müddətinin göstəricisi ([\d,]+) il")
    out["ext_avg_maturity_y"] = _num_az(m.group(1)) if m else None
    m = g(r"strateji valyuta ehtiyatları \([^)]*\) ([\d,]+) milyard ABŞ dolları")
    out["strategic_reserves_usd_bn"] = _num_az(m.group(1)) if m else None
    m = g(r"Xarici dövlət borcunun ([\d,]+) faizi 5 ilə qədər")
    out["ext_due_5y_pct"] = _num_az(m.group(1)) if m else None
    i = s.find("xarici dövlət borcunun valyuta tərkibi")
    out["ext_ccy_pct"] = _mix(s[i:i + 400]) if i >= 0 else {}
    m = g(r"dövlət zəmanətli borcun məbləği \(daxili və xarici dövlət zəmanətli borc\) ([\d.,]+) milyon manat")
    out["guar_total_azn"] = _num_az(m.group(1))
    m = g(r"Dövlət zəmanətinin ([\d.,]+) milyon manatı \(([\d.,]+) milyon ABŞ dolları\)")
    out["guar_ext_azn"], out["guar_ext_usd"] = _num_az(m.group(1)), _num_az(m.group(2))
    m = g(r"([\d.,]+) milyon manatı və ya [\d,]+ faizi isə daxili dövlət zəmanətli")
    out["guar_dom_azn"] = _num_az(m.group(1)) if m else None
    i = s.find("zəmanətli borc portfelinin valyuta tərkibi")
    out["guar_ccy_pct"] = _mix(s[i:i + 400]) if i >= 0 else {}
    m = g(r"Dövlət zəmanətli borcun ([\d,]+) faizi 5 ilə qədər")
    out["guar_due_5y_pct"] = _num_az(m.group(1)) if m else None
    m = g(r"2029-cu ildə başa ([\d.,]+) [\d,]+% çatan")
    out["eurobond_2029_usd"] = _num_az(m.group(1)) if m else None
    m = g(r"2032-ci ildə başa ([\d.,]+) [\d,]+% çatan")
    out["eurobond_2032_usd"] = _num_az(m.group(1)) if m else None
    if abs(out["ext_azn"] + out["dom_azn"] - out["total_azn"]) > 1.0:
        raise ValueError("dövlət borcu: xarici + daxili ≠ cəm")
    return out


def public_debt() -> dict:
    url, status = SEED_DEBT["url"], "fiksatura"
    try:
        page, _, _ = fm.fetch_raw("minfin_debt_page", "minfin", "debt_bulletin_page.html", MINFIN_BULLETIN_PAGE)
        t = page.decode("utf-8", "ignore")
        i = t.find('class="pdfs-page')
        links = re.findall(r'href="(/uploads/static-pages/files/[0-9a-f]+\.pdf)"', t[i:] if i >= 0 else t)
        url = MINFIN_BASE + links[0] if links else url
        raw, st, p = fm.fetch_raw("minfin_debt_bulletin", "minfin", "debt_bulletin.pdf", url,
                                  validate=lambda b: b[:4] == b"%PDF")
        data = _parse_debt_pdf(pdf_text(raw))
        data["url"], status = url, st
        _cache_json("minfin", "debt_parsed.json", data)
        fm.record("minfin_debt_bulletin", "minfin", url, st, p, last_obs=data.get("date"))
    except Exception as exc:                                       # noqa: BLE001
        data = _last_json("minfin", "debt_parsed.json")
        status = f"keş: {type(exc).__name__}" if data else "fiksatura"
        data = data or dict(SEED_DEBT)
        fm.record("minfin_debt_bulletin", "minfin", url, status, None, note=str(exc)[:120])
    data["status"] = status
    return data


# ---------------------------------------------------------------- CBAR bulletin: reserves, banks
def _last_row_value(df: pd.DataFrame, col: int) -> tuple[float, str]:
    """Tables 1.x/2.x: column 0 holds years (YYYY) followed by month rows ('01'..'12')."""
    year, last = None, None
    for lab, v in zip(df.iloc[:, 0].astype(str), df.iloc[:, col]):
        lab = lab.strip()
        if re.fullmatch(r"\d{4}(\.0)?", lab):
            year = int(float(lab))
            mon = 12
        elif re.fullmatch(r"\d{1,2}", lab) and year:
            mon = int(lab)
        else:
            continue
        x = pd.to_numeric(v, errors="coerce")
        if pd.notna(x):
            last = (float(x), f"{year}-{mon:02d}")
    if last is None:
        raise ValueError("cədvəldə rəqəm tapılmadı")
    v, ym = last
    return v, (pd.Period(ym, "M").end_time.date().isoformat())


def cbar() -> dict:
    out = {"status": "xəta"}
    try:
        raw, st, p, url = fm.cbar_bulletin()
        x = pd.ExcelFile(__import__("io").BytesIO(raw))
        t22 = pd.read_excel(x, "2.2", header=None)
        out["reserves_usd"], out["reserves_date"] = _last_row_value(t22.iloc[7:], 1)
        t52 = pd.read_excel(x, "5.2", header=None)
        dates = [(j, v) for j, v in enumerate(t52.iloc[5]) if isinstance(v, (pd.Timestamp,)) or hasattr(v, "year")]
        j, d = dates[-1]
        lab = t52.iloc[:, 0].astype(str).str.strip()
        pick = lambda pat, col=j: float(t52.loc[lab.str.match(pat), col].iloc[0])      # noqa: E731
        out.update({"bank_date": pd.Timestamp(d).date().isoformat(),
                    "bank_assets_azn": pick(r"^11\. Cəmi aktivlər"), "bank_loans_azn": pick(r"^7\. Müştərilərə"),
                    "bank_deposits_azn": pick(r"^1\. Depozitlər"), "bank_capital_azn": pick(r"^12\. Cəmi kapital"),
                    "bank_deposits_fx_azn": pick(r"^1\. Depozitlər", j + 1)})
        t56 = pd.read_excel(x, "5.6", header=None)
        dcol = [jj for jj, v in enumerate(t56.iloc[5]) if hasattr(v, "year")][-1]
        lab6 = t56.iloc[:, 0].astype(str).str.strip()
        out["npl_azn"] = float(t56.loc[lab6.str.startswith("Qeyri-işlək kredit"), dcol].iloc[0])
        out["npl_ratio"] = float(t56.loc[lab6.str.startswith("QİK/Kredit"), dcol].iloc[0])
        out["npl_date"] = pd.Timestamp(t56.iloc[5, dcol]).date().isoformat()
        out.update({"status": st, "url": url})
    except Exception as exc:                                       # noqa: BLE001
        out["error"] = f"{type(exc).__name__}: {exc}"[:160]
    return out


# ---------------------------------------------------------------- upstream (read-only) inputs
BBL_PER_TONNE = 7.33                         # Azeri Light conversion (assumption, documented)


def ministry_sofaz_plan() -> pd.DataFrame:
    """Ministry Bottom-up 'base 60' rows 93-96, 140-141 (SOFAZ revenue, spending, transfer,
    assets; FX; Brent), 2017-2030. Ministry input — CAEM/Bottom-up caveats apply."""
    import openpyxl
    f = config.MINISTRY_DIR / "Ministry_Bottom_up_Model" / "MOE REPORT 3 PAGES.xlsx"
    wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
    ws = wb["base 60"]
    rows = {3: "year", 93: "sofaz_rev_azn", 94: "sofaz_exp_azn", 95: "transfer_azn",
            96: "sofaz_assets_usd", 140: "usd_azn", 141: "brent"}
    got = {}
    for i, r in enumerate(ws.iter_rows(min_row=1, max_row=141, max_col=16, values_only=True), start=1):
        if i in rows:
            got[rows[i]] = list(r[2:16])
    wb.close()
    d = pd.DataFrame(got).astype(float)
    d["year"] = d["year"].astype(int)
    return d.set_index("year")


def fr1_inputs() -> dict:
    from . import spine
    B = spine.baseline()
    H = spine.micro_fr1_dataset()
    y = config.LAST_ACTUAL
    return {"B": B, "H": H, "y": y}


# ---------------------------------------------------------------- assembly
COLS = ["kod", "kateqoriya", "ad_az", "deyer", "vahid", "mln_usd", "mln_azn", "pay_faiz",
        "tarix", "menbe", "status", "url", "qeyd"]


def _row(kod, kat, ad, deyer, vahid, tarix, menbe, status, url="", qeyd="", pay=None):
    v = None if deyer is None or (isinstance(deyer, float) and np.isnan(deyer)) else float(deyer)
    usd = azn = None
    if v is None and pay is not None:
        v = float(pay)
    if v is not None and vahid == "mln USD":
        usd, azn = v, v * PEG
    elif v is not None and vahid == "mln AZN":
        usd, azn = v / PEG, v
    return {"kod": kod, "kateqoriya": kat, "ad_az": ad, "deyer": v, "vahid": vahid, "mln_usd": usd,
            "mln_azn": azn, "pay_faiz": pay, "tarix": tarix, "menbe": menbe, "status": status,
            "url": url, "qeyd": qeyd}


def fi_key_rate_durations(mat: dict) -> dict:
    """Bucket weights -> key-rate durations on the UST 2y/5y/10y nodes (assumed bucket durations
    0.5 / 2.0 / 4.0 / 7.5 years; SOFAZ does not publish duration)."""
    w = {k: v / 100 for k, v in mat.items()}
    return {"ust2": w.get("0-1", 0) * 0.5 + w.get("1-3", 0) * 2.0, "ust5": w.get("3-5", 0) * 4.0,
            "ust10": w.get("5+", 0) * 7.5}


def collect() -> dict:
    """All exposure inputs as a dict (used by var.py / car.py / dsa.py without re-reading CSVs)."""
    s, d, c = sofaz(), public_debt(), cbar()
    try:
        plan = ministry_sofaz_plan()
    except Exception:                                              # noqa: BLE001
        plan = None
    fr = fr1_inputs()
    fm.flush_status()
    return {"sofaz": s, "debt": d, "cbar": c, "plan": plan, "fr1": fr}


def table(x: dict) -> pd.DataFrame:
    s, d, c, plan, fr = x["sofaz"], x["debt"], x["cbar"], x["plan"], x["fr1"]
    R = []
    S_URL, D_URL = s.get("url", ""), d.get("url", "")
    tot = s.get("recent_total_usd") or s["total_usd"]
    tdate = s.get("recent_date") or s["date"]
    R.append(_row("sofaz_total", "ARDNF", "ARDNF-nin aktivləri (cəmi)", tot, "mln USD", tdate, "ARDNF (oilfund.az)",
                  s.get("recent_status", s["status"]), SOFAZ_RECENT, "manat hesabları daxil"))
    P = s.get("portfolio_usd") or s["total_usd"]
    for k, ad in (("fixed_income", "Sabit gəlirli alətlər və pul bazarı"), ("equities", "Səhmlər"),
                  ("gold", "Qızıl"), ("real_estate", "Daşınmaz əmlak və infrastruktur")):
        pct = s["class_pct"][k]
        R.append(_row(f"sofaz_class_{k}", "ARDNF aktiv sinfi", ad, P * pct / 100, "mln USD", s["date"],
                      "ARDNF investisiya nəticələri", s["status"], S_URL, pay=pct))
    gold_pct = s["class_pct"]["gold"]
    for k, pct in s["ccy_pct"].items():
        if pct is None:
            continue
        val = pct - gold_pct if k == "USD" else pct
        ad = {"USD": "ABŞ dolları (qızıl xaric)", "EUR": "Avro", "GBP": "Funt sterlinq", "CNY": "Çin yuanı",
              "JPY": "Yapon yeni", "OTHER": "Digər valyutalar"}[k]
        R.append(_row(f"sofaz_ccy_{k}", "ARDNF valyuta", ad, P * val / 100, "mln USD", s["date"],
                      "ARDNF investisiya nəticələri", s["status"], S_URL,
                      "ARDNF qızılı USD payına daxil edir; burada ayrıca göstərilir" if k == "USD" else "", pay=val))
    for k, pct in s["maturity_pct"].items():
        R.append(_row(f"sofaz_fi_mat_{k}", "ARDNF istiqraz müddəti", f"Sabit gəlirli: {k} il", None, "%", s["date"],
                      "ARDNF investisiya nəticələri", s["status"], S_URL, pay=pct))
    krd = fi_key_rate_durations(s["maturity_pct"])
    R.append(_row("sofaz_fi_duration", "ARDNF istiqraz müddəti", "Modifikasiya olunmuş müddət (təxmini)",
                  sum(krd.values()), "il", s["date"], "törəmə: müddət qrupları × fərz olunan qrup müddəti",
                  "törəmə", S_URL, "qrup müddətləri 0,5/2/4/7,5 il — FƏRZİYYƏ; ARDNF müddəti açıqlamır"))
    for k, pct in s["rating_pct"].items():
        R.append(_row(f"sofaz_fi_rating_{k}", "ARDNF kredit reytinqi", f"Reytinq {k}", None, "%", s["date"],
                      "ARDNF investisiya nəticələri", s["status"], S_URL, pay=pct))
    if s.get("gold_tons"):
        R.append(_row("sofaz_gold_tons", "ARDNF aktiv sinfi", "Qızıl ehtiyatı", s["gold_tons"], "ton", s["date"],
                      "ARDNF investisiya nəticələri", s["status"], S_URL))
    if c.get("reserves_usd") is not None:
        R.append(_row("cbar_reserves", "AMB", "AMB-nin rəsmi beynəlxalq ehtiyatları", c["reserves_usd"], "mln USD",
                      c["reserves_date"], "AMB statistik bülleteni, c.2.2", c["status"], c.get("url", "")))
        R.append(_row("strategic_reserves", "Strateji ehtiyatlar", "Strateji valyuta ehtiyatları (ARDNF + AMB)",
                      tot + c["reserves_usd"], "mln USD", max(tdate, c["reserves_date"]), "törəmə", "törəmə", "",
                      f"MN bülleteni ({d['date']}): {d.get('strategic_reserves_usd_bn')} mlrd USD — yoxlama"))
    R.append(_row("debt_public_total", "Dövlət borcu", "Dövlət borcu (xarici + daxili)", d["total_azn"], "mln AZN",
                  d["date"], "Maliyyə Nazirliyi, Dövlət borcu üzrə statistik bülleten", d["status"], D_URL,
                  f"ÜDM-in {d['total_azn'] / d['gdp_proj_azn'] * 100:.1f}%-i (MN-in 2026 ÜDM proqnozu)"))
    R.append(_row("debt_external", "Dövlət borcu", "Xarici dövlət borcu", d["ext_usd"], "mln USD", d["date"],
                  "Maliyyə Nazirliyi", d["status"], D_URL, f"{d['ext_azn']:.1f} mln AZN"))
    R.append(_row("debt_domestic", "Dövlət borcu", "Daxili dövlət borcu", d["dom_azn"], "mln AZN", d["date"],
                  "Maliyyə Nazirliyi", d["status"], D_URL,
                  f"DQK {d.get('dom_securities_azn')} + hökumətin üzərinə götürdüyü zəmanətli {d.get('dom_assumed_guar_azn')}"))
    for k, pct in (d.get("ext_ccy_pct") or {}).items():
        R.append(_row(f"debt_ext_ccy_{k}", "Xarici borc valyuta", f"Xarici dövlət borcu: {k}", d["ext_usd"] * pct / 100,
                      "mln USD", d["date"], "Maliyyə Nazirliyi", d["status"], D_URL, pay=pct))
    for kod, ad, key, unit in (("debt_floating_total", "Dəyişkən faizli borcun payı (ümumi)", "floating_total_pct", "%"),
                               ("debt_floating_ext", "Dəyişkən faizli borcun payı (xarici)", "floating_ext_pct", "%"),
                               ("debt_service_share", "Borca xidmətin büdcə xərclərində payı", "debt_service_exp_pct", "%"),
                               ("debt_ext_avg_maturity", "Xarici borcun orta ödəmə müddəti", "ext_avg_maturity_y", "il"),
                               ("debt_ext_due_5y", "Xarici borcun 5 ilədək ödənilən payı", "ext_due_5y_pct", "%"),
                               ("eurobond_2029", "Avrobond 2029 (kupon 5,125%)", "eurobond_2029_usd", "mln USD"),
                               ("eurobond_2032", "Avrobond 2032 (kupon 3,5%)", "eurobond_2032_usd", "mln USD")):
        if d.get(key) is not None:
            R.append(_row(kod, "Dövlət borcu", ad, d[key], unit, d["date"], "Maliyyə Nazirliyi", d["status"], D_URL))
    R.append(_row("cl_guaranteed_total", "Şərti öhdəliklər", "Dövlət zəmanətli borc (cəmi)", d["guar_total_azn"],
                  "mln AZN", d["date"], "Maliyyə Nazirliyi", d["status"], D_URL, "şərti öhdəlik (açıq)"))
    R.append(_row("cl_guaranteed_ext", "Şərti öhdəliklər", "Xarici dövlət zəmanətli borc", d["guar_ext_usd"], "mln USD",
                  d["date"], "Maliyyə Nazirliyi", d["status"], D_URL))
    if d.get("guar_dom_azn") is not None:
        R.append(_row("cl_guaranteed_dom", "Şərti öhdəliklər", "Daxili dövlət zəmanətli borc", d["guar_dom_azn"], "mln AZN",
                      d["date"], "Maliyyə Nazirliyi", d["status"], D_URL))
    for k, pct in (d.get("guar_ccy_pct") or {}).items():
        R.append(_row(f"cl_guar_ccy_{k}", "Şərti öhdəliklər valyuta", f"Zəmanətli borc: {k}", None, "%", d["date"],
                      "Maliyyə Nazirliyi", d["status"], D_URL, pay=pct))
    return _table_part2(R, x)


def _table_part2(R: list, x: dict) -> pd.DataFrame:
    s, d, c, plan, fr = x["sofaz"], x["debt"], x["cbar"], x["plan"], x["fr1"]
    B, H, y = fr["B"], fr["H"], fr["y"]
    src = "MikroUnit FR1 (FR1_analysis_dataset / FR1_forecast_full)"
    for yr, rev_oil, rev_tot, kind in ((y, H.loc[y, "rev_oil_n"], H.loc[y, "rev_tot_n"], "faktiki"),
                                       (y + 1, B.loc[y + 1, "fr1_rev_oil_n"], B.loc[y + 1, "fr1_rev_tot_n"], "FR1 baza")):
        R.append(_row(f"budget_rev_oil_{yr}", "Büdcə", f"Büdcənin neft gəlirləri {yr} ({kind})", rev_oil, "mln AZN",
                      str(yr), src, "yuxarı axın", pay=rev_oil / rev_tot * 100,
                      qeyd=f"ümumi gəlirlərin {rev_oil / rev_tot * 100:.1f}%-i"))
        R.append(_row(f"budget_rev_tot_{yr}", "Büdcə", f"Büdcənin ümumi gəlirləri {yr} ({kind})", rev_tot, "mln AZN",
                      str(yr), src, "yuxarı axın"))
    if "transfer_n" in H.columns and pd.notna(H.loc[y, "transfer_n"]):
        R.append(_row(f"sofaz_transfer_{y}", "Büdcə", f"ARDNF-dən büdcəyə transfert {y}", H.loc[y, "transfer_n"],
                      "mln AZN", str(y), src, "yuxarı axın"))
    if plan is not None:
        for yr in (y + 1, y + 2):
            R.append(_row(f"sofaz_transfer_plan_{yr}", "Büdcə", f"ARDNF transferti — Nazirlik planı {yr}",
                          plan.loc[yr, "transfer_azn"], "mln AZN", str(yr), "Nazirlik Bottom-up 'base 60' r.95",
                          "yuxarı axın", qeyd=f"Brent fərziyyəsi {plan.loc[yr, 'brent']:.0f} USD"))
        R.append(_row(f"sofaz_assets_ministry_{y}", "ARDNF", f"ARDNF aktivləri — Nazirlik 'base 60' {y}",
                      plan.loc[y, "sofaz_assets_usd"], "mln USD", str(y), "Nazirlik Bottom-up 'base 60' r.96",
                      "yuxarı axın", qeyd=f"ARDNF faktiki ilin əvvəli {s.get('start_year_usd')} mln USD — Nazirlik "
                                           "rəqəmi köhnədir (UYĞUNSUZLUQ, yoxlanmalı)"))
    # exports by commodity (FR1 history; oil / gas split derived from volumes x prices)
    xo = H.loc[y, "oil_exp_vol"] * BBL_PER_TONNE * H.loc[y, "oil_exp_price"]
    xg = H.loc[y, "gas_exp_vol"] * H.loc[y, "gas_exp_price"]
    R.append(_row(f"exports_goods_{y}", "İxrac", f"Mal ixracı {y}", H.loc[y, "x_g_usd"], "mln USD", str(y), src, "yuxarı axın"))
    R.append(_row(f"exports_oilgas_{y}", "İxrac", f"Neft-qaz ixracı {y}", H.loc[y, "x_g_oil_usd"], "mln USD", str(y), src,
                  "yuxarı axın", pay=H.loc[y, "x_g_oil_usd"] / H.loc[y, "x_g_usd"] * 100))
    R.append(_row(f"exports_oil_{y}", "İxrac", f"Xam neft ixracı {y} (törəmə)", xo, "mln USD", str(y),
                  "törəmə: həcm × 7,33 barel/ton × ixrac qiyməti", "törəmə",
                  qeyd=f"{H.loc[y, 'oil_exp_vol']:.2f} mln ton × {H.loc[y, 'oil_exp_price']:.1f} USD/barel"))
    R.append(_row(f"exports_gas_{y}", "İxrac", f"Təbii qaz ixracı {y} (törəmə)", xg, "mln USD", str(y),
                  "törəmə: həcm (mlrd m³) × qiymət (USD/min m³)", "törəmə",
                  qeyd=f"{H.loc[y, 'gas_exp_vol']:.2f} mlrd m³ × {H.loc[y, 'gas_exp_price']:.0f} USD; "
                       f"neft+qaz qalığı {H.loc[y, 'x_g_oil_usd'] - xo - xg:.0f} mln USD (neft məhsulları və s.)"))
    if c.get("bank_assets_azn") is not None:
        bu = "AMB statistik bülleteni, c.5.2/5.6"
        for kod, ad, key in (("bank_assets", "Bank sektoru: cəmi aktivlər", "bank_assets_azn"),
                             ("bank_loans", "Bank sektoru: müştərilərə kreditlər", "bank_loans_azn"),
                             ("bank_deposits", "Bank sektoru: depozitlər", "bank_deposits_azn"),
                             ("bank_deposits_fx", "Bank sektoru: xarici valyutada depozitlər", "bank_deposits_fx_azn"),
                             ("bank_capital", "Bank sektoru: cəmi kapital", "bank_capital_azn")):
            R.append(_row(kod, "Bank sektoru", ad, c[key], "mln AZN", c["bank_date"], bu, c["status"], c.get("url", "")))
        R.append(_row("bank_npl", "Bank sektoru", "Qeyri-işlək kreditlər (90+ gün)", c["npl_azn"], "mln AZN", c["npl_date"],
                      bu, c["status"], c.get("url", ""), pay=c["npl_ratio"] * 100,
                      qeyd=f"kredit portfelinin {c['npl_ratio'] * 100:.2f}%-i"))
        R.append(_row("bank_capital_to_assets", "Bank sektoru", "Kapital / aktivlər (leverec, törəmə)",
                      c["bank_capital_azn"] / c["bank_assets_azn"] * 100, "%", c["bank_date"], "törəmə", "törəmə",
                      qeyd="kapital adekvatlığı (RWA) açıq deyil — məlumat sorğusu"))
    sof = next(r["mln_usd"] for r in R if r["kod"] == "sofaz_total")
    res = next((r["mln_usd"] for r in R if r["kod"] == "cbar_reserves"), 0.0) or 0.0
    debt = d["total_azn"] / PEG
    guar = d["guar_total_azn"] / PEG
    R.append(_row("fiscal_capital", "Xalis dəyər", "Fiskal kapital: ARDNF + AMB ehtiyatları − dövlət borcu",
                  sof + res - debt, "mln USD", config.as_of().isoformat(), "törəmə", "törəmə",
                  qeyd="AMB ehtiyatları suveren balansa tam daxil edilib (konsolidasiya fərziyyəsi)"))
    R.append(_row("fiscal_capital_cl", "Xalis dəyər", "Fiskal kapital, zəmanətli borc çıxılmaqla",
                  sof + res - debt - guar, "mln USD", config.as_of().isoformat(), "törəmə", "törəmə",
                  qeyd="ehtiyatlı variant: zəmanətlərin 100%-i öhdəlik sayılır"))
    out = pd.DataFrame(R, columns=COLS)
    out["alinma_utc"] = fm._utc()
    return out


DATA_REQUESTS = [
    ("DR01", "Bank sektoru", "Kapital adekvatlığı (RWA, I və II dərəcəli kapital), bank üzrə stress testi nəticələri, "
     "valyuta mövqeyi", "AMB (Maliyyə sabitliyi departamenti)", "Bank sektoru şərti öhdəliyinin (rekapitalizasiya) "
     "kalibrlənməsi; hazırda kapital/aktiv leverecindən istifadə olunur", "yüksək"),
    ("DR02", "Şərti öhdəliklər", "Dövlət müəssisələrinin (ARDNŞ, ADY, AZAL, Azərenerji və s.) zəmanətsiz borcları: "
     "valyuta, ödəmə qrafiki, faiz növü", "Maliyyə Nazirliyi; Dövlət Müəssisələrinin Monitorinqi Agentliyi",
     "Şərti öhdəliklər xəritəsi (Blueprint L4); hazırda yalnız açıq dövlət zəmanətli borc daxildir", "yüksək"),
    ("DR03", "ARDNF", "İstiqraz portfelinin modifikasiya olunmuş müddəti (duration), səhm portfelinin valyuta/region "
     "bölgüsü, daşınmaz əmlakın qiymətləndirmə üsulu, aylıq portfel gəlirliliyi seriyası", "ARDNF",
     "VaR-ın dəqiqləşdirilməsi və geriyə doğru sınağı; hazırda müddət qruplarından təxmin edilir", "yüksək"),
    ("DR04", "AMB ehtiyatları", "AMB rəsmi ehtiyatlarının valyuta və aktiv tərkibi (qızıl payı daxil)", "AMB",
     "Suveren xalis valyuta mövqeyinin VaR-ı; hazırda ehtiyatlar 100% USD fərz edilir", "orta"),
    ("DR05", "Xarici borc", "Ölkənin ümumi xarici borcu (dövlət, banklar, dövlət müəssisələri, özəl sektor) ödəmə "
     "müddəti üzrə; beynəlxalq investisiya mövqeyi", "AMB", "İqtisadiyyatın xarici öhdəliklərə məruz qalması", "orta"),
    ("DR06", "Suveren spred", "Azərbaycan avrobondlarının gündəlik bazar gəlirliliyi/spredi və suveren CDS", "Maliyyə "
     "Nazirliyi (Bloomberg/Refinitiv abunəsi)", "Hazırda EM korporativ spredi (ICE BofA) proksi kimi istifadə olunur", "orta"),
    ("DR07", "Büdcə", "ARDNF transferlərinin 2027–2030 ortamüddətli planı (Ortamüddətli Xərclər Çərçivəsi)", "Maliyyə "
     "Nazirliyi", "ARDNF adekvatlığı və fiskal kapital; hazırda Nazirlik 'base 60' planı istifadə olunur", "yüksək"),
    ("DR08", "Şərti öhdəliklər", "Dövlət-özəl tərəfdaşlıq öhdəlikləri, məhkəmə iddiaları, Əmanətlərin Sığortalanması "
     "Fondunun öhdəlikləri", "Maliyyə Nazirliyi; ƏSF", "Şərti öhdəliklər xəritəsi", "aşağı"),
    ("DR09", "Daxili bazar", "Dövlət istiqrazlarının gəlirlilik əyrisi (gündəlik, BFB)", "BFB; Maliyyə Nazirliyi",
     "Daxili borcun faiz riski", "aşağı"),
    ("DR10", "Risk iştahı", "Fiskal kapital, borc/ÜDM, ARDNF örtük illəri və VaR limitləri üzrə risk iştahı həddləri",
     "İqtisadiyyat Nazirliyi (qərar)", "K1/K2 ehtimallarının həddləri hazırda parametr kimi təklif olunur", "yüksək"),
    ("DR11", "Uyğunsuzluq", "MikroUnit FR1 debt_azn 2025 = 38 451 mln AZN; MN bülleteninə görə 2026-nın əvvəlinə "
     "dövlət borcu ≈ 26,0 mlrd AZN. Tərif fərqi aydınlaşdırılmalıdır", "MikroUnit (§15.5.2) komandası",
     "DSA başlanğıc qalığı MN rəqəmindən götürülür; FR1 yalnız balans axını üçün istifadə olunur", "yüksək"),
    ("DR12", "Uyğunsuzluq", "Nazirlik 'base 60' ARDNF aktivləri 2025 = 58 984 mln USD; ARDNF faktiki 2026-nın "
     "əvvəlinə 73 541 mln USD", "İqtisadiyyat Nazirliyi (Bottom-up modeli)", "ARDNF yolu faktiki qalıqdan başlayır", "orta"),
]


def data_requests() -> pd.DataFrame:
    return pd.DataFrame(DATA_REQUESTS, columns=["sorgu_id", "movzu", "lazim_olan_melumat", "qurum", "istifade_meqsedi",
                                                "prioritet"]).assign(status="göndərilməyib", tarix=config.as_of().isoformat())


def run(ctx: dict | None = None) -> dict:
    ctx = ctx if ctx is not None else {}
    x = collect()
    t = table(x)
    p1, p2 = config.OUTPUT / "V1_exposures.csv", config.OUTPUT / "V1b_data_requests.csv"
    t.to_csv(p1, index=False, lineterminator="\n")
    data_requests().to_csv(p2, index=False, lineterminator="\n")
    fm.register_catalog("V1_exposures.csv", "exposures",
                        "Suveren balans məruz qalmaları: ARDNF (valyuta, aktiv sinfi, müddət, reytinq), AMB ehtiyatları, "
                        "dövlət və zəmanətli borc, büdcənin neft asılılığı, ixrac, bank sektoru — mənbə, tarix, status",
                        list(t.columns), "gündəlik (mənbələr aylıq/rüblük yenilənir)")
    fm.register_catalog("V1b_data_requests.csv", "exposures",
                        "Açıq olmayan məlumatlar üzrə sorğular və aşkarlanmış uyğunsuzluqlar",
                        list(pd.read_csv(p2, nrows=0).columns), "dəyişdikdə")
    fm.flush_status()
    ctx["exposures"] = x
    return {"V1_exposures": str(p1), "V1b_data_requests": str(p2), "n": len(t),
            "status": {k: x[k].get("status") for k in ("sofaz", "debt", "cbar")}}


if __name__ == "__main__":
    r = run()
    print(r)
    print(pd.read_csv(r["V1_exposures"])[["kod", "deyer", "vahid", "tarix", "status"]].to_string())
