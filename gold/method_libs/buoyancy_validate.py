"""Validate buoyancy estimator against Dudine & Jalles (2017) Appendix Tables A1a-c.
Usage: python3 -I scripts/buoyancy_validate.py  -> prints table, writes scripts/buoyancy_validation.json"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import buoyancy_lib as L
pub = json.load(open(os.path.join(L.HERE, 'buoyancy_published_A1.json')))
d = L.load()
rows = []
for gdpcode in ('NY.GDP.MKTP.CN', 'NGDP'):
    for iso, p in sorted(pub.items()):
        tax = d.get(('GC.TAX.TOTL.CN', iso)); gdp = d.get((gdpcode, iso))
        if not tax or not gdp or p['lr'] is None: continue
        e = L.estimate(tax, gdp)
        if not e: continue
        rows.append(dict(iso=iso, gdp=gdpcode, pub_lr=p['lr'], rec_lr=round(e['lr'], 3), pub_sr=p['sr'], rec_sr=round(e['sr'], 3), n=e['n'], first=e['first'], last=e['last']))
json.dump(rows, open(os.path.join(L.HERE, 'buoyancy_validation.json'), 'w'), indent=1)
for g in ('NY.GDP.MKTP.CN',):
    rs = [r for r in rows if r['gdp'] == g]
    for r in rs: print(r['iso'], r['first'], r['last'], r['n'], 'LR pub %.3f rec %.3f | SR pub %.3f rec %.3f' % (r['pub_lr'], r['rec_lr'], r['pub_sr'], r['rec_sr']))
    for tol in (0.05, 0.1, 0.15, 0.2, 0.3):
        print(g, 'tol', tol, 'LR match', sum(abs(r['pub_lr'] - r['rec_lr']) <= tol for r in rs), 'of', len(rs), '; SR match', sum(abs(r['pub_sr'] - r['rec_sr']) <= tol for r in rs))
