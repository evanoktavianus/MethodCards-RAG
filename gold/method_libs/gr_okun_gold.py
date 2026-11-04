"""Regenerates items/okun_difference/OKUN-*.json. python3 -I scripts/gr_okun_gold.py"""
import json, os, sys, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gr_okun_lib import LUR, G, NAMES, fit, sample, ols
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'items', 'okun_difference'); os.makedirs(OUT, exist_ok=True)
DOC = '89d05760-b533-4e9d-b20b-baf123bafa80'
W = (1993, 2019)
def N(i): return {'ESP':'Spain','USA':'the United States','GBR':'the United Kingdom','KOR':'South Korea','CHL':'Chile','BRA':'Brazil','CAN':'Canada','DEU':'Germany','GRC':'Greece','JPN':'Japan','MEX':'Mexico','SWE':'Sweden','ITA':'Italy','AUS':'Australia','PRT':'Portugal','IRL':'Ireland'}[i]
# indicators for hidden-subject conditions (over every country where computable)
def ind(iso):
    u, g = LUR.get(iso, {}), G.get(iso, {}); d = {}
    if 2009 in u and 2008 in u: d['du2009'] = u[2009] - u[2008]
    gs = [g[t] for t in range(1993, 2020) if t in g]
    if len(gs) == 27: d['avg_g'] = sum(gs) / 27; d['min_g'] = min(gs)
    if 2019 in u: d['u2019'] = u[2019]
    if 2009 in g: d['g2009'] = g[2009]
    if 2000 in u: d['u2000'] = u[2000]
    us = [u[t] for t in range(1993, 2020) if t in u]
    if len(us) == 27: d['maxu'] = max(us)
    return d
IND = {i: ind(i) for i in set(LUR) | set(G)}
def uniq(target, conds):
    s = [i for i, d in IND.items() if all(k in d and (d[k] > t if op == '>' else d[k] < t) for k, op, t in conds)]
    return s == [target]
def hidden_cond(target):
    import math
    d = IND[target]
    def thr(k, op, r):
        v = d[k]; return math.floor(v / r) * r if op == '>' else math.ceil(v / r) * r
    for nk in (2, 3):
        for ks in itertools.combinations(['du2009', 'avg_g', 'min_g', 'u2019', 'g2009', 'u2000', 'maxu'], nk):
            for r in (1, 0.5, 0.25, 0.1):
                for ops in itertools.product('<>', repeat=nk):
                    c = [(k, op, round(thr(k, op, r), 2)) for k, op in zip(ks, ops)]
                    if all((d[k] > t if op == '>' else d[k] < t) for k, op, t in c) and uniq(target, c): return c
    return None
TXT = {'du2009': 'its unemployment rate changed by {op} {t:g} percentage points between 2008 and 2009',
       'avg_g': 'its average annual real GDP growth over 1993 to 2019 was {op} {t:g} percent',
       'min_g': 'its weakest single year of real GDP growth between 1993 and 2019 was {op} {t:g} percent',
       'u2019': 'its unemployment rate in 2019 was {op} {t:g} percent',
       'g2009': 'its real GDP growth in 2009 was {op} {t:g} percent',
       'u2000': 'its unemployment rate in 2000 was {op} {t:g} percent',
       'maxu': 'its highest unemployment rate between 1993 and 2019 was {op} {t:g} percent'}
def cond_text(c):
    return ' and '.join(TXT[k].format(op='above' if op == '>' else 'below', t=t) for k, op, t in c)
# (id, style, iso, quantity, param, claimed value or None)
SPEC = [('named','ESP','beta',None,None),('named','USA','neutral',None,None),('named','GBR','pred',-3,None),
        ('named','KOR','beta',None,None),('named','CHL','neutral',None,None),('named','BRA','pred',-2,None),
        ('hidden','CAN','beta',None,None),('hidden','DEU','pred',-4,None),('hidden','GRC','beta',None,None),
        ('hidden','JPN','neutral',None,None),('hidden','MEX','pred',-6,None),('hidden','SWE','beta',None,None),
        ('claim','ITA','beta',None,0.3),('claim','AUS','beta',None,0.6),('claim','PRT','neutral',None,1.5),('claim','IRL','neutral',None,1.5)]
TOL = {'beta': 0.05, 'neutral': 0.4, 'pred': 0.25}
def query(style, iso, q, p, claimed):
    w = 'from 1993 to 2019'
    if style == 'named':
        c = N(iso)
        if q == 'beta': return "Using %s's annual data %s, by how many percentage points does the unemployment rate typically change when real GDP growth is one percentage point lower? Show how you obtained the figure." % (c[0].upper()+c[1:] if c[0]!='t' else c, w)
        if q == 'neutral': return "Based on annual data %s, what rate of real GDP growth has been consistent with an unchanged unemployment rate in %s? Show how you obtained the figure." % (w, c)
        return "Suppose real GDP in %s were to change by %d percent in one year. Based on the relationship between growth and the change in the unemployment rate in annual data %s, how many percentage points would you expect the unemployment rate to move? Show how you obtained the figure." % (c, p, w)
    if style == 'hidden':
        cc = cond_text(hidden_cond(iso)); base = "There is exactly one economy in the IMF World Economic Outlook database (October 2025) for which %s. " % cc
        if q == 'beta': return base + "For that economy, using annual data %s, by how many percentage points does the unemployment rate typically change when real GDP growth is one percentage point lower? Show how you obtained the figure." % w
        if q == 'neutral': return base + "For that economy, based on annual data %s, what rate of real GDP growth has been consistent with an unchanged unemployment rate? Show how you obtained the figure." % w
        return base + "Suppose its real GDP were to change by %d percent in one year. Based on the relationship between growth and the change in the unemployment rate in annual data %s, how many percentage points would you expect its unemployment rate to move? Show how you obtained the figure." % (p, w)
    c = N(iso)
    if q == 'beta': return "An analyst note says: \"In %s, each percentage point of slower real GDP growth has typically added about %.1f percentage points to the unemployment rate (annual data %s).\" Is this statement accurate?" % (c, claimed, w)
    return "An analyst note says: \"In %s, real GDP has had to grow by roughly %.1f percent a year just to keep the unemployment rate from rising (annual data %s).\" Is this statement accurate?" % (c, claimed, w)
n = 0; out = []
for style, iso, q, p, claimed in SPEC:
    n += 1; f = fit(iso, *W); a, b = f['alpha'], f['beta']
    val = {'beta': -b, 'neutral': f['neutral_growth'], 'pred': a + b * (p if p is not None else 0)}[q]
    tol = TOL[q]; true = None
    if style == 'claim':
        true = abs(claimed - val) <= tol
        assert abs(abs(claimed - val) - tol) > 0.1 * tol and (true or abs(claimed - val) > 2 * tol), (iso, claimed, val)
    desc = {'beta': 'Okun slope (pp rise in unemployment per 1pp slower growth, sign flipped)', 'neutral': 'growth rate at which the fitted change in unemployment is zero (-alpha/beta)', 'pred': 'fitted change in unemployment (pp) for the stated growth'}[q]
    hid = hidden_cond(iso) if style == 'hidden' else None
    if style == 'hidden': assert hid and uniq(iso, hid)
    item = {
      'id': 'OKUN-%02d' % n, 'family': 'methodology', 'method': 'okun_difference', 'style': style, 'tier': 'medium', 'status': 'validated',
      'validation_label': 'formula-validated', 'method_kind': 'textbook identity', 'famous_method': True,
      'query': query(style, iso, q, p, claimed),
      'claims': {
        'text': [{'id': 'T1', 'kind': 'text', 'importance': 'vital', 'text': 'Identifies the applicable methodology: a simple regression of the annual change in the unemployment rate on real GDP growth (the output-unemployment relationship, Okun-type law, difference form).',
                  'accept': 'Okun-type difference-form regression of change in unemployment rate on real GDP growth (levels-gap form acceptable only if it reproduces the same quantity from the same data); NOT a Phillips curve, NOT an employment-elasticity or output-gap calculation.',
                  'supporting_passages': ['%s p.89-91 eq.(2); p.117-118 (Delta u = alpha + beta Delta y)' % DOC]}],
        'data': [{'id': 'D1', 'kind': 'data', 'importance': 'okay', 'text': 'Uses WEO unemployment rate (LUR) and real GDP growth (NGDP_RPCH), annual, %d to %d (change in unemployment needs LUR from %d).' % (W[0], W[1], W[0]-1)}],
        'computation': []},
      'grading': {'tolerance': 'absolute %.2f %s; OLS with intercept, one regressor (growth), annual, 1993-2019 inclusive; slope reported as a positive number = pp rise in unemployment per 1pp slower growth' % (tol, 'percentage points' if q != 'neutral' else 'percentage points of growth'),
                  'sensitivity_note': 'see sens fields in validation'},
      'provenance': {'frozen_data': 'frozen_extra/weo_oct2025_lur.csv, weo_oct2025_ngdp_rpch.csv (WEO Oct 2025)', 'gold_script': 'scripts/gr_okun_gold.py (lib scripts/gr_okun_lib.py)'},
      'method_doc_ids': [DOC], 'gold_report_ids': [], 'published_value': None,
      'published_note': 'No published figure for these exact data/window; Nicaragua 2022 Article IV (bbf21b8d-fcdf-4423-8f2c-9ab49d0d9713 p53) quotes quarterly Okun coefficients (advanced economies about -0.3, CAPDR about -0.16) which are in the same range as our annual slopes but not a like-for-like match.',
      'recomputed_value': round(val, 4), 'quantity': desc, 'country_iso3': iso, 'inputs': ['LUR', 'NGDP_RPCH'],
      'distractors': ['Phillips-curve wage/inflation relation', 'output-gap based natural-rate (NAIRU) estimation', 'employment elasticity of growth', 'fiscal multiplier / sensitivity of the budget to growth'],
      'gold_script': 'scripts/gr_okun_gold.py', 'alpha': round(a, 4), 'beta_slope': round(b, 4), 'r2': round(f['r2'], 3), 'n_obs': f['n'],
      'validation': {'sens_1995_2019_beta': round(-fit(iso, 1995, 2019)['beta'], 3) if fit(iso, 1995, 2019) else None,
                     'sens_1993_2024_beta': round(-fit(iso, 1993, 2024)['beta'], 3) if fit(iso, 1993, 2024) else None}}
    if q == 'pred': item['scenario_growth_pct'] = p
    if hid: item['hidden_condition'] = [list(c) for c in hid]; item['hidden_set_size'] = 1
    ans = {'beta': 'the slope is about %.2f' % -b, 'neutral': 'about %.1f percent growth' % f['neutral_growth'], 'pred': 'about %+.2f percentage points' % val}[q]
    comp = {'id': 'C1', 'kind': 'computation', 'importance': 'vital', 'text': 'Gold %s for %s: %.3f (tolerance +-%.2f).' % (desc, NAMES[iso] if False else iso, val, tol), 'target': round(val, 3), 'tolerance_abs': tol}
    item['claims']['computation'].append(comp)
    if style == 'claim':
        item['truth'] = bool(true)
        item['claims']['computation'].append({'id': 'A1', 'kind': 'answer', 'importance': 'vital', 'text': 'Verdict: the statement is %s (claimed %.1f vs recomputed %.2f, tolerance +-%.2f).' % ('accurate' if true else 'not accurate', claimed, val, tol), 'target': 'accurate' if true else 'not accurate'})
    item['answer_summary'] = 'For %s, %s.' % (iso, ans)
    json.dump(item, open(os.path.join(OUT, item['id'] + '.json'), 'w'), indent=1)
    out.append((item['id'], style, iso, q, round(val, 3), item.get('truth'), item['query'][:150]))
for o in out: print(o)
