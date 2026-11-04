"""Selection rule for the instance extension (CI-21..). Run with python3 -I.
Pool: every published country-year in published_ci.json (68) and published_ci_extension.json (66) that is not already an item.
Eligible = recomputable from frozen data AND |recomputed - published| <= 0.10 AND same class AND recomputed score >= 0.05 from both cutoffs
           AND published score >= 0.03 from both cutoffs (same margin filter as the first 20 items).
Selection = at most 2 country-years per country (keep the smallest |diff|), then drop the largest-|diff| ones until 20 remain."""
import json, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ci_lib import *
HERE = os.path.dirname(os.path.abspath(__file__))
def margin(x): return min(abs(x - 2.69), abs(x - 3.05))
used = {(json.load(open(f))['subject']['iso3'], json.load(open(f))['subject']['year']) for f in glob.glob(HERE + '/../../items/lic_dsf_ci/CI-*.json')
        if not json.load(open(f)).get('instance_extension')}
P0 = json.load(open(HERE + '/published_ci.json')); P1 = json.load(open(HERE + '/published_ci_extension.json'))
def pool_stats():
    n = rc = wi = sc = 0
    for p in P1:
        n += 1; r = ci(p['iso3'], p['year'])
        if not r: continue
        rc += 1; d = abs(r[0] - p['published_ci']); wi += d <= .1; sc += d <= .1 and category(r[0]) == category(p['published_ci'])
    return dict(parsed_new=n, recomputable=rc, within_010=wi, within_and_same_class=sc)
def eligible():
    el = []
    for p in P0 + P1:
        if (p['iso3'], p['year']) in used: continue
        r = ci(p['iso3'], p['year'])
        if r and abs(r[0] - p['published_ci']) <= .1 and category(r[0]) == category(p['published_ci']) and margin(r[0]) >= .05 and margin(p['published_ci']) >= .03:
            el.append(dict(p, recomputed=r[0], diff=abs(r[0] - p['published_ci']), origin='extension' if 'source' in p else 'original_list'))
    return el
def select(n=20):
    by = {}
    for e in sorted(eligible(), key=lambda e: e['diff']): by.setdefault(e['iso3'], []).append(e)
    cand = [e for v in by.values() for e in v[:2]]
    cand.sort(key=lambda e: e['diff']); cand = cand[:n]
    return sorted(cand, key=lambda e: (e['iso3'], e['year']))
if __name__ == '__main__':
    print(pool_stats(), 'eligible', len(eligible()))
    for e in select(): print(e['iso3'], e['year'], e['published_ci'], round(e['recomputed'], 3), round(e['diff'], 3), category(e['recomputed']), e['origin'])
