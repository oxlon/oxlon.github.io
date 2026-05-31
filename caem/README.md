# CAEM Macro-Fiscal Dashboard — static site (oxlon.uk/caem)

A **fully static** web app — no server, no Python, no build step. It runs the entire
IMF-style Financial-Programming engine **in the browser** (`assets/engine.js`).
Deploy exactly like the report site: upload this folder so it serves at **oxlon.uk/caem**
(the report site `../website/` serves at oxlon.uk/az; the report's sidebar links here).

## Deploy
Upload the whole `caem/` folder to the web root so the path is `oxlon.uk/caem/`. That's it.
Open `index.html` over **http(s)** (not `file://` — browsers block `fetch` of local files on file://).
Local preview: `cd caem && python3 -m http.server 8012` → http://localhost:8012

## Contents
```
index.html            the dashboard
assets/engine.js      client-side FPP engine (HP gap, Phillips, Taylor, debt, fan, editable data)
assets/app.js         UI (figures, scenario console, fan charts, info drawer, impact summary)
assets/style.css      styles
data/series.json      CAEM series + 2025 SSC actuals + calibration (drives the live engine)
data/figures.json     160 figures extracted from CAEM.xlsb
```

## What it does
- Reproduces CAEM's spine (HP output gap, open-economy Phillips curve, smoothed Taylor rule,
  debt dynamics) — validated against the workbook to ≈0.1 pp; verified identical to the Python engine.
- **Live scenario console** (12 shocks) + **quick-scenario presets** → recompute & overlay.
- **Fan charts** (Bank-of-England red), **scenario-impact summary**, **2025 forecast-vs-actual scorecard**.
- **Editable data** ("✎ Update data"): enter a new year's outturn → re-anchors and re-forecasts.
- **CSV export** of the forecast.
- Re-anchored to the **2025 official outturn** (SSC, Jan 2026); forecasts **2026+**.

## Updating the data
Re-run the (offline) pipeline in `../../caem/engine/`:
`build_series.py` → `data/series.json`, `build_figures.py` → `data/figures.json`, then copy both
into `caem/data/`. Bump the `?v=` query on the script/style tags in `index.html` to bust caches.

See `../../caem/ROADMAP.md` for the honest status and the remaining improvement plan.

## On-premise deployment, roles & audit
**On-prem:** because the app is fully static (HTML + JS + JSON, engine runs in the browser), it can be hosted
entirely **inside the Ministry's network** — copy the `caem/` folder to any internal web server (IIS, nginx,
Apache, or a SharePoint/file share served over HTTP). No external calls, no data leaves the premises. This
satisfies data-sovereignty requirements. (An optional Python/FastAPI build also exists for server-side use.)

**Roles:** the dashboard is read-only for viewers; analysts use the Scenario console, Update-data and Save.
Enforced role-based access control (login, per-user permissions) requires the **server build** — it cannot be
truly enforced by a static client. Documented as the production-hardening phase, not faked here.

**Audit trail:** within a session the data banner records entered actuals, the status line records each run,
and 💾 Saved scenarios persist named forecast rounds (browser storage). A durable, multi-user audit log
(who changed which assumption, when) also belongs to the server build.
