"""FR3 §3.2: which candidates the 2019 break dummy D18 is significant for (HAC-F, <=2020), EN and AZ."""
from .common import az, azm, num
from ._fr3_v236_tables import chosen_rows

LAB = {
    ('E4', 'prod_non + mw'): ('the chosen state wage E4', 'seçilmiş dövlət sektoru E4'),
    ('E4', 'mw'): ('the state wage on the minimum wage alone', 'təkcə minimum əmək haqqı ilə dövlət sektoru əmək haqqı'),
    ('E4', 'exp_pe + mw'): ('the state wage with fiscal capacity', 'fiskal imkanlar daxil olan dövlət sektoru namizədi'),
    ('E1', 'prod_tot'): ('the chosen aggregate E1', 'seçilmiş aqreqat E1'),
    ('E1', 'prod_tot + mw'): ('the aggregate candidate with the minimum wage', 'minimum əmək haqqı daxil olan aqreqat namizədi'),
    ('E2', 'prod_non'): ('the chosen non-oil wage E2', 'seçilmiş qeyri-neft E2'),
    ('E2', 'prod_non + mw'): ('the non-oil candidate with the minimum wage', 'minimum əmək haqqı daxil olan qeyri-neft namizədi'),
    ('E3', 'prod_non'): ('the chosen private wage E3', 'seçilmiş özəl sektor E3'),
    ('E3', 'prod_non + mw'): ('the private candidate with the minimum wage', 'minimum əmək haqqı daxil olan özəl sektor namizədi'),
    ('E3', 'prod_non + w_state'): ('the private candidate with the state wage', 'dövlət sektoru əmək haqqı daxil olan özəl sektor namizədi'),
    ('E3', 'prod_non + w_oil'): ('the private candidate with the oil wage', 'neft sektoru əmək haqqı daxil olan özəl sektor namizədi'),
    ('E3r', 'prod_non + mw'): ('the ratio model', 'nisbət modeli'),
    ('E5', 'w_non'): ('the oil wage E5', 'neft sektoru E5')}


def _join(w, conj):
    return w[0] if len(w) == 1 else ', '.join(w[:-1]) + f' {conj} ' + w[-1]


def blocks(V):
    ch = chosen_rows(V)
    rows = [(r['eq'], r['drivers'], r['break p (<=2020)']) for r in V['hb_rows']]
    sig = sorted([x for x in rows if x[2] < 0.05], key=lambda x: x[2])
    ns = [x for x in rows if x[2] >= 0.05 and ch.get(x[0]) == x[1]]
    en = ('It is significant (p < 0.05) for ' + _join([f"{LAB[(e, d)][0]} ({p:.3f})" for e, d, p in sig], 'and')
          + ('; not for ' + _join([f"{LAB[(e, d)][0]} ({p:.3f})" for e, d, p in ns], 'or') if ns else '') + '.')
    a = ('O, ' + _join([f"{LAB[(e, d)][1]} ({az(p, 3)})" for e, d, p in sig], 'və') + ' üçün əhəmiyyətlidir'
         + ('; ' + _join([f"{LAB[(e, d)][1]} ({az(p, 3)})" for e, d, p in ns], 'və') + ' üçün əhəmiyyətli deyil' if ns else '') + '.')
    c, s = V['mw_dols_d18']['E4'][0], V['d18_e4']
    return (dict(fr3v236_d18=(en, True), fr3v236_d18v=(f"(minimum-wage elasticity {c:.3f}, D18 {num(s, 3)})", True)),
            dict(fr3v236_d18=(a, True), fr3v236_d18v=(f"(minimum əmək haqqı elastikliyi {az(c, 3)}, D18 {azm(s, 3)})", True)))
