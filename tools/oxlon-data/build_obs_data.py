import csv, json, os, sys, glob, datetime
D = sys.argv[1]; OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

# ---- BLS: unemployment rate (SA) and CPI-U all items (NSA) -> 12-month inflation
un = {}; cpi = {}; bad = []
for p in sorted(glob.glob(os.path.join(D, "bls_*.json"))):
    d = json.load(open(p))
    for s in d["Results"]["series"]:
        for o in s["data"]:
            per = o["period"]
            if not per.startswith("M") or per == "M13":
                continue
            key = f'{o["year"]}-{per[1:]}'
            try:
                v = float(o["value"])
            except ValueError:
                bad.append((s["seriesID"], key, o["value"])); continue
            (un if s["seriesID"] == "LNS14000000" else cpi)[key] = v
# Full calendar, so that a month BLS did not publish stays in place as a gap.
first = min(set(un) | set(cpi)); last = max(set(un) | set(cpi))
months = []
yy, mm = map(int, first.split("-"))
while f"{yy}-{mm:02d}" <= last:
    months.append(f"{yy}-{mm:02d}"); mm += 1
    if mm == 13: yy += 1; mm = 1
def prev12(k):
    y, m = map(int, k.split("-")); return f"{y-1}-{m:02d}"
rows = []
for k in months:
    if k < "1949-01":
        continue
    u = un.get(k); c = cpi.get(k); c0 = cpi.get(prev12(k))
    infl = round(100.0 * (c / c0 - 1.0), 2) if (c is not None and c0 is not None) else None
    rows.append([k, u, infl])
missing = [r[0] for r in rows if r[1] is None or r[2] is None]
print("BLS months", len(rows), rows[0][0], rows[-1][0], "missing", missing[:12], "bad", bad[:6])
for probe in ["1974-12", "1980-03", "1982-11", "2009-10", "2020-04", "2022-06", rows[-1][0]]:
    print("  ", [r for r in rows if r[0] == probe])
payload = {"start": rows[0][0], "end": rows[-1][0],
           "u": [r[1] for r in rows], "pi": [r[2] for r in rows]}
with open(os.path.join(OUT, "us-macro.js"), "w") as f:
    f.write("/* US unemployment rate (BLS LNS14000000, seasonally adjusted) and 12-month CPI inflation computed from CPI-U all items (BLS CUUR0000SA0, not seasonally adjusted), monthly. Source: U.S. Bureau of Labor Statistics. */\n")
    f.write("window.OXLON_USMACRO=" + json.dumps(payload, separators=(",", ":")) + ";\n")

# ---- BIS policy rates, monthly end of period
keep = ["CH","JP","XM","SE","DK","CZ","GB","CA","KR","US","NZ","AU","NO","TH","MY","IL","PL","CN","HU","CL","PH","PE","ID","IN","ZA","MX","CO","TR"]
names = {"CH":"Switzerland","JP":"Japan","XM":"Euro area","SE":"Sweden","DK":"Denmark","CZ":"Czechia","GB":"United Kingdom","CA":"Canada","KR":"Korea","US":"United States","NZ":"New Zealand","AU":"Australia","NO":"Norway","TH":"Thailand","MY":"Malaysia","IL":"Israel","PL":"Poland","CN":"China","HU":"Hungary","CL":"Chile","PH":"Philippines","PE":"Peru","ID":"Indonesia","IN":"India","ZA":"South Africa","MX":"Mexico","CO":"Colombia","TR":"Türkiye"}
series = {k: {} for k in keep}
for r in csv.DictReader(open(os.path.join(D, "bis_all.csv"), newline="")):
    a = r["REF_AREA"]
    if a in series and r["OBS_VALUE"] not in ("", "NaN"):
        series[a][r["TIME_PERIOD"]] = float(r["OBS_VALUE"])
allm = []
y, m = 1990, 1
while (y, m) <= (2026, 10):
    allm.append(f"{y}-{m:02d}"); m += 1
    if m == 13: y += 1; m = 1
# order economies by mean rate 2010-01..2026-10 (low at the front)
def mean_recent(a):
    xs = [v for k, v in series[a].items() if k >= "2010-01"]
    return sum(xs) / len(xs)
order = sorted(keep, key=mean_recent)
vals = []
for a in order:
    vals.append([series[a].get(k) for k in allm])
cov = {a: sum(v is not None for v in vals[i]) for i, a in enumerate(order)}
print("BIS economies", len(order), "months", len(allm))
print("  order:", [(a, round(mean_recent(a), 2), cov[a]) for a in order])
mx = max(v for row in vals for v in row if v is not None)
print("  max", mx)
payload = {"start": allm[0], "end": allm[-1], "codes": order, "names": [names[a] for a in order], "r": vals}
with open(os.path.join(OUT, "policy-rates.js"), "w") as f:
    f.write("/* Central bank policy rates, monthly, end of period. Source: BIS, Central bank policy rates (WS_CBPOL), stats.bis.org. */\n")
    f.write("window.OXLON_POLICY=" + json.dumps(payload, separators=(",", ":")) + ";\n")

# ---- CBOE VIX daily close
rows = list(csv.DictReader(open(os.path.join(D, "vix.csv"), newline="")))
base = datetime.date(1990, 1, 1)
days = []; closes = []
for r in rows:
    mm, dd, yy = map(int, r["DATE"].split("/"))
    days.append((datetime.date(yy, mm, dd) - base).days)
    closes.append(round(float(r["CLOSE"]), 2))
deltas = [days[0]] + [days[i] - days[i - 1] for i in range(1, len(days))]
print("VIX days", len(days), rows[0]["DATE"], rows[-1]["DATE"], "max delta", max(deltas[1:]), "min close", min(closes))
payload = {"base": "1990-01-01", "dd": deltas, "c": closes}
with open(os.path.join(OUT, "vix.js"), "w") as f:
    f.write("/* CBOE Volatility Index (VIX), daily close. Source: Cboe Global Markets, VIX historical data (cdn.cboe.com). */\n")
    f.write("window.OXLON_VIX=" + json.dumps(payload, separators=(",", ":")) + ";\n")
for fn in ["us-macro.js", "policy-rates.js", "vix.js"]:
    print(fn, os.path.getsize(os.path.join(OUT, fn)), "bytes")
