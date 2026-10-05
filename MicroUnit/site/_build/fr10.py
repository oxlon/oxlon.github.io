"""fr10.py — FR10 page: enterprises' financial condition, production efficiency and market position."""
from . import html, req, common, synth
from .core import v, esc
from .common import SCEN
from .labels import nace
from . import fr10_data as D
from . import fr10_text as T

SECTIONS = [("teleb", "Tələb"), ("model", "Model: A və B qatları"), ("data", "Məlumat"), ("results", "Nəticələr (A qatı)"),
            ("warning", "Erkən xəbərdarlıq"), ("check", "Yoxlama"), ("layerb", "B qatı — sintetik"),
            ("limits", "Məhdudiyyətlər"), ("files", "Fayllar")]

FLAGS = [("F_negative_margin", "mənfi marja"), ("F_margin", "marjanın enişi"), ("F_share", "payın enişi"),
         ("F_productivity", "məhsuldarlığın enişi"), ("F_renewal", "investisiya (yenilənmə)"), ("F_stocks", "ehtiyatların artımı")]


def build(t, pre="../"):
    d = D.load()
    o = ["<h1>FR10 — Müəssisələrin maliyyə vəziyyəti, istehsal effektivliyi və bazar payı</h1>",
         html.kicker("FR10", "FR10.ipynb", "docs/FR10_Methodology.md"),
         common.intro("Sənaye sahələri, bölmələr, mülkiyyət formaları, regionlar və məhsullar üzrə (A qatı — real DSK və "
                      "iş kitabı məlumatı) maliyyə vəziyyəti, effektivlik və bazar mövqeyi, 2030-a qədər proqnoz və erkən "
                      "xəbərdarlıq siyahısı. Müəssisə səviyyəsində mühərrik (B qatı) hazırdır, lakin hələ "
                      "<strong>sintetik</strong> fayl üzərində işləyir — bu, səhifədə ayrıca və aydın işarələnib."),
         html.h2("teleb", 1, "Tələb"), req.block("FR10", t),
         html.h2("model", 2, "Model: A və B qatları"), T.model(d),
         html.h2("data", 3, "Məlumat"), T.data(d, pre)]
    o += results(d)
    o += warning(d)
    o += check(d)
    o += layerb(d, pre)
    o += [html.h2("limits", 8, "Məhdudiyyətlər"), "<p>Metodologiya sənədinin 17-ci bölməsindən.</p>",
          common.limits_list(T.LIMITS)]
    o.append(common.files_section(9, "FR10", pre))
    return "\n".join(o)


def results(d):
    sc = d["sc"]
    o = [html.h2("results", 4, "Nəticələr (A qatı)"),
         html.fig("fr10_industry", "Sənaye məhsulu (dörd bölmə), nominal", D.industry_fig(d),
                  "Bölmə məhsulu = 2025 məhsulu × FR1-in nominal əlavə dəyər indeksi; zolaq FR1 çəkilişləri və sahə "
                  "modelinin qeyri-müəyyənliyini birləşdirir.", "Pəncərə 2005–2030."),
         html.fig("fr10_sections", "Mədənçıxarma və emal sənayesi", D.sections_fig(d),
                  "Mədənçıxarma neft hasilatının azalması ilə enir; emal sənayesi FR1-in emal yolunu izləyir.",
                  "Pəncərə 2005–2030."),
         html.h3("Ssenarilər, 2026–2030"),
         common.scen_table([
             ("Sənaye məhsulu, nominal artım", "% illik", {s: v(sc.loc[s, "industry nominal output growth % pa"], 2, sign=True) for s in SCEN}),
             ("Emal sənayesi, nominal artım", "% illik", {s: v(sc.loc[s, "manufacturing nominal growth % pa"], 2, sign=True) for s in SCEN}),
             ("Emal sənayesi, real artım (FR1)", "% illik", {s: v(sc.loc[s, "manufacturing real growth % pa (FR1 rva_man)"], 2, sign=True) for s in SCEN}),
             ("Neft emalı, real artım", "% illik", {s: v(sc.loc[s, "refining real growth % pa"], 2, sign=True) for s in SCEN}),
             ("Mədənçıxarmanın sənayedə payı, 2030", "%", {s: v(sc.loc[s, "mining share of industry 2030 %"], 1) for s in SCEN}),
             ("Qeyri-dövlət payı, 2030", "%", {s: v(sc.loc[s, "non-state share 2030 % (composition)"], 1) for s in SCEN}),
             ("Emal sahələri üzrə HHI, 2030", "", {s: v(sc.loc[s, "HHI manufacturing 2030"], 0) for s in SCEN}),
             ("Bakının payı, 2030", "%", {s: v(sc.loc[s, "Baku share 2030 %"], 1) for s in SCEN}),
             ("Emal: ümumi mənfəət / əlavə dəyər, 2030", "%", {s: v(sc.loc[s, "manufacturing GOS % VA 2030"], 1) for s in SCEN})]),
         html.fig("fr10_hhi", "Bazar mövqeyi: emal sahələri üzrə konsentrasiya (HHI)", D.hhi_fig(d),
                  "HHI emal sənayesinin 24 sahəsinin paylarından hesablanır (müəssisə səviyyəsində deyil); B qatı real "
                  "məlumatla NACE × region üzrə müəssisə HHI-ni verəcək.", "Pəncərə 2005–2030.")]
    return o


def warning(d):
    e = d["ew"]
    e = e[(e.n_flags > 0) | (e.watch_list)].sort_values(["watch_list", "n_flags"], ascending=False)
    rows = []
    for r in e.itertuples():
        fl = [lab for col, lab in FLAGS if getattr(r, col) is True or getattr(r, col) == "FLAG"]
        ins = [lab for col, lab in FLAGS if getattr(r, col) == "insufficient data"]
        txt = ", ".join(fl) or "—"
        if ins:
            txt += f' <span class="src-en">(məlumat çatmır: {", ".join(ins)})</span>'
        rows.append([esc(nace(r.nace2)), v(r.share_2025_pct, 2), v(r.margin_2023_25, 1), txt, v(r.n_flags, 0),
                     html.pill("gap", "izləmədə") if r.watch_list else html.pill("neutral", "yox")])
    n_watch = int(d["ew"].watch_list.sum())
    return [html.h2("warning", 5, "Erkən xəbərdarlıq"),
            "<p>Bayraqlar 2023–25 ortalamasını 2020–22 ilə müqayisə edir və hər sahənin öz dəyişkənliyi ilə ölçülür; "
            "emalın 0,5 %-dən kiçik sahələri üçün siyahıya düşmək iki bayraq tələb edir, mənfi marja avtomatik izləmədir, "
            "çatmayan investisiya məlumatı sıfır deyil, «məlumat çatmır» kimi göstərilir. Bunlar şəffaf hədlərdir, "
            f"qiymətləndirilmiş ehtimallar deyil. İzləmə siyahısında {v(n_watch, 0)} sahə var.</p>",
            html.table(["Sahə", "Emalda pay 2025, %", "Marja 2023–25, %", "Bayraqlar", "Kompozit bayraq sayı", "İzləmə"], rows,
                       cols=["c-wide", "c-num", "c-num", "c-text", "c-num", "c-tight"])]


def check(d):
    h = d["hold"][d["hold"].selected == True]  # noqa: E712
    rows = [[esc(T.sys_az(r.system)), esc(T.MEAS_AZ.get(r.measure, r.measure)), esc(T.W_AZ.get(r.weighting, r.weighting)),
             common.u_cell(r.U_vs_random_walk), common.u_cell(r.U_vs_constant_growth), v(r.DM_p_vs_cg, 3)]
            for r in h.itertuples()]
    p = d["plaus"]
    flagged = int(p.flag.notna().sum())
    return [html.h2("check", 6, "Yoxlama"), T.check_intro(),
            html.table(["Sistem", "Ölçü", "Çəki", "U: təsadüfi gəzişmə", "U: sabit artım", "DM p (SA)"], rows,
                       cls="tbl tbl-dense tbl-backtest", cols=["c-wide", "c-tight", "c-tight", "c-num", "c-num", "c-num"]),
            T.check_outro(h),
            f"<p>Hər proqnoz artımı vahidin öz tarixi ilə müqayisə olunur (2010–2019, 2021–2025 ortaları, ən yaxşı və ən "
            f"pis beşillik): {v(len(p), 0)} vahiddən {v(flagged, 0)}-i bayraqlanıb. "
            f"{v(int(d['ident'].passed.sum()), 0)}/{v(len(d['ident']), 0)} hesab eyniliyi ödənir (konstruksiyaya görə).</p>"]


def layerb(d, pre):
    s = synth.panel()
    return [html.h2("layerb", 7, "B qatı — müəssisə səviyyəsində mühərrik (sintetik)"),
            html.synth_banner(pre, f"<code>data/firm_panel/FR10_firm_panel_SYNTHETIC.csv</code> — {v(s['rows'], 0)} sətir, "
                              f"{v(s['firms'], 0)} uydurma müəssisə, {v(s['nace'], 0)} NACE bölməsi, {s['y0']}–{s['y1']}."),
            T.layerb_text(d, s, pre)]
