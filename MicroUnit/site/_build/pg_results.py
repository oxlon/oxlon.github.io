"""pg_results.py — every output file, grouped by module, with a one-line description and its row count.

Descriptions are composed from the file name by the rules below (most specific first), so a new
output file is listed automatically on the next build.
"""
import re

from . import core, html, nbinfo
from .core import v, esc

RULES = [
    (r"SYNTHETIC_pipeline_tests", "B qatı boru xətti testləri (sintetik məlumatla)"),
    (r"SYNTHETIC_", "B qatının sintetik nümayiş çıxışı — su nişanlı, tapıntı deyil"),
    (r"swap_tests", "Sintetik faylın real faylla əvəz edilməsi testləri"),
    (r"validation_report", "Giriş faylının validator hesabatı (sətir × sahə)"),
    (r"(input_schema|business_register_schema)", "B qatı giriş faylının sxemi (məlumat müqaviləsi)"),
    (r"data_source_matrix", "Göstəricilər sistemi: məlumat → mənbə → göstərici → təqdimat forması"),
    (r"data_gaps", "Məlumat boşluqları, alternativlər və Sifarişçi ilə razılaşdırılacaq addımlar"),
    (r"data_integrity", "Məlumat bütövlüyü tapıntıları"),
    (r"dsk_manifest", "Yığılmış DSK fayllarının manifesti"),
    (r"presentation_spec", "MİİS istifadəçi görünüşlərinin spesifikasiyası"),
    (r"noar_constructs", "Gecikmə ehtiva edən, lakin avtoreqressiv olmayan konstruksiyalar"),
    (r"holdout|backtest", "Nümunədən kənar yoxlama: RMSE, Theil U, DM testləri"),
    (r"fan|band_meta", "Qeyri-müəyyənlik zolaqları (kvantillər)"),
    (r"identity_checks", "Hesab eyniliklərinin yoxlaması"),
    (r"equation_audit|coefficients|elasticit|fe_estimates|iv_dwh|chow|collinearity|determinants", "Qiymətləndirmə nəticələri və diaqnostika"),
    (r"rejected_spec|selection|specification", "Spesifikasiya seçimi və rədd edilmiş variantlar"),
    (r"sensitivity|levers|addfactor", "Həssaslıq təhlili və rıçaqlar"),
    (r"scenario", "Ssenarilər (Əsas / Mənfi / İslahat)"),
    (r"early_warning", "Erkən xəbərdarlıq göstəriciləri"),
    (r"plausibility|vs_history|last_actual", "Ağlabatanlıq: proqnoz öz tarixi ilə müqayisədə"),
    (r"forecast|nowcast", "Proqnoz 2026–2030"),
    (r"history|dataset|annual_raw|workbook|panel|dsk_", "Tarixi məlumat (modelin girişi)"),
    (r"concentration|hhi|pcm|margins|barriers|merger", "Bazar strukturu və rəqabət göstəriciləri"),
    (r"multiplier", "Multiplikatorlar və ötürmə"),
    (r"accounts", "Sektor və bazar hesabları (real, deflyator, nominal)"),
]


def describe(name):
    stem = name[:-4]
    for pat, txt in RULES:
        if re.search(pat, stem, re.I):
            return txt
    return "Analitik cədvəl"


SECS = [("about", "Necə oxumalı")] + [(c.lower(), c) for c in nbinfo.ORDER]


def build(texts):
    o = ["<h1>Nəticələr və fayllar</h1>",
         '<p class="lead-in">Modulun bütün çıxış faylları — tələblər üzrə qruplaşdırılmış, hər birinin qısa təsviri və '
         "sətir sayı ilə. Siyahı yığım anında <code>MicroUnit/output/</code> qovluğundan qurulur; hər fayl adı birbaşa "
         "açılan keçiddir.</p>",
         html.h2("about", 1, "Necə oxumalı")]
    total = 0
    blocks = []
    for i, c in enumerate(nbinfo.ORDER, start=2):
        files = sorted(p.name for p in core.OUT.glob(f"{c}_*.csv"))
        total += len(files)
        rows = []
        for f in files:
            core.mark(core.OUT / f)
            syn = "_SYNTHETIC_" in f
            tag = " " + html.pill("gap", "SİNTETİK") if syn else ""
            rows.append([html.flink("output/" + f, ""), esc(describe(f)) + tag, v(core.nrows(f), 0)])
        blocks.append(html.h2(c.lower(), i, c))
        blocks.append(f'<p><a href="fr/{c.lower()}.html">{c} səhifəsi</a> · dəftər {html.chip(c + ".ipynb")} · '
                      f"{v(len(files), 0)} fayl.</p>")
        blocks.append(html.table(["Fayl", "Təsvir", "Sətir"], rows, cols=["c-wide", "c-text", "c-num"]))
    o.append(f"<p>Cəmi {v(total, 0)} CSV faylı. Sətir sayına başlıq sətri daxil deyil. <strong>SİNTETİK</strong> "
             "işarəli fayllar FR10/FR12-nin B qatının sintetik məlumatla nümayiş çıxışlarıdır: onlar su nişanı daşıyır və "
             'heç bir tapıntıda işlədilmir (<a href="synthetic.html">ətraflı</a>). Real məlumat yükləndikdə onların yerini '
             "<code>FR10_FIRM_*</code> və <code>FR12_FIRM_*</code> faylları tutur.</p>")
    o += blocks
    return "\n".join(o), SECS
