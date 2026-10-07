"""FR3 v2.3.6 blocks (AUTO:fr3v236_*): every run-dependent number of the FR3 text after the minimum-wage / D18 corrections."""
from ._fr3_v236_vals import vals
from ._fr3_v236_ctx import ctx
from ._fr3_v236_d18 import blocks as d18_blocks
from . import _fr3_v236_tables as T1, _fr3_v236_tables2 as T2, _fr3_v236_en as EN, _fr3_v236_az as AZ

TABLES = dict(homog=T1.homog, mwrange=T2.mw_ranges, select=T1.select, eqs=T2.equations, hold=T1.holdout,
              now=T1.nowcast, res=T1.results, sens=T2.sensitivity, fan=T1.fan)
BLOCK = set(TABLES) | {'spill', 'holdtxt'}


def blocks():
    V = vals()
    C = ctx(V)
    out = {}
    for lang, mod in (('en', EN), ('az', AZ)):
        d = {k: f(V, lang) for k, f in TABLES.items()}
        d.update(mod.blocks(V, C))
        out[lang] = {f'fr3v236_{k}': (v, k not in BLOCK) for k, v in d.items()}
    e, a = d18_blocks(V)
    out['en'].update(e)
    out['az'].update(a)
    return out['en'], out['az']
