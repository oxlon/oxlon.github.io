import csv, sys, os, json, collections
src = sys.argv[1]; out = sys.argv[2]
cols = ["3 Mo","6 Mo","1 Yr","2 Yr","3 Yr","5 Yr","7 Yr","10 Yr"]
acc = collections.OrderedDict()
for y in range(1990, 2027):
    p = os.path.join(src, f"t{y}.csv")
    with open(p, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            m, d, yy = row["Date"].split("/")
            key = f"{yy}-{m}"
            vals = []
            for c in cols:
                v = row.get(c, "")
                vals.append(float(v) if v not in ("", None, "N/A") else None)
            acc.setdefault(key, []).append(vals)
months = sorted(acc.keys())
# keep complete months only: drop the current partial month (Nov 2026)
months = [k for k in months if k <= "2026-10"]
series = []
missing = 0
for k in months:
    rows = acc[k]
    mv = []
    for j in range(len(cols)):
        xs = [r[j] for r in rows if r[j] is not None]
        if not xs:
            missing += 1; mv.append(None)
        else:
            mv.append(round(sum(xs)/len(xs), 2))
    series.append(mv)
print("months", len(months), months[0], months[-1], "missing cells", missing)
for probe in ["1990-01","2000-05","2007-02","2008-12","2013-05","2020-04","2023-07","2026-10"]:
    i = months.index(probe); print(probe, series[i])
payload = {
  "source": "U.S. Department of the Treasury, Daily Treasury Par Yield Curve Rates; monthly averages of daily values computed by Oxlon",
  "maturities": [0.25, 0.5, 1, 2, 3, 5, 7, 10],
  "labels": ["3M","6M","1Y","2Y","3Y","5Y","7Y","10Y"],
  "start": months[0], "end": months[-1],
  "y": series,
}
with open(out, "w") as f:
    f.write("/* US Treasury par yield curve, monthly averages of daily rates, " + months[0] + " to " + months[-1] + ".\n   Source: U.S. Department of the Treasury, Daily Treasury Par Yield Curve Rates (home.treasury.gov). */\n")
    f.write("window.OXLON_YIELDS=" + json.dumps(payload, separators=(",",":")) + ";\n")
print("bytes", os.path.getsize(out))
