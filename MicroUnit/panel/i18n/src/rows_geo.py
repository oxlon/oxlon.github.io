# az.csv source rows (part 3): English spellings of the 14 economic regions that the FR10/FR12 registries carry in
# coefficient labels, equation titles and synthetic-model terms, and the short regressor tags of the FR12 panel
# equation titles («— FE + reg + lend»). (mode, en, az)
# The region rules never touch identifiers: not after ':', '|', '/', '.', '_' or '-' (fr12:reg:new:Shirvan-Salyan,
# reg_Shaki-Zagatala, …:reg_sh|Mil-Mughan) and not before two spaces (aligned columns of the text-format summary).
import re

_REG = [
    ("Baku city", "Bakı şəhəri"), ("Nakhchivan AR", "Naxçıvan MR"), ("Absheron-Khizi", "Abşeron-Xızı"),
    ("Daghlig Shirvan", "Dağlıq Şirvan"), ("Ganja-Dashkasan", "Gəncə-Daşkəsən"), ("Garabagh", "Qarabağ"),
    ("Gazakh-Tovuz", "Qazax-Tovuz"), ("Guba-Khachmaz", "Quba-Xaçmaz"), ("Lankaran-Astara", "Lənkəran-Astara"),
    ("Central Aran", "Mərkəzi Aran"), ("Mil-Mughan", "Mil-Muğan"), ("Shaki-Zagatala", "Şəki-Zaqatala"),
    ("Eastern Zangezur", "Şərqi Zəngəzur"), ("Shirvan-Salyan", "Şirvan-Salyan"),
]
_PRE, _POST = r"(?<![\w:|/.\-])", r"(?![\w\-])(?! {2})"

ROWS = [("regex", _PRE + re.escape(en) + _POST, az) for en, az in _REG] + [
    ("regex", _PRE + r"Nakhchivan(?! AR)" + _POST, "Naxçıvan"),
    ("phrase", "SYNTHETIC panel üzrə", "sintetik panel üzrə"),
] + [
    ("regex", r"(— FE[^\n\[]*?\+ )" + tag + r"\b", r"\g<1>" + az)
    for tag, az in (("reg", "regional buraxılış"), ("non", "qeyri-neft ÜDM"), ("lend", "kredit faizi"),
                    ("cred", "kredit artımı"), ("dem", "tələb"), ("pcm", "marja"), ("brk", "tərif qırılması"),
                    ("d2022", "2022 impulsu"))
]
