"""FR1 blocks of 2026-10-07 (AUTO:fr1v236_coefsens / _brent / _pens): coefficient sensitivity, the Brent chain-linking
note under the multiplier table, and the pension assumption."""
import pandas as pd

from .common import DATA, RefreshError, az, azpm, csv, pm


def _cs():
    d = csv('FR1_coef_sensitivity.csv')
    d['sw'] = d.swing_pct.abs()
    g = lambda eq, co, comp: d[(d.eq_id == eq) & (d.coefficient == co) & (d.component_id == f'fr1:{comp}')].iloc[0]  # noqa: E731
    top = d.sort_values('sw', ascending=False).iloc[0]
    if (top.eq_id, top.coefficient) != ('FR1.E3_hhdisp', 'ln_gdpnon'):
        raise RefreshError('FR1 coefficient sensitivity: the largest effect is no longer E3 ln_gdpnon - rewrite the text')
    return dict(e3h=g('FR1.E3_hhdisp', 'ln_gdpnon', 'rhhdisp'), e3n=g('FR1.E3_hhdisp', 'ln_gdpnon', 'rgdpnon'),
                e3c=g('FR1.E3_hhdisp', 'ln_gdpnon', 'cpi'), wbh=g('FR1.E3_hhdisp', 'ln_wagebill_r', 'rhhdisp'),
                d1=g('FR1.D1_cons', 'ln_hhdisp_pc', 'rgdpnon'), g4=g('FR1.G4_infl', 'dln_wage', 'cpi'),
                e4=g('FR1.E4_lf', 'trend', 'emp'))


def _r(r, f):
    return f"{f(r.effect_minus_se_pct)}/{f(r.effect_plus_se_pct)}%"


def _brent():
    m = csv('FR1_multipliers.csv')
    m.columns = ['exp', 'year'] + list(m.columns[2:])
    b = m[m.exp == 'Brent +10 USD/bbl'].set_index('year')
    va = b[[c for c in b.columns if c.startswith('rva_')]]
    if (b.rgdpnon <= 0).any():
        raise RefreshError('FR1 Brent note: non-oil GDP no longer rises in every year - rewrite the explanation')
    return b.rgdp.tolist(), float(va.min().min()), list(b.index)


def _pens():
    p = pd.read_csv(DATA / 'dsmf_pension' / 'pension_indexation.csv')
    r = p[p.year == p.year.max()].iloc[0]
    return int(r.year), float(r.index_pct)


def blocks(F, lang):
    c = _cs()
    g, vmin, yrs = _brent()
    mining = F.ACC.loc['Mining & quarrying', 'real_growth_avg_pct']
    if vmin < -1e-9 or mining >= 0:
        raise RefreshError('FR1 Brent note: a sector falls or mining no longer declines - rewrite the explanation')
    py, pi = _pens()
    if lang == 'en':
        f = lambda v: pm(v, 2)  # noqa: E731
        cs = (f"**Coefficient sensitivity** (`FR1_coef_sensitivity.csv`, ±1 SE, 2030, baseline; current run): the largest effects "
              f"come from the E3 household-income coefficients — non-oil GDP (household income {_r(c['e3h'], f)}, non-oil GDP "
              f"{_r(c['e3n'], f)}, CPI {_r(c['e3c'], f)}) and the real wage bill (household income {_r(c['wbh'], f)}); then the D1 "
              f"income elasticity (non-oil GDP {_r(c['d1'], f)}); for CPI the G4 wage pass-through ({_r(c['g4'], f)}); for "
              f"employment the E4 participation trend ({_r(c['e4'], f)}). The E3 effects are asymmetric: a ±1 SE change multiplies "
              f"a log level inside an exponential and is amplified by the income–consumption loop.")
        br = (f"**Brent +10 and chain-linked real GDP.** Real GDP deviates by {', '.join(pm(x, 2) for x in g)}% in "
              f"{yrs[0]}–{yrs[-1]} although no sector's value added falls (smallest sector deviation {pm(vmin, 2)}%). Chain-linked "
              f"GDP weights each sector's growth by its previous-year nominal share; the higher oil price raises the share of mining, "
              f"whose real output follows the declining oil and gas path ({pm(mining, 1)}% a year), so the same sector volumes add up "
              f"to slightly lower aggregate growth. It is a weighting effect of the index, not a contraction; non-oil GDP rises.")
        pe = (f"pensions at the decided {py} indexation ({pm(pi, 1)}%, Presidential Order; `data/dsmf_pension/pension_indexation.csv`) "
              f"and indexed to CPI from {py + 1}")
    else:
        f = lambda v: azpm(v, 2)  # noqa: E731
        cs = (f"**Əmsal həssaslığı** (`FR1_coef_sensitivity.csv`, ±1 s.x., 2030, Əsas ssenari; cari icra): ən güclü təsirlər E3 "
              f"ev təsərrüfatlarının gəliri tənliyinin əmsallarındandır — qeyri-neft ÜDM (ev təsərrüfatlarının gəliri {_r(c['e3h'], f)}, "
              f"qeyri-neft ÜDM {_r(c['e3n'], f)}, İQİ {_r(c['e3c'], f)}) və real əmək haqqı fondu (ev təsərrüfatlarının gəliri "
              f"{_r(c['wbh'], f)}); sonra D1 gəlir elastikliyi (qeyri-neft ÜDM {_r(c['d1'], f)}); İQİ üçün G4 əmək haqqı ötürülməsi "
              f"({_r(c['g4'], f)}); məşğulluq üçün E4 iştirak trendi ({_r(c['e4'], f)}). E3 təsirləri asimmetrikdir: ±1 s.x. dəyişikliyi "
              f"eksponent daxilindəki loqarifmik səviyyəyə vurulur və gəlir–istehlak dövrəsi ilə güclənir.")
        br = (f"**Brent +10 və zəncirvari real ÜDM.** Heç bir sektorun əlavə dəyəri azalmasa da (ən kiçik sektor kənarlaşması "
              f"{azpm(vmin, 2)}%), real ÜDM {yrs[0]}–{yrs[-1]}-cu illərdə {', '.join(azpm(x, 2) for x in g)}% kənarlaşır. Zəncirvari "
              f"ÜDM hər sektorun artımını onun əvvəlki ilin nominal payı ilə çəkiləndirir; yüksək neft qiyməti real hasilatı azalan "
              f"neft-qaz trayektoriyasını izləyən (ildə {azpm(mining, 1)}%) mədənçıxarmanın payını artırır, ona görə də eyni sektor "
              f"həcmləri bir qədər aşağı aqreqat artım verir. Bu, indeksin çəki effektidir, azalma deyil; qeyri-neft ÜDM artır.")
        pe = (f"pensiyalar {py}-cı ildə qərar verilmiş indeksasiya ilə ({azpm(pi, 1)}%, Prezidentin Sərəncamı; "
              f"`data/dsmf_pension/pension_indexation.csv`), {py + 1}-ci ildən İQİ-yə indeksləşdirilir")
    return dict(fr1v236_coefsens=(cs, False), fr1v236_brent=(br, False), fr1v236_pens=(pe, True))
