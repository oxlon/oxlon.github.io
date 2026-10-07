"""b_hub.py — PolicyUnit/index.html: the hub page (style copied from RiskUnit/panel/_build/b_hub.py) linking the
Siyasət paneli, the sibling units' panels (MicroUnit §15.5.2, RiskUnit §15.5.3, §15.5.1 site), docs and the API."""
from . import bcore as C


def _n(x):
    return f"{x:,}".replace(",", " ")


def build(stats, stamp):
    U = C.UNIT
    from .b_docs import TITLES
    docs = "".join(f'<li><a href="docs/{p.name}">{TITLES.get(p.name, p.stem.replace("_", " "))}</a> · '
                   f'<a href="panel/index.html#/metod/{p.stem}">paneldə oxu</a></li>' for p in sorted(C.DOCS.glob("*.md")))
    docs += '<li><a href="config/README_az.md">Konfiqurasiya: yeni ssenari və alət (NFR4)</a></li>'
    api = '<li><a href="api/openapi.yaml">API təsviri (OpenAPI)</a> <code>api/openapi.yaml</code></li>' if (U / "api" / "openapi.yaml").exists() else ""
    sib = [("../MicroUnit/panel/index.html", "MikroUnit İş paneli (§15.5.2)", "Sektor, bazar müvazinəti, rəqabət, məşğulluq — siyasət təsirlərinin əsas mühərriki"),
           ("../RiskUnit/panel/index.html", "Risk paneli (§15.5.3)", "Risk reyestri, paylanmalar, stress testləri — siyasətin risk profili buradan gəlir"),
           ("../1551_v3/index.html", "Makro proqnozlar (§15.5.1)", "OxLon və Nazirlik makro modelləri — baza proqnozu")]
    sibs = "".join(f'<li><a href="{h}">{t}</a> — {d}</li>' for h, t, d in sib if (U / h).resolve().exists())
    launch = "SiyasetModel_Baslat.command" if (U / "SiyasetModel_Baslat.command").exists() else None
    v = stamp.get("vintage") or {}
    html = f"""<!doctype html>
<html lang="az">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Siyasət təsiri bölməsi — MİİS §15.5.4</title>
<link rel="icon" href="data:,">
<link rel="stylesheet" href="panel/assets/hub.css">
</head>
<body>
<header class="top">
  <div class="wrap">
    <div class="eyebrow">Azərbaycan Respublikası İqtisadiyyat Nazirliyi</div>
    <h1>İqtisadi siyasətlərin təsir analizi — MİİS §15.5.4</h1>
    <p class="lead">Siyasət alətinin (vergi, xərc, sosial ödəniş, minimum əmək haqqı, uçot dərəcəsi, tarif və s.) iqtisadiyyata
    təsiri baza proqnozu ilə müqayisədə: makro (ÜDM, inflyasiya, işsizlik) və mikro (sektorlar, bazar müvazinəti) təsirlər
    qısa, orta və uzun müddətdə; girdi-çıxdı (IO) modeli ilə sektor təsirləri; mikrosimulyasiya ilə məşğulluq, gəlir
    bölgüsü və yoxsulluq; yan təsirlər və risklər; seçilmiş əsas göstəricilər (KPI) üzrə ssenarilərin müqayisəsi.</p>
    <div class="facts">
      <span class="fact"><b>{stats['scenarios']}</b> rəsmi ssenari</span>
      <span class="fact"><b>{stats['instruments']}</b> siyasət aləti</span>
      <span class="fact"><b>{stats['kpi']}</b> KPI kataloqda</span>
      <span class="fact"><b>{stats['indicators']}</b> əsas göstərici</span>
      <span class="fact"><b>{stats['outputs']}</b> çıxış faylı</span>
      <span class="fact">son hesablama <b>{stamp['date']}</b></span>
    </div>
  </div>
</header>
<div class="wrap">
  <section>
    <h2><span class="dot" style="background:var(--moe)"></span>Haradan başlamalı</h2>
    <p class="sec-note">Qərar və təhlil üçün <b>Siyasət paneli</b>. Panel çıxış fayllarından yığılır və brauzerdə birbaşa açılır;
    yeni ssenarinin hesablanması üçün yerli server lazımdır.</p>
    <div class="pair">
      <a class="card" style="--k: var(--moe)" href="panel/index.html">
        <span class="kind">Siyasət paneli</span>
        <h3>Ssenarilər, təsirlər, KPI, hesabat</h3>
        <p>Hər ssenarinin əsas nəticələri bir baxışda, sonra ətraflı təhlil — bir neçə kliklə.</p>
        <ul>
          <li>Ssenari qurucusu: alətlər kataloqundan seçin, ölçü, illər, hədəf sektor, maliyyələşmə</li>
          <li>Makro və mikro təsirlər (qısa / orta / uzun), IO sektor təsirləri, sosial təsirlər</li>
          <li>Yan təsirlər və risk profili, KPI ilə çoxkriteriyalı reytinq, metodların müqayisəsi</li>
          <li>Tarixi validasiya (sapma hesabatı); hesabat qurucusu (PDF, Excel, Word, CSV)</li>
        </ul>
        <span class="go">Siyasət panelini aç →</span>
        <span class="file">panel/index.html</span>
      </a>
      <div class="card" style="--k: var(--caem)">
        <span class="kind">Əlaqəli bölmələr</span>
        <h3>MİİS-in digər modulları</h3>
        <p>Siyasət təsiri bu modulların baza proqnozları və risk paylanmaları üzərində qurulur.</p>
        <ul>{sibs}</ul>
        <span class="file">../MicroUnit · ../RiskUnit · ../1551_v3</span>
      </div>
    </div>
  </section>
  <section>
    <h2><span class="dot" style="background:var(--caem)"></span>Sənədlər və API</h2>
    <div class="note"><h3>Metodologiya</h3><ul>{docs}</ul>
    <h3 style="margin-top:12px">API</h3><ul>{api or '<li>API hazırlanır</li>'}</ul></div>
  </section>
  <div class="note">
    <h3>Yeni ssenarinin hesablanması üçün</h3>
    <p>{('<b>' + launch + '</b> (macOS) və ya <b>SiyasetModel_Baslat.bat</b> (Windows) faylını iki dəfə klikləyin — yerli server başlayır və panel brauzerdə açılır.') if launch else 'Yerli serveri başladın (<code>SiyasetModel_Baslat.command</code> / <code>.bat</code>) və paneli <code>http://127.0.0.1:8792/panel/</code> ünvanında açın.'}
    Server olmadan panel tam işləyir (bütün nəticələr paketdədir); yalnız yeni hesablama aparıla bilmir.</p>
    <h3 style="margin-top:12px">Yeniləmə</h3>
    <p><code>python3 run_all.py</code>, sonra <code>python3 panel/build_panel.py</code> — panel və bu səhifə yenidən yığılır.</p>
  </div>
  <footer>Yığılıb {stamp['date']} · {stats['outputs']} çıxış faylı · möhür {stamp['md5']} · MikroUnit vintajı {v.get('micro_vintage', '—')}</footer>
</div>
</body>
</html>
"""
    p = U / "index.html"
    p.write_text(html, encoding="utf-8")
    return p
