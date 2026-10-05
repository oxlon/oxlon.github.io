"""pg_data.py — data sources: workbook, DSK tables, FR10/FR12 source matrices, gaps, integrity findings."""
from . import core, html
from .core import v, esc, esc_az
from .labels import status, PILLAR_AZ

SECS = [("workbook", "Nazirliyin iş kitabı"), ("dsk", "DSK-dan toplanmış cədvəllər"), ("fr10-matrix", "FR10 mənbə matrisi"),
        ("fr12-matrix", "FR12 mənbə matrisi"), ("gaps", "Məlumat boşluqları"), ("integrity", "Məlumat bütövlüyü")]

WB = "data/Statistik data dinamika 05.06.2026 +.xlsx"
DSK = [("data/dsk", "FR4", "əmək bazarı: fəaliyyət növləri və mülkiyyət formaları üzrə məşğullar və muzdlu işçilər"),
       ("data/dsk_services", "FR5", "əhaliyə pullu xidmətlər: növlər üzrə dəyər, həcm indeksləri, regionlar"),
       ("data/dsk_enterprise", "FR10, FR12", "sənaye, milli hesablar, sahibkarlıq, statistik vahidlər"),
       ("data/dsk_competition", "FR12", "sahibkarlıq və reyestr cədvəlləri — cari və arxivləşdirilmiş buraxılışlar")]

# FR1–FR5 keep their integrity findings in the methodology documents (prose, not CSV); one-line summaries here.
INTEGRITY_DOCS = [
    ("FR1", "2.3", ["Büdcə xərclərinin eyniliyi borc xidməti daxil edilmədən ödənmir — üçtərəfli eynilik tətbiq olunur.",
                    "2006-dan əvvəl investisiyanın bölgüləri cəmlə uzlaşmır — investisiya tənlikləri 2006-dan başlayır.",
                    "Sənaye investisiyasında 1995–97 üzrə yalançı sıfırlar və 2024 üzrə uyğunsuzluq qeydə alınıb."]),
    ("FR3", "8.3", ["DVX sətirlərində təkrar blok aşkarlanıb; DSK və DVX orta əmək haqqını fərqli göstərir."]),
    ("FR4", "4", ["Məşğulluq Agentliyinin sıraları rəqəmsal qeydiyyata keçidlə qırılır — qiymətləndirmədə işlədilmir.",
                  "İş kitabının <code>priv_share</code> sırası özəl məşğulluq payı deyil.",
                  "Büdcə təşkilatlarının sayında 2025 enişi sətrin tərifinin dəyişməsi kimi görünür — təsdiq istənib.",
                  "DVX-də iki sətir bloku bayt-bayt təkrarlanır; iş kitabında iki fərqli işçi sayı sırası var."]),
    ("FR5", "5", ["1995-dən əvvəlki nominal dəyərlər köhnə manatla eyni sətirdədir.",
                  "Bəzi DSK xanaları mətn kimi saxlanılıb — xüsusi oxuyucu ilə həll olunub.",
                  "«Digər pullu xidmətlər» təsnifatca qeyri-sabitdir; zəncirvari həcmlər cəmə toplanmır.",
                  "Regional sıralar milli cəmlə uzlaşmır — hesabatda göstərilir, model girişi deyil."]),
]


def count_files(rel):
    p = core.UNIT / rel
    return sum(1 for f in p.rglob("*") if f.suffix.lower() in (".xls", ".xlsx") and f.is_file())


def workbook():
    p = core.mark(core.UNIT / WB)
    try:
        import openpyxl
        names = openpyxl.load_workbook(p, read_only=True).sheetnames
    except Exception:                       # noqa: BLE001
        names = []
    return names


def matrix(name, anchor):
    m = core.csv(name)
    rows = []
    for r in m.itertuples():
        cls, lab = status(r.status)
        rows.append([esc(r.id), esc(PILLAR_AZ.get(r.pillar, r.pillar)), esc(r.indicator_az),
                     f'<span class="src-en">{esc_az(r.source_institution)} · {esc_az(r.dataset_table_row)}</span>',
                     esc_az(r.years_available_now), html.pill(cls, lab),
                     f'<span class="src-en">{esc_az(r.presentation_form)}</span>'])
    sg = m.status_group.value_counts()
    head = (" · ".join(f"{html.pill(status(k)[0], status(k)[1])} {v(sg.get(k, 0), 0)}"
                       for k in ("available now", "requested", "not available")))
    return (f"<p>{v(len(m), 0)} göstərici: {head}. Mənbə: {html.flink('output/' + name, '')}.</p>"
            + html.table(["Kod", "Sütun", "Göstərici", "Mənbə · cədvəl/sətir", "Mövcud illər", "Status", "Təqdimat forması"],
                         rows, cols=["c-tight", "c-tight", "c-text", "c-text", "c-tight", "c-tight", "c-text"]))


def gaps(name):
    g = core.csv(name)
    alt = "alternative_proxy" if "alternative_proxy" in g.columns else "alternative_used_now"
    rows = [[f'<span class="src-en">{esc_az(getattr(r, c))}</span>' for c in ("gap", "impact", alt, "action_to_agree_with_Customer")]
            for r in g.itertuples()]
    return html.table(["Boşluq", "Təsiri", "İndi işlədilən alternativ", "Sifarişçi ilə razılaşdırılacaq addım"], rows,
                      cols=["c-text", "c-text", "c-text", "c-text"])


def findings(name):
    f = core.csv(name)
    rows = [[esc_az(r.id), f'<span class="src-en">{esc_az(r.finding)}</span>', f'<span class="src-en">{esc_az(r.consequence)}</span>']
            for r in f.itertuples()]
    return html.table(["Kod", "Tapıntı", "Nəticəsi"], rows, cols=["c-tight", "c-text", "c-text"])


def build(texts):
    sheets = workbook()
    dsk_rows = [[f"<code>{esc(rel)}/</code>", esc(mods), esc(what), v(count_files(rel), 0)] for rel, mods, what in DSK]
    o = ["<h1>Məlumat mənbələri</h1>",
         '<p class="lead-in">Modulun hansı məlumatı, hansı mənbədən, hansı göstərici üçün və hansı formada işlətdiyi; '
         "çatmayan məlumat və onun alternativləri; mənbələrdə aşkarlanan problemlər. FR10 və FR12 üçün tələb olunan mənbə "
         "matrisləri tam şəkildə verilir. Matris və tapıntı cədvəllərindəki mətnlər modulların tərcümə cədvəlləri (<code>FRx_strings_az.csv</code>) "
         "əsasında Azərbaycan dilində göstərilir.</p>",
         html.h2("workbook", 1, "Nazirliyin iş kitabı"),
         f"<p>{html.chip(WB)} — {v(len(sheets), 0)} vərəq. FR1–FR5-in əsas mənbəyi; FR10 və FR12 də onun "
         "regional, DVX, lisenziya və yoxlama vərəqlərini oxuyur. Vərəqlər: " + ", ".join(esc(s.strip()) for s in sheets) + ".</p>",
         html.h2("dsk", 2, "DSK-dan toplanmış cədvəllər"),
         "<p>İş kitabında olmayan məlumat Dövlət Statistika Komitəsinin saytından toplanıb və <code>data/</code> qovluğunda "
         "saxlanılır:</p>",
         html.table(["Qovluq", "Modul", "Məzmun", "Fayl"], dsk_rows, cols=["c-tight", "c-tight", "c-text", "c-num"]),
         "<p>FR10 və FR12 hər faylı manifestdə qeyd edir (<code>FR10_dsk_manifest.csv</code>, "
         "<code>FR12_dsk_manifest.csv</code>; FR12-də URL və SHA-256 ilə).</p>",
         html.h2("fr10-matrix", 3, "FR10 mənbə matrisi"),
         "<p>Tələbin istədiyi kimi: hansı məlumat, hansı mənbədən, hansı analitik göstərici üçün, istifadəçiyə hansı formada.</p>",
         matrix("FR10_data_source_matrix.csv", "fr10"),
         html.h2("fr12-matrix", 4, "FR12 mənbə matrisi"), matrix("FR12_data_source_matrix.csv", "fr12"),
         html.h2("gaps", 5, "Məlumat boşluqları və alternativlər"),
         html.h3("FR10"), gaps("FR10_data_gaps_and_alternatives.csv"),
         html.h3("FR12"), gaps("FR12_data_gaps_and_alternatives.csv"),
         html.h2("integrity", 6, "Məlumat bütövlüyü tapıntıları"),
         "<p>Qiymətləndirmədən əvvəl hər modul öz mənbələrini yoxlayıb; tapılan problemlər düzəldilməyib, qeydə alınıb və "
         "modelin onlara reaksiyası yazılıb.</p>"]
    for code, sec, items in INTEGRITY_DOCS:
        core.mark(core.DOCS / f"{code}_Methodology.md")
        o.append(html.h3(f"{code} — metodologiya sənədi, §{sec}"))
        o.append("<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"
                 f"<p>Ətraflı: {html.doc_links(code, '')}.</p>")
    o += [html.h3("FR10"), findings("FR10_data_integrity_findings.csv"),
          html.h3("FR12"), findings("FR12_data_integrity_findings.csv")]
    return "\n".join(o), SECS
