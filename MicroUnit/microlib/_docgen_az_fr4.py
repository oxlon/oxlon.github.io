"""FR4 Azerbaijani AUTO blocks (docs/az/FR4_Metodologiya.md), rendered from the same objects as the English cell 20.2.
Called at the end of FR4.ipynb Part 20.2 / Part 26 with the notebook namespace; nothing is recomputed differently."""
from types import SimpleNamespace

from .docgen_az import num, num_t, pct, translator, ordsuf, locsuf

QTY = {"total": "ümumi", "labour_force": "işçi qüvvəsi", "agriculture": "kənd təsərrüfatı", "services": "digər xidmətlər",
       "construction": "tikinti", "hired": "muzdlu işçilər", "budget": "büdcə", "nonbudget": "qeyri-büdcə",
       "state": "dövlət", "nonstate": "qeyri-dövlət", "hotel": "yerləşdirmə və iaşə", "ict": "informasiya və rabitə",
       "industry": "sənaye", "mining": "mədənçıxarma", "market_services": "bazar xidmətləri", "manuf": "emal sənayesi"}


def _dir(x):
    return "artır" if x > 0.005 else ("azalır" if x < -0.005 else "dəyişmir")


def _yr(y):
    return f"{y}-{ordsuf(y)} ildə"


def results(ns):
    n = SimpleNamespace(**{k: v for k, v in ns.items() if not k.startswith("__")})
    tr = translator("FR4", QTY)
    Y0, Y1, FY = n.Y0, n.Y1, n.FC_YEARS
    pm = lambda x, d=2: pct(x, d)  # noqa: E731
    tb = n.tb
    t0, t1 = n.TOT["Baseline"].loc[Y0], n.TOT["Baseline"].loc[Y1]
    rows = sorted([(n.G8_AZ[g],) + tuple(n.band(n.G8_LABEL[g])) for g in n.G8_KEYS], key=lambda r: -r[1])
    L11 = ["## 11. Əsas ssenarinin nəticələri, 2026–2030", "",
           f"Ümumi məşğulluq (FR1) {num(t0, 0)} min nəfərdən {num(t1, 0)} min nəfərədək "
           f"{'artır' if t1 >= t0 else 'azalır'} — **ildə {pm(tb[0])}** (90% zolaq: {pm(tb[1])} ilə {pm(tb[2])} arası).", "",
           "| Qrup | İllik, % | 90% zolaq |", "|---|---|---|"]
    L11 += [f"| {r[0]} | {r[1]:+.2f} | {r[2]:+.2f} ilə {r[3]:+.2f} arası |" for r in rows]
    Eb, Ib = n.Eb, n.Ib
    L11 += ["",
            f"- **Sənaye daxilində** (məşğul əhali əsasında): mədənçıxarma ildə {pm(n.cagr(Eb.mining))} (onun neft hissəsi "
            f"E9 tənliyinə tabedir), emal sənayesi {pm(n.cagr(Eb.manuf))}.",
            f"- **Digər xidmətlər daxilində**: bazar xidmətləri {_dir(n.mk_e)} (məşğul əhali üzrə ildə {pm(n.mk_e)}, muzdlu "
            f"işçilər üzrə {pm(n.mk_h)}), büdcədən maliyyələşən xidmətlər isə məşğul əhali əsasında {_dir(n.pb_e)} "
            f"({pm(n.pb_e)}), muzdlu işçilər əsasında {_dir(n.pb_h)} ({pm(n.pb_h)}): digər xidmətlərin buraxılışı artdıqca E6 "
            "məşğulluğu büdcədən maliyyələşən blokdan bazar xidmətlərinə doğru keçirir"
            + (" və burada bu keçid büdcədən maliyyələşən bloku mütləq ifadədə kiçildəcək qədər sürətlidir." if n.pb_e < 0
               else "."),
            f"- **Tikinti**: FR1-də tikinti buraxılışı {_yr(FY[0])} {pm(n.JR.loc['Construction', 'junction_growth_pct'], 1)} "
            f"dəyişir; tikintidə məşğulluq həmin il {pm(n.c26)}, ümumi məşğulluq isə {pm(n.t26)} dəyişir — "
            + ("enmə var, lakin sönümlüdür (kiçik elastikliyə yarım çəki verilir)." if n.c26 < 0 else "sönümlü reaksiya."),
            "",
            "Müqayisə üçün birinci versiya (FR1-in əvvəlki yolu ilə): yerləşdirmə və iaşə +2,42%, informasiya və rabitə "
            "+1,43%, tikinti +1,24% … ticarət +0,32%, cəmi +0,53%.", "",
            f"- **Dövlət sektorunda** məşğulluq: {num(Ib.state.loc[Y0], 1)} → {num(Ib.state.loc[Y1], 1)} min nəfər "
            f"(ildə {pm(n.sb[0])}; zolaq {pm(n.sb[1])} ilə {pm(n.sb[2])} arası), pay "
            f"{num(Ib['state share, %'].loc[Y0], 1)}% → {num(Ib['state share, %'].loc[Y1], 1)}%.",
            f"- **Büdcə təşkilatları** (σ = {num(n.SIGMA_PUB, 3)}): {num(Ib['budget organisations'].loc[Y0], 1)} → "
            f"{num(Ib['budget organisations'].loc[Y1], 1)} min nəfər (ildə {pm(n.bb[0])}; zolaq {pm(n.bb[1])} ilə "
            f"{pm(n.bb[2])} arası), {_yr(Y1)} muzdlu işçilərin {num(Ib['budget share of hired, %'].loc[Y1], 1)}%-i.",
            f"- **Neft sektorunda** məşğulluq, vergi uçotu əsasında: {num(Ib['oil, tax-record basis'].loc[Y0], 1)} → "
            f"{num(Ib['oil, tax-record basis'].loc[Y1], 1)} min nəfər (ildə {pm(n.ob[0])}; zolaq {pm(n.ob[1])} ilə "
            f"{pm(n.ob[2])} arası); statistik əsasda {num(Ib['oil, statistical basis'].loc[Y0], 1)} → "
            f"{num(Ib['oil, statistical basis'].loc[Y1], 1)}.", ""]
    sp, INST = n._spr, n.INST
    oa, orf = INST["Adverse"]["oil, tax-record basis"].loc[Y1], INST["Reform"]["oil, tax-record basis"].loc[Y1]
    L11 += [f"**Ssenarilər.** {_yr(Y1).capitalize()} FR1-in ssenariləri real neft ÜDM-i üzrə {num(sp['rgdpoil'], 1)}%, "
            f"qeyri-neft ÜDM üzrə {num(sp['rgdpnon'], 2)}%, məşğulluq üzrə {num(sp['emp'], 2)}% fərqlənir; buna görə FR4-ün "
            f"məşğulluğu da {num(sp['emp'], 2)}% ({num(n.SC.employed_2030.max() - n.SC.employed_2030.min(), 1)} min nəfər) "
            f"fərqlənir. Neft sektorunda məşğulluq ssenarilər arasında {num((orf / oa - 1) * 100, 1)}% ayrılır "
            f"(Mənfi {num(oa, 1)}, İslahat {num(orf, 1)} min nəfər).", "",
            f"**Yelpik qrafikləri** (`FR4_fan_employment.csv`, `FR4_fan_summary_2030.csv`): {num(n.N_REP, 0)} təkrarlama — "
            f"tarixi qalıq yollarının yenidən seçilməsi ({len(n.cols)} tənlik üzrə {n.STARTS[0]}–{n.STARTS[-1]} illərində "
            f"başlayan {len(n.STARTS)} birgə {n.H_} illik yol, mərkəzləşdirilmiş; E9 üçün başlanğıclar "
            f"{n.S9[0]}–{n.S9[-1]}), parametr çəkilişləri və "
            + (f"FR1-in {len(n.DRAW_IDS)} makro çəkilişi birləşdirilir." if n.DRAW_IDS is not None
               else "FR1 çəkilişləri OLMADAN (ehtiyat variant).")
            + " Hər nöqtəvi proqnoz öz kvartillərarası zolağının daxilindədir (Hissə 17.5-də yoxlanılır).", "", "---", ""]
    L12 = [f"## 12. Rıçaqlar və həssaslıqlar ({Y1}, Əsas ssenari)", "", f"| Rıçaq | {Y1}-{ordsuf(Y1)} ilə təsir |",
           "|---|---|"]
    for lev, g in n.LVT.groupby("lever", sort=False):
        g = g.reindex(g.difference_pct.abs().sort_values(ascending=False).index).head(3)
        eff = "; ".join(f"{tr(q)} {num_t(r.difference, 1, True)} min ({r.difference_pct:+.1f}%)"
                        for q, r in zip(g.quantity, g.itertuples()))
        L12.append(f"| {tr(lev)} | {eff} |")
    L12 += ["", "Sönmə sətri proqnoz qaydası deyil, yalnız həssaslıqdır. Ən böyük dəyişkənliyi yenə dövlət payı rıçağı "
            "yaradır: bu, ekonometrik deyil, siyasi qərardır.", "", "---", ""]
    bl = n.cmpt["Baseline"].loc[Y1]
    e2gap = (f"İki blok {_yr(Y1)} məşğulluq üzrə {num(abs(bl['employed diff, %']), 2)}% (bütün ssenarilər və illər üzrə ən "
             f"çoxu {num(n.mx, 2)}%), işçi qüvvəsi üzrə isə ən çoxu {num(n.mxl, 2)}% fərqlənir. Hər ikisi {Y0}-{ordsuf(Y0)} "
             "ilin göstəricisini təkrarlayır.")
    return {"e2gap": e2gap, "results": "\n" + "\n".join(L11 + L12) + "\n"}


def cells(ns):
    nc, ncode = ns["_ncell"], ns["_ncode"]
    return f"{nc} xana ({ncode} kod, {nc - ncode} markdown)"


__all__ = ["results", "cells", "locsuf"]
