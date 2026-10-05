"""p_meta.py — tab definitions, home KPIs, drawer texts, FR10/FR12 early-warning lists, FR12 IO scenarios, glossary."""
import datetime as dt
import hashlib
import os

from . import pcore as C
from .pinfo import I
from .pnames import nace, GROUP_AZ, CHANGE_AZ

FRS = [
    dict(c="FR1", slug="fr1", t="Sektorlar", full="İqtisadi sektorlar və bazarlar", st="done",
         kpi=["FR1|Aqreqatlar|ÜDM|Real", "FR1|Aqreqatlar|Qeyri neft-qaz ÜDM|Real"],
         lead="On iki DSK sektoru, aqreqatlar, bazarlar, əmək, kredit, xarici və fiskal göstəricilər — real, nominal və deflyator."),
    dict(c="FR3", slug="fr3", t="Əmək haqqı", full="Orta aylıq əmək haqqı", st="partial",
         kpi=["FR3|Bölgülər üzrə əmək haqqı|Orta aylıq əmək haqqı|Nominal",
              "FR3|Bölgülər üzrə əmək haqqı|Orta aylıq əmək haqqı|Real (2015 qiymətləri)"],
         lead="Ölkə ortası, dövlət/qeyri-dövlət, neft/qeyri-neft; sənaye sahələri; sektorlar və büdcə üzrə orta əmək haqqı mənbələrdə yoxdur."),
    dict(c="FR4", slug="fr4", t="Məşğulluq", full="Əhalinin məşğulluq göstəriciləri", st="done",
         kpi=["FR4|19 fəaliyyət növü|Cəmi|Məşğul əhali", "FR4|İnstitusional bölgülər|Dövlət sektoru|"],
         lead="19 fəaliyyət növü (məşğul əhali və muzdlu işçilər), 8 qrup, dövlət/büdcə/neft bölgüləri."),
    dict(c="FR5", slug="fr5", t="Xidmətlər", full="Əhaliyə göstərilən pullu xidmətlər", st="done",
         kpi=["FR5|Cəmi|Pullu xidmətlər, cəmi|Real həcm", "FR5|Cəmi|Pullu xidmətlər, cəmi|Nominal dəyər"],
         lead="Cəmi və 13 xidmət növü: real həcm, nominal dəyər, deflyator, pay; institusional bölgülər."),
    dict(c="FR10", slug="fr10", t="Müəssisələr", full="Müəssisələrin maliyyə vəziyyəti, effektivliyi və bazar payı", st="partial",
         kpi=["FR10|Sənaye bölmələri|Sənaye, cəmi (4 bölmə)|Buraxılış", "FR10|Bazar mövqeyi|Emal sahələri üzrə HHI|"],
         lead="30 sənaye sahəsi, 4 bölmə, 14 region, bazar payları, məhsullar (A qatı — real məlumat). Müəssisə səviyyəsi sintetikdir."),
    dict(c="FR12", slug="fr12", t="Rəqabət", full="Rəqabət mühiti: giriş, çıxış, konsentrasiya", st="partial",
         kpi=["FR12|Fəaliyyət qrupları: giriş və çıxış|Bütün sahələr|Giriş əmsalı",
              "FR12|Fəaliyyət qrupları: giriş və çıxış|Bütün sahələr|Qeydiyyatdakı vahidlər"],
         lead="11 fəaliyyət qrupu və 14 region üzrə giriş/çıxış, konsentrasiya hədləri, ssenari təhlili, erkən xəbərdarlıq."),
]
SCEN_KEYS = ["FR1|Aqreqatlar|ÜDM|Real", "FR1|Aqreqatlar|Qeyri neft-qaz ÜDM|Real", "FR1|Qiymətlər|İstehlak qiymətləri indeksi|Nominal",
             "FR1|Əmək bazarı|İşsizlik səviyyəsi|", "FR3|Bölgülər üzrə əmək haqqı|Orta aylıq əmək haqqı|Nominal",
             "FR4|19 fəaliyyət növü|Cəmi|Məşğul əhali", "FR5|Cəmi|Pullu xidmətlər, cəmi|Real həcm",
             "FR10|Sənaye bölmələri|Sənaye, cəmi (4 bölmə)|Buraxılış", "FR10|Sənaye bölmələri|Emal sənayesi|Buraxılış",
             "FR12|Fəaliyyət qrupları: giriş və çıxış|Bütün sahələr|Giriş əmsalı"]
GLOSS = [
    ("Əsas / Mənfi / İslahat", "FR1-in üç makro ssenarisi (Baseline / Adverse / Reform); bütün modullar onları istifadə edir."),
    ("5–95 % zolağı", "Simulyasiyaların 90 %-nin düşdüyü aralıq: proqnozun dürüst qeyri-müəyyənliyi."),
    ("Theil U", "Modelin xətası / sadə etalonun xətası. 1-dən kiçik — model etalondan yaxşıdır."),
    ("Təsadüfi gəzişmə", "Etalon: gələcək dəyər son müşahidəyə bərabərdir."),
    ("Sabit artım", "Etalon: gələcək artım keçmiş ortalama artıma bərabərdir."),
    ("Hold-out", "Model seçimində toxunulmayan son illər; proqnoz dəqiqliyi orada yoxlanılır."),
    ("Real / nominal / deflyator", "Real — sabit (2015) qiymətlərlə həcm; nominal — cari qiymətlərlə; deflyator — qiymət indeksi."),
    ("HHI", "Herfindahl–Hirschman indeksi: payların kvadratlarının cəmi (0–10 000); böyük dəyər — yüksək konsentrasiya."),
    ("Giriş / çıxış əmsalı", "Yeni qeydiyyatlar / ləğv edilənlər, qeydiyyatdakı vahidlərin faizi ilə."),
    ("Faiz bəndi", "İki faiz göstəricisi arasındakı fərq (məs. 5,0 %-dən 5,5 %-ə = +0,5 f.b.)."),
    ("Sintetik məlumat", "Uydurma, DSK cəmlərinə kalibrlənmiş test faylı; nəticəsi təhlil deyil, boru xəttinin nümayişidir."),
]


def _ew():
    e = C.csv("FR10_early_warning.csv", dtype={"nace2": str})
    flags = [("F_negative_margin", "mənfi marja"), ("F_margin", "marjanın enişi"), ("F_share", "payın enişi"),
             ("F_productivity", "məhsuldarlığın enişi"), ("F_renewal", "investisiya"), ("F_stocks", "ehtiyatlar")]
    ew10 = [{"n": f"{r['nace2']} · {nace(r['nace2'])}", "share": C.fnum(r["share_2025_pct"]), "w": bool(r["watch_list"]),
             "fl": [lab for k, lab in flags if r[k] is True or r[k] == "FLAG"], "nf": int(r["n_flags"])} for r in e.to_dict("records")]
    e12 = C.csv("FR12_early_warning.csv")
    f12 = [("F_conc", "konsentrasiya"), ("F_entry", "giriş"), ("F_exit", "çıxış"), ("F_mob", "mobillik"), ("F_margin_entry", "marja↑ giriş↓")]
    ew12 = [{"n": GROUP_AZ.get(r["group"], r["group"]), "score": C.fnum(r["score"]), "w": bool(r["watch_list"]),
             "fl": [lab for k, lab in f12 if str(r[k]).lower() in ("true", "yes")]} for r in e12.to_dict("records")]
    return ew10, ew12


def _io():
    s, a = C.csv("FR12_scenario_summary.csv"), C.csv("FR12_scenario_assumptions.csv")
    out = []
    for i, r in enumerate(s.to_dict("records")):
        out.append({"s": r["scenario"], "m": GROUP_AZ.get(r["market"], r["market"]), "ch": CHANGE_AZ.get(a.loc[i, "change"], a.loc[i, "change"]),
                    "as": r["assumption"], "src": "fərziyyə" if str(a.loc[i, "structure_source"]).startswith("ASSUMPTION") else "A qatı hədləri",
                    "h": [C.fnum(r["hhi_min"]), C.fnum(r["hhi_max"])], "p": [C.fnum(r["d_price_min"]), C.fnum(r["d_price_max"])],
                    "q": [C.fnum(r["d_output_min"]), C.fnum(r["d_output_max"])], "cs": [C.fnum(r["d_cs_pct_min"]), C.fnum(r["d_cs_pct_max"])]})
    return out


def build(data_dir, ids):
    for f in FRS:
        for k in f["kpi"]:
            if k not in ids:
                raise SystemExit(f"build_panel: home KPI series not found: {k}")
    for k in SCEN_KEYS:
        if k not in ids:
            raise SystemExit(f"build_panel: scenario-comparison series not found: {k}")
    ew10, ew12 = _ew()
    files = sorted(C.USED)
    h = hashlib.md5()
    for f in files:
        h.update((C.OUT / f).read_bytes())
    sde = os.environ.get("SOURCE_DATE_EPOCH")
    date = dt.datetime.utcfromtimestamp(int(sde)).strftime("%Y-%m-%d") if sde else dt.date.today().isoformat()
    meta = {"frs": FRS, "info": I, "scen": SCEN_KEYS, "gloss": GLOSS, "ew10": ew10, "ew12": ew12, "io": _io(),
            "stamp": {"md5": h.hexdigest()[:12], "date": date, "files": len(files)}}
    C.js_bundle(data_dir / "meta.js", "META", meta)
    return meta
