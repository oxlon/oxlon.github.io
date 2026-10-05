"""fr12_text.py — FR12 prose blocks (numbers injected from the outputs)."""
from . import html, common
from .core import v, esc, num
from .labels import status, GROUP_AZ

PANEL_AZ = {"activity": "fəaliyyət qrupları", "region": "regionlar", "sme": "KOS payı"}
METRIC_AZ = {"entry rate, % (births / identity stock)": "giriş əmsalı, %", "log births": "doğumlar (loq)",
             "exit rate, %": "çıxış əmsalı, %", "log-odds SME output share": "KOS buraxılış payı (log-odds)"}
FLAG_AZ = {"F_conc": "konsentrasiya", "F_entry": "giriş", "F_exit": "çıxış", "F_mob": "pay mobilliyi",
           "F_margin_entry": "marja ↑, giriş ↓"}


def model(d):
    return ("<p><strong>Niyə «rəqabət strategiyası» birbaşa qiymətləndirilmir.</strong> Strategiya — xərc liderliyi, "
            "fərqləndirmə, gizli sövdələşmə, girişin qarşısının alınması — rəhbərliyin niyyətidir və heç bir statistik "
            "mənbədə qeyd olunmur. Nazirliyin 24 avqust 2026 tövsiyəsinə uyğun olaraq FR12 strategiyaların özünü deyil, "
            "onların müşahidə olunan izlərini ölçür: giriş əmsalı və girənlərin ölçüsü, çıxış və sağ qalma, bazar "
            "paylarının qeyri-sabitliyi, qiymət-xərc marjası və Boone göstəricisi, HHI və CR4/CR8.</p>"
            "<p><strong>A qatı (işlək)</strong> — 11 DSK fəaliyyət qrupu, 19 NACE bölməsi, 14 iqtisadi region və vergi "
            "ödəyicilərinin ölçü qrupları üzrə aqreqat məlumat (DSK statistik reyestri, sahibkarlıq cədvəlləri, arxivləşdirilmiş "
            "DSK buraxılışları, iş kitabı, FR1 və FR10 çıxışları). <strong>B qatı</strong> — müəssisə × NACE bölməsi × region × il "
            "səviyyəsində rəqabət mühərriki; DSK biznes reyestri tələb olunub, cavab gələnə qədər sintetik fayl üzərində.</p>"
            "<p><strong>Giriş/çıxış modeli.</strong> Doğumlar (yeni qeydiyyatlar) vahid effektləri olan loq modeli ilə, say "
            "eynilik N<sub>t</sub> = (N<sub>t−1</sub> + B<sub>t</sub>) / (1 + x<sub>t</sub>) ilə, giriş əmsalı B/N kimi "
            "qurulur. Hər panel üzrə cəmi beş il olduğundan qayda — sürücülər, lövbər, rejim (struktur / sıfır modellə "
            "kombinasiya / sıfır model) — kəsimdən əvvəlki məlumatla seçilir və hər başlanğıcda yenidən tətbiq olunur; "
            "struktur model qalib gəlmədikdə sıfır modellə kombinasiya işlədilir. Əmsallar sərhədli nisbətlər olduğundan "
            "DOLS və Engle–Granger tətbiq edilmir (bu açıq yazılır).</p>")


def data(d, pre):
    m = d["mat"]
    sg = m.status_group.value_counts()
    chips = " ".join(f'{html.pill(status(k)[0], status(k)[1])} {v(sg.get(k, 0), 0)}'
                     for k in ("available now", "requested", "not available"))
    return (f"<p>{v(len(d['man']), 0)} giriş faylı manifestdə URL və SHA-256 ilə qeyd olunub (<code>FR12_dsk_manifest.csv</code>); "
            "DSK sahibkarlıq cədvəlləri yalnız son iki ili nəşr etdiyi üçün arxiv buraxılışları bərpa edilib. Mənbə matrisi "
            f"{v(len(m), 0)} göstərici: {chips}. Tam matris, {v(len(d['gaps']), 0)} boşluq və {v(len(d['find']), 0)} "
            f"məlumat bütövlüyü tapıntısı: <a href=\"{pre}data.html#fr12-matrix\">Məlumat mənbələri → FR12</a>. "
            "Üç müəssisə populyasiyası (sahibkarlıq subyektləri, statistik vahidlər, aktiv vergi ödəyiciləri) heç vaxt bir "
            "əmsalda qarışdırılmır.</p>")


def scen_intro():
    return ("<p>Şəffaf, kalibrlənmiş Kurno alətləri: bazar HHI (simmetrik ekvivalent firma sayı N = 1/HHI), tələb "
            "elastikliyi ε və davranış parametri θ ilə təsvir olunur. Ssenarilər: (S1) giriş maneələrinin azaldılması, "
            "(S2) birləşmə, (S3) xərc şoku / vergi, (S4) idxal rəqabəti, (S5) dövlət müəssisəsi — qarışıq oliqopoliya. Hər "
            "nəticə tək rəqəm deyil, <strong>aralıqdır</strong>: HHI-nin aşağı və yuxarı hədləri × ε × θ üzrə; «mərkəzi» "
            "dəyər seçilmir. Mobil rabitə, bank və sement bazarları ictimai məlumatdan təxmini quruluşla kalibrlənib — "
            "bunlar <strong>illüstrativ fərziyyələrdir</strong> və tənzimləyici məlumatı ilə əvəz edilməlidir.</p>")


def scen_outro(d):
    m = d["merger"]
    rows = [[esc(GROUP_AZ.get(r.market, r.market)), f"{v(r.hhi_post_min, 0)} – {v(r.hhi_post_max, 0)}", v(r.d_hhi, 0),
             f'<span class="src-en">{esc(r.us)}</span>', f'<span class="src-en">{esc(r.eu)}</span>'] for r in m.itertuples()]
    return ("<p><strong>Birləşmə skrininqi (S2)</strong> — ABŞ 2010 və Aİ hədləri ilə:</p>"
            + html.table(["Bazar", "Birləşmədən sonra HHI", "ΔHHI", "ABŞ 2010", "Aİ"], rows,
                         cols=["c-tight", "c-num", "c-num", "c-text", "c-text"]))


def zf(z):
    return num(z, 0 if float(z).is_integer() else 1)


def warning(d):
    e = d["ew"]
    fl = d["fl"]
    rows = []
    for r in e.itertuples():
        raised = [lab for c, lab in FLAG_AZ.items() if str(getattr(r, c)).lower() in ("yes", "true")]
        rows.append([esc(GROUP_AZ.get(r.group, r.name)), ", ".join(raised) or "—", v(r.n_available, 0), v(r.score, 2),
                     html.pill("gap", "izləmədə") if bool(r.watch_list) else html.pill("done", "yox")])
    rw = fl[fl.null == "random walk"].set_index("z_threshold").false_listing_rate
    zstar = d["fl"].z_threshold.max()
    n_watch = int(e.watch_list.astype(bool).sum())
    return [f"<p>Hər bayraq son ortalamanı əvvəlki ilə müqayisə edir və göstəricinin həmin sektordakı öz dəyişkənliyi ilə "
            f"ölçülür (z). Hədd z* = {zf(zstar)} simulyasiya ilə seçilib: təsadüfi gəzişmə sıfır fərziyyəsi altında "
            f"dəyişməyən sektorun siyahıya düşmə ehtimalı ənənəvi z = {zf(rw.index.min())} üçün {v(rw.iloc[0] * 100, 1, pct=True)}, "
            f"z* üçün {v(rw.loc[zstar] * 100, 1, pct=True)} olur. Kompozit bal mövcud bayraqlar üzrə çəkili paydır. "
            f"İzləmə siyahısında hazırda {v(n_watch, 0)} sektor var; tək bayraqlar izlənilir.</p>",
            html.table(["Fəaliyyət qrupu", "Qaldırılmış bayraqlar", "Mövcud göstərici", "Bal", "İzləmə"], rows,
                       cols=["c-wide", "c-text", "c-num", "c-num", "c-tight"])]


def check(d):
    h = d["hold"]
    rows = [[esc(PANEL_AZ.get(r.panel, r.panel)), esc(METRIC_AZ.get(r.metric, r.metric)), esc(str(r.targets)), v(r.n, 0),
             common.u_cell(r.theil_rule_vs_rw), common.u_cell(r.theil_rule_vs_constant), v(r.dm_p_rule_vs_rw, 2),
             v(r.dm_p_rule_vs_constant, 2)] for r in h.itertuples()]
    return ["<p>Seçim yalnız 2022-yə qədərki məlumatla aparılıb; hold-out heç bir seçim üçün işlədilməyib (fəaliyyət: hədəf "
            "2024, regionlar: 2024–2025). Etalonlar: təsadüfi gəzişmə (son müşahidə) və sabit (təlim illərinin ortası). "
            "Hədəf illəri çox az olduğundan DM testi vahidlər üzrə cütləşdirilir və göstərici xarakterlidir.</p>",
            html.table(["Panel", "Göstərici", "Hədəf", "n", "U: təsadüfi gəzişmə", "U: sabit", "DM p (TG)", "DM p (sabit)"],
                       rows, cls="tbl tbl-dense tbl-backtest",
                       cols=["c-tight", "c-text", "c-tight", "c-num", "c-num", "c-num", "c-num", "c-num"]),
            "<p><strong>Açıq nəticə.</strong> Giriş əmsalı qaydaları hər iki paneldə təsadüfi gəzişməni üstələyir; doğumların "
            "özündə isə fəaliyyət qaydası təsadüfi gəzişməyə yaxındır və sabitdən bir qədər pisdir — qazanc sürücüdən "
            "deyil, axın və sayın birgə modelləşdirilməsindən gəlir. Regional çıxış və KOS payı qaydaları təsadüfi gəzişməni "
            "üstələmir. Təsadüfi gəzişmə yalnız etalondur: son dəyərlə proqnoz Sifarişçinin istisna etdiyi öz tarixindən "
            f"proqnozdur. {v(int(d['ident'].passed.sum()), 0)}/{v(len(d['ident']), 0)} hesab yoxlaması keçir.</p>"]


def layerb(d, pre):
    c = d["cal"]
    rows = [[f'<span class="src-en">{esc(r.target)}</span>', f'<span class="src-en">{esc(r.dimension)}</span>',
             f'<span class="src-en">{esc(r.status)}</span>', v(r.cells, 0), v(r.max_abs_rel_error_pct, 2)] for r in c.itertuples()]
    sw = d["swap"]
    pp = d["pipe"]
    return ("<p>Sintetik reyestr DSK aqreqatlarına kalibrlənib (bölmələr və regionlar üzrə doğulan və ləğv edilən vahidlər, "
            "2025 sonuna say, bölmələr üzrə buraxılış, KOS payları). Kalibrləmə xətaları bunu yoxlayır — bu, "
            "Azərbaycan müəssisələri haqqında tapıntı deyil, faylın DSK cəmlərini düzgün təkrarladığının sübutudur:</p>"
            + html.table(["Hədəf", "Ölçü", "Status", "Xana", "Maks. nisbi xəta, %"], rows,
                         cols=["c-text", "c-tight", "c-text", "c-num", "c-num"])
            + f"<p>Boru xətti testləri: {v(int(pp.passed.sum()), 0)}/{v(len(pp), 0)} keçir; əvəzetmə testləri: "
            f"{v(int(sw.passed.sum()), 0)}/{v(len(sw), 0)} keçir; validator hesabatında {v(len(d['val']), 0)} sətir. "
            f"Testlərin tam cədvəli və faylın əvəz edilməsi: <a href=\"{pre}synthetic.html#replace\">Sintetik məlumat</a>.</p>")


LIMITS = ["Hər fəaliyyət qrupu və region üzrə cəmi beş illik müşahidə: seçim və hold-out testlərinin gücü çox aşağıdır, "
          "uyğunluq yoxlaması zəifdir, zolaqlar hər üfüq üzrə 1–4 tarixi xəta cütünə əsaslanır.",
          "006 cədvəlində 2022 tərif dəyişikliyi üç illik məlumatla qiymətləndirilən bir qırılma termi ilə nəzərə alınır.",
          "Fəaliyyət paneli bazara girişi deyil, qeydiyyatları (fərdi sahibkarlar daxil) sayır; reyestrdən çıxış bazardan "
          "çıxışı azaldır (fəaliyyətsiz vahidlər qeydiyyatda qalır).",
          "Fəaliyyət qrupları antiinhisar bazarlarından xeyli genişdir; A qatında konsentrasiya ölçülmür, hədlərlə verilir.",
          "Sənaye iqtisadiyyatı ssenariləri qiymətləndirmə deyil, açıq fərziyyələrlə kalibrləmədir; davranış parametri və "
          "elastikliklər əsas qeyri-müəyyənlik mənbəyidir və açıq dəyişdirilir.",
          "B qatı sintetik məlumatla işləyir: o, boru xəttini sübut edir, Azərbaycan müəssisələri haqqında heç bir faktı yox."]
