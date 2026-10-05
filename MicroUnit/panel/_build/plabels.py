"""plabels.py — Azerbaijani names for codes that the outputs carry in English (names only, no numbers)."""
SEC12 = {"agr": "Kənd, meşə və balıqçılıq", "min": "Mədənçıxarma", "man": "Emal sənayesi", "elc": "Elektrik enerjisi, qaz",
         "wat": "Su təchizatı, tullantılar", "con": "Tikinti", "trd": "Ticarət; nəqliyyat vasitələrinin təmiri",
         "tou": "Turizm və ictimai iaşə", "tra": "Nəqliyyat və anbar", "ict": "İnformasiya və rabitə",
         "oth": "Sosial və digər xidmətlər", "nettax": "Məhsula xalis vergilər", "non": "Qeyri-neft sektorları"}
FR1_VAR = {
    "rgdp": "Real ÜDM", "rgdpnon": "Real qeyri-neft ÜDM", "rgdpoil": "Real neft-qaz ÜDM", "rcons": "Real istehlak",
    "rinv_non": "Qeyri-neft investisiyaları (real)", "rinv_tot": "Əsas kapitala investisiyalar (real)",
    "rinv_priv": "Özəl investisiyalar (real)", "rinv_state": "Dövlət investisiyaları (real)",
    "rx_non": "Qeyri-neft ixracı (real)", "rm_non": "Qeyri-neft idxalı (real)", "emp": "Məşğul əhali",
    "wage": "Orta aylıq əmək haqqı", "rwage": "Real orta əmək haqqı", "rhhdisp": "Ev təsərrüfatlarının real gəliri",
    "lf": "İqtisadi fəal əhali", "unemp": "İşsizlik səviyyəsi", "rdep_tot": "Depozitlər (real)",
    "rcred_tot": "Kreditlər (real)", "rcred_hh": "Ev təsərrüfatlarına kreditlər (real)", "lendrate": "Kredit faizi",
    "infl": "İnflyasiya", "gap": "İstehsal boşluğu", "realrate": "Real faiz dərəcəsi", "gdp_n": "Nominal ÜDM",
    "p_gdp": "ÜDM deflyatoru", "x_g_oil_usd": "Neft-qaz ixracı, mln USD", "rev_oil_n": "Neft-qaz büdcə gəlirləri",
    "rrev_nonoil": "Qeyri-neft büdcə gəlirləri (real)", "rev_tot_n": "Büdcə gəlirləri", "rexp_cur": "Cari xərclər (real)",
    "rexp_soc": "Sosial xərclər (real)", "exp_cap_n": "Əsaslı xərclər", "exp_tot_n": "Büdcə xərcləri",
    "balance_n": "Büdcə balansı", "debt_azn": "Dövlət borcu", "rretail": "Pərakəndə ticarət (real)",
    "rcater": "İctimai iaşə (real)", "rserv_hh": "Əhaliyə pullu xidmətlər (real)", "pension": "Orta pensiya",
    "oil_exp_price": "Neftin ixrac qiyməti", "cpi": "İstehlak qiymətləri indeksi", "p_cons": "İstehlak deflyatoru",
    "p_inv": "İnvestisiya deflyatoru", "p_retail": "Pərakəndə ticarət deflyatoru", "nom_retail": "Pərakəndə ticarət (nominal)",
    "share_retail": "Pərakəndə ticarətin payı", "p_cater": "İaşə deflyatoru", "nom_cater": "İctimai iaşə (nominal)",
    "share_cater": "İaşənin payı", "p_serv_hh": "Xidmətlər deflyatoru", "nom_serv_hh": "Pullu xidmətlər (nominal)",
    "share_serv_hh": "Pullu xidmətlərin payı", "debt_serv_n": "Borc xidməti", "pop": "Əhali"}
for _k, _n in SEC12.items():
    FR1_VAR[f"rva_{_k}"] = f"Əlavə dəyər (real): {_n}"
    FR1_VAR[f"K_{_k}"] = f"Əsas fondlar: {_n}"
    FR1_VAR[f"p_{_k}"] = f"Deflyator: {_n}"
FR1_RATE = {"infl", "unemp", "gap", "realrate", "lendrate", "share_retail", "share_cater", "share_serv_hh"}
FR1_GROUP = {"1 Sectors (value added)": "Sektorlar (əlavə dəyər)", "2 Aggregates": "Aqreqatlar",
             "3 Consumer markets": "İstehlak bazarları", "4 Investment market": "İnvestisiya bazarı",
             "5 Labour market": "Əmək bazarı", "6 Credit and deposits": "Kreditlər və depozitlər",
             "7 External market": "Xarici bazar", "8 Fiscal": "Fiskal", "9 Prices": "Qiymətlər"}
METRIC = {"real": "Real", "nominal": "Nominal", "deflator": "Deflyator"}
UNIT_AZ = {"mln AZN": "mln AZN", "thousand persons": "min nəfər", "AZN per month": "AZN/ay", "%": "%",
           "2015 = 100": "2015 = 100", "2015 = 1": "2015 = 1"}
SCEN_AZ = {"B": "Əsas", "A": "Mənfi", "R": "İslahat"}

FR4_ACT = {"agr": "Kənd, meşə və balıqçılıq", "mining": "Mədənçıxarma", "manuf": "Emal sənayesi",
           "elec": "Elektrik enerjisi, qaz", "water": "Su təchizatı", "constr": "Tikinti", "trade": "Ticarət və təmir",
           "transp": "Nəqliyyat və anbar", "hotel": "Yerləşdirmə və iaşə", "ict": "İnformasiya və rabitə",
           "fin": "Maliyyə və sığorta", "realest": "Daşınmaz əmlak", "prof": "Peşə, elmi və texniki fəaliyyət",
           "admsup": "İnzibati və yardımçı xidmətlər", "pubadm": "Dövlət idarəetməsi və müdafiə", "educ": "Təhsil",
           "health": "Səhiyyə və sosial xidmətlər", "art": "İncəsənət, əyləncə", "othsvc": "Digər xidmətlər",
           "total": "Cəmi"}
FR3_SEC = {"ind": "Sənaye", "agr": "Kənd təsərrüfatı", "con": "Tikinti", "trd": "Ticarət", "tou": "Turizm və iaşə",
           "tra": "Nəqliyyat", "ict": "İnformasiya və rabitə", "oth": "Digər xidmətlər"}
