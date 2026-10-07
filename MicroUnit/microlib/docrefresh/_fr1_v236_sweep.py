"""FR1 v2.3.6 sweep blocks (AUTO:fr1v236_*): restriction-table rows and the §8.4 accounts sentence."""
import json

from .common import DATA, az, azpm, pm


def _mw():
    d = json.load(open(DATA / 'dsk_minwage' / 'minwage_path.json', encoding='utf-8'))
    return d['legal_level_first_forecast_year_azn'], d['growth_pct_a_year_from_second_forecast_year']


def _vals(F):
    E = F.E
    free = E['FR1.E3_hhdisp.free']
    lev = [c for c in free['coefficients'] if c['name'] != 'const' and not c['name'].startswith('d_')]
    r = [x for x in E['FR1.E3_hhdisp']['restrictions'] if 'Homogen' in x['text_az']][0]
    so = E['FR1.G5_defl_oth']['restrictions']
    joint = [x for x in so if 'Birgə' in x['text_az']][0]
    single = [x for x in so if 'tək' in x['text_az']][0]
    infl = [c for c in E['FR1.G5_defl_oth.free']['coefficients'] if c['name'] == 'infl'][0]['coef']
    tou_el = [c for c in E['FR1.C8_tou']['coefficients'] if c['name'] == 'ln_hhdisp_pc'][0]['coef']
    A = F.ACC
    return dict(s=sum(c['coef'] for c in lev), n=len(lev), p=r['p'], se=r['se_tested_combination'], imp=r['imposed'],
                txt_az=r['text_az'].split(':', 1)[1].strip(), jp=joint['p'], sp=single['p'], infl=infl, tou_el=tou_el,
                tou=A.loc['Tourism & catering', 'real_growth_avg_pct'], soc=A.loc['Social & other services', 'deflator_infl_avg_pct'])


def _p(p):
    return f"{p:.3f}"


def sweep_en(F):
    v = _vals(F)
    rej = v['p'] < 0.05
    verd = ('**Rejected** — imposed on theory grounds (v2.3)' if rej and v['imp'] else '**Rejected**' if rej
            else 'Not rejected (low power) — imposed')
    lab = 'non-oil GDP + pension + wage-bill' if v['n'] == 3 else 'non-oil GDP + pension'
    sv = ('Not rejected — imposed' if v['sp'] >= 0.05 else '**Rejected**') + \
         (f" (no-drift joint test rejected, p = {_p(v['jp'])})" if v['jp'] < 0.05 else f" (no-drift joint test p = {_p(v['jp'])})")
    return dict(
        fr1v236_e3hom=(f"Household income: {lab} elasticities = 1 | {v['s']:.3f} | {_p(v['p'])} | {v['se']:.3f} | {verd}", True),
        fr1v236_socdefl=(f"Social-services deflator: pass-through 1 (drift free) | {v['infl']:.2f} | {_p(v['sp'])} | — | {sv}", True),
        fr1v236_tou=(f"{pm(v['tou'], 1)}% a year comes from its income elasticity ({v['tou_el']:.1f})", True),
        fr1v236_soc=(f"{v['soc']:.1f}% a year", True),
        fr1v236_mw=(_mw_en(), True))


def _mw_en():
    lv, g = _mw()
    return (f"minimum wage at the legal {lv:.0f} AZN in {F_Y1} and then {pm(g['Baseline'], 0)}% a year (Adverse {pm(g['Adverse'], 0)}%, "
            f"Reform {pm(g['Reform'], 0)}%; `data/dsk_minwage/minwage_path.json`, the same path as FR3)")


def _mw_az():
    lv, g = _mw()
    return (f"minimum əmək haqqı {F_Y1}-cı ildə qanuni {lv:.0f} manat, sonra ildə {pm(g['Baseline'], 0)}% (Mənfi ssenaridə "
            f"{pm(g['Adverse'], 0)}%, İslahatda {pm(g['Reform'], 0)}%; `data/dsk_minwage/minwage_path.json`, FR3 ilə eyni yol)")


F_Y1 = 2026


def sweep_az(F):
    v = _vals(F)
    rej = v['p'] < 0.05
    verd = ('**Rədd edilib** — nəzəri əsaslarla qoyulub (v2.3)' if rej and v['imp'] else '**Rədd edilib**' if rej
            else 'Rədd edilməyib (aşağı güc) — qoyulub')
    sv = ('Rədd edilməyib — qoyulub' if v['sp'] >= 0.05 else '**Rədd edilib**') + \
         (f" (dreyfsiz birgə test rədd edilib, p = {_p(v['jp'])})" if v['jp'] < 0.05 else f" (dreyfsiz birgə test p = {_p(v['jp'])})")
    return dict(
        fr1v236_e3hom=(f"Ev təsərrüfatlarının gəliri: {v['txt_az']} | {v['s']:.3f} | {_p(v['p'])} | {v['se']:.3f} | {verd}", True),
        fr1v236_socdefl=(f"Sosial xidmətlərin deflyatoru: ötürülmə əmsalı 1 (dreyf sərbəst) | {v['infl']:.2f} | {_p(v['sp'])} | — | {sv}", True),
        fr1v236_tou=(f"Turizmin ildə {azpm(v['tou'], 1)}% artımı daha sürətlə artan adambaşına gəlirə görə onun gəlir "
                     f"elastikliyindən ({az(v['tou_el'], 1)})", True),
        fr1v236_soc=(f"ildə {az(v['soc'], 1)}% artır", True),
        fr1v236_mw=(_mw_az(), True))
