"""Greedy hidden-subject predicate builder: conjunction of one-sided cuts on frozen 2023 WEO indicators with set size exactly 1."""
import math, csv, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from ci_lib import *
from ci_lib import _load
def wload(code):
    return _load(FE + '/weo_oct2025_%s.csv' % code)
FEATS = {
 'population (millions)': ('lp', 2023, 'lp'), 'GDP per capita (current US$)': ('ngdpdpc', 2023, ''),
 'real GDP growth (%)': ('ngdp_rpch', 2023, ''), 'CPI inflation (%)': ('pcpipch', 2023, ''),
 'general government gross debt (% of GDP)': ('ggxwdg_ngdp', 2023, ''), 'current account balance (% of GDP)': ('bca_ngdpd', 2023, ''),
 'government revenue (% of GDP)': ('ggr_ngdp', 2023, '')}
DATA = {k: wload(v[0]) for k, v in FEATS.items()}
def val(k, i): return DATA[k].get(i, {}).get(FEATS[k][1])
def rnd(x, d):
    if x == 0: return 0.0
    s = 10 ** (math.floor(math.log10(abs(x))) - 1)
    return (math.ceil(x / s) * s) if d == '<' else (math.floor(x / s) * s)
def build(t, max_conds=3):
    univ = [i for i in GDPPC if i in DATA['population (millions)']]
    cur = [i for i in univ if all(val(k, i) is not None for k in FEATS)]
    if t not in cur: return None
    conds = []
    while len(cur) > 1 and len(conds) < max_conds:
        best = None
        for k in FEATS:
            for d in ('<', '>'):
                x = rnd(val(k, t), d)
                m = [i for i in cur if (val(k, i) < x if d == '<' else val(k, i) > x)]
                if t in m and (best is None or len(m) < len(best[0])) and k not in [c[0] for c in conds]: best = (m, (k, d, x))
        if not best: return None
        cur = best[0]; conds.append(best[1])
    return (conds, cur) if cur == [t] else None
if __name__ == '__main__':
    from select_items import elig
    for t in sorted({e['iso3'] for e in elig}): print(t, build(t))
