"""p_hub.py — MicroUnit/index.html: the hub page (macro hub style) linking Klassik görünüş and İş paneli."""
from . import pcore as C


def _n(x):
    return f"{x:,}".replace(",", " ")


def build(S, meta):
    nser = len(S)
    npath = sum(len(r["s"]) for r in S)
    nband = sum("q" in r for r in S)
    st = meta["stamp"]
    html = f"""<!doctype html>
<html lang="az">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Mikroiqtisadi modul — MİİS §15.5.2</title>
<link rel="stylesheet" href="panel/assets/hub.css">
</head>
<body>
<header class="top">
  <div class="wrap">
    <div class="eyebrow">Azərbaycan Respublikası İqtisadiyyat Nazirliyi</div>
    <h1>Mikroiqtisadi təhlil və proqnoz modulu — MİİS §15.5.2</h1>
    <p class="lead">Altı funksional tələb (FR1, FR3, FR4, FR5, FR10, FR12) üzrə struktur ekonometrik modellər və onların 2026–2030 proqnozları,
    üç ssenari ilə. Hər iki görünüş eyni çıxış fayllarından yığılır və brauzerdə birbaşa açılır — server və internet lazım deyil.</p>
    <div class="facts">
      <span class="fact"><b>6</b> funksional tələb</span>
      <span class="fact"><b>{_n(nser)}</b> proqnoz göstəricisi</span>
      <span class="fact"><b>{_n(npath)}</b> ssenari üzrə sıra, hər biri 2026–2030</span>
      <span class="fact"><b>{_n(nband)}</b> göstəricidə 5–95 % zolağı</span>
    </div>
  </div>
</header>
<div class="wrap">
  <section>
    <h2><span class="dot" style="background:var(--moe)"></span>Mikroiqtisadi modul (§15.5.2)</h2>
    <p class="sec-note">Sektorlar və bazarlar, orta əmək haqqı, məşğulluq, pullu xidmətlər, müəssisələrin maliyyə vəziyyəti və bazar payı,
    rəqabət mühiti. Bütün modellər strukturdur (AR/ARIMA/ARCH/GARCH yoxdur) və sadə etalonlara qarşı nümunədən kənar yoxlanılıb.</p>
    <div class="pair">
      <a class="card" style="--k: var(--moe)" href="site/index.html">
        <span class="kind">Klassik görünüş</span>
        <h3>Metodologiya və sənədlər</h3>
        <p>Hər tələb öz səhifəsində: tələb mətni, model, məlumat, nəticə, yoxlama və məhdudiyyətlər.</p>
        <ul>
          <li>Ortaq metod standartları və hold-out xülasəsi</li>
          <li>Məlumat mənbələri, FR10/FR12 mənbə matrisləri, məlumat boşluqları</li>
          <li>Sintetik məlumat və onun əvəz edilməsi</li>
          <li>Bütün çıxış faylları, dəftərlər və icra ardıcıllığı</li>
        </ul>
        <span class="go">Klassik görünüşü aç →</span>
        <span class="file">site/index.html</span>
      </a>
      <a class="card" style="--k: var(--moe)" href="panel/index.html">
        <span class="kind">İş paneli</span>
        <h3>Proqnozlar — açıq və interaktiv</h3>
        <p>Bütün proqnozlar illər üzrə, üç ssenaridə: kartlar, qrafiklər, cədvəllər.</p>
        <ul>
          <li>Hər tələb üçün bütün göstəricilər, qruplar üzrə «Hamısı» cədvəli</li>
          <li>Əsas / Mənfi / İslahat ssenariləri və onların müqayisəsi</li>
          <li>Bir böyük proqnoz cədvəli: süzgəc, axtarış, CSV və Excel ixracı</li>
          <li>Sürətli axtarış (Ctrl K), qısa tur və bələdçi</li>
        </ul>
        <span class="go">İş panelini aç →</span>
        <span class="file">panel/index.html</span>
      </a>
    </div>
  </section>
  <div class="note">
    <h3>Yeniləmə</h3>
    <p>Dəftərlər bu ardıcıllıqla icra olunur: FR1 → FR3 → FR4 → FR5 → FR10 → FR12. Sonra:</p>
    <ul><li><code>python3 site/build_site.py</code> — klassik görünüş</li><li><code>python3 panel/build_panel.py</code> — iş paneli və bu səhifə</li></ul>
    <p>FR10 və FR12-nin müəssisə səviyyəsi (B qatı) Nazirlik öz məlumatını yükləyənə qədər <b>sintetik</b> fayllarla işləyir; onların nəticələri tapıntı kimi göstərilmir.</p>
  </div>
  <footer>Yığılıb {st['date']} · {st['files']} çıxış faylı · möhür {st['md5']}</footer>
</div>
</body>
</html>
"""
    (C.UNIT / "index.html").write_text(html, encoding="utf-8")
