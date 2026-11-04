# RA-NN: traditional reserve-adequacy benchmarks (3 months of imports, 100% of short-term external debt, 20% of broad money) per IMF "Assessing Reserve Adequacy" (2011)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
R = psv('FI.RES.TOTL.CD'); I = psv('NE.IMP.GNFS.CD'); S = psv('DT.DOD.DSTC.CD'); M = psv('FM.LBL.BMNY.GD.ZS'); G = psv('NY.GDP.MKTP.CD'); N = names()
YEARS = list(range(2012, 2023))
def metrics(k, y):
    mo = R[k][y] / (I[k][y] / 12); std = 100 * R[k][y] / S[k][y]; m2 = 100 * R[k][y] / (M[k][y] / 100 * G[k][y])
    return mo, std, m2
def ok(k, y):
    if k not in N or N[k]['income_group'] in ('Aggregates', 'High income'): return False
    if not all(y in D.get(k, {}) and D[k][y] > 0 for D in (R, I, S, M, G)): return False
    mo, std, m2 = metrics(k, y)
    return abs(mo - 3) > 0.5 and abs(std - 100) > 15 and abs(m2 - 20) > 4
def flags(mo, std, m2): return (mo >= 3, std >= 100, m2 >= 20)
def build():
    rng = random.Random(37); cand = [(k, y) for k in R for y in YEARS if ok(k, y)]; rng.shuffle(cand)
    used = set(); n = 0
    hid = {}
    for y in YEARS:
        univ = lambda k: ok(k, y)
        for c in hidden_candidates(y, univ, rng): hid.setdefault(c[0], []).append((y, c[1]))
    # hidden candidates must be unique within the whole universe-region, already ensured; reject if country already used
    hk = list(hid); rng.shuffle(hk)
    for st in split_styles(5, 5, 4):
        n += 1; iid = 'RA-%02d' % n; pred = size = None
        if st == 'hidden':
            k = next(k for k in hk if k not in used); y, pred = rng.choice(hid[k]); size = 1
        else:
            k, y = next((k, y) for k, y in cand if k not in used)
        used.add(k); mo, std, m2 = metrics(k, y); f = flags(mo, std, m2); nm = cname(k)
        if st == 'named':
            q = ('Does %s hold enough foreign exchange reserves to withstand a sudden stop in capital flows as of %d?' % (nm, y)) if n % 2 else ('Were %s reserves adequate against external shocks in %d?' % (nm, y) if False else 'In %d, how comfortable was %s\'s reserve cushion against external financing pressure?' % (y, nm))
        elif st == 'hidden':
            q = 'Consider %s. How adequate were its foreign exchange reserves against external financing risks that year?' % pred
        else:
            truth = (n % 2 == 1); w = rng.choice([0, 1, 2]); nmz = ['imports', 'short-term external debt', 'broad money'][w]
            said = f[w] if truth else (not f[w])
            q = 'A staff note says that in %d the reserves of %s %s the customary cover benchmark for %s. Is that correct?' % (y, nm, 'met' if said else 'fell short of', nmz)
        vt = 'States %d of 3 benchmarks met (imports cover %s, short-term-debt cover %s, broad-money cover %s)%s' % (sum(f), 'met' if f[0] else 'missed', 'met' if f[1] else 'missed', 'met' if f[2] else 'missed', '; for claim items also judges the statement TRUE or FALSE' if st == 'claim' else '')
        comps = [('Reserves cover of %s imports in %d = %.1f months (benchmark 3)' % (nm, y, mo), round(mo, 3), 0.3, 'months', 'full = within 0.3 months (total reserves incl. gold over imports of goods and services / 12)'),
                 ('Reserves as a share of short-term external debt = %.0f %% (benchmark 100)' % std, round(std, 2), max(10.0, round(0.05 * std, 1)), 'percent', 'full = within 5 percent of the value (min 10 pp); short-term debt on original maturity'),
                 ('Reserves as a share of broad money (M2 = M2/GDP x GDP in US dollars) = %.1f %% (benchmark 20)' % m2, round(m2, 3), max(2.0, round(0.05 * m2, 1)), 'percent', 'full = within 5 percent of the value (min 2 pp)')]
        cl = mk_claims('Identifies that the answer uses the traditional reserve-adequacy rules of thumb: reserves of at least 3 months of imports, full (100 percent) cover of short-term external debt (Greenspan-Guidotti), and about 20 percent of broad money.',
                       'full = names the traditional / rule-of-thumb reserve adequacy metrics (imports, short-term debt, M2); acceptable alternative: IMF ARA risk-weighted metric if the three traditional metrics are also computed; no = reserves to GDP only, or a debt sustainability analysis',
                       comps, vt, 'full = benchmark verdicts match the recomputation', 'Uses WDI total reserves, imports of goods and services, short-term external debt, M2 as % GDP and GDP in current US dollars.')
        it = base_item(iid, {'named': 'M-named', 'hidden': 'M-hidden', 'claim': 'M-claim'}[st], q, 'reserve_adequacy_traditional_metrics',
                       ['e7c9a1d0-858e-4c4a-b336-1e4bd26d8504'], [], ['FI.RES.TOTL.CD', 'NE.IMP.GNFS.CD', 'DT.DOD.DSTC.CD', 'FM.LBL.BMNY.GD.ZS', 'NY.GDP.MKTP.CD'], st,
                       ['IMF risk-weighted ARA composite metric (needs exchange-rate regime, portfolio liabilities)', 'external debt sustainability analysis', 'debt-carrying-capacity classification', 'reserves-to-GDP ratio only'], True, cl,
                       None, round(mo, 3), 0.3, 'gold_scripts/ext_procedures/build_reserve_adequacy.py',
                       'non-high-income countries, 2012-2022, all five series present, 0.5 months / 15 pp / 4 pp away from each benchmark; seeded draw; one per country',
                       ['IMF (2011) Assessing Reserve Adequacy, traditional-metrics section', 'frozen WDI 2026-10-08 extract (frozen_extra/wdi_20261008_ara_ig_extract.psv)'], size, pred,
                       'No corpus country report is the gold source; recomputed from frozen WDI. Cross-check against WDI own months-of-imports series failed (that series excludes gold, 443 of 5942 country-years match), so it is not used as a published value.')
        it['iso3'] = k; it['year'] = y; it['method_class'] = 'institutional procedure'
        save('reserve_adequacy_traditional', it)
    return n
if __name__ == '__main__':
    print(build())
