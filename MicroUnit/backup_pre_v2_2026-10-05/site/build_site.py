#!/usr/bin/env python3
"""build_site.py — regenerate the MİİS §15.5.2 presentation site from the module's outputs.

    python3 site/build_site.py            # from MicroUnit/

Reads MicroUnit/output/FR*_*.csv, MicroUnit/docs/FR*_Methodology.md, the data READMEs and the
requirement sources; writes every page under MicroUnit/site/, then runs the link checker and the
figure checks. Every number on the site comes from those files at build time. Deterministic: two
runs on the same day (or with SOURCE_DATE_EPOCH set) give byte-identical pages.
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True       # keep site/_build free of __pycache__

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _build import core, html, req, check            # noqa: E402
from _build import fr1, fr3, fr4, fr5, fr10, fr12     # noqa: E402
from _build import pg_index, pg_method, pg_data, pg_synth, pg_nb, pg_results  # noqa: E402
from _build.common import FR_SECTIONS                 # noqa: E402

FR_PAGES = [
    ("fr/fr1.html", "FR1 — Sektorlar və bazarlar", fr1, FR_SECTIONS),
    ("fr/fr3.html", "FR3 — Orta aylıq əmək haqqı", fr3, FR_SECTIONS),
    ("fr/fr4.html", "FR4 — Məşğulluq göstəriciləri", fr4, FR_SECTIONS),
    ("fr/fr5.html", "FR5 — Əhaliyə göstərilən pullu xidmətlər", fr5, FR_SECTIONS),
    ("fr/fr10.html", "FR10 — Müəssisələrin maliyyə vəziyyəti, effektivliyi və bazar payı", fr10, fr10.SECTIONS),
    ("fr/fr12.html", "FR12 — Rəqabət mühiti", fr12, fr12.SECTIONS),
]

TOP_PAGES = [
    ("index.html", "Ümumi baxış", pg_index),
    ("methodology.html", "Metod", pg_method),
    ("data.html", "Məlumat mənbələri", pg_data),
    ("synthetic.html", "Sintetik məlumat və onun əvəz edilməsi", pg_synth),
    ("notebooks.html", "Jupyter dəftərləri", pg_nb),
    ("results.html", "Nəticələr və fayllar", pg_results),
]


def write(path, text):
    p = core.SITE / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main():
    date = core.build_date()
    texts = req.texts()
    for path, title, mod, secs in FR_PAGES:
        core.reset_used()
        req.texts()                      # record the requirement sources on this page
        body = mod.build(texts)
        write(path, html.page(path, title, secs, body, date))
        print("wrote", path)
    for path, title, mod in TOP_PAGES:
        core.reset_used()
        body, secs = mod.build(texts)
        write(path, html.page(path, title, secs, body, date))
        print("wrote", path)
    ok = check.run(core.SITE)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
