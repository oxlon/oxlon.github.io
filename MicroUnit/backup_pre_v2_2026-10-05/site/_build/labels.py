"""labels.py — Azerbaijani labels for codes that the output files carry in English.

Only names are translated here; no number is ever typed in this file.
"""
NACE_AZ = {
    "06": "Xam neft və təbii qaz hasilatı", "07": "Metal filizlərinin hasilatı", "08": "Digər faydalı qazıntılar",
    "09": "Mədənçıxarma sahəsində xidmətlər", "10": "Qida məhsulları", "11": "İçkilər", "12": "Tütün məmulatları",
    "13": "Toxuculuq", "14": "Geyim", "15": "Dəri və ayaqqabı", "16": "Ağac emalı", "17": "Kağız və karton",
    "18": "Poliqrafiya", "19": "Neft emalı məhsulları", "20": "Kimya məhsulları", "21": "Əczaçılıq məhsulları",
    "22": "Rezin və plastik kütlə", "23": "Digər qeyri-metal mineral məhsullar", "24": "Metallurgiya",
    "25": "Hazır metal məmulatları", "26": "Kompüter və elektronika", "27": "Elektrik avadanlığı",
    "28": "Maşın və avadanlıq", "29": "Avtomobil və qoşqular", "30": "Digər nəqliyyat vasitələri", "31": "Mebel",
    "32": "Digər hazır məmulatlar", "33": "Maşın və avadanlığın təmiri və quraşdırılması",
    "35": "Elektrik enerjisi, qaz və buxar", "36": "Su təchizatı",
    "B": "Mədənçıxarma", "C": "Emal sənayesi", "D": "Elektrik enerjisi, qaz və buxar", "E": "Su təchizatı, tullantılar",
}
SEC_EN_AZ = {"Mining": "Mədənçıxarma", "Manufacturing": "Emal sənayesi", "Electricity": "Elektrik enerjisi, qaz və buxar",
             "Water": "Su təchizatı, tullantılar", "Industry": "Sənaye, cəmi"}
GROUP_AZ = {"AGR": "Kənd təsərrüfatı", "IND": "Sənaye", "CON": "Tikinti", "TRD": "Ticarət", "TRA": "Nəqliyyat",
            "ACC": "Yerləşdirmə və iaşə", "ICT": "İnformasiya və rabitə", "REA": "Daşınmaz əmlak", "EDU": "Təhsil",
            "HEA": "Səhiyyə və sosial xidmətlər", "OTH": "Digər sahələr", "ALL": "Bütün sahələr",
            "MOB": "Mobil rabitə", "BNK": "Bank sektoru", "CEM": "Sement"}
REGION_AZ = {"Baku city": "Bakı şəhəri", "Absheron-Khizi": "Abşeron-Xızı", "Central Aran": "Mərkəzi Aran",
             "Daghlig Shirvan": "Dağlıq Şirvan", "East Zangezur": "Şərqi Zəngəzur", "Ganja-Dashkasan": "Gəncə-Daşkəsən",
             "Gazakh-Tovuz": "Qazax-Tovuz", "Guba-Khachmaz": "Quba-Xaçmaz", "Karabakh": "Qarabağ", "Garabagh": "Qarabağ",
             "Lankaran-Astara": "Lənkəran-Astara", "Mil-Mughan": "Mil-Muğan", "Nakhchivan": "Naxçıvan",
             "Nakhchivan AR": "Naxçıvan MR", "Shaki-Zagatala": "Şəki-Zaqatala", "Shirvan-Salyan": "Şirvan-Salyan"}
STATUS_AZ = {"available now": ("done", "mövcuddur"), "requested": ("partial", "tələb olunub"),
             "not available": ("gap", "mövcud deyil")}
PILLAR_AZ = {"market position": "Bazar mövqeyi", "financial condition": "Maliyyə vəziyyəti",
             "production efficiency": "İstehsal effektivliyi", "Concentration and intensity": "Konsentrasiya və intensivlik",
             "Entry and exit": "Giriş və çıxış", "Barriers and regulation": "Maneələr və tənzimləmə",
             "Firm level (Layer B)": "Müəssisə səviyyəsi (B qatı)", "Margins and market power": "Marjalar və bazar gücü"}
CHANGE_AZ = {"Entry-barrier reduction / licensing simplification": "Giriş maneələrinin azaldılması / lisenziyalaşdırmanın sadələşdirilməsi",
             "Entry of a 4th mobile operator": "Dördüncü mobil operatorun girişi",
             "Merger of two firms": "İki müəssisənin birləşməsi", "Merger of two banks": "İki bankın birləşməsi",
             "Cost shock / excise or tax increase": "Xərc şoku / aksiz və ya vergi artımı",
             "Energy-cost shock": "Enerji xərcləri şoku", "Import competition (tariff cut)": "İdxal rəqabəti (tarifin azaldılması)",
             "SOE partial privatisation (mixed oligopoly)": "Dövlət müəssisəsinin qismən özəlləşdirilməsi (qarışıq oliqopoliya)",
             "SOE full privatisation (mixed oligopoly)": "Dövlət müəssisəsinin tam özəlləşdirilməsi (qarışıq oliqopoliya)"}


def nace(code):
    c = str(code)
    c = c.zfill(2) if c.isdigit() else c
    return NACE_AZ.get(c, c)


def status(s):
    s = str(s)
    for k, (cls, lab) in STATUS_AZ.items():
        if s.startswith(k):
            return cls, lab
    return "neutral", s
