"""b_hub.py — RiskUnit/index.html: the hub page (macro hub style) linking the Risk paneli, the classic report pages,
the methodology documents, the reports and the API."""
from . import bcore as C


def _n(x):
    return f"{x:,}".replace(",", " ")


def build(stats, stamp):
    U = C.UNIT
    api = [("api/openapi.yaml", "API təsviri (OpenAPI)")] if (U / "api" / "openapi.yaml").exists() else []
    api.append(("output/risk_api.json", "Maşın üçün JSON (FR4)"))
    from .b_docs import TITLES
    docs = "".join(f'<li><a href="docs/{p.name}">{TITLES.get(p.name, p.stem.replace("_", " "))}</a> · <a href="panel/index.html#/metod/{p.stem}">paneldə oxu</a></li>'
                   for p in sorted(C.DOCS.glob("*.md")))
    reps = "".join(f'<li><a href="reports/{p.name}">{p.name}</a></li>' for p in sorted((U / "reports").glob("*.*")))
    apis = "".join(f'<li><a href="{h}">{t}</a> <code>{h}</code></li>' for h, t in api)
    launch = ("RiskModel_Baslat.command" if (U / "RiskModel_Baslat.command").exists() else None)
    html = f"""<!doctype html>
<html lang="az">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Risk bölməsi — MİİS §15.5.3</title>
<link rel="icon" href="data:,">
<link rel="stylesheet" href="panel/assets/hub.css">
</head>
<body>
<header class="top">
  <div class="wrap">
    <div class="eyebrow">Azərbaycan Respublikası İqtisadiyyat Nazirliyi</div>
    <h1>İqtisadi risklərin idarəedilməsi və qərar dəstək sistemi — MİİS §15.5.3</h1>
    <p class="lead">Makro (OxLon və Nazirlik) və mikro (FR1–FR12) proqnozların ətrafında risk paylanması: hər gün yenilənən
    məlumat və onun rəsmi proqnozlara təsiri, risk reyestri (ehtimal × təsir), riskə məruz dəyər (VaR) və kapital (CaR),
    miqyaslanma, stress testləri, risk azaldıcı tədbirlər və onların optimal portfeli, CAEM risk vərəqləri və geriyə doğru sınaqlar.</p>
    <div class="facts">
      <span class="fact"><b>{stats['risks']}</b> risk reyestrdə</span>
      <span class="fact"><b>{stats['feeds']}</b> avtomatik məlumat axını</span>
      <span class="fact"><b>{_n(stats['impact'])}</b> proqnoz təsiri sətri (D6)</span>
      <span class="fact"><b>{stats['measures']}</b> risk azaldıcı tədbir</span>
      <span class="fact"><b>{stats['outputs']}</b> çıxış faylı</span>
      <span class="fact">vəziyyət tarixi <b>{stamp['as_of']}</b></span>
    </div>
  </div>
</header>
<div class="wrap">
  <section>
    <h2><span class="dot" style="background:var(--moe)"></span>Haradan başlamalı</h2>
    <p class="sec-note">Gündəlik iş və qərar üçün <b>Risk paneli</b>. Əvvəlki (v1) rəhbərlik və analitik hesabat səhifələri
    <b>Klassik hesabat</b> kimi saxlanılır. Hər iki görünüş eyni çıxış fayllarından yığılır və brauzerdə birbaşa açılır;
    canlı hesablamalar (stress, miqyaslanma, optimallaşdırma, məlumatın yenilənməsi) üçün yerli server lazımdır.</p>
    <div class="pair">
      <a class="card" style="--k: var(--moe)" href="panel/index.html">
        <span class="kind">Risk paneli</span>
        <h3>Bu gün, reyestr, paylanmalar, tədbirlər</h3>
        <p>Rəhbərlik üçün «Bu gün» xülasəsi və hər riskin tam təhlili — bir neçə kliklə.</p>
        <ul>
          <li>Bu günün məlumatı rəsmi proqnozları necə dəyişir (D6, D7)</li>
          <li>R01–R19: ehtimal, təsir, trend, istilik xəritəsi, ötürmə və təsirlənən dəyişənlər</li>
          <li>VaR / ES / CaR, borc davamlılığı, ARDNF adekvatlığı; miqyaslanma və stress testləri</li>
          <li>Tədbirlər portfeli (büdcə üzrə səmərəli sərhəd), icra planı; hesabat qurucusu (PDF, Excel, Word, CSV)</li>
        </ul>
        <span class="go">Risk panelini aç →</span>
        <span class="file">panel/index.html</span>
      </a>
      <div class="card" style="--k: var(--caem)">
        <span class="kind">Klassik hesabat</span>
        <h3>Rəhbərlik və analitik səhifələri (v1)</h3>
        <p>Əvvəlki statik hesabat: rəhbərlik paneli və analitik paneli, PDF və Excel hesabatları.</p>
        <ul>
          <li><a href="site/index.html">Rəhbərlik səhifəsi</a> · <a href="site/analitik.html">Analitik səhifəsi</a></li>
          <li>Hesabat faylları: <code>reports/</code></li>
        </ul>
        <a class="go" href="site/index.html">Klassik hesabatı aç →</a>
        <span class="file">site/index.html · site/analitik.html</span>
      </div>
    </div>
  </section>
  <section>
    <h2><span class="dot" style="background:var(--caem)"></span>Sənədlər, hesabatlar, API</h2>
    <div class="note"><h3>Metodologiya</h3><ul>{docs}</ul>
    <h3 style="margin-top:12px">Hesabat faylları</h3><ul>{reps}</ul>
    <h3 style="margin-top:12px">API</h3><ul>{apis}</ul></div>
  </section>
  <div class="note">
    <h3>Canlı hesablamalar üçün</h3>
    <p>{('<b>' + launch + '</b> (macOS) və ya <b>RiskModel_Baslat.bat</b> (Windows) faylını iki dəfə klikləyin — yerli server başlayır və panel brauzerdə açılır.') if launch else 'Yerli serveri başladın (<code>RiskModel_Baslat.command</code> / <code>.bat</code> və ya <code>python3 api/server.py</code>) və paneli serverin ünvanında açın.'}
    Server olmadan panel tam işləyir (bütün nəticələr paketdədir); yalnız yeni hesablama aparıla bilməz.</p>
    <h3 style="margin-top:12px">Yeniləmə</h3>
    <p><code>python3 run_all.py --daily</code> (gündəlik dövr) və ya <code>python3 run_all.py --fetch</code> (tam dövr), sonra
    <code>python3 panel/build_panel.py</code> — panel və bu səhifə yenidən yığılır.</p>
  </div>
  <footer>Yığılıb {stamp['date']} · {stats['outputs']} çıxış faylı · möhür {stamp['md5']}</footer>
</div>
</body>
</html>
"""
    p = U / "index.html"
    p.write_text(html, encoding="utf-8")
    return p
