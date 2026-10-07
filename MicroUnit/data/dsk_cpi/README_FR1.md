# DSK monthly consumer prices for the FR1 2026 CPI nowcast (v2.3.3)

FR1.ipynb (Part 12.3) reads every `*.csv` in this folder **and** the latest RiskUnit vintage
(`../RiskUnit/data/vintages/<date>/dsk_cpi.csv`, refreshed by the RiskUnit DSK fetcher from stat.gov.az), plus the monthly
y/y CPI columns of the Ministry workbook (`Monetar sektoru`, row 86). The most recent month of the nowcast year wins.
Format: `series,date,value,unit` (series `dsk_cpi_yoy` = CPI, % change on the same month of the previous year).

| file | source | md5 |
|---|---|---|
| `dsk_cpi_2026-10-06.csv` | copy of `RiskUnit/data/vintages/2026-10-06/dsk_cpi.csv` (DSK release, August 2026) | see notebook output `FR1_cpi_nowcast.csv` |

To refresh: drop a newer file in the same format here (or let the RiskUnit fetcher add a vintage) and re-run FR1.
