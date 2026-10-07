"""FR1 v2.3.5 note paragraph (EN + AZ): pension policy cost, employment elasticity (FR1 vs FR4), minimum-wage series.
Figures: FR1_doc_figures.json (engine responses), FR1_equations.json, FR4_equations.json; pre-v2.3.5: v22_reference.json."""
import json

from .common import OUT, az, azpm, pm


def _fr4():
    try:
        with open(OUT / "FR4_equations.json", encoding="utf-8") as f:
            E = {e["id"]: e for e in json.load(f)["equations"]}
    except FileNotFoundError:
        return None
    c = lambda i, n: next((x["coef"] for x in E[i]["coefficients"] if x["name"] == n), float("nan")) if i in E else float("nan")
    return dict(emp=c("FR4.E4_pooled_emp", "d_lo_sq"), hired=c("FR4.E4_pooled_hired", "d_lo_sq"),
                mkt_emp=c("FR4.E6_emp", "ln_rva_oth"), mkt_hired=c("FR4.E6_hired", "ln_rva_oth"))


def _v(F):
    d = F.docfig["v23"]["v235"]; old = F.ref["v23"]["pre_v235"]; e2 = F.E["FR1.E2_wage"]["holdout"]
    global v5
    v5 = F.ref["v23"]["v235"]
    return d, old, e2, _fr4()


def v235_en(F):
    d, old, e2, f4 = _v(F); p10 = d["pension10"]; m10 = d["minwage10"]; st = d["istate1bn"]; mw = d["minwage"]
    yr = [2026, 2027, 2028, 2029, 2030]
    L = lambda dd, k: ", ".join(pm(dd[k][str(y)] if str(y) in dd[k] else dd[k][y], 0) for y in yr)
    fr4 = (f" FR4's sector equations give a higher elasticity for hired (formal) employees than for total employment: sector share "
           f"{f4['hired']:.3f} vs {f4['emp']:.3f}, market services {f4['mkt_hired']:.2f} vs {f4['mkt_emp']:.2f}; a policy unit should read FR1's "
           "employment as total (LFS) employment, dominated by self-employment and agriculture, and take formal-job effects from FR4.") if f4 else ""
    return f"""**v2.3.5 (2026-10-06): pension cost, employment, minimum wage.** (1) A real pension increase improved the budget balance: pensions
are paid by DSMF, outside the state budget, and FR1 had no financing identity, so only the revenue gain (consumption → VAT) showed.
A real increase above CPI indexation (policy input `pension_real_g`) is now financed by a state-budget transfer to DSMF (current
spending) = DSMF pension spending ({f"{d['pens_exp_base']:,.0f}".replace(',', ' ')} mln AZN in 2025, bridged from 2024) × (1 − 1/cumulative real increase); actual pension
rises in history and the hold-out are inside the observed spending (off there). +10% real pensions from 2026: balance
{L(p10, 'balance_n')} mln AZN in 2026–30 (before: {", ".join(pm(v, 0) for v in old['pension10_dbal'])}); spending {L(p10, 'exp_tot_n')}, revenue {L(p10, 'rev_tot_n')}. (2) Employment:
FR1's E1 relates the employment RATE to per-capita non-oil GDP with an elasticity of {d['e1_cf']['ln_gdpnon_pc']:.3f} (p = {d['e1_p']['ln_gdpnon_pc']:.3f}; measured
unemployment is very stable), so +1 bn AZN of state investment raises non-oil GDP {pm(st['rgdpnon']['2030'] if '2030' in st['rgdpnon'] else st['rgdpnon'][2030])}% but employment only
{pm(st['emp']['2030'] if '2030' in st['emp'] else st['emp'][2030], 3)}% by 2030 — the estimated elasticity, not re-specified.{fr4} (3) The workbook's minimum wage (`Sosial sektor` row 51)
shows in year t the level in force from 1 January t+1 (2024: 400, effective 01.01.2025). FR1 now uses the annual average of the level in force
(`data/dsk_minwage/`, DSK 004_1): 2019 {v5['minwage_2019']:.1f} (v2.3.5; 195.0 in v2.3.6), 2024 {mw['used'].get('2024', mw['used'].get(2024)):.0f}, 2025 {mw['used'].get('2025', mw['used'].get(2025)):.0f}. E2
re-estimated: minimum-wage elasticity {old['e2_cf']['ln_minwage']:.3f} (p = {old['e2_p_minwage']:.2f}) → **{v5['e2_cf']['ln_minwage']:.3f}** (p = {v5['e2_p_minwage']:.3f}), productivity {old['e2_cf']['ln_prod_non']:.2f} → {v5['e2_cf']['ln_prod_non']:.2f},
CPI {old['e2_cf']['ln_cpi']:.2f} → {v5['e2_cf']['ln_cpi']:.2f}; wage hold-out U {old['e2_holdout_u']:.2f} → {v5['e2_holdout_u']:.2f} (a data correction, not a specification choice). Minimum wage +10%
(2030): wage {pm(old['minwage10_2030']['wage'])} → {pm(v5['minwage10_2030']['wage'])}%, real disposable income {pm(old['minwage10_2030']['rhhdisp'])} → {pm(v5['minwage10_2030']['rhhdisp'])}%, CPI
{pm(old['minwage10_2030']['cpi'])} → {pm(v5['minwage10_2030']['cpi'])}%. Baseline CPI inflation 2026–30: {", ".join(f"{v:.1f}" for v in v5['infl_baseline'])}% (before: {", ".join(f"{v:.1f}" for v in old['infl_baseline'])}). (v2.3.5 run; corrected in v2.3.6 below.)"""


def v235_az(F):
    d, old, e2, f4 = _v(F); p10 = d["pension10"]; m10 = d["minwage10"]; st = d["istate1bn"]; mw = d["minwage"]
    yr = [2026, 2027, 2028, 2029, 2030]
    G = lambda dd, k, y=2030: dd[k][str(y)] if str(y) in dd[k] else dd[k][y]
    L = lambda dd, k: ", ".join(azpm(G(dd, k, y), 0) for y in yr)
    U = lambda k: mw["used"].get(str(k), mw["used"].get(k))
    fr4 = (f" FR4-ün sektor tənlikləri muzdlu (formal) işçilər üçün ümumi məşğulluqdan daha yüksək elastiklik verir: sektor payı {az(f4['hired'], 3)} — "
           f"{az(f4['emp'], 3)}-ə qarşı, bazar xidmətləri {az(f4['mkt_hired'])} — {az(f4['mkt_emp'])}-ə qarşı; siyasət bölməsi FR1-in məşğulluğunu özünüməşğulluq və kənd "
           "təsərrüfatının üstünlük təşkil etdiyi ümumi (İQM) məşğulluq kimi oxumalı, formal iş yerlərinə təsiri isə FR4-dən götürməlidir.") if f4 else ""
    return f"""**v2.3.5 (2026-10-06): pensiya xərci, məşğulluq, minimum əmək haqqı.** (1) Pensiyanın real artımı büdcə balansını yaxşılaşdırırdı: pensiyaları
dövlət büdcəsindən kənar DSMF ödəyir, FR1-də isə maliyyələşdirmə eyniliyi yox idi, buna görə yalnız gəlir qazancı (istehlak → ƏDV) görünürdü. İQİ
indeksasiyasından yuxarı real artım (siyasət girişi `pension_real_g`) indi dövlət büdcəsindən DSMF-ə transfertlə (cari xərclər) maliyyələşdirilir =
DSMF pensiya xərcləri (2025-də {az(d['pens_exp_base'], 0)} mln AZN, 2024-dən körpü ilə) × (1 − 1/məcmu real artım); tarixdə və nümunədən kənar yoxlamada faktiki
artımlar müşahidə olunan xərclərin içindədir (orada söndürülüb). 2026-dan +10% real pensiya: balans 2026–30-da {L(p10, 'balance_n')} mln AZN (əvvəl:
{", ".join(azpm(v, 0) for v in old['pension10_dbal'])}); xərclər {L(p10, 'exp_tot_n')}, gəlirlər {L(p10, 'rev_tot_n')}. (2) Məşğulluq: FR1-in E1 tənliyi məşğulluq SƏVİYYƏSİNİ adambaşına qeyri-neft
ÜDM ilə {az(d['e1_cf']['ln_gdpnon_pc'], 3)} elastikliklə əlaqələndirir (p = {az(d['e1_p']['ln_gdpnon_pc'], 3)}; ölçülən işsizlik çox sabitdir), buna görə +1 mlrd AZN dövlət investisiyası
2030-a qədər qeyri-neft ÜDM-i {azpm(G(st, 'rgdpnon'))}%, məşğulluğu isə cəmi {azpm(G(st, 'emp'), 3)}% artırır — bu qiymətləndirilmiş elastiklikdir, yenidən spesifikasiya
edilməyib.{fr4} (3) İş kitabındakı minimum əmək haqqı (`Sosial sektor`, 51-ci sətir) t ilində t+1 ilin 1 yanvarından qüvvədə olan səviyyəni göstərir (2024: 400,
01.01.2025-dən). FR1 indi qüvvədə olan səviyyənin illik ortasından istifadə edir (`data/dsk_minwage/`, DSK 004_1): 2019 {az(v5['minwage_2019'], 1)} (v2.3.5; v2.3.6-da 195,0),
2024 {az(U(2024), 0)}, 2025 {az(U(2025), 0)}. E2 yenidən qiymətləndirilib: minimum əmək haqqı elastikliyi {az(old['e2_cf']['ln_minwage'], 3)} (p = {az(old['e2_p_minwage'])}) → **{az(v5['e2_cf']['ln_minwage'], 3)}**
(p = {az(v5['e2_p_minwage'], 3)}), məhsuldarlıq {az(old['e2_cf']['ln_prod_non'])} → {az(v5['e2_cf']['ln_prod_non'])}, İQİ {az(old['e2_cf']['ln_cpi'])} → {az(v5['e2_cf']['ln_cpi'])}; əmək haqqının nümunədən kənar U-su
{az(old['e2_holdout_u'])} → {az(v5['e2_holdout_u'])} (məlumat düzəlişidir, spesifikasiya seçimi deyil). Minimum əmək haqqı +10% (2030): əmək haqqı {azpm(old['minwage10_2030']['wage'])} →
{azpm(v5['minwage10_2030']['wage'])}%, real sərəncamda qalan gəlir {azpm(old['minwage10_2030']['rhhdisp'])} → {azpm(v5['minwage10_2030']['rhhdisp'])}%, İQİ {azpm(old['minwage10_2030']['cpi'])} → {azpm(v5['minwage10_2030']['cpi'])}%. Əsas ssenaridə 2026–30
İQİ inflyasiyası: {", ".join(az(v, 1) for v in v5['infl_baseline'])}% (əvvəl: {", ".join(az(v, 1) for v in old['infl_baseline'])}). (v2.3.5 icrası; v2.3.6-da düzəldilib.)"""
