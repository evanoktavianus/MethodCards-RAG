import json, os, sys, itertools
sys.path.insert(0, os.path.dirname(__file__))
from ci_lib import *
P = json.load(open(os.path.join(os.path.dirname(__file__), 'published_ci.json')))
def margin(x): return min(abs(x - 2.69), abs(x - 3.05))
elig = []
for p in P:
    r = ci(p['iso3'], p['year'])
    if not r: continue
    v = r[0]
    if abs(v - p['published_ci']) <= 0.10 and category(v) == category(p['published_ci']) and margin(v) >= 0.05 and margin(p['published_ci']) >= 0.03:
        elig.append(dict(p, recomputed=v))
if __name__ == '__main__':
    print(len(elig), 'eligible')
    for e in elig: print(e['iso3'], e['year'], e['published_ci'], round(e['recomputed'], 3), category(e['recomputed']))
    # hidden-subject predicate search over all WEO economies, year 2023 values
    PC = {i: GDPPC[i].get(2023) for i in GDPPC}
    pop = LP; gr = G
    import csv
    inf = {}
    for r in csv.DictReader(open(FE + '/weo_oct2025_pcpipch.csv')):
        inf[r['iso3']] = {int(k): float(v) for k, v in r.items() if k.isdigit() and v}
    feats = {'pop2023': lambda i: pop.get(i, {}).get(2023), 'gdppc2023': lambda i: PC.get(i), 'growth2023': lambda i: gr.get(i, {}).get(2023), 'infl2023': lambda i: inf.get(i, {}).get(2023)}
    univ = [i for i in GDPPC if all(f(i) is not None for f in feats.values())]
    print(len(univ), 'universe')
    tgt = {e['iso3'] for e in elig}
    for t in sorted(tgt):
        found = None
        for (a, fa), (b, fb) in itertools.combinations(feats.items(), 2):
            for da in ('<', '>'):
                for db in ('<', '>'):
                    # choose thresholds just beyond target value (rounded)
                    ta, tb = fa(t), fb(t)
                    if ta is None or tb is None: continue
                    import math
                    for ra in (lambda x: round(x, -2) if abs(x) > 500 else round(x, 0), lambda x: round(x, 1)):
                        xa = ra(ta) + (1 if da == '<' else -1) * 0 ; xb = ra(tb)
                    # simple: thresholds are target value rounded outward to 2 sig digits
                    def out(x, d):
                        s = 10 ** (math.floor(math.log10(abs(x))) - 1) if x else 1
                        return (math.ceil(x / s) * s) if d == '<' else (math.floor(x / s) * s)
                    xa, xb = out(ta, da), out(tb, db)
                    m = [i for i in univ if (fa(i) < xa if da == '<' else fa(i) > xa) and (fb(i) < xb if db == '<' else fb(i) > xb)]
                    if m == [t]: found = (a, da, xa, b, db, xb); break
                if found: break
            if found: break
        print(t, found)
