"""pg_synth.py — the synthetic firm panel and business register, and how the Ministry replaces them."""
import pandas as pd

from . import core, html, synth
from .core import v, esc, esc_az

SECS = [("what", "Nə sintetikdir"), ("calibration", "Nəyə kalibrlənib"), ("replace", "Faylın əvəz edilməsi"),
        ("columns", "Sütunlar (sxem)"), ("tests", "Əvəzetmə testləri"), ("privacy", "Məxfilik")]

FP = "data/firm_panel/"
BR = "data/business_register/"


def _map(rel):
    p = core.mark(core.UNIT / rel)
    m = pd.read_csv(p)
    return m.rename(columns={"field_en": "column_en", "field_az": "column_az"})


def tests_table(name):
    rows = [[f'<span class="src-en">{esc_az(t)}</span>', html.pill("done", "keçdi") if ok else html.pill("gap", "keçmədi"),
             f'<span class="src-en">{esc_az(det)}</span>'] for t, ok, det in synth.swap_rows(name)]
    return html.table(["Test (çıxış faylından, ingiliscə)", "Nəticə", "Təfərrüat"], rows, cols=["c-text", "c-tight", "c-text"])


def build(texts):
    p, r = synth.panel(), synth.register()
    core.raw(FP + "README_FR10_firm_panel.md")
    core.raw(BR + "README_FR12_business_register.md")
    cal = core.csv("FR12_SYNTHETIC_calibration_errors_summary.csv")
    exact = int(cal.status.str.startswith("exact").sum())
    m10, m12 = _map(FP + "FR10_firm_panel_column_map.csv"), _map(BR + "FR12_business_register_column_map.csv")
    req10 = m10[m10.required.astype(str) == "True"].column_en.tolist()
    req12 = m12[m12.required.astype(str) == "True"].column_en.tolist()
    o = ["<h1>Sintetik məlumat və onun əvəz edilməsi</h1>",
         html.synth_banner("", "FR10 müəssisə paneli və FR12 biznes reyestri <strong>uydurma</strong> fayllardır: onlarda heç "
                           "bir real müəssisə, VÖEN və ya real rəqəm yoxdur."),
         '<p class="lead-in">Nazirlik müəssisə məlumatını layihə ilə paylaşmır — öz məlumatını öz sistemində yükləyəcək. '
         "Ona görə FR10 və FR12-nin müəssisə səviyyəsində mühərrikləri (B qatı) eyni sxemdə sintetik fayllarla təhvil "
         "verilir. Bu səhifə onların nə olduğunu, nəyə kalibrləndiyini və Nazirliyin onları necə əvəz edəcəyini göstərir.</p>",
         '<p class="box">Sintetik məlumatla qiymətləndirilmiş bütün müəssisə səviyyəsi modelləri (model kartları, '
         'əmsallar, marjinal effektlər, ROC, sağ qalma əyriləri, parametr bərpası): '
         '<a href="fr/fr10-sintetik.html">FR10 · Sintetik B qatı</a> · <a href="fr/fr12-sintetik.html">FR12 · Sintetik B qatı</a>. '
         'Real faylı yükləmək: <a href="api.html#yukle">API və avtomatlaşdırma</a>.</p>',
         html.h2("what", 1, "Nə sintetikdir"),
         html.table(["", "FR10 müəssisə paneli", "FR12 biznes reyestri"], [
             ["Fayl", f"<code>{FP}FR10_firm_panel_SYNTHETIC.csv / .xlsx</code>", f"<code>{BR}FR12_business_register_SYNTHETIC.csv / .xlsx</code>"],
             ["Sətir", v(p["rows"], 0), v(r["rows"], 0)],
             ["Müəssisə / qeyd", f"{v(p['firms'], 0)} uydurma müəssisə", f"{v(r['records'], 0)} qeyd ({r['last']}: {v(r['active'], 0)} aktiv müəssisəni təmsil edir)"],
             ["NACE", f"{v(p['nace'], 0)} bölmə (2 rəqəmli)", f"{v(r['sections'], 0)} seksiya, {v(r['nace'], 0)} bölmə"],
             ["Region / illər", f"{v(p['regions'], 0)} region, {p['y0']}–{p['y1']}", f"{v(r['regions'], 0)} region, {r['y0']}–{r['y1']}"],
             ["Sütun", v(p["cols"], 0), v(r["cols"], 0)],
             ["Hər sətrin ilk sütunu", f"<code>{esc(p['marker'])}</code>" + (" (bütün sətirlərdə)" if p["all_marked"] else ""),
              f"<code>{esc(r['marker'])}</code>" + (" (bütün sətirlərdə)" if r["all_marked"] else "")],
             ["Çıxışlar", "<code>output/FR10_SYNTHETIC_*.csv</code> (su nişanlı)", "<code>output/FR12_SYNTHETIC_*.csv</code> (su nişanlı)"]],
             cols=["c-tight", "c-text", "c-text"]),
         "<p>Sintetik fayllardan alınan nəticələr yalnız <strong>boru xəttinin texniki nümayişidir</strong>: onlar heç bir "
         "tapıntıda işlədilmir və bu saytda qrafik və ya cədvəl şəklində təhlil nəticəsi kimi göstərilmir. FR12-də hər "
         "müəssisə identifikatoru <code>SYN-</code> ilə başlayır" + (" (yoxlanılıb)" if r["syn_ids"] else "") + "; xlsx fayllar "
         "qalın xəbərdarlıqlı README vərəqi ilə açılır.</p>",
         html.h2("calibration", 2, "Nəyə kalibrlənib"),
         "<p><strong>FR10 paneli</strong> təsadüfi yaradılıb, lakin DSK sahə aqreqatları ilə uzlaşdırılıb: müəssisələrin "
         "sayı, buraxılış, işçilərin sayı və əmək haqqı. Boru xətti testləri müəssisə gəlirlərinin DSK sahə buraxılışına, "
         "müəssisə saylarının DSK aktiv müəssisə sayına bərabər olduğunu yoxlayır (FR10 səhifəsi, B qatı).</p>"
         "<p><strong>FR12 reyestri</strong> DSK aqreqatlarına kalibrlənib: bölmələr və regionlar üzrə doğulan və ləğv "
         "edilən vahidlər, 2025 sonuna say, bölmələr üzrə buraxılış, KOS payları; ölçü qrupları 1 iyul 2026 vəziyyətinə "
         f"təxmini uyğunlaşdırılıb. {v(len(cal), 0)} kalibrləmə hədəfindən {v(exact, 0)}-i «dəqiq» statusundadır "
         "(<code>FR12_SYNTHETIC_calibration_errors_summary.csv</code>). Mikro və kiçik müəssisələr qruplaşdırılıb: "
         "<code>weight</code> sütunu sətrin neçə eyni müəssisəni təmsil etdiyini göstərir.</p>",
         html.h2("replace", 3, "Faylın əvəz edilməsi"), steps(),
         html.h2("columns", 4, "Sütunlar (sxem)"),
         f"<p>FR10: {v(len(m10), 0)} sütun, onlardan {v(len(req10), 0)}-i məcburi; FR12: {v(len(m12), 0)} sütun, "
         f"{v(len(req12), 0)}-i məcburi. Başlıqlar ingilis və ya Azərbaycan dilində ola bilər; tam xəritə "
         f"(EN ↔ AZ ↔ tip ↔ vahid ↔ məcburilik ↔ mənbə) {html.flink(FP + 'FR10_firm_panel_column_map.csv', '')} və "
         f"{html.flink(BR + 'FR12_business_register_column_map.csv', '')} fayllarındadır.</p>",
         colmap(m12, "FR12 biznes reyestri — sütunlar"),
         html.h2("tests", 5, "Əvəzetmə testləri"),
         "<p>Dəftərlər real faylın yüklənməsini müvəqqəti qovluqda sınaqdan keçirir: real adlı fayl, Azərbaycan dilində "
         "başlıqlar, mühit dəyişəninin prioriteti, qırıq fayllar (çatmayan sütun, mənfi gəlir, balans uyğunsuzluğu).</p>",
         html.h3("FR10 — müəssisə paneli"), tests_table("FR10_firm_panel_swap_tests.csv"),
         html.h3("FR12 — biznes reyestri"), tests_table("FR12_business_register_swap_tests.csv"),
         html.h2("privacy", 6, "Məxfilik"),
         "<p>Müəssisə identifikatorları psevdonimləşdirilmiş qalmalıdır (VÖEN yox). Real məlumatla nəticələr yalnız "
         "Nazirliyin öz sistemində saxlanılır; real adlı faylı bu layihəyə köçürməyin. Sintetik generator heç vaxt real "
         f"adlı fayl yazmır. README faylları: {html.flink(FP + 'README_FR10_firm_panel.md', '')}, "
         f"{html.flink(BR + 'README_FR12_business_register.md', '')}.</p>"]
    return "\n".join(o), SECS


def steps():
    li = [
        f"Real faylı eyni sxemdə saxlayın: <code>{FP}FR10_firm_panel.csv</code> və ya <code>.xlsx</code> (vərəq "
        f"<code>data</code>); <code>{BR}FR12_business_register.csv</code> və ya <code>.xlsx</code>.",
        "Və ya faylın yolunu mühit dəyişənində verin: <code>FIRM_PANEL_PATH</code> (FR10), <code>BUSREG_PATH</code> (FR12). "
        "Prioritet: mühit dəyişəni → real adlı fayl → sintetik fayl.",
        f"Şablondan başlayın: {html.flink(FP + 'FR10_firm_panel_TEMPLATE.csv', '')}, "
        f"{html.flink(BR + 'FR12_business_register_TEMPLATE.csv', '')} (və .xlsx); nümunə sətrini silin. Başlıqlar "
        "ingilis və ya Azərbaycan dilində ola bilər; FR12-də <code>weight</code> sütunu buraxıla bilər (1 sayılır).",
        "<code>data_status</code> sütunu olmayan və ya dəyəri sintetik işarədən fərqli olan fayl REAL sayılır.",
        "<code>FR10.ipynb</code> / <code>FR12.ipynb</code> dəftərini yenidən icra edin. Banner "
        "<code>DATA_MODE = REAL</code> çap edir.",
        "Validator <code>output/FR10_firm_panel_validation_report.csv</code> və "
        "<code>output/FR12_business_register_validation_report.csv</code> fayllarına hər səhvi sətir və sahə üzrə yazır; "
        "ciddi səhvlər icranı dayandırır, xəbərdarlıqlar dayandırmır.",
        "Çıxışlar <code>FR10_FIRM_*.csv</code> və <code>FR12_FIRM_*.csv</code> adlanır (su nişanı olmadan) və sintetik "
        "çıxışların yerini tutur. A qatının nəticələri dəyişmir. Sonra <code>python3 site/build_site.py</code>."]
    return "<ol>" + "".join(f"<li>{x}</li>" for x in li) + "</ol>"


def colmap(m, title):
    rows = [[f"<code>{esc(r.column_en)}</code>", esc(r.column_az),
             html.pill("done", "məcburi") if str(r.required) == "True" else html.pill("neutral", "könüllü")]
            for r in m.itertuples()]
    return html.h3(title) + html.table(["Sütun (EN)", "Sütun (AZ)", ""], rows, cols=["c-tight", "c-text", "c-tight"])
