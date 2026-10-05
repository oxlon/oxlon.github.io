"""pg_nb.py — the six notebooks: what each does, inputs, run order, recorded runtime."""
from . import core, html, nbinfo
from .core import v


def auto_blocks():
    """Number of generated (AUTO) blocks in each methodology document."""
    out = {}
    for c in nbinfo.ORDER:
        t = core.raw(core.DOCS / f"{c}_Methodology.md")
        out[c] = t.count("<!-- AUTO:")
    return out

SECS = [("list", "Altı dəftər"), ("order", "İcra ardıcıllığı"), ("rules", "Dəftərlərin ortaq qaydaları")]


def build(texts):
    o = ["<h1>Jupyter dəftərləri</h1>",
         '<p class="lead-in">Hər tələb bir dəftərdir. Bu səhifə hər dəftərin nə etdiyini, hansı modulların çıxışlarını '
         "oxuduğunu, son qeydə alınmış icranın vaxtını və yazdığı çıxış fayllarının sayını göstərir — hamısı .ipynb "
         "fayllarının özündən oxunur.</p>",
         html.h2("list", 1, "Altı dəftər"), nbinfo.table(""),
         "<p>«Girişləri» sütunu dəftərin kodunda oxunan digər modul çıxışlarından avtomatik müəyyən edilir. «İcra» — son "
         "icrada birinci kod xanasının başlanğıcından sonuncunun bitməsinə qədər qeydə alınmış vaxtdır; «Xəta» — saxlanılmış "
         "xəta çıxışlarının sayı.</p>",
         html.h2("order", 2, "İcra ardıcıllığı"), nbinfo.run_block(""),
         html.h2("rules", 3, "Dəftərlərin ortaq qaydaları"),
         "<ul><li>Metodologiya sənədlərinin rəqəm blokları <code>AUTO</code> işarələri arasında dəftərin son xanası "
         "tərəfindən çıxış fayllarından yenidən yazılır: "
         + ", ".join(f"{c} — {v(n, 0)} blok" for c, n in auto_blocks().items())
         + ". Blok sayı sıfır olan sənədlərdə rəqəmlər yenidən icra olunmuş çıxışlardan köçürülüb (sənədin revizya "
         "qeydinə bax); bu sayt isə hər rəqəmi birbaşa çıxış fayllarından oxuyur.</li>"
         "<li>FR10 və FR12 əvvəlcə <code>DATA_MODE</code> bannerini çap edir: <code>SYNTHETIC</code> və ya "
         "<code>REAL</code>; sintetik rejimdə B qatının bütün çıxışları <code>*_SYNTHETIC_*</code> adlanır və su "
         'nişanı daşıyır (<a href="synthetic.html">ətraflı</a>).</li>'
         "<li>Toxum (seed) sabitdir, ona görə simulyasiyalar və zolaqlar təkrar icrada eynidir.</li></ul>"]
    return "\n".join(o), SECS
