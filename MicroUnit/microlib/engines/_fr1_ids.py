"""FR1 indicator ids, Azerbaijani/English labels and units (shared by the FR1 notebook catalogue and the engine).

Ids (contract section C):
  fr1:<column>                      every column of FR1_forecast_full.csv (model variables)
  fr1:acc:<entity>:<metric>         accounts (FR1_accounts_long.csv); metric real|deflator|nominal|*_growth_pct
  fr1:contrib:<comp>|total          contribution of each GDP component to real GDP growth, pp
  fr1:dec:<sector>:<driver>         decomposition of a sector's real growth into its drivers, pp
  fr1:cred:<sector>                 nominal credit by sector (households = G2; business credit at fixed shares)
  fr1:inv:<sector>                  real fixed investment by sector (calibrated shares x total), mln AZN 2015
"""
SEC_AZ = {"agr": "Kənd, meşə və balıqçılıq", "min": "Mədənçıxarma", "man": "Emal sənayesi",
          "elc": "Elektrik enerjisi, qaz", "wat": "Su təchizatı, tullantılar", "con": "Tikinti",
          "trd": "Ticarət; nəqliyyat vasitələrinin təmiri", "tou": "Turizm və ictimai iaşə",
          "tra": "Nəqliyyat və anbar", "ict": "İnformasiya və rabitə", "oth": "Sosial və digər xidmətlər",
          "nettax": "Məhsula xalis vergilər"}
SEC_EN = {"agr": "Agriculture, forestry & fishing", "min": "Mining & quarrying", "man": "Manufacturing",
          "elc": "Electricity, gas & steam", "wat": "Water supply & waste", "con": "Construction",
          "trd": "Trade & vehicle repair", "tou": "Tourism & catering", "tra": "Transport & storage",
          "ict": "Information & communication", "oth": "Social & other services", "nettax": "Net taxes on products"}

R15, NOM, PERS = "mln AZN, 2015 qiymətləri", "mln AZN, cari qiymətlər", "min nəfər"
# code: (label_az, label_en, unit_az, kind, group_az)
VAR = {
    "rgdp": ("Real ÜDM", "Real GDP", R15, "level", "Aqreqatlar"),
    "rgdpnon": ("Real qeyri-neft ÜDM", "Real non-oil GDP", R15, "level", "Aqreqatlar"),
    "rgdpoil": ("Real neft-qaz ÜDM", "Real oil-gas GDP", R15, "level", "Karbohidrogen bloku"),
    "rcons": ("Real istehlak (istehlak bazarı)", "Real consumption (consumer market)", R15, "level", "Tələb"),
    "rinv_non": ("Qeyri-neft investisiyaları (real)", "Real non-oil investment", R15, "level", "Tələb"),
    "rinv_tot": ("Əsas kapitala investisiyalar (real)", "Real fixed investment", R15, "level", "Tələb"),
    "rinv_priv": ("Qeyri-dövlət investisiyaları (real)", "Real non-state investment", R15, "level", "Tələb"),
    "rinv_state": ("Dövlət investisiyaları (real)", "Real state investment", R15, "level", "Fiskal blok"),
    "rx_non": ("Qeyri-neft mal ixracı (real)", "Real non-oil goods exports", R15, "level", "Xarici bazar"),
    "rm_non": ("Qeyri-neft mal idxalı (real)", "Real non-oil goods imports", R15, "level", "Xarici bazar"),
    "emp": ("Məşğul əhali", "Employment", PERS, "level", "Əmək bazarı"),
    "wage": ("Orta aylıq nominal əmək haqqı", "Average monthly nominal wage", "AZN/ay", "level", "Əmək bazarı"),
    "rwage": ("Real orta əmək haqqı", "Real average wage", "AZN/ay, 2015 qiymətləri", "level", "Əmək bazarı"),
    "rhhdisp": ("Ev təsərrüfatlarının real sərəncamda qalan gəliri", "Real household disposable income", R15,
                "level", "Gəlir"),
    "lf": ("İqtisadi fəal əhali", "Labour force", PERS, "level", "Əmək bazarı"),
    "unemp": ("İşsizlik səviyyəsi", "Unemployment rate", "%", "rate", "Əmək bazarı"),
    "rdep_tot": ("Depozitlər (real)", "Real deposits", R15, "level", "Kreditlər və depozitlər"),
    "rcred_tot": ("Kreditlər (real)", "Real credit to the economy", R15, "level", "Kreditlər və depozitlər"),
    "rcred_hh": ("Ev təsərrüfatlarına kreditlər (real)", "Real household credit", R15, "level",
                 "Kreditlər və depozitlər"),
    "lendrate": ("Kreditlər üzrə orta faiz dərəcəsi", "Average lending rate", "%", "rate", "Kreditlər və depozitlər"),
    "infl": ("İnflyasiya (İQİ)", "CPI inflation", "%", "rate", "Qiymətlər"),
    "gap": ("İstehsal boşluğu (təsviri)", "Output gap (descriptive)", "%", "rate", "Aqreqatlar"),
    "realrate": ("Real kredit faizi (ex post)", "Real lending rate (ex post)", "%", "rate", "Kreditlər və depozitlər"),
    "gdp_n": ("Nominal ÜDM", "Nominal GDP", NOM, "level", "Aqreqatlar"),
    "p_gdp": ("ÜDM deflyatoru", "GDP deflator", "2015 = 1", "index", "Qiymətlər"),
    "x_g_oil_usd": ("Neft-qaz ixracı", "Oil and gas exports", "mln ABŞ dolları", "level", "Karbohidrogen bloku"),
    "rev_oil_n": ("Neft-qaz büdcə gəlirləri", "Oil and gas budget revenue", NOM, "level", "Fiskal blok"),
    "rrev_nonoil": ("Qeyri-neft büdcə gəlirləri (real)", "Real non-oil budget revenue", R15, "level", "Fiskal blok"),
    "rev_tot_n": ("Büdcə gəlirləri", "Budget revenue", NOM, "level", "Fiskal blok"),
    "rexp_cur": ("Cari xərclər (real)", "Real current expenditure", R15, "level", "Fiskal blok"),
    "rexp_soc": ("Sosial xərclər (real)", "Real social expenditure", R15, "level", "Fiskal blok"),
    "exp_cap_n": ("Əsaslı xərclər", "Capital expenditure", NOM, "level", "Fiskal blok"),
    "exp_tot_n": ("Büdcə xərcləri", "Budget expenditure", NOM, "level", "Fiskal blok"),
    "balance_n": ("Büdcə balansı", "Budget balance", NOM, "level", "Fiskal blok"),
    "debt_azn": ("Dövlət borcu (xarici + daxili, Maliyyə Nazirliyinin anlayışı; dövlət zəmanətli borc daxil deyil)",
                 "Public debt (external + domestic, Ministry of Finance concept; excl. state-guaranteed debt)", NOM, "level", "Fiskal blok"),
    "debt_serv_n": ("Borc xidməti", "Debt service", NOM, "level", "Fiskal blok"),
    "rretail": ("Pərakəndə ticarət dövriyyəsi (real)", "Real retail trade turnover", R15, "level", "İstehlak bazarları"),
    "rcater": ("İctimai iaşə dövriyyəsi (real)", "Real catering turnover", R15, "level", "İstehlak bazarları"),
    "rserv_hh": ("Əhaliyə ödənişli xidmətlər (real)", "Real paid services to households", R15, "level",
                 "İstehlak bazarları"),
    "pension": ("Orta aylıq pensiya", "Average monthly pension", "AZN/ay", "level", "Gəlir"),
    "oil_exp_price": ("Neftin ixrac qiyməti", "Oil export price", "ABŞ dolları/barel", "level", "Karbohidrogen bloku"),
    "cpi": ("İstehlak qiymətləri indeksi", "Consumer price index", "2015 = 100", "index", "Qiymətlər"),
    "p_cons": ("İstehlak deflyatoru", "Consumption deflator", "2015 = 1", "index", "Qiymətlər"),
    "p_inv": ("İnvestisiya deflyatoru", "Investment deflator", "2015 = 1", "index", "Qiymətlər"),
    "K_non": ("Əsas fondlar: qeyri-neft iqtisadiyyatı", "Capital stock: non-oil economy", R15, "level",
              "Əsas fondlar"),
    "pop": ("Əhali", "Population", PERS, "level", "Demoqrafiya"),
    # v2.2
    "hhdisp_n": ("Ev təsərrüfatlarının sərəncamda qalan gəliri (nominal)", "Household disposable income (nominal)", NOM,
                 "level", "Gəlir"),
    "hhinc_n": ("Əhalinin pul gəlirləri (nominal)", "Household money income (nominal)", NOM, "level", "Gəlir"),
    "inc_wb_n": ("Gəlir: işçilərə əmək ödənişləri", "Income: compensation of employees", NOM, "level", "Gəlir"),
    "inc_tr_n": ("Gəlir: alınmış transfertlər", "Income: transfers received", NOM, "level", "Gəlir"),
    "inc_oth_n": ("Gəlir: sahibkarlıq və mülkiyyət gəlirləri", "Income: entrepreneurial and property income", NOM,
                  "level", "Gəlir"),
    "gdpnon_n": ("Qeyri-neft ÜDM (nominal)", "Non-oil GDP (nominal)", NOM, "level", "Aqreqatlar"),
    "nobd_pct": ("Qeyri-neft büdcə balansı, qeyri-neft ÜDM-ə nisbətən", "Non-oil budget balance, % of non-oil GDP",
                 "%", "rate", "Fiskal blok"),
    "exp_pubinv_n": ("Dövlət İnvestisiya Proqramı (dövlət əsaslı vəsait qoyuluşu)",
                     "State Investment Programme (public capital investment)", NOM, "level", "Fiskal blok"),
    "gas_exp_price": ("Qazın ixrac qiyməti", "Gas export price", "ABŞ dolları / min m³", "level", "Karbohidrogen bloku"),
    "xsh_oil": ("Neftin karbohidrogen ixracında payı (dəyərlə)", "Oil share of hydrocarbon export value", "pay (0–1)",
                "share", "Karbohidrogen bloku"),
    "dln_xpi": ("Karbohidrogen ixrac qiymətləri indeksinin dəyişməsi (ABŞ dolları)",
                "Hydrocarbon export price index, change (USD)", "%", "rate", "Karbohidrogen bloku"),
}
for _k, _az in (("retail", "Pərakəndə ticarət"), ("cater", "İctimai iaşə"), ("serv_hh", "Ödənişli xidmətlər")):
    _en = {"retail": "Retail trade", "cater": "Catering", "serv_hh": "Paid services"}[_k]
    VAR[f"p_{_k}"] = (f"Deflyator: {_az}", f"Deflator: {_en}", "2015 = 1", "index", "İstehlak bazarları")
    VAR[f"nom_{_k}"] = (f"{_az} (nominal)", f"{_en} (nominal)", NOM, "level", "İstehlak bazarları")
    VAR[f"share_{_k}"] = (f"{_az}: istehlak bazarında pay", f"{_en}: share of consumer market", "pay (0–1)",
                          "share", "İstehlak bazarları")
for _k in SEC_AZ:
    VAR[f"p_{_k}"] = (f"Deflyator: {SEC_AZ[_k]}", f"Deflator: {SEC_EN[_k]}", "2015 = 1", "index", "Qiymətlər")
    if _k != "nettax":
        VAR[f"K_{_k}"] = (f"Əsas fondlar: {SEC_AZ[_k]}", f"Capital stock: {SEC_EN[_k]}", R15, "level", "Əsas fondlar")
    VAR[f"rva_{_k}"] = (f"Real əlavə dəyər: {SEC_AZ[_k]}", f"Real value added: {SEC_EN[_k]}", R15, "level",
                        "Sektorlar (real əlavə dəyər)")

GROUP_AZ = {"1 Sectors (value added)": "Sektorlar (əlavə dəyər)", "2 Aggregates": "Aqreqatlar",
            "3 Consumer markets": "İstehlak bazarları", "4 Investment market": "İnvestisiya bazarı",
            "5 Labour market": "Əmək bazarı", "6 Credit and deposits": "Kreditlər və depozitlər",
            "7 External market": "Xarici bazar", "8 Fiscal": "Fiskal", "9 Prices": "Qiymətlər"}
METRIC_AZ = {"real": "real dəyər", "deflator": "deflyator", "nominal": "nominal dəyər",
             "real_growth_pct": "real artım, %", "deflator_growth_pct": "deflyator inflyasiyası, %",
             "nominal_growth_pct": "nominal artım, %"}
METRIC_EN = {"real": "real value", "deflator": "deflator", "nominal": "nominal value",
             "real_growth_pct": "real growth, %", "deflator_growth_pct": "deflator inflation, %",
             "nominal_growth_pct": "nominal growth, %"}
METRICS = ("real", "deflator", "nominal")
UNIT_AZ = {"mln AZN": "mln AZN", "thousand persons": PERS, "AZN per month": "AZN/ay", "%": "%",
           "2015 = 100": "2015 = 100", "2015 = 1": "2015 = 1"}

DRIVER = {"total_growth": "total", "trend (deterministic)": "trend", "scenario TFP boost": "tfp",
          "add-factor change (anchor)": "addf", "residual (interaction)": "resid",
          "population (unit elasticity)": "pop"}
DRIVER_AZ = {"total": "ümumi real artım", "trend": "deterministik trend", "tfp": "ssenari TFP əlavəsi",
             "addf": "düzəliş əmsalının dəyişməsi (ankor)", "resid": "qalıq (qarşılıqlı təsir)",
             "pop": "əhali (vahid elastiklik)", "K_man": "əsas fondlar (emal)", "K_agr": "əsas fondlar (k/t)",
             "rva_con": "tikinti əlavə dəyəri", "rx_non": "qeyri-neft ixracı", "rva_agr": "k/t əlavə dəyəri",
             "rgdpnon": "qeyri-neft ÜDM", "rgdpnon_pc": "adambaşına qeyri-neft ÜDM",
             "rinv_state": "dövlət investisiyaları", "rinv_priv": "qeyri-dövlət investisiyaları",
             "rcons": "istehlak", "rhhdisp_pc": "adambaşına real gəlir", "K_ict_pc": "adambaşına İKT fondları",
             "rm_non": "qeyri-neft idxalı", "hc": "karbohidrogen tranziti", "rcred_tot": "kreditlər",
             "trend_post2015": "trend (2015-dən sonra)"}
CRED_AZ = {"trd": "Ticarət və xidmət", "ene": "Energetika, kimya, təbii ehtiyatlar", "agr": "Kənd təsərrüfatı",
           "con": "Tikinti və daşınmaz əmlak", "ind": "Sənaye və istehsal", "tra": "Nəqliyyat və rabitə",
           "oth": "Digər (qalıq: cəmi − sektorlar − ev təsərrüfatları)"}
RATE_COLS = {"infl", "unemp", "lendrate", "realrate", "gap", "nobd_pct", "dln_xpi"}


def var_id(col):
    return f"fr1:{col}"


def acc_id(key, metric):
    return f"fr1:acc:{key}:{metric}"


def contrib_id(comp):
    return f"fr1:contrib:{comp}"


def dec_id(sector, driver):
    return f"fr1:dec:{sector}:{DRIVER.get(driver, driver)}"


def cred_id(sec):
    return f"fr1:cred:{sec}"


def inv_id(sec):
    return f"fr1:inv:{sec}"
