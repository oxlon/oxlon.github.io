"""p_meta.py — v2 meta bundle: tabs and plain-language intros, home KPIs (stable ids), glossary, not-forecast lists,
group order, FR10/FR12 early-warning lists, FR12 IO scenarios, build stamp."""
import datetime as dt
import hashlib
import os

from . import pcore as C
from .pnames import nace, GROUP_AZ, CHANGE_AZ

FRS = [
    dict(c="FR1", slug="fr1", t="Sektorlar", full="İqtisadi sektorlar və bazarlar", st="done", kpi=["fr1:rgdp", "fr1:rgdpnon"],
         lead="On iki sektorun real əlavə dəyəri, ÜDM, istehlak, investisiya, əmək bazarı, kredit, xarici ticarət, büdcə və qiymətlər.",
         intro="Bu bölmə sualı cavablandırır: neftin qiyməti, dövlət investisiyası və xarici tələb dəyişəndə iqtisadiyyatın hər sektoru "
               "2030-a qədər necə inkişaf edəcək? Model bütün sektorları bir sistem kimi həll edir; nəticələr digər beş modula ötürülür."),
    dict(c="FR3", slug="fr3", t="Əmək haqqı", full="Orta aylıq əmək haqqı", st="partial", kpi=["fr3:w_avg", "fr3:rw_avg"],
         lead="Ölkə ortası, dövlət/qeyri-dövlət, neft/qeyri-neft bölgüləri, sənaye sahələri və sektorlar üzrə muzdlu işçilər.",
         intro="Orta aylıq əmək haqqı məhsuldarlıq, qiymətlər və minimum əmək haqqı ilə izah olunur. Bölgülər (dövlət/qeyri-dövlət, "
               "neft/qeyri-neft) eyni milli ortaya uzlaşdırılır ki, hissələr cəmlə üst-üstə düşsün."),
    dict(c="FR4", slug="fr4", t="Məşğulluq", full="Əhalinin məşğulluq göstəriciləri", st="done", kpi=["fr4:emp:total", "fr4:state"],
         lead="19 fəaliyyət növü üzrə məşğul əhali və muzdlu işçilər, 8 qrup, dövlət/büdcə/neft bölgüləri.",
         intro="Ümumi məşğulluq FR1-dən gəlir; bu bölmə onu fəaliyyət növləri arasında bölür. Paylar sahənin real buraxılışına "
               "bağlıdır və həmişə müsbət qalır, cəmi isə ümumi məşğulluğa bərabərdir."),
    dict(c="FR5", slug="fr5", t="Xidmətlər", full="Əhaliyə göstərilən pullu xidmətlər", st="done", kpi=["fr5:vol:total", "fr5:val:total"],
         lead="Cəmi və 13 xidmət növü: real həcm, nominal dəyər, deflyator, pay; institusional bölgülər.",
         intro="Əhalinin pullu xidmətlərə xərci real gəlir və xidmətlərin nisbi qiyməti ilə izah olunur; 13 növ arasında bölgü "
               "tələb sistemi (LA-AIDS) ilə aparılır."),
    dict(c="FR10", slug="fr10", t="Müəssisələr", full="Müəssisələrin maliyyə vəziyyəti, effektivliyi və bazar payı", st="partial",
         kpi=["fr10:ind_output", "fr10:hhi_man"],
         lead="30 sənaye sahəsi, 4 bölmə, 14 iqtisadi rayon, bazar payları və məhsullar (A qatı — real məlumat). Müəssisə səviyyəsi sintetikdir.",
         intro="Sənaye sahələrinin buraxılışı, payları, əmək məhsuldarlığı, marjası və regional bölgüsü DSK məlumatı ilə proqnozlaşdırılır "
               "(A qatı). Müəssisə səviyyəsində ekonometrika (B qatı) Nazirlik real faylı yükləyənə qədər sintetik məlumatla nümayiş olunur."),
    dict(c="FR12", slug="fr12", t="Rəqabət", full="Rəqabət mühiti: giriş, çıxış, konsentrasiya", st="partial",
         kpi=["fr12:act:entry:ALL", "fr12:act:N:ALL"],
         lead="11 fəaliyyət qrupu, NACE bölmələri və 14 iqtisadi rayon üzrə giriş/çıxış, konsentrasiya hədləri, ssenari təhlili, erkən xəbərdarlıq.",
         intro="Bazara yeni müəssisələrin girişi, çıxışı və konsentrasiya (HHI, CR4) izlənir. Məlumatda boşluqlar olan illər "
               "interpolyasiya ilə doldurulub və qrafiklərdə boş dairə ilə göstərilir."),
]
SCEN_KEYS = ["fr1:rgdp", "fr1:rgdpnon", "fr1:cpi", "fr1:unemp", "fr3:w_avg", "fr4:emp:total", "fr5:vol:total",
             "fr10:ind_output", "fr10:hhi_man", "fr12:act:entry:ALL"]
GLOSS = [
    ("Əsas / Mənfi / İslahat", "FR1-in üç makro ssenarisi; bütün modullar onları istifadə edir."),
    ("Ssenari qurucusu", "Öz ssenarinizi yaratmaq: ekzogen fərziyyələri, əmsalları və alətləri dəyişib zənciri yenidən hesablamaq."),
    ("5–95 % zolağı", "Simulyasiyaların 90 %-nin düşdüyü aralıq: proqnozun dürüst qeyri-müəyyənliyi."),
    ("Tənlik", "Göstəricini izah edən qiymətləndirilmiş əlaqə: asılı dəyişən, izahedici dəyişənlər və əmsallar."),
    ("Əmsal ± standart xəta", "Qiymətləndirilmiş təsir və onun dəqiqliyi; 95 % etibarlılıq intervalı təxminən əmsal ± 2 standart xəta."),
    ("Determinasiya əmsalı (R²)", "Asılı dəyişənin dəyişkənliyinin tənliklə izah olunan payı (0–1)."),
    ("Kointeqrasiya", "Səviyyələr arasında uzunmüddətli tarazlıq əlaqəsi; p ≤ 0,10 olduqda müəyyən edilmiş sayılır."),
    ("Dayanıqlıq hökmü", "Stabil — əmsallar rekursiv və «bir ili çıxarmaqla» qiymətləndirmədə işarəsini saxlayır, struktur qırılma yoxdur; "
                         "qismən stabil — zəif əlamətlər var; qeyri-stabil — işarə dəyişir və ya qırılma güclüdür."),
    ("Tornado qrafiki", "Hər əmsal ±1 standart xəta dəyişəndə 2030-cu il proqnozunun neçə faiz dəyişdiyini göstərir."),
    ("Theil U", "Modelin xətası / sadə etalonun xətası. 1-dən kiçik — model etalondan yaxşıdır."),
    ("Təsadüfi gəzişmə / sabit artım", "Etalonlar: gələcək dəyər son müşahidəyə bərabərdir / keçmiş orta artımla davam edir."),
    ("Nümunədən kənar yoxlama", "Model seçimində toxunulmayan son illər; proqnoz dəqiqliyi orada yoxlanılır."),
    ("Doldurulmuş (interpolyasiya)", "Mənbədə olmayan il qonşu illər arasında interpolyasiya ilə doldurulub; qrafikdə boş dairə və qırıq xətt, cədvəldə kursiv."),
    ("Real / nominal / deflyator", "Real — sabit (2015) qiymətlərlə həcm; nominal — cari qiymətlərlə; deflyator — qiymət indeksi."),
    ("HHI", "Herfindahl–Hirschman indeksi: payların kvadratlarının cəmi (0–10 000); böyük dəyər — yüksək konsentrasiya."),
    ("Giriş / çıxış əmsalı", "Yeni qeydiyyatlar / ləğv edilənlər, qeydiyyatdakı vahidlərin faizi ilə."),
    ("Faiz bəndi (f.b.)", "İki faiz göstəricisi arasındakı fərq (məs. 5,0 %-dən 5,5 %-ə = +0,5 f.b.)."),
    ("Sintetik məlumat", "Uydurma, DSK cəmlərinə kalibrlənmiş test faylı; nəticəsi təhlil deyil, hesablama xəttinin nümayişidir."),
]


def _ew(tr):
    e = C.csv("FR10_early_warning.csv", dtype={"nace2": str})
    flags = [("F_negative_margin", "mənfi marja"), ("F_margin", "marjanın enişi"), ("F_share", "payın enişi"),
             ("F_productivity", "məhsuldarlığın enişi"), ("F_renewal", "investisiya"), ("F_stocks", "ehtiyatlar")]
    ew10 = [{"n": f"{r['nace2']} · {nace(r['nace2'])}", "share": C.fnum(r["share_2025_pct"]), "w": bool(r["watch_list"]),
             "fl": [lab for k, lab in flags if k in r and (r[k] is True or r[k] == "FLAG")], "nf": int(r["n_flags"])}
            for r in e.to_dict("records")]
    e12 = C.csv("FR12_early_warning.csv")
    f12 = [("F_conc", "konsentrasiya"), ("F_entry", "giriş"), ("F_exit", "çıxış"), ("F_mob", "mobillik"), ("F_margin_entry", "marja↑ giriş↓")]
    ew12 = [{"n": GROUP_AZ.get(r["group"], r["group"]), "score": C.fnum(r["score"]), "w": bool(r["watch_list"]),
             "fl": [lab for k, lab in f12 if k in r and str(r[k]).lower() in ("true", "yes")]} for r in e12.to_dict("records")]
    return ew10, ew12


def _io(tr):
    s, a = C.csv("FR12_scenario_summary.csv"), C.csv("FR12_scenario_assumptions.csv")
    out = []
    for i, r in enumerate(s.to_dict("records")):
        ch = a.loc[i, "change"] if i < len(a) else ""
        out.append({"s": r["scenario"], "m": GROUP_AZ.get(r["market"], r["market"]), "ch": CHANGE_AZ.get(ch, tr(ch)),
                    "as": tr(r["assumption"]), "src": "fərziyyə" if str(a.loc[i, "structure_source"]).startswith("ASSUMPTION") else "A qatı hədləri",
                    "h": [C.fnum(r["hhi_min"]), C.fnum(r["hhi_max"])], "p": [C.fnum(r["d_price_min"]), C.fnum(r["d_price_max"])],
                    "q": [C.fnum(r["d_output_min"]), C.fnum(r["d_output_max"])], "cs": [C.fnum(r["d_cs_pct_min"]), C.fnum(r["d_cs_pct_max"])]})
    return out


def _notfc(tr):
    out = {}
    for f in FRS:
        p = C.OUT / f"{f['c']}_not_forecast.csv"
        if not p.exists():
            continue
        d = C.csv(p.name, dtype=str, keep_default_na=False)
        out[f["c"]] = [{"id": r.get("id"), "l": tr(r.get("component_az") or r.get("label_az") or ""), "why": tr(r.get("reason_az", "")),
                        "alt": [x for x in (r.get("alternative_ids") or "").split(";") if x], "pat": bool(r.get("id_pattern"))}
                       for r in d.to_dict("records")]
    return out


def _why(nf, idx, syne):
    """One-line reason for every requirement marked 'partial', from the data: Layer B still on synthetic files,
    components the module does not forecast (FRx_not_forecast.csv), unstable equations among those used in the forecast."""
    out = {}
    for f in FRS:
        if f["st"] != "partial":
            continue
        parts = []
        if str(((syne or {}).get(f["c"]) or {}).get("mode", "")).upper() == "SYNTHETIC":
            parts.append("müəssisə səviyyəsi (B qatı) hələ sintetik məlumatla")
        rows = nf.get(f["c"], [])
        if rows:
            grp = any(r.get("pat") for r in rows)
            parts.append(f"{len(rows)} göstərici{' qrupu' if grp else ''} proqnozlaşdırılmır")
        used = [e for e in idx or [] if e.get("f") == f["c"] and e.get("used")]
        bad = sum(1 for e in used if e.get("v") == "qeyri-stabil")
        if used and bad:
            parts.append(f"qeyri-stabil tənlik: {bad} / {len(used)}")
        if parts:
            out[f["c"]] = " · ".join(parts)
    return out


def build(data_dir, ids, groups, tr, extra=None, idx=None, syne=None):
    for f in FRS:
        for k in f["kpi"]:
            if k not in ids:
                raise SystemExit(f"build_panel: home KPI series not found: {k}")
    for k in SCEN_KEYS:
        if k not in ids:
            raise SystemExit(f"build_panel: scenario-comparison series not found: {k}")
    ew10, ew12 = _ew(tr)
    files = sorted(C.USED)
    h = hashlib.md5()
    for f in files:
        h.update((C.OUT / f).read_bytes())
    sde = os.environ.get("SOURCE_DATE_EPOCH")
    date = dt.datetime.fromtimestamp(int(sde), dt.timezone.utc).strftime("%Y-%m-%d") if sde else dt.date.today().isoformat()
    nf = _notfc(tr)
    idx = idx if idx is not None else (C.BUNDLES.get("EQI") or {}).get("rows")
    syne = syne if syne is not None else C.BUNDLES.get("SYNE")
    meta = {"frs": FRS, "scen": SCEN_KEYS, "gloss": GLOSS, "ew10": ew10, "ew12": ew12, "io": _io(tr), "nf": nf,
            "why": _why(nf, idx, syne), "groups": groups, "stamp": {"md5": h.hexdigest()[:12], "date": date, "files": len(files)}}
    meta.update(extra or {})
    C.js_bundle(data_dir / "meta.js", "META", meta)
    return meta
