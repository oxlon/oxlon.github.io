"""b_names.py — Azerbaijani names, units and groups of the D4 market-panel series (the feeds keep the source's own,
often English, titles in the `name` column; the panel shows these instead)."""
import re

GROUPS = [("cbar_fx", "Məzənnələr (AMB)"), ("cbar_rate", "Uçot dərəcəsi və faiz dəhlizi (AMB)"), ("bfb", "Bakı Fond Birjası: AMB notları və MN istiqrazları"),
          ("brent", "Neft"), ("azeri_light", "Neft"), ("dsk_macro", "DSK: aylıq makro göstəricilər (Yanvar–ay)"), ("dsk_cpi", "DSK: istehlak qiymətləri"),
          ("dsk_tables", "DSK: rüblük və illik cədvəllər"), ("sofaz", "ARDNF"), ("minfin", "Maliyyə Nazirliyi"),
          ("eurusd", "Qlobal bazarlar və risk indeksləri"), ("vix", "Qlobal bazarlar və risk indeksləri"), ("ust10", "Qlobal bazarlar və risk indeksləri"),
          ("fedfunds", "Qlobal bazarlar və risk indeksləri"), ("gpr", "Qlobal bazarlar və risk indeksləri"), ("epu", "Qlobal bazarlar və risk indeksləri")]
FIXED = {
    "azeri_light_proxy": ("Azeri Light (proksi: Brent + median spred)", "USD/barel"), "brent_usd_daily": ("Brent neft qiyməti (gündəlik)", "USD/barel"),
    "bfb_cbar_note_avg_yield": ("AMB notları: orta gəlirlilik", "%"), "bfb_cbar_note_cut_yield": ("AMB notları: kəsmə gəlirliliyi", "%"),
    "bfb_cbar_note_demand_azn": ("AMB notları: tələb", "AZN"), "bfb_cbar_note_volume_azn": ("AMB notları: yerləşdirmə həcmi", "AZN"),
    "bfb_mof_bond_avg_yield": ("MN istiqrazları (DQK): orta gəlirlilik", "%"), "bfb_mof_bond_cut_yield": ("MN istiqrazları: kəsmə gəlirliliyi", "%"),
    "bfb_mof_bond_demand_azn": ("MN istiqrazları: tələb", "AZN"), "bfb_mof_bond_volume_azn": ("MN istiqrazları: yerləşdirmə həcmi", "AZN"),
    "cbar_corridor_ceiling": ("Faiz dəhlizinin yuxarı həddi", "%"), "cbar_corridor_floor": ("Faiz dəhlizinin aşağı həddi", "%"),
    "cbar_decision": ("Uçot dərəcəsi qərarı (dəyişmə)", "f.b."), "cbar_policy_rate": ("AMB uçot dərəcəsi", "%"),
    "dsk_cpi_food_mm": ("İQİ: ərzaq, aylıq dəyişmə", "%"), "dsk_cpi_food_yoy": ("İQİ: ərzaq, illik", "%"), "dsk_cpi_mm": ("İQİ: aylıq dəyişmə", "%"),
    "dsk_cpi_nonfood_mm": ("İQİ: qeyri-ərzaq, aylıq", "%"), "dsk_cpi_nonfood_yoy": ("İQİ: qeyri-ərzaq, illik", "%"), "dsk_cpi_yoy": ("İQİ: illik", "%"),
    "dsk_cpi_ytd_avg_yoy": ("İQİ: Yanvar–ay ortası, illik", "%"), "dsk_q_gdp_nominal": ("Rüblük nominal ÜDM", "mln AZN"),
    "dsk_q_gdp_real": ("Rüblük real ÜDM (2005 qiymətləri)", "mln AZN"), "dsk_q_gdp_real_yoy": ("Rüblük real ÜDM: illik artım", "%"),
    "epu_global": ("Qlobal iqtisadi siyasət qeyri-müəyyənliyi (EPU)", "indeks"), "eurusd": ("EUR/USD məzənnəsi", "USD/EUR"), "fedfunds": ("ABŞ federal fondlar faizi", "%"),
    "gpr_global": ("Geosiyasi risk indeksi (qlobal)", "indeks"), "gpr_isr": ("Geosiyasi risk: İsrail", "indeks"), "gpr_rus": ("Geosiyasi risk: Rusiya", "indeks"),
    "gpr_tur": ("Geosiyasi risk: Türkiyə", "indeks"), "minfin_operative_report": ("MN: son operativ büdcə hesabatı", "rüb"),
    "minfin_state_rev_fakt": ("Dövlət büdcəsinin vergi və qeyri-vergi gəlirləri: faktiki", "mln AZN"),
    "minfin_state_rev_tesdiq": ("Dövlət büdcəsinin vergi və qeyri-vergi gəlirləri: təsdiq", "mln AZN"),
    "sofaz_assets_usd_mln": ("ARDNF aktivləri", "mln USD"), "sofaz_gold_tons": ("ARDNF qızılı", "ton"), "sofaz_gold_usd_mln": ("ARDNF qızılı", "mln USD"),
    "sofaz_gold_share_pct": ("ARDNF: qızılın payı", "%"), "sofaz_transfers_cum_azn_mln": ("ARDNF: dövlət büdcəsinə transfertlər (yığılmış)", "mln AZN"),
    "ust10y": ("ABŞ 10 illik istiqraz gəlirliyi", "%"), "vix": ("VIX — qlobal risk iştahı indeksi", "indeks"),
}
DSK_MACRO = {"agriculture": "Kənd təsərrüfatı məhsulları", "budget_bal": "Dövlət büdcəsinin balansı", "budget_exp": "Dövlət büdcəsinin xərcləri",
             "budget_rev": "Dövlət büdcəsinin gəlirləri", "cpi": "İstehlak qiymətləri indeksi", "credit": "Kredit qoyuluşları", "deposits": "Əhalinin bank əmanətləri",
             "export": "İxrac", "ext_debt_usd": "Xarici dövlət borcu (mln USD)", "gdp_nonoil": "Qeyri-neft-qaz ÜDM", "gdp_oil": "Neft-qaz ÜDM", "gdp": "Ümumi daxili məhsul",
             "import": "İdxal", "incomes": "Əhalinin nominal gəlirləri", "industry_nonoil": "Qeyri-neft-qaz sənayesi", "industry": "Sənaye məhsulu",
             "investment": "Əsas kapitala investisiyalar", "reserves_usd": "Strateji valyuta ehtiyatları (mln USD)", "retail": "Pərakəndə ticarət dövriyyəsi",
             "trade": "Xarici ticarət dövriyyəsi", "wage": "Orta aylıq nominal əmək haqqı"}
DSK_A = {"average_monthly_nominal_wages": "Orta aylıq nominal əmək haqqı", "consumer_price_indeces": "İstehlak qiymətləri indeksi",
         "gross_domestic_product_at_constant_price": "ÜDM (sabit qiymətlərlə)", "income_of_population": "Əhalinin gəlirləri",
         "industrial_producer_price_index": "Sənaye məhsulu istehsalçılarının qiymət indeksi", "loans_to_economy_end_of_the_year": "İqtisadiyyata kreditlər (ilin sonu)",
         "population_savings_in_banks": "Əhalinin bank əmanətləri", "population_size_end_of_the_year": "Əhalinin sayı (ilin sonu)",
         "state_budget_expenditure": "Dövlət büdcəsinin xərcləri", "state_budget_revenue": "Dövlət büdcəsinin gəlirləri"}
SOFAZ = {"cny": "CNY", "eur": "EUR", "gbp": "GBP", "jpy": "JPY", "other": "digər valyutalar", "usd": "USD"}
CLS = {"equities": "səhmlər", "fixed_income": "sabit gəlirli alətlər", "gold": "qızıl", "real_estate": "daşınmaz əmlak"}


def group(feed):
    for k, g in GROUPS:
        if feed == k:
            return g
    return "Digər"


def name(series, name0, unit0):
    """(Azerbaijani name, unit) of a D4 series."""
    if series in FIXED:
        return FIXED[series]
    m = re.match(r"dsk_(\w+?)_ytd(_yoy)?$", series)
    if m and m.group(1) in DSK_MACRO:
        return DSK_MACRO[m.group(1)] + (": illik artım (Yanvar–ay)" if m.group(2) else " (Yanvar–ay, cəmi)"), unit0
    m = re.match(r"dsk_a_(\w+)$", series)
    if m and m.group(1) in DSK_A:
        return DSK_A[m.group(1)] + ": illik artım", unit0
    m = re.match(r"sofaz_ccy_(\w+)_mln$", series)
    if m:
        return f"ARDNF: {SOFAZ.get(m.group(1), m.group(1))} mövqeyi", "mln, valyutada"
    m = re.match(r"sofaz_class_(\w+)_pct$", series)
    if m:
        return f"ARDNF aktiv sinfi: {CLS.get(m.group(1), m.group(1))}", "%"
    m = re.match(r"cbar_([a-z]{3})$", series)
    if m:
        return f"{(name0 or m.group(1).upper())} — AMB rəsmi məzənnəsi", unit0
    return name0 or series, unit0
