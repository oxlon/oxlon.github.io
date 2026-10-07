"""FR1 v2.3.6 note paragraph (EN + AZ): minimum-wage month weighting, public-pay control in E2, G4 wage pass-through.
Figures: FR1_doc_figures.json, FR1_v23_decisions.csv; v2.3.5 values: v22_reference.json."""
from .common import az, azpm, pm


def _v(F):
    d = F.docfig["v23"]["v235"]; v5 = F.ref["v23"]["v235"]
    dec = F.dec23[F.dec23.group == "E2"].set_index("spec")
    G = lambda dd, k, y=2030: dd[k][str(y)] if str(y) in dd[k] else dd[k][y]
    return d, v5, dec, G


def v236_en(F):
    d, v5, dec, G = _v(F); m20 = d["minwage20"]; o20 = v5["minwage20_2030"]; sec = d["e2_sector"]; g4 = d["g4_wage"]
    ad = dec[dec.adopted.astype(str) == "True"]
    th = d["e2_cf"]["ln_minwage"]
    rows = "; ".join(f"{r.variant.split(': ', 1)[1]}: U {r.U_rw:.2f}{'' if r.signs_ok else ' (wrong sign — rejected)'}" for _, r in dec.iterrows())
    return f"""**v2.3.6 (2026-10-06): minimum wage — month weighting and the public-pay channel.** (1) The annual minimum wage is the
month-weighted level in force from the DSK 004_1 schedule: 2019 = (2×130 + 6×180 + 4×250)/12 = 195.0 (v2.3.5: {v5['minwage_2019']:.1f}); FR3 uses the
same series and the legal 2026 level (400 AZN, in force since 01.01.2025), its growth lever applying from 2027. (2) Every
minimum-wage increase (2019, 2022, 2023) coincided with a public-pay reform. The minimum-wage elasticity is {sec['state']['coef']:+.3f} for STATE wages
(p = {sec['state']['p']:.3f}) and {sec['nonstate']['coef']:+.3f} for NON-STATE wages (p = {sec['nonstate']['p']:.2f}), so a single average-wage elasticity attributes public pay to
every employee. Candidates (Part 11.7, wage hold-out U vs RW, v2.3.5 form {dec.U_rw_v22.iloc[0]:.2f}): {rows}. **Adopted: the minimum-wage elasticity
restricted to the state / non-state channels** ({d['e2_restriction'].split(' -> ')[0]}): **{v5['e2_cf']['ln_minwage']:.3f} → {th:.3f}**; productivity and CPI are
re-estimated ({d['e2_cf']['ln_prod_non']:.2f}, {d['e2_cf']['ln_cpi']:.2f}). Minimum wage +20% (Baseline 2030): average wage {pm(o20['wage'])} → **{pm(G(m20, 'wage'))}%**, real GDP {pm(o20['rgdp'])} →
{pm(G(m20, 'rgdp'))}%, real disposable income {pm(o20['rhhdisp'])} → {pm(G(m20, 'rhhdisp'))}%, CPI {pm(o20['cpi'])} → {pm(G(m20, 'cpi'))}% (inflation {pm(o20['infl_2026'])} → {pm(G(m20, 'infl', 2026))} pp in 2026).
(3) G4's wage pass-through is {g4['coef']:.3f} (s.e. {g4['se']:.3f}, p = {g4['p']:.2f}; 95% interval about {g4['coef'] - 2.1 * g4['se']:+.2f} to {g4['coef'] + 2.1 * g4['se']:+.2f}): it treats public-pay
rises like private unit labour costs, so the minimum wage → wage → CPI response remains on the strong side (the PolicyUnit 2019
validation: observed CPI response far smaller); a non-state-wage cost term needs a non-state wage block and is not adopted here.
Baseline CPI inflation 2026–30: {", ".join(f"{v:.1f}" for v in F.base.loc[[2026, 2027, 2028, 2029, 2030], 'infl'])}% (v2.3.5: {", ".join(f"{v:.1f}" for v in v5['infl_baseline'])})."""


def v236_az(F):
    d, v5, dec, G = _v(F); m20 = d["minwage20"]; o20 = v5["minwage20_2030"]; sec = d["e2_sector"]; g4 = d["g4_wage"]
    th = d["e2_cf"]["ln_minwage"]
    NM = {"pubref_steps": "dövlət sektoru islahatı addımları", "pubref_index": "islahatların məcmu indeksi",
          "mw_sector": "dövlət / qeyri-dövlət kanalları ilə məhdudlaşdırılmış elastiklik"}
    rows = "; ".join(f"{NM.get(k, k)}: U {az(r.U_rw)}{'' if r.signs_ok else ' (yanlış işarə — rədd edilib)'}" for k, r in dec.iterrows())
    return f"""**v2.3.6 (2026-10-06): minimum əmək haqqı — ayların çəkisi və dövlət sektoru kanalı.** (1) İllik minimum əmək haqqı DSK 004_1 cədvəli üzrə
qüvvədə olan səviyyənin ay çəkili ortasıdır: 2019 = (2×130 + 6×180 + 4×250)/12 = 195,0 (v2.3.5: {az(v5['minwage_2019'], 1)}); FR3 eyni sırayı və 2026-nın qanuni səviyyəsini
(400 AZN, 01.01.2025-dən) istifadə edir, artım rıçağı 2027-dən tətbiq olunur. (2) Minimum əmək haqqının hər artımı (2019, 2022, 2023) dövlət sektorunda
əmək haqqı islahatı ilə üst-üstə düşüb. Minimum əmək haqqı elastikliyi DÖVLƏT əmək haqları üçün {azpm(sec['state']['coef'], 3)} (p = {az(sec['state']['p'], 3)}), QEYRİ-DÖVLƏT
əmək haqları üçün {azpm(sec['nonstate']['coef'], 3)}-dir (p = {az(sec['nonstate']['p'])}), yəni vahid orta əmək haqqı elastikliyi dövlət sektorunun artımını bütün işçilərə aid edir.
Namizədlər (Hissə 11.7; əmək haqqının U-su, v2.3.5 forması {az(dec.U_rw_v22.iloc[0])}): {rows}. **Qəbul edilib: dövlət / qeyri-dövlət kanalları ilə
məhdudlaşdırılmış minimum əmək haqqı elastikliyi**: **{az(v5['e2_cf']['ln_minwage'], 3)} → {az(th, 3)}**; məhsuldarlıq və İQİ yenidən qiymətləndirilib ({az(d['e2_cf']['ln_prod_non'])}, {az(d['e2_cf']['ln_cpi'])}).
Minimum əmək haqqı +20% (Əsas ssenari, 2030): orta əmək haqqı {azpm(o20['wage'])} → **{azpm(G(m20, 'wage'))}%**, real ÜDM {azpm(o20['rgdp'])} → {azpm(G(m20, 'rgdp'))}%, real sərəncamda qalan
gəlir {azpm(o20['rhhdisp'])} → {azpm(G(m20, 'rhhdisp'))}%, İQİ {azpm(o20['cpi'])} → {azpm(G(m20, 'cpi'))}% (inflyasiya 2026-da {azpm(o20['infl_2026'])} → {azpm(G(m20, 'infl', 2026))} f.b.). (3) G4-də əmək haqqının
ötürülməsi {az(g4['coef'], 3)}-dir (s.x. {az(g4['se'], 3)}, p = {az(g4['p'])}): dövlət sektorunun əmək haqqı artımlarını özəl sektorun vahid əmək xərcləri kimi qəbul
edir, buna görə minimum əmək haqqı → əmək haqqı → İQİ reaksiyası güclü tərəfdə qalır (PolicyUnit-in 2019 yoxlaması: faktiki İQİ reaksiyası xeyli kiçik);
qeyri-dövlət əmək haqqı xərci həddi ayrıca qeyri-dövlət əmək haqqı bloku tələb edir və burada qəbul edilməyib. Əsas ssenaridə 2026–30 İQİ
inflyasiyası: {", ".join(az(v, 1) for v in F.base.loc[[2026, 2027, 2028, 2029, 2030], 'infl'])}% (v2.3.5: {", ".join(az(v, 1) for v in v5['infl_baseline'])})."""
