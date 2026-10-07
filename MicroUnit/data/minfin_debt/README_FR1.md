# Ministry of Finance public-debt bulletin, for the FR1 2026 debt anchor (v2.3.4)

FR1.ipynb (Part 12.4) reads every `*.json` here **and** the latest RiskUnit vintage
(`../RiskUnit/data/vintages/minfin/<date>/debt_parsed.json`, parsed by the RiskUnit fetcher from maliyye.gov.az).
Fields used: `date` (stock date), `total_azn` (public debt, mln AZN = external + domestic; state-guaranteed debt excluded),
`ext_usd`, `dom_azn`, `url`. The most recent date in the nowcast year wins.

| file | source |
|---|---|
| `minfin_debt_2026-10-06.json` | copy of `RiskUnit/data/vintages/minfin/2026-10-06/debt_parsed.json` (bulletin as of 01.07.2026) |
