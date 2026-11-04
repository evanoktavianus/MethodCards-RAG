import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from ci_lib import *
P = json.load(open(os.path.join(os.path.dirname(__file__), 'published_ci.json')))
TOL = 0.10
rows = []
for p in P:
    r = ci(p['iso3'], p['year'])
    if not r: rows.append((p, None)); continue
    rows.append((p, r[0]))
ok = [(p, v) for p, v in rows if v is not None and abs(v - p['published_ci']) <= TOL]
print('country-years with published CI:', len(P), ' recomputable:', sum(v is not None for _, v in rows), ' within +/-%.2f: %d' % (TOL, len(ok)))
print('category agrees (all recomputable):', sum(v is not None and category(v) == category(p['published_ci']) for p, v in rows))
print('iso3 year published recomputed diff cat_pub cat_mine within')
for p, v in rows:
    if v is None: print(p['iso3'], p['year'], p['published_ci'], 'NA'); continue
    print(p['iso3'], p['year'], p['published_ci'], round(v, 3), round(v - p['published_ci'], 3), category(p['published_ci']), category(v), 'Y' if abs(v - p['published_ci']) <= TOL else 'n')
