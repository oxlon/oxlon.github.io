"""pg_api.py — api.html: a plain-language summary of api/OXUYUN.md (uploading data, autonomous runs,
the one-click launcher, scenarios, reports). The full guide is linked, not copied."""
from . import core, html, v2nav
from .core import esc

SECS = [("baslat", "Bir kliklə işə salmaq"), ("yukle", "Məlumat yükləmək"), ("avtonom", "Avtonom rejim"),
        ("icra", "Modelləri yenidən icra etmək"), ("ssenari", "Ssenarilər və hesabatlar"),
        ("miis", "MİİS ilə inteqrasiya"), ("tehlukesizlik", "Təhlükəsizlik")]

KINDS = [("workbook", "Nazirliyin iş kitabı (<code>Statistik data dinamika *.xlsx</code>)", "FR1 və bütün asılı modullar"),
         ("dsk", "DSK cədvəli (<code>.xls</code>)", "FR4, FR5, FR10, FR12 — faylın bölməsinə görə"),
         ("firm_panel", "FR10 müəssisə paneli (<code>.csv</code> / <code>.xlsx</code>)", "FR10 (B qatı sintetikdən reala keçir)"),
         ("business_register", "FR12 biznes reyestri (<code>.csv</code> / <code>.xlsx</code>)", "FR12 (B qatı)"),
         ("series", "Ayrı müşahidələr (JSON)", "yalnız saxlanılır, dəftərlərin girişi deyil")]


def build(texts):
    core.mark(core.UNIT / "api" / "OXUYUN.md")
    pre = ""
    rows = [[f"<code>{k}</code>", w, esc(s)] for k, w, s in KINDS]
    o = ["<h1>API və avtomatlaşdırma</h1>",
         '<p class="lead-in">Modul yalnız bu sayt deyil: onun məlumatını yeniləmək, modelləri yenidən icra etmək və '
         "nəticələri Nazirliyin sistemlərinə ötürmək üçün yerli server və JSON API var. Bu səhifə ən vacib addımları "
         f"sadə dillə izah edir; texniki təfərrüat {html.flink('api/OXUYUN.md', pre, 'api/OXUYUN.md')} sənədində, "
         f"müqavilə {html.flink('api/openapi.yaml', pre, 'api/openapi.yaml')} faylındadır.</p>",
         html.h2("baslat", 1, "Bir kliklə işə salmaq"),
         "<p>Modulun qovluğunda iki başladıcı fayl var: <strong>macOS</strong> üçün "
         f"{html.flink('MikroModel_Baslat.command', pre, 'MikroModel_Baslat.command')}, <strong>Windows</strong> üçün "
         f"{html.flink('MikroModel_Baslat.bat', pre, 'MikroModel_Baslat.bat')}. İki dəfə klikləyin — server başlayır və "
         "brauzerdə <code>http://127.0.0.1:8790/panel/</code> açılır. Server işləyəndə İş panelinin ssenari qurucusu "
         "canlı hesablayır; server olmadan (fayl kimi açılanda) panel və bu sayt yalnız hazır nəticələri göstərir.</p>",
         html.table(["Ünvan", "Nədir"], [["<code>/</code>", "Mərkəz səhifəsi"], ["<code>/panel/</code>", "İş paneli"],
                                         ["<code>/site/</code>", "Klassik görünüş (bu sayt)"],
                                         ["<code>/api/v1/…</code>", "JSON API"]], cols=["c-tight", "c-text"]),
         f'<p><a href="{pre}{v2nav.PANEL}">İş panelini aç →</a> · <a href="{pre}{v2nav.PANEL_SCEN}">Ssenari qurucusu →</a> · '
         f'<a href="{pre}{v2nav.PANEL_REPORT}">Hesabat qurucusu →</a></p>',
         html.h2("yukle", 2, "Məlumat yükləmək"),
         "<p>Yeni məlumat iki addımla daxil edilir: <strong>yükləmə və yoxlama</strong>, sonra <strong>tətbiq</strong>. "
         "Hər fayl dəftərlərin öz qaydaları ilə yoxlanılır (vərəqlər, ünvanlar, vahidlər, illər, məcburi sütunlar, "
         "təkrarlar); səhvlər sətir və sahə üzrə Azərbaycan dilində qaytarılır. Rədd edilən fayl heç nəyi dəyişmir. "
         "Tətbiq zamanı köhnə fayl <code>data/_replaced/</code> qovluğuna köçürülür — istənilən vaxt geri qaytarmaq olar.</p>",
         html.table(["Növ", "Fayl", "Hansı modullara təsir edir"], rows, cols=["c-tight", "c-text", "c-text"]),
         "<p>Sintetik nişanlı fayllar (<code>*_SYNTHETIC*</code>, <code>*_TEMPLATE*</code>) heç vaxt əvəz edilmir və "
         "sintetik nişanlı panel real məlumat kimi qəbul olunmur.</p>",
         html.h2("avtonom", 3, "Avtonom rejim"),
         "<p>Server bir qovluğu izləyə bilər: ora atılan fayl özü tanınır (adına görə), yoxlanılır, tətbiq olunur və "
         "təsirlənən modullar yenidən icra edilir. Qəbul edilən fayl <code>_applied/</code>, rədd edilən "
         "<code>_rejected/</code> alt qovluğuna köçürülür, yanında Azərbaycan dilində hesabat qalır. Əlavə olaraq hər gün "
         "müəyyən saatda tam icra və DSK saytından cədvəllərin yenilənməsi (yalnız dəyişiklik olduqda icra) qurula bilər.</p>",
         "<pre>python3 api/server.py --watch data/inbox_drop --auto-run \\\n    --poll 30 --schedule 06:30 --dsk-refresh --snapshot</pre>",
         "<p>Serveri kompüter açılanda başlatmaq üçün macOS-da <code>launchd</code>, Windows-da tapşırıq planlayıcısı "
         "(Task Scheduler) istifadə olunur.</p>",
         html.h2("icra", 4, "Modelləri yenidən icra etmək"),
         "<p><code>run_all.py</code> altı dəftəri asılılıq ardıcıllığı ilə icra edir (FR1 → FR3 → FR4 → FR5 → FR10 → FR12), "
         "sonra İş panelini və bu saytı yenidən yığır. İlk xətada dayanır — asılı modullar köhnə girişlərlə icra edilmir. "
         "Hər icranın jurnalı, girişlərin və çıxışların yoxlama cəmləri və əvvəlki icra ilə bayt-bayt müqayisə "
         "<code>logs/</code> qovluğunda saxlanılır.</p>",
         "<pre>python3 run_all.py                 # hamısı\npython3 run_all.py --stage FR4     # FR4 və asılıları\n"
         "python3 run_all.py --dry-run       # plan, icrasız</pre>",
         html.h2("ssenari", 5, "Ssenarilər və hesabatlar"),
         "<p>Ssenari qurucusu ekzogen fərziyyələri (2026–2030), qiymətləndirilmiş əmsalları (standart xəta və 95 % "
         "etibarlılıq intervalı daxilində) və modul rıçaqlarını dəyişməyə imkan verir. FR1-dəki dəyişiklik zəncirvari "
         "olaraq FR3, FR4, FR5, FR10 və FR12-yə ötürülür. Ssenarilər saxlanılır, açılır, surəti çıxarılır və JSON kimi "
         "ixrac olunur. Hesabat qurucusu seçilmiş modullar, göstəricilər, ssenarilər və illər üzrə PDF (çap), Excel, "
         "Word və CSV hesabatı hazırlayır.</p>",
         html.h2("miis", 6, "MİİS ilə inteqrasiya"),
         "<ol><li>MİİS yeni faylı göndərir və yoxlama hesabatını alır.</li><li>Fayl tətbiq olunur və icra başlayır.</li>"
         "<li>İcranın vəziyyəti izlənilir; «ok» olduqda proqnozlar və tənliklər API ilə götürülür.</li></ol>"
         "<p>Göstərici identifikatorları sabitdir: <code>fr&lt;k&gt;:&lt;kod&gt;</code> (məsələn, <code>fr1:rgdp</code>); "
         "kataloq hər modulun <code>FRx_indicator_catalog.csv</code> faylındadır. FR10/FR12 nəticələri sintetik "
         "məlumatla işlədikcə «SİNTETİK» nişanlıdır.</p>",
         html.h2("tehlukesizlik", 7, "Təhlükəsizlik"),
         "<ul><li>Oxu və yazı nişanları mühit dəyişəni ilə verilir; standart sınaq nişanları ilə server "
         "şəbəkəyə açılmır — istehsalda mütləq dəyişdirin.</li><li>İstehsalda server HTTPS ilə əks proksi arxasında "
         "işlədilir.</li><li>Statik fayllar yalnız <code>panel/</code> və <code>site/</code> qovluqlarından verilir; yükləmə "
         "ölçüsü məhdudlaşdırılıb.</li></ul>"]
    return "\n".join(o), SECS
