#!/usr/bin/env python3
"""build_site.py — regenerate the MİİS §15.5.2 «Klassik görünüş» site from the module's outputs.

    python3 site/build_site.py            # from MicroUnit/

Reads MicroUnit/output/FR*_* (CSV and the FRx_equations.json registries), MicroUnit/docs/ (and
docs/az/ when present), api/OXUYUN.md and the requirement sources; writes every page under
MicroUnit/site/, then runs three checks, any of which fails the build:
  * the forecast completeness check (every catalog component has 2026–2030 in every scenario),
  * the link / figure checker (every link, anchor and inline chart; no external resource),
  * the leftover-English check (word list + allow-list, _build/xlate.py).
Deterministic: two runs on the same day (or with SOURCE_DATE_EPOCH set) give byte-identical pages.
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True       # keep site/_build free of __pycache__

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _build import core, html, req, check, xlate                         # noqa: E402
from _build import fr1, fr3, fr4, fr5, fr10, fr12                        # noqa: E402
from _build import pg_index, pg_method, pg_data, pg_synth, pg_nb, pg_results  # noqa: E402
from _build import pg_rob, pg_api, pg_eqs, pg_fc, pg_lb10, pg_lb12, v2fr, v2data  # noqa: E402
from _build.common import FR_SECTIONS                                    # noqa: E402

FR_PAGES = [
    ("FR1", "fr/fr1.html", "FR1 — Sektorlar və bazarlar", fr1, FR_SECTIONS),
    ("FR3", "fr/fr3.html", "FR3 — Orta aylıq əmək haqqı", fr3, FR_SECTIONS),
    ("FR4", "fr/fr4.html", "FR4 — Məşğulluq göstəriciləri", fr4, FR_SECTIONS),
    ("FR5", "fr/fr5.html", "FR5 — Əhaliyə göstərilən pullu xidmətlər", fr5, FR_SECTIONS),
    ("FR10", "fr/fr10.html", "FR10 — Müəssisələrin maliyyə vəziyyəti, effektivliyi və bazar payı", fr10, fr10.SECTIONS),
    ("FR12", "fr/fr12.html", "FR12 — Rəqabət mühiti", fr12, fr12.SECTIONS),
]

TOP_PAGES = [
    ("index.html", "Ümumi baxış", pg_index),
    ("dayaniqliq.html", "Modellərin dayanıqlığı", pg_rob),
    ("methodology.html", "Metod", pg_method),
    ("data.html", "Məlumat mənbələri", pg_data),
    ("synthetic.html", "Sintetik məlumat və onun əvəz edilməsi", pg_synth),
    ("notebooks.html", "Jupyter dəftərləri", pg_nb),
    ("api.html", "API və avtomatlaşdırma", pg_api),
    ("results.html", "Nəticələr və fayllar", pg_results),
]


def write(path, text):
    p = core.SITE / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main():
    date = core.build_date()
    texts = req.texts()
    for m, path, title, mod, secs in FR_PAGES:
        core.reset_used()
        req.texts()                      # record the requirement sources on this page
        body, s2 = v2fr.augment(m, mod.build(texts), list(secs), path)
        write(path, html.page(path, title, s2, body, date))
        print("wrote", path)
        short = title.split(" — ", 1)[1]
        for sub, label, builder in (("proqnoz", "Proqnoz cədvəlləri", pg_fc.build),
                                    ("tenlikler", "Tənliklər", pg_eqs.build)):
            core.reset_used()
            p2 = f"fr/{m.lower()}-{sub}.html"
            try:
                b2, s3 = builder(m, short)
            except pg_fc.Incomplete as e:
                print("FORECAST COMPLETENESS CHECK FAILED:", e)
                return 1
            write(p2, html.page(p2, f"{m} — {label}", s3, b2, date))
            print("wrote", p2)
    for m, mod in (("FR10", pg_lb10), ("FR12", pg_lb12)):
        core.reset_used()
        p2 = f"fr/{m.lower()}-sintetik.html"
        b2, s3 = mod.build(texts)
        write(p2, html.page(p2, f"{m} — Sintetik B qatı", s3, b2, date))
        print("wrote", p2)
    for path, title, mod in TOP_PAGES:
        core.reset_used()
        body, secs = mod.build(texts)
        write(path, html.page(path, title, secs, body, date))
        print("wrote", path)
    print("FORECAST COMPLETENESS CHECK: OK — every catalog component has 2026–2030 in every scenario")
    ok = check.run(core.SITE)
    ok_az = xlate.run(core.SITE, extra=v2data.codes())
    return 0 if (ok and ok_az) else 1


if __name__ == "__main__":
    sys.exit(main())
