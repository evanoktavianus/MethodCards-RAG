# MC-NN: Maastricht-type convergence tests (deficit <=3, debt <=60, inflation <= mean of three lowest EU rates + 1.5pp) from frozen WEO Oct 2025
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
DEF = weo('ggxcnl_ngdp'); DEBT = weo('ggxwdg_ngdp'); INF = weo('pcpipch')
def ref(y):
    v = sorted(INF[k][y] for k in EU27 if y in INF.get(k, {}))
    return sum(v[:3]) / 3 + 1.5, v[:3]
def row(k, y):
    d = -DEF[k][y]; db = DEBT[k][y]; p = INF[k][y]; r, _ = ref(y)
    return d, db, p, r, p - r
def robust(k, y):
    if not all(y in D.get(k, {}) for D in (DEF, DEBT, INF)): return False
    d, db, p, r, m = row(k, y)
    return abs(d - 3) > 0.4 and abs(db - 60) > 3 and abs(m) > 0.4
YEARS = list(range(2012, 2025))
def verdict(d, db, m): return (d <= 3, db <= 60, m <= 0)
def words(v): return ['deficit %s' % ('met' if v[0] else 'missed'), 'debt %s' % ('met' if v[1] else 'missed'), 'inflation %s' % ('met' if v[2] else 'missed')]
def build():
    rng = random.Random(23); cand = [(k, y) for k in EU27 for y in YEARS if robust(k, y)]
    rng.shuffle(cand); used = set(); items = []; n = 0
    def take(pred=lambda k, y: True):
        for k, y in cand:
            if k not in used and pred(k, y): return k, y
    hid = {}
    for y in YEARS:
        for m_, hi_lo in (('ggxwdg_ngdp', 'hi'), ('pcpipch', 'hi'), ('pcpipch', 'lo'), ('ggxcnl_ngdp', 'lo')):
            W = {'ggxwdg_ngdp': DEBT, 'pcpipch': INF, 'ggxcnl_ngdp': DEF}[m_]
            lst = sorted((W[k][y], k) for k in EU27 if y in W.get(k, {}))
            t = lst[-1] if hi_lo == 'hi' else lst[0]
            if sum(1 for v, _ in lst if v == t[0]) == 1 and robust(t[1], y):
                ph = {('ggxwdg_ngdp', 'hi'): 'the highest gross public debt ratio', ('pcpipch', 'hi'): 'the highest consumer price inflation',
                      ('pcpipch', 'lo'): 'the lowest consumer price inflation', ('ggxcnl_ngdp', 'lo'): 'the largest general government deficit'}[(m_, hi_lo)]
                hid.setdefault(t[1], []).append((y, 'the European Union member with %s in %d' % (ph, y), 1))
    hk = [k for k in hid]; rng.shuffle(hk)
    for st in split_styles(6, 5, 5):
        n += 1; iid = 'MC-%02d' % n; pred = size = None
        if st == 'hidden':
            k = next(k for k in hk if k not in used); y, pred, size = rng.choice(hid[k])
        else:
            k, y = take()
        used.add(k); d, db, p, r, m = row(k, y); v = verdict(d, db, m); nm = cname(k)
        if st == 'named':
            q = ('In %d, would %s have passed the public-finance and price-stability tests a European Union member must meet before adopting the euro?' % (y, nm)) if n % 2 else ('Did %s clear the euro-entry bar on deficit, debt and inflation in %d?' % (nm, y))
        elif st == 'hidden':
            q = 'Consider %s. Did it pass the public-finance and price-stability tests for euro adoption that year?' % pred
        else:
            truth = (n % 2 == 1)
            which = rng.choice([0, 1, 2]); nmz = ['deficit', 'debt', 'inflation'][which]
            said = v[which] if truth else (not v[which])
            q = 'A convergence note says that in %d %s %s the %s test for euro entry. Is that correct?' % (y, nm, 'passed' if said else 'failed', nmz)
        vt = 'States %s (%d of 3 tests met: %s)%s' % ('; '.join(words(v)), sum(v), 'deficit, debt, inflation', '; for claim items also judges the statement TRUE or FALSE by comparing with this result' if st == 'claim' else '')
        comps = [('Euro-entry inflation limit in %d = mean of the three lowest EU inflation rates plus 1.5 pp = %.2f %%' % (y, r), round(r, 3), 0.3, 'percent', 'full = within 0.3 pp (simple average of three lowest EU rates, consumer prices)'),
                 ('%s inflation minus that limit in %d = %+.2f pp' % (nm, y, m), round(m, 3), 0.3, 'pp', 'full = within tolerance; sign matters'),
                 ('%s general government deficit in %d = %.2f %% of GDP (limit 3)' % (nm, y, d), round(d, 3), 0.3, 'percent of GDP', 'full = within tolerance'),
                 ('%s gross public debt in %d = %.1f %% of GDP (limit 60)' % (nm, y, db), round(db, 2), 1.0, 'percent of GDP', 'full = within tolerance')]
        cl = mk_claims('Identifies that the answer applies the Maastricht (euro-adoption) convergence criteria: deficit at or below 3 percent of GDP, debt at or below 60 percent, inflation within 1.5 pp of the three best performers.',
                       'full = names the Maastricht / euro convergence criteria; acceptable alternatives: EMU entry tests; no = Stability and Growth Pact fiscal rules only, debt sustainability analysis, or fiscal-rule calibration',
                       comps, vt, 'full = verdict per test matches the recomputation', 'Uses WEO general government net lending/borrowing (GGXCNL_NGDP), gross debt (GGXWDG_NGDP) and CPI inflation (PCPIPCH) for EU27.')
        it = base_item(iid, {'named': 'M-named', 'hidden': 'M-hidden', 'claim': 'M-claim'}[st], q, 'maastricht_convergence_criteria',
                       ['e3b52b4e-bd1c-4659-b48e-6cf3c5b854c6'], [], ['GGXCNL_NGDP', 'GGXWDG_NGDP', 'PCPIPCH'], st,
                       ['Stability and Growth Pact fiscal-rule compliance', 'debt-stabilising primary balance', 'public debt sustainability analysis', 'fiscal-rule calibration'], True, cl,
                       round(r, 3), round(r, 3), 0.3, 'gold_scripts/ext_procedures/build_convergence.py',
                       'EU27 country-years 2012-2024 where deficit is 0.4pp+ from 3, debt 3pp+ from 60, inflation 0.4pp+ from the limit; seeded draw; one per country',
                       ['IMF WEO Oct 1996 (EMU and the World Economy), convergence-table notes', 'frozen WEO Oct 2025 (reference_data + frozen_extra)'], size, pred,
                       'No corpus country report is the gold source; values are recomputed from frozen WEO. Proxy caveat: consumer-price inflation (PCPIPCH) stands in for the treaty HICP measure, and the three lowest rates are taken over all EU27 without outlier screening (the note says a simple average of the three is used for illustration).')
        it['iso3'] = k; it['year'] = y; it['method_class'] = 'institutional procedure'
        save('convergence_criteria', it)
    return n
if __name__ == '__main__':
    print(build())
