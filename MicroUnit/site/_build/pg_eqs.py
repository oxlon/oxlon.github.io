"""pg_eqs.py — fr/frX-tenlikler.html: every equation of the module's registry, grouped by sub-task,
filterable, each expandable to the full regression output."""
from collections import Counter

from . import core, html, v2data as V, v2nav, v2eq
from .core import esc

READ = ("<div class=\"box read-guide\"><p><strong>Necə oxumalı.</strong> Hər sətir bir tənlikdir. Başlığın altındakı "
        "zolaq tənliyin keyfiyyətini bir baxışda göstərir:</p><ul>"
        "<li><strong>R²</strong> — determinasiya əmsalı: asılı dəyişənin dəyişkənliyinin nə qədərini tənlik izah edir "
        "(1-ə yaxın — çox; səviyyə tənliklərində yüksək R² adi haldır, tək başına keyfiyyət sübutu deyil).</li>"
        "<li><strong>n</strong> — müşahidələrin sayı (illik məlumatda adətən 15–30).</li>"
        "<li><strong>DW</strong> — Durbin–Watson: 2-yə yaxın olduqda qalıqlarda avtokorrelyasiya yoxdur.</li>"
        "<li><strong>kointeqrasiya p</strong> — səviyyə əlaqəsinin uzunmüddətli olub-olmadığı (p ≤ 0,10 — "
        "kointeqrasiya müəyyən edilib; əks halda t-statistikaları təsviridir).</li>"
        "<li><strong>U</strong> — nümunədən kənar yoxlamada Theil U: 1-dən kiçik (yaşıl) — tənlik təsadüfi gəzişmə və ya "
        "sabit artım etalonundan daha dəqiqdir.</li>"
        "<li><strong>Hökm nişanı</strong> — dayanıqlıq: yaşıl «stabil», sarı «qismən stabil», qırmızı «qeyri-stabil» "
        "(qayda aşağıda).</li></ul><p>Sətirə klikləyin — tam reqressiya nəticəsi açılır: əmsallar cədvəli, uyğunluq, "
        "diaqnostika, məhdudiyyətlər, rekursiv əmsallar və faktiki/qiymətləndirilmiş qrafiki, mətn şəklində xülasə "
        "(«Kopyala» düyməsi ilə).</p></div>")


def counts(eqs):
    vc = Counter(V.verdict_of(e) for e in eqs)
    used = sum(1 for e in eqs if e.get("used_in_forecast"))
    items = [(len(eqs), "tənlik cəmi"), (used, "proqnozda istifadə olunur")] + [(vc.get(k, 0), k) for k in V.VERDICTS]
    return '<ul class="count-strip cs-many">' + "".join(
        f'<li><span class="cs-n">{core.num(n, 0)}</span><span class="cs-l">{esc(lab)}</span></li>' for n, lab in items) + "</ul>"


def filters(subs):
    opt = "".join(f'<option value="{esc(s)}">{esc(s)}</option>' for s in subs)
    return ('<div class="filter-bar eq-filter" hidden><label for="f-sub">Alt-tapşırıq</label>'
            f'<select id="f-sub" data-attr="sub"><option value="">hamısı</option>{opt}</select>'
            '<label for="f-used">İstifadə</label><select id="f-used" data-attr="used"><option value="">hamısı</option>'
            '<option value="1">proqnozda istifadə olunur</option><option value="0">alternativ / yoxlama</option></select>'
            '<label for="f-ver">Hökm</label><select id="f-ver" data-attr="verdict"><option value="">hamısı</option>'
            + "".join(f'<option value="{v}">{v}</option>' for v in V.VERDICTS)
            + '</select><button type="button" class="eq-expand" data-open="1">Hamısını aç</button>'
            '<button type="button" class="eq-expand" data-open="0">Hamısını bağla</button>'
            '<span class="count" aria-live="polite"></span></div>')


def build(m, title, pre="../"):
    reg = V.registry(m)
    eqs = V.equations(m)
    path = f"fr/{m.lower()}-tenlikler.html"
    groups = {}
    for e in eqs:
        groups.setdefault(V.az(e.get("subtask") or "Digər"), []).append(e)
    subs = sorted(groups)
    secs = [("oxu", "Necə oxumalı"), ("qayda", "Dayanıqlıq hökmünün qaydası")]
    o = [f"<h1>{esc(m)} — Tənliklər və tam reqressiya nəticələri</h1>", v2nav.strip(m, path),
         f'<p class="lead-in">{esc(title)} modulunun qiymətləndirdiyi bütün {core.num(len(eqs), 0)} tənlik — proqnozda '
         "istifadə olunanlar, alternativ spesifikasiyalar və rədd edilmiş variantlar. Rəqəmlər dəftərin öz "
         f"qiymətləndirmələridir; tənlik reyestri {html.flink('output/' + m + '_equations.json', pre)} faylındadır.</p>",
         html.h2("oxu", 1, "Necə oxumalı"), READ, counts(eqs),
         html.h2("qayda", 2, "Dayanıqlıq hökmünün qaydası"),
         f"<p>{esc(V.az_numbers(reg.get('verdict_rule_az') or ''))}</p>",
         (f'<p class="eq-na">{esc(V.az(reg.get("conventions_az") or ""))}</p>' if reg.get("conventions_az") else ""),
         html.h2("siyahi", 3, "Tənliklər siyahısı"), filters(subs)]
    secs.append(("siyahi", "Tənliklər siyahısı"))
    for i, s in enumerate(subs, 1):
        gid = f"alt-{i}"
        g = groups[s]
        used = sum(1 for e in g if e.get("used_in_forecast"))
        o.append(f'<section class="eq-group" data-sub="{esc(s)}"><h3 id="{gid}">{esc(s)} '
                 f'<span class="grp-n">{core.num(len(g), 0)} tənlik · {core.num(used, 0)} proqnozda</span></h3>')
        o += [v2eq.card(e, pre) for e in g]
        o.append("</section>")
    return "\n".join(o), secs
