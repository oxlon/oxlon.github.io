"""NFR1 deviation report `docs/Sapma_hesabati.md` (Azerbaijani), generated ONLY from the V_nfr1_ outputs
and the event register — numbers are never typed into this module. Static texts below describe
mechanisms and limitations (no numbers); result-dependent sentences are built from the outputs."""
from __future__ import annotations

import math
import time

import pandas as pd

from . import config
from . import nfr1_data as D
from . import nfr1_models as M

DOC = config.DOCS / "Sapma_hesabati.md"
CF_AZ = {"pre2": "hadisədən əvvəlki 2 ilin ortası (o vaxtkı informasiya dəsti)",
         "pre1": "hadisədən əvvəlki il (təsadüfi gəzinti)",
         "trend2": "son 2 ilin xətti trendi", "zero": "sıfır (sadə fərq)",
         "flat10": "son 10 ildə minimum əmək haqqının dəyişmədiyi illərdə dövlət − qeyri-dövlət fərqinin ortası (DiD paralel trend)",
         "file": "IO/mikrosimulyasiya agentinin faylındakı əks-faktual (tənzimlənən qiymət: 0; bazar maddəsi: 2023 artımı; siyasətsiz paylanma)"}
KIND_UNIT = {"growth": "f.b. (artım)", "rate": "f.b.", "level_pp": "f.b.", "cumlevel": "% (səviyyə)",
             "did": "f.b. (fərq)", "io_e7": "f.b.", "ms_file": "f.b. (pay)"}
MECH_AZ = {
    "E1": "Minimum əmək haqqı FR1 E2 (orta maaş), FR3 E4 (dövlət sektoru maaşı) və G4 (maaş → İQİ) tənlikləri ilə ötürülür; "
          "mikrosimulyasiya statik ilk dövrə qaydalarını və formallaşma üçün davranış qatını tətbiq edir. Vergi islahatının "
          "formallaşma (bəyan edilən maaş və muzdlu məşğulluq) kanalı MikroUnit zəncirində yoxdur; büdcə maaşlarının ayrıca "
          "artımı modelləşdirilməyib — dövlət sektoru üzrə fakt həm də bu artımları ehtiva edir.",
    "E3": "Eyni kanallar; 2024 minimum əmək haqqının dəyişmədiyi ildir (plasebo: gözlənilən siyasət təsiri sıfırdır). 2022-də "
          "qlobal inflyasiya şoku və büdcə təşkilatlarında əlavə maaş artımları ilə qarışıqlıq var. 2025 sətirləri E2-nin "
          "qiymətləndirmə nümunəsindən kənardır (yeganə həqiqi nümunədən kənar makro yoxlama).",
    "E5": "Məzənnə FR1 G4 tənliyində (cari və gecikmiş məzənnə dəyişməsi) inflyasiyaya, oradan real maaşa ötürülür; IO qiymət "
          "modeli idxal qiymətlərinin tam və dərhal ötürülməsini fərz edir (yuxarı hədd). Eyni dövrdə neft qiymətinin "
          "çöküşü baş verib — real göstəricilərdə siyasət təsirini ayırmaq mümkün deyil.",
    "E7": "IO qiymət modeli tənzimlənən qiymətlərin birbaşa və dolayı (aralıq istehlak) ötürülməsini hesablayır; MikroUnit "
          "overlay və CAEM yalnız yanacaq şokunu İQİ səviyyəsinə ötürür (avtobus/metro və tullantı tarifləri onlarda yoxdur).",
}
LIMITS_AZ = [
    "Parametrlər tam nümunə üzrədir: hadisədən əvvəlki məlumatla yenidən qiymətləndirmə aparılmayıb, OxLon/Nazirlik "
    "proqnoz vintajları (hadisədən əvvəlki rəsmi proqnoz) layihədə yoxdur, CAEM-də vintaj yoxdur → nümunədaxili hadisələr "
    "proqnoz gücünü deyil, struktur uyğunluğu yoxlayır (Blueprint «Option 2 — honest»).",
    "Bütün fakt dəyərləri cari (yenidən işlənmiş) DSK/AMB vintajıdır; ilkin dərc dəyərləri arxivləşdirilməyib.",
    "Köçürülmüş şok: tarixi alət yolu MikroUnit-in cari (2026–2030) strukturuna tətbiq edilir; hadisə ili zəncirin "
    "2027-ci ilinə uyğunlaşdırılır, çünki FR3-də 2026 nowcast ilə bağlanıb və ilk il reaksiya vermir.",
    "Model intervalı yalnız əsas əmsalların standart xətalarından (delta metodu, kovariasiyalar nəzərə alınmadan) qurulur; "
    "IO intervalı cədvəl ili / yanacaq qarışığı həssaslığıdır; CAEM və overlay üçün statistik interval yoxdur.",
    "Mikrosimulyasiya SİNTETİK ev təsərrüfatı faylı ilə işləyir — real ev təsərrüfatı məlumatı deyil.",
]


def fmt(x, d=1, sign=False) -> str:
    try:
        x = float(x)
    except (TypeError, ValueError):
        return str(x) if x not in (None, "") else "—"
    if not math.isfinite(x):
        return "—"
    s = f"{abs(x):,.{d}f}".replace(",", " ").replace(".", ",")
    return ("−" if x < 0 else ("+" if sign and x > 0 else "")) + s


def _s(v) -> str:
    if v is None or (isinstance(v, float) and not math.isfinite(v)) or v == "":
        return "—"
    return str(v)


def table(head, rows) -> list[str]:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(_s(c).replace("|", "\\|") for c in r) + " |" for r in rows]
    return out + [""]


def _read(name) -> pd.DataFrame:
    p = config.OUTPUT / name
    return pd.read_csv(p, keep_default_na=False, na_values=[""]) if p.exists() else pd.DataFrame()


def _rng(r) -> str:
    lo, hi = r.get("pred_lo"), r.get("pred_hi")
    return f"[{fmt(lo)}; {fmt(hi)}]" if pd.notna(lo) and pd.notna(hi) else "—"


def _cls(r) -> str:
    c = r["class_az"]
    return f"**{c}**" if r["score"] >= 0 else c


def _sentence(r) -> str:
    """Result-dependent explanation of one primary comparison."""
    if r["score"] < 0:
        return (f"{r['label_az']} ({r['year']}, {r['method_az']}): müşahidə olunan təsir {fmt(r['obs_effect'])} "
                f"əks-faktualın səs-küyündən (σ = {fmt(r['sigma_cf'])}) kiçikdir — test aşağı güclüdür; proqnoz "
                f"{fmt(r['pred'])}, sapma {fmt(r['error'], sign=True)}.")
    way = "artıq" if r["error"] > 0 else "az"
    return (f"{r['label_az']} ({r['year']}, {r['method_az']}): proqnoz {fmt(r['pred'])}, fakt {fmt(r['obs_effect'])} — "
            f"model təsiri {fmt(abs(r['pct_error']), 0)} % {way} qiymətləndirir (sapma {fmt(r['error'], sign=True)}); "
            f"sinif: {r['class_az']}" + (f"; alternativ əks-faktualla: {r['class_alt_cf']}" if isinstance(r.get("class_alt_cf"), str) else "") + ".")


def _event_section(eid, ev, obs, cmp, evs) -> list[str]:
    e = ev[ev.event_id == eid].iloc[0]
    s = evs[evs.event_id == eid].iloc[0]
    g = cmp[cmp.event_id == eid]
    L = [f"### {eid}. {e['event_name_az']}", "",
         f"- **Siyasət:** {e['instruments_az']}", f"- **Tarix:** {e['event_date_az']}; **hüquqi əsas:** {e['legal_source']}",
         f"- **Nümunə statusu:** {'nümunədaxili' if 'bəli' in s['in_sample'] else ''}"
         f"{' / ' if '/' in s['in_sample'] else ''}{'nümunədən kənar' if 'xeyr' in s['in_sample'] else ''} — "
         f"{'; '.join(dict.fromkeys(ev[ev.event_id == eid]['in_sample_note_az']))}",
         f"- **Modellər:** " + "; ".join(M.METHOD_LABEL_AZ[m] for m in s["methods"].split(";")),
         f"- **Ötürmə mexanizmi və qarışıqlıq:** {MECH_AZ.get(eid, '')}", "", "**Məlumat və əks-faktual:**", ""]
    o = obs[obs.event_id == eid]
    L += table(["Göstərici", "İl", "Fakt", "Əks-faktual (qayda)", "Müşahidə olunan təsir", "σ əks-faktual (n)", "Mənbə"],
               [[r.label_az, r.year, fmt(r.obs_raw, 2), f"{fmt(r.cf, 2)} ({r.cf_rule})", fmt(r.obs_effect, 2),
                 f"{fmt(r.sigma_cf, 2)} ({int(r.sigma_n)})", _s(r.obs_source) + (f" — {r.obs_note_az}" if isinstance(r.obs_note_az, str) and r.obs_note_az else "")]
                for r in o.itertuples()])
    L += ["**Proqnoz və fakt:**", ""]
    L += table(["Göstərici", "İl", "Metod", "Proqnoz [interval]", "Fakt (təsir)", "Sapma", "% sapma", "İstiqamət",
                "İntervalda", "Sadə etalon (qayda)", "Etalondan yaxşı", "Güc", "Nümunə", "Sinif", "Alt. əks-faktual"],
               [[("**" + r["label_az"] + "**") if r["primary_row"] else r["label_az"], r["year"], r["method_az"],
                 f"{fmt(r['pred'], 2)} {_rng(r)}", fmt(r["obs_effect"], 2), fmt(r["error"], 2, sign=True),
                 fmt(r["pct_error"], 0), r["dir_hit"], r["in_model_band"], f"{fmt(r['naive'], 2)} ({r['naive_rule']})",
                 r["beats_naive"], r["power"],
                 "daxili" if r["in_sample"] == "bəli" else "kənar", _cls(r), r["class_alt_cf"]] for _, r in g.iterrows()])
    L += ["**Sapmalar və izah (əsas göstəricilər):**", ""]
    L += ["- " + _sentence(r) for _, r in g[g.primary_row == 1].iterrows()]
    L += ["", f"**Hökm:** {s['verdict_az']} — əsas göstəricilər üzrə həlledici müqayisələrin orta balı "
          f"{fmt(s['primary_mean_score'], 2)} (2 = uyğun, 1 = qismən, 0 = uyğunsuz); həlledici müqayisələr: "
          f"{int(s['n_decisive'])} / {int(s['n_comparisons'])}; istiqamət uyğunluğu {fmt(100 * s['dir_hit_rate'], 0)} %; "
          f"sadə etalondan yaxşı: {fmt(100 * s['beats_naive_rate'], 0)} %."
          + (" Nümunədaxili müqayisələr struktur uyğunluğu göstərir, proqnoz gücünü yox." if "bəli" in s["in_sample"] else "")
          + (f" Diqqət: hökm cəmi {int(s['n_primary_decisive'])} həlledici əsas müqayisəyə əsaslanır — zəif sübut."
             if s["n_primary_decisive"] < 2 else ""), ""]
    return L


def _sens() -> list[str]:
    t = _read("V_nfr1_tolerance_sensitivity.csv")
    if t.empty:
        return []
    sets = list(dict.fromkeys(t.tol_set))
    rows = [[eid] + [f"{g.set_index('tol_set').loc[k, 'verdict_az']} ({fmt(g.set_index('tol_set').loc[k, 'primary_mean_score'], 2)}; "
                     f"{int(g.set_index('tol_set').loc[k, 'n_ok'])}/{int(g.set_index('tol_set').loc[k, 'n_part'])}/"
                     f"{int(g.set_index('tol_set').loc[k, 'n_fail'])})" for k in sets]
            for eid, g in t.groupby("event_id", sort=False)]
    par = [f"- **{k}**: " + t[t.tol_set == k].params.iloc[0].replace(";", ", ") for k in sets]
    return (table(["Hadisə"] + sets, rows) + ["Xanada: hökm (əsas balı; uyğun/qismən/uyğunsuz sayı). Parametrlər:", ""]
            + par + ["", "«Keçdi» hökmlərinin sayı: " + ", ".join(
                f"{k} — {int((t[t.tol_set == k].verdict_az == 'keçdi').sum())}" for k in sets)
                + f" (cəmi {t.event_id.nunique()} hadisə). Nazirlik qaydanı təsdiqləyənə qədər «təklif» sütunu əsasdır; "
                  "yumşaq qayda bu hesabatın ilk versiyasında istifadə edilmişdi.", ""])


def _findings(cmp) -> list[str]:
    d = cmp[cmp.score >= 0]
    L = []
    for eid, g in d[d.primary_row == 1].groupby("event_id", sort=False):
        b = g.groupby("method")["pct_error"].median().sort_values()
        L.append(f"- {eid}: əsas göstəricilər üzrə ən kiçik median % sapma — {M.METHOD_LABEL_AZ[b.index[0]]} "
                 f"({fmt(b.iloc[0], 0)} %)" + (f"; ən böyük — {M.METHOD_LABEL_AZ[b.index[-1]]} ({fmt(b.iloc[-1], 0)} %)"
                                             if len(b) > 1 else "") + ".")
    bad = d[d.score == 0]
    if len(bad):
        L.append("- Tolerantlıqdan kənar (uyğunsuz) müqayisələr: " + "; ".join(
            f"{r.row_id} {r.method} (proqnoz {fmt(r.pred, 1)}, fakt {fmt(r.obs_effect, 1)})" for r in bad.itertuples()) + ".")
    low = cmp[cmp.score < 0]
    if len(low):
        L.append(f"- Aşağı güclü (hökmə daxil edilməyən) müqayisələr: {len(low)} — " + ", ".join(dict.fromkeys(low.row_id))
                 + "; bu göstəricilərdə illik məlumatla siyasət təsirini əks-faktualın səs-küyündən ayırmaq mümkün deyil.")
    pl = cmp[cmp.label_az.str.contains("plasebo")]
    if len(pl):
        L.append(f"- Plasebo (2024, minimum əmək haqqı dəyişməyib): {len(pl)} müqayisədən "
                 f"{int((pl.score == 2).sum())} «uyğun» — modellər siyasət olmayan ildə saxta təsir yaratmır.")
    return L


def _nfr2(cmp) -> list[str]:
    rows = []
    for rid, g in cmp.groupby("row_id", sort=False):
        if g.method.nunique() < 2:
            continue
        p = g.set_index("method")["pred"]
        rows.append([rid, g.label_az.iloc[0], g.year.iloc[0], fmt(g.obs_effect.iloc[0], 2),
                     "; ".join(f"{m}: {fmt(v, 2)}" for m, v in p.items()), fmt(p.max() - p.min(), 2),
                     g.loc[g.abs_error.idxmin(), "method"]])
    return table(["Sətir", "Göstərici", "İl", "Fakt", "Metodlar üzrə proqnoz", "Metodlararası fərq", "Ən yaxın metod"], rows)


RECOMMEND_AZ = [
    "Tolerantlıq qaydası (bölmə 2.4) Nazirlik tərəfindən təsdiqlənməli və ya dəyişdirilməlidir (Sorğuda NFR1 cavabsızdır); "
    "parametrlər `validate.TOL`-da, nəticə `V_nfr1_tolerance.csv`-də.",
    "Proqnoz vintajlarının arxivi (ex ante ssenari nəticələri vintaj id ilə) yaradılmalıdır ki, növbəti hadisələr "
    "(məs. 2026 gəlir vergisinin bərpası) həqiqi nümunədən kənar qiymətləndirilsin.",
    "DSK-dan aylıq İQİ maddə sıraları və ilkin dərc dəyərləri alınmalıdır (E7 tipli hadisə tədqiqatı və vintaj testi üçün).",
    "Ev təsərrüfatı büdcə sorğusu (HBS) mikroməlumatı ilə sintetik fayl əvəz edildikdə E1 yoxsulluq testi təkrarlanmalıdır.",
    "Yeni hadisə = `config/historical_events.csv`-yə sətirlər (kod dəyişikliyi tələb olunmur; yeni şok növü üçün `nfr1_models.shock`).",
]


def write(log=print) -> str:
    from . import validate as V
    ev, obs, cmp = D.events(), _read("V_nfr1_observed.csv"), _read("V_nfr1_comparisons.csv")
    evs, ms, tol, meta = (_read(n) for n in ("V_nfr1_events.csv", "V_nfr1_methods.csv", "V_nfr1_tolerance.csv",
                                             "V_nfr1_run_meta.csv"))
    mt = dict(zip(meta["key"], meta["value"])) if len(meta) else {}
    n_ev = len(evs)
    L = ["# Sapma hesabatı — təsir analizi modellərinin retrospektiv validasiyası (NFR1, MİİS §15.5.4)", "",
         f"*Avtomatik yaradılıb: `python3 -m policyunit.validate` ({mt.get('run_at', time.strftime('%Y-%m-%d %H:%M'))}). "
         "Bütün rəqəmlər `output/V_nfr1_*.csv` fayllarındandır; bu sənəd əl ilə redaktə edilmir.*", "",
         "## 1. Qəbul meyarı və xülasə", "",
         "TT qəbul meyarı: «Model nəticələri ən azı 2 tarixi siyasət hadisəsi üzərində sınaqdan keçirilir və sapma "
         f"hesabatı sənədləşdirilir». **Status: {n_ev} hadisə, {len(cmp)} proqnoz–fakt müqayisəsi, "
         f"{cmp.method.nunique() if len(cmp) else 0} metod — meyar {'yerinə yetirilib' if n_ev >= 2 else 'YERİNƏ YETİRİLMƏYİB'}.** "
         "Meyar prosedurdur (sınaq + sənəd); hökmlər aşağıdakı təklif olunan tolerantlıq qaydası ilə verilir.", ""]
    L += table(["Hadisə", "Tarix", "Nümunə", "Metodlar", "≥2 metodlu göstərici (NFR2)", "Həlledici / cəmi (əsas)",
                "Uyğun / qismən / uyğunsuz (həlledicilər)", "Hökm"],
               [[f"{r.event_id}. {r.event_name_az}", r.event_date_az, r.in_sample.replace("bəli", "daxili").replace("xeyr", "kənar"),
                 r.n_methods, f"{r.rows_with_2plus_methods} ({r.nfr2_ok})", f"{r.n_decisive} / {r.n_comparisons} ({r.n_primary_decisive})",
                 f"{fmt(100 * r.share_ok, 0)} / {fmt(100 * r.share_part, 0)} / {fmt(100 * r.share_fail, 0)} %",
                 f"**{r.verdict_az}**"] for r in evs.itertuples()])
    L += ["Metodlar üzrə (bütün hadisələr):", ""]
    L += table(["Metod", "Müqayisə (həlledici)", "Hadisələr", "Orta bal", "İstiqamət uyğunluğu", "Median % sapma",
                "Orta sapma (işarəli)", "Sadə etalondan yaxşı"],
               [[r.method_az, f"{r.n} ({r.n_decisive})", r.events, fmt(r.mean_score, 2), f"{fmt(100 * r.dir_hit_rate, 0)} %",
                 fmt(r.median_pct_error, 0), fmt(r.mean_error, 2, sign=True), f"{fmt(100 * r.beats_naive_rate, 0)} %"]
                for r in ms.itertuples()])
    L += ["## 2. Metodologiya", "", "### 2.1 Əks-faktual (baza ilə müqayisə)", ""]
    L += [f"- `{k}` — {v}" for k, v in CF_AZ.items()]
    L += ["", "Hər göstərici üçün əsas və alternativ qayda verilir (sinif hər ikisi ilə hesablanır). σ əks-faktual — eyni "
          "qaydanın hadisədən əvvəlki 10 ildə «psevdo-hadisələr» üzrə xətasının 1,4826 × median |xəta| ölçüsü (sürüşmə daxil); "
          "DiD üçün minimum əmək haqqının dəyişmədiyi illərdə fərqin standart kənarlaşması.", "",
          "### 2.2 Model proqnozları", ""]
    L += [f"- **{v}** (`{k}`)" for k, v in M.METHOD_LABEL_AZ.items()]
    L += ["", "MikroUnit zənciri: hadisənin alət yolu məlumatdan qurulur (illik orta minimum əmək haqqı — DSK 004_1; AMB "
          "rəsmi orta məzənnəsi; IO E7 yanacaq şoku) və cari zəncirə köçürülür; təsir = ssenari − eyni vintajın bazası.", "",
          "### 2.3 Metriklər", "",
          "sapma = proqnoz − fakt (təsir); % sapma = |sapma| / |fakt|; istiqamət (işarə) uyğunluğu; fakt model "
          "intervalındadırmı (ayrıca, tolerantlığa əlavə edilmir); fakt model intervalı ± 1,96·σ əks-faktual daxilindədirmi; "
          "model qeyri-trivial sadə etalondan yaxşıdırmı:", ""] + [f"- `{k}` — {v}" for k, v in D.NAIVE_AZ.items()] + ["",
          "### 2.4 Tolerantlıq qaydası — TƏKLİF (Nazirlik hədd müəyyən etməyib)", ""]
    L += table(["Parametr", "Dəyər", "Qayda", "Status"], [[r.param, fmt(r.value, 2), r.rule_az, r.status_az] for r in tol.itertuples()])
    L += [f"Hadisə hökmü — əsas göstəricilər üzrə həlledici müqayisələrin orta balı: ≥ {fmt(V.VERDICT[0][0], 2)} «keçdi», "
          f"≥ {fmt(V.VERDICT[1][0], 2)} «şərti keçdi», əks halda «keçmədi». Aşağı güclü müqayisələr hökmə daxil edilmir, "
          f"plasebo sətirləri isə |sapma| ≤ σ_əf olduqda «uyğun» sayılır; «keçdi» üçün ən azı {V.TOL['min_decisive']} "
          "həlledici əsas müqayisə tələb olunur.", "", "### 2.5 Hökmlərin tolerantlıq seçiminə həssaslığı", ""] + _sens() + ["## 3. Hadisələr", ""]
    for eid in evs.event_id:
        L += _event_section(eid, ev, obs, cmp, evs)
    L += ["## 4. NFR2 — eyni hadisə üçün metodların müqayisəsi", ""] + _nfr2(cmp)
    L += ["## 5. Ümumi nəticələr", ""] + _findings(cmp) + ["", "Metodlar üzrə sistematik meyl (vahidlər qarışıqdır — yalnız işarə informativdir):", ""]
    for r in ms.itertuples():
        bias = "artıq" if r.mean_error > 0 else "az"
        L.append(f"- {r.method_az}: orta bal {fmt(r.mean_score, 2)}, təsirləri orta hesabla {bias} qiymətləndirir "
                 f"(orta sapma {fmt(r.mean_error, 2, sign=True)}), median % sapma {fmt(r.median_pct_error, 0)}.")
    L += ["", "**Məhdudiyyətlər:**", ""] + [f"- {x}" for x in LIMITS_AZ]
    L += ["", "**Tövsiyələr:**", ""] + [f"- {x}" for x in RECOMMEND_AZ]
    L += ["", "## 6. Fayllar və vintaj", "",
          "`config/historical_events.csv` (hadisə reyestri), `output/V_nfr1_observed.csv`, `V_nfr1_comparisons.csv`, "
          "`V_nfr1_events.csv`, `V_nfr1_methods.csv`, `V_nfr1_tolerance.csv`, `V_nfr1_run_meta.csv`; istifadə olunan "
          "digər agentlərin faylları: `V_io_e7_fuel_2024.csv`, `V_io_e7_sensitivity.csv`, `V_microsim_2019_package.csv`, "
          "`V_microsim_2025_minwage.csv`.", ""]
    L += table(["Açar", "Dəyər"], [[k, f"`{v}`"] for k, v in mt.items() if k not in ("tolerance",)])
    config.DOCS.mkdir(parents=True, exist_ok=True)
    DOC.write_text("\n".join(L), encoding="utf-8")
    log(f"  [nfr1] hesabat: {DOC.name} ({len(L)} sətir)")
    return str(DOC)
