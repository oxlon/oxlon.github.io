# Oxlon website — deployment notes

Last updated: 21 April 2026

## What this is

A complete, static, deploy-ready site for **oxlon.uk** (and, later, oxlon.ai).
Roughly 15 live pages plus nine legacy redirects, a 404, sitemap, robots.txt,
and a `_redirects` file for Netlify / Cloudflare Pages.

## File map

### Live pages (top-nav order)

| URL                      | File                         | Purpose                                        |
|--------------------------|------------------------------|------------------------------------------------|
| `/`                      | `index.html`                 | Home                                           |
| `/econai`                | `econai.html`                | Platform / product page (flagship)             |
| `/learning` `/atlas`     | `learning.html`              | Oxlon Atlas — executive learning programmes    |
| `/advisory`              | `advisory.html`              | Advisory overview — four practice areas        |
| `/economics-of-ai`       | `economics-of-ai.html`       | Flagship programme, sub-page of advisory       |
| `/research`              | `research.html`              | Research hub — 12 papers + 6 insight cards     |
| `/about`                 | `about.html`                 | Firm story + three founders                    |
| `/contact`               | `contact.html`               | Scoping-call page + form                       |
| `/case/azerbaijan`       | `case-azerbaijan.html`       | Flagship case study (Ministry of Economy)      |
| `/insight-april-fomc`    | `insight-april-fomc.html`    | Template insight post — April FOMC readout     |
| `/legal` `/privacy` `/terms` `/cookies` | `legal.html`  | Combined privacy + terms + cookies doc |
| `/404`                   | `404.html`                   | Branded not-found page                         |

### Internal

| File                     | Purpose                                                      |
|--------------------------|--------------------------------------------------------------|
| `design-system.html`     | Internal reference — **disallowed in robots.txt**; keep live |
| `assets/site.css`        | Shared stylesheet (tokens, components)                       |
| `assets/site.js`         | Shared top-bar + footer renderer                             |
| `favicon.svg`            | SVG favicon (ink deep + cream 'o')                           |

### Deploy-layer

| File                     | Purpose                                                      |
|--------------------------|--------------------------------------------------------------|
| `robots.txt`             | Indexing rules + AI-training bot opt-outs                    |
| `sitemap.xml`            | 10-URL sitemap for search console submission                 |
| `_redirects`             | 301 redirects (Netlify / Cloudflare Pages format)            |

### Legacy redirects (HTML-meta, belt-and-braces)

Every legacy URL from the old site redirects to the most topically-appropriate
new page — preserving any residual SEO equity rather than dumping everything
onto `/`. The redirects are done two ways:

1. **Server-side** via `_redirects` (takes precedence when supported).
2. **Client-side** via `<meta refresh>` inside each HTML file (fallback).

Legacy files included: `artificial-intelligence.html`, `big-data-services.html`,
`business-intelligence.html`, `data-analytics.html`, `data-management.html`,
`data-science-consulting.html`, `data-visualization-services.html`,
`about-us.html`, `about-us-2.html`.

---

## Before you deploy — the 10-point checklist

### Critical (must do)

1. **Buy the LinkedIn company handle.** Footer links assume `linkedin.com/company/oxlon/`. If that slug isn't available, fix in `assets/site.js` → `FOOT_COLS` → "Firm" column and in `contact.html`.
2. **Set up the email addresses.** The site promises: `info@`, `research@`, `press@`, `hiring@`, `privacy@` at `oxlon.uk`. Set these up before the site goes live — each is referenced as a `mailto:` link.
3. **Wire the newsletter form.** `research.html` has a sign-up form that currently no-ops on submit. Point the `<form>` to Buttondown / Substack / Beehiiv (recommend Buttondown — privacy-respecting, matches the tone). The legal page already names Buttondown as the processor; if you choose something else, update `legal.html` in the "Processors" section.
4. **Wire the contact form.** `contact.html` has a form that currently no-ops. Point at Formspree, Basin, or your own endpoint. Recommend: set up a dedicated inbox (e.g. `enquiries@oxlon.uk`) that receives submissions.
5. **Disable Cloudflare email obfuscation.** If you host on Cloudflare and its automatic email-protection feature is on, it rewrites `mailto:` links. Turn it off (Dashboard → Email Security → Email Address Obfuscation → Off). The site files now use plain `mailto:` links and no longer require Cloudflare's email-decode script.

### Important (should do)

6. **Add analytics.** The legal page names Plausible. Add the script to each page's `<head>`. One-line drop-in: `<script defer data-domain="oxlon.uk" src="https://plausible.io/js/script.js"></script>`.
7. **Register the domain + Ltd company.** The legal page says "registration number to follow". Replace with the Companies House number once you have it.
8. **Upload the sitemap** to Google Search Console and Bing Webmaster Tools. This is a one-time five-minute job that pays off for years.
9. **Buy `oxlon.ai`** and park it on the same hosting, with a 301 from `oxlon.uk` → `oxlon.ai` the moment you're ready to switch. Until then, don't split the brand across two live domains.
10. **Update the favicon** if you want something more distinctive than the generic 'o' in a circle. The current one is a placeholder good enough for soft-launch; a real mark deserves a proper designer pass later.

### Nice to have

- Replace the text-only `avatar` letters (o/f/m) on `about.html` with photographs of the founders.
- Write three more insight posts so all six cards on `/research` link to live content. The `insight-april-fomc.html` page is the template — copy, rename, and update the text.
- Write a press page at `/press` (logos, bios, headshots, media contacts) once you've had your first serious press interaction.
- Add a `/case/ministry-of-finance-country-x` page once you have a second reference client cleared for public mention.

---

## Hosting recommendations

**Recommended: Cloudflare Pages** (free tier, fast, has the right primitives).

1. Connect a GitHub repo containing everything in this folder.
2. Build command: *(leave empty — static site)*
3. Output directory: `/` (root of repo)
4. Assign `oxlon.uk` as the custom domain.
5. The `_redirects` file will be picked up automatically.
6. Turn **off** "Email Obfuscation" under domain → Email → Settings.

**Alternative: Netlify** (same architecture, works identically).

**Not recommended: a traditional cPanel/VPS setup.** The `_redirects` file syntax won't work; you'll need to write `.htaccess` equivalents by hand. If you must, I can provide an Apache rewrite block separately.

---

## Ongoing: the content cadence

The site's flywheel is research + insights + the memo. A realistic steady-state schedule:

- **Working papers** — one new or materially updated paper per quarter. Upload the PDF, update `research.html` with the abstract and bibliographic entry.
- **Insights** — two per month. A 5–10 minute post in the format of `insight-april-fomc.html`. Update the card on `research.html` with a link to the new page. (Within six months, build this into a real CMS rather than hand-editing HTML — Sanity or Contentful are both fine.)
- **The Oxlon Memo** — fortnightly, via Buttondown. Short: a chart, a paragraph, a link, a sign-off. Takes 30–40 minutes to write if the research is already done.
- **Meeting readouts** — within 36 hours of every FOMC, MPC, and ECB meeting. A one-page post in the format of the April FOMC readout. A chart, four paragraphs, a takeaway.

At that cadence, by the end of year one you'll have ~30 papers and insights, a mailing list in the low thousands, and a research hub that ranks organically for the queries your buyers type.

---

## A final note on the legal page

The `legal.html` page is deliberately written in plain English and, on a first-pass read, is materially better than what most firms of your size publish. It is **not** a substitute for a formal review by a UK data-protection solicitor before launch — specifically, the retention periods, the processor list, and the liability cap should all be sanity-checked against your actual operations. Budget £800–£1,500 for the review; it is cheap insurance.

If you want, I can produce a separate Markdown version of the legal page for your solicitor to mark up in track-changes.

---

*End.*
