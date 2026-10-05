"""fr12.py — FR12 page: competition environment."""
from . import html, req, common, synth
from .core import v, esc, esc_az
from .common import SCEN
from .labels import GROUP_AZ, CHANGE_AZ
from . import fr12_data as D
from . import fr12_text as T

SECTIONS = [("teleb", "Tələb"), ("model", "Model: A və B qatları"), ("data", "Məlumat"),
            ("results", "Giriş və çıxış: nəticələr"), ("scenarios", "Ssenari təhlili (sənaye iqtisadiyyatı)"),
            ("warning", "Erkən xəbərdarlıq"), ("check", "Yoxlama"), ("layerb", "B qatı — sintetik"),
            ("limits", "Məhdudiyyətlər"), ("files", "Fayllar")]


def build(t, pre="../"):
    d = D.load()
    o = ["<h1>FR12 — Rəqabət mühiti: intensivlik, giriş və çıxış, ssenarilər, erkən xəbərdarlıq</h1>",
         html.kicker("FR12", "FR12.ipynb", "docs/FR12_Methodology.md"),
         common.intro("Sektorlar üzrə rəqabət intensivliyi, müəssisələrin bazara giriş və çıxış tezliyi və onların "
                      "2030-a qədər proqnozu, siyasət dəyişikliklərinin sənaye iqtisadiyyatı əsasında ssenari təhlili və "
                      "rəqabətin pisləşdiyi sektorlar üçün erkən xəbərdarlıq. Müəssisə səviyyəsində rəqabət mühərriki "
                      "(B qatı) DSK biznes reyestri gələnə qədər <strong>sintetik</strong> fayl üzərində işləyir."),
         html.h2("teleb", 1, "Tələb"), req.block("FR12", t),
         html.h2("model", 2, "Model: A və B qatları"), T.model(d),
         html.h2("data", 3, "Məlumat"), T.data(d, pre)]
    o += results(d)
    o += scenarios(d)
    o += [html.h2("warning", 6, "Erkən xəbərdarlıq")] + T.warning(d)
    o += [html.h2("check", 7, "Yoxlama")] + T.check(d)
    s = synth.register()
    o += [html.h2("layerb", 8, "B qatı — müəssisə səviyyəsində rəqabət mühərriki (sintetik)"),
          html.synth_banner(pre, f"<code>data/business_register/FR12_business_register_SYNTHETIC.csv</code> — "
                            f"{v(s['rows'], 0)} sətir, {v(s['records'], 0)} uydurma qeyd ({s['last']}-ci ildə "
                            f"{v(s['active'], 0)} aktiv müəssisəni təmsil edir), {v(s['sections'], 0)} NACE bölməsi, "
                            f"{v(s['regions'], 0)} region, {s['y0']}–{s['y1']}."),
          T.layerb(d, pre)]
    o += [html.h2("limits", 9, "Məhdudiyyətlər"), "<p>Metodologiya sənədinin 19-cu bölməsindən.</p>",
          common.limits_list(T.LIMITS)]
    o.append(common.files_section(10, "FR12", pre))
    return "\n".join(o)


def results(d):
    b = d["fc_all"]["Baseline"]
    f = d["fall"]
    rows = [("Giriş əmsalı", "%", [v(b.loc[y, "entry"], 2) for y in common.YEARS],
             common.band_txt(f.loc[2030, "entry_p5"], f.loc[2030, "entry_p95"], 2)),
            ("Çıxış əmsalı", "%", [v(b.loc[y, "exit"], 2) for y in common.YEARS],
             common.band_txt(f.loc[2030, "exit_p5"], f.loc[2030, "exit_p95"], 2)),
            ("Yeni qeydiyyatlar", "vahid", [v(b.loc[y, "new"], 0) for y in common.YEARS],
             common.band_txt(f.loc[2030, "new_p5"], f.loc[2030, "new_p95"], 0)),
            ("Qeydiyyatdakı subyektlər", "vahid", [v(b.loc[y, "N"], 0) for y in common.YEARS],
             common.band_txt(f.loc[2030, "N_p5"], f.loc[2030, "N_p95"], 0))]
    fc = d["fc_all"]
    srows = [("Giriş əmsalı, 2030", "%", {s: v(fc[s].loc[2030, "entry"], 2) for s in SCEN}),
             ("Çıxış əmsalı, 2030", "%", {s: v(fc[s].loc[2030, "exit"], 2) for s in SCEN}),
             ("Yeni qeydiyyatlar, 2030", "vahid", {s: v(fc[s].loc[2030, "new"], 0) for s in SCEN}),
             ("Qeydiyyatdakı subyektlər, 2030", "vahid", {s: v(fc[s].loc[2030, "N"], 0) for s in SCEN})]
    return [html.h2("results", 4, "Giriş və çıxış: nəticələr"),
            html.fig("fr12_entry", "Bazara giriş əmsalı, bütün fəaliyyət sahələri", D.rate_fig(d, "entry", "giriş əmsalı, %"),
                     "Yeni qeydiyyatlar / ilin sonuna qeydiyyatdakı subyektlər. Doğumlar stabil qaldığı halda say artdığı "
                     "üçün əmsal azalır. 2021 nəşr olunmayıb; 2022-də DSK 006 cədvəlində tərif dəyişib (modeldə qırılma termi); 2025 hələ "
                     "nəşr olunmadığı üçün cari qiymətləndirmədir.",
                     "Pəncərə 2019–2030."),
            common.year_table(rows),
            html.fig("fr12_exit", "Bazardan çıxış əmsalı, bütün fəaliyyət sahələri", D.rate_fig(d, "exit", "çıxış əmsalı, %"),
                     "Reyestrdən çıxış bazardan çıxışı azaldır: fəaliyyətsiz vahidlər qeydiyyatda qalır.", "Pəncərə 2019–2030."),
            html.h3("Ssenarilər"), common.scen_table(srows),
            "<p>Giriş və çıxış FR1-in makro ssenarilərinə zəif reaksiya verir: seçilmiş qayda tələb sürücüsünü nəzərə alır, "
            "lakin onun təsiri kiçikdir; regionlar üzrə fərq daha böyükdür (<code>FR12_forecast_entry_exit.csv</code>).</p>",
            html.fig("fr12_groups", "Fəaliyyət qrupları üzrə giriş əmsalı: 2025 və 2030", D.groups_fig(d),
                     "Əsas ssenari; on bir DSK fəaliyyət qrupu.", "Mənbə: FR12_forecast_entry_exit.csv.")]


def scenarios(d):
    s = d["scen"]
    a = d["sass"]
    rows = []
    for i, r in enumerate(s.itertuples()):
        src = a.iloc[i].structure_source if i < len(a) else ""
        kind = html.pill("partial", "fərziyyə") if str(src).startswith("ASSUMPTION") else html.pill("done", "A qatı hədləri")
        rows.append([esc(r.scenario), esc(GROUP_AZ.get(r.market, r.market)), esc(CHANGE_AZ.get(a.iloc[i].change, a.iloc[i].change)),
                     f'<span class="src-en">{esc_az(r.assumption)}</span>', kind,
                     f"{v(r.hhi_min, 0)} – {v(r.hhi_max, 0)}", f"{v(r.d_price_min, 2)} … {v(r.d_price_max, 2)}",
                     f"{v(r.d_output_min, 2)} … {v(r.d_output_max, 2)}", f"{v(r.d_cs_pct_min, 2)} … {v(r.d_cs_pct_max, 2)}"])
    return [html.h2("scenarios", 5, "Ssenari təhlili (sənaye iqtisadiyyatı)"), T.scen_intro(),
            html.table(["", "Bazar", "Dəyişiklik", "Fərziyyə (çıxış faylından)", "Struktur", "HHI aralığı",
                        "Qiymət, %", "Buraxılış, %", "İstehlakçı izafisi, gəlirin %-i"], rows,
                       cols=["c-tight", "c-tight", "c-text", "c-text", "c-tight", "c-num", "c-num", "c-num", "c-num"]),
            T.scen_outro(d)]
