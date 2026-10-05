"""pg_index.py — landing page: scope, headline indicators, requirement grid, synthetic notice, how to run."""
from . import core, html, figs, synth, nbinfo
from .core import v, esc
from .common import YEARS
from . import fr1_data, fr3_data, fr4_data, fr5_data, fr10_data, fr12_data

SECS = [("what", "Əhatə"), ("headline", "Baş göstəricilər, 2026–2030"), ("fr-grid", "Altı tələb"),
        ("synthetic", "Sintetik məlumat haqqında"), ("run", "Modulun işə salınması")]


def headline_fig(d1):
    data = []
    for k, lab, col, bc in (("rgdp", "Real ÜDM", figs.ACCENT, figs.BAND),
                            ("rgdpnon", "Qeyri-neft ÜDM", figs.GREY, "rgba(95,99,104,0.10)")):
        fan = d1["fan"][k]
        h = d1["hist"][k]
        data += figs.band(fan.index, fan.p5, fan.p95, name=f"5–95 % zolağı: {lab}", color=bc)
        data.append(figs.line(list(h.index) + YEARS, list(h.values) + d1["scen"]["Baseline"][k], lab + ", real artım", col,
                              "solid", 2.6, hfmt=".1f"))
    return figs.spec(data, figs.layout("real artım, %", x0=2006))


def cards(d10, d12):
    p, r = synth.panel(), synth.register()
    syn10 = "SYNTHETIC" in str(p["marker"])
    syn12 = "SYNTHETIC" in str(r["marker"])
    return [
        ("FR1", "fr/fr1.html", "Sektorlar və bazarlar", "done", "qarşılanıb",
         "On iki DSK sektoru üzrə struktur tənliklər, eyni vaxtda həll olunan sistem, üç ssenari və zolaqlar."),
        ("FR3", "fr/fr3.html", "Orta aylıq əmək haqqı", "partial", "qismən",
         "Dövlət/qeyri-dövlət və neft/qeyri-neft üzrə proqnoz; sektorlar və büdcə/qeyri-büdcə üzrə orta əmək haqqı "
         "mənbələrdə yoxdur və bu açıq göstərilir."),
        ("FR4", "fr/fr4.html", "Məşğulluq", "done", "qarşılanıb",
         "Dörd bölgünün hamısı üzrə say və artım sürəti; sektor tərkibi iqtisadiyyata zəif reaksiya verir."),
        ("FR5", "fr/fr5.html", "Pullu xidmətlər", "done", "qarşılanıb",
         "Tələb sistemi: aqreqat həcm və on üç növ üzrə tərkib; test pəncərəsində təsadüfi gəzişməni üstələmir."),
        ("FR10", "fr/fr10.html", "Müəssisələr: maliyyə, effektivlik, bazar payı", "partial" if syn10 else "done",
         "A qatı işləkdir; B qatı sintetik" if syn10 else "qarşılanıb",
         f"Sahə, region, mülkiyyət və məhsul üzrə A qatı; {v(len(d10['mat']), 0)} göstəricilik mənbə matrisi; "
         "müəssisə mühərriki Nazirlik məlumatını gözləyir."),
        ("FR12", "fr/fr12.html", "Rəqabət mühiti", "partial" if syn12 else "done",
         "A qatı işləkdir; B qatı sintetik" if syn12 else "qarşılanıb",
         "Giriş/çıxış proqnozu, sənaye iqtisadiyyatı ssenariləri və erkən xəbərdarlıq; müəssisə səviyyəsi DSK biznes "
         "reyestrini gözləyir."),
    ]


def build(texts):
    d1, d3, d4, d5 = fr1_data.load(), fr3_data.load(), fr4_data.load(), fr5_data.load()
    d10, d12 = fr10_data.load(), fr12_data.load()
    rows = []
    for mod, d in ((fr1_data, d1), (fr4_data, d4), (fr3_data, d3), (fr5_data, d5), (fr10_data, d10), (fr12_data, d12)):
        for lab, unit, vals, band, dec, code in mod.headline(d):
            rows.append([f'{esc(lab)} <a href="fr/{code.lower()}.html" class="src-en">{code}</a>', esc(unit)]
                        + [v(x, dec) for x in vals] + [f"{v(band[0], dec)} … {v(band[1], dec)}"])
    tbl = html.table(["Göstərici", "Vahid"] + [str(y) for y in YEARS] + ["5–95 % zolağı, 2030"], rows,
                     cols=["c-wide", "c-tight"] + ["c-num"] * 5 + ["c-text"])
    grid = "".join(
        f'<div class="card"><div class="card-head"><span class="card-code">{c}</span>{html.pill(st, stl)}</div>'
        f'<a class="card-title" href="{href}">{esc(t)}</a><div class="card-line">{line}</div></div>'
        for c, href, t, st, stl, line in cards(d10, d12))
    p, r = synth.panel(), synth.register()
    o = ["<h1>MİİS §15.5.2 — Mikroiqtisadi təhlil və proqnozlaşdırma</h1>",
         '<p class="lead-in">İqtisadiyyat Nazirliyi üçün mikroiqtisadi modulun təqdimat saytı: altı funksional tələbin '
         "hər biri öz səhifəsində — tələb mətnindən modelə, məlumata, 2026–2030 proqnozuna, nümunədən kənar yoxlamaya və "
         "məhdudiyyətlərə qədər. Saytdakı hər rəqəm yığım anında modulun çıxış fayllarından oxunur.</p>",
         html.h2("what", 1, "Əhatə"),
         "<p>§15.5.2 alt-modulu Texniki Tapşırığın FR1, FR3, FR4, FR5, FR10 və FR12 tələblərini əhatə edir (Nazirliyin "
         "24 avqust 2026 tarixli yazılı təsdiqinə görə FR2 və FR6–FR9 bu alt-modulda tələb olunmur). Bütün modellər "
         "strukturdur: heç bir AR/ARIMA/ARCH/GARCH komponenti və asılı dəyişənin gecikməsi yoxdur; hər tənlik "
         "iqtisadi sürücülərlə izah olunur. FR1 makro çərçivəni və üç ssenarini — <strong>Əsas</strong>, "
         "<strong>Mənfi</strong>, <strong>İslahat</strong> — verir; digər modullar onları istifadə edir. Ümumi "
         f'standartlar <a href="methodology.html">Metod</a>, mənbələr <a href="data.html">Məlumat mənbələri</a> səhifəsindədir.</p>',
         html.h2("headline", 2, "Baş göstəricilər, 2026–2030"),
         html.fig("index_headline", "Real ÜDM və qeyri-neft ÜDM-in artımı", headline_fig(d1),
                  "2025-ə qədər faktiki, 2026–2030 Əsas ssenari üzrə proqnoz; zolaqlar FR1-in birgə simulyasiyasından.",
                  "Pəncərə 2006–2030."),
         tbl,
         "<p>Bütün sətirlər Əsas ssenaridir; zolaq 5-ci və 95-ci faizlər arasındakı aralıqdır (90 %). Zolaqlar enlidir — "
         "illik məlumatla beşillik proqnozun dürüst qeyri-müəyyənliyi belədir. Mənfi və İslahat ssenariləri hər tələbin "
         "öz səhifəsindədir.</p>",
         html.h2("fr-grid", 3, "Altı tələb"), f'<div class="card-grid">{grid}</div>',
         "<p>Status rəngləri makro modulla eynidir: yaşıl — tələb qarşılanıb, sarı — qismən (səbəbi səhifədə "
         "ölçülmüş şəkildə yazılıb), qırmızı — qarşılanmayıb.</p>",
         html.h2("synthetic", 4, "Sintetik məlumat haqqında"),
         html.synth_banner("", f"FR10 müəssisə paneli ({v(p['rows'], 0)} sətir) və FR12 biznes reyestri "
                           f"({v(r['rows'], 0)} sətir) uydurma fayllardır."),
         "<p>Nazirlik müəssisə məlumatını layihə ilə paylaşmır; o, öz məlumatını öz sistemində yükləyəcək. Ona görə FR10 və "
         "FR12-nin B qatı eyni sxemdə sintetik fayllarla təhvil verilir və sınaqdan keçirilir. Bu fayllardan alınan heç bir "
         "rəqəm saytda tapıntı kimi göstərilmir. Əvəzetmə qaydası: "
         '<a href="synthetic.html">Sintetik məlumat və onun əvəz edilməsi</a>.</p>',
         html.h2("run", 5, "Modulun işə salınması"), nbinfo.run_block(""),
         ]
    return "\n".join(o), SECS
