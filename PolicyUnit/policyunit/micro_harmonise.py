"""MicroUnit chain results (baseline vs scenario) -> harmonised OUT_COLS rows."""
from __future__ import annotations

from . import config, microbridge as mb
from .engine_base import row

Y = config.MICRO_YEARS
FR1_SECTORS = {"agr": "Kənd təsərrüfatı", "min": "Mədənçıxarma", "man": "Emal sənayesi",
               "elc": "Elektrik enerjisi", "wat": "Su təchizatı", "con": "Tikinti", "trd": "Ticarət",
               "tou": "Turizm və iaşə", "tra": "Nəqliyyat", "ict": "İnformasiya və rabitə",
               "oth": "Digər xidmətlər"}
FR4_SECTORS = ["agr", "mining", "manuf", "elec", "water", "constr", "trade", "transp", "hotel", "ict",
               "fin", "realest", "prof", "admsup", "pubadm", "educ", "health", "art", "othsvc"]
FR12_SECTORS = ["AGR", "IND", "CON", "TRD", "TRA", "ACC", "ICT", "REA", "EDU", "HEA", "OTH"]

# indicator, label_az, unit, module, series id, group
HEAD = [
    ("gdp_real", "Real ÜDM", "mln AZN 2015", "FR1", "fr1:rgdp", "makro"),
    ("gdp_nonoil_real", "Real qeyri-neft ÜDM", "mln AZN 2015", "FR1", "fr1:rgdpnon", "makro"),
    ("gdp_nominal", "Nominal ÜDM", "mln AZN", "FR1", "fr1:gdp_n", "makro"),
    ("cpi", "İstehlak qiymətləri indeksi", "2015 = 100", "FR1", "fr1:cpi", "makro"),
    ("infl", "İnflyasiya (İQİ)", "%", "FR1", "fr1:infl", "makro"),
    ("unemp_rate", "İşsizlik səviyyəsi", "%", "FR1", "fr1:unemp", "əmək"),
    ("employment", "Məşğulluq (ümumi, İQS; FR1)", "min nəfər", "FR1", "fr1:emp", "əmək"),
    ("employment_hired", "Muzdlu işçilər (formal; FR4)", "min nəfər", "FR4", "fr4:hired:total", "əmək"),
    ("wage_nominal", "Orta aylıq nominal əmək haqqı", "AZN", "FR1", "fr1:wage", "əmək"),
    ("wage_real", "Real orta əmək haqqı", "AZN 2015", "FR1", "fr1:rwage", "əmək"),
    ("hh_disp_real", "Real sərəncamda qalan gəlir", "mln AZN 2015", "FR1", "fr1:rhhdisp", "sosial"),
    ("cons_real", "Real ev təsərrüfatı istehlakı", "mln AZN 2015", "FR1", "fr1:rcons", "makro"),
    ("exports_nonoil_real", "Real qeyri-neft ixracı", "mln AZN 2015", "FR1", "fr1:rx_non", "xarici"),
    ("imports_nonoil_real", "Real qeyri-neft idxalı", "mln AZN 2015", "FR1", "fr1:rm_non", "xarici"),
    ("budget_balance", "Dövlət büdcəsinin balansı", "mln AZN", "FR1", "fr1:balance_n", "fiskal"),
    ("debt", "Dövlət borcu", "mln AZN", "FR1", "fr1:debt_azn", "fiskal"),
    ("capital_nonoil", "Qeyri-neft kapital ehtiyatı", "mln AZN 2015", "FR1", "fr1:K_non", "uzun"),
    ("services_real", "Pullu xidmətlərin real həcmi (FR5)", "mln AZN", "FR5", "fr5:vol:total", "xidmət"),
    ("hhi_man", "Emal sənayesində HHI (FR10)", "indeks", "FR10", "fr10:hhi_man", "bazar"),
    ("industry_output", "Sənaye buraxılışı (FR10)", "mln AZN", "FR10", "fr10:ind_output", "sektor"),
]


def _ser(res, mod, sid):
    return mb.series(res, mod, sid)


def rows(base, scen, method, tier, note="") -> list[dict]:
    out = []

    def add(ind, lab, unit, b, v, grp, nt=note):
        if b is None or v is None:
            return
        for i, y in enumerate(Y):
            out.append(row(ind, lab, unit, y, b[i], v[i], method, tier, grp, nt))

    for ind, lab, unit, mod, sid, grp in HEAD:
        add(ind, lab, unit, _ser(base, mod, sid), _ser(scen, mod, sid), grp)
    # derived ratios (pp of GDP)
    for ind, lab, sid in (("budget_balance_pct", "Büdcə balansı (ÜDM-ə %)", "fr1:balance_n"),
                          ("debt_pct", "Dövlət borcu (ÜDM-ə %)", "fr1:debt_azn")):
        b = [100 * a / g for a, g in zip(_ser(base, "FR1", sid), _ser(base, "FR1", "fr1:gdp_n"))]
        v = [100 * a / g for a, g in zip(_ser(scen, "FR1", sid), _ser(scen, "FR1", "fr1:gdp_n"))]
        add(ind, lab, "% ÜDM", b, v, "fiskal")
    # current-account proxy: (real non-oil net exports) x GDP deflator, mln AZN
    def ca(r):
        x, m, p = _ser(r, "FR1", "fr1:rx_non"), _ser(r, "FR1", "fr1:rm_non"), _ser(r, "FR1", "fr1:p_gdp")
        return [(a - b) * c for a, b, c in zip(x, m, p)]
    add("ca_proxy", "Cari hesab proksisi (qeyri-neft xalis ixrac, nominal)", "mln AZN", ca(base), ca(scen),
        "xarici", (note + "; " if note else "") + "FR1-də cari hesab yoxdur — qeyri-neft xalis ixrac proksisi")
    for sec, lab in FR1_SECTORS.items():
        add(f"sector_va:{sec}", f"Əlavə dəyər — {lab}", "mln AZN 2015",
            _ser(base, "FR1", f"fr1:rva_{sec}"), _ser(scen, "FR1", f"fr1:rva_{sec}"), "sektor")
        add(f"sector_price:{sec}", f"Deflator — {lab}", "indeks",
            _ser(base, "FR1", f"fr1:p_{sec}"), _ser(scen, "FR1", f"fr1:p_{sec}"), "sektor")
    for sec in FR4_SECTORS:
        add(f"sector_emp:{sec}", f"Məşğulluq — {sec} (FR4)", "min nəfər",
            _ser(base, "FR4", f"fr4:emp:{sec}"), _ser(scen, "FR4", f"fr4:emp:{sec}"), "sektor")
        add(f"sector_hired:{sec}", f"Muzdlu işçilər — {sec} (FR4)", "min nəfər",
            _ser(base, "FR4", f"fr4:hired:{sec}"), _ser(scen, "FR4", f"fr4:hired:{sec}"), "sektor")
    for sec in FR12_SECTORS:
        for ind, sid, lab, unit in (("hhi", "fr12:conc:hhi_upper", "HHI (yuxarı sərhəd)", "indeks"),
                                    ("entry", "fr12:act:entry", "Yeni müəssisələr", "say"),
                                    ("exit", "fr12:act:exit", "Fəaliyyəti dayanan müəssisələr", "say")):
            add(f"{ind}:{sec}", f"{lab} — {sec} (FR12)", unit,
                _ser(base, "FR12", f"{sid}:{sec}"), _ser(scen, "FR12", f"{sid}:{sec}"), "bazar")
    for mod, pref, ind, lab, unit, grp in (
            ("FR10", "fr10:output_real_mn_AZN_2015", "industry_output", "Sənaye sahəsi buraxılışı", "mln AZN 2015", "sektor"),
            ("FR10", "fr10:gos_proxy_margin_pct", "industry_margin", "Marja proksisi", "%", "sektor"),
            ("FR10", "fr10:reg_output", "region_output", "Regional sənaye buraxılışı", "mln AZN", "regional"),
            ("FR5", "fr5:vol", "services_real", "Pullu xidmətlər (real)", "mln AZN", "xidmət")):
        ids = [k for k in scen["results"].get(mod, {}).get("series", {}) if k.startswith(pref + ":")]
        for sid in sorted(ids):
            code = sid[len(pref) + 1:]
            if code == "total":
                continue
            add(f"{ind}:{code}", f"{lab} — {code}", unit, _ser(base, mod, sid), _ser(scen, mod, sid), grp)
    return out


def fr12_io_rows(scen, method, tier, year) -> list[dict]:
    """FR12 industrial-organisation toolkit (entry scenario S1) — deviation-only rows."""
    io = scen["results"].get("FR12", {}).get("meta", {}).get("io") or {}
    s1 = io.get("S1_entry") or {}
    out = []
    for k, lab, unit in (("d_price_pct", "Bazar qiyməti", "%"), ("d_markup_pp", "Marja (mark-up)", "pp"),
                         ("d_output_pct", "Bazar buraxılışı", "%"), ("d_cs_pct_rev", "İstehlakçı rifahı", "%")):
        v = s1.get(k)
        if v is None:
            continue
        out.append(row(f"market:{io.get('market')}:{k}", f"{lab} — {io.get('market_name', '')} (FR12 giriş ssenarisi)",
                       unit, year, float("nan"), float("nan"), method, tier, "bazar",
                       f"FR12 sənaye iqtisadiyyatı alət dəsti; HHI {io.get('hhi', float('nan')):.0f}; "
                       f"{io.get('structure_source', '')}", delta=float(v), delta_pct=float(v)))
    return out
