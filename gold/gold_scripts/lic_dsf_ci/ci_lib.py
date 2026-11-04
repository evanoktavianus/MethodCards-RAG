"""Composite Indicator (CI) of the Joint Bank-Fund Debt Sustainability Framework for low-income countries.
CI = 0.385*CPIA + 2.719*g + 4.052*IC - 3.990*IC^2 + 2.022*REM + 13.520*WG   (g, IC, REM, WG as fractions)
 CPIA: 10-year average IRAI; g: 10-year average real GDP growth (5 past + 5 projected, centred on report year Y);
 IC: import coverage of reserves, 10-yr avg of reserves/imports, capped at 57.963 percent; REM: remittances % GDP, capped 15.494;
 WG: world real growth, 10-yr avg. Cutoffs: Weak < 2.69, Strong > 3.05, Medium between.
Reads ONLY release/official_benchmark/reference_data and frozen_extra (python3 -I)."""
import csv, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FE = os.path.join(ROOT, 'frozen_extra')
def _load(path):
    d = {}
    for r in csv.DictReader(open(path)):
        d[r['iso3']] = {int(k): float(v) for k, v in r.items() if k.isdigit() and v not in ('', 'NaN')}
    return d
G = _load(FE + '/weo_oct2025_ngdp_rpch.csv')
RP = _load(FE + '/weo_oct2025_ngdprppppc.csv'); LP = _load(FE + '/weo_oct2025_lp.csv')
CPIA = _load(FE + '/wdi_20261008_cpia_irai.csv'); RES = _load(FE + '/wdi_20261008_fires_totl_cd.csv')
IMP = _load(FE + '/wdi_20261008_ne_imp_gnfs_cd.csv'); REM = _load(FE + '/wdi_20261008_remit_gdp.csv')
GDPPC = _load(FE + '/weo_oct2025_ngdpdpc.csv')
_W = {}
for _i in RP:
    if _i in LP:
        for _y, _v in RP[_i].items():
            if _y in LP[_i]: _W[_y] = _W.get(_y, 0) + _v * LP[_i][_y]
WG = {y: 100 * (_W[y] / _W[y - 1] - 1) for y in _W if y - 1 in _W}
CAP_IC, CAP_REM = 57.963, 15.494
def avg(s, a, b, need=None):
    v = [s[y] for y in range(a, b + 1) if y in s]
    need = need or (b - a + 1) // 2 + 1
    return sum(v) / len(v) if len(v) >= need else None
def components(iso, Y):
    cp = avg(CPIA.get(iso, {}), Y - 10, Y - 1)
    ic_s = {y: 100 * RES[iso][y] / IMP[iso][y] for y in RES.get(iso, {}) if y in IMP.get(iso, {})}
    ic = avg(ic_s, Y - 10, Y - 1)
    rem = avg(REM.get(iso, {}), Y - 10, Y - 1)
    g = avg(G.get(iso, {}), Y - 5, Y + 4, 10)
    wg = sum(WG[y] for y in range(Y - 5, Y + 5)) / 10
    if None in (cp, ic, rem, g): return None
    return dict(cpia=cp, g=g, ic=min(ic, CAP_IC), rem=min(rem, CAP_REM), wg=wg)
def ci(iso, Y):
    c = components(iso, Y)
    if not c: return None
    parts = dict(cpia=.385 * c['cpia'], g=2.719 * c['g'] / 100, ic=4.052 * c['ic'] / 100, ic2=-3.99 * (c['ic'] / 100) ** 2,
                 rem=2.022 * c['rem'] / 100, wg=13.52 * c['wg'] / 100)
    return sum(parts.values()), parts, c
def category(x): return 'weak' if x < 2.69 else ('strong' if x > 3.05 else 'medium')
