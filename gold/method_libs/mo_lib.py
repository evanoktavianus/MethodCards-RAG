# monetary_other cluster: shared loader and gold formulas. Run with python3 -I from the gold/ directory.
import os
HERE = os.path.dirname(os.path.abspath(__file__))
PSV = os.path.join(HERE, '..', 'frozen_extra', 'wdi_20261008_monetary_other.psv')
def load():
    d = {}
    for l in open(PSV):
        c, i, p, v = l.rstrip('\n').split('|')
        p = [int(x) for x in p.strip('{}').split(',')]
        v = [None if x == 'NULL' else float(x) for x in v.strip('{}').split(',')]
        d.setdefault(c, {}).setdefault(i, {}).update({y: x for y, x in zip(p, v) if x is not None})
    return d
D = load()
def g(code, iso, y):
    return D.get(code, {}).get(iso, {}).get(y)
# 1. income velocity of broad money V = GDP / M2 (both LCU)  [WEO Apr 1985, p130: "GNP at annual rates / average stock of money"]
def velocity(iso, y):
    gd, m = g('NY.GDP.MKTP.CN', iso, y), g('FM.LBL.BMNY.CN', iso, y)
    return gd / m if gd and m else None
def velocity_change(iso, y0, y1):
    a, b = velocity(iso, y0), velocity(iso, y1)
    return 100 * (b / a - 1) if a and b else None
# 2. real lending rate = (i - pi)/(1+pi), pi = GDP deflator inflation  [doc 0343a0da p65: nominal rate minus inflation]
def real_rate(iso, y):
    i, p = g('FR.INR.LEND', iso, y), g('NY.GDP.DEFL.KD.ZG', iso, y)
    return (i - p) / (1 + p / 100) if i is not None and p is not None else None
def real_rate_simple(iso, y):
    i, p = g('FR.INR.LEND', iso, y), g('NY.GDP.DEFL.KD.ZG', iso, y)
    return i - p if i is not None and p is not None else None
# 3. real depreciation vs US$ = nominal depreciation (% fall in dollar value of local currency) - GDP-deflator inflation [docs 9879c7bb p33, e946326c p34]
def nominal_dep(iso, y):
    e1, e0 = g('PA.NUS.FCRF', iso, y), g('PA.NUS.FCRF', iso, y - 1)
    return 100 * (1 - e0 / e1) if e1 and e0 else None
def real_dep(iso, y):
    n, p = nominal_dep(iso, y), g('NY.GDP.DEFL.KD.ZG', iso, y)
    return n - p if n is not None and p is not None else None
