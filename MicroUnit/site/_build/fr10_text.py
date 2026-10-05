"""fr10_text.py — FR10 prose blocks (numbers injected from the outputs)."""
from . import html
from .core import v, esc, esc_az
from .labels import status

MEAS_AZ = {"nominal": "nominal", "real": "real", "shares_pp": "paylar, f.b."}
W_AZ = {"unweighted": "çəkisiz", "share-weighted": "paya görə çəkili"}


def sys_az(s):
    import re
    n = re.search(r"\d+", s)
    n = n.group(0) if n else ""
    if s.startswith("manufacturing"):
        return f"Emal sənayesi, {n} sahə — proqnoz modeli"
    if "regions" in s:
        return f"{n} iqtisadi region"
    return s


def model(d):
    p = d["pool"]
    return ("<p>FR10 iki qatlıdır. <strong>A qatı</strong> (işlək) — 30 sənaye sahəsi (NACE 06–36), 4 bölmə, ölçü "
            "qrupları, dövlət / qeyri-dövlət, 14 iqtisadi region və təxminən 140 məhsul üzrə DSK və iş kitabı "
            "məlumatı; bütün nəticələr buradan gəlir. <strong>B qatı</strong> — müəssisə səviyyəsində mühərrik "
            "(sxem, validator, maliyyə əmsalları, Altman Z''-EM, TFP indeksi, NACE × region üzrə bazar payları, "
            "HHI/CR4, giriş/çıxış/sağ qalma, həmyaşıd müqayisəsi, müəssisə proqnozları); o, Nazirlik real müəssisə "
            "panelini öz sistemində yükləyənə qədər <strong>sintetik</strong> fayl üzərində yalnız sınaqdan keçirilir.</p>"
            "<p><strong>Sahə modeli.</strong> Neft emalı istehsal gücü ilə məhdudlaşan, neftin qiyməti ilə idarə olunan "
            "emalçı kimi modelləşdirilir; qalan emal sahələri birləşdirilmiş «əlaqəli sektor» tələb modeli ilə "
            f"(β = {v(p.beta, 3)}, s.x. {v(p.se, 3)}; vəhşi bootstrap p = {v(p.p_wild, 3)}) və sabit payların bərabər çəkili "
            "kombinasiyası ilə bölüşdürülür — qayda əvvəlcədən sabitlənib, çünki modelin sabit paylar üzərində nümunədən "
            "kənar üstünlüyü təsdiqlənməyib. Mədənçıxarma sahələri birbaşa, regionlar isə multinomial-logit pay sistemi "
            "ilə modelləşdirilir. Asılı dəyişənin gecikməsi və öz tarixindən proqnoz yoxdur; səviyyə əlaqələri DOLS, "
            "panellər iki tərəfli sabit effektlər, Driscoll–Kraay xətaları və vəhşi klaster bootstrap ilə.</p>")


def data(d, pre):
    m = d["mat"]
    sg = m.status_group.value_counts()
    man = d["man"]
    present = int((man.status == "present").sum())
    gone = int(len(man) - present)
    chips = " ".join(f'{html.pill(status(k)[0], status(k)[1])} {v(sg.get(k, 0), 0)}'
                     for k in ("available now", "requested", "not available"))
    return (f"<p>{v(present, 0)} DSK cədvəli yığılıb və manifestdə qeyd olunub (<code>FR10_dsk_manifest.csv</code>); "
            f"daha {v(gone, 0)} cədvəl DSK saytında artıq nəşr olunmur. Göstəricilər sistemi — hansı məlumat, hansı "
            f"mənbədən, hansı göstərici üçün, hansı formada — {v(len(m), 0)} göstəricilik mənbə matrisindədir: {chips}. "
            f"Tam matris, {v(len(d['gaps']), 0)} məlumat boşluğu və alternativləri, {v(len(d['find']), 0)} məlumat "
            f"bütövlüyü tapıntısı: <a href=\"{pre}data.html#fr10-matrix\">Məlumat mənbələri → FR10</a>.</p>")


def check_intro():
    return ("<p>Faktiki işlədilən proqnoz modeli 2019-a qədərki məlumatla yenidən qiymətləndirilib və 2020–2025 üçün "
            "FR1-in faktiki sektor əlavə dəyəri, deflyatorları və neftin qiyməti ilə simulyasiya olunub; heç bir FR10 "
            "nəticəsi modelə verilmir. Etalonlar: təsadüfi gəzişmə və sahənin öz 2014–2019 orta artımı.</p>")


def check_outro(h):
    r = h[(h.measure == "real") & (h.weighting == "share-weighted")]
    u = r.U_vs_constant_growth.iloc[0] if len(r) else float("nan")
    p = r.DM_p_vs_cg.iloc[0] if len(r) else float("nan")
    ru = h[(h.measure == "real") & (h.weighting == "unweighted")]
    return (f"<p><strong>Açıq nəticə.</strong> Nominal sahə məhsulu hər iki etalonu üstələyir. Real sahə məhsulu isə "
            f"sabit artımı <em>üstələmir</em>: çəkisiz U {v(ru.U_vs_constant_growth.iloc[0], 3)} (fərq əhəmiyyətsizdir), "
            f"paya görə çəkili U {v(u, 3)} — əhəmiyyətli dərəcədə pis (DM p {v(p, 3)}). Real sahə yolları zolaqları ilə "
            "birlikdə oxunmalıdır; nominal məhsul daha etibarlı nəticədir. Regional paylar hər iki etalonu üstələyir.</p>")


def layerb_text(d, s, pre):
    pipe = d["pipe"]
    swap = d["swap"]
    rows = [[esc_az(r.test), esc_az(str(r.value)), html.pill("done", "keçdi") if r.passed else html.pill("gap", "keçmədi")]
            for r in pipe.itertuples()]
    return ("<p>B qatı müəssisə panelini <code>data/firm_panel/</code> qovluğundan oxuyur. Təhvil verilən fayl "
            "sintetikdir: təsadüfi yaradılıb, lakin DSK sahə aqreqatları (müəssisə sayı, buraxılış, işçi sayı və əmək "
            "haqqı) ilə uzlaşdırılıb. Onun nəticələri (<code>FR10_SYNTHETIC_*.csv</code>, su nişanlı) heç bir tapıntıda "
            "işlədilmir və bu saytda qrafik kimi göstərilmir. Aşağıdakı cədvəl yalnız mühərrikin düzgün işlədiyini "
            "yoxlayır:</p>"
            + html.table(["Boru xətti testi", "Dəyər", "Nəticə"], rows, cols=["c-wide", "c-text", "c-tight"])
            + f"<p>Əvəzetmə testləri: {v(int(swap.passed.sum()), 0)}/{v(len(swap), 0)} keçir; real fayl üzrə validator "
            f"hesabatı hazırda {v(len(d['val']), 0)} sətir ehtiva edir (sintetik rejimdə boşdur). Faylın necə əvəz "
            f"olunduğu addım-addım: <a href=\"{pre}synthetic.html#replace\">Sintetik məlumat və onun əvəz edilməsi</a>.</p>")


LIMITS = ["Əlaqəli sektor elastikliyi nümunə daxilində əhəmiyyətlidir, lakin onun sabit paylar üzərində nümunədən kənar "
          "üstünlüyü təsdiqlənməyib; baza kombinasiyası əvvəlcədən sabitlənmiş qaydaya əsaslanır.",
          "Real sahə məhsulu nümunədən kənar yoxlamada sabit artımdan əhəmiyyətli dərəcədə pisdir.",
          "Neft emalı qaydası yeni güc olmadığını fərz edir; rıçaq 2015–25 maksimumunu göstərir.",
          "B qatının məlumatı gələnə qədər maliyyə vəziyyəti aqreqat səviyyədədir; sahə üzrə ümumi mənfəət göstəricisi "
          "yuxarı həddir (qeyri-formal buraxılış, nəzərə alınmayan vergilər).",
          "Effektivlik ölçüləri implisit deflyatorlara və daimi inventar üsulu ilə kapitala əsaslanır; kiçik sahələrdə TFP səs-küylüdür.",
          "Determinantlar panelinin gücü onun qısa illik nümunəsi ilə məhduddur.",
          "İxrac, sahə üzrə istehsalçı qiymətləri, enerji xərcləri, sahə krediti və yenilənmə əmsalları mövcud deyil.",
          "Sintetik rejimdə B qatı analiz deyil, sınaqdan keçmiş boru xəttidir; Nazirlik öz məlumatını yüklədikdə analizə çevrilir."]
